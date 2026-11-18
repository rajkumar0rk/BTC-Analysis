# Stage 6 — Every BTCUSD 1m candle: 200 points, clean paths and executable entries

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
| 15min_close_breakout_long    | 2026_H1_validation          |      275 |     30.91 |       -85.297 |           0.294 |    23593.1         |               -221.41 |              190 |
| 15min_close_breakout_long    | 2026_H2_seen_recheck        |      232 |     25.43 |       -88.172 |           0.233 |    20455.9         |               -202.7  |              173 |
| 15min_close_breakout_long    | 2026_Nov_recent_exploratory |       17 |     23.53 |       -93.181 |           0.235 |     1713.45        |               -190.58 |               13 |
| 15min_close_breakout_short   | 2025_train                  |      732 |     28.14 |      -126.674 |           0.16  |    93222.9         |               -267.94 |              526 |
| 15min_close_breakout_short   | 2026_H1_validation          |      349 |     30.95 |       -85.14  |           0.298 |    29829           |               -220.36 |              241 |
| 15min_close_breakout_short   | 2026_H2_seen_recheck        |      220 |     25.45 |       -91.865 |           0.232 |    20210.3         |               -201.25 |              164 |
| 15min_close_breakout_short   | 2026_Nov_recent_exploratory |       37 |     21.62 |      -110.724 |           0.189 |     4343.51        |               -188.21 |               29 |
| 20m_accepted_breakout_long   | 2025_train                  |     9234 |     31.71 |      -117.345 |           0.18  |        1.08356e+06 |              -7123.25 |             6306 |
| 20m_accepted_breakout_long   | 2026_H1_validation          |     3566 |     27.12 |       -89.795 |           0.242 |   320328           |               -226.25 |             2599 |
| 20m_accepted_breakout_long   | 2026_H2_seen_recheck        |     2476 |     27.02 |       -83.411 |           0.246 |   206526           |               -203.04 |             1807 |
| 20m_accepted_breakout_long   | 2026_Nov_recent_exploratory |      341 |     23.75 |       -92.67  |           0.221 |    31715.8         |               -190.64 |              260 |
| 20m_accepted_breakout_short  | 2025_train                  |     9068 |     30.02 |      -121.984 |           0.169 |        1.10617e+06 |               -276.1  |             6346 |
| 20m_accepted_breakout_short  | 2026_H1_validation          |     3975 |     29.38 |       -85.057 |           0.272 |   338101           |               -230.24 |             2807 |
| 20m_accepted_breakout_short  | 2026_H2_seen_recheck        |     2482 |     24.62 |       -92.503 |           0.213 |   229707           |               -206.55 |             1871 |
| 20m_accepted_breakout_short  | 2026_Nov_recent_exploratory |      398 |     28.89 |       -82.748 |           0.279 |    32933.6         |               -190.38 |              283 |
| 20m_rejected_sweep_long      | 2025_train                  |     6845 |     32.46 |      -110.692 |           0.194 |   757690           |               -284.65 |             4623 |
| 20m_rejected_sweep_long      | 2026_H1_validation          |     3275 |     29.31 |       -84.409 |           0.257 |   276439           |               -221.46 |             2315 |
| 20m_rejected_sweep_long      | 2026_H2_seen_recheck        |     2242 |     27.39 |       -81.923 |           0.246 |   183961           |               -201.64 |             1628 |
| 20m_rejected_sweep_long      | 2026_Nov_recent_exploratory |      259 |     27.8  |       -84.779 |           0.269 |    21957.7         |               -190.23 |              187 |
| 20m_rejected_sweep_short     | 2025_train                  |     6706 |     32.36 |      -110.152 |           0.193 |   738699           |               -273.73 |             4536 |
| 20m_rejected_sweep_short     | 2026_H1_validation          |     3110 |     29.77 |       -80.19  |           0.269 |   249392           |               -221.68 |             2184 |
| 20m_rejected_sweep_short     | 2026_H2_seen_recheck        |     2146 |     25.26 |       -87.84  |           0.207 |   188505           |               -205.93 |             1604 |
| 20m_rejected_sweep_short     | 2026_Nov_recent_exploratory |      236 |     35.17 |       -55.908 |           0.391 |    13245.1         |               -190.7  |              153 |
| 5min_close_breakout_long     | 2025_train                  |     2425 |     28.58 |      -127.186 |           0.156 |   308425           |               -273.04 |             1732 |
| 5min_close_breakout_long     | 2026_H1_validation          |      993 |     27.69 |       -91.114 |           0.243 |    90603.4         |               -222.13 |              718 |
| 5min_close_breakout_long     | 2026_H2_seen_recheck        |      811 |     26.02 |       -86.518 |           0.233 |    70165.7         |               -202.67 |              600 |
| 5min_close_breakout_long     | 2026_Nov_recent_exploratory |       90 |     20    |       -99.934 |           0.17  |     9107           |               -190.64 |               72 |
| 5min_close_breakout_short    | 2025_train                  |     2345 |     29.85 |      -121.752 |           0.172 |   285508           |               -268.5  |             1645 |
| 5min_close_breakout_short    | 2026_H1_validation          |     1197 |     30.16 |       -83.026 |           0.289 |    99510.1         |               -220.87 |              836 |
| 5min_close_breakout_short    | 2026_H2_seen_recheck        |      775 |     23.35 |       -98.345 |           0.198 |    76354.9         |               -201.64 |              594 |
| 5min_close_breakout_short    | 2026_Nov_recent_exploratory |      120 |     24.17 |       -94.015 |           0.226 |    11543.2         |               -190.09 |               91 |
| 60m_rejected_sweep_long      | 2025_train                  |     2318 |     32.27 |      -112.082 |           0.188 |   259880           |               -268.28 |             1570 |
| 60m_rejected_sweep_long      | 2026_H1_validation          |     1220 |     28.28 |       -89.114 |           0.247 |   108857           |               -221.01 |              875 |
| 60m_rejected_sweep_long      | 2026_H2_seen_recheck        |      926 |     27    |       -84.823 |           0.228 |    78879.2         |               -201.62 |              676 |
| 60m_rejected_sweep_long      | 2026_Nov_recent_exploratory |       92 |     25    |       -93.868 |           0.234 |     8767.62        |               -190.15 |               69 |
| 60m_rejected_sweep_short     | 2025_train                  |     2098 |     32.17 |      -109.701 |           0.195 |   230321           |               -273.55 |             1423 |
| 60m_rejected_sweep_short     | 2026_H1_validation          |     1140 |     28.33 |       -84.235 |           0.251 |    96303.9         |               -221.68 |              817 |
| 60m_rejected_sweep_short     | 2026_H2_seen_recheck        |      884 |     24.21 |       -90.435 |           0.198 |    79977           |               -205.93 |              670 |
| 60m_rejected_sweep_short     | 2026_Nov_recent_exploratory |       63 |     38.1  |       -60.239 |           0.362 |     3924.8         |               -190.7  |               39 |
| compression_break_long       | 2025_train                  |      412 |     32.28 |      -127.664 |           0.168 |    52767.6         |              -7123.25 |              279 |
| compression_break_long       | 2026_H1_validation          |      192 |     21.35 |      -100.833 |           0.177 |    19451.3         |               -220.84 |              151 |
| compression_break_long       | 2026_H2_seen_recheck        |      221 |     20.36 |       -90.292 |           0.159 |    19954.6         |               -203.04 |              176 |
| compression_break_long       | 2026_Nov_recent_exploratory |       25 |      0    |      -157.095 |           0     |     3927.38        |               -190.51 |               25 |
| compression_break_short      | 2025_train                  |      383 |     28.46 |      -126.355 |           0.151 |    48563.8         |               -276.1  |              274 |
| compression_break_short      | 2026_H1_validation          |      231 |     23.38 |       -93.477 |           0.197 |    21593.2         |               -221.51 |              177 |
| compression_break_short      | 2026_H2_seen_recheck        |      220 |     17.73 |      -100.609 |           0.139 |    22271.5         |               -201.7  |              181 |
| compression_break_short      | 2026_Nov_recent_exploratory |       33 |     18.18 |       -95.839 |           0.153 |     3162.69        |               -190.27 |               27 |
| every_minute_long            | 2025_train                  |   109926 |     33.26 |      -118.042 |           0.183 |        1.29759e+07 |              -7123.25 |            73367 |
| every_minute_long            | 2026_H1_validation          |    28830 |     31.34 |       -84.749 |           0.285 |        2.44342e+06 |               -334.09 |            19794 |
| every_minute_long            | 2026_H2_seen_recheck        |    14184 |     29.59 |       -84.499 |           0.262 |        1.19853e+06 |               -245.4  |             9987 |
| every_minute_long            | 2026_Nov_recent_exploratory |     2488 |     29.38 |       -82.366 |           0.289 |   205181           |               -190.78 |             1757 |
| every_minute_short           | 2025_train                  |   110040 |     33.75 |      -116.545 |           0.187 |        1.28248e+07 |              -2828.37 |            72898 |
| every_minute_short           | 2026_H1_validation          |    28606 |     31.98 |       -82.529 |           0.295 |        2.36083e+06 |              -1454.85 |            19459 |
| every_minute_short           | 2026_H2_seen_recheck        |    14177 |     29.11 |       -85.772 |           0.255 |        1.21603e+06 |               -213.3  |            10050 |
| every_minute_short           | 2026_Nov_recent_exploratory |     2427 |     33.42 |       -71.253 |           0.345 |   172932           |               -190.84 |             1616 |
| strong_burst_long            | 2025_train                  |     5779 |     31.56 |      -115.3   |           0.185 |   666317           |               -275.03 |             3955 |
| strong_burst_long            | 2026_H1_validation          |     2829 |     27.71 |       -88.273 |           0.252 |   249844           |               -226.25 |             2045 |
| strong_burst_long            | 2026_H2_seen_recheck        |     1981 |     27.71 |       -79.63  |           0.261 |   157837           |               -202.95 |             1432 |
| strong_burst_long            | 2026_Nov_recent_exploratory |      251 |     20.72 |      -104.242 |           0.179 |    26211.8         |               -190.64 |              199 |
| strong_burst_short           | 2025_train                  |     5755 |     29.96 |      -119.047 |           0.176 |   685206           |               -270.69 |             4031 |
| strong_burst_short           | 2026_H1_validation          |     3069 |     29.52 |       -84.789 |           0.27  |   260217           |               -230.24 |             2163 |
| strong_burst_short           | 2026_H2_seen_recheck        |     2025 |     25.19 |       -89.069 |           0.218 |   180617           |               -205.93 |             1515 |
| strong_burst_short           | 2026_Nov_recent_exploratory |      275 |     30.18 |       -77.299 |           0.303 |    21388.8         |               -190.4  |              192 |
| trend_pullback_reclaim_long  | 2025_train                  |     8443 |     32.07 |      -114.517 |           0.185 |   966867           |               -276.26 |             5735 |
| trend_pullback_reclaim_long  | 2026_H1_validation          |     3267 |     28.99 |       -84.918 |           0.26  |   277429           |               -222.62 |             2320 |
| trend_pullback_reclaim_long  | 2026_H2_seen_recheck        |     2326 |     26.18 |       -85.671 |           0.238 |   199288           |               -202.58 |             1717 |
| trend_pullback_reclaim_long  | 2026_Nov_recent_exploratory |      248 |     25    |       -87.801 |           0.236 |    21935.3         |               -190.63 |              186 |
| trend_pullback_reclaim_short | 2025_train                  |     8497 |     33.07 |      -112.114 |           0.196 |   952655           |               -299.22 |             5687 |
| trend_pullback_reclaim_short | 2026_H1_validation          |     3802 |     29.75 |       -82.723 |           0.281 |   314512           |               -223.86 |             2671 |
| trend_pullback_reclaim_short | 2026_H2_seen_recheck        |     2239 |     25.59 |       -88.088 |           0.227 |   197368           |               -208.08 |             1666 |
| trend_pullback_reclaim_short | 2026_Nov_recent_exploratory |      387 |     29.97 |       -77.235 |           0.3   |    29983           |               -190.35 |              271 |

## Rankings from 2025 training only (not evidence of future profitability)
| rule                         |   trades |   avg_net_pts |   win_pct |   losses_or_flat |
|:-----------------------------|---------:|--------------:|----------:|-----------------:|
| 60m_rejected_sweep_short     |     2098 |      -109.701 |     32.17 |             1423 |
| 20m_rejected_sweep_short     |     6706 |      -110.152 |     32.36 |             4536 |
| 20m_rejected_sweep_long      |     6845 |      -110.692 |     32.46 |             4623 |
| 60m_rejected_sweep_long      |     2318 |      -112.082 |     32.27 |             1570 |
| trend_pullback_reclaim_short |     8497 |      -112.114 |     33.07 |             5687 |
| trend_pullback_reclaim_long  |     8443 |      -114.517 |     32.07 |             5735 |
| strong_burst_long            |     5779 |      -115.3   |     31.56 |             3955 |
| every_minute_short           |   110040 |      -116.545 |     33.75 |            72898 |
| 20m_accepted_breakout_long   |     9234 |      -117.345 |     31.71 |             6306 |
| every_minute_long            |   109926 |      -118.042 |     33.26 |            73367 |
| strong_burst_short           |     5755 |      -119.047 |     29.96 |             4031 |
| 5min_close_breakout_short    |     2345 |      -121.752 |     29.85 |             1645 |
| 20m_accepted_breakout_short  |     9068 |      -121.984 |     30.02 |             6346 |
| 15min_close_breakout_long    |      711 |      -123.735 |     30.38 |              495 |
| compression_break_short      |      383 |      -126.355 |     28.46 |              274 |
| 15min_close_breakout_short   |      732 |      -126.674 |     28.14 |              526 |

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
