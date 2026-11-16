# SQL judge experiments: results log (12 to 13 Oct 2026)

All runs on Kanishk's PC (RTX 4070 Super 12 GB, Ollama, OLLAMA_CONTEXT_LENGTH=16384), code in Main\sqljudge, pydantic-ai 1.44.0.
Judge: qwen3:8b (Ollama, same as ClaimDB). Prompt: ClaimDB FACT_CHECKER_PROMPT_3SHOT verbatim for A (checked character for character); B/C change one or two sentences.
Claims: subset_210 (70 per label, seed 13) from ClaimDB public test (1000 claims, 11 BIRD dev DBs), and the full public test (1000). 20 tool call limit, 100 row cap, 30 s query timeout.

## Conditions
- A: judge writes SQL itself (ClaimDB setup, no schema).
- B: A + CREATE TABLE schema given with the claim.
- C: judge asks Arctic-Text2SQL-R1-7B (GGUF Q8_0 via Ollama) in natural language; builder gets schema + question + claim's Extra Information hint; returns SQL + rows.
- C+vals3: C, but builder schema also shows 3 example values per column (OmniSQL style comments). Judge input unchanged.

## HEADLINE: full 1000 claims (finished 13 Oct, 2:58 pm IST)
| Run | Acc | 95% CI (bootstrap) | Macro-F1 | Recall E/C/NEI | Pred NEI |
|---|---|---|---|---|---|
| ClaimDB published qwen3:8b run | 52.1 | 49.0 to 55.1 | 0.488 | 102/333, 103/331, 316/336 | 703 |
| A (our reproduction) | 56.0 | 53.1 to 59.0 | 0.533 | 105/333, 130/331, 325/336 | 699 |
| C (Arctic Q8, plain) | 76.0 | 73.4 to 78.6 | 0.759 | 216/333, 265/331, 279/336 | 361 |

- C vs A: +20.0 points; only C right 283, only A right 83; exact McNemar p = 1.2e-26.
- C vs ClaimDB's run: +23.9 points (p = 7e-36). A vs ClaimDB: +3.9 (p = 0.011).
- On the 790 claims outside the 210: A 55.2%, C 76.5% (the 210 result generalises within ClaimDB).
- C beats A on all 11 databases (C range 68% to 87%, A range 42% to 76%).
- C: no failed runs; 983 builder calls (0.98 per claim), 27 SQL errors, 61 empty results, 143 claims with no call; 29.0 s/claim (A 23.4 s/claim).
- Trade-off: NEI recall drops (325 to 279 of 336), true/false recall rises a lot (105 to 216, 130 to 265).
- Context from ClaimDB released runs on the same 1000 (cross-setup; our setup scores ~4 points above ClaimDB's for the same model): qwen3:32b 57.4, nemotron-3-nano:30b 66.7, qwen3-coder:30b 67.2, gpt-oss:20b 74.0, gpt-5-nano 78.7, claude-haiku-4-5 80.9, gpt-5-mini 82.7.

## Results on 210 claims (12 Oct)
| Run | Acc | 95% CI (bootstrap) | Recall E/C/NEI (of 70) | Pred NEI |
|---|---|---|---|---|
| ClaimDB released qwen3:8b run | 48.6 | 41.9 to 55.2 | 21/17/64 | 153 |
| A (our reproduction) | 59.0 | 52.4 to 65.7 | 25/30/69 | 141 |
| B | 61.0 | 54.3 to 67.1 | 25/35/68 | 139 |
| C (Q8) | 74.3 | 68.1 to 80.0 | 48/54/54 | 78 |
| C+vals3 (Q8) | 78.1 | 72.4 to 83.3 | 48/60/56 | 69 |
| gpt-5-mini (ClaimDB release, reference) | 83.8 | | | |

Exact McNemar (paired): A vs ClaimDB +10.5 (p=0.002); B vs A +1.9 (p=0.7); C vs A +15.2 (p=0.00045); C vs B +13.3 (p=0.0013); C+vals vs C +3.8 (p=0.23, not significant); C+vals vs A p=1e-5; C+vals vs B p=3e-5.

## Full 1000, A details
- 2722 queries, 919 failed (34%), 148 claims with no query. Pred NEI 699 vs ClaimDB 703 (same behaviour as ClaimDB's run).
- Breakdown by A's queries (strict: "no such table" or "no such column"): grounding error 482 claims (A 43.8, C 73.7); other error 25 (68.0 / 72.0, includes 3 "no such function"); all ran 345 (65.5 / 78.6); no query 148 (71.6 / 78.4). Earlier figures 485/22 counted "no such function" as grounding; corrected in the final report.
- Fixed by C (283): A said NEI on 256; 180 had a grounding error, 75 all ran, 25 no query, 3 other.

## Mechanism (candidate insight, from the 210)
- A: 619 queries, 219 failed (153 no such column, 54 no such table); 2.95 queries/claim.
- B: schema removes errors (113 queries, 5 failed) but judge skips querying on 121/210 claims (58%), always answering NEI; 65 of those were true/false claims. When B queries, 72/89 correct (81%).
- C: judge queries on 182/210 claims, ~1 builder call per claim.
- Remaining C failures (210): 24 true/false claims judged NEI; 16 had empty/null builder results (value format issues, e.g. State='CA' not 'California'; satscores.cds lacks leading zero so joins with schools/frpm fail for counties 01 to 09).

## ClaimDB log diagnostic (re-verified 13 Oct)
- 11 open models <=14B with complete runs (llama3.2:1b excluded, only 146 claims). Pooled model-claim pairs on E/C claims. Strict grounding error pairs: accuracy 20.8%, NEI 68.2%; all queries ran: 43.8%; never queried: 21.9%.
- Across the 19 models with complete runs: failed-call share vs accuracy, Pearson r = -0.88. Correlational.

## Builder alone (189 BIRD questions behind the 210 claims, execution accuracy)
- Arctic Q4_K_M: 115/189 = 60.8% (simple 71/102, moderate 34/62, challenging 10/25), 5.5 s/question.
- Arctic Q8_0: 118/189 = 62.4%, 8.6 s/question. Q8 vs Q4 McNemar p=0.45 (no significant difference).
- Arctic Q8_0 + vals3: 120/189 = 63.5% (+1.1 over plain, small; BIRD hints already give most values).
- Snowflake reports 68.9% on full BIRD dev; gap likely from harder subset mix and bare schema, not mainly quantization.
- Arctic training data (from its paper): BIRD train, Spider train/dev, Gretel synthetic; BIRD dev used only for evaluation, so no direct contamination of our databases.

## Decisions (approved by Kanishk)
- Context 16384 for all runs; Arctic gets the claim's hint; main C uses Q8_0; C+vals3 is a separate labelled variant.
- A and B run locally (not OpenRouter) for a clean comparison; teammates' OpenRouter / 27B runs are robustness checks only (record model, provider, pydantic-ai version, thinking on/off).
- B stays in the report as a pilot-only result (not rerun on 1000). The pilot (C beat B, p = 0.0013) is why C was prioritised for the full run.
- Credit: A and B runs are credited to Kushagra and Navtej (their assigned conditions), with Kanishk's permission, since their PCs could not run them. From now on they get literature, research and report tasks, not hardware heavy runs.
- AI Use Statement names only Claude (Kanishk's explicit instruction).

## Final report (13 Oct)
- Midsem_Report_Small_Judge_Specialist_SQL_final.pdf and midsem_report_overleaf_final.zip in Main\sqljudge\report. 6 pages including references, abstract 200 words.
- Every number re-derived from the raw result files with an independent script on 13 Oct; all match.
- TODO for the team: replace the CEDAR BibTeX entry with the official DBLP export.

## Threats to validity / reviewer questions (13 Oct check)
- Claims are generated from BIRD text-to-SQL questions, so a BIRD-trained builder fits by construction: needs a non-BIRD claim dataset.
- C uses two models (8B + 7B): compare against larger single judges, report cost and latency.
- Single run per condition: repeat runs for variance.
- One judge, one builder: add Qwen3 4B, Llama 3.1 8B judges and FINER-SQL 3B, SLM-SQL 1.5B builders.
- C trades NEI recall for true/false recall: report per-label recall and macro-F1.

## Post-midsem working plan
Daily small research steps on candidate pathways (generalisation incl. non-BIRD data, mechanism analysis, training with mentor approval, realistic multi-claim inputs, efficiency), each ending with a written decision. Goal: a main-conference paper.

## Notes
- Kanishk's PC had blue screens on 9, 10 and 12 Oct (bugchecks 0xC2, 0x50, 0x139): likely RAM instability or a driver, predates Ollama. Suggested mdsched and checking XMP/EXPO. 12/13 Oct ran ~18 hours without a crash.
- Report: built section by section with Kanishk on 13 Oct; nothing drafted without his approval.
