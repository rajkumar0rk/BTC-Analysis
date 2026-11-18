# Stage 6 — Every ETHUSD 1m candle: 200 points, clean paths and executable entries

## Dataset audit
- Real 1m candles loaded: **987,840**
- Fully eligible next-open entries: **986,704** per direction
- All long+short entry paths evaluated: **1,973,408**
- Gaps: **0** missing minutes across **0** breaks; never filled
- Predeclared directional rule names: **18**
- Strict zero-loss strategies with at least 100 trades in a period: **0** cells (not a guarantee)

## Honest definitions
- 'Clean 200' means no adverse midprice movement in ANY 1m OHLC bar before or in the TP minute.
- First 200 achieved within horizon is an ex-post label, not an entry signal.
- 200 net after standard fees requires a larger dynamic price target, computed using actual entry BTC price.
- Same-bar stop and target ambiguity is ALWAYS counted as a stop.
- One trade at a time separately for each candidate model, no forced daily trades.
- Standard scenario: 0.05% taker each side + 18% GST and 5 points adverse slippage each side.
- Scalper scenario: closing fee waived only if the modeled holding time is <=30m, conditional on eligibility.
- All historical intervals including November 2026 are exploratory; do not claim an independent holdout.

## Unconditional all-candle reference (not a portfolio)
| rule               | period                      |   horizon_min |   signals |   target_200_pct |   clean_200_zero_adverse_pct |   tp_before_stop_100_pct |   target_200_net_after_fees_pct |
|:-------------------|:----------------------------|--------------:|----------:|-----------------:|-----------------------------:|-------------------------:|--------------------------------:|
| every_minute_long  | 2025_train                  |            30 |    525181 |           50.306 |                      4.0506  |                   30.223 |                          33.417 |
| every_minute_long  | 2025_train                  |            60 |    525181 |           63.027 |                      4.1321  |                   32.763 |                          47.517 |
| every_minute_long  | 2025_train                  |           240 |    525181 |           81.276 |                      4.17228 |                   34.059 |                          71.998 |
| every_minute_long  | 2026_H1_validation          |            30 |    260401 |           31.236 |                      2.55183 |                   22.318 |                          20.001 |
| every_minute_long  | 2026_H1_validation          |            60 |    260401 |           44.479 |                      2.79415 |                   27.677 |                          31.644 |
| every_minute_long  | 2026_H1_validation          |           240 |    260401 |           69.43  |                      2.92856 |                   32.246 |                          58.698 |
| every_minute_long  | 2026_H2_seen_recheck        |            30 |    176881 |           24.462 |                      2.0918  |                   19.243 |                          14.078 |
| every_minute_long  | 2026_H2_seen_recheck        |            60 |    176881 |           37.429 |                      2.36147 |                   26.006 |                          24.809 |
| every_minute_long  | 2026_H2_seen_recheck        |           240 |    176881 |           64.975 |                      2.58027 |                   33.545 |                          53.092 |
| every_minute_long  | 2026_Nov_recent_exploratory |            30 |     24241 |           28.761 |                      2.35139 |                   20.655 |                          17.128 |
| every_minute_long  | 2026_Nov_recent_exploratory |            60 |     24241 |           41.756 |                      2.5824  |                   25.7   |                          28.419 |
| every_minute_long  | 2026_Nov_recent_exploratory |           240 |     24241 |           64.296 |                      2.68553 |                   28.856 |                          52.118 |
| every_minute_short | 2025_train                  |            30 |    525181 |           50.146 |                      4.30366 |                   30.418 |                          33.836 |
| every_minute_short | 2025_train                  |            60 |    525181 |           62.403 |                      4.38782 |                   32.927 |                          47.595 |
| every_minute_short | 2025_train                  |           240 |    525181 |           80.71  |                      4.40077 |                   33.927 |                          71.703 |
| every_minute_short | 2026_H1_validation          |            30 |    260401 |           32.821 |                      2.59408 |                   23.923 |                          21.169 |
| every_minute_short | 2026_H1_validation          |            60 |    260401 |           46.993 |                      2.83179 |                   30.039 |                          34.225 |
| every_minute_short | 2026_H1_validation          |           240 |    260401 |           71.89  |                      2.90705 |                   34.542 |                          62.128 |
| every_minute_short | 2026_H2_seen_recheck        |            30 |    176881 |           23.632 |                      2.15286 |                   18.604 |                          13.534 |
| every_minute_short | 2026_H2_seen_recheck        |            60 |    176881 |           36.195 |                      2.42706 |                   25.011 |                          24.155 |
| every_minute_short | 2026_H2_seen_recheck        |           240 |    176881 |           60.762 |                      2.59157 |                   30.749 |                          49.856 |
| every_minute_short | 2026_Nov_recent_exploratory |            30 |     24241 |           32.297 |                      2.76804 |                   24.558 |                          20.597 |
| every_minute_short | 2026_Nov_recent_exploratory |            60 |     24241 |           46.273 |                      2.99493 |                   30.811 |                          32.73  |
| every_minute_short | 2026_Nov_recent_exploratory |           240 |     24241 |           73.466 |                      3.13106 |                   36.715 |                          63.038 |

## Predeclared executable strategies at 200 gross TP / 100 stop / 30m max
| rule                         | period                      |   trades |   win_pct |   avg_net_pts |   profit_factor |   max_drawdown_pts |   worst_net_trade_pts |   losses_or_flat |
|:-----------------------------|:----------------------------|---------:|----------:|--------------:|----------------:|-------------------:|----------------------:|-----------------:|
| 15min_close_breakout_long    | 2025_train                  |      711 |     30.38 |      -123.735 |           0.168 |    87975.6         |               -273.04 |              495 |
| 15min_close_breakout_long    | 2026_H1_validation          |      274 |     31.02 |       -84.945 |           0.295 |    23411.3         |               -221.41 |              189 |
| 15min_close_breakout_long    | 2026_H2_seen_recheck        |      231 |     25.54 |       -88.284 |           0.234 |    20393.5         |               -202.7  |              172 |
| 15min_close_breakout_long    | 2026_Nov_recent_exploratory |       17 |     23.53 |       -93.181 |           0.235 |     1713.45        |               -190.58 |               13 |
| 15min_close_breakout_short   | 2025_train                  |      732 |     28.01 |      -126.971 |           0.159 |    93440.7         |               -267.94 |              527 |
| 15min_close_breakout_short   | 2026_H1_validation          |      348 |     31.03 |       -85.178 |           0.298 |    29757           |               -220.36 |              240 |
| 15min_close_breakout_short   | 2026_H2_seen_recheck        |      220 |     25.45 |       -91.865 |           0.232 |    20210.3         |               -201.25 |              164 |
| 15min_close_breakout_short   | 2026_Nov_recent_exploratory |       37 |     21.62 |      -110.724 |           0.189 |     4343.51        |               -188.21 |               29 |
| 20m_accepted_breakout_long   | 2025_train                  |     9233 |     31.7  |      -117.308 |           0.18  |        1.08311e+06 |              -7123.25 |             6306 |
| 20m_accepted_breakout_long   | 2026_H1_validation          |     3565 |     27.07 |       -89.907 |           0.242 |   320637           |               -226.25 |             2600 |
| 20m_accepted_breakout_long   | 2026_H2_seen_recheck        |     2475 |     27.03 |       -83.394 |           0.246 |   206488           |               -203.04 |             1806 |
| 20m_accepted_breakout_long   | 2026_Nov_recent_exploratory |      341 |     23.75 |       -92.785 |           0.221 |    31754.9         |               -190.64 |              260 |
| 20m_accepted_breakout_short  | 2025_train                  |     9067 |     30.03 |      -121.941 |           0.169 |        1.10565e+06 |               -276.1  |             6344 |
| 20m_accepted_breakout_short  | 2026_H1_validation          |     3975 |     29.36 |       -85.284 |           0.271 |   339006           |               -230.24 |             2808 |
| 20m_accepted_breakout_short  | 2026_H2_seen_recheck        |     2482 |     24.62 |       -92.616 |           0.212 |   229986           |               -206.55 |             1871 |
| 20m_accepted_breakout_short  | 2026_Nov_recent_exploratory |      399 |     28.82 |       -83.033 |           0.278 |    33130.2         |               -190.38 |              284 |
| 20m_rejected_sweep_long      | 2025_train                  |     6845 |     32.56 |      -110.375 |           0.195 |   755515           |               -284.65 |             4616 |
| 20m_rejected_sweep_long      | 2026_H1_validation          |     3272 |     29.34 |       -84.125 |           0.258 |   275258           |               -221.46 |             2312 |
| 20m_rejected_sweep_long      | 2026_H2_seen_recheck        |     2244 |     27.41 |       -81.897 |           0.246 |   184067           |               -201.64 |             1629 |
| 20m_rejected_sweep_long      | 2026_Nov_recent_exploratory |      260 |     28.08 |       -84.387 |           0.273 |    21940.5         |               -190.23 |              187 |
| 20m_rejected_sweep_short     | 2025_train                  |     6711 |     32.39 |      -110.113 |           0.193 |   738994           |               -273.73 |             4537 |
| 20m_rejected_sweep_short     | 2026_H1_validation          |     3117 |     29.87 |       -80.127 |           0.269 |   249755           |               -221.68 |             2186 |
| 20m_rejected_sweep_short     | 2026_H2_seen_recheck        |     2140 |     25.14 |       -88.299 |           0.205 |   188960           |               -205.93 |             1602 |
| 20m_rejected_sweep_short     | 2026_Nov_recent_exploratory |      235 |     35.32 |       -56.47  |           0.387 |    13321.3         |               -190.7  |              152 |
| 5min_close_breakout_long     | 2025_train                  |     2422 |     28.49 |      -127.417 |           0.155 |   308604           |               -273.04 |             1732 |
| 5min_close_breakout_long     | 2026_H1_validation          |      991 |     27.75 |       -90.919 |           0.244 |    90227.5         |               -222.13 |              716 |
| 5min_close_breakout_long     | 2026_H2_seen_recheck        |      809 |     26.08 |       -86.288 |           0.234 |    69806.8         |               -202.67 |              598 |
| 5min_close_breakout_long     | 2026_Nov_recent_exploratory |       89 |     19.1  |      -102.348 |           0.16  |     9221.87        |               -190.64 |               72 |
| 5min_close_breakout_short    | 2025_train                  |     2344 |     29.86 |      -121.897 |           0.172 |   285726           |               -268.5  |             1644 |
| 5min_close_breakout_short    | 2026_H1_validation          |     1197 |     30.16 |       -83.026 |           0.289 |    99510.1         |               -220.87 |              836 |
| 5min_close_breakout_short    | 2026_H2_seen_recheck        |      777 |     23.29 |       -98.474 |           0.197 |    76651.5         |               -201.64 |              596 |
| 5min_close_breakout_short    | 2026_Nov_recent_exploratory |      120 |     24.17 |       -94.015 |           0.226 |    11543.2         |               -190.09 |               91 |
| 60m_rejected_sweep_long      | 2025_train                  |     2318 |     32.27 |      -112.013 |           0.189 |   259647           |               -268.28 |             1570 |
| 60m_rejected_sweep_long      | 2026_H1_validation          |     1222 |     28.4  |       -88.914 |           0.248 |   108791           |               -221.01 |              875 |
| 60m_rejected_sweep_long      | 2026_H2_seen_recheck        |      924 |     27.06 |       -84.497 |           0.229 |    78408.4         |               -201.62 |              674 |
| 60m_rejected_sweep_long      | 2026_Nov_recent_exploratory |       93 |     24.73 |       -94.85  |           0.23  |     8952.82        |               -190.15 |               70 |
| 60m_rejected_sweep_short     | 2025_train                  |     2096 |     32.2  |      -109.658 |           0.195 |   230013           |               -273.55 |             1421 |
| 60m_rejected_sweep_short     | 2026_H1_validation          |     1140 |     28.33 |       -84.901 |           0.249 |    97063.6         |               -221.68 |              817 |
| 60m_rejected_sweep_short     | 2026_H2_seen_recheck        |      879 |     24.57 |       -89.523 |           0.202 |    78722.7         |               -205.93 |              663 |
| 60m_rejected_sweep_short     | 2026_Nov_recent_exploratory |       63 |     38.1  |       -57.828 |           0.371 |     3772.88        |               -190.7  |               39 |
| compression_break_long       | 2025_train                  |      410 |     32.44 |      -127.536 |           0.169 |    52384           |              -7123.25 |              277 |
| compression_break_long       | 2026_H1_validation          |      196 |     21.43 |      -100.702 |           0.178 |    19828.9         |               -220.84 |              154 |
| compression_break_long       | 2026_H2_seen_recheck        |      218 |     21.1  |       -88.702 |           0.168 |    19392.8         |               -203.04 |              172 |
| compression_break_long       | 2026_Nov_recent_exploratory |       25 |      0    |      -157.095 |           0     |     3927.38        |               -190.51 |               25 |
| compression_break_short      | 2025_train                  |      384 |     28.65 |      -125.786 |           0.153 |    48471.7         |               -276.1  |              274 |
| compression_break_short      | 2026_H1_validation          |      228 |     23.68 |       -93.427 |           0.199 |    21301.4         |               -221.51 |              174 |
| compression_break_short      | 2026_H2_seen_recheck        |      222 |     17.12 |      -102.418 |           0.132 |    22874.2         |               -201.7  |              184 |
| compression_break_short      | 2026_Nov_recent_exploratory |       33 |     18.18 |       -95.839 |           0.153 |     3162.69        |               -190.27 |               27 |
| every_minute_long            | 2025_train                  |   109926 |     33.26 |      -118.042 |           0.183 |        1.29759e+07 |              -7123.25 |            73367 |
| every_minute_long            | 2026_H1_validation          |    28830 |     31.34 |       -84.749 |           0.285 |        2.44342e+06 |               -334.09 |            19794 |
| every_minute_long            | 2026_H2_seen_recheck        |    14184 |     29.59 |       -84.499 |           0.262 |        1.19853e+06 |               -245.4  |             9987 |
| every_minute_long            | 2026_Nov_recent_exploratory |     2488 |     29.38 |       -82.366 |           0.289 |   205181           |               -190.78 |             1757 |
| every_minute_short           | 2025_train                  |   110040 |     33.75 |      -116.545 |           0.187 |        1.28248e+07 |              -2828.37 |            72898 |
| every_minute_short           | 2026_H1_validation          |    28606 |     31.98 |       -82.529 |           0.295 |        2.36083e+06 |              -1454.85 |            19459 |
| every_minute_short           | 2026_H2_seen_recheck        |    14177 |     29.11 |       -85.772 |           0.255 |        1.21603e+06 |               -213.3  |            10050 |
| every_minute_short           | 2026_Nov_recent_exploratory |     2427 |     33.42 |       -71.253 |           0.345 |   172932           |               -190.84 |             1616 |
| strong_burst_long            | 2025_train                  |     5771 |     31.59 |      -115.114 |           0.185 |   664321           |               -275.03 |             3948 |
| strong_burst_long            | 2026_H1_validation          |     2829 |     27.68 |       -88.276 |           0.251 |   249852           |               -226.25 |             2046 |
| strong_burst_long            | 2026_H2_seen_recheck        |     1977 |     27.67 |       -79.68  |           0.261 |   157616           |               -202.95 |             1430 |
| strong_burst_long            | 2026_Nov_recent_exploratory |      250 |     20.4  |      -104.959 |           0.176 |    26286.8         |               -190.64 |              199 |
| strong_burst_short           | 2025_train                  |     5752 |     29.99 |      -119.039 |           0.176 |   684802           |               -270.69 |             4027 |
| strong_burst_short           | 2026_H1_validation          |     3068 |     29.63 |       -84.476 |           0.271 |   259173           |               -230.24 |             2159 |
| strong_burst_short           | 2026_H2_seen_recheck        |     2017 |     25.38 |       -88.508 |           0.22  |   178936           |               -205.93 |             1505 |
| strong_burst_short           | 2026_Nov_recent_exploratory |      277 |     29.96 |       -78.236 |           0.298 |    21802.8         |               -190.4  |              194 |
| trend_pullback_reclaim_long  | 2025_train                  |     8453 |     32.06 |      -114.605 |           0.184 |   968752           |               -276.26 |             5743 |
| trend_pullback_reclaim_long  | 2026_H1_validation          |     3261 |     29.01 |       -84.749 |           0.26  |   276368           |               -222.62 |             2315 |
| trend_pullback_reclaim_long  | 2026_H2_seen_recheck        |     2333 |     26.36 |       -85.38  |           0.239 |   199211           |               -202.58 |             1718 |
| trend_pullback_reclaim_long  | 2026_Nov_recent_exploratory |      250 |     25.6  |       -86.388 |           0.242 |    21757.6         |               -190.63 |              186 |
| trend_pullback_reclaim_short | 2025_train                  |     8497 |     33.02 |      -112.277 |           0.195 |   954039           |               -299.22 |             5691 |
| trend_pullback_reclaim_short | 2026_H1_validation          |     3798 |     29.81 |       -82.49  |           0.282 |   313297           |               -223.86 |             2666 |
| trend_pullback_reclaim_short | 2026_H2_seen_recheck        |     2247 |     25.55 |       -88.334 |           0.227 |   198625           |               -208.08 |             1673 |
| trend_pullback_reclaim_short | 2026_Nov_recent_exploratory |      387 |     30.23 |       -76.923 |           0.302 |    29862           |               -190.35 |              270 |

## Rankings from 2025 training only (not evidence of future profitability)
| rule                         |   trades |   avg_net_pts |   win_pct |   losses_or_flat |
|:-----------------------------|---------:|--------------:|----------:|-----------------:|
| 60m_rejected_sweep_short     |     2096 |      -109.658 |     32.2  |             1421 |
| 20m_rejected_sweep_short     |     6711 |      -110.113 |     32.39 |             4537 |
| 20m_rejected_sweep_long      |     6845 |      -110.375 |     32.56 |             4616 |
| 60m_rejected_sweep_long      |     2318 |      -112.013 |     32.27 |             1570 |
| trend_pullback_reclaim_short |     8497 |      -112.277 |     33.02 |             5691 |
| trend_pullback_reclaim_long  |     8453 |      -114.605 |     32.06 |             5743 |
| strong_burst_long            |     5771 |      -115.114 |     31.59 |             3948 |
| every_minute_short           |   110040 |      -116.545 |     33.75 |            72898 |
| 20m_accepted_breakout_long   |     9233 |      -117.308 |     31.7  |             6306 |
| every_minute_long            |   109926 |      -118.042 |     33.26 |            73367 |
| strong_burst_short           |     5752 |      -119.039 |     29.99 |             4027 |
| 5min_close_breakout_short    |     2344 |      -121.897 |     29.86 |             1644 |
| 20m_accepted_breakout_short  |     9067 |      -121.941 |     30.03 |             6344 |
| 15min_close_breakout_long    |      711 |      -123.735 |     30.38 |              495 |
| compression_break_short      |      384 |      -125.786 |     28.65 |              274 |
| 15min_close_breakout_short   |      732 |      -126.971 |     28.01 |              527 |

## Reproducible audit artifacts
- every_candle_directional_labels.csv.gz (one entry time per long/short case)
- all_candle_conditional_rates.csv
- new_york_hour_profile.csv
- trade_ledger.csv.gz (one open trade at a time per independently measured setup)
- trade_summary.csv
- zero_loss_candidates.csv (may contain header only)
- quality.json (archive gaps, fees, exact sample counts)

## Safeguards / limitations
- No historical bid/ask quote, order-book depth or intraminute tick path
- Favorable target may be unfillable at modeled high/low
- Missing source minutes not fabricated; skip signals spanning gaps
- All four historical splits are used for exploratory research, not pristine forward testing
- Overlapping minute labels produce severely correlated observations
- Fee voucher credits are not counted as cash; historical Scalper Offer unknown
- Funding, market impact, liquidation, capital and margin not reconstructed
- No ability to guarantee a 200-point move without losses
- Only rule-based subset scanned; many possible rules not tested
- 200 BTC points represents quote-price move, not dollar account P&L

Conclusions must come from the actual table, not from choosing perfect historical candles.
