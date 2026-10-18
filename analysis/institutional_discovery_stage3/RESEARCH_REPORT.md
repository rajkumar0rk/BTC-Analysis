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
| accepted_12h_breakout             | immediate | recheck_seen |   89 |  -18.733 |     37.08 |     58 |           0.883 |            4806.17 |        380.09 |        264.94 |                 -93.165 |                   58.582 |
| accepted_12h_breakout             | immediate | train        |  304 | -140.836 |     36.51 |    191 |           0.566 |           45444.2  |        504.22 |        502.53 |                -217.865 |                  -61.393 |
| accepted_12h_breakout             | immediate | validation   |  147 |  -99.296 |     31.97 |     93 |           0.63  |           17683.8  |        438.2  |        399.89 |                -190.645 |                  -23.372 |
| accepted_12h_breakout__oi_falling | immediate | recheck_seen |   47 |  -13.36  |     38.3  |     37 |           0.915 |            2443.09 |        383.03 |        289.47 |                -101.687 |                   74.636 |
| accepted_12h_breakout__oi_falling | immediate | train        |  147 | -117.496 |     40.14 |    115 |           0.657 |           22009.5  |        584.04 |        546.49 |                -241.663 |                    8.822 |
| accepted_12h_breakout__oi_falling | immediate | validation   |   75 | -129.731 |     33.33 |     61 |           0.525 |           11616.2  |        427.8  |        411.87 |                -230.348 |                  -23.986 |
| accepted_12h_breakout__oi_rising  | immediate | recheck_seen |    8 |   70.633 |     37.5  |      7 |           1.243 |            2006.67 |        760.56 |        393.5  |                 nan     |                  nan     |
| accepted_12h_breakout__oi_rising  | immediate | train        |   32 |  100.687 |     56.25 |     29 |           1.686 |            2255.03 |        526.62 |        357.03 |                 -61.708 |                  280.399 |
| accepted_12h_breakout__oi_rising  | immediate | validation   |   12 | -214.959 |     16.67 |     12 |           0.464 |            3466.54 |        400.38 |        528.5  |                 nan     |                  nan     |
| expansion_fade                    | immediate | recheck_seen |  391 | -105.608 |     37.6  |     95 |           0.46  |           44047.8  |        262.67 |        298.79 |                -139.301 |                  -70.094 |
| expansion_fade                    | immediate | train        | 1153 | -111.688 |     39.64 |    286 |           0.611 |          135828    |        486.72 |        487.87 |                -144.994 |                  -68.998 |
| expansion_fade                    | immediate | validation   |  593 | -112.924 |     39.8  |    156 |           0.505 |           71981.8  |        339.59 |        397.52 |                -149.251 |                  -73.71  |
| expansion_follow                  | immediate | recheck_seen |  391 |  -88.03  |     33.76 |     95 |           0.538 |           36538.9  |        298.79 |        262.67 |                -127.029 |                  -53.84  |
| expansion_follow                  | immediate | train        | 1153 | -146.03  |     35.91 |    286 |           0.527 |          171216    |        487.87 |        486.72 |                -187.45  |                 -112.902 |
| expansion_follow                  | immediate | validation   |  593 |  -84.52  |     37.61 |    156 |           0.609 |           50145.2  |        397.52 |        339.59 |                -123.244 |                  -48.859 |
| rejected_12h_sweep                | immediate | recheck_seen |   45 |  -81.027 |     37.78 |     35 |           0.57  |            5274.63 |        275.89 |        269.63 |                -213.475 |                   53.965 |
| rejected_12h_sweep                | immediate | train        |  164 | -173.444 |     33.54 |    129 |           0.396 |           29118.3  |        403.11 |        497.06 |                -250.005 |                  -97.12  |
| rejected_12h_sweep                | immediate | validation   |   75 |   -5.701 |     46.67 |     64 |           0.97  |            5101.67 |        439.16 |        332.46 |                -122.715 |                  123.151 |
| rejected_12h_sweep__oi_falling    | immediate | recheck_seen |   17 |   14.95  |     64.71 |     17 |           1.087 |            1403.42 |        338.12 |        295    |                 nan     |                  nan     |
| rejected_12h_sweep__oi_falling    | immediate | train        |   76 | -126.073 |     35.53 |     71 |           0.524 |           10177.5  |        439.84 |        536.39 |                -234.253 |                  -14.512 |
| rejected_12h_sweep__oi_falling    | immediate | validation   |   30 |  119.755 |     50    |     28 |           1.919 |            1075.34 |        499.05 |        286.7  |                 -57.979 |                  361.47  |
| rejected_12h_sweep__oi_rising     | immediate | recheck_seen |    3 |   60.568 |     33.33 |      3 |           1.23  |             790.99 |        676.67 |        305.17 |                 nan     |                  nan     |
| rejected_12h_sweep__oi_rising     | immediate | train        |   13 | -387.868 |     23.08 |     12 |           0.093 |            5042.28 |        247.96 |        524.04 |                 nan     |                  nan     |
| rejected_12h_sweep__oi_rising     | immediate | validation   |   10 |    4.258 |     40    |     10 |           1.017 |            2020.69 |        512.9  |        437.35 |                 nan     |                  nan     |
| strong_close_follow               | immediate | recheck_seen |  170 |  -61.175 |     35.88 |     73 |           0.634 |           11199.8  |        314.18 |        252.53 |                -111.805 |                   -3.087 |
| strong_close_follow               | immediate | train        |  591 | -165.045 |     35.36 |    247 |           0.477 |           97541.5  |        472.56 |        498.45 |                -222.32  |                 -112.138 |
| strong_close_follow               | immediate | validation   |  256 | -101.954 |     35.16 |    115 |           0.6   |           30301.1  |        425.97 |        383.6  |                -161.519 |                  -43.196 |
| strong_close_follow__oi_falling   | immediate | recheck_seen |   65 |  -72.21  |     32.31 |     45 |           0.606 |            6509.69 |        304.12 |        300.24 |                -159.096 |                    4.924 |
| strong_close_follow__oi_falling   | immediate | train        |  219 | -155.788 |     37.44 |    165 |           0.546 |           34697    |        550.91 |        553.3  |                -251.997 |                  -64.102 |
| strong_close_follow__oi_falling   | immediate | validation   |  102 |  -78.114 |     37.25 |     73 |           0.677 |           13594.4  |        423.51 |        393.23 |                -176.177 |                   42.612 |
| strong_close_follow__oi_rising    | immediate | recheck_seen |   20 |   11.352 |     35    |     16 |           1.059 |            2602.75 |        482.75 |        266.8  |                -267.355 |                  296.218 |
| strong_close_follow__oi_rising    | immediate | train        |   61 | -139.065 |     44.26 |     50 |           0.551 |           10825.8  |        459.5  |        515.02 |                -334.805 |                   13.344 |
| strong_close_follow__oi_rising    | immediate | validation   |   26 | -198.134 |     26.92 |     26 |           0.418 |            5695.52 |        385.17 |        496.37 |                -439.143 |                   38.418 |
| weak_close_fade                   | immediate | recheck_seen |   20 |  -66.694 |     40    |     18 |           0.684 |            1905.24 |        302.57 |        271.9  |                -255.749 |                  180.188 |
| weak_close_fade                   | immediate | train        |   48 |  -26.526 |     41.67 |     41 |           0.907 |            5767.73 |        547.64 |        533.71 |                -220.007 |                  178.664 |
| weak_close_fade                   | immediate | validation   |   29 | -169.532 |     37.93 |     24 |           0.404 |            5719.12 |        322.34 |        485.09 |                -332.88  |                   25.91  |

## Confirmation at first completed 5m close; entry at minute 5 open
| rule                              | scheme     | period       |   n |     mean |   win_pct |   days |   profit_factor |   max_drawdown_pts |   avg_mfe_pts |   avg_mae_pts |   bootstrap_mean_95_low |   bootstrap_mean_95_high |
|:----------------------------------|:-----------|:-------------|----:|---------:|----------:|-------:|----------------:|-------------------:|--------------:|--------------:|------------------------:|-------------------------:|
| accepted_12h_breakout             | 5m_confirm | recheck_seen |  37 |   61.455 |     48.65 |     31 |           1.641 |            1050.79 |        449.85 |        197.69 |                 -58.16  |                  233.438 |
| accepted_12h_breakout             | 5m_confirm | train        | 132 | -211.751 |     31.82 |    110 |           0.418 |           30422.9  |        442.64 |        520.34 |                -321.392 |                 -108.588 |
| accepted_12h_breakout             | 5m_confirm | validation   |  55 |  -53.373 |     36.36 |     46 |           0.789 |            7835.63 |        478.15 |        361.06 |                -208.395 |                   96.332 |
| accepted_12h_breakout__oi_falling | 5m_confirm | recheck_seen |  19 |  -12.633 |     47.37 |     17 |           0.89  |            1238.15 |        364.05 |        221.79 |                 nan     |                  nan     |
| accepted_12h_breakout__oi_falling | 5m_confirm | train        |  69 | -179.05  |     36.23 |     60 |           0.527 |           15342.6  |        499.09 |        567.64 |                -332.086 |                   -9.831 |
| accepted_12h_breakout__oi_falling | 5m_confirm | validation   |  32 | -123.289 |     34.38 |     30 |           0.497 |            6006.49 |        386.78 |        353.06 |                -308.092 |                   90.581 |
| accepted_12h_breakout__oi_rising  | 5m_confirm | recheck_seen |   2 | 1098.6   |     50    |      2 |          12.541 |             190.39 |       2136.25 |         90.75 |                 nan     |                  nan     |
| accepted_12h_breakout__oi_rising  | 5m_confirm | train        |  13 |   39.592 |     53.85 |     13 |           1.296 |             987.77 |        453    |        318.04 |                 nan     |                  nan     |
| accepted_12h_breakout__oi_rising  | 5m_confirm | validation   |   4 |  266.301 |     25    |      4 |           2.494 |             431.2  |        686.75 |        210.62 |                 nan     |                  nan     |
| expansion_fade                    | 5m_confirm | recheck_seen | 219 |  -77.32  |     32.88 |     78 |           0.524 |           18896.1  |        251.68 |        247.98 |                -118.715 |                  -29.184 |
| expansion_fade                    | 5m_confirm | train        | 617 | -172.159 |     33.55 |    243 |           0.459 |          110698    |        421.14 |        502.52 |                -220.755 |                 -119.339 |
| expansion_fade                    | 5m_confirm | validation   | 312 | -130.383 |     36.54 |    135 |           0.43  |           42774.8  |        300.92 |        361.26 |                -178.379 |                  -78.881 |
| expansion_follow                  | 5m_confirm | recheck_seen | 170 |  -34.838 |     37.06 |     76 |           0.772 |            8078.8  |        329.52 |        223.27 |                 -94.369 |                   14.681 |
| expansion_follow                  | 5m_confirm | train        | 533 | -194.807 |     30.39 |    215 |           0.414 |          104318    |        425.52 |        486.39 |                -241.33  |                 -138.184 |
| expansion_follow                  | 5m_confirm | validation   | 278 | -112.119 |     34.17 |    115 |           0.506 |           31169    |        372.02 |        356.5  |                -166.219 |                  -52.498 |
| rejected_12h_sweep                | 5m_confirm | recheck_seen |  20 |    8.442 |     40    |     19 |           1.078 |            1165.49 |        292.95 |        131.45 |                -107.838 |                  136.45  |
| rejected_12h_sweep                | 5m_confirm | train        |  66 | -273.923 |     30.3  |     57 |           0.271 |           18422.4  |        329.36 |        490.32 |                -428.875 |                 -140.252 |
| rejected_12h_sweep                | 5m_confirm | validation   |  34 |   -9.753 |     35.29 |     31 |           0.944 |            2246.85 |        376.72 |        327.93 |                -183.362 |                  186.992 |
| rejected_12h_sweep__oi_falling    | 5m_confirm | recheck_seen |   8 |  127.97  |     75    |      8 |          17.817 |              41.87 |        294.94 |         76.31 |                 nan     |                  nan     |
| rejected_12h_sweep__oi_falling    | 5m_confirm | train        |  29 | -125.273 |     44.83 |     27 |           0.585 |            5406.85 |        420.05 |        384.98 |                -321.125 |                   57.388 |
| rejected_12h_sweep__oi_falling    | 5m_confirm | validation   |  13 |   55.045 |     38.46 |     13 |           1.366 |             670.05 |        394.5  |        313.23 |                 nan     |                  nan     |
| rejected_12h_sweep__oi_rising     | 5m_confirm | recheck_seen |   1 |  847.765 |    100    |      1 |         nan     |               0    |       1365.5  |        161.5  |                 nan     |                  nan     |
| rejected_12h_sweep__oi_rising     | 5m_confirm | train        |   9 | -531.078 |     11.11 |      8 |           0.066 |            4779.7  |        168.83 |        670.83 |                 nan     |                  nan     |
| rejected_12h_sweep__oi_rising     | 5m_confirm | validation   |   3 |  401.693 |     33.33 |      3 |           3.103 |             572.99 |        931.83 |        245.33 |                 nan     |                  nan     |
| strong_close_follow               | 5m_confirm | recheck_seen |  69 |  -43.511 |     39.13 |     42 |           0.704 |            4110.56 |        331.01 |        227.2  |                -142.021 |                   70.741 |
| strong_close_follow               | 5m_confirm | train        | 251 | -234.533 |     28.29 |    152 |           0.338 |           58867.8  |        398.45 |        494.23 |                -306.822 |                 -162.759 |
| strong_close_follow               | 5m_confirm | validation   | 108 |  -99.472 |     31.48 |     73 |           0.595 |           13794.5  |        417.11 |        358.27 |                -198.625 |                    6.172 |
| strong_close_follow__oi_falling   | 5m_confirm | recheck_seen |  23 |  -89.761 |     34.78 |     21 |           0.372 |            2467.3  |        233.46 |        243.98 |                -188.443 |                   -2.333 |
| strong_close_follow__oi_falling   | 5m_confirm | train        |  93 | -240.081 |     33.33 |     83 |           0.417 |           24899.7  |        484.06 |        559.12 |                -385.532 |                  -91.746 |
| strong_close_follow__oi_falling   | 5m_confirm | validation   |  43 |  -50.391 |     34.88 |     37 |           0.755 |            5958.12 |        391.66 |        321.7  |                -169.265 |                   97.375 |
| strong_close_follow__oi_rising    | 5m_confirm | recheck_seen |   8 |  298.753 |     50    |      7 |           4.434 |             340.06 |        792.44 |        137.56 |                 nan     |                  nan     |
| strong_close_follow__oi_rising    | 5m_confirm | train        |  27 | -140.988 |     40.74 |     25 |           0.475 |            4290.4  |        355.43 |        407.83 |                -321.99  |                   75.818 |
| strong_close_follow__oi_rising    | 5m_confirm | validation   |   8 |  124.708 |     25    |      8 |           1.794 |             825.81 |        540.44 |        234.38 |                 nan     |                  nan     |
| weak_close_fade                   | 5m_confirm | recheck_seen |  10 |   75.511 |     40    |     10 |           1.603 |             858.89 |        388.95 |        160.5  |                 nan     |                  nan     |
| weak_close_fade                   | 5m_confirm | train        |  26 |  -40.204 |     34.62 |     24 |           0.848 |            3094.29 |        473.79 |        355.77 |                -240.678 |                  189.21  |
| weak_close_fade                   | 5m_confirm | validation   |  12 | -183.498 |     25    |     12 |           0.219 |            2201.98 |        229.42 |        418.92 |                 nan     |                  nan     |

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
