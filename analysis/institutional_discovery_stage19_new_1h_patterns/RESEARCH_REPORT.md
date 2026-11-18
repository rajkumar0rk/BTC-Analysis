# Stage19 — Research NEW 1-hour pattern families for monthly consistency

This does not modify any previous Stage14, Stage18 or profit-lock strategies.
Seven new 1H price-action families, five pre-entry 4H regimes, 2/3R,
4h and 8h hold tested on Delta BTCUSD 1m, all months 2025/2026.
Structural 1H stops, conservative stop-first 1m replay, fee/GST/slip.

## Train selection and test outcome
Candidate family and conditions selected by 2025 month results only.
**2026 is previously research exposed and is not a pristine validation**.
Sampled models: 140; true 23-positive: 0.

## Top 2025-ranked configurations and 2026 behavior
| model                                                   | pattern                   | regime             |   target_R |   max_hold |   trades |   profitable_months_2025 |   losing_months_2025 |   no_trade_months_2025 |   modeled_2025_pct |   profitable_months_2026 |   losing_months_2026 |   no_trade_months_2026 |   modeled_2026_pct | all_23_positive   | useful_2025   |
|:--------------------------------------------------------|:--------------------------|:-------------------|-----------:|-----------:|---------:|-------------------------:|---------------------:|-----------------------:|-------------------:|-------------------------:|---------------------:|-----------------------:|-------------------:|:------------------|:--------------|
| strong_momentum_6h__4h_adx_le20__2R__480min             | strong_momentum_6h        | 4h_adx_le20        |          2 |        480 |      119 |                        8 |                    3 |                      1 |            -4.1168 |                        2 |                    8 |                      1 |            -5.3173 | False             | False         |
| strong_momentum_6h__4h_efficiency_ge30__2R__480min      | strong_momentum_6h        | 4h_efficiency_ge30 |          2 |        480 |      200 |                        6 |                    6 |                      0 |            -2.3202 |                        4 |                    7 |                      0 |            -9.3337 | False             | False         |
| compression_expansion_12h__4h_atr_ratio_le1__2R__480min | compression_expansion_12h | 4h_atr_ratio_le1   |          2 |        480 |       41 |                        6 |                    6 |                      0 |            -3.9018 |                        4 |                    3 |                      4 |             0.2509 | False             | False         |
| compression_expansion_12h__4h_atr_ratio_le1__3R__480min | compression_expansion_12h | 4h_atr_ratio_le1   |          3 |        480 |       41 |                        6 |                    6 |                      0 |            -3.9145 |                        4 |                    3 |                      4 |             0.9068 | False             | False         |
| strong_momentum_6h__4h_adx_le20__3R__480min             | strong_momentum_6h        | 4h_adx_le20        |          3 |        480 |      119 |                        6 |                    5 |                      1 |            -4.1233 |                        2 |                    8 |                      1 |            -6.7986 | False             | False         |
| ema20_pullback_confirm__4h_efficiency_ge30__3R__480min  | ema20_pullback_confirm    | 4h_efficiency_ge30 |          3 |        480 |      199 |                        6 |                    6 |                      0 |            -7.2824 |                        4 |                    7 |                      0 |            -1.0981 | False             | False         |
| strong_momentum_6h__4h_efficiency_ge30__3R__480min      | strong_momentum_6h        | 4h_efficiency_ge30 |          3 |        480 |      199 |                        5 |                    7 |                      0 |            -0.794  |                        2 |                    9 |                      0 |            -9.0562 | False             | False         |
| strong_momentum_6h__4h_efficiency_ge30__3R__240min      | strong_momentum_6h        | 4h_efficiency_ge30 |          3 |        240 |      205 |                        5 |                    7 |                      0 |            -1.3715 |                        4 |                    7 |                      0 |            -3.4035 | False             | False         |
| compression_expansion_12h__4h_adx_le20__3R__480min      | compression_expansion_12h | 4h_adx_le20        |          3 |        480 |       17 |                        5 |                    6 |                      1 |            -1.5896 |                        0 |                    3 |                      8 |            -1.8442 | False             | False         |
| compression_expansion_12h__4h_adx_le20__2R__480min      | compression_expansion_12h | 4h_adx_le20        |          2 |        480 |       17 |                        5 |                    6 |                      1 |            -1.8351 |                        0 |                    3 |                      8 |            -1.8442 | False             | False         |
| compression_expansion_12h__4h_atr_ratio_le1__2R__240min | compression_expansion_12h | 4h_atr_ratio_le1   |          2 |        240 |       41 |                        5 |                    7 |                      0 |            -2.5354 |                        5 |                    3 |                      3 |             1.0218 | False             | False         |
| compression_expansion_12h__4h_atr_ratio_le1__3R__240min | compression_expansion_12h | 4h_atr_ratio_le1   |          3 |        240 |       41 |                        5 |                    7 |                      0 |            -2.7592 |                        5 |                    3 |                      3 |             1.5224 | False             | False         |
| compression_expansion_12h__all__2R__240min              | compression_expansion_12h | all                |          2 |        240 |       59 |                        5 |                    7 |                      0 |            -3.225  |                        7 |                    4 |                      0 |             2.8578 | False             | False         |
| compression_expansion_12h__all__3R__240min              | compression_expansion_12h | all                |          3 |        240 |       59 |                        5 |                    7 |                      0 |            -3.4471 |                        7 |                    4 |                      0 |             4.9116 | False             | False         |
| strong_momentum_6h__4h_adx_le20__3R__240min             | strong_momentum_6h        | 4h_adx_le20        |          3 |        240 |      126 |                        5 |                    6 |                      1 |            -3.5802 |                        2 |                    7 |                      2 |            -3.1399 | False             | False         |
| ema20_pullback_confirm__4h_adx_le20__3R__480min         | ema20_pullback_confirm    | 4h_adx_le20        |          3 |        480 |      139 |                        5 |                    6 |                      1 |            -4.3672 |                        4 |                    6 |                      1 |            -7.9133 | False             | False         |
| ema20_pullback_confirm__4h_adx_ge25__3R__480min         | ema20_pullback_confirm    | 4h_adx_ge25        |          3 |        480 |      216 |                        5 |                    7 |                      0 |            -4.4939 |                        4 |                    7 |                      0 |            -8.3651 | False             | False         |
| strong_momentum_6h__4h_adx_le20__2R__240min             | strong_momentum_6h        | 4h_adx_le20        |          2 |        240 |      126 |                        5 |                    6 |                      1 |            -4.7823 |                        2 |                    7 |                      2 |            -3.0578 | False             | False         |
| strong_momentum_6h__4h_atr_ratio_le1__2R__480min        | strong_momentum_6h        | 4h_atr_ratio_le1   |          2 |        480 |      233 |                        5 |                    7 |                      0 |            -5.5165 |                        2 |                    9 |                      0 |           -12.254  | False             | False         |
| ema20_pullback_confirm__4h_efficiency_ge30__3R__240min  | ema20_pullback_confirm    | 4h_efficiency_ge30 |          3 |        240 |      211 |                        5 |                    7 |                      0 |            -8.1552 |                        4 |                    7 |                      0 |            -3.6622 | False             | False         |

## Monthly performance (top 5)
| model                                                   | month_ist   |   trades |   net_R |   modeled_return_pct | status    |
|:--------------------------------------------------------|:------------|---------:|--------:|---------------------:|:----------|
| compression_expansion_12h__4h_atr_ratio_le1__2R__480min | 2025-01     |        1 | -0.7153 |              -0.3576 | Loss      |
| compression_expansion_12h__4h_atr_ratio_le1__2R__480min | 2025-02     |        2 | -2.2819 |              -1.1377 | Loss      |
| compression_expansion_12h__4h_atr_ratio_le1__2R__480min | 2025-03     |        1 |  1.3997 |               0.6998 | Profit    |
| compression_expansion_12h__4h_atr_ratio_le1__2R__480min | 2025-04     |        1 |  0.7742 |               0.3871 | Profit    |
| compression_expansion_12h__4h_atr_ratio_le1__2R__480min | 2025-05     |        1 | -1.1232 |              -0.5616 | Loss      |
| compression_expansion_12h__4h_atr_ratio_le1__2R__480min | 2025-06     |        5 | -4.1668 |              -2.0678 | Loss      |
| compression_expansion_12h__4h_atr_ratio_le1__2R__480min | 2025-07     |        1 |  0.6808 |               0.3404 | Profit    |
| compression_expansion_12h__4h_atr_ratio_le1__2R__480min | 2025-08     |        1 |  1.799  |               0.8995 | Profit    |
| compression_expansion_12h__4h_atr_ratio_le1__2R__480min | 2025-09     |        1 |  0.073  |               0.0365 | Profit    |
| compression_expansion_12h__4h_atr_ratio_le1__2R__480min | 2025-10     |        2 | -2.4103 |              -1.2016 | Loss      |
| compression_expansion_12h__4h_atr_ratio_le1__2R__480min | 2025-11     |        3 | -2.6635 |              -1.3265 | Loss      |
| compression_expansion_12h__4h_atr_ratio_le1__2R__480min | 2025-12     |        2 |  0.7402 |               0.3646 | Profit    |
| compression_expansion_12h__4h_atr_ratio_le1__2R__480min | 2026-01     |        0 |  0      |               0      | No trades |
| compression_expansion_12h__4h_atr_ratio_le1__2R__480min | 2026-02     |        4 |  1.9336 |               0.963  | Profit    |
| compression_expansion_12h__4h_atr_ratio_le1__2R__480min | 2026-03     |        0 |  0      |               0      | No trades |
| compression_expansion_12h__4h_atr_ratio_le1__2R__480min | 2026-04     |        2 |  1.2625 |               0.6283 | Profit    |
| compression_expansion_12h__4h_atr_ratio_le1__2R__480min | 2026-05     |        2 |  0.0221 |               0.011  | Profit    |
| compression_expansion_12h__4h_atr_ratio_le1__2R__480min | 2026-06     |        0 |  0      |               0      | No trades |
| compression_expansion_12h__4h_atr_ratio_le1__2R__480min | 2026-07     |        5 | -1.6176 |              -0.8096 | Loss      |
| compression_expansion_12h__4h_atr_ratio_le1__2R__480min | 2026-08     |        1 | -1.1734 |              -0.5867 | Loss      |
| compression_expansion_12h__4h_atr_ratio_le1__2R__480min | 2026-09     |        3 | -0.8346 |              -0.4187 | Loss      |
| compression_expansion_12h__4h_atr_ratio_le1__2R__480min | 2026-10     |        3 |  0.9596 |               0.4769 | Profit    |
| compression_expansion_12h__4h_atr_ratio_le1__2R__480min | 2026-11     |        0 |  0      |               0      | No trades |
| compression_expansion_12h__4h_atr_ratio_le1__3R__480min | 2025-01     |        1 | -0.7153 |              -0.3576 | Loss      |
| compression_expansion_12h__4h_atr_ratio_le1__3R__480min | 2025-02     |        2 | -2.2819 |              -1.1377 | Loss      |
| compression_expansion_12h__4h_atr_ratio_le1__3R__480min | 2025-03     |        1 |  2.3991 |               1.1996 | Profit    |
| compression_expansion_12h__4h_atr_ratio_le1__3R__480min | 2025-04     |        1 |  0.7742 |               0.3871 | Profit    |
| compression_expansion_12h__4h_atr_ratio_le1__3R__480min | 2025-05     |        1 | -1.1232 |              -0.5616 | Loss      |
| compression_expansion_12h__4h_atr_ratio_le1__3R__480min | 2025-06     |        5 | -4.1668 |              -2.0678 | Loss      |
| compression_expansion_12h__4h_atr_ratio_le1__3R__480min | 2025-07     |        1 |  0.6808 |               0.3404 | Profit    |
| compression_expansion_12h__4h_atr_ratio_le1__3R__480min | 2025-08     |        1 |  1.2689 |               0.6345 | Profit    |
| compression_expansion_12h__4h_atr_ratio_le1__3R__480min | 2025-09     |        1 |  0.073  |               0.0365 | Profit    |
| compression_expansion_12h__4h_atr_ratio_le1__3R__480min | 2025-10     |        2 | -2.4103 |              -1.2016 | Loss      |
| compression_expansion_12h__4h_atr_ratio_le1__3R__480min | 2025-11     |        3 | -2.6635 |              -1.3265 | Loss      |
| compression_expansion_12h__4h_atr_ratio_le1__3R__480min | 2025-12     |        2 |  0.2457 |               0.1188 | Profit    |
| compression_expansion_12h__4h_atr_ratio_le1__3R__480min | 2026-01     |        0 |  0      |               0      | No trades |
| compression_expansion_12h__4h_atr_ratio_le1__3R__480min | 2026-02     |        4 |  2.9342 |               1.4632 | Profit    |
| compression_expansion_12h__4h_atr_ratio_le1__3R__480min | 2026-03     |        0 |  0      |               0      | No trades |
| compression_expansion_12h__4h_atr_ratio_le1__3R__480min | 2026-04     |        2 |  1.5814 |               0.7872 | Profit    |
| compression_expansion_12h__4h_atr_ratio_le1__3R__480min | 2026-05     |        2 |  0.0221 |               0.011  | Profit    |
| compression_expansion_12h__4h_atr_ratio_le1__3R__480min | 2026-06     |        0 |  0      |               0      | No trades |
| compression_expansion_12h__4h_atr_ratio_le1__3R__480min | 2026-07     |        5 | -1.6176 |              -0.8096 | Loss      |
| compression_expansion_12h__4h_atr_ratio_le1__3R__480min | 2026-08     |        1 | -1.1734 |              -0.5867 | Loss      |
| compression_expansion_12h__4h_atr_ratio_le1__3R__480min | 2026-09     |        3 | -0.8346 |              -0.4187 | Loss      |
| compression_expansion_12h__4h_atr_ratio_le1__3R__480min | 2026-10     |        3 |  0.9596 |               0.4769 | Profit    |
| compression_expansion_12h__4h_atr_ratio_le1__3R__480min | 2026-11     |        0 |  0      |               0      | No trades |
| strong_momentum_6h__4h_adx_le20__2R__480min             | 2025-01     |        0 |  0      |               0      | No trades |
| strong_momentum_6h__4h_adx_le20__2R__480min             | 2025-02     |        8 | -5.9255 |              -2.9282 | Loss      |
| strong_momentum_6h__4h_adx_le20__2R__480min             | 2025-03     |        5 |  1.1625 |               0.5761 | Profit    |
| strong_momentum_6h__4h_adx_le20__2R__480min             | 2025-04     |        3 |  2.2806 |               1.1358 | Profit    |
| strong_momentum_6h__4h_adx_le20__2R__480min             | 2025-05     |        5 |  2.0416 |               1.0205 | Profit    |
| strong_momentum_6h__4h_adx_le20__2R__480min             | 2025-06     |        8 |  0.2479 |               0.1092 | Profit    |
| strong_momentum_6h__4h_adx_le20__2R__480min             | 2025-07     |       15 | -6.5462 |              -3.239  | Loss      |
| strong_momentum_6h__4h_adx_le20__2R__480min             | 2025-08     |        3 |  0.1476 |               0.0674 | Profit    |
| strong_momentum_6h__4h_adx_le20__2R__480min             | 2025-09     |        9 |  1.5854 |               0.7851 | Profit    |
| strong_momentum_6h__4h_adx_le20__2R__480min             | 2025-10     |        3 |  0.7227 |               0.3554 | Profit    |
| strong_momentum_6h__4h_adx_le20__2R__480min             | 2025-11     |        4 | -4.2516 |              -2.109  | Loss      |
| strong_momentum_6h__4h_adx_le20__2R__480min             | 2025-12     |        3 |  0.3321 |               0.1599 | Profit    |
| strong_momentum_6h__4h_adx_le20__2R__480min             | 2026-01     |        2 | -2.3972 |              -1.195  | Loss      |
| strong_momentum_6h__4h_adx_le20__2R__480min             | 2026-02     |        6 | -2.8973 |              -1.4488 | Loss      |
| strong_momentum_6h__4h_adx_le20__2R__480min             | 2026-03     |        3 | -1.8463 |              -0.9219 | Loss      |
| strong_momentum_6h__4h_adx_le20__2R__480min             | 2026-04     |        7 | -1.9544 |              -0.9755 | Loss      |
| strong_momentum_6h__4h_adx_le20__2R__480min             | 2026-05     |        4 | -1.9109 |              -0.9528 | Loss      |
| strong_momentum_6h__4h_adx_le20__2R__480min             | 2026-06     |        3 | -2.2426 |              -1.1175 | Loss      |
| strong_momentum_6h__4h_adx_le20__2R__480min             | 2026-07     |        9 |  5.4746 |               2.7622 | Profit    |
| strong_momentum_6h__4h_adx_le20__2R__480min             | 2026-08     |        4 |  2.1225 |               1.0621 | Profit    |
| strong_momentum_6h__4h_adx_le20__2R__480min             | 2026-09     |       14 | -5.0936 |              -2.5247 | Loss      |
| strong_momentum_6h__4h_adx_le20__2R__480min             | 2026-10     |        1 | -0.0776 |              -0.0388 | Loss      |
| strong_momentum_6h__4h_adx_le20__2R__480min             | 2026-11     |        0 |  0      |               0      | No trades |
| strong_momentum_6h__4h_adx_le20__3R__480min             | 2025-01     |        0 |  0      |               0      | No trades |
| strong_momentum_6h__4h_adx_le20__3R__480min             | 2025-02     |        8 | -5.9255 |              -2.9282 | Loss      |
| strong_momentum_6h__4h_adx_le20__3R__480min             | 2025-03     |        5 |  1.1939 |               0.5917 | Profit    |
| strong_momentum_6h__4h_adx_le20__3R__480min             | 2025-04     |        3 |  4.2806 |               2.1405 | Profit    |
| strong_momentum_6h__4h_adx_le20__3R__480min             | 2025-05     |        5 |  2.6384 |               1.3193 | Profit    |
| strong_momentum_6h__4h_adx_le20__3R__480min             | 2025-06     |        8 | -1.7509 |              -0.8907 | Loss      |
| strong_momentum_6h__4h_adx_le20__3R__480min             | 2025-07     |       15 | -7.2047 |              -3.5551 | Loss      |
| strong_momentum_6h__4h_adx_le20__3R__480min             | 2025-08     |        3 |  0.1981 |               0.0925 | Profit    |
| strong_momentum_6h__4h_adx_le20__3R__480min             | 2025-09     |        9 |  1.0828 |               0.5341 | Profit    |
| strong_momentum_6h__4h_adx_le20__3R__480min             | 2025-10     |        3 |  1.7233 |               0.8528 | Profit    |
| strong_momentum_6h__4h_adx_le20__3R__480min             | 2025-11     |        4 | -4.2516 |              -2.109  | Loss      |
| strong_momentum_6h__4h_adx_le20__3R__480min             | 2025-12     |        3 | -0.1624 |              -0.0855 | Loss      |
| strong_momentum_6h__4h_adx_le20__3R__480min             | 2026-01     |        2 | -2.3972 |              -1.195  | Loss      |
| strong_momentum_6h__4h_adx_le20__3R__480min             | 2026-02     |        6 | -3.8625 |              -1.9199 | Loss      |
| strong_momentum_6h__4h_adx_le20__3R__480min             | 2026-03     |        3 | -1.8463 |              -0.9219 | Loss      |
| strong_momentum_6h__4h_adx_le20__3R__480min             | 2026-04     |        7 | -1.9544 |              -0.9755 | Loss      |
| strong_momentum_6h__4h_adx_le20__3R__480min             | 2026-05     |        4 | -1.9109 |              -0.9528 | Loss      |
| strong_momentum_6h__4h_adx_le20__3R__480min             | 2026-06     |        3 | -2.2426 |              -1.1175 | Loss      |
| strong_momentum_6h__4h_adx_le20__3R__480min             | 2026-07     |        9 |  4.7098 |               2.373  | Profit    |
| strong_momentum_6h__4h_adx_le20__3R__480min             | 2026-08     |        4 |  0.6786 |               0.3389 | Profit    |
| strong_momentum_6h__4h_adx_le20__3R__480min             | 2026-09     |       14 | -5.0936 |              -2.5247 | Loss      |
| strong_momentum_6h__4h_adx_le20__3R__480min             | 2026-10     |        1 | -0.0776 |              -0.0388 | Loss      |
| strong_momentum_6h__4h_adx_le20__3R__480min             | 2026-11     |        0 |  0      |               0      | No trades |
| strong_momentum_6h__4h_efficiency_ge30__2R__480min      | 2025-01     |        2 |  3.7646 |               1.8912 | Profit    |
| strong_momentum_6h__4h_efficiency_ge30__2R__480min      | 2025-02     |        4 | -1.2433 |              -0.6223 | Loss      |
| strong_momentum_6h__4h_efficiency_ge30__2R__480min      | 2025-03     |        9 |  2.9232 |               1.4634 | Profit    |
| strong_momentum_6h__4h_efficiency_ge30__2R__480min      | 2025-04     |        7 |  2.5737 |               1.2829 | Profit    |
| strong_momentum_6h__4h_efficiency_ge30__2R__480min      | 2025-05     |       10 | -5.9641 |              -2.9472 | Loss      |
| strong_momentum_6h__4h_efficiency_ge30__2R__480min      | 2025-06     |       14 | -1.3704 |              -0.6982 | Loss      |
| strong_momentum_6h__4h_efficiency_ge30__2R__480min      | 2025-07     |        8 | -3.259  |              -1.621  | Loss      |
| strong_momentum_6h__4h_efficiency_ge30__2R__480min      | 2025-08     |        9 | -0.8421 |              -0.4258 | Loss      |
| strong_momentum_6h__4h_efficiency_ge30__2R__480min      | 2025-09     |       10 |  0.7844 |               0.3842 | Profit    |
| strong_momentum_6h__4h_efficiency_ge30__2R__480min      | 2025-10     |        5 |  2.8025 |               1.4017 | Profit    |
| strong_momentum_6h__4h_efficiency_ge30__2R__480min      | 2025-11     |        8 | -4.9924 |              -2.4751 | Loss      |
| strong_momentum_6h__4h_efficiency_ge30__2R__480min      | 2025-12     |        3 |  0.3321 |               0.1599 | Profit    |
| strong_momentum_6h__4h_efficiency_ge30__2R__480min      | 2026-01     |        8 | -1.6131 |              -0.8176 | Loss      |
| strong_momentum_6h__4h_efficiency_ge30__2R__480min      | 2026-02     |       12 |  1.6092 |               0.7833 | Profit    |
| strong_momentum_6h__4h_efficiency_ge30__2R__480min      | 2026-03     |       10 | -4.2569 |              -2.119  | Loss      |
| strong_momentum_6h__4h_efficiency_ge30__2R__480min      | 2026-04     |        8 | -1.9023 |              -0.9518 | Loss      |
| strong_momentum_6h__4h_efficiency_ge30__2R__480min      | 2026-05     |       11 | -4.1269 |              -2.0517 | Loss      |
| strong_momentum_6h__4h_efficiency_ge30__2R__480min      | 2026-06     |       10 | -2.0557 |              -1.038  | Loss      |
| strong_momentum_6h__4h_efficiency_ge30__2R__480min      | 2026-07     |       19 |  0.1998 |               0.0918 | Profit    |
| strong_momentum_6h__4h_efficiency_ge30__2R__480min      | 2026-08     |        6 |  1.1206 |               0.5556 | Profit    |
| strong_momentum_6h__4h_efficiency_ge30__2R__480min      | 2026-09     |       13 | -3.6193 |              -1.8063 | Loss      |
| strong_momentum_6h__4h_efficiency_ge30__2R__480min      | 2026-10     |       11 | -7.3592 |              -3.6291 | Loss      |
| strong_momentum_6h__4h_efficiency_ge30__2R__480min      | 2026-11     |        3 |  2.6816 |               1.3392 | Profit    |

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
