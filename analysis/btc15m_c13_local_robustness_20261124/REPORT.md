# C13 local robustness training / frozen validation

27 predeclared C13-neighbor configurations; 216 training path/cost replays. Selected C12: {'sl': 3.0, 'rr': 3.0, 'flip': False, 'filter': 'slope3'}. Training gate passed: False.
Training: Sep-Dec 2024 (Aug warmup), Jan-Dec 2025 (source starts Jan 1 UTC). Validation: Jan-Oct 2026 (Dec 2025 warmup, no pre-2026 entries). 2026 was examined in previous research, so this is a procedural holdout, not genuinely untouched OOS. No tuning on validation results.
No combined strategies, hedging, monthly or account-history switches. Fixed exposure. Baseline costs 0.05% taker per side+GST18%, slip 0.02% per side; stress slip 0.06%. Funding excluded.

|   period |   profile | stress   |     net |     dd |   months |   trades |   wins |   losses |
|---------:|----------:|:---------|--------:|-------:|---------:|---------:|-------:|---------:|
|     2024 |        80 | False    | 10.0258 | 14.798 |        2 |       17 |      6 |       11 |
|     2024 |        80 | True     |  9.3885 | 15.05  |        2 |       17 |      6 |       11 |
|     2024 |       100 | False    | 12.1422 | 18.272 |        2 |       17 |      6 |       11 |
|     2024 |       100 | True     | 11.3318 | 18.576 |        2 |       17 |      6 |       11 |
|     2025 |        80 | False    | 23.8897 | 12.759 |        8 |       44 |     14 |       30 |
|     2025 |        80 | True     | 22.1241 | 12.843 |        8 |       44 |     14 |       30 |
|     2025 |       100 | False    | 29.0305 | 15.699 |        8 |       44 |     14 |       30 |
|     2025 |       100 | True     | 26.7367 | 15.903 |        8 |       44 |     14 |       30 |
|     2026 |        80 | False    | 35.835  | 15.682 |        7 |       26 |     11 |       15 |
|     2026 |        80 | True     | 34.6848 | 15.788 |        6 |       26 |     11 |       15 |
|     2026 |       100 | False    | 45.3851 | 19.18  |        6 |       26 |     11 |       15 |
|     2026 |       100 | True     | 43.851  | 19.309 |        6 |       26 |     11 |       15 |

## Monthly returns (normal costs, worse of two paths)
| month_ist   |          80 |         100 |
|:------------|------------:|------------:|
| 2024-09     |  16.7174    |  21.034     |
| 2024-10     |  -1.23851   |  -1.66221   |
| 2024-11     |  -6.51212   |  -8.10743   |
| 2024-12     |   2.09776   |   2.53234   |
| 2025-01     |  -1.52504   |  -2.01701   |
| 2025-02     |   2.5578    |   3.12875   |
| 2025-03     |  -6.05438   |  -7.62294   |
| 2025-04     |  12.3542    |  15.4276    |
| 2025-05     |  -4.24993   |  -5.42734   |
| 2025-06     |   4.11262   |   5.08133   |
| 2025-07     |   3.37584   |   4.14048   |
| 2025-08     |   3.54515   |   4.36808   |
| 2025-09     |   3.28312   |   4.10053   |
| 2025-10     |   9.43764   |  11.7467    |
| 2025-11     |   7.27438   |   9.01391   |
| 2025-12     | -10.1762    | -12.5741    |
| 2026-01     |  -7.33829   |  -9.11498   |
| 2026-02     |   9.00041   |  11.1939    |
| 2026-03     |   0.0431973 |  -0.0485034 |
| 2026-04     |  -5.41689   |  -6.74289   |
| 2026-05     |  13.3224    |  16.7548    |
| 2026-06     |   6.72911   |   8.27647   |
| 2026-07     |  -3.00086   |  -3.74398   |
| 2026-08     |   7.07851   |   8.84805   |
| 2026-09     |   6.72248   |   8.39745   |
| 2026-10     |   6.01257   |   7.49763   |

