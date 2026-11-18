# Stage19 — Research NEW 1-hour pattern families for monthly consistency

This does not modify any previous Stage14, Stage18 or profit-lock strategies.
Seven new 1H price-action families, five pre-entry 4H regimes, 2/3R,
4h and 8h hold tested on Delta ETHUSD 1m, all months 2025/2026.
Structural 1H stops, conservative stop-first 1m replay, fee/GST/slip.

## Train selection and test outcome
Candidate family and conditions selected by 2025 month results only.
**2026 is previously research exposed and is not a pristine validation**.
Sampled models: 140; true 23-positive: 0.

## Top 2025-ranked configurations and 2026 behavior
| model                                                | pattern                | regime             |   target_R |   max_hold |   trades |   profitable_months_2025 |   losing_months_2025 |   no_trade_months_2025 |   modeled_2025_pct |   profitable_months_2026 |   losing_months_2026 |   no_trade_months_2026 |   modeled_2026_pct | all_23_positive   | useful_2025   |
|:-----------------------------------------------------|:-----------------------|:-------------------|-----------:|-----------:|---------:|-------------------------:|---------------------:|-----------------------:|-------------------:|-------------------------:|---------------------:|-----------------------:|-------------------:|:------------------|:--------------|
| failed_break_12h__4h_atr_ratio_le1__3R__480min       | failed_break_12h       | 4h_atr_ratio_le1   |          3 |        480 |      174 |                        8 |                    4 |                      0 |            11.7437 |                        3 |                    7 |                      1 |           -14.8508 | False             | False         |
| overextension_reversal__4h_atr_ratio_le1__3R__480min | overextension_reversal | 4h_atr_ratio_le1   |          3 |        480 |      290 |                        8 |                    4 |                      0 |            11.341  |                        4 |                    6 |                      1 |            -9.2672 | False             | False         |
| overextension_reversal__4h_atr_ratio_le1__2R__480min | overextension_reversal | 4h_atr_ratio_le1   |          2 |        480 |      291 |                        8 |                    4 |                      0 |             7.8491 |                        5 |                    5 |                      1 |            -4.9865 | False             | False         |
| ema20_pullback_confirm__all__3R__240min              | ema20_pullback_confirm | all                |          3 |        240 |      340 |                        8 |                    4 |                      0 |             3.0653 |                        2 |                    8 |                      1 |           -17.3983 | False             | False         |
| ema20_pullback_confirm__all__3R__480min              | ema20_pullback_confirm | all                |          3 |        480 |      325 |                        8 |                    4 |                      0 |            -2.6915 |                        1 |                    9 |                      1 |           -19.0689 | False             | False         |
| ema20_pullback_confirm__4h_atr_ratio_le1__3R__240min | ema20_pullback_confirm | 4h_atr_ratio_le1   |          3 |        240 |      224 |                        7 |                    5 |                      0 |             8.1271 |                        3 |                    7 |                      1 |           -11.0589 | False             | False         |
| failed_break_12h__4h_atr_ratio_le1__2R__480min       | failed_break_12h       | 4h_atr_ratio_le1   |          2 |        480 |      176 |                        7 |                    5 |                      0 |             7.2032 |                        2 |                    8 |                      1 |           -16.1875 | False             | False         |
| failed_break_12h__4h_adx_ge25__3R__480min            | failed_break_12h       | 4h_adx_ge25        |          3 |        480 |      123 |                        7 |                    5 |                      0 |             6.3355 |                        2 |                    8 |                      1 |            -9.1482 | False             | False         |
| ema20_pullback_confirm__4h_adx_le20__3R__240min      | ema20_pullback_confirm | 4h_adx_le20        |          3 |        240 |      140 |                        7 |                    4 |                      1 |             5.8896 |                        1 |                    9 |                      1 |            -9.7091 | False             | False         |
| failed_break_12h__4h_efficiency_ge30__3R__480min     | failed_break_12h       | 4h_efficiency_ge30 |          3 |        480 |      149 |                        7 |                    5 |                      0 |             4.978  |                        5 |                    5 |                      1 |            -2.0854 | False             | False         |
| strong_momentum_6h__4h_adx_le20__3R__480min          | strong_momentum_6h     | 4h_adx_le20        |          3 |        480 |       85 |                        7 |                    4 |                      1 |             3.7248 |                        2 |                    8 |                      1 |            -4.6538 | False             | False         |
| ema20_pullback_confirm__4h_adx_le20__2R__480min      | ema20_pullback_confirm | 4h_adx_le20        |          2 |        480 |      137 |                        7 |                    4 |                      1 |             3.2933 |                        2 |                    8 |                      1 |            -9.3687 | False             | False         |
| strong_momentum_6h__4h_atr_ratio_le1__3R__240min     | strong_momentum_6h     | 4h_atr_ratio_le1   |          3 |        240 |      134 |                        7 |                    5 |                      0 |             2.4406 |                        4 |                    6 |                      1 |            -1.3252 | False             | False         |
| failed_break_12h__4h_adx_ge25__2R__240min            | failed_break_12h       | 4h_adx_ge25        |          2 |        240 |      125 |                        7 |                    5 |                      0 |             1.3421 |                        1 |                    9 |                      1 |            -7.4961 | False             | False         |
| failed_break_12h__4h_efficiency_ge30__2R__480min     | failed_break_12h       | 4h_efficiency_ge30 |          2 |        480 |      150 |                        7 |                    5 |                      0 |             0.643  |                        3 |                    7 |                      1 |            -5.6576 | False             | False         |
| strong_momentum_6h__4h_atr_ratio_le1__2R__240min     | strong_momentum_6h     | 4h_atr_ratio_le1   |          2 |        240 |      135 |                        7 |                    5 |                      0 |             0.1747 |                        4 |                    6 |                      1 |            -1.971  | False             | False         |
| ema20_pullback_confirm__all__2R__240min              | ema20_pullback_confirm | all                |          2 |        240 |      341 |                        7 |                    5 |                      0 |            -1.4664 |                        2 |                    8 |                      1 |           -13.4407 | False             | False         |
| inside_bar_breakout__4h_adx_ge25__2R__480min         | inside_bar_breakout    | 4h_adx_ge25        |          2 |        480 |      308 |                        7 |                    5 |                      0 |           -11.6666 |                        1 |                    9 |                      1 |           -21.8845 | False             | False         |
| ema20_pullback_confirm__4h_adx_le20__3R__480min      | ema20_pullback_confirm | 4h_adx_le20        |          3 |        480 |      136 |                        6 |                    5 |                      1 |             5.842  |                        2 |                    8 |                      1 |           -11.4652 | False             | False         |
| ema20_pullback_confirm__4h_atr_ratio_le1__2R__240min | ema20_pullback_confirm | 4h_atr_ratio_le1   |          2 |        240 |      225 |                        6 |                    6 |                      0 |             4.0409 |                        4 |                    6 |                      1 |            -8.6134 | False             | False         |

## Monthly performance (top 5)
| model                                                | month_ist   |   trades |    net_R |   modeled_return_pct | status    |
|:-----------------------------------------------------|:------------|---------:|---------:|---------------------:|:----------|
| ema20_pullback_confirm__all__3R__240min              | 2025-01     |       11 |   2.3037 |               1.1393 | Profit    |
| ema20_pullback_confirm__all__3R__240min              | 2025-02     |        9 |   1.6557 |               0.8027 | Profit    |
| ema20_pullback_confirm__all__3R__240min              | 2025-03     |       18 |   2.4236 |               1.2095 | Profit    |
| ema20_pullback_confirm__all__3R__240min              | 2025-04     |       15 |  -7.8763 |              -3.8792 | Loss      |
| ema20_pullback_confirm__all__3R__240min              | 2025-05     |       18 |   2.7272 |               1.3349 | Profit    |
| ema20_pullback_confirm__all__3R__240min              | 2025-06     |       18 |  -4.4284 |              -2.2031 | Loss      |
| ema20_pullback_confirm__all__3R__240min              | 2025-07     |       11 |   0.5573 |               0.2587 | Profit    |
| ema20_pullback_confirm__all__3R__240min              | 2025-08     |        6 |   1.9907 |               0.9852 | Profit    |
| ema20_pullback_confirm__all__3R__240min              | 2025-09     |       13 |  -2.4188 |              -1.2288 | Loss      |
| ema20_pullback_confirm__all__3R__240min              | 2025-10     |       10 |  -1.1373 |              -0.5844 | Loss      |
| ema20_pullback_confirm__all__3R__240min              | 2025-11     |        7 |   2.2037 |               1.0914 | Profit    |
| ema20_pullback_confirm__all__3R__240min              | 2025-12     |       20 |   8.6231 |               4.3324 | Profit    |
| ema20_pullback_confirm__all__3R__240min              | 2026-01     |       18 |   4.5752 |               2.2903 | Profit    |
| ema20_pullback_confirm__all__3R__240min              | 2026-02     |       11 |   0.2421 |               0.1092 | Profit    |
| ema20_pullback_confirm__all__3R__240min              | 2026-03     |       13 |  -2.8306 |              -1.4114 | Loss      |
| ema20_pullback_confirm__all__3R__240min              | 2026-04     |       17 |  -3.711  |              -1.8459 | Loss      |
| ema20_pullback_confirm__all__3R__240min              | 2026-05     |       26 |  -3.1634 |              -1.5921 | Loss      |
| ema20_pullback_confirm__all__3R__240min              | 2026-06     |       14 |  -1.6942 |              -0.8607 | Loss      |
| ema20_pullback_confirm__all__3R__240min              | 2026-07     |       17 |  -8.7832 |              -4.3176 | Loss      |
| ema20_pullback_confirm__all__3R__240min              | 2026-08     |       23 |  -9.3149 |              -4.5678 | Loss      |
| ema20_pullback_confirm__all__3R__240min              | 2026-09     |       20 |  -5.0895 |              -2.5417 | Loss      |
| ema20_pullback_confirm__all__3R__240min              | 2026-10     |       25 |  -8.0958 |              -3.9884 | Loss      |
| ema20_pullback_confirm__all__3R__240min              | 2026-11     |        0 |   0      |               0      | No trades |
| ema20_pullback_confirm__all__3R__480min              | 2025-01     |       11 |   1.0383 |               0.4857 | Profit    |
| ema20_pullback_confirm__all__3R__480min              | 2025-02     |        9 |   0.7901 |               0.3669 | Profit    |
| ema20_pullback_confirm__all__3R__480min              | 2025-03     |       17 |  -3.4784 |              -1.74   | Loss      |
| ema20_pullback_confirm__all__3R__480min              | 2025-04     |       14 | -10.5439 |              -5.153  | Loss      |
| ema20_pullback_confirm__all__3R__480min              | 2025-05     |       19 |   1.5608 |               0.7262 | Profit    |
| ema20_pullback_confirm__all__3R__480min              | 2025-06     |       17 |  -4.1367 |              -2.0712 | Loss      |
| ema20_pullback_confirm__all__3R__480min              | 2025-07     |       11 |   2.6446 |               1.2925 | Profit    |
| ema20_pullback_confirm__all__3R__480min              | 2025-08     |        6 |   3.0101 |               1.4904 | Profit    |
| ema20_pullback_confirm__all__3R__480min              | 2025-09     |       13 |  -6.8148 |              -3.3857 | Loss      |
| ema20_pullback_confirm__all__3R__480min              | 2025-10     |        9 |   0.7291 |               0.3373 | Profit    |
| ema20_pullback_confirm__all__3R__480min              | 2025-11     |        7 |   0.2744 |               0.1084 | Profit    |
| ema20_pullback_confirm__all__3R__480min              | 2025-12     |       19 |  10.3091 |               5.2027 | Profit    |
| ema20_pullback_confirm__all__3R__480min              | 2026-01     |       16 |   5.6557 |               2.8266 | Profit    |
| ema20_pullback_confirm__all__3R__480min              | 2026-02     |       11 |  -1.8568 |              -0.9371 | Loss      |
| ema20_pullback_confirm__all__3R__480min              | 2026-03     |       11 |  -3.7865 |              -1.8899 | Loss      |
| ema20_pullback_confirm__all__3R__480min              | 2026-04     |       17 |  -2.4137 |              -1.2231 | Loss      |
| ema20_pullback_confirm__all__3R__480min              | 2026-05     |       24 |  -2.8327 |              -1.448  | Loss      |
| ema20_pullback_confirm__all__3R__480min              | 2026-06     |       14 |  -3.7439 |              -1.8696 | Loss      |
| ema20_pullback_confirm__all__3R__480min              | 2026-07     |       16 |  -8.6415 |              -4.2516 | Loss      |
| ema20_pullback_confirm__all__3R__480min              | 2026-08     |       21 |  -8.4979 |              -4.185  | Loss      |
| ema20_pullback_confirm__all__3R__480min              | 2026-09     |       20 |  -9.6545 |              -4.7475 | Loss      |
| ema20_pullback_confirm__all__3R__480min              | 2026-10     |       23 |  -5.9796 |              -2.9895 | Loss      |
| ema20_pullback_confirm__all__3R__480min              | 2026-11     |        0 |   0      |               0      | No trades |
| failed_break_12h__4h_atr_ratio_le1__3R__480min       | 2025-01     |        7 |   7.7027 |               3.8998 | Profit    |
| failed_break_12h__4h_atr_ratio_le1__3R__480min       | 2025-02     |        5 |   1.5765 |               0.7775 | Profit    |
| failed_break_12h__4h_atr_ratio_le1__3R__480min       | 2025-03     |        9 |   7.2077 |               3.6436 | Profit    |
| failed_break_12h__4h_atr_ratio_le1__3R__480min       | 2025-04     |        7 |  -0.2094 |              -0.1155 | Loss      |
| failed_break_12h__4h_atr_ratio_le1__3R__480min       | 2025-05     |       12 |  -6.2011 |              -3.0649 | Loss      |
| failed_break_12h__4h_atr_ratio_le1__3R__480min       | 2025-06     |       11 |   1.5464 |               0.7461 | Profit    |
| failed_break_12h__4h_atr_ratio_le1__3R__480min       | 2025-07     |        6 |  -2.7455 |              -1.3721 | Loss      |
| failed_break_12h__4h_atr_ratio_le1__3R__480min       | 2025-08     |        8 |   5.2469 |               2.6313 | Profit    |
| failed_break_12h__4h_atr_ratio_le1__3R__480min       | 2025-09     |       10 |   3.6091 |               1.7893 | Profit    |
| failed_break_12h__4h_atr_ratio_le1__3R__480min       | 2025-10     |        7 |  -2.9543 |              -1.4768 | Loss      |
| failed_break_12h__4h_atr_ratio_le1__3R__480min       | 2025-11     |        8 |   6.1639 |               3.1032 | Profit    |
| failed_break_12h__4h_atr_ratio_le1__3R__480min       | 2025-12     |        4 |   1.7135 |               0.8562 | Profit    |
| failed_break_12h__4h_atr_ratio_le1__3R__480min       | 2026-01     |        7 |   3.8812 |               1.936  | Profit    |
| failed_break_12h__4h_atr_ratio_le1__3R__480min       | 2026-02     |        6 |  -0.5498 |              -0.2903 | Loss      |
| failed_break_12h__4h_atr_ratio_le1__3R__480min       | 2026-03     |       10 |  -9.2181 |              -4.5169 | Loss      |
| failed_break_12h__4h_atr_ratio_le1__3R__480min       | 2026-04     |        6 |  -2.4779 |              -1.247  | Loss      |
| failed_break_12h__4h_atr_ratio_le1__3R__480min       | 2026-05     |        7 |   2.5629 |               1.2646 | Profit    |
| failed_break_12h__4h_atr_ratio_le1__3R__480min       | 2026-06     |        8 |  -7.0818 |              -3.4922 | Loss      |
| failed_break_12h__4h_atr_ratio_le1__3R__480min       | 2026-07     |        9 |  -2.1065 |              -1.0698 | Loss      |
| failed_break_12h__4h_atr_ratio_le1__3R__480min       | 2026-08     |        7 |   0.6919 |               0.3282 | Profit    |
| failed_break_12h__4h_atr_ratio_le1__3R__480min       | 2026-09     |        8 |  -7.5868 |              -3.7334 | Loss      |
| failed_break_12h__4h_atr_ratio_le1__3R__480min       | 2026-10     |       12 |  -9.9042 |              -4.8537 | Loss      |
| failed_break_12h__4h_atr_ratio_le1__3R__480min       | 2026-11     |        0 |   0      |               0      | No trades |
| overextension_reversal__4h_atr_ratio_le1__2R__480min | 2025-01     |        8 |   1.2426 |               0.6099 | Profit    |
| overextension_reversal__4h_atr_ratio_le1__2R__480min | 2025-02     |        7 |  -3.2357 |              -1.6168 | Loss      |
| overextension_reversal__4h_atr_ratio_le1__2R__480min | 2025-03     |       19 |   1.7829 |               0.8556 | Profit    |
| overextension_reversal__4h_atr_ratio_le1__2R__480min | 2025-04     |       11 |   6.2477 |               3.1511 | Profit    |
| overextension_reversal__4h_atr_ratio_le1__2R__480min | 2025-05     |       12 |  -1.7652 |              -0.8981 | Loss      |
| overextension_reversal__4h_atr_ratio_le1__2R__480min | 2025-06     |       13 |   4.2445 |               2.1227 | Profit    |
| overextension_reversal__4h_atr_ratio_le1__2R__480min | 2025-07     |       12 |  -3.3258 |              -1.6676 | Loss      |
| overextension_reversal__4h_atr_ratio_le1__2R__480min | 2025-08     |       12 |   0.2562 |               0.101  | Profit    |
| overextension_reversal__4h_atr_ratio_le1__2R__480min | 2025-09     |       14 |  -2.9682 |              -1.4904 | Loss      |
| overextension_reversal__4h_atr_ratio_le1__2R__480min | 2025-10     |       12 |   2.2421 |               1.0975 | Profit    |
| overextension_reversal__4h_atr_ratio_le1__2R__480min | 2025-11     |       15 |   3.6843 |               1.8335 | Profit    |
| overextension_reversal__4h_atr_ratio_le1__2R__480min | 2025-12     |        8 |   7.246  |               3.6647 | Profit    |
| overextension_reversal__4h_atr_ratio_le1__2R__480min | 2026-01     |       12 |  -3.349  |              -1.6867 | Loss      |
| overextension_reversal__4h_atr_ratio_le1__2R__480min | 2026-02     |       15 |   4.1072 |               2.0347 | Profit    |
| overextension_reversal__4h_atr_ratio_le1__2R__480min | 2026-03     |       21 | -17.7353 |              -8.5105 | Loss      |
| overextension_reversal__4h_atr_ratio_le1__2R__480min | 2026-04     |       13 |   3.1218 |               1.5376 | Profit    |
| overextension_reversal__4h_atr_ratio_le1__2R__480min | 2026-05     |       14 |   0.0084 |              -0.0252 | Loss      |
| overextension_reversal__4h_atr_ratio_le1__2R__480min | 2026-06     |       11 |   0.9602 |               0.4639 | Profit    |
| overextension_reversal__4h_atr_ratio_le1__2R__480min | 2026-07     |       16 |  -1.7811 |              -0.9169 | Loss      |
| overextension_reversal__4h_atr_ratio_le1__2R__480min | 2026-08     |       11 |   2.3078 |               1.1372 | Profit    |
| overextension_reversal__4h_atr_ratio_le1__2R__480min | 2026-09     |       17 |  -2.9291 |              -1.4884 | Loss      |
| overextension_reversal__4h_atr_ratio_le1__2R__480min | 2026-10     |       18 |   5.6534 |               2.832  | Profit    |
| overextension_reversal__4h_atr_ratio_le1__2R__480min | 2026-11     |        0 |   0      |               0      | No trades |
| overextension_reversal__4h_atr_ratio_le1__3R__480min | 2025-01     |        8 |   1.178  |               0.5777 | Profit    |
| overextension_reversal__4h_atr_ratio_le1__3R__480min | 2025-02     |        7 |  -2.2351 |              -1.1289 | Loss      |
| overextension_reversal__4h_atr_ratio_le1__3R__480min | 2025-03     |       19 |   2.9557 |               1.4395 | Profit    |
| overextension_reversal__4h_atr_ratio_le1__3R__480min | 2025-04     |       11 |   5.1564 |               2.5814 | Profit    |
| overextension_reversal__4h_atr_ratio_le1__3R__480min | 2025-05     |       12 |  -2.0473 |              -1.0396 | Loss      |
| overextension_reversal__4h_atr_ratio_le1__3R__480min | 2025-06     |       13 |   3.2427 |               1.6021 | Profit    |
| overextension_reversal__4h_atr_ratio_le1__3R__480min | 2025-07     |       12 |  -2.3252 |              -1.1801 | Loss      |
| overextension_reversal__4h_atr_ratio_le1__3R__480min | 2025-08     |       12 |   2.8385 |               1.3864 | Profit    |
| overextension_reversal__4h_atr_ratio_le1__3R__480min | 2025-09     |       14 |  -2.9229 |              -1.4682 | Loss      |
| overextension_reversal__4h_atr_ratio_le1__3R__480min | 2025-10     |       12 |   4.6976 |               2.3318 | Profit    |
| overextension_reversal__4h_atr_ratio_le1__3R__480min | 2025-11     |       15 |   5.4159 |               2.7091 | Profit    |
| overextension_reversal__4h_atr_ratio_le1__3R__480min | 2025-12     |        7 |   6.2374 |               3.1394 | Profit    |
| overextension_reversal__4h_atr_ratio_le1__3R__480min | 2026-01     |       12 |  -3.2418 |              -1.6361 | Loss      |
| overextension_reversal__4h_atr_ratio_le1__3R__480min | 2026-02     |       15 |   0.7617 |               0.3445 | Profit    |
| overextension_reversal__4h_atr_ratio_le1__3R__480min | 2026-03     |       21 | -17.7353 |              -8.5105 | Loss      |
| overextension_reversal__4h_atr_ratio_le1__3R__480min | 2026-04     |       13 |  -3.1018 |              -1.5663 | Loss      |
| overextension_reversal__4h_atr_ratio_le1__3R__480min | 2026-05     |       14 |   3.3319 |               1.6313 | Profit    |
| overextension_reversal__4h_atr_ratio_le1__3R__480min | 2026-06     |       11 |  -2.0415 |              -1.0301 | Loss      |
| overextension_reversal__4h_atr_ratio_le1__3R__480min | 2026-07     |       16 |  -1.161  |              -0.6131 | Loss      |
| overextension_reversal__4h_atr_ratio_le1__3R__480min | 2026-08     |       11 |   1.306  |               0.6225 | Profit    |
| overextension_reversal__4h_atr_ratio_le1__3R__480min | 2026-09     |       17 |  -3.1103 |              -1.5782 | Loss      |
| overextension_reversal__4h_atr_ratio_le1__3R__480min | 2026-10     |       18 |   6.2011 |               3.1037 | Profit    |
| overextension_reversal__4h_atr_ratio_le1__3R__480min | 2026-11     |        0 |   0      |               0      | No trades |

## Caveats
- All historical 2026 data was used previously; not pristine forward holdout
- Multiple hypothesis testing across entry families and risk parameters
- Missing 1m source day 2026-10-31; simulations censor entries near source gaps
- 1m OHLC stop-first; unmodeled funding, spread, impact and liquidation
- Months with no trade are not counted as profitable
- Account percentage is a hypothetical constant-risk sizing model
- Each configuration is exclusive-position standalone; do not sum overlapping models
- No daily/weekly guard; no guaranteed monthly return
Use exact monthly CSV and full ledger for evidence and portfolio experiments.
