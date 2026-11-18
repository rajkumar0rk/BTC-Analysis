# ETHUSD — causal family audit across all completed Jan2025–Oct2026 months

**Representative research families only**. For exact source-code portability across
the previous BTC research scripts, inspect the independent matrix job as well.
All price data in this backtest are **native ETH prices**; only fixed 100/200
BTC-point rules are translated at each trade to ETH percentage-equivalent
using concurrent observed BTCUSD/ETHUSD data.

- Tested representative entry families: **52**
- Tested account models: **205**
- Positive in ALL 22 months: **0**
- At least +10% in ALL 22 months: **0**
- Costs: 0.05% taker/side + 18% GST; assumed 0.25 ETH pts adverse slip/side.
- Equity risk 0.5% per stop distance, max 3x notional; stop-first 1m fills.
- Funding, actual spread, real fills, liquidation/margin and minimum contract sizes are not observed.

## One 2025-only selected model per ETH strategy family

| family                              | model                                        |   positive2025 |   positive2026 |   months_ge10 |   trades |   wins |   losses |   net_total_return_pct |   max_trade_close_drawdown_pct |
|:------------------------------------|:---------------------------------------------|---------------:|---------------:|--------------:|---------:|-------:|---------:|-----------------------:|-------------------------------:|
| 1h:hourly_reversal_3c               | 1h:hourly_reversal_3c__SL2.5_RR2             |             10 |              2 |             0 |      644 |    284 |      360 |              -5.68256  |                      -24.8382  |
| 4h:engulfing_reversal               | 4h:engulfing_reversal__SL1.5_RR3             |              9 |              6 |             0 |      190 |     78 |      112 |              16.0852   |                       -4.76376 |
| 1h:trend_efficiency                 | 1h:trend_efficiency__SL1.5_RR2               |              9 |              2 |             0 |      390 |    146 |      244 |              -2.05388  |                      -16.6458  |
| 4h:trend_efficiency                 | 4h:trend_efficiency__SL1.5_RR2               |              9 |              2 |             0 |      170 |     62 |      108 |              -5.86023  |                      -12.5304  |
| 4h:rsi2_extreme_fade                | 4h:rsi2_extreme_fade__SL1.5_RR3              |              8 |              3 |             0 |      193 |     74 |      119 |               0.264792 |                      -15.981   |
| 4h:donchian_break                   | 4h:donchian_break__SL2.5_RR2                 |              8 |              3 |             0 |       74 |     30 |       44 |              -0.200403 |                       -5.09492 |
| 4h:volume_1p5x_cont                 | 4h:volume_1p5x_cont__SL2.5_RR2               |              8 |              4 |             0 |      195 |     87 |      108 |               1.09478  |                       -5.11197 |
| 1h:failed_auction                   | 1h:failed_auction__SL1.5_RR2                 |              8 |              4 |             0 |      110 |     47 |       63 |              -0.890379 |                       -4.82104 |
| 4h:failed_auction                   | 4h:failed_auction__SL1.5_RR2                 |              7 |              2 |             0 |       19 |     11 |        8 |               3.43166  |                       -1.62178 |
| 4h:momentum_expansion               | 4h:momentum_expansion__SL1.5_RR2             |              7 |              3 |             0 |      248 |     96 |      152 |              -3.18033  |                      -11.1861  |
| 4h:inside_bar_break                 | 4h:inside_bar_break__SL1.5_RR3               |              7 |              5 |             0 |      118 |     39 |       79 |               3.55249  |                       -4.77464 |
| 4h:ema20_pullback                   | 4h:ema20_pullback__SL2.5_RR3                 |              7 |              5 |             0 |      125 |     53 |       72 |               1.15122  |                       -5.18116 |
| 1h:rsi2_extreme_fade                | 1h:rsi2_extreme_fade__SL2.5_RR2              |              7 |              5 |             0 |      566 |    250 |      316 |              -6.95703  |                      -10.7024  |
| 1h:engulfing_reversal               | 1h:engulfing_reversal__SL2.5_RR3             |              7 |              5 |             0 |      592 |    260 |      332 |               8.35235  |                       -9.37641 |
| 1h:inside_bar_break                 | 1h:inside_bar_break__SL2.5_RR2               |              7 |              6 |             0 |      414 |    183 |      231 |              -3.91021  |                      -10.7192  |
| 15min:ema9_21_crossover             | 15min:ema9_21_crossover__SL2.5_RR3           |              7 |              2 |             0 |     1215 |    427 |      788 |             -35.7394   |                      -50.8719  |
| 15min:trend_efficiency              | 15min:trend_efficiency__SL2.5_RR3            |              6 |              4 |             2 |      673 |    226 |      447 |              -7.67303  |                      -22.6107  |
| 4h:ema9_21_crossover                | 4h:ema9_21_crossover__SL2.5_RR3              |              6 |              4 |             0 |      119 |     47 |       72 |               0.38281  |                       -3.59189 |
| 15min:squeeze_break                 | 15min:squeeze_break__SL2.5_RR3               |              6 |              1 |             0 |      361 |    119 |      242 |             -23.7821   |                      -31.1399  |
| 4h:squeeze_break                    | 4h:squeeze_break__SL2.5_RR2                  |              5 |              2 |             0 |       26 |      8 |       18 |              -2.57674  |                       -3.48113 |
| 15min:trend_retest                  | 15min:trend_retest__SL1.5_RR3                |              5 |              0 |             0 |       81 |     19 |       62 |             -13.9503   |                      -17.3251  |
| 1h:donchian_break                   | 1h:donchian_break__SL1.5_RR2                 |              5 |              5 |             0 |      506 |    189 |      317 |              -7.35139  |                      -16.2706  |
| 1h:squeeze_break                    | 1h:squeeze_break__SL1.5_RR2                  |              5 |              4 |             0 |      116 |     41 |       75 |              -6.59341  |                       -9.87984 |
| 1h:ema9_21_crossover                | 1h:ema9_21_crossover__SL2.5_RR3              |              5 |              7 |             0 |      386 |    165 |      221 |              -1.86665  |                      -11.6059  |
| 1h:ema20_pullback                   | 1h:ema20_pullback__SL2.5_RR2                 |              5 |              5 |             0 |      436 |    167 |      269 |             -17.4435   |                      -21.8592  |
| 15min:failed_auction                | 15min:failed_auction__SL2.5_RR3              |              5 |              4 |             0 |      504 |    182 |      322 |             -27.6044   |                      -34.8462  |
| 15min:supertrend_ema_proxy          | 15min:supertrend_ema_proxy__SL2.5_RR3        |              5 |              2 |             0 |      987 |    322 |      665 |             -42.8043   |                      -44.6907  |
| 1h:momentum_expansion               | 1h:momentum_expansion__SL1.5_RR2             |              4 |              4 |             1 |      924 |    347 |      577 |             -21.9039   |                      -25.3849  |
| 1h:volume_1p5x_cont                 | 1h:volume_1p5x_cont__SL2.5_RR2               |              4 |              5 |             0 |      708 |    292 |      416 |             -20.8456   |                      -22.4508  |
| 15min:engulfing_reversal            | 15min:engulfing_reversal__SL2.5_RR3          |              4 |              5 |             0 |     1729 |    637 |     1092 |             -36.1792   |                      -36.6128  |
| 15min:volume_1p5x_cont              | 15min:volume_1p5x_cont__SL2.5_RR2            |              4 |              1 |             0 |     2099 |    785 |     1314 |             -69.7913   |                      -71.1593  |
| 15min:donchian_break                | 15min:donchian_break__SL2.5_RR2              |              3 |              1 |             0 |     1583 |    577 |     1006 |             -65.0277   |                      -67.8133  |
| 15min:ema20_pullback                | 15min:ema20_pullback__SL2.5_RR3              |              3 |              4 |             0 |     1381 |    464 |      917 |             -53.5953   |                      -54.8955  |
| 15min:inside_bar_break              | 15min:inside_bar_break__SL2.5_RR2            |              3 |              1 |             0 |     1339 |    489 |      850 |             -63.229    |                      -64.8846  |
| 5min:prevday_break                  | 5min:prevday_break__SL2.5_RR2                |              3 |              0 |             0 |      958 |    336 |      622 |             -65.745    |                      -66.7689  |
| 5min:prevday_sweep                  | 5min:prevday_sweep__SL2.5_RR3                |              2 |              0 |             0 |      873 |    342 |      531 |             -54.8941   |                      -55.7348  |
| 15min:momentum_expansion            | 15min:momentum_expansion__SL2.5_RR3          |              2 |              1 |             0 |     1878 |    614 |     1264 |             -72.4411   |                      -74.0387  |
| 15min:vwap_reclaim                  | 15min:vwap_reclaim__SL2.5_RR3                |              2 |              1 |             0 |     1429 |    462 |      967 |             -71.7658   |                      -72.0803  |
| 5min:squeeze_break                  | 5min:squeeze_break__SL2.5_RR3                |              1 |              0 |             0 |     1215 |    385 |      830 |             -84.9503   |                      -85.0783  |
| 5min:trend_efficiency               | 5min:trend_efficiency__SL2.5_RR3             |              1 |              0 |             0 |     1865 |    571 |     1294 |             -89.7012   |                      -89.744   |
| 15min:rsi2_extreme_fade             | 15min:rsi2_extreme_fade__SL2.5_RR2           |              1 |              1 |             0 |     1776 |    670 |     1106 |             -77.411    |                      -77.411   |
| 5min:ist_opening_range_break        | 5min:ist_opening_range_break__SL2.5_RR3      |              1 |              0 |             0 |     1746 |    530 |     1216 |             -93.485    |                      -93.594   |
| 5min:failed_auction                 | 5min:failed_auction__SL2.5_RR3               |              1 |              0 |             0 |     1699 |    573 |     1126 |             -92.191    |                      -92.2759  |
| 5min:donchian_break                 | 5min:donchian_break__SL2.5_RR3               |              1 |              0 |             0 |     4603 |   1452 |     3151 |             -99.7002   |                      -99.7177  |
| 5min:ema9_21_crossover              | 5min:ema9_21_crossover__SL2.5_RR3            |              1 |              0 |             0 |     3748 |   1159 |     2589 |             -99.6027   |                      -99.6037  |
| 5min:ema20_pullback                 | 5min:ema20_pullback__SL2.5_RR3               |              1 |              0 |             0 |     4281 |   1329 |     2952 |             -99.7701   |                      -99.7769  |
| 5min:engulfing_reversal             | 5min:engulfing_reversal__SL2.5_RR3           |              1 |              0 |             0 |     5284 |   1725 |     3559 |             -99.945    |                      -99.9519  |
| 5min:inside_bar_break               | 5min:inside_bar_break__SL2.5_RR3             |              0 |              0 |             0 |     3847 |   1295 |     2552 |             -98.919    |                      -98.9533  |
| 5min:volume_1p5x_cont               | 5min:volume_1p5x_cont__SL2.5_RR3             |              0 |              0 |             0 |     5809 |   1840 |     3969 |             -99.9547   |                      -99.9564  |
| 5min:rsi2_extreme_fade              | 5min:rsi2_extreme_fade__SL2.5_RR3            |              0 |              0 |             0 |     4930 |   1705 |     3225 |             -99.8292   |                      -99.831   |
| 5min:momentum_expansion             | 5min:momentum_expansion__SL2.5_RR3           |              0 |              0 |             0 |     5750 |   1850 |     3900 |             -99.9454   |                      -99.9463  |
| 5min:price_level_break_fixed100_200 | 5min:price_level_break_fixed100_200__SL1_RR2 |              0 |              0 |             0 |     1530 |    435 |     1095 |             -99.8719   |                      -99.8732  |

## Monthly NET account results for best 2025-ranked family

| month   |   return_pct |   trades |   wins |   losses |   equity_start |   equity_end |
|:--------|-------------:|---------:|-------:|---------:|---------------:|-------------:|
| 2025-01 |   -1.01998   |       26 |     10 |       16 |       1000     |      989.8   |
| 2025-02 |    0.157164  |       28 |     14 |       14 |        989.8   |      991.356 |
| 2025-03 |    2.37824   |       26 |     12 |       14 |        991.356 |     1014.93  |
| 2025-04 |    3.21799   |       31 |     17 |       14 |       1014.93  |     1047.59  |
| 2025-05 |    0.217606  |       31 |     16 |       15 |       1047.59  |     1049.87  |
| 2025-06 |   -2.56255   |       26 |      9 |       17 |       1049.87  |     1022.97  |
| 2025-07 |    0.33178   |       28 |     14 |       14 |       1022.97  |     1026.36  |
| 2025-08 |    2.16257   |       32 |     16 |       16 |       1026.36  |     1048.56  |
| 2025-09 |    2.06842   |       25 |     13 |       12 |       1048.56  |     1070.25  |
| 2025-10 |    5.46636   |       25 |     16 |        9 |       1070.25  |     1128.75  |
| 2025-11 |    3.94688   |       31 |     16 |       15 |       1128.75  |     1173.3   |
| 2025-12 |    0.523035  |       31 |     14 |       17 |       1173.3   |     1179.44  |
| 2026-01 |    3.51067   |       30 |     15 |       15 |       1179.44  |     1220.84  |
| 2026-02 |   -0.442723  |       25 |     12 |       13 |       1220.84  |     1215.44  |
| 2026-03 |   -0.354694  |       28 |     11 |       17 |       1215.44  |     1211.13  |
| 2026-04 |   -0.0759166 |       35 |     16 |       19 |       1211.13  |     1210.21  |
| 2026-05 |   -3.73398   |       33 |     13 |       20 |       1210.21  |     1165.02  |
| 2026-06 |   -4.08529   |       28 |     11 |       17 |       1165.02  |     1117.43  |
| 2026-07 |   -8.42404   |       33 |      6 |       27 |       1117.43  |     1023.29  |
| 2026-08 |   -4.91336   |       31 |     10 |       21 |       1023.29  |      973.015 |
| 2026-09 |   -4.12615   |       27 |      8 |       19 |        973.015 |      932.867 |
| 2026-10 |    1.1049    |       33 |     15 |       18 |        932.867 |      943.174 |

## Caveats

- These family representatives are not strict byte-for-byte executions of all old BTC scripts.
- The independent original-code audit can fail on prior-stage output dependencies.
- Positive backtest months do not guarantee future ETH profits.
- January 2025 IST first 5.5 hours are missing from archive (starts Jan1 UTC).
- UTC 2026-10-31 candles are present in BTC and ETH manifests; November 2026 excluded.
- Using only 2025 to pick each family reduces but does not remove selection bias.
- A nominal 0.25 ETH price-point slippage is NOT a live verified bid/ask spread.
