# Stage 13 — 4H trend + 1H EMA20 pullback + 15M breakout

Rules predeclared: two pullback strictness choices, optional 15M breakout volume,
2R/3R target and 4h/8h maximum hold, 16 strategy configurations.
Every signal uses completed candles, next 1M OPEN execution, and structural stop.
No fixed trading time. Historical 2026 has already been researched.

## Monthly research consistency
| pullback      | volume      |   target_R |   max_hold_min |   trades_2025 |   profitable_2025 |   losing_2025 |   no_trade_2025 |   net_2025 |   trades_2026 |   profitable_2026 |   losing_2026 |   no_trade_2026 |   net_2026 | sufficient_samples   | positive_2025_H1_H2   | passes_monthly_gate   |
|:--------------|:------------|-----------:|---------------:|--------------:|------------------:|--------------:|----------------:|-----------:|--------------:|------------------:|--------------:|----------------:|-----------:|:---------------------|:----------------------|:----------------------|
| near_half_atr | any         |          2 |            240 |           371 |                 2 |            10 |               0 |  -26559.9  |           293 |                 3 |             8 |               0 |  -31534.2  | True                 | False                 | False                 |
| near_half_atr | any         |          2 |            480 |           319 |                 4 |             8 |               0 |  -22083.7  |           258 |                 1 |            10 |               0 |  -22581    | True                 | False                 | False                 |
| near_half_atr | any         |          3 |            240 |           362 |                 4 |             8 |               0 |  -25514.3  |           289 |                 4 |             7 |               0 |  -27133.7  | True                 | False                 | False                 |
| near_half_atr | any         |          3 |            480 |           303 |                 5 |             7 |               0 |  -13945    |           250 |                 2 |             9 |               0 |  -17651.7  | True                 | False                 | False                 |
| near_half_atr | volume_1p2x |          2 |            240 |           254 |                 2 |            10 |               0 |  -15989.7  |           205 |                 4 |             7 |               0 |  -18900.6  | True                 | False                 | False                 |
| near_half_atr | volume_1p2x |          2 |            480 |           232 |                 4 |             8 |               0 |   -9553.46 |           187 |                 4 |             7 |               0 |  -13828.2  | True                 | False                 | False                 |
| near_half_atr | volume_1p2x |          3 |            240 |           249 |                 1 |            11 |               0 |  -16450.1  |           202 |                 4 |             7 |               0 |  -13081.3  | True                 | False                 | False                 |
| near_half_atr | volume_1p2x |          3 |            480 |           222 |                 5 |             7 |               0 |   -4109.43 |           181 |                 3 |             8 |               0 |   -8240.01 | True                 | False                 | False                 |
| touch         | any         |          2 |            240 |           202 |                 1 |            11 |               0 |  -22978.4  |           151 |                 3 |             8 |               0 |  -17260.7  | True                 | False                 | False                 |
| touch         | any         |          2 |            480 |           183 |                 2 |            10 |               0 |  -23711.5  |           142 |                 1 |            10 |               0 |  -24136.1  | True                 | False                 | False                 |
| touch         | any         |          3 |            240 |           201 |                 1 |            11 |               0 |  -19960.9  |           151 |                 3 |             8 |               0 |  -16601.3  | True                 | False                 | False                 |
| touch         | any         |          3 |            480 |           182 |                 3 |             9 |               0 |  -15510.4  |           141 |                 2 |             9 |               0 |  -19556.8  | True                 | False                 | False                 |
| touch         | volume_1p2x |          2 |            240 |           141 |                 3 |             9 |               0 |   -9997.38 |            98 |                 3 |             8 |               0 |   -7769.72 | True                 | False                 | False                 |
| touch         | volume_1p2x |          2 |            480 |           135 |                 3 |             9 |               0 |  -13780.1  |            94 |                 3 |             8 |               0 |  -12125.9  | True                 | False                 | False                 |
| touch         | volume_1p2x |          3 |            240 |           140 |                 5 |             7 |               0 |   -8017.6  |            97 |                 3 |             8 |               0 |   -5267.66 | True                 | False                 | False                 |
| touch         | volume_1p2x |          3 |            480 |           134 |                 3 |             9 |               0 |   -9039.61 |            92 |                 3 |             8 |               0 |   -6330.94 | True                 | False                 | False                 |

## Full standard after-fee period results
| pullback      | volume      |   target_R |   max_hold_min | period                      | fee            |   trades |   longs |   shorts |   wins |   losses |   win_rate |   mean_net |   net_total |   profit_factor |   worst_trade |   max_drawdown |
|:--------------|:------------|-----------:|---------------:|:----------------------------|:---------------|---------:|--------:|---------:|-------:|---------:|-----------:|-----------:|------------:|----------------:|--------------:|---------------:|
| near_half_atr | any         |          2 |            240 | 2025_train                  | standard_taker |      371 |     197 |      174 |    154 |      217 |      41.51 |     -71.59 |   -26559.9  |           0.783 |      -1664.16 |       28821.1  |
| near_half_atr | any         |          2 |            240 | 2026_H1_validation          | standard_taker |      174 |      70 |      104 |     66 |      108 |      37.93 |     -62.73 |   -10915.1  |           0.784 |      -1492.04 |       10940.2  |
| near_half_atr | any         |          2 |            240 | 2026_H2_seen_recheck        | standard_taker |      109 |      60 |       49 |     27 |       82 |      24.77 |    -166.5  |   -18148.3  |           0.42  |      -1086.43 |       18918.5  |
| near_half_atr | any         |          2 |            240 | 2026_Nov_recent_exploratory | standard_taker |       10 |       0 |       10 |      3 |        7 |      30    |    -247.07 |    -2470.73 |           0.25  |       -769.39 |        2470.73 |
| near_half_atr | any         |          2 |            480 | 2025_train                  | standard_taker |      319 |     164 |      155 |    122 |      197 |      38.24 |     -69.23 |   -22083.7  |           0.832 |      -1682.24 |       28261.7  |
| near_half_atr | any         |          2 |            480 | 2026_H1_validation          | standard_taker |      157 |      64 |       93 |     60 |       97 |      38.22 |     -41.29 |    -6482.39 |           0.882 |      -1492.04 |       11177.2  |
| near_half_atr | any         |          2 |            480 | 2026_H2_seen_recheck        | standard_taker |       93 |      53 |       40 |     26 |       67 |      27.96 |    -162.58 |   -15119.6  |           0.526 |      -1397.36 |       15889.7  |
| near_half_atr | any         |          2 |            480 | 2026_Nov_recent_exploratory | standard_taker |        8 |       0 |        8 |      3 |        5 |      37.5  |    -122.37 |     -978.98 |           0.597 |       -769.39 |        1203.53 |
| near_half_atr | any         |          3 |            240 | 2025_train                  | standard_taker |      362 |     191 |      171 |    144 |      218 |      39.78 |     -70.48 |   -25514.3  |           0.788 |      -1664.16 |       29630.4  |
| near_half_atr | any         |          3 |            240 | 2026_H1_validation          | standard_taker |      172 |      69 |      103 |     63 |      109 |      36.63 |     -53.41 |    -9187.08 |           0.821 |      -1492.04 |        9884.91 |
| near_half_atr | any         |          3 |            240 | 2026_H2_seen_recheck        | standard_taker |      107 |      60 |       47 |     24 |       83 |      22.43 |    -145.7  |   -15590.4  |           0.477 |       -969.4  |       16179.9  |
| near_half_atr | any         |          3 |            240 | 2026_Nov_recent_exploratory | standard_taker |       10 |       0 |       10 |      3 |        7 |      30    |    -235.62 |    -2356.19 |           0.285 |       -769.39 |        2356.19 |
| near_half_atr | any         |          3 |            480 | 2025_train                  | standard_taker |      303 |     155 |      148 |    107 |      196 |      35.31 |     -46.02 |   -13945    |           0.891 |      -1664.16 |       22331.3  |
| near_half_atr | any         |          3 |            480 | 2026_H1_validation          | standard_taker |      151 |      61 |       90 |     53 |       98 |      35.1  |     -25.03 |    -3779.96 |           0.932 |      -1492.04 |        7287.79 |
| near_half_atr | any         |          3 |            480 | 2026_H2_seen_recheck        | standard_taker |       91 |      52 |       39 |     23 |       68 |      25.27 |    -145.87 |   -13273.8  |           0.579 |      -1397.36 |       14480.2  |
| near_half_atr | any         |          3 |            480 | 2026_Nov_recent_exploratory | standard_taker |        8 |       0 |        8 |      3 |        5 |      37.5  |     -74.75 |     -597.99 |           0.754 |       -769.39 |        1203.53 |
| near_half_atr | volume_1p2x |          2 |            240 | 2025_train                  | standard_taker |      254 |     131 |      123 |    108 |      146 |      42.52 |     -62.95 |   -15989.7  |           0.81  |      -1515.41 |       19466.6  |
| near_half_atr | volume_1p2x |          2 |            240 | 2026_H1_validation          | standard_taker |      128 |      54 |       74 |     47 |       81 |      36.72 |     -47.87 |    -6127.34 |           0.839 |      -1492.04 |       10407.6  |
| near_half_atr | volume_1p2x |          2 |            240 | 2026_H2_seen_recheck        | standard_taker |       68 |      38 |       30 |     21 |       47 |      30.88 |    -165.14 |   -11229.2  |           0.493 |      -1086.43 |       12137    |
| near_half_atr | volume_1p2x |          2 |            240 | 2026_Nov_recent_exploratory | standard_taker |        9 |       0 |        9 |      3 |        6 |      33.33 |    -171.55 |    -1543.98 |           0.431 |       -895.81 |        1861.33 |
| near_half_atr | volume_1p2x |          2 |            480 | 2025_train                  | standard_taker |      232 |     116 |      116 |     93 |      139 |      40.09 |     -41.18 |    -9553.46 |           0.896 |      -1558.98 |       13526.7  |
| near_half_atr | volume_1p2x |          2 |            480 | 2026_H1_validation          | standard_taker |      120 |      50 |       70 |     50 |       70 |      41.67 |     -46.92 |    -5631    |           0.872 |      -1492.04 |        9273.47 |
| near_half_atr | volume_1p2x |          2 |            480 | 2026_H2_seen_recheck        | standard_taker |       60 |      35 |       25 |     20 |       40 |      33.33 |    -129.99 |    -7799.27 |           0.639 |      -1056.23 |        9591.32 |
| near_half_atr | volume_1p2x |          2 |            480 | 2026_Nov_recent_exploratory | standard_taker |        7 |       0 |        7 |      3 |        4 |      42.86 |     -56.85 |     -397.92 |           0.81  |       -895.81 |        1203.53 |
| near_half_atr | volume_1p2x |          3 |            240 | 2025_train                  | standard_taker |      249 |     126 |      123 |     99 |      150 |      39.76 |     -66.06 |   -16450.1  |           0.805 |      -1515.41 |       20505.5  |
| near_half_atr | volume_1p2x |          3 |            240 | 2026_H1_validation          | standard_taker |      125 |      53 |       72 |     45 |       80 |      36    |      -2.51 |     -313.57 |           0.992 |      -1492.04 |       10371.8  |
| near_half_atr | volume_1p2x |          3 |            240 | 2026_H2_seen_recheck        | standard_taker |       68 |      38 |       30 |     19 |       49 |      27.94 |    -166.74 |   -11338.3  |           0.493 |      -1086.43 |       11982.4  |
| near_half_atr | volume_1p2x |          3 |            240 | 2026_Nov_recent_exploratory | standard_taker |        9 |       0 |        9 |      3 |        6 |      33.33 |    -158.83 |    -1429.44 |           0.473 |       -895.81 |        1746.79 |
| near_half_atr | volume_1p2x |          3 |            480 | 2025_train                  | standard_taker |      222 |     108 |      114 |     82 |      140 |      36.94 |     -18.51 |    -4109.43 |           0.955 |      -1558.98 |       10443.6  |
| near_half_atr | volume_1p2x |          3 |            480 | 2026_H1_validation          | standard_taker |      114 |      47 |       67 |     45 |       69 |      39.47 |       5.29 |      602.65 |           1.014 |      -1492.04 |        7618.91 |
| near_half_atr | volume_1p2x |          3 |            480 | 2026_H2_seen_recheck        | standard_taker |       60 |      35 |       25 |     18 |       42 |      30    |    -147.1  |    -8825.73 |           0.604 |      -1056.23 |        9312.98 |
| near_half_atr | volume_1p2x |          3 |            480 | 2026_Nov_recent_exploratory | standard_taker |        7 |       0 |        7 |      3 |        4 |      42.86 |      -2.42 |      -16.93 |           0.992 |       -895.81 |        1203.53 |
| touch         | any         |          2 |            240 | 2025_train                  | standard_taker |      202 |     110 |       92 |     81 |      121 |      40.1  |    -113.75 |   -22978.4  |           0.675 |      -1664.16 |       25548.8  |
| touch         | any         |          2 |            240 | 2026_H1_validation          | standard_taker |       91 |      34 |       57 |     34 |       57 |      37.36 |     -66.68 |    -6067.73 |           0.78  |      -1365.06 |        6920.76 |
| touch         | any         |          2 |            240 | 2026_H2_seen_recheck        | standard_taker |       56 |      33 |       23 |     11 |       45 |      19.64 |    -183.63 |   -10283.4  |           0.334 |       -969.4  |       10382.7  |
| touch         | any         |          2 |            240 | 2026_Nov_recent_exploratory | standard_taker |        4 |       0 |        4 |      1 |        3 |      25    |    -227.39 |     -909.55 |           0.006 |       -575.43 |         909.55 |
| touch         | any         |          2 |            480 | 2025_train                  | standard_taker |      183 |      99 |       84 |     66 |      117 |      36.07 |    -129.57 |   -23711.5  |           0.698 |      -1664.16 |       26016.5  |
| touch         | any         |          2 |            480 | 2026_H1_validation          | standard_taker |       86 |      33 |       53 |     28 |       58 |      32.56 |    -152.37 |   -13103.9  |           0.624 |      -1365.06 |       13103.9  |
| touch         | any         |          2 |            480 | 2026_H2_seen_recheck        | standard_taker |       52 |      31 |       21 |     13 |       39 |      25    |    -185.62 |    -9652.27 |           0.425 |       -969.4  |        9865.14 |
| touch         | any         |          2 |            480 | 2026_Nov_recent_exploratory | standard_taker |        4 |       0 |        4 |      1 |        3 |      25    |    -344.98 |    -1379.92 |           0.1   |       -855.76 |        1379.92 |
| touch         | any         |          3 |            240 | 2025_train                  | standard_taker |      201 |     109 |       92 |     79 |      122 |      39.3  |     -99.31 |   -19960.9  |           0.718 |      -1664.16 |       24311.5  |
| touch         | any         |          3 |            240 | 2026_H1_validation          | standard_taker |       91 |      34 |       57 |     33 |       58 |      36.26 |     -43.46 |    -3955.03 |           0.86  |      -1365.06 |        7782.53 |
| touch         | any         |          3 |            240 | 2026_H2_seen_recheck        | standard_taker |       56 |      33 |       23 |      9 |       47 |      16.07 |    -209.58 |   -11736.7  |           0.262 |       -969.4  |       11836    |
| touch         | any         |          3 |            240 | 2026_Nov_recent_exploratory | standard_taker |        4 |       0 |        4 |      1 |        3 |      25    |    -227.39 |     -909.55 |           0.006 |       -575.43 |         909.55 |
| touch         | any         |          3 |            480 | 2025_train                  | standard_taker |      182 |      98 |       84 |     64 |      118 |      35.16 |     -85.22 |   -15510.4  |           0.803 |      -1664.16 |       19094.6  |
| touch         | any         |          3 |            480 | 2026_H1_validation          | standard_taker |       86 |      33 |       53 |     26 |       60 |      30.23 |     -89.13 |    -7665.35 |           0.785 |      -1365.06 |        8362.3  |
| touch         | any         |          3 |            480 | 2026_H2_seen_recheck        | standard_taker |       51 |      30 |       21 |     11 |       40 |      21.57 |    -206.11 |   -10511.6  |           0.376 |       -969.4  |       10724.4  |
| touch         | any         |          3 |            480 | 2026_Nov_recent_exploratory | standard_taker |        4 |       0 |        4 |      1 |        3 |      25    |    -344.98 |    -1379.92 |           0.1   |       -855.76 |        1379.92 |
| touch         | volume_1p2x |          2 |            240 | 2025_train                  | standard_taker |      141 |      68 |       73 |     62 |       79 |      43.97 |     -70.9  |    -9997.38 |           0.789 |      -1515.41 |       14376.1  |
| touch         | volume_1p2x |          2 |            240 | 2026_H1_validation          | standard_taker |       65 |      25 |       40 |     22 |       43 |      33.85 |     -21.06 |    -1368.61 |           0.93  |      -1365.06 |        7404.78 |
| touch         | volume_1p2x |          2 |            240 | 2026_H2_seen_recheck        | standard_taker |       29 |      17 |       12 |      7 |       22 |      24.14 |    -201.16 |    -5833.69 |           0.366 |       -969.4  |        5933    |
| touch         | volume_1p2x |          2 |            240 | 2026_Nov_recent_exploratory | standard_taker |        4 |       0 |        4 |      1 |        3 |      25    |    -141.85 |     -567.42 |           0.38  |       -575.43 |         884.77 |
| touch         | volume_1p2x |          2 |            480 | 2025_train                  | standard_taker |      135 |      65 |       70 |     52 |       83 |      38.52 |    -102.07 |   -13780.1  |           0.758 |      -1558.98 |       16860    |
| touch         | volume_1p2x |          2 |            480 | 2026_H1_validation          | standard_taker |       63 |      24 |       39 |     23 |       40 |      36.51 |    -109.99 |    -6929.44 |           0.729 |      -1408.48 |        8152.85 |
| touch         | volume_1p2x |          2 |            480 | 2026_H2_seen_recheck        | standard_taker |       28 |      16 |       12 |      8 |       20 |      28.57 |    -175.8  |    -4922.35 |           0.524 |      -1056.23 |        5135.22 |
| touch         | volume_1p2x |          2 |            480 | 2026_Nov_recent_exploratory | standard_taker |        3 |       0 |        3 |      1 |        2 |      33.33 |     -91.36 |     -274.09 |           0.595 |       -575.43 |         677.15 |
| touch         | volume_1p2x |          3 |            240 | 2025_train                  | standard_taker |      140 |      67 |       73 |     59 |       81 |      42.14 |     -57.27 |    -8017.6  |           0.834 |      -1515.41 |       14867.7  |
| touch         | volume_1p2x |          3 |            240 | 2026_H1_validation          | standard_taker |       64 |      25 |       39 |     21 |       43 |      32.81 |      33.67 |     2154.84 |           1.111 |      -1365.06 |        7467.16 |
| touch         | volume_1p2x |          3 |            240 | 2026_H2_seen_recheck        | standard_taker |       29 |      17 |       12 |      6 |       23 |      20.69 |    -236.38 |    -6855.08 |           0.267 |       -969.4  |        6954.39 |
| touch         | volume_1p2x |          3 |            240 | 2026_Nov_recent_exploratory | standard_taker |        4 |       0 |        4 |      1 |        3 |      25    |    -141.85 |     -567.42 |           0.38  |       -575.43 |         884.77 |
| touch         | volume_1p2x |          3 |            480 | 2025_train                  | standard_taker |      134 |      64 |       70 |     49 |       85 |      36.57 |     -67.46 |    -9039.61 |           0.843 |      -1558.98 |       14908.9  |
| touch         | volume_1p2x |          3 |            480 | 2026_H1_validation          | standard_taker |       62 |      24 |       38 |     21 |       41 |      33.87 |      -5.78 |     -358.52 |           0.986 |      -1408.48 |        8520.56 |
| touch         | volume_1p2x |          3 |            480 | 2026_H2_seen_recheck        | standard_taker |       27 |      15 |       12 |      6 |       21 |      22.22 |    -211.05 |    -5698.33 |           0.453 |      -1056.23 |        5911.2  |
| touch         | volume_1p2x |          3 |            480 | 2026_Nov_recent_exploratory | standard_taker |        3 |       0 |        3 |      1 |        2 |      33.33 |     -91.36 |     -274.09 |           0.595 |       -575.43 |         677.15 |

## Baseline monthly table: strict touch + volume + 2R + 8h
| pullback   | volume      |   target_R |   max_hold_min | month_ist   |   trades |   net_pts | status   |
|:-----------|:------------|-----------:|---------------:|:------------|---------:|----------:|:---------|
| touch      | volume_1p2x |          2 |            480 | 2025-01     |        8 |   1203.17 | Profit   |
| touch      | volume_1p2x |          2 |            480 | 2025-02     |       12 |   -613.8  | Loss     |
| touch      | volume_1p2x |          2 |            480 | 2025-03     |       12 |  -2635.8  | Loss     |
| touch      | volume_1p2x |          2 |            480 | 2025-04     |        8 |  -1530.38 | Loss     |
| touch      | volume_1p2x |          2 |            480 | 2025-05     |        8 |  -1679.95 | Loss     |
| touch      | volume_1p2x |          2 |            480 | 2025-06     |       20 |  -2788.36 | Loss     |
| touch      | volume_1p2x |          2 |            480 | 2025-07     |        6 |   1549.81 | Profit   |
| touch      | volume_1p2x |          2 |            480 | 2025-08     |       17 |  -1038.77 | Loss     |
| touch      | volume_1p2x |          2 |            480 | 2025-09     |       18 |  -2708.82 | Loss     |
| touch      | volume_1p2x |          2 |            480 | 2025-10     |       10 |    353.63 | Profit   |
| touch      | volume_1p2x |          2 |            480 | 2025-11     |       11 |  -3623.63 | Loss     |
| touch      | volume_1p2x |          2 |            480 | 2025-12     |        5 |   -267.19 | Loss     |
| touch      | volume_1p2x |          2 |            480 | 2026-01     |       13 |  -5276.22 | Loss     |
| touch      | volume_1p2x |          2 |            480 | 2026-02     |       13 |   3073.5  | Profit   |
| touch      | volume_1p2x |          2 |            480 | 2026-03     |        3 |   2112.36 | Profit   |
| touch      | volume_1p2x |          2 |            480 | 2026-04     |       12 |   -893.14 | Loss     |
| touch      | volume_1p2x |          2 |            480 | 2026-05     |       16 |  -4417.13 | Loss     |
| touch      | volume_1p2x |          2 |            480 | 2026-06     |        6 |  -1528.81 | Loss     |
| touch      | volume_1p2x |          2 |            480 | 2026-07     |        4 |  -1125.79 | Loss     |
| touch      | volume_1p2x |          2 |            480 | 2026-08     |       11 |    347.35 | Profit   |
| touch      | volume_1p2x |          2 |            480 | 2026-09     |        5 |   -112.77 | Loss     |
| touch      | volume_1p2x |          2 |            480 | 2026-10     |        8 |  -4031.14 | Loss     |
| touch      | volume_1p2x |          2 |            480 | 2026-11     |        3 |   -274.09 | Loss     |

## Interpretation
A passed research gate requires >=70% profitable active months in each year,
at least 9 active months 2025 and 8 in 2026, and positive expectancy in
2025, 2026 H1 and 2026 H2 with >=50/25/15 trades.
Passing historical rules does NOT establish live profitability.

## Caveats
- All tested historical periods already used in previous research, not a pristine out-of-sample test
- 2026-10-31 is missing from source; 2026-11 ends Nov 16
- Fees 0.05% taker/side, 18% GST, adverse 5 BTC points slippage per side; included in standard net
- Scalper Offer closing fee waiver is hypothetical and not assumed for standard PnL
- Funding, order-book spreads, margin, liquidation and impact not modeled
- Stops resolved first when OHLC bar touches stop and target; gap stop can fill worse
- All months with zero trades included; no guarantee of monthly profitability
- Aggregate BTC price points are not account profit or capital returns
- One open trade at a time within a model, LONG and SHORT mutually exclusive

Reproduce using scripts/research_trend_pullback_breakout_stage13.py.
Detailed events/trades saved in the associated GitHub Actions artifact.
