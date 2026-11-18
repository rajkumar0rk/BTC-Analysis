# Stage 3 — Direction after hourly expansion: acceptance, rejection and OI

## Hypothesis and status
Stage 2 predicts volatility, not price direction. Test whether close location, 12-hour range acceptance or failed sweep makes the next hour directional enough to cover fees.
All thresholds and execution styles are fixed inside the versioned source. THIS IS EXPLORATORY HISTORICAL RESEARCH, NOT FOR LIVE TRADING.
2025 training; Jan-Jun 2026 validation; Jul-Oct 2026 previously inspected chronological recheck, NOT an independent holdout.

## Next-hour directional gross outcomes (a descriptive forecast, not tradable P&L)
| rule                              | period       |    n |   mean |   win_pct |   days |   bootstrap_mean_95_low |   bootstrap_mean_95_high |
|:----------------------------------|:-------------|-----:|-------:|----------:|-------:|------------------------:|-------------------------:|
| accepted_12h_breakout             | recheck_seen |   90 |  4.933 |     53.33 |     63 |                  -0.13  |                   10.316 |
| accepted_12h_breakout             | train        |  277 |  3.158 |     47.29 |    187 |                  -0.456 |                    6.942 |
| accepted_12h_breakout             | validation   |  127 |  0.547 |     43.31 |     87 |                  -3.369 |                    4.521 |
| accepted_12h_breakout__oi_falling | recheck_seen |   58 |  7.322 |     58.62 |     46 |                  -0.207 |                   15.175 |
| accepted_12h_breakout__oi_falling | train        |  150 |  2.779 |     46.67 |    123 |                  -1.923 |                    7.359 |
| accepted_12h_breakout__oi_falling | validation   |   79 |  2.896 |     45.57 |     61 |                  -2.112 |                    7.797 |
| accepted_12h_breakout__oi_rising  | recheck_seen |    4 | -0.075 |     50    |      3 |                 nan     |                  nan     |
| accepted_12h_breakout__oi_rising  | train        |   21 |  9.264 |     57.14 |     21 |                  -4.613 |                   24.296 |
| accepted_12h_breakout__oi_rising  | validation   |    7 |  6.664 |     42.86 |      7 |                 nan     |                  nan     |
| expansion_fade                    | recheck_seen |  503 | -0.874 |     51.89 |    125 |                  -2.305 |                    0.379 |
| expansion_fade                    | train        | 1032 | -1.271 |     53.1  |    298 |                  -3.155 |                    0.791 |
| expansion_fade                    | validation   |  610 | -0.083 |     53.44 |    162 |                  -1.533 |                    1.459 |
| expansion_follow                  | recheck_seen |  503 |  0.874 |     48.11 |    125 |                  -0.379 |                    2.305 |
| expansion_follow                  | train        | 1032 |  1.271 |     46.71 |    298 |                  -0.791 |                    3.155 |
| expansion_follow                  | validation   |  610 |  0.083 |     46.39 |    162 |                  -1.459 |                    1.533 |
| rejected_12h_sweep                | recheck_seen |   42 |  6.014 |     64.29 |     37 |                  -0.729 |                   13.867 |
| rejected_12h_sweep                | train        |  130 | -2.588 |     51.54 |    107 |                  -7.485 |                    1.392 |
| rejected_12h_sweep                | validation   |   64 |  1.67  |     46.88 |     59 |                  -2.978 |                    5.889 |
| rejected_12h_sweep__oi_falling    | recheck_seen |   19 |  6.532 |     63.16 |     19 |                 nan     |                  nan     |
| rejected_12h_sweep__oi_falling    | train        |   54 |  3.557 |     66.67 |     50 |                  -4.508 |                   10.799 |
| rejected_12h_sweep__oi_falling    | validation   |   27 |  2.869 |     55.56 |     26 |                  -5.187 |                    9.648 |
| rejected_12h_sweep__oi_rising     | recheck_seen |    3 | 13.467 |     66.67 |      3 |                 nan     |                  nan     |
| rejected_12h_sweep__oi_rising     | train        |    9 |  1.244 |     33.33 |      8 |                 nan     |                  nan     |
| rejected_12h_sweep__oi_rising     | validation   |    4 | -8.15  |     25    |      4 |                 nan     |                  nan     |
| strong_close_follow               | recheck_seen |  188 |  2.76  |     54.26 |     86 |                   0.435 |                    5.145 |
| strong_close_follow               | train        |  448 |  0.113 |     45.98 |    231 |                  -2.607 |                    2.577 |
| strong_close_follow               | validation   |  215 |  0.094 |     41.4  |    115 |                  -2.685 |                    2.893 |
| strong_close_follow__oi_falling   | recheck_seen |   67 |  4.325 |     58.21 |     51 |                  -0.944 |                   10     |
| strong_close_follow__oi_falling   | train        |  175 |  2.304 |     47.43 |    136 |                  -1.862 |                    6.68  |
| strong_close_follow__oi_falling   | validation   |   87 |  1.072 |     41.38 |     71 |                  -3.803 |                    6.201 |
| strong_close_follow__oi_rising    | recheck_seen |   22 | -3.089 |     36.36 |     16 |                 -11.594 |                    2.01  |
| strong_close_follow__oi_rising    | train        |   44 | -4.644 |     38.64 |     38 |                 -13.622 |                    4.871 |
| strong_close_follow__oi_rising    | validation   |   18 |  2.086 |     38.89 |     17 |                 nan     |                  nan     |
| weak_close_fade                   | recheck_seen |   31 | -0.361 |     45.16 |     26 |                  -4.435 |                    3.918 |
| weak_close_fade                   | train        |   51 |  5.505 |     60.78 |     43 |                  -0.408 |                   11.74  |
| weak_close_fade                   | validation   |   31 | -0.49  |     48.39 |     26 |                  -6.064 |                    5.213 |

## Immediate-entry execution after taker fees/GST and slippage (500 target, 350 stop, 60m max)
| rule                              | scheme    | period       |    n |    mean |   win_pct |   days |   profit_factor |   max_drawdown_pts |   avg_mfe_pts |   avg_mae_pts |   bootstrap_mean_95_low |   bootstrap_mean_95_high |
|:----------------------------------|:----------|:-------------|-----:|--------:|----------:|-------:|----------------:|-------------------:|--------------:|--------------:|------------------------:|-------------------------:|
| accepted_12h_breakout             | immediate | recheck_seen |   90 |  -7.719 |     22.22 |     63 |           0.426 |             749.97 |         19.81 |         11.96 |                 -12.772 |                   -2.371 |
| accepted_12h_breakout             | immediate | train        |  277 | -10.53  |     28.16 |    187 |           0.447 |            2916.76 |         31.98 |         22.34 |                 -14.096 |                   -6.699 |
| accepted_12h_breakout             | immediate | validation   |  127 | -12.051 |     23.62 |     87 |           0.268 |            1530.45 |         18.29 |         15.47 |                 -15.916 |                   -8.047 |
| accepted_12h_breakout__oi_falling | immediate | recheck_seen |   58 |  -5.317 |     24.14 |     46 |           0.604 |             389.46 |         23.71 |         12.76 |                 -12.828 |                    2.565 |
| accepted_12h_breakout__oi_falling | immediate | train        |  150 | -10.886 |     25.33 |    123 |           0.425 |            1654.41 |         34.08 |         22.34 |                 -15.588 |                   -6.333 |
| accepted_12h_breakout__oi_falling | immediate | validation   |   79 |  -9.745 |     21.52 |     61 |           0.337 |             769.89 |         18.96 |         13.82 |                 -14.75  |                   -4.802 |
| accepted_12h_breakout__oi_rising  | immediate | recheck_seen |    4 | -12.632 |     25    |      3 |           0.081 |              50.53 |         12.04 |          9.39 |                 nan     |                  nan     |
| accepted_12h_breakout__oi_rising  | immediate | train        |   21 |  -4.452 |     38.1  |     21 |           0.712 |             200.58 |         40.72 |         20.79 |                 -18.241 |                   10.58  |
| accepted_12h_breakout__oi_rising  | immediate | validation   |    7 |  -5.926 |     42.86 |      7 |           0.656 |             105.3  |         27.44 |         13.73 |                 nan     |                  nan     |
| expansion_fade                    | immediate | recheck_seen |  503 | -13.506 |     14.12 |    125 |           0.084 |            6793.68 |         10.54 |         12.77 |                 -14.932 |                  -12.262 |
| expansion_fade                    | immediate | train        | 1032 | -15.628 |     26.16 |    298 |           0.234 |           16158.3  |         21.96 |         25.7  |                 -17.933 |                  -13.162 |
| expansion_fade                    | immediate | validation   |  610 | -12.742 |     17.7  |    162 |           0.147 |            7786.57 |         13.26 |         15.27 |                 -14.231 |                  -11.145 |
| expansion_follow                  | immediate | recheck_seen |  503 | -11.759 |     14.31 |    125 |           0.162 |            5914.78 |         12.77 |         10.54 |                 -12.986 |                  -10.336 |
| expansion_follow                  | immediate | train        | 1032 | -12.309 |     24.71 |    298 |           0.353 |           12703.1  |         25.81 |         22.01 |                 -14.336 |                  -10.385 |
| expansion_follow                  | immediate | validation   |  610 | -12.576 |     17.05 |    162 |           0.181 |            7671.29 |         15.27 |         13.26 |                 -14.112 |                  -11.163 |
| rejected_12h_sweep                | immediate | recheck_seen |   42 |  -6.636 |     19.05 |     37 |           0.379 |             278.72 |         14.44 |          8.59 |                 -13.395 |                    1.117 |
| rejected_12h_sweep                | immediate | train        |  130 | -16.201 |     23.08 |    107 |           0.179 |            2106.8  |         21.11 |         25.56 |                 -21.135 |                  -12.207 |
| rejected_12h_sweep                | immediate | validation   |   64 | -10.988 |     20.31 |     59 |           0.237 |             717.46 |         15.6  |         14.21 |                 -15.704 |                   -6.717 |
| rejected_12h_sweep__oi_falling    | immediate | recheck_seen |   19 |  -6.055 |     15.79 |     19 |           0.488 |             131.07 |         15.38 |         10.51 |                 nan     |                  nan     |
| rejected_12h_sweep__oi_falling    | immediate | train        |   54 | -10.097 |     31.48 |     50 |           0.32  |             565.74 |         26.29 |         19.36 |                 -18.241 |                   -2.819 |
| rejected_12h_sweep__oi_falling    | immediate | validation   |   27 |  -9.772 |     18.52 |     26 |           0.265 |             290.77 |         17.32 |         15.1  |                 -17.84  |                   -2.99  |
| rejected_12h_sweep__oi_rising     | immediate | recheck_seen |    3 |   0.547 |     33.33 |      3 |           1.049 |              29.58 |         27.83 |         11.42 |                 nan     |                  nan     |
| rejected_12h_sweep__oi_rising     | immediate | train        |    9 | -12.254 |     22.22 |      8 |           0.299 |             149.83 |         22.42 |         17.84 |                 nan     |                  nan     |
| rejected_12h_sweep__oi_rising     | immediate | validation   |    4 | -20.5   |      0    |      4 |           0     |              82    |          5.5  |         13.91 |                 nan     |                  nan     |
| strong_close_follow               | immediate | recheck_seen |  188 |  -9.857 |     19.15 |     86 |           0.22  |            1853.16 |         14.52 |          9.78 |                 -12.161 |                   -7.484 |
| strong_close_follow               | immediate | train        |  448 | -13.534 |     26.12 |    231 |           0.334 |            6063.39 |         27.18 |         24.05 |                 -16.219 |                  -11.031 |
| strong_close_follow               | immediate | validation   |  215 | -12.485 |     19.07 |    115 |           0.243 |            2684.18 |         16.53 |         14.26 |                 -15.276 |                   -9.667 |
| strong_close_follow__oi_falling   | immediate | recheck_seen |   67 |  -8.278 |     17.91 |     51 |           0.387 |             647.22 |         18.86 |         10.89 |                 -13.519 |                   -2.638 |
| strong_close_follow__oi_falling   | immediate | train        |  175 | -11.349 |     26.29 |    136 |           0.402 |            1986.06 |         32.22 |         21.82 |                 -15.501 |                   -6.92  |
| strong_close_follow__oi_falling   | immediate | validation   |   87 | -11.505 |     16.09 |     71 |           0.284 |            1000.97 |         17.62 |         14.14 |                 -16.475 |                   -6.352 |
| strong_close_follow__oi_rising    | immediate | recheck_seen |   22 | -15.681 |      9.09 |     16 |           0.051 |             344.98 |          8.55 |         13.11 |                 -24.202 |                  -10.415 |
| strong_close_follow__oi_rising    | immediate | train        |   44 | -18.037 |     20.45 |     38 |           0.224 |             818.5  |         23.6  |         28.74 |                 -27.092 |                   -8.525 |
| strong_close_follow__oi_rising    | immediate | validation   |   18 | -10.435 |     22.22 |     17 |           0.365 |             231.41 |         17.92 |         12.32 |                 nan     |                  nan     |
| weak_close_fade                   | immediate | recheck_seen |   31 | -12.988 |     12.9  |     26 |           0.053 |             402.64 |          9.98 |         10.24 |                 -17.107 |                   -8.792 |
| weak_close_fade                   | immediate | train        |   51 |  -8.001 |     27.45 |     43 |           0.397 |             412.36 |         23.66 |         22.34 |                 -13.931 |                   -1.79  |
| weak_close_fade                   | immediate | validation   |   31 | -13.127 |     16.13 |     26 |           0.105 |             409.28 |         13.5  |         14.39 |                 -18.823 |                   -7.404 |

## Confirmation at first completed 5m close; entry at minute 5 open
| rule                              | scheme     | period       |   n |    mean |   win_pct |   days |   profit_factor |   max_drawdown_pts |   avg_mfe_pts |   avg_mae_pts |   bootstrap_mean_95_low |   bootstrap_mean_95_high |
|:----------------------------------|:-----------|:-------------|----:|--------:|----------:|-------:|----------------:|-------------------:|--------------:|--------------:|------------------------:|-------------------------:|
| accepted_12h_breakout             | 5m_confirm | recheck_seen |  40 |  -9.812 |     22.5  |     32 |           0.328 |             424.91 |         18.05 |         13.19 |                 -16.216 |                   -3.266 |
| accepted_12h_breakout             | 5m_confirm | train        | 131 | -13.608 |     27.48 |    106 |           0.392 |            1782.7  |         30.91 |         24.32 |                 -21.125 |                   -6.68  |
| accepted_12h_breakout             | 5m_confirm | validation   |  60 | -12.813 |     23.33 |     49 |           0.238 |             768.81 |         16.46 |         15.24 |                 -18.049 |                   -7.634 |
| accepted_12h_breakout__oi_falling | 5m_confirm | recheck_seen |  27 |  -7.981 |     22.22 |     23 |           0.448 |             279.05 |         21.18 |         13.49 |                 -17.77  |                    1.091 |
| accepted_12h_breakout__oi_falling | 5m_confirm | train        |  74 | -17.392 |     16.22 |     66 |           0.294 |            1341.57 |         28.44 |         25.64 |                 -26.33  |                   -7.81  |
| accepted_12h_breakout__oi_falling | 5m_confirm | validation   |  40 | -10.665 |     22.5  |     35 |           0.324 |             426.61 |         16.6  |         13.22 |                 -16.833 |                   -4.094 |
| accepted_12h_breakout__oi_rising  | 5m_confirm | recheck_seen |   1 |   1.878 |    100    |      1 |         nan     |               0    |         19.95 |          1.45 |                 nan     |                  nan     |
| accepted_12h_breakout__oi_rising  | 5m_confirm | train        |  13 |  -3.788 |     53.85 |     13 |           0.753 |             125.43 |         41.77 |         21.44 |                 nan     |                  nan     |
| accepted_12h_breakout__oi_rising  | 5m_confirm | validation   |   4 |  -5.58  |     50    |      4 |           0.461 |              37.67 |         23.36 |          6.95 |                 nan     |                  nan     |
| expansion_fade                    | 5m_confirm | recheck_seen | 282 | -13.112 |     10.64 |    110 |           0.062 |            3697.69 |          9.12 |         10.93 |                 -14.778 |                  -11.512 |
| expansion_fade                    | 5m_confirm | train        | 556 | -16.669 |     22.84 |    250 |           0.181 |            9267.94 |         18.86 |         23.05 |                 -19.319 |                  -14.016 |
| expansion_fade                    | 5m_confirm | validation   | 298 | -13.159 |     16.11 |    137 |           0.117 |            3921.31 |         11.73 |         13.73 |                 -14.939 |                  -11.278 |
| expansion_follow                  | 5m_confirm | recheck_seen | 216 | -11.468 |     13.43 |     98 |           0.168 |            2477.09 |         12.94 |         10.84 |                 -13.762 |                   -9.021 |
| expansion_follow                  | 5m_confirm | train        | 473 | -13.483 |     24.1  |    217 |           0.31  |            6377.53 |         25.08 |         21.22 |                 -16.119 |                  -10.561 |
| expansion_follow                  | 5m_confirm | validation   | 310 | -13.336 |     15.81 |    129 |           0.16  |            4134.01 |         14.05 |         13.61 |                 -15.357 |                  -11.228 |
| rejected_12h_sweep                | 5m_confirm | recheck_seen |  18 |  -8.505 |     11.11 |     18 |           0.184 |             153.09 |         10.53 |          6.89 |                 nan     |                  nan     |
| rejected_12h_sweep                | 5m_confirm | train        |  58 | -19.318 |     12.07 |     53 |           0.107 |            1120.43 |         18.86 |         23.59 |                 -25.498 |                  -13.212 |
| rejected_12h_sweep                | 5m_confirm | validation   |  34 | -11.991 |     26.47 |     33 |           0.193 |             407.68 |         13.34 |         13.32 |                 -17.368 |                   -6.203 |
| rejected_12h_sweep__oi_falling    | 5m_confirm | recheck_seen |   7 | -11.006 |      0    |      7 |           0     |              77.04 |          7.59 |          7.39 |                 nan     |                  nan     |
| rejected_12h_sweep__oi_falling    | 5m_confirm | train        |  30 | -14.441 |     16.67 |     29 |           0.143 |             433.23 |         23.15 |         20.23 |                 -22.592 |                   -6.936 |
| rejected_12h_sweep__oi_falling    | 5m_confirm | validation   |  13 | -13.021 |     15.38 |     13 |           0.184 |             169.27 |         11.53 |         12.67 |                 nan     |                  nan     |
| rejected_12h_sweep__oi_rising     | 5m_confirm | recheck_seen |   2 |  12.638 |     50    |      2 |           4.702 |               6.83 |         33.4  |         11.3  |                 nan     |                  nan     |
| rejected_12h_sweep__oi_rising     | 5m_confirm | train        |   6 | -18.776 |     16.67 |      6 |           0.21  |             129.74 |         18.7  |         22.18 |                 nan     |                  nan     |
| rejected_12h_sweep__oi_rising     | 5m_confirm | validation   |   2 | -21.543 |      0    |      2 |           0     |              43.09 |          5.75 |         14.93 |                 nan     |                  nan     |
| strong_close_follow               | 5m_confirm | recheck_seen |  81 | -11.71  |     14.81 |     51 |           0.115 |             948.47 |         12.84 |         10.94 |                 -15.299 |                   -8.654 |
| strong_close_follow               | 5m_confirm | train        | 193 | -14.104 |     26.42 |    135 |           0.327 |            2722.01 |         27.03 |         22.82 |                 -18.239 |                   -9.506 |
| strong_close_follow               | 5m_confirm | validation   | 106 | -11.816 |     20.75 |     72 |           0.224 |            1252.5  |         15.41 |         12.7  |                 -15.075 |                   -8.149 |
| strong_close_follow__oi_falling   | 5m_confirm | recheck_seen |  31 | -10.235 |     16.13 |     26 |           0.215 |             380.84 |         15.64 |         10.97 |                 -15.664 |                   -4.025 |
| strong_close_follow__oi_falling   | 5m_confirm | train        |  83 | -16.029 |     18.07 |     74 |           0.294 |            1388.89 |         27.89 |         25.08 |                 -22.98  |                   -8.388 |
| strong_close_follow__oi_falling   | 5m_confirm | validation   |  43 | -11.297 |     18.6  |     39 |           0.303 |             512.01 |         16.2  |         12.22 |                 -17.349 |                   -4.584 |
| strong_close_follow__oi_rising    | 5m_confirm | recheck_seen |   8 | -16.722 |     25    |      8 |           0.102 |             133.77 |         12.12 |         18.88 |                 nan     |                  nan     |
| strong_close_follow__oi_rising    | 5m_confirm | train        |  16 | -14.084 |     31.25 |     16 |           0.328 |             251.68 |         25.31 |         23.33 |                 nan     |                  nan     |
| strong_close_follow__oi_rising    | 5m_confirm | validation   |   8 | -11.146 |     25    |      8 |           0.176 |             108.23 |         15.36 |         10.34 |                 nan     |                  nan     |
| weak_close_fade                   | 5m_confirm | recheck_seen |  14 | -16.86  |      0    |     13 |           0     |             236.04 |          7.94 |         10.71 |                 nan     |                  nan     |
| weak_close_fade                   | 5m_confirm | train        |  26 | -11.23  |     19.23 |     23 |           0.333 |             311.42 |         21.11 |         20.96 |                 -19.589 |                   -1.741 |
| weak_close_fade                   | 5m_confirm | validation   |  16 | -12.352 |     18.75 |     16 |           0.057 |             197.64 |         10.77 |         11.56 |                 nan     |                  nan     |

## OI incremental contrast against price-only parent (not causal identification)
| period       | base                  | filter     |   n_base |   n_filter |   base_accuracy_pct |   filter_accuracy_pct |   accuracy_delta_pp |   base_mean_gross_pts |   filter_mean_gross_pts |
|:-------------|:----------------------|:-----------|---------:|-----------:|--------------------:|----------------------:|--------------------:|----------------------:|------------------------:|
| recheck_seen | strong_close_follow   | oi_rising  |      188 |         22 |               54.26 |                 36.36 |              -17.89 |                  2.76 |                   -3.09 |
| recheck_seen | strong_close_follow   | oi_falling |      188 |         67 |               54.26 |                 58.21 |                3.95 |                  2.76 |                    4.33 |
| recheck_seen | accepted_12h_breakout | oi_rising  |       90 |          4 |               53.33 |                 50    |               -3.33 |                  4.93 |                   -0.08 |
| recheck_seen | accepted_12h_breakout | oi_falling |       90 |         58 |               53.33 |                 58.62 |                5.29 |                  4.93 |                    7.32 |
| recheck_seen | rejected_12h_sweep    | oi_rising  |       42 |          3 |               64.29 |                 66.67 |                2.38 |                  6.01 |                   13.47 |
| recheck_seen | rejected_12h_sweep    | oi_falling |       42 |         19 |               64.29 |                 63.16 |               -1.13 |                  6.01 |                    6.53 |
| train        | strong_close_follow   | oi_rising  |      448 |         44 |               45.98 |                 38.64 |               -7.35 |                  0.11 |                   -4.64 |
| train        | strong_close_follow   | oi_falling |      448 |        175 |               45.98 |                 47.43 |                1.45 |                  0.11 |                    2.3  |
| train        | accepted_12h_breakout | oi_rising  |      277 |         21 |               47.29 |                 57.14 |                9.85 |                  3.16 |                    9.26 |
| train        | accepted_12h_breakout | oi_falling |      277 |        150 |               47.29 |                 46.67 |               -0.63 |                  3.16 |                    2.78 |
| train        | rejected_12h_sweep    | oi_rising  |      130 |          9 |               51.54 |                 33.33 |              -18.21 |                 -2.59 |                    1.24 |
| train        | rejected_12h_sweep    | oi_falling |      130 |         54 |               51.54 |                 66.67 |               15.13 |                 -2.59 |                    3.56 |
| validation   | strong_close_follow   | oi_rising  |      215 |         18 |               41.4  |                 38.89 |               -2.51 |                  0.09 |                    2.09 |
| validation   | strong_close_follow   | oi_falling |      215 |         87 |               41.4  |                 41.38 |               -0.02 |                  0.09 |                    1.07 |
| validation   | accepted_12h_breakout | oi_rising  |      127 |          7 |               43.31 |                 42.86 |               -0.45 |                  0.55 |                    6.66 |
| validation   | accepted_12h_breakout | oi_falling |      127 |         79 |               43.31 |                 45.57 |                2.26 |                  0.55 |                    2.9  |
| validation   | rejected_12h_sweep    | oi_rising  |       64 |          4 |               46.88 |                 25    |              -21.88 |                  1.67 |                   -8.15 |
| validation   | rejected_12h_sweep    | oi_falling |       64 |         27 |               46.88 |                 55.56 |                8.68 |                  1.67 |                    2.87 |

## Limitations
- 2026 July-Oct is previously seen, NOT a globally untouched holdout
- L1 bid/ask historical spread and market impact unavailable; simulated fills only
- OI is descriptive positioning proxy, not observed institutional trades
- Funding for sub-hour holds not reconstructed; additional real cost possible
- Multiple variants and repeated research create selection bias
- BTC points are not account USD; sizes, collateral and liquidation excluded
- Day bootstrap intervals unadjusted for multiple hypothesis tests
- Overlapping strategy variants must NEVER be aggregated as independent returns

MFE and MAE are derived from 1m OHLC and are upper-bound-like paths within the exit minute; stop-first conservative where both limits touch.
Full ledgers and quality notes are saved alongside this report.
No positive edge should be claimed without post-selection truly forward observations, realistic quote-based fills and independent robustness replication.
