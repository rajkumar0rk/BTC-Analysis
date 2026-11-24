# ATR exit stability training / frozen validation

18 predeclared configurations; 144 training path/cost replays. Selected C05: {'atr': 3.5, 'rr': 3.5, 'wait': 4, 'flip': False, 'filter': 'h4ema50'}. Training gate passed: True.
Training: Feb-Dec 2024 (Feb 1-2 warmup), Jan-Dec 2025 (source starts Jan 1 UTC). Validation: Jan-Oct 2026 (Dec 2025 warmup, no pre-2026 entries). 2026 was examined in previous research, so this is a procedural holdout, not genuinely untouched OOS. No tuning on validation results.
One confirmed higher-timeframe EMA50 trend filter (H1 or H4). ATR14 initial SL, fixed R-multiple TP, four-bar reclaim. No adaptive rules. No combined strategies, hedging, monthly or account-history switches. Fixed exposure. Baseline costs 0.05% taker per side+GST18%, slip 0.02% per side; stress slip 0.06%. Funding excluded.

|   period |   profile | stress   |     net |     dd |   months |   trades |   wins |   losses |
|---------:|----------:|:---------|--------:|-------:|---------:|---------:|-------:|---------:|
|     2024 |        80 | False    | 33.5109 | 13.089 |        5 |       88 |     28 |       60 |
|     2024 |        80 | True     | 21.661  | 14.422 |        5 |       90 |     27 |       63 |
|     2024 |       100 | False    | 42.3822 | 16.18  |        5 |       88 |     28 |       60 |
|     2024 |       100 | True     | 26.7649 | 17.901 |        5 |       90 |     27 |       63 |
|     2025 |        80 | False    | 22.7282 | 11.735 |        9 |       88 |     25 |       63 |
|     2025 |        80 | True     | 22.5515 | 12.161 |        9 |       89 |     26 |       63 |
|     2025 |       100 | False    | 28.4807 | 14.479 |        9 |       88 |     25 |       63 |
|     2025 |       100 | True     | 28.2369 | 14.997 |        9 |       89 |     26 |       63 |
|     2026 |        80 | False    |  2.9148 | 14.99  |        5 |       63 |     14 |       49 |
|     2026 |        80 | True     | -4.9303 | 19.356 |        5 |       64 |     13 |       51 |
|     2026 |       100 | False    |  3.2684 | 18.53  |        5 |       63 |     14 |       49 |
|     2026 |       100 | True     | -6.4567 | 23.751 |        5 |       64 |     13 |       51 |

## Monthly returns (normal costs, worse of two paths)
| month_ist   |        80 |       100 |
|:------------|----------:|----------:|
| 2024-02     | -2.24323  | -2.83049  |
| 2024-03     | 26.8165   | 34.2296   |
| 2024-04     |  4.16998  |  5.16854  |
| 2024-05     | -2.81272  | -3.52039  |
| 2024-06     |  4.98034  |  6.21709  |
| 2024-07     |  6.39424  |  7.99711  |
| 2024-08     | -0.774177 | -1.02602  |
| 2024-09     |  4.15098  |  5.12709  |
| 2024-10     | -3.06527  | -3.85951  |
| 2024-11     | -3.67024  | -4.60646  |
| 2024-12     | -1.30661  | -1.71474  |
| 2025-01     |  4.37988  |  5.46619  |
| 2025-02     |  4.61604  |  5.72338  |
| 2025-03     | -7.18758  | -8.93704  |
| 2025-04     |  9.15225  | 11.4844   |
| 2025-05     |  1.7076   |  2.09851  |
| 2025-06     |  1.12208  |  1.38997  |
| 2025-07     | -0.906897 | -1.15186  |
| 2025-08     |  5.05479  |  6.30266  |
| 2025-09     |  1.04883  |  1.28564  |
| 2025-10     |  0.874062 |  1.08133  |
| 2025-11     |  8.07544  | 10.0595   |
| 2025-12     | -5.94237  | -7.39716  |
| 2026-01     |  6.15647  |  7.70635  |
| 2026-02     |  9.86113  | 12.3759   |
| 2026-03     | -0.11736  | -0.195743 |
| 2026-04     | -1.56293  | -1.98521  |
| 2026-05     | -3.5719   | -4.45005  |
| 2026-06     |  1.82042  |  2.21166  |
| 2026-07     |  0.985469 |  1.19011  |
| 2026-08     |  2.5311   |  3.14993  |
| 2026-09     | -7.2625   | -9.00548  |
| 2026-10     | -4.80144  | -5.97155  |

