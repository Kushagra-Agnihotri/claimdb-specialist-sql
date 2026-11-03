"""Look up what a provider is ACTUALLY serving right now, before putting a tag into sweep_judges.py /
sweep_builders.py. This is the fix for how three of your five result files happened: a guessed or
half-remembered tag ("llama-3.1-8b-instant", "qwen3-8b", "qwen/qwen3-8b:free") that 404'd on every
single one of 210 claims. Querying the provider's own /models endpoint takes under a second and tells
you definitively whether a tag exists right now -- model catalogs on Groq/OpenRouter change often
enough that any hardcoded list (including one I'd write into a script) can go stale within weeks.

Usage:
  export GROQ_API_KEY=...
  export OPENROUTER_API_KEY=...
  python check_providers.py --provider groq
  python check_providers.py --provider openrouter --keyword qwen
  python check_providers.py --provider ollama                     # local, no key needed
  python check_providers.py --provider groq --keyword llama
  python check_providers.py --all --keyword mistral                # check every provider at once
"""
import argparse
from providers import PROVIDERS, list_live_models


def show(provider: str, keyword: str | None):
    print(f"\n=== {provider} ===")
    try:
        models = list_live_models(provider)
    except Exception as e:
        print(f"  could not list models: {e}")
        return
    if keyword:
        models = [m for m in models if keyword.lower() in m.lower()]
    if not models:
        print(f"  (no models{' matching ' + repr(keyword) if keyword else ''})")
        return
    for m in models:
        print(f"  {m}")
    print(f"  -- {len(models)} model(s)")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--provider", choices=list(PROVIDERS), help="which provider to query")
    p.add_argument("--all", action="store_true", help="query every provider in providers.py")
    p.add_argument("--keyword", default=None, help="filter to tags containing this substring, e.g. qwen/llama/mistral")
    a = p.parse_args()
    if not a.provider and not a.all:
        raise SystemExit("pass --provider <name> or --all")
    for name in (PROVIDERS if a.all else [a.provider]):
        show(name, a.keyword)
