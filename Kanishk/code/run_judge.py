"""Run a small judge on ClaimDB claims under one condition.

  A  : ClaimDB exact (judge writes SQL, no schema given)
  B  : judge writes SQL, schema given with the claim
  C  : judge asks an NL2SQL builder in natural language, no schema given
  CS : NL2SQL builder, schema also given to the judge
  S  : simple path (pathway #3), condition S: judge uses a Python lookup tool (simple_tools.py), no SQL, no builder

Example (Windows PowerShell, Ollama running):
  python run_judge.py --claims ..\\data\\subset_150.jsonl --db-root D:\\bird\\dev_databases --model qwen3:8b --condition A
  python run_judge.py ... --condition C --builder hf.co/mradermacher/Arctic-Text2SQL-R1-7B-GGUF:Q4_K_M
"""
import argparse, asyncio, json, time
from pathlib import Path
from pydantic_ai import Agent, Tool, UsageLimits
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.ollama import OllamaProvider
from pydantic_ai.providers.openai import OpenAIProvider
from common import (ClaimVerdict, judge_prompt, judge_input, load_jsonl, db_path, schema_ddl, schema_ddl_with_values,
                    execute_sql, rows_to_text, safe_name, load_results_repair)

def make_tools(condition, claim, db_file, args, builder, log):
    db = claim["db_name"]
    if condition == "S":
        return simple_tools_for(db, db_file, args, log)
    if condition in ("A", "B"):
        def run_sql(sql_query: str) -> str:
            rows, err = execute_sql(db_file, sql_query, args.sql_timeout, args.max_rows)
            log.append({"tool": "sql", "sql": sql_query, "error": err, "n_rows": None if rows is None else min(len(rows), args.max_rows or len(rows)),
                        "truncated": bool(rows) and bool(args.max_rows) and len(rows) > args.max_rows})
            return err if err else rows_to_text(rows, args.max_rows)
        return [Tool(run_sql, takes_ctx=False, name=f"{db}_execute_sql",
                     description=f"Executes SQL queries on the SQLite {db.replace('_', ' ').title()} database. The queries must be SQLite-compatible.")]
    def ask_database(question: str) -> str:
        t = time.time()
        try:
            nvals = getattr(args, 'builder_values', 0)
            builder_schema = schema_ddl_with_values(db_file, nvals) if nvals else schema_ddl(db_file)
            sql, raw = builder.sql_for(builder_schema, question, claim.get("extra_info", ""))
        except Exception as e:  # builder server problems should not kill the run
            log.append({"tool": "builder", "question": question, "error": f"builder failure: {e}"})
            return f"error: the NL-to-SQL tool failed: {e}"
        rows, err = execute_sql(db_file, sql, args.sql_timeout, args.max_rows) if sql else (None, "error: the NL-to-SQL tool returned no SQL")
        log.append({"tool": "builder", "question": question, "sql": sql, "error": err,
                    "n_rows": None if rows is None else min(len(rows), args.max_rows or len(rows)), "builder_seconds": round(time.time() - t, 2),
                    "builder_raw": raw[-4000:]})
        return json.dumps({"sql": sql, "result": err if err else rows_to_text(rows, args.max_rows)})
    return [Tool(ask_database, takes_ctx=False, name=f"{db}_ask_database",
                 description=(f"Ask a question in natural language about the '{db}' database. An NL-to-SQL model "
                              "writes a SQLite query for it and executes it. Returns the SQL query and its result."))]

def simple_tools_for(db, db_file, args, log):
    from typing import Literal, Optional
    from simple_tools import LookupEngine, Filter
    eng = LookupEngine(db_file, args.max_rows or 100, args.sql_timeout)

    def describe_tables(table: str = "") -> str:
        """List the tables of the database with their columns.

        Args:
            table: optional table name; give it to see that table's columns with example values, leave empty to list all tables.
        """
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
        """Look up rows in ONE table. All filters must hold (AND).

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
        """
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

async def judge_one(claim, args, model, builder):
    db_file = db_path(args.db_root, claim["db_name"])
    schema = schema_ddl(db_file) if args.condition in ("B", "CS") else None
    log = []
    agent = Agent(model, name="Fact-Checker", instructions=judge_prompt(args.condition), output_type=ClaimVerdict,
                  output_retries=20, tools=make_tools(args.condition, claim, db_file, args, builder, log))
    t = time.time()
    try:
        res = await agent.run(judge_input(claim, schema), usage_limits=UsageLimits(tool_calls_limit=args.max_calls))
        out = {"verdict": res.output.verdict, "justification": res.output.justification, "error": None,
               "all_messages": json.loads(res.all_messages_json().decode())}
    except Exception as e:   # same convention as ClaimDB: a failed run has an empty verdict and counts as wrong
        out = {"verdict": "", "justification": "", "error": f"{type(e).__name__}: {e}", "all_messages": []}
    return {"claim_id": claim["claim_id"], "label": claim["label"], "db_name": claim["db_name"],
            "condition": args.condition, "model": args.model, "builder": args.builder,
            "seconds": round(time.time() - t, 1), "tool_log": log, **out}

async def main(args):
    claims = load_jsonl(args.claims)
    out = Path(args.out or Path(__file__).resolve().parent.parent / "results" / f"{safe_name(args.model)}__{args.condition}"
               f"{'__' + safe_name(args.builder) if args.builder else ''}"
               f"{f'__vals{args.builder_values}' if args.builder_values else ''}.jsonl")
    out.parent.mkdir(parents=True, exist_ok=True)
    done = {r["claim_id"] for r in load_results_repair(out)}
    todo = [c for c in claims if c["claim_id"] not in done]
    provider = (OllamaProvider(base_url=args.base_url) if args.provider == "ollama"
                else OpenAIProvider(base_url=args.base_url, api_key=args.api_key))
    model = OpenAIChatModel(model_name=args.model, provider=provider)
    builder = None
    if args.condition in ("C", "CS"):
        if not args.builder:
            raise SystemExit("--builder is required for conditions C and CS")
        from builder import Builder
        builder = Builder(args.builder, backend=args.builder_backend, template=args.builder_template,
                          base_url=args.builder_url)
    print(f"{args.model} | condition {args.condition} | builder {args.builder} | {len(todo)} of {len(claims)} claims left -> {out}")
    meta = {"max_calls": args.max_calls, "max_rows": args.max_rows, "sql_timeout": args.sql_timeout,
            "builder_backend": args.builder_backend, "builder_template": args.builder_template,
            "builder_values": args.builder_values}
    for i, c in enumerate(todo, 1):
        r = await judge_one(c, args, model, builder)
        r["config"] = meta
        with open(out, "a", encoding="utf-8") as f:
            f.write(json.dumps(r, default=str) + "\n")
        ok = "OK " if r["verdict"] == c["label"] else "-- "
        print(f"[{i}/{len(todo)}] {ok}{c['claim_id']} gold={c['label']} pred={r['verdict'] or 'FAILED'} "
              f"calls={len(r['tool_log'])} {r['seconds']}s")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--claims", required=True); p.add_argument("--db-root", required=True, type=Path)
    p.add_argument("--model", required=True, help="judge model tag, e.g. qwen3:8b")
    p.add_argument("--condition", required=True, choices=["A", "B", "C", "CS", "S"])
    p.add_argument("--builder", default=None, help="builder model (Ollama tag or HF id)")
    p.add_argument("--builder-backend", default="openai", choices=["openai", "hf"])
    p.add_argument("--builder-template", default="omnisql", choices=["omnisql", "finer"])
    p.add_argument("--builder-url", default="http://localhost:11434/v1")
    p.add_argument("--builder-values", type=int, default=0,
                   help="0 = builder sees the plain schema (main C). N>0 = builder schema also shows N example values per column")
    p.add_argument("--provider", default="ollama", choices=["ollama", "openai"])
    p.add_argument("--base-url", default="http://localhost:11434/v1"); p.add_argument("--api-key", default="none")
    p.add_argument("--max-calls", type=int, default=20, help="ClaimDB used 20")
    p.add_argument("--max-rows", type=int, default=100, help="rows returned per query (0 = no cap)")
    p.add_argument("--sql-timeout", type=int, default=30)
    p.add_argument("--out", default=None)
    a = p.parse_args(); a.max_rows = a.max_rows or None
    asyncio.run(main(a))
