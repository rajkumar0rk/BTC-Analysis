# Independent liquidity sweep reclaim reversal strategy research

**Predeclared qualifying models: 0/64**

## Qualifying results
None

## Top models by 2025 performance (2026 reported without selecting on it)
| symbol   | model                                        |   signals |   trades |   wins |   losses |   win_rate_pct |   profit_factor |   avg_win_loss_ratio |   biggest_winner_R |   winners_over_10R |   net_return_pct |   max_drawdown_pct |   fees_usd |   funding_proxy_usd |   return_2025_pct |   return_2026_pct |   profit_months |   loss_months |   active_months |
|:---------|:---------------------------------------------|----------:|---------:|-------:|---------:|---------------:|----------------:|---------------------:|-------------------:|-------------------:|-----------------:|-------------------:|-----------:|--------------------:|------------------:|------------------:|----------------:|--------------:|----------------:|
| ETHUSD   | sweep96_depth0.2_ema0_init0.75atr_trail12atr |        68 |       60 |     10 |       50 |         16.667 |          1.764  |               8.8202 |             26.014 |                  5 |           25.049 |            -14.638 |     54.543 |              -4.905 |            29.128 |            -3.159 |               7 |            14 |              21 |
| ETHUSD   | sweep96_depth0.2_ema0_init0.75atr_trail8atr  |        68 |       63 |     15 |       48 |         23.81  |          1.8221 |               5.8306 |             30.923 |                  3 |           27.809 |            -14.547 |     58.658 |              -4.147 |            28.813 |            -0.779 |               8 |            13 |              21 |
| ETHUSD   | sweep48_depth0.2_ema0_init0.75atr_trail12atr |       108 |       97 |     10 |       87 |         10.309 |          0.9886 |               8.6011 |             26.014 |                  5 |           -0.604 |            -24.133 |     86.955 |              -3.887 |            16.594 |           -14.751 |               6 |            17 |              23 |
| ETHUSD   | sweep48_depth0.2_ema0_init0.75atr_trail8atr  |       108 |      103 |     16 |       87 |         15.534 |          1.0243 |               5.5698 |             30.923 |                  3 |            1.358 |            -22.939 |     94.844 |              -3.549 |            15.988 |           -12.613 |               8 |            15 |              23 |
| ETHUSD   | sweep96_depth0.2_ema0_init1.25atr_trail12atr |        68 |       59 |     13 |       46 |         22.034 |          1.3023 |               4.6082 |             15.609 |                  2 |            7.71  |            -11     |     29.041 |              -3.835 |            13.563 |            -5.154 |               7 |            14 |              21 |
| ETHUSD   | sweep96_depth0.2_ema0_init1.25atr_trail8atr  |        68 |       62 |     19 |       43 |         30.645 |          1.6144 |               3.6536 |             18.554 |                  2 |           15.794 |             -9.609 |     31.373 |              -2.78  |            13.521 |             2.002 |              10 |            11 |              21 |
| ETHUSD   | sweep96_depth0.2_ema1_init0.75atr_trail8atr  |         4 |        4 |      2 |        2 |         50     |          6.5449 |               6.5449 |             14.053 |                  1 |            7.213 |             -5.35  |      3.051 |               0.259 |             7.87  |            -0.609 |               2 |             2 |               4 |
| ETHUSD   | sweep96_depth0.4_ema1_init0.75atr_trail8atr  |         3 |        3 |      2 |        1 |         66.667 |         13.2313 |               6.6156 |             14.053 |                  1 |            7.87  |             -5.35  |      1.919 |               0.403 |             7.87  |             0     |               2 |             1 |               3 |
| ETHUSD   | sweep96_depth0.4_ema1_init0.75atr_trail12atr |         3 |        2 |      1 |        1 |         50     |         40.519  |              40.519  |             15.238 |                  1 |            7.431 |             -6.802 |      1.203 |               0.199 |             7.431 |             0     |               2 |             1 |               3 |
| ETHUSD   | sweep96_depth0.2_ema1_init0.75atr_trail12atr |         4 |        3 |      1 |        2 |         33.333 |          9.0409 |              18.0818 |             15.238 |                  1 |            6.776 |             -6.802 |      2.33  |               0.055 |             7.431 |            -0.609 |               2 |             2 |               4 |
| ETHUSD   | sweep48_depth0.2_ema0_init1.25atr_trail8atr  |       108 |      100 |     24 |       76 |         24     |          1.046  |               3.3125 |             18.554 |                  2 |            1.982 |            -15.992 |     52.879 |              -3.254 |             6.495 |            -4.237 |              11 |            12 |              23 |
| ETHUSD   | sweep48_depth0.2_ema0_init1.25atr_trail12atr |       108 |       92 |     17 |       75 |         18.478 |          0.8992 |               3.967  |             15.609 |                  2 |           -4.042 |            -20.94  |     46.366 |              -4.338 |             6.111 |            -9.568 |               7 |            16 |              23 |

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
