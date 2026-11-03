r"""Arctic-Text2SQL-R1-7B as judge, two ways -- the "new baseline" from the mentor meeting notes.

(1) Condition A and B: Arctic plays the judge role directly, writing and executing its own SQL just
    like any other model in sweep_judges.py. This tells us how good a pure text-to-SQL specialist is
    at the *agentic fact-checking loop* (deciding what to query, reading results, picking a verdict) --
    a skill it was never trained for -- as opposed to SQL-writing in isolation (which eval_builder.py
    already measures against BIRD gold SQL).

(2) Condition C, self-delegation: Arctic is *both* judge and builder -- it asks itself natural-language
    questions and answers them with SQL via the same ask_database tool other judges use in Condition C.
    Comparing this to the main Condition-C results (Qwen3-8B/Llama3.1-8B judge + Arctic builder) isolates
    whether Condition C's gain comes from having a *separate* specialist model, or just from the judge no
    longer having to write SQL itself.

Recalibrated alongside sweep_judges.py: Arctic-as-judge now runs through the same validate-before-run +
retry-with-backoff path (sweep_lib.run_config). Defaults to Ollama, since that's the only backend proven
to actually work in your last batch of result files -- flip `PROVIDER` below only after confirming the
tag with check_providers.py.

Usage:
  ollama pull a-kore/Arctic-Text2SQL-R1-7B
  python sweep_arctic.py --claims subset_210.jsonl --db-root D:\bird\dev_databases

Then compare against the Qwen3-8B/Llama3.1-8B Condition-C rows:
  python aggregate_results.py --glob "results/*Arctic*.jsonl"
"""
import argparse
import asyncio

from sweep_lib import run_config

ARCTIC = "a-kore/Arctic-Text2SQL-R1-7B"
PROVIDER = "ollama"   # flip to "groq"/"openrouter" only with a tag confirmed via check_providers.py


async def main(a):
    # (1) Arctic as judge, writes its own SQL -- Condition A (no schema) and B (schema given, since
    #     Arctic was trained to expect the schema up front rather than fetch it with a tool).
    for condition in ("A", "B"):
        try:
            await run_config(a.claims, a.db_root, ARCTIC, condition, provider=PROVIDER,
                              max_calls=a.max_calls, max_rows=a.max_rows, sql_timeout=a.sql_timeout,
                              max_retries=a.max_retries, pace_seconds=a.pace_seconds,
                              validate=not a.no_validate, suggest_keyword="arctic")
        except Exception as e:
            print(f"\n[SKIPPING Arctic condition {condition}] {e}\n")

    # (2) Arctic as judge AND builder -- Condition C, self-delegation.
    try:
        await run_config(a.claims, a.db_root, ARCTIC, "C", builder_tag=ARCTIC,
                          builder_backend=a.builder_backend, builder_template="omnisql", builder_url=a.builder_url,
                          provider=PROVIDER, max_calls=a.max_calls, max_rows=a.max_rows, sql_timeout=a.sql_timeout,
                          max_retries=a.max_retries, pace_seconds=a.pace_seconds,
                          validate=not a.no_validate, suggest_keyword="arctic")
    except Exception as e:
        print(f"\n[SKIPPING Arctic self-delegation (condition C)] {e}\n")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--claims", required=True)
    p.add_argument("--db-root", required=True)
    p.add_argument("--builder-backend", default="openai", choices=["openai", "hf"])
    p.add_argument("--builder-url", default="http://localhost:11434/v1")
    p.add_argument("--max-calls", type=int, default=20)
    p.add_argument("--max-rows", type=int, default=100)
    p.add_argument("--sql-timeout", type=int, default=30)
    p.add_argument("--max-retries", type=int, default=5)
    p.add_argument("--pace-seconds", type=float, default=0.0, help="delay before each request; raise this if PROVIDER is a rate-limited cloud API")
    p.add_argument("--no-validate", action="store_true")
    a = p.parse_args()
    asyncio.run(main(a))
