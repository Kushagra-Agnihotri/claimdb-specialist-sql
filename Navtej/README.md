# SQL-Judge experiments: Conditions A, B, C on ClaimDB

## Quick start (Navtej's runs: pipeline 1 and pipeline 2)

Everything runs through Ollama (judge and builder). No API keys. **Run every command from this `Navtej/` folder.**

```
Navtej/
├── core/          shared Python: run_judge.py (both pipelines), common.py, score.py,
│                  builder.py (pipeline 2 only), eval_builder.py, make_subset.py
├── pipeline1_A/   run_A.sh, score_A.sh   judge writes its own SQL (Condition A)
├── pipeline2_C/   run_C.sh, score_C.sh   judge asks an NL2SQL builder (Condition C)
├── subsets/       claim files; test-public.jsonl = the 1,000 ClaimDB test claims
├── tests/
└── results/       created by the scripts when you run; not on GitHub
    ├── pipeline1_A/<model>/<claimset>/
    └── pipeline2_C/<model>/<builder>/<claimset>/
```

Each results folder holds `results.jsonl` (one line per claim), `run.log` (per-claim lines),
`passes.log` (one line per pass), `score.txt` and `backups/`.

```bash
# once, on the GPU machine
ollama pull a-kore/Arctic-Text2SQL-R1-7B     # builder for pipeline 2
ollama pull ministral-3:3b                    # judges
ollama pull ministral-3:8b
python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
export BIRD_DB_ROOT=/path/to/bird/dev_databases    # folder with the 11 BIRD dev databases
OLLAMA_CONTEXT_LENGTH=16384 ollama serve &         # if Ollama isn't already running

# pipeline 1: judge writes SQL
nohup ./pipeline1_A/run_A.sh --model ministral-3:8b --name ministral-8b --claims subsets/test-public.jsonl > /dev/null 2>&1 &

# pipeline 2: judge + Arctic builder (default builder)
nohup ./pipeline2_C/run_C.sh --model ministral-3:8b --name ministral-8b --claims subsets/test-public.jsonl > /dev/null 2>&1 &

# pipeline 2 with another builder (Section 3): change --builder; it gets its own builder folder
nohup ./pipeline2_C/run_C.sh --model ministral-3:8b --name ministral-8b --builder <omnisql-ollama-tag> --claims subsets/test-public.jsonl > /dev/null 2>&1 &

# scoring (finds the folder itself; writes score.txt next to the results)
./pipeline1_A/score_A.sh --name ministral-8b --claims subsets/test-public.jsonl
./pipeline2_C/score_C.sh --name ministral-8b --claims subsets/test-public.jsonl
./pipeline1_A/score_A.sh --all
./pipeline2_C/score_C.sh --all
```

Options (both run scripts): `--model` (required), `--name` (results folder name), `--claims` (default
`subsets/subset_210.jsonl`; use `subsets/test-public.jsonl` for the 1,000-claim runs), `--db-root` (or `$BIRD_DB_ROOT`),
`--ollama-url` (or `$OLLAMA_URL`, default `http://localhost:11434/v1`), `--results-root` (top results folder, default
`Navtej/results`; the pipeline folder is added under it, so e.g. a Google Drive path works on Colab),
`--stall-min` (default 20), `--once`. `run_C.sh` also takes `--builder` (default `a-kore/Arctic-Text2SQL-R1-7B`) and
`--builder-name` (folder name; default is the last part of the tag, e.g. `Arctic-Text2SQL-R1-7B`).

The run scripts loop until every claim has a line and resume after crashes. A pass that writes nothing for
`--stall-min` minutes is killed and restarted. Between passes, only infrastructure failures (HTTP 429/502/503/504,
connection errors, Ollama crashes) are dropped and retried. Model-side failures (20-call limit, malformed tool calls,
other errors) are kept and count as wrong, as in ClaimDB. Run one judge at a time per GPU to avoid running out of memory.

## Background (original harness notes)

The notes below come from the original harness. Commands there use the old flat layout (`python run_judge.py` from
`code/`); in this folder the same programs are in `core/`, e.g. `python core/run_judge.py ...`.

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
