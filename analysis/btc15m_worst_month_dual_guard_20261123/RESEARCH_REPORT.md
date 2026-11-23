# BTCUSD 15M Reclaim — Repair the worst loss month without reducing profits

Full 114-configuration, 228-path simulation, 22-month Jan2025–Oct2026, 1-minute exit execution.
The original 15M Supertrend(10,3)+EMA20 Reclaim entry, 3% price SL and 9% fixed TP, no Supertrend flip exit.
Causal tests only: pause new entries after 2–5 realized losing trades in the same month AND current cash equity down at least 0%,1%,2%,3%,4%,5%,6%,7%,8%,9%,10%,12%,14%, or 16% from previous month-end marked-to-market equity.
Both no-protection original and +8.25% trigger/0% lock models used as control starting points.
Every pause rule only blocks FUTURE signals; it never rewrites past trades or closes an already open trade.
One trade per ST regime, no simultaneous positions. Original monthly equity returns exactly validated.
Strict success = (a) every original 16 profitable month returns no worse, (b) total net return >= original +97.5183%, and (c) worst monthly return less negative than −15.3196%.
Fee+18% GST on 0.05% taker each side and adverse 0.02% slippage each side modeled.
1x notional, starting $1000 equity. Funding, real execution, gap slippage and liquidation NOT fully modeled.
These 22 months have been heavily explored and are IN-SAMPLE, not prospective prediction.

## Strict pass count

0 of 113 non-original variants met all three conditions.

## Strict qualifying models

None met the full requirements.

## Best worst-month improvement (even if profitable months sacrificed)

| config                                        |   trades |   net_return_pct |   profitable_months |   original_win_months_preserved |   original_losing_months_improved |   mar2025_pct |   dec2025_pct |   worst_month_return_pct |   net_negative_month_sum_pp |   max_floating_drawdown_pct |   pause_entries_skipped |
|:----------------------------------------------|---------:|-----------------:|--------------------:|--------------------------------:|----------------------------------:|--------------:|--------------:|-------------------------:|----------------------------:|----------------------------:|------------------------:|
| reclaim_NOFLIP_ORIG_MLOSSDDN2D6_SL300_TP3R    |       60 |         124.474  |                  15 |                              15 |                                 2 |       -6.1775 |       -8.9013 |                  -8.9013 |                    -42.02   |                      21.047 |                      48 |
| reclaim_NOFLIP_LATE825_MLOSSDDN2D6_SL300_TP3R |       62 |         143.976  |                  16 |                              15 |                                 3 |       -6.1775 |       -8.9013 |                  -8.9013 |                    -37.1435 |                      21.047 |                      48 |
| reclaim_NOFLIP_ORIG_MLOSSDDN2D1_SL300_TP3R    |       57 |          95.5459 |                  13 |                              10 |                                 4 |       -6.1775 |       -8.9013 |                  -8.9013 |                    -46.9516 |                      21.047 |                      92 |
| reclaim_NOFLIP_LATE825_MLOSSDDN2D0_SL300_TP3R |       58 |          95.2465 |                  13 |                               9 |                                 5 |       -6.1775 |       -8.9013 |                  -8.9013 |                    -42.1889 |                      24.043 |                      98 |
| reclaim_NOFLIP_ORIG_MLOSSDDN2D0_SL300_TP3R    |       56 |          79.6391 |                  12 |                               9 |                                 4 |       -6.1775 |       -8.9013 |                  -8.9013 |                    -47.0654 |                      24.043 |                      98 |
| reclaim_NOFLIP_ORIG_MLOSSDDN2D3_SL300_TP3R    |       59 |          83.466  |                  13 |                              11 |                                 3 |       -6.1775 |       -8.9013 |                  -8.9013 |                    -52.7276 |                      22.546 |                      84 |
| reclaim_NOFLIP_LATE825_MLOSSDDN2D2_SL300_TP3R |       61 |          99.406  |                  14 |                              11 |                                 4 |       -6.1775 |       -8.9013 |                  -8.9013 |                    -47.8512 |                      22.546 |                      84 |
| reclaim_NOFLIP_ORIG_MLOSSDDN2D2_SL300_TP3R    |       59 |          83.466  |                  13 |                              11 |                                 3 |       -6.1775 |       -8.9013 |                  -8.9013 |                    -52.7276 |                      22.546 |                      84 |
| reclaim_NOFLIP_ORIG_MLOSSDDN2D5_SL300_TP3R    |       59 |          83.4751 |                  13 |                              12 |                                 2 |       -6.1775 |       -8.9013 |                  -8.9013 |                    -54.1268 |                      22.542 |                      82 |
| reclaim_NOFLIP_ORIG_MLOSSDDN2D4_SL300_TP3R    |       59 |          83.466  |                  13 |                              11 |                                 3 |       -6.1775 |       -8.9013 |                  -8.9013 |                    -52.7276 |                      22.546 |                      84 |
| reclaim_NOFLIP_LATE825_MLOSSDDN2D4_SL300_TP3R |       61 |          99.406  |                  14 |                              11 |                                 4 |       -6.1775 |       -8.9013 |                  -8.9013 |                    -47.8512 |                      22.546 |                      84 |
| reclaim_NOFLIP_LATE825_MLOSSDDN2D5_SL300_TP3R |       61 |          99.4158 |                  14 |                              12 |                                 3 |       -6.1775 |       -8.9013 |                  -8.9013 |                    -49.2504 |                      22.542 |                      82 |
| reclaim_NOFLIP_LATE825_MLOSSDDN2D3_SL300_TP3R |       61 |          99.406  |                  14 |                              11 |                                 4 |       -6.1775 |       -8.9013 |                  -8.9013 |                    -47.8512 |                      22.546 |                      84 |
| reclaim_NOFLIP_LATE825_MLOSSDDN2D1_SL300_TP3R |       59 |         112.535  |                  14 |                              10 |                                 5 |       -6.1775 |       -8.9013 |                  -8.9013 |                    -42.0752 |                      21.047 |                      92 |
| reclaim_NOFLIP_LATE825_MLOSSDDN2D7_SL300_TP3R |       70 |         112.441  |                  16 |                              15 |                                 3 |       -7.1804 |       -8.9013 |                  -9.1239 |                    -36.9322 |                      23.526 |                      24 |
| reclaim_NOFLIP_ORIG_MLOSSDDN2D7_SL300_TP3R    |       68 |          95.4589 |                  15 |                              15 |                                 2 |       -7.1804 |       -8.9013 |                  -9.1239 |                    -41.8087 |                      23.526 |                      24 |
| reclaim_NOFLIP_LATE825_MLOSSDDN2D8_SL300_TP3R |       71 |         105.779  |                  16 |                              15 |                                 3 |      -10.0909 |       -8.9013 |                 -10.0909 |                    -39.8427 |                      23.526 |                      22 |
| reclaim_NOFLIP_ORIG_MLOSSDDN2D8_SL300_TP3R    |       69 |          89.3301 |                  15 |                              15 |                                 2 |      -10.0909 |       -8.9013 |                 -10.0909 |                    -44.7192 |                      23.526 |                      22 |
| reclaim_NOFLIP_LATE825_MLOSSDDN3D1_SL300_TP3R |       66 |         171.234  |                  16 |                              13 |                                 6 |       -1.064  |      -11.7622 |                 -11.7622 |                    -25.5615 |                      25.928 |                      49 |
| reclaim_NOFLIP_ORIG_MLOSSDDN3D3_SL300_TP3R    |       68 |         119.672  |                  15 |                              14 |                                 3 |       -4.171  |      -11.7622 |                 -11.7622 |                    -42.4227 |                      25.928 |                      33 |

## Best net profit (even if worst month unchanged)

| config                                        |   trades |   net_return_pct |   profitable_months |   original_win_months_preserved |   original_losing_months_improved |   mar2025_pct |   dec2025_pct |   worst_month_return_pct |   net_negative_month_sum_pp |   max_floating_drawdown_pct |   pause_entries_skipped |
|:----------------------------------------------|---------:|-----------------:|--------------------:|--------------------------------:|----------------------------------:|--------------:|--------------:|-------------------------:|----------------------------:|----------------------------:|------------------------:|
| reclaim_NOFLIP_LATE825_MLOSSDDN3D0_SL300_TP3R |       66 |          171.234 |                  16 |                              13 |                                 6 |       -1.064  |      -11.7622 |                 -11.7622 |                    -25.5615 |                      25.928 |                      49 |
| reclaim_NOFLIP_LATE825_MLOSSDDN3D1_SL300_TP3R |       66 |          171.234 |                  16 |                              13 |                                 6 |       -1.064  |      -11.7622 |                 -11.7622 |                    -25.5615 |                      25.928 |                      49 |
| reclaim_NOFLIP_LATE825_MLOSSDDN4D1_SL300_TP3R |       72 |          151.783 |                  16 |                              13 |                                 5 |       -4.171  |      -14.5332 |                 -14.5332 |                    -32.673  |                      25.937 |                      31 |
| reclaim_NOFLIP_LATE825_MLOSSDDN4D0_SL300_TP3R |       72 |          151.783 |                  16 |                              13 |                                 5 |       -4.171  |      -14.5332 |                 -14.5332 |                    -32.673  |                      25.937 |                      31 |
| reclaim_NOFLIP_ORIG_MLOSSDDN3D1_SL300_TP3R    |       64 |          149.552 |                  15 |                              13 |                                 5 |       -1.064  |      -11.7622 |                 -11.7622 |                    -30.4379 |                      25.928 |                      49 |
| reclaim_NOFLIP_ORIG_MLOSSDDN3D0_SL300_TP3R    |       64 |          149.552 |                  15 |                              13 |                                 5 |       -1.064  |      -11.7622 |                 -11.7622 |                    -30.4379 |                      25.928 |                      49 |
| reclaim_NOFLIP_LATE825_MLOSSDDN2D6_SL300_TP3R |       62 |          143.976 |                  16 |                              15 |                                 3 |       -6.1775 |       -8.9013 |                  -8.9013 |                    -37.1435 |                      21.047 |                      48 |
| reclaim_NOFLIP_LATE825_MLOSSDDN5D1_SL300_TP3R |       73 |          143.88  |                  17 |                              15 |                                 3 |       -7.1804 |      -15.3196 |                 -15.3196 |                    -31.54   |                      19.948 |                       9 |
| reclaim_NOFLIP_LATE825_MLOSSDDN5D0_SL300_TP3R |       73 |          143.88  |                  17 |                              15 |                                 3 |       -7.1804 |      -15.3196 |                 -15.3196 |                    -31.54   |                      19.948 |                       9 |
| reclaim_NOFLIP_LATE825_MLOSSDDN4D3_SL300_TP3R |       73 |          143.876 |                  16 |                              14 |                                 4 |       -4.171  |      -14.5332 |                 -14.5332 |                    -35.3596 |                      25.937 |                      27 |
| reclaim_NOFLIP_LATE825_MLOSSDDN4D4_SL300_TP3R |       73 |          143.876 |                  16 |                              14 |                                 4 |       -4.171  |      -14.5332 |                 -14.5332 |                    -35.3596 |                      25.937 |                      27 |
| reclaim_NOFLIP_LATE825_MLOSSDDN4D2_SL300_TP3R |       73 |          143.876 |                  16 |                              14 |                                 4 |       -4.171  |      -14.5332 |                 -14.5332 |                    -35.3596 |                      25.937 |                      27 |
| reclaim_NOFLIP_LATE825_MLOSSDDN3D4_SL300_TP3R |       70 |          138.758 |                  16 |                              14 |                                 4 |       -4.171  |      -11.7622 |                 -11.7622 |                    -37.5462 |                      25.928 |                      33 |
| reclaim_NOFLIP_LATE825_MLOSSDDN3D3_SL300_TP3R |       70 |          138.758 |                  16 |                              14 |                                 4 |       -4.171  |      -11.7622 |                 -11.7622 |                    -37.5462 |                      25.928 |                      33 |
| reclaim_NOFLIP_LATE825_MLOSSDDN3D2_SL300_TP3R |       70 |          138.758 |                  16 |                              14 |                                 4 |       -4.171  |      -11.7622 |                 -11.7622 |                    -37.5462 |                      25.928 |                      33 |
| reclaim_NOFLIP_LATE825_MLOSSDDN5D4_SL300_TP3R |       74 |          136.221 |                  17 |                              16 |                                 2 |       -7.1804 |      -15.3196 |                 -15.3196 |                    -34.2267 |                      20.86  |                       5 |
| reclaim_NOFLIP_LATE825_MLOSSDDN5D5_SL300_TP3R |       74 |          136.221 |                  17 |                              16 |                                 2 |       -7.1804 |      -15.3196 |                 -15.3196 |                    -34.2267 |                      20.86  |                       5 |
| reclaim_NOFLIP_LATE825_MLOSSDDN5D7_SL300_TP3R |       74 |          136.221 |                  17 |                              16 |                                 2 |       -7.1804 |      -15.3196 |                 -15.3196 |                    -34.2267 |                      20.86  |                       5 |
| reclaim_NOFLIP_LATE825_MLOSSDDN5D2_SL300_TP3R |       74 |          136.221 |                  17 |                              16 |                                 2 |       -7.1804 |      -15.3196 |                 -15.3196 |                    -34.2267 |                      20.86  |                       5 |
| reclaim_NOFLIP_LATE825_MLOSSDDN5D6_SL300_TP3R |       74 |          136.221 |                  17 |                              16 |                                 2 |       -7.1804 |      -15.3196 |                 -15.3196 |                    -34.2267 |                      20.86  |                       5 |

## Original six losing months

month_ist
2025-01    -2.017007
2025-03   -13.329557
2025-05    -5.965644
2025-12   -15.319644
2026-04    -4.876433
2026-07    -3.743978

