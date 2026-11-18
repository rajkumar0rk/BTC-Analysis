# Stage 5 — Can volatility-scaled exits improve BTC directional expectancy?

## Method
Signals from Stage 3 are **unchanged**: expansion follow, accepted 12h breakout, and rejected 12h sweep.
Entry at first next-hour 1m open. No entry optimization. Independent model/rule strategies never overlap trades.
Compare Stage 3-style 500/350 60m fixed exits with risk-scaled 2R target, 4h trailing, or 4h timeout.
Risk: prior 48h typical hourly range clipped to 200–1200 points; volatility stop 1R.
Trailing activation 0.75R, trail distance 0.5R; trailing changes only after fully completed minute closes.
Every model uses 0.05% per side taker + 18% GST and 5 points adverse slippage per side.

## Net point results
| rule                  | exit_model          | period               |   trades |   days |   avg_net |   win_pct |   profit_factor |   max_drawdown_pts |   avg_gross |   avg_cost |   avg_mfe |   avg_mae |   avg_hold_min |   ci95_low |   ci95_high |
|:----------------------|:--------------------|:---------------------|---------:|-------:|----------:|----------:|----------------:|-------------------:|------------:|-----------:|----------:|----------:|---------------:|-----------:|------------:|
| accepted_12h_breakout | fixed_60m_reference | 2025_train           |      277 |    187 |   -110.57 |     40.79 |           0.573 |           31941.9  |        2.84 |     113.41 |    376.98 |    298.85 |           16   |    -158.7  |      -62.57 |
| accepted_12h_breakout | fixed_60m_reference | 2026_H1_validation   |      127 |     87 |    -90.88 |     34.65 |           0.589 |           11928.4  |       -8.04 |      82.85 |    310.09 |    273.77 |           30.3 |    -153.92 |      -25.16 |
| accepted_12h_breakout | fixed_60m_reference | 2026_H2_seen_recheck |       90 |     63 |    -21.54 |     45.56 |           0.873 |            4585.48 |       62.8  |      84.34 |    366.98 |    225    |           35.8 |     -99.62 |       51    |
| accepted_12h_breakout | vol_2R_4h           | 2025_train           |      269 |    187 |    -22.87 |     39.03 |           0.95  |           23313    |       90.8  |     113.68 |    837.69 |    574.53 |           96.7 |    -134.68 |      104.28 |
| accepted_12h_breakout | vol_2R_4h           | 2026_H1_validation   |      125 |     87 |    -67.09 |     32.8  |           0.783 |            9343.22 |       15.84 |      82.93 |    524.16 |    386.95 |           91.3 |    -170.9  |       38.58 |
| accepted_12h_breakout | vol_2R_4h           | 2026_H2_seen_recheck |       86 |     63 |    -30.12 |     43.02 |           0.867 |            6363.13 |       54.11 |      84.23 |    453.15 |    282.58 |           91.4 |    -133.52 |       71.01 |
| accepted_12h_breakout | vol_timeout_4h      | 2025_train           |      240 |    186 |     73.78 |     36.67 |           1.159 |           21805.8  |      187.56 |     113.78 |   1179.91 |    590.57 |          146.2 |     -79.22 |      260    |
| accepted_12h_breakout | vol_timeout_4h      | 2026_H1_validation   |      114 |     87 |    -21.96 |     28.07 |           0.932 |           11658    |       61.32 |      83.28 |    761.83 |    404.71 |          139.5 |    -160.4  |      137.58 |
| accepted_12h_breakout | vol_timeout_4h      | 2026_H2_seen_recheck |       76 |     63 |    -15.58 |     34.21 |           0.939 |            8206.31 |       68.36 |      83.94 |    676.44 |    305.17 |          145.6 |    -175.49 |      143.85 |
| accepted_12h_breakout | vol_trail_4h        | 2025_train           |      273 |    187 |   -105.88 |     54.95 |           0.698 |           32721.3  |        7.79 |     113.67 |    695.37 |    489.38 |           52   |    -190.88 |      -21.65 |
| accepted_12h_breakout | vol_trail_4h        | 2026_H1_validation   |      125 |     87 |    -55.16 |     52.8  |           0.756 |            7244.49 |       27.79 |      82.94 |    452.65 |    329.05 |           58   |    -124.72 |       29.04 |
| accepted_12h_breakout | vol_trail_4h        | 2026_H2_seen_recheck |       86 |     63 |    -31.07 |     59.3  |           0.821 |            5712.72 |       53.36 |      84.43 |    421.18 |    239.66 |           43.8 |    -108.47 |       56.9  |
| expansion_follow      | fixed_60m_reference | 2025_train           |     1033 |    298 |   -121.63 |     39.3  |           0.526 |          126055    |      -11.24 |     110.39 |    341.54 |    299.77 |           21.4 |    -145.94 |      -92    |
| expansion_follow      | fixed_60m_reference | 2026_H1_validation   |      609 |    162 |    -85.65 |     37.27 |           0.569 |           52163.8  |       -1.12 |      84.53 |    292.32 |    251.4  |           37.2 |    -110.72 |      -60.71 |
| expansion_follow      | fixed_60m_reference | 2026_H2_seen_recheck |      504 |    125 |    -72.26 |     37.5  |           0.592 |           37662.8  |       11.51 |      83.78 |    269.76 |    224.79 |           43.3 |    -100.36 |      -45.55 |
| expansion_follow      | vol_2R_4h           | 2025_train           |      954 |    298 |   -114.47 |     36.48 |           0.757 |          111242    |       -4.2  |     110.27 |    755.29 |    581.58 |          100.3 |    -174.66 |      -49.69 |
| expansion_follow      | vol_2R_4h           | 2026_H1_validation   |      568 |    162 |    -70.51 |     34.86 |           0.757 |           40048.6  |       13.91 |      84.42 |    483.38 |    353.65 |           95.4 |    -110.93 |      -35.29 |
| expansion_follow      | vol_2R_4h           | 2026_H2_seen_recheck |      450 |    125 |    -67.22 |     36.89 |           0.714 |           32262    |       17.03 |      84.25 |    381.56 |    278.68 |           97.6 |    -107.84 |      -34.01 |
| expansion_follow      | vol_timeout_4h      | 2025_train           |      776 |    298 |    -51.59 |     32.99 |           0.897 |           57121.9  |       59.35 |     110.94 |   1062.25 |    606.4  |          139.8 |    -151.84 |       40.23 |
| expansion_follow      | vol_timeout_4h      | 2026_H1_validation   |      441 |    162 |    -72.8  |     30.16 |           0.765 |           32919.3  |       11.47 |      84.27 |    666.63 |    369.48 |          138.4 |    -139.2  |      -18.01 |
| expansion_follow      | vol_timeout_4h      | 2026_H2_seen_recheck |      351 |    125 |    -64.2  |     30.2  |           0.747 |           27881    |       19.8  |      84    |    524.8  |    292.72 |          142.4 |    -133.03 |        4.08 |
| expansion_follow      | vol_trail_4h        | 2025_train           |     1020 |    298 |   -115.99 |     52.45 |           0.675 |          118707    |       -5.59 |     110.4  |    649.91 |    487.91 |           58.3 |    -158.59 |      -61.08 |
| expansion_follow      | vol_trail_4h        | 2026_H1_validation   |      594 |    162 |    -38.28 |     52.86 |           0.815 |           23393.2  |       46.33 |      84.61 |    435.33 |    291.19 |           62.7 |     -73.9  |       -4.09 |
| expansion_follow      | vol_trail_4h        | 2026_H2_seen_recheck |      486 |    125 |    -67.53 |     48.15 |           0.627 |           33766.8  |       16.42 |      83.95 |    334.67 |    234.28 |           62.9 |     -96.71 |      -37.79 |
| rejected_12h_sweep    | fixed_60m_reference | 2025_train           |      130 |    107 |   -207.01 |     35.38 |           0.364 |           27692    |      -95.74 |     111.27 |    308.04 |    381.17 |           22.9 |    -336.21 |      -90.58 |
| rejected_12h_sweep    | fixed_60m_reference | 2026_H1_validation   |       64 |     59 |   -141.6  |     32.81 |           0.399 |            9449.08 |      -57.12 |      84.48 |    272.97 |    268.74 |           33.8 |    -224.79 |      -53.24 |
| rejected_12h_sweep    | fixed_60m_reference | 2026_H2_seen_recheck |       42 |     37 |    -48.96 |     42.86 |           0.678 |            2422.68 |       35.36 |      84.32 |    252.5  |    210.05 |           49.7 |    -122.03 |       35.82 |
| rejected_12h_sweep    | vol_2R_4h           | 2025_train           |      130 |    107 |   -194.43 |     35.38 |           0.647 |           28650.3  |      -83.17 |     111.25 |    722.36 |    658.54 |          104.4 |    -396.66 |       24.73 |
| rejected_12h_sweep    | vol_2R_4h           | 2026_H1_validation   |       64 |     59 |   -146.71 |     31.25 |           0.581 |           10751.8  |      -62.18 |      84.53 |    480.6  |    401.57 |           86.2 |    -282.65 |       -1.11 |
| rejected_12h_sweep    | vol_2R_4h           | 2026_H2_seen_recheck |       42 |     37 |     -3.97 |     45.24 |           0.978 |            1954.68 |       80.34 |      84.31 |    387.22 |    232.91 |          119.6 |    -120.89 |      111.22 |
| rejected_12h_sweep    | vol_timeout_4h      | 2025_train           |      127 |    107 |   -246.59 |     29.92 |           0.588 |           32308.8  |     -135.4  |     111.19 |    878.96 |    695.61 |          132.9 |    -459.7  |        0.71 |
| rejected_12h_sweep    | vol_timeout_4h      | 2026_H1_validation   |       64 |     59 |   -168.09 |     26.56 |           0.547 |           12412.7  |      -83.54 |      84.55 |    617.96 |    410.64 |          118.6 |    -315.59 |       -0.09 |
| rejected_12h_sweep    | vol_timeout_4h      | 2026_H2_seen_recheck |       41 |     37 |    112.76 |     43.9  |           1.632 |            2008.47 |      197.02 |      84.26 |    571.66 |    235.41 |          166.1 |     -64.38 |      295.85 |
| rejected_12h_sweep    | vol_trail_4h        | 2025_train           |      130 |    107 |   -233.57 |     50.77 |           0.477 |           31149.3  |     -122.32 |     111.25 |    610.41 |    595.9  |           64.2 |    -410.98 |      -49.24 |
| rejected_12h_sweep    | vol_trail_4h        | 2026_H1_validation   |       64 |     59 |   -124.88 |     43.75 |           0.569 |            8249.19 |      -40.38 |      84.5  |    439.68 |    357.92 |           63   |    -245.17 |       -5.28 |
| rejected_12h_sweep    | vol_trail_4h        | 2026_H2_seen_recheck |       42 |     37 |      1.07 |     54.76 |           1.007 |            2004.68 |       85.36 |      84.29 |    382.68 |    217.52 |           84.4 |     -95.73 |       94.6  |

## Interpretation
Returns are BTC price points on a 1 BTC-price-unit equivalent, NOT actual account USD.
Compare signs, cost robustness, trade counts and confidence intervals across periods;
any isolated positive cell does not demonstrate a repeatable edge.

## Limitations
- The later 2026 period is previously researched, not untouched
- Stop and take fills are 1m OHLC approximations
- No historical spread, L2 impact or funding cashflows
- No live position sizing, liquidation/margin, or account PNL
- Multiple comparisons; bootstrap intervals are exploratory
- No conclusions from 2026 seen recheck alone

Further research must be frozen and prospectively evaluated on uninspected fresh data.
