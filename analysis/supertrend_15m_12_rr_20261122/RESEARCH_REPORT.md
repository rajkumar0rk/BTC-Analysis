# BTCUSD 15m Supertrend touch: 12 stop:target point tuples

Interpretation: 1 unit = **100 BTC price points**, e.g. 1:3 is
hard SL 100 pts / TP 300 pts; 3:12 = SL 300 / TP 1200.
15m closing-stop retained as a secondary exit. 1m hard SL including entry
minute adverse move; 1m TP only after entry minute (conservative).
42 causal volume/ATR filter combinations × 12 ratios × 10 profit protection
= **5,040 configurations**; **22 complete IST entry months Jan2025–Oct2026**.
Research only; previously examined history, no untouched OOS.

## Quality/summary
{
  "variants": 5040,
  "net_profitable": 0,
  "ratio_count": 12,
  "filter_combinations": 42,
  "protection_modes": 10,
  "total_trade_ledger_rows": 1299120,
  "data_minutes": 993600,
  "bar15": 66240
}

## No filter — 12 RRs, fixed TP and point stop, no profit protection
| vol_filter   | atr_filter   | rr   | protection   |   trades |   wins |   win_rate_pct |   tp_exits |   sl_exits |   protection_exits |   supertrend_close_exits |   ambiguous_exits |   net_pts |   net_per_trade_pts |    pf |   max_dd_pts |   profitable_months |   flat_months |
|:-------------|:-------------|:-----|:-------------|---------:|-------:|---------------:|-----------:|-----------:|-------------------:|-------------------------:|------------------:|----------:|--------------------:|------:|-------------:|--------------------:|--------------:|
| vol_off      | atr_off      | 1:1  | off          |      782 |     82 |          10.49 |        325 |        321 |                  0 |                      136 |                 6 |  -94369.9 |             -120.68 | 0.009 |      94369.9 |                   0 |             0 |
| vol_off      | atr_off      | 1:2  | off          |      782 |    207 |          26.47 |        207 |        396 |                  0 |                      179 |                 1 |  -94125.7 |             -120.37 | 0.157 |      94224.3 |                   0 |             0 |
| vol_off      | atr_off      | 1:3  | off          |      782 |    155 |          19.82 |        155 |        435 |                  0 |                      192 |                 0 |  -93523.5 |             -119.6  | 0.234 |      93722.1 |                   0 |             0 |
| vol_off      | atr_off      | 1:4  | off          |      782 |    133 |          17.01 |        132 |        454 |                  0 |                      196 |                 0 |  -89113.3 |             -113.96 | 0.295 |      89467.2 |                   1 |             0 |
| vol_off      | atr_off      | 2:2  | off          |      782 |    256 |          32.74 |        256 |        209 |                  0 |                      317 |                 1 |  -97232.1 |             -124.34 | 0.181 |      97330.7 |                   0 |             0 |
| vol_off      | atr_off      | 2:4  | off          |      782 |    166 |          21.23 |        165 |        250 |                  0 |                      367 |                 0 |  -93595.5 |             -119.69 | 0.333 |      93949.5 |                   1 |             0 |
| vol_off      | atr_off      | 2:6  | off          |      782 |    122 |          15.6  |        120 |        266 |                  0 |                      396 |                 0 |  -92027.2 |             -117.68 | 0.387 |      92269.5 |                   1 |             0 |
| vol_off      | atr_off      | 2:8  | off          |      782 |    108 |          13.81 |        100 |        270 |                  0 |                      412 |                 0 |  -83959.7 |             -107.37 | 0.451 |      84401.9 |                   0 |             0 |
| vol_off      | atr_off      | 3:3  | off          |      782 |    217 |          27.75 |        217 |        140 |                  0 |                      425 |                 0 |  -95742.3 |             -122.43 | 0.293 |      96125.9 |                   0 |             0 |
| vol_off      | atr_off      | 3:6  | off          |      782 |    135 |          17.26 |        133 |        162 |                  0 |                      487 |                 0 |  -91407.1 |             -116.89 | 0.413 |      92125.6 |                   1 |             0 |
| vol_off      | atr_off      | 3:9  | off          |      782 |    111 |          14.19 |         99 |        170 |                  0 |                      513 |                 0 |  -83132.6 |             -106.31 | 0.486 |      84450.7 |                   2 |             0 |
| vol_off      | atr_off      | 3:12 | off          |      782 |     97 |          12.4  |         75 |        175 |                  0 |                      532 |                 0 |  -80186.8 |             -102.54 | 0.514 |      82350.1 |                   1 |             0 |

## No filter — best ex-post protection per RR
| rr   |   sl_pts |   tp_pts |   trades |   off_net | best_protection   |   best_net |   improvement_pts |   best_profitable_months |   best_ambiguous_events |
|:-----|---------:|---------:|---------:|----------:|:------------------|-----------:|------------------:|-------------------------:|------------------------:|
| 1:1  |      100 |      100 |      782 |  -94369.9 | off               |   -94369.9 |                 0 |                        0 |                       6 |
| 1:2  |      100 |      200 |      782 |  -94125.7 | off               |   -94125.7 |                 0 |                        0 |                       1 |
| 1:3  |      100 |      300 |      782 |  -93523.5 | off               |   -93523.5 |                 0 |                        0 |                       0 |
| 1:4  |      100 |      400 |      782 |  -89113.3 | off               |   -89113.3 |                 0 |                        1 |                       0 |
| 2:2  |      200 |      200 |      782 |  -97232.1 | off               |   -97232.1 |                 0 |                        0 |                       1 |
| 2:4  |      200 |      400 |      782 |  -93595.5 | off               |   -93595.5 |                 0 |                        1 |                       0 |
| 2:6  |      200 |      600 |      782 |  -92027.2 | off               |   -92027.2 |                 0 |                        1 |                       0 |
| 2:8  |      200 |      800 |      782 |  -83959.7 | off               |   -83959.7 |                 0 |                        0 |                       0 |
| 3:3  |      300 |      300 |      782 |  -95742.3 | off               |   -95742.3 |                 0 |                        0 |                       0 |
| 3:6  |      300 |      600 |      782 |  -91407.1 | off               |   -91407.1 |                 0 |                        1 |                       0 |
| 3:9  |      300 |      900 |      782 |  -83132.6 | off               |   -83132.6 |                 0 |                        2 |                       0 |
| 3:12 |      300 |     1200 |      782 |  -80186.8 | off               |   -80186.8 |                 0 |                        1 |                       0 |

## Volume >=2x and ATR >=0.30% — best ex-post protection per RR
| rr   |   trades |   off_net | best_protection   |   best_net |   improvement_pts |   best_profitable_months |
|:-----|---------:|----------:|:------------------|-----------:|------------------:|-------------------------:|
| 1:1  |      100 | -13195.2  | off               |  -13195.2  |              0    |                        0 |
| 1:2  |      100 | -12481.6  | off               |  -12481.6  |              0    |                        1 |
| 1:3  |      100 | -13614    | be_200            |  -13281.2  |            332.87 |                        0 |
| 1:4  |      100 | -12814.5  | off               |  -12814.5  |              0    |                        2 |
| 2:2  |      100 | -11502.9  | off               |  -11502.9  |              0    |                        1 |
| 2:4  |      100 | -13285.4  | off               |  -13285.4  |              0    |                        0 |
| 2:6  |      100 | -13298.8  | off               |  -13298.8  |              0    |                        2 |
| 2:8  |      100 | -11157.1  | off               |  -11157.1  |              0    |                        4 |
| 3:3  |      100 | -12011    | off               |  -12011    |              0    |                        2 |
| 3:6  |      100 | -10354.9  | off               |  -10354.9  |              0    |                        7 |
| 3:9  |      100 |  -7113.78 | off               |   -7113.78 |              0    |                        7 |
| 3:12 |      100 |  -4261.82 | off               |   -4261.82 |              0    |                        7 |

## Volume >=2x and ATR >=0.40% — best ex-post protection per RR
| rr   |   trades |   off_net | best_protection   |   best_net |   improvement_pts |   best_profitable_months |
|:-----|---------:|----------:|:------------------|-----------:|------------------:|-------------------------:|
| 1:1  |       44 |  -5781.62 | off               |   -5781.62 |              0    |                        0 |
| 1:2  |       44 |  -5581.74 | off               |   -5581.74 |              0    |                        0 |
| 1:3  |       44 |  -6381.27 | be_200            |   -5881.56 |            499.71 |                        1 |
| 1:4  |       44 |  -5681.68 | be_200            |   -5181.98 |            499.7  |                        2 |
| 2:2  |       44 |  -3752.33 | off               |   -3752.33 |              0    |                        2 |
| 2:4  |       44 |  -5382.75 | be_200            |   -4551.86 |            830.89 |                        3 |
| 2:6  |       44 |  -4249.39 | off               |   -4249.39 |              0    |                        3 |
| 2:8  |       44 |  -3890.91 | lock_500_200      |   -3583.81 |            307.1  |                        4 |
| 3:3  |       44 |  -6033.16 | be_200            |   -5461.28 |            571.88 |                        3 |
| 3:6  |       44 |  -4484.61 | off               |   -4484.61 |              0    |                        4 |
| 3:9  |       44 |  -3992.8  | lock_500_200      |   -3419.27 |            573.53 |                        5 |
| 3:12 |       44 |  -1294.39 | off               |   -1294.39 |              0    |                        6 |

## Full-history positive-net combinations: 0/5040

## Top 25 by full-history net (hindsight-ranked; NOT validation)
| vol_filter   | atr_filter     | rr   | protection           |   trades |   wins |   win_rate_pct |   tp_exits |   sl_exits |   protection_exits |   supertrend_close_exits |   ambiguous_exits |   net_pts |   net_per_trade_pts |    pf |   max_dd_pts |   profitable_months |   flat_months |
|:-------------|:---------------|:-----|:---------------------|---------:|-------:|---------------:|-----------:|-----------:|-------------------:|-------------------------:|------------------:|----------:|--------------------:|------:|-------------:|--------------------:|--------------:|
| vol_ge_2p0   | atrpct_ge_0p40 | 3:12 | off                  |       44 |      9 |          20.45 |          9 |         20 |                  0 |                       15 |                 0 |  -1294.39 |              -29.42 | 0.883 |      4623.17 |                   6 |             9 |
| vol_ge_2p0   | atrpct_ge_0p40 | 3:12 | lock_500_200         |       44 |     13 |          29.55 |          7 |         19 |                  6 |                       12 |                 1 |  -2020.09 |              -45.91 | 0.801 |      5204.29 |                   5 |             9 |
| vol_ge_2p0   | atrpct_ge_0p40 | 3:12 | be_200               |       44 |      6 |          13.64 |          6 |         13 |                 19 |                        6 |                 6 |  -2163.23 |              -49.16 | 0.752 |      4249.59 |                   4 |             9 |
| vol_le_0p8   | atrpct_ge_0p40 | 1:4  | trail_300_100        |       43 |     11 |          25.58 |          3 |         29 |                  8 |                        3 |                 6 |  -2349.41 |              -54.64 | 0.63  |      4276.67 |                   3 |             7 |
| vol_le_0p8   | atrpct_ge_0p40 | 3:6  | trail_500_300        |       43 |     13 |          30.23 |          7 |         13 |                  6 |                       17 |                 2 |  -2504.82 |              -58.25 | 0.707 |      4558.25 |                   5 |             7 |
| vol_le_0p8   | atrpct_ge_0p40 | 2:8  | trail_500_300        |       43 |     11 |          25.58 |          4 |         22 |                  7 |                       10 |                 1 |  -2520.63 |              -58.62 | 0.694 |      4574.06 |                   5 |             7 |
| vol_le_0p8   | atrpct_ge_0p40 | 3:6  | trail_500_200        |       43 |     13 |          30.23 |          4 |         13 |                  9 |                       17 |                 4 |  -2638    |              -61.35 | 0.691 |      4891.31 |                   4 |             7 |
| vol_le_0p8   | atrpct_ge_0p40 | 3:9  | trail_500_300        |       43 |     13 |          30.23 |          2 |         13 |                 11 |                       17 |                 2 |  -2685.25 |              -62.45 | 0.685 |      4738.69 |                   5 |             7 |
| vol_le_0p8   | atrpct_ge_0p40 | 2:6  | trail_500_200        |       43 |     11 |          25.58 |          4 |         22 |                  7 |                       10 |                 3 |  -2776.25 |              -64.56 | 0.663 |      5029.57 |                   4 |             7 |
| vol_le_0p8   | atrpct_ge_0p40 | 2:6  | trail_500_300        |       43 |     11 |          25.58 |          6 |         22 |                  5 |                       10 |                 1 |  -2835.42 |              -65.94 | 0.656 |      4888.85 |                   5 |             7 |
| vol_le_0p8   | atrpct_ge_0p40 | 2:8  | trail_500_200        |       43 |     11 |          25.58 |          1 |         22 |                 10 |                       10 |                 3 |  -2963.05 |              -68.91 | 0.641 |      5216.36 |                   4 |             7 |
| vol_le_0p8   | atrpct_ge_0p40 | 3:9  | trail_500_200        |       43 |     13 |          30.23 |          0 |         13 |                 13 |                       17 |                 4 |  -2977.03 |              -69.23 | 0.651 |      5230.34 |                   4 |             7 |
| vol_le_0p8   | atrpct_ge_0p40 | 3:12 | trail_500_200        |       43 |     13 |          30.23 |          0 |         13 |                 13 |                       17 |                 4 |  -2977.03 |              -69.23 | 0.651 |      5230.34 |                   4 |             7 |
| vol_le_0p8   | atrpct_ge_0p40 | 3:12 | trail_500_300        |       43 |     13 |          30.23 |          0 |         13 |                 13 |                       17 |                 2 |  -3097.46 |              -72.03 | 0.637 |      5150.89 |                   5 |             7 |
| vol_le_0p8   | atrpct_ge_0p40 | 1:3  | step_200_100_plus200 |       43 |      9 |          20.93 |          6 |         29 |                  5 |                        3 |                 5 |  -3100.87 |              -72.11 | 0.515 |      4844.91 |                   3 |             7 |
| vol_ge_2p0   | atrpct_ge_0p40 | 3:12 | trail_1000_200       |       44 |      9 |          20.45 |          1 |         20 |                  8 |                       15 |                 7 |  -3126.44 |              -71.06 | 0.718 |      5775.04 |                   5 |             9 |
| vol_le_0p8   | atrpct_ge_0p40 | 1:4  | step_200_100_plus200 |       43 |      8 |          18.6  |          2 |         29 |                  9 |                        3 |                 7 |  -3300.75 |              -76.76 | 0.485 |      5044.79 |                   3 |             7 |
| vol_ge_2p0   | atrpct_ge_0p40 | 3:9  | lock_500_200         |       44 |     13 |          29.55 |          8 |         19 |                  5 |                       12 |                 1 |  -3419.27 |              -77.71 | 0.663 |      5703.99 |                   5 |             9 |
| vol_le_0p8   | atrpct_ge_0p40 | 2:4  | trail_300_100        |       43 |     13 |          30.23 |          3 |         21 |                 10 |                        9 |                 8 |  -3445.25 |              -80.12 | 0.556 |      5733.04 |                   4 |             7 |
| vol_ge_2p0   | atrpct_ge_0p40 | 2:8  | lock_500_200         |       44 |     12 |          27.27 |          8 |         29 |                  4 |                        3 |                 1 |  -3583.81 |              -81.45 | 0.621 |      5335.03 |                   4 |             9 |
| vol_le_0p8   | atrpct_ge_0p40 | 2:6  | trail_300_100        |       43 |     13 |          30.23 |          0 |         21 |                 13 |                        9 |                 9 |  -3627    |              -84.35 | 0.532 |      5914.79 |                   4 |             7 |
| vol_le_0p8   | atrpct_ge_0p40 | 2:8  | trail_300_100        |       43 |     13 |          30.23 |          0 |         21 |                 13 |                        9 |                 9 |  -3627    |              -84.35 | 0.532 |      5914.79 |                   4 |             7 |
| vol_le_0p8   | atrpct_ge_0p40 | 1:4  | off                  |       43 |     10 |          23.26 |         10 |         30 |                  0 |                        3 |                 0 |  -3700.52 |              -86.06 | 0.435 |      3745.56 |                   3 |             7 |
| vol_le_0p8   | atrpct_ge_0p40 | 1:4  | lock_500_200         |       43 |     10 |          23.26 |         10 |         30 |                  0 |                        3 |                 0 |  -3700.52 |              -86.06 | 0.435 |      3745.56 |                   3 |             7 |
| vol_le_0p8   | atrpct_ge_0p40 | 1:4  | trail_500_200        |       43 |     10 |          23.26 |         10 |         30 |                  0 |                        3 |                 0 |  -3700.52 |              -86.06 | 0.435 |      3745.56 |                   3 |             7 |

## Top 15 by positive months (note flat/no-trade months)
| vol_filter   | atr_filter     | rr   | protection     |   trades |   wins |   win_rate_pct |   tp_exits |   sl_exits |   protection_exits |   supertrend_close_exits |   ambiguous_exits |   net_pts |   net_per_trade_pts |    pf |   max_dd_pts |   profitable_months |   flat_months |
|:-------------|:---------------|:-----|:---------------|---------:|-------:|---------------:|-----------:|-----------:|-------------------:|-------------------------:|------------------:|----------:|--------------------:|------:|-------------:|--------------------:|--------------:|
| vol_ge_1p0   | atrrel_le_0p8  | 3:12 | off            |      174 |     22 |          12.64 |         17 |         17 |                  0 |                      140 |                 0 | -12303.4  |              -70.71 | 0.611 |     15624.1  |                   8 |             0 |
| vol_off      | atrrel_le_0p8  | 3:12 | trail_1000_200 |      239 |     34 |          14.23 |          3 |         26 |                 24 |                      186 |                18 | -19495    |              -81.57 | 0.553 |     22703    |                   8 |             0 |
| vol_off      | atrrel_le_0p8  | 3:6  | off            |      239 |     45 |          18.83 |         44 |         23 |                  0 |                      172 |                 0 | -19637    |              -82.16 | 0.521 |     21597.5  |                   8 |             0 |
| vol_off      | atrrel_le_0p8  | 3:6  | trail_1000_200 |      239 |     45 |          18.83 |         44 |         23 |                  0 |                      172 |                 0 | -19637    |              -82.16 | 0.521 |     21597.5  |                   8 |             0 |
| vol_off      | atrrel_le_0p8  | 3:9  | off            |      239 |     34 |          14.23 |         27 |         26 |                  0 |                      186 |                 0 | -21288.7  |              -89.07 | 0.512 |     23618.7  |                   8 |             0 |
| vol_off      | atrrel_le_0p8  | 3:9  | trail_1000_200 |      239 |     34 |          14.23 |         27 |         26 |                  0 |                      186 |                 0 | -21288.7  |              -89.07 | 0.512 |     23618.7  |                   8 |             0 |
| vol_ge_2p0   | atrpct_ge_0p30 | 3:12 | off            |      100 |     19 |          19    |         18 |         39 |                  0 |                       43 |                 0 |  -4261.82 |              -42.62 | 0.822 |      9621.04 |                   7 |             0 |
| vol_ge_2p0   | atrpct_ge_0p30 | 3:12 | trail_1000_200 |      100 |     19 |          19    |          4 |         39 |                 15 |                       42 |                13 |  -6720.23 |              -67.2  | 0.719 |     10659    |                   7 |             0 |
| vol_ge_2p0   | atrpct_ge_0p30 | 3:9  | off            |      100 |     21 |          21    |         21 |         39 |                  0 |                       40 |                 0 |  -7113.78 |              -71.14 | 0.699 |     10293.5  |                   7 |             0 |
| vol_ge_2p0   | atrpct_ge_0p30 | 3:9  | trail_1000_200 |      100 |     21 |          21    |         21 |         39 |                  0 |                       40 |                 0 |  -7113.78 |              -71.14 | 0.699 |     10293.5  |                   7 |             0 |
| vol_ge_1p25  | atrrel_le_0p8  | 3:12 | off            |      146 |     19 |          13.01 |         14 |         14 |                  0 |                      118 |                 0 | -10029.2  |              -68.69 | 0.616 |     13658.8  |                   7 |             1 |
| vol_ge_2p0   | atrpct_ge_0p30 | 3:6  | off            |      100 |     25 |          25    |         25 |         37 |                  0 |                       38 |                 0 | -10354.9  |             -103.55 | 0.54  |     11665    |                   7 |             0 |
| vol_ge_2p0   | atrpct_ge_0p30 | 3:6  | trail_1000_200 |      100 |     25 |          25    |         25 |         37 |                  0 |                       38 |                 0 | -10354.9  |             -103.55 | 0.54  |     11665    |                   7 |             0 |
| vol_ge_1p25  | atrrel_le_0p8  | 3:6  | trail_500_300  |      146 |     28 |          19.18 |         17 |         12 |                 11 |                      106 |                 5 | -13291.4  |              -91.04 | 0.45  |     14393.5  |                   7 |             1 |
| vol_ge_1p25  | atrrel_le_0p8  | 3:6  | lock_500_200   |      146 |     28 |          19.18 |         21 |         12 |                  7 |                      106 |                 1 | -13370.2  |              -91.58 | 0.447 |     14808.7  |                   7 |             1 |

## Ranked by 2025 average P&L per trade only (>=30 2025 trades; >=60 total)
| vol_filter   | atr_filter     | rr   | protection           |   trades |   wins |   win_rate_pct |   tp_exits |   sl_exits |   protection_exits |   supertrend_close_exits |   ambiguous_exits |   net_pts |   net_per_trade_pts |    pf |   max_dd_pts |   profitable_months |   flat_months |   n_2025 |   net_2025 |   avgnet_2025 |
|:-------------|:---------------|:-----|:---------------------|---------:|-------:|---------------:|-----------:|-----------:|-------------------:|-------------------------:|------------------:|----------:|--------------------:|------:|-------------:|--------------------:|--------------:|---------:|-----------:|--------------:|
| vol_ge_2p0   | atrpct_ge_0p30 | 3:12 | off                  |      100 |     19 |          19    |         18 |         39 |                  0 |                       43 |                 0 |  -4261.82 |              -42.62 | 0.822 |      9621.04 |                   7 |             0 |       60 |   -2681.62 |        -44.69 |
| vol_ge_2p0   | atrpct_ge_0p30 | 3:9  | off                  |      100 |     21 |          21    |         21 |         39 |                  0 |                       40 |                 0 |  -7113.78 |              -71.14 | 0.699 |     10293.5  |                   7 |             0 |       60 |   -3734.64 |        -62.24 |
| vol_ge_2p0   | atrpct_ge_0p30 | 3:9  | trail_1000_200       |      100 |     21 |          21    |         21 |         39 |                  0 |                       40 |                 0 |  -7113.78 |              -71.14 | 0.699 |     10293.5  |                   7 |             0 |       60 |   -3734.64 |        -62.24 |
| vol_ge_2p0   | atrpct_ge_0p30 | 3:12 | trail_1000_200       |      100 |     19 |          19    |          4 |         39 |                 15 |                       42 |                13 |  -6720.23 |              -67.2  | 0.719 |     10659    |                   7 |             0 |       60 |   -3940.2  |        -65.67 |
| vol_ge_2p0   | atrpct_ge_0p30 | 3:12 | lock_500_200         |      100 |     27 |          27    |         13 |         37 |                 13 |                       37 |                 3 |  -6872.68 |              -68.73 | 0.692 |      9852.47 |                   6 |             0 |       60 |   -4719.32 |        -78.66 |
| vol_le_0p8   | atrpct_ge_0p30 | 1:3  | step_200_100_plus200 |      101 |     19 |          18.81 |         13 |         61 |                 13 |                       14 |                 8 | -10210.6  |             -101.09 | 0.31  |     11900.3  |                   1 |             0 |       49 |   -4609.43 |        -94.07 |
| vol_ge_1p25  | atrrel_le_0p8  | 3:12 | off                  |      146 |     19 |          13.01 |         14 |         14 |                  0 |                      118 |                 0 | -10029.2  |              -68.69 | 0.616 |     13658.8  |                   7 |             1 |       89 |   -8404.38 |        -94.43 |
| vol_le_0p8   | atrpct_ge_0p30 | 1:4  | trail_300_100        |      101 |     21 |          20.79 |          2 |         65 |                 19 |                       15 |                12 | -10589.5  |             -104.85 | 0.322 |     12364    |                   2 |             0 |       49 |   -4640.32 |        -94.7  |
| vol_ge_1p5   | atrrel_le_0p8  | 3:12 | off                  |      109 |     13 |          11.93 |          9 |         12 |                  0 |                       88 |                 0 |  -9804.36 |              -89.95 | 0.516 |     12712.4  |                   3 |             1 |       65 |   -6200.17 |        -95.39 |
| vol_ge_1p5   | atrpct_ge_0p30 | 3:12 | off                  |      146 |     23 |          15.75 |         22 |         64 |                  0 |                       60 |                 0 | -13398.2  |              -91.77 | 0.642 |     16135    |                   5 |             0 |       84 |   -8195.84 |        -97.57 |
| vol_ge_1p0   | atrrel_le_0p8  | 3:12 | off                  |      174 |     22 |          12.64 |         17 |         17 |                  0 |                      140 |                 0 | -12303.4  |              -70.71 | 0.611 |     15624.1  |                   8 |             0 |      103 |  -10162.3  |        -98.66 |
| vol_ge_1p5   | atrpct_ge_0p30 | 3:12 | trail_1000_200       |      146 |     24 |          16.44 |          6 |         63 |                 18 |                       59 |                15 | -15316.1  |             -104.91 | 0.586 |     17780.2  |                   5 |             0 |       84 |   -8565.86 |       -101.97 |
| vol_ge_1p5   | atrpct_ge_0p30 | 3:9  | off                  |      146 |     26 |          17.81 |         26 |         63 |                  0 |                       57 |                 0 | -16250.1  |             -111.3  | 0.557 |     17487.8  |                   5 |             0 |       84 |   -8649.21 |       -102.97 |
| vol_ge_1p5   | atrpct_ge_0p30 | 3:9  | trail_1000_200       |      146 |     26 |          17.81 |         26 |         63 |                  0 |                       57 |                 0 | -16250.1  |             -111.3  | 0.557 |     17487.8  |                   5 |             0 |       84 |   -8649.21 |       -102.97 |
| vol_ge_1p5   | atrpct_ge_0p30 | 3:12 | lock_500_200         |      146 |     34 |          23.29 |         17 |         59 |                 16 |                       54 |                 3 | -14509.9  |              -99.38 | 0.58  |     16247.3  |                   6 |             0 |       84 |   -8734.42 |       -103.98 |
| vol_le_0p8   | atrpct_ge_0p30 | 2:4  | trail_300_100        |      101 |     25 |          24.75 |          2 |         37 |                 23 |                       39 |                15 | -11715.9  |             -116    | 0.325 |     13751    |                   2 |             0 |       49 |   -5124.99 |       -104.59 |
| vol_le_0p8   | atrpct_ge_0p30 | 2:6  | trail_300_100        |      101 |     25 |          24.75 |          0 |         37 |                 25 |                       39 |                15 | -11870.1  |             -117.53 | 0.316 |     13905.1  |                   2 |             0 |       49 |   -5124.99 |       -104.59 |
| vol_le_0p8   | atrpct_ge_0p30 | 2:8  | trail_300_100        |      101 |     25 |          24.75 |          0 |         37 |                 25 |                       39 |                15 | -11870.1  |             -117.53 | 0.316 |     13905.1  |                   2 |             0 |       49 |   -5124.99 |       -104.59 |
| vol_ge_2p0   | atrpct_ge_0p20 | 3:12 | off                  |      193 |     29 |          15.03 |         26 |         70 |                  0 |                       97 |                 0 | -18095.2  |              -93.76 | 0.614 |     21925    |                   5 |             0 |      112 |  -11805.4  |       -105.41 |
| vol_ge_1p25  | atrrel_le_0p8  | 3:12 | trail_1000_200       |      146 |     20 |          13.7  |          2 |         14 |                 14 |                      116 |                12 | -12151.9  |              -83.23 | 0.534 |     15224.4  |                   5 |             1 |       89 |   -9391.59 |       -105.52 |

## Execution / limitations
- Entries are identical across all 12 RR configurations for a given filter;
  there is no second entry within the same bullish Supertrend cycle.
- OHLC cannot establish same-minute high-low sequence. Existing hard and
  protective stops win over targets when both touched in a single 1m.
- A newly armed protective stop and its touch within a 1m is assumed
  high-then-low and filled at stop, marked *ambiguous*.
- A take-profit at or below a protection activation is executed before
  a protection stop activated that minute; the latter cannot preempt TP.
- Entry minute low below the hard point SL is **counted as a stop**.
- Entry minute favorable high is ignored because it might predate fill.
- No bid/ask queue, spread, funding, margin or liquidation modeling;
  0.05% taker per side, GST 18% on fees, 5 BTC points/slippage per side.
- P&L is 1BTC-equivalent BTC **price points**, not leveraged account profit.
- Monthly attribution is IST **entry month** so total and monthly sum
  agree; previous reports used exit months. Don't compare month counts
  without this adjustment.
- All date partitions have previously been used for strategy research.
- Filtered configurations heavily overlap; never sum their trade counts.
