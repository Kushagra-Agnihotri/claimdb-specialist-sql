# Small-Judge Specialist-SQL for ClaimDB

Can a small open-source LLM judge verify database claims more accurately by **delegating SQL generation** to a specialist NL2SQL model?

## Key Result

| Setup | Judge | Builder | Accuracy (1000 claims) |
|---|---|---|---|
| **A** — judge writes SQL | Qwen3-8B | — | 56.0% |
| **C** — specialist writes SQL | Qwen3-8B | Arctic-Text2SQL-R1-7B | **76.0%** (+20pt, p < 0.001) |

The specialist eliminates schema-grounding errors (missing table/column references drop from 25% to 9% of claims), which is the primary driver of the accuracy gain.

## Experimental Conditions

| Condition | Who writes SQL? | Schema given to judge? |
|---|---|---|
| A | Judge itself | No (must discover via sqlite_master) |
| B | Judge itself | Yes (CREATE TABLE DDL in prompt) |
| C | Arctic-Text2SQL-R1-7B specialist | No |
| C+values | Specialist + example column values | No |

## Setup

```bash
# Python 3.11+
pip install -r code/requirements.txt

# Ollama (for local GPU inference)
ollama pull qwen3:8b
ollama pull hf.co/mradermacher/Arctic-Text2SQL-R1-7B-GGUF:Q4_K_M
```

You need the BIRD dev databases from [bird-bench.github.io](https://bird-bench.github.io).

## Running

```bash
# Condition A (baseline)
python code/run_judge.py --claims data/subset_210.jsonl \
  --db-root /path/to/dev_databases --model qwen3:8b --condition A

# Condition C (specialist)
python code/run_judge.py --claims data/subset_210.jsonl \
  --db-root /path/to/dev_databases --model qwen3:8b --condition C \
  --builder hf.co/mradermacher/Arctic-Text2SQL-R1-7B-GGUF:Q4_K_M

# Score and compare
python code/score.py results/qwen3_8b__A.jsonl results/qwen3_8b__C__*.jsonl
```

## Project Page

See the full experiment documentation at the [GitHub Pages site](https://f20240718.github.io/claimdb-specialist-sql/).

## References

- ClaimDB: [github.com/claimdb/claimdb](https://github.com/claimdb/claimdb)
- BIRD benchmark: [bird-bench.github.io](https://bird-bench.github.io)
- Arctic-Text2SQL-R1-7B: [huggingface.co/a-kore/Arctic-Text2SQL-R1-7B](https://huggingface.co/a-kore/Arctic-Text2SQL-R1-7B)

---

BITS Pilani · Independent Learning Lab Module (ILLM) · 2026
