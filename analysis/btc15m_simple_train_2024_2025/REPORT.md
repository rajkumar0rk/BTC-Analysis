# Simple EMA20 reclaim training / frozen validation

24 predeclared configs; 96 training path replays. Selected C13: {'sl': 3.0, 'rr': 3.0, 'flip': False, 'filter': 'slope4'}. Training gate passed: False.
Training: Sep-Dec 2024 (Aug warmup), Jan-Dec 2025 (source starts Jan 1 UTC). Validation: Jan-Oct 2026 (Dec 2025 warmup, no pre-2026 entries). 2026 was examined in previous research, so this is a procedural holdout, not genuinely untouched OOS. No tuning on validation results.
No combined strategies, hedging, monthly or account-history switches. Fixed exposure. Baseline costs 0.05% taker per side+GST18%, slip 0.02% per side; stress slip 0.06%. Funding excluded.

|   period |   profile | stress   |     net |     dd |   months |   trades |   wins |   losses |
|---------:|----------:|:---------|--------:|-------:|---------:|---------:|-------:|---------:|
|     2024 |        80 | False    | 17.8325 | 16.682 |        3 |       18 |      7 |       11 |
|     2024 |        80 | True     | 17.1181 | 16.802 |        3 |       18 |      7 |       11 |
|     2024 |       100 | False    | 22.0882 | 20.395 |        3 |       18 |      7 |       11 |
|     2024 |       100 | True     | 21.1653 | 20.54  |        3 |       18 |      7 |       11 |
|     2025 |        80 | False    |  7.1915 | 17.131 |        8 |       46 |     13 |       33 |
|     2025 |        80 | True     |  5.591  | 17.485 |        8 |       46 |     13 |       33 |
|     2025 |       100 | False    |  7.7141 | 21.071 |        8 |       46 |     13 |       33 |
|     2025 |       100 | True     |  5.7066 | 21.493 |        8 |       46 |     13 |       33 |
|     2026 |        80 | False    | 38.2552 | 14.059 |        7 |       29 |     12 |       17 |
|     2026 |        80 | True     | 33.4687 | 14.221 |        6 |       30 |     12 |       18 |
|     2026 |       100 | False    | 48.4944 | 17.303 |        6 |       29 |     12 |       17 |
|     2026 |       100 | True     | 42.0842 | 17.5   |        6 |       30 |     12 |       18 |

## Monthly returns (normal costs, worse of two paths)
| month_ist   |          80 |         100 |
|:------------|------------:|------------:|
| 2024-09     |  20.1696    |  25.509     |
| 2024-10     |   5.37774   |   6.58965   |
| 2024-11     |  -8.86082   | -10.9932    |
| 2024-12     |   2.09776   |   2.53234   |
| 2025-01     |  -1.52504   |  -2.01701   |
| 2025-02     |   2.5578    |   3.12875   |
| 2025-03     |  -6.05438   |  -7.62294   |
| 2025-04     |   3.01163   |   3.58794   |
| 2025-05     |  -8.28632   | -10.3676    |
| 2025-06     |   5.42085   |   6.73693   |
| 2025-07     |   3.17612   |   3.88885   |
| 2025-08     |   3.54515   |   4.36808   |
| 2025-09     |   3.28312   |   4.10053   |
| 2025-10     |   9.43764   |  11.7467    |
| 2025-11     |   7.27438   |   9.01391   |
| 2025-12     | -12.4329    | -15.3196    |
| 2026-01     |  -5.68728   |  -7.17126   |
| 2026-02     |   9.00041   |  11.1939    |
| 2026-03     |   0.0431973 |  -0.0485034 |
| 2026-04     |  -5.41689   |  -6.74289   |
| 2026-05     |  13.3224    |  16.7548    |
| 2026-06     |   6.72911   |   8.27647   |
| 2026-07     |  -3.00086   |  -3.74398   |
| 2026-08     |   7.07851   |   8.84805   |
| 2026-09     |   6.72248   |   8.39745   |
| 2026-10     |   6.01257   |   7.49763   |

