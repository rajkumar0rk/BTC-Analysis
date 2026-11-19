# Independent impulse-dislocation follow-through research

**Predeclared qualifying models: 0/64**

## Qualifying results
None

## Top models by 2025 performance (2026 reported without selecting on it)
| symbol   | model                                                 |   signals |   trades |   wins |   losses |   win_rate_pct |   profit_factor |   avg_win_loss_ratio |   biggest_winner_R |   winners_over_10R |   net_return_pct |   max_drawdown_pct |   fees_usd |   funding_proxy_usd |   return_2025_pct |   return_2026_pct |   profit_months |   loss_months |   active_months |
|:---------|:------------------------------------------------------|----------:|---------:|-------:|---------:|---------------:|----------------:|---------------------:|-------------------:|-------------------:|-----------------:|-------------------:|-----------:|--------------------:|------------------:|------------------:|----------------:|--------------:|----------------:|
| ETHUSD   | impulse2_volume1.5_reversal0_init1.25atr_trail10atr   |        80 |       73 |     14 |       59 |         19.178 |          1.9023 |               8.0168 |             30.928 |                  4 |           38.777 |            -15.917 |     46.706 |               1.14  |            33.664 |             3.825 |              12 |            11 |              23 |
| ETHUSD   | impulse2_volume1.5_reversal0_init1.75atr_trail10atr   |        80 |       70 |     17 |       53 |         24.286 |          1.8965 |               5.9125 |             22.092 |                  3 |           31.82  |            -12.332 |     30.691 |               2.092 |            28.92  |             2.25  |              12 |            11 |              23 |
| ETHUSD   | impulse2_volume1.5_reversal0_init1.25atr_trail6atr    |        80 |       75 |     17 |       58 |         22.667 |          1.9416 |               6.6244 |             28.49  |                  3 |           38     |            -12.263 |     47.018 |              -0.992 |            28.888 |             7.069 |              12 |            11 |              23 |
| ETHUSD   | impulse2_volume1.5_reversal0_init1.75atr_trail6atr    |        80 |       74 |     19 |       55 |         25.676 |          1.8943 |               5.4835 |             23.316 |                  3 |           30.865 |            -10.822 |     32.099 |               0.402 |            26.887 |             3.135 |              14 |             9 |              23 |
| ETHUSD   | impulse2_volume2.5_reversal0_init1.25atr_trail10atr   |        64 |       60 |     11 |       49 |         18.333 |          2.0307 |               9.0459 |             30.928 |                  3 |           34.436 |            -13.585 |     35.708 |              -1.317 |            25.988 |             6.705 |              10 |            13 |              23 |
| ETHUSD   | impulse1.5_volume2.5_reversal0_init1.25atr_trail6atr  |        92 |       85 |     21 |       64 |         24.706 |          1.7746 |               5.4084 |             28.49  |                  3 |           34.021 |            -12.007 |     52.881 |               0.479 |            23.783 |             8.271 |              11 |            12 |              23 |
| ETHUSD   | impulse1.5_volume2.5_reversal0_init1.25atr_trail10atr |        92 |       79 |     15 |       64 |         18.987 |          1.7065 |               7.2811 |             30.928 |                  3 |           30.48  |            -15.047 |     47.35  |               2.894 |            22.119 |             6.847 |              10 |            13 |              23 |
| ETHUSD   | impulse2_volume2.5_reversal0_init1.25atr_trail6atr    |        64 |       61 |     14 |       47 |         22.951 |          1.9801 |               6.6475 |             28.49  |                  2 |           30.798 |            -11.33  |     35.232 |              -2.207 |            20.877 |             8.208 |              10 |            13 |              23 |
| ETHUSD   | impulse2_volume2.5_reversal0_init1.75atr_trail10atr   |        64 |       60 |     13 |       47 |         21.667 |          1.8223 |               6.5884 |             22.092 |                  3 |           23.99  |            -11.839 |     24.182 |               0.62  |            20.584 |             2.824 |              11 |            12 |              23 |
| ETHUSD   | impulse1.5_volume2.5_reversal0_init1.75atr_trail6atr  |        92 |       85 |     23 |       62 |         27.059 |          1.627  |               4.3858 |             20.35  |                  3 |           23.322 |            -10.69  |     35.689 |               0.837 |            18.863 |             3.751 |              11 |            12 |              23 |
| ETHUSD   | impulse1.5_volume1.5_reversal0_init1.25atr_trail6atr  |       131 |      110 |     23 |       87 |         20.909 |          1.4606 |               5.5248 |             28.49  |                  4 |           25.706 |            -13.916 |     65.12  |               2.36  |            18.678 |             5.922 |              12 |            11 |              23 |
| ETHUSD   | impulse1.5_volume1.5_reversal0_init1.25atr_trail10atr |       131 |      102 |     17 |       85 |         16.667 |          1.3957 |               6.9783 |             30.928 |                  4 |           21.933 |            -18.273 |     59.107 |               4.091 |            18.625 |             2.789 |              11 |            12 |              23 |

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
