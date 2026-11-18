# Stage 13 — 4H trend + 1H EMA20 pullback + 15M breakout

Rules predeclared: two pullback strictness choices, optional 15M breakout volume,
2R/3R target and 4h/8h maximum hold, 16 strategy configurations.
Every signal uses completed candles, next 1M OPEN execution, and structural stop.
No fixed trading time. Historical 2026 has already been researched.

## Monthly research consistency
| pullback      | volume      |   target_R |   max_hold_min |   trades_2025 |   profitable_2025 |   losing_2025 |   no_trade_2025 |   net_2025 |   trades_2026 |   profitable_2026 |   losing_2026 |   no_trade_2026 |   net_2026 | sufficient_samples   | positive_2025_H1_H2   | passes_monthly_gate   |
|:--------------|:------------|-----------:|---------------:|--------------:|------------------:|--------------:|----------------:|-----------:|--------------:|------------------:|--------------:|----------------:|-----------:|:---------------------|:----------------------|:----------------------|
| near_half_atr | any         |          2 |            240 |           279 |                 2 |            10 |               0 |  -33468.7  |           251 |                 3 |             7 |               1 |  -27738.2  | True                 | False                 | False                 |
| near_half_atr | any         |          2 |            480 |           254 |                 5 |             7 |               0 |  -24208.8  |           223 |                 3 |             7 |               1 |  -18899.8  | True                 | False                 | False                 |
| near_half_atr | any         |          3 |            240 |           275 |                 3 |             9 |               0 |  -20802.7  |           245 |                 2 |             8 |               1 |  -24884.8  | True                 | False                 | False                 |
| near_half_atr | any         |          3 |            480 |           250 |                 6 |             6 |               0 |    -703.2  |           215 |                 3 |             7 |               1 |  -15010.4  | True                 | False                 | False                 |
| near_half_atr | volume_1p2x |          2 |            240 |           179 |                 6 |             6 |               0 |  -13605.6  |           177 |                 2 |             8 |               1 |  -18945.1  | True                 | False                 | False                 |
| near_half_atr | volume_1p2x |          2 |            480 |           167 |                 5 |             7 |               0 |   -2084.75 |           166 |                 5 |             5 |               1 |  -16337.3  | True                 | False                 | False                 |
| near_half_atr | volume_1p2x |          3 |            240 |           177 |                 6 |             6 |               0 |   -6297    |           172 |                 3 |             7 |               1 |  -14304.5  | True                 | False                 | False                 |
| near_half_atr | volume_1p2x |          3 |            480 |           163 |                 6 |             6 |               0 |    9327.8  |           160 |                 5 |             5 |               1 |   -6168.55 | True                 | False                 | False                 |
| touch         | any         |          2 |            240 |           157 |                 3 |             9 |               0 |  -17423.3  |           129 |                 6 |             4 |               1 |   -1807.3  | True                 | False                 | False                 |
| touch         | any         |          2 |            480 |           149 |                 4 |             8 |               0 |  -16584.5  |           123 |                 4 |             6 |               1 |   -6653.71 | True                 | False                 | False                 |
| touch         | any         |          3 |            240 |           155 |                 3 |             9 |               0 |  -10582.7  |           128 |                 4 |             6 |               1 |   -3547.92 | True                 | False                 | False                 |
| touch         | any         |          3 |            480 |           147 |                 5 |             7 |               0 |   -5967.61 |           121 |                 3 |             7 |               1 |  -11182.5  | True                 | False                 | False                 |
| touch         | volume_1p2x |          2 |            240 |            99 |                 5 |             7 |               0 |   -9930.06 |            97 |                 5 |             5 |               1 |   -4956.75 | True                 | False                 | False                 |
| touch         | volume_1p2x |          2 |            480 |            95 |                 6 |             6 |               0 |   -6513.23 |            93 |                 3 |             7 |               1 |   -8847.92 | True                 | False                 | False                 |
| touch         | volume_1p2x |          3 |            240 |            98 |                 6 |             6 |               0 |   -7883.52 |            96 |                 5 |             5 |               1 |   -3245.47 | True                 | False                 | False                 |
| touch         | volume_1p2x |          3 |            480 |            94 |                 6 |             6 |               0 |   -6233.1  |            92 |                 5 |             5 |               1 |   -6790.53 | True                 | False                 | False                 |

## Full standard after-fee period results
| pullback      | volume      |   target_R |   max_hold_min | period               | fee            |   trades |   longs |   shorts |   wins |   losses |   win_rate |   mean_net |   net_total |   profit_factor |   worst_trade |   max_drawdown |
|:--------------|:------------|-----------:|---------------:|:---------------------|:---------------|---------:|--------:|---------:|-------:|---------:|-----------:|-----------:|------------:|----------------:|--------------:|---------------:|
| near_half_atr | any         |          2 |            240 | 2025_train           | standard_taker |      279 |     133 |      146 |    108 |      171 |      38.71 |    -119.96 |   -33468.7  |           0.732 |      -1688.81 |       35862.6  |
| near_half_atr | any         |          2 |            240 | 2026_H1_validation   | standard_taker |      142 |      61 |       81 |     56 |       86 |      39.44 |     -32.82 |    -4661.12 |           0.893 |      -1589.81 |        6990.31 |
| near_half_atr | any         |          2 |            240 | 2026_H2_seen_recheck | standard_taker |      109 |      72 |       37 |     25 |       84 |      22.94 |    -211.72 |   -23077    |           0.289 |      -1405.5  |       23077    |
| near_half_atr | any         |          2 |            480 | 2025_train           | standard_taker |      254 |     121 |      133 |     96 |      158 |      37.8  |     -95.31 |   -24208.8  |           0.819 |      -1740.17 |       31583.7  |
| near_half_atr | any         |          2 |            480 | 2026_H1_validation   | standard_taker |      130 |      54 |       76 |     54 |       76 |      41.54 |      -9.05 |    -1176.09 |           0.975 |      -1589.81 |        9667    |
| near_half_atr | any         |          2 |            480 | 2026_H2_seen_recheck | standard_taker |       93 |      63 |       30 |     27 |       66 |      29.03 |    -190.58 |   -17723.7  |           0.5   |      -1405.5  |       17723.7  |
| near_half_atr | any         |          3 |            240 | 2025_train           | standard_taker |      275 |     129 |      146 |    103 |      172 |      37.45 |     -75.65 |   -20802.7  |           0.834 |      -1688.81 |       23015.5  |
| near_half_atr | any         |          3 |            240 | 2026_H1_validation   | standard_taker |      139 |      59 |       80 |     54 |       85 |      38.85 |     -24.06 |    -3344.65 |           0.922 |      -1589.81 |        9149.73 |
| near_half_atr | any         |          3 |            240 | 2026_H2_seen_recheck | standard_taker |      106 |      69 |       37 |     24 |       82 |      22.64 |    -203.21 |   -21540.1  |           0.313 |      -1012.29 |       21540.1  |
| near_half_atr | any         |          3 |            480 | 2025_train           | standard_taker |      250 |     118 |      132 |     87 |      163 |      34.8  |      -2.81 |     -703.2  |           0.995 |      -1740.17 |       22559.3  |
| near_half_atr | any         |          3 |            480 | 2026_H1_validation   | standard_taker |      124 |      51 |       73 |     48 |       76 |      38.71 |       8.81 |     1092.31 |           1.024 |      -1589.81 |       11285.4  |
| near_half_atr | any         |          3 |            480 | 2026_H2_seen_recheck | standard_taker |       91 |      61 |       30 |     25 |       66 |      27.47 |    -176.95 |   -16102.7  |           0.527 |      -1134.25 |       16102.7  |
| near_half_atr | volume_1p2x |          2 |            240 | 2025_train           | standard_taker |      179 |      86 |       93 |     71 |      108 |      39.66 |     -76.01 |   -13605.6  |           0.822 |      -1688.81 |       15497.2  |
| near_half_atr | volume_1p2x |          2 |            240 | 2026_H1_validation   | standard_taker |      107 |      46 |       61 |     44 |       63 |      41.12 |      -6.58 |     -703.78 |           0.98  |      -1589.81 |        5659.73 |
| near_half_atr | volume_1p2x |          2 |            240 | 2026_H2_seen_recheck | standard_taker |       70 |      46 |       24 |     16 |       54 |      22.86 |    -260.59 |   -18241.3  |           0.234 |      -1405.5  |       18241.3  |
| near_half_atr | volume_1p2x |          2 |            480 | 2025_train           | standard_taker |      167 |      82 |       85 |     69 |       98 |      41.32 |     -12.48 |    -2084.75 |           0.975 |      -1740.17 |       15662.2  |
| near_half_atr | volume_1p2x |          2 |            480 | 2026_H1_validation   | standard_taker |      101 |      42 |       59 |     44 |       57 |      43.56 |      10.39 |     1049.46 |           1.027 |      -1589.81 |        5476.78 |
| near_half_atr | volume_1p2x |          2 |            480 | 2026_H2_seen_recheck | standard_taker |       65 |      45 |       20 |     18 |       47 |      27.69 |    -267.49 |   -17386.8  |           0.379 |      -1405.5  |       17415.4  |
| near_half_atr | volume_1p2x |          3 |            240 | 2025_train           | standard_taker |      177 |      84 |       93 |     69 |      108 |      38.98 |     -35.58 |    -6297    |           0.918 |      -1688.81 |       12097.9  |
| near_half_atr | volume_1p2x |          3 |            240 | 2026_H1_validation   | standard_taker |      104 |      44 |       60 |     43 |       61 |      41.35 |      18.26 |     1899.32 |           1.055 |      -1589.81 |        6597.96 |
| near_half_atr | volume_1p2x |          3 |            240 | 2026_H2_seen_recheck | standard_taker |       68 |      44 |       24 |     16 |       52 |      23.53 |    -238.29 |   -16203.8  |           0.277 |      -1182.02 |       16203.8  |
| near_half_atr | volume_1p2x |          3 |            480 | 2025_train           | standard_taker |      163 |      79 |       84 |     61 |      102 |      37.42 |      57.23 |     9327.8  |           1.111 |      -1740.17 |       12548.6  |
| near_half_atr | volume_1p2x |          3 |            480 | 2026_H1_validation   | standard_taker |       97 |      40 |       57 |     40 |       57 |      41.24 |      78.55 |     7619.28 |           1.203 |      -1589.81 |        7775.37 |
| near_half_atr | volume_1p2x |          3 |            480 | 2026_H2_seen_recheck | standard_taker |       63 |      43 |       20 |     17 |       46 |      26.98 |    -218.85 |   -13787.8  |           0.476 |      -1182.02 |       13816.5  |
| touch         | any         |          2 |            240 | 2025_train           | standard_taker |      157 |      78 |       79 |     66 |       91 |      42.04 |    -110.98 |   -17423.3  |           0.744 |      -1669.22 |       20356.1  |
| touch         | any         |          2 |            240 | 2026_H1_validation   | standard_taker |       73 |      29 |       44 |     35 |       38 |      47.95 |     120.76 |     8815.76 |           1.5   |      -1589.81 |        2427.41 |
| touch         | any         |          2 |            240 | 2026_H2_seen_recheck | standard_taker |       56 |      38 |       18 |     17 |       39 |      30.36 |    -189.7  |   -10623.1  |           0.372 |      -1012.29 |       10623.1  |
| touch         | any         |          2 |            480 | 2025_train           | standard_taker |      149 |      74 |       75 |     54 |       95 |      36.24 |    -111.31 |   -16584.5  |           0.793 |      -1740.17 |       24869.4  |
| touch         | any         |          2 |            480 | 2026_H1_validation   | standard_taker |       70 |      27 |       43 |     31 |       39 |      44.29 |      40.07 |     2805.22 |           1.112 |      -1589.81 |        5911.06 |
| touch         | any         |          2 |            480 | 2026_H2_seen_recheck | standard_taker |       53 |      36 |       17 |     16 |       37 |      30.19 |    -178.47 |    -9458.93 |           0.519 |      -1134.25 |        9458.93 |
| touch         | any         |          3 |            240 | 2025_train           | standard_taker |      155 |      76 |       79 |     64 |       91 |      41.29 |     -68.28 |   -10582.7  |           0.845 |      -1669.22 |       16505.6  |
| touch         | any         |          3 |            240 | 2026_H1_validation   | standard_taker |       72 |      29 |       43 |     34 |       38 |      47.22 |     109.01 |     7848.55 |           1.425 |      -1589.81 |        3602.3  |
| touch         | any         |          3 |            240 | 2026_H2_seen_recheck | standard_taker |       56 |      38 |       18 |     16 |       40 |      28.57 |    -203.51 |   -11396.5  |           0.357 |      -1012.29 |       11396.5  |
| touch         | any         |          3 |            480 | 2025_train           | standard_taker |      147 |      72 |       75 |     49 |       98 |      33.33 |     -40.6  |    -5967.61 |           0.927 |      -1740.17 |       19214.7  |
| touch         | any         |          3 |            480 | 2026_H1_validation   | standard_taker |       68 |      27 |       41 |     29 |       39 |      42.65 |      26.92 |     1830.54 |           1.073 |      -1589.81 |        6920.53 |
| touch         | any         |          3 |            480 | 2026_H2_seen_recheck | standard_taker |       53 |      36 |       17 |     15 |       38 |      28.3  |    -245.53 |   -13013    |           0.369 |      -1134.25 |       13013    |
| touch         | volume_1p2x |          2 |            240 | 2025_train           | standard_taker |       99 |      50 |       49 |     43 |       56 |      43.43 |    -100.3  |    -9930.06 |           0.755 |      -1667.85 |       13073.6  |
| touch         | volume_1p2x |          2 |            240 | 2026_H1_validation   | standard_taker |       57 |      21 |       36 |     29 |       28 |      50.88 |     121.69 |     6936.29 |           1.431 |      -1589.81 |        2156.15 |
| touch         | volume_1p2x |          2 |            240 | 2026_H2_seen_recheck | standard_taker |       40 |      27 |       13 |     10 |       30 |      25    |    -297.33 |   -11893    |           0.178 |      -1182.02 |       11893    |
| touch         | volume_1p2x |          2 |            480 | 2025_train           | standard_taker |       95 |      48 |       47 |     38 |       57 |      40    |     -68.56 |    -6513.23 |           0.866 |      -1740.17 |       12089.2  |
| touch         | volume_1p2x |          2 |            480 | 2026_H1_validation   | standard_taker |       55 |      20 |       35 |     27 |       28 |      49.09 |      68.54 |     3769.51 |           1.185 |      -1589.81 |        4840.9  |
| touch         | volume_1p2x |          2 |            480 | 2026_H2_seen_recheck | standard_taker |       38 |      26 |       12 |      9 |       29 |      23.68 |    -332.04 |   -12617.4  |           0.277 |      -1182.02 |       12617.4  |
| touch         | volume_1p2x |          3 |            240 | 2025_train           | standard_taker |       98 |      49 |       49 |     42 |       56 |      42.86 |     -80.44 |    -7883.52 |           0.806 |      -1667.85 |       11555.8  |
| touch         | volume_1p2x |          3 |            240 | 2026_H1_validation   | standard_taker |       56 |      21 |       35 |     28 |       28 |      50    |     150.89 |     8449.6  |           1.5   |      -1589.81 |        2872.68 |
| touch         | volume_1p2x |          3 |            240 | 2026_H2_seen_recheck | standard_taker |       40 |      27 |       13 |     10 |       30 |      25    |    -292.38 |   -11695.1  |           0.192 |      -1182.02 |       11695.1  |
| touch         | volume_1p2x |          3 |            480 | 2025_train           | standard_taker |       94 |      47 |       47 |     34 |       60 |      36.17 |     -66.31 |    -6233.1  |           0.875 |      -1740.17 |       11619.5  |
| touch         | volume_1p2x |          3 |            480 | 2026_H1_validation   | standard_taker |       54 |      20 |       34 |     26 |       28 |      48.15 |     110.91 |     5989.25 |           1.294 |      -1589.81 |        5233.82 |
| touch         | volume_1p2x |          3 |            480 | 2026_H2_seen_recheck | standard_taker |       38 |      26 |       12 |      9 |       29 |      23.68 |    -336.31 |   -12779.8  |           0.268 |      -1182.02 |       12779.8  |

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
| touch      | volume_1p2x |          2 |            480 | 2025-09     |       10 |  -9418.85 | Loss     |
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
| touch      | volume_1p2x |          2 |            480 | 2026-11     |        0 |      0    | No trade |

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
