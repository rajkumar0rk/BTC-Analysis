# Stage 8 — Anytime BTCUSD directional participation patterns

## Test definition
- Use genuine Delta India BTCUSD 1m OHLCV resampled into complete 5m bars.
- Signal uses only **fully completed** candles and previous 24 complete 5m bars.
- Entry always at the next 1m candle's OPEN, not signal-bar extreme.
- Identify relative volume and volatility spikes; test breakouts, failed sweeps,
  follow-through, absorption, 3-bar momentum, compression, exhaustion, etc.
- Evaluate first passage to +200 GROSS and +200 NET (price-scaled fee threshold)
  before stops 100/200, in 30 and 60 minute windows.
- Replay one position at a time per pattern/side/model. Same-bar stop prioritized.
- Cost: taker 0.05% per side, GST 18% on fees, 5 points adverse slip each side.
- Scam prevention: +200 in the future does not imply a deployable direction prediction.
- Chronology used for stability, NOT pristine validation; 2026 already inspected.

## 2025 highest directional probabilities, followed by both 2026 windows
| pattern                          | direction   | period               |   horizon_min |   signals |   gross200_pct |   gross200_before_sl100_pct |   gross200_before_sl200_pct |   net200_possible_pct |   net200_before_sl100_pct |   clean_gross200_pct |   avg_volume_ratio |   avg_range_ratio |
|:---------------------------------|:------------|:---------------------|--------------:|----------:|---------------:|----------------------------:|----------------------------:|----------------------:|--------------------------:|---------------------:|-------------------:|------------------:|
| M_exhaustion_reversal            | LONG        | 2025_train           |            30 |       180 |          51.11 |                       30.56 |                       41.11 |                 36.67 |                     21.11 |                3.889 |               2.19 |              2.73 |
| M_exhaustion_reversal            | LONG        | 2026_H1_validation   |            30 |        72 |          27.78 |                       22.22 |                       26.39 |                 16.67 |                     15.28 |                1.389 |               2.18 |              2.76 |
| M_exhaustion_reversal            | LONG        | 2026_H2_seen_recheck |            30 |        49 |          26.53 |                       22.45 |                       22.45 |                 18.37 |                     16.33 |                2.041 |               2.24 |              3.06 |
| M_exhaustion_reversal            | SHORT       | 2025_train           |            30 |       141 |          42.55 |                       30.5  |                       37.59 |                 24.11 |                     18.44 |                2.837 |               2.33 |              2.67 |
| M_exhaustion_reversal            | SHORT       | 2026_H1_validation   |            30 |        61 |          32.79 |                       19.67 |                       26.23 |                 16.39 |                      9.84 |                3.279 |               2.22 |              2.62 |
| M_exhaustion_reversal            | SHORT       | 2026_H2_seen_recheck |            30 |        74 |          33.78 |                       24.32 |                       31.08 |                 14.86 |                     13.51 |                0     |               2.58 |              2.94 |
| I_5m_impulse_then_hold           | LONG        | 2025_train           |            30 |       421 |          46.56 |                       29.69 |                       39.9  |                 28.98 |                     18.76 |                3.8   |               3.06 |              2.22 |
| I_5m_impulse_then_hold           | LONG        | 2026_H1_validation   |            30 |       163 |          38.04 |                       22.09 |                       33.74 |                 28.83 |                     14.72 |                3.067 |               3.06 |              2.29 |
| I_5m_impulse_then_hold           | LONG        | 2026_H2_seen_recheck |            30 |       143 |          34.27 |                       21.68 |                       30.77 |                 23.78 |                     14.69 |                2.797 |               3.45 |              2.35 |
| Q_volume2_range2_strong_wick     | LONG        | 2025_train           |            30 |       560 |          48.39 |                       29.46 |                       40.54 |                 30.36 |                     18.39 |                3.036 |               3.6  |              3.24 |
| Q_volume2_range2_strong_wick     | LONG        | 2026_H1_validation   |            30 |       221 |          37.1  |                       24.89 |                       31.22 |                 24.89 |                     16.29 |                1.357 |               3.49 |              3.36 |
| Q_volume2_range2_strong_wick     | LONG        | 2026_H2_seen_recheck |            30 |       251 |          23.11 |                       17.13 |                       20.72 |                 11.55 |                      8.37 |                0.797 |               4.01 |              3.57 |
| B_volume3_range2_directional     | SHORT       | 2025_train           |            30 |       691 |          53.26 |                       29.38 |                       41.68 |                 35.17 |                     16.93 |                2.894 |               4.57 |              5.45 |
| B_volume3_range2_directional     | SHORT       | 2026_H1_validation   |            30 |       370 |          44.59 |                       27.57 |                       38.65 |                 31.62 |                     18.65 |                1.892 |               5.01 |              3.91 |
| B_volume3_range2_directional     | SHORT       | 2026_H2_seen_recheck |            30 |       245 |          35.51 |                       21.22 |                       32.24 |                 22.86 |                     13.88 |                3.265 |               5.25 |              4.88 |
| G_volume3_sweep_reject           | SHORT       | 2025_train           |            30 |       208 |          47.6  |                       28.85 |                       41.35 |                 27.88 |                     16.35 |                5.288 |               4.47 |              3.61 |
| G_volume3_sweep_reject           | SHORT       | 2026_H1_validation   |            30 |        88 |          28.41 |                       17.05 |                       23.86 |                 14.77 |                      6.82 |                2.273 |               4.3  |              3.45 |
| G_volume3_sweep_reject           | SHORT       | 2026_H2_seen_recheck |            30 |        77 |          29.87 |                       23.38 |                       27.27 |                 22.08 |                     15.58 |                1.299 |               4.56 |              3.59 |
| G_volume3_sweep_reject           | LONG        | 2025_train           |            30 |       241 |          48.13 |                       28.63 |                       40.66 |                 26.14 |                     14.94 |                2.49  |               4.25 |              3.18 |
| G_volume3_sweep_reject           | LONG        | 2026_H1_validation   |            30 |       130 |          41.54 |                       28.46 |                       34.62 |                 23.85 |                     14.62 |                3.077 |               4.29 |              3.18 |
| G_volume3_sweep_reject           | LONG        | 2026_H2_seen_recheck |            30 |        94 |          31.91 |                       22.34 |                       25.53 |                 19.15 |                     14.89 |                5.319 |               4.43 |              3.41 |
| J_absorption_then_resolution     | LONG        | 2025_train           |            30 |       140 |          46.43 |                       28.57 |                       40.71 |                 27.86 |                     16.43 |                4.286 |               2.5  |              2.86 |
| J_absorption_then_resolution     | LONG        | 2026_H1_validation   |            30 |        76 |          44.74 |                       26.32 |                       40.79 |                 30.26 |                     14.47 |                6.579 |               2.45 |              2.92 |
| J_absorption_then_resolution     | LONG        | 2026_H2_seen_recheck |            30 |        46 |          23.91 |                       15.22 |                       19.57 |                 19.57 |                      6.52 |                0     |               2.92 |              3.07 |
| Q_volume2_range2_strong_wick     | SHORT       | 2025_train           |            30 |       558 |          47.67 |                       28.49 |                       38.71 |                 29.93 |                     15.41 |                3.763 |               3.58 |              6.67 |
| Q_volume2_range2_strong_wick     | SHORT       | 2026_H1_validation   |            30 |       265 |          43.02 |                       26.04 |                       36.23 |                 33.21 |                     19.25 |                1.132 |               3.67 |              3.44 |
| Q_volume2_range2_strong_wick     | SHORT       | 2026_H2_seen_recheck |            30 |       205 |          22.93 |                       15.61 |                       20.49 |                 14.15 |                      9.27 |                1.951 |               3.79 |              3.85 |
| F_volume2_liquidity_sweep_reject | LONG        | 2025_train           |            30 |       523 |          45.89 |                       28.49 |                       38.81 |                 26.77 |                     15.87 |                3.442 |               3.27 |              2.73 |
| F_volume2_liquidity_sweep_reject | LONG        | 2026_H1_validation   |            30 |       295 |          36.27 |                       24.41 |                       29.49 |                 20    |                     11.86 |                2.373 |               3.25 |              2.68 |
| F_volume2_liquidity_sweep_reject | LONG        | 2026_H2_seen_recheck |            30 |       204 |          29.41 |                       19.61 |                       25.98 |                 16.18 |                     11.76 |                4.412 |               3.35 |              2.9  |
| A_volume2_range2_directional     | SHORT       | 2025_train           |            30 |      1276 |          48.51 |                       28.45 |                       39.11 |                 31.5  |                     16.54 |                3.527 |               3.61 |              4.61 |
| A_volume2_range2_directional     | SHORT       | 2026_H1_validation   |            30 |       696 |          41.38 |                       25.14 |                       35.06 |                 29.6  |                     17.53 |                1.58  |               3.8  |              3.35 |
| A_volume2_range2_directional     | SHORT       | 2026_H2_seen_recheck |            30 |       443 |          29.57 |                       19.86 |                       26.86 |                 17.16 |                     11.06 |                2.032 |               3.99 |              4    |
| H_5m_impulse_then_breakout       | LONG        | 2025_train           |            30 |       208 |          45.19 |                       28.37 |                       38.94 |                 28.37 |                     17.79 |                4.327 |               3.8  |              2.66 |
| H_5m_impulse_then_breakout       | LONG        | 2026_H1_validation   |            30 |        68 |          45.59 |                       25    |                       42.65 |                 35.29 |                     19.12 |                2.941 |               3.7  |              2.69 |
| H_5m_impulse_then_breakout       | LONG        | 2026_H2_seen_recheck |            30 |        69 |          30.43 |                       20.29 |                       26.09 |                 21.74 |                     15.94 |                4.348 |               4.42 |              3.03 |

## 200 gross target / 100 stop / 30-minute hold: selected rule outcomes
| pattern                          | direction   | period                      |   trades |   win_pct |   mean_net_pts |   profit_factor |   losses_or_flat |
|:---------------------------------|:------------|:----------------------------|---------:|----------:|---------------:|----------------:|-----------------:|
| A_volume2_range2_directional     | LONG        | 2025_train                  |     1153 |     29.4  |       -132.394 |           0.128 |              814 |
| A_volume2_range2_directional     | LONG        | 2026_H1_validation          |      581 |     25.47 |       -111.189 |           0.177 |              433 |
| A_volume2_range2_directional     | LONG        | 2026_H2_seen_recheck        |      474 |     22.57 |       -103.004 |           0.166 |              367 |
| A_volume2_range2_directional     | LONG        | 2026_Nov_recent_exploratory |       45 |     22.22 |       -113.577 |           0.148 |               35 |
| A_volume2_range2_directional     | SHORT       | 2025_train                  |     1246 |     29.05 |       -133.157 |           0.134 |              884 |
| A_volume2_range2_directional     | SHORT       | 2026_H1_validation          |      677 |     26.88 |       -104.887 |           0.199 |              495 |
| A_volume2_range2_directional     | SHORT       | 2026_H2_seen_recheck        |      418 |     22.49 |       -105.357 |           0.167 |              324 |
| A_volume2_range2_directional     | SHORT       | 2026_Nov_recent_exploratory |       52 |     32.69 |        -76.724 |           0.297 |               35 |
| B_volume3_range2_directional     | LONG        | 2025_train                  |      605 |     28.93 |       -136.935 |           0.121 |              430 |
| B_volume3_range2_directional     | LONG        | 2026_H1_validation          |      298 |     27.18 |       -106.019 |           0.195 |              217 |
| B_volume3_range2_directional     | LONG        | 2026_H2_seen_recheck        |      280 |     21.79 |       -104.505 |           0.161 |              219 |
| B_volume3_range2_directional     | LONG        | 2026_Nov_recent_exploratory |       24 |     20.83 |       -119.245 |           0.127 |               19 |
| B_volume3_range2_directional     | SHORT       | 2025_train                  |      681 |     30.25 |       -131.515 |           0.14  |              475 |
| B_volume3_range2_directional     | SHORT       | 2026_H1_validation          |      360 |     28.06 |       -103.781 |           0.213 |              259 |
| B_volume3_range2_directional     | SHORT       | 2026_H2_seen_recheck        |      235 |     23.83 |       -107.104 |           0.17  |              179 |
| B_volume3_range2_directional     | SHORT       | 2026_Nov_recent_exploratory |       32 |     40.62 |        -54.982 |           0.422 |               19 |
| C_volume2_range1p5_directional   | LONG        | 2025_train                  |     1556 |     28.6  |       -134.236 |           0.124 |             1111 |
| C_volume2_range1p5_directional   | LONG        | 2026_H1_validation          |      733 |     25.24 |       -108.65  |           0.178 |              548 |
| C_volume2_range1p5_directional   | LONG        | 2026_H2_seen_recheck        |      592 |     23.65 |       -100.61  |           0.174 |              452 |
| C_volume2_range1p5_directional   | LONG        | 2026_Nov_recent_exploratory |       52 |     21.15 |       -116.694 |           0.139 |               41 |
| C_volume2_range1p5_directional   | SHORT       | 2025_train                  |     1673 |     27.08 |       -137.804 |           0.122 |             1220 |
| C_volume2_range1p5_directional   | SHORT       | 2026_H1_validation          |      880 |     26.7  |       -104.933 |           0.198 |              645 |
| C_volume2_range1p5_directional   | SHORT       | 2026_H2_seen_recheck        |      550 |     22.73 |       -105.809 |           0.166 |              425 |
| C_volume2_range1p5_directional   | SHORT       | 2026_Nov_recent_exploratory |       62 |     30.65 |        -84.141 |           0.259 |               43 |
| D_volume2_12bar_breakout         | LONG        | 2025_train                  |     1160 |     26.72 |       -139.058 |           0.113 |              850 |
| D_volume2_12bar_breakout         | LONG        | 2026_H1_validation          |      542 |     25.46 |       -107.849 |           0.181 |              404 |
| D_volume2_12bar_breakout         | LONG        | 2026_H2_seen_recheck        |      443 |     24.38 |        -97.791 |           0.181 |              335 |
| D_volume2_12bar_breakout         | LONG        | 2026_Nov_recent_exploratory |       37 |     24.32 |       -112.312 |           0.164 |               28 |
| D_volume2_12bar_breakout         | SHORT       | 2025_train                  |     1274 |     27    |       -139.659 |           0.119 |              930 |
| D_volume2_12bar_breakout         | SHORT       | 2026_H1_validation          |      715 |     28.25 |       -101.194 |           0.215 |              513 |
| D_volume2_12bar_breakout         | SHORT       | 2026_H2_seen_recheck        |      411 |     23.84 |       -105.188 |           0.175 |              313 |
| D_volume2_12bar_breakout         | SHORT       | 2026_Nov_recent_exploratory |       55 |     27.27 |        -91.159 |           0.231 |               40 |
| E_volume2_24bar_breakout         | LONG        | 2025_train                  |     1008 |     26.79 |       -139.203 |           0.113 |              738 |
| E_volume2_24bar_breakout         | LONG        | 2026_H1_validation          |      463 |     25.27 |       -107.167 |           0.185 |              346 |
| E_volume2_24bar_breakout         | LONG        | 2026_H2_seen_recheck        |      386 |     24.61 |        -97.815 |           0.182 |              291 |
| E_volume2_24bar_breakout         | LONG        | 2026_Nov_recent_exploratory |       35 |     20    |       -126.525 |           0.121 |               28 |
| E_volume2_24bar_breakout         | SHORT       | 2025_train                  |     1110 |     26.67 |       -140.809 |           0.118 |              814 |
| E_volume2_24bar_breakout         | SHORT       | 2026_H1_validation          |      607 |     28.67 |       -100.696 |           0.223 |              433 |
| E_volume2_24bar_breakout         | SHORT       | 2026_H2_seen_recheck        |      344 |     24.13 |       -107.193 |           0.174 |              261 |
| E_volume2_24bar_breakout         | SHORT       | 2026_Nov_recent_exploratory |       48 |     27.08 |        -93.263 |           0.225 |               35 |
| F_volume2_liquidity_sweep_reject | LONG        | 2025_train                  |      523 |     29.45 |       -130.478 |           0.132 |              369 |
| F_volume2_liquidity_sweep_reject | LONG        | 2026_H1_validation          |      295 |     28.47 |        -97.195 |           0.213 |              211 |
| F_volume2_liquidity_sweep_reject | LONG        | 2026_H2_seen_recheck        |      203 |     25.12 |       -100.702 |           0.176 |              152 |
| F_volume2_liquidity_sweep_reject | LONG        | 2026_Nov_recent_exploratory |       27 |     22.22 |       -117.434 |           0.123 |               21 |
| F_volume2_liquidity_sweep_reject | SHORT       | 2025_train                  |      462 |     27.92 |       -130.946 |           0.125 |              333 |
| F_volume2_liquidity_sweep_reject | SHORT       | 2026_H1_validation          |      205 |     23.9  |       -105.184 |           0.164 |              156 |
| F_volume2_liquidity_sweep_reject | SHORT       | 2026_H2_seen_recheck        |      188 |     19.68 |       -102.614 |           0.134 |              151 |
| F_volume2_liquidity_sweep_reject | SHORT       | 2026_Nov_recent_exploratory |       14 |     35.71 |        -57.466 |           0.386 |                9 |
| G_volume3_sweep_reject           | LONG        | 2025_train                  |      241 |     29.05 |       -135.299 |           0.127 |              171 |
| G_volume3_sweep_reject           | LONG        | 2026_H1_validation          |      130 |     32.31 |        -90.977 |           0.248 |               88 |
| G_volume3_sweep_reject           | LONG        | 2026_H2_seen_recheck        |       94 |     27.66 |        -91.729 |           0.214 |               68 |
| G_volume3_sweep_reject           | LONG        | 2026_Nov_recent_exploratory |       14 |     21.43 |       -122.211 |           0.112 |               11 |
| G_volume3_sweep_reject           | SHORT       | 2025_train                  |      208 |     30.77 |       -127.333 |           0.14  |              144 |
| G_volume3_sweep_reject           | SHORT       | 2026_H1_validation          |       88 |     23.86 |       -101.092 |           0.168 |               67 |
| G_volume3_sweep_reject           | SHORT       | 2026_H2_seen_recheck        |       77 |     27.27 |        -85.007 |           0.221 |               56 |
| G_volume3_sweep_reject           | SHORT       | 2026_Nov_recent_exploratory |        9 |     44.44 |        -37.133 |           0.547 |                5 |
| H_5m_impulse_then_breakout       | LONG        | 2025_train                  |      199 |     28.14 |       -135.765 |           0.118 |              143 |
| H_5m_impulse_then_breakout       | LONG        | 2026_H1_validation          |       66 |     27.27 |       -108.924 |           0.196 |               48 |
| H_5m_impulse_then_breakout       | LONG        | 2026_H2_seen_recheck        |       68 |     26.47 |       -105.544 |           0.172 |               50 |
| H_5m_impulse_then_breakout       | LONG        | 2026_Nov_recent_exploratory |        5 |     20    |       -107.715 |           0.154 |                4 |
| H_5m_impulse_then_breakout       | SHORT       | 2025_train                  |      203 |     28.08 |       -137.215 |           0.122 |              146 |
| H_5m_impulse_then_breakout       | SHORT       | 2026_H1_validation          |       91 |     24.18 |       -117.026 |           0.17  |               69 |
| H_5m_impulse_then_breakout       | SHORT       | 2026_H2_seen_recheck        |       75 |     24    |       -100.261 |           0.199 |               57 |
| H_5m_impulse_then_breakout       | SHORT       | 2026_Nov_recent_exploratory |        9 |     22.22 |       -121.318 |           0.15  |                7 |
| I_5m_impulse_then_hold           | LONG        | 2025_train                  |      403 |     30.02 |       -129.289 |           0.134 |              282 |
| I_5m_impulse_then_hold           | LONG        | 2026_H1_validation          |      159 |     23.9  |       -112.597 |           0.175 |              121 |
| I_5m_impulse_then_hold           | LONG        | 2026_H2_seen_recheck        |      141 |     24.82 |       -102.297 |           0.183 |              106 |
| I_5m_impulse_then_hold           | LONG        | 2026_Nov_recent_exploratory |       12 |     16.67 |       -137.181 |           0.105 |               10 |
| I_5m_impulse_then_hold           | SHORT       | 2025_train                  |      431 |     29.7  |       -131.166 |           0.137 |              303 |
| I_5m_impulse_then_hold           | SHORT       | 2026_H1_validation          |      213 |     23.94 |       -113.752 |           0.175 |              162 |
| I_5m_impulse_then_hold           | SHORT       | 2026_H2_seen_recheck        |      136 |     25    |        -98.17  |           0.194 |              102 |
| I_5m_impulse_then_hold           | SHORT       | 2026_Nov_recent_exploratory |       19 |     42.11 |        -67.267 |           0.367 |               11 |
| J_absorption_then_resolution     | LONG        | 2025_train                  |      139 |     28.78 |       -137.21  |           0.127 |               99 |
| J_absorption_then_resolution     | LONG        | 2026_H1_validation          |       76 |     26.32 |       -106.009 |           0.204 |               56 |
| J_absorption_then_resolution     | LONG        | 2026_H2_seen_recheck        |       46 |     23.91 |       -102.969 |           0.135 |               35 |
| J_absorption_then_resolution     | LONG        | 2026_Nov_recent_exploratory |        6 |     16.67 |       -120.311 |           0.127 |                5 |
| J_absorption_then_resolution     | SHORT       | 2025_train                  |      149 |     28.19 |       -133.728 |           0.126 |              107 |
| J_absorption_then_resolution     | SHORT       | 2026_H1_validation          |       57 |     24.56 |       -107.946 |           0.168 |               43 |
| J_absorption_then_resolution     | SHORT       | 2026_H2_seen_recheck        |       42 |     23.81 |       -105.363 |           0.165 |               32 |
| J_absorption_then_resolution     | SHORT       | 2026_Nov_recent_exploratory |        8 |     12.5  |       -155.296 |           0.084 |                7 |
| K_compression_to_expansion       | LONG        | 2025_train                  |       58 |     18.97 |       -148.738 |           0.083 |               47 |
| K_compression_to_expansion       | LONG        | 2026_H1_validation          |       13 |     23.08 |       -125.14  |           0.094 |               10 |
| K_compression_to_expansion       | LONG        | 2026_H2_seen_recheck        |       23 |     17.39 |        -97.778 |           0.127 |               19 |
| K_compression_to_expansion       | LONG        | 2026_Nov_recent_exploratory |        5 |      0    |       -190.268 |           0     |                5 |
| K_compression_to_expansion       | SHORT       | 2025_train                  |       43 |     18.6  |       -164.973 |           0.064 |               35 |
| K_compression_to_expansion       | SHORT       | 2026_H1_validation          |       27 |     29.63 |       -107.635 |           0.159 |               19 |
| K_compression_to_expansion       | SHORT       | 2026_H2_seen_recheck        |       20 |     30    |        -89.534 |           0.268 |               14 |
| K_compression_to_expansion       | SHORT       | 2026_Nov_recent_exploratory |        3 |     33.33 |          5.169 |           1.183 |                2 |
| L_3bar_volume_acceleration       | LONG        | 2025_train                  |      656 |     23.93 |       -145.728 |           0.099 |              499 |
| L_3bar_volume_acceleration       | LONG        | 2026_H1_validation          |      230 |     24.78 |       -105.918 |           0.184 |              173 |
| L_3bar_volume_acceleration       | LONG        | 2026_H2_seen_recheck        |      216 |     25    |        -96.072 |           0.185 |              162 |
| L_3bar_volume_acceleration       | LONG        | 2026_Nov_recent_exploratory |       16 |      6.25 |       -140.631 |           0.04  |               15 |
| L_3bar_volume_acceleration       | SHORT       | 2025_train                  |      646 |     25.54 |       -139.766 |           0.114 |              481 |
| L_3bar_volume_acceleration       | SHORT       | 2026_H1_validation          |      309 |     31.39 |        -93.229 |           0.242 |              212 |
| L_3bar_volume_acceleration       | SHORT       | 2026_H2_seen_recheck        |      222 |     23.42 |       -104.931 |           0.166 |              170 |
| L_3bar_volume_acceleration       | SHORT       | 2026_Nov_recent_exploratory |       31 |     35.48 |        -67.598 |           0.352 |               20 |
| M_exhaustion_reversal            | LONG        | 2025_train                  |      180 |     30.56 |       -124.842 |           0.148 |              125 |
| M_exhaustion_reversal            | LONG        | 2026_H1_validation          |       71 |     28.17 |        -99.096 |           0.199 |               51 |
| M_exhaustion_reversal            | LONG        | 2026_H2_seen_recheck        |       49 |     28.57 |        -82.77  |           0.233 |               35 |
| M_exhaustion_reversal            | LONG        | 2026_Nov_recent_exploratory |        5 |      0    |       -198.601 |           0     |                5 |
| M_exhaustion_reversal            | SHORT       | 2025_train                  |      141 |     32.62 |       -116.439 |           0.16  |               95 |
| M_exhaustion_reversal            | SHORT       | 2026_H1_validation          |       61 |     27.87 |        -97.022 |           0.186 |               44 |
| M_exhaustion_reversal            | SHORT       | 2026_H2_seen_recheck        |       74 |     25.68 |        -95.303 |           0.207 |               55 |
| M_exhaustion_reversal            | SHORT       | 2026_Nov_recent_exploratory |        6 |     50    |        -37.343 |           0.546 |                3 |
| N_quiet_then_volume2_range2      | LONG        | 2025_train                  |       96 |     23.96 |       -142.392 |           0.092 |               73 |
| N_quiet_then_volume2_range2      | LONG        | 2026_H1_validation          |       44 |     27.27 |       -109.779 |           0.172 |               32 |
| N_quiet_then_volume2_range2      | LONG        | 2026_H2_seen_recheck        |       44 |     29.55 |        -74.88  |           0.253 |               31 |
| N_quiet_then_volume2_range2      | LONG        | 2026_Nov_recent_exploratory |        3 |      0    |       -164.961 |           0     |                3 |
| N_quiet_then_volume2_range2      | SHORT       | 2025_train                  |       85 |     21.18 |       -147.004 |           0.084 |               67 |
| N_quiet_then_volume2_range2      | SHORT       | 2026_H1_validation          |       47 |     19.15 |       -129.545 |           0.117 |               38 |
| N_quiet_then_volume2_range2      | SHORT       | 2026_H2_seen_recheck        |       26 |     23.08 |        -80.544 |           0.226 |               20 |
| N_quiet_then_volume2_range2      | SHORT       | 2026_Nov_recent_exploratory |        3 |     33.33 |        -47.908 |           0.411 |                2 |
| O_moderate_expansion_breakout    | LONG        | 2025_train                  |      739 |     24.9  |       -141.137 |           0.108 |              555 |
| O_moderate_expansion_breakout    | LONG        | 2026_H1_validation          |      280 |     24.64 |       -102.035 |           0.19  |              211 |
| O_moderate_expansion_breakout    | LONG        | 2026_H2_seen_recheck        |      224 |     26.79 |        -95.647 |           0.197 |              164 |
| O_moderate_expansion_breakout    | LONG        | 2026_Nov_recent_exploratory |       18 |     16.67 |       -119.472 |           0.121 |               15 |
| O_moderate_expansion_breakout    | SHORT       | 2025_train                  |      821 |     26.31 |       -136.048 |           0.121 |              605 |
| O_moderate_expansion_breakout    | SHORT       | 2026_H1_validation          |      352 |     27.27 |        -99.637 |           0.209 |              256 |
| O_moderate_expansion_breakout    | SHORT       | 2026_H2_seen_recheck        |      223 |     24.66 |        -99.411 |           0.18  |              168 |
| O_moderate_expansion_breakout    | SHORT       | 2026_Nov_recent_exploratory |       33 |     30.3  |        -87.958 |           0.253 |               23 |
| P_volume_absorption_unconfirmed  | LONG        | 2025_train                  |       20 |     20    |       -153.358 |           0.067 |               16 |
| P_volume_absorption_unconfirmed  | LONG        | 2026_H1_validation          |        9 |     22.22 |       -136.992 |           0.081 |                7 |
| P_volume_absorption_unconfirmed  | LONG        | 2026_H2_seen_recheck        |        8 |     12.5  |       -113.642 |           0.111 |                7 |
| P_volume_absorption_unconfirmed  | SHORT       | 2025_train                  |       29 |     17.24 |       -139.83  |           0.078 |               24 |
| P_volume_absorption_unconfirmed  | SHORT       | 2026_H1_validation          |       13 |     46.15 |        -51.052 |           0.458 |                7 |
| P_volume_absorption_unconfirmed  | SHORT       | 2026_H2_seen_recheck        |       10 |     40    |        -30.894 |           0.486 |                6 |
| Q_volume2_range2_strong_wick     | LONG        | 2025_train                  |      547 |     30.53 |       -125.928 |           0.139 |              380 |
| Q_volume2_range2_strong_wick     | LONG        | 2026_H1_validation          |      216 |     27.31 |       -109.755 |           0.189 |              157 |
| Q_volume2_range2_strong_wick     | LONG        | 2026_H2_seen_recheck        |      239 |     22.18 |       -100.354 |           0.159 |              186 |
| Q_volume2_range2_strong_wick     | LONG        | 2026_Nov_recent_exploratory |       19 |     26.32 |       -110.353 |           0.149 |               14 |
| Q_volume2_range2_strong_wick     | SHORT       | 2025_train                  |      545 |     29.36 |       -131.719 |           0.133 |              385 |
| Q_volume2_range2_strong_wick     | SHORT       | 2026_H1_validation          |      261 |     27.59 |        -99.256 |           0.209 |              189 |
| Q_volume2_range2_strong_wick     | SHORT       | 2026_H2_seen_recheck        |      199 |     17.59 |       -112.226 |           0.124 |              164 |
| Q_volume2_range2_strong_wick     | SHORT       | 2026_Nov_recent_exploratory |       20 |     35    |        -77.855 |           0.31  |               13 |

## Top historical net cells (exploratory only)
| pattern                          | direction   | period                      | model              |   trades |   win_pct |   mean_net_pts |   losses_or_flat |
|:---------------------------------|:------------|:----------------------------|:-------------------|---------:|----------:|---------------:|-----------------:|
| M_exhaustion_reversal            | SHORT       | 2026_Nov_recent_exploratory | net200_sl200_30m   |        6 |     66.67 |         60.648 |                2 |
| M_exhaustion_reversal            | SHORT       | 2026_Nov_recent_exploratory | net200_sl200_60m   |        6 |     66.67 |         50.591 |                2 |
| M_exhaustion_reversal            | SHORT       | 2026_Nov_recent_exploratory | gross200_sl200_30m |        6 |     66.67 |         44.288 |                2 |
| K_compression_to_expansion       | SHORT       | 2026_Nov_recent_exploratory | net200_sl200_30m   |        3 |     33.33 |         38.407 |                2 |
| K_compression_to_expansion       | SHORT       | 2026_Nov_recent_exploratory | net200_sl100_30m   |        3 |     33.33 |         38.407 |                2 |
| M_exhaustion_reversal            | SHORT       | 2026_Nov_recent_exploratory | gross200_sl200_60m |        6 |     66.67 |         27.779 |                2 |
| K_compression_to_expansion       | SHORT       | 2026_Nov_recent_exploratory | gross200_sl100_30m |        3 |     33.33 |          5.169 |                2 |
| K_compression_to_expansion       | SHORT       | 2026_Nov_recent_exploratory | gross200_sl200_30m |        3 |     33.33 |          5.169 |                2 |
| G_volume3_sweep_reject           | SHORT       | 2026_Nov_recent_exploratory | gross200_sl200_60m |        9 |     66.67 |          1.557 |                3 |
| F_volume2_liquidity_sweep_reject | SHORT       | 2026_Nov_recent_exploratory | gross200_sl200_60m |       14 |     64.29 |          0.604 |                5 |
| F_volume2_liquidity_sweep_reject | SHORT       | 2026_Nov_recent_exploratory | net200_sl200_60m   |       14 |     57.14 |          0.03  |                6 |
| M_exhaustion_reversal            | LONG        | 2026_Nov_recent_exploratory | net200_sl200_60m   |        5 |     40    |         -3.602 |                3 |

## Stable positive expectancy across known chronological periods
**0** of 272 candidate rule-direction-model triples achieved positive net results in 2025, Jan-Jun 2026, AND Jul-Oct 2026 with at least 60/30/30 non-overlapping trades respectively.

None found at the predeclared sample thresholds.

## Caveats
- 1m OHLC stop-first on same-bar ambiguity; tick fills unobserved
- Historical order book/spread, impact, funding, liquidation and margin not modeled
- Candle volume directional sign is a proxy, NOT real taker/order flow
- Positive cells from many variants may be random; no multiple-test adjustment
- Gross200 can be much less than 200 NET after fees
- 5m completed candles enter at immediate following 1m OPEN only
- Multiple event models overlap, do NOT sum into a portfolio
- No stop guarantees no loss; overnight gaps may exceed stops
- Always need fresh forward research before live trading

## Files
- pattern_probabilities.csv: every pattern, period, side and horizon
- strategy_results.csv: all fee, stop and horizon variants
- chronological_stability.csv: selection audit
- events.csv.gz and trade_ledger.csv.gz: full evidence in Actions artifacts
- quality.json: test assumptions
