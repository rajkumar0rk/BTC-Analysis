# BTC +200/−100 scalp — causal regime and entry selection, 1× account

**Decision: NO_2025_TRAINING_QUALIFIED_STRATEGY**

## Rules and market regime

- Long/short signal after complete 15m close, entry at next 1m OPEN. All 1h EMA20/50, ADX14 and ATR14 are from LAST COMPLETED 1H candle.
- TREND_UP/DOWN: 1h ADX>=25 and EMA20>EMA50, hour close>EMA20 (reverse for short). RANGE: ADX<=18. Other classified hours: TRANSITION.
- 12 predeclared pattern families × high-vol/no-extra-vol-gate plus one fixed 12:00 IST benchmark. No 2026-driven optimization.
- Fixed raw 200 BTC points TP, 100 BTC points SL, 4h max hold or IST day-end, stop-first 1m replay. Full account 1× exposure with 0.05% fee per side and GST18% plus 5 adverse points/side.
- Minimum 30 2025 trades in each half, positive mean after-cost BTC-equivalent points in BOTH halves, and positive normal-style 95%-lower mean bound on 2025 all. Otherwise **NO SELECTED STRATEGY**.

## Complete-market 2025 and seen-2026 checks

|   ranking_2025_only | candidate                     |   2025_ALL_trades |   2025_ALL_tp_first_pct |   2025_ALL_net_win_pct |   2025_ALL_net_points_mean |   2025_ALL_net_points_lower95 |   2025_H1_net_points_mean |   2025_H2_net_points_mean |   2026_H1_SEEN_trades |   2026_H1_SEEN_net_points_mean |   2026_H2_SEEN_trades |   2026_H2_SEEN_net_points_mean | train_qualified   |
|--------------------:|:------------------------------|------------------:|------------------------:|-----------------------:|---------------------------:|------------------------------:|--------------------------:|--------------------------:|----------------------:|-------------------------------:|----------------------:|-------------------------------:|:------------------|
|                   1 | V01_EXHAUSTION_FADE_HIGHVOL   |                45 |                  48.889 |                 48.889 |                    -72.452 |                      -117.183 |                   -82.689 |                   -53.898 |                    23 |                       -113.542 |                     3 |                         96.396 | False             |
|                   2 | R01_12BAR_SWEEP_HIGHVOL       |                31 |                  48.387 |                 48.387 |                    -73.816 |                      -127.006 |                   -60.97  |                  -100.791 |                    16 |                        -77.678 |                     3 |                        -90.511 | False             |
|                   3 | D00_FIXED_CLOCK_BENCHMARK     |               361 |                  37.673 |                 37.673 |                   -116.358 |                      -131.541 |                   -93.963 |                  -138.141 |                   181 |                        -86.323 |                   122 |                        -87.954 | False             |
|                   4 | T01_PULLBACK_BREAK_HIGHVOL    |               105 |                  37.143 |                 37.143 |                   -112.503 |                      -139.906 |                  -133.734 |                   -81.89  |                    61 |                       -104.593 |                    15 |                       -116.993 | False             |
|                   5 | V01_EXHAUSTION_FADE           |               149 |                  37.584 |                 37.584 |                   -116.711 |                      -140.168 |                  -125.208 |                  -109.578 |                    73 |                       -101.289 |                    47 |                        -83.403 | False             |
|                   6 | T01_PULLBACK_BREAK            |               237 |                  35.443 |                 35.865 |                   -122.421 |                      -140.597 |                  -134.862 |                  -110.693 |                   125 |                        -93.576 |                    75 |                        -81.602 | False             |
|                   7 | T03_INSIDE_RELEASE            |                88 |                  34.091 |                 35.227 |                   -125.073 |                      -155.272 |                   -93.29  |                  -150.369 |                    52 |                       -105.765 |                    21 |                        -80.629 | False             |
|                   8 | R01_12BAR_SWEEP               |               136 |                  31.618 |                 31.618 |                   -131.634 |                      -155.391 |                  -121.097 |                  -145.805 |                    55 |                        -88.269 |                    48 |                       -107.739 | False             |
|                   9 | T04_STRONG_CONT               |               134 |                  32.09  |                 32.09  |                   -132.085 |                      -155.787 |                  -132.625 |                  -131.575 |                    75 |                        -90.353 |                    44 |                        -75.042 | False             |
|                  10 | R03_4H_SWEEP_HIGHVOL          |                32 |                  37.5   |                 37.5   |                   -106.243 |                      -157.31  |                   -95.098 |                  -130.763 |                    17 |                       -102.176 |                     4 |                        -39.525 | False             |
|                  11 | M01_RECLAIM                   |               149 |                  31.544 |                 31.544 |                   -135.165 |                      -157.638 |                  -159.272 |                  -115.467 |                    81 |                        -90.206 |                    49 |                        -84.002 | False             |
|                  12 | T02_8BAR_BREAK_HIGHVOL        |                61 |                  32.787 |                 32.787 |                   -124.377 |                      -160.321 |                  -118.771 |                  -130.984 |                    41 |                       -104.719 |                    12 |                        -99.436 | False             |
|                  13 | T05_TWO_BAR                   |               212 |                  28.774 |                 28.774 |                   -143.129 |                      -161.363 |                  -147.651 |                  -139.167 |                   117 |                       -113.623 |                    70 |                        -80.014 | False             |
|                  14 | T02_8BAR_BREAK                |               166 |                  29.518 |                 29.518 |                   -140.674 |                      -161.527 |                  -139.162 |                  -141.982 |                    95 |                        -90.372 |                    57 |                        -81.052 | False             |
|                  15 | T05_TWO_BAR_HIGHVOL           |                90 |                  30     |                 30     |                   -134.027 |                      -162.176 |                  -140.815 |                  -125.915 |                    56 |                       -118     |                    15 |                        -58.639 | False             |
|                  16 | R03_4H_SWEEP                  |               137 |                  29.197 |                 29.197 |                   -139.14  |                      -162.276 |                  -128.794 |                  -152.819 |                    54 |                        -79.641 |                    49 |                       -106.276 | False             |
|                  17 | B02_TRANSITION_BREAK          |               154 |                  29.87  |                 29.87  |                   -141.028 |                      -162.746 |                  -128.112 |                  -153.29  |                    74 |                       -128.325 |                    42 |                       -121.745 | False             |
|                  18 | M01_RECLAIM_HIGHVOL           |                52 |                  32.692 |                 32.692 |                   -125.153 |                      -163.486 |                  -166.412 |                   -77.018 |                    35 |                        -96.467 |                     8 |                       -158.628 | False             |
|                  19 | R02_BOLLINGER_REENTRY         |               149 |                  28.188 |                 28.859 |                   -142.225 |                      -164.236 |                  -132.14  |                  -154.239 |                    65 |                        -89.054 |                    50 |                        -85.366 | False             |
|                  20 | B01_SQUEEZE_IGNITION          |               279 |                  26.882 |                 26.882 |                   -149.534 |                      -165.258 |                  -135.791 |                  -161.526 |                   141 |                       -112.17  |                    84 |                        -76.747 | False             |
|                  21 | R02_BOLLINGER_REENTRY_HIGHVOL |                36 |                  33.333 |                 33.333 |                   -119.447 |                      -165.672 |                   -98.678 |                  -166.65  |                    26 |                       -110.781 |                     2 |                       -193.239 | False             |
|                  22 | T04_STRONG_CONT_HIGHVOL       |                51 |                  31.373 |                 31.373 |                   -127.774 |                      -166.488 |                  -135.775 |                  -117.227 |                    32 |                       -125.954 |                     7 |                       -113.826 | False             |
|                  23 | T03_INSIDE_RELEASE_HIGHVOL    |                29 |                  34.483 |                 34.483 |                   -120.713 |                      -173.274 |                   -69.177 |                  -168.814 |                    23 |                       -139.628 |                     3 |                          3.436 | False             |
|                  24 | B01_SQUEEZE_IGNITION_HIGHVOL  |                99 |                  24.242 |                 24.242 |                   -149.958 |                      -175.256 |                  -153.019 |                  -146.286 |                    61 |                       -108.275 |                    11 |                        -59.674 | False             |
|                  25 | B02_TRANSITION_BREAK_HIGHVOL  |                44 |                  20.455 |                 20.455 |                   -161.81  |                      -197.995 |                  -140.002 |                  -193.31  |                    30 |                       -101.041 |                     4 |                       -124.484 | False             |

## Top candidates by training-only score — chronological period audits

| candidate                   |   2025_rank | period       |   trades |   tp_hit_first |   tp_first_pct |   net_win_pct |   mean_net_BTC_points |   net_account_return_pct |
|:----------------------------|------------:|:-------------|---------:|---------------:|---------------:|--------------:|----------------------:|-------------------------:|
| V01_EXHAUSTION_FADE_HIGHVOL |           1 | 2025_H1      |       29 |             13 |         44.828 |        44.828 |               -82.689 |                  -2.5905 |
| V01_EXHAUSTION_FADE_HIGHVOL |           1 | 2025_H2      |       16 |              9 |         56.25  |        56.25  |               -53.898 |                  -0.8142 |
| V01_EXHAUSTION_FADE_HIGHVOL |           1 | 2025_ALL     |       45 |             22 |         48.889 |        48.889 |               -72.452 |                  -3.3836 |
| V01_EXHAUSTION_FADE_HIGHVOL |           1 | 2026_H1_SEEN |       23 |              6 |         26.087 |        26.087 |              -113.542 |                  -3.7713 |
| V01_EXHAUSTION_FADE_HIGHVOL |           1 | 2026_H2_SEEN |        3 |              3 |        100     |       100     |                96.396 |                   0.3653 |
| V01_EXHAUSTION_FADE_HIGHVOL |           1 | ALL          |       71 |             31 |         43.662 |        43.662 |               -78.629 |                  -6.6876 |
| R01_12BAR_SWEEP_HIGHVOL     |           2 | 2025_H1      |       21 |             11 |         52.381 |        52.381 |               -60.97  |                  -1.4037 |
| R01_12BAR_SWEEP_HIGHVOL     |           2 | 2025_H2      |       10 |              4 |         40     |        40     |              -100.791 |                  -1.1053 |
| R01_12BAR_SWEEP_HIGHVOL     |           2 | 2025_ALL     |       31 |             15 |         48.387 |        48.387 |               -73.816 |                  -2.4935 |
| R01_12BAR_SWEEP_HIGHVOL     |           2 | 2026_H1_SEEN |       16 |              6 |         37.5   |        37.5   |               -77.678 |                  -1.82   |
| R01_12BAR_SWEEP_HIGHVOL     |           2 | 2026_H2_SEEN |        3 |              1 |         33.333 |        33.333 |               -90.511 |                  -0.4593 |
| R01_12BAR_SWEEP_HIGHVOL     |           2 | ALL          |       50 |             22 |         44     |        44     |               -76.053 |                  -4.7078 |
| D00_FIXED_CLOCK_BENCHMARK   |           3 | 2025_H1      |      178 |             76 |         42.697 |        42.697 |               -93.963 |                 -15.9723 |
| D00_FIXED_CLOCK_BENCHMARK   |           3 | 2025_H2      |      183 |             60 |         32.787 |        32.787 |              -138.141 |                 -20.9587 |
| D00_FIXED_CLOCK_BENCHMARK   |           3 | 2025_ALL     |      361 |            136 |         37.673 |        37.673 |              -116.358 |                 -33.5834 |
| D00_FIXED_CLOCK_BENCHMARK   |           3 | 2026_H1_SEEN |      181 |             66 |         36.464 |        36.464 |               -86.323 |                 -18.671  |
| D00_FIXED_CLOCK_BENCHMARK   |           3 | 2026_H2_SEEN |      122 |             41 |         33.607 |        35.246 |               -87.954 |                 -13.5921 |
| D00_FIXED_CLOCK_BENCHMARK   |           3 | ALL          |      664 |            243 |         36.596 |        36.898 |              -102.952 |                 -53.3259 |
| T01_PULLBACK_BREAK_HIGHVOL  |           4 | 2025_H1      |       62 |             18 |         29.032 |        29.032 |              -133.734 |                  -8.5013 |
| T01_PULLBACK_BREAK_HIGHVOL  |           4 | 2025_H2      |       43 |             21 |         48.837 |        48.837 |               -81.89  |                  -3.7028 |
| T01_PULLBACK_BREAK_HIGHVOL  |           4 | 2025_ALL     |      105 |             39 |         37.143 |        37.143 |              -112.503 |                 -11.8894 |
| T01_PULLBACK_BREAK_HIGHVOL  |           4 | 2026_H1_SEEN |       61 |             18 |         29.508 |        29.508 |              -104.593 |                  -8.8469 |
| T01_PULLBACK_BREAK_HIGHVOL  |           4 | 2026_H2_SEEN |       15 |              4 |         26.667 |        26.667 |              -116.993 |                  -2.1178 |
| T01_PULLBACK_BREAK_HIGHVOL  |           4 | ALL          |      181 |             61 |         33.702 |        33.702 |              -110.209 |                 -21.3853 |
| V01_EXHAUSTION_FADE         |           5 | 2025_H1      |       68 |             22 |         32.353 |        32.353 |              -125.208 |                  -8.5813 |
| V01_EXHAUSTION_FADE         |           5 | 2025_H2      |       81 |             34 |         41.975 |        41.975 |              -109.578 |                  -7.9663 |
| V01_EXHAUSTION_FADE         |           5 | 2025_ALL     |      149 |             56 |         37.584 |        37.584 |              -116.711 |                 -15.864  |
| V01_EXHAUSTION_FADE         |           5 | 2026_H1_SEEN |       73 |             23 |         31.507 |        31.507 |              -101.289 |                  -9.4407 |
| V01_EXHAUSTION_FADE         |           5 | 2026_H2_SEEN |       47 |             17 |         36.17  |        38.298 |               -83.403 |                  -5.1659 |
| V01_EXHAUSTION_FADE         |           5 | ALL          |      269 |             96 |         35.688 |        36.059 |              -106.706 |                 -27.7431 |
| T01_PULLBACK_BREAK          |           6 | 2025_H1      |      115 |             33 |         28.696 |        29.565 |              -134.862 |                 -15.0199 |
| T01_PULLBACK_BREAK          |           6 | 2025_H2      |      122 |             51 |         41.803 |        41.803 |              -110.693 |                 -12.0283 |
| T01_PULLBACK_BREAK          |           6 | 2025_ALL     |      237 |             84 |         35.443 |        35.865 |              -122.421 |                 -25.2416 |
| T01_PULLBACK_BREAK          |           6 | 2026_H1_SEEN |      125 |             42 |         33.6   |        34.4   |               -93.576 |                 -14.9108 |
| T01_PULLBACK_BREAK          |           6 | 2026_H2_SEEN |       75 |             28 |         37.333 |        38.667 |               -81.602 |                  -8.0945 |
| T01_PULLBACK_BREAK          |           6 | ALL          |      437 |            154 |         35.24  |        35.927 |              -107.164 |                 -41.5377 |
| T03_INSIDE_RELEASE          |           7 | 2025_H1      |       39 |             17 |         43.59  |        43.59  |               -93.29  |                  -3.8125 |
| T03_INSIDE_RELEASE          |           7 | 2025_H2      |       49 |             13 |         26.531 |        28.571 |              -150.369 |                  -6.6894 |
| T03_INSIDE_RELEASE          |           7 | 2025_ALL     |       88 |             30 |         34.091 |        35.227 |              -125.073 |                 -10.2469 |
| T03_INSIDE_RELEASE          |           7 | 2026_H1_SEEN |       52 |             16 |         30.769 |        30.769 |              -105.765 |                  -7.4194 |
| T03_INSIDE_RELEASE          |           7 | 2026_H2_SEEN |       21 |              8 |         38.095 |        38.095 |               -80.629 |                  -2.2639 |
| T03_INSIDE_RELEASE          |           7 | ALL          |      161 |             54 |         33.54  |        34.161 |              -113.04  |                 -18.7872 |
| R01_12BAR_SWEEP             |           8 | 2025_H1      |       78 |             26 |         33.333 |        33.333 |              -121.097 |                  -9.3102 |
| R01_12BAR_SWEEP             |           8 | 2025_H2      |       58 |             17 |         29.31  |        29.31  |              -145.805 |                  -7.5467 |
| R01_12BAR_SWEEP             |           8 | 2025_ALL     |      136 |             43 |         31.618 |        31.618 |              -131.634 |                 -16.1543 |
| R01_12BAR_SWEEP             |           8 | 2026_H1_SEEN |       55 |             20 |         36.364 |        36.364 |               -88.269 |                  -6.2809 |
| R01_12BAR_SWEEP             |           8 | 2026_H2_SEEN |       48 |             12 |         25     |        29.167 |              -107.739 |                  -6.7369 |
| R01_12BAR_SWEEP             |           8 | ALL          |      239 |             75 |         31.381 |        32.218 |              -116.856 |                 -26.7144 |
| T04_STRONG_CONT             |           9 | 2025_H1      |       65 |             19 |         29.231 |        29.231 |              -132.625 |                  -8.7612 |
| T04_STRONG_CONT             |           9 | 2025_H2      |       69 |             24 |         34.783 |        34.783 |              -131.575 |                  -8.2209 |
| T04_STRONG_CONT             |           9 | 2025_ALL     |      134 |             43 |         32.09  |        32.09  |              -132.085 |                 -16.2619 |
| T04_STRONG_CONT             |           9 | 2026_H1_SEEN |       75 |             27 |         36     |        36     |               -90.353 |                  -8.8303 |
| T04_STRONG_CONT             |           9 | 2026_H2_SEEN |       44 |             18 |         40.909 |        40.909 |               -75.042 |                  -4.3427 |
| T04_STRONG_CONT             |           9 | ALL          |      253 |             88 |         34.783 |        34.783 |              -109.793 |                 -26.9716 |
| R03_4H_SWEEP_HIGHVOL        |          10 | 2025_H1      |       22 |              9 |         40.909 |        40.909 |               -95.098 |                  -2.2757 |
| R03_4H_SWEEP_HIGHVOL        |          10 | 2025_H2      |       10 |              3 |         30     |        30     |              -130.763 |                  -1.3915 |
| R03_4H_SWEEP_HIGHVOL        |          10 | 2025_ALL     |       32 |             12 |         37.5   |        37.5   |              -106.243 |                  -3.6356 |
| R03_4H_SWEEP_HIGHVOL        |          10 | 2026_H1_SEEN |       17 |              5 |         29.412 |        29.412 |              -102.176 |                  -2.5254 |
| R03_4H_SWEEP_HIGHVOL        |          10 | 2026_H2_SEEN |        4 |              2 |         50     |        50     |               -39.525 |                  -0.2766 |
| R03_4H_SWEEP_HIGHVOL        |          10 | ALL          |       53 |             19 |         35.849 |        35.849 |               -99.903 |                  -6.329  |
| M01_RECLAIM                 |          11 | 2025_H1      |       67 |             14 |         20.896 |        20.896 |              -159.272 |                 -10.3639 |
| M01_RECLAIM                 |          11 | 2025_H2      |       82 |             33 |         40.244 |        40.244 |              -115.467 |                  -8.4619 |
| M01_RECLAIM                 |          11 | 2025_ALL     |      149 |             47 |         31.544 |        31.544 |              -135.165 |                 -17.9488 |
| M01_RECLAIM                 |          11 | 2026_H1_SEEN |       81 |             28 |         34.568 |        35.802 |               -90.206 |                  -9.5251 |
| M01_RECLAIM                 |          11 | 2026_H2_SEEN |       49 |             18 |         36.735 |        36.735 |               -84.002 |                  -5.3521 |
| M01_RECLAIM                 |          11 | ALL          |      279 |             93 |         33.333 |        33.692 |              -113.127 |                 -29.7374 |
| T02_8BAR_BREAK_HIGHVOL      |          12 | 2025_H1      |       33 |             11 |         33.333 |        33.333 |              -118.771 |                  -4.1327 |
| T02_8BAR_BREAK_HIGHVOL      |          12 | 2025_H2      |       28 |              9 |         32.143 |        32.143 |              -130.984 |                  -3.628  |
| T02_8BAR_BREAK_HIGHVOL      |          12 | 2025_ALL     |       61 |             20 |         32.787 |        32.787 |              -124.377 |                  -7.6107 |
| T02_8BAR_BREAK_HIGHVOL      |          12 | 2026_H1_SEEN |       41 |             12 |         29.268 |        29.268 |              -104.719 |                  -6.043  |
| T02_8BAR_BREAK_HIGHVOL      |          12 | 2026_H2_SEEN |       12 |              4 |         33.333 |        33.333 |               -99.436 |                  -1.5151 |
| T02_8BAR_BREAK_HIGHVOL      |          12 | ALL          |      114 |             36 |         31.579 |        31.579 |              -114.682 |                 -14.5091 |

## Selected candidate or exploratory leader — 1× net-account monthly PnL

Selected candidate (when qualifying): None

Exploratory leader (not approved when no qualification): V01_EXHAUSTION_FADE_HIGHVOL

### Simulated actual account

|                                        | 0                                                                            |
|:---------------------------------------|:-----------------------------------------------------------------------------|
| strategy                               | h1_ema20_50_m15_prior4_ema20_touch_previous_high_break_200tp_100sl_1x        |
| trades                                 | 71                                                                           |
| longs                                  | 36                                                                           |
| shorts                                 | 35                                                                           |
| tp_before_sl_count                     | 31                                                                           |
| sl_before_tp_count                     | 40                                                                           |
| time_or_day_exit_count                 | 0                                                                            |
| tp_first_pct_of_trades                 | 43.662                                                                       |
| net_win_trades                         | 31                                                                           |
| net_loss_trades                        | 40                                                                           |
| net_trade_win_rate_pct                 | 43.662                                                                       |
| days_in_sample                         | 667                                                                          |
| net_profitable_days                    | 31                                                                           |
| net_losing_days                        | 40                                                                           |
| no_trade_days                          | 596                                                                          |
| tp_days_pct_all_calendar               | 4.6477                                                                       |
| positive_months                        | 3                                                                            |
| negative_months                        | 12                                                                           |
| flat_months                            | 7                                                                            |
| capital_start_usd                      | 10000.0                                                                      |
| capital_end_usd                        | 9331.24                                                                      |
| full_period_compounded_net_account_pct | -6.68759                                                                     |
| mean_after_fee_BTC_price_points        | -78.6286                                                                     |
| mean_gross_BTC_price_points            | 30.9859                                                                      |
| total_gross_usd                        | 227.06                                                                       |
| total_fee_gst_usd                      | 812.34                                                                       |
| total_slippage_usd                     | 83.48                                                                        |
| total_net_usd                          | -668.76                                                                      |
| net_profit_factor                      | 0.322                                                                        |
| trade_close_max_drawdown_pct           | 7.0273                                                                       |
| 2025_net_compounded_pct                | -3.38358                                                                     |
| 2026_JanOct_net_compounded_pct         | -3.41972                                                                     |
| research_warning                       | 2026 previously researched in BTC-Analysis; this is NOT an untouched holdout |
| conclusion_warning                     | A 200-point daily profit target is not a daily profit guarantee              |

### Monthly

| month_ist   |   days |   entries |   tp_hit_first |   sl_hit_first |   time_or_day_exit |   winning_days |   losing_days |   no_trade_days |   compounded_net_account_pct |   sum_of_daily_net_usd | archive_boundary_incomplete   |
|:------------|-------:|----------:|---------------:|---------------:|-------------------:|---------------:|--------------:|----------------:|-----------------------------:|-----------------------:|:------------------------------|
| 2025-01     |     30 |         8 |              4 |              4 |                  0 |              4 |             4 |              22 |                    -0.629367 |               -62.9367 | True                          |
| 2025-02     |     28 |         4 |              2 |              2 |                  0 |              2 |             2 |              24 |                    -0.322651 |               -32.0621 | False                         |
| 2025-03     |     31 |         7 |              4 |              3 |                  0 |              4 |             3 |              24 |                    -0.317386 |               -31.4371 | False                         |
| 2025-04     |     30 |         8 |              3 |              5 |                  0 |              3 |             5 |              22 |                    -0.898006 |               -88.6652 | False                         |
| 2025-05     |     31 |         2 |              0 |              2 |                  0 |              0 |             2 |              29 |                    -0.449147 |               -43.9486 | False                         |
| 2025-06     |     30 |         0 |              0 |              0 |                  0 |              0 |             0 |              30 |                     0        |                 0      | False                         |
| 2025-07     |     31 |         0 |              0 |              0 |                  0 |              0 |             0 |              31 |                     0        |                 0      | False                         |
| 2025-08     |     31 |         0 |              0 |              0 |                  0 |              0 |             0 |              31 |                     0        |                 0      | False                         |
| 2025-09     |     30 |         0 |              0 |              0 |                  0 |              0 |             0 |              30 |                     0        |                 0      | False                         |
| 2025-10     |     31 |         4 |              2 |              2 |                  0 |              2 |             2 |              27 |                    -0.336765 |               -32.8041 | False                         |
| 2025-11     |     30 |         4 |              2 |              2 |                  0 |              2 |             2 |              26 |                    -0.258437 |               -25.0895 | False                         |
| 2025-12     |     31 |         8 |              5 |              3 |                  0 |              5 |             3 |              23 |                    -0.221158 |               -21.4149 | False                         |
| 2026-01     |     31 |         0 |              0 |              0 |                  0 |              0 |             0 |              31 |                     0        |                 0      | False                         |
| 2026-02     |     28 |         9 |              3 |              6 |                  0 |              3 |             6 |              19 |                    -1.21259  |              -117.156  | False                         |
| 2026-03     |     31 |         7 |              1 |              6 |                  0 |              1 |             6 |              24 |                    -1.49739  |              -142.918  | False                         |
| 2026-04     |     30 |         3 |              1 |              2 |                  0 |              1 |             2 |              27 |                    -0.413571 |               -38.8821 | False                         |
| 2026-05     |     31 |         0 |              0 |              0 |                  0 |              0 |             0 |              31 |                     0        |                 0      | False                         |
| 2026-06     |     30 |         4 |              1 |              3 |                  0 |              1 |             3 |              26 |                    -0.698642 |               -65.4117 | False                         |
| 2026-07     |     31 |         0 |              0 |              0 |                  0 |              0 |             0 |              31 |                     0        |                 0      | False                         |
| 2026-08     |     31 |         1 |              1 |              0 |                  0 |              1 |             0 |              30 |                     0.12614  |                11.7275 | False                         |
| 2026-09     |     30 |         1 |              1 |              0 |                  0 |              1 |             0 |              29 |                     0.11696  |                10.8878 | False                         |
| 2026-10     |     30 |         1 |              1 |              0 |                  0 |              1 |             0 |              29 |                     0.121795 |                11.3512 | True                          |

## Important limits

- One or fewer trades opened per IST calendar date per independently tested candidate
- All strategy candidates use the same fixed 200 raw point TP / 100 raw point SL at 1x and 1m stop-first execution
- Regime classification is based ONLY on already closed 1h ADX14 + EMA20/50; no incomplete 1h current candle
- Stricter HIGHVOL variant checks completed 1h ATR14 / BTC close >=0.7%
- 2025 only ranks; 2026 checks are retrospective SEEN historical data due earlier research; NOT untouched validation
- No funding, orderbook, bid/ask beyond assumed 5pt slippage, lot feasibility, or mark liquidation
- Historical train sample standard-error bound is heuristic and not multiple-testing or serial-dependence adjusted
- January 2025 (partial Jan1 IST) and October 2026 (Oct31 IST missing) are incomplete archive-boundary months
- No assumption that trading every day or net profit every day is achievable
