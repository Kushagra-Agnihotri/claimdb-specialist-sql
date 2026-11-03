r"""NL2SQL builder variations (Condition C: judge delegates SQL-writing to a specialist, no schema given
to the judge itself). Fixes the two judges already used in the midsem results (qwen3:8b, llama3.1:8b)
and sweeps the *builder* model, to see how much of Condition C's gain is specific to Arctic-Text2SQL-R1
versus any reasonably good text-to-SQL specialist.

Recalibrated alongside sweep_judges.py: the judge side now goes through sweep_lib's validate-before-run
+ retry-with-backoff, and both judges here default to local Ollama -- the only backend that actually
produced real judge behavior in your last batch of result files (the Groq/OpenRouter judge tags you
tried all 404'd; see sweep_judges.py's docstring for the full breakdown). If you move a judge to a
cloud provider, check its tag with check_providers.py first.

Builder notes:
  - Arctic-Text2SQL-R1-7B: the model used in the midsem report; served via Ollama (GGUF build) or
    vLLM/HF if you have one locally.
  - OmniSQL-7B: same prompt family (builder.py's "omnisql" template was written for this family),
    useful as a same-size, different-training-data comparison point.
  - FINER-SQL / SLM-SQL (smaller, e.g. 3B): tests whether a *smaller* specialist still rescues a
    small judge, or whether the judge needs a strong builder to see the Condition-C gain. These
    typically ship without a GGUF/Ollama build, hence backend="hf" + template="finer" below -- check
    the model card and adjust FINER_SYSTEM/FINER_USER in builder.py if its expected prompt differs.
    The builder itself is NOT run through providers.py/validate_model (it's a local HF/Ollama load,
    not a judge call through the cloud-provider registry) -- a bad builder tag will surface as a
    normal Python exception from Builder.__init__ the first time it's used, not a 404 you discover
    after 210 claims.

Usage:
  ollama pull a-kore/Arctic-Text2SQL-R1-7B        # or the GGUF mirror you used for the midsem report
  ollama pull <your-omnisql-7b-tag>                # if you have an Ollama/GGUF build
  python sweep_builders.py --claims subset_210.jsonl --db-root D:\bird\dev_databases

Then: python aggregate_results.py --glob "results/*__C__*.jsonl" --csv builder_sweep.csv
"""
import argparse
import asyncio

from sweep_lib import run_config

# (judge tag, provider, pace_seconds, suggest_keyword) -- same shape as sweep_judges.py's JUDGES
JUDGES = [
    ("qwen3:8b", "ollama", 0.0, "qwen"),
    ("llama3.1:8b", "ollama", 0.0, "llama"),
]

# (builder tag, backend, template) -- comment out rows for models you haven't pulled/downloaded yet;
# Builder (builder.py) raises a clear error for a missing Ollama tag or HF id rather than hang.
BUILDERS = [
    ("a-kore/Arctic-Text2SQL-R1-7B", "openai", "omnisql"),   # midsem-report builder, as reference point
    ("omnisql-7b",                   "openai", "omnisql"),   # same prompt family, different training data
    ("griffith-bigdata/FINER-SQL-3B-BIRD", "hf", "finer"),   # smaller specialist, HF backend (no GGUF)
]


async def main(a):
    skipped = []
    for judge, provider, pace, kw in JUDGES:
        for tag, backend, template in BUILDERS:
            try:
                await run_config(
                    a.claims, a.db_root, judge, "C",
                    builder_tag=tag, builder_backend=backend, builder_template=template,
                    builder_url=a.builder_url,
                    provider=provider, max_calls=a.max_calls, max_rows=a.max_rows, sql_timeout=a.sql_timeout,
                    max_retries=a.max_retries, pace_seconds=pace, validate=not a.no_validate,
                    suggest_keyword=kw,
                )
            except Exception as e:
                print(f"\n[SKIPPING judge={judge} builder={tag}] {e}\n")
                skipped.append((judge, tag, str(e)))
    if skipped:
        print(f"\n=== {len(skipped)} (judge, builder) pair(s) skipped this run ===")
        for judge, tag, err in skipped:
            print(f"  judge={judge} builder={tag}: {err.splitlines()[0]}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--claims", required=True)
    p.add_argument("--db-root", required=True)
    p.add_argument("--builder-url", default="http://localhost:11434/v1",
                    help="OpenAI-compatible server for 'openai'-backend builders (Ollama/vLLM); ignored for 'hf' builders")
    p.add_argument("--max-calls", type=int, default=20)
    p.add_argument("--max-rows", type=int, default=100)
    p.add_argument("--sql-timeout", type=int, default=30)
    p.add_argument("--max-retries", type=int, default=5)
    p.add_argument("--no-validate", action="store_true")
    a = p.parse_args()
    asyncio.run(main(a))
