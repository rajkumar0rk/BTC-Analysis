# Stage 3 — Direction after hourly expansion: acceptance, rejection and OI

## Hypothesis and status
Stage 2 predicts volatility, not price direction. Test whether close location, 12-hour range acceptance or failed sweep makes the next hour directional enough to cover fees.
All thresholds and execution styles are fixed inside the versioned source. THIS IS EXPLORATORY HISTORICAL RESEARCH, NOT FOR LIVE TRADING.
2025 training; Jan-Jun 2026 validation; Jul-Oct 2026 previously inspected chronological recheck, NOT an independent holdout.

## Next-hour directional gross outcomes (a descriptive forecast, not tradable P&L)
| rule                              | period       |    n |     mean |   win_pct |   days |   bootstrap_mean_95_low |   bootstrap_mean_95_high |
|:----------------------------------|:-------------|-----:|---------:|----------:|-------:|------------------------:|-------------------------:|
| accepted_12h_breakout             | recheck_seen |   89 |   76.079 |     57.3  |     58 |                   2.377 |                  151.598 |
| accepted_12h_breakout             | train        |  304 |  -11.076 |     45.07 |    191 |                 -88.659 |                   69.296 |
| accepted_12h_breakout             | validation   |  147 |   -1.493 |     38.1  |     93 |                 -94.309 |                   74.542 |
| accepted_12h_breakout__oi_falling | recheck_seen |   47 |   82.255 |     59.57 |     37 |                  -6.905 |                  170.734 |
| accepted_12h_breakout__oi_falling | train        |  147 |   12.939 |     46.26 |    115 |                -109.722 |                  139.071 |
| accepted_12h_breakout__oi_falling | validation   |   75 |  -32.8   |     38.67 |     61 |                -134.336 |                   75.197 |
| accepted_12h_breakout__oi_rising  | recheck_seen |    8 |  164.25  |     37.5  |      7 |                 nan     |                  nan     |
| accepted_12h_breakout__oi_rising  | train        |   32 |  229.656 |     65.62 |     29 |                  66.613 |                  411.265 |
| accepted_12h_breakout__oi_rising  | validation   |   12 | -113.542 |     33.33 |     12 |                 nan     |                  nan     |
| expansion_fade                    | recheck_seen |  391 |   -8.789 |     50.64 |     95 |                 -42.362 |                   28.468 |
| expansion_fade                    | train        | 1153 |   17.171 |     52.12 |    286 |                 -15.001 |                   59.168 |
| expansion_fade                    | validation   |  593 |  -14.202 |     50.93 |    156 |                 -49.45  |                   24.536 |
| expansion_follow                  | recheck_seen |  391 |    8.789 |     49.36 |     95 |                 -28.468 |                   42.362 |
| expansion_follow                  | train        | 1153 |  -17.171 |     47.88 |    286 |                 -59.168 |                   15.001 |
| expansion_follow                  | validation   |  593 |   14.202 |     49.07 |    156 |                 -24.536 |                   49.45  |
| rejected_12h_sweep                | recheck_seen |   45 |   15.289 |     53.33 |     35 |                -114.499 |                  148.611 |
| rejected_12h_sweep                | train        |  164 |  -43.671 |     45.73 |    129 |                -118.633 |                   32.005 |
| rejected_12h_sweep                | validation   |   75 |   93.18  |     58.67 |     64 |                 -22.269 |                  222.389 |
| rejected_12h_sweep__oi_falling    | recheck_seen |   17 |  107.029 |     76.47 |     17 |                 nan     |                  nan     |
| rejected_12h_sweep__oi_falling    | train        |   76 |    0.309 |     50    |     71 |                -107.644 |                  110.868 |
| rejected_12h_sweep__oi_falling    | validation   |   30 |  217.067 |     60    |     28 |                  43.046 |                  456.679 |
| rejected_12h_sweep__oi_rising     | recheck_seen |    3 |  164     |     33.33 |      3 |                 nan     |                  nan     |
| rejected_12h_sweep__oi_rising     | train        |   13 | -254.692 |     30.77 |     12 |                 nan     |                  nan     |
| rejected_12h_sweep__oi_rising     | validation   |   10 |  104.5   |     60    |     10 |                 nan     |                  nan     |
| strong_close_follow               | recheck_seen |  170 |   35.632 |     54.12 |     73 |                 -15.54  |                   91.777 |
| strong_close_follow               | train        |  591 |  -35.032 |     46.53 |    247 |                 -91.289 |                   18.471 |
| strong_close_follow               | validation   |  256 |   -4.562 |     42.58 |    115 |                 -64.938 |                   55.6   |
| strong_close_follow__oi_falling   | recheck_seen |   65 |   23.385 |     53.85 |     45 |                 -61.859 |                  102.893 |
| strong_close_follow__oi_falling   | train        |  219 |  -26.537 |     45.66 |    165 |                -122.68  |                   66.805 |
| strong_close_follow__oi_falling   | validation   |  102 |   18.956 |     45.1  |     73 |                 -79.2   |                  140.089 |
| strong_close_follow__oi_rising    | recheck_seen |   20 |  111.075 |     45    |     16 |                -165.699 |                  392.352 |
| strong_close_follow__oi_rising    | train        |   61 |   -9.426 |     52.46 |     50 |                -204.568 |                  143.908 |
| strong_close_follow__oi_rising    | validation   |   26 | -100.519 |     38.46 |     26 |                -340.308 |                  136.512 |
| weak_close_fade                   | recheck_seen |   20 |   28.275 |     40    |     18 |                -158.196 |                  277.967 |
| weak_close_fade                   | train        |   48 |   99.76  |     47.92 |     41 |                 -91.2   |                  302.844 |
| weak_close_fade                   | validation   |   29 |  -71.431 |     48.28 |     24 |                -235.873 |                  124.677 |

## Immediate-entry execution after taker fees/GST and slippage (500 target, 350 stop, 60m max)
| rule                              | scheme    | period       |    n |     mean |   win_pct |   days |   profit_factor |   max_drawdown_pts |   avg_mfe_pts |   avg_mae_pts |   bootstrap_mean_95_low |   bootstrap_mean_95_high |
|:----------------------------------|:----------|:-------------|-----:|---------:|----------:|-------:|----------------:|-------------------:|--------------:|--------------:|------------------------:|-------------------------:|
| accepted_12h_breakout             | immediate | recheck_seen |   89 |  -53.754 |     37.08 |     58 |           0.637 |            6289.01 |        267.04 |        194.98 |                -104.493 |                   -3.337 |
| accepted_12h_breakout             | immediate | train        |  304 | -174.701 |     32.89 |    191 |           0.372 |           53495.8  |        303.23 |        298.22 |                -214.263 |                 -134.349 |
| accepted_12h_breakout             | immediate | validation   |  147 | -140.134 |     31.97 |     93 |           0.433 |           21359.9  |        276.19 |        268.85 |                -194.333 |                  -95.182 |
| accepted_12h_breakout__oi_falling | immediate | recheck_seen |   47 |  -53.19  |     38.3  |     37 |           0.661 |            4511.9  |        287.41 |        205.06 |                -137.504 |                   30.414 |
| accepted_12h_breakout__oi_falling | immediate | train        |  147 | -193.587 |     32.65 |    115 |           0.339 |           28963.9  |        314.87 |        299.57 |                -262.515 |                 -133.715 |
| accepted_12h_breakout__oi_falling | immediate | validation   |   75 |  -97.776 |     37.33 |     61 |           0.578 |            7713.92 |        296.19 |        254.87 |                -183.325 |                   -8.006 |
| accepted_12h_breakout__oi_rising  | immediate | recheck_seen |    8 |  -84.463 |     37.5  |      7 |           0.53  |            1120.2  |        258.69 |        218.62 |                 nan     |                  nan     |
| accepted_12h_breakout__oi_rising  | immediate | train        |   32 |   17.195 |     53.12 |     29 |           1.104 |            2329.74 |        384.17 |        286.69 |                 -98.794 |                  129.641 |
| accepted_12h_breakout__oi_rising  | immediate | validation   |   12 | -285.895 |      8.33 |     12 |           0.107 |            3430.74 |        185.75 |        320.33 |                 nan     |                  nan     |
| expansion_fade                    | immediate | recheck_seen |  391 |  -97.177 |     36.57 |     95 |           0.434 |           39063.7  |        214.45 |        213.78 |                -121.045 |                  -68.245 |
| expansion_fade                    | immediate | train        | 1153 | -124.337 |     37.99 |    286 |           0.486 |          144117    |        302.81 |        273.53 |                -144.621 |                 -100.804 |
| expansion_fade                    | immediate | validation   |  593 | -129.746 |     34.57 |    156 |           0.408 |           78477.7  |        251.31 |        264.65 |                -156.77  |                 -102.415 |
| expansion_follow                  | immediate | recheck_seen |  391 |  -96.133 |     33.5  |     95 |           0.462 |           39823.8  |        231.99 |        200.46 |                -128.11  |                  -68.606 |
| expansion_follow                  | immediate | train        | 1153 | -143.002 |     35.39 |    286 |           0.43  |          165922    |        297.05 |        276.89 |                -169.479 |                 -120.925 |
| expansion_follow                  | immediate | validation   |  593 |  -85.44  |     37.94 |    156 |           0.568 |           50690.4  |        292.22 |        238.39 |                -112.215 |                  -59.878 |
| rejected_12h_sweep                | immediate | recheck_seen |   45 |  -89.58  |     37.78 |     35 |           0.474 |            5105.3  |        212.88 |        183.63 |                -159.991 |                   -9.015 |
| rejected_12h_sweep                | immediate | train        |  164 | -175.795 |     31.71 |    129 |           0.365 |           29601.9  |        269.12 |        282.1  |                -234.345 |                 -119.546 |
| rejected_12h_sweep                | immediate | validation   |   75 |  -92.159 |     38.67 |     64 |           0.542 |            7295.67 |        290.16 |        234.15 |                -168.508 |                  -14.982 |
| rejected_12h_sweep__oi_falling    | immediate | recheck_seen |   17 |   -3.333 |     58.82 |     17 |           0.975 |            1205.98 |        253.71 |        172.85 |                 nan     |                  nan     |
| rejected_12h_sweep__oi_falling    | immediate | train        |   76 | -179.722 |     31.58 |     71 |           0.374 |           14586.8  |        270.42 |        291.64 |                -253.961 |                  -95.462 |
| rejected_12h_sweep__oi_falling    | immediate | validation   |   30 | -109.934 |     36.67 |     28 |           0.49  |            3345.97 |        284.02 |        236.58 |                -219.498 |                    4.653 |
| rejected_12h_sweep__oi_rising     | immediate | recheck_seen |    3 | -121.051 |     33.33 |      3 |           0.522 |             760.5  |        374.33 |        252.33 |                 nan     |                  nan     |
| rejected_12h_sweep__oi_rising     | immediate | train        |   13 | -243.991 |     30.77 |     12 |           0.219 |            3485.41 |        238    |        284.88 |                 nan     |                  nan     |
| rejected_12h_sweep__oi_rising     | immediate | validation   |   10 |  -31     |     40    |     10 |           0.802 |            1094.74 |        306    |        230.85 |                 nan     |                  nan     |
| strong_close_follow               | immediate | recheck_seen |  170 |  -64.23  |     35.88 |     73 |           0.587 |           12869.1  |        249.06 |        190.49 |                -106.768 |                  -21.812 |
| strong_close_follow               | immediate | train        |  591 | -156.648 |     34.35 |    247 |           0.4   |           92579.1  |        288.96 |        284.6  |                -191.177 |                 -123.749 |
| strong_close_follow               | immediate | validation   |  256 | -119.029 |     34.77 |    115 |           0.479 |           31256.1  |        287.27 |        261.29 |                -157.096 |                  -79.73  |
| strong_close_follow__oi_falling   | immediate | recheck_seen |   65 |  -77.481 |     32.31 |     45 |           0.547 |            7253.99 |        251.54 |        215.7  |                -148.765 |                  -13.716 |
| strong_close_follow__oi_falling   | immediate | train        |  219 | -176.153 |     33.33 |    165 |           0.366 |           39241.7  |        300.47 |        290.06 |                -226.677 |                 -128.982 |
| strong_close_follow__oi_falling   | immediate | validation   |  102 | -105.966 |     38.24 |     73 |           0.53  |           11282.7  |        287.17 |        261.21 |                -174.933 |                  -32.249 |
| strong_close_follow__oi_rising    | immediate | recheck_seen |   20 |  -54.226 |     30    |     16 |           0.678 |            2048.69 |        244.05 |        188.35 |                -186.622 |                   69.746 |
| strong_close_follow__oi_rising    | immediate | train        |   61 |  -76.462 |     45.9  |     50 |           0.653 |            6579.76 |        315.07 |        285.62 |                -168.237 |                   17.802 |
| strong_close_follow__oi_rising    | immediate | validation   |   26 | -206.358 |     19.23 |     26 |           0.234 |            5600.34 |        246.56 |        295.48 |                -322.693 |                  -95.737 |
| weak_close_fade                   | immediate | recheck_seen |   20 |  -97.455 |     40    |     18 |           0.467 |            1949.1  |        224.35 |        196.82 |                -213.84  |                   41.966 |
| weak_close_fade                   | immediate | train        |   48 | -151.294 |     33.33 |     41 |           0.446 |            7262.1  |        305.36 |        293.62 |                -266.158 |                  -35.829 |
| weak_close_fade                   | immediate | validation   |   29 | -214.337 |     24.14 |     24 |           0.244 |            6215.78 |        187.66 |        303.02 |                -328.33  |                  -72.49  |

## Confirmation at first completed 5m close; entry at minute 5 open
| rule                              | scheme     | period       |   n |     mean |   win_pct |   days |   profit_factor |   max_drawdown_pts |   avg_mfe_pts |   avg_mae_pts |   bootstrap_mean_95_low |   bootstrap_mean_95_high |
|:----------------------------------|:-----------|:-------------|----:|---------:|----------:|-------:|----------------:|-------------------:|--------------:|--------------:|------------------------:|-------------------------:|
| accepted_12h_breakout             | 5m_confirm | recheck_seen |  37 |   -1.996 |     45.95 |     31 |           0.981 |            1259.78 |        288.7  |        178.74 |                 -80.924 |                   84.254 |
| accepted_12h_breakout             | 5m_confirm | train        | 132 | -154.906 |     33.33 |    110 |           0.402 |           21005.1  |        287.2  |        288.78 |                -213.896 |                  -96.54  |
| accepted_12h_breakout             | 5m_confirm | validation   |  55 | -124.734 |     32.73 |     46 |           0.45  |            7762.69 |        280.6  |        254.04 |                -208.759 |                  -44.757 |
| accepted_12h_breakout__oi_falling | 5m_confirm | recheck_seen |  19 |   -1.287 |     47.37 |     17 |           0.986 |             838.39 |        309.74 |        193    |                 nan     |                  nan     |
| accepted_12h_breakout__oi_falling | 5m_confirm | train        |  69 | -147.853 |     34.78 |     60 |           0.436 |           10201.9  |        296.3  |        299.47 |                -237.306 |                  -60.549 |
| accepted_12h_breakout__oi_falling | 5m_confirm | validation   |  32 | -123.371 |     31.25 |     30 |           0.437 |            4962.8  |        269.08 |        258.77 |                -225.753 |                   -0.244 |
| accepted_12h_breakout__oi_rising  | 5m_confirm | recheck_seen |   2 |  110.688 |     50    |      2 |           2.163 |             190.39 |        305.25 |         90.75 |                 nan     |                  nan     |
| accepted_12h_breakout__oi_rising  | 5m_confirm | train        |  13 |  -79.238 |     46.15 |     13 |           0.622 |            2237.01 |        299.42 |        269.54 |                 nan     |                  nan     |
| accepted_12h_breakout__oi_rising  | 5m_confirm | validation   |   4 |  -85.492 |     25    |      4 |           0.545 |             470.67 |        241.38 |        191    |                 nan     |                  nan     |
| expansion_fade                    | 5m_confirm | recheck_seen | 219 | -109.286 |     31.96 |     78 |           0.366 |           24903.8  |        198.78 |        201.89 |                -136.879 |                  -79.563 |
| expansion_fade                    | 5m_confirm | train        | 617 | -166.266 |     31.44 |    243 |           0.367 |          104475    |        274.52 |        277.27 |                -191.016 |                 -139.699 |
| expansion_fade                    | 5m_confirm | validation   | 312 | -122.269 |     33.33 |    135 |           0.4   |           38792.5  |        235.63 |        242.25 |                -157.138 |                  -84.826 |
| expansion_follow                  | 5m_confirm | recheck_seen | 170 |  -73.721 |     36.47 |     76 |           0.534 |           14181    |        246.04 |        189.41 |                -115.395 |                  -35.166 |
| expansion_follow                  | 5m_confirm | train        | 533 | -159.693 |     31.89 |    215 |           0.386 |           85941.8  |        277.62 |        272.89 |                -191.036 |                 -127.446 |
| expansion_follow                  | 5m_confirm | validation   | 278 | -122.196 |     32.37 |    115 |           0.434 |           33970.4  |        260.64 |        246.53 |                -158.69  |                  -79.205 |
| rejected_12h_sweep                | 5m_confirm | recheck_seen |  20 |   -6.471 |     40    |     19 |           0.938 |            1096.53 |        248    |        128.15 |                -107.326 |                   95.411 |
| rejected_12h_sweep                | 5m_confirm | train        |  66 | -177.676 |     30.3  |     57 |           0.361 |           12112.6  |        259.95 |        264.91 |                -271.165 |                  -88.484 |
| rejected_12h_sweep                | 5m_confirm | validation   |  34 | -132.958 |     29.41 |     31 |           0.394 |            4557.8  |        238.59 |        257.07 |                -247.544 |                  -17.349 |
| rejected_12h_sweep__oi_falling    | 5m_confirm | recheck_seen |   8 |  139.415 |     75    |      8 |          19.321 |              41.87 |        282.19 |         76.31 |                 nan     |                  nan     |
| rejected_12h_sweep__oi_falling    | 5m_confirm | train        |  29 |  -88.796 |     41.38 |     27 |           0.607 |            3244.29 |        308.03 |        231.28 |                -228.937 |                   24.115 |
| rejected_12h_sweep__oi_falling    | 5m_confirm | validation   |  13 | -103.617 |     30.77 |     13 |           0.487 |            1358.01 |        265.73 |        260.65 |                 nan     |                  nan     |
| rejected_12h_sweep__oi_rising     | 5m_confirm | recheck_seen |   1 |  397.499 |    100    |      1 |         nan     |               0    |        773    |        161.5  |                 nan     |                  nan     |
| rejected_12h_sweep__oi_rising     | 5m_confirm | train        |   9 | -337.354 |     11.11 |      8 |           0.114 |            3036.18 |        156.72 |        359.33 |                 nan     |                  nan     |
| rejected_12h_sweep__oi_rising     | 5m_confirm | validation   |   3 |  -37.195 |     33.33 |      3 |           0.786 |             521.96 |        338    |        170.33 |                 nan     |                  nan     |
| strong_close_follow               | 5m_confirm | recheck_seen |  69 |  -72.019 |     37.68 |     42 |           0.542 |            5350.02 |        247.44 |        193.58 |                -141.413 |                   -6.604 |
| strong_close_follow               | 5m_confirm | train        | 251 | -163.878 |     31.08 |    152 |           0.379 |           41551    |        269.17 |        278.16 |                -210.114 |                 -122.214 |
| strong_close_follow               | 5m_confirm | validation   | 108 | -115.326 |     31.48 |     73 |           0.464 |           13215.4  |        268.24 |        247.4  |                -179.854 |                  -47.423 |
| strong_close_follow__oi_falling   | 5m_confirm | recheck_seen |  23 |  -92.281 |     34.78 |     21 |           0.352 |            2525.26 |        229.35 |        216.15 |                -170.429 |                   -6.447 |
| strong_close_follow__oi_falling   | 5m_confirm | train        |  93 | -174.155 |     31.18 |     83 |           0.378 |           16196.4  |        287.48 |        295.48 |                -251.618 |                  -99.903 |
| strong_close_follow__oi_falling   | 5m_confirm | validation   |  43 | -100.532 |     32.56 |     37 |           0.514 |            5578.65 |        269.22 |        249.2  |                -183.734 |                  -17.366 |
| strong_close_follow__oi_rising    | 5m_confirm | recheck_seen |   8 |   62.062 |     50    |      7 |           1.506 |             625.89 |        313    |        137.56 |                 nan     |                  nan     |
| strong_close_follow__oi_rising    | 5m_confirm | train        |  27 |  -65.599 |     44.44 |     25 |           0.677 |            3315.41 |        265.89 |        245.87 |                -201.206 |                   81.416 |
| strong_close_follow__oi_rising    | 5m_confirm | validation   |   8 |  -86.522 |     25    |      8 |           0.534 |            1014.42 |        266.12 |        215.75 |                 nan     |                  nan     |
| weak_close_fade                   | 5m_confirm | recheck_seen |  10 |  -41.115 |     40    |     10 |           0.683 |             903.92 |        236.45 |        149.45 |                 nan     |                  nan     |
| weak_close_fade                   | 5m_confirm | train        |  26 | -122.933 |     38.46 |     24 |           0.544 |            3567.8  |        317.25 |        270.19 |                -280.74  |                   50.898 |
| weak_close_fade                   | 5m_confirm | validation   |  12 | -194.244 |     25    |     12 |           0.203 |            2330.93 |        184.71 |        329.17 |                 nan     |                  nan     |

## OI incremental contrast against price-only parent (not causal identification)
| period       | base                  | filter     |   n_base |   n_filter |   base_accuracy_pct |   filter_accuracy_pct |   accuracy_delta_pp |   base_mean_gross_pts |   filter_mean_gross_pts |
|:-------------|:----------------------|:-----------|---------:|-----------:|--------------------:|----------------------:|--------------------:|----------------------:|------------------------:|
| recheck_seen | strong_close_follow   | oi_rising  |      170 |         20 |               54.12 |                 45    |               -9.12 |                 35.63 |                  111.08 |
| recheck_seen | strong_close_follow   | oi_falling |      170 |         65 |               54.12 |                 53.85 |               -0.27 |                 35.63 |                   23.38 |
| recheck_seen | accepted_12h_breakout | oi_rising  |       89 |          8 |               57.3  |                 37.5  |              -19.8  |                 76.08 |                  164.25 |
| recheck_seen | accepted_12h_breakout | oi_falling |       89 |         47 |               57.3  |                 59.57 |                2.27 |                 76.08 |                   82.26 |
| recheck_seen | rejected_12h_sweep    | oi_rising  |       45 |          3 |               53.33 |                 33.33 |              -20    |                 15.29 |                  164    |
| recheck_seen | rejected_12h_sweep    | oi_falling |       45 |         17 |               53.33 |                 76.47 |               23.14 |                 15.29 |                  107.03 |
| train        | strong_close_follow   | oi_rising  |      591 |         61 |               46.53 |                 52.46 |                5.93 |                -35.03 |                   -9.43 |
| train        | strong_close_follow   | oi_falling |      591 |        219 |               46.53 |                 45.66 |               -0.87 |                -35.03 |                  -26.54 |
| train        | accepted_12h_breakout | oi_rising  |      304 |         32 |               45.07 |                 65.62 |               20.56 |                -11.08 |                  229.66 |
| train        | accepted_12h_breakout | oi_falling |      304 |        147 |               45.07 |                 46.26 |                1.19 |                -11.08 |                   12.94 |
| train        | rejected_12h_sweep    | oi_rising  |      164 |         13 |               45.73 |                 30.77 |              -14.96 |                -43.67 |                 -254.69 |
| train        | rejected_12h_sweep    | oi_falling |      164 |         76 |               45.73 |                 50    |                4.27 |                -43.67 |                    0.31 |
| validation   | strong_close_follow   | oi_rising  |      256 |         26 |               42.58 |                 38.46 |               -4.12 |                 -4.56 |                 -100.52 |
| validation   | strong_close_follow   | oi_falling |      256 |        102 |               42.58 |                 45.1  |                2.52 |                 -4.56 |                   18.96 |
| validation   | accepted_12h_breakout | oi_rising  |      147 |         12 |               38.1  |                 33.33 |               -4.76 |                 -1.49 |                 -113.54 |
| validation   | accepted_12h_breakout | oi_falling |      147 |         75 |               38.1  |                 38.67 |                0.57 |                 -1.49 |                  -32.8  |
| validation   | rejected_12h_sweep    | oi_rising  |       75 |         10 |               58.67 |                 60    |                1.33 |                 93.18 |                  104.5  |
| validation   | rejected_12h_sweep    | oi_falling |       75 |         30 |               58.67 |                 60    |                1.33 |                 93.18 |                  217.07 |

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
