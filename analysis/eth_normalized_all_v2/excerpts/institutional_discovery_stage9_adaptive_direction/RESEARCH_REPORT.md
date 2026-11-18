# Stage 9 — Adaptive entry discovery from closed BTC candles

## Method
Any-time model with NO hour, weekday or session inputs. 33 completed-bar
price/volume/volatility features from 5m ETHUSD futures candles.
Train Jan-Sep 2025; select cutoff Oct-Dec 2025; report 2026
chronologically without adjusting decisions after seeing later results.
Classification goal: net +200 before -100 within 30m, stop-first.

## Prediction skill
| side   | period          |     n |   hit_rate |      auc |   average_precision |   mean_pred |   top_decile_label_rate |
|:-------|:----------------|------:|-----------:|---------:|--------------------:|------------:|------------------------:|
| LONG   | train           | 78282 |      18.94 |   0.5881 |              0.2467 |      0.1894 |                   28.09 |
| LONG   | select_2025Q4   | 26265 |      19.44 |   0.5285 |              0.2152 |      0.19   |                   23.13 |
| LONG   | check_2026H1    | 51916 |      13.7  |   0.5663 |              0.17   |      0.1895 |                   19.32 |
| LONG   | recheck_2026H2  | 35304 |      10.88 |   0.5686 |              0.1381 |      0.1886 |                   15.89 |
| LONG   | november_recent |     0 |     nan    | nan      |            nan      |    nan      |                  nan    |
| SHORT  | train           | 78282 |      19.28 |   0.5888 |              0.2544 |      0.1928 |                   29.61 |
| SHORT  | select_2025Q4   | 26265 |      20.01 |   0.5373 |              0.2255 |      0.194  |                   24.52 |
| SHORT  | check_2026H1    | 51916 |      15    |   0.5692 |              0.1829 |      0.1946 |                   20.84 |
| SHORT  | recheck_2026H2  | 35304 |      10.49 |   0.5957 |              0.1443 |      0.1941 |                   17.12 |
| SHORT  | november_recent |     0 |     nan    | nan      |            nan      |    nan      |                  nan    |

## Chosen probability cutoff
| side   |   selected_threshold |   selection_trades |   selection_net |
|:-------|---------------------:|-------------------:|----------------:|
| LONG   |                 0.25 |                192 |         -117.07 |
| SHORT  |                 0.3  |                133 |          -92.35 |

## Independently replayed net trading outcomes
| side   | period          | cutoff_model      |   threshold | tp_model   |   trades |   mean_net_pts |   profit_factor |   wins |   losses |   win_pct |   sum_net_pts |   whatif_avg_pts |
|:-------|:----------------|:------------------|------------:|:-----------|---------:|---------------:|----------------:|-------:|---------:|----------:|--------------:|-----------------:|
| LONG   | train           | trained_threshold |     0.25    | gross200   |      353 |         -61.67 |           0.428 |    168 |      185 |     47.59 |     -21771.1  |           -14.27 |
| LONG   | train           | trained_threshold |     0.25    | net200     |      343 |         -39.14 |           0.677 |    142 |      201 |     41.4  |     -13426.5  |             8.24 |
| LONG   | train           | baseline_top10pct |     0.21212 | gross200   |     6724 |         -94.15 |           0.266 |   2540 |     4184 |     37.78 |    -633092    |           -45.1  |
| LONG   | train           | baseline_top10pct |     0.21212 | net200     |     6212 |         -86.48 |           0.398 |   1859 |     4353 |     29.93 |    -537218    |           -37.43 |
| LONG   | select_2025Q4   | trained_threshold |     0.25    | gross200   |      195 |        -128.46 |           0.154 |     61 |      134 |     31.28 |     -25050    |           -71.34 |
| LONG   | select_2025Q4   | trained_threshold |     0.25    | net200     |      192 |        -117.07 |           0.296 |     48 |      144 |     25    |     -22478.4  |           -59.9  |
| LONG   | select_2025Q4   | baseline_top10pct |     0.21212 | gross200   |     2589 |        -124.71 |           0.164 |    856 |     1733 |     33.06 |    -322884    |           -67.03 |
| LONG   | select_2025Q4   | baseline_top10pct |     0.21212 | net200     |     2403 |        -121.46 |           0.278 |    583 |     1820 |     24.26 |    -291863    |           -63.82 |
| LONG   | check_2026H1    | trained_threshold |     0.25    | gross200   |      255 |         -83.69 |           0.304 |     83 |      172 |     32.55 |     -21339.7  |           -46.68 |
| LONG   | check_2026H1    | trained_threshold |     0.25    | net200     |      252 |         -81.01 |           0.376 |     68 |      184 |     26.98 |     -20413.6  |           -43.99 |
| LONG   | check_2026H1    | baseline_top10pct |     0.21212 | gross200   |     4170 |         -83.16 |           0.299 |   1341 |     2829 |     32.16 |    -346759    |           -45.95 |
| LONG   | check_2026H1    | baseline_top10pct |     0.21212 | net200     |     3857 |         -83.81 |           0.344 |   1010 |     2847 |     26.19 |    -323265    |           -46.69 |
| LONG   | recheck_2026H2  | trained_threshold |     0.25    | gross200   |      175 |         -73.97 |           0.331 |     59 |      116 |     33.71 |     -12945.5  |           -37.02 |
| LONG   | recheck_2026H2  | trained_threshold |     0.25    | net200     |      171 |         -66.51 |           0.434 |     51 |      120 |     29.82 |     -11372.4  |           -29.64 |
| LONG   | recheck_2026H2  | baseline_top10pct |     0.21212 | gross200   |     2482 |         -86.68 |           0.263 |    738 |     1744 |     29.73 |    -215141    |           -49.08 |
| LONG   | recheck_2026H2  | baseline_top10pct |     0.21212 | net200     |     2291 |         -85.25 |           0.31  |    567 |     1724 |     24.75 |    -195304    |           -47.74 |
| LONG   | november_recent | trained_threshold |     0.25    | gross200   |        0 |         nan    |         nan     |      0 |        0 |    nan    |        nan    |           nan    |
| LONG   | november_recent | trained_threshold |     0.25    | net200     |        0 |         nan    |         nan     |      0 |        0 |    nan    |        nan    |           nan    |
| LONG   | november_recent | baseline_top10pct |     0.21212 | gross200   |        0 |         nan    |         nan     |      0 |        0 |    nan    |        nan    |           nan    |
| LONG   | november_recent | baseline_top10pct |     0.21212 | net200     |        0 |         nan    |         nan     |      0 |        0 |    nan    |        nan    |           nan    |
| SHORT  | train           | trained_threshold |     0.3     | gross200   |      295 |         -35.72 |           0.598 |    167 |      128 |     56.61 |     -10536.4  |            12.25 |
| SHORT  | train           | trained_threshold |     0.3     | net200     |      290 |         -12.52 |           0.883 |    138 |      152 |     47.59 |      -3630.86 |            35.69 |
| SHORT  | train           | baseline_top10pct |     0.22761 | gross200   |     6820 |         -90.24 |           0.282 |   2691 |     4129 |     39.46 |    -615439    |           -40.74 |
| SHORT  | train           | baseline_top10pct |     0.22761 | net200     |     6346 |         -81.93 |           0.424 |   1985 |     4361 |     31.28 |    -519957    |           -32.46 |
| SHORT  | select_2025Q4   | trained_threshold |     0.3     | gross200   |      136 |        -109.25 |           0.21  |     51 |       85 |     37.5  |     -14858.5  |           -53.38 |
| SHORT  | select_2025Q4   | trained_threshold |     0.3     | net200     |      133 |         -92.35 |           0.396 |     41 |       92 |     30.83 |     -12282.4  |           -36.38 |
| SHORT  | select_2025Q4   | baseline_top10pct |     0.22761 | gross200   |     2698 |        -119.22 |           0.177 |    938 |     1760 |     34.77 |    -321642    |           -61.86 |
| SHORT  | select_2025Q4   | baseline_top10pct |     0.22761 | net200     |     2513 |        -112.54 |           0.312 |    658 |     1855 |     26.18 |    -282824    |           -55.19 |
| SHORT  | check_2026H1    | trained_threshold |     0.3     | gross200   |      238 |         -99.13 |           0.232 |     64 |      174 |     26.89 |     -23593.1  |           -62.12 |
| SHORT  | check_2026H1    | trained_threshold |     0.3     | net200     |      233 |         -91.65 |           0.325 |     54 |      179 |     23.18 |     -21353.6  |           -54.69 |
| SHORT  | check_2026H1    | baseline_top10pct |     0.22761 | gross200   |     4445 |         -82.28 |           0.305 |   1442 |     3003 |     32.44 |    -365754    |           -45.06 |
| SHORT  | check_2026H1    | baseline_top10pct |     0.22761 | net200     |     4087 |         -80.14 |           0.368 |   1092 |     2995 |     26.72 |    -327545    |           -42.96 |
| SHORT  | recheck_2026H2  | trained_threshold |     0.3     | gross200   |      157 |         -73.98 |           0.333 |     55 |      102 |     35.03 |     -11615    |           -36.81 |
| SHORT  | recheck_2026H2  | trained_threshold |     0.3     | net200     |      154 |         -78.45 |           0.358 |     42 |      112 |     27.27 |     -12081.3  |           -41.31 |
| SHORT  | recheck_2026H2  | baseline_top10pct |     0.22761 | gross200   |     2644 |         -82.11 |           0.286 |    811 |     1833 |     30.67 |    -217106    |           -44.47 |
| SHORT  | recheck_2026H2  | baseline_top10pct |     0.22761 | net200     |     2437 |         -83.11 |           0.328 |    607 |     1830 |     24.91 |    -202527    |           -45.53 |
| SHORT  | november_recent | trained_threshold |     0.3     | gross200   |        0 |         nan    |         nan     |      0 |        0 |    nan    |        nan    |           nan    |
| SHORT  | november_recent | trained_threshold |     0.3     | net200     |        0 |         nan    |         nan     |      0 |        0 |    nan    |        nan    |           nan    |
| SHORT  | november_recent | baseline_top10pct |     0.22761 | gross200   |        0 |         nan    |         nan     |      0 |        0 |    nan    |        nan    |           nan    |
| SHORT  | november_recent | baseline_top10pct |     0.22761 | net200     |        0 |         nan    |         nan     |      0 |        0 |    nan    |        nan    |           nan    |

## Exploratory feature importance by 2025 selection permutation
| side   | feature          |   AP_drop |
|:-------|:-----------------|----------:|
| SHORT  | range_regime     |   0.01517 |
| LONG   | range_regime     |   0.01103 |
| LONG   | abs_ret_12       |   0.00683 |
| SHORT  | trend_12         |   0.00614 |
| LONG   | range_ratio      |   0.00274 |
| SHORT  | trend_24         |   0.00262 |
| SHORT  | distance_l24     |   0.00199 |
| LONG   | range_2          |   0.00198 |
| LONG   | trend_12         |   0.00193 |
| SHORT  | range_24         |   0.00191 |
| SHORT  | range_6          |   0.00165 |
| LONG   | candle_body_frac |   0.00163 |
| SHORT  | range_ratio      |   0.00163 |
| SHORT  | distance_h24     |   0.00142 |
| LONG   | volume_ratio     |   0.00122 |
| SHORT  | range_2          |   0.00111 |
| LONG   | wick_down_frac   |   0.00099 |
| LONG   | trend_24         |   0.00083 |
| LONG   | volume_12        |   0.00082 |
| LONG   | range_12         |   0.00079 |

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
