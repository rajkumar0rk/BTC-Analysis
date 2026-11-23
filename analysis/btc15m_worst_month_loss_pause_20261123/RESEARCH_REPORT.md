# BTCUSD 15M Reclaim — Repair the worst loss month without reducing profits

Full 58-configuration, 116-path simulation, 22-month Jan2025–Oct2026, 1-minute exit execution.
The original 15M Supertrend(10,3)+EMA20 Reclaim entry, 3% price SL and 9% fixed TP, no Supertrend flip exit.
Causal tests only: pause after 1–5 monthly losing trades; after 1–5 monthly initial-stop exits; after -3% through -15% realized cash drawdown relative to prior month-end equity; or 3–30 day cooldown after 2–4 consecutive net losers.
Both no-protection original and +8.25% trigger/0% lock models used as control starting points.
Every pause rule only blocks FUTURE signals; it never rewrites past trades or closes an already open trade.
One trade per ST regime, no simultaneous positions. Original monthly equity returns exactly validated.
Strict success = (a) every original 16 profitable month returns no worse, (b) total net return >= original +97.5183%, and (c) worst monthly return less negative than −15.3196%.
Fee+18% GST on 0.05% taker each side and adverse 0.02% slippage each side modeled.
1x notional, starting $1000 equity. Funding, real execution, gap slippage and liquidation NOT fully modeled.
These 22 months have been heavily explored and are IN-SAMPLE, not prospective prediction.

## Strict pass count

0 of 57 non-original variants met all three conditions.

## Strict qualifying models

None met the full requirements.

## Best worst-month improvement (even if profitable months sacrificed)

| config                                      |   trades |   net_return_pct |   profitable_months |   original_win_months_preserved |   original_losing_months_improved |   mar2025_pct |   dec2025_pct |   worst_month_return_pct |   net_negative_month_sum_pp |   max_floating_drawdown_pct |   pause_entries_skipped |
|:--------------------------------------------|---------:|-----------------:|--------------------:|--------------------------------:|----------------------------------:|--------------:|--------------:|-------------------------:|----------------------------:|----------------------------:|------------------------:|
| reclaim_NOFLIP_ORIG_MLOSS1_SL300_TP3R       |       29 |          87.576  |                  12 |                               7 |                                 5 |       -3.1404 |       -3.1356 |                  -4.528  |                    -32.7629 |                      17.918 |                     226 |
| reclaim_NOFLIP_ORIG_MSTOP1_SL300_TP3R       |       29 |          87.576  |                  12 |                               7 |                                 5 |       -3.1404 |       -3.1356 |                  -4.528  |                    -32.7629 |                      17.918 |                     226 |
| reclaim_NOFLIP_LATE825_MSTOP1_SL300_TP3R    |       29 |          87.576  |                  12 |                               7 |                                 5 |       -3.1404 |       -3.1356 |                  -4.528  |                    -32.7629 |                      17.918 |                     226 |
| reclaim_NOFLIP_LATE825_MLOSS1_SL300_TP3R    |       29 |          87.576  |                  12 |                               7 |                                 5 |       -3.1404 |       -3.1356 |                  -4.528  |                    -32.7629 |                      17.918 |                     226 |
| reclaim_NOFLIP_LATE825_MDD3_SL300_TP3R      |       47 |          54.5877 |                  11 |                               9 |                                 4 |       -3.1404 |       -5.9523 |                  -5.9523 |                    -44.0829 |                      20.993 |                     156 |
| reclaim_NOFLIP_LATE825_MDD5_SL300_TP3R      |       60 |         105.871  |                  14 |                              12 |                                 3 |       -6.1775 |       -5.9523 |                  -6.1775 |                    -48.2244 |                      22.542 |                     108 |
| reclaim_NOFLIP_LATE825_MSTOP2_SL300_TP3R    |       50 |         144.447  |                  15 |                               9 |                                 5 |       -6.1775 |       -6.1775 |                  -6.1775 |                    -36.9307 |                      19.599 |                     140 |
| reclaim_NOFLIP_LATE825_MLOSS2_SL300_TP3R    |       50 |         144.447  |                  15 |                               9 |                                 5 |       -6.1775 |       -6.1775 |                  -6.1775 |                    -36.9307 |                      19.599 |                     140 |
| reclaim_NOFLIP_LATE825_CLOSS2D30_SL300_TP3R |       40 |          32.0937 |                  12 |                               7 |                                 3 |       -6.1775 |        0.1675 |                  -6.1775 |                    -43.3463 |                      28.612 |                     254 |
| reclaim_NOFLIP_ORIG_MSTOP2_SL300_TP3R       |       50 |         144.447  |                  15 |                               9 |                                 5 |       -6.1775 |       -6.1775 |                  -6.1775 |                    -36.9307 |                      19.599 |                     140 |
| reclaim_NOFLIP_ORIG_MLOSS2_SL300_TP3R       |       50 |         144.447  |                  15 |                               9 |                                 5 |       -6.1775 |       -6.1775 |                  -6.1775 |                    -36.9307 |                      19.599 |                     140 |
| reclaim_NOFLIP_ORIG_CLOSS2D30_SL300_TP3R    |       40 |          32.0937 |                  12 |                               7 |                                 3 |       -6.1775 |        0.1675 |                  -6.1775 |                    -43.3463 |                      28.612 |                     254 |
| reclaim_NOFLIP_ORIG_MDD3_SL300_TP3R         |       47 |          49.97   |                  11 |                               9 |                                 3 |       -3.1404 |       -5.9523 |                  -7.3926 |                    -46.9343 |                      23.353 |                     155 |
| reclaim_NOFLIP_ORIG_MDD5_SL300_TP3R         |       58 |          49.9645 |                  12 |                              10 |                                 2 |       -6.1775 |       -5.9523 |                  -7.3926 |                    -61.7899 |                      25.524 |                     125 |
| reclaim_NOFLIP_LATE825_MLOSS3_SL300_TP3R    |       63 |         198.436  |                  17 |                              13 |                                 6 |       -1.064  |       -9.1239 |                  -9.1239 |                    -21.4657 |                      25.931 |                      75 |
| reclaim_NOFLIP_ORIG_MDD7_SL300_TP3R         |       69 |          49.8978 |                  14 |                              13 |                                 2 |       -7.1804 |       -8.9013 |                  -9.1239 |                    -53.4399 |                      28.162 |                      40 |
| reclaim_NOFLIP_LATE825_CLOSS3D30_SL300_TP3R |       50 |          25.0128 |                  12 |                               8 |                                 5 |       -1.0689 |       -5.9523 |                  -9.1239 |                    -38.9666 |                      20.078 |                     150 |
| reclaim_NOFLIP_LATE825_MSTOP3_SL300_TP3R    |       63 |         198.436  |                  17 |                              13 |                                 6 |       -1.064  |       -9.1239 |                  -9.1239 |                    -21.4657 |                      25.931 |                      75 |
| reclaim_NOFLIP_ORIG_MLOSS3_SL300_TP3R       |       61 |         174.58   |                  16 |                              13 |                                 5 |       -1.064  |       -9.1239 |                  -9.1239 |                    -26.3421 |                      25.931 |                      75 |
| reclaim_NOFLIP_ORIG_CLOSS3D30_SL300_TP3R    |       49 |          25.2107 |                  12 |                               8 |                                 4 |       -1.0689 |       -5.9523 |                  -9.1239 |                    -41.8181 |                      20.078 |                     150 |

## Best net profit (even if worst month unchanged)

| config                                     |   trades |   net_return_pct |   profitable_months |   original_win_months_preserved |   original_losing_months_improved |   mar2025_pct |   dec2025_pct |   worst_month_return_pct |   net_negative_month_sum_pp |   max_floating_drawdown_pct |   pause_entries_skipped |
|:-------------------------------------------|---------:|-----------------:|--------------------:|--------------------------------:|----------------------------------:|--------------:|--------------:|-------------------------:|----------------------------:|----------------------------:|------------------------:|
| reclaim_NOFLIP_LATE825_MLOSS3_SL300_TP3R   |       63 |          198.436 |                  17 |                              13 |                                 6 |       -1.064  |       -9.1239 |                  -9.1239 |                    -21.4657 |                      25.931 |                      75 |
| reclaim_NOFLIP_LATE825_MSTOP3_SL300_TP3R   |       63 |          198.436 |                  17 |                              13 |                                 6 |       -1.064  |       -9.1239 |                  -9.1239 |                    -21.4657 |                      25.931 |                      75 |
| reclaim_NOFLIP_ORIG_MLOSS3_SL300_TP3R      |       61 |          174.58  |                  16 |                              13 |                                 5 |       -1.064  |       -9.1239 |                  -9.1239 |                    -26.3421 |                      25.931 |                      75 |
| reclaim_NOFLIP_ORIG_MSTOP3_SL300_TP3R      |       61 |          174.58  |                  16 |                              13 |                                 5 |       -1.064  |       -9.1239 |                  -9.1239 |                    -26.3421 |                      25.931 |                      75 |
| reclaim_NOFLIP_LATE825_MLOSS4_SL300_TP3R   |       70 |          168.361 |                  17 |                              14 |                                 5 |       -4.171  |      -14.5332 |                 -14.5332 |                    -31.6156 |                      25.937 |                      34 |
| reclaim_NOFLIP_LATE825_MSTOP4_SL300_TP3R   |       70 |          168.361 |                  17 |                              14 |                                 5 |       -4.171  |      -14.5332 |                 -14.5332 |                    -31.6156 |                      25.937 |                      34 |
| reclaim_NOFLIP_LATE825_MSTOP5_SL300_TP3R   |       72 |          151.787 |                  18 |                              16 |                                 3 |       -7.1804 |      -15.3196 |                 -15.3196 |                    -30.4827 |                      19.948 |                      11 |
| reclaim_NOFLIP_LATE825_MLOSS5_SL300_TP3R   |       72 |          151.787 |                  18 |                              16 |                                 3 |       -7.1804 |      -15.3196 |                 -15.3196 |                    -30.4827 |                      19.948 |                      11 |
| reclaim_NOFLIP_ORIG_MSTOP4_SL300_TP3R      |       68 |          146.909 |                  16 |                              14 |                                 4 |       -4.171  |      -14.5332 |                 -14.5332 |                    -36.4921 |                      25.937 |                      34 |
| reclaim_NOFLIP_ORIG_MLOSS4_SL300_TP3R      |       68 |          146.909 |                  16 |                              14 |                                 4 |       -4.171  |      -14.5332 |                 -14.5332 |                    -36.4921 |                      25.937 |                      34 |
| reclaim_NOFLIP_ORIG_MLOSS2_SL300_TP3R      |       50 |          144.447 |                  15 |                               9 |                                 5 |       -6.1775 |       -6.1775 |                  -6.1775 |                    -36.9307 |                      19.599 |                     140 |
| reclaim_NOFLIP_LATE825_MSTOP2_SL300_TP3R   |       50 |          144.447 |                  15 |                               9 |                                 5 |       -6.1775 |       -6.1775 |                  -6.1775 |                    -36.9307 |                      19.599 |                     140 |
| reclaim_NOFLIP_LATE825_MLOSS2_SL300_TP3R   |       50 |          144.447 |                  15 |                               9 |                                 5 |       -6.1775 |       -6.1775 |                  -6.1775 |                    -36.9307 |                      19.599 |                     140 |
| reclaim_NOFLIP_ORIG_MSTOP2_SL300_TP3R      |       50 |          144.447 |                  15 |                               9 |                                 5 |       -6.1775 |       -6.1775 |                  -6.1775 |                    -36.9307 |                      19.599 |                     140 |
| reclaim_NOFLIP_LATE825_CLOSS4D3_SL300_TP3R |       70 |          138.762 |                  17 |                              14 |                                 4 |      -10.0909 |       -9.7396 |                 -10.0909 |                    -30.1579 |                      17.632 |                      13 |
| reclaim_NOFLIP_ORIG_MLOSS5_SL300_TP3R      |       70 |          131.66  |                  17 |                              16 |                                 2 |       -7.1804 |      -15.3196 |                 -15.3196 |                    -35.3591 |                      19.948 |                      11 |
| reclaim_NOFLIP_ORIG_MSTOP5_SL300_TP3R      |       70 |          131.66  |                  17 |                              16 |                                 2 |       -7.1804 |      -15.3196 |                 -15.3196 |                    -35.3591 |                      19.948 |                      11 |
| reclaim_NOFLIP_ORIG_CLOSS4D3_SL300_TP3R    |       68 |          119.676 |                  16 |                              14 |                                 3 |      -10.0909 |       -9.7396 |                 -10.0909 |                    -35.0343 |                      17.632 |                      13 |
| reclaim_NOFLIP_LATE825_MDD15_SL300_TP3R    |       77 |          114.679 |                  17 |                              16 |                                 1 |      -13.3296 |      -15.3196 |                 -15.3196 |                    -40.3758 |                      20.86  |                       0 |
| reclaim_NOFLIP_LATE825_SL300_TP3R          |       77 |          114.679 |                  17 |                              16 |                                 1 |      -13.3296 |      -15.3196 |                 -15.3196 |                    -40.3758 |                      20.86  |                       0 |

## Original six losing months

month_ist
2025-01    -2.017007
2025-03   -13.329557
2025-05    -5.965644
2025-12   -15.319644
2026-04    -4.876433
2026-07    -3.743978

