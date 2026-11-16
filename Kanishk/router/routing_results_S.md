# Routing results (pathway #3), cheap path = S

Positive = sent to S (simple path: judge + Python lookup tool); negative = sent to C (Arctic builder). Seconds = mean judge time per claim.

## qwen3_8b (1000 claims with both S and C)

Always S 61.8 (27.2 s)  |  Always C 76.0 (29.0 s)  |  Perfect per-claim choice 85.4

| Router | Sent to S | Accuracy | vs always C | McNemar p vs C | Random router, same share | Seconds per claim |
|---|---|---|---|---|---|---|
| complexity_strict, true label | 22% | 75.6 | -0.4 | | | 26.9 |
| complexity_strict, linear | 37% | 71.9 | -4.1 | 0.00022 | 70.8 | 28.0 |
| complexity_strict, mlp2 | 36% | 72.6 | -3.4 | 0.00099 | 70.9 | 27.3 |
| complexity_strict, mlp3 | 26% | 73.0 | -3.0 | 0.00064 | 72.3 | 27.7 |
| complexity_loose, true label | 69% | 65.6 | -10.4 | | | 26.9 |
| complexity_loose, linear | 70% | 64.9 | -11.1 | 1.2e-13 | 66.2 | 27.9 |
| complexity_loose, mlp2 | 75% | 65.4 | -10.6 | 5.5e-12 | 65.4 | 27.4 |
| complexity_loose, mlp3 | 85% | 64.3 | -11.7 | 1.2e-12 | 64.0 | 27.2 |
| answerability, true label | 34% | 79.6 | +3.6 | | | 25.2 |
| answerability, linear | 34% | 76.5 | +0.5 | 0.64 | 71.2 | 26.1 |
| answerability, mlp2 | 36% | 76.6 | +0.6 | 0.58 | 70.9 | 26.6 |
| answerability, mlp3 | 38% | 76.5 | +0.5 | 0.66 | 70.6 | 26.5 |
