"""Shared driver logic for running a judge over a claim set under one (model, condition, builder) config.

Factored out of run_judge.py's CLI so the multi-config sweeps (sweep_judges.py, sweep_builders.py,
sweep_arctic.py) reuse the exact same agent loop and output format as a single run_judge.py invocation.

Recalibrated after the first cloud-API attempt (5 result files, 4 of them effectively dead):
  - llama-3.1-8b-instant @ Groq        -> 404 "does not exist" on every one of 210 claims
  - qwen3-8b @ Groq                    -> 404 "does not exist" on every one of 210 claims
  - qwen/qwen3-8b:free @ OpenRouter    -> 404 "deprecated" on every one of 210 claims
  - qwen/qwen3.8-27b @ Groq            -> ran, but burned most of its budget on 413/429s from Groq's
                                           free-tier ITPM=7000 / TPD=200000 caps
That produced two concrete bugs this file now fixes:

1. RESUMABILITY WAS WRONG FOR FAILURES. The original "done" set was every claim_id already written to
   the output file, success or not -- so a claim that 404'd on attempt 1 was permanently marked done and
   would be silently skipped on every later re-run, forever recording "wrong answer" for a claim the
   model never actually got to see. `_load_last_rows` now keeps only each claim_id's LATEST row (dict
   overwrite, oldest-to-newest, same convention score.py's load() already uses) and a claim only counts
   as done if that latest row succeeded (non-empty verdict, no error). Re-running after fixing a tag, or
   after a transient failure, now actually retries exactly the claims that need it.

2. NO RETRY AT ALL. A 429 (rate limit) or a transient 5xx was being written to the output file as a
   final, scored answer. judge_with_retry() below classifies the error judge_one() already caught
   (run_judge.py swallows exceptions into a per-claim "error" string rather than raising) and reacts
   per class:
     - "dead_model"  (404 "does not exist" / "deprecated") -> raise immediately, no retry. Retrying a
       tag that doesn't exist just burns through the whole claim set producing 210 identical errors --
       exactly what happened. This surfaces the problem after 1 claim instead of 210.
     - "rate_limit"  (429)    -> parse Groq's own "try again in Xm12s" hint from the error text and
       sleep that long (+2s buffer) before retrying, falling back to a fixed wait if no hint is present.
     - "too_large"   (413)    -> halve max_rows (floor 10) for the rest of this run and retry; this is
       the one closest to Groq's free-tier ITPM cap, where the running tool-call transcript itself grows
       past the per-minute input-token budget.
     - anything else that looks transient (timeouts, connection errors, 5xx) -> capped exponential backoff.
   Retries are capped (max_retries) so a truly broken endpoint still fails fast rather than hanging the
   whole sweep.

Also: run_config can now validate a (provider, model_tag) pair against the provider's live /models
endpoint (providers.py) BEFORE spending a single claim on it -- the single change that would have turned
each of the three dead-tag files into a one-line error instead of 210 rows of identical 404s.
"""
import asyncio as _asyncio
import json
import re
import types
from pathlib import Path

from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.ollama import OllamaProvider
from pydantic_ai.providers.openai import OpenAIProvider

from common import load_jsonl, safe_name
from run_judge import judge_one

# ----------------------------------------------------------------------------------------- error triage
_WAIT_RE = re.compile(r"try again in\s+(?:(\d+)m)?(\d+(?:\.\d+)?)s", re.I)


def classify_error(err: str | None) -> str | None:
    """None = no error (success). Otherwise one of: dead_model, rate_limit, too_large, transient, other."""
    if not err:
        return None
    low = err.lower()
    if ("model_not_found" in low or "does not exist or you do not have access" in low
            or "was deprecated" in low or "model_decommissioned" in low):
        return "dead_model"
    # Check "too_large" before "rate_limit": Groq reuses the SAME code ('rate_limit_exceeded') for both
    # its 413 "request too large" (per-request token cap) and its 429 "rate limit reached" (per-minute/
    # per-day cap) errors, so the more specific status-code/wording match must win, or every 413 in your
    # last batch of result files would have been (mis-)retried as a plain rate limit instead of having
    # max_rows shrunk.
    if "status_code: 413" in low or "request too large" in low or "reduce your message size" in low:
        return "too_large"
    if "rate_limit_exceeded" in low or "status_code: 429" in low:
        return "rate_limit"
    if "status_code: 5" in low or "timeout" in low or "connection" in low or "temporarily unavailable" in low:
        return "transient"
    return "other"


def parse_wait_seconds(err: str, default: float = 30.0, cap: float = 900.0) -> float:
    """Pulls Groq's own "Please try again in 8m15.5s" out of the error text; falls back to `default`."""
    m = _WAIT_RE.search(err or "")
    if not m:
        return default
    minutes = float(m.group(1) or 0)
    seconds = float(m.group(2) or 0)
    return min(minutes * 60 + seconds + 2, cap)   # +2s buffer past what the provider asked for


def _is_success(row: dict) -> bool:
    return bool(row.get("verdict")) and not row.get("error")


def _load_last_rows(out: Path) -> dict:
    """claim_id -> most recent row written for it. A file can contain the same claim_id more than once
    across separate run_config invocations (a failed attempt, then a later successful retry); the later
    line always wins, same convention as score.py's load()."""
    last = {}
    if out.exists():
        for line in open(out, encoding="utf-8"):
            if line.strip():
                row = json.loads(line)
                last[row["claim_id"]] = row
    return last


async def judge_with_retry(claim, args, model, builder, max_retries: int, pace_seconds: float, tag: str):
    """Runs judge_one with retry/backoff based on classify_error(). Mutates args.max_rows in place on a
    'too_large' hit (persists for the rest of this run -- there's no point growing it back)."""
    attempt = 0
    while True:
        if pace_seconds:
            await _asyncio.sleep(pace_seconds)
        r = await judge_one(claim, args, model, builder)
        kind = classify_error(r.get("error"))
        if kind is None:
            return r
        if kind == "dead_model":
            raise RuntimeError(
                f"[{tag}] model tag rejected by the API: {r['error']}\n"
                "This is a dead/renamed/deprecated tag, not a transient failure -- retrying would just "
                "repeat this 404 for every remaining claim (which is exactly what happened before). Fix "
                "the tag -- run check_providers.py against this provider to see what it serves right "
                "now -- then re-run; already-completed claims for OTHER models are untouched.")
        if attempt >= max_retries:
            print(f"    [{tag}] [give up] {claim['claim_id']} after {attempt} retries: {r['error'][:200]}")
            return r
        attempt += 1
        if kind == "rate_limit":
            wait = parse_wait_seconds(r["error"])
            print(f"    [{tag}] [retry {attempt}/{max_retries}] rate limited on {claim['claim_id']}, "
                  f"waiting {wait:.0f}s")
            await _asyncio.sleep(wait)
        elif kind == "too_large":
            args.max_rows = max(10, (args.max_rows or 100) // 2)
            print(f"    [{tag}] [retry {attempt}/{max_retries}] request too large on {claim['claim_id']}, "
                  f"shrinking max_rows to {args.max_rows} and retrying")
        else:  # transient / other
            wait = min(5 * 2 ** attempt, 60)
            print(f"    [{tag}] [retry {attempt}/{max_retries}] {kind} error on {claim['claim_id']}, "
                  f"waiting {wait}s")
            await _asyncio.sleep(wait)


# --------------------------------------------------------------------------------------------- driver
async def run_config(claims_path, db_root, model_tag, condition, builder_tag=None,
                      builder_backend="openai", builder_template="omnisql",
                      builder_url="http://localhost:11434/v1",
                      provider="ollama", base_url=None, api_key=None,
                      max_calls=20, max_rows=100, sql_timeout=30, out=None,
                      max_retries=5, pace_seconds=0.0, validate=True, suggest_keyword=None):
    """Run one (judge model, condition, builder) configuration over a claim set.

    `provider` is a key into providers.PROVIDERS ("ollama" | "groq" | "openrouter") when base_url/api_key
    are left as None -- base_url and api_key are then resolved from there (including reading the right
    env var for a cloud key). Pass base_url/api_key explicitly to bypass the registry entirely.

    Resumable: a claim only counts as done if its most recent recorded row actually succeeded (see
    _load_last_rows/_is_success above) -- a 404/429/413 from a previous attempt is retried, not skipped.
    """
    max_rows = max_rows or None  # same convention as run_judge.py's CLI: 0 means "no cap"
    tag = f"{model_tag}|{condition}" + (f"|{builder_tag}" if builder_tag else "")

    from providers import PROVIDERS, resolve_api_key, validate_model
    if provider not in PROVIDERS and (base_url is None or api_key is None):
        raise ValueError(f"unknown provider {provider!r} and no explicit base_url/api_key given; "
                          f"known providers: {list(PROVIDERS)}")
    resolved_base_url = base_url or PROVIDERS[provider]["base_url"]
    resolved_api_key = api_key if api_key is not None else resolve_api_key(provider)

    if validate and provider in PROVIDERS and provider != "ollama":
        validate_model(provider, model_tag, suggest_keyword)  # raises with live-catalog suggestions on a dead tag

    claims = load_jsonl(claims_path)
    out = Path(out or f"results/{safe_name(model_tag)}__{condition}"
               f"{'__' + safe_name(builder_tag) if builder_tag else ''}.jsonl")
    out.parent.mkdir(parents=True, exist_ok=True)
    last_rows = _load_last_rows(out)
    done = {cid for cid, row in last_rows.items() if _is_success(row)}
    todo = [c for c in claims if c["claim_id"] not in done]
    if not todo:
        print(f"[skip] {out} already complete ({len(claims)} claims)")
        return out
    n_retryable = sum(1 for c in todo if c["claim_id"] in last_rows)
    if n_retryable:
        print(f"  [{tag}] {n_retryable} previously-failed claim(s) will be retried")

    prov = (OllamaProvider(base_url=resolved_base_url) if provider == "ollama"
            else OpenAIProvider(base_url=resolved_base_url, api_key=resolved_api_key))
    model = OpenAIChatModel(model_name=model_tag, provider=prov)

    builder = None
    if condition in ("C", "CS"):
        if not builder_tag:
            raise ValueError(f"condition {condition} needs a builder_tag")
        from builder import Builder
        builder = Builder(builder_tag, backend=builder_backend, template=builder_template, base_url=builder_url)

    args = types.SimpleNamespace(db_root=db_root, condition=condition, sql_timeout=sql_timeout,
                                  max_rows=max_rows, max_calls=max_calls, model=model_tag, builder=builder_tag)

    print(f"\n=== {model_tag} ({provider}) | condition {condition} | builder {builder_tag} | "
          f"{len(todo)}/{len(claims)} claims left -> {out} ===")
    meta = {"max_calls": max_calls, "max_rows": max_rows, "sql_timeout": sql_timeout,
            "builder_backend": builder_backend, "builder_template": builder_template, "provider": provider}
    for i, c in enumerate(todo, 1):
        r = await judge_with_retry(c, args, model, builder, max_retries, pace_seconds, tag)
        r["config"] = {**meta, "max_rows": args.max_rows}  # reflects any too_large shrink that happened
        with open(out, "a", encoding="utf-8") as f:
            f.write(json.dumps(r, default=str) + "\n")
        ok = "OK " if r["verdict"] == c["label"] else "-- "
        print(f"  [{i}/{len(todo)}] {ok}{c['claim_id']} gold={c['label']} pred={r['verdict'] or 'FAILED'} "
              f"calls={len(r['tool_log'])} {r['seconds']}s")
    return out
