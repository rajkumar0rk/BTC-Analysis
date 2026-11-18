# BTCUSD + ETHUSD: two-hour failed breakout reversal

Independent, causal paired-market strategy study.
Selection uses 2025 only; 2026 is previously exposed and not blind out of sample.

## 2025-only selection
| model                                    |   train_2025_positive_months |   train_2025_net_return_sum_pct |   train_2025_pf_min |
|:-----------------------------------------|-----------------------------:|--------------------------------:|--------------------:|
| two_hour_failed_breakout__SL1.5_RR2_H720 |                           13 |                        8.39749  |            1.05497  |
| two_hour_failed_breakout__SL2.5_RR2_H720 |                           12 |                       -0.759825 |            0.981122 |
| two_hour_failed_breakout__SL2.5_RR3_H720 |                           11 |                        2.22566  |            1.02918  |
| two_hour_failed_breakout__SL1.5_RR3_H720 |                           11 |                        0.919365 |            0.948    |
| two_hour_failed_breakout__SL1.5_RR2_H360 |                            9 |                       -6.23046  |            0.848857 |
| two_hour_failed_breakout__SL2.5_RR3_H360 |                            9 |                       -6.76635  |            0.792713 |
| two_hour_failed_breakout__SL2.5_RR2_H360 |                            9 |                       -9.35141  |            0.77485  |
| two_hour_failed_breakout__SL1.5_RR3_H360 |                            8 |                      -11.8846   |            0.746945 |

## Selected model, both markets
| market   | model                                    |   profit_factor |   total_positive_trade_pnl_usd |   total_losing_trade_pnl_abs_usd |   total_net_pnl_usd |   net_return_pct |   net_return_2025_pct |   net_return_2026_pct |   profit_factor_2025 |   profit_factor_2026 |   trades |   wins |   losses |   win_rate_pct |   positive_months |   loss_months |   zero_trade_months |   strong_months_pf_ge_1p5_positive_min3trades |   strong_months_2025 |   strong_months_2026 |   positive_months_2025 |   positive_months_2026 |   trades_2025 |   trades_2026 |   max_closed_trade_drawdown_pct |   worst_month_pct |
|:---------|:-----------------------------------------|----------------:|-------------------------------:|---------------------------------:|--------------------:|-----------------:|----------------------:|----------------------:|---------------------:|---------------------:|---------:|-------:|---------:|---------------:|------------------:|--------------:|--------------------:|----------------------------------------------:|---------------------:|---------------------:|-----------------------:|-----------------------:|--------------:|--------------:|--------------------------------:|------------------:|
| BTCUSD   | two_hour_failed_breakout__SL1.5_RR2_H720 |        0.92104  |                        876.244 |                          951.364 |            -75.1194 |         -7.51194 |               2.78032 |              -10.0138 |              1.05497 |             0.768999 |      349 |    155 |      194 |        44.4126 |                11 |            11 |                   0 |                                             6 |                    4 |                    2 |                      6 |                      5 |           194 |           155 |                        -13.0525 |          -6.33403 |
| ETHUSD   | two_hour_failed_breakout__SL1.5_RR2_H720 |        0.906507 |                        847.52  |                          934.929 |            -87.4094 |         -8.74094 |               5.61718 |              -13.5945 |              1.1144  |             0.676556 |      336 |    140 |      196 |        41.6667 |                 9 |            13 |                   0 |                                             3 |                    3 |                    0 |                      7 |                      2 |           191 |           145 |                        -14.9787 |          -3.98354 |

## 22 monthly net returns and profit factors
| market   | model                                    | month   |   net_return_pct |   profit_factor |   trades |   wins |   losses |   winning_net_pnl_usd |   losing_net_pnl_abs_usd |   net_pnl_usd |   equity_start_usd |   equity_end_usd |
|:---------|:-----------------------------------------|:--------|-----------------:|----------------:|---------:|-------:|---------:|----------------------:|-------------------------:|--------------:|-------------------:|-----------------:|
| BTCUSD   | two_hour_failed_breakout__SL1.5_RR2_H720 | 2025-01 |        -0.327647 |        0.912336 |       13 |      6 |        7 |              34.0987  |                 37.3752  |      -3.27647 |           1000     |          996.724 |
| BTCUSD   | two_hour_failed_breakout__SL1.5_RR2_H720 | 2025-02 |         1.41417  |        1.44567  |       12 |      5 |        7 |              45.7225  |                 31.6271  |      14.0953  |            996.724 |         1010.82  |
| BTCUSD   | two_hour_failed_breakout__SL1.5_RR2_H720 | 2025-03 |        -6.33403  |        0.212866 |       20 |      6 |       14 |              17.3146  |                 81.3401  |     -64.0255  |           1010.82  |          946.793 |
| BTCUSD   | two_hour_failed_breakout__SL1.5_RR2_H720 | 2025-04 |        -0.444659 |        0.878887 |       14 |      7 |        7 |              30.5508  |                 34.7608  |      -4.21    |            946.793 |          942.583 |
| BTCUSD   | two_hour_failed_breakout__SL1.5_RR2_H720 | 2025-05 |        -0.303523 |        0.936634 |       16 |      6 |       10 |              42.2885  |                 45.1495  |      -2.86096 |            942.583 |          939.722 |
| BTCUSD   | two_hour_failed_breakout__SL1.5_RR2_H720 | 2025-06 |         3.86129  |        2.0583   |       17 |      9 |        8 |              70.5718  |                 34.2864  |      36.2854  |            939.722 |          976.008 |
| BTCUSD   | two_hour_failed_breakout__SL1.5_RR2_H720 | 2025-07 |        -1.16211  |        0.790106 |       20 |     10 |       10 |              42.6958  |                 54.0381  |     -11.3423  |            976.008 |          964.666 |
| BTCUSD   | two_hour_failed_breakout__SL1.5_RR2_H720 | 2025-08 |         2.82551  |        1.86289  |       19 |     12 |        7 |              58.8446  |                 31.5879  |      27.2567  |            964.666 |          991.922 |
| BTCUSD   | two_hour_failed_breakout__SL1.5_RR2_H720 | 2025-09 |         0.906341 |        1.17831  |       17 |      9 |        8 |              59.4103  |                 50.4201  |       8.9902  |            991.922 |         1000.91  |
| BTCUSD   | two_hour_failed_breakout__SL1.5_RR2_H720 | 2025-10 |        -2.42011  |        0.566006 |       17 |      6 |       11 |              31.5914  |                 55.8145  |     -24.2231  |           1000.91  |          976.689 |
| BTCUSD   | two_hour_failed_breakout__SL1.5_RR2_H720 | 2025-11 |         2.7395   |        1.64097  |       20 |     11 |        9 |              68.4999  |                 41.7436  |      26.7564  |            976.689 |         1003.45  |
| BTCUSD   | two_hour_failed_breakout__SL1.5_RR2_H720 | 2025-12 |         2.42739  |        4.17591  |        9 |      6 |        3 |              32.027   |                  7.66947 |      24.3575  |           1003.45  |         1027.8   |
| BTCUSD   | two_hour_failed_breakout__SL1.5_RR2_H720 | 2026-01 |        -3.80871  |        0.314009 |       15 |      5 |       10 |              17.919   |                 57.065   |     -39.1461  |           1027.8   |          988.657 |
| BTCUSD   | two_hour_failed_breakout__SL1.5_RR2_H720 | 2026-02 |         3.21789  |        2.26072  |       13 |      7 |        6 |              57.0485  |                 25.2347  |      31.8139  |            988.657 |         1020.47  |
| BTCUSD   | two_hour_failed_breakout__SL1.5_RR2_H720 | 2026-03 |        -5.83807  |        0.161556 |       19 |      2 |       17 |              11.4794  |                 71.0552  |     -59.5758  |           1020.47  |          960.895 |
| BTCUSD   | two_hour_failed_breakout__SL1.5_RR2_H720 | 2026-04 |         3.16041  |        2.3677   |       13 |      9 |        4 |              52.5721  |                 22.2039  |      30.3682  |            960.895 |          991.263 |
| BTCUSD   | two_hour_failed_breakout__SL1.5_RR2_H720 | 2026-05 |         0.534283 |        1.18994  |       13 |      7 |        6 |              33.1792  |                 27.8831  |       5.29615 |            991.263 |          996.56  |
| BTCUSD   | two_hour_failed_breakout__SL1.5_RR2_H720 | 2026-06 |        -4.98497  |        0.409085 |       23 |      6 |       17 |              34.3917  |                 84.0699  |     -49.6782  |            996.56  |          946.881 |
| BTCUSD   | two_hour_failed_breakout__SL1.5_RR2_H720 | 2026-07 |        -2.23269  |        0.496121 |       11 |      3 |        8 |              20.8154  |                 41.9563  |     -21.1409  |            946.881 |          925.74  |
| BTCUSD   | two_hour_failed_breakout__SL1.5_RR2_H720 | 2026-08 |         0.584571 |        1.24229  |       13 |      6 |        7 |              27.7465  |                 22.3349  |       5.41161 |            925.74  |          931.152 |
| BTCUSD   | two_hour_failed_breakout__SL1.5_RR2_H720 | 2026-09 |        -0.961575 |        0.829945 |       19 |      8 |       11 |              43.6984  |                 52.6521  |      -8.95373 |            931.152 |          922.198 |
| BTCUSD   | two_hour_failed_breakout__SL1.5_RR2_H720 | 2026-10 |         0.290848 |        1.06527  |       16 |      9 |        7 |              43.7782  |                 41.096   |       2.68219 |            922.198 |          924.881 |
| ETHUSD   | two_hour_failed_breakout__SL1.5_RR2_H720 | 2025-01 |         2.04107  |        1.57848  |       16 |      8 |        8 |              55.6943  |                 35.2836  |      20.4107  |           1000     |         1020.41  |
| ETHUSD   | two_hour_failed_breakout__SL1.5_RR2_H720 | 2025-02 |        -1.61834  |        0.662272 |       15 |      6 |        9 |              32.3829  |                 48.8966  |     -16.5137  |           1020.41  |         1003.9   |
| ETHUSD   | two_hour_failed_breakout__SL1.5_RR2_H720 | 2025-03 |         3.37502  |        2.69425  |       12 |      8 |        4 |              53.8798  |                 19.9981  |      33.8817  |           1003.9   |         1037.78  |
| ETHUSD   | two_hour_failed_breakout__SL1.5_RR2_H720 | 2025-04 |        -0.390505 |        0.834648 |       10 |      4 |        6 |              20.4563  |                 24.5089  |      -4.05258 |           1037.78  |         1033.73  |
| ETHUSD   | two_hour_failed_breakout__SL1.5_RR2_H720 | 2025-05 |        -0.758108 |        0.771883 |       12 |      5 |        7 |              26.5173  |                 34.354   |      -7.83676 |           1033.73  |         1025.89  |
| ETHUSD   | two_hour_failed_breakout__SL1.5_RR2_H720 | 2025-06 |         0.956411 |        1.20146  |       18 |      8 |       10 |              58.5158  |                 48.7041  |       9.81171 |           1025.89  |         1035.7   |
| ETHUSD   | two_hour_failed_breakout__SL1.5_RR2_H720 | 2025-07 |        -0.292067 |        0.9454   |       21 |      9 |       12 |              52.3771  |                 55.402   |      -3.02494 |           1035.7   |         1032.68  |
| ETHUSD   | two_hour_failed_breakout__SL1.5_RR2_H720 | 2025-08 |        -3.98354  |        0.361342 |       19 |      4 |       15 |              23.2746  |                 64.4117  |     -41.137   |           1032.68  |          991.539 |
| ETHUSD   | two_hour_failed_breakout__SL1.5_RR2_H720 | 2025-09 |         0.447997 |        1.08628  |       19 |      9 |       10 |              55.9273  |                 51.4852  |       4.44207 |            991.539 |          995.981 |
| ETHUSD   | two_hour_failed_breakout__SL1.5_RR2_H720 | 2025-10 |         1.43775  |        1.32696  |       20 |     10 |       10 |              58.1161  |                 43.7963  |      14.3197  |            995.981 |         1010.3   |
| ETHUSD   | two_hour_failed_breakout__SL1.5_RR2_H720 | 2025-11 |         3.34718  |        2.20954  |       15 |      8 |        7 |              61.7748  |                 27.9582  |      33.8166  |           1010.3   |         1044.12  |
| ETHUSD   | two_hour_failed_breakout__SL1.5_RR2_H720 | 2025-12 |         1.1545   |        1.33283  |       14 |      7 |        7 |              48.2715  |                 36.2173  |      12.0543  |           1044.12  |         1056.17  |
| ETHUSD   | two_hour_failed_breakout__SL1.5_RR2_H720 | 2026-01 |         0.261623 |        1.06587  |       14 |      7 |        7 |              44.7108  |                 41.9476  |       2.76318 |           1056.17  |         1058.93  |
| ETHUSD   | two_hour_failed_breakout__SL1.5_RR2_H720 | 2026-02 |        -2.51419  |        0.410245 |       13 |      5 |        8 |              18.52    |                 45.1437  |     -26.6237  |           1058.93  |         1032.31  |
| ETHUSD   | two_hour_failed_breakout__SL1.5_RR2_H720 | 2026-03 |        -2.4774   |        0.531176 |       15 |      4 |       11 |              28.9758  |                 54.5502  |     -25.5745  |           1032.31  |         1006.74  |
| ETHUSD   | two_hour_failed_breakout__SL1.5_RR2_H720 | 2026-04 |        -2.32885  |        0.437064 |       12 |      3 |        9 |              18.203   |                 41.6484  |     -23.4454  |           1006.74  |          983.291 |
| ETHUSD   | two_hour_failed_breakout__SL1.5_RR2_H720 | 2026-05 |         0.297052 |        1.07823  |       16 |      8 |        8 |              40.2574  |                 37.3365  |       2.92088 |            983.291 |          986.212 |
| ETHUSD   | two_hour_failed_breakout__SL1.5_RR2_H720 | 2026-06 |        -3.34338  |        0.13642  |       14 |      3 |       11 |               5.20873 |                 38.1816  |     -32.9728  |            986.212 |          953.239 |
| ETHUSD   | two_hour_failed_breakout__SL1.5_RR2_H720 | 2026-07 |        -0.613654 |        0.891737 |       17 |      7 |       10 |              48.1815  |                 54.0311  |      -5.8496  |            953.239 |          947.39  |
| ETHUSD   | two_hour_failed_breakout__SL1.5_RR2_H720 | 2026-08 |        -0.433517 |        0.869558 |       13 |      7 |        6 |              27.3788  |                 31.4859  |      -4.1071  |            947.39  |          943.283 |
| ETHUSD   | two_hour_failed_breakout__SL1.5_RR2_H720 | 2026-09 |        -2.24378  |        0.628481 |       18 |      6 |       12 |              35.8041  |                 56.9693  |     -21.1652  |            943.283 |          922.118 |
| ETHUSD   | two_hour_failed_breakout__SL1.5_RR2_H720 | 2026-10 |        -1.03316  |        0.77646  |       13 |      4 |        9 |              33.0918  |                 42.6188  |      -9.52699 |            922.118 |          912.591 |

## Quality
{
  "selected_model": "two_hour_failed_breakout__SL1.5_RR2_H720",
  "criteria": "2025-only combined market ranking: number of positive months, then combined net account return, then minimum PF",
  "models_per_market": 8,
  "months": 22,
  "markets": [
    "BTCUSD",
    "ETHUSD"
  ],
  "signals": "Two completed 1h bars: breakout of previous 12h range, then close back inside; reverse at next 1m open",
  "entry_timing": "1h bars right-labelled; entry at next 1m OPEN after B completed",
  "stop_first_gap_aware": true,
  "risk_fraction": 0.005,
  "max_notional_leverage": 3.0,
  "fee_per_side_with_GST": 0.00059,
  "btc_slippage_points_per_side": 5.0,
  "eth_slippage_fraction_per_side": 0.0002,
  "data": "Native manifest-hash verified original 1m BTCUSD and ETHUSD",
  "incomplete": "Jan 2025 IST first 5.5h absent because data begins Jan1 UTC; Nov2026 excluded",
  "caveats": [
    "2026 previously examined; not independent OOS",
    "No actual spread, funding, market impact, margin, liquidation or discrete lot sizes",
    "Trade-close drawdown underestimates intratrade drawdown",
    "Historical backtests are not forward profitability proof"
  ]
}
