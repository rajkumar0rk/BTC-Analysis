# Independent directional-efficiency shock strategy research

**Predeclared qualifying models: 0/64**

## Qualifying results
None

## Top models by 2025 performance (2026 reported without selecting on it)
| symbol   | model                                           |   signals |   trades |   wins |   losses |   win_rate_pct |   profit_factor |   avg_win_loss_ratio |   biggest_winner_R |   winners_over_10R |   net_return_pct |   max_drawdown_pct |   fees_usd |   funding_proxy_usd |   return_2025_pct |   return_2026_pct |   profit_months |   loss_months |   active_months |
|:---------|:------------------------------------------------|----------:|---------:|-------:|---------:|---------------:|----------------:|---------------------:|-------------------:|-------------------:|-----------------:|-------------------:|-----------:|--------------------:|------------------:|------------------:|----------------:|--------------:|----------------:|
| ETHUSD   | efficiency16h_ge0.45_ema1_init1.75atr_trail6atr |       208 |      106 |     32 |       74 |         30.189 |          1.8846 |               4.358  |             21.196 |                  5 |          108.412 |            -17.545 |    136.074 |               9.386 |            60.982 |            29.463 |              13 |            10 |              23 |
| ETHUSD   | efficiency16h_ge0.45_ema1_init1.25atr_trail6atr |       208 |      113 |     28 |       85 |         24.779 |          2.0227 |               6.1404 |             29.674 |                  7 |          155.717 |            -19.011 |    209.854 |              10.424 |            58.382 |            61.456 |              13 |            10 |              23 |
| ETHUSD   | efficiency16h_ge0.45_ema0_init1.75atr_trail6atr |       334 |      170 |     45 |      125 |         26.471 |          1.5136 |               4.2045 |             21.196 |                  6 |           94.038 |            -18.673 |    198.229 |               7.081 |            47.632 |            31.433 |              14 |             9 |              23 |
| ETHUSD   | efficiency8h_ge0.45_ema1_init1.75atr_trail6atr  |       333 |      161 |     41 |      120 |         25.466 |          1.4698 |               4.3018 |             31.373 |                  5 |           78.176 |            -21.624 |    184.259 |               7.904 |            36.279 |            30.744 |              13 |            10 |              23 |
| ETHUSD   | efficiency8h_ge0.45_ema1_init1.25atr_trail6atr  |       333 |      176 |     39 |      137 |         22.159 |          1.534  |               5.3888 |             43.923 |                  6 |          115.978 |            -24.132 |    298.399 |              13.024 |            36.051 |            58.748 |              12 |            11 |              23 |
| ETHUSD   | efficiency16h_ge0.45_ema1_init1.75atr_trail4atr |       208 |      120 |     39 |       81 |         32.5   |          1.5776 |               3.2765 |             21.831 |                  3 |           63.32  |            -15.391 |    124.168 |               5.209 |            33.551 |            22.29  |              13 |            10 |              23 |
| ETHUSD   | efficiency16h_ge0.45_ema0_init1.25atr_trail6atr |       334 |      184 |     43 |      141 |         23.37  |          1.5974 |               5.2378 |             29.674 |                  8 |          129.639 |            -21.22  |    286.569 |               8.91  |            32.693 |            73.061 |              15 |             8 |              23 |
| BTCUSD   | efficiency16h_ge0.65_ema0_init1.75atr_trail6atr |        73 |       49 |     16 |       33 |         32.653 |          2.034  |               4.1951 |             22.479 |                  2 |           45.378 |            -15.719 |     71.819 |               5.874 |            28.925 |            12.761 |              13 |            10 |              23 |
| ETHUSD   | efficiency8h_ge0.45_ema1_init1.75atr_trail4atr  |       333 |      177 |     57 |      120 |         32.203 |          1.5106 |               3.1801 |             32.247 |                  4 |           76.128 |            -17.462 |    187.428 |               4.167 |            27.641 |            37.987 |              13 |            10 |              23 |
| ETHUSD   | efficiency16h_ge0.45_ema1_init1.25atr_trail4atr |       208 |      128 |     35 |       93 |         27.344 |          1.6513 |               4.3877 |             30.564 |                  4 |           84.093 |            -16.773 |    180.194 |               6.447 |            25.807 |            46.331 |              14 |             9 |              23 |
| BTCUSD   | efficiency8h_ge0.45_ema1_init1.25atr_trail6atr  |       318 |      165 |     29 |      136 |         17.576 |          1.3239 |               6.2086 |             48.498 |                  9 |           61.888 |            -30.099 |    350.87  |               2.734 |            25.189 |            29.315 |              11 |            12 |              23 |
| ETHUSD   | efficiency16h_ge0.45_ema0_init1.75atr_trail4atr |       334 |      194 |     63 |      131 |         32.474 |          1.3125 |               2.7292 |             21.831 |                  3 |           52.881 |            -15.856 |    190.826 |               4.564 |            25.168 |            22.141 |              15 |             8 |              23 |

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
