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
| LONG   | train           | 78282 |      18.94 | 0.5876 |              0.2453 |      0.1894 |                   28.01 |
| LONG   | select_2025Q4   | 26265 |      19.44 | 0.5285 |              0.2148 |      0.19   |                   23.43 |
| LONG   | check_2026H1    | 51916 |      13.7  | 0.5672 |              0.1702 |      0.1895 |                   19.69 |
| LONG   | recheck_2026H2  | 35304 |      10.88 | 0.5664 |              0.1381 |      0.1886 |                   15.75 |
| LONG   | november_recent |  4801 |      11.98 | 0.5551 |              0.1464 |      0.1892 |                   15.96 |
| SHORT  | train           | 78282 |      19.28 | 0.5886 |              0.2543 |      0.1928 |                   29.56 |
| SHORT  | select_2025Q4   | 26265 |      20.01 | 0.5374 |              0.2258 |      0.194  |                   24.55 |
| SHORT  | check_2026H1    | 51916 |      15    | 0.5691 |              0.183  |      0.1946 |                   20.99 |
| SHORT  | recheck_2026H2  | 35304 |      10.49 | 0.596  |              0.1446 |      0.1942 |                   17.09 |
| SHORT  | november_recent |  4801 |      15.37 | 0.5915 |              0.2191 |      0.1961 |                   26.75 |

## Chosen probability cutoff
| side   |   selected_threshold |   selection_trades |   selection_net |
|:-------|---------------------:|-------------------:|----------------:|
| LONG   |                 0.25 |                164 |         -117.75 |
| SHORT  |                 0.25 |                786 |         -100.7  |

## Independently replayed net trading outcomes
| side   | period          | cutoff_model      |   threshold | tp_model   |   trades |   mean_net_pts |   profit_factor |   wins |   losses |   win_pct |   sum_net_pts |   whatif_avg_pts |
|:-------|:----------------|:------------------|------------:|:-----------|---------:|---------------:|----------------:|-------:|---------:|----------:|--------------:|-----------------:|
| LONG   | train           | trained_threshold |     0.25    | gross200   |      345 |         -68.08 |           0.391 |    157 |      188 |     45.51 |     -23489.2  |           -20.6  |
| LONG   | train           | trained_threshold |     0.25    | net200     |      337 |         -45.25 |           0.635 |    134 |      203 |     39.76 |     -15249.1  |             2.3  |
| LONG   | train           | baseline_top10pct |     0.21228 | gross200   |     6736 |         -95.44 |           0.261 |   2509 |     4227 |     37.25 |    -642851    |           -46.46 |
| LONG   | train           | baseline_top10pct |     0.21228 | net200     |     6242 |         -87.91 |           0.392 |   1842 |     4400 |     29.51 |    -548752    |           -38.98 |
| LONG   | select_2025Q4   | trained_threshold |     0.25    | gross200   |      167 |        -127.85 |           0.155 |     53 |      114 |     31.74 |     -21351.1  |           -70.19 |
| LONG   | select_2025Q4   | trained_threshold |     0.25    | net200     |      164 |        -117.75 |           0.294 |     41 |      123 |     25    |     -19311.8  |           -60.25 |
| LONG   | select_2025Q4   | baseline_top10pct |     0.21228 | gross200   |     2617 |        -123.81 |           0.165 |    871 |     1746 |     33.28 |    -324004    |           -66.08 |
| LONG   | select_2025Q4   | baseline_top10pct |     0.21228 | net200     |     2437 |        -120.37 |           0.281 |    595 |     1842 |     24.42 |    -293341    |           -62.7  |
| LONG   | check_2026H1    | trained_threshold |     0.25    | gross200   |      235 |         -87.16 |           0.289 |     72 |      163 |     30.64 |     -20481.7  |           -49.97 |
| LONG   | check_2026H1    | trained_threshold |     0.25    | net200     |      233 |         -82.57 |           0.367 |     61 |      172 |     26.18 |     -19238.9  |           -45.38 |
| LONG   | check_2026H1    | baseline_top10pct |     0.21228 | gross200   |     4185 |         -82.93 |           0.3   |   1353 |     2832 |     32.33 |    -347043    |           -45.68 |
| LONG   | check_2026H1    | baseline_top10pct |     0.21228 | net200     |     3888 |         -82.08 |           0.355 |   1036 |     2852 |     26.65 |    -319136    |           -44.91 |
| LONG   | recheck_2026H2  | trained_threshold |     0.25    | gross200   |      160 |         -82.38 |           0.293 |     50 |      110 |     31.25 |     -13181.2  |           -45.1  |
| LONG   | recheck_2026H2  | trained_threshold |     0.25    | net200     |      157 |         -74.78 |           0.388 |     43 |      114 |     27.39 |     -11740.9  |           -37.59 |
| LONG   | recheck_2026H2  | baseline_top10pct |     0.21228 | gross200   |     2467 |         -88.09 |           0.258 |    717 |     1750 |     29.06 |    -217319    |           -50.41 |
| LONG   | recheck_2026H2  | baseline_top10pct |     0.21228 | net200     |     2281 |         -86.09 |           0.308 |    554 |     1727 |     24.29 |    -196382    |           -48.49 |
| LONG   | november_recent | trained_threshold |     0.25    | gross200   |       16 |         -84.53 |           0.32  |      5 |       11 |     31.25 |      -1352.47 |           -50.39 |
| LONG   | november_recent | trained_threshold |     0.25    | net200     |       16 |         -97.92 |           0.277 |      3 |       13 |     18.75 |      -1566.73 |           -63.79 |
| LONG   | november_recent | baseline_top10pct |     0.21228 | gross200   |      399 |         -94    |           0.243 |    105 |      294 |     26.32 |     -37505.9  |           -59.94 |
| LONG   | november_recent | baseline_top10pct |     0.21228 | net200     |      371 |         -93.68 |           0.282 |     82 |      289 |     22.1  |     -34756.3  |           -59.59 |
| SHORT  | train           | trained_threshold |     0.25    | gross200   |     1954 |         -74.75 |           0.35  |    860 |     1094 |     44.01 |    -146054    |           -26.1  |
| SHORT  | train           | trained_threshold |     0.25    | net200     |     1880 |         -61.96 |           0.53  |    672 |     1208 |     35.74 |    -116484    |           -13.35 |
| SHORT  | train           | baseline_top10pct |     0.22767 | gross200   |     6813 |         -90.52 |           0.281 |   2680 |     4133 |     39.34 |    -616685    |           -41.03 |
| SHORT  | train           | baseline_top10pct |     0.22767 | net200     |     6336 |         -82.26 |           0.423 |   1977 |     4359 |     31.2  |    -521193    |           -32.79 |
| SHORT  | select_2025Q4   | trained_threshold |     0.25    | gross200   |      809 |        -113.59 |           0.193 |    298 |      511 |     36.84 |     -91893.6  |           -56.29 |
| SHORT  | select_2025Q4   | trained_threshold |     0.25    | net200     |      786 |        -100.7  |           0.363 |    230 |      556 |     29.26 |     -79149    |           -43.34 |
| SHORT  | select_2025Q4   | baseline_top10pct |     0.22767 | gross200   |     2693 |        -118.33 |           0.179 |    943 |     1750 |     35.02 |    -318653    |           -61.01 |
| SHORT  | select_2025Q4   | baseline_top10pct |     0.22767 | net200     |     2512 |        -112.03 |           0.313 |    659 |     1853 |     26.23 |    -281415    |           -54.72 |
| SHORT  | check_2026H1    | trained_threshold |     0.25    | gross200   |     1433 |         -88.55 |           0.277 |    434 |      999 |     30.29 |    -126898    |           -51.47 |
| SHORT  | check_2026H1    | trained_threshold |     0.25    | net200     |     1362 |         -83.98 |           0.352 |    345 |     1017 |     25.33 |    -114375    |           -46.92 |
| SHORT  | check_2026H1    | baseline_top10pct |     0.22767 | gross200   |     4447 |         -82.79 |           0.302 |   1433 |     3014 |     32.22 |    -368157    |           -45.55 |
| SHORT  | check_2026H1    | baseline_top10pct |     0.22767 | net200     |     4090 |         -80.47 |           0.367 |   1086 |     3004 |     26.55 |    -329126    |           -43.27 |
| SHORT  | recheck_2026H2  | trained_threshold |     0.25    | gross200   |      881 |         -83.03 |           0.289 |    277 |      604 |     31.44 |     -73152.6  |           -45.42 |
| SHORT  | recheck_2026H2  | trained_threshold |     0.25    | net200     |      839 |         -85.55 |           0.323 |    214 |      625 |     25.51 |     -71775    |           -47.85 |
| SHORT  | recheck_2026H2  | baseline_top10pct |     0.22767 | gross200   |     2648 |         -82.37 |           0.286 |    813 |     1835 |     30.7  |    -218122    |           -44.76 |
| SHORT  | recheck_2026H2  | baseline_top10pct |     0.22767 | net200     |     2444 |         -83.64 |           0.326 |    607 |     1837 |     24.84 |    -204406    |           -46.07 |
| SHORT  | november_recent | trained_threshold |     0.25    | gross200   |      187 |         -74.17 |           0.358 |     64 |      123 |     34.22 |     -13870.5  |           -39.92 |
| SHORT  | november_recent | trained_threshold |     0.25    | net200     |      174 |         -70.3  |           0.438 |     49 |      125 |     28.16 |     -12231.6  |           -36.07 |
| SHORT  | november_recent | baseline_top10pct |     0.22767 | gross200   |      502 |         -68.85 |           0.381 |    177 |      325 |     35.26 |     -34564.2  |           -34.73 |
| SHORT  | november_recent | baseline_top10pct |     0.22767 | net200     |      452 |         -65.69 |           0.455 |    132 |      320 |     29.2  |     -29690.7  |           -31.51 |

## Exploratory feature importance by 2025 selection permutation
| side   | feature      |   AP_drop |
|:-------|:-------------|----------:|
| SHORT  | range_regime |   0.01533 |
| LONG   | range_regime |   0.01181 |
| LONG   | abs_ret_12   |   0.00785 |
| SHORT  | trend_12     |   0.00608 |
| SHORT  | trend_24     |   0.00263 |
| LONG   | range_ratio  |   0.00225 |
| SHORT  | distance_l24 |   0.00224 |
| SHORT  | range_24     |   0.00189 |
| SHORT  | range_6      |   0.00166 |
| LONG   | range_2      |   0.0016  |
| SHORT  | range_ratio  |   0.00148 |
| LONG   | volume_12    |   0.00145 |
| SHORT  | range_2      |   0.00144 |
| SHORT  | distance_h24 |   0.00143 |
| LONG   | range_12     |   0.00126 |
| LONG   | volume_ratio |   0.0012  |
| LONG   | trend_12     |   0.00113 |
| LONG   | range_3      |   0.00111 |
| LONG   | volume_accel |   0.00083 |
| SHORT  | trend_3      |   0.00068 |

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
