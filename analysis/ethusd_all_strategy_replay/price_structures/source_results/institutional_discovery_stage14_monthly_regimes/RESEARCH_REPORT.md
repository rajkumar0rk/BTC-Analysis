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

**Models passing the research gate: 0 / 424**

## 2025-selected leaders, and their actual 2026 behavior
| family                            | regime                        |   target_R |   max_hold_min |   year2025_n |   profit_months_2025 |   loss_months_2025 |   net_2025 |   year2026_n |   profit_months_2026 |   loss_months_2026 |   net_2026 |
|:----------------------------------|:------------------------------|-----------:|---------------:|-------------:|---------------------:|-------------------:|-----------:|-------------:|---------------------:|-------------------:|-----------:|
| S11_04_trend_pullback_engulf      | 1h_volume_burst_adx20         |          3 |            240 |          422 |                    8 |                  4 |  -10892    |          271 |                    0 |                 11 |  -32293.9  |
| S13_pullback_near_half_atr        | 4h_efficiency30_adx25         |          3 |            480 |           62 |                    7 |                  4 |    8181.06 |           71 |                    3 |                  8 |   -3823.48 |
| S11_07_failed_break_followthrough | 4h_low_atr_then_5m_burst      |          2 |            480 |           72 |                    7 |                  5 |   -1096.16 |           35 |                    4 |                  6 |    1189.64 |
| S13_pullback_touch                | all_entries                   |          3 |            240 |          128 |                    7 |                  5 |   -2500.5  |          135 |                    4 |                  7 |   -3799.36 |
| S11_04_trend_pullback_engulf      | 4h_channel_break_in_direction |          3 |            240 |          158 |                    7 |                  5 |   -4623.1  |           72 |                    2 |                  9 |  -10329.8  |
| S11_05_market_structure_shift     | 4h_adx25_directional_drift    |          3 |            240 |           60 |                    7 |                  5 |   -6205.85 |           52 |                    4 |                  7 |    3038.68 |
| S11_04_trend_pullback_engulf      | 1h_volume_burst_adx20         |          3 |            480 |          422 |                    7 |                  5 |   -6278.23 |          267 |                    1 |                 10 |  -29587.5  |
| S11_04_trend_pullback_engulf      | 4h_channel_break_in_direction |          3 |            480 |          157 |                    7 |                  5 |   -7128.4  |           72 |                    2 |                  9 |   -9004.44 |
| S13_pullback_near_half_atr        | 4h_efficiency30_adx25         |          3 |            240 |           64 |                    6 |                  5 |   10663.3  |           78 |                    2 |                  9 |  -12376.5  |
| S11_06_inside_bar_break           | 4h_low_atr_then_5m_burst      |          2 |            240 |          127 |                    6 |                  5 |    2931.31 |           69 |                    3 |                  8 |   -4959.43 |
| S13_pullback_touch                | all_entries                   |          3 |            480 |          123 |                    6 |                  6 |   -1594.55 |          126 |                    4 |                  7 |  -12254.3  |
| S11_02_sweep_then_confirm         | 4h_ranging_adx18              |          3 |            480 |          160 |                    6 |                  6 |   -2649.06 |           86 |                    1 |                  9 |   -9994.68 |
| S11_05_market_structure_shift     | 4h_adx25_directional_drift    |          2 |            480 |           61 |                    6 |                  6 |   -6844.06 |           52 |                    6 |                  5 |     447.94 |
| S11_05_market_structure_shift     | 4h_adx25_directional_drift    |          2 |            240 |           62 |                    6 |                  6 |   -7138.68 |           52 |                    5 |                  6 |    -763.65 |
| S11_05_market_structure_shift     | 1h_volume_burst_adx20         |          2 |            240 |          100 |                    6 |                  6 |   -9020.1  |           95 |                    2 |                  9 |  -17514    |
| S11_04_trend_pullback_engulf      | 4h_channel_break_in_direction |          2 |            240 |          171 |                    6 |                  6 |  -12642.9  |           77 |                    3 |                  8 |   -4054.69 |
| S11_04_trend_pullback_engulf      | 4h_channel_break_in_direction |          2 |            480 |          170 |                    6 |                  6 |  -14825.2  |           77 |                    3 |                  8 |   -3525.66 |
| S11_04_trend_pullback_engulf      | 1h_volume_burst_adx20         |          2 |            480 |          443 |                    6 |                  6 |  -23264.5  |          277 |                    3 |                  8 |  -25456.6  |
| S11_03_breakout_retest            | 4h_adx25                      |          3 |            240 |          459 |                    6 |                  6 |  -43831.2  |          264 |                    0 |                 11 |  -28705.6  |
| S11_03_breakout_retest            | 4h_adx25                      |          3 |            480 |          444 |                    6 |                  6 |  -51300.6  |          258 |                    2 |                  9 |  -29610.5  |

## Passing models
None passed the predeclared criteria.

## Monthly results for those 2025-selected leaders
| family                            | regime                        |   target_R |   max_hold_min | month_ist   |   trades |   net_pts | status    |
|:----------------------------------|:------------------------------|-----------:|---------------:|:------------|---------:|----------:|:----------|
| S11_04_trend_pullback_engulf      | 1h_volume_burst_adx20         |          3 |            240 | 2025-01     |       28 |   1652.4  | Profit    |
| S11_04_trend_pullback_engulf      | 1h_volume_burst_adx20         |          3 |            240 | 2025-02     |       33 |  -8211.13 | Loss      |
| S11_04_trend_pullback_engulf      | 1h_volume_burst_adx20         |          3 |            240 | 2025-03     |       32 |   7416.81 | Profit    |
| S11_04_trend_pullback_engulf      | 1h_volume_burst_adx20         |          3 |            240 | 2025-04     |       23 |   2088.46 | Profit    |
| S11_04_trend_pullback_engulf      | 1h_volume_burst_adx20         |          3 |            240 | 2025-05     |       16 |   2060.36 | Profit    |
| S11_04_trend_pullback_engulf      | 1h_volume_burst_adx20         |          3 |            240 | 2025-06     |       38 |    587.75 | Profit    |
| S11_04_trend_pullback_engulf      | 1h_volume_burst_adx20         |          3 |            240 | 2025-07     |       45 |  -9384.6  | Loss      |
| S11_04_trend_pullback_engulf      | 1h_volume_burst_adx20         |          3 |            240 | 2025-08     |       48 | -10602.5  | Loss      |
| S11_04_trend_pullback_engulf      | 1h_volume_burst_adx20         |          3 |            240 | 2025-09     |       29 |    627.08 | Profit    |
| S11_04_trend_pullback_engulf      | 1h_volume_burst_adx20         |          3 |            240 | 2025-10     |       48 |   2458.44 | Profit    |
| S11_04_trend_pullback_engulf      | 1h_volume_burst_adx20         |          3 |            240 | 2025-11     |       58 |   1246.18 | Profit    |
| S11_04_trend_pullback_engulf      | 1h_volume_burst_adx20         |          3 |            240 | 2025-12     |       24 |   -831.18 | Loss      |
| S11_04_trend_pullback_engulf      | 1h_volume_burst_adx20         |          3 |            240 | 2026-01     |       36 |  -1299.58 | Loss      |
| S11_04_trend_pullback_engulf      | 1h_volume_burst_adx20         |          3 |            240 | 2026-02     |       40 |  -6893.15 | Loss      |
| S11_04_trend_pullback_engulf      | 1h_volume_burst_adx20         |          3 |            240 | 2026-03     |       26 |  -2926.48 | Loss      |
| S11_04_trend_pullback_engulf      | 1h_volume_burst_adx20         |          3 |            240 | 2026-04     |       14 |  -1509.73 | Loss      |
| S11_04_trend_pullback_engulf      | 1h_volume_burst_adx20         |          3 |            240 | 2026-05     |       18 |   -144.63 | Loss      |
| S11_04_trend_pullback_engulf      | 1h_volume_burst_adx20         |          3 |            240 | 2026-06     |       15 |  -1652.94 | Loss      |
| S11_04_trend_pullback_engulf      | 1h_volume_burst_adx20         |          3 |            240 | 2026-07     |       18 |  -3344.3  | Loss      |
| S11_04_trend_pullback_engulf      | 1h_volume_burst_adx20         |          3 |            240 | 2026-08     |       21 |  -4765.08 | Loss      |
| S11_04_trend_pullback_engulf      | 1h_volume_burst_adx20         |          3 |            240 | 2026-09     |       18 |   -585.75 | Loss      |
| S11_04_trend_pullback_engulf      | 1h_volume_burst_adx20         |          3 |            240 | 2026-10     |       38 |  -6796.4  | Loss      |
| S11_04_trend_pullback_engulf      | 1h_volume_burst_adx20         |          3 |            240 | 2026-11     |       27 |  -2375.86 | Loss      |
| S11_04_trend_pullback_engulf      | 4h_channel_break_in_direction |          3 |            240 | 2025-01     |       22 |  -2631.61 | Loss      |
| S11_04_trend_pullback_engulf      | 4h_channel_break_in_direction |          3 |            240 | 2025-02     |       14 |  -3524.29 | Loss      |
| S11_04_trend_pullback_engulf      | 4h_channel_break_in_direction |          3 |            240 | 2025-03     |        5 |   -917.23 | Loss      |
| S11_04_trend_pullback_engulf      | 4h_channel_break_in_direction |          3 |            240 | 2025-04     |        7 |   4857.46 | Profit    |
| S11_04_trend_pullback_engulf      | 4h_channel_break_in_direction |          3 |            240 | 2025-05     |       13 |   2398.98 | Profit    |
| S11_04_trend_pullback_engulf      | 4h_channel_break_in_direction |          3 |            240 | 2025-06     |       12 |   3730.51 | Profit    |
| S11_04_trend_pullback_engulf      | 4h_channel_break_in_direction |          3 |            240 | 2025-07     |       14 |    284.44 | Profit    |
| S11_04_trend_pullback_engulf      | 4h_channel_break_in_direction |          3 |            240 | 2025-08     |       31 | -13196.1  | Loss      |
| S11_04_trend_pullback_engulf      | 4h_channel_break_in_direction |          3 |            240 | 2025-09     |       11 |   1978.3  | Profit    |
| S11_04_trend_pullback_engulf      | 4h_channel_break_in_direction |          3 |            240 | 2025-10     |       12 |   2860.6  | Profit    |
| S11_04_trend_pullback_engulf      | 4h_channel_break_in_direction |          3 |            240 | 2025-11     |        9 |  -1657.28 | Loss      |
| S11_04_trend_pullback_engulf      | 4h_channel_break_in_direction |          3 |            240 | 2025-12     |        8 |   1193.08 | Profit    |
| S11_04_trend_pullback_engulf      | 4h_channel_break_in_direction |          3 |            240 | 2026-01     |       10 |    358.86 | Profit    |
| S11_04_trend_pullback_engulf      | 4h_channel_break_in_direction |          3 |            240 | 2026-02     |        7 |  -2816.43 | Loss      |
| S11_04_trend_pullback_engulf      | 4h_channel_break_in_direction |          3 |            240 | 2026-03     |       10 |   -817.53 | Loss      |
| S11_04_trend_pullback_engulf      | 4h_channel_break_in_direction |          3 |            240 | 2026-04     |        3 |   -329.74 | Loss      |
| S11_04_trend_pullback_engulf      | 4h_channel_break_in_direction |          3 |            240 | 2026-05     |        5 |   -505.79 | Loss      |
| S11_04_trend_pullback_engulf      | 4h_channel_break_in_direction |          3 |            240 | 2026-06     |       10 |   1427.95 | Profit    |
| S11_04_trend_pullback_engulf      | 4h_channel_break_in_direction |          3 |            240 | 2026-07     |        6 |  -1547.9  | Loss      |
| S11_04_trend_pullback_engulf      | 4h_channel_break_in_direction |          3 |            240 | 2026-08     |        5 |  -1736.03 | Loss      |
| S11_04_trend_pullback_engulf      | 4h_channel_break_in_direction |          3 |            240 | 2026-09     |        6 |   -581.13 | Loss      |
| S11_04_trend_pullback_engulf      | 4h_channel_break_in_direction |          3 |            240 | 2026-10     |        6 |  -2397.95 | Loss      |
| S11_04_trend_pullback_engulf      | 4h_channel_break_in_direction |          3 |            240 | 2026-11     |        4 |  -1384.14 | Loss      |
| S11_07_failed_break_followthrough | 4h_low_atr_then_5m_burst      |          2 |            480 | 2025-01     |        7 |  -1811.53 | Loss      |
| S11_07_failed_break_followthrough | 4h_low_atr_then_5m_burst      |          2 |            480 | 2025-02     |       10 |  -2604.72 | Loss      |
| S11_07_failed_break_followthrough | 4h_low_atr_then_5m_burst      |          2 |            480 | 2025-03     |       10 |   1144.29 | Profit    |
| S11_07_failed_break_followthrough | 4h_low_atr_then_5m_burst      |          2 |            480 | 2025-04     |        4 |    333.17 | Profit    |
| S11_07_failed_break_followthrough | 4h_low_atr_then_5m_burst      |          2 |            480 | 2025-05     |        3 |  -1337.13 | Loss      |
| S11_07_failed_break_followthrough | 4h_low_atr_then_5m_burst      |          2 |            480 | 2025-06     |        7 |   1168.92 | Profit    |
| S11_07_failed_break_followthrough | 4h_low_atr_then_5m_burst      |          2 |            480 | 2025-07     |        2 |   -310.43 | Loss      |
| S11_07_failed_break_followthrough | 4h_low_atr_then_5m_burst      |          2 |            480 | 2025-08     |        1 |    547.44 | Profit    |
| S11_07_failed_break_followthrough | 4h_low_atr_then_5m_burst      |          2 |            480 | 2025-09     |        8 |    687.3  | Profit    |
| S11_07_failed_break_followthrough | 4h_low_atr_then_5m_burst      |          2 |            480 | 2025-10     |        5 |  -1723.76 | Loss      |
| S11_07_failed_break_followthrough | 4h_low_atr_then_5m_burst      |          2 |            480 | 2025-11     |        6 |   1447.16 | Profit    |
| S11_07_failed_break_followthrough | 4h_low_atr_then_5m_burst      |          2 |            480 | 2025-12     |        9 |   1363.13 | Profit    |
| S11_07_failed_break_followthrough | 4h_low_atr_then_5m_burst      |          2 |            480 | 2026-01     |        7 |    247.28 | Profit    |
| S11_07_failed_break_followthrough | 4h_low_atr_then_5m_burst      |          2 |            480 | 2026-02     |        4 |   1277.57 | Profit    |
| S11_07_failed_break_followthrough | 4h_low_atr_then_5m_burst      |          2 |            480 | 2026-03     |        4 |    824.26 | Profit    |
| S11_07_failed_break_followthrough | 4h_low_atr_then_5m_burst      |          2 |            480 | 2026-04     |        1 |    251.16 | Profit    |
| S11_07_failed_break_followthrough | 4h_low_atr_then_5m_burst      |          2 |            480 | 2026-05     |        1 |   -321.27 | Loss      |
| S11_07_failed_break_followthrough | 4h_low_atr_then_5m_burst      |          2 |            480 | 2026-06     |        4 |   -119.04 | Loss      |
| S11_07_failed_break_followthrough | 4h_low_atr_then_5m_burst      |          2 |            480 | 2026-07     |        3 |   -275.84 | Loss      |
| S11_07_failed_break_followthrough | 4h_low_atr_then_5m_burst      |          2 |            480 | 2026-08     |        3 |   -290.94 | Loss      |
| S11_07_failed_break_followthrough | 4h_low_atr_then_5m_burst      |          2 |            480 | 2026-09     |        3 |   -235.49 | Loss      |
| S11_07_failed_break_followthrough | 4h_low_atr_then_5m_burst      |          2 |            480 | 2026-10     |        5 |   -168.05 | Loss      |
| S11_07_failed_break_followthrough | 4h_low_atr_then_5m_burst      |          2 |            480 | 2026-11     |        0 |      0    | No trades |
| S13_pullback_near_half_atr        | 4h_efficiency30_adx25         |          3 |            480 | 2025-01     |        0 |      0    | No trades |
| S13_pullback_near_half_atr        | 4h_efficiency30_adx25         |          3 |            480 | 2025-02     |        5 |    439.12 | Profit    |
| S13_pullback_near_half_atr        | 4h_efficiency30_adx25         |          3 |            480 | 2025-03     |        7 |    224.34 | Profit    |
| S13_pullback_near_half_atr        | 4h_efficiency30_adx25         |          3 |            480 | 2025-04     |        6 |  -1558.58 | Loss      |
| S13_pullback_near_half_atr        | 4h_efficiency30_adx25         |          3 |            480 | 2025-05     |        3 |    288.21 | Profit    |
| S13_pullback_near_half_atr        | 4h_efficiency30_adx25         |          3 |            480 | 2025-06     |        7 |   5717.07 | Profit    |
| S13_pullback_near_half_atr        | 4h_efficiency30_adx25         |          3 |            480 | 2025-07     |        7 |   6978.67 | Profit    |
| S13_pullback_near_half_atr        | 4h_efficiency30_adx25         |          3 |            480 | 2025-08     |        2 |   2217.33 | Profit    |
| S13_pullback_near_half_atr        | 4h_efficiency30_adx25         |          3 |            480 | 2025-09     |        7 |   -599.18 | Loss      |
| S13_pullback_near_half_atr        | 4h_efficiency30_adx25         |          3 |            480 | 2025-10     |        6 |   1463.44 | Profit    |
| S13_pullback_near_half_atr        | 4h_efficiency30_adx25         |          3 |            480 | 2025-11     |        7 |  -3101.72 | Loss      |
| S13_pullback_near_half_atr        | 4h_efficiency30_adx25         |          3 |            480 | 2025-12     |        5 |  -3887.64 | Loss      |
| S13_pullback_near_half_atr        | 4h_efficiency30_adx25         |          3 |            480 | 2026-01     |       10 |   4607.47 | Profit    |
| S13_pullback_near_half_atr        | 4h_efficiency30_adx25         |          3 |            480 | 2026-02     |        4 |  -2788.76 | Loss      |
| S13_pullback_near_half_atr        | 4h_efficiency30_adx25         |          3 |            480 | 2026-03     |        5 |   -488.8  | Loss      |
| S13_pullback_near_half_atr        | 4h_efficiency30_adx25         |          3 |            480 | 2026-04     |        2 |   -664.19 | Loss      |
| S13_pullback_near_half_atr        | 4h_efficiency30_adx25         |          3 |            480 | 2026-05     |        5 |   -430.3  | Loss      |
| S13_pullback_near_half_atr        | 4h_efficiency30_adx25         |          3 |            480 | 2026-06     |       11 |    419.17 | Profit    |
| S13_pullback_near_half_atr        | 4h_efficiency30_adx25         |          3 |            480 | 2026-07     |        5 |   -848.79 | Loss      |
| S13_pullback_near_half_atr        | 4h_efficiency30_adx25         |          3 |            480 | 2026-08     |        5 |    380.34 | Profit    |
| S13_pullback_near_half_atr        | 4h_efficiency30_adx25         |          3 |            480 | 2026-09     |        4 |  -1524.22 | Loss      |
| S13_pullback_near_half_atr        | 4h_efficiency30_adx25         |          3 |            480 | 2026-10     |       10 |  -1631.36 | Loss      |
| S13_pullback_near_half_atr        | 4h_efficiency30_adx25         |          3 |            480 | 2026-11     |       10 |   -854.04 | Loss      |
| S13_pullback_touch                | all_entries                   |          3 |            240 | 2025-01     |        5 |   1202.36 | Profit    |
| S13_pullback_touch                | all_entries                   |          3 |            240 | 2025-02     |        9 |    851.04 | Profit    |
| S13_pullback_touch                | all_entries                   |          3 |            240 | 2025-03     |       18 |   -893.04 | Loss      |
| S13_pullback_touch                | all_entries                   |          3 |            240 | 2025-04     |       12 |   -658.12 | Loss      |
| S13_pullback_touch                | all_entries                   |          3 |            240 | 2025-05     |        9 |  -1580.01 | Loss      |
| S13_pullback_touch                | all_entries                   |          3 |            240 | 2025-06     |       10 |     29.16 | Profit    |
| S13_pullback_touch                | all_entries                   |          3 |            240 | 2025-07     |       13 |   6059.72 | Profit    |
| S13_pullback_touch                | all_entries                   |          3 |            240 | 2025-08     |        9 |  -1530.28 | Loss      |
| S13_pullback_touch                | all_entries                   |          3 |            240 | 2025-09     |       15 |  -8885.44 | Loss      |
| S13_pullback_touch                | all_entries                   |          3 |            240 | 2025-10     |        8 |   1626.87 | Profit    |
| S13_pullback_touch                | all_entries                   |          3 |            240 | 2025-11     |       11 |   1052.78 | Profit    |
| S13_pullback_touch                | all_entries                   |          3 |            240 | 2025-12     |        9 |    224.46 | Profit    |
| S13_pullback_touch                | all_entries                   |          3 |            240 | 2026-01     |       14 |   2795.27 | Profit    |
| S13_pullback_touch                | all_entries                   |          3 |            240 | 2026-02     |       13 |   4286.06 | Profit    |
| S13_pullback_touch                | all_entries                   |          3 |            240 | 2026-03     |       10 |   1827.12 | Profit    |
| S13_pullback_touch                | all_entries                   |          3 |            240 | 2026-04     |       11 |   -205.03 | Loss      |
| S13_pullback_touch                | all_entries                   |          3 |            240 | 2026-05     |       13 |   -983.47 | Loss      |
| S13_pullback_touch                | all_entries                   |          3 |            240 | 2026-06     |        7 |    738.23 | Profit    |
| S13_pullback_touch                | all_entries                   |          3 |            240 | 2026-07     |       10 |  -4529.62 | Loss      |
| S13_pullback_touch                | all_entries                   |          3 |            240 | 2026-08     |       12 |    -33.33 | Loss      |
| S13_pullback_touch                | all_entries                   |          3 |            240 | 2026-09     |       14 |  -3370.15 | Loss      |
| S13_pullback_touch                | all_entries                   |          3 |            240 | 2026-10     |       19 |  -3054.76 | Loss      |
| S13_pullback_touch                | all_entries                   |          3 |            240 | 2026-11     |       12 |  -1269.68 | Loss      |

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
