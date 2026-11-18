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
| accepted_12h_breakout | fixed_60m_reference | 2025_train           |      277 |    187 |    -10.53 |     28.16 |           0.447 |            2916.76 |        3.16 |      13.69 |     31.98 |     22.34 |           60   |     -14.93 |       -6.63 |
| accepted_12h_breakout | fixed_60m_reference | 2026_H1_validation   |      127 |     87 |    -12.05 |     23.62 |           0.268 |            1530.45 |        0.55 |      12.6  |     18.29 |     15.47 |           60   |     -15.98 |       -8.52 |
| accepted_12h_breakout | fixed_60m_reference | 2026_H2_seen_recheck |       90 |     63 |     -7.72 |     22.22 |           0.426 |             749.97 |        4.93 |      12.65 |     19.81 |     11.96 |           60   |     -13.16 |       -2.86 |
| accepted_12h_breakout | vol_2R_4h           | 2025_train           |      237 |    186 |     -5.16 |     38.82 |           0.791 |            1618.44 |        8.54 |      13.7  |     51.15 |     37.43 |          238.9 |     -13.79 |        4.47 |
| accepted_12h_breakout | vol_2R_4h           | 2026_H1_validation   |      109 |     86 |    -12.28 |     28.44 |           0.46  |            1338.79 |        0.34 |      12.62 |     31.72 |     27.38 |          238.7 |     -19.87 |       -3.78 |
| accepted_12h_breakout | vol_2R_4h           | 2026_H2_seen_recheck |       74 |     63 |     -8.96 |     31.08 |           0.459 |             796.3  |        3.68 |      12.64 |     29.14 |     18.96 |          240   |     -16.7  |       -1.17 |
| accepted_12h_breakout | vol_timeout_4h      | 2025_train           |      237 |    186 |     -6.72 |     38.82 |           0.729 |            1643.58 |        6.98 |      13.7  |     51.25 |     37.67 |          239.9 |     -14.67 |        1.47 |
| accepted_12h_breakout | vol_timeout_4h      | 2026_H1_validation   |      109 |     86 |    -12.28 |     28.44 |           0.46  |            1338.79 |        0.34 |      12.62 |     31.72 |     27.38 |          238.7 |     -19.87 |       -3.78 |
| accepted_12h_breakout | vol_timeout_4h      | 2026_H2_seen_recheck |       74 |     63 |     -8.96 |     31.08 |           0.459 |             796.3  |        3.68 |      12.64 |     29.14 |     18.96 |          240   |     -16.7  |       -1.17 |
| accepted_12h_breakout | vol_trail_4h        | 2025_train           |      237 |    186 |     -4.8  |     39.24 |           0.805 |            1495.61 |        8.9  |      13.7  |     50.82 |     37.42 |          237.3 |     -12.99 |        4.88 |
| accepted_12h_breakout | vol_trail_4h        | 2026_H1_validation   |      109 |     86 |    -11.97 |     28.44 |           0.474 |            1304.32 |        0.65 |      12.62 |     31.72 |     27.38 |          238.5 |     -19.43 |       -3.33 |
| accepted_12h_breakout | vol_trail_4h        | 2026_H2_seen_recheck |       74 |     63 |     -8.96 |     31.08 |           0.459 |             796.3  |        3.68 |      12.64 |     29.14 |     18.96 |          240   |     -16.7  |       -1.17 |
| expansion_follow      | fixed_60m_reference | 2025_train           |     1032 |    298 |    -12.31 |     24.71 |           0.353 |           12703.1  |        1.27 |      13.58 |     25.81 |     22.01 |           60   |     -14.15 |      -10.43 |
| expansion_follow      | fixed_60m_reference | 2026_H1_validation   |      610 |    162 |    -12.58 |     17.05 |           0.181 |            7671.29 |        0.08 |      12.66 |     15.27 |     13.26 |           60   |     -14    |      -11.16 |
| expansion_follow      | fixed_60m_reference | 2026_H2_seen_recheck |      503 |    125 |    -11.76 |     14.31 |           0.162 |            5914.78 |        0.87 |      12.63 |     12.77 |     10.54 |           60   |     -13.32 |      -10.45 |
| expansion_follow      | vol_2R_4h           | 2025_train           |      599 |    297 |     -9.69 |     34.56 |           0.631 |            5812.85 |        3.93 |      13.62 |     45.07 |     38.76 |          239   |     -14.44 |       -5.15 |
| expansion_follow      | vol_2R_4h           | 2026_H1_validation   |      333 |    162 |    -11.22 |     29.43 |           0.4   |            3735.99 |        1.42 |      12.63 |     28.87 |     23.65 |          239.6 |     -14.76 |       -7.86 |
| expansion_follow      | vol_2R_4h           | 2026_H2_seen_recheck |      263 |    125 |    -12.12 |     25.48 |           0.309 |            3212.18 |        0.51 |      12.63 |     21.8  |     19.58 |          240   |     -16.75 |       -7.99 |
| expansion_follow      | vol_timeout_4h      | 2025_train           |      599 |    297 |     -9.51 |     34.89 |           0.632 |            5704.52 |        4.11 |      13.62 |     45.68 |     38.46 |          239.6 |     -14.37 |       -4.99 |
| expansion_follow      | vol_timeout_4h      | 2026_H1_validation   |      333 |    162 |    -11.22 |     29.43 |           0.4   |            3735.99 |        1.42 |      12.63 |     28.87 |     23.65 |          239.6 |     -14.76 |       -7.86 |
| expansion_follow      | vol_timeout_4h      | 2026_H2_seen_recheck |      263 |    125 |    -12.12 |     25.48 |           0.309 |            3212.18 |        0.51 |      12.63 |     21.8  |     19.58 |          240   |     -16.75 |       -7.99 |
| expansion_follow      | vol_trail_4h        | 2025_train           |      600 |    297 |     -9.44 |     34.67 |           0.641 |            5782.4  |        4.18 |      13.62 |     45.24 |     38.86 |          238.7 |     -14.28 |       -4.9  |
| expansion_follow      | vol_trail_4h        | 2026_H1_validation   |      333 |    162 |    -11.12 |     29.43 |           0.405 |            3701.52 |        1.52 |      12.63 |     28.87 |     23.65 |          239.5 |     -14.61 |       -7.69 |
| expansion_follow      | vol_trail_4h        | 2026_H2_seen_recheck |      263 |    125 |    -12.12 |     25.48 |           0.309 |            3212.18 |        0.51 |      12.63 |     21.8  |     19.58 |          240   |     -16.75 |       -7.99 |
| rejected_12h_sweep    | fixed_60m_reference | 2025_train           |      130 |    107 |    -16.2  |     23.08 |           0.179 |            2106.8  |       -2.59 |      13.61 |     21.11 |     25.56 |           60   |     -21.02 |      -12.08 |
| rejected_12h_sweep    | fixed_60m_reference | 2026_H1_validation   |       64 |     59 |    -10.99 |     20.31 |           0.237 |             717.46 |        1.67 |      12.66 |     15.6  |     14.21 |           60   |     -15.08 |       -6.22 |
| rejected_12h_sweep    | fixed_60m_reference | 2026_H2_seen_recheck |       42 |     37 |     -6.64 |     19.05 |           0.379 |             278.72 |        6.01 |      12.65 |     14.44 |      8.59 |           60   |     -12.74 |        2.28 |
| rejected_12h_sweep    | vol_2R_4h           | 2025_train           |      122 |    107 |    -20.94 |     33.61 |           0.348 |            2560.31 |       -7.33 |      13.61 |     36.15 |     46.23 |          237.4 |     -32.24 |       -8.87 |
| rejected_12h_sweep    | vol_2R_4h           | 2026_H1_validation   |       63 |     59 |    -12.53 |     30.16 |           0.37  |             883.41 |        0.13 |      12.66 |     27.91 |     27.84 |          240   |     -19.43 |       -5.62 |
| rejected_12h_sweep    | vol_2R_4h           | 2026_H2_seen_recheck |       40 |     37 |     -4.47 |     35    |           0.613 |             237.06 |        8.17 |      12.64 |     24.78 |     13.11 |          240   |     -12.47 |        3.87 |
| rejected_12h_sweep    | vol_timeout_4h      | 2025_train           |      122 |    107 |    -20.94 |     33.61 |           0.348 |            2560.31 |       -7.33 |      13.61 |     36.15 |     46.23 |          237.4 |     -32.24 |       -8.87 |
| rejected_12h_sweep    | vol_timeout_4h      | 2026_H1_validation   |       63 |     59 |    -12.53 |     30.16 |           0.37  |             883.41 |        0.13 |      12.66 |     27.91 |     27.84 |          240   |     -19.43 |       -5.62 |
| rejected_12h_sweep    | vol_timeout_4h      | 2026_H2_seen_recheck |       40 |     37 |     -4.47 |     35    |           0.613 |             237.06 |        8.17 |      12.64 |     24.78 |     13.11 |          240   |     -12.47 |        3.87 |
| rejected_12h_sweep    | vol_trail_4h        | 2025_train           |      122 |    107 |    -20.94 |     33.61 |           0.348 |            2560.31 |       -7.33 |      13.61 |     36.15 |     46.23 |          237.4 |     -32.24 |       -8.87 |
| rejected_12h_sweep    | vol_trail_4h        | 2026_H1_validation   |       63 |     59 |    -12.53 |     30.16 |           0.37  |             883.41 |        0.13 |      12.66 |     27.91 |     27.84 |          240   |     -19.43 |       -5.62 |
| rejected_12h_sweep    | vol_trail_4h        | 2026_H2_seen_recheck |       40 |     37 |     -4.47 |     35    |           0.613 |             237.06 |        8.17 |      12.64 |     24.78 |     13.11 |          240   |     -12.47 |        3.87 |

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
