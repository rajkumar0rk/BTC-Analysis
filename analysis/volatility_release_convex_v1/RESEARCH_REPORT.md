# BTC-first volatility compression and exceptional range release

Predeclared 1h range >=2x preceding 168h median, with preceding 6h median <=75% of same baseline. Enter next 1m open in release direction or inverted placebo. Stop 1x completed ATR, fixed 10R target, max 12h hold; stop-first intrabar ordering.
Same rule on both native instruments. No month-end liquidation. BTC-only 2025 parameter selection; identical frozen rules evaluated on ETH; 2026 historical validation.

## Complete summary

| market   | model                                     |   dislocation_threshold |   mode |   stopmult |   rr |   profit_factor |   net_return_22m_pct |   net_return_2025_pct |   net_return_2026_jan_oct_pct | year2025_above_500pct   | year2026_ytd_above_500pct   |   strong_pf1p5_return5_months |   strong_pf1p5_return10_months |   positive_months |   trades |   wins |   losses |   max_month_end_nav_drawdown_pct |   worst_month_pct |
|:---------|:------------------------------------------|------------------------:|-------:|-----------:|-----:|----------------:|---------------------:|----------------------:|------------------------------:|:------------------------|:----------------------------|------------------------------:|-------------------------------:|------------------:|---------:|-------:|---------:|---------------------------------:|------------------:|
| BTCUSD   | volatility_release_ratio2_mode+1_SL1_RR10 |                       2 |      1 |          1 |   10 |        0.786213 |             -13.8507 |              -5.10388 |                      -9.21728 | False                   | False                       |                             0 |                              0 |                 8 |      137 |     35 |      102 |                         -15.628  |          -4.87871 |
| BTCUSD   | volatility_release_ratio2_mode-1_SL1_RR10 |                       2 |     -1 |          1 |   10 |        0.772715 |             -13.9158 |             -12.9134  |                      -1.15102 | False                   | False                       |                             0 |                              0 |                 9 |      140 |     35 |      105 |                         -16.2313 |          -6.20278 |
| ETHUSD   | volatility_release_ratio2_mode+1_SL1_RR10 |                       2 |      1 |          1 |   10 |        0.721889 |             -15.0892 |             -13.1774  |                      -2.20201 | False                   | False                       |                             0 |                              0 |                 8 |      135 |     35 |      100 |                         -15.0892 |          -4.38243 |
| ETHUSD   | volatility_release_ratio2_mode-1_SL1_RR10 |                       2 |     -1 |          1 |   10 |        0.774112 |             -12.8319 |              -8.31146 |                      -4.93019 | False                   | False                       |                             1 |                              0 |                 9 |      143 |     37 |      106 |                         -19.0935 |          -5.7016  |

## Monthly results

| market   | model                                     | month   |   profit_factor |   net_return_pct |   net_exit_pnl_usd |   month_nav_change_usd |   trades |   wins |   losses |   nav_start_usd |   nav_end_usd |   open_positions_at_month_end |
|:---------|:------------------------------------------|:--------|----------------:|-----------------:|-------------------:|-----------------------:|---------:|-------:|---------:|----------------:|--------------:|------------------------------:|
| BTCUSD   | volatility_release_ratio2_mode+1_SL1_RR10 | 2025-01 |      0.422422   |       -1.40645   |         -14.0645   |             -14.0645   |        5 |      1 |        4 |        1000     |       985.935 |                             0 |
| BTCUSD   | volatility_release_ratio2_mode+1_SL1_RR10 | 2025-02 |      0.299728   |       -2.19091   |         -21.6009   |             -21.6009   |        6 |      1 |        5 |         985.935 |       964.335 |                             0 |
| BTCUSD   | volatility_release_ratio2_mode+1_SL1_RR10 | 2025-03 |      4.45295    |        4.36784   |          42.1206   |              42.1206   |        4 |      2 |        2 |         964.335 |      1006.46  |                             0 |
| BTCUSD   | volatility_release_ratio2_mode+1_SL1_RR10 | 2025-04 |     12.3009     |        1.4516    |          11.2974   |              14.6097   |        2 |      1 |        1 |        1006.46  |      1021.06  |                             1 |
| BTCUSD   | volatility_release_ratio2_mode+1_SL1_RR10 | 2025-05 |      0.572718   |       -2.4503    |         -21.7069   |             -25.0191   |       11 |      3 |        8 |        1021.06  |       996.046 |                             0 |
| BTCUSD   | volatility_release_ratio2_mode+1_SL1_RR10 | 2025-06 |      0.984455   |       -0.041386  |          -0.412223 |              -0.412223 |        5 |      1 |        4 |         996.046 |       995.634 |                             0 |
| BTCUSD   | volatility_release_ratio2_mode+1_SL1_RR10 | 2025-07 |      0          |       -2.17144   |         -27.8893   |             -21.6196   |        4 |      0 |        4 |         995.634 |       974.014 |                             1 |
| BTCUSD   | volatility_release_ratio2_mode+1_SL1_RR10 | 2025-08 |      2.91568    |        4.57689   |          50.8493   |              44.5796   |        7 |      3 |        4 |         974.014 |      1018.59  |                             0 |
| BTCUSD   | volatility_release_ratio2_mode+1_SL1_RR10 | 2025-09 |      0.0991049  |       -3.0382    |         -30.9469   |             -30.9469   |        6 |      1 |        5 |        1018.59  |       987.647 |                             0 |
| BTCUSD   | volatility_release_ratio2_mode+1_SL1_RR10 | 2025-10 |      1.40224    |        1.01112   |           9.98627  |               9.98627  |        7 |      3 |        4 |         987.647 |       997.633 |                             0 |
| BTCUSD   | volatility_release_ratio2_mode+1_SL1_RR10 | 2025-11 |    nan          |        0         |           0        |               0        |        0 |      0 |        0 |         997.633 |       997.633 |                             0 |
| BTCUSD   | volatility_release_ratio2_mode+1_SL1_RR10 | 2025-12 |      0.42249    |       -4.87871   |         -48.6716   |             -48.6716   |       13 |      2 |       11 |         997.633 |       948.961 |                             0 |
| BTCUSD   | volatility_release_ratio2_mode+1_SL1_RR10 | 2026-01 |      1.97699    |        2.62991   |          24.9568   |              24.9568   |        6 |      2 |        4 |         948.961 |       973.918 |                             0 |
| BTCUSD   | volatility_release_ratio2_mode+1_SL1_RR10 | 2026-02 |      0.211803   |       -1.61566   |         -26.0046   |             -15.7352   |        8 |      2 |        6 |         973.918 |       958.183 |                             1 |
| BTCUSD   | volatility_release_ratio2_mode+1_SL1_RR10 | 2026-03 |      1.98983    |        0.776662  |          17.7113   |               7.44185  |        5 |      2 |        3 |         958.183 |       965.625 |                             0 |
| BTCUSD   | volatility_release_ratio2_mode+1_SL1_RR10 | 2026-04 |      1.31977    |        1.0425    |          10.0666   |              10.0666   |        7 |      2 |        5 |         965.625 |       975.691 |                             0 |
| BTCUSD   | volatility_release_ratio2_mode+1_SL1_RR10 | 2026-05 |      1.02172    |        0.0728498 |           0.710789 |               0.710789 |        8 |      3 |        5 |         975.691 |       976.402 |                             0 |
| BTCUSD   | volatility_release_ratio2_mode+1_SL1_RR10 | 2026-06 |      0.0575483  |       -2.68958   |         -26.2611   |             -26.2611   |        6 |      1 |        5 |         976.402 |       950.141 |                             0 |
| BTCUSD   | volatility_release_ratio2_mode+1_SL1_RR10 | 2026-07 |      0.61235    |       -2.0325    |         -19.3116   |             -19.3116   |       11 |      3 |        8 |         950.141 |       930.829 |                             0 |
| BTCUSD   | volatility_release_ratio2_mode+1_SL1_RR10 | 2026-08 |      0          |       -3.32742   |         -30.9726   |             -30.9726   |        5 |      0 |        5 |         930.829 |       899.857 |                             0 |
| BTCUSD   | volatility_release_ratio2_mode+1_SL1_RR10 | 2026-09 |      0.276084   |       -1.4493    |         -13.0416   |             -13.0416   |        4 |      1 |        3 |         899.857 |       886.815 |                             0 |
| BTCUSD   | volatility_release_ratio2_mode+1_SL1_RR10 | 2026-10 |      0.3149     |       -2.85541   |         -25.3222   |             -25.3222   |        7 |      1 |        6 |         886.815 |       861.493 |                             0 |
| BTCUSD   | volatility_release_ratio2_mode-1_SL1_RR10 | 2025-01 |      0.812126   |       -0.3551    |          -3.551    |              -3.551    |        5 |      2 |        3 |        1000     |       996.449 |                             0 |
| BTCUSD   | volatility_release_ratio2_mode-1_SL1_RR10 | 2025-02 |      0.707329   |       -0.912194  |          -9.08954  |              -9.08954  |        6 |      1 |        5 |         996.449 |       987.359 |                             0 |
| BTCUSD   | volatility_release_ratio2_mode-1_SL1_RR10 | 2025-03 |      0          |       -2.88288   |         -28.4644   |             -28.4644   |        5 |      0 |        5 |         987.359 |       958.895 |                             0 |
| BTCUSD   | volatility_release_ratio2_mode-1_SL1_RR10 | 2025-04 |      0          |       -1.83972   |         -17.641    |             -17.641    |        3 |      0 |        3 |         958.895 |       941.254 |                             0 |
| BTCUSD   | volatility_release_ratio2_mode-1_SL1_RR10 | 2025-05 |      0.00662433 |       -6.20278   |         -58.3839   |             -58.3839   |       11 |      1 |       10 |         941.254 |       882.87  |                             0 |
| BTCUSD   | volatility_release_ratio2_mode-1_SL1_RR10 | 2025-06 |      4.15879    |        4.47402   |          39.4998   |              39.4998   |        4 |      2 |        2 |         882.87  |       922.37  |                             0 |
| BTCUSD   | volatility_release_ratio2_mode-1_SL1_RR10 | 2025-07 |      0.825771   |       -0.610551  |          -5.63154  |              -5.63154  |        6 |      1 |        5 |         922.37  |       916.738 |                             0 |
| BTCUSD   | volatility_release_ratio2_mode-1_SL1_RR10 | 2025-08 |      0          |       -4.41797   |         -40.5013   |             -40.5013   |        7 |      0 |        7 |         916.738 |       876.237 |                             0 |
| BTCUSD   | volatility_release_ratio2_mode-1_SL1_RR10 | 2025-09 |      1.35087    |        0.743083  |           6.51117  |               6.51117  |        5 |      2 |        3 |         876.237 |       882.748 |                             0 |
| BTCUSD   | volatility_release_ratio2_mode-1_SL1_RR10 | 2025-10 |      0.389367   |       -2.2843    |         -20.1646   |             -20.1646   |        7 |      1 |        6 |         882.748 |       862.584 |                             0 |
| BTCUSD   | volatility_release_ratio2_mode-1_SL1_RR10 | 2025-11 |    nan          |        0         |           0        |               0        |        0 |      0 |        0 |         862.584 |       862.584 |                             0 |
| BTCUSD   | volatility_release_ratio2_mode-1_SL1_RR10 | 2025-12 |      1.15804    |        0.960155  |           8.28214  |               8.28214  |       13 |      5 |        8 |         862.584 |       870.866 |                             0 |
| BTCUSD   | volatility_release_ratio2_mode-1_SL1_RR10 | 2026-01 |      0.175217   |       -3.80983   |         -33.1785   |             -33.1785   |        8 |      1 |        7 |         870.866 |       837.687 |                             0 |
| BTCUSD   | volatility_release_ratio2_mode-1_SL1_RR10 | 2026-02 |      0.845941   |        1.30359   |          -3.69268  |              10.92     |        7 |      2 |        5 |         837.687 |       848.607 |                             1 |
| BTCUSD   | volatility_release_ratio2_mode-1_SL1_RR10 | 2026-03 |      3.43484    |        2.74795   |          37.932    |              23.3193   |        6 |      3 |        3 |         848.607 |       871.927 |                             0 |
| BTCUSD   | volatility_release_ratio2_mode-1_SL1_RR10 | 2026-04 |      0.19422    |       -3.48673   |         -30.4017   |             -30.4017   |        8 |      1 |        7 |         871.927 |       841.525 |                             0 |
| BTCUSD   | volatility_release_ratio2_mode-1_SL1_RR10 | 2026-05 |      1.09304    |        0.189298  |           1.59299  |               1.59299  |        6 |      3 |        3 |         841.525 |       843.118 |                             0 |
| BTCUSD   | volatility_release_ratio2_mode-1_SL1_RR10 | 2026-06 |      2.87971    |        3.39134   |          27.8142   |              28.593    |        5 |      2 |        3 |         843.118 |       871.711 |                             1 |
| BTCUSD   | volatility_release_ratio2_mode-1_SL1_RR10 | 2026-07 |      1.49099    |        1.88386   |          17.2006   |              16.4219   |       11 |      5 |        6 |         871.711 |       888.133 |                             0 |
| BTCUSD   | volatility_release_ratio2_mode-1_SL1_RR10 | 2026-08 |      1.04378    |        0.123023  |           1.09261  |               1.09261  |        5 |      1 |        4 |         888.133 |       889.225 |                             0 |
| BTCUSD   | volatility_release_ratio2_mode-1_SL1_RR10 | 2026-09 |      0.683963   |       -0.628705  |          -5.5906   |              -5.5906   |        4 |      1 |        3 |         889.225 |       883.635 |                             0 |
| BTCUSD   | volatility_release_ratio2_mode-1_SL1_RR10 | 2026-10 |      0.444162   |       -2.57944   |         -22.7928   |             -22.7928   |        8 |      1 |        7 |         883.635 |       860.842 |                             0 |
| ETHUSD   | volatility_release_ratio2_mode+1_SL1_RR10 | 2025-01 |      0          |       -1.14118   |         -11.4118   |             -11.4118   |        2 |      0 |        2 |        1000     |       988.588 |                             0 |
| ETHUSD   | volatility_release_ratio2_mode+1_SL1_RR10 | 2025-02 |      0.144105   |       -3.8505    |         -38.0656   |             -38.0656   |        9 |      1 |        8 |         988.588 |       950.523 |                             0 |
| ETHUSD   | volatility_release_ratio2_mode+1_SL1_RR10 | 2025-03 |      1.19091    |        0.425884  |           4.04813  |               4.04813  |        6 |      2 |        4 |         950.523 |       954.571 |                             0 |
| ETHUSD   | volatility_release_ratio2_mode+1_SL1_RR10 | 2025-04 |      0.158505   |       -2.90213   |         -27.7029   |             -27.7029   |        8 |      2 |        6 |         954.571 |       926.868 |                             0 |
| ETHUSD   | volatility_release_ratio2_mode+1_SL1_RR10 | 2025-05 |      0          |       -0.585635  |          -5.42806  |              -5.42806  |        1 |      0 |        1 |         926.868 |       921.44  |                             0 |
| ETHUSD   | volatility_release_ratio2_mode+1_SL1_RR10 | 2025-06 |      0.258642   |       -1.30852   |         -12.0572   |             -12.0572   |        4 |      1 |        3 |         921.44  |       909.383 |                             0 |
| ETHUSD   | volatility_release_ratio2_mode+1_SL1_RR10 | 2025-07 |      0.602062   |       -0.484147  |          -4.40275  |              -4.40275  |        3 |      1 |        2 |         909.383 |       904.98  |                             0 |
| ETHUSD   | volatility_release_ratio2_mode+1_SL1_RR10 | 2025-08 |      0.220971   |       -1.80412   |         -16.3269   |             -16.3269   |        5 |      1 |        4 |         904.98  |       888.653 |                             0 |
| ETHUSD   | volatility_release_ratio2_mode+1_SL1_RR10 | 2025-09 |      0.257605   |       -1.34728   |         -11.9726   |             -11.9726   |        5 |      2 |        3 |         888.653 |       876.68  |                             0 |
| ETHUSD   | volatility_release_ratio2_mode+1_SL1_RR10 | 2025-10 |      1.11828    |        0.238015  |           2.08663  |               2.08663  |        5 |      1 |        4 |         876.68  |       878.767 |                             0 |
| ETHUSD   | volatility_release_ratio2_mode+1_SL1_RR10 | 2025-11 |      1.0221     |        0.0646009 |           0.567691 |               0.567691 |        7 |      2 |        5 |         878.767 |       879.335 |                             0 |
| ETHUSD   | volatility_release_ratio2_mode+1_SL1_RR10 | 2025-12 |      0.802823   |       -1.26328   |         -11.1084   |             -11.1084   |       12 |      3 |        9 |         879.335 |       868.226 |                             0 |
| ETHUSD   | volatility_release_ratio2_mode+1_SL1_RR10 | 2026-01 |      2.461      |        1.75134   |          15.2056   |              15.2056   |        3 |      1 |        2 |         868.226 |       883.432 |                             0 |
| ETHUSD   | volatility_release_ratio2_mode+1_SL1_RR10 | 2026-02 |      1.34772    |        0.600729  |           5.30704  |               5.30704  |        7 |      4 |        3 |         883.432 |       888.739 |                             0 |
| ETHUSD   | volatility_release_ratio2_mode+1_SL1_RR10 | 2026-03 |      2.14294    |        2.8627    |          25.442    |              25.442    |        8 |      3 |        5 |         888.739 |       914.181 |                             0 |
| ETHUSD   | volatility_release_ratio2_mode+1_SL1_RR10 | 2026-04 |      3.41527    |        3.65413   |          33.4054   |              33.4054   |        6 |      3 |        3 |         914.181 |       947.586 |                             0 |
| ETHUSD   | volatility_release_ratio2_mode+1_SL1_RR10 | 2026-05 |      1.17663    |        0.454186  |           4.30381  |               4.30381  |        6 |      2 |        4 |         947.586 |       951.89  |                             0 |
| ETHUSD   | volatility_release_ratio2_mode+1_SL1_RR10 | 2026-06 |      0.775047   |       -0.698594  |          -6.64984  |              -6.64984  |        8 |      2 |        6 |         951.89  |       945.24  |                             0 |
| ETHUSD   | volatility_release_ratio2_mode+1_SL1_RR10 | 2026-07 |      0.66426    |       -1.22954   |         -11.6221   |             -11.6221   |        9 |      3 |        6 |         945.24  |       933.618 |                             0 |
| ETHUSD   | volatility_release_ratio2_mode+1_SL1_RR10 | 2026-08 |      0          |       -4.38243   |         -40.9151   |             -40.9151   |        7 |      0 |        7 |         933.618 |       892.703 |                             0 |
| ETHUSD   | volatility_release_ratio2_mode+1_SL1_RR10 | 2026-09 |      0          |       -2.52813   |         -22.5687   |             -22.5687   |        4 |      0 |        4 |         892.703 |       870.134 |                             0 |
| ETHUSD   | volatility_release_ratio2_mode+1_SL1_RR10 | 2026-10 |      0.573131   |       -2.41645   |         -21.0264   |             -21.0264   |       10 |      1 |        9 |         870.134 |       849.108 |                             0 |
| ETHUSD   | volatility_release_ratio2_mode-1_SL1_RR10 | 2025-01 |      0          |       -0.791913  |          -7.91913  |              -7.91913  |        2 |      0 |        2 |        1000     |       992.081 |                             0 |
| ETHUSD   | volatility_release_ratio2_mode-1_SL1_RR10 | 2025-02 |      1.44308    |        1.30539   |          12.9505   |              12.9505   |        8 |      3 |        5 |         992.081 |      1005.03  |                             0 |
| ETHUSD   | volatility_release_ratio2_mode-1_SL1_RR10 | 2025-03 |      0.208272   |       -2.73681   |         -27.5058   |             -27.5058   |        7 |      1 |        6 |        1005.03  |       977.526 |                             0 |
| ETHUSD   | volatility_release_ratio2_mode-1_SL1_RR10 | 2025-04 |      1.07299    |        0.173914  |           1.70005  |               1.70005  |        8 |      4 |        4 |         977.526 |       979.226 |                             0 |
| ETHUSD   | volatility_release_ratio2_mode-1_SL1_RR10 | 2025-05 |      0          |       -0.584864  |          -5.72714  |              -5.72714  |        1 |      0 |        1 |         979.226 |       973.499 |                             0 |
| ETHUSD   | volatility_release_ratio2_mode-1_SL1_RR10 | 2025-06 |      0          |       -2.32065   |         -22.5915   |             -22.5915   |        4 |      0 |        4 |         973.499 |       950.907 |                             0 |
| ETHUSD   | volatility_release_ratio2_mode-1_SL1_RR10 | 2025-07 |      0          |       -1.8       |         -17.1164   |             -17.1164   |        3 |      0 |        3 |         950.907 |       933.791 |                             0 |
| ETHUSD   | volatility_release_ratio2_mode-1_SL1_RR10 | 2025-08 |      0          |       -2.86652   |         -26.7673   |             -26.7673   |        5 |      0 |        5 |         933.791 |       907.023 |                             0 |
| ETHUSD   | volatility_release_ratio2_mode-1_SL1_RR10 | 2025-09 |      0          |       -2.82363   |         -25.611    |             -25.611    |        5 |      0 |        5 |         907.023 |       881.412 |                             0 |
| ETHUSD   | volatility_release_ratio2_mode-1_SL1_RR10 | 2025-10 |      1.89204    |        2.15008   |          18.9511   |              18.9511   |        6 |      2 |        4 |         881.412 |       900.363 |                             0 |
| ETHUSD   | volatility_release_ratio2_mode-1_SL1_RR10 | 2025-11 |      1.26868    |        0.794293  |           7.15153  |               7.15153  |        6 |      1 |        5 |         900.363 |       907.515 |                             0 |
| ETHUSD   | volatility_release_ratio2_mode-1_SL1_RR10 | 2025-12 |      1.26243    |        1.03254   |           9.37046  |               9.37046  |       11 |      5 |        6 |         907.515 |       916.885 |                             0 |
| ETHUSD   | volatility_release_ratio2_mode-1_SL1_RR10 | 2026-01 |      0.27587    |       -1.26644   |         -11.6118   |             -11.6118   |        4 |      1 |        3 |         916.885 |       905.274 |                             0 |
| ETHUSD   | volatility_release_ratio2_mode-1_SL1_RR10 | 2026-02 |      0.0379171  |       -3.22787   |         -29.221    |             -29.221    |        7 |      1 |        6 |         905.274 |       876.053 |                             0 |
| ETHUSD   | volatility_release_ratio2_mode-1_SL1_RR10 | 2026-03 |      0          |       -5.7016    |         -49.949    |             -49.949    |       10 |      0 |       10 |         876.053 |       826.104 |                             0 |
| ETHUSD   | volatility_release_ratio2_mode-1_SL1_RR10 | 2026-04 |      0.492785   |       -1.56977   |         -12.9679   |             -12.9679   |        7 |      1 |        6 |         826.104 |       813.136 |                             0 |
| ETHUSD   | volatility_release_ratio2_mode-1_SL1_RR10 | 2026-05 |      2.65873    |        2.1502    |          17.4841   |              17.4841   |        5 |      3 |        2 |         813.136 |       830.62  |                             0 |
| ETHUSD   | volatility_release_ratio2_mode-1_SL1_RR10 | 2026-06 |      1.74454    |        3.62896   |          21.4135   |              30.1429   |        8 |      2 |        6 |         830.62  |       860.763 |                             1 |
| ETHUSD   | volatility_release_ratio2_mode-1_SL1_RR10 | 2026-07 |      1.01157    |       -0.96545   |           0.419158 |              -8.31024  |       12 |      5 |        7 |         860.763 |       852.452 |                             0 |
| ETHUSD   | volatility_release_ratio2_mode-1_SL1_RR10 | 2026-08 |      3.71878    |        5.47272   |          46.6524   |              46.6524   |        6 |      3 |        3 |         852.452 |       899.105 |                             0 |
| ETHUSD   | volatility_release_ratio2_mode-1_SL1_RR10 | 2026-09 |      1.69628    |        0.975489  |           8.77067  |               8.77067  |        5 |      3 |        2 |         899.105 |       907.875 |                             0 |
| ETHUSD   | volatility_release_ratio2_mode-1_SL1_RR10 | 2026-10 |      0.437117   |       -3.98669   |         -36.1942   |             -36.1942   |       13 |      2 |       11 |         907.875 |       871.681 |                             0 |

## Execution limitations

{
  "source": "original Delta India native trade 1m SHA256 checked by load()",
  "months": 22,
  "initial_equity_usd": 1000,
  "risk_per_trade_pct": 0.5,
  "max_notional_leverage": 3,
  "taker_fee_each_side": 0.0005,
  "GST": 0.18,
  "BTC_slippage_points_per_side": 5,
  "ETH_slippage_fraction_each_side": 0.0002,
  "months_nav": "Mark-to-market at IST calendar month boundary, open trades retained; monthly PF based on exits",
  "missing_first_ist_2025_hours": 5.5,
  "excluded_november_2026": true,
  "unmodeled": [
    "funding",
    "real order-book spread",
    "market impact",
    "margin/liquidation",
    "lot constraints",
    "live fills"
  ],
  "caveat": "Range-release signal is not evidence of forced institutional execution; 2026 historical data are research-exposed"
}
