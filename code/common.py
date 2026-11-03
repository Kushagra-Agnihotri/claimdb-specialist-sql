"""Shared pieces: data loading, schema extraction, safe SQL execution, and the ClaimDB prompt.

The judge prompt, output schema and input format are copied verbatim from ClaimDB
(claimdb/experiments.py, github.com/claimdb/claimdb) so that Condition A reproduces their setup.
"""
import json, sqlite3, time
from pathlib import Path
from typing import Literal
from pydantic import BaseModel, Field

# ----------------------------------------------------------------------------- ClaimDB prompt (verbatim)
class ClaimVerdict(BaseModel):
    verdict: Literal["ENTAILED", "CONTRADICTED", "NOT ENOUGH INFO"] = Field(
        ..., description="Whether the claim is supported, contradicted, or undecidable from the database.")
    justification: str = Field(..., description="Brief justification (1-2 sentences) of the verdict.")

_SQL_ACCESS = ("You will have access to a SQLite database and may execute arbitrary SQL queries over it "
               "using specialized tools.")
_SCHEMA_LINE = "You should always start by querying the database for the schema (tables and columns)."

BASE_PROMPT = f"""
You are a fact-checking assistant operating over structured data. You will be given a natural-language claim and optional external information. {_SQL_ACCESS}

Your task is to determine whether the claim is "ENTAILED", "CONTRADICTED", or "NOT ENOUGH INFO" based on evidence you obtain from the database. The labels are defined as follows:

- ENTAILED: The claim is supported by the database.
- CONTRADICTED: The claim is refuted by the database.
- NOT ENOUGH INFO: The database does not provide sufficient evidence to decide.

Use the available tools to query the database and gather evidence before making a decision. Do not ask the user for clarification or additional information.

{_SCHEMA_LINE}
"""

_OUTPUT_FMT = f"""
Your answer should be in JSON format, adhering to the following schema:
{json.dumps(ClaimVerdict.model_json_schema(), indent=2)}
"""
EX1 = """
Output Example 1:
{
    "verdict": "ENTAILED",
    "justification": "The database shows that the population of France is 67 million, which supports the claim."
}
"""
EX2 = """
Output Example 2:
{
    "verdict": "CONTRADICTED",
    "justification": "The database indicates that the capital of Germany is Berlin, contradicting the claim."
}
"""
EX3 = """
Output Example 3:
{
    "verdict": "NOT ENOUGH INFO",
    "justification": "The database does not contain any information about the population of Sacramento."
}
"""

# Minimal, explicit edits per condition. Everything else stays identical to ClaimDB.
_BUILDER_ACCESS = ("You will have access to a SQLite database through a specialized tool: you ask a question in "
                   "natural language, an NL-to-SQL model writes and executes a SQL query for it, and you receive "
                   "the SQL query and its result.")
_SCHEMA_GIVEN = "The database schema (tables and columns) is provided together with the claim."

def judge_prompt(condition: str) -> str:
    """A: ClaimDB exact. B: schema given. C: NL2SQL builder, no schema. CS: builder + schema given."""
    p = BASE_PROMPT
    if condition in ("C", "CS"):
        p = p.replace(_SQL_ACCESS, _BUILDER_ACCESS)
    if condition in ("B", "CS"):
        p = p.replace(_SCHEMA_LINE, _SCHEMA_GIVEN)
    elif condition == "C":
        p = p.replace(_SCHEMA_LINE, "")
    return p + _OUTPUT_FMT + "\n" + EX1 + EX2 + EX3

def judge_input(claim: dict, schema_ddl: str | None) -> str:
    base = f"Claim: {claim['claim']}\nExtra Information: {claim['extra_info']}"   # ClaimDB format
    return base if schema_ddl is None else f"Database schema:\n{schema_ddl}\n\n{base}"

# ----------------------------------------------------------------------------- data
def load_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]

def db_path(db_root: Path, db_name: str) -> Path:
    """BIRD layout: <db_root>/<db_name>/<db_name>.sqlite"""
    p = Path(db_root) / db_name / f"{db_name}.sqlite"
    if not p.exists():
        raise FileNotFoundError(f"Database not found: {p}")
    return p

_SCHEMA_CACHE: dict = {}
def schema_ddl(db_file: Path) -> str:
    """CREATE TABLE statements straight from sqlite_master (what NL2SQL models expect)."""
    key = str(db_file)
    if key not in _SCHEMA_CACHE:
        con = sqlite3.connect(f"file:{db_file}?mode=ro", uri=True)
        rows = con.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' AND sql IS NOT NULL").fetchall()
        con.close()
        _SCHEMA_CACHE[key] = "\n\n".join(r[0].strip() + ";" for r in rows)
    return _SCHEMA_CACHE[key]

# ----------------------------------------------------------------------------- SQL execution
def execute_sql(db_file: Path, query: str, timeout: int = 30, max_rows: int | None = 100):
    """Read-only execution with a timeout (same idea as ClaimDB's sqlite_execute_with_timeout).
    Returns (rows, error_string). Errors mimic the MCP Toolbox wording the ClaimDB agents saw."""
    start = time.time()
    con = sqlite3.connect(f"file:{db_file}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    con.set_progress_handler(lambda: 1 if time.time() - start > timeout else 0, 1000)
    try:
        cur = con.execute(query)
        rows = cur.fetchmany(max_rows + 1) if max_rows else cur.fetchall()
        rows = [dict(r) for r in rows]
        return rows, None
    except sqlite3.OperationalError as e:
        msg = "query timed out" if "interrupted" in str(e) else str(e)
        return None, f"error while invoking tool: unable to execute query: SQL logic error: {msg}" + ("" if msg == "query timed out" else f" ({getattr(e, 'sqlite_errorcode', 1)})")
    except Exception as e:  # noqa
        return None, f"error while invoking tool: unable to execute query: {e}"
    finally:
        con.set_progress_handler(None, 0); con.close()

def rows_to_text(rows, max_rows: int | None) -> str:
    if max_rows and len(rows) > max_rows:
        return json.dumps(rows[:max_rows], default=str, separators=(',', ':')) + f"\n[Output truncated: showing the first {max_rows} rows only. Use aggregation or LIMIT.]"
    return json.dumps(rows, default=str, separators=(',', ':'))

def safe_name(s: str) -> str:
    """Windows-safe file names (model tags contain ':' and '/')."""
    return "".join(c if c.isalnum() or c in "-_." else "_" for c in s)
