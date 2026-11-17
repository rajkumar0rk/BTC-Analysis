# Stage14 — Finding monthly consistency from known-at-entry BTC market regime

## What was measured
Original Stage11 eight market-structure entry families and Stage13 two trend-pullback variants.
Each compared across 12 predeclared 4H/1H/previous-month regimes, 2R/3R
and 4h/8h maximum holds. Entries can occur at any time. Same structural stop.
1m conservative stop-first replay and standard fees/GST/slippage.

## Monthly consistency gate
>=9 active 2025 and >=8 active 2026; >=75% profitable active months each year; >=60/30/20 trades and net-positive 2025/H1/H2

Months with no trades are shown separately and cannot count as profitable.
2026 windows are research-exposed and NOT independent tests.

**Models passing the research gate: 0 / 428**

## 2025-selected leaders, and their actual 2026 behavior
| family                            | regime                          |   target_R |   max_hold_min |   year2025_n |   profit_months_2025 |   loss_months_2025 |   net_2025 |   year2026_n |   profit_months_2026 |   loss_months_2026 |   net_2026 |
|:----------------------------------|:--------------------------------|-----------:|---------------:|-------------:|---------------------:|-------------------:|-----------:|-------------:|---------------------:|-------------------:|-----------:|
| S11_07_failed_break_followthrough | 1h_volume_burst_adx20           |          2 |            480 |          151 |                    8 |                  4 |    7423.54 |          113 |                    2 |                  9 |  -16678.8  |
| S11_05_market_structure_shift     | 1h_volume_burst_adx20           |          3 |            480 |          134 |                    8 |                  4 |     890.51 |          109 |                    4 |                  7 |  -14303.7  |
| S11_07_failed_break_followthrough | 1h_volume_burst_adx20           |          2 |            240 |          151 |                    8 |                  4 |     494.31 |          113 |                    2 |                  9 |  -16468.8  |
| S11_03_breakout_retest            | 4h_low_atr_then_5m_burst        |          3 |            480 |           63 |                    7 |                  5 |    3285.42 |           37 |                    3 |                  7 |   -3606.38 |
| S13_pullback_near_half_atr        | previous_month_ranging_4h_adx18 |          2 |            240 |           65 |                    7 |                  3 |    3075.34 |           28 |                    6 |                  1 |    4642.65 |
| S11_06_inside_bar_break           | 4h_low_atr_then_5m_burst        |          3 |            480 |          110 |                    7 |                  5 |    2779.75 |           61 |                    4 |                  6 |     813.69 |
| S11_07_failed_break_followthrough | 1h_volume_burst_adx20           |          3 |            480 |          149 |                    7 |                  5 |    -545.39 |          112 |                    1 |                 10 |  -17771.2  |
| S11_05_market_structure_shift     | 1h_volume_burst_adx20           |          2 |            480 |          138 |                    7 |                  5 |   -4068.88 |          110 |                    1 |                 10 |  -15862.4  |
| S11_07_failed_break_followthrough | 1h_volume_burst_adx20           |          3 |            240 |          149 |                    7 |                  5 |   -6131.91 |          112 |                    2 |                  9 |  -15097.6  |
| S13_pullback_near_half_atr        | previous_month_ranging_4h_adx18 |          3 |            240 |           63 |                    6 |                  4 |    4348.02 |           28 |                    6 |                  1 |    6840.65 |
| S11_05_market_structure_shift     | 1h_volume_burst_adx20           |          2 |            240 |          139 |                    6 |                  6 |   -4005.89 |          110 |                    2 |                  9 |  -12630.3  |
| S11_01_sweep_rejection            | 4h_high_atr_adx25               |          3 |            240 |          194 |                    6 |                  5 |   -4198.57 |          140 |                    3 |                  8 |  -20485.6  |
| S11_08_compression_breakout       | 1h_volume_burst_adx20           |          2 |            240 |           64 |                    6 |                  6 |   -4591.36 |           66 |                    0 |                 10 |  -13322.3  |
| S11_08_compression_breakout       | 1h_volume_burst_adx20           |          2 |            480 |           64 |                    6 |                  6 |   -5470.94 |           66 |                    0 |                 10 |  -14667.6  |
| S11_02_sweep_then_confirm         | 1h_volume_burst_adx20           |          3 |            480 |          337 |                    6 |                  6 |  -21773.1  |          276 |                    2 |                  9 |  -26993.7  |
| S11_02_sweep_then_confirm         | 1h_volume_burst_adx20           |          2 |            480 |          363 |                    6 |                  6 |  -27396.4  |          285 |                    2 |                  9 |  -24356.7  |
| S11_03_breakout_retest            | 4h_low_atr_then_5m_burst        |          3 |            240 |           64 |                    5 |                  7 |    1292.15 |           38 |                    3 |                  7 |   -3323.12 |
| S11_01_sweep_rejection            | 4h_high_atr_adx25               |          3 |            480 |          182 |                    5 |                  6 |    -474.84 |          135 |                    1 |                 10 |  -20561.2  |
| S11_04_trend_pullback_engulf      | 4h_low_atr_then_5m_burst        |          3 |            480 |           91 |                    5 |                  7 |   -2709.77 |           47 |                    5 |                  6 |   -1604.41 |
| S11_03_breakout_retest            | 4h_low_atr_then_5m_burst        |          2 |            480 |           64 |                    5 |                  7 |   -4036.35 |           38 |                    2 |                  8 |   -4634.18 |

## Passing models
None passed the predeclared criteria.

## Monthly results for those 2025-selected leaders
| family                            | regime                          |   target_R |   max_hold_min | month_ist   |   trades |   net_pts | status    |
|:----------------------------------|:--------------------------------|-----------:|---------------:|:------------|---------:|----------:|:----------|
| S11_03_breakout_retest            | 4h_low_atr_then_5m_burst        |          3 |            480 | 2025-01     |        3 |    341.65 | Profit    |
| S11_03_breakout_retest            | 4h_low_atr_then_5m_burst        |          3 |            480 | 2025-02     |        9 |  -1099.4  | Loss      |
| S11_03_breakout_retest            | 4h_low_atr_then_5m_burst        |          3 |            480 | 2025-03     |        5 |  -1433.46 | Loss      |
| S11_03_breakout_retest            | 4h_low_atr_then_5m_burst        |          3 |            480 | 2025-04     |        6 |   2462.37 | Profit    |
| S11_03_breakout_retest            | 4h_low_atr_then_5m_burst        |          3 |            480 | 2025-05     |        3 |   2139.03 | Profit    |
| S11_03_breakout_retest            | 4h_low_atr_then_5m_burst        |          3 |            480 | 2025-06     |        6 |    563.8  | Profit    |
| S11_03_breakout_retest            | 4h_low_atr_then_5m_burst        |          3 |            480 | 2025-07     |        6 |    939.56 | Profit    |
| S11_03_breakout_retest            | 4h_low_atr_then_5m_burst        |          3 |            480 | 2025-08     |        4 |   -415.97 | Loss      |
| S11_03_breakout_retest            | 4h_low_atr_then_5m_burst        |          3 |            480 | 2025-09     |        7 |  -1687.43 | Loss      |
| S11_03_breakout_retest            | 4h_low_atr_then_5m_burst        |          3 |            480 | 2025-10     |        5 |    681.33 | Profit    |
| S11_03_breakout_retest            | 4h_low_atr_then_5m_burst        |          3 |            480 | 2025-11     |        6 |  -2599.55 | Loss      |
| S11_03_breakout_retest            | 4h_low_atr_then_5m_burst        |          3 |            480 | 2025-12     |        3 |   3393.49 | Profit    |
| S11_03_breakout_retest            | 4h_low_atr_then_5m_burst        |          3 |            480 | 2026-01     |        3 |   -451.5  | Loss      |
| S11_03_breakout_retest            | 4h_low_atr_then_5m_burst        |          3 |            480 | 2026-02     |       10 |  -2086.49 | Loss      |
| S11_03_breakout_retest            | 4h_low_atr_then_5m_burst        |          3 |            480 | 2026-03     |        3 |   -969.54 | Loss      |
| S11_03_breakout_retest            | 4h_low_atr_then_5m_burst        |          3 |            480 | 2026-04     |        1 |   -251.85 | Loss      |
| S11_03_breakout_retest            | 4h_low_atr_then_5m_burst        |          3 |            480 | 2026-05     |        0 |      0    | No trades |
| S11_03_breakout_retest            | 4h_low_atr_then_5m_burst        |          3 |            480 | 2026-06     |        2 |    606.39 | Profit    |
| S11_03_breakout_retest            | 4h_low_atr_then_5m_burst        |          3 |            480 | 2026-07     |        3 |   -405.88 | Loss      |
| S11_03_breakout_retest            | 4h_low_atr_then_5m_burst        |          3 |            480 | 2026-08     |        3 |   1333.49 | Profit    |
| S11_03_breakout_retest            | 4h_low_atr_then_5m_burst        |          3 |            480 | 2026-09     |        5 |   -480.04 | Loss      |
| S11_03_breakout_retest            | 4h_low_atr_then_5m_burst        |          3 |            480 | 2026-10     |        5 |   -976.16 | Loss      |
| S11_03_breakout_retest            | 4h_low_atr_then_5m_burst        |          3 |            480 | 2026-11     |        2 |     75.2  | Profit    |
| S11_05_market_structure_shift     | 1h_volume_burst_adx20           |          3 |            480 | 2025-01     |        7 |   -883.27 | Loss      |
| S11_05_market_structure_shift     | 1h_volume_burst_adx20           |          3 |            480 | 2025-02     |       14 |   2001.41 | Profit    |
| S11_05_market_structure_shift     | 1h_volume_burst_adx20           |          3 |            480 | 2025-03     |        5 |    603.87 | Profit    |
| S11_05_market_structure_shift     | 1h_volume_burst_adx20           |          3 |            480 | 2025-04     |        7 |   2930.72 | Profit    |
| S11_05_market_structure_shift     | 1h_volume_burst_adx20           |          3 |            480 | 2025-05     |       15 |    451.1  | Profit    |
| S11_05_market_structure_shift     | 1h_volume_burst_adx20           |          3 |            480 | 2025-06     |       12 |     23.85 | Profit    |
| S11_05_market_structure_shift     | 1h_volume_burst_adx20           |          3 |            480 | 2025-07     |        8 |   1021.46 | Profit    |
| S11_05_market_structure_shift     | 1h_volume_burst_adx20           |          3 |            480 | 2025-08     |       17 |  -6619.14 | Loss      |
| S11_05_market_structure_shift     | 1h_volume_burst_adx20           |          3 |            480 | 2025-09     |       14 |   4271.01 | Profit    |
| S11_05_market_structure_shift     | 1h_volume_burst_adx20           |          3 |            480 | 2025-10     |       18 |   1612.83 | Profit    |
| S11_05_market_structure_shift     | 1h_volume_burst_adx20           |          3 |            480 | 2025-11     |       14 |  -2634.62 | Loss      |
| S11_05_market_structure_shift     | 1h_volume_burst_adx20           |          3 |            480 | 2025-12     |        3 |  -1888.71 | Loss      |
| S11_05_market_structure_shift     | 1h_volume_burst_adx20           |          3 |            480 | 2026-01     |       14 |    915.47 | Profit    |
| S11_05_market_structure_shift     | 1h_volume_burst_adx20           |          3 |            480 | 2026-02     |       11 |    261.92 | Profit    |
| S11_05_market_structure_shift     | 1h_volume_burst_adx20           |          3 |            480 | 2026-03     |        4 |    114.9  | Profit    |
| S11_05_market_structure_shift     | 1h_volume_burst_adx20           |          3 |            480 | 2026-04     |        8 |  -2976.51 | Loss      |
| S11_05_market_structure_shift     | 1h_volume_burst_adx20           |          3 |            480 | 2026-05     |       10 |  -2482.03 | Loss      |
| S11_05_market_structure_shift     | 1h_volume_burst_adx20           |          3 |            480 | 2026-06     |       10 |    163.86 | Profit    |
| S11_05_market_structure_shift     | 1h_volume_burst_adx20           |          3 |            480 | 2026-07     |       15 |  -2488.08 | Loss      |
| S11_05_market_structure_shift     | 1h_volume_burst_adx20           |          3 |            480 | 2026-08     |        8 |  -1452.17 | Loss      |
| S11_05_market_structure_shift     | 1h_volume_burst_adx20           |          3 |            480 | 2026-09     |        8 |  -3182.19 | Loss      |
| S11_05_market_structure_shift     | 1h_volume_burst_adx20           |          3 |            480 | 2026-10     |       14 |  -2997.1  | Loss      |
| S11_05_market_structure_shift     | 1h_volume_burst_adx20           |          3 |            480 | 2026-11     |        7 |   -181.79 | Loss      |
| S11_07_failed_break_followthrough | 1h_volume_burst_adx20           |          2 |            240 | 2025-01     |        9 |   1579.37 | Profit    |
| S11_07_failed_break_followthrough | 1h_volume_burst_adx20           |          2 |            240 | 2025-02     |       12 |  -1418.31 | Loss      |
| S11_07_failed_break_followthrough | 1h_volume_burst_adx20           |          2 |            240 | 2025-03     |        9 |  -1529.45 | Loss      |
| S11_07_failed_break_followthrough | 1h_volume_burst_adx20           |          2 |            240 | 2025-04     |       17 |   1774    | Profit    |
| S11_07_failed_break_followthrough | 1h_volume_burst_adx20           |          2 |            240 | 2025-05     |       13 |  -3208.81 | Loss      |
| S11_07_failed_break_followthrough | 1h_volume_burst_adx20           |          2 |            240 | 2025-06     |       15 |   1865.45 | Profit    |
| S11_07_failed_break_followthrough | 1h_volume_burst_adx20           |          2 |            240 | 2025-07     |        6 |   2305.68 | Profit    |
| S11_07_failed_break_followthrough | 1h_volume_burst_adx20           |          2 |            240 | 2025-08     |       15 |  -5628.65 | Loss      |
| S11_07_failed_break_followthrough | 1h_volume_burst_adx20           |          2 |            240 | 2025-09     |       11 |    836.02 | Profit    |
| S11_07_failed_break_followthrough | 1h_volume_burst_adx20           |          2 |            240 | 2025-10     |       13 |   1015.62 | Profit    |
| S11_07_failed_break_followthrough | 1h_volume_burst_adx20           |          2 |            240 | 2025-11     |       22 |   1398.35 | Profit    |
| S11_07_failed_break_followthrough | 1h_volume_burst_adx20           |          2 |            240 | 2025-12     |        9 |   1505.04 | Profit    |
| S11_07_failed_break_followthrough | 1h_volume_burst_adx20           |          2 |            240 | 2026-01     |       11 |  -2771.88 | Loss      |
| S11_07_failed_break_followthrough | 1h_volume_burst_adx20           |          2 |            240 | 2026-02     |       10 |  -3047.84 | Loss      |
| S11_07_failed_break_followthrough | 1h_volume_burst_adx20           |          2 |            240 | 2026-03     |       11 |   1178.8  | Profit    |
| S11_07_failed_break_followthrough | 1h_volume_burst_adx20           |          2 |            240 | 2026-04     |        8 |  -1292.23 | Loss      |
| S11_07_failed_break_followthrough | 1h_volume_burst_adx20           |          2 |            240 | 2026-05     |       17 |  -1682.87 | Loss      |
| S11_07_failed_break_followthrough | 1h_volume_burst_adx20           |          2 |            240 | 2026-06     |        6 |  -1567    | Loss      |
| S11_07_failed_break_followthrough | 1h_volume_burst_adx20           |          2 |            240 | 2026-07     |       14 |   -836.4  | Loss      |
| S11_07_failed_break_followthrough | 1h_volume_burst_adx20           |          2 |            240 | 2026-08     |       10 |  -2689.97 | Loss      |
| S11_07_failed_break_followthrough | 1h_volume_burst_adx20           |          2 |            240 | 2026-09     |        8 |    667.04 | Profit    |
| S11_07_failed_break_followthrough | 1h_volume_burst_adx20           |          2 |            240 | 2026-10     |       13 |  -3008.48 | Loss      |
| S11_07_failed_break_followthrough | 1h_volume_burst_adx20           |          2 |            240 | 2026-11     |        5 |  -1417.93 | Loss      |
| S11_07_failed_break_followthrough | 1h_volume_burst_adx20           |          2 |            480 | 2025-01     |        9 |    616.13 | Profit    |
| S11_07_failed_break_followthrough | 1h_volume_burst_adx20           |          2 |            480 | 2025-02     |       12 |   -113.55 | Loss      |
| S11_07_failed_break_followthrough | 1h_volume_burst_adx20           |          2 |            480 | 2025-03     |        9 |  -1472.54 | Loss      |
| S11_07_failed_break_followthrough | 1h_volume_burst_adx20           |          2 |            480 | 2025-04     |       17 |   1982.3  | Profit    |
| S11_07_failed_break_followthrough | 1h_volume_burst_adx20           |          2 |            480 | 2025-05     |       13 |  -3314.62 | Loss      |
| S11_07_failed_break_followthrough | 1h_volume_burst_adx20           |          2 |            480 | 2025-06     |       15 |   3092.06 | Profit    |
| S11_07_failed_break_followthrough | 1h_volume_burst_adx20           |          2 |            480 | 2025-07     |        6 |   3787.56 | Profit    |
| S11_07_failed_break_followthrough | 1h_volume_burst_adx20           |          2 |            480 | 2025-08     |       15 |  -5923.62 | Loss      |
| S11_07_failed_break_followthrough | 1h_volume_burst_adx20           |          2 |            480 | 2025-09     |       11 |   1268.49 | Profit    |
| S11_07_failed_break_followthrough | 1h_volume_burst_adx20           |          2 |            480 | 2025-10     |       13 |   1661.74 | Profit    |
| S11_07_failed_break_followthrough | 1h_volume_burst_adx20           |          2 |            480 | 2025-11     |       22 |   2216.46 | Profit    |
| S11_07_failed_break_followthrough | 1h_volume_burst_adx20           |          2 |            480 | 2025-12     |        9 |   3623.13 | Profit    |
| S11_07_failed_break_followthrough | 1h_volume_burst_adx20           |          2 |            480 | 2026-01     |       11 |  -2142.82 | Loss      |
| S11_07_failed_break_followthrough | 1h_volume_burst_adx20           |          2 |            480 | 2026-02     |       10 |  -3047.84 | Loss      |
| S11_07_failed_break_followthrough | 1h_volume_burst_adx20           |          2 |            480 | 2026-03     |       11 |   1178.8  | Profit    |
| S11_07_failed_break_followthrough | 1h_volume_burst_adx20           |          2 |            480 | 2026-04     |        8 |  -1292.23 | Loss      |
| S11_07_failed_break_followthrough | 1h_volume_burst_adx20           |          2 |            480 | 2026-05     |       17 |  -2117.8  | Loss      |
| S11_07_failed_break_followthrough | 1h_volume_burst_adx20           |          2 |            480 | 2026-06     |        6 |  -1567    | Loss      |
| S11_07_failed_break_followthrough | 1h_volume_burst_adx20           |          2 |            480 | 2026-07     |       14 |   -836.4  | Loss      |
| S11_07_failed_break_followthrough | 1h_volume_burst_adx20           |          2 |            480 | 2026-08     |       10 |  -1452.55 | Loss      |
| S11_07_failed_break_followthrough | 1h_volume_burst_adx20           |          2 |            480 | 2026-09     |        8 |   1072.1  | Profit    |
| S11_07_failed_break_followthrough | 1h_volume_burst_adx20           |          2 |            480 | 2026-10     |       13 |  -4284.53 | Loss      |
| S11_07_failed_break_followthrough | 1h_volume_burst_adx20           |          2 |            480 | 2026-11     |        5 |  -2188.55 | Loss      |
| S13_pullback_near_half_atr        | previous_month_ranging_4h_adx18 |          2 |            240 | 2025-01     |        0 |      0    | No trades |
| S13_pullback_near_half_atr        | previous_month_ranging_4h_adx18 |          2 |            240 | 2025-02     |       13 |    156.64 | Profit    |
| S13_pullback_near_half_atr        | previous_month_ranging_4h_adx18 |          2 |            240 | 2025-03     |        0 |      0    | No trades |
| S13_pullback_near_half_atr        | previous_month_ranging_4h_adx18 |          2 |            240 | 2025-04     |        5 |   1766.49 | Profit    |
| S13_pullback_near_half_atr        | previous_month_ranging_4h_adx18 |          2 |            240 | 2025-05     |        2 |   -393.6  | Loss      |
| S13_pullback_near_half_atr        | previous_month_ranging_4h_adx18 |          2 |            240 | 2025-06     |        5 |   2666.84 | Profit    |
| S13_pullback_near_half_atr        | previous_month_ranging_4h_adx18 |          2 |            240 | 2025-07     |       15 |  -2657.97 | Loss      |
| S13_pullback_near_half_atr        | previous_month_ranging_4h_adx18 |          2 |            240 | 2025-08     |        1 |   1206.86 | Profit    |
| S13_pullback_near_half_atr        | previous_month_ranging_4h_adx18 |          2 |            240 | 2025-09     |        5 |    567.42 | Profit    |
| S13_pullback_near_half_atr        | previous_month_ranging_4h_adx18 |          2 |            240 | 2025-10     |        3 |    233.13 | Profit    |
| S13_pullback_near_half_atr        | previous_month_ranging_4h_adx18 |          2 |            240 | 2025-11     |        5 |    417.99 | Profit    |
| S13_pullback_near_half_atr        | previous_month_ranging_4h_adx18 |          2 |            240 | 2025-12     |       11 |   -888.46 | Loss      |
| S13_pullback_near_half_atr        | previous_month_ranging_4h_adx18 |          2 |            240 | 2026-01     |        3 |    246.48 | Profit    |
| S13_pullback_near_half_atr        | previous_month_ranging_4h_adx18 |          2 |            240 | 2026-02     |        7 |   1343.79 | Profit    |
| S13_pullback_near_half_atr        | previous_month_ranging_4h_adx18 |          2 |            240 | 2026-03     |        4 |   2214.51 | Profit    |
| S13_pullback_near_half_atr        | previous_month_ranging_4h_adx18 |          2 |            240 | 2026-04     |        7 |    994.68 | Profit    |
| S13_pullback_near_half_atr        | previous_month_ranging_4h_adx18 |          2 |            240 | 2026-05     |        4 |    655.69 | Profit    |
| S13_pullback_near_half_atr        | previous_month_ranging_4h_adx18 |          2 |            240 | 2026-06     |        2 |   -856.83 | Loss      |
| S13_pullback_near_half_atr        | previous_month_ranging_4h_adx18 |          2 |            240 | 2026-07     |        0 |      0    | No trades |
| S13_pullback_near_half_atr        | previous_month_ranging_4h_adx18 |          2 |            240 | 2026-08     |        1 |     44.33 | Profit    |
| S13_pullback_near_half_atr        | previous_month_ranging_4h_adx18 |          2 |            240 | 2026-09     |        0 |      0    | No trades |
| S13_pullback_near_half_atr        | previous_month_ranging_4h_adx18 |          2 |            240 | 2026-10     |        0 |      0    | No trades |
| S13_pullback_near_half_atr        | previous_month_ranging_4h_adx18 |          2 |            240 | 2026-11     |        0 |      0    | No trades |

## Limitations
- Stage11 and Stage13 original entry criteria reused, no future information
- Previous-month regime values lag one calendar month, in Asia/Kolkata
- Higher-timeframe ADX and volume are from complete 4H/1H bars
- A no-trade month is not a winning month; sparse models excluded by sample gate
- Trade variants are standalone and overlap; never add net PnL across configurations
- All historical 2026 windows have already been used in research; no virgin holdout
- No bid/ask spread history, funding cashflows, order book impact, margin or liquidation
- 1m OHLC stop-first, gapped stops fill at worse open or stop; intraminute uncertainty
- Many tested conditions create multiple-testing/selection bias
- Net BTC price points, not risk-sized dollar account monthly return
- 2026-10-31 missing from source; 2026-11 through the 16th only
- Nothing establishes zero-loss months or future profitability

Scripts and full trade logs are saved. To establish forward profitability
freeze a single model and evaluate data acquired after this research.
