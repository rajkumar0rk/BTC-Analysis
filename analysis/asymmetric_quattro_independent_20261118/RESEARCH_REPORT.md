# Independent Quattro-style breakout: BTCUSD + ETHUSD, Delta India

## Result summary
|   unit_risk |   starting_equity |   final_equity |   net_return_pct |   trades |   win_rate_pct |   profit_factor |   average_win_usd |   average_loss_usd |   biggest_winner_R |   max_mark_to_market_drawdown_pct |   entry_fees_plus_exit_fees_usd |   funding_proxy_usd |   missing_funding_settlement_count |   data_gap_exits |   pessimistic_same_minute_exits | pyramid_units_distribution   |   positive_months |   negative_months |   flat_months | symbol   |
|------------:|------------------:|---------------:|-----------------:|---------:|---------------:|----------------:|------------------:|-------------------:|-------------------:|----------------------------------:|--------------------------------:|--------------------:|-----------------------------------:|-----------------:|--------------------------------:|:-----------------------------|------------------:|------------------:|--------------:|:---------|
|       0.005 |              1000 |       1012.91  |           1.2909 |       21 |          23.81 |          1.085  |           32.9601 |            -9.4933 |             21.433 |                           -10.157 |                          16.176 |              12.077 |                                  0 |                0 |                               0 | {4: 8, 2: 5, 1: 6, 3: 2}     |                 3 |                 5 |            15 | BTCUSD   |
|       0.02  |              1000 |        983.183 |          -1.6817 |       21 |          23.81 |          0.9742 |          126.941  |           -40.72   |             21.433 |                           -32.577 |                          66.958 |              47.009 |                                  0 |                0 |                               0 | {4: 8, 2: 5, 1: 6, 3: 2}     |                 3 |                 5 |            15 | BTCUSD   |
|       0.005 |              1000 |        934.71  |          -6.529  |       20 |          20    |          0.5764 |           22.2139 |            -9.6341 |             11.234 |                           -13.979 |                          10.31  |               6.753 |                                  0 |                0 |                               0 | {3: 2, 4: 11, 1: 5, 2: 2}    |                 2 |                 7 |            14 | ETHUSD   |
|       0.02  |              1000 |        739.211 |         -26.0789 |       20 |          20    |          0.5533 |           80.756  |           -36.4883 |             11.234 |                           -43.491 |                          38.913 |              25.227 |                                  0 |                0 |                               0 | {3: 2, 4: 11, 1: 5, 2: 2}    |                 2 |                 7 |            14 | ETHUSD   |

## Monthly IST mark-to-market
| symbol   |   risk_per_unit | month_ist   |   net_return_pct |   start_equity |   end_equity |   entries | exposure   | month_status   |
|:---------|----------------:|:------------|-----------------:|---------------:|-------------:|----------:|:-----------|:---------------|
| BTCUSD   |           0.005 | 2025-01     |           0      |       1000     |     1000     |         0 | False      | flat           |
| BTCUSD   |           0.005 | 2025-02     |           0      |       1000     |     1000     |         0 | False      | flat           |
| BTCUSD   |           0.005 | 2025-03     |           0      |       1000     |     1000     |         0 | False      | flat           |
| BTCUSD   |           0.005 | 2025-04     |           0      |       1000     |     1000     |         0 | False      | flat           |
| BTCUSD   |           0.005 | 2025-05     |           0      |       1000     |     1000     |         0 | False      | flat           |
| BTCUSD   |           0.005 | 2025-06     |           0      |       1000     |     1000     |         0 | False      | flat           |
| BTCUSD   |           0.005 | 2025-07     |           0      |       1000     |     1000     |         0 | False      | flat           |
| BTCUSD   |           0.005 | 2025-08     |          -0.4552 |       1000     |      995.448 |         2 | True       | loss           |
| BTCUSD   |           0.005 | 2025-09     |          -1.9187 |        995.448 |      976.348 |         5 | True       | loss           |
| BTCUSD   |           0.005 | 2025-10     |           6.6234 |        976.348 |     1041.02  |         3 | True       | profit         |
| BTCUSD   |           0.005 | 2025-11     |           0      |       1041.02  |     1041.02  |         0 | False      | flat           |
| BTCUSD   |           0.005 | 2025-12     |           0      |       1041.02  |     1041.02  |         0 | False      | flat           |
| BTCUSD   |           0.005 | 2026-01     |           0      |       1041.02  |     1041.02  |         0 | False      | flat           |
| BTCUSD   |           0.005 | 2026-02     |           0      |       1041.02  |     1041.02  |         0 | False      | flat           |
| BTCUSD   |           0.005 | 2026-03     |           0      |       1041.02  |     1041.02  |         0 | False      | flat           |
| BTCUSD   |           0.005 | 2026-04     |           0      |       1041.02  |     1041.02  |         0 | False      | flat           |
| BTCUSD   |           0.005 | 2026-05     |          -1.0651 |       1041.02  |     1029.93  |         2 | True       | loss           |
| BTCUSD   |           0.005 | 2026-06     |           0      |       1029.93  |     1029.93  |         0 | False      | flat           |
| BTCUSD   |           0.005 | 2026-07     |           0      |       1029.93  |     1029.93  |         0 | False      | flat           |
| BTCUSD   |           0.005 | 2026-08     |           2.613  |       1029.93  |     1056.84  |         2 | True       | profit         |
| BTCUSD   |           0.005 | 2026-09     |           1.2715 |       1056.84  |     1070.28  |         2 | True       | profit         |
| BTCUSD   |           0.005 | 2026-10     |          -4.4713 |       1070.28  |     1022.42  |         4 | True       | loss           |
| BTCUSD   |           0.005 | 2026-11     |          -0.9304 |       1022.42  |     1012.91  |         1 | True       | loss           |
| BTCUSD   |           0.02  | 2025-01     |           0      |       1000     |     1000     |         0 | False      | flat           |
| BTCUSD   |           0.02  | 2025-02     |           0      |       1000     |     1000     |         0 | False      | flat           |
| BTCUSD   |           0.02  | 2025-03     |           0      |       1000     |     1000     |         0 | False      | flat           |
| BTCUSD   |           0.02  | 2025-04     |           0      |       1000     |     1000     |         0 | False      | flat           |
| BTCUSD   |           0.02  | 2025-05     |           0      |       1000     |     1000     |         0 | False      | flat           |
| BTCUSD   |           0.02  | 2025-06     |           0      |       1000     |     1000     |         0 | False      | flat           |
| BTCUSD   |           0.02  | 2025-07     |           0      |       1000     |     1000     |         0 | False      | flat           |
| BTCUSD   |           0.02  | 2025-08     |          -1.874  |       1000     |      981.26  |         2 | True       | loss           |
| BTCUSD   |           0.02  | 2025-09     |          -7.6246 |        981.26  |      906.442 |         5 | True       | loss           |
| BTCUSD   |           0.02  | 2025-10     |          22.6085 |        906.442 |     1111.38  |         3 | True       | profit         |
| BTCUSD   |           0.02  | 2025-11     |           0      |       1111.38  |     1111.38  |         0 | False      | flat           |
| BTCUSD   |           0.02  | 2025-12     |           0      |       1111.38  |     1111.38  |         0 | False      | flat           |
| BTCUSD   |           0.02  | 2026-01     |           0      |       1111.38  |     1111.38  |         0 | False      | flat           |
| BTCUSD   |           0.02  | 2026-02     |           0      |       1111.38  |     1111.38  |         0 | False      | flat           |
| BTCUSD   |           0.02  | 2026-03     |           0      |       1111.38  |     1111.38  |         0 | False      | flat           |
| BTCUSD   |           0.02  | 2026-04     |           0      |       1111.38  |     1111.38  |         0 | False      | flat           |
| BTCUSD   |           0.02  | 2026-05     |          -4.2264 |       1111.38  |     1064.4   |         2 | True       | loss           |
| BTCUSD   |           0.02  | 2026-06     |           0      |       1064.4   |     1064.4   |         0 | False      | flat           |
| BTCUSD   |           0.02  | 2026-07     |           0      |       1064.4   |     1064.4   |         0 | False      | flat           |
| BTCUSD   |           0.02  | 2026-08     |          10.2536 |       1064.4   |     1173.54  |         2 | True       | profit         |
| BTCUSD   |           0.02  | 2026-09     |           4.8366 |       1173.54  |     1230.3   |         2 | True       | profit         |
| BTCUSD   |           0.02  | 2026-10     |         -16.997  |       1230.3   |     1021.19  |         4 | True       | loss           |
| BTCUSD   |           0.02  | 2026-11     |          -3.7217 |       1021.19  |      983.183 |         1 | True       | loss           |
| ETHUSD   |           0.005 | 2025-01     |           0      |       1000     |     1000     |         0 | False      | flat           |
| ETHUSD   |           0.005 | 2025-02     |           0      |       1000     |     1000     |         0 | False      | flat           |
| ETHUSD   |           0.005 | 2025-03     |           0      |       1000     |     1000     |         0 | False      | flat           |
| ETHUSD   |           0.005 | 2025-04     |           0      |       1000     |     1000     |         0 | False      | flat           |
| ETHUSD   |           0.005 | 2025-05     |           0      |       1000     |     1000     |         0 | False      | flat           |
| ETHUSD   |           0.005 | 2025-06     |           0      |       1000     |     1000     |         0 | False      | flat           |
| ETHUSD   |           0.005 | 2025-07     |          -2.4954 |       1000     |      975.046 |         2 | True       | loss           |
| ETHUSD   |           0.005 | 2025-08     |           3.9595 |        975.046 |     1013.65  |         3 | True       | profit         |
| ETHUSD   |           0.005 | 2025-09     |          -2.2673 |       1013.65  |      990.671 |         3 | True       | loss           |
| ETHUSD   |           0.005 | 2025-10     |          -1.4583 |        990.671 |      976.224 |         3 | True       | loss           |
| ETHUSD   |           0.005 | 2025-11     |          -0.472  |        976.224 |      971.617 |         1 | True       | loss           |
| ETHUSD   |           0.005 | 2025-12     |           0      |        971.617 |      971.617 |         0 | False      | flat           |
| ETHUSD   |           0.005 | 2026-01     |           0      |        971.617 |      971.617 |         0 | False      | flat           |
| ETHUSD   |           0.005 | 2026-02     |           0      |        971.617 |      971.617 |         0 | False      | flat           |
| ETHUSD   |           0.005 | 2026-03     |           0      |        971.617 |      971.617 |         0 | False      | flat           |
| ETHUSD   |           0.005 | 2026-04     |           0      |        971.617 |      971.617 |         0 | False      | flat           |
| ETHUSD   |           0.005 | 2026-05     |           0      |        971.617 |      971.617 |         0 | False      | flat           |
| ETHUSD   |           0.005 | 2026-06     |           0      |        971.617 |      971.617 |         0 | False      | flat           |
| ETHUSD   |           0.005 | 2026-07     |           0      |        971.617 |      971.617 |         0 | False      | flat           |
| ETHUSD   |           0.005 | 2026-08     |           3.1651 |        971.617 |     1002.37  |         1 | True       | profit         |
| ETHUSD   |           0.005 | 2026-09     |          -4.9662 |       1002.37  |      952.59  |         5 | True       | loss           |
| ETHUSD   |           0.005 | 2026-10     |          -0.5249 |        952.59  |      947.589 |         1 | True       | loss           |
| ETHUSD   |           0.005 | 2026-11     |          -1.3592 |        947.589 |      934.71  |         1 | True       | loss           |
| ETHUSD   |           0.02  | 2025-01     |           0      |       1000     |     1000     |         0 | False      | flat           |
| ETHUSD   |           0.02  | 2025-02     |           0      |       1000     |     1000     |         0 | False      | flat           |
| ETHUSD   |           0.02  | 2025-03     |           0      |       1000     |     1000     |         0 | False      | flat           |
| ETHUSD   |           0.02  | 2025-04     |           0      |       1000     |     1000     |         0 | False      | flat           |
| ETHUSD   |           0.02  | 2025-05     |           0      |       1000     |     1000     |         0 | False      | flat           |
| ETHUSD   |           0.02  | 2025-06     |           0      |       1000     |     1000     |         0 | False      | flat           |
| ETHUSD   |           0.02  | 2025-07     |          -9.793  |       1000     |      902.07  |         2 | True       | loss           |
| ETHUSD   |           0.02  | 2025-08     |          14.861  |        902.07  |     1036.13  |         3 | True       | profit         |
| ETHUSD   |           0.02  | 2025-09     |          -8.9598 |       1036.13  |      943.292 |         3 | True       | loss           |
| ETHUSD   |           0.02  | 2025-10     |          -5.7822 |        943.292 |      888.749 |         3 | True       | loss           |
| ETHUSD   |           0.02  | 2025-11     |          -1.8879 |        888.749 |      871.971 |         1 | True       | loss           |
| ETHUSD   |           0.02  | 2025-12     |           0      |        871.971 |      871.971 |         0 | False      | flat           |
| ETHUSD   |           0.02  | 2026-01     |           0      |        871.971 |      871.971 |         0 | False      | flat           |
| ETHUSD   |           0.02  | 2026-02     |           0      |        871.971 |      871.971 |         0 | False      | flat           |
| ETHUSD   |           0.02  | 2026-03     |           0      |        871.971 |      871.971 |         0 | False      | flat           |
| ETHUSD   |           0.02  | 2026-04     |           0      |        871.971 |      871.971 |         0 | False      | flat           |
| ETHUSD   |           0.02  | 2026-05     |           0      |        871.971 |      871.971 |         0 | False      | flat           |
| ETHUSD   |           0.02  | 2026-06     |           0      |        871.971 |      871.971 |         0 | False      | flat           |
| ETHUSD   |           0.02  | 2026-07     |           0      |        871.971 |      871.971 |         0 | False      | flat           |
| ETHUSD   |           0.02  | 2026-08     |          12.6605 |        871.971 |      982.366 |         1 | True       | profit         |
| ETHUSD   |           0.02  | 2026-09     |         -18.7191 |        982.366 |      798.476 |         5 | True       | loss           |
| ETHUSD   |           0.02  | 2026-10     |          -2.0997 |        798.476 |      781.71  |         1 | True       | loss           |
| ETHUSD   |           0.02  | 2026-11     |          -5.4366 |        781.71  |      739.211 |         1 | True       | loss           |

## Caveats
- Daily EMA200 needs 200 complete days, so first 200 days are warmup
- No genuine untouched holdout (all historical periods previously research exposed)
- Long-only source code condition is close above daily EMA200; README mentions rising EMA and is inconsistent
- Fees, GST, hypothetical slippage, and funding proxy included; not actual order book
- For contradictory 1m stop/add OHLC ordering, pessimistic fill assumption used
- At 1m data gap, unknown gap exposure exits at next observed open
- Monthly net equity is IST mark-to-market including estimated close-out fee
- Partial November 2026, no 2022-2024 archived Delta data
- Pyramiding 4 x 2% initial nominal risk can produce large account drawdowns
- Not automatically a tradable or safe strategy

Source: scripts/research_asymmetric_quattro_independent.py
