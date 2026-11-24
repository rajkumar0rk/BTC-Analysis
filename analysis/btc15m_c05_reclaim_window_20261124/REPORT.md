# C05 reclaim window and trend slope training / frozen validation

7 independent reclaim timing or trend-slope variants plus protected C05 control; 64 training path/cost replays. Selected C00: {'atr': 3.5, 'rr': 3.5, 'wait': 2, 'flip': False, 'filter': 'h4ema50', 'activation': 2.5, 'lock': 0.0}. Training gate passed: True.
Training: Feb-Dec 2024 (Feb 1-2 warmup), Jan-Dec 2025 (source starts Jan 1 UTC). Validation: Jan-Oct 2026 (Dec 2025 warmup, no pre-2026 entries). 2026 was examined in previous research, so this is a procedural holdout, not genuinely untouched OOS. No tuning on validation results.
Confirmed H4 EMA50, fixed ATR14 stop and TP, fixed 2.5R delayed entry-price lock; one reclaim timeout change or confirmed H4 EMA slope condition. Zero-R lock is price breakeven before fees and slippage. No adaptive rules. No combined strategies, hedging, monthly or account-history switches. Fixed exposure. Baseline costs 0.05% taker per side+GST18%, slip 0.02% per side; stress slip 0.06%. Funding excluded.

|   period |   profile | stress   |      net |     dd |   months |   trades |   wins |   losses |
|---------:|----------:|:---------|---------:|-------:|---------:|---------:|-------:|---------:|
|     2024 |        80 | False    |  55.3164 |  7.356 |        7 |       75 |     27 |       48 |
|     2024 |        80 | True     |  45.2401 |  7.618 |        7 |       76 |     26 |       50 |
|     2024 |       100 | False    |  72.2885 |  9.124 |        7 |       75 |     27 |       48 |
|     2024 |       100 | True     |  58.4445 |  9.446 |        7 |       76 |     26 |       50 |
|     2025 |        80 | False    |  28.4964 | 11.287 |        9 |       81 |     24 |       57 |
|     2025 |        80 | True     |  28.5974 | 11.715 |        9 |       82 |     25 |       57 |
|     2025 |       100 | False    |  36.1215 | 13.936 |        9 |       81 |     24 |       57 |
|     2025 |       100 | True     |  36.2425 | 14.456 |        9 |       82 |     25 |       57 |
|     2026 |        80 | False    | -11.7217 | 21.334 |        3 |       54 |      8 |       46 |
|     2026 |        80 | True     | -13.2327 | 22.464 |        3 |       54 |      8 |       46 |
|     2026 |       100 | False    | -14.5901 | 25.985 |        3 |       54 |      8 |       46 |
|     2026 |       100 | True     | -16.4149 | 27.314 |        3 |       54 |      8 |       46 |

## Monthly returns (normal costs, worse of two paths)
| month_ist   |        80 |       100 |
|:------------|----------:|----------:|
| 2024-02     | -0.544005 | -0.712241 |
| 2024-03     | 15.0454   | 18.9588   |
| 2024-04     |  8.34022  | 10.4641   |
| 2024-05     | -2.81272  | -3.52039  |
| 2024-06     |  6.51164  |  8.15881  |
| 2024-07     | 10.3717   | 13.0741   |
| 2024-08     | -0.774177 | -1.02602  |
| 2024-09     |  6.70448  |  8.36628  |
| 2024-10     | -1.93388  | -2.4516   |
| 2024-11     |  1.91743  |  2.3743   |
| 2024-12     |  3.63065  |  4.48551  |
| 2025-01     |  2.77326  |  3.46348  |
| 2025-02     |  4.61604  |  5.72338  |
| 2025-03     | -5.55229  | -6.92452  |
| 2025-04     | 10.4901   | 13.1978   |
| 2025-05     |  2.81437  |  3.49092  |
| 2025-06     |  1.12208  |  1.38997  |
| 2025-07     | -0.82401  | -1.0437   |
| 2025-08     |  5.80893  |  7.25825  |
| 2025-09     |  1.27018  |  1.56356  |
| 2025-10     |  1.4534   |  1.80804  |
| 2025-11     |  8.07544  | 10.0595   |
| 2025-12     | -5.46475  | -6.80845  |
| 2026-01     |  6.15647  |  7.70635  |
| 2026-02     | -1.0199   | -1.28686  |
| 2026-03     | -1.15043  | -1.45458  |
| 2026-04     | -6.36881  | -7.90676  |
| 2026-05     | -2.75351  | -3.43423  |
| 2026-06     |  0.825789 |  0.980961 |
| 2026-07     | -0.918655 | -1.15767  |
| 2026-08     |  1.40705  |  1.74176  |
| 2026-09     | -5.22145  | -6.49174  |
| 2026-10     | -2.78157  | -3.46768  |

