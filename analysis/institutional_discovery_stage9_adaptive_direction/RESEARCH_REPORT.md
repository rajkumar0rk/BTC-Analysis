# Stage 9 — Adaptive entry discovery from closed BTC candles

## Method
Any-time model with NO hour, weekday or session inputs. 33 completed-bar
price/volume/volatility features from 5m BTCUSD futures candles.
Train Jan-Sep 2025; select cutoff Oct-Dec 2025; report 2026
chronologically without adjusting decisions after seeing later results.
Classification goal: net +200 before -100 within 30m, stop-first.

## Prediction skill
| side   | period          |     n |   hit_rate |    auc |   average_precision |   mean_pred |   top_decile_label_rate |
|:-------|:----------------|------:|-----------:|-------:|--------------------:|------------:|------------------------:|
| LONG   | train           | 78286 |      12.28 | 0.6157 |              0.1814 |      0.1229 |                   22    |
| LONG   | select_2025Q4   | 26264 |      14.66 | 0.5789 |              0.1811 |      0.1248 |                   20.34 |
| LONG   | check_2026H1    | 51916 |      11.15 | 0.586  |              0.1508 |      0.1249 |                   19.24 |
| LONG   | recheck_2026H2  | 35017 |       7.72 | 0.6307 |              0.1286 |      0.1216 |                   15.73 |
| LONG   | november_recent |  4471 |      10.22 | 0.6256 |              0.1508 |      0.1247 |                   17.82 |
| SHORT  | train           | 78286 |      12.44 | 0.629  |              0.192  |      0.1244 |                   22.67 |
| SHORT  | select_2025Q4   | 26264 |      15.38 | 0.5674 |              0.1884 |      0.1262 |                   22.36 |
| SHORT  | check_2026H1    | 51916 |      12.37 | 0.597  |              0.165  |      0.1266 |                   19.11 |
| SHORT  | recheck_2026H2  | 35017 |       7.55 | 0.6513 |              0.1246 |      0.1233 |                   15.03 |
| SHORT  | november_recent |  4471 |      14.05 | 0.6292 |              0.2197 |      0.128  |                   26.2  |

## Chosen probability cutoff
| side   |   selected_threshold |   selection_trades |   selection_net |
|:-------|---------------------:|-------------------:|----------------:|
| LONG   |                 0.2  |                417 |         -128.42 |
| SHORT  |                 0.25 |                 32 |          -91.49 |

## Independently replayed net trading outcomes
| side   | period          | cutoff_model      |   threshold | tp_model   |   trades |   mean_net_pts |   profit_factor |   wins |   losses |   win_pct |   sum_net_pts |   whatif_avg_pts |
|:-------|:----------------|:------------------|------------:|:-----------|---------:|---------------:|----------------:|-------:|---------:|----------:|--------------:|-----------------:|
| LONG   | train           | trained_threshold |     0.2     | gross200   |     1143 |        -113.93 |           0.19  |    433 |      710 |     37.88 |    -130216    |           -54.09 |
| LONG   | train           | trained_threshold |     0.2     | net200     |     1077 |        -100.17 |           0.364 |    320 |      757 |     29.71 |    -107886    |           -40.46 |
| LONG   | train           | baseline_top10pct |     0.16447 | gross200   |     6216 |        -125.1  |           0.16  |   2076 |     4140 |     33.4  |    -777623    |           -65.7  |
| LONG   | train           | baseline_top10pct |     0.16447 | net200     |     5472 |        -119.34 |           0.281 |   1358 |     4114 |     24.82 |    -653015    |           -60.06 |
| LONG   | select_2025Q4   | trained_threshold |     0.2     | gross200   |      431 |        -130.68 |           0.147 |    139 |      292 |     32.25 |     -56323.6  |           -71.28 |
| LONG   | select_2025Q4   | trained_threshold |     0.2     | net200     |      417 |        -128.42 |           0.256 |     96 |      321 |     23.02 |     -53550.7  |           -69.03 |
| LONG   | select_2025Q4   | baseline_top10pct |     0.16447 | gross200   |     2267 |        -132.43 |           0.143 |    700 |     1567 |     30.88 |    -300218    |           -73.28 |
| LONG   | select_2025Q4   | baseline_top10pct |     0.16447 | net200     |     2015 |        -128.89 |           0.249 |    455 |     1560 |     22.58 |    -259706    |           -69.74 |
| LONG   | check_2026H1    | trained_threshold |     0.2     | gross200   |      813 |         -96.9  |           0.25  |    263 |      550 |     32.35 |     -78778    |           -52.38 |
| LONG   | check_2026H1    | trained_threshold |     0.2     | net200     |      765 |        -101.25 |           0.297 |    183 |      582 |     23.92 |     -77453.7  |           -56.76 |
| LONG   | check_2026H1    | baseline_top10pct |     0.16447 | gross200   |     3877 |         -95.02 |           0.253 |   1250 |     2627 |     32.24 |    -368379    |           -51.11 |
| LONG   | check_2026H1    | baseline_top10pct |     0.16447 | net200     |     3446 |         -95.9  |           0.312 |    848 |     2598 |     24.61 |    -330464    |           -52.1  |
| LONG   | recheck_2026H2  | trained_threshold |     0.2     | gross200   |      509 |         -83.17 |           0.289 |    181 |      328 |     35.56 |     -42334.3  |           -39.39 |
| LONG   | recheck_2026H2  | trained_threshold |     0.2     | net200     |      468 |         -79.71 |           0.373 |    137 |      331 |     29.27 |     -37303.7  |           -35.88 |
| LONG   | recheck_2026H2  | baseline_top10pct |     0.16447 | gross200   |     2201 |         -95.05 |           0.235 |    687 |     1514 |     31.21 |    -209203    |           -50.91 |
| LONG   | recheck_2026H2  | baseline_top10pct |     0.16447 | net200     |     1927 |         -93.39 |           0.296 |    484 |     1443 |     25.12 |    -179959    |           -49.29 |
| LONG   | november_recent | trained_threshold |     0.2     | gross200   |       75 |        -119.94 |           0.17  |     18 |       57 |     24    |      -8995.69 |           -75.9  |
| LONG   | november_recent | trained_threshold |     0.2     | net200     |       74 |        -114.17 |           0.249 |     15 |       59 |     20.27 |      -8448.61 |           -70.15 |
| LONG   | november_recent | baseline_top10pct |     0.16447 | gross200   |      374 |        -111.32 |           0.195 |    100 |      274 |     26.74 |     -41632.8  |           -68.35 |
| LONG   | november_recent | baseline_top10pct |     0.16447 | net200     |      345 |        -109.5  |           0.255 |     71 |      274 |     20.58 |     -37776.1  |           -66.54 |
| SHORT  | train           | trained_threshold |     0.25    | gross200   |       98 |         -45.14 |           0.494 |     60 |       38 |     61.22 |      -4423.38 |            14.25 |
| SHORT  | train           | trained_threshold |     0.25    | net200     |       93 |         -17.92 |           0.839 |     45 |       48 |     48.39 |      -1666.28 |            41.44 |
| SHORT  | train           | baseline_top10pct |     0.17554 | gross200   |     6057 |        -120.01 |           0.172 |   2131 |     3926 |     35.18 |    -726890    |           -60.52 |
| SHORT  | train           | baseline_top10pct |     0.17554 | net200     |     5227 |        -115.6  |           0.292 |   1334 |     3893 |     25.52 |    -604260    |           -56.23 |
| SHORT  | select_2025Q4   | trained_threshold |     0.25    | gross200   |       36 |         -95.89 |           0.265 |     15 |       21 |     41.67 |      -3452.02 |           -40.45 |
| SHORT  | select_2025Q4   | trained_threshold |     0.25    | net200     |       32 |         -91.49 |           0.389 |     10 |       22 |     31.25 |      -2927.75 |           -35.58 |
| SHORT  | select_2025Q4   | baseline_top10pct |     0.17554 | gross200   |     2145 |        -124.57 |           0.16  |    724 |     1421 |     33.75 |    -267211    |           -65.3  |
| SHORT  | select_2025Q4   | baseline_top10pct |     0.17554 | net200     |     1886 |        -119.48 |           0.282 |    467 |     1419 |     24.76 |    -225336    |           -60.35 |
| SHORT  | check_2026H1    | trained_threshold |     0.25    | gross200   |       63 |         -96.18 |           0.237 |     20 |       43 |     31.75 |      -6059.36 |           -50.79 |
| SHORT  | check_2026H1    | trained_threshold |     0.25    | net200     |       63 |         -86.49 |           0.37  |     16 |       47 |     25.4  |      -5448.62 |           -41.1  |
| SHORT  | check_2026H1    | baseline_top10pct |     0.17554 | gross200   |     3692 |        -100.88 |           0.233 |   1135 |     2557 |     30.74 |    -372454    |           -56.95 |
| SHORT  | check_2026H1    | baseline_top10pct |     0.17554 | net200     |     3237 |         -99.74 |           0.298 |    781 |     2456 |     24.13 |    -322866    |           -55.85 |
| SHORT  | recheck_2026H2  | trained_threshold |     0.25    | gross200   |       32 |        -129.17 |           0.124 |      6 |       26 |     18.75 |      -4133.53 |           -84.71 |
| SHORT  | recheck_2026H2  | trained_threshold |     0.25    | net200     |       32 |        -115.06 |           0.219 |      6 |       26 |     18.75 |      -3682.05 |           -70.61 |
| SHORT  | recheck_2026H2  | baseline_top10pct |     0.17554 | gross200   |     2105 |        -100.53 |           0.215 |    607 |     1498 |     28.84 |    -211626    |           -56.37 |
| SHORT  | recheck_2026H2  | baseline_top10pct |     0.17554 | net200     |     1859 |        -100.76 |           0.265 |    420 |     1439 |     22.59 |    -187318    |           -56.64 |
| SHORT  | november_recent | trained_threshold |     0.25    | gross200   |       14 |         -26.99 |           0.683 |      8 |        6 |     57.14 |       -377.8  |            17.2  |
| SHORT  | november_recent | trained_threshold |     0.25    | net200     |       14 |          13.04 |           1.15  |      7 |        7 |     50    |        182.61 |            57.21 |
| SHORT  | november_recent | baseline_top10pct |     0.17554 | gross200   |      394 |         -71.93 |           0.364 |    156 |      238 |     39.59 |     -28339.9  |           -29.07 |
| SHORT  | november_recent | baseline_top10pct |     0.17554 | net200     |      342 |         -70.29 |           0.453 |    106 |      236 |     30.99 |     -24037.5  |           -27.27 |

## Exploratory feature importance by 2025 selection permutation
| side   | feature           |   AP_drop |
|:-------|:------------------|----------:|
| SHORT  | range_regime      |   0.02622 |
| LONG   | range_regime      |   0.01252 |
| SHORT  | wick_down_frac    |   0.00554 |
| SHORT  | wick_up_frac      |   0.00497 |
| SHORT  | trend_24          |   0.00437 |
| SHORT  | trend_12          |   0.00424 |
| LONG   | prior_close_loc   |   0.00357 |
| LONG   | range_ratio       |   0.00349 |
| LONG   | prior_range_ratio |   0.0028  |
| SHORT  | prior_range_ratio |   0.00154 |
| SHORT  | range_ratio       |   0.0013  |
| SHORT  | range_accel       |   0.00105 |
| SHORT  | volume_24         |   0.00086 |
| LONG   | wick_up_frac      |   0.00079 |
| LONG   | trend_3           |   0.00066 |
| SHORT  | range_3           |   0.00061 |
| LONG   | trend_24          |   0.0005  |
| SHORT  | range_2           |   0.00044 |
| LONG   | range_accel       |   0.00043 |
| LONG   | range_12          |   0.00039 |

## Interpretation
- More frequent +200 gross excursions do NOT guarantee a positive net result.
- Any positive results with tiny independent trade counts are not validated.
- All trades have known-at-entry features; zero next-bar lookahead.
- 0.05% taker per side, GST 18%, adverse 5 pts per side included.
- Scalper offer sensitivity is separate, not assumed qualified.
- No 2026 result should be treated as an untouched holdout.
- 2026 periods are research-exposed, not independent virgin holdouts
- Target labels of 5m signals overlap and overstate effective sample size
- 1m OHLC stop-first; no historical spread, fills, impact or funding
- Threshold selection among nine alternatives creates selection bias
- Model probabilities can drift with changes in BTC price/volatility
- No guarantee of profitability or zero losses
