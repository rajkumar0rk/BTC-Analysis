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
| accepted_12h_breakout | fixed_60m_reference | 2026_H2_seen_recheck |       79 |     55 |    -40.16 |     43.04 |           0.775 |            4585.48 |       44.61 |      84.77 |    363.35 |    232.73 |           36.7 |    -109.58 |       35.39 |
| accepted_12h_breakout | vol_2R_4h           | 2025_train           |      269 |    187 |    -22.87 |     39.03 |           0.95  |           23313    |       90.8  |     113.68 |    837.41 |    575.15 |           96.7 |    -134.68 |      104.28 |
| accepted_12h_breakout | vol_2R_4h           | 2026_H1_validation   |      125 |     87 |    -67.09 |     32.8  |           0.783 |            9343.22 |       15.84 |      82.93 |    524.16 |    386.96 |           91.4 |    -170.9  |       38.58 |
| accepted_12h_breakout | vol_2R_4h           | 2026_H2_seen_recheck |       75 |     55 |    -74.9  |     40    |           0.682 |            5617.38 |        9.79 |      84.69 |    418.99 |    288.84 |           93.1 |    -170.45 |       13.7  |
| accepted_12h_breakout | vol_timeout_4h      | 2025_train           |      240 |    186 |     73.78 |     36.67 |           1.159 |           21805.8  |      187.56 |     113.78 |   1179.91 |    591.27 |          146.2 |     -79.22 |      260    |
| accepted_12h_breakout | vol_timeout_4h      | 2026_H1_validation   |      114 |     87 |    -21.96 |     28.07 |           0.932 |           11658    |       61.32 |      83.28 |    761.83 |    404.71 |          139.5 |    -160.4  |      137.58 |
| accepted_12h_breakout | vol_timeout_4h      | 2026_H2_seen_recheck |       67 |     55 |    -92.94 |     31.34 |           0.658 |            7460.56 |       -8.47 |      84.46 |    595.23 |    312.91 |          139.9 |    -231.4  |       84.34 |
| accepted_12h_breakout | vol_trail_4h        | 2025_train           |      273 |    187 |   -105.88 |     54.95 |           0.698 |           32721.3  |        7.79 |     113.67 |    695.37 |    489.99 |           52   |    -190.88 |      -21.65 |
| accepted_12h_breakout | vol_trail_4h        | 2026_H1_validation   |      125 |     87 |    -55.16 |     52.8  |           0.756 |            7244.49 |       27.79 |      82.94 |    452.65 |    329.06 |           58   |    -124.72 |       29.04 |
| accepted_12h_breakout | vol_trail_4h        | 2026_H2_seen_recheck |       75 |     55 |    -61.37 |     57.33 |           0.667 |            5712.72 |       23.51 |      84.89 |    390.49 |    249.72 |           44.1 |    -141.41 |       17.75 |
| expansion_follow      | fixed_60m_reference | 2025_train           |     1032 |    298 |   -121.3  |     39.34 |           0.527 |          125592    |      -10.91 |     110.38 |    341.82 |    299.63 |           21.5 |    -145.66 |      -91.73 |
| expansion_follow      | fixed_60m_reference | 2026_H1_validation   |      609 |    162 |    -85.65 |     37.27 |           0.569 |           52163.8  |       -1.12 |      84.53 |    292.32 |    251.4  |           37.2 |    -110.72 |      -60.71 |
| expansion_follow      | fixed_60m_reference | 2026_H2_seen_recheck |      433 |    111 |    -78.43 |     36.26 |           0.558 |           35239.8  |        6.13 |      84.56 |    263.21 |    224.36 |           44.7 |    -106.14 |      -51.9  |
| expansion_follow      | vol_2R_4h           | 2025_train           |      953 |    298 |   -113.53 |     36.52 |           0.758 |          111242    |       -3.26 |     110.27 |    755.98 |    581.06 |          100.4 |    -172.68 |      -49.69 |
| expansion_follow      | vol_2R_4h           | 2026_H1_validation   |      568 |    162 |    -70.51 |     34.86 |           0.757 |           40048.6  |       13.91 |      84.42 |    483.38 |    353.59 |           95.4 |    -110.93 |      -35.29 |
| expansion_follow      | vol_2R_4h           | 2026_H2_seen_recheck |      384 |    111 |    -70.54 |     36.72 |           0.697 |           29506.4  |       14.56 |      85.1  |    369.87 |    275.3  |           99.9 |    -108.85 |      -38.02 |
| expansion_follow      | vol_timeout_4h      | 2025_train           |      775 |    298 |    -50.36 |     33.03 |           0.899 |           57121.9  |       60.58 |     110.94 |   1063.42 |    605.8  |          139.8 |    -150.95 |       41.17 |
| expansion_follow      | vol_timeout_4h      | 2026_H1_validation   |      441 |    162 |    -72.8  |     30.16 |           0.765 |           32919.3  |       11.47 |      84.27 |    666.63 |    369.4  |          138.4 |    -139.2  |      -18.01 |
| expansion_follow      | vol_timeout_4h      | 2026_H2_seen_recheck |      303 |    111 |    -78.15 |     29.37 |           0.695 |           26061.2  |        6.61 |      84.76 |    500.14 |    292.06 |          143.1 |    -156.38 |       -4.99 |
| expansion_follow      | vol_trail_4h        | 2025_train           |     1019 |    298 |   -115.12 |     52.5  |           0.677 |          117700    |       -4.72 |     110.4  |    650.4  |    487.34 |           58.3 |    -158.59 |      -60.33 |
| expansion_follow      | vol_trail_4h        | 2026_H1_validation   |      594 |    162 |    -38.28 |     52.86 |           0.815 |           23393.2  |       46.33 |      84.61 |    435.33 |    291.2  |           62.7 |     -73.9  |       -4.09 |
| expansion_follow      | vol_trail_4h        | 2026_H2_seen_recheck |      415 |    111 |    -76.38 |     47.23 |           0.583 |           32750.2  |        8.42 |      84.8  |    322.86 |    235.23 |           65.2 |    -107.73 |      -47.06 |
| rejected_12h_sweep    | fixed_60m_reference | 2025_train           |      130 |    107 |   -207.01 |     35.38 |           0.364 |           27692    |      -95.74 |     111.27 |    308.04 |    381.17 |           22.9 |    -336.21 |      -90.58 |
| rejected_12h_sweep    | fixed_60m_reference | 2026_H1_validation   |       64 |     59 |   -141.6  |     32.81 |           0.399 |            9449.08 |      -57.12 |      84.48 |    272.97 |    268.74 |           33.8 |    -224.79 |      -53.24 |
| rejected_12h_sweep    | fixed_60m_reference | 2026_H2_seen_recheck |       39 |     35 |    -49.21 |     43.59 |           0.671 |            2422.68 |       35.02 |      84.24 |    251.15 |    208.48 |           50.7 |    -132.55 |       30.27 |
| rejected_12h_sweep    | vol_2R_4h           | 2025_train           |      130 |    107 |   -194.43 |     35.38 |           0.647 |           28650.3  |      -83.17 |     111.25 |    722.36 |    658.54 |          104.4 |    -396.66 |       24.73 |
| rejected_12h_sweep    | vol_2R_4h           | 2026_H1_validation   |       64 |     59 |   -146.71 |     31.25 |           0.581 |           10751.8  |      -62.18 |      84.53 |    480.6  |    401.57 |           86.2 |    -282.65 |       -1.11 |
| rejected_12h_sweep    | vol_2R_4h           | 2026_H2_seen_recheck |       39 |     35 |      6.1  |     46.15 |           1.035 |            1954.68 |       90.33 |      84.23 |    396.66 |    234.83 |          125.6 |    -135.03 |      121.93 |
| rejected_12h_sweep    | vol_timeout_4h      | 2025_train           |      127 |    107 |   -246.59 |     29.92 |           0.588 |           32308.8  |     -135.4  |     111.19 |    878.96 |    695.61 |          132.9 |    -459.7  |        0.71 |
| rejected_12h_sweep    | vol_timeout_4h      | 2026_H1_validation   |       64 |     59 |   -168.09 |     26.56 |           0.547 |           12412.7  |      -83.54 |      84.55 |    617.96 |    410.64 |          118.6 |    -315.59 |       -0.09 |
| rejected_12h_sweep    | vol_timeout_4h      | 2026_H2_seen_recheck |       39 |     35 |    106.41 |     43.59 |           1.603 |            2008.47 |      190.61 |      84.2  |    566.29 |    237.89 |          165.9 |    -118.5  |      289.67 |
| rejected_12h_sweep    | vol_trail_4h        | 2025_train           |      130 |    107 |   -233.57 |     50.77 |           0.477 |           31149.3  |     -122.32 |     111.25 |    610.41 |    595.9  |           64.2 |    -410.98 |      -49.24 |
| rejected_12h_sweep    | vol_trail_4h        | 2026_H1_validation   |       64 |     59 |   -124.88 |     43.75 |           0.569 |            8249.19 |      -40.38 |      84.5  |    439.68 |    357.92 |           63   |    -245.17 |       -5.28 |
| rejected_12h_sweep    | vol_trail_4h        | 2026_H2_seen_recheck |       39 |     35 |     15.15 |     56.41 |           1.1   |            1458.83 |       99.36 |      84.21 |    391.77 |    218.26 |           87.6 |    -113.98 |      111    |

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
