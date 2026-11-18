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
| J_absorption_then_resolution     | LONG        | 2025_train           |            30 |       109 |          59.63 |                       37.61 |                       49.54 |                 38.53 |                     24.77 |                8.257 |               2.35 |              2.22 |
| J_absorption_then_resolution     | LONG        | 2026_H1_validation   |            30 |        54 |          29.63 |                       24.07 |                       25.93 |                 16.67 |                     12.96 |                3.704 |               2.1  |              2.31 |
| J_absorption_then_resolution     | LONG        | 2026_H2_seen_recheck |            30 |        46 |          36.96 |                       15.22 |                       30.43 |                 21.74 |                      8.7  |                2.174 |               2.37 |              2.6  |
| J_absorption_then_resolution     | SHORT       | 2025_train           |            30 |       102 |          59.8  |                       36.27 |                       48.04 |                 46.08 |                     26.47 |                4.902 |               2.31 |              2.39 |
| J_absorption_then_resolution     | SHORT       | 2026_H1_validation   |            30 |        55 |          40    |                       32.73 |                       38.18 |                 32.73 |                     25.45 |                1.818 |               2.5  |              2.39 |
| J_absorption_then_resolution     | SHORT       | 2026_H2_seen_recheck |            30 |        48 |          25    |                       20.83 |                       22.92 |                 22.92 |                     18.75 |                0     |               2.55 |              2.27 |
| G_volume3_sweep_reject           | LONG        | 2025_train           |            30 |       163 |          56.44 |                       33.13 |                       46.01 |                 44.79 |                     24.54 |                5.521 |               4.12 |              3.22 |
| G_volume3_sweep_reject           | LONG        | 2026_H1_validation   |            30 |       125 |          38.4  |                       26.4  |                       32    |                 22.4  |                     15.2  |                4     |               4.68 |              3.55 |
| G_volume3_sweep_reject           | LONG        | 2026_H2_seen_recheck |            30 |        98 |          32.65 |                       21.43 |                       27.55 |                 20.41 |                     13.27 |                2.041 |               4.26 |              3.3  |
| I_5m_impulse_then_hold           | SHORT       | 2025_train           |            30 |       319 |          60.82 |                       31.03 |                       44.51 |                 48.28 |                     21.94 |                3.762 |               2.73 |              2.05 |
| I_5m_impulse_then_hold           | SHORT       | 2026_H1_validation   |            30 |       160 |          46.25 |                       26.88 |                       38.12 |                 36.88 |                     20    |                6.875 |               3.32 |              2.48 |
| I_5m_impulse_then_hold           | SHORT       | 2026_H2_seen_recheck |            30 |       103 |          32.04 |                       19.42 |                       28.16 |                 25.24 |                     15.53 |                2.913 |               3.29 |              2.62 |
| B_volume3_range2_directional     | SHORT       | 2025_train           |            30 |       458 |          65.28 |                       30.79 |                       46.07 |                 49.78 |                     20.52 |                5.677 |               4.32 |              3.52 |
| B_volume3_range2_directional     | SHORT       | 2026_H1_validation   |            30 |       320 |          48.44 |                       30    |                       40.62 |                 39.06 |                     24.38 |                4.688 |               5.43 |              4.18 |
| B_volume3_range2_directional     | SHORT       | 2026_H2_seen_recheck |            30 |       225 |          34.22 |                       22.22 |                       29.78 |                 24.44 |                     14.67 |                1.333 |               5.32 |              4.1  |
| A_volume2_range2_directional     | SHORT       | 2025_train           |            30 |       963 |          62.51 |                       30.63 |                       45.17 |                 47.35 |                     20.98 |                4.361 |               3.34 |              3.1  |
| A_volume2_range2_directional     | SHORT       | 2026_H1_validation   |            30 |       634 |          44.95 |                       29.34 |                       37.7  |                 36.28 |                     23.03 |                3.785 |               3.94 |              3.47 |
| A_volume2_range2_directional     | SHORT       | 2026_H2_seen_recheck |            30 |       396 |          34.34 |                       22.73 |                       29.55 |                 23.74 |                     15.91 |                1.263 |               4.07 |              3.51 |
| D_volume2_12bar_breakout         | SHORT       | 2025_train           |            30 |       964 |          62.24 |                       30.6  |                       44.29 |                 45.64 |                     19.81 |                4.357 |               3.35 |              2.75 |
| D_volume2_12bar_breakout         | SHORT       | 2026_H1_validation   |            30 |       640 |          46.41 |                       30    |                       39.06 |                 37.5  |                     23.59 |                3.75  |               3.94 |              3.2  |
| D_volume2_12bar_breakout         | SHORT       | 2026_H2_seen_recheck |            30 |       395 |          30.38 |                       22.03 |                       26.84 |                 21.01 |                     15.19 |                1.013 |               4.11 |              3.17 |
| I_5m_impulse_then_hold           | LONG        | 2025_train           |            30 |       281 |          61.92 |                       30.6  |                       46.98 |                 47.69 |                     20.64 |                3.559 |               3.14 |              2.49 |
| I_5m_impulse_then_hold           | LONG        | 2026_H1_validation   |            30 |       135 |          48.15 |                       31.85 |                       41.48 |                 34.81 |                     21.48 |                7.407 |               3.1  |              2.39 |
| I_5m_impulse_then_hold           | LONG        | 2026_H2_seen_recheck |            30 |       109 |          30.28 |                       19.27 |                       26.61 |                 23.85 |                     15.6  |                0.917 |               3.72 |              2.47 |
| Q_volume2_range2_strong_wick     | LONG        | 2025_train           |            30 |       374 |          60.7  |                       30.48 |                       43.58 |                 48.66 |                     23.8  |                5.615 |               3.49 |              3.23 |
| Q_volume2_range2_strong_wick     | LONG        | 2026_H1_validation   |            30 |       190 |          39.47 |                       26.32 |                       34.21 |                 30    |                     20    |                6.316 |               3.53 |              3.54 |
| Q_volume2_range2_strong_wick     | LONG        | 2026_H2_seen_recheck |            30 |       198 |          31.82 |                       17.68 |                       26.26 |                 25.25 |                     14.14 |                1.01  |               3.66 |              3.22 |
| C_volume2_range1p5_directional   | SHORT       | 2025_train           |            30 |      1350 |          60    |                       30.07 |                       43.93 |                 44    |                     20    |                4.148 |               3.14 |              2.71 |
| C_volume2_range1p5_directional   | SHORT       | 2026_H1_validation   |            30 |       812 |          43.47 |                       28.33 |                       36.58 |                 34.48 |                     21.67 |                3.202 |               3.66 |              3.1  |
| C_volume2_range1p5_directional   | SHORT       | 2026_H2_seen_recheck |            30 |       543 |          33.15 |                       23.02 |                       28.91 |                 22.47 |                     15.84 |                1.657 |               3.7  |              3.04 |
| F_volume2_liquidity_sweep_reject | LONG        | 2025_train           |            30 |       444 |          54.73 |                       29.5  |                       41.44 |                 41.44 |                     20.72 |                4.054 |               3.06 |              2.58 |
| F_volume2_liquidity_sweep_reject | LONG        | 2026_H1_validation   |            30 |       319 |          39.5  |                       27.27 |                       32.92 |                 24.14 |                     15.99 |                3.762 |               3.33 |              2.79 |
| F_volume2_liquidity_sweep_reject | LONG        | 2026_H2_seen_recheck |            30 |       204 |          27.94 |                       17.65 |                       24.02 |                 18.63 |                     11.76 |                1.471 |               3.29 |              2.76 |
| M_exhaustion_reversal            | LONG        | 2025_train           |            30 |       129 |          57.36 |                       29.46 |                       43.41 |                 39.53 |                     18.6  |                4.651 |               2.02 |              2.26 |
| M_exhaustion_reversal            | LONG        | 2026_H1_validation   |            30 |        61 |          34.43 |                       22.95 |                       29.51 |                 19.67 |                      9.84 |                0     |               2.42 |              2.8  |
| M_exhaustion_reversal            | LONG        | 2026_H2_seen_recheck |            30 |        47 |          31.91 |                       21.28 |                       29.79 |                 17.02 |                     10.64 |                2.128 |               2.09 |              2.66 |

## 200 gross target / 100 stop / 30-minute hold: selected rule outcomes
| pattern                          | direction   | period                      |   trades |   win_pct |   mean_net_pts |   profit_factor |   losses_or_flat |
|:---------------------------------|:------------|:----------------------------|---------:|----------:|---------------:|----------------:|-----------------:|
| A_volume2_range2_directional     | LONG        | 2025_train                  |      989 |     29.73 |       -122.172 |           0.173 |              695 |
| A_volume2_range2_directional     | LONG        | 2026_H1_validation          |      553 |     30.56 |        -84.85  |           0.288 |              384 |
| A_volume2_range2_directional     | LONG        | 2026_H2_seen_recheck        |      437 |     22.65 |        -99.781 |           0.199 |              338 |
| A_volume2_range2_directional     | LONG        | 2026_Nov_recent_exploratory |       49 |     26.53 |        -95.181 |           0.236 |               36 |
| A_volume2_range2_directional     | SHORT       | 2025_train                  |      960 |     30.63 |       -119.079 |           0.18  |              666 |
| A_volume2_range2_directional     | SHORT       | 2026_H1_validation          |      626 |     32.75 |        -79.412 |           0.31  |              421 |
| A_volume2_range2_directional     | SHORT       | 2026_H2_seen_recheck        |      381 |     25.46 |        -93.989 |           0.223 |              284 |
| A_volume2_range2_directional     | SHORT       | 2026_Nov_recent_exploratory |       57 |     36.84 |        -61.17  |           0.416 |               36 |
| B_volume3_range2_directional     | LONG        | 2025_train                  |      487 |     28.54 |       -129.153 |           0.155 |              348 |
| B_volume3_range2_directional     | LONG        | 2026_H1_validation          |      267 |     31.84 |        -85.468 |           0.301 |              182 |
| B_volume3_range2_directional     | LONG        | 2026_H2_seen_recheck        |      249 |     26.51 |        -90.281 |           0.249 |              183 |
| B_volume3_range2_directional     | LONG        | 2026_Nov_recent_exploratory |       31 |     29.03 |        -89.776 |           0.279 |               22 |
| B_volume3_range2_directional     | SHORT       | 2025_train                  |      456 |     30.48 |       -120.069 |           0.182 |              317 |
| B_volume3_range2_directional     | SHORT       | 2026_H1_validation          |      316 |     31.96 |        -83.424 |           0.304 |              215 |
| B_volume3_range2_directional     | SHORT       | 2026_H2_seen_recheck        |      222 |     26.13 |        -92.212 |           0.229 |              164 |
| B_volume3_range2_directional     | SHORT       | 2026_Nov_recent_exploratory |       37 |     32.43 |        -71.411 |           0.353 |               25 |
| C_volume2_range1p5_directional   | LONG        | 2025_train                  |     1339 |     30.02 |       -121.846 |           0.172 |              937 |
| C_volume2_range1p5_directional   | LONG        | 2026_H1_validation          |      675 |     29.63 |        -86.573 |           0.276 |              475 |
| C_volume2_range1p5_directional   | LONG        | 2026_H2_seen_recheck        |      541 |     22.74 |        -99.021 |           0.197 |              418 |
| C_volume2_range1p5_directional   | LONG        | 2026_Nov_recent_exploratory |       59 |     27.12 |        -92.147 |           0.25  |               43 |
| C_volume2_range1p5_directional   | SHORT       | 2025_train                  |     1337 |     30.74 |       -118.875 |           0.176 |              926 |
| C_volume2_range1p5_directional   | SHORT       | 2026_H1_validation          |      790 |     31.39 |        -82.068 |           0.296 |              542 |
| C_volume2_range1p5_directional   | SHORT       | 2026_H2_seen_recheck        |      514 |     25.68 |        -93.202 |           0.225 |              382 |
| C_volume2_range1p5_directional   | SHORT       | 2026_Nov_recent_exploratory |       76 |     34.21 |        -69.509 |           0.362 |               50 |
| D_volume2_12bar_breakout         | LONG        | 2025_train                  |      987 |     28.37 |       -128.041 |           0.157 |              707 |
| D_volume2_12bar_breakout         | LONG        | 2026_H1_validation          |      487 |     28.75 |        -90.702 |           0.262 |              347 |
| D_volume2_12bar_breakout         | LONG        | 2026_H2_seen_recheck        |      381 |     25.2  |        -91.652 |           0.234 |              285 |
| D_volume2_12bar_breakout         | LONG        | 2026_Nov_recent_exploratory |       37 |     27.03 |        -85.983 |           0.254 |               27 |
| D_volume2_12bar_breakout         | SHORT       | 2025_train                  |      954 |     30.92 |       -119.105 |           0.183 |              659 |
| D_volume2_12bar_breakout         | SHORT       | 2026_H1_validation          |      625 |     32.16 |        -81.688 |           0.308 |              424 |
| D_volume2_12bar_breakout         | SHORT       | 2026_H2_seen_recheck        |      371 |     23.72 |        -98.476 |           0.207 |              283 |
| D_volume2_12bar_breakout         | SHORT       | 2026_Nov_recent_exploratory |       64 |     31.25 |        -78.764 |           0.314 |               44 |
| E_volume2_24bar_breakout         | LONG        | 2025_train                  |      884 |     27.83 |       -129.273 |           0.153 |              638 |
| E_volume2_24bar_breakout         | LONG        | 2026_H1_validation          |      406 |     28.08 |        -92.659 |           0.257 |              292 |
| E_volume2_24bar_breakout         | LONG        | 2026_H2_seen_recheck        |      325 |     25.23 |        -92.856 |           0.231 |              243 |
| E_volume2_24bar_breakout         | LONG        | 2026_Nov_recent_exploratory |       28 |     28.57 |        -87.646 |           0.279 |               20 |
| E_volume2_24bar_breakout         | SHORT       | 2025_train                  |      830 |     29.52 |       -123.993 |           0.172 |              585 |
| E_volume2_24bar_breakout         | SHORT       | 2026_H1_validation          |      532 |     32.52 |        -81.836 |           0.313 |              359 |
| E_volume2_24bar_breakout         | SHORT       | 2026_H2_seen_recheck        |      302 |     25.17 |        -97.178 |           0.221 |              226 |
| E_volume2_24bar_breakout         | SHORT       | 2026_Nov_recent_exploratory |       53 |     32.08 |        -76.528 |           0.323 |               36 |
| F_volume2_liquidity_sweep_reject | LONG        | 2025_train                  |      444 |     30.63 |       -117.38  |           0.174 |              308 |
| F_volume2_liquidity_sweep_reject | LONG        | 2026_H1_validation          |      319 |     30.41 |        -83.857 |           0.277 |              222 |
| F_volume2_liquidity_sweep_reject | LONG        | 2026_H2_seen_recheck        |      204 |     23.04 |        -97.096 |           0.188 |              157 |
| F_volume2_liquidity_sweep_reject | LONG        | 2026_Nov_recent_exploratory |       35 |     22.86 |        -98.554 |           0.206 |               27 |
| F_volume2_liquidity_sweep_reject | SHORT       | 2025_train                  |      409 |     30.81 |       -115.993 |           0.181 |              283 |
| F_volume2_liquidity_sweep_reject | SHORT       | 2026_H1_validation          |      205 |     26.34 |        -90.751 |           0.222 |              151 |
| F_volume2_liquidity_sweep_reject | SHORT       | 2026_H2_seen_recheck        |      186 |     24.73 |        -76.046 |           0.248 |              140 |
| F_volume2_liquidity_sweep_reject | SHORT       | 2026_Nov_recent_exploratory |       12 |     25    |       -112.438 |           0.154 |                9 |
| G_volume3_sweep_reject           | LONG        | 2025_train                  |      163 |     35.58 |       -107.204 |           0.204 |              105 |
| G_volume3_sweep_reject           | LONG        | 2026_H1_validation          |      125 |     29.6  |        -89.477 |           0.26  |               88 |
| G_volume3_sweep_reject           | LONG        | 2026_H2_seen_recheck        |       98 |     29.59 |        -80.487 |           0.261 |               69 |
| G_volume3_sweep_reject           | LONG        | 2026_Nov_recent_exploratory |       16 |      6.25 |       -139.113 |           0.049 |               15 |
| G_volume3_sweep_reject           | SHORT       | 2025_train                  |      163 |     31.29 |       -109.558 |           0.2   |              112 |
| G_volume3_sweep_reject           | SHORT       | 2026_H1_validation          |       79 |     32.91 |        -73.511 |           0.295 |               53 |
| G_volume3_sweep_reject           | SHORT       | 2026_H2_seen_recheck        |       78 |     26.92 |        -69.085 |           0.277 |               57 |
| G_volume3_sweep_reject           | SHORT       | 2026_Nov_recent_exploratory |        6 |     16.67 |       -124.441 |           0.14  |                5 |
| H_5m_impulse_then_breakout       | LONG        | 2025_train                  |      112 |     27.68 |       -135.065 |           0.143 |               81 |
| H_5m_impulse_then_breakout       | LONG        | 2026_H1_validation          |       42 |     28.57 |       -100.728 |           0.235 |               30 |
| H_5m_impulse_then_breakout       | LONG        | 2026_H2_seen_recheck        |       52 |     25    |        -98.868 |           0.209 |               39 |
| H_5m_impulse_then_breakout       | LONG        | 2026_Nov_recent_exploratory |        4 |     25    |       -109.07  |           0.201 |                3 |
| H_5m_impulse_then_breakout       | SHORT       | 2025_train                  |      140 |     27.14 |       -135.627 |           0.131 |              102 |
| H_5m_impulse_then_breakout       | SHORT       | 2026_H1_validation          |       69 |     27.54 |        -97.87  |           0.244 |               50 |
| H_5m_impulse_then_breakout       | SHORT       | 2026_H2_seen_recheck        |       48 |     29.17 |        -84.757 |           0.292 |               34 |
| H_5m_impulse_then_breakout       | SHORT       | 2026_Nov_recent_exploratory |        5 |     20    |       -121.101 |           0.158 |                4 |
| I_5m_impulse_then_hold           | LONG        | 2025_train                  |      280 |     31.07 |       -122.965 |           0.168 |              193 |
| I_5m_impulse_then_hold           | LONG        | 2026_H1_validation          |      134 |     34.33 |        -75.147 |           0.336 |               88 |
| I_5m_impulse_then_hold           | LONG        | 2026_H2_seen_recheck        |      106 |     22.64 |       -104.876 |           0.174 |               82 |
| I_5m_impulse_then_hold           | LONG        | 2026_Nov_recent_exploratory |       14 |     21.43 |       -112.145 |           0.184 |               11 |
| I_5m_impulse_then_hold           | SHORT       | 2025_train                  |      318 |     32.39 |       -118.323 |           0.181 |              215 |
| I_5m_impulse_then_hold           | SHORT       | 2026_H1_validation          |      157 |     29.3  |        -90.627 |           0.266 |              111 |
| I_5m_impulse_then_hold           | SHORT       | 2026_H2_seen_recheck        |       97 |     19.59 |       -114.298 |           0.169 |               78 |
| I_5m_impulse_then_hold           | SHORT       | 2026_Nov_recent_exploratory |       14 |     28.57 |        -94.647 |           0.269 |               10 |
| J_absorption_then_resolution     | LONG        | 2025_train                  |      109 |     38.53 |        -92.368 |           0.254 |               67 |
| J_absorption_then_resolution     | LONG        | 2026_H1_validation          |       54 |     25.93 |        -97.864 |           0.219 |               40 |
| J_absorption_then_resolution     | LONG        | 2026_H2_seen_recheck        |       46 |     19.57 |       -109.388 |           0.148 |               37 |
| J_absorption_then_resolution     | LONG        | 2026_Nov_recent_exploratory |        7 |     14.29 |       -138.271 |           0.113 |                6 |
| J_absorption_then_resolution     | SHORT       | 2025_train                  |      102 |     36.27 |       -103.215 |           0.238 |               65 |
| J_absorption_then_resolution     | SHORT       | 2026_H1_validation          |       55 |     36.36 |        -65.169 |           0.375 |               35 |
| J_absorption_then_resolution     | SHORT       | 2026_H2_seen_recheck        |       48 |     20.83 |       -103.233 |           0.182 |               38 |
| J_absorption_then_resolution     | SHORT       | 2026_Nov_recent_exploratory |        4 |      0    |       -153.663 |           0     |                4 |
| K_compression_to_expansion       | LONG        | 2025_train                  |       21 |     33.33 |       -112.29  |           0.174 |               14 |
| K_compression_to_expansion       | LONG        | 2026_H1_validation          |       10 |     30    |        -61.213 |           0.387 |                7 |
| K_compression_to_expansion       | LONG        | 2026_H2_seen_recheck        |       15 |      6.67 |       -141.27  |           0.057 |               14 |
| K_compression_to_expansion       | LONG        | 2026_Nov_recent_exploratory |        1 |      0    |       -190.399 |           0     |                1 |
| K_compression_to_expansion       | SHORT       | 2025_train                  |       16 |     31.25 |       -119.438 |           0.139 |               11 |
| K_compression_to_expansion       | SHORT       | 2026_H1_validation          |       17 |     35.29 |        -69.608 |           0.373 |               11 |
| K_compression_to_expansion       | SHORT       | 2026_H2_seen_recheck        |       18 |     22.22 |        -88.199 |           0.223 |               14 |
| K_compression_to_expansion       | SHORT       | 2026_Nov_recent_exploratory |        1 |    100    |        115.902 |         nan     |                0 |
| L_3bar_volume_acceleration       | LONG        | 2025_train                  |      516 |     27.71 |       -129.824 |           0.152 |              373 |
| L_3bar_volume_acceleration       | LONG        | 2026_H1_validation          |      202 |     24.26 |        -98.252 |           0.21  |              153 |
| L_3bar_volume_acceleration       | LONG        | 2026_H2_seen_recheck        |      176 |     29.55 |        -81.71  |           0.27  |              124 |
| L_3bar_volume_acceleration       | LONG        | 2026_Nov_recent_exploratory |       24 |     16.67 |        -94.962 |           0.168 |               20 |
| L_3bar_volume_acceleration       | SHORT       | 2025_train                  |      538 |     27.14 |       -129.536 |           0.149 |              392 |
| L_3bar_volume_acceleration       | SHORT       | 2026_H1_validation          |      258 |     30.23 |        -85.042 |           0.287 |              180 |
| L_3bar_volume_acceleration       | SHORT       | 2026_H2_seen_recheck        |      179 |     25.14 |        -94.292 |           0.229 |              134 |
| L_3bar_volume_acceleration       | SHORT       | 2026_Nov_recent_exploratory |       36 |     19.44 |       -114.468 |           0.157 |               29 |
| M_exhaustion_reversal            | LONG        | 2025_train                  |      129 |     30.23 |       -122.115 |           0.179 |               90 |
| M_exhaustion_reversal            | LONG        | 2026_H1_validation          |       61 |     29.51 |        -88.297 |           0.25  |               43 |
| M_exhaustion_reversal            | LONG        | 2026_H2_seen_recheck        |       47 |     23.4  |        -95.528 |           0.199 |               36 |
| M_exhaustion_reversal            | LONG        | 2026_Nov_recent_exploratory |       10 |     40    |        -46.323 |           0.505 |                6 |
| M_exhaustion_reversal            | SHORT       | 2025_train                  |      127 |     28.35 |       -124.302 |           0.157 |               91 |
| M_exhaustion_reversal            | SHORT       | 2026_H1_validation          |       48 |     47.92 |        -35.754 |           0.563 |               25 |
| M_exhaustion_reversal            | SHORT       | 2026_H2_seen_recheck        |       67 |     28.36 |        -87.31  |           0.248 |               48 |
| M_exhaustion_reversal            | SHORT       | 2026_Nov_recent_exploratory |        2 |     50    |        -47.366 |           0.462 |                1 |
| N_quiet_then_volume2_range2      | LONG        | 2025_train                  |       63 |     19.05 |       -147.619 |           0.102 |               51 |
| N_quiet_then_volume2_range2      | LONG        | 2026_H1_validation          |       38 |     31.58 |        -84.501 |           0.302 |               26 |
| N_quiet_then_volume2_range2      | LONG        | 2026_H2_seen_recheck        |       32 |     21.88 |       -102.404 |           0.177 |               25 |
| N_quiet_then_volume2_range2      | LONG        | 2026_Nov_recent_exploratory |        2 |      0    |       -188.065 |           0     |                2 |
| N_quiet_then_volume2_range2      | SHORT       | 2025_train                  |       54 |     33.33 |       -115.122 |           0.164 |               36 |
| N_quiet_then_volume2_range2      | SHORT       | 2026_H1_validation          |       58 |     27.59 |        -88.292 |           0.245 |               42 |
| N_quiet_then_volume2_range2      | SHORT       | 2026_H2_seen_recheck        |       30 |     23.33 |        -94.542 |           0.207 |               23 |
| N_quiet_then_volume2_range2      | SHORT       | 2026_Nov_recent_exploratory |        4 |     25    |       -102.593 |           0.22  |                3 |
| O_moderate_expansion_breakout    | LONG        | 2025_train                  |      601 |     28.12 |       -126.52  |           0.154 |              432 |
| O_moderate_expansion_breakout    | LONG        | 2026_H1_validation          |      218 |     27.06 |        -89.413 |           0.241 |              159 |
| O_moderate_expansion_breakout    | LONG        | 2026_H2_seen_recheck        |      201 |     24.88 |        -88.525 |           0.207 |              151 |
| O_moderate_expansion_breakout    | LONG        | 2026_Nov_recent_exploratory |       27 |      7.41 |       -112.801 |           0.075 |               25 |
| O_moderate_expansion_breakout    | SHORT       | 2025_train                  |      666 |     27.78 |       -126.942 |           0.157 |              481 |
| O_moderate_expansion_breakout    | SHORT       | 2026_H1_validation          |      278 |     28.78 |        -86.113 |           0.272 |              198 |
| O_moderate_expansion_breakout    | SHORT       | 2026_H2_seen_recheck        |      217 |     21.2  |       -104.145 |           0.176 |              171 |
| O_moderate_expansion_breakout    | SHORT       | 2026_Nov_recent_exploratory |       29 |     24.14 |        -94.656 |           0.219 |               22 |
| P_volume_absorption_unconfirmed  | LONG        | 2025_train                  |        6 |     50    |        -89.274 |           0.272 |                3 |
| P_volume_absorption_unconfirmed  | LONG        | 2026_H1_validation          |        6 |     16.67 |       -123.78  |           0.111 |                5 |
| P_volume_absorption_unconfirmed  | LONG        | 2026_H2_seen_recheck        |        3 |     33.33 |        -95.077 |           0.272 |                2 |
| P_volume_absorption_unconfirmed  | SHORT       | 2025_train                  |       14 |     28.57 |       -105.954 |           0.186 |               10 |
| P_volume_absorption_unconfirmed  | SHORT       | 2026_H1_validation          |        5 |     40    |        -83.458 |           0.236 |                3 |
| P_volume_absorption_unconfirmed  | SHORT       | 2026_H2_seen_recheck        |       12 |     33.33 |        -80.922 |           0.165 |                8 |
| P_volume_absorption_unconfirmed  | SHORT       | 2026_Nov_recent_exploratory |        1 |      0    |       -178.545 |           0     |                1 |
| Q_volume2_range2_strong_wick     | LONG        | 2025_train                  |      374 |     31.02 |       -119.422 |           0.176 |              258 |
| Q_volume2_range2_strong_wick     | LONG        | 2026_H1_validation          |      190 |     29.47 |        -84.818 |           0.274 |              134 |
| Q_volume2_range2_strong_wick     | LONG        | 2026_H2_seen_recheck        |      195 |     23.08 |        -99.441 |           0.186 |              150 |
| Q_volume2_range2_strong_wick     | LONG        | 2026_Nov_recent_exploratory |       19 |     26.32 |        -99.075 |           0.218 |               14 |
| Q_volume2_range2_strong_wick     | SHORT       | 2025_train                  |      301 |     26.25 |       -133.022 |           0.143 |              222 |
| Q_volume2_range2_strong_wick     | SHORT       | 2026_H1_validation          |      188 |     30.32 |        -87.237 |           0.277 |              131 |
| Q_volume2_range2_strong_wick     | SHORT       | 2026_H2_seen_recheck        |      157 |     25.48 |        -87.133 |           0.248 |              117 |
| Q_volume2_range2_strong_wick     | SHORT       | 2026_Nov_recent_exploratory |       21 |     47.62 |        -20.338 |           0.738 |               11 |

## Top historical net cells (exploratory only)
| pattern                          | direction   | period                      | model              |   trades |   win_pct |   mean_net_pts |   losses_or_flat |
|:---------------------------------|:------------|:----------------------------|:-------------------|---------:|----------:|---------------:|-----------------:|
| K_compression_to_expansion       | SHORT       | 2026_Nov_recent_exploratory | net200_sl100_60m   |        1 |    100    |        200     |                0 |
| K_compression_to_expansion       | SHORT       | 2026_Nov_recent_exploratory | net200_sl200_30m   |        1 |    100    |        200     |                0 |
| K_compression_to_expansion       | SHORT       | 2026_Nov_recent_exploratory | net200_sl200_60m   |        1 |    100    |        200     |                0 |
| K_compression_to_expansion       | SHORT       | 2026_Nov_recent_exploratory | net200_sl100_30m   |        1 |    100    |        200     |                0 |
| K_compression_to_expansion       | SHORT       | 2026_Nov_recent_exploratory | gross200_sl100_30m |        1 |    100    |        115.902 |                0 |
| K_compression_to_expansion       | SHORT       | 2026_Nov_recent_exploratory | gross200_sl200_30m |        1 |    100    |        115.902 |                0 |
| K_compression_to_expansion       | SHORT       | 2026_Nov_recent_exploratory | gross200_sl100_60m |        1 |    100    |        115.902 |                0 |
| K_compression_to_expansion       | SHORT       | 2026_Nov_recent_exploratory | gross200_sl200_60m |        1 |    100    |        115.902 |                0 |
| N_quiet_then_volume2_range2      | SHORT       | 2026_Nov_recent_exploratory | net200_sl200_60m   |        4 |     75    |         49.39  |                1 |
| P_volume_absorption_unconfirmed  | LONG        | 2025_train                  | net200_sl200_30m   |        6 |     50    |         28.805 |                3 |
| G_volume3_sweep_reject           | SHORT       | 2026_Nov_recent_exploratory | gross200_sl200_60m |        6 |     66.67 |         27.44  |                2 |
| F_volume2_liquidity_sweep_reject | SHORT       | 2026_Nov_recent_exploratory | gross200_sl200_60m |       12 |     66.67 |         27.364 |                4 |

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
