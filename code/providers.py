"""Provider registry for OpenAI-compatible endpoints the judge/builder can hit: local Ollama, and the
two cloud APIs you actually tried (Groq, OpenRouter). Centralizes base_url + the API-key env var name,
and adds a model-tag *validator* against each provider's live /models endpoint.

Why this exists: of the five result files you sent back, THREE are 100%-failed runs (every one of
210 claims has an empty verdict) because the configured model tag didn't exist on that provider any
more, and a fourth spent most of its budget on rate limits rather than claims:

  - "llama-3.1-8b-instant" on Groq  -> 404 "does not exist or you do not have access to it"
                                        (Groq retired this exact tag)
  - "qwen3-8b" on Groq              -> 404, same reason (never existed under that exact tag on Groq)
  - "qwen/qwen3-8b:free" on OpenRouter -> 404 "deprecated... migrate to qwen/qwen3.7-plus"
  - "qwen/qwen3.8-27b" on Groq      -> DID run, but Groq's free "on_demand" tier caps ITPM (input
                                        tokens/min) at 7000 and TPD (tokens/day) at 200000. An agentic
                                        judge resends its whole growing tool-call transcript on every
                                        turn, so it blew through both limits well before 210 claims
                                        (413 "request too large", then repeated 429s).

A whole sweep burned on a dead tag looks identical, in the output file, to a whole sweep burned on a
real code bug -- you don't find out until the file comes back with every verdict empty. validate_model()
below catches a dead tag in under a second, before any claim is spent, by asking the provider what it
is actually serving right now -- instead of guessing a fresh tag from a (10-months-stale) training set,
which is exactly how "llama-3.1-8b-instant" and "qwen3-8b" ended up in a results file as 210 identical
404s. Use check_providers.py to see each provider's live catalog before filling in JUDGES in
sweep_judges.py.
"""
import json as _json
import os
import urllib.error
import urllib.request

PROVIDERS = {
    "ollama": {
        "base_url": "http://localhost:11434/v1",
        "api_key_env": None,          # no key needed locally
    },
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "api_key_env": "GROQ_API_KEY",
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "api_key_env": "OPENROUTER_API_KEY",
    },
}


def resolve_api_key(provider: str) -> str:
    env = PROVIDERS[provider]["api_key_env"]
    if env is None:
        return "none"   # Ollama ignores the key, but OpenAIProvider still wants a string
    key = os.environ.get(env)
    if not key:
        raise RuntimeError(f"{provider}: set the {env} environment variable before running this sweep "
                            f"(export {env}=...).")
    return key


def list_live_models(provider: str, timeout: int = 15) -> list[str]:
    """GET {base_url}/models and return the ids the provider is *currently* serving. Ollama, Groq and
    OpenRouter are all OpenAI-compatible here, so one request shape works for all three -- this is the
    live source of truth, not a hardcoded tag list that goes stale the moment a provider reshuffles
    its catalog (which is exactly what happened to three of your five result files)."""
    cfg = PROVIDERS[provider]
    req = urllib.request.Request(cfg["base_url"].rstrip("/") + "/models")
    key = resolve_api_key(provider)
    if key != "none":
        req.add_header("Authorization", f"Bearer {key}")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = _json.loads(resp.read())
    return sorted(m["id"] for m in data.get("data", []))


def validate_model(provider: str, model_tag: str, suggest_keyword: str | None = None) -> None:
    """Raise with a helpful message (and close-match suggestions pulled from the LIVE catalog) if
    model_tag isn't currently served by provider. Call this before burning claims on a sweep -- it is
    exactly what would have caught all three dead tags above, in under a second each, instead of after
    210 claims' worth of identical 404s."""
    try:
        live = list_live_models(provider)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
        print(f"  [warn] could not reach {provider}'s /models endpoint to pre-validate {model_tag!r} "
              f"({e}); proceeding without validation -- failures will only show up per-claim.")
        return
    if model_tag in live:
        return
    kw = (suggest_keyword or model_tag.split("/")[-1].split(":")[0].split("-")[0]).lower()
    close = [m for m in live if kw in m.lower()]
    hint = (f" Closest matches on {provider} right now: {close[:8]}" if close
            else f" No {kw!r}-like model found on {provider} right now -- run "
                 f"'python check_providers.py --provider {provider}' to see its full live catalog.")
    raise RuntimeError(f"{provider}: model tag {model_tag!r} is not currently served (renamed, "
                        f"retired, or never existed under that exact tag).{hint}")
