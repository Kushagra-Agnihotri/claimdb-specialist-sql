# SQL-Judge experiments: Conditions A, B, C on ClaimDB

## Setup C runs (different judge SLMs, same Arctic builder) — quick start

Everything runs through Ollama (judge and builder). No API keys. Run from `code/`.

```bash
# once, on the GPU machine
ollama pull a-kore/Arctic-Text2SQL-R1-7B     # builder (same for every run)
ollama pull ministral-3:3b                    # judges
ollama pull ministral-3:8b
python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
export BIRD_DB_ROOT=/path/to/bird/dev_databases    # folder with the 11 BIRD dev databases
# start Ollama with a 16k context if it isn't already running as a service:
OLLAMA_CONTEXT_LENGTH=16384 ollama serve &

# run (survives logout; each run resumes where it stopped)
nohup ./run_C.sh --model ministral-3:3b --name ministral-3b > /dev/null 2>&1 &
nohup ./run_C.sh --model ministral-3:8b --name ministral-8b > /dev/null 2>&1 &   # or after the first finishes

# another claim set: just point --claims at it
nohup ./run_C.sh --model ministral-3:8b --name ministral-8b --claims subsets/subset_1000.jsonl > /dev/null 2>&1 &

# score (finds the folder itself; writes score.txt next to the results)
./score_C.sh --name ministral-3b
./score_C.sh --all
```

Results layout: `results/<name>/<claimset>/` with `results.jsonl` (one line per claim), `run.log` (per-claim lines),
`passes.log` (one line per pass), `score.txt`, and `backups/`.

`run_C.sh` options: `--model` (required), `--name`, `--builder` (default `a-kore/Arctic-Text2SQL-R1-7B`),
`--claims` (default `subsets/subset_210.jsonl`), `--db-root` (or `$BIRD_DB_ROOT`), `--ollama-url` (or `$OLLAMA_URL`,
default `http://localhost:11434/v1`), `--results-root`, `--stall-min` (default 20), `--once`.
It loops until every claim has a line, kills a pass that writes nothing for `--stall-min` minutes, and between
passes drops only lines that failed because the *server* failed (HTTP 429/5xx, connection errors) so they are retried.
Model-side failures (20-call limit, crashes) are kept and count as wrong, as in ClaimDB.
Running two judges at the same time on one GPU can run out of memory; running them one after the other is safer.

What this runs, on the same ClaimDB claims:

| Condition | Judge gets | Question it answers |
|---|---|---|
| A  | ClaimDB exactly: the judge writes SQL, no schema given | Reproduction |
| B  | the judge writes SQL, schema (CREATE TABLE statements) given with the claim | How much does knowing the schema help? |
| C  | the judge asks an NL2SQL builder in plain English, no schema | Does handing SQL writing to a specialist help? |
| CS | builder, and the schema is also given to the judge | Does the builder help beyond schema access? (compare with B) |

Prompt, input format, output format, the 20 tool-call limit and output retries are copied from ClaimDB
(`claimdb/experiments.py`). The only deliberate deviation in all conditions: query results are capped at 100 rows
(with a "truncated" note) so long outputs cannot overflow a local model's context. It applies equally to A, B and C.

## One-time setup (Windows)

1. **Python 3.11** from python.org (tick "Add python.exe to PATH").
2. **Ollama for Windows** from ollama.com. Then set a larger context window and restart Ollama
   (quit it from the system tray, open it again):
   ```
   setx OLLAMA_CONTEXT_LENGTH 16384
   ```
3. Pull the judge models used in ClaimDB's table:
   ```
   ollama pull qwen3:8b
   ollama pull qwen3:4b
   ollama pull llama3.1:8b
   ```
4. **BIRD dev databases**: from https://bird-bench.github.io download the dev set, unzip it, then unzip the
   `dev_databases.zip` inside it. You need the folder that contains 11 sub-folders such as `california_schools`,
   `formula_1`, `superhero` (each with a `.sqlite` file). Below this is `C:\bird\dev_databases`.
5. In this folder: `pip install -r requirements.txt`

## Who runs what for the midsem (decided 11 Oct 2026)

All three runs use the judge `qwen3:8b` and `subsets\subset_210.jsonl`. Nothing else changes.

* **Condition A** (ClaimDB reproduction): one of Kushagra / Navtej
* **Condition B** (schema given): the other of Kushagra / Navtej
* **Condition C** (NL2SQL builder, Arctic-Text2SQL-R1-7B) and the builder-alone test: Kanishk

## Runs, in priority order

Each run resumes where it stopped if interrupted. Results go to `results\`.

```
# 1. Reproduction (Condition A) on the 210 balanced claims (70 per label)
python run_judge.py --claims subsets\subset_210.jsonl --db-root C:\bird\dev_databases --model qwen3:8b --condition A

# 2. Schema given (Condition B), same claims
python run_judge.py --claims subsets\subset_210.jsonl --db-root C:\bird\dev_databases --model qwen3:8b --condition B

# 3. Score and compare (add the ClaimDB released file to check reproduction, if downloaded)
python score.py results\qwen3_8b__A.jsonl results\qwen3_8b__B.jsonl

# 4. Builder on its own, on the BIRD questions behind these claims
ollama pull a-kore/Arctic-Text2SQL-R1-7B
python eval_builder.py --claims subsets\subset_210.jsonl --source subsets\BIRD-source.jsonl --db-root C:\bird\dev_databases --builder a-kore/Arctic-Text2SQL-R1-7B

# 5. Builder as the judge's tool (Conditions C and CS)
python run_judge.py --claims subsets\subset_210.jsonl --db-root C:\bird\dev_databases --model qwen3:8b --condition C  --builder a-kore/Arctic-Text2SQL-R1-7B
python run_judge.py --claims subsets\subset_210.jsonl --db-root C:\bird\dev_databases --model qwen3:8b --condition CS --builder a-kore/Arctic-Text2SQL-R1-7B
python score.py results\qwen3_8b__A.jsonl results\qwen3_8b__C__a-kore_Arctic-Text2SQL-R1-7B.jsonl
```

Reference (ClaimDB's released runs) on the same subsets:

| Subset | qwen3:4b | qwen3:8b | llama3.1:8b | gpt-5-mini |
|---|---|---|---|---|
| **subset_210 (70 per label), used for the midsem** | 0.471 | **0.486** | 0.329 | 0.838 |
| subset_60 (20 per label) | 0.400 | 0.517 | 0.317 | 0.767 |
| subset_150 (50 per label) | 0.473 | 0.493 | 0.333 | 0.807 |

Our Condition A should land near these. With 210 claims, one claim is about 0.5 points; expect a few points of run-to-run noise.

## Notes

* **GPU memory.** The judge and the builder both live in Ollama. If a 12 GB card runs out of memory in C/CS,
  use `qwen3:4b` as the judge or set `OLLAMA_CONTEXT_LENGTH` to 8192 for that run (and record it).
* **FINER-SQL 3B / SLM-SQL 1.5B** (Sir's suggestion). If no Ollama/GGUF build exists, install a CUDA build of
  torch plus `transformers accelerate`, then use `--builder-backend hf --builder griffith-bigdata/FINER-SQL-3B-BIRD
  --builder-template finer`. Check each model card's prompt format and adjust `builder.py` if needed.
* **Timing.** Qwen3 "thinks" before answering, so expect roughly 20 to 60 seconds per claim. 60 claims is
  about 30 to 60 minutes per condition.
* Every result line keeps the full transcript (`all_messages`) and a `tool_log` of every SQL query or builder
  call, so the error analysis can be done afterwards without re-running.
