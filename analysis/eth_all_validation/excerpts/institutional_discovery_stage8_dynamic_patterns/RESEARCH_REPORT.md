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
| pattern                        | direction   | period               |   horizon_min |   signals |   gross200_pct |   gross200_before_sl100_pct |   gross200_before_sl200_pct |   net200_possible_pct |   net200_before_sl100_pct |   clean_gross200_pct |   avg_volume_ratio |   avg_range_ratio |
|:-------------------------------|:------------|:---------------------|--------------:|----------:|---------------:|----------------------------:|----------------------------:|----------------------:|--------------------------:|---------------------:|-------------------:|------------------:|
| B_volume3_range2_directional   | LONG        | 2025_train           |            30 |       488 |           0.2  |                        0.2  |                        0.2  |                  0.2  |                      0.2  |                    0 |               4.77 |              3.95 |
| B_volume3_range2_directional   | LONG        | 2026_H1_validation   |            30 |       269 |           0    |                        0    |                        0    |                  0    |                      0    |                    0 |               4.94 |              4.21 |
| B_volume3_range2_directional   | LONG        | 2026_H2_seen_recheck |            30 |       256 |           0    |                        0    |                        0    |                  0    |                      0    |                    0 |               5.18 |              3.84 |
| E_volume2_24bar_breakout       | SHORT       | 2025_train           |            30 |       837 |           0.12 |                        0.12 |                        0.12 |                  0.12 |                      0.12 |                    0 |               3.43 |              2.82 |
| E_volume2_24bar_breakout       | SHORT       | 2026_H1_validation   |            30 |       543 |           0    |                        0    |                        0    |                  0    |                      0    |                    0 |               4.15 |              3.32 |
| E_volume2_24bar_breakout       | SHORT       | 2026_H2_seen_recheck |            30 |       326 |           0    |                        0    |                        0    |                  0    |                      0    |                    0 |               4.37 |              3.25 |
| E_volume2_24bar_breakout       | LONG        | 2025_train           |            30 |       888 |           0.11 |                        0.11 |                        0.11 |                  0.11 |                      0.11 |                    0 |               3.71 |              3.13 |
| E_volume2_24bar_breakout       | LONG        | 2026_H1_validation   |            30 |       416 |           0    |                        0    |                        0    |                  0    |                      0    |                    0 |               3.99 |              3.46 |
| E_volume2_24bar_breakout       | LONG        | 2026_H2_seen_recheck |            30 |       348 |           0    |                        0    |                        0    |                  0    |                      0    |                    0 |               4.41 |              3.29 |
| A_volume2_range2_directional   | LONG        | 2025_train           |            30 |       998 |           0.1  |                        0.1  |                        0.1  |                  0.1  |                      0.1  |                    0 |               3.59 |              3.35 |
| A_volume2_range2_directional   | LONG        | 2026_H1_validation   |            30 |       557 |           0    |                        0    |                        0    |                  0    |                      0    |                    0 |               3.64 |              3.53 |
| A_volume2_range2_directional   | LONG        | 2026_H2_seen_recheck |            30 |       454 |           0    |                        0    |                        0    |                  0    |                      0    |                    0 |               3.99 |              3.38 |
| D_volume2_12bar_breakout       | LONG        | 2025_train           |            30 |       992 |           0.1  |                        0.1  |                        0.1  |                  0.1  |                      0.1  |                    0 |               3.6  |              3.06 |
| D_volume2_12bar_breakout       | LONG        | 2026_H1_validation   |            30 |       499 |           0    |                        0    |                        0    |                  0    |                      0    |                    0 |               3.76 |              3.31 |
| D_volume2_12bar_breakout       | LONG        | 2026_H2_seen_recheck |            30 |       406 |           0    |                        0    |                        0    |                  0    |                      0    |                    0 |               4.16 |              3.18 |
| A_volume2_range2_directional   | SHORT       | 2025_train           |            30 |       963 |           0.1  |                        0.1  |                        0.1  |                  0.1  |                      0.1  |                    0 |               3.34 |              3.1  |
| A_volume2_range2_directional   | SHORT       | 2026_H1_validation   |            30 |       636 |           0    |                        0    |                        0    |                  0    |                      0    |                    0 |               3.94 |              3.46 |
| A_volume2_range2_directional   | SHORT       | 2026_H2_seen_recheck |            30 |       399 |           0    |                        0    |                        0    |                  0    |                      0    |                    0 |               4.07 |              3.5  |
| D_volume2_12bar_breakout       | SHORT       | 2025_train           |            30 |       962 |           0.1  |                        0.1  |                        0.1  |                  0.1  |                      0.1  |                    0 |               3.35 |              2.75 |
| D_volume2_12bar_breakout       | SHORT       | 2026_H1_validation   |            30 |       639 |           0    |                        0    |                        0    |                  0    |                      0    |                    0 |               3.94 |              3.2  |
| D_volume2_12bar_breakout       | SHORT       | 2026_H2_seen_recheck |            30 |       397 |           0    |                        0    |                        0    |                  0    |                      0    |                    0 |               4.11 |              3.16 |
| C_volume2_range1p5_directional | SHORT       | 2025_train           |            30 |      1348 |           0.07 |                        0.07 |                        0.07 |                  0.07 |                      0.07 |                    0 |               3.13 |              2.71 |
| C_volume2_range1p5_directional | SHORT       | 2026_H1_validation   |            30 |       811 |           0    |                        0    |                        0    |                  0    |                      0    |                    0 |               3.66 |              3.1  |
| C_volume2_range1p5_directional | SHORT       | 2026_H2_seen_recheck |            30 |       545 |           0    |                        0    |                        0    |                  0    |                      0    |                    0 |               3.7  |              3.04 |
| C_volume2_range1p5_directional | LONG        | 2025_train           |            30 |      1348 |           0.07 |                        0.07 |                        0.07 |                  0.07 |                      0.07 |                    0 |               3.32 |              2.93 |
| C_volume2_range1p5_directional | LONG        | 2026_H1_validation   |            30 |       690 |           0    |                        0    |                        0    |                  0    |                      0    |                    0 |               3.46 |              3.19 |
| C_volume2_range1p5_directional | LONG        | 2026_H2_seen_recheck |            30 |       571 |           0    |                        0    |                        0    |                  0    |                      0    |                    0 |               3.72 |              3.04 |
| O_moderate_expansion_breakout  | SHORT       | 2025_train           |            30 |       677 |           0    |                        0    |                        0    |                  0    |                      0    |                    0 |               2.05 |              1.6  |
| O_moderate_expansion_breakout  | SHORT       | 2026_H1_validation   |            30 |       295 |           0    |                        0    |                        0    |                  0    |                      0    |                    0 |               2.02 |              1.61 |
| O_moderate_expansion_breakout  | SHORT       | 2026_H2_seen_recheck |            30 |       225 |           0    |                        0    |                        0    |                  0    |                      0    |                    0 |               2.07 |              1.6  |
| O_moderate_expansion_breakout  | LONG        | 2025_train           |            30 |       604 |           0    |                        0    |                        0    |                  0    |                      0    |                    0 |               2.04 |              1.59 |
| O_moderate_expansion_breakout  | LONG        | 2026_H1_validation   |            30 |       228 |           0    |                        0    |                        0    |                  0    |                      0    |                    0 |               2.02 |              1.6  |
| O_moderate_expansion_breakout  | LONG        | 2026_H2_seen_recheck |            30 |       209 |           0    |                        0    |                        0    |                  0    |                      0    |                    0 |               2.08 |              1.58 |
| L_3bar_volume_acceleration     | SHORT       | 2025_train           |            30 |       542 |           0    |                        0    |                        0    |                  0    |                      0    |                    0 |               2.77 |              2.1  |
| L_3bar_volume_acceleration     | SHORT       | 2026_H1_validation   |            30 |       265 |           0    |                        0    |                        0    |                  0    |                      0    |                    0 |               3.37 |              2.45 |
| L_3bar_volume_acceleration     | SHORT       | 2026_H2_seen_recheck |            30 |       189 |           0    |                        0    |                        0    |                  0    |                      0    |                    0 |               3.46 |              2.39 |

## 200 gross target / 100 stop / 30-minute hold: selected rule outcomes
| pattern                          | direction   | period                      |   trades |   win_pct |   mean_net_pts |   profit_factor |   losses_or_flat |
|:---------------------------------|:------------|:----------------------------|---------:|----------:|---------------:|----------------:|-----------------:|
| A_volume2_range2_directional     | LONG        | 2025_train                  |      866 |     17.21 |        -13.638 |           0.199 |              717 |
| A_volume2_range2_directional     | LONG        | 2026_H1_validation          |      483 |      9.94 |        -12.835 |           0.1   |              435 |
| A_volume2_range2_directional     | LONG        | 2026_H2_seen_recheck        |      391 |      5.37 |        -13.401 |           0.063 |              370 |
| A_volume2_range2_directional     | LONG        | 2026_Nov_recent_exploratory |       45 |      6.67 |        -12.634 |           0.172 |               42 |
| A_volume2_range2_directional     | SHORT       | 2025_train                  |      826 |     18.77 |        -12.543 |           0.233 |              671 |
| A_volume2_range2_directional     | SHORT       | 2026_H1_validation          |      545 |     12.84 |        -12.493 |           0.128 |              475 |
| A_volume2_range2_directional     | SHORT       | 2026_H2_seen_recheck        |      353 |      7.08 |        -13.407 |           0.055 |              328 |
| A_volume2_range2_directional     | SHORT       | 2026_Nov_recent_exploratory |       50 |     10    |        -10.829 |           0.225 |               45 |
| B_volume3_range2_directional     | LONG        | 2025_train                  |      428 |     19.16 |        -13.218 |           0.25  |              346 |
| B_volume3_range2_directional     | LONG        | 2026_H1_validation          |      235 |     13.62 |        -12.015 |           0.142 |              203 |
| B_volume3_range2_directional     | LONG        | 2026_H2_seen_recheck        |      223 |      7.17 |        -12.818 |           0.082 |              207 |
| B_volume3_range2_directional     | LONG        | 2026_Nov_recent_exploratory |       28 |     10.71 |         -9.439 |           0.309 |               25 |
| B_volume3_range2_directional     | SHORT       | 2025_train                  |      409 |     20.05 |        -12.593 |           0.26  |              327 |
| B_volume3_range2_directional     | SHORT       | 2026_H1_validation          |      283 |     12.72 |        -13.064 |           0.111 |              247 |
| B_volume3_range2_directional     | SHORT       | 2026_H2_seen_recheck        |      204 |      8.33 |        -12.976 |           0.072 |              187 |
| B_volume3_range2_directional     | SHORT       | 2026_Nov_recent_exploratory |       32 |     15.62 |         -8.608 |           0.364 |               27 |
| C_volume2_range1p5_directional   | LONG        | 2025_train                  |     1157 |     15.99 |        -13.925 |           0.171 |              972 |
| C_volume2_range1p5_directional   | LONG        | 2026_H1_validation          |      588 |      9.01 |        -12.921 |           0.086 |              535 |
| C_volume2_range1p5_directional   | LONG        | 2026_H2_seen_recheck        |      486 |      4.73 |        -13.517 |           0.056 |              463 |
| C_volume2_range1p5_directional   | LONG        | 2026_Nov_recent_exploratory |       54 |      7.41 |        -12.835 |           0.147 |               50 |
| C_volume2_range1p5_directional   | SHORT       | 2025_train                  |     1141 |     16.21 |        -13.013 |           0.188 |              956 |
| C_volume2_range1p5_directional   | SHORT       | 2026_H1_validation          |      675 |     11.41 |        -12.565 |           0.112 |              598 |
| C_volume2_range1p5_directional   | SHORT       | 2026_H2_seen_recheck        |      469 |      5.54 |        -13.558 |           0.046 |              443 |
| C_volume2_range1p5_directional   | SHORT       | 2026_Nov_recent_exploratory |       68 |      7.35 |        -11.866 |           0.163 |               63 |
| D_volume2_12bar_breakout         | LONG        | 2025_train                  |      843 |     15.54 |        -13.985 |           0.186 |              712 |
| D_volume2_12bar_breakout         | LONG        | 2026_H1_validation          |      426 |      9.86 |        -12.993 |           0.092 |              384 |
| D_volume2_12bar_breakout         | LONG        | 2026_H2_seen_recheck        |      338 |      5.62 |        -13.383 |           0.073 |              319 |
| D_volume2_12bar_breakout         | LONG        | 2026_Nov_recent_exploratory |       34 |      8.82 |        -10.706 |           0.245 |               31 |
| D_volume2_12bar_breakout         | SHORT       | 2025_train                  |      806 |     16.63 |        -13.103 |           0.207 |              672 |
| D_volume2_12bar_breakout         | SHORT       | 2026_H1_validation          |      530 |     12.45 |        -12.569 |           0.119 |              464 |
| D_volume2_12bar_breakout         | SHORT       | 2026_H2_seen_recheck        |      342 |      6.14 |        -14.074 |           0.049 |              321 |
| D_volume2_12bar_breakout         | SHORT       | 2026_Nov_recent_exploratory |       56 |      7.14 |        -10.759 |           0.202 |               52 |
| E_volume2_24bar_breakout         | LONG        | 2025_train                  |      758 |     15.83 |        -14.241 |           0.191 |              638 |
| E_volume2_24bar_breakout         | LONG        | 2026_H1_validation          |      351 |     10.26 |        -12.996 |           0.101 |              315 |
| E_volume2_24bar_breakout         | LONG        | 2026_H2_seen_recheck        |      290 |      5.52 |        -13.756 |           0.076 |              274 |
| E_volume2_24bar_breakout         | LONG        | 2026_Nov_recent_exploratory |       25 |      8    |        -11.059 |           0.24  |               23 |
| E_volume2_24bar_breakout         | SHORT       | 2025_train                  |      693 |     17.17 |        -12.761 |           0.229 |              574 |
| E_volume2_24bar_breakout         | SHORT       | 2026_H1_validation          |      446 |     13.9  |        -12.651 |           0.119 |              384 |
| E_volume2_24bar_breakout         | SHORT       | 2026_H2_seen_recheck        |      278 |      7.55 |        -14.006 |           0.054 |              257 |
| E_volume2_24bar_breakout         | SHORT       | 2026_Nov_recent_exploratory |       46 |      8.7  |         -9.676 |           0.255 |               42 |
| F_volume2_liquidity_sweep_reject | LONG        | 2025_train                  |      430 |     16.74 |        -14.722 |           0.149 |              358 |
| F_volume2_liquidity_sweep_reject | LONG        | 2026_H1_validation          |      304 |      7.24 |        -13.248 |           0.056 |              282 |
| F_volume2_liquidity_sweep_reject | LONG        | 2026_H2_seen_recheck        |      201 |      6.97 |        -12.88  |           0.032 |              187 |
| F_volume2_liquidity_sweep_reject | LONG        | 2026_Nov_recent_exploratory |       35 |      2.86 |        -16.267 |           0.01  |               34 |
| F_volume2_liquidity_sweep_reject | SHORT       | 2025_train                  |      393 |     12.72 |        -13.427 |           0.087 |              343 |
| F_volume2_liquidity_sweep_reject | SHORT       | 2026_H1_validation          |      198 |      5.56 |        -13.006 |           0.041 |              187 |
| F_volume2_liquidity_sweep_reject | SHORT       | 2026_H2_seen_recheck        |      178 |      5.62 |        -12.74  |           0.032 |              168 |
| F_volume2_liquidity_sweep_reject | SHORT       | 2026_Nov_recent_exploratory |       11 |      0    |        -12.889 |           0     |               11 |
| G_volume3_sweep_reject           | LONG        | 2025_train                  |      162 |     19.75 |        -14.155 |           0.158 |              130 |
| G_volume3_sweep_reject           | LONG        | 2026_H1_validation          |      121 |      4.96 |        -15.627 |           0.041 |              115 |
| G_volume3_sweep_reject           | LONG        | 2026_H2_seen_recheck        |       98 |      7.14 |        -12.061 |           0.036 |               91 |
| G_volume3_sweep_reject           | LONG        | 2026_Nov_recent_exploratory |       16 |      0    |        -18.37  |           0     |               16 |
| G_volume3_sweep_reject           | SHORT       | 2025_train                  |      160 |     12.5  |        -12.689 |           0.119 |              140 |
| G_volume3_sweep_reject           | SHORT       | 2026_H1_validation          |       77 |      7.79 |        -12.036 |           0.06  |               71 |
| G_volume3_sweep_reject           | SHORT       | 2026_H2_seen_recheck        |       75 |      6.67 |        -13.386 |           0.014 |               70 |
| G_volume3_sweep_reject           | SHORT       | 2026_Nov_recent_exploratory |        6 |      0    |        -14.076 |           0     |                6 |
| H_5m_impulse_then_breakout       | LONG        | 2025_train                  |      103 |     20.39 |        -12.926 |           0.268 |               82 |
| H_5m_impulse_then_breakout       | LONG        | 2026_H1_validation          |       40 |     15    |        -10.875 |           0.181 |               34 |
| H_5m_impulse_then_breakout       | LONG        | 2026_H2_seen_recheck        |       49 |     12.24 |        -11.709 |           0.179 |               43 |
| H_5m_impulse_then_breakout       | LONG        | 2026_Nov_recent_exploratory |        4 |     25    |          2.211 |           1.282 |                3 |
| H_5m_impulse_then_breakout       | SHORT       | 2025_train                  |      131 |     18.32 |        -15.338 |           0.205 |              107 |
| H_5m_impulse_then_breakout       | SHORT       | 2026_H1_validation          |       65 |     15.38 |        -13.291 |           0.114 |               55 |
| H_5m_impulse_then_breakout       | SHORT       | 2026_H2_seen_recheck        |       46 |     10.87 |        -11.329 |           0.135 |               41 |
| H_5m_impulse_then_breakout       | SHORT       | 2026_Nov_recent_exploratory |        4 |      0    |        -16.614 |           0     |                4 |
| I_5m_impulse_then_hold           | LONG        | 2025_train                  |      258 |     17.05 |        -13.697 |           0.185 |              214 |
| I_5m_impulse_then_hold           | LONG        | 2026_H1_validation          |      124 |      8.06 |        -11.372 |           0.096 |              114 |
| I_5m_impulse_then_hold           | LONG        | 2026_H2_seen_recheck        |      100 |      8    |        -13.467 |           0.087 |               92 |
| I_5m_impulse_then_hold           | LONG        | 2026_Nov_recent_exploratory |       14 |     14.29 |         -7.835 |           0.367 |               12 |
| I_5m_impulse_then_hold           | SHORT       | 2025_train                  |      290 |     17.24 |        -13.718 |           0.212 |              240 |
| I_5m_impulse_then_hold           | SHORT       | 2026_H1_validation          |      146 |     13.01 |        -13.069 |           0.142 |              127 |
| I_5m_impulse_then_hold           | SHORT       | 2026_H2_seen_recheck        |       95 |      8.42 |        -12.854 |           0.071 |               87 |
| I_5m_impulse_then_hold           | SHORT       | 2026_Nov_recent_exploratory |       13 |      7.69 |        -10.118 |           0.328 |               12 |
| J_absorption_then_resolution     | LONG        | 2025_train                  |      108 |     11.11 |        -15.692 |           0.077 |               96 |
| J_absorption_then_resolution     | LONG        | 2026_H1_validation          |       54 |      5.56 |        -15.543 |           0.013 |               51 |
| J_absorption_then_resolution     | LONG        | 2026_H2_seen_recheck        |       46 |      6.52 |        -11.454 |           0.082 |               43 |
| J_absorption_then_resolution     | LONG        | 2026_Nov_recent_exploratory |        7 |      0    |        -15.743 |           0     |                7 |
| J_absorption_then_resolution     | SHORT       | 2025_train                  |      102 |     12.75 |        -13.707 |           0.188 |               89 |
| J_absorption_then_resolution     | SHORT       | 2026_H1_validation          |       55 |      9.09 |        -14.072 |           0.072 |               50 |
| J_absorption_then_resolution     | SHORT       | 2026_H2_seen_recheck        |       47 |      8.51 |        -12.627 |           0.056 |               43 |
| J_absorption_then_resolution     | SHORT       | 2026_Nov_recent_exploratory |        4 |      0    |        -12.785 |           0     |                4 |
| K_compression_to_expansion       | LONG        | 2025_train                  |       21 |     19.05 |        -13.172 |           0.178 |               17 |
| K_compression_to_expansion       | LONG        | 2026_H1_validation          |       10 |     20    |        -10.571 |           0.035 |                8 |
| K_compression_to_expansion       | LONG        | 2026_H2_seen_recheck        |       15 |      0    |        -14.432 |           0     |               15 |
| K_compression_to_expansion       | LONG        | 2026_Nov_recent_exploratory |        1 |      0    |        -17.767 |           0     |                1 |
| K_compression_to_expansion       | SHORT       | 2025_train                  |       16 |      0    |        -17.915 |           0     |               16 |
| K_compression_to_expansion       | SHORT       | 2026_H1_validation          |       17 |      0    |        -12.02  |           0     |               17 |
| K_compression_to_expansion       | SHORT       | 2026_H2_seen_recheck        |       18 |      0    |        -15.381 |           0     |               18 |
| K_compression_to_expansion       | SHORT       | 2026_Nov_recent_exploratory |        1 |      0    |        -15.249 |           0     |                1 |
| L_3bar_volume_acceleration       | LONG        | 2025_train                  |      481 |     14.14 |        -15.178 |           0.119 |              413 |
| L_3bar_volume_acceleration       | LONG        | 2026_H1_validation          |      200 |     10    |        -12.308 |           0.108 |              180 |
| L_3bar_volume_acceleration       | LONG        | 2026_H2_seen_recheck        |      168 |      7.14 |        -11.81  |           0.089 |              156 |
| L_3bar_volume_acceleration       | LONG        | 2026_Nov_recent_exploratory |       23 |      4.35 |        -15.928 |           0.077 |               22 |
| L_3bar_volume_acceleration       | SHORT       | 2025_train                  |      509 |     14.73 |        -15.298 |           0.136 |              434 |
| L_3bar_volume_acceleration       | SHORT       | 2026_H1_validation          |      246 |     10.57 |        -13.353 |           0.107 |              220 |
| L_3bar_volume_acceleration       | SHORT       | 2026_H2_seen_recheck        |      173 |      8.09 |        -13.179 |           0.066 |              159 |
| L_3bar_volume_acceleration       | SHORT       | 2026_Nov_recent_exploratory |       35 |     11.43 |        -11.221 |           0.089 |               31 |
| M_exhaustion_reversal            | LONG        | 2025_train                  |      129 |     19.38 |        -13.653 |           0.142 |              104 |
| M_exhaustion_reversal            | LONG        | 2026_H1_validation          |       58 |      8.62 |        -14.601 |           0.051 |               53 |
| M_exhaustion_reversal            | LONG        | 2026_H2_seen_recheck        |       47 |      6.38 |        -14.314 |           0.028 |               44 |
| M_exhaustion_reversal            | LONG        | 2026_Nov_recent_exploratory |       10 |     10    |         -9.027 |           0.352 |                9 |
| M_exhaustion_reversal            | SHORT       | 2025_train                  |      125 |     12    |        -14.45  |           0.086 |              110 |
| M_exhaustion_reversal            | SHORT       | 2026_H1_validation          |       48 |     12.5  |         -9.205 |           0.058 |               42 |
| M_exhaustion_reversal            | SHORT       | 2026_H2_seen_recheck        |       63 |      6.35 |        -11.028 |           0.066 |               59 |
| M_exhaustion_reversal            | SHORT       | 2026_Nov_recent_exploratory |        2 |      0    |        -10.499 |           0     |                2 |
| N_quiet_then_volume2_range2      | LONG        | 2025_train                  |       63 |     19.05 |        -11.182 |           0.284 |               51 |
| N_quiet_then_volume2_range2      | LONG        | 2026_H1_validation          |       38 |     15.79 |        -13.297 |           0.028 |               32 |
| N_quiet_then_volume2_range2      | LONG        | 2026_H2_seen_recheck        |       32 |      0    |        -13.728 |           0     |               32 |
| N_quiet_then_volume2_range2      | LONG        | 2026_Nov_recent_exploratory |        2 |      0    |        -18.733 |           0     |                2 |
| N_quiet_then_volume2_range2      | SHORT       | 2025_train                  |       54 |     14.81 |        -10.331 |           0.324 |               46 |
| N_quiet_then_volume2_range2      | SHORT       | 2026_H1_validation          |       58 |      6.9  |        -12.985 |           0.018 |               54 |
| N_quiet_then_volume2_range2      | SHORT       | 2026_H2_seen_recheck        |       29 |     10.34 |        -13.375 |           0.071 |               26 |
| N_quiet_then_volume2_range2      | SHORT       | 2026_Nov_recent_exploratory |        4 |      0    |        -14.012 |           0     |                4 |
| O_moderate_expansion_breakout    | LONG        | 2025_train                  |      550 |     10.91 |        -15.115 |           0.078 |              490 |
| O_moderate_expansion_breakout    | LONG        | 2026_H1_validation          |      217 |      6.91 |        -13.329 |           0.054 |              202 |
| O_moderate_expansion_breakout    | LONG        | 2026_H2_seen_recheck        |      196 |      4.08 |        -13.496 |           0.035 |              188 |
| O_moderate_expansion_breakout    | LONG        | 2026_Nov_recent_exploratory |       27 |      0    |        -16.229 |           0     |               27 |
| O_moderate_expansion_breakout    | SHORT       | 2025_train                  |      613 |     14.68 |        -13.982 |           0.136 |              523 |
| O_moderate_expansion_breakout    | SHORT       | 2026_H1_validation          |      273 |     10.26 |        -12.962 |           0.081 |              245 |
| O_moderate_expansion_breakout    | SHORT       | 2026_H2_seen_recheck        |      210 |      2.38 |        -13.66  |           0.016 |              205 |
| O_moderate_expansion_breakout    | SHORT       | 2026_Nov_recent_exploratory |       27 |      7.41 |        -11.922 |           0.061 |               25 |
| P_volume_absorption_unconfirmed  | LONG        | 2025_train                  |        6 |     33.33 |         -6.823 |           0.123 |                4 |
| P_volume_absorption_unconfirmed  | LONG        | 2026_H1_validation          |        6 |      0    |        -15.618 |           0     |                6 |
| P_volume_absorption_unconfirmed  | LONG        | 2026_H2_seen_recheck        |        3 |      0    |        -18.665 |           0     |                3 |
| P_volume_absorption_unconfirmed  | SHORT       | 2025_train                  |       14 |      0    |        -12.961 |           0     |               14 |
| P_volume_absorption_unconfirmed  | SHORT       | 2026_H1_validation          |        5 |      0    |        -15.338 |           0     |                5 |
| P_volume_absorption_unconfirmed  | SHORT       | 2026_H2_seen_recheck        |       12 |      0    |        -12.247 |           0     |               12 |
| P_volume_absorption_unconfirmed  | SHORT       | 2026_Nov_recent_exploratory |        1 |      0    |        -13.343 |           0     |                1 |
| Q_volume2_range2_strong_wick     | LONG        | 2025_train                  |      354 |     22.6  |        -12.359 |           0.251 |              274 |
| Q_volume2_range2_strong_wick     | LONG        | 2026_H1_validation          |      182 |     12.64 |        -12.097 |           0.16  |              159 |
| Q_volume2_range2_strong_wick     | LONG        | 2026_H2_seen_recheck        |      188 |      5.85 |        -12.196 |           0.079 |              177 |
| Q_volume2_range2_strong_wick     | LONG        | 2026_Nov_recent_exploratory |       18 |     11.11 |        -13.742 |           0.079 |               16 |
| Q_volume2_range2_strong_wick     | SHORT       | 2025_train                  |      287 |     18.82 |        -12.812 |           0.196 |              233 |
| Q_volume2_range2_strong_wick     | SHORT       | 2026_H1_validation          |      181 |     13.81 |        -12.296 |           0.143 |              156 |
| Q_volume2_range2_strong_wick     | SHORT       | 2026_H2_seen_recheck        |      150 |      8    |        -12.818 |           0.063 |              138 |
| Q_volume2_range2_strong_wick     | SHORT       | 2026_Nov_recent_exploratory |       21 |      9.52 |         -9.78  |           0.266 |               19 |

## Top historical net cells (exploratory only)
| pattern                         | direction   | period                      | model              |   trades |   win_pct |   mean_net_pts |   losses_or_flat |
|:--------------------------------|:------------|:----------------------------|:-------------------|---------:|----------:|---------------:|-----------------:|
| N_quiet_then_volume2_range2     | SHORT       | 2026_Nov_recent_exploratory | gross200_sl100_60m |        4 |     25    |          8.465 |                3 |
| N_quiet_then_volume2_range2     | SHORT       | 2026_Nov_recent_exploratory | gross200_sl200_60m |        4 |     25    |          8.465 |                3 |
| N_quiet_then_volume2_range2     | SHORT       | 2026_Nov_recent_exploratory | net200_sl100_60m   |        4 |     25    |          8.465 |                3 |
| N_quiet_then_volume2_range2     | SHORT       | 2026_Nov_recent_exploratory | net200_sl200_60m   |        4 |     25    |          8.465 |                3 |
| H_5m_impulse_then_breakout      | LONG        | 2026_Nov_recent_exploratory | gross200_sl200_30m |        4 |     25    |          2.211 |                3 |
| H_5m_impulse_then_breakout      | LONG        | 2026_Nov_recent_exploratory | gross200_sl100_30m |        4 |     25    |          2.211 |                3 |
| H_5m_impulse_then_breakout      | LONG        | 2026_Nov_recent_exploratory | net200_sl100_30m   |        4 |     25    |          2.211 |                3 |
| H_5m_impulse_then_breakout      | LONG        | 2026_Nov_recent_exploratory | net200_sl200_30m   |        4 |     25    |          2.211 |                3 |
| P_volume_absorption_unconfirmed | SHORT       | 2025_train                  | net200_sl200_60m   |       14 |     14.29 |          2.121 |               12 |
| P_volume_absorption_unconfirmed | SHORT       | 2025_train                  | net200_sl100_60m   |       14 |     14.29 |          2.121 |               12 |
| P_volume_absorption_unconfirmed | SHORT       | 2025_train                  | gross200_sl200_60m |       14 |     14.29 |          1.054 |               12 |
| P_volume_absorption_unconfirmed | SHORT       | 2025_train                  | gross200_sl100_60m |       14 |     14.29 |          1.054 |               12 |

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
