# Independent clustered extreme-arrival relaxation paired BTC ETH audit

PARTIAL OVERLAP differential: hourly extreme-arrival density followed by first quiet hour, continuation/fade at next 1m open, 1m stop-first 1.5 ATR SL, 2.5R TP, 12h maximum hold.
Same 8 variants on BTC and ETH; 2025-only joint selection and 2026 fixed historical check.
All USD PnL and account monthly NAV include modeled taker fees, GST and adverse slippage.
Monthly profit factor is exit-month net-trade PF; monthly return is account month-end marked NAV including open position; they differ around boundaries.

## Selected identical model on both assets (2025-only combined ranking)

| market   | model                     |   extreme_multiplier |   min_cluster_events | direction    |   slippage_multiplier |   profit_factor |   net_return_22m_pct |   net_return_2025_pct |   net_return_2026_jan_oct_pct | year2025_above_500pct   | year2026_ytd_above_500pct   |   strong_pf1p5_return5_months |   strong_pf1p5_return10_months |   positive_months |   trades |   wins |   losses |   max_monthend_nav_drawdown_pct |   worst_month_pct |
|:---------|:--------------------------|---------------------:|---------------------:|:-------------|----------------------:|----------------:|---------------------:|----------------------:|------------------------------:|:------------------------|:----------------------------|------------------------------:|-------------------------------:|------------------:|---------:|-------:|---------:|--------------------------------:|------------------:|
| BTCUSD   | cluster_x2.00_count3_cont |                    2 |                    3 | continuation |                     1 |        0.78327  |             -38.3358 |             -26.8813  |                      -15.6657 | False                   | False                       |                             0 |                              0 |                 2 |      784 |    288 |      496 |                        -38.3358 |          -5.31652 |
| ETHUSD   | cluster_x2.00_count3_cont |                    2 |                    3 | continuation |                     1 |        0.878515 |             -25.3972 |              -5.03837 |                      -21.439  | False                   | False                       |                             2 |                              0 |                 7 |      789 |    304 |      485 |                        -33.2627 |          -7.02177 |

## All 22 months, selected model, both native assets side by side

| market   | model                     | month   |   profit_factor |   net_return_pct |   net_exit_pnl_usd |   month_nav_change_usd |   trades |   wins |   losses |   nav_start_usd |   nav_end_usd |   open_positions_at_month_end |
|:---------|:--------------------------|:--------|----------------:|-----------------:|-------------------:|-----------------------:|---------:|-------:|---------:|----------------:|--------------:|------------------------------:|
| BTCUSD   | cluster_x2.00_count3_cont | 2025-01 |        0.836093 |       -1.24106   |         -12.4106   |             -12.4106   |       28 |     13 |       15 |        1000     |       987.589 |                             0 |
| BTCUSD   | cluster_x2.00_count3_cont | 2025-02 |        0.59159  |       -5.31652   |         -52.5053   |             -52.5053   |       42 |     12 |       30 |         987.589 |       935.084 |                             0 |
| BTCUSD   | cluster_x2.00_count3_cont | 2025-03 |        0.883906 |       -0.579328  |         -10.4129   |              -5.41721  |       33 |     13 |       20 |         935.084 |       929.667 |                             1 |
| BTCUSD   | cluster_x2.00_count3_cont | 2025-04 |        0.806477 |       -2.5833    |         -17.4524   |             -24.0161   |       34 |     14 |       20 |         929.667 |       905.651 |                             1 |
| BTCUSD   | cluster_x2.00_count3_cont | 2025-05 |        0.602496 |       -5.03451   |         -47.1631   |             -45.5951   |       42 |     14 |       28 |         905.651 |       860.056 |                             0 |
| BTCUSD   | cluster_x2.00_count3_cont | 2025-06 |        0.927465 |       -0.464526  |          -5.41783  |              -3.99518  |       32 |     12 |       20 |         860.056 |       856.06  |                             1 |
| BTCUSD   | cluster_x2.00_count3_cont | 2025-07 |        0.727079 |       -3.02917   |         -24.5089   |             -25.9315   |       36 |     15 |       21 |         856.06  |       830.129 |                             0 |
| BTCUSD   | cluster_x2.00_count3_cont | 2025-08 |        0.788869 |       -1.74145   |         -14.4563   |             -14.4563   |       32 |     10 |       22 |         830.129 |       815.673 |                             0 |
| BTCUSD   | cluster_x2.00_count3_cont | 2025-09 |        0.939258 |       -0.664121  |          -5.27787  |              -5.41706  |       38 |     12 |       26 |         815.673 |       810.256 |                             1 |
| BTCUSD   | cluster_x2.00_count3_cont | 2025-10 |        0.545631 |       -4.73621   |         -38.5146   |             -38.3754   |       38 |     11 |       27 |         810.256 |       771.88  |                             0 |
| BTCUSD   | cluster_x2.00_count3_cont | 2025-11 |        0.943412 |       -0.779932  |          -4.78078  |              -6.02014  |       35 |     11 |       24 |         771.88  |       765.86  |                             1 |
| BTCUSD   | cluster_x2.00_count3_cont | 2025-12 |        0.631797 |       -4.5273    |         -32.9391   |             -34.6728   |       37 |     14 |       23 |         765.86  |       731.187 |                             1 |
| BTCUSD   | cluster_x2.00_count3_cont | 2026-01 |        0.719946 |       -3.06896   |         -25.413    |             -22.4399   |       42 |     14 |       28 |         731.187 |       708.747 |                             0 |
| BTCUSD   | cluster_x2.00_count3_cont | 2026-02 |        1.01213  |        0.0861276 |           0.615948 |               0.610427 |       29 |     12 |       17 |         708.747 |       709.358 |                             1 |
| BTCUSD   | cluster_x2.00_count3_cont | 2026-03 |        0.79414  |       -1.60582   |         -11.9143   |             -11.391    |       32 |     15 |       17 |         709.358 |       697.967 |                             1 |
| BTCUSD   | cluster_x2.00_count3_cont | 2026-04 |        1.02675  |        0.201103  |           1.92147  |               1.40363  |       38 |     15 |       23 |         697.967 |       699.37  |                             0 |
| BTCUSD   | cluster_x2.00_count3_cont | 2026-05 |        0.684043 |       -3.18451   |         -22.2715   |             -22.2715   |       34 |     14 |       20 |         699.37  |       677.099 |                             0 |
| BTCUSD   | cluster_x2.00_count3_cont | 2026-06 |        0.778971 |       -2.44311   |         -16.5423   |             -16.5423   |       37 |     11 |       26 |         677.099 |       660.557 |                             0 |
| BTCUSD   | cluster_x2.00_count3_cont | 2026-07 |        0.719547 |       -3.11318   |         -20.5643   |             -20.5643   |       32 |     10 |       22 |         660.557 |       639.992 |                             0 |
| BTCUSD   | cluster_x2.00_count3_cont | 2026-08 |        0.781462 |       -2.23241   |         -15.3222   |             -14.2873   |       38 |     15 |       23 |         639.992 |       625.705 |                             1 |
| BTCUSD   | cluster_x2.00_count3_cont | 2026-09 |        0.924112 |       -1.09714   |          -4.77998  |              -6.86489  |       35 |     14 |       21 |         625.705 |       618.84  |                             1 |
| BTCUSD   | cluster_x2.00_count3_cont | 2026-10 |        0.949599 |       -0.355256  |          -3.24847  |              -2.19847  |       40 |     17 |       23 |         618.84  |       616.642 |                             0 |
| ETHUSD   | cluster_x2.00_count3_cont | 2025-01 |        1.71626  |        5.67915   |          56.7915   |              56.7915   |       33 |     17 |       16 |        1000     |      1056.79  |                             0 |
| ETHUSD   | cluster_x2.00_count3_cont | 2025-02 |        1.99663  |        5.77833   |          61.0649   |              61.0649   |       28 |     15 |       13 |        1056.79  |      1117.86  |                             0 |
| ETHUSD   | cluster_x2.00_count3_cont | 2025-03 |        0.562802 |       -4.2958    |         -47.2769   |             -48.0209   |       31 |     12 |       19 |        1117.86  |      1069.84  |                             1 |
| ETHUSD   | cluster_x2.00_count3_cont | 2025-04 |        0.566822 |       -4.2534    |         -42.7837   |             -45.5043   |       31 |      8 |       23 |        1069.84  |      1024.33  |                             1 |
| ETHUSD   | cluster_x2.00_count3_cont | 2025-05 |        1.12178  |        1.70048   |          13.9539   |              17.4185   |       42 |     18 |       24 |        1024.33  |      1041.75  |                             0 |
| ETHUSD   | cluster_x2.00_count3_cont | 2025-06 |        1.17647  |        2.02405   |          21.0856   |              21.0856   |       41 |     18 |       23 |        1041.75  |      1062.84  |                             0 |
| ETHUSD   | cluster_x2.00_count3_cont | 2025-07 |        0.511753 |       -4.51155   |         -47.9503   |             -47.9503   |       35 |     11 |       24 |        1062.84  |      1014.88  |                             0 |
| ETHUSD   | cluster_x2.00_count3_cont | 2025-08 |        1.60491  |        4.4745    |          45.411    |              45.411    |       34 |     15 |       19 |        1014.88  |      1060.3   |                             0 |
| ETHUSD   | cluster_x2.00_count3_cont | 2025-09 |        1.05284  |        0.211001  |           4.12438  |               2.23723  |       28 |     10 |       18 |        1060.3   |      1062.53  |                             1 |
| ETHUSD   | cluster_x2.00_count3_cont | 2025-10 |        0.69558  |       -3.72592   |         -41.4763   |             -39.5892   |       42 |     11 |       31 |        1062.53  |      1022.94  |                             0 |
| ETHUSD   | cluster_x2.00_count3_cont | 2025-11 |        0.763999 |       -2.41469   |         -22.5381   |             -24.7009   |       33 |     10 |       23 |        1022.94  |       998.243 |                             1 |
| ETHUSD   | cluster_x2.00_count3_cont | 2025-12 |        0.472248 |       -4.87124   |         -50.7897   |             -48.6268   |       36 |     10 |       26 |         998.243 |       949.616 |                             0 |
| ETHUSD   | cluster_x2.00_count3_cont | 2026-01 |        0.827272 |       -1.88581   |         -17.908    |             -17.908    |       38 |     14 |       24 |         949.616 |       931.708 |                             0 |
| ETHUSD   | cluster_x2.00_count3_cont | 2026-02 |        0.85002  |       -1.56215   |         -14.7485   |             -14.5547   |       38 |     16 |       22 |         931.708 |       917.154 |                             1 |
| ETHUSD   | cluster_x2.00_count3_cont | 2026-03 |        0.871039 |       -1.25303   |         -11.9203   |             -11.4922   |       35 |     15 |       20 |         917.154 |       905.661 |                             1 |
| ETHUSD   | cluster_x2.00_count3_cont | 2026-04 |        1.33938  |        2.91481   |          27.0201   |              26.3983   |       40 |     22 |       18 |         905.661 |       932.06  |                             0 |
| ETHUSD   | cluster_x2.00_count3_cont | 2026-05 |        0.580388 |       -3.91132   |         -38.2077   |             -36.4558   |       33 |     12 |       21 |         932.06  |       895.604 |                             1 |
| ETHUSD   | cluster_x2.00_count3_cont | 2026-06 |        0.528194 |       -5.95643   |         -51.5941   |             -53.346    |       41 |     14 |       27 |         895.604 |       842.258 |                             0 |
| ETHUSD   | cluster_x2.00_count3_cont | 2026-07 |        0.830607 |       -1.6839    |         -14.1828   |             -14.1828   |       35 |     13 |       22 |         842.258 |       828.075 |                             0 |
| ETHUSD   | cluster_x2.00_count3_cont | 2026-08 |        0.475177 |       -7.02177   |         -58.1455   |             -58.1455   |       39 |     10 |       29 |         828.075 |       769.93  |                             0 |
| ETHUSD   | cluster_x2.00_count3_cont | 2026-09 |        0.869055 |       -1.44851   |         -10.2145   |             -11.1525   |       36 |     14 |       22 |         769.93  |       758.777 |                             1 |
| ETHUSD   | cluster_x2.00_count3_cont | 2026-10 |        0.834542 |       -1.68027   |         -13.6875   |             -12.7495   |       40 |     19 |       21 |         758.777 |       746.028 |                             0 |

## All variants summary

| market   | model                     |   extreme_multiplier |   min_cluster_events | direction    |   slippage_multiplier |   profit_factor |   net_return_22m_pct |   net_return_2025_pct |   net_return_2026_jan_oct_pct | year2025_above_500pct   | year2026_ytd_above_500pct   |   strong_pf1p5_return5_months |   strong_pf1p5_return10_months |   positive_months |   trades |   wins |   losses |   max_monthend_nav_drawdown_pct |   worst_month_pct |
|:---------|:--------------------------|---------------------:|---------------------:|:-------------|----------------------:|----------------:|---------------------:|----------------------:|------------------------------:|:------------------------|:----------------------------|------------------------------:|-------------------------------:|------------------:|---------:|-------:|---------:|--------------------------------:|------------------:|
| BTCUSD   | cluster_x2.00_count3_cont |                  2   |                    3 | continuation |                     1 |        0.78327  |            -38.3358  |            -26.8813   |                    -15.6657   | False                   | False                       |                             0 |                              0 |                 2 |      784 |    288 |      496 |                        -38.3358 |          -5.31652 |
| BTCUSD   | cluster_x2.00_count3_fade |                  2   |                    3 | contrarian   |                     1 |        0.709741 |            -51.3033  |            -28.3154   |                    -32.068    | False                   | False                       |                             0 |                              0 |                 1 |      801 |    311 |      490 |                        -51.3033 |          -7.85898 |
| BTCUSD   | cluster_x2.00_count4_cont |                  2   |                    4 | continuation |                     1 |        0.786041 |            -23.913   |            -24.6011   |                      0.912631 | False                   | False                       |                             0 |                              0 |                 7 |      488 |    189 |      299 |                        -28.8505 |          -5.48023 |
| BTCUSD   | cluster_x2.00_count4_fade |                  2   |                    4 | contrarian   |                     1 |        0.765289 |            -29.3074  |             -9.45366  |                    -21.9266   | False                   | False                       |                             0 |                              0 |                 5 |      488 |    198 |      290 |                        -29.3074 |          -6.51551 |
| BTCUSD   | cluster_x2.50_count3_cont |                  2.5 |                    3 | continuation |                     1 |        0.797791 |            -25.3043  |            -16.8434   |                    -10.1746   | False                   | False                       |                             0 |                              0 |                 6 |      530 |    198 |      332 |                        -25.3043 |          -4.81334 |
| BTCUSD   | cluster_x2.50_count3_fade |                  2.5 |                    3 | contrarian   |                     1 |        0.729006 |            -36.2381  |            -18.7827   |                    -21.4923   | False                   | False                       |                             0 |                              0 |                 3 |      542 |    211 |      331 |                        -37.2724 |          -6.82478 |
| BTCUSD   | cluster_x2.50_count4_cont |                  2.5 |                    4 | continuation |                     1 |        0.867636 |             -9.90155 |            -10.2372   |                      0.373897 | False                   | False                       |                             0 |                              0 |                 9 |      302 |    120 |      182 |                        -14.7309 |          -3.76787 |
| BTCUSD   | cluster_x2.50_count4_fade |                  2.5 |                    4 | contrarian   |                     1 |        0.815676 |            -15.1623  |             -4.04396  |                    -11.5869   | False                   | False                       |                             0 |                              0 |                 6 |      301 |    121 |      180 |                        -17.5709 |          -4.22457 |
| ETHUSD   | cluster_x2.00_count3_cont |                  2   |                    3 | continuation |                     1 |        0.878515 |            -25.3972  |             -5.03837  |                    -21.439    | False                   | False                       |                             2 |                              0 |                 7 |      789 |    304 |      485 |                        -33.2627 |          -7.02177 |
| ETHUSD   | cluster_x2.00_count3_fade |                  2   |                    3 | contrarian   |                     1 |        0.750892 |            -42.6375  |            -24.0794   |                    -24.4441   | False                   | False                       |                             0 |                              0 |                 4 |      806 |    331 |      475 |                        -43.0501 |          -9.10231 |
| ETHUSD   | cluster_x2.00_count4_cont |                  2   |                    4 | continuation |                     1 |        0.888035 |            -14.1664  |             -2.0603   |                    -12.3608   | False                   | False                       |                             0 |                              0 |                 7 |      467 |    180 |      287 |                        -20.4283 |          -4.07647 |
| ETHUSD   | cluster_x2.00_count4_fade |                  2   |                    4 | contrarian   |                     1 |        0.743353 |            -27.8134  |            -16.1897   |                    -13.869    | False                   | False                       |                             0 |                              0 |                 5 |      476 |    200 |      276 |                        -29.6864 |          -4.60639 |
| ETHUSD   | cluster_x2.50_count3_cont |                  2.5 |                    3 | continuation |                     1 |        0.876428 |            -16.6242  |             -7.62335  |                     -9.74366  | False                   | False                       |                             0 |                              0 |                 9 |      502 |    188 |      314 |                        -20.4435 |          -6.71328 |
| ETHUSD   | cluster_x2.50_count3_fade |                  2.5 |                    3 | contrarian   |                     1 |        0.799496 |            -24.6311  |            -11.1326   |                    -15.1894   | False                   | False                       |                             0 |                              0 |                 6 |      523 |    228 |      295 |                        -24.6464 |          -7.24618 |
| ETHUSD   | cluster_x2.50_count4_cont |                  2.5 |                    4 | continuation |                     1 |        0.860169 |            -10.4674  |              0.187799 |                    -10.6352   | False                   | False                       |                             0 |                              0 |                 8 |      274 |    105 |      169 |                        -13.5577 |          -4.36883 |
| ETHUSD   | cluster_x2.50_count4_fade |                  2.5 |                    4 | contrarian   |                     1 |        0.841047 |            -11.0351  |             -8.1167   |                     -3.17624  | False                   | False                       |                             0 |                              0 |                 6 |      290 |    128 |      162 |                        -13.1892 |          -4.13136 |

## Combined 2025 selection ranking

| model                     |   strong5 |   strong10 |   positive |   compounded_proxy |
|:--------------------------|----------:|-----------:|-----------:|-------------------:|
| cluster_x2.00_count3_cont |         2 |          0 |          6 |           -34.9025 |
| cluster_x2.50_count3_cont |         0 |          0 |          9 |           -25.6529 |
| cluster_x2.50_count4_cont |         0 |          0 |          8 |           -10.2394 |
| cluster_x2.50_count4_fade |         0 |          0 |          6 |           -12.0745 |
| cluster_x2.00_count4_cont |         0 |          0 |          6 |           -29.3395 |
| cluster_x2.50_count3_fade |         0 |          0 |          6 |           -31.8763 |
| cluster_x2.00_count4_fade |         0 |          0 |          5 |           -26.8155 |
| cluster_x2.00_count3_fade |         0 |          0 |          3 |           -59.2897 |

## Doubled slippage sensitivity

| market   | model                                             |   extreme_multiplier |   min_cluster_events | direction    |   slippage_multiplier |   profit_factor |   net_return_22m_pct |   net_return_2025_pct |   net_return_2026_jan_oct_pct | year2025_above_500pct   | year2026_ytd_above_500pct   |   strong_pf1p5_return5_months |   strong_pf1p5_return10_months |   positive_months |   trades |   wins |   losses |   max_monthend_nav_drawdown_pct |   worst_month_pct |
|:---------|:--------------------------------------------------|---------------------:|---------------------:|:-------------|----------------------:|----------------:|---------------------:|----------------------:|------------------------------:|:------------------------|:----------------------------|------------------------------:|-------------------------------:|------------------:|---------:|-------:|---------:|--------------------------------:|------------------:|
| BTCUSD   | cluster_x2.00_count3_cont_sensitivity_2x_slippage |                    2 |                    3 | continuation |                     2 |        0.764157 |             -41.3114 |              -29.0285 |                      -17.3068 | False                   | False                       |                             0 |                              0 |                 1 |      784 |    286 |      498 |                        -41.3114 |          -6.12675 |
| ETHUSD   | cluster_x2.00_count3_cont_sensitivity_2x_slippage |                    2 |                    3 | continuation |                     2 |        0.832659 |             -34.6115 |               -9.254  |                      -27.9434 | False                   | False                       |                             2 |                              0 |                 7 |      796 |    295 |      501 |                        -41.2164 |          -8.13278 |

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
