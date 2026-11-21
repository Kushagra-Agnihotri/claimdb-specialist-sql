# Kanishk's working notes: Nov 2026 session (Section 1, Section 3, pathway #3, simple path S)

Context for teammates and for any Claude assistant picking this up. All numbers come from the files in `results/` and `router/` (qwen3 judges and llama judges on the ClaimDB public test, 1,000 claims, 11 BIRD dev databases). Older context: `docs/` (October results, ClaimDB setup analysis, the 11 Oct handoff document with the literature review in its appendix).

## Standing rules for this project
- Kanishk is kept in the loop on every decision; nothing in the report is drafted or edited without his approval.
- No dashes in written text. AI Use Statement names only Claude.
- Every new or changed file goes to this repo first.

## 1. Setups
| Setup | What the judge does | Code |
|---|---|---|
| A | writes SQL itself (ClaimDB exact) | `code/run_judge.py --condition A` |
| B | writes SQL, schema given | `--condition B` (210 claim pilot only) |
| C | asks a builder (NL2SQL model) in English; builder writes and runs SQL | `--condition C --builder <model>` |
| S | fills a lookup form; Python builds and runs the SQL (new, 15 Nov) | `--condition S`, tool in `code/simple_tools.py` |

Same prompt (ClaimDB 3 shot), output format, 20 tool call limit, 16k context, 100 row cap, 30 s query timeout in every setup.

## 2. Section 1 results (judge with Arctic Text2SQL R1 7B Q8_0), 1,000 claims
| Judge | ClaimDB release | Our A | Our C | C 95% CI | only A right / only C right | McNemar p (A vs C) | A s/claim | C s/claim |
|---|---|---|---|---|---|---|---|---|
| qwen3:14b | 53.1 | not run | 76.5 | | | | | 21.1 (Colab) |
| qwen3:8b | 52.1 | 56.0 | 76.0 | 73.3 to 78.4 | 83 / 283 | 1e-26 | 23.4 | 29.0 |
| qwen3:4b | 51.1 | 54.3 | 68.3 | 65.5 to 71.2 | 121 / 261 | 6e-13 | 36.7 | 40.2 |
| qwen3:1.7b | 36.6 | 35.9 | 54.7 | 51.8 to 57.8 | 30 / 218 | 2e-36 | 2.5 | 7.8 |
| llama3.1:8b | 34.4 | 35.7 | 54.7 | 51.7 to 57.8 | 121 / 311 | 2e-20 | 4.9 | 18.9 |
| llama3.2:3b | 38.7 | 32.1 | 45.2 | 42.3 to 48.3 | 132 / 263 | 4e-11 | 3.3 | 11.8 |

- qwen3:14b C: first 59 claims on the PC, rest on Colab (L4 then A100); 1 failed claim. PC only partial file in `results/_superseded`.
- llama3.2:3b A has 130 failed runs (output format / tool retry limits).
- Tool calls per claim (A / C): qwen3:8b 2.72 / 0.98, qwen3:4b 1.45 / 0.75, qwen3:1.7b 0.41 / 0.37, llama3.1:8b 2.00 / 1.05, llama3.2:3b 3.52 / 0.71; qwen3:14b C 1.20. ClaimDB release: 2.78, 1.24, 0.65, 2.07, 2.70.
- qwen3:8b accuracy per gold label, A / C / S: ENTAILED 31.5 / 64.9 / 41.7; CONTRADICTED 39.3 / 80.1 / 49.5; NEI 96.7 / 83.0 / 93.8. Share of NEI verdicts: A 69.9%, S 59.8%, C 36.1% (true 33.6%).

## 3. Section 3 (other builders)
| Judge | Builder | Claims | Accuracy | Ran on |
|---|---|---|---|---|
| qwen3:4b | OmniSQL 7B Q8 | 1000 | 65.5 | Colab A100 |
| llama3.1:8b | OmniSQL 7B Q8 | 1000 | 54.0 | Colab A100 |
| qwen3:4b | SLM SQL 1.5B (HF backend) | 676 | 54.1 | PC, partial |
| qwen3:4b | Qwen2.5 Coder 7B Q8 | 63 | 42.9 | Colab, partial |
| llama3.1:8b | SLM SQL 1.5B | 0 | pending | |

Colab Pro compute units are used up; the L4 was slower than the RTX 4070 Super. RKIC access requested from Prof. Dhruv Kumar.

## 4. Pathway #3 router (`router/`)
- Labels (`make_labels.py`): ClaimDB train split minus claims on the 11 test DBs = 46,486 claims on 69 BIRD train DBs; 7 whole DBs held out for threshold tuning (5,834 claims), 62 DBs for training (40,652); test = 1,000 public claims. Labels from each claim's BIRD gold SQL parsed with sqlglot:
  - strict simple = 1 table, no nested SELECT / set operation / window function (test: 215 claims)
  - loose simple = at most 2 tables, same other conditions (test: 692 claims, includes the 215)
  - non-answerable = gold label is NOT ENOUGH INFO (test: 336 claims)
  - These are three separate yes/no labels over the same claims, so the shares do not add to 100%. Test split by tables: 215 one table, 477 two tables, 308 three or more or nested.
- Embeddings (`embed.py`): "classification: " + claim + hint through nomic-embed-text (Ollama), 768 numbers, frozen.
- Classifiers (`train_router.py`): StandardScaler; logistic regression (class balanced), MLP 256, MLP 256+128 (oversampled); threshold = best balanced accuracy on the 7 held out DBs.
- Test AUC (LR / MLP2 / MLP3): strict 0.72 / 0.68 / 0.67; loose 0.64 / 0.61 / 0.61; non-answerable 0.95 / 0.95 / 0.94. MLPs never beat LR.
- Evaluation (`eval_routing.py`, `--cheap A` or `--cheap S`): offline, combines existing per claim verdicts. Results in `routing_results.md` (A) and `routing_results_S.md` (S).

Routing with A as the cheap path (LR router):
| Judge | Always A | Always C | Strict true | Strict LR | Loose true | Non answerable true | Non answerable LR | p vs C | Oracle |
|---|---|---|---|---|---|---|---|---|---|
| qwen3:8b | 56.0 | 76.0 | 74.1 | 69.8 | 61.9 | 80.6 | 76.0 | 1 | 84.3 |
| qwen3:4b | 54.3 | 68.3 | 66.9 | 62.6 | 58.6 | 74.3 | 70.9 | 0.007 | 80.4 |
| qwen3:1.7b | 35.9 | 54.7 | 50.9 | 48.9 | 41.9 | 56.0 | 53.8 | 0.15 | 57.7 |
| llama3.1:8b | 35.7 | 54.7 | 51.3 | 46.5 | 41.5 | 57.6 | 55.3 | 0.66 | 66.8 |
| llama3.2:3b | 32.1 | 45.2 | 43.9 | 41.4 | 36.7 | 46.9 | 45.3 | 1 | 58.4 |

"Answer NEI directly when the non-answerable router fires, otherwise C" (Sir's question, tuned threshold, no judge on 34% of claims): qwen3:8b 76.0 (29.0 to 19.6 s), qwen3:4b 72.1 (p 0.0002), qwen3:1.7b 54.2, llama3.1:8b 62.8 (p 7e-13), llama3.2:3b 56.2 (p 3e-19). Caveat: the classifier gives the verdict on those claims, from ClaimDB's NEI wording.

## 5. Simple path S (Python lookup tool, `code/simple_tools.py`)
- Tools: `describe_tables(table)`; `lookup(table, filters, aggregate, column, columns, group_by, order_by, descending, limit)`, one table per call. Filters = != > >= < <= contains starts_with is_null not_null; aggregates count count_distinct sum avg min max.
- Names resolved exactly, then ignoring case, then ignoring spaces/underscores; wrong names return the closest real names. Parameterised SQL built by Python; read only; 30 s timeout; 100 rows. Zero matches: shows similar stored values ("Marvel" → "Marvel Comics").
- `patch_condition_s.py` added condition S to `common.py` and `run_judge.py` (purely additive).
- qwen3:8b, 1,000 claims: S 61.8 (8 failed), A 56.0, C 76.0; S vs A p = 0.0003, S vs C p = 3e-15; 27.2 s vs C 29.0 s. 1,136 lookups (98 errors), 903 describe calls, 163 claims with no tool call. Pilot (30 claims): S 19, A 20, C 26.
- S vs C on subsets (qwen3:8b):
  | Claims | n | S | C | p | sec S / C |
  |---|---|---|---|---|---|
  | router says non answerable | 340 | 84.4 | 82.9 | 0.64 | 19.1 / 27.8 |
  | truly NEI | 336 | 93.8 | 83.0 | 5e-6 | 15.4 / 26.9 |
  | truly one table (strict) | 215 | 74.9 | 76.7 | 0.64 | 19.8 / 29.9 |
  | strict router says simple | 371 | 59.0 | 70.1 | 0.0002 | 26.5 / 29.4 |
  | truly two tables or fewer (loose) | 692 | 61.6 | 76.6 | 4e-12 | 25.9 / 29.0 |
- Reading: with correct labels, one table claims can go to S at no accuracy loss and a third less time; the text only router cannot find them (AUC 0.72). That is the case for #4.
- Status: qwen3:4b S was running on all 1,000 (about 175 done on 16 Nov); llama3.1:8b, qwen3:1.7b, llama3.2:3b queued. Sir's 15 Nov note says to use only subsets, so the plan is to restrict remaining S runs to the routed subsets (pending Kanishk's go ahead).

## 5b. Subset plan (21 Nov, Sir's note: subset only, plan before running)
- Subset: `code/subsets/subset_210.jsonl` (70 ENTAILED, 70 CONTRADICTED, 70 NEI, seed 13, all 11 DBs; same 210 as the midsem pilot). Inside it: 71 claims the non-answerable router sends to S (56 truly NEI), 75 the strict router calls simple, 41 truly one table.
- No reruns of A or C: both exist on all 1,000 claims for 5 judges, the subset is a filter. qwen3:8b S exists on all 1,000. qwen3:4b S has 39 of the 210.
- New runs (queued on the PC, 21 Nov): S on subset_210 for qwen3:1.7b, llama3.2:3b, llama3.1:8b, qwen3:4b (qwen3:4b resumes and runs only the missing 171). After each, `router/subset_report.py` rewrites `router/subset_report_subset_210.md`.
- The report answers: (1) A vs S vs C accuracy, seconds and tool calls per claim (point 6, n calls); (2) S vs C on the claims the router sends to S (point 4); (3) S vs C on one table claims; (4) end to end routing on the subset, including "answer NEI directly".
- qwen3:8b on subset_210: A 59.0, S 59.0, C 74.3; calls per claim 2.95 / 2.05 / 1.00. Routed claims (71): S 78.9 vs C 81.7, p = 0.83. Truly one table (41): S 75.6 vs C 80.5, p = 0.69.
- Old full 1,000 S lines for the other judges are commented out in the queue.

## 6. Meet notes (15 Nov) and status
- Show all three routes on examples with every intermediate step and prompts → `reports/Walkthrough_A_C_S.pdf` (claims 5584 and 1005).
- What is answerability → non-answerable = gold NEI (336 of 1,000: 111 out of schema, 113 counterfactual, 112 subjective).
- Python script → section 5 above and `code/simple_tools.py`.
- Check that the 33% routed claims are comparable to NL2SQL → section 5 table: 84.4 vs 82.9, p = 0.64.
- "Use only subset of samples, plan all experiments before starting experiments."
- Point 6 from the earlier list: compare NL2SQL vs [SQL writing + SQL executor] × n calls → calls per claim in section 2.

## 7. Proposed #4 (not run)
Qwen3 0.6B fine tuned with LoRA as the router, input = claim + hint + schema (table and column names). Same labels, splits, results and evaluation script; only the predictions file changes. Main question: can schema access make complexity routing (one table claims → S) work.

## Repo layout (Kanishk/)
- `code/` judge harness (A, B, C, CS, S), builder wrapper, scoring, subsets (`pilot30_S.jsonl` is the S pilot)
- `router/` pathway #3 scripts, metrics, predictions, routing tables, `labels.jsonl.gz`; the 146 MB embedding file is not committed (`python embed.py` regenerates it in about 30 min)
- `results/` every result file, gzipped (`gunzip -k` before use)
- `runner/` the PC job queue (`run_tonight.bat` starts `runner.py`, which runs each new line of `tonight_queue.txt` once)
- `colab/` Colab notebook and parallel queue script
- `reports/` PDFs (midsem report, roadmap, traces, meeting brief, study guide, walkthrough) and `generators/` (HTML to PDF scripts)
- `docs/` October results, ClaimDB setup analysis, November results, the 11 Oct handoff context, reference checks and BibTeX
- BIRD dev databases are not committed: get them from bird-bench.github.io (`dev_databases/<db>/<db>.sqlite`)
