"""Adds condition S (simple path: judge + Python lookup tool) to common.py and run_judge.py.
Purely additive: A, B, C and CS behave exactly as before. Run once from sqljudge/code."""
import sys

def patch(path, pairs):
    s = open(path, encoding="utf-8").read()
    if "simple_tools_for" in s or "_LOOKUP_ACCESS" in s:
        print(path, "already patched"); return
    for old, new in pairs:
        assert s.count(old) == 1, (path, old[:60], s.count(old))
        s = s.replace(old, new)
    open(path, "w", encoding="utf-8", newline="").write(s)
    print(path, "patched")

patch("common.py", [
("""_SCHEMA_GIVEN = "The database schema (tables and columns) is provided together with the claim."
""",
"""_SCHEMA_GIVEN = "The database schema (tables and columns) is provided together with the claim."
# condition S (simple path, pathway #3): Python lookup tool instead of SQL or a builder
_LOOKUP_ACCESS = ("You will have access to a SQLite database through two specialized tools: one lists the tables and "
                  "columns, the other looks up rows in one table using simple filters and can count, sum, average, or "
                  "take the minimum or maximum of a column. You do not need to write SQL.")
_LOOKUP_SCHEMA = "You should always start by listing the tables and columns."
"""),
("""    p = BASE_PROMPT
    if condition in ("C", "CS"):""",
"""    p = BASE_PROMPT
    if condition == "S":
        p = p.replace(_SQL_ACCESS, _LOOKUP_ACCESS).replace(_SCHEMA_LINE, _LOOKUP_SCHEMA)
    if condition in ("C", "CS"):"""),
])

patch("run_judge.py", [
("""  CS : NL2SQL builder, schema also given to the judge
""",
"""  CS : NL2SQL builder, schema also given to the judge
  S  : simple path (pathway #3), condition S: judge uses a Python lookup tool (simple_tools.py), no SQL, no builder
"""),
("""def make_tools(condition, claim, db_file, args, builder, log):
    db = claim["db_name"]
""",
"""def make_tools(condition, claim, db_file, args, builder, log):
    db = claim["db_name"]
    if condition == "S":
        return simple_tools_for(db, db_file, args, log)
"""),
("""async def judge_one(claim, args, model, builder):""",
"""def simple_tools_for(db, db_file, args, log):
    from typing import Literal, Optional
    from simple_tools import LookupEngine, Filter
    eng = LookupEngine(db_file, args.max_rows or 100, args.sql_timeout)

    def describe_tables(table: str = "") -> str:
        \"\"\"List the tables of the database with their columns.

        Args:
            table: optional table name; give it to see that table's columns with example values, leave empty to list all tables.
        \"\"\"
        try:
            out, err = eng.describe(table), None
        except Exception as e:
            out = err = str(e)
        log.append({"tool": "describe", "table": table, "error": err})
        return out

    def lookup(table: str, filters: Optional[list[Filter]] = None,
               aggregate: Literal["none", "count", "count_distinct", "sum", "avg", "min", "max"] = "none",
               column: str = "", columns: Optional[list[str]] = None, group_by: str = "", order_by: str = "",
               descending: bool = False, limit: int = 20) -> str:
        \"\"\"Look up rows in ONE table. All filters must hold (AND).

        Args:
            table: the table to look in.
            filters: conditions on columns of this table, e.g. [{"column": "height_cm", "op": ">", "value": 200}].
            aggregate: "none" returns rows; otherwise count / count_distinct / sum / avg / min / max of `column` over the matching rows ("count" without a column counts rows).
            column: the column to aggregate.
            columns: the columns to return when aggregate is "none" (default: all columns).
            group_by: optional column; returns one result per distinct value of it.
            order_by: a column, or "value" to sort by the aggregate result.
            descending: sort from largest to smallest.
            limit: maximum rows to return (at most 100).
        \"\"\"
        kw = dict(table=table, filters=filters, aggregate=aggregate, column=column, columns=columns,
                  group_by=group_by, order_by=order_by, descending=descending, limit=limit)
        text, info = eng.lookup(**kw)
        log.append({"tool": "lookup", "args": {k: (v if k != "filters" else [f if isinstance(f, dict) else f.model_dump() for f in (v or [])])
                                               for k, v in kw.items()}, **info})
        return text

    name = db.replace('_', ' ').title()
    return [Tool(describe_tables, takes_ctx=False, name=f"{db}_describe_tables",
                 description=f"Lists the tables and columns of the {name} database."),
            Tool(lookup, takes_ctx=False, name=f"{db}_lookup",
                 description=(f"Looks up rows in one table of the {name} database with simple filters, optionally "
                              "counting, summing, averaging or taking the minimum or maximum of a column. No SQL needed."))]

async def judge_one(claim, args, model, builder):"""),
("""    p.add_argument("--condition", required=True, choices=["A", "B", "C", "CS"])""",
 """    p.add_argument("--condition", required=True, choices=["A", "B", "C", "CS", "S"])"""),
])
