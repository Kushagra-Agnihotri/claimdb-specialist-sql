# Kanishk's workspace

Code, results and reports from Kanishk's PC and Colab runs (Section 1, Section 3, pathway #3 router, simple path S).
Start with `NOTES.md` for the full context and every number; `docs/` holds the October context.

Quick start (Windows, from `Kanishk/code`, Ollama running, BIRD dev databases in `..\data\dev_databases\dev_databases`):

    python run_judge.py --claims subsets\test-public.jsonl --db-root ..\data\dev_databases\dev_databases --model qwen3:8b --condition S
    python ..\router\eval_routing.py --cheap S

Results are stored gzipped in `results/`; unzip them into `results/` next to `code/` before scoring or routing.
