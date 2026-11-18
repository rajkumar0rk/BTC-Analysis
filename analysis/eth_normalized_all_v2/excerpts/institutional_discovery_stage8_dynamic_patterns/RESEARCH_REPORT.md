# Stage 8 — Anytime ETHUSD directional participation patterns

## Test definition
- Use genuine Delta India ETHUSD 1m OHLCV resampled into complete 5m bars.
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
| I_5m_impulse_then_hold           | SHORT       | 2025_train           |            30 |       318 |          60.69 |                       30.82 |                       44.34 |                 48.11 |                     22.01 |                3.774 |               2.72 |              2.04 |
| I_5m_impulse_then_hold           | SHORT       | 2026_H1_validation   |            30 |       158 |          45.57 |                       25.95 |                       37.34 |                 36.08 |                     18.99 |                6.962 |               3.32 |              2.49 |
| I_5m_impulse_then_hold           | SHORT       | 2026_H2_seen_recheck |            30 |       103 |          33.01 |                       19.42 |                       28.16 |                 26.21 |                     15.53 |                2.913 |               3.38 |              2.67 |
| B_volume3_range2_directional     | SHORT       | 2025_train           |            30 |       456 |          65.13 |                       30.7  |                       45.83 |                 49.56 |                     20.39 |                5.702 |               4.33 |              3.52 |
| B_volume3_range2_directional     | SHORT       | 2026_H1_validation   |            30 |       321 |          48.29 |                       29.91 |                       40.5  |                 38.94 |                     24.3  |                4.673 |               5.42 |              4.18 |
| B_volume3_range2_directional     | SHORT       | 2026_H2_seen_recheck |            30 |       226 |          34.51 |                       22.57 |                       30.09 |                 24.78 |                     15.04 |                1.327 |               5.32 |              4.09 |
| D_volume2_12bar_breakout         | SHORT       | 2025_train           |            30 |       961 |          62.33 |                       30.59 |                       44.33 |                 45.68 |                     19.77 |                4.37  |               3.35 |              2.75 |
| D_volume2_12bar_breakout         | SHORT       | 2026_H1_validation   |            30 |       641 |          46.33 |                       29.95 |                       39    |                 37.44 |                     23.56 |                3.744 |               3.94 |              3.2  |
| D_volume2_12bar_breakout         | SHORT       | 2026_H2_seen_recheck |            30 |       398 |          30.4  |                       22.11 |                       26.88 |                 21.11 |                     15.33 |                1.005 |               4.11 |              3.16 |
| A_volume2_range2_directional     | SHORT       | 2025_train           |            30 |       963 |          62.51 |                       30.53 |                       44.96 |                 47.25 |                     20.87 |                4.361 |               3.34 |              3.1  |
| A_volume2_range2_directional     | SHORT       | 2026_H1_validation   |            30 |       632 |          44.94 |                       29.27 |                       37.66 |                 36.23 |                     22.94 |                3.797 |               3.95 |              3.47 |
| A_volume2_range2_directional     | SHORT       | 2026_H2_seen_recheck |            30 |       395 |          34.43 |                       22.78 |                       29.62 |                 24.05 |                     16.2  |                1.266 |               4.08 |              3.51 |
| I_5m_impulse_then_hold           | LONG        | 2025_train           |            30 |       283 |          61.48 |                       30.39 |                       46.64 |                 47.35 |                     20.49 |                3.534 |               3.13 |              2.48 |
| I_5m_impulse_then_hold           | LONG        | 2026_H1_validation   |            30 |       134 |          48.51 |                       32.09 |                       41.79 |                 35.07 |                     21.64 |                7.463 |               3.11 |              2.4  |
| I_5m_impulse_then_hold           | LONG        | 2026_H2_seen_recheck |            30 |       109 |          30.28 |                       19.27 |                       26.61 |                 23.85 |                     15.6  |                0.917 |               3.72 |              2.47 |
| Q_volume2_range2_strong_wick     | LONG        | 2025_train           |            30 |       372 |          60.75 |                       30.38 |                       43.55 |                 48.66 |                     23.66 |                5.376 |               3.5  |              3.23 |
| Q_volume2_range2_strong_wick     | LONG        | 2026_H1_validation   |            30 |       191 |          39.79 |                       26.18 |                       34.03 |                 29.84 |                     19.9  |                6.283 |               3.53 |              3.53 |
| Q_volume2_range2_strong_wick     | LONG        | 2026_H2_seen_recheck |            30 |       196 |          32.14 |                       17.86 |                       26.53 |                 25.51 |                     14.29 |                1.02  |               3.67 |              3.24 |
| C_volume2_range1p5_directional   | SHORT       | 2025_train           |            30 |      1348 |          60.01 |                       30.04 |                       43.92 |                 43.99 |                     19.96 |                4.154 |               3.14 |              2.71 |
| C_volume2_range1p5_directional   | SHORT       | 2026_H1_validation   |            30 |       813 |          43.42 |                       28.29 |                       36.53 |                 34.44 |                     21.65 |                3.198 |               3.66 |              3.09 |
| C_volume2_range1p5_directional   | SHORT       | 2026_H2_seen_recheck |            30 |       545 |          33.21 |                       23.12 |                       28.99 |                 22.57 |                     15.96 |                1.651 |               3.69 |              3.04 |
| F_volume2_liquidity_sweep_reject | LONG        | 2025_train           |            30 |       444 |          54.95 |                       29.5  |                       41.67 |                 41.44 |                     20.72 |                4.054 |               3.06 |              2.58 |
| F_volume2_liquidity_sweep_reject | LONG        | 2026_H1_validation   |            30 |       319 |          39.5  |                       27.27 |                       32.92 |                 24.14 |                     15.99 |                3.762 |               3.33 |              2.79 |
| F_volume2_liquidity_sweep_reject | LONG        | 2026_H2_seen_recheck |            30 |       203 |          28.08 |                       17.73 |                       24.14 |                 18.72 |                     11.82 |                1.478 |               3.29 |              2.76 |
| M_exhaustion_reversal            | LONG        | 2025_train           |            30 |       129 |          57.36 |                       29.46 |                       43.41 |                 39.53 |                     18.6  |                4.651 |               2.02 |              2.26 |
| M_exhaustion_reversal            | LONG        | 2026_H1_validation   |            30 |        61 |          34.43 |                       22.95 |                       29.51 |                 19.67 |                      9.84 |                0     |               2.42 |              2.8  |
| M_exhaustion_reversal            | LONG        | 2026_H2_seen_recheck |            30 |        48 |          31.25 |                       20.83 |                       29.17 |                 16.67 |                     10.42 |                2.083 |               2.08 |              2.64 |

## 200 gross target / 100 stop / 30-minute hold: selected rule outcomes
| pattern                          | direction   | period               |   trades |   win_pct |   mean_net_pts |   profit_factor |   losses_or_flat |
|:---------------------------------|:------------|:---------------------|---------:|----------:|---------------:|----------------:|-----------------:|
| A_volume2_range2_directional     | LONG        | 2025_train           |      988 |     29.66 |       -122.173 |           0.172 |              695 |
| A_volume2_range2_directional     | LONG        | 2026_H1_validation   |      555 |     30.45 |        -85.242 |           0.286 |              386 |
| A_volume2_range2_directional     | LONG        | 2026_H2_seen_recheck |      431 |     22.97 |        -99.551 |           0.202 |              332 |
| A_volume2_range2_directional     | SHORT       | 2025_train           |      960 |     30.52 |       -119.699 |           0.179 |              667 |
| A_volume2_range2_directional     | SHORT       | 2026_H1_validation   |      623 |     32.58 |        -79.724 |           0.309 |              420 |
| A_volume2_range2_directional     | SHORT       | 2026_H2_seen_recheck |      380 |     25.26 |        -94.506 |           0.221 |              284 |
| B_volume3_range2_directional     | LONG        | 2025_train           |      486 |     28.4  |       -129.606 |           0.153 |              348 |
| B_volume3_range2_directional     | LONG        | 2026_H1_validation   |      267 |     31.84 |        -85.468 |           0.301 |              182 |
| B_volume3_range2_directional     | LONG        | 2026_H2_seen_recheck |      245 |     26.94 |        -89.849 |           0.253 |              179 |
| B_volume3_range2_directional     | SHORT       | 2025_train           |      454 |     30.4  |       -120.312 |           0.181 |              316 |
| B_volume3_range2_directional     | SHORT       | 2026_H1_validation   |      317 |     31.86 |        -83.732 |           0.303 |              216 |
| B_volume3_range2_directional     | SHORT       | 2026_H2_seen_recheck |      222 |     25.68 |        -93.192 |           0.226 |              165 |
| C_volume2_range1p5_directional   | LONG        | 2025_train           |     1340 |     30.07 |       -121.529 |           0.172 |              937 |
| C_volume2_range1p5_directional   | LONG        | 2026_H1_validation   |      676 |     29.59 |        -86.743 |           0.275 |              476 |
| C_volume2_range1p5_directional   | LONG        | 2026_H2_seen_recheck |      539 |     22.82 |        -98.96  |           0.198 |              416 |
| C_volume2_range1p5_directional   | SHORT       | 2025_train           |     1335 |     30.71 |       -119.127 |           0.176 |              925 |
| C_volume2_range1p5_directional   | SHORT       | 2026_H1_validation   |      791 |     31.35 |        -82.2   |           0.296 |              543 |
| C_volume2_range1p5_directional   | SHORT       | 2026_H2_seen_recheck |      516 |     25.58 |        -93.545 |           0.224 |              384 |
| D_volume2_12bar_breakout         | LONG        | 2025_train           |      986 |     28.4  |       -127.924 |           0.157 |              706 |
| D_volume2_12bar_breakout         | LONG        | 2026_H1_validation   |      488 |     28.69 |        -90.929 |           0.261 |              348 |
| D_volume2_12bar_breakout         | LONG        | 2026_H2_seen_recheck |      380 |     25.26 |        -91.441 |           0.235 |              284 |
| D_volume2_12bar_breakout         | SHORT       | 2025_train           |      951 |     30.91 |       -119.406 |           0.183 |              657 |
| D_volume2_12bar_breakout         | SHORT       | 2026_H1_validation   |      626 |     32.11 |        -81.855 |           0.307 |              425 |
| D_volume2_12bar_breakout         | SHORT       | 2026_H2_seen_recheck |      373 |     23.59 |        -98.923 |           0.206 |              285 |
| E_volume2_24bar_breakout         | LONG        | 2025_train           |      883 |     27.86 |       -129.144 |           0.154 |              637 |
| E_volume2_24bar_breakout         | LONG        | 2026_H1_validation   |      407 |     28.01 |        -92.926 |           0.256 |              293 |
| E_volume2_24bar_breakout         | LONG        | 2026_H2_seen_recheck |      324 |     25.31 |        -92.613 |           0.232 |              242 |
| E_volume2_24bar_breakout         | SHORT       | 2025_train           |      827 |     29.5  |       -124.358 |           0.171 |              583 |
| E_volume2_24bar_breakout         | SHORT       | 2026_H1_validation   |      533 |     32.46 |        -82.033 |           0.312 |              360 |
| E_volume2_24bar_breakout         | SHORT       | 2026_H2_seen_recheck |      304 |     25    |        -97.734 |           0.219 |              228 |
| F_volume2_liquidity_sweep_reject | LONG        | 2025_train           |      444 |     30.63 |       -117.239 |           0.174 |              308 |
| F_volume2_liquidity_sweep_reject | LONG        | 2026_H1_validation   |      319 |     30.72 |        -83.496 |           0.278 |              221 |
| F_volume2_liquidity_sweep_reject | LONG        | 2026_H2_seen_recheck |      203 |     23.15 |        -96.881 |           0.189 |              156 |
| F_volume2_liquidity_sweep_reject | SHORT       | 2025_train           |      408 |     30.64 |       -116.504 |           0.18  |              283 |
| F_volume2_liquidity_sweep_reject | SHORT       | 2026_H1_validation   |      205 |     26.34 |        -90.751 |           0.222 |              151 |
| F_volume2_liquidity_sweep_reject | SHORT       | 2026_H2_seen_recheck |      186 |     24.73 |        -76.046 |           0.248 |              140 |
| G_volume3_sweep_reject           | LONG        | 2025_train           |      163 |     35.58 |       -107.204 |           0.204 |              105 |
| G_volume3_sweep_reject           | LONG        | 2026_H1_validation   |      125 |     29.6  |        -89.477 |           0.26  |               88 |
| G_volume3_sweep_reject           | LONG        | 2026_H2_seen_recheck |       98 |     29.59 |        -80.487 |           0.261 |               69 |
| G_volume3_sweep_reject           | SHORT       | 2025_train           |      163 |     31.29 |       -109.558 |           0.2   |              112 |
| G_volume3_sweep_reject           | SHORT       | 2026_H1_validation   |       79 |     32.91 |        -73.511 |           0.295 |               53 |
| G_volume3_sweep_reject           | SHORT       | 2026_H2_seen_recheck |       78 |     26.92 |        -69.085 |           0.277 |               57 |
| H_5m_impulse_then_breakout       | LONG        | 2025_train           |      113 |     27.43 |       -135.676 |           0.141 |               82 |
| H_5m_impulse_then_breakout       | LONG        | 2026_H1_validation   |       43 |     30.23 |        -95.76  |           0.256 |               30 |
| H_5m_impulse_then_breakout       | LONG        | 2026_H2_seen_recheck |       52 |     25    |        -98.868 |           0.209 |               39 |
| H_5m_impulse_then_breakout       | SHORT       | 2025_train           |      139 |     26.62 |       -137.353 |           0.126 |              102 |
| H_5m_impulse_then_breakout       | SHORT       | 2026_H1_validation   |       69 |     27.54 |        -97.87  |           0.244 |               50 |
| H_5m_impulse_then_breakout       | SHORT       | 2026_H2_seen_recheck |       49 |     28.57 |        -87.021 |           0.282 |               35 |
| I_5m_impulse_then_hold           | LONG        | 2025_train           |      282 |     30.85 |       -123.417 |           0.166 |              195 |
| I_5m_impulse_then_hold           | LONG        | 2026_H1_validation   |      133 |     34.59 |        -74.369 |           0.34  |               87 |
| I_5m_impulse_then_hold           | LONG        | 2026_H2_seen_recheck |      106 |     22.64 |       -104.876 |           0.174 |               82 |
| I_5m_impulse_then_hold           | SHORT       | 2025_train           |      317 |     32.18 |       -119.051 |           0.179 |              215 |
| I_5m_impulse_then_hold           | SHORT       | 2026_H1_validation   |      155 |     28.39 |        -93.115 |           0.255 |              111 |
| I_5m_impulse_then_hold           | SHORT       | 2026_H2_seen_recheck |       97 |     19.59 |       -115.442 |           0.168 |               78 |
| J_absorption_then_resolution     | LONG        | 2025_train           |      109 |     38.53 |        -92.368 |           0.254 |               67 |
| J_absorption_then_resolution     | LONG        | 2026_H1_validation   |       54 |     25.93 |        -97.864 |           0.219 |               40 |
| J_absorption_then_resolution     | LONG        | 2026_H2_seen_recheck |       46 |     19.57 |       -109.388 |           0.148 |               37 |
| J_absorption_then_resolution     | SHORT       | 2025_train           |      102 |     36.27 |       -103.215 |           0.238 |               65 |
| J_absorption_then_resolution     | SHORT       | 2026_H1_validation   |       55 |     36.36 |        -65.169 |           0.375 |               35 |
| J_absorption_then_resolution     | SHORT       | 2026_H2_seen_recheck |       48 |     20.83 |       -103.233 |           0.182 |               38 |
| K_compression_to_expansion       | LONG        | 2025_train           |       21 |     33.33 |       -112.29  |           0.174 |               14 |
| K_compression_to_expansion       | LONG        | 2026_H1_validation   |       10 |     30    |        -61.213 |           0.387 |                7 |
| K_compression_to_expansion       | LONG        | 2026_H2_seen_recheck |       15 |      6.67 |       -141.27  |           0.057 |               14 |
| K_compression_to_expansion       | SHORT       | 2025_train           |       16 |     31.25 |       -119.438 |           0.139 |               11 |
| K_compression_to_expansion       | SHORT       | 2026_H1_validation   |       17 |     35.29 |        -69.608 |           0.373 |               11 |
| K_compression_to_expansion       | SHORT       | 2026_H2_seen_recheck |       18 |     22.22 |        -88.199 |           0.223 |               14 |
| L_3bar_volume_acceleration       | LONG        | 2025_train           |      515 |     27.77 |       -129.604 |           0.153 |              372 |
| L_3bar_volume_acceleration       | LONG        | 2026_H1_validation   |      203 |     24.14 |        -98.661 |           0.209 |              154 |
| L_3bar_volume_acceleration       | LONG        | 2026_H2_seen_recheck |      174 |     29.89 |        -80.672 |           0.275 |              122 |
| L_3bar_volume_acceleration       | SHORT       | 2025_train           |      540 |     27.04 |       -130.043 |           0.148 |              394 |
| L_3bar_volume_acceleration       | SHORT       | 2026_H1_validation   |      258 |     30.23 |        -85.042 |           0.287 |              180 |
| L_3bar_volume_acceleration       | SHORT       | 2026_H2_seen_recheck |      179 |     25.14 |        -94.292 |           0.229 |              134 |
| M_exhaustion_reversal            | LONG        | 2025_train           |      129 |     30.23 |       -122.115 |           0.179 |               90 |
| M_exhaustion_reversal            | LONG        | 2026_H1_validation   |       61 |     29.51 |        -88.297 |           0.25  |               43 |
| M_exhaustion_reversal            | LONG        | 2026_H2_seen_recheck |       48 |     22.92 |        -97.585 |           0.192 |               37 |
| M_exhaustion_reversal            | SHORT       | 2025_train           |      128 |     28.12 |       -123.528 |           0.157 |               92 |
| M_exhaustion_reversal            | SHORT       | 2026_H1_validation   |       48 |     47.92 |        -35.754 |           0.563 |               25 |
| M_exhaustion_reversal            | SHORT       | 2026_H2_seen_recheck |       66 |     28.79 |        -85.709 |           0.254 |               47 |
| N_quiet_then_volume2_range2      | LONG        | 2025_train           |       63 |     19.05 |       -147.619 |           0.102 |               51 |
| N_quiet_then_volume2_range2      | LONG        | 2026_H1_validation   |       38 |     31.58 |        -84.501 |           0.302 |               26 |
| N_quiet_then_volume2_range2      | LONG        | 2026_H2_seen_recheck |       32 |     21.88 |       -102.404 |           0.177 |               25 |
| N_quiet_then_volume2_range2      | SHORT       | 2025_train           |       54 |     33.33 |       -115.122 |           0.164 |               36 |
| N_quiet_then_volume2_range2      | SHORT       | 2026_H1_validation   |       58 |     25.86 |        -93.713 |           0.22  |               43 |
| N_quiet_then_volume2_range2      | SHORT       | 2026_H2_seen_recheck |       30 |     23.33 |        -94.542 |           0.207 |               23 |
| O_moderate_expansion_breakout    | LONG        | 2025_train           |      597 |     27.81 |       -127.411 |           0.153 |              431 |
| O_moderate_expansion_breakout    | LONG        | 2026_H1_validation   |      218 |     27.06 |        -89.449 |           0.241 |              159 |
| O_moderate_expansion_breakout    | LONG        | 2026_H2_seen_recheck |      200 |     24.5  |        -89.191 |           0.205 |              151 |
| O_moderate_expansion_breakout    | SHORT       | 2025_train           |      665 |     27.82 |       -126.759 |           0.157 |              480 |
| O_moderate_expansion_breakout    | SHORT       | 2026_H1_validation   |      280 |     28.93 |        -85.699 |           0.274 |              199 |
| O_moderate_expansion_breakout    | SHORT       | 2026_H2_seen_recheck |      221 |     21.27 |       -104.055 |           0.176 |              174 |
| P_volume_absorption_unconfirmed  | LONG        | 2025_train           |        6 |     50    |        -89.274 |           0.272 |                3 |
| P_volume_absorption_unconfirmed  | LONG        | 2026_H1_validation   |        6 |     16.67 |       -123.78  |           0.111 |                5 |
| P_volume_absorption_unconfirmed  | LONG        | 2026_H2_seen_recheck |        3 |     33.33 |        -95.077 |           0.272 |                2 |
| P_volume_absorption_unconfirmed  | SHORT       | 2025_train           |       14 |     28.57 |       -105.954 |           0.186 |               10 |
| P_volume_absorption_unconfirmed  | SHORT       | 2026_H1_validation   |        5 |     40    |        -83.458 |           0.236 |                3 |
| P_volume_absorption_unconfirmed  | SHORT       | 2026_H2_seen_recheck |       12 |     33.33 |        -80.922 |           0.165 |                8 |
| Q_volume2_range2_strong_wick     | LONG        | 2025_train           |      372 |     30.91 |       -119.587 |           0.175 |              257 |
| Q_volume2_range2_strong_wick     | LONG        | 2026_H1_validation   |      191 |     29.32 |        -85.343 |           0.271 |              135 |
| Q_volume2_range2_strong_wick     | LONG        | 2026_H2_seen_recheck |      193 |     23.32 |        -99.843 |           0.187 |              148 |
| Q_volume2_range2_strong_wick     | SHORT       | 2025_train           |      301 |     26.25 |       -132.982 |           0.143 |              222 |
| Q_volume2_range2_strong_wick     | SHORT       | 2026_H1_validation   |      186 |     29.57 |        -88.923 |           0.27  |              131 |
| Q_volume2_range2_strong_wick     | SHORT       | 2026_H2_seen_recheck |      157 |     25.48 |        -87.133 |           0.248 |              117 |

## Top historical net cells (exploratory only)
| pattern                         | direction   | period               | model              |   trades |   win_pct |   mean_net_pts |   losses_or_flat |
|:--------------------------------|:------------|:---------------------|:-------------------|---------:|----------:|---------------:|-----------------:|
| P_volume_absorption_unconfirmed | LONG        | 2025_train           | net200_sl200_30m   |        6 |     50    |         28.805 |                3 |
| M_exhaustion_reversal           | SHORT       | 2026_H1_validation   | net200_sl200_60m   |       48 |     64.58 |         27.039 |               17 |
| M_exhaustion_reversal           | SHORT       | 2026_H1_validation   | net200_sl200_30m   |       48 |     60.42 |         12.538 |               19 |
| P_volume_absorption_unconfirmed | LONG        | 2025_train           | gross200_sl200_30m |        6 |     66.67 |          6.853 |                2 |
| P_volume_absorption_unconfirmed | LONG        | 2025_train           | gross200_sl200_60m |        6 |     83.33 |         -5.989 |                1 |
| M_exhaustion_reversal           | SHORT       | 2026_H1_validation   | gross200_sl200_60m |       48 |     66.67 |         -7.467 |               16 |
| M_exhaustion_reversal           | SHORT       | 2026_H1_validation   | net200_sl100_60m   |       48 |     47.92 |        -10.407 |               25 |
| M_exhaustion_reversal           | SHORT       | 2026_H1_validation   | gross200_sl200_30m |       48 |     60.42 |        -14.013 |               19 |
| M_exhaustion_reversal           | SHORT       | 2026_H1_validation   | net200_sl100_30m   |       48 |     47.92 |        -19.038 |               25 |
| P_volume_absorption_unconfirmed | LONG        | 2025_train           | net200_sl200_60m   |        6 |     50    |        -20.519 |                3 |
| P_volume_absorption_unconfirmed | LONG        | 2026_H2_seen_recheck | gross200_sl200_60m |        3 |     66.67 |        -28.449 |                1 |
| M_exhaustion_reversal           | SHORT       | 2026_H1_validation   | gross200_sl100_60m |       48 |     50    |        -33.3   |               24 |

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
