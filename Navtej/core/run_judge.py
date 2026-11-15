"""Run a small judge on ClaimDB claims under one condition.

  A  : ClaimDB exact (judge writes SQL, no schema given)
  B  : judge writes SQL, schema given with the claim
  C  : judge asks an NL2SQL builder in natural language, no schema given
  CS : NL2SQL builder, schema also given to the judge

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
from common import (ClaimVerdict, judge_prompt, judge_input, load_jsonl, db_path, schema_ddl,
                    execute_sql, rows_to_text, safe_name)

def make_tools(condition, claim, db_file, args, builder, log):
    db = claim["db_name"]
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
            sql, raw = builder.sql_for(schema_ddl(db_file), question, claim.get("extra_info", ""))
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
    out = Path(args.out or f"results/{safe_name(args.model)}__{args.condition}"
               f"{'__' + safe_name(args.builder) if args.builder else ''}.jsonl")
    out.parent.mkdir(parents=True, exist_ok=True)
    done = {json.loads(l)["claim_id"] for l in open(out, encoding="utf-8")} if out.exists() else set()
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
            "builder_backend": args.builder_backend, "builder_template": args.builder_template}
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
    p.add_argument("--condition", required=True, choices=["A", "B", "C", "CS"])
    p.add_argument("--builder", default=None, help="builder model (Ollama tag or HF id)")
    p.add_argument("--builder-backend", default="openai", choices=["openai", "hf"])
    p.add_argument("--builder-template", default="omnisql", choices=["omnisql", "finer"])
    p.add_argument("--builder-url", default="http://localhost:11434/v1")
    p.add_argument("--provider", default="ollama", choices=["ollama", "openai"])
    p.add_argument("--base-url", default="http://localhost:11434/v1"); p.add_argument("--api-key", default="none")
    p.add_argument("--max-calls", type=int, default=20, help="ClaimDB used 20")
    p.add_argument("--max-rows", type=int, default=100, help="rows returned per query (0 = no cap)")
    p.add_argument("--sql-timeout", type=int, default=30)
    p.add_argument("--out", default=None)
    a = p.parse_args(); a.max_rows = a.max_rows or None
    asyncio.run(main(a))
