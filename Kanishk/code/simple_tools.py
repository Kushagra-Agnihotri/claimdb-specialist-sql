"""Simple path (pathway #3): the judge checks a claim with a small Python lookup tool instead of writing SQL
or calling an NL2SQL builder.

Two tools per database:
  <db>_describe_tables(table="")   lists every table with its columns (or one table's columns with example values)
  <db>_lookup(table, filters, aggregate, column, columns, group_by, order_by, descending, limit)
                                   one-table lookup with simple filters and an optional count / sum / avg / min / max
The judge fills in arguments; Python checks every table and column name against the real schema, builds a
parameterised SQLite query itself and runs it read only. The judge never writes SQL, so there are no syntax
errors, and a wrong name gets a helpful message with the closest real names instead of "no such column".
"""
import difflib, json, re, sqlite3, time
from pathlib import Path
from typing import Literal, Optional, Union

try:
    from pydantic import BaseModel, Field

    class Filter(BaseModel):
        """One condition on a column of the looked-up table."""
        column: str = Field(..., description="column name in the table")
        op: Literal["=", "!=", ">", ">=", "<", "<=", "contains", "starts_with", "is_null", "not_null"] = Field(
            "=", description="comparison; text '=' ignores upper/lower case; 'contains' matches part of a text")
        value: Optional[Union[str, float, int]] = Field(None, description="value to compare with (not needed for is_null / not_null)")
except ImportError:      # the engine itself works without pydantic (used for offline tests)
    Filter = dict

OPS = ("=", "!=", ">", ">=", "<", "<=", "contains", "starts_with", "is_null", "not_null")
AGGS = ("none", "count", "count_distinct", "sum", "avg", "min", "max")
NUMERIC = ("INT", "REAL", "FLOA", "DOUB", "NUM", "DEC")


def _q(name):
    return '"' + name.replace('"', '""') + '"'


def _norm(s):
    return re.sub(r"[^a-z0-9]", "", str(s).lower())


class LookupError_(Exception):
    pass


class LookupEngine:
    def __init__(self, db_file: Path, max_rows: int = 100, timeout: int = 30):
        self.db_file, self.max_rows, self.timeout = db_file, max_rows, timeout
        con = self._connect()
        self.tables = {}                                    # real table name -> [(column, declared type)]
        for (t,) in con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY rowid"):
            self.tables[t] = [(r[1], (r[2] or "").upper()) for r in con.execute(f"PRAGMA table_info({_q(t)})")]
        con.close()

    # ------------------------------------------------------------------ helpers
    def _connect(self):
        con = sqlite3.connect(f"file:{self.db_file}?mode=ro", uri=True)
        start = time.time()
        con.set_progress_handler(lambda: 1 if time.time() - start > self.timeout else 0, 1000)
        return con

    @staticmethod
    def _resolve(name, candidates, kind, where=""):
        """exact, then case-insensitive, then ignoring spaces/underscores/punctuation; otherwise a helpful error."""
        if name in candidates:
            return name
        low = {c.lower(): c for c in candidates}
        if str(name).lower() in low:
            return low[str(name).lower()]
        nm = {_norm(c): c for c in candidates}
        if _norm(name) in nm:
            return nm[_norm(name)]
        close = difflib.get_close_matches(str(name), list(candidates), n=3, cutoff=0.5)
        hint = f" Closest names: {', '.join(close)}." if close else ""
        raise LookupError_(f"error: there is no {kind} called '{name}'{where}.{hint} "
                           f"Available {kind}s: {', '.join(candidates)}.")

    def _table(self, table):
        return self._resolve(table, list(self.tables), "table")

    def _col(self, t, column):
        return self._resolve(column, [c for c, _ in self.tables[t]], "column", f" in table '{t}'")

    def _is_num(self, t, c):
        typ = dict(self.tables[t])[c]
        return any(k in typ for k in NUMERIC)

    @staticmethod
    def _to_num(v):
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            return v
        try:
            f = float(str(v).replace(",", "").strip())
            return int(f) if f.is_integer() and "." not in str(v) else f
        except (TypeError, ValueError):
            return v

    def _examples(self, t, c, k=5):
        con = self._connect()
        try:
            return [r[0] for r in con.execute(f"SELECT DISTINCT {_q(c)} FROM {_q(t)} WHERE {_q(c)} IS NOT NULL LIMIT {k}")]
        except sqlite3.Error:
            return []
        finally:
            con.close()

    def _similar(self, t, c, value, k=8):
        """Stored values that look like the value the judge searched for (substring first, then fuzzy match)."""
        v = "" if value is None else str(value).strip()
        con = self._connect()
        try:
            out = [r[0] for r in con.execute(
                f"SELECT DISTINCT {_q(c)} FROM {_q(t)} WHERE {_q(c)} LIKE ? LIMIT {k}", (f"%{v}%",))] if v else []
            if not out:
                pool = [r[0] for r in con.execute(
                    f"SELECT DISTINCT {_q(c)} FROM {_q(t)} WHERE {_q(c)} IS NOT NULL LIMIT 5000")]
                low = {str(p).lower(): p for p in pool}
                out = [low[m] for m in difflib.get_close_matches(v.lower(), list(low), n=k, cutoff=0.4)] or pool[:k]
            return out
        except sqlite3.Error:
            return []
        finally:
            con.close()

    # ------------------------------------------------------------------ tool 1
    def describe(self, table: str = "") -> str:
        if not table:
            return "\n".join(f"{t}({', '.join(c + (' ' + typ if typ else '') for c, typ in cols)})"
                             for t, cols in self.tables.items())
        t = self._table(table)
        lines = [f"Table {t}:"]
        for c, typ in self.tables[t]:
            ex = ", ".join(repr(v)[:40] for v in self._examples(t, c, 3))
            lines.append(f"  {c} {typ}  e.g. {ex}")
        con = self._connect()
        try:
            fks = con.execute(f"PRAGMA foreign_key_list({_q(t)})").fetchall()   # id, seq, table, from, to, ...
        finally:
            con.close()
        if fks:
            lines.append("Links to other tables: " + "; ".join(f"{fk[3]} -> {fk[2]}.{fk[4] or 'id'}" for fk in fks))
        return "\n".join(lines)

    # ------------------------------------------------------------------ tool 2
    def build(self, table, filters=None, aggregate="none", column="", columns=None, group_by="", order_by="",
              descending=False, limit=20):
        t = self._table(table)
        aggregate = (aggregate or "none").lower().strip()
        if aggregate not in AGGS:
            raise LookupError_(f"error: aggregate must be one of {', '.join(AGGS)}.")
        where, params = [], []
        for f in filters or []:
            f = f if isinstance(f, dict) else f.model_dump()
            c = self._col(t, f.get("column", ""))
            op = str(f.get("op", "=")).strip().lower().replace(" ", "_")
            op = {"==": "=", "<>": "!=", "like": "contains", "is_not_null": "not_null", "isnull": "is_null"}.get(op, op)
            if op not in OPS:
                raise LookupError_(f"error: filter op must be one of {', '.join(OPS)}.")
            v = f.get("value")
            if op == "is_null":
                where.append(f"{_q(c)} IS NULL")
            elif op == "not_null":
                where.append(f"{_q(c)} IS NOT NULL")
            elif op == "contains":
                where.append(f"{_q(c)} LIKE ?"); params.append(f"%{v}%")
            elif op == "starts_with":
                where.append(f"{_q(c)} LIKE ?"); params.append(f"{v}%")
            elif self._is_num(t, c) or (op not in ("=", "!=") and isinstance(self._to_num(v), (int, float))):
                where.append(f"{_q(c)} {op} ?"); params.append(self._to_num(v))
            else:   # text equality ignores case and surrounding spaces
                where.append(f"TRIM({_q(c)}) {op} ? COLLATE NOCASE"); params.append(str(v).strip())
        wsql = f" WHERE {' AND '.join(where)}" if where else ""
        limit = max(1, min(int(limit or 20), self.max_rows))
        gb = self._col(t, group_by) if group_by else ""
        if aggregate == "none":
            cols = [self._col(t, c) for c in (columns or [])] or [c for c, _ in self.tables[t]]
            sel = ", ".join(_q(c) for c in cols)
            if gb:
                sel = f"{_q(gb)}, COUNT(*) AS row_count"
            sql = f"SELECT {sel} FROM {_q(t)}{wsql}" + (f" GROUP BY {_q(gb)}" if gb else "")
        else:
            if aggregate == "count" and not column:
                expr = "COUNT(*)"
            else:
                if not column:
                    raise LookupError_(f"error: aggregate '{aggregate}' needs a column.")
                c = self._col(t, column)
                expr = {"count": f"COUNT({_q(c)})", "count_distinct": f"COUNT(DISTINCT {_q(c)})", "sum": f"SUM({_q(c)})",
                        "avg": f"AVG({_q(c)})", "min": f"MIN({_q(c)})", "max": f"MAX({_q(c)})"}[aggregate]
            sql = f"SELECT {(_q(gb) + ', ') if gb else ''}{expr} AS value FROM {_q(t)}{wsql}" + (f" GROUP BY {_q(gb)}" if gb else "")
        if order_by:
            ob = "value" if order_by.lower() in ("value", "result") and aggregate != "none" else \
                 ("row_count" if order_by.lower() in ("row_count", "count") and gb and aggregate == "none" else _q(self._col(t, order_by)))
            sql += f" ORDER BY {ob} {'DESC' if descending else 'ASC'}"
        if aggregate == "none" or gb:
            sql += f" LIMIT {limit}"
        return t, sql, params, wsql

    def lookup(self, **kw):
        """Returns (text for the judge, log dict)."""
        try:
            t, sql, params, wsql = self.build(**kw)
        except LookupError_ as e:
            return str(e), {"error": str(e)}
        except Exception as e:  # bad argument types etc.
            return f"error: could not run the lookup: {e}", {"error": str(e)}
        con = self._connect(); con.row_factory = sqlite3.Row
        try:
            rows = [dict(r) for r in con.execute(sql, params).fetchall()]
            n_match = con.execute(f"SELECT COUNT(*) FROM {_q(t)}{wsql}", params).fetchone()[0]
        except sqlite3.Error as e:
            msg = "query timed out" if "interrupted" in str(e) else str(e)
            return f"error: the lookup failed: {msg}", {"sql": sql, "params": params, "error": msg}
        finally:
            con.close()
        out = {"rows_matching_filters": n_match, "result": rows}
        if n_match == 0 and kw.get("filters"):   # most often a value written differently: show real values
            hints = {}
            for f in kw["filters"]:
                f = f if isinstance(f, dict) else f.model_dump()
                try:
                    c = self._col(t, f.get("column", ""))
                except LookupError_:
                    continue
                op = str(f.get("op", "=")).strip().lower()
                if self._is_num(t, c) or op not in ("=", "==", "starts_with", "contains", "like"):
                    continue
                v = str(f.get("value", "")).strip()
                con = self._connect()
                try:   # does this value exist in the column on its own?
                    alone = con.execute(f"SELECT 1 FROM {_q(t)} WHERE TRIM({_q(c)}) LIKE ? LIMIT 1",
                                        (v if op in ("=", "==") else f"%{v}%",)).fetchone()
                except sqlite3.Error:
                    alone = True
                finally:
                    con.close()
                if not alone:
                    hints[c] = self._similar(t, c, v)
            if hints:
                out["note"] = ("No rows matched. These searched values do not exist in the column; stored values that "
                               "look similar are shown (the value may be written differently in the database).")
                out["similar_stored_values"] = hints
            else:
                out["note"] = "No rows matched. Each searched value exists in its column, but no row matches all filters together."
        text = json.dumps(out, default=str, separators=(",", ":"))
        if (not kw.get("aggregate") or kw.get("aggregate") == "none") and not kw.get("group_by"):
            if n_match > len(rows):
                text += f"\n[Showing {len(rows)} of {n_match} matching rows. Use an aggregate or more filters.]"
        return text, {"sql": sql, "params": params, "error": None, "n_rows": len(rows), "n_match": n_match}
