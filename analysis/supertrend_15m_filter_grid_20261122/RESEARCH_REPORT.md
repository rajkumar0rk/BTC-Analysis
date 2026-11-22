# BTCUSD 15m bullish Supertrend line touch: volume × ATR filters

Full 210-configuration search; complete IST Jan 2025–Oct 2026.
See NOVELTY_CHECK.md and quality.json. All P&L is **price-point equivalent**,
not account $ or return; fees/GST/slippage estimated, funding excluded.
Data selection, filtering, and 1m execution strictly causal at order placement.

## Unfiltered baseline parity — PASS
|   tp_pct |   expected_trades |   found_trades |   expected_wins |   found_wins |   expected_net_pts |   found_net_pts | passes   |
|---------:|------------------:|---------------:|----------------:|-------------:|-------------------:|----------------:|:---------|
|      0.2 |               782 |            782 |             315 |          315 |           -95477.5 |        -95477.5 | True     |
|      0.4 |               782 |            782 |             220 |          220 |           -87667.5 |        -87667.5 | True     |
|      0.5 |               782 |            782 |             191 |          191 |           -86638.4 |        -86638.4 | True     |
|      0.6 |               781 |            781 |             163 |          163 |           -88524.1 |        -88524.1 | True     |
|      1   |               781 |            781 |             115 |          115 |           -88680.5 |        -88680.5 | True     |

## Top 2025-trained configurations (>=30 2025, >=60 total trades)
| volume_filter   | volatility_filter   |   tp_pct |   trades |   wins |   win_rate_pct |   net_pts |   net_avg_pts |    pf |   positive_months |   flat_months |   max_drawdown_pts |   net_avg_pts_2025 |   trades_2025 |
|:----------------|:--------------------|---------:|---------:|-------:|---------------:|----------:|--------------:|------:|------------------:|--------------:|-------------------:|-------------------:|--------------:|
| vol_ge_1p25     | atrpct_ge_0p40      |      0.2 |       73 |     45 |          61.64 |  -7395.03 |       -101.3  | 0.283 |                 5 |             7 |            7554.19 |             -87.86 |            43 |
| vol_ge_2p0      | atrpct_ge_0p30      |      1   |      100 |     23 |          23    |  -7978.11 |        -79.78 | 0.688 |                 6 |             0 |           13090.9  |             -94.11 |            60 |
| vol_ge_1p5      | atrpct_ge_0p40      |      0.2 |       64 |     40 |          62.5  |  -6486.16 |       -101.35 | 0.286 |                 4 |             7 |            6698.04 |             -96.82 |            40 |
| vol_ge_1p0      | atrrel_le_0p8       |      0.5 |      174 |     37 |          21.26 | -16802    |        -96.56 | 0.421 |                 4 |             0 |           18353.1  |            -110.69 |           103 |
| vol_ge_1p0      | atrrel_le_0p8       |      0.4 |      174 |     45 |          25.86 | -16424.9  |        -94.4  | 0.395 |                 6 |             0 |           17658.8  |            -113.84 |           103 |
| vol_ge_1p5      | atrrel_le_0p8       |      0.6 |      109 |     19 |          17.43 | -11040.8  |       -101.29 | 0.421 |                 4 |             1 |           12968.7  |            -116.21 |            65 |
| vol_ge_1p25     | atrrel_le_0p8       |      0.6 |      145 |     26 |          17.93 | -14292.7  |        -98.57 | 0.43  |                 4 |             1 |           16610.9  |            -116.66 |            89 |
| vol_ge_1p0      | atrrel_le_0p8       |      0.2 |      174 |     67 |          38.51 | -18647.7  |       -107.17 | 0.197 |                 0 |             0 |           18706.1  |            -116.99 |           103 |
| vol_ge_1p0      | atrrel_le_0p8       |      0.6 |      173 |     31 |          17.92 | -17843.8  |       -103.14 | 0.418 |                 4 |             0 |           19888.8  |            -118.03 |           103 |
| vol_ge_1p25     | atrrel_le_0p8       |      0.5 |      146 |     31 |          21.23 | -13947.8  |        -95.53 | 0.421 |                 4 |             1 |           15772    |            -118.28 |            89 |
| vol_ge_1p5      | atrpct_ge_0p30      |      1   |      146 |     29 |          19.86 | -17072.4  |       -116.93 | 0.567 |                 5 |             0 |           22159.6  |            -120.9  |            84 |
| vol_ge_1p25     | atrrel_le_0p8       |      0.2 |      146 |     57 |          39.04 | -15233.1  |       -104.34 | 0.203 |                 0 |             1 |           15291.4  |            -121.44 |            89 |
| vol_ge_1p0      | atrpct_ge_0p40      |      0.2 |       94 |     56 |          59.57 | -10347.7  |       -110.08 | 0.258 |                 5 |             5 |           10755.9  |            -121.47 |            56 |
| vol_ge_1p25     | atrrel_le_0p8       |      1   |      145 |     20 |          13.79 | -14456.7  |        -99.7  | 0.474 |                 4 |             1 |           17890.2  |            -123.29 |            89 |
| vol_ge_1p25     | atrrel_le_0p8       |      0.4 |      146 |     37 |          25.34 | -13916.8  |        -95.32 | 0.386 |                 5 |             1 |           14879.4  |            -124.19 |            89 |
| vol_ge_1p5      | atrrel_le_0p8       |      0.5 |      109 |     22 |          20.18 | -11206.8  |       -102.81 | 0.397 |                 5 |             1 |           12543.2  |            -124.81 |            65 |
| vol_off         | atrrel_le_0p8       |      0.5 |      239 |     54 |          22.59 | -23395.7  |        -97.89 | 0.432 |                 2 |             0 |           24806.5  |            -125.17 |           146 |
| vol_ge_2p0      | atrpct_ge_0p30      |      0.2 |      100 |     62 |          62    | -10459.2  |       -104.59 | 0.279 |                 4 |             0 |           11225.6  |            -125.98 |            60 |
| vol_ge_1p0      | atrrel_le_0p8       |      1   |      173 |     24 |          13.87 | -17502.3  |       -101.17 | 0.474 |                 4 |             0 |           20662.6  |            -126.71 |           103 |
| vol_ge_1p5      | atrrel_le_0p8       |      0.2 |      109 |     44 |          40.37 | -11539    |       -105.86 | 0.207 |                 2 |             1 |           11664.9  |            -127.04 |            65 |

## Most profitable entire 22-month paths (descriptive ONLY, hindsight-ranked)
| volume_filter   | volatility_filter   |   tp_pct |   trades |   wins |   win_rate_pct |   net_pts |   net_avg_pts |    pf |   positive_months |   flat_months |   max_drawdown_pts |
|:----------------|:--------------------|---------:|---------:|-------:|---------------:|----------:|--------------:|------:|------------------:|--------------:|-------------------:|
| vol_ge_2p0      | atrpct_ge_0p40      |      0.2 |       44 |     31 |          70.45 |  -3517.8  |        -79.95 | 0.366 |                 3 |             9 |            4166.25 |
| vol_le_0p8      | atrpct_ge_0p40      |      0.5 |       43 |     16 |          37.21 |  -3660.41 |        -85.13 | 0.59  |                 6 |             7 |            4988.51 |
| vol_le_0p8      | atrrel_ge_1p25      |      0.5 |       56 |     18 |          32.14 |  -4123.37 |        -73.63 | 0.584 |                 7 |             4 |            4872.87 |
| vol_ge_2p0      | atrpct_ge_0p40      |      0.6 |       44 |     16 |          36.36 |  -4242.68 |        -96.42 | 0.617 |                 4 |             9 |            6835.9  |
| vol_le_0p8      | atrpct_ge_0p40      |      0.4 |       43 |     17 |          39.53 |  -4585.43 |       -106.64 | 0.469 |                 6 |             7 |            5560.56 |
| vol_ge_2p0      | atrpct_ge_0p40      |      1   |       44 |     10 |          22.73 |  -5138.03 |       -116.77 | 0.599 |                 5 |             9 |            8748.68 |
| vol_le_0p8      | atrrel_ge_1p25      |      0.4 |       56 |     19 |          33.93 |  -5159.53 |        -92.13 | 0.465 |                 5 |             4 |            5710.18 |
| vol_le_0p8      | atrpct_ge_0p40      |      0.6 |       43 |     12 |          27.91 |  -5170.11 |       -120.24 | 0.488 |                 3 |             7 |            5409.46 |
| vol_ge_2p0      | atrpct_ge_0p40      |      0.5 |       44 |     17 |          38.64 |  -5250.24 |       -119.32 | 0.52  |                 4 |             9 |            7697.8  |
| vol_le_0p8      | atrpct_ge_0p40      |      1   |       43 |      8 |          18.6  |  -5483.73 |       -127.53 | 0.506 |                 3 |             7 |            6441.79 |
| vol_ge_2p0      | atrpct_ge_0p40      |      0.4 |       44 |     19 |          43.18 |  -5800.76 |       -131.84 | 0.439 |                 4 |             9 |            7598.33 |
| vol_le_0p8      | atrrel_ge_1p25      |      0.6 |       56 |     13 |          23.21 |  -5908.11 |       -105.5  | 0.471 |                 5 |             4 |            5919.1  |
| vol_ge_2p0      | atrrel_le_0p8       |      0.4 |       65 |     19 |          29.23 |  -6420.66 |        -98.78 | 0.403 |                 6 |             3 |            6931.36 |
| vol_le_0p8      | atrpct_ge_0p40      |      0.2 |       43 |     20 |          46.51 |  -6457.12 |       -150.17 | 0.167 |                 4 |             7 |            6726.32 |
| vol_ge_1p5      | atrpct_ge_0p40      |      0.2 |       64 |     40 |          62.5  |  -6486.16 |       -101.35 | 0.286 |                 4 |             7 |            6698.04 |
| vol_ge_2p0      | atrrel_le_0p8       |      0.6 |       65 |     12 |          18.46 |  -7328.32 |       -112.74 | 0.395 |                 5 |             3 |            8412.17 |
| vol_ge_2p0      | atrrel_le_0p8       |      0.5 |       65 |     14 |          21.54 |  -7366.9  |       -113.34 | 0.378 |                 6 |             3 |            8156.87 |
| vol_ge_1p25     | atrpct_ge_0p40      |      0.2 |       73 |     45 |          61.64 |  -7395.03 |       -101.3  | 0.283 |                 5 |             7 |            7554.19 |
| vol_le_0p8      | atrrel_ge_1p25      |      0.2 |       56 |     22 |          39.29 |  -7549.67 |       -134.82 | 0.158 |                 2 |             4 |            7702.6  |
| vol_ge_2p0      | atrrel_le_0p8       |      0.2 |       65 |     28 |          43.08 |  -7551.96 |       -116.18 | 0.193 |                 3 |             3 |            7615.69 |

## Configurations with positive total net P&L
0 / 210

## Most positive complete months
| volume_filter   | volatility_filter   |   tp_pct |   trades |   wins |   win_rate_pct |   net_pts |   net_avg_pts |    pf |   positive_months |   flat_months |   max_drawdown_pts |
|:----------------|:--------------------|---------:|---------:|-------:|---------------:|----------:|--------------:|------:|------------------:|--------------:|-------------------:|
| vol_le_0p8      | atrrel_ge_1p25      |      0.5 |       56 |     18 |          32.14 |  -4123.37 |        -73.63 | 0.584 |                 7 |             4 |            4872.87 |
| vol_le_0p8      | atrpct_ge_0p40      |      0.5 |       43 |     16 |          37.21 |  -3660.41 |        -85.13 | 0.59  |                 6 |             7 |            4988.51 |
| vol_le_0p8      | atrpct_ge_0p40      |      0.4 |       43 |     17 |          39.53 |  -4585.43 |       -106.64 | 0.469 |                 6 |             7 |            5560.56 |
| vol_ge_2p0      | atrrel_le_0p8       |      0.4 |       65 |     19 |          29.23 |  -6420.66 |        -98.78 | 0.403 |                 6 |             3 |            6931.36 |
| vol_ge_2p0      | atrrel_le_0p8       |      0.5 |       65 |     14 |          21.54 |  -7366.9  |       -113.34 | 0.378 |                 6 |             3 |            8156.87 |
| vol_ge_2p0      | atrpct_ge_0p30      |      1   |      100 |     23 |          23    |  -7978.11 |        -79.78 | 0.688 |                 6 |             0 |           13090.9  |
| vol_ge_1p0      | atrrel_le_0p8       |      0.4 |      174 |     45 |          25.86 | -16424.9  |        -94.4  | 0.395 |                 6 |             0 |           17658.8  |
| vol_ge_1p25     | atrpct_ge_0p30      |      1   |      173 |     33 |          19.08 | -22215.2  |       -128.41 | 0.529 |                 6 |             0 |           24904.9  |
| vol_ge_1p25     | atrpct_ge_0p30      |      0.6 |      173 |     48 |          27.75 | -23017.1  |       -133.05 | 0.461 |                 6 |             0 |           24768.2  |
| vol_off         | atrrel_le_0p8       |      0.6 |      238 |     46 |          19.33 | -24093.5  |       -101.23 | 0.441 |                 6 |             0 |           26157.7  |
| vol_off         | atrrel_le_0p8       |      1   |      238 |     34 |          14.29 | -24402.1  |       -102.53 | 0.473 |                 6 |             0 |           27521.6  |
| vol_off         | atrrel_ge_1p25      |      1   |      185 |     24 |          12.97 | -33913.5  |       -183.32 | 0.332 |                 6 |             0 |           34761.7  |
| vol_ge_2p0      | atrpct_ge_0p40      |      1   |       44 |     10 |          22.73 |  -5138.03 |       -116.77 | 0.599 |                 5 |             9 |            8748.68 |
| vol_le_0p8      | atrrel_ge_1p25      |      0.4 |       56 |     19 |          33.93 |  -5159.53 |        -92.13 | 0.465 |                 5 |             4 |            5710.18 |
| vol_le_0p8      | atrrel_ge_1p25      |      0.6 |       56 |     13 |          23.21 |  -5908.11 |       -105.5  | 0.471 |                 5 |             4 |            5919.1  |

## Interpretation and warnings
- A support-line touch can be a continued breakdown, not a bounce.
- This tests only last COMPLETED 15m volume and volatility, not unfinished touch-bar volume.
- Filters that reject early touches can allow a **later** touch in the same bullish cycle.
- Gross target may be profitable while net results lose to costs.
- 2025 used for screening; 2026 is research-seen, not untouched OOS.
- No confidence/uncertainty or true live-limit queue position is established.
