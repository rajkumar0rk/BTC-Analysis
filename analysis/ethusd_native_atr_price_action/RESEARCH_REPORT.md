# Native ETHUSD ATR price-action family backtest

All source ETHUSD candles are UNscaled. **No BTC fixed 200-point stop/target.**
Tested 8 entry-pattern families × 3 timeframes × 2 ATR stops × 2R/3R
× 240/720-minute maximum hold.

## Simulation and costs
Total model variations: 192; trades across separate models: 298299.
One position per independent model. Slippage assumed 0.02% per side.
Taker fee 0.05% per side plus GST 18%. Missing funding/real order book.

## Ranked only using Jan-Dec 2025
| model                                                   |   months_positive_2025 |   months_positive_2026 |   months_positive_all | complete_22_positive   |   compounding_2025_pct |   compounding_2026_pct |   max_month_end_drawdown_pct |   trades |   wins |   losses |
|:--------------------------------------------------------|-----------------------:|-----------------------:|----------------------:|:-----------------------|-----------------------:|-----------------------:|-----------------------------:|---------:|-------:|---------:|
| 4h_strong_momentum|SL=1.5ATR|TP=3R|hold=240m            |                      9 |                      4 |                    13 | False                  |                 2.1787 |                -2.0171 |                      4.18016 |      216 |     92 |      124 |
| 4h_strong_momentum|SL=1.5ATR|TP=2R|hold=240m            |                      9 |                      4 |                    13 | False                  |                 1.8223 |                -1.6828 |                      4.45248 |      216 |     92 |      124 |
| 4h_strong_momentum|SL=3ATR|TP=2R|hold=720m              |                      9 |                      3 |                    12 | False                  |                 0.6283 |                -0.538  |                      2.30493 |      186 |     81 |      105 |
| 4h_strong_momentum|SL=3ATR|TP=3R|hold=720m              |                      8 |                      3 |                    11 | False                  |                 0.182  |                -0.6032 |                      2.36894 |      186 |     81 |      105 |
| 4h_strong_momentum|SL=1.5ATR|TP=3R|hold=720m            |                      8 |                      3 |                    11 | False                  |                -0.0585 |                 0.5622 |                      3.62763 |      194 |     80 |      114 |
| 4h_strong_momentum|SL=1.5ATR|TP=2R|hold=720m            |                      8 |                      4 |                    12 | False                  |                -1.1524 |                 0.6569 |                      3.62763 |      197 |     81 |      116 |
| 4h_donchian20_breakout|SL=1.5ATR|TP=3R|hold=720m        |                      7 |                      3 |                    10 | False                  |                 4.0759 |                -2.997  |                      5.01197 |      156 |     62 |       94 |
| 4h_donchian20_breakout|SL=1.5ATR|TP=3R|hold=240m        |                      7 |                      3 |                    10 | False                  |                 3.5108 |                -3.6762 |                      5.78597 |      185 |     79 |      106 |
| 4h_donchian20_breakout|SL=1.5ATR|TP=2R|hold=720m        |                      7 |                      3 |                    10 | False                  |                 3.4628 |                -3.075  |                      5.53021 |      160 |     65 |       95 |
| 4h_rsi2_reversal_confirm|SL=1.5ATR|TP=3R|hold=720m      |                      7 |                      3 |                    10 | False                  |                 3.3302 |                -1.6504 |                      5.76632 |      134 |     67 |       67 |
| 4h_rsi2_reversal_confirm|SL=1.5ATR|TP=2R|hold=720m      |                      7 |                      3 |                    10 | False                  |                 2.7313 |                -2.28   |                      6.31249 |      134 |     67 |       67 |
| 4h_donchian20_breakout|SL=1.5ATR|TP=2R|hold=240m        |                      7 |                      3 |                    10 | False                  |                 2.6412 |                -3.4283 |                      6.0755  |      185 |     79 |      106 |
| 4h_donchian20_breakout|SL=3ATR|TP=2R|hold=720m          |                      7 |                      5 |                    12 | False                  |                 1.6806 |                -2.1154 |                      3.1178  |      152 |     64 |       88 |
| 4h_donchian20_breakout|SL=3ATR|TP=3R|hold=720m          |                      7 |                      5 |                    12 | False                  |                 1.2297 |                -2.1795 |                      3.18128 |      152 |     64 |       88 |
| 4h_ema20_pullback|SL=3ATR|TP=3R|hold=720m               |                      7 |                      5 |                    12 | False                  |                -0.4265 |                 0.2558 |                      2.93215 |      228 |     97 |      131 |
| 4h_ema20_pullback|SL=3ATR|TP=2R|hold=720m               |                      7 |                      5 |                    12 | False                  |                -0.9175 |                 0.2558 |                      2.93215 |      228 |     97 |      131 |
| 1h_failed_break_followthrough|SL=1.5ATR|TP=3R|hold=720m |                      7 |                      3 |                    10 | False                  |                -2.1455 |               -12.9232 |                     19.603   |      397 |    164 |      233 |
| 1h_rsi2_reversal_confirm|SL=1.5ATR|TP=2R|hold=720m      |                      6 |                      3 |                     9 | False                  |                 7.4803 |               -11.7855 |                     12.0575  |      473 |    210 |      263 |
| 1h_strong_momentum|SL=3ATR|TP=2R|hold=720m              |                      6 |                      4 |                    10 | False                  |                 2.9916 |                -6.9533 |                     10.3068  |      544 |    242 |      302 |
| 1h_rsi2_reversal_confirm|SL=1.5ATR|TP=3R|hold=720m      |                      6 |                      2 |                     8 | False                  |                 2.7112 |                -8.7018 |                     11.8886  |      464 |    202 |      262 |

## Selected model's 2025 and 2026 monthly actual ETH-dollar risk
| model                                        | month_ist   |   trades |   winning_trades |   losing_trades |   flat_trades |   net_account_return_pct |   mean_initial_stop_eth_usd |   mean_initial_target_eth_usd |
|:---------------------------------------------|:------------|---------:|-----------------:|----------------:|--------------:|-------------------------:|----------------------------:|------------------------------:|
| 4h_strong_momentum|SL=1.5ATR|TP=3R|hold=240m | 2025-01     |        8 |                6 |               2 |             0 |                 0.386932 |                    112.457  |                      337.371  |
| 4h_strong_momentum|SL=1.5ATR|TP=3R|hold=240m | 2025-02     |        8 |                2 |               6 |             0 |                -0.754428 |                    104.411  |                      313.234  |
| 4h_strong_momentum|SL=1.5ATR|TP=3R|hold=240m | 2025-03     |        9 |                7 |               2 |             0 |                 0.582573 |                     77.1464 |                      231.439  |
| 4h_strong_momentum|SL=1.5ATR|TP=3R|hold=240m | 2025-04     |        9 |                3 |               6 |             0 |                 0.013427 |                     68.6893 |                      206.068  |
| 4h_strong_momentum|SL=1.5ATR|TP=3R|hold=240m | 2025-05     |       15 |                7 |               8 |             0 |                 0.673706 |                     82.9682 |                      248.905  |
| 4h_strong_momentum|SL=1.5ATR|TP=3R|hold=240m | 2025-06     |        8 |                2 |               6 |             0 |                 0.0768   |                     71.7844 |                      215.353  |
| 4h_strong_momentum|SL=1.5ATR|TP=3R|hold=240m | 2025-07     |       12 |                6 |               6 |             0 |                 0.723135 |                     88.8719 |                      266.616  |
| 4h_strong_momentum|SL=1.5ATR|TP=3R|hold=240m | 2025-08     |       14 |               10 |               4 |             0 |                 0.885039 |                    141.52   |                      424.56   |
| 4h_strong_momentum|SL=1.5ATR|TP=3R|hold=240m | 2025-09     |        7 |                4 |               3 |             0 |                 1.16651  |                     99.7898 |                      299.369  |
| 4h_strong_momentum|SL=1.5ATR|TP=3R|hold=240m | 2025-10     |       15 |               10 |               5 |             0 |                 0.174769 |                    146.885  |                      440.656  |
| 4h_strong_momentum|SL=1.5ATR|TP=3R|hold=240m | 2025-11     |       13 |                3 |              10 |             0 |                -1.14933  |                    128.051  |                      384.154  |
| 4h_strong_momentum|SL=1.5ATR|TP=3R|hold=240m | 2025-12     |       10 |                4 |               6 |             0 |                -0.594424 |                     93.3198 |                      279.959  |
| 4h_strong_momentum|SL=1.5ATR|TP=3R|hold=240m | 2026-01     |        6 |                5 |               1 |             0 |                 1.20154  |                     69.7446 |                      209.234  |
| 4h_strong_momentum|SL=1.5ATR|TP=3R|hold=240m | 2026-02     |       13 |                7 |               6 |             0 |                 1.04331  |                     85.2004 |                      255.601  |
| 4h_strong_momentum|SL=1.5ATR|TP=3R|hold=240m | 2026-03     |        7 |                2 |               5 |             0 |                -0.031815 |                     80.4842 |                      241.453  |
| 4h_strong_momentum|SL=1.5ATR|TP=3R|hold=240m | 2026-04     |        7 |                1 |               6 |             0 |                 0.008652 |                     64.1158 |                      192.347  |
| 4h_strong_momentum|SL=1.5ATR|TP=3R|hold=240m | 2026-05     |        6 |                0 |               6 |             0 |                -1.42928  |                     46.4973 |                      139.492  |
| 4h_strong_momentum|SL=1.5ATR|TP=3R|hold=240m | 2026-06     |       13 |                5 |               8 |             0 |                 0.531693 |                     50.2788 |                      150.837  |
| 4h_strong_momentum|SL=1.5ATR|TP=3R|hold=240m | 2026-07     |       10 |                2 |               8 |             0 |                -0.480052 |                     42.09   |                      126.27   |
| 4h_strong_momentum|SL=1.5ATR|TP=3R|hold=240m | 2026-08     |        8 |                2 |               6 |             0 |                -0.946566 |                     32.0491 |                       96.1473 |
| 4h_strong_momentum|SL=1.5ATR|TP=3R|hold=240m | 2026-09     |        9 |                2 |               7 |             0 |                -0.491293 |                     59.1018 |                      177.305  |
| 4h_strong_momentum|SL=1.5ATR|TP=3R|hold=240m | 2026-10     |        9 |                2 |               7 |             0 |                -1.40284  |                     54.675  |                      164.025  |

## Limitations
- ETHUSD source is native raw unscaled data with sha256 verified per partition
- No literal 200-point BTC stops, targets, or virtual BTC price units
- ATR/percent distances adapt natively to ETH price history; actual ETH USD stop/target shown in audit
- 0.02% slippage assumption is not measured spread, realized fill or market impact
- Funding, contract lot size, margin availability, liquidation and actual spread are NOT included
- One exclusive trade per model, returns compounded at monthly IST exit time
- 2026 is previously explored through BTC strategy research, not a pristine OOS sample
- Selection uses 2025 only, then reports 2026 without parameter alteration
- 2026 November excluded; full Jan25-Oct26 data all verified complete
