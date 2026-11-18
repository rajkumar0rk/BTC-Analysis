# Stage 13 — 4H trend + 1H EMA20 pullback + 15M breakout

Rules predeclared: two pullback strictness choices, optional 15M breakout volume,
2R/3R target and 4h/8h maximum hold, 16 strategy configurations.
Every signal uses completed candles, next 1M OPEN execution, and structural stop.
No fixed trading time. Historical 2026 has already been researched.

## Monthly research consistency
| pullback      | volume      |   target_R |   max_hold_min |   trades_2025 |   profitable_2025 |   losing_2025 |   no_trade_2025 |   net_2025 |   trades_2026 |   profitable_2026 |   losing_2026 |   no_trade_2026 |   net_2026 | sufficient_samples   | positive_2025_H1_H2   | passes_monthly_gate   |
|:--------------|:------------|-----------:|---------------:|--------------:|------------------:|--------------:|----------------:|-----------:|--------------:|------------------:|--------------:|----------------:|-----------:|:---------------------|:----------------------|:----------------------|
| near_half_atr | any         |          2 |            240 |           279 |                 2 |            10 |               0 |  -34031.2  |           273 |                 3 |             8 |               0 |  -28964.4  | True                 | False                 | False                 |
| near_half_atr | any         |          2 |            480 |           254 |                 5 |             7 |               0 |  -23935.6  |           242 |                 3 |             8 |               0 |  -20214.4  | True                 | False                 | False                 |
| near_half_atr | any         |          3 |            240 |           275 |                 3 |             9 |               0 |  -21365.2  |           267 |                 2 |             9 |               0 |  -25486.1  | True                 | False                 | False                 |
| near_half_atr | any         |          3 |            480 |           250 |                 6 |             6 |               0 |    -429.97 |           233 |                 3 |             8 |               0 |  -13794.5  | True                 | False                 | False                 |
| near_half_atr | volume_1p2x |          2 |            240 |           179 |                 6 |             6 |               0 |  -14168.1  |           192 |                 2 |             9 |               0 |  -19010.1  | True                 | False                 | False                 |
| near_half_atr | volume_1p2x |          2 |            480 |           167 |                 5 |             7 |               0 |   -1811.52 |           181 |                 5 |             6 |               0 |  -16631.1  | True                 | False                 | False                 |
| near_half_atr | volume_1p2x |          3 |            240 |           177 |                 6 |             6 |               0 |   -6859.5  |           187 |                 4 |             7 |               0 |  -13744.6  | True                 | False                 | False                 |
| near_half_atr | volume_1p2x |          3 |            480 |           163 |                 6 |             6 |               0 |    9601.03 |           175 |                 6 |             5 |               0 |   -4203.14 | True                 | False                 | False                 |
| touch         | any         |          2 |            240 |           156 |                 3 |             9 |               0 |  -17430    |           142 |                 6 |             5 |               0 |   -3597.61 | True                 | False                 | False                 |
| touch         | any         |          2 |            480 |           148 |                 4 |             8 |               0 |  -15755.3  |           134 |                 4 |             7 |               0 |   -8339.37 | True                 | False                 | False                 |
| touch         | any         |          3 |            240 |           154 |                 3 |             9 |               0 |  -10589.3  |           141 |                 4 |             7 |               0 |   -5338.23 | True                 | False                 | False                 |
| touch         | any         |          3 |            480 |           146 |                 5 |             7 |               0 |   -5138.49 |           132 |                 3 |             8 |               0 |  -12366.1  | True                 | False                 | False                 |
| touch         | volume_1p2x |          2 |            240 |            98 |                 5 |             7 |               0 |   -9936.67 |           105 |                 5 |             6 |               0 |   -5927.87 | True                 | False                 | False                 |
| touch         | volume_1p2x |          2 |            480 |            94 |                 6 |             6 |               0 |   -5684.11 |           101 |                 3 |             8 |               0 |   -9492.37 | True                 | False                 | False                 |
| touch         | volume_1p2x |          3 |            240 |            97 |                 6 |             6 |               0 |   -7890.13 |           104 |                 5 |             6 |               0 |   -4216.59 | True                 | False                 | False                 |
| touch         | volume_1p2x |          3 |            480 |            93 |                 6 |             6 |               0 |   -5403.98 |           100 |                 6 |             5 |               0 |   -6516.37 | True                 | False                 | False                 |

## Full standard after-fee period results
| pullback      | volume      |   target_R |   max_hold_min | period                      | fee            |   trades |   longs |   shorts |   wins |   losses |   win_rate |   mean_net |   net_total |   profit_factor |   worst_trade |   max_drawdown |
|:--------------|:------------|-----------:|---------------:|:----------------------------|:---------------|---------:|--------:|---------:|-------:|---------:|-----------:|-----------:|------------:|----------------:|--------------:|---------------:|
| near_half_atr | any         |          2 |            240 | 2025_train                  | standard_taker |      279 |     133 |      146 |    107 |      172 |      38.35 |    -121.98 |   -34031.2  |           0.729 |      -1688.81 |       36425.1  |
| near_half_atr | any         |          2 |            240 | 2026_H1_validation          | standard_taker |      142 |      61 |       81 |     56 |       86 |      39.44 |     -32.82 |    -4661.12 |           0.893 |      -1589.81 |        6990.31 |
| near_half_atr | any         |          2 |            240 | 2026_H2_seen_recheck        | standard_taker |      110 |      73 |       37 |     26 |       84 |      23.64 |    -203.19 |   -22350.3  |           0.311 |      -1405.5  |       22350.3  |
| near_half_atr | any         |          2 |            240 | 2026_Nov_recent_exploratory | standard_taker |       21 |       0 |       21 |      7 |       14 |      33.33 |     -93    |    -1952.96 |           0.594 |       -751.17 |        2384.86 |
| near_half_atr | any         |          2 |            480 | 2025_train                  | standard_taker |      254 |     121 |      133 |     96 |      158 |      37.8  |     -94.23 |   -23935.6  |           0.82  |      -1740.17 |       31310.5  |
| near_half_atr | any         |          2 |            480 | 2026_H1_validation          | standard_taker |      130 |      54 |       76 |     54 |       76 |      41.54 |      -9.05 |    -1176.09 |           0.975 |      -1589.81 |        9667    |
| near_half_atr | any         |          2 |            480 | 2026_H2_seen_recheck        | standard_taker |       94 |      64 |       30 |     28 |       66 |      29.79 |    -180.82 |   -16997.1  |           0.521 |      -1405.5  |       16997.1  |
| near_half_atr | any         |          2 |            480 | 2026_Nov_recent_exploratory | standard_taker |       18 |       0 |       18 |      6 |       12 |      33.33 |    -113.4  |    -2041.28 |           0.641 |      -1008.79 |        2427.65 |
| near_half_atr | any         |          3 |            240 | 2025_train                  | standard_taker |      275 |     129 |      146 |    102 |      173 |      37.09 |     -77.69 |   -21365.2  |           0.83  |      -1688.81 |       23578    |
| near_half_atr | any         |          3 |            240 | 2026_H1_validation          | standard_taker |      139 |      59 |       80 |     54 |       85 |      38.85 |     -24.06 |    -3344.65 |           0.922 |      -1589.81 |        9149.73 |
| near_half_atr | any         |          3 |            240 | 2026_H2_seen_recheck        | standard_taker |      107 |      70 |       37 |     25 |       82 |      23.36 |    -197.47 |   -21129.4  |           0.326 |      -1012.29 |       21129.4  |
| near_half_atr | any         |          3 |            240 | 2026_Nov_recent_exploratory | standard_taker |       21 |       0 |       21 |      7 |       14 |      33.33 |     -48.19 |    -1012.02 |           0.789 |       -751.17 |        2292.35 |
| near_half_atr | any         |          3 |            480 | 2025_train                  | standard_taker |      250 |     118 |      132 |     87 |      163 |      34.8  |      -1.72 |     -429.97 |           0.997 |      -1740.17 |       22286    |
| near_half_atr | any         |          3 |            480 | 2026_H1_validation          | standard_taker |      124 |      51 |       73 |     48 |       76 |      38.71 |       8.81 |     1092.31 |           1.024 |      -1589.81 |       11285.4  |
| near_half_atr | any         |          3 |            480 | 2026_H2_seen_recheck        | standard_taker |       91 |      61 |       30 |     26 |       65 |      28.57 |    -157.02 |   -14288.5  |           0.571 |      -1134.25 |       14288.5  |
| near_half_atr | any         |          3 |            480 | 2026_Nov_recent_exploratory | standard_taker |       18 |       0 |       18 |      6 |       12 |      33.33 |     -33.24 |     -598.34 |           0.895 |      -1008.79 |        1925.65 |
| near_half_atr | volume_1p2x |          2 |            240 | 2025_train                  | standard_taker |      179 |      86 |       93 |     70 |      109 |      39.11 |     -79.15 |   -14168.1  |           0.816 |      -1688.81 |       16059.7  |
| near_half_atr | volume_1p2x |          2 |            240 | 2026_H1_validation          | standard_taker |      107 |      46 |       61 |     44 |       63 |      41.12 |      -6.58 |     -703.78 |           0.98  |      -1589.81 |        5659.73 |
| near_half_atr | volume_1p2x |          2 |            240 | 2026_H2_seen_recheck        | standard_taker |       71 |      47 |       24 |     17 |       54 |      23.94 |    -246.69 |   -17514.7  |           0.264 |      -1405.5  |       17514.7  |
| near_half_atr | volume_1p2x |          2 |            240 | 2026_Nov_recent_exploratory | standard_taker |       14 |       0 |       14 |      5 |        9 |      35.71 |     -56.55 |     -791.69 |           0.75  |       -811.86 |        1369.08 |
| near_half_atr | volume_1p2x |          2 |            480 | 2025_train                  | standard_taker |      167 |      82 |       85 |     69 |       98 |      41.32 |     -10.85 |    -1811.52 |           0.978 |      -1740.17 |       15389    |
| near_half_atr | volume_1p2x |          2 |            480 | 2026_H1_validation          | standard_taker |      101 |      42 |       59 |     44 |       57 |      43.56 |      10.39 |     1049.46 |           1.027 |      -1589.81 |        5476.78 |
| near_half_atr | volume_1p2x |          2 |            480 | 2026_H2_seen_recheck        | standard_taker |       66 |      46 |       20 |     19 |       47 |      28.79 |    -252.43 |   -16660.1  |           0.405 |      -1405.5  |       16688.7  |
| near_half_atr | volume_1p2x |          2 |            480 | 2026_Nov_recent_exploratory | standard_taker |       14 |       0 |       14 |      5 |        9 |      35.71 |     -72.89 |    -1020.5  |           0.79  |      -1008.79 |        2678.74 |
| near_half_atr | volume_1p2x |          3 |            240 | 2025_train                  | standard_taker |      177 |      84 |       93 |     68 |      109 |      38.42 |     -38.75 |    -6859.5  |           0.911 |      -1688.81 |       12660.4  |
| near_half_atr | volume_1p2x |          3 |            240 | 2026_H1_validation          | standard_taker |      104 |      44 |       60 |     43 |       61 |      41.35 |      18.26 |     1899.32 |           1.055 |      -1589.81 |        6597.96 |
| near_half_atr | volume_1p2x |          3 |            240 | 2026_H2_seen_recheck        | standard_taker |       69 |      45 |       24 |     17 |       52 |      24.64 |    -228.89 |   -15793.1  |           0.295 |      -1182.02 |       15793.1  |
| near_half_atr | volume_1p2x |          3 |            240 | 2026_Nov_recent_exploratory | standard_taker |       14 |       0 |       14 |      5 |        9 |      35.71 |      10.66 |      149.25 |           1.047 |       -811.86 |        1369.08 |
| near_half_atr | volume_1p2x |          3 |            480 | 2025_train                  | standard_taker |      163 |      79 |       84 |     61 |      102 |      37.42 |      58.9  |     9601.03 |           1.114 |      -1740.17 |       12275.4  |
| near_half_atr | volume_1p2x |          3 |            480 | 2026_H1_validation          | standard_taker |       97 |      40 |       57 |     40 |       57 |      41.24 |      78.55 |     7619.28 |           1.203 |      -1589.81 |        7775.37 |
| near_half_atr | volume_1p2x |          3 |            480 | 2026_H2_seen_recheck        | standard_taker |       64 |      44 |       20 |     18 |       46 |      28.12 |    -197.84 |   -12661.5  |           0.519 |      -1182.02 |       12690.1  |
| near_half_atr | volume_1p2x |          3 |            480 | 2026_Nov_recent_exploratory | standard_taker |       14 |       0 |       14 |      5 |        9 |      35.71 |      59.93 |      839.05 |           1.172 |      -1008.79 |        2678.74 |
| touch         | any         |          2 |            240 | 2025_train                  | standard_taker |      156 |      78 |       78 |     65 |       91 |      41.67 |    -111.73 |   -17430    |           0.744 |      -1669.22 |       20362.8  |
| touch         | any         |          2 |            240 | 2026_H1_validation          | standard_taker |       73 |      29 |       44 |     35 |       38 |      47.95 |     120.76 |     8815.76 |           1.5   |      -1589.81 |        2427.41 |
| touch         | any         |          2 |            240 | 2026_H2_seen_recheck        | standard_taker |       56 |      38 |       18 |     17 |       39 |      30.36 |    -189.7  |   -10623.1  |           0.372 |      -1012.29 |       10623.1  |
| touch         | any         |          2 |            240 | 2026_Nov_recent_exploratory | standard_taker |       13 |       0 |       13 |      4 |        9 |      30.77 |    -137.72 |    -1790.31 |           0.368 |       -751.17 |        2139.76 |
| touch         | any         |          2 |            480 | 2025_train                  | standard_taker |      148 |      74 |       74 |     54 |       94 |      36.49 |    -106.46 |   -15755.3  |           0.801 |      -1740.17 |       24040.3  |
| touch         | any         |          2 |            480 | 2026_H1_validation          | standard_taker |       70 |      27 |       43 |     31 |       39 |      44.29 |      40.07 |     2805.22 |           1.112 |      -1589.81 |        5911.06 |
| touch         | any         |          2 |            480 | 2026_H2_seen_recheck        | standard_taker |       53 |      36 |       17 |     16 |       37 |      30.19 |    -178.47 |    -9458.93 |           0.519 |      -1134.25 |        9458.93 |
| touch         | any         |          2 |            480 | 2026_Nov_recent_exploratory | standard_taker |       11 |       0 |       11 |      4 |        7 |      36.36 |    -153.24 |    -1685.66 |           0.531 |      -1008.79 |        1948.58 |
| touch         | any         |          3 |            240 | 2025_train                  | standard_taker |      154 |      76 |       78 |     63 |       91 |      40.91 |     -68.76 |   -10589.3  |           0.845 |      -1669.22 |       16512.2  |
| touch         | any         |          3 |            240 | 2026_H1_validation          | standard_taker |       72 |      29 |       43 |     34 |       38 |      47.22 |     109.01 |     7848.55 |           1.425 |      -1589.81 |        3602.3  |
| touch         | any         |          3 |            240 | 2026_H2_seen_recheck        | standard_taker |       56 |      38 |       18 |     16 |       40 |      28.57 |    -203.51 |   -11396.5  |           0.357 |      -1012.29 |       11396.5  |
| touch         | any         |          3 |            240 | 2026_Nov_recent_exploratory | standard_taker |       13 |       0 |       13 |      4 |        9 |      30.77 |    -137.72 |    -1790.31 |           0.368 |       -751.17 |        2139.76 |
| touch         | any         |          3 |            480 | 2025_train                  | standard_taker |      146 |      72 |       74 |     49 |       97 |      33.56 |     -35.2  |    -5138.49 |           0.936 |      -1740.17 |       18385.6  |
| touch         | any         |          3 |            480 | 2026_H1_validation          | standard_taker |       68 |      27 |       41 |     29 |       39 |      42.65 |      26.92 |     1830.54 |           1.073 |      -1589.81 |        6920.53 |
| touch         | any         |          3 |            480 | 2026_H2_seen_recheck        | standard_taker |       53 |      36 |       17 |     15 |       38 |      28.3  |    -245.53 |   -13013    |           0.369 |      -1134.25 |       13013    |
| touch         | any         |          3 |            480 | 2026_Nov_recent_exploratory | standard_taker |       11 |       0 |       11 |      4 |        7 |      36.36 |    -107.61 |    -1183.66 |           0.671 |      -1008.79 |        1948.58 |
| touch         | volume_1p2x |          2 |            240 | 2025_train                  | standard_taker |       98 |      50 |       48 |     42 |       56 |      42.86 |    -101.39 |    -9936.67 |           0.755 |      -1667.85 |       13080.2  |
| touch         | volume_1p2x |          2 |            240 | 2026_H1_validation          | standard_taker |       57 |      21 |       36 |     29 |       28 |      50.88 |     121.69 |     6936.29 |           1.431 |      -1589.81 |        2156.15 |
| touch         | volume_1p2x |          2 |            240 | 2026_H2_seen_recheck        | standard_taker |       40 |      27 |       13 |     10 |       30 |      25    |    -297.33 |   -11893    |           0.178 |      -1182.02 |       11893    |
| touch         | volume_1p2x |          2 |            240 | 2026_Nov_recent_exploratory | standard_taker |        8 |       0 |        8 |      2 |        6 |      25    |    -121.39 |     -971.12 |           0.366 |       -520.64 |        1082.51 |
| touch         | volume_1p2x |          2 |            480 | 2025_train                  | standard_taker |       94 |      48 |       46 |     38 |       56 |      40.43 |     -60.47 |    -5684.11 |           0.881 |      -1740.17 |       11260.1  |
| touch         | volume_1p2x |          2 |            480 | 2026_H1_validation          | standard_taker |       55 |      20 |       35 |     27 |       28 |      49.09 |      68.54 |     3769.51 |           1.185 |      -1589.81 |        4840.9  |
| touch         | volume_1p2x |          2 |            480 | 2026_H2_seen_recheck        | standard_taker |       38 |      26 |       12 |      9 |       29 |      23.68 |    -332.04 |   -12617.4  |           0.277 |      -1182.02 |       12617.4  |
| touch         | volume_1p2x |          2 |            480 | 2026_Nov_recent_exploratory | standard_taker |        8 |       0 |        8 |      3 |        5 |      37.5  |     -80.56 |     -644.45 |           0.767 |      -1008.79 |        1866.88 |
| touch         | volume_1p2x |          3 |            240 | 2025_train                  | standard_taker |       97 |      49 |       48 |     41 |       56 |      42.27 |     -81.34 |    -7890.13 |           0.805 |      -1667.85 |       11562.4  |
| touch         | volume_1p2x |          3 |            240 | 2026_H1_validation          | standard_taker |       56 |      21 |       35 |     28 |       28 |      50    |     150.89 |     8449.6  |           1.5   |      -1589.81 |        2872.68 |
| touch         | volume_1p2x |          3 |            240 | 2026_H2_seen_recheck        | standard_taker |       40 |      27 |       13 |     10 |       30 |      25    |    -292.38 |   -11695.1  |           0.192 |      -1182.02 |       11695.1  |
| touch         | volume_1p2x |          3 |            240 | 2026_Nov_recent_exploratory | standard_taker |        8 |       0 |        8 |      2 |        6 |      25    |    -121.39 |     -971.12 |           0.366 |       -520.64 |        1082.51 |
| touch         | volume_1p2x |          3 |            480 | 2025_train                  | standard_taker |       93 |      47 |       46 |     34 |       59 |      36.56 |     -58.11 |    -5403.98 |           0.89  |      -1740.17 |       10790.4  |
| touch         | volume_1p2x |          3 |            480 | 2026_H1_validation          | standard_taker |       54 |      20 |       34 |     26 |       28 |      48.15 |     110.91 |     5989.25 |           1.294 |      -1589.81 |        5233.82 |
| touch         | volume_1p2x |          3 |            480 | 2026_H2_seen_recheck        | standard_taker |       38 |      26 |       12 |      9 |       29 |      23.68 |    -336.31 |   -12779.8  |           0.268 |      -1182.02 |       12779.8  |
| touch         | volume_1p2x |          3 |            480 | 2026_Nov_recent_exploratory | standard_taker |        8 |       0 |        8 |      3 |        5 |      37.5  |      34.27 |      274.16 |           1.099 |      -1008.79 |        1866.88 |

## Baseline monthly table: strict touch + volume + 2R + 8h
| pullback   | volume      |   target_R |   max_hold_min | month_ist   |   trades |   net_pts | status   |
|:-----------|:------------|-----------:|---------------:|:------------|---------:|----------:|:---------|
| touch      | volume_1p2x |          2 |            480 | 2025-01     |        2 |  -2438.7  | Loss     |
| touch      | volume_1p2x |          2 |            480 | 2025-02     |        8 |   5522.56 | Profit   |
| touch      | volume_1p2x |          2 |            480 | 2025-03     |       15 |  -4371.22 | Loss     |
| touch      | volume_1p2x |          2 |            480 | 2025-04     |        6 |   2942.76 | Profit   |
| touch      | volume_1p2x |          2 |            480 | 2025-05     |        7 |  -5845.57 | Loss     |
| touch      | volume_1p2x |          2 |            480 | 2025-06     |        7 |   1785.06 | Profit   |
| touch      | volume_1p2x |          2 |            480 | 2025-07     |       11 |   2464.75 | Profit   |
| touch      | volume_1p2x |          2 |            480 | 2025-08     |        6 |    353.86 | Profit   |
| touch      | volume_1p2x |          2 |            480 | 2025-09     |        9 |  -8589.73 | Loss     |
| touch      | volume_1p2x |          2 |            480 | 2025-10     |        6 |   6385.2  | Profit   |
| touch      | volume_1p2x |          2 |            480 | 2025-11     |        9 |  -2765.1  | Loss     |
| touch      | volume_1p2x |          2 |            480 | 2025-12     |        8 |  -1127.98 | Loss     |
| touch      | volume_1p2x |          2 |            480 | 2026-01     |       11 |   -423.96 | Loss     |
| touch      | volume_1p2x |          2 |            480 | 2026-02     |       11 |   1981.49 | Profit   |
| touch      | volume_1p2x |          2 |            480 | 2026-03     |       10 |   3975.86 | Profit   |
| touch      | volume_1p2x |          2 |            480 | 2026-04     |        6 |   2787.93 | Profit   |
| touch      | volume_1p2x |          2 |            480 | 2026-05     |       12 |  -4350.02 | Loss     |
| touch      | volume_1p2x |          2 |            480 | 2026-06     |        5 |   -201.79 | Loss     |
| touch      | volume_1p2x |          2 |            480 | 2026-07     |        9 |  -5371.81 | Loss     |
| touch      | volume_1p2x |          2 |            480 | 2026-08     |       10 |  -3125.67 | Loss     |
| touch      | volume_1p2x |          2 |            480 | 2026-09     |        6 |  -2133.03 | Loss     |
| touch      | volume_1p2x |          2 |            480 | 2026-10     |       13 |  -1986.92 | Loss     |
| touch      | volume_1p2x |          2 |            480 | 2026-11     |        8 |   -644.45 | Loss     |

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
