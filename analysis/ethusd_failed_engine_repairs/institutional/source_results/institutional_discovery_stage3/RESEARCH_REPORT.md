# Stage 3 — Direction after hourly expansion: acceptance, rejection and OI

## Hypothesis and status
Stage 2 predicts volatility, not price direction. Test whether close location, 12-hour range acceptance or failed sweep makes the next hour directional enough to cover fees.
All thresholds and execution styles are fixed inside the versioned source. THIS IS EXPLORATORY HISTORICAL RESEARCH, NOT FOR LIVE TRADING.
2025 training; Jan-Jun 2026 validation; Jul-Oct 2026 previously inspected chronological recheck, NOT an independent holdout.

## Next-hour directional gross outcomes (a descriptive forecast, not tradable P&L)
| rule                              | period       |    n |     mean |   win_pct |   days |   bootstrap_mean_95_low |   bootstrap_mean_95_high |
|:----------------------------------|:-------------|-----:|---------:|----------:|-------:|------------------------:|-------------------------:|
| accepted_12h_breakout             | recheck_seen |   90 |  138.303 |     53.33 |     63 |                  -3.636 |                  289.234 |
| accepted_12h_breakout             | train        |  277 |   88.541 |     47.29 |    187 |                 -12.788 |                  194.639 |
| accepted_12h_breakout             | validation   |  127 |   15.343 |     43.31 |     87 |                 -94.468 |                  126.77  |
| accepted_12h_breakout__oi_falling | recheck_seen |   58 |  205.302 |     58.62 |     46 |                  -5.798 |                  425.463 |
| accepted_12h_breakout__oi_falling | train        |  150 |   77.916 |     46.67 |    123 |                 -53.913 |                  206.328 |
| accepted_12h_breakout__oi_falling | validation   |   79 |   81.185 |     45.57 |     61 |                 -59.213 |                  218.595 |
| accepted_12h_breakout__oi_rising  | recheck_seen |    4 |   -2.103 |     50    |      3 |                 nan     |                  nan     |
| accepted_12h_breakout__oi_rising  | train        |   21 |  259.747 |     57.14 |     21 |                -129.336 |                  681.193 |
| accepted_12h_breakout__oi_rising  | validation   |    7 |  186.85  |     42.86 |      7 |                 nan     |                  nan     |
| expansion_fade                    | recheck_seen |  504 |  -24.452 |     51.79 |    125 |                 -64.389 |                   10.593 |
| expansion_fade                    | train        | 1033 |  -35.663 |     53.05 |    298 |                 -88.463 |                   22.093 |
| expansion_fade                    | validation   |  609 |   -4.065 |     53.37 |    162 |                 -44.945 |                   39.322 |
| expansion_follow                  | recheck_seen |  504 |   24.452 |     48.21 |    125 |                 -10.593 |                   64.389 |
| expansion_follow                  | train        | 1033 |   35.663 |     46.76 |    298 |                 -22.093 |                   88.463 |
| expansion_follow                  | validation   |  609 |    4.065 |     46.47 |    162 |                 -39.322 |                   44.945 |
| rejected_12h_sweep                | recheck_seen |   42 |  168.626 |     64.29 |     37 |                 -20.425 |                  388.809 |
| rejected_12h_sweep                | train        |  130 |  -72.574 |     51.54 |    107 |                -209.856 |                   39.038 |
| rejected_12h_sweep                | validation   |   64 |   46.809 |     46.88 |     59 |                 -83.496 |                  165.116 |
| rejected_12h_sweep__oi_falling    | recheck_seen |   19 |  183.129 |     63.16 |     19 |                 nan     |                  nan     |
| rejected_12h_sweep__oi_falling    | train        |   54 |   99.741 |     66.67 |     50 |                -126.38  |                  302.767 |
| rejected_12h_sweep__oi_falling    | validation   |   27 |   80.426 |     55.56 |     26 |                -145.42  |                  270.509 |
| rejected_12h_sweep__oi_rising     | recheck_seen |    3 |  377.572 |     66.67 |      3 |                 nan     |                  nan     |
| rejected_12h_sweep__oi_rising     | train        |    9 |   34.891 |     33.33 |      8 |                 nan     |                  nan     |
| rejected_12h_sweep__oi_rising     | validation   |    4 | -228.506 |     25    |      4 |                 nan     |                  nan     |
| strong_close_follow               | recheck_seen |  188 |   77.379 |     54.26 |     86 |                  12.199 |                  144.26  |
| strong_close_follow               | train        |  449 |    3.31  |     46.1  |    231 |                 -72.938 |                   72.227 |
| strong_close_follow               | validation   |  215 |    2.634 |     41.4  |    115 |                 -75.28  |                   81.125 |
| strong_close_follow__oi_falling   | recheck_seen |   67 |  121.273 |     58.21 |     51 |                 -26.46  |                  280.367 |
| strong_close_follow__oi_falling   | train        |  176 |   64.614 |     47.73 |    136 |                 -51.404 |                  186.766 |
| strong_close_follow__oi_falling   | validation   |   87 |   30.068 |     41.38 |     71 |                -106.619 |                  173.872 |
| strong_close_follow__oi_rising    | recheck_seen |   22 |  -86.598 |     36.36 |     16 |                -325.061 |                   56.367 |
| strong_close_follow__oi_rising    | train        |   44 | -130.215 |     38.64 |     38 |                -381.916 |                  136.569 |
| strong_close_follow__oi_rising    | validation   |   18 |   58.489 |     38.89 |     17 |                 nan     |                  nan     |
| weak_close_fade                   | recheck_seen |   31 |  -10.13  |     45.16 |     26 |                -124.34  |                  109.843 |
| weak_close_fade                   | train        |   51 |  154.344 |     60.78 |     43 |                 -11.443 |                  329.153 |
| weak_close_fade                   | validation   |   31 |  -13.747 |     48.39 |     26 |                -170.013 |                  146.157 |

## Immediate-entry execution after taker fees/GST and slippage (500 target, 350 stop, 60m max)
| rule                              | scheme    | period       |    n |     mean |   win_pct |   days |   profit_factor |   max_drawdown_pts |   avg_mfe_pts |   avg_mae_pts |   bootstrap_mean_95_low |   bootstrap_mean_95_high |
|:----------------------------------|:----------|:-------------|-----:|---------:|----------:|-------:|----------------:|-------------------:|--------------:|--------------:|------------------------:|-------------------------:|
| accepted_12h_breakout             | immediate | recheck_seen |   90 |  -21.539 |     45.56 |     63 |           0.873 |            4585.48 |        366.98 |        225    |                 -87.481 |                   51.691 |
| accepted_12h_breakout             | immediate | train        |  277 | -110.571 |     40.79 |    187 |           0.573 |           31941.9  |        376.98 |        298.85 |                -158.894 |                  -62.795 |
| accepted_12h_breakout             | immediate | validation   |  127 |  -90.884 |     34.65 |     87 |           0.589 |           11928.4  |        310.09 |        273.77 |                -150.978 |                  -21.331 |
| accepted_12h_breakout__oi_falling | immediate | recheck_seen |   58 |   -0.344 |     48.28 |     46 |           0.998 |            2494.96 |        405.89 |        227.49 |                 -99.262 |                  101.456 |
| accepted_12h_breakout__oi_falling | immediate | train        |  150 | -108.691 |     40.67 |    123 |           0.571 |           16657    |        405.6  |        313.9  |                -169.886 |                  -48.327 |
| accepted_12h_breakout__oi_falling | immediate | validation   |   79 |  -79.381 |     36.71 |     61 |           0.628 |            6657.22 |        317.82 |        261.26 |                -164.269 |                  -10.863 |
| accepted_12h_breakout__oi_rising  | immediate | recheck_seen |    4 |  -19.634 |     50    |      3 |           0.856 |             545.68 |        310.87 |        196.61 |                 nan     |                  nan     |
| accepted_12h_breakout__oi_rising  | immediate | train        |   21 | -100.021 |     42.86 |     21 |           0.623 |            2792.73 |        352.07 |        269.29 |                -267.724 |                   66.765 |
| accepted_12h_breakout__oi_rising  | immediate | validation   |    7 |  -22.213 |     42.86 |      7 |           0.889 |             981.59 |        328.44 |        206.48 |                 nan     |                  nan     |
| expansion_fade                    | immediate | recheck_seen |  504 |  -86.347 |     38.1  |    125 |           0.516 |           43806.2  |        241.41 |        241.38 |                -109.197 |                  -61.454 |
| expansion_fade                    | immediate | train        | 1033 | -103.196 |     41.24 |    298 |           0.578 |          108255    |        325.83 |        309.05 |                -129.718 |                  -77.884 |
| expansion_fade                    | immediate | validation   |  609 | -104.422 |     39.08 |    162 |           0.484 |           65222.7  |        260.11 |        264.14 |                -129.055 |                  -77.06  |
| expansion_follow                  | immediate | recheck_seen |  504 |  -72.262 |     37.5  |    125 |           0.592 |           37662.8  |        269.76 |        224.79 |                 -97.245 |                  -46.556 |
| expansion_follow                  | immediate | train        | 1033 | -115.208 |     39.3  |    298 |           0.539 |          119423    |        341.54 |        299.77 |                -139.531 |                  -91.882 |
| expansion_follow                  | immediate | validation   |  609 |  -85.652 |     37.27 |    162 |           0.569 |           52161.9  |        292.32 |        251.4  |                -111.999 |                  -60.181 |
| rejected_12h_sweep                | immediate | recheck_seen |   42 |  -48.958 |     42.86 |     37 |           0.678 |            2422.68 |        252.5  |        210.05 |                -131.348 |                   30.893 |
| rejected_12h_sweep                | immediate | train        |  130 | -156.16  |     35.38 |    107 |           0.431 |           21081.4  |        308.04 |        381.17 |                -227.852 |                  -90.341 |
| rejected_12h_sweep                | immediate | validation   |   64 | -141.595 |     32.81 |     59 |           0.399 |            9449.08 |        272.97 |        268.74 |                -215.603 |                  -62.364 |
| rejected_12h_sweep__oi_falling    | immediate | recheck_seen |   19 | -111.216 |     31.58 |     19 |           0.402 |            2789.88 |        215.45 |        245.03 |                 nan     |                  nan     |
| rejected_12h_sweep__oi_falling    | immediate | train        |   54 |  -12.391 |     50    |     50 |           0.936 |            4803.59 |        377.52 |        301.53 |                -132.545 |                   93.891 |
| rejected_12h_sweep__oi_falling    | immediate | validation   |   27 | -143.915 |     33.33 |     26 |           0.391 |            3885.7  |        268.12 |        282.87 |                -262.093 |                   -4.377 |
| rejected_12h_sweep__oi_rising     | immediate | recheck_seen |    3 |   39.259 |     66.67 |      3 |           1.268 |             439.53 |        464.02 |        284.11 |                 nan     |                  nan     |
| rejected_12h_sweep__oi_rising     | immediate | train        |    9 | -236.926 |     22.22 |      8 |           0.264 |            2132.33 |        276.33 |        334.58 |                 nan     |                  nan     |
| rejected_12h_sweep__oi_rising     | immediate | validation   |    4 | -291.179 |      0    |      4 |           0     |            1164.71 |        154.21 |        287.03 |                 nan     |                  nan     |
| strong_close_follow               | immediate | recheck_seen |  188 |  -16.837 |     45.21 |     86 |           0.886 |            7207.42 |        313.21 |        201.37 |                 -67.021 |                   26.542 |
| strong_close_follow               | immediate | train        |  449 | -118.433 |     40.09 |    231 |           0.547 |           53176.5  |        340.7  |        312.49 |                -154.295 |                  -81.061 |
| strong_close_follow               | immediate | validation   |  215 | -108.617 |     33.49 |    115 |           0.506 |           23352.7  |        287.08 |        266.81 |                -149.308 |                  -63.389 |
| strong_close_follow__oi_falling   | immediate | recheck_seen |   67 |   -0.949 |     46.27 |     51 |           0.993 |            3372.08 |        362.04 |        199.9  |                 -76.571 |                   70.735 |
| strong_close_follow__oi_falling   | immediate | train        |  176 |  -81.927 |     44.32 |    136 |           0.66  |           14419.2  |        393.71 |        302.61 |                -139.244 |                  -19.262 |
| strong_close_follow__oi_falling   | immediate | validation   |   87 | -114.477 |     32.18 |     71 |           0.5   |            9959.5  |        292.83 |        277.46 |                -189.551 |                  -36.916 |
| strong_close_follow__oi_rising    | immediate | recheck_seen |   22 | -113.843 |     36.36 |     16 |           0.375 |            2504.54 |        216.84 |        248.51 |                -230.714 |                  -17.755 |
| strong_close_follow__oi_rising    | immediate | train        |   44 | -199.628 |     29.55 |     38 |           0.352 |            9174.74 |        253.55 |        317.49 |                -297.786 |                 -106.852 |
| strong_close_follow__oi_rising    | immediate | validation   |   18 |  -99.356 |     33.33 |     17 |           0.547 |            2317.6  |        290.66 |        236.53 |                 nan     |                  nan     |
| weak_close_fade                   | immediate | recheck_seen |   31 |  -76.932 |     38.71 |     26 |           0.571 |            2384.89 |        247.32 |        224.53 |                -187.095 |                   30.108 |
| weak_close_fade                   | immediate | train        |   51 | -132.643 |     37.25 |     43 |           0.488 |            6926.97 |        314.95 |        343.1  |                -234.009 |                  -28.151 |
| weak_close_fade                   | immediate | validation   |   31 | -149.352 |     29.03 |     26 |           0.335 |            4644.19 |        231.81 |        261.47 |                -257.265 |                  -14.543 |

## Confirmation at first completed 5m close; entry at minute 5 open
| rule                              | scheme     | period       |   n |     mean |   win_pct |   days |   profit_factor |   max_drawdown_pts |   avg_mfe_pts |   avg_mae_pts |   bootstrap_mean_95_low |   bootstrap_mean_95_high |
|:----------------------------------|:-----------|:-------------|----:|---------:|----------:|-------:|----------------:|-------------------:|--------------:|--------------:|------------------------:|-------------------------:|
| accepted_12h_breakout             | 5m_confirm | recheck_seen |  40 |  -86.372 |     37.5  |     32 |           0.586 |            3471.16 |        299.23 |        247.75 |                -194.352 |                   11.902 |
| accepted_12h_breakout             | 5m_confirm | train        | 131 | -126.416 |     38.17 |    106 |           0.525 |           16632.2  |        354.2  |        327.73 |                -197.321 |                  -62.962 |
| accepted_12h_breakout             | 5m_confirm | validation   |  60 | -113.18  |     30    |     49 |           0.525 |            6790.83 |        279.25 |        274.65 |                -209.504 |                  -18.182 |
| accepted_12h_breakout__oi_falling | 5m_confirm | recheck_seen |  27 |  -82.718 |     37.04 |     23 |           0.581 |            2646.68 |        311.32 |        250.88 |                -205.387 |                   33.477 |
| accepted_12h_breakout__oi_falling | 5m_confirm | train        |  74 | -192.258 |     29.73 |     66 |           0.349 |           14227.1  |        317.54 |        351.81 |                -272.808 |                 -103.531 |
| accepted_12h_breakout__oi_falling | 5m_confirm | validation   |  40 | -102.527 |     30    |     35 |           0.55  |            4101.09 |        277.64 |        250.3  |                -209.776 |                    4.803 |
| accepted_12h_breakout__oi_rising  | 5m_confirm | recheck_seen |   1 |  427.761 |    100    |      1 |         nan     |               0    |        559.35 |         40.65 |                 nan     |                  nan     |
| accepted_12h_breakout__oi_rising  | 5m_confirm | train        |  13 |   54.178 |     61.54 |     13 |           1.304 |            1350.87 |        469.52 |        281.99 |                 nan     |                  nan     |
| accepted_12h_breakout__oi_rising  | 5m_confirm | validation   |   4 |   49.491 |     50    |      4 |           1.319 |             323.07 |        382.01 |        194.86 |                 nan     |                  nan     |
| expansion_fade                    | 5m_confirm | recheck_seen | 283 | -110.077 |     36.04 |    110 |           0.382 |           31682    |        210.52 |        232.22 |                -142.342 |                  -76.337 |
| expansion_fade                    | 5m_confirm | train        | 556 | -121.893 |     39.57 |    250 |           0.507 |           68153.4  |        304.48 |        295.62 |                -152.023 |                  -90.738 |
| expansion_fade                    | 5m_confirm | validation   | 298 |  -76.771 |     40.6  |    137 |           0.582 |           24222.8  |        257.51 |        238.64 |                -114.197 |                  -39.545 |
| expansion_follow                  | 5m_confirm | recheck_seen | 216 |  -84.558 |     34.72 |     98 |           0.539 |           19245.8  |        256.11 |        233.63 |                -119.392 |                  -51.667 |
| expansion_follow                  | 5m_confirm | train        | 474 |  -95.273 |     41.98 |    217 |           0.602 |           45765.8  |        348.42 |        290.83 |                -129.021 |                  -65.568 |
| expansion_follow                  | 5m_confirm | validation   | 309 | -122.308 |     29.13 |    129 |           0.442 |           37793.3  |        266.61 |        255.85 |                -159.235 |                  -77.525 |
| rejected_12h_sweep                | 5m_confirm | recheck_seen |  18 |  -36.25  |     44.44 |     18 |           0.731 |             907.51 |        241.67 |        184.5  |                 nan     |                  nan     |
| rejected_12h_sweep                | 5m_confirm | train        |  58 |  -68.533 |     43.1  |     53 |           0.677 |            5634.86 |        337.9  |        263.91 |                -157.649 |                   23.462 |
| rejected_12h_sweep                | 5m_confirm | validation   |  34 | -129.838 |     29.41 |     33 |           0.448 |            4465.71 |        248.5  |        246.65 |                -226.624 |                  -16.261 |
| rejected_12h_sweep__oi_falling    | 5m_confirm | recheck_seen |   7 |  -95.376 |     42.86 |      7 |           0.45  |            1050.53 |        210.68 |        186.85 |                 nan     |                  nan     |
| rejected_12h_sweep__oi_falling    | 5m_confirm | train        |  30 |   10.724 |     53.33 |     29 |           1.064 |            1390.48 |        404.53 |        235.33 |                -114.263 |                  127.529 |
| rejected_12h_sweep__oi_falling    | 5m_confirm | validation   |  13 | -112.879 |     30.77 |     13 |           0.479 |            1770.75 |        226.03 |        239.94 |                 nan     |                  nan     |
| rejected_12h_sweep__oi_rising     | 5m_confirm | recheck_seen |   2 |  241.538 |    100    |      2 |         nan     |               0    |        461.92 |        316.82 |                 nan     |                  nan     |
| rejected_12h_sweep__oi_rising     | 5m_confirm | train        |   6 | -175.327 |     33.33 |      6 |           0.421 |            1051.96 |        280.84 |        310.28 |                 nan     |                  nan     |
| rejected_12h_sweep__oi_rising     | 5m_confirm | validation   |   2 | -234.524 |      0    |      2 |           0     |             469.05 |        161.22 |        206.78 |                 nan     |                  nan     |
| strong_close_follow               | 5m_confirm | recheck_seen |  81 |  -56.675 |     40.74 |     51 |           0.659 |            4741.79 |        270.58 |        218.21 |                -125.791 |                   12.778 |
| strong_close_follow               | 5m_confirm | train        | 194 | -101.252 |     42.27 |    135 |           0.596 |           19714.6  |        350.46 |        308.82 |                -154.32  |                  -55.526 |
| strong_close_follow               | 5m_confirm | validation   | 106 | -106.124 |     29.25 |     72 |           0.508 |           11249.2  |        273.14 |        252.63 |                -163.72  |                  -43.638 |
| strong_close_follow__oi_falling   | 5m_confirm | recheck_seen |  31 |  -51.964 |     38.71 |     26 |           0.684 |            2374.06 |        283.27 |        221.22 |                -152.395 |                   60.34  |
| strong_close_follow__oi_falling   | 5m_confirm | train        |  84 | -149.687 |     35.71 |     75 |           0.45  |           12573.7  |        315.09 |        339.47 |                -228.033 |                  -63.609 |
| strong_close_follow__oi_falling   | 5m_confirm | validation   |  43 |  -95.325 |     27.91 |     39 |           0.55  |            4098.97 |        276.53 |        242.65 |                -198.83  |                    5.339 |
| strong_close_follow__oi_rising    | 5m_confirm | recheck_seen |   8 |  -75.418 |     50    |      8 |           0.655 |             914.25 |        282.65 |        252.86 |                 nan     |                  nan     |
| strong_close_follow__oi_rising    | 5m_confirm | train        |  16 |  -39.702 |     50    |     16 |           0.826 |            1725.98 |        374.56 |        263.9  |                 nan     |                  nan     |
| strong_close_follow__oi_rising    | 5m_confirm | validation   |   8 | -104.898 |     25    |      8 |           0.493 |            1656.76 |        294.04 |        251.81 |                 nan     |                  nan     |
| weak_close_fade                   | 5m_confirm | recheck_seen |  14 | -180.136 |     14.29 |     13 |           0.207 |            2521.9  |        222.7  |        239.22 |                 nan     |                  nan     |
| weak_close_fade                   | 5m_confirm | train        |  26 | -119.117 |     34.62 |     23 |           0.537 |            4736.05 |        278.97 |        272.61 |                -275.319 |                   21.913 |
| weak_close_fade                   | 5m_confirm | validation   |  16 | -124.479 |     31.25 |     16 |           0.414 |            1991.67 |        251.02 |        257.77 |                 nan     |                  nan     |

## OI incremental contrast against price-only parent (not causal identification)
| period       | base                  | filter     |   n_base |   n_filter |   base_accuracy_pct |   filter_accuracy_pct |   accuracy_delta_pp |   base_mean_gross_pts |   filter_mean_gross_pts |
|:-------------|:----------------------|:-----------|---------:|-----------:|--------------------:|----------------------:|--------------------:|----------------------:|------------------------:|
| recheck_seen | strong_close_follow   | oi_rising  |      188 |         22 |               54.26 |                 36.36 |              -17.89 |                 77.38 |                  -86.6  |
| recheck_seen | strong_close_follow   | oi_falling |      188 |         67 |               54.26 |                 58.21 |                3.95 |                 77.38 |                  121.27 |
| recheck_seen | accepted_12h_breakout | oi_rising  |       90 |          4 |               53.33 |                 50    |               -3.33 |                138.3  |                   -2.1  |
| recheck_seen | accepted_12h_breakout | oi_falling |       90 |         58 |               53.33 |                 58.62 |                5.29 |                138.3  |                  205.3  |
| recheck_seen | rejected_12h_sweep    | oi_rising  |       42 |          3 |               64.29 |                 66.67 |                2.38 |                168.63 |                  377.57 |
| recheck_seen | rejected_12h_sweep    | oi_falling |       42 |         19 |               64.29 |                 63.16 |               -1.13 |                168.63 |                  183.13 |
| train        | strong_close_follow   | oi_rising  |      449 |         44 |               46.1  |                 38.64 |               -7.47 |                  3.31 |                 -130.22 |
| train        | strong_close_follow   | oi_falling |      449 |        176 |               46.1  |                 47.73 |                1.62 |                  3.31 |                   64.61 |
| train        | accepted_12h_breakout | oi_rising  |      277 |         21 |               47.29 |                 57.14 |                9.85 |                 88.54 |                  259.75 |
| train        | accepted_12h_breakout | oi_falling |      277 |        150 |               47.29 |                 46.67 |               -0.63 |                 88.54 |                   77.92 |
| train        | rejected_12h_sweep    | oi_rising  |      130 |          9 |               51.54 |                 33.33 |              -18.21 |                -72.57 |                   34.89 |
| train        | rejected_12h_sweep    | oi_falling |      130 |         54 |               51.54 |                 66.67 |               15.13 |                -72.57 |                   99.74 |
| validation   | strong_close_follow   | oi_rising  |      215 |         18 |               41.4  |                 38.89 |               -2.51 |                  2.63 |                   58.49 |
| validation   | strong_close_follow   | oi_falling |      215 |         87 |               41.4  |                 41.38 |               -0.02 |                  2.63 |                   30.07 |
| validation   | accepted_12h_breakout | oi_rising  |      127 |          7 |               43.31 |                 42.86 |               -0.45 |                 15.34 |                  186.85 |
| validation   | accepted_12h_breakout | oi_falling |      127 |         79 |               43.31 |                 45.57 |                2.26 |                 15.34 |                   81.18 |
| validation   | rejected_12h_sweep    | oi_rising  |       64 |          4 |               46.88 |                 25    |              -21.88 |                 46.81 |                 -228.51 |
| validation   | rejected_12h_sweep    | oi_falling |       64 |         27 |               46.88 |                 55.56 |                8.68 |                 46.81 |                   80.43 |

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
