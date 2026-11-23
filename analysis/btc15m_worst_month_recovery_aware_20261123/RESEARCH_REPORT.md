# BTCUSD 15M Reclaim — Repair the worst loss month without reducing profits

Full 70-configuration, 140-path simulation, 22-month Jan2025–Oct2026, 1-minute exit execution.
The original 15M Supertrend(10,3)+EMA20 Reclaim entry, 3% price SL and 9% fixed TP, no Supertrend flip exit.
Causal recovery-aware risk limits: pause only after 2 or 3 net losing exits AND 0–8% observed realized equity drawdown from prior month-end, but only when the PREVIOUS completed month was profitable by 0–5%. A prior losing month disables pauses to allow recovery.
Both no-protection original and +8.25% trigger/0% lock models used as control starting points.
Every pause rule only blocks FUTURE signals; it never rewrites past trades or closes an already open trade.
One trade per ST regime, no simultaneous positions. Original monthly equity returns exactly validated.
Strict success = (a) every original 16 profitable month returns no worse, (b) total net return >= original +97.5183%, and (c) worst monthly return less negative than −15.3196%.
Fee+18% GST on 0.05% taker each side and adverse 0.02% slippage each side modeled.
1x notional, starting $1000 equity. Funding, real execution, gap slippage and liquidation NOT fully modeled.
These 22 months have been heavily explored and are IN-SAMPLE, not prospective prediction.

## Strict pass count

0 of 69 non-original variants met all three conditions.

## Strict qualifying models

None met the full requirements.

## Best worst-month improvement (even if profitable months sacrificed)

| config                                              |   trades |   net_return_pct |   profitable_months |   original_win_months_preserved |   original_losing_months_improved |   mar2025_pct |   dec2025_pct |   worst_month_return_pct |   net_negative_month_sum_pp |   max_floating_drawdown_pct |   pause_entries_skipped |
|:----------------------------------------------------|---------:|-----------------:|--------------------:|--------------------------------:|----------------------------------:|--------------:|--------------:|-------------------------:|----------------------------:|----------------------------:|------------------------:|
| reclaim_NOFLIP_ORIG_MLOSSDDN2D5_PMUP1_SL300_TP3R    |       67 |          42.1759 |                  12 |                              11 |                                 2 |       -6.1775 |       -8.9013 |                  -10.082 |                    -52.7051 |                      31.698 |                      46 |
| reclaim_NOFLIP_ORIG_MLOSSDDN2D7_PMUP1_SL300_TP3R    |       72 |          93.3982 |                  15 |                              15 |                                 2 |       -7.1804 |       -8.9013 |                  -10.082 |                    -42.7668 |                      24.332 |                      16 |
| reclaim_NOFLIP_ORIG_MLOSSDDN2D7_PMUP0_SL300_TP3R    |       72 |          93.3982 |                  15 |                              15 |                                 2 |       -7.1804 |       -8.9013 |                  -10.082 |                    -42.7668 |                      24.332 |                      16 |
| reclaim_NOFLIP_ORIG_MLOSSDDN2D5_PMUP2_SL300_TP3R    |       67 |          42.1759 |                  12 |                              11 |                                 2 |       -6.1775 |       -8.9013 |                  -10.082 |                    -52.7051 |                      31.698 |                      46 |
| reclaim_NOFLIP_LATE825_MLOSSDDN2D6_PMUP2_SL300_TP3R |       70 |         112.472  |                  16 |                              15 |                                 3 |       -6.1775 |       -8.9013 |                  -10.082 |                    -36.8875 |                      24.332 |                      29 |
| reclaim_NOFLIP_ORIG_MLOSSDDN2D6_PMUP2_SL300_TP3R    |       68 |          95.4878 |                  15 |                              15 |                                 2 |       -6.1775 |       -8.9013 |                  -10.082 |                    -41.7639 |                      24.332 |                      29 |
| reclaim_NOFLIP_LATE825_MLOSSDDN2D7_PMUP3_SL300_TP3R |       74 |         110.201  |                  16 |                              15 |                                 3 |       -7.1804 |       -8.9013 |                  -10.082 |                    -37.8903 |                      24.332 |                      16 |
| reclaim_NOFLIP_LATE825_MLOSSDDN2D6_PMUP0_SL300_TP3R |       70 |         112.472  |                  16 |                              15 |                                 3 |       -6.1775 |       -8.9013 |                  -10.082 |                    -36.8875 |                      24.332 |                      29 |
| reclaim_NOFLIP_LATE825_MLOSSDDN2D4_PMUP2_SL300_TP3R |       69 |          54.5208 |                  13 |                              10 |                                 4 |       -6.1775 |       -8.9013 |                  -10.082 |                    -46.4295 |                      31.701 |                      48 |
| reclaim_NOFLIP_ORIG_MLOSSDDN2D4_PMUP0_SL300_TP3R    |       67 |          42.1689 |                  12 |                              10 |                                 3 |       -6.1775 |       -8.9013 |                  -10.082 |                    -51.3059 |                      31.701 |                      48 |
| reclaim_NOFLIP_ORIG_MLOSSDDN2D5_PMUP3_SL300_TP3R    |       67 |          42.1759 |                  12 |                              11 |                                 2 |       -6.1775 |       -8.9013 |                  -10.082 |                    -52.7051 |                      31.698 |                      46 |
| reclaim_NOFLIP_LATE825_MLOSSDDN2D6_PMUP3_SL300_TP3R |       70 |         112.472  |                  16 |                              15 |                                 3 |       -6.1775 |       -8.9013 |                  -10.082 |                    -36.8875 |                      24.332 |                      29 |
| reclaim_NOFLIP_LATE825_MLOSSDDN2D5_PMUP0_SL300_TP3R |       69 |          54.5284 |                  13 |                              11 |                                 3 |       -6.1775 |       -8.9013 |                  -10.082 |                    -47.8287 |                      31.698 |                      46 |
| reclaim_NOFLIP_LATE825_MLOSSDDN2D7_PMUP0_SL300_TP3R |       74 |         110.201  |                  16 |                              15 |                                 3 |       -7.1804 |       -8.9013 |                  -10.082 |                    -37.8903 |                      24.332 |                      16 |
| reclaim_NOFLIP_LATE825_MLOSSDDN2D5_PMUP2_SL300_TP3R |       69 |          54.5284 |                  13 |                              11 |                                 3 |       -6.1775 |       -8.9013 |                  -10.082 |                    -47.8287 |                      31.698 |                      46 |
| reclaim_NOFLIP_ORIG_MLOSSDDN2D4_PMUP2_SL300_TP3R    |       67 |          42.1689 |                  12 |                              10 |                                 3 |       -6.1775 |       -8.9013 |                  -10.082 |                    -51.3059 |                      31.701 |                      48 |
| reclaim_NOFLIP_ORIG_MLOSSDDN2D6_PMUP0_SL300_TP3R    |       68 |          95.4878 |                  15 |                              15 |                                 2 |       -6.1775 |       -8.9013 |                  -10.082 |                    -41.7639 |                      24.332 |                      29 |
| reclaim_NOFLIP_ORIG_MLOSSDDN2D4_PMUP1_SL300_TP3R    |       67 |          42.1689 |                  12 |                              10 |                                 3 |       -6.1775 |       -8.9013 |                  -10.082 |                    -51.3059 |                      31.701 |                      48 |
| reclaim_NOFLIP_ORIG_MLOSSDDN2D7_PMUP2_SL300_TP3R    |       72 |          93.3982 |                  15 |                              15 |                                 2 |       -7.1804 |       -8.9013 |                  -10.082 |                    -42.7668 |                      24.332 |                      16 |
| reclaim_NOFLIP_LATE825_MLOSSDDN2D5_PMUP1_SL300_TP3R |       69 |          54.5284 |                  13 |                              11 |                                 3 |       -6.1775 |       -8.9013 |                  -10.082 |                    -47.8287 |                      31.698 |                      46 |

## Best net profit (even if worst month unchanged)

| config                                              |   trades |   net_return_pct |   profitable_months |   original_win_months_preserved |   original_losing_months_improved |   mar2025_pct |   dec2025_pct |   worst_month_return_pct |   net_negative_month_sum_pp |   max_floating_drawdown_pct |   pause_entries_skipped |
|:----------------------------------------------------|---------:|-----------------:|--------------------:|--------------------------------:|----------------------------------:|--------------:|--------------:|-------------------------:|----------------------------:|----------------------------:|------------------------:|
| reclaim_NOFLIP_LATE825_MLOSSDDN3D0_PMUP2_SL300_TP3R |       71 |          131.294 |                  16 |                              13 |                                 5 |       -1.064  |      -11.7622 |                 -11.7622 |                    -27.4597 |                      26.709 |                      36 |
| reclaim_NOFLIP_LATE825_MLOSSDDN3D0_PMUP3_SL300_TP3R |       71 |          131.294 |                  16 |                              13 |                                 5 |       -1.064  |      -11.7622 |                 -11.7622 |                    -27.4597 |                      26.709 |                      36 |
| reclaim_NOFLIP_LATE825_MLOSSDDN3D0_PMUP0_SL300_TP3R |       71 |          131.294 |                  16 |                              13 |                                 5 |       -1.064  |      -11.7622 |                 -11.7622 |                    -27.4597 |                      26.709 |                      36 |
| reclaim_NOFLIP_LATE825_SL300_TP3R                   |       77 |          114.679 |                  17 |                              16 |                                 1 |      -13.3296 |      -15.3196 |                 -15.3196 |                    -40.3758 |                      20.86  |                       0 |
| reclaim_NOFLIP_ORIG_MLOSSDDN3D0_PMUP2_SL300_TP3R    |       69 |          112.805 |                  15 |                              13 |                                 4 |       -1.064  |      -11.7622 |                 -11.7622 |                    -32.3361 |                      26.709 |                      36 |
| reclaim_NOFLIP_ORIG_MLOSSDDN3D0_PMUP3_SL300_TP3R    |       69 |          112.805 |                  15 |                              13 |                                 4 |       -1.064  |      -11.7622 |                 -11.7622 |                    -32.3361 |                      26.709 |                      36 |
| reclaim_NOFLIP_ORIG_MLOSSDDN3D0_PMUP0_SL300_TP3R    |       69 |          112.805 |                  15 |                              13 |                                 4 |       -1.064  |      -11.7622 |                 -11.7622 |                    -32.3361 |                      26.709 |                      36 |
| reclaim_NOFLIP_LATE825_MLOSSDDN2D6_PMUP1_SL300_TP3R |       70 |          112.472 |                  16 |                              15 |                                 3 |       -6.1775 |       -8.9013 |                 -10.082  |                    -36.8875 |                      24.332 |                      29 |
| reclaim_NOFLIP_LATE825_MLOSSDDN2D6_PMUP3_SL300_TP3R |       70 |          112.472 |                  16 |                              15 |                                 3 |       -6.1775 |       -8.9013 |                 -10.082  |                    -36.8875 |                      24.332 |                      29 |
| reclaim_NOFLIP_LATE825_MLOSSDDN2D6_PMUP2_SL300_TP3R |       70 |          112.472 |                  16 |                              15 |                                 3 |       -6.1775 |       -8.9013 |                 -10.082  |                    -36.8875 |                      24.332 |                      29 |
| reclaim_NOFLIP_LATE825_MLOSSDDN2D6_PMUP0_SL300_TP3R |       70 |          112.472 |                  16 |                              15 |                                 3 |       -6.1775 |       -8.9013 |                 -10.082  |                    -36.8875 |                      24.332 |                      29 |
| reclaim_NOFLIP_LATE825_MLOSSDDN2D7_PMUP0_SL300_TP3R |       74 |          110.201 |                  16 |                              15 |                                 3 |       -7.1804 |       -8.9013 |                 -10.082  |                    -37.8903 |                      24.332 |                      16 |
| reclaim_NOFLIP_LATE825_MLOSSDDN2D7_PMUP1_SL300_TP3R |       74 |          110.201 |                  16 |                              15 |                                 3 |       -7.1804 |       -8.9013 |                 -10.082  |                    -37.8903 |                      24.332 |                      16 |
| reclaim_NOFLIP_LATE825_MLOSSDDN2D7_PMUP3_SL300_TP3R |       74 |          110.201 |                  16 |                              15 |                                 3 |       -7.1804 |       -8.9013 |                 -10.082  |                    -37.8903 |                      24.332 |                      16 |
| reclaim_NOFLIP_LATE825_MLOSSDDN2D7_PMUP2_SL300_TP3R |       74 |          110.201 |                  16 |                              15 |                                 3 |       -7.1804 |       -8.9013 |                 -10.082  |                    -37.8903 |                      24.332 |                      16 |
| reclaim_NOFLIP_LATE825_MLOSSDDN3D4_PMUP0_SL300_TP3R |       74 |          110.191 |                  16 |                              14 |                                 4 |       -4.171  |      -11.7622 |                 -11.7622 |                    -36.3426 |                      26.709 |                      22 |
| reclaim_NOFLIP_LATE825_MLOSSDDN3D2_PMUP0_SL300_TP3R |       74 |          110.191 |                  16 |                              14 |                                 4 |       -4.171  |      -11.7622 |                 -11.7622 |                    -36.3426 |                      26.709 |                      22 |
| reclaim_NOFLIP_LATE825_MLOSSDDN3D4_PMUP3_SL300_TP3R |       74 |          110.191 |                  16 |                              14 |                                 4 |       -4.171  |      -11.7622 |                 -11.7622 |                    -36.3426 |                      26.709 |                      22 |
| reclaim_NOFLIP_LATE825_MLOSSDDN3D4_PMUP2_SL300_TP3R |       74 |          110.191 |                  16 |                              14 |                                 4 |       -4.171  |      -11.7622 |                 -11.7622 |                    -36.3426 |                      26.709 |                      22 |
| reclaim_NOFLIP_LATE825_MLOSSDDN3D2_PMUP2_SL300_TP3R |       74 |          110.191 |                  16 |                              14 |                                 4 |       -4.171  |      -11.7622 |                 -11.7622 |                    -36.3426 |                      26.709 |                      22 |

## Original six losing months

month_ist
2025-01    -2.017007
2025-03   -13.329557
2025-05    -5.965644
2025-12   -15.319644
2026-04    -4.876433
2026-07    -3.743978

