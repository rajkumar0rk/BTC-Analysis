# Delta BTCUSD 1H Bollinger (30,2), ATR14 structural stop, 3R

**Method:** the exact indicator parameters of the Daily BB30 backtest, now on fully closed 1-hour candles, same 1m fill/exit engine. No fitting to dates.
**Signal:** close > BB upper LONG or close < BB lower SHORT; ATR(14) Wilder; SL 0.25 ATR outside signal candle wick; TP fixed at 3x entry-to-SL distance; allow every signal.
**Entry:** next genuine 1-minute candle OPEN, adverse $5; **Exit:** minute stop or target, stop-first ambiguity, adverse $5.
**Costs:** Delta futures taker 0.05% each side + 18% GST on fees; historical hourly funding-rate series as approximate settlement proxy; 1% initial stop risk per trade, 2x aggregate notional cap.
**Account:** starts at $10,000, IST monthly marked P&L; no forced month-end liquidation, partial November is not full-month observation.

## Comparison including all trade losses
| scenario   | period           |   trades |   wins |   losses |   win_rate_pct |   net_profit_factor |   net_closed_usd |   avg_net_R |   targets_hit |   median_held_minutes |
|:-----------|:-----------------|---------:|-------:|---------:|---------------:|--------------------:|-----------------:|------------:|--------------:|----------------------:|
| isolated   | 2025             |      183 |     47 |      136 |          25.68 |               0.84  |         -2180.82 |     -0.1276 |            47 |                 671   |
| isolated   | 2026_Jan_Oct     |      173 |     45 |      128 |          26.01 |               0.87  |         -1435.6  |     -0.105  |            45 |                 698   |
| isolated   | 2026_Nov_partial |        9 |      3 |        6 |          33.33 |               1.343 |           145.77 |      0.269  |             3 |                1174   |
| isolated   | through_Oct_2026 |      356 |     92 |      264 |          25.84 |               0.854 |         -3616.42 |     -0.1166 |            92 |                 674.5 |
| isolated   | entire_archive   |      365 |     95 |      270 |          26.03 |               0.862 |         -3470.65 |     -0.1071 |            95 |                 678   |
| concurrent | 2025             |      968 |    232 |      736 |          23.97 |               0.807 |         -5593.93 |     -0.2345 |           232 |                 336.5 |
| concurrent | 2026_Jan_Oct     |      755 |    179 |      576 |          23.71 |               0.881 |         -1735.45 |     -0.2526 |           179 |                 339   |
| concurrent | 2026_Nov_partial |       57 |     18 |       39 |          31.58 |               1.843 |           479.86 |      0.1257 |            18 |                 314   |
| concurrent | through_Oct_2026 |     1723 |    411 |     1312 |          23.85 |               0.832 |         -7329.38 |     -0.2425 |           411 |                 337   |
| concurrent | entire_archive   |     1780 |    429 |     1351 |          24.1  |               0.845 |         -6849.52 |     -0.2307 |           429 |                 337   |

## One position only — IST month-end marked P&L
| month_ist   |   end_equity_usd |   net_return_pct |   trades_closed |   wins |   losses |   net_closed_usd | open_position_at_end   | complete   |
|:------------|-----------------:|-----------------:|----------------:|-------:|---------:|-----------------:|:-----------------------|:-----------|
| 2025-01     |         10261.7  |            2.617 |              15 |      5 |       10 |           286.77 | True                   | True       |
| 2025-02     |          9711.52 |           -5.361 |              23 |      5 |       18 |          -575.26 | False                  | True       |
| 2025-03     |          9338.11 |           -3.845 |               4 |      0 |        4 |          -404.18 | True                   | True       |
| 2025-04     |          9260.23 |           -0.834 |               1 |      0 |        1 |           -92.64 | True                   | True       |
| 2025-05     |          9316.66 |            0.609 |              13 |      4 |        9 |            80.28 | True                   | True       |
| 2025-06     |          8641.96 |           -7.242 |              24 |      5 |       19 |          -653.03 | False                  | True       |
| 2025-07     |          7600.07 |          -12.056 |              30 |      6 |       24 |         -1041.88 | False                  | True       |
| 2025-08     |          7686.63 |            1.139 |              11 |      3 |        8 |           -30.33 | True                   | True       |
| 2025-09     |          7887.28 |            2.61  |               8 |      3 |        5 |           230.83 | True                   | True       |
| 2025-10     |          8657.09 |            9.76  |              19 |      8 |       11 |           856.52 | False                  | True       |
| 2025-11     |          9616.36 |           11.081 |               9 |      5 |        4 |           904.52 | True                   | True       |
| 2025-12     |          7757.33 |          -19.332 |              26 |      3 |       23 |         -1742.44 | True                   | True       |
| 2026-01     |          8834.44 |           13.885 |              20 |      9 |       11 |           998.67 | True                   | True       |
| 2026-02     |          8699.01 |           -1.533 |              19 |      5 |       14 |           -48.44 | True                   | True       |
| 2026-03     |          9177.82 |            5.504 |              18 |      6 |       12 |           408.41 | False                  | True       |
| 2026-04     |          8349.39 |           -9.026 |              12 |      1 |       11 |          -828.43 | False                  | True       |
| 2026-05     |          8008.99 |           -4.077 |              13 |      3 |       10 |          -315.65 | True                   | True       |
| 2026-06     |          8404.16 |            4.934 |              19 |      6 |       13 |           205.25 | True                   | True       |
| 2026-07     |          7080.65 |          -15.748 |              17 |      1 |       16 |         -1174.18 | True                   | True       |
| 2026-08     |          7045.64 |           -0.494 |              14 |      4 |       10 |           -19.16 | False                  | True       |
| 2026-09     |          6802.45 |           -3.452 |              24 |      6 |       18 |          -267.73 | True                   | True       |
| 2026-10     |          6414.15 |           -5.708 |              17 |      4 |       13 |          -394.34 | True                   | True       |
| 2026-11     |          6529.35 |            1.796 |               9 |      3 |        6 |           145.77 | False                  | False      |

## Overlapping entries — IST month-end marked P&L
| month_ist   |   account_return_pct |   end_marked_equity_usd |   trades_closed |   winners |   losers |   closed_net_usd |   open_positions_eom | complete   |
|:------------|---------------------:|------------------------:|----------------:|----------:|---------:|-----------------:|---------------------:|:-----------|
| 2025-01     |               -5.224 |                 9477.6  |              75 |        22 |       53 |          -437.46 |                    3 | True       |
| 2025-02     |                3.622 |                 9820.87 |              85 |        26 |       59 |           258.34 |                    0 | True       |
| 2025-03     |              -20.779 |                 7780.23 |              82 |        17 |       65 |         -2086.23 |                    3 | True       |
| 2025-04     |               -2.961 |                 7549.84 |              71 |        18 |       53 |          -308.73 |                    4 | True       |
| 2025-05     |               -5.109 |                 7164.15 |              82 |        17 |       65 |          -394.15 |                    5 | True       |
| 2025-06     |              -11.65  |                 6329.55 |              78 |        21 |       57 |          -744.66 |                    1 | True       |
| 2025-07     |               -6.778 |                 5900.52 |              74 |        16 |       58 |          -397.33 |                    1 | True       |
| 2025-08     |               -4.628 |                 5627.48 |              81 |        17 |       64 |          -322.24 |                    3 | True       |
| 2025-09     |               -5.24  |                 5332.61 |              68 |        15 |       53 |          -290.12 |                    2 | True       |
| 2025-10     |                3.049 |                 5495.19 |              99 |        30 |       69 |           217.78 |                    0 | True       |
| 2025-11     |                5.754 |                 5811.37 |              91 |        23 |       68 |           274.72 |                    3 | True       |
| 2025-12     |              -24.782 |                 4371.18 |              82 |        10 |       72 |         -1363.84 |                    1 | True       |
| 2026-01     |               21.71  |                 5320.18 |              82 |        27 |       55 |           797.88 |                    3 | True       |
| 2026-02     |                1.242 |                 5386.26 |              83 |        22 |       61 |           226.78 |                    1 | True       |
| 2026-03     |               -1.552 |                 5302.67 |              86 |        23 |       63 |          -128.05 |                    0 | True       |
| 2026-04     |               -9.56  |                 4795.75 |              62 |        11 |       51 |          -574.01 |                    2 | True       |
| 2026-05     |               -7.612 |                 4430.68 |              57 |        15 |       42 |          -280.22 |                    4 | True       |
| 2026-06     |                6.468 |                 4717.26 |              92 |        26 |       66 |           199.7  |                    5 | True       |
| 2026-07     |              -25.906 |                 3495.19 |              78 |         9 |       69 |         -1139.21 |                    2 | True       |
| 2026-08     |               -3.884 |                 3359.45 |              74 |        17 |       57 |          -136.93 |                    1 | True       |
| 2026-09     |               -8.74  |                 3065.85 |              80 |        20 |       60 |          -316.85 |                    2 | True       |
| 2026-10     |              -11.182 |                 2723.04 |              61 |         9 |       52 |          -384.52 |                    3 | True       |
| 2026-11     |               15.697 |                 3150.48 |              57 |        18 |       39 |           479.86 |                    0 | False      |

## Data/validity limitations
- Period exposure previously researched: not pristine out of sample.
- Funding estimates are proxy rates, not settled funding cashflow. Missing rates are unmodeled.
- Fees 0.05% taker per side plus 18% GST, adverse 5 price points each fill.
- No L1 order book, impact, actual liquidation or exact contract lot-size rounding.
- Concurrent overlapping opposite-direction positions may not be operationally possible in one netted trading account.
- Account figures for partial November include open-position mark-to-market; not realized profit.
- 1H interval labels refer to the close boundary; no indicator or ATR lookahead.

Results are historical model outputs, not validated live fill probabilities or independent out-of-sample proof. Refer to trade ledgers for every trade.
