# Routing results (pathway #3), cheap path = A

Positive = sent to A (judge writes its own SQL); negative = sent to C (Arctic builder). Seconds = mean judge time per claim.

## llama3.1_8b (1000 claims with both A and C)

Always A 35.7 (4.9 s)  |  Always C 54.7 (18.9 s)  |  Perfect per-claim choice 66.8

| Router | Sent to A | Accuracy | vs always C | McNemar p vs C | Random router, same share | Seconds per claim |
|---|---|---|---|---|---|---|
| complexity_strict, true label | 22% | 51.3 | -3.4 | | | 16.0 |
| complexity_strict, linear | 37% | 46.5 | -8.2 | 4.2e-11 | 47.7 | 13.5 |
| complexity_strict, mlp2 | 36% | 47.3 | -7.4 | 1.5e-09 | 48.0 | 14.0 |
| complexity_strict, mlp3 | 26% | 49.7 | -5.0 | 4.2e-07 | 49.8 | 15.4 |
| complexity_loose, true label | 69% | 41.5 | -13.2 | | | 9.9 |
| complexity_loose, linear | 70% | 42.3 | -12.4 | 8.4e-13 | 41.5 | 9.4 |
| complexity_loose, mlp2 | 75% | 39.7 | -15.0 | 1.6e-17 | 40.4 | 8.5 |
| complexity_loose, mlp3 | 85% | 39.2 | -15.5 | 3.3e-16 | 38.6 | 7.0 |
| answerability, true label | 34% | 57.6 | +2.9 | | | 13.2 |
| answerability, linear | 34% | 55.3 | +0.6 | 0.66 | 48.4 | 13.3 |
| answerability, mlp2 | 36% | 55.0 | +0.3 | 0.87 | 48.0 | 13.3 |
| answerability, mlp3 | 38% | 54.3 | -0.4 | 0.81 | 47.6 | 13.0 |

## llama3.2_3b (1000 claims with both A and C)

Always A 32.1 (3.3 s)  |  Always C 45.2 (11.8 s)  |  Perfect per-claim choice 58.4

| Router | Sent to A | Accuracy | vs always C | McNemar p vs C | Random router, same share | Seconds per claim |
|---|---|---|---|---|---|---|
| complexity_strict, true label | 22% | 43.9 | -1.3 | | | 10.3 |
| complexity_strict, linear | 37% | 41.4 | -3.8 | 0.0012 | 40.3 | 8.8 |
| complexity_strict, mlp2 | 36% | 41.0 | -4.2 | 0.00053 | 40.4 | 8.6 |
| complexity_strict, mlp3 | 26% | 42.9 | -2.3 | 0.021 | 41.8 | 9.5 |
| complexity_loose, true label | 69% | 36.7 | -8.5 | | | 6.6 |
| complexity_loose, linear | 70% | 36.5 | -8.7 | 9.9e-08 | 36.1 | 6.2 |
| complexity_loose, mlp2 | 75% | 36.6 | -8.6 | 6e-07 | 35.3 | 5.6 |
| complexity_loose, mlp3 | 85% | 35.3 | -9.9 | 5.8e-08 | 34.0 | 4.5 |
| answerability, true label | 34% | 46.9 | +1.7 | | | 8.9 |
| answerability, linear | 34% | 45.3 | +0.1 | 1 | 40.8 | 8.8 |
| answerability, mlp2 | 36% | 44.7 | -0.5 | 0.76 | 40.4 | 8.9 |
| answerability, mlp3 | 38% | 44.6 | -0.6 | 0.71 | 40.2 | 8.7 |

## qwen3_1.7b (1000 claims with both A and C)

Always A 35.9 (2.5 s)  |  Always C 54.7 (7.8 s)  |  Perfect per-claim choice 57.7

| Router | Sent to A | Accuracy | vs always C | McNemar p vs C | Random router, same share | Seconds per claim |
|---|---|---|---|---|---|---|
| complexity_strict, true label | 22% | 50.9 | -3.8 | | | 6.7 |
| complexity_strict, linear | 37% | 48.9 | -5.8 | 7.9e-11 | 47.7 | 5.8 |
| complexity_strict, mlp2 | 36% | 47.1 | -7.6 | 1.2e-16 | 47.9 | 5.8 |
| complexity_strict, mlp3 | 26% | 49.2 | -5.5 | 4.1e-12 | 49.8 | 6.3 |
| complexity_loose, true label | 69% | 41.9 | -12.8 | | | 4.1 |
| complexity_loose, linear | 70% | 42.2 | -12.5 | 1.3e-22 | 41.6 | 4.2 |
| complexity_loose, mlp2 | 75% | 40.5 | -14.2 | 2.6e-26 | 40.6 | 3.9 |
| complexity_loose, mlp3 | 85% | 39.0 | -15.7 | 3.1e-29 | 38.7 | 3.3 |
| answerability, true label | 34% | 56.0 | +1.3 | | | 7.0 |
| answerability, linear | 34% | 53.8 | -0.9 | 0.15 | 48.3 | 6.9 |
| answerability, mlp2 | 36% | 53.1 | -1.6 | 0.023 | 47.9 | 6.6 |
| answerability, mlp3 | 38% | 52.8 | -1.9 | 0.0066 | 47.5 | 6.5 |

## qwen3_4b (1000 claims with both A and C)

Always A 54.3 (36.7 s)  |  Always C 68.3 (40.2 s)  |  Perfect per-claim choice 80.4

| Router | Sent to A | Accuracy | vs always C | McNemar p vs C | Random router, same share | Seconds per claim |
|---|---|---|---|---|---|---|
| complexity_strict, true label | 22% | 66.9 | -1.4 | | | 38.3 |
| complexity_strict, linear | 37% | 62.6 | -5.7 | 3.5e-06 | 63.1 | 37.8 |
| complexity_strict, mlp2 | 36% | 64.5 | -3.8 | 0.0011 | 63.2 | 37.8 |
| complexity_strict, mlp3 | 26% | 65.2 | -3.1 | 0.0024 | 64.6 | 38.4 |
| complexity_loose, true label | 69% | 58.6 | -9.7 | | | 37.6 |
| complexity_loose, linear | 70% | 57.5 | -10.8 | 6.8e-11 | 58.5 | 37.8 |
| complexity_loose, mlp2 | 75% | 56.9 | -11.4 | 8.9e-12 | 57.8 | 37.6 |
| complexity_loose, mlp3 | 85% | 55.9 | -12.4 | 2.4e-12 | 56.3 | 37.0 |
| answerability, true label | 34% | 74.3 | +6.0 | | | 36.9 |
| answerability, linear | 34% | 70.9 | +2.6 | 0.0073 | 63.4 | 37.2 |
| answerability, mlp2 | 36% | 70.1 | +1.8 | 0.089 | 63.1 | 37.3 |
| answerability, mlp3 | 38% | 70.7 | +2.4 | 0.032 | 63.0 | 37.1 |

## qwen3_8b (1000 claims with both A and C)

Always A 56.0 (23.4 s)  |  Always C 76.0 (29.0 s)  |  Perfect per-claim choice 84.3

| Router | Sent to A | Accuracy | vs always C | McNemar p vs C | Random router, same share | Seconds per claim |
|---|---|---|---|---|---|---|
| complexity_strict, true label | 22% | 74.1 | -1.9 | | | 26.4 |
| complexity_strict, linear | 37% | 69.8 | -6.2 | 8.1e-08 | 68.5 | 26.0 |
| complexity_strict, mlp2 | 36% | 69.3 | -6.7 | 1.4e-09 | 68.9 | 25.6 |
| complexity_strict, mlp3 | 26% | 71.0 | -5.0 | 7.8e-08 | 70.7 | 26.3 |
| complexity_loose, true label | 69% | 61.9 | -14.1 | | | 24.5 |
| complexity_loose, linear | 70% | 61.1 | -14.9 | 2.6e-21 | 62.0 | 24.6 |
| complexity_loose, mlp2 | 75% | 60.0 | -16.0 | 5.6e-23 | 61.0 | 24.9 |
| complexity_loose, mlp3 | 85% | 58.8 | -17.2 | 8.2e-24 | 59.1 | 23.9 |
| answerability, true label | 34% | 80.6 | +4.6 | | | 25.5 |
| answerability, linear | 34% | 76.0 | +0.0 | 1 | 69.2 | 25.9 |
| answerability, mlp2 | 36% | 75.9 | -0.1 | 1 | 68.8 | 26.0 |
| answerability, mlp3 | 38% | 75.5 | -0.5 | 0.68 | 68.4 | 25.9 |
