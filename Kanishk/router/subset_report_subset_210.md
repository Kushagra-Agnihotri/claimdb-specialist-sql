# Subset report: subset_210 (210 claims)

Router = logistic regression on frozen embeddings (threshold tuned on held out databases). S = judge + Python lookup tool, C = judge + Arctic builder, A = judge writes SQL. p = exact McNemar.

## llama3.1_8b: 210 of 210 subset claims have A, S and C

| Setup | Accuracy | Seconds per claim | Tool calls per claim |
|---|---|---|---|
| A (judge writes SQL) | 39.0 | 4.4 | 1.71 |
| S (Python lookup tool) | 23.3 | 10.6 | 1.27 |
| C (Arctic builder) | 53.3 | 19.5 | 1.04 |

| Claims (within the subset) | n | S | C | only S right / only C right | p | Seconds S / C |
|---|---|---|---|---|---|---|
| non-answerable router says yes | 71 | 45.1 | 62.0 | 12 / 24 | 0.065 | 9.3 / 22.4 |
|   of which gold NEI | 56 | 51.8 | 60.7 | 11 / 16 | 0.44 | 9.4 / 23.5 |
|   of which gold ENTAILED or CONTRADICTED | 15 | 20.0 | 66.7 | 1 / 8 | 0.039 | 8.8 / 18.2 |
| strict router says simple | 75 | 17.3 | 53.3 | 4 / 31 | 3.5e-06 | 12.3 / 18.8 |
| truly one table (strict label) | 41 | 26.8 | 53.7 | 4 / 15 | 0.019 | 9.8 / 19.3 |

| Routing on the subset | Accuracy | p vs always C | Seconds per claim |
|---|---|---|---|
| always C | 53.3 | | 19.5 |
| non-answerable yes -> S, else C | 47.6 | 0.065 | 15.1 |
| strict simple yes -> S, else C | 40.5 | 3.5e-06 | 17.2 |
| non-answerable yes -> answer NEI directly (no judge), else C | 59.0 | 0.05 | 12.0 |

## llama3.2_3b: 210 of 210 subset claims have A, S and C

| Setup | Accuracy | Seconds per claim | Tool calls per claim |
|---|---|---|---|
| A (judge writes SQL) | 35.2 | 3.3 | 3.49 |
| S (Python lookup tool) | 15.2 | 5.3 | 2.10 |
| C (Arctic builder) | 44.3 | 11.7 | 0.68 |

| Claims (within the subset) | n | S | C | only S right / only C right | p | Seconds S / C |
|---|---|---|---|---|---|---|
| non-answerable router says yes | 71 | 22.5 | 50.7 | 8 / 28 | 0.0012 | 4.4 / 12.7 |
|   of which gold NEI | 56 | 25.0 | 48.2 | 7 / 20 | 0.019 | 4.1 / 12.9 |
|   of which gold ENTAILED or CONTRADICTED | 15 | 13.3 | 60.0 | 1 / 8 | 0.039 | 5.8 / 11.8 |
| strict router says simple | 75 | 18.7 | 48.0 | 5 / 27 | 0.00011 | 5.6 / 11.0 |
| truly one table (strict label) | 41 | 17.1 | 43.9 | 2 / 13 | 0.0074 | 7.3 / 9.3 |

| Routing on the subset | Accuracy | p vs always C | Seconds per claim |
|---|---|---|---|
| always C | 44.3 | | 11.7 |
| non-answerable yes -> S, else C | 34.8 | 0.0012 | 9.0 |
| strict simple yes -> S, else C | 33.8 | 0.00011 | 9.8 |
| non-answerable yes -> answer NEI directly (no judge), else C | 53.8 | 0.0017 | 7.4 |

## qwen3_1.7b: 210 of 210 subset claims have A, S and C

| Setup | Accuracy | Seconds per claim | Tool calls per claim |
|---|---|---|---|
| A (judge writes SQL) | 34.8 | 2.7 | 0.47 |
| S (Python lookup tool) | 36.2 | 4.2 | 0.34 |
| C (Arctic builder) | 55.7 | 8.2 | 0.40 |

| Claims (within the subset) | n | S | C | only S right / only C right | p | Seconds S / C |
|---|---|---|---|---|---|---|
| non-answerable router says yes | 71 | 78.9 | 85.9 | 3 / 8 | 0.23 | 2.6 / 6.5 |
|   of which gold NEI | 56 | 98.2 | 96.4 | 2 / 1 | 1 | 2.5 / 4.6 |
|   of which gold ENTAILED or CONTRADICTED | 15 | 6.7 | 46.7 | 1 / 7 | 0.07 | 2.9 / 13.9 |
| strict router says simple | 75 | 30.7 | 46.7 | 5 / 17 | 0.017 | 3.0 / 8.6 |
| truly one table (strict label) | 41 | 36.6 | 53.7 | 4 / 11 | 0.12 | 2.9 / 8.9 |

| Routing on the subset | Accuracy | p vs always C | Seconds per claim |
|---|---|---|---|
| always C | 55.7 | | 8.2 |
| non-answerable yes -> S, else C | 53.3 | 0.23 | 6.9 |
| strict simple yes -> S, else C | 50.0 | 0.017 | 6.2 |
| non-answerable yes -> answer NEI directly (no judge), else C | 53.3 | 0.18 | 6.0 |

## qwen3_4b: 210 of 210 subset claims have A, S and C

| Setup | Accuracy | Seconds per claim | Tool calls per claim |
|---|---|---|---|
| A (judge writes SQL) | 51.4 | 36.5 | 1.28 |
| S (Python lookup tool) | 62.4 | 47.9 | 1.53 |
| C (Arctic builder) | 67.6 | 42.5 | 0.77 |

| Claims (within the subset) | n | S | C | only S right / only C right | p | Seconds S / C |
|---|---|---|---|---|---|---|
| non-answerable router says yes | 71 | 78.9 | 66.2 | 17 / 8 | 0.11 | 49.0 / 43.4 |
|   of which gold NEI | 56 | 92.9 | 71.4 | 15 / 3 | 0.0075 | 48.9 / 44.3 |
|   of which gold ENTAILED or CONTRADICTED | 15 | 26.7 | 46.7 | 2 / 5 | 0.45 | 49.4 / 39.8 |
| strict router says simple | 75 | 60.0 | 66.7 | 15 / 20 | 0.5 | 45.2 / 45.9 |
| truly one table (strict label) | 41 | 78.0 | 63.4 | 10 / 4 | 0.18 | 34.9 / 43.1 |

| Routing on the subset | Accuracy | p vs always C | Seconds per claim |
|---|---|---|---|
| always C | 67.6 | | 42.5 |
| non-answerable yes -> S, else C | 71.9 | 0.11 | 44.4 |
| strict simple yes -> S, else C | 65.2 | 0.5 | 42.2 |
| non-answerable yes -> answer NEI directly (no judge), else C | 71.9 | 0.093 | 27.8 |

## qwen3_8b: 210 of 210 subset claims have A, S and C

| Setup | Accuracy | Seconds per claim | Tool calls per claim |
|---|---|---|---|
| A (judge writes SQL) | 59.0 | 25.5 | 2.95 |
| S (Python lookup tool) | 59.0 | 26.0 | 2.05 |
| C (Arctic builder) | 74.3 | 29.5 | 1.00 |

| Claims (within the subset) | n | S | C | only S right / only C right | p | Seconds S / C |
|---|---|---|---|---|---|---|
| non-answerable router says yes | 71 | 78.9 | 81.7 | 10 / 12 | 0.83 | 20.2 / 27.9 |
|   of which gold NEI | 56 | 92.9 | 80.4 | 10 / 3 | 0.092 | 16.0 / 25.9 |
|   of which gold ENTAILED or CONTRADICTED | 15 | 26.7 | 86.7 | 0 / 9 | 0.0039 | 36.1 / 35.5 |
| strict router says simple | 75 | 58.7 | 69.3 | 14 / 22 | 0.24 | 25.4 / 27.1 |
| truly one table (strict label) | 41 | 75.6 | 80.5 | 2 / 4 | 0.69 | 17.4 / 29.3 |

| Routing on the subset | Accuracy | p vs always C | Seconds per claim |
|---|---|---|---|
| always C | 74.3 | | 29.5 |
| non-answerable yes -> S, else C | 73.3 | 0.83 | 26.9 |
| strict simple yes -> S, else C | 70.5 | 0.24 | 28.9 |
| non-answerable yes -> answer NEI directly (no judge), else C | 73.3 | 0.84 | 20.1 |
