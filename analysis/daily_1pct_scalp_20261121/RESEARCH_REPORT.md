# BTC daily 1% NET ACCOUNT scalp (research; not a guaranteed daily return)

## Predeclared settings

- BTCUSD Delta India 1m authentic candles; 15m triggers and completed 1h EMA confirmation.
- 2x notional leverage at each entry; one trade per IST day; 12:00-18:59 IST.
- Stop exactly -1% account NAV and TP exactly +1% account NAV after 0.05% taker/side, 18% GST and 5 USD/side slippage.
- 4h maximum hold or before day boundary, 1m stop-first OHLC execution.

## Summary per fixed setup

| model    |   capital_start_usd |   capital_end_usd |   net_compounded_return_pct |   max_trade_close_drawdown_pct |   trades |   profitable_trades |   losing_or_flat_trades |   profit_factor_usd |   days_in_sample |   positive_days |   negative_days |   no_trade_or_flat_days |   days_net_1pct_target_reached |   daily_target_hit_pct_all_days |   months_positive |   months_negative |   months_zero |   model_gross_usd |   total_fee_gst_usd |   total_slippage_usd |   year2025_return_pct |   year2026_JanOct_return_pct |
|:---------|--------------------:|------------------:|----------------------------:|-------------------------------:|---------:|--------------------:|------------------------:|--------------------:|-----------------:|----------------:|----------------:|------------------------:|-------------------------------:|--------------------------------:|------------------:|------------------:|--------------:|------------------:|--------------------:|---------------------:|----------------------:|-----------------------------:|
| trend    |               10000 |           4620.49 |                    -53.7951 |                        54.7056 |      364 |                 137 |                     227 |              0.6167 |              669 |             137 |             227 |                     305 |                            115 |                          17.19  |                 3 |                19 |             0 |           1280.25 |             6069.84 |               589.93 |              -32.5555 |                     -31.4921 |
| sweep    |               10000 |           4378.86 |                    -56.2114 |                        56.2114 |      226 |                  69 |                     157 |              0.4052 |              669 |              69 |             157 |                     443 |                             48 |                           7.175 |                 0 |                22 |             0 |          -1518.02 |             3742.6  |               360.52 |              -34.4502 |                     -33.198  |
| combined |               10000 |           3037.05 |                    -69.6295 |                        70.2279 |      464 |                 165 |                     299 |              0.5427 |              669 |             165 |             299 |                     205 |                            131 |                          19.581 |                 2 |                20 |             0 |             49.32 |             6401.35 |               610.92 |              -47.0761 |                     -42.6147 |

## Every complete IST month

| model    | month_ist   |   trades |   target_1pct_days |   winning_days |   losing_days |   no_trade_or_flat_days |   monthly_return_pct |
|:---------|:------------|---------:|-------------------:|---------------:|--------------:|------------------------:|---------------------:|
| trend    | 2025-01     |       15 |                  6 |              6 |             9 |                      16 |            -2.45014  |
| trend    | 2025-02     |       12 |                  5 |              6 |             6 |                      16 |            -0.361638 |
| trend    | 2025-03     |       16 |                  4 |              5 |            11 |                      15 |            -5.77664  |
| trend    | 2025-04     |       18 |                  5 |              6 |            12 |                      12 |            -5.88012  |
| trend    | 2025-05     |       19 |                  6 |              8 |            11 |                      12 |            -0.948772 |
| trend    | 2025-06     |       20 |                  6 |              8 |            12 |                      10 |            -3.45694  |
| trend    | 2025-07     |       13 |                  1 |              1 |            12 |                      18 |            -8.20028  |
| trend    | 2025-08     |       16 |                  7 |              8 |             8 |                      15 |             0.694634 |
| trend    | 2025-09     |       15 |                  2 |              7 |             8 |                      15 |            -3.00224  |
| trend    | 2025-10     |       18 |                  7 |              8 |            10 |                      13 |            -2.89703  |
| trend    | 2025-11     |       16 |                  5 |              7 |             9 |                      14 |            -3.85382  |
| trend    | 2025-12     |       15 |                  5 |              6 |             9 |                      16 |            -2.25406  |
| trend    | 2026-01     |       19 |                  6 |              8 |            11 |                      12 |            -1.95446  |
| trend    | 2026-02     |       12 |                  5 |              5 |             7 |                      16 |            -0.566667 |
| trend    | 2026-03     |       18 |                  7 |              7 |            11 |                      13 |            -4.00762  |
| trend    | 2026-04     |       16 |                  8 |              8 |             8 |                      14 |             0.425964 |
| trend    | 2026-05     |       18 |                  6 |              6 |            12 |                      13 |            -4.02601  |
| trend    | 2026-06     |       22 |                  4 |              6 |            16 |                       8 |           -10.8629   |
| trend    | 2026-07     |       16 |                  4 |              4 |            12 |                      15 |            -7.2032   |
| trend    | 2026-08     |       22 |                  5 |              5 |            17 |                       9 |            -7.59876  |
| trend    | 2026-09     |       14 |                  5 |              5 |             9 |                      16 |            -1.40911  |
| trend    | 2026-10     |       14 |                  6 |              7 |             7 |                      17 |             0.794882 |
| sweep    | 2025-01     |        7 |                  1 |              1 |             6 |                      24 |            -4.36044  |
| sweep    | 2025-02     |        9 |                  2 |              2 |             7 |                      19 |            -2.91448  |
| sweep    | 2025-03     |        9 |                  3 |              4 |             5 |                      22 |            -1.37527  |
| sweep    | 2025-04     |       12 |                  4 |              5 |             7 |                      18 |            -1.6798   |
| sweep    | 2025-05     |        8 |                  0 |              2 |             6 |                      23 |            -4.69653  |
| sweep    | 2025-06     |       20 |                  3 |              9 |            11 |                      10 |            -3.0244   |
| sweep    | 2025-07     |       12 |                  3 |              4 |             8 |                      19 |            -4.15941  |
| sweep    | 2025-08     |        9 |                  1 |              4 |             5 |                      22 |            -2.33901  |
| sweep    | 2025-09     |        9 |                  1 |              1 |             8 |                      21 |            -5.60602  |
| sweep    | 2025-10     |        8 |                  1 |              1 |             7 |                      23 |            -5.25182  |
| sweep    | 2025-11     |        9 |                  3 |              3 |             6 |                      21 |            -2.99921  |
| sweep    | 2025-12     |        7 |                  2 |              2 |             5 |                      24 |            -2.98951  |
| sweep    | 2026-01     |       11 |                  2 |              4 |             7 |                      20 |            -1.54333  |
| sweep    | 2026-02     |       13 |                  5 |              6 |             7 |                      15 |            -1.06874  |
| sweep    | 2026-03     |       12 |                  2 |              2 |            10 |                      19 |            -7.74398  |
| sweep    | 2026-04     |       13 |                  3 |              5 |             8 |                      17 |            -3.62106  |
| sweep    | 2026-05     |       13 |                  5 |              5 |             8 |                      18 |            -2.30383  |
| sweep    | 2026-06     |        6 |                  1 |              1 |             5 |                      24 |            -3.95     |
| sweep    | 2026-07     |       11 |                  2 |              2 |             9 |                      20 |            -6.02403  |
| sweep    | 2026-08     |       10 |                  1 |              2 |             8 |                      21 |            -6.24237  |
| sweep    | 2026-09     |        9 |                  1 |              2 |             7 |                      21 |            -4.04809  |
| sweep    | 2026-10     |        9 |                  2 |              2 |             7 |                      22 |            -2.77414  |
| combined | 2025-01     |       19 |                  6 |              6 |            13 |                      12 |            -5.75193  |
| combined | 2025-02     |       18 |                  6 |              7 |            11 |                      10 |            -2.27869  |
| combined | 2025-03     |       20 |                  4 |              6 |            14 |                      11 |            -8.54146  |
| combined | 2025-04     |       25 |                  7 |              8 |            17 |                       5 |            -7.93616  |
| combined | 2025-05     |       22 |                  6 |              9 |            13 |                       9 |            -2.60329  |
| combined | 2025-06     |       28 |                  9 |             14 |            14 |                       2 |            -0.256296 |
| combined | 2025-07     |       19 |                  1 |              1 |            18 |                      12 |           -13.5724   |
| combined | 2025-08     |       18 |                  7 |             10 |             8 |                      13 |             1.64573  |
| combined | 2025-09     |       22 |                  2 |              7 |            15 |                       8 |            -8.4308   |
| combined | 2025-10     |       20 |                  7 |              8 |            12 |                      11 |            -4.21311  |
| combined | 2025-11     |       20 |                  6 |              8 |            12 |                      10 |            -5.77655  |
| combined | 2025-12     |       18 |                  6 |              7 |            11 |                      13 |            -3.2412   |
| combined | 2026-01     |       24 |                  6 |              9 |            15 |                       7 |            -4.64451  |
| combined | 2026-02     |       20 |                  8 |              9 |            11 |                       8 |            -1.41175  |
| combined | 2026-03     |       23 |                  8 |              8 |            15 |                       8 |            -6.868    |
| combined | 2026-04     |       23 |                  9 |             11 |            12 |                       7 |            -1.22555  |
| combined | 2026-05     |       22 |                  7 |              7 |            15 |                       9 |            -5.9453   |
| combined | 2026-06     |       23 |                  3 |              5 |            18 |                       7 |           -13.5017   |
| combined | 2026-07     |       20 |                  4 |              4 |            16 |                      11 |           -10.1059   |
| combined | 2026-08     |       23 |                  5 |              5 |            18 |                       8 |            -8.52277  |
| combined | 2026-09     |       19 |                  6 |              7 |            12 |                      11 |            -2.37581  |
| combined | 2026-10     |       18 |                  8 |              9 |             9 |                      13 |             1.60071  |

## Limitations

- The goal is 1% net account profit on qualifying days, NOT guaranteed daily income
- At most one trade each IST day; no-trade days are failures of daily-profit goal
- 5 USD/side slippage is assumed, not actual bid/ask prices; funding unmodeled
- Original 1m source label convention must be independently verified on live Delta candles
- Both years were already studied on earlier research, so 2026 is not untouched validation
- No forward trading recommendation until paper audit and independent data are positive
