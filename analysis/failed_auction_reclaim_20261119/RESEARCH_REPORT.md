# Independent failed-auction reclaim reversal strategy research

**Predeclared qualifying models: 0/64**

## Qualifying results
None

## Top models by 2025 performance (2026 reported without selecting on it)
| symbol   | model                                             |   signals |   trades |   wins |   losses |   win_rate_pct |   profit_factor |   avg_win_loss_ratio |   biggest_winner_R |   winners_over_10R |   net_return_pct |   max_drawdown_pct |   fees_usd |   funding_proxy_usd |   return_2025_pct |   return_2026_pct |   profit_months |   loss_months |   active_months |
|:---------|:--------------------------------------------------|----------:|---------:|-------:|---------:|---------------:|----------------:|---------------------:|-------------------:|-------------------:|-----------------:|-------------------:|-----------:|--------------------:|------------------:|------------------:|----------------:|--------------:|----------------:|
| ETHUSD   | auction96_reclaim0.55_vol1_init1.5atr_trail5atr   |       130 |      111 |     38 |       73 |         34.234 |          1.434  |               2.7548 |             14.171 |                  2 |           18.101 |             -9.103 |     49.624 |              -0.877 |            19.889 |            -1.491 |              13 |            10 |              23 |
| ETHUSD   | auction48_reclaim0.55_vol1.5_init1.5atr_trail5atr |       165 |      142 |     43 |       99 |         30.282 |          1.6619 |               3.8263 |             68.057 |                  3 |           37.778 |            -15.544 |     71.676 |               0.675 |            18.738 |            16.035 |              10 |            13 |              23 |
| ETHUSD   | auction96_reclaim0.55_vol1.5_init1.5atr_trail5atr |       103 |       90 |     32 |       58 |         35.556 |          1.5684 |               2.8427 |             14.171 |                  2 |           18.421 |             -8.039 |     39.994 |              -1.055 |            17.628 |             0.674 |              13 |             9 |              22 |
| ETHUSD   | auction96_reclaim0.55_vol1_init1atr_trail5atr     |       130 |      119 |     30 |       89 |         25.21  |          1.2309 |               3.6516 |             21.257 |                  4 |           12.319 |            -15.186 |     76.42  |              -2.351 |            15.956 |            -3.137 |              11 |            12 |              23 |
| ETHUSD   | auction96_reclaim0.55_vol1.5_init1.5atr_trail8atr |       103 |       88 |     29 |       59 |         32.955 |          1.2724 |               2.5886 |             11.634 |                  2 |            9.393 |            -11.491 |     37.186 |               0.218 |            13.866 |            -3.928 |               9 |            13 |              22 |
| ETHUSD   | auction96_reclaim0.55_vol1.5_init1atr_trail5atr   |       103 |       95 |     25 |       70 |         26.316 |          1.3086 |               3.664  |             21.257 |                  3 |           12.702 |            -14.899 |     60.363 |              -2.065 |            13.6   |            -0.791 |              11 |            11 |              22 |
| ETHUSD   | auction48_reclaim0.55_vol1.5_init1.5atr_trail8atr |       165 |      132 |     36 |       96 |         27.273 |          1.4458 |               3.8556 |             65.728 |                  3 |           25.45  |            -21.395 |     63.695 |              -1.958 |            13.587 |            10.444 |               8 |            15 |              23 |
| ETHUSD   | auction96_reclaim0.55_vol1.5_init1atr_trail8atr   |       103 |       95 |     22 |       73 |         23.158 |          1.0991 |               3.647  |             17.451 |                  3 |            4.395 |            -16.879 |     59.309 |              -4.508 |            12.808 |            -7.458 |               7 |            15 |              22 |
| BTCUSD   | auction48_reclaim0.55_vol1.5_init1.5atr_trail8atr |       192 |      151 |     37 |      114 |         24.503 |          1.074  |               3.3091 |             22.213 |                  4 |            5.078 |            -13.329 |    110.297 |              10.676 |            12.724 |            -6.783 |              10 |            13 |              23 |
| ETHUSD   | auction48_reclaim0.55_vol1_init1.5atr_trail5atr   |       224 |      176 |     51 |      125 |         28.977 |          1.3917 |               3.411  |             68.057 |                  3 |           27.087 |            -20.076 |     83.135 |              -0.284 |            12.278 |            13.189 |              12 |            11 |              23 |
| ETHUSD   | auction48_reclaim0.55_vol1.5_init1atr_trail8atr   |       165 |      144 |     27 |      117 |         18.75  |          1.4211 |               6.1581 |             98.592 |                  4 |           29.501 |            -27.087 |     99.227 |              -3.242 |             9.354 |            18.424 |               8 |            15 |              23 |
| ETHUSD   | auction96_reclaim0.55_vol1_init1.5atr_trail8atr   |       130 |      108 |     31 |       77 |         28.704 |          1.0566 |               2.6244 |             11.634 |                  2 |            2.442 |            -16.686 |     44.306 |               1.296 |             9.068 |            -6.076 |              10 |            13 |              23 |

## Promising exploratory candidates (not validated)
None

## Candidate trade concentration
None

## Caution
- Open source historical data already research-exposed; 2026 is not independent untouched holdout
- Monthly NAV and unrealized liquidation fee at IST calendar boundary
- 1min bar OHLC cannot provide order book, spread, or exact intrabar order
- The same-minute entry candle stop check deferred to next 1min open
- True settled funding cashflows and liquidation margin not independently verified
- 2026 November partial; no 2022-2024 Delta history in repository
- No qualifying model is NOT evidence all asymmetric strategies fail
