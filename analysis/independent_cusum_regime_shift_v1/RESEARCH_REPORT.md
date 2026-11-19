# Independent CUSUM directional drift-change paired BTC ETH audit

PARTIAL OVERLAP differential: 1H mean-adjusted one-sided cumulative normalized-return excursions, continuation/fade at next 1m open, 1m stop-first 1.5 ATR SL, 2.5R TP, 12h maximum hold.
Same 8 variants on BTC and ETH; 2025-only joint selection and 2026 fixed historical check.
All USD PnL and account monthly NAV include modeled taker fees, GST and adverse slippage.
Monthly profit factor is exit-month net-trade PF; monthly return is account month-end marked NAV including open position; they differ around boundaries.

## Selected identical model on both assets (2025-only combined ranking)

| market   | model                 |   kappa |   threshold | direction    |   slippage_multiplier |   profit_factor |   net_return_22m_pct |   net_return_2025_pct |   net_return_2026_jan_oct_pct | year2025_above_500pct   | year2026_ytd_above_500pct   |   strong_pf1p5_return5_months |   strong_pf1p5_return10_months |   positive_months |   trades |   wins |   losses |   max_monthend_nav_drawdown_pct |   worst_month_pct |
|:---------|:----------------------|--------:|------------:|:-------------|----------------------:|----------------:|---------------------:|----------------------:|------------------------------:|:------------------------|:----------------------------|------------------------------:|-------------------------------:|------------------:|---------:|-------:|---------:|--------------------------------:|------------------:|
| BTCUSD   | cusum_k0.40_h3.5_cont |     0.4 |         3.5 | continuation |                     1 |        0.849581 |             -18.1634 |              -11.4825 |                      -7.5476  | False                   | False                       |                             0 |                              0 |                 8 |      449 |    180 |      269 |                        -20.2412 |          -7.05963 |
| ETHUSD   | cusum_k0.40_h3.5_cont |     0.4 |         3.5 | continuation |                     1 |        1.09607  |              14.1585 |               23.7351 |                      -7.73953 | False                   | False                       |                             1 |                              0 |                13 |      447 |    189 |      258 |                        -11.9902 |          -4.18481 |

## All 22 months, selected model, both native assets side by side

| market   | model                 | month   |   profit_factor |   net_return_pct |   net_exit_pnl_usd |   month_nav_change_usd |   trades |   wins |   losses |   nav_start_usd |   nav_end_usd |   open_positions_at_month_end |
|:---------|:----------------------|:--------|----------------:|-----------------:|-------------------:|-----------------------:|---------:|-------:|---------:|----------------:|--------------:|------------------------------:|
| BTCUSD   | cusum_k0.40_h3.5_cont | 2025-01 |        1.48416  |        2.60501   |          26.0501   |              26.0501   |       19 |      9 |       10 |        1000     |      1026.05  |                             0 |
| BTCUSD   | cusum_k0.40_h3.5_cont | 2025-02 |        0.635602 |       -2.31403   |         -27.1598   |             -23.7431   |       22 |      8 |       14 |        1026.05  |      1002.31  |                             1 |
| BTCUSD   | cusum_k0.40_h3.5_cont | 2025-03 |        0.809101 |       -1.70102   |         -13.6327   |             -17.0495   |       23 |      9 |       14 |        1002.31  |       985.258 |                             0 |
| BTCUSD   | cusum_k0.40_h3.5_cont | 2025-04 |        1.1717   |        0.81014   |           7.98196  |               7.98196  |       17 |      8 |        9 |         985.258 |       993.24  |                             0 |
| BTCUSD   | cusum_k0.40_h3.5_cont | 2025-05 |        0.415202 |       -3.91017   |         -38.8374   |             -38.8374   |       19 |      7 |       12 |         993.24  |       954.402 |                             0 |
| BTCUSD   | cusum_k0.40_h3.5_cont | 2025-06 |        1.14249  |        0.957888  |           8.03653  |               9.1421   |       21 |      8 |       13 |         954.402 |       963.544 |                             1 |
| BTCUSD   | cusum_k0.40_h3.5_cont | 2025-07 |        0.283166 |       -6.22607   |         -58.8854   |             -59.9909   |       22 |      6 |       16 |         963.544 |       903.553 |                             0 |
| BTCUSD   | cusum_k0.40_h3.5_cont | 2025-08 |        0.891928 |       -0.555713  |          -5.02116  |              -5.02116  |       18 |      8 |       10 |         903.553 |       898.532 |                             0 |
| BTCUSD   | cusum_k0.40_h3.5_cont | 2025-09 |        0.314295 |       -7.05963   |         -63.433    |             -63.433    |       26 |      6 |       20 |         898.532 |       835.099 |                             0 |
| BTCUSD   | cusum_k0.40_h3.5_cont | 2025-10 |        1.43629  |        2.14966   |          17.9518   |              17.9518   |       23 |     12 |       11 |         835.099 |       853.051 |                             0 |
| BTCUSD   | cusum_k0.40_h3.5_cont | 2025-11 |        2.70604  |        4.21111   |          35.9229   |              35.9229   |       17 |      8 |        9 |         853.051 |       888.974 |                             0 |
| BTCUSD   | cusum_k0.40_h3.5_cont | 2025-12 |        0.958596 |       -0.427312  |          -2.8052   |              -3.79869  |       25 |     12 |       13 |         888.974 |       885.175 |                             1 |
| BTCUSD   | cusum_k0.40_h3.5_cont | 2026-01 |        0.611321 |       -2.11909   |         -20.9819   |             -18.7576   |       19 |      4 |       15 |         885.175 |       866.417 |                             1 |
| BTCUSD   | cusum_k0.40_h3.5_cont | 2026-02 |        0.832401 |       -0.859446  |          -6.21563  |              -7.44639  |       17 |      8 |        9 |         866.417 |       858.971 |                             0 |
| BTCUSD   | cusum_k0.40_h3.5_cont | 2026-03 |        1.68113  |        3.17479   |          27.2705   |              27.2705   |       21 |     12 |        9 |         858.971 |       886.242 |                             0 |
| BTCUSD   | cusum_k0.40_h3.5_cont | 2026-04 |        2.61293  |        2.88228   |          25.544    |              25.544    |       15 |      7 |        8 |         886.242 |       911.786 |                             0 |
| BTCUSD   | cusum_k0.40_h3.5_cont | 2026-05 |        0.55407  |       -3.25105   |         -29.6427   |             -29.6427   |       22 |      9 |       13 |         911.786 |       882.143 |                             0 |
| BTCUSD   | cusum_k0.40_h3.5_cont | 2026-06 |        0.513356 |       -3.93474   |         -34.71     |             -34.71     |       23 |      7 |       16 |         882.143 |       847.433 |                             0 |
| BTCUSD   | cusum_k0.40_h3.5_cont | 2026-07 |        1.23638  |        0.822794  |           6.97263  |               6.97263  |       13 |      5 |        8 |         847.433 |       854.406 |                             0 |
| BTCUSD   | cusum_k0.40_h3.5_cont | 2026-08 |        0.607733 |       -3.06551   |         -26.1919   |             -26.1919   |       22 |      8 |       14 |         854.406 |       828.214 |                             0 |
| BTCUSD   | cusum_k0.40_h3.5_cont | 2026-09 |        1.01088  |       -0.0581725 |           0.550965 |              -0.481792 |       23 |     10 |       13 |         828.214 |       827.732 |                             1 |
| BTCUSD   | cusum_k0.40_h3.5_cont | 2026-10 |        0.813469 |       -1.13155   |         -10.399    |              -9.36624  |       22 |      9 |       13 |         827.732 |       818.366 |                             0 |
| ETHUSD   | cusum_k0.40_h3.5_cont | 2025-01 |        4.1543   |        8.99014   |          89.265    |              89.9014   |       18 |     13 |        5 |        1000     |      1089.9   |                             1 |
| ETHUSD   | cusum_k0.40_h3.5_cont | 2025-02 |        1.57937  |        2.46567   |          28.653    |              26.8734   |       18 |      9 |        9 |        1089.9   |      1116.77  |                             1 |
| ETHUSD   | cusum_k0.40_h3.5_cont | 2025-03 |        1.29343  |        1.68014   |          17.6202   |              18.7633   |       21 |     11 |       10 |        1116.77  |      1135.54  |                             0 |
| ETHUSD   | cusum_k0.40_h3.5_cont | 2025-04 |        1.90488  |        3.59346   |          42.8867   |              40.8051   |       20 |     10 |       10 |        1135.54  |      1176.34  |                             1 |
| ETHUSD   | cusum_k0.40_h3.5_cont | 2025-05 |        1.22871  |        1.53425   |          15.9664   |              18.048    |       22 |      8 |       14 |        1176.34  |      1194.39  |                             0 |
| ETHUSD   | cusum_k0.40_h3.5_cont | 2025-06 |        1.39377  |        2.30093   |          27.4821   |              27.4821   |       22 |     10 |       12 |        1194.39  |      1221.87  |                             0 |
| ETHUSD   | cusum_k0.40_h3.5_cont | 2025-07 |        0.579411 |       -2.42855   |         -29.6738   |             -29.6738   |       18 |      6 |       12 |        1221.87  |      1192.2   |                             0 |
| ETHUSD   | cusum_k0.40_h3.5_cont | 2025-08 |        1.41869  |        1.93847   |          23.1105   |              23.1105   |       19 |      6 |       13 |        1192.2   |      1215.31  |                             0 |
| ETHUSD   | cusum_k0.40_h3.5_cont | 2025-09 |        1.17709  |        0.775445  |           9.42405  |               9.42405  |       19 |      8 |       11 |        1215.31  |      1224.73  |                             0 |
| ETHUSD   | cusum_k0.40_h3.5_cont | 2025-10 |        2.0383   |        4.00444   |          49.0437   |              49.0437   |       20 |      9 |       11 |        1224.73  |      1273.78  |                             0 |
| ETHUSD   | cusum_k0.40_h3.5_cont | 2025-11 |        0.847496 |       -0.844157  |         -10.7527   |             -10.7527   |       20 |      7 |       13 |        1273.78  |      1263.03  |                             0 |
| ETHUSD   | cusum_k0.40_h3.5_cont | 2025-12 |        0.764083 |       -2.03278   |         -25.6745   |             -25.6745   |       26 |     10 |       16 |        1263.03  |      1237.35  |                             0 |
| ETHUSD   | cusum_k0.40_h3.5_cont | 2026-01 |        0.934984 |       -0.455271  |          -5.73143  |              -5.6333   |       23 |      8 |       15 |        1237.35  |      1231.72  |                             1 |
| ETHUSD   | cusum_k0.40_h3.5_cont | 2026-02 |        1.12171  |        0.588865  |           7.35127  |               7.25315  |       19 |      9 |       10 |        1231.72  |      1238.97  |                             0 |
| ETHUSD   | cusum_k0.40_h3.5_cont | 2026-03 |        1.26376  |        1.24345   |          15.406    |              15.406    |       21 |     11 |       10 |        1238.97  |      1254.38  |                             0 |
| ETHUSD   | cusum_k0.40_h3.5_cont | 2026-04 |        2.31045  |        3.40691   |          42.7355   |              42.7355   |       17 |     12 |        5 |        1254.38  |      1297.11  |                             0 |
| ETHUSD   | cusum_k0.40_h3.5_cont | 2026-05 |        0.432552 |       -4.18481   |         -54.2816   |             -54.2816   |       21 |      7 |       14 |        1297.11  |      1242.83  |                             0 |
| ETHUSD   | cusum_k0.40_h3.5_cont | 2026-06 |        0.725714 |       -2.33127   |         -28.9738   |             -28.9738   |       25 |      7 |       18 |        1242.83  |      1213.86  |                             0 |
| ETHUSD   | cusum_k0.40_h3.5_cont | 2026-07 |        0.91114  |       -0.36043   |          -4.3751   |              -4.3751   |       16 |      7 |        9 |        1213.86  |      1209.48  |                             0 |
| ETHUSD   | cusum_k0.40_h3.5_cont | 2026-08 |        1.14168  |        0.764642  |           9.2482   |               9.2482   |       18 |      9 |        9 |        1209.48  |      1218.73  |                             0 |
| ETHUSD   | cusum_k0.40_h3.5_cont | 2026-09 |        0.511441 |       -3.66302   |         -44.6423   |             -44.6423   |       22 |      5 |       17 |        1218.73  |      1174.09  |                             0 |
| ETHUSD   | cusum_k0.40_h3.5_cont | 2026-10 |        0.663786 |       -2.76826   |         -32.5018   |             -32.5018   |       22 |      7 |       15 |        1174.09  |      1141.59  |                             0 |

## All variants summary

| market   | model                 |   kappa |   threshold | direction    |   slippage_multiplier |   profit_factor |   net_return_22m_pct |   net_return_2025_pct |   net_return_2026_jan_oct_pct | year2025_above_500pct   | year2026_ytd_above_500pct   |   strong_pf1p5_return5_months |   strong_pf1p5_return10_months |   positive_months |   trades |   wins |   losses |   max_monthend_nav_drawdown_pct |   worst_month_pct |
|:---------|:----------------------|--------:|------------:|:-------------|----------------------:|----------------:|---------------------:|----------------------:|------------------------------:|:------------------------|:----------------------------|------------------------------:|-------------------------------:|------------------:|---------:|-------:|---------:|--------------------------------:|------------------:|
| BTCUSD   | cusum_k0.20_h3.5_cont |     0.2 |         3.5 | continuation |                     1 |        0.780657 |           -38.404    |             -20.8776  |                     -22.151   | False                   | False                       |                             0 |                              0 |                 5 |      694 |    261 |      433 |                       -38.404   |          -6.70035 |
| BTCUSD   | cusum_k0.20_h3.5_fade |     0.2 |         3.5 | contrarian   |                     1 |        0.733367 |           -43.6485   |             -30.4783  |                     -18.944   | False                   | False                       |                             0 |                              0 |                 7 |      682 |    254 |      428 |                       -44.6718  |          -9.31675 |
| BTCUSD   | cusum_k0.20_h5.0_cont |     0.2 |         5   | continuation |                     1 |        0.788347 |           -21.9041   |             -14.3115  |                      -8.86062 | False                   | False                       |                             0 |                              0 |                 7 |      400 |    153 |      247 |                       -24.4374  |          -6.6285  |
| BTCUSD   | cusum_k0.20_h5.0_fade |     0.2 |         5   | contrarian   |                     1 |        0.749682 |           -27.1104   |             -15.0642  |                     -14.1827  | False                   | False                       |                             0 |                              0 |                 6 |      394 |    152 |      242 |                       -28.6743  |          -6.97086 |
| BTCUSD   | cusum_k0.40_h3.5_cont |     0.4 |         3.5 | continuation |                     1 |        0.849581 |           -18.1634   |             -11.4825  |                      -7.5476  | False                   | False                       |                             0 |                              0 |                 8 |      449 |    180 |      269 |                       -20.2412  |          -7.05963 |
| BTCUSD   | cusum_k0.40_h3.5_fade |     0.4 |         3.5 | contrarian   |                     1 |        0.649299 |           -41.3161   |             -23.9884  |                     -22.7962  | False                   | False                       |                             0 |                              0 |                 5 |      444 |    158 |      286 |                       -41.3161  |          -7.2478  |
| BTCUSD   | cusum_k0.40_h5.0_cont |     0.4 |         5   | continuation |                     1 |        0.794508 |           -13.7034   |              -6.86324 |                      -7.34425 | False                   | False                       |                             0 |                              0 |                 7 |      246 |     96 |      150 |                       -13.7034  |          -2.90999 |
| BTCUSD   | cusum_k0.40_h5.0_fade |     0.4 |         5   | contrarian   |                     1 |        0.786729 |           -15.1686   |              -4.84987 |                     -10.8446  | False                   | False                       |                             0 |                              0 |                 7 |      242 |     92 |      150 |                       -16.1148  |          -3.75183 |
| ETHUSD   | cusum_k0.20_h3.5_cont |     0.2 |         3.5 | continuation |                     1 |        0.995569 |            -0.961177 |               7.16922 |                      -7.5865  | False                   | False                       |                             2 |                              0 |                11 |      692 |    273 |      419 |                       -16.1822  |          -7.1185  |
| ETHUSD   | cusum_k0.20_h3.5_fade |     0.2 |         3.5 | contrarian   |                     1 |        0.743797 |           -40.3353   |             -30.1269  |                     -14.6099  | False                   | False                       |                             0 |                              0 |                 4 |      693 |    266 |      427 |                       -40.9824  |         -10.3996  |
| ETHUSD   | cusum_k0.20_h5.0_cont |     0.2 |         5   | continuation |                     1 |        1.12452  |            15.3955   |              19.0294  |                      -3.05291 | False                   | False                       |                             0 |                              0 |                10 |      406 |    175 |      231 |                        -7.86444 |          -3.20145 |
| ETHUSD   | cusum_k0.20_h5.0_fade |     0.2 |         5   | contrarian   |                     1 |        0.678796 |           -32.6217   |             -23.8222  |                     -11.5512  | False                   | False                       |                             0 |                              0 |                 7 |      393 |    139 |      254 |                       -32.9667  |          -5.14915 |
| ETHUSD   | cusum_k0.40_h3.5_cont |     0.4 |         3.5 | continuation |                     1 |        1.09607  |            14.1585   |              23.7351  |                      -7.73953 | False                   | False                       |                             1 |                              0 |                13 |      447 |    189 |      258 |                       -11.9902  |          -4.18481 |
| ETHUSD   | cusum_k0.40_h3.5_fade |     0.4 |         3.5 | contrarian   |                     1 |        0.773761 |           -24.3504   |             -25.9236  |                       2.12369 | False                   | False                       |                             0 |                              0 |                 8 |      439 |    167 |      272 |                       -31.4683  |          -5.92522 |
| ETHUSD   | cusum_k0.40_h5.0_cont |     0.4 |         5   | continuation |                     1 |        1.17193  |            11.0076   |              14.9457  |                      -3.42601 | False                   | False                       |                             0 |                              0 |                14 |      225 |    100 |      125 |                        -3.948   |          -2.46526 |
| ETHUSD   | cusum_k0.40_h5.0_fade |     0.4 |         5   | contrarian   |                     1 |        0.644185 |           -22.2098   |             -17.7471  |                      -5.42558 | False                   | False                       |                             0 |                              0 |                 6 |      226 |     78 |      148 |                       -23.3336  |          -3.24726 |

## Combined 2025 selection ranking

| model                 |   strong5 |   strong10 |   positive |   compounded_proxy |
|:----------------------|----------:|-----------:|-----------:|-------------------:|
| cusum_k0.40_h3.5_cont |         1 |          0 |         14 |           10.5173  |
| cusum_k0.20_h3.5_cont |         1 |          0 |         10 |          -15.4628  |
| cusum_k0.40_h5.0_cont |         0 |          0 |         14 |            7.22293 |
| cusum_k0.20_h5.0_cont |         0 |          0 |         10 |            3.13822 |
| cusum_k0.40_h5.0_fade |         0 |          0 |          7 |          -24.1328  |
| cusum_k0.20_h5.0_fade |         0 |          0 |          7 |          -42.4172  |
| cusum_k0.20_h3.5_fade |         0 |          0 |          5 |          -69.7844  |
| cusum_k0.40_h3.5_fade |         0 |          0 |          4 |          -56.1092  |

## Doubled slippage sensitivity

| market   | model                                         |   kappa |   threshold | direction    |   slippage_multiplier |   profit_factor |   net_return_22m_pct |   net_return_2025_pct |   net_return_2026_jan_oct_pct | year2025_above_500pct   | year2026_ytd_above_500pct   |   strong_pf1p5_return5_months |   strong_pf1p5_return10_months |   positive_months |   trades |   wins |   losses |   max_monthend_nav_drawdown_pct |   worst_month_pct |
|:---------|:----------------------------------------------|--------:|------------:|:-------------|----------------------:|----------------:|---------------------:|----------------------:|------------------------------:|:------------------------|:----------------------------|------------------------------:|-------------------------------:|------------------:|---------:|-------:|---------:|--------------------------------:|------------------:|
| BTCUSD   | cusum_k0.40_h3.5_cont_sensitivity_2x_slippage |     0.4 |         3.5 | continuation |                     2 |        0.835762 |            -19.8359  |              -12.3071 |                      -8.58536 | False                   | False                       |                             0 |                              0 |                 8 |      449 |    178 |      271 |                        -21.8282 |          -7.15909 |
| ETHUSD   | cusum_k0.40_h3.5_cont_sensitivity_2x_slippage |     0.4 |         3.5 | continuation |                     2 |        1.05178  |              7.58158 |               19.3018 |                      -9.82402 | False                   | False                       |                             1 |                              0 |                12 |      447 |    187 |      260 |                        -13.3094 |          -4.44171 |

## Execution limitations and data

{
  "original_native_partition_sha256_verified_by_loader": true,
  "sha256_manifest": {
    "BTCUSD": "53bb09d9b406c0278d9d090012dfcf7c8099126b3b63f5f2a6996de6d7d7f1ec",
    "ETHUSD": "3ebac667958a86a44e8b3fdd04e9b1614672d7d1b83ff95b1db951599f129f6a"
  },
  "months": 22,
  "original_2025_ist_january_first_5h30m_missing": true,
  "btc_repaired_october_checked_against_manifest": true,
  "monthly_return": "mark to market account NAV at IST end of month; no month-end forced liquidation",
  "monthly_profit_factor": "sum winning net-trade PnL / abs(sum losing net-trade PnL) for exits in month",
  "full_year2025": "compounded sequential NAV Jan-Dec",
  "year2026": "Jan-Oct YTD only",
  "initial_equity_usd": 1000,
  "one_position_at_time": true,
  "risk_per_trade": 0.005,
  "max_notional_leverage": 3,
  "taker_fee_each_side": 0.0005,
  "GST": 0.18,
  "BTC_slip_points_each_side": 5,
  "ETH_slip_fraction_each_side": 0.0002,
  "sensitivity_double_slippage": true,
  "stop_first_gap_aware_1m": true,
  "no_new_entry_last_12h": true,
  "lagged_48_hour_baseline": true,
  "training": "single joint BTC+ETH 2025 selection, historically exposed 2026 fixed-parameter check",
  "excluded_november_2026": true,
  "omitted": [
    "funding",
    "real bid/ask spread",
    "market impact",
    "margin/liquidation",
    "contract lots",
    "live fills"
  ]
}
