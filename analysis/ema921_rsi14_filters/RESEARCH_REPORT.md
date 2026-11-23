# BTCUSD EMA9/21 1H + 15M RSI14 filter experiment — 5M cross entry

## Results (Monday–Friday entries, 1m execution)
Same original 1H/15M/5M EMA9/21 trigger as baseline, only add a completed-candle RSI14 trend-strength gate on the 1H, 15M, or both. 
LONG RSI>=cutoff (50/55/60), SHORT RSI<=100-cutoff. For BOTH mode both must pass. 
Fixed exits independently 100/200 and 400/1200 BTC points. Next 1m open, one position, no trailing, stop-first if 1m ambiguous.

| case                      |   pre_overlap_signal_count |   trades |   wins |   losses |   win_rate_pct |   positive_months_22 |   return_2025_pct |   return_2026_JanOct_pct |   net_1x_account_pct |   max_closed_trade_drawdown_pct |   profit_factor_net_points |
|:--------------------------|---------------------------:|---------:|-------:|---------:|---------------:|---------------------:|------------------:|-------------------------:|---------------------:|--------------------------------:|---------------------------:|
| BOTH_60_SL100_TP200       |                        257 |      200 |     66 |      134 |          33.00 |                    0 |            -13.66 |                    -9.46 |               -21.82 |                           21.82 |                       0.21 |
| M15_60_ONLY_SL100_TP200   |                        342 |      260 |     77 |      183 |          29.62 |                    0 |            -19.11 |                   -12.85 |               -29.50 |                           29.50 |                       0.18 |
| H1_60_ONLY_SL100_TP200    |                        774 |      581 |    191 |      390 |          32.87 |                    0 |            -32.76 |                   -28.46 |               -51.89 |                           51.93 |                       0.21 |
| BOTH_55_SL100_TP200       |                        986 |      717 |    227 |      490 |          31.66 |                    0 |            -40.60 |                   -33.73 |               -60.63 |                           60.68 |                       0.19 |
| H1_50_M15_55_SL100_TP200  |                       1189 |      841 |    267 |      574 |          31.75 |                    0 |            -44.71 |                   -39.21 |               -66.39 |                           66.43 |                       0.20 |
| M15_55_ONLY_SL100_TP200   |                       1194 |      845 |    267 |      578 |          31.60 |                    0 |            -44.97 |                   -39.53 |               -66.73 |                           66.77 |                       0.19 |
| H1_55_ONLY_SL100_TP200    |                       1290 |      924 |    296 |      628 |          32.03 |                    0 |            -49.10 |                   -40.05 |               -69.48 |                           69.52 |                       0.20 |
| H1_55_M15_50_SL100_TP200  |                       1290 |      924 |    296 |      628 |          32.03 |                    0 |            -49.10 |                   -40.05 |               -69.48 |                           69.52 |                       0.20 |
| BOTH_50_SL100_TP200       |                       1633 |     1123 |    358 |      765 |          31.88 |                    0 |            -55.20 |                   -47.78 |               -76.61 |                           76.64 |                       0.20 |
| NO_RSI_SL100_TP200        |                       1643 |     1130 |    359 |      771 |          31.77 |                    0 |            -55.47 |                   -48.21 |               -76.94 |                           76.97 |                       0.20 |
| BOTH_60_SL400_TP1200      |                        257 |      172 |     46 |      126 |          26.74 |                    9 |            -11.93 |                    -3.72 |               -15.21 |                           20.87 |                       0.78 |
| H1_60_ONLY_SL400_TP1200   |                        774 |      419 |    118 |      301 |          28.16 |                    8 |            -13.81 |                   -14.93 |               -26.67 |                           34.53 |                       0.84 |
| M15_60_ONLY_SL400_TP1200  |                        342 |      227 |     56 |      171 |          24.67 |                    8 |            -19.53 |                    -8.31 |               -26.22 |                           30.44 |                       0.70 |
| BOTH_55_SL400_TP1200      |                        986 |      538 |    143 |      395 |          26.58 |                    4 |            -27.91 |                   -19.47 |               -41.95 |                           46.59 |                       0.77 |
| H1_55_ONLY_SL400_TP1200   |                       1290 |      633 |    171 |      462 |          27.01 |                    6 |            -30.70 |                   -19.52 |               -44.23 |                           48.46 |                       0.78 |
| H1_55_M15_50_SL400_TP1200 |                       1290 |      633 |    171 |      462 |          27.01 |                    6 |            -30.70 |                   -19.52 |               -44.23 |                           48.46 |                       0.78 |
| H1_50_M15_55_SL400_TP1200 |                       1189 |      630 |    166 |      464 |          26.35 |                    6 |            -33.08 |                   -21.55 |               -47.50 |                           53.94 |                       0.76 |
| M15_55_ONLY_SL400_TP1200  |                       1194 |      633 |    166 |      467 |          26.22 |                    6 |            -33.84 |                   -22.10 |               -48.46 |                           54.78 |                       0.75 |
| BOTH_50_SL400_TP1200      |                       1633 |      767 |    206 |      561 |          26.86 |                    7 |            -36.82 |                   -22.22 |               -50.86 |                           55.46 |                       0.78 |
| NO_RSI_SL400_TP1200       |                       1643 |      773 |    208 |      565 |          26.91 |                    7 |            -37.20 |                   -21.42 |               -50.65 |                           55.27 |                       0.78 |

## RSI filter signal counts before weekday/position overlap exclusions
| filter       |   rsi_period |   1h_bullish_min |   1h_bearish_max |   15m_bullish_min |   15m_bearish_max |   candidate_signals_all_days |   candidate_long |   candidate_short |
|:-------------|-------------:|-----------------:|-----------------:|------------------:|------------------:|-----------------------------:|-----------------:|------------------:|
| NO_RSI       |           14 |              nan |              nan |               nan |               nan |                         1643 |              827 |               816 |
| BOTH_50      |           14 |               50 |               50 |                50 |                50 |                         1633 |              821 |               812 |
| BOTH_55      |           14 |               55 |               45 |                55 |                45 |                          986 |              512 |               474 |
| BOTH_60      |           14 |               60 |               40 |                60 |                40 |                          257 |              128 |               129 |
| H1_55_ONLY   |           14 |               55 |               45 |               nan |               nan |                         1290 |              652 |               638 |
| M15_55_ONLY  |           14 |              nan |              nan |                55 |                45 |                         1194 |              621 |               573 |
| H1_60_ONLY   |           14 |               60 |               40 |               nan |               nan |                          774 |              377 |               397 |
| M15_60_ONLY  |           14 |              nan |              nan |                60 |                40 |                          342 |              174 |               168 |
| H1_55_M15_50 |           14 |               55 |               45 |                50 |                50 |                         1290 |              652 |               638 |
| H1_50_M15_55 |           14 |               50 |               50 |                55 |                45 |                         1189 |              617 |               572 |

## Monthly net 1x account returns for no RSI vs both-timeframe 50/55/60
| month_ist   |   BOTH_50_SL100_TP200 |   BOTH_50_SL400_TP1200 |   BOTH_55_SL100_TP200 |   BOTH_55_SL400_TP1200 |   BOTH_60_SL100_TP200 |   BOTH_60_SL400_TP1200 |   NO_RSI_SL100_TP200 |   NO_RSI_SL400_TP1200 |
|:------------|----------------------:|-----------------------:|----------------------:|-----------------------:|----------------------:|-----------------------:|---------------------:|----------------------:|
| 2025-01     |                 -8.25 |                   0.26 |                 -6.72 |                  -0.41 |                 -2.16 |                  -1.98 |                -8.25 |                  0.26 |
| 2025-02     |                 -5.41 |                  -8.92 |                 -2.54 |                  -6.96 |                 -1.16 |                  -4.43 |                -5.64 |                 -9.46 |
| 2025-03     |                 -5.69 |                   3.60 |                 -3.59 |                  -1.16 |                 -0.26 |                   0.17 |                -5.69 |                  3.60 |
| 2025-04     |                 -5.15 |                  -5.26 |                 -2.61 |                  -2.21 |                 -1.18 |                  -2.29 |                -5.15 |                 -5.26 |
| 2025-05     |                 -7.27 |                  -1.58 |                 -4.02 |                  -0.05 |                 -1.25 |                   0.75 |                -7.48 |                 -2.12 |
| 2025-06     |                 -3.81 |                  -5.79 |                 -2.64 |                  -2.91 |                 -0.95 |                  -0.07 |                -3.75 |                 -4.83 |
| 2025-07     |                 -6.41 |                  -6.35 |                 -4.77 |                  -7.70 |                 -1.61 |                  -1.46 |                -6.41 |                 -6.35 |
| 2025-08     |                 -5.90 |                  -6.60 |                 -4.26 |                  -3.48 |                 -1.67 |                  -2.91 |                -5.90 |                 -6.60 |
| 2025-09     |                -10.43 |                  -5.79 |                 -6.59 |                  -3.45 |                 -1.57 |                  -1.45 |               -10.61 |                 -6.24 |
| 2025-10     |                 -7.78 |                  -1.67 |                 -5.55 |                  -1.73 |                 -0.88 |                   0.88 |                -7.78 |                 -1.67 |
| 2025-11     |                 -5.13 |                   0.69 |                 -3.22 |                   1.79 |                 -1.22 |                   0.75 |                -5.13 |                  0.69 |
| 2025-12     |                 -6.26 |                  -6.81 |                 -4.33 |                  -3.62 |                 -0.66 |                  -0.43 |                -6.26 |                 -6.81 |
| 2026-01     |                 -6.46 |                   0.69 |                 -3.54 |                   2.21 |                 -0.97 |                  -1.07 |                -6.46 |                  0.69 |
| 2026-02     |                 -8.02 |                  -2.73 |                 -4.98 |                  -6.04 |                 -1.07 |                  -0.33 |                -8.52 |                 -1.73 |
| 2026-03     |                 -6.94 |                   0.31 |                 -4.96 |                  -2.50 |                 -1.13 |                  -1.88 |                -6.94 |                  0.31 |
| 2026-04     |                 -5.34 |                  -9.52 |                 -2.29 |                  -1.77 |                 -0.47 |                   2.56 |                -5.59 |                 -9.52 |
| 2026-05     |                 -6.06 |                  -6.01 |                 -4.15 |                  -4.99 |                 -0.99 |                   0.35 |                -6.06 |                 -6.01 |
| 2026-06     |                 -6.55 |                   5.57 |                 -3.49 |                   5.01 |                 -0.61 |                   0.58 |                -6.55 |                  5.57 |
| 2026-07     |                 -4.40 |                  -7.71 |                 -2.97 |                  -9.38 |                 -0.67 |                  -6.37 |                -4.40 |                 -7.71 |
| 2026-08     |                 -7.06 |                  -1.96 |                 -5.07 |                  -2.14 |                 -1.38 |                  -1.71 |                -7.06 |                 -1.96 |
| 2026-09     |                 -7.47 |                  -3.43 |                 -5.00 |                  -1.83 |                 -1.73 |                   0.91 |                -7.47 |                 -3.43 |
| 2026-10     |                 -4.54 |                   0.92 |                 -3.81 |                   0.79 |                 -0.86 |                   3.50 |                -4.54 |                  0.92 |

## Methodology / cautions
- Original 1m candles: 992,160, gaps 0.
- January 2025 IST starts 330 minutes after month start. November 2026 incomplete and excluded.
- 2025 and Jan-Oct 2026 already researched. This is not blind out-of-sample evidence; parameter comparisons are multiple tests.
- True Wilder RSI(14) (SMA-seeded RMA), computed only on the latest completed 1H / 15M bars.
- Entry filter on Monday–Friday IST, existing positions may exit on weekends.
- Gross-to-net: 0.05% taker per side + GST18% on fees and $5 adverse price slippage per side.
- Stops/targets measured from post-slip entry, stop-first 1m tie, gap-stop on the next available 1m open.
- IST month-end flat, no timeout/trailing/EMA exit. Max DD measured at closes only (understates intratrade DD).
- Account 1x notional per trade with compounded returns, no funding, actual bid/ask spread, liquidation/margin.
- Baseline 100/200=1130 trades/359 wins; 400/1200=773 trades/208 wins: parity PASSED.
- RSI filter changes how many signals remain; trades can increase due to removal of longer overlapping positions.

## Files
- NOVELTY_CHECK.md, summary.csv, monthly_results.csv, signal_filter_counts.csv, trade_ledger.csv, quality.json.
