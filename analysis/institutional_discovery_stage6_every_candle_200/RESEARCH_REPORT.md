# Stage 6 — Every BTCUSD 1m candle: 200 points, clean paths and executable entries

## Dataset audit
- Real 1m candles loaded: **984,960**
- Fully eligible next-open entries: **983,644** per direction
- All long+short entry paths evaluated: **1,967,288**
- Gaps: **1,440** missing minutes across **1** breaks; never filled
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
| every_minute_long  | 2025_train                  |            30 |    525181 |           37.496 |                      3.56239 |                   25.889 |                          19.666 |
| every_minute_long  | 2025_train                  |            60 |    525181 |           51.514 |                      3.80002 |                   30.772 |                          32.005 |
| every_minute_long  | 2025_train                  |           240 |    525181 |           74.407 |                      3.88609 |                   33.989 |                          59.365 |
| every_minute_long  | 2026_H1_validation          |            30 |    260401 |           28.402 |                      2.36942 |                   20.94  |                          16.089 |
| every_minute_long  | 2026_H1_validation          |            60 |    260401 |           41.658 |                      2.67472 |                   27.061 |                          26.923 |
| every_minute_long  | 2026_H1_validation          |           240 |    260401 |           67.321 |                      2.84984 |                   32.546 |                          53.891 |
| every_minute_long  | 2026_H2_seen_recheck        |            30 |    175441 |           19.957 |                      1.86786 |                   16.106 |                           9.956 |
| every_minute_long  | 2026_H2_seen_recheck        |            60 |    175441 |           31.931 |                      2.25261 |                   23.14  |                          18.718 |
| every_minute_long  | 2026_H2_seen_recheck        |           240 |    175441 |           60.281 |                      2.59859 |                   32.17  |                          45.928 |
| every_minute_long  | 2026_Nov_recent_exploratory |            30 |     22621 |           27.452 |                      2.32969 |                   19.995 |                          14.761 |
| every_minute_long  | 2026_Nov_recent_exploratory |            60 |     22621 |           39.317 |                      2.49768 |                   24.778 |                          24.698 |
| every_minute_long  | 2026_Nov_recent_exploratory |           240 |     22621 |           63.22  |                      2.67893 |                   29.371 |                          48.406 |
| every_minute_short | 2025_train                  |            30 |    525181 |           37.508 |                      3.70215 |                   25.985 |                          20.031 |
| every_minute_short | 2025_train                  |            60 |    525181 |           51.135 |                      3.95844 |                   30.778 |                          32.266 |
| every_minute_short | 2025_train                  |           240 |    525181 |           74.298 |                      4.07498 |                   33.843 |                          59.932 |
| every_minute_short | 2026_H1_validation          |            30 |    260401 |           29.796 |                      2.43471 |                   22.437 |                          16.991 |
| every_minute_short | 2026_H1_validation          |            60 |    260401 |           43.945 |                      2.70621 |                   29.051 |                          29.017 |
| every_minute_short | 2026_H1_validation          |           240 |    260401 |           69.776 |                      2.80222 |                   34.182 |                          57.689 |
| every_minute_short | 2026_H2_seen_recheck        |            30 |    175441 |           19.447 |                      1.90548 |                   15.834 |                           9.407 |
| every_minute_short | 2026_H2_seen_recheck        |            60 |    175441 |           31.55  |                      2.2794  |                   22.886 |                          18.422 |
| every_minute_short | 2026_H2_seen_recheck        |           240 |    175441 |           57.858 |                      2.49657 |                   30.647 |                          44.543 |
| every_minute_short | 2026_Nov_recent_exploratory |            30 |     22621 |           31.798 |                      2.74966 |                   24.446 |                          18.505 |
| every_minute_short | 2026_Nov_recent_exploratory |            60 |     22621 |           45.387 |                      2.94417 |                   30.255 |                          30.379 |
| every_minute_short | 2026_Nov_recent_exploratory |           240 |     22621 |           72.472 |                      3.20499 |                   36.997 |                          60.294 |

## Predeclared executable strategies at 200 gross TP / 100 stop / 30m max
| rule                         | period                      |   trades |   win_pct |   avg_net_pts |   profit_factor |   max_drawdown_pts |   worst_net_trade_pts |   losses_or_flat |
|:-----------------------------|:----------------------------|---------:|----------:|--------------:|----------------:|-------------------:|----------------------:|-----------------:|
| 15min_close_breakout_long    | 2025_train                  |      908 |     28.52 |      -137.593 |           0.123 |   124934           |               -258.19 |              649 |
| 15min_close_breakout_long    | 2026_H1_validation          |      378 |     23.28 |      -115.426 |           0.167 |    43749.4         |               -224.8  |              290 |
| 15min_close_breakout_long    | 2026_H2_seen_recheck        |      254 |     24.41 |      -101.313 |           0.177 |    25831.6         |               -212.89 |              192 |
| 15min_close_breakout_long    | 2026_Nov_recent_exploratory |       21 |      9.52 |      -139.825 |           0.063 |     2936.33        |               -205.41 |               19 |
| 15min_close_breakout_short   | 2025_train                  |     1003 |     28.22 |      -137.861 |           0.124 |   138350           |               -256.52 |              720 |
| 15min_close_breakout_short   | 2026_H1_validation          |      471 |     27.6  |      -102.544 |           0.217 |    48423.5         |               -223.77 |              341 |
| 15min_close_breakout_short   | 2026_H2_seen_recheck        |      278 |     25.54 |       -99.488 |           0.191 |    27976.2         |               -211.58 |              207 |
| 15min_close_breakout_short   | 2026_Nov_recent_exploratory |       49 |     22.45 |      -120.436 |           0.162 |     5901.34        |               -204.1  |               38 |
| 20m_accepted_breakout_long   | 2025_train                  |     9446 |     27.15 |      -133.761 |           0.121 |        1.26351e+06 |               -275.92 |             6881 |
| 20m_accepted_breakout_long   | 2026_H1_validation          |     3948 |     25.51 |      -101.166 |           0.193 |   399432           |               -225.16 |             2941 |
| 20m_accepted_breakout_long   | 2026_H2_seen_recheck        |     2690 |     23.2  |       -98.54  |           0.172 |   265175           |               -212.99 |             2066 |
| 20m_accepted_breakout_long   | 2026_Nov_recent_exploratory |      335 |     22.09 |      -107.433 |           0.169 |    35989.9         |               -205.32 |              261 |
| 20m_accepted_breakout_short  | 2025_train                  |     9842 |     27.29 |      -133.76  |           0.124 |        1.31646e+06 |               -263.88 |             7156 |
| 20m_accepted_breakout_short  | 2026_H1_validation          |     4440 |     27.07 |       -99.848 |           0.207 |   443327           |               -224.53 |             3238 |
| 20m_accepted_breakout_short  | 2026_H2_seen_recheck        |     2708 |     22.49 |      -100.848 |           0.161 |   273281           |               -213.92 |             2099 |
| 20m_accepted_breakout_short  | 2026_Nov_recent_exploratory |      400 |     30.5  |       -85.895 |           0.259 |    34479           |               -204.98 |              278 |
| 20m_rejected_sweep_long      | 2025_train                  |     6536 |     29.31 |      -126.592 |           0.136 |   827405           |               -259.97 |             4620 |
| 20m_rejected_sweep_long      | 2026_H1_validation          |     3185 |     26.41 |       -99.16  |           0.195 |   316003           |               -224.93 |             2344 |
| 20m_rejected_sweep_long      | 2026_H2_seen_recheck        |     2109 |     25.27 |       -92.816 |           0.189 |   195749           |               -212.35 |             1576 |
| 20m_rejected_sweep_long      | 2026_Nov_recent_exploratory |      257 |     29.18 |       -96.46  |           0.23  |    24790.3         |               -205.84 |              182 |
| 20m_rejected_sweep_short     | 2025_train                  |     6131 |     27.84 |      -128.14  |           0.129 |   785698           |               -257.75 |             4424 |
| 20m_rejected_sweep_short     | 2026_H1_validation          |     3182 |     27.22 |       -93.952 |           0.205 |   299360           |               -224.87 |             2316 |
| 20m_rejected_sweep_short     | 2026_H2_seen_recheck        |     2082 |     23.34 |       -96.641 |           0.162 |   201207           |               -212.73 |             1596 |
| 20m_rejected_sweep_short     | 2026_Nov_recent_exploratory |      222 |     27.48 |       -85.117 |           0.235 |    18896           |               -205.3  |              161 |
| 5min_close_breakout_long     | 2025_train                  |     2890 |     25.47 |      -140.577 |           0.108 |   406266           |               -258.34 |             2154 |
| 5min_close_breakout_long     | 2026_H1_validation          |     1169 |     24.72 |      -105.422 |           0.183 |   123239           |               -224.48 |              880 |
| 5min_close_breakout_long     | 2026_H2_seen_recheck        |      877 |     25.43 |       -93.863 |           0.193 |    82318           |               -212.72 |              654 |
| 5min_close_breakout_long     | 2026_Nov_recent_exploratory |       90 |     23.33 |      -104.494 |           0.174 |     9404.49        |               -205.32 |               69 |
| 5min_close_breakout_short    | 2025_train                  |     3052 |     27    |      -135.74  |           0.122 |   414279           |               -264.33 |             2228 |
| 5min_close_breakout_short    | 2026_H1_validation          |     1375 |     28    |       -99.637 |           0.214 |   137280           |               -224.54 |              990 |
| 5min_close_breakout_short    | 2026_H2_seen_recheck        |      891 |     22.33 |      -104.699 |           0.163 |    93528.4         |               -211.9  |              692 |
| 5min_close_breakout_short    | 2026_Nov_recent_exploratory |      134 |     28.36 |       -92.835 |           0.233 |    12439.9         |               -204.95 |               96 |
| 60m_rejected_sweep_long      | 2025_train                  |     2408 |     27.99 |      -129.679 |           0.127 |   312268           |               -258.42 |             1734 |
| 60m_rejected_sweep_long      | 2026_H1_validation          |     1233 |     27.66 |       -98.962 |           0.199 |   122021           |               -224.93 |              892 |
| 60m_rejected_sweep_long      | 2026_H2_seen_recheck        |      878 |     25.06 |       -92.939 |           0.187 |    81721.9         |               -212.03 |              658 |
| 60m_rejected_sweep_long      | 2026_Nov_recent_exploratory |       92 |     31.52 |       -88.244 |           0.263 |     8118.43        |               -203.88 |               63 |
| 60m_rejected_sweep_short     | 2025_train                  |     2131 |     27.78 |      -127.094 |           0.128 |   270923           |               -257.75 |             1539 |
| 60m_rejected_sweep_short     | 2026_H1_validation          |     1213 |     26.88 |       -96.489 |           0.196 |   117041           |               -224.87 |              887 |
| 60m_rejected_sweep_short     | 2026_H2_seen_recheck        |      855 |     23.04 |       -94.711 |           0.163 |    81075.1         |               -212.73 |              658 |
| 60m_rejected_sweep_short     | 2026_Nov_recent_exploratory |       72 |     26.39 |       -92.218 |           0.212 |     6793.47        |               -205.3  |               53 |
| compression_break_long       | 2025_train                  |      930 |     24.52 |      -132.608 |           0.105 |   123325           |               -257.48 |              702 |
| compression_break_long       | 2026_H1_validation          |      281 |     17.79 |      -109.682 |           0.132 |    30907           |               -224.17 |              231 |
| compression_break_long       | 2026_H2_seen_recheck        |      336 |     18.45 |       -97.97  |           0.129 |    33036.9         |               -212.07 |              274 |
| compression_break_long       | 2026_Nov_recent_exploratory |       30 |      3.33 |      -136.902 |           0.024 |     4107.07        |               -205.08 |               29 |
| compression_break_short      | 2025_train                  |      965 |     22.38 |      -135.698 |           0.097 |   130948           |               -263.88 |              749 |
| compression_break_short      | 2026_H1_validation          |      334 |     24.55 |       -89.998 |           0.186 |    30059.3         |               -222.47 |              252 |
| compression_break_short      | 2026_H2_seen_recheck        |      358 |     15.92 |      -103.016 |           0.115 |    37000.2         |               -211.25 |              301 |
| compression_break_short      | 2026_Nov_recent_exploratory |       35 |     28.57 |       -80.501 |           0.242 |     3155.25        |               -202.71 |               25 |
| every_minute_long            | 2025_train                  |    68914 |     31.59 |      -126.068 |           0.151 |        8.68788e+06 |               -856.69 |            47144 |
| every_minute_long            | 2026_H1_validation          |    25436 |     30.17 |       -95.838 |           0.235 |        2.43783e+06 |               -365.68 |            17761 |
| every_minute_long            | 2026_H2_seen_recheck        |    11870 |     26.94 |       -95.784 |           0.202 |        1.13706e+06 |               -215.54 |             8672 |
| every_minute_long            | 2026_Nov_recent_exploratory |     2246 |     28.18 |      -100.145 |           0.22  |   224927           |               -205.54 |             1613 |
| every_minute_short           | 2025_train                  |    68926 |     31.73 |      -125.333 |           0.152 |        8.63883e+06 |              -1725.2  |            47054 |
| every_minute_short           | 2026_H1_validation          |    25274 |     30.83 |       -93.776 |           0.243 |        2.3701e+06  |               -319.3  |            17482 |
| every_minute_short           | 2026_H2_seen_recheck        |    12074 |     26.25 |       -98.225 |           0.192 |        1.18603e+06 |               -220.26 |             8905 |
| every_minute_short           | 2026_Nov_recent_exploratory |     2153 |     33.16 |       -84.449 |           0.283 |   181818           |               -205.55 |             1439 |
| strong_burst_long            | 2025_train                  |     6807 |     27.46 |      -131.541 |           0.122 |   895400           |               -264.4  |             4938 |
| strong_burst_long            | 2026_H1_validation          |     3178 |     24.89 |      -103.257 |           0.184 |   328151           |               -224.91 |             2387 |
| strong_burst_long            | 2026_H2_seen_recheck        |     2377 |     22.76 |       -96.5   |           0.171 |   229528           |               -212.99 |             1836 |
| strong_burst_long            | 2026_Nov_recent_exploratory |      303 |     23.1  |      -103.69  |           0.177 |    31418.1         |               -205.02 |              233 |
| strong_burst_short           | 2025_train                  |     7093 |     26.91 |      -132.693 |           0.119 |   941274           |               -282.04 |             5184 |
| strong_burst_short           | 2026_H1_validation          |     3442 |     25.68 |      -102.425 |           0.189 |   352880           |               -224.87 |             2558 |
| strong_burst_short           | 2026_H2_seen_recheck        |     2379 |     21.94 |       -98.136 |           0.158 |   233650           |               -216.43 |             1857 |
| strong_burst_short           | 2026_Nov_recent_exploratory |      285 |     25.61 |       -96.695 |           0.206 |    27558.1         |               -205.26 |              212 |
| trend_pullback_reclaim_long  | 2025_train                  |     8291 |     28.44 |      -129.9   |           0.129 |        1.077e+06   |               -281.74 |             5933 |
| trend_pullback_reclaim_long  | 2026_H1_validation          |     3632 |     26.54 |       -99.125 |           0.2   |   360214           |               -225.07 |             2668 |
| trend_pullback_reclaim_long  | 2026_H2_seen_recheck        |     2418 |     22.99 |       -98.627 |           0.168 |   238578           |               -213.25 |             1862 |
| trend_pullback_reclaim_long  | 2026_Nov_recent_exploratory |      276 |     18.84 |      -117.477 |           0.136 |    32423.6         |               -205.41 |              224 |
| trend_pullback_reclaim_short | 2025_train                  |     8660 |     29.71 |      -126.547 |           0.139 |        1.09607e+06 |               -265.25 |             6087 |
| trend_pullback_reclaim_short | 2026_H1_validation          |     4051 |     29.33 |       -93.354 |           0.233 |   378302           |               -224.52 |             2863 |
| trend_pullback_reclaim_short | 2026_H2_seen_recheck        |     2423 |     23.32 |       -98.357 |           0.17  |   238517           |               -213.33 |             1858 |
| trend_pullback_reclaim_short | 2026_Nov_recent_exploratory |      397 |     29.47 |       -94.387 |           0.23  |    37471.6         |               -205.15 |              280 |

## Rankings from 2025 training only (not evidence of future profitability)
| rule                         |   trades |   avg_net_pts |   win_pct |   losses_or_flat |
|:-----------------------------|---------:|--------------:|----------:|-----------------:|
| every_minute_short           |    68926 |      -125.333 |     31.73 |            47054 |
| every_minute_long            |    68914 |      -126.068 |     31.59 |            47144 |
| trend_pullback_reclaim_short |     8660 |      -126.547 |     29.71 |             6087 |
| 20m_rejected_sweep_long      |     6536 |      -126.592 |     29.31 |             4620 |
| 60m_rejected_sweep_short     |     2131 |      -127.094 |     27.78 |             1539 |
| 20m_rejected_sweep_short     |     6131 |      -128.14  |     27.84 |             4424 |
| 60m_rejected_sweep_long      |     2408 |      -129.679 |     27.99 |             1734 |
| trend_pullback_reclaim_long  |     8291 |      -129.9   |     28.44 |             5933 |
| strong_burst_long            |     6807 |      -131.541 |     27.46 |             4938 |
| compression_break_long       |      930 |      -132.608 |     24.52 |              702 |
| strong_burst_short           |     7093 |      -132.693 |     26.91 |             5184 |
| 20m_accepted_breakout_short  |     9842 |      -133.76  |     27.29 |             7156 |
| 20m_accepted_breakout_long   |     9446 |      -133.761 |     27.15 |             6881 |
| compression_break_short      |      965 |      -135.698 |     22.38 |              749 |
| 5min_close_breakout_short    |     3052 |      -135.74  |     27    |             2228 |
| 15min_close_breakout_long    |      908 |      -137.593 |     28.52 |              649 |

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
