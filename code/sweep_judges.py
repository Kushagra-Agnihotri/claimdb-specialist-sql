r"""Table 2: open-source judge comparison under Condition A (ClaimDB exact setup, no schema, judge
writes its own SQL). Fixes the condition and claim subset and varies only the judge model: 3 Qwen,
2 Mistral, 2 LLaMA.

RECALIBRATED after your first attempt (5 result files back): 4 of them were dead or crippled --
  - llama-3.1-8b-instant @ Groq        -> 404 on all 210 claims (Groq retired that exact tag)
  - qwen3-8b @ Groq                    -> 404 on all 210 claims (never existed under that tag on Groq)
  - qwen/qwen3-8b:free @ OpenRouter    -> 404 on all 210 claims ("deprecated... migrate to qwen3.7-plus")
  - qwen/qwen3.8-27b @ Groq            -> ran, but mostly hit Groq's free-tier ITPM=7000/TPD=200000 caps
Only qwen3:8b on local Ollama (113/210, still running when you grabbed the file) actually produced real
judge behavior.

So this sweep now defaults every one of the 7 judges to Ollama -- the one backend proven to work -- and
leaves clearly marked per-model override slots for Groq/OpenRouter. Three things changed to make
switching a model to a cloud provider safe instead of a repeat of the above:

  1. Each entry validates its tag against the provider's LIVE /models list before spending any claims
     on it (sweep_lib.run_config -> providers.validate_model). A dead tag now fails in under a second
     with a list of close matches, instead of producing 210 identical 404s.
  2. One model's failure (dead tag, exhausted quota, whatever) no longer kills the whole sweep -- it's
     caught per-model, printed, and the script moves on to the next judge.
  3. Rate limits (429) and oversized requests (413) are retried with backoff / a shrunk max_rows
     automatically (sweep_lib.judge_with_retry) instead of being written to the file as permanent wrong
     answers. `pace_seconds` below adds a deliberate gap between requests for cloud models to stay under
     free-tier per-minute caps in the first place, rather than only reacting after a 429.

Before flipping any model's provider to "groq"/"openrouter": run check_providers.py first and copy a
REAL, currently-live tag -- don't hand-guess one, that's how 3 of the 4 dead runs happened.

  export GROQ_API_KEY=...            # if you use any groq entries below
  export OPENROUTER_API_KEY=...      # if you use any openrouter entries below
  python check_providers.py --provider groq --keyword qwen
  python check_providers.py --provider groq --keyword llama
  python check_providers.py --provider groq --keyword mistral

  python sweep_judges.py --claims subset_210.jsonl --db-root D:\bird\dev_databases
  python sweep_judges.py --claims subset_210.jsonl --db-root D:\bird\dev_databases --condition B

Resumable: re-running after a crash, a fixed tag, or Ctrl-C only retries claims that didn't already
succeed (sweep_lib._load_last_rows) -- it will NOT re-spend a correctly-answered claim.
Then: python aggregate_results.py --glob "results/*__A.jsonl" --csv table2.csv
"""
import argparse
import asyncio

from sweep_lib import run_config

# Each entry: (model_tag, provider, pace_seconds, suggest_keyword)
#   provider      - "ollama" (local, free, slow, proven working) | "groq" | "openrouter"
#   pace_seconds  - deliberate delay before each request; 0 for local Ollama (no limit to respect),
#                   a few seconds for cloud free tiers so you approach the ITPM/RPM cap instead of
#                   slamming into it and relying purely on retries
#   suggest_keyword - used to rank close-match suggestions if the tag turns out not to exist any more
#
# All default to Ollama. Pull each one first (`ollama pull <tag>`) or flip its provider to "groq"/
# "openrouter" with a tag you confirmed via check_providers.py.
JUDGES = [
    ("qwen3:4b",         "ollama", 0.0, "qwen"),      # Qwen, small
    ("qwen3:8b",         "ollama", 0.0, "qwen"),      # Qwen, matches the midsem-report headline model
    ("qwen3:14b",        "ollama", 0.0, "qwen"),      # Qwen, large
    ("mistral-nemo:12b", "ollama", 0.0, "mistral"),   # Mistral #1
    ("mistral:7b",       "ollama", 0.0, "mistral"),   # Mistral #2
    ("llama3.2:3b",      "ollama", 0.0, "llama"),     # LLaMA #1, small
    ("llama3.1:8b",      "ollama", 0.0, "llama"),     # LLaMA #2
]


async def main(a):
    skipped = []
    for model, provider, pace, kw in JUDGES:
        try:
            await run_config(
                a.claims, a.db_root, model, a.condition,
                provider=provider, base_url=a.base_url if provider == "ollama" and a.base_url else None,
                max_calls=a.max_calls, max_rows=a.max_rows, sql_timeout=a.sql_timeout,
                max_retries=a.max_retries, pace_seconds=pace, validate=not a.no_validate,
                suggest_keyword=kw,
            )
        except Exception as e:
            # One bad model (dead tag, exhausted quota, missing API key) must not take the rest of the
            # sweep down with it -- that's the failure mode that produced 4 near-empty result files.
            print(f"\n[SKIPPING {model} on {provider}] {e}\n")
            skipped.append((model, provider, str(e)))
    if skipped:
        print(f"\n=== {len(skipped)} model(s) skipped this run ===")
        for model, provider, err in skipped:
            print(f"  {model} ({provider}): {err.splitlines()[0]}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--claims", required=True)
    p.add_argument("--db-root", required=True)
    p.add_argument("--condition", default="A", choices=["A", "B"],
                    help="A = ClaimDB exact (default); B = schema given. C/CS need a builder, use sweep_builders.py instead.")
    p.add_argument("--base-url", default=None, help="override Ollama's base_url (ignored for groq/openrouter entries)")
    p.add_argument("--max-calls", type=int, default=20)
    p.add_argument("--max-rows", type=int, default=100)
    p.add_argument("--sql-timeout", type=int, default=30)
    p.add_argument("--max-retries", type=int, default=5, help="per-claim retries on rate-limit/transient errors")
    p.add_argument("--no-validate", action="store_true", help="skip the live /models pre-check (not recommended)")
    a = p.parse_args()
    asyncio.run(main(a))
