# SQL judge experiments: Table 2 runs (Nov 2026)

Setup C (judge asks Arctic-Text2SQL-R1-7B GGUF Q8_0), same harness and settings as the Oct runs (Ollama, context 16384, 20 tool calls), all 1,000 ClaimDB public-test claims. PC runs are driven by sqljudge\run_tonight.bat + runner.py, which reads sqljudge\tonight_queue.txt (status in tonight_status.txt, logs in tonight_logs\). Colab runs use sqljudge\colab (notebook + bundle + colab_queue.py; results in Google Drive MyDrive/sqljudge_colab/results).
Comparison column = ClaimDB's released per-claim runs (github claimdb/claimdb experiments/public), re-scored by us on the same claims; their full-test numbers match the paper table exactly (qwen3:4b 51.1, llama3.1:8b 34.4, ministral-3:8b 53.3, qwen3:8b 52.1).

## Section 1 results (judges with Arctic)
| Judge | n | Ours C (95% CI) | ClaimDB same claims | Gain | only ours / only ClaimDB, McNemar p | E / C / NEI acc ours vs ClaimDB | calls/claim ours vs ClaimDB | sec/claim |
|---|---|---|---|---|---|---|---|---|
| qwen3:14b | 1000 | 76.5 | 53.1 | +23.4 | not yet computed | | | ~18 on Colab A100 |
| qwen3:8b | 1000 | 76.0 (73.3 to 78.4) | 52.1 | +23.9 | 314 / 75, p = 7e-36 | 64.9/80.1/83.0 vs 30.6/31.1/94.0 | 0.98 vs 2.78 | 29.0 |
| qwen3:4b | 1000 | 68.3 (65.5 to 71.2) | 51.1 | +17.2 | 293 / 121, p = 1.5e-17 | 65.2/66.2/73.5 vs 45.0/21.8/86.0 | 0.75 vs 1.24 | 40.2 |
| qwen3:1.7b | 1000 | 54.7 (51.8 to 57.8) | 36.6 | +18.1 | 212 / 31, p = 2.5e-34 | 34.2/35.0/94.3 vs 6.0/4.8/98.2 | 0.37 vs 0.65 | 7.8 |
| llama3.1:8b | 1000 | 54.7 (51.7 to 57.8) | 34.4 | +20.3 | 326 / 123, p = 2.9e-22 | 63.4/37.8/62.8 vs 22.2/7.9/72.6 | 1.05 vs 2.07 | 18.9 |
| llama3.2:3b | 1000 | 45.2 (42.3 to 48.3) | 38.7 | +6.5 | 226 / 161, p = 1.1e-3 | 69.7/14.8/50.9 vs 37.2/10.0/68.5 | 0.71 vs 2.70 | 11.8 |

qwen3:14b: first 59 claims on PC, rest on Colab (L4 then A100), 1 failed verdict. Full file now in PC results; the PC-only 59-claim file is in results\_superseded.

Observations
- The builder gain holds across sizes (1.7B to 14B) and two families (Qwen, Llama): +17 to +24 points over ClaimDB for the same judge, except llama3.2:3b (+6.5).
- Qwen3 14B (76.5) is no better than 8B (76.0): with Arctic, scale stops helping after 8B; possibly the builder (about 62% execution accuracy alone) becomes the bottleneck. To check.
- Our qwen3:4b (68.3) beats every Qwen3 up to 32B in ClaimDB (32B 57.4) and qwen3-coder:30b (67.2); our qwen3:8b (76.0) beats gpt-oss:20b (74.0).
- Largest relative gain on CONTRADICTED claims. Same NEI trade-off everywhere. About half as many tool calls with the builder.
- Caveat: our harness alone adds about 4 points for qwen3:8b (A 56.0 vs ClaimDB 52.1); our own A for all judges is now done (see below).

## Section 3 (Kanishk's grid cells)
- qwen3:4b + OmniSQL-7B Q8: 1000 done on Colab, 65.5. llama3.1:8b + OmniSQL: 1000 on Colab, 54.0.
- qwen3:4b + SLM-SQL-1.5B: 676 rows (54.1). qwen3:4b + Qwen2.5-Coder-7B: 63 rows (42.9). llama3.1:8b + SLM-SQL: not started. Waiting on compute.

## Compute notes (12 Nov)
- Colab L4 is slower than the RTX 4070 Super for these runs (about 52 s/claim with 2 parallel workers; ollama ps showed 100% GPU, both models loaded). A100 about 18 to 24 s/claim but often unavailable on Colab Pro. Decision: long runs on the PC; Colab only when an A100 is free.
- Laptop browser closed overnight on 12 Nov (likely an Intel driver update via Windows Update). Pause Windows Update and Store app updates on run nights.
- PC lock screen blocks remote start; the runner keeps running when the PC is locked.

## A baselines (our harness, judge writes its own SQL), PC run 15 Nov
| Judge | A | C (Arctic) | Perfect per-claim A/C | NEI share of A verdicts | failed |
|---|---|---|---|---|---|
| qwen3:8b | 56.0 | 76.0 | 84.3 | 70% | 0 |
| qwen3:4b | 54.3 | 68.3 | 80.4 | 60% | 0 |
| qwen3:1.7b | 35.9 | 54.7 | 57.7 | 95% (skips tools on about 2/3 of claims, 2.5 s/claim) | 0 |
| llama3.1:8b | 35.7 | 54.7 | 66.8 | 72% | 4 |
| llama3.2:3b | 32.1 | 45.2 | 58.4 | | 130 (output format / tool retry limits) |

## Pathway #3 router (15 Nov)
Code in sqljudge\router (make_labels.py, embed.py, train_router.py, eval_routing.py); outputs router_metrics.json, preds\, routing_results.md. Frozen nomic-embed-text embeddings; train 40,652 claims on 62 BIRD DBs, threshold tuned on 7 held-out DBs (5,834 claims), test = 1,000 public claims. Positive = send to A, negative = send to C.
- Classifier quality (test AUC, linear / mlp2 / mlp3): complexity_strict 0.72 / 0.68 / 0.67; complexity_loose 0.64 / 0.61 / 0.61; answerability 0.95 / 0.95 / 0.94 (balanced accuracy about 0.88). The MLPs never beat logistic regression.
- Complexity routing lowers accuracy vs always C for every judge, even with true labels.
- Answerability routing (NEI claims to A, about 34% of claims), linear router vs always C:

| Judge | Always C | True-label routing | Linear router | McNemar p | Random router, same share |
|---|---|---|---|---|---|
| qwen3:8b | 76.0 | 80.6 | 76.0 | 1 | 69.2 |
| qwen3:4b | 68.3 | 74.3 | 70.9 | 0.0073 | 63.4 |
| qwen3:1.7b | 54.7 | 56.0 | 53.8 | 0.15 | 48.3 |
| llama3.1:8b | 54.7 | 57.6 | 55.3 | 0.66 | 48.4 |
| llama3.2:3b | 45.2 | 46.9 | 45.3 | 1 | 40.8 |

Takeaway: routing helps significantly only for qwen3:4b (+2.6); router errors erase the gain for the others. A is not faster than C (qwen3:8b 23.4 vs 29.0 s/claim), so this is an accuracy router, not a cost router.

## Next research step (agreed with Sir, 11 Nov meet)
Pathways 3 and 4: route each claim to a cheap "simple path" (judge + small Python lookup tool, no builder) or to C. #3 = MLP (2 to 3 layers) on frozen sentence embeddings (done, above, with A as the stand-in for the simple path); #4 = a separate small SLM (e.g. Qwen3-0.6B) fine-tuned as the classifier. Labels from each claim's BIRD gold SQL (single table = simple), made once and shared by all judges. Evaluate offline by combining per-claim results of the two paths.

## Work division (Experiment_Division_Plan.pdf, dated 1 Nov 2026, in sqljudge\report)
- Section 1, judges with Arctic: Kanishk qwen3 1.7B/4B/14B, llama 3.2 3B / 3.1 8B; Navtej ministral-3 3B/8B, mistral-nemo 12B (+ ministral-3 14B optional).
- Section 2, qwen3:8b with other builders: Kushagra OmniSQL-7B, Qwen2.5-Coder-7B, FINER-SQL 3B, SLM-SQL 1.5B, plus builder-alone eval on 189 BIRD questions.
- Section 3, 3 x 3 grid judges {qwen3:4b, llama3.1:8b, ministral-3:8b} x builders {OmniSQL-7B, Qwen2.5-Coder-7B, SLM-SQL 1.5B}: Kanishk 5 cells, Navtej 2, Kushagra 2.
