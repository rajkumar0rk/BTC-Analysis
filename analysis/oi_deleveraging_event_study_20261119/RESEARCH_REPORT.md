# Institutional falsification: OI deleveraging and momentum

## Pre-registered mechanism
When open-interest collapses in an exceptional directional price impulse,
forced position closure may either accelerate price discovery (follow-through)
or exhaust the move (opposite-direction control). Test BOTH at exactly
the same event timestamps with identical costs and risk.

## Exact independent backtest results
| symbol   | scenario         |   slip_bps |   closed_trades |   wins |   losses |   win_rate_pct |   avg_win_over_avg_loss |   profit_factor |   biggest_winner_R |   winners_ge_10R |   max_consecutive_losses |   top_winner_pct_of_gross_wins |   net_return_total_pct |   return_2025_pct |   return_2026_through_nov17_pct |   max_MTM_drawdown_pct |   fees_GST_usd |   funding_proxy_usd |   blocked_leverage |   profitable_months |   losing_months |
|:---------|:-----------------|-----------:|----------------:|-------:|---------:|---------------:|------------------------:|----------------:|-------------------:|-----------------:|-------------------------:|-------------------------------:|-----------------------:|------------------:|--------------------------------:|-----------------------:|---------------:|--------------------:|-------------------:|--------------------:|----------------:|
| BTCUSD   | follow           |          2 |             682 |    134 |      548 |        19.6481 |                 3.06403 |        0.749233 |            25.3299 |                9 |                       23 |                          3.696 |                -53.78  |           -41.379 |                         -21.155 |                -58.207 |        456.042 |               1.931 |                  0 |                   4 |              19 |
| BTCUSD   | opposite_control |          2 |             568 |    112 |      456 |        19.7183 |                 3.84249 |        0.94377  |            19.7205 |               11 |                       16 |                          4.066 |                -16.441 |             7.555 |                         -22.31  |                -35.079 |        630.764 |               2.458 |                  0 |                  11 |              12 |
| BTCUSD   | follow_stressed  |          6 |             705 |    129 |      576 |        18.2979 |                 2.79233 |        0.625365 |            17.4926 |                8 |                       24 |                          3.905 |                -72.716 |           -53.378 |                         -41.478 |                -75.015 |        380.979 |               1.543 |                  0 |                   3 |              20 |
| ETHUSD   | follow           |          2 |             696 |    126 |      570 |        18.1034 |                 4.07498 |        0.900785 |            22.1457 |               13 |                       21 |                          4.034 |                -28.533 |           -11.359 |                         -19.375 |                -45.438 |        435.788 |              -3.457 |                  0 |                   9 |              14 |
| ETHUSD   | opposite_control |          2 |             673 |    128 |      545 |        19.0193 |                 3.58043 |        0.840908 |            16.9736 |               15 |                       24 |                          3.018 |                -37.144 |           -23.064 |                         -18.301 |                -39.109 |        341.518 |               5.19  |                  0 |                   8 |              15 |
| ETHUSD   | follow_stressed  |          6 |             710 |    122 |      588 |        17.1831 |                 3.98451 |        0.826718 |            22.0474 |               13 |                       23 |                          4.52  |                -47.565 |           -21.35  |                         -33.33  |                -58.897 |        393.816 |              -2.866 |                  0 |                   8 |              15 |

## Monthly net NAV including mark-to-market liquidation costs
| symbol   | scenario         |   slip_bps | month_ist   |   net_return_pct |   end_equity |   entries | position_exposure   |
|:---------|:-----------------|-----------:|:------------|-----------------:|-------------:|----------:|:--------------------|
| BTCUSD   | follow           |          2 | 2025-01     |          -2.81   |      971.9   |        15 | True                |
| BTCUSD   | follow           |          2 | 2025-02     |          -0.6088 |      965.983 |        22 | True                |
| BTCUSD   | follow           |          2 | 2025-03     |          -6.684  |      901.416 |        34 | True                |
| BTCUSD   | follow           |          2 | 2025-04     |          -8.7168 |      822.842 |        34 | True                |
| BTCUSD   | follow           |          2 | 2025-05     |          -0.5951 |      817.946 |        22 | True                |
| BTCUSD   | follow           |          2 | 2025-06     |           4.8541 |      857.649 |        26 | True                |
| BTCUSD   | follow           |          2 | 2025-07     |         -12.2161 |      752.879 |        32 | True                |
| BTCUSD   | follow           |          2 | 2025-08     |          -3.8937 |      723.563 |        26 | True                |
| BTCUSD   | follow           |          2 | 2025-09     |          -4.8349 |      688.58  |        27 | True                |
| BTCUSD   | follow           |          2 | 2025-10     |          -2.5399 |      671.09  |        51 | True                |
| BTCUSD   | follow           |          2 | 2025-11     |          -1.773  |      659.192 |        34 | True                |
| BTCUSD   | follow           |          2 | 2025-12     |         -11.0717 |      586.208 |        37 | True                |
| BTCUSD   | follow           |          2 | 2026-01     |          -0.7211 |      581.981 |        37 | True                |
| BTCUSD   | follow           |          2 | 2026-02     |          -6.9029 |      541.807 |        36 | True                |
| BTCUSD   | follow           |          2 | 2026-03     |          -5.5305 |      511.843 |        32 | True                |
| BTCUSD   | follow           |          2 | 2026-04     |          -5.4854 |      483.766 |        34 | True                |
| BTCUSD   | follow           |          2 | 2026-05     |          -2.2981 |      472.649 |        24 | True                |
| BTCUSD   | follow           |          2 | 2026-06     |           1.5922 |      480.174 |        28 | True                |
| BTCUSD   | follow           |          2 | 2026-07     |          -5.0214 |      456.063 |        22 | True                |
| BTCUSD   | follow           |          2 | 2026-08     |          10.1546 |      502.374 |        26 | True                |
| BTCUSD   | follow           |          2 | 2026-09     |         -11.7107 |      443.542 |        38 | True                |
| BTCUSD   | follow           |          2 | 2026-10     |          -1.3392 |      437.602 |        32 | True                |
| BTCUSD   | follow           |          2 | 2026-11     |           5.6204 |      462.197 |        13 | True                |
| BTCUSD   | opposite_control |          2 | 2025-01     |          -2.9831 |      970.169 |        17 | True                |
| BTCUSD   | opposite_control |          2 | 2025-02     |           0.5798 |      975.794 |        16 | True                |
| BTCUSD   | opposite_control |          2 | 2025-03     |           7.9149 |     1053.03  |        17 | True                |
| BTCUSD   | opposite_control |          2 | 2025-04     |           1.5177 |     1069.01  |        19 | True                |
| BTCUSD   | opposite_control |          2 | 2025-05     |           2.9531 |     1100.58  |        29 | True                |
| BTCUSD   | opposite_control |          2 | 2025-06     |           8.0545 |     1189.22  |        24 | True                |
| BTCUSD   | opposite_control |          2 | 2025-07     |           0.1869 |     1191.45  |        26 | True                |
| BTCUSD   | opposite_control |          2 | 2025-08     |          -3.6851 |     1147.54  |        23 | True                |
| BTCUSD   | opposite_control |          2 | 2025-09     |          -4.3034 |     1098.16  |        23 | True                |
| BTCUSD   | opposite_control |          2 | 2025-10     |           5.5809 |     1159.44  |        27 | True                |
| BTCUSD   | opposite_control |          2 | 2025-11     |          -1.4663 |     1142.44  |        20 | True                |
| BTCUSD   | opposite_control |          2 | 2025-12     |          -5.8554 |     1075.55  |        34 | True                |
| BTCUSD   | opposite_control |          2 | 2026-01     |           5.4507 |     1134.17  |        25 | True                |
| BTCUSD   | opposite_control |          2 | 2026-02     |           1.6469 |     1152.85  |        25 | True                |
| BTCUSD   | opposite_control |          2 | 2026-03     |           1.8387 |     1174.05  |        35 | True                |
| BTCUSD   | opposite_control |          2 | 2026-04     |          -3.8404 |     1128.96  |        32 | True                |
| BTCUSD   | opposite_control |          2 | 2026-05     |           5.3697 |     1189.58  |        21 | True                |
| BTCUSD   | opposite_control |          2 | 2026-06     |          -5.123  |     1128.64  |        25 | True                |
| BTCUSD   | opposite_control |          2 | 2026-07     |          -6.3397 |     1057.09  |        29 | True                |
| BTCUSD   | opposite_control |          2 | 2026-08     |          -2.6365 |     1029.22  |        23 | True                |
| BTCUSD   | opposite_control |          2 | 2026-09     |          -4.0915 |      987.108 |        19 | True                |
| BTCUSD   | opposite_control |          2 | 2026-10     |         -11.3736 |      874.838 |        35 | True                |
| BTCUSD   | opposite_control |          2 | 2026-11     |          -4.4862 |      835.591 |        24 | True                |
| BTCUSD   | follow_stressed  |          5 | 2025-01     |          -3.7732 |      962.268 |        16 | True                |
| BTCUSD   | follow_stressed  |          5 | 2025-02     |          -1.3941 |      948.853 |        22 | True                |
| BTCUSD   | follow_stressed  |          5 | 2025-03     |          -9.6997 |      856.817 |        36 | True                |
| BTCUSD   | follow_stressed  |          5 | 2025-04     |         -11.5418 |      757.925 |        36 | True                |
| BTCUSD   | follow_stressed  |          5 | 2025-05     |          -4.0526 |      727.209 |        24 | True                |
| BTCUSD   | follow_stressed  |          5 | 2025-06     |           3.395  |      751.898 |        26 | True                |
| BTCUSD   | follow_stressed  |          5 | 2025-07     |         -13.4229 |      650.971 |        32 | True                |
| BTCUSD   | follow_stressed  |          5 | 2025-08     |          -5.9332 |      612.347 |        27 | True                |
| BTCUSD   | follow_stressed  |          5 | 2025-09     |          -7.7107 |      565.131 |        29 | True                |
| BTCUSD   | follow_stressed  |          5 | 2025-10     |          -7.0252 |      525.43  |        55 | True                |
| BTCUSD   | follow_stressed  |          5 | 2025-11     |          -4.1095 |      503.837 |        34 | True                |
| BTCUSD   | follow_stressed  |          5 | 2025-12     |          -7.4667 |      466.217 |        39 | True                |
| BTCUSD   | follow_stressed  |          5 | 2026-01     |          -7.9487 |      429.159 |        39 | True                |
| BTCUSD   | follow_stressed  |          5 | 2026-02     |          -7.7824 |      395.76  |        36 | True                |
| BTCUSD   | follow_stressed  |          5 | 2026-03     |          -7.1403 |      367.501 |        33 | True                |
| BTCUSD   | follow_stressed  |          5 | 2026-04     |          -6.9171 |      342.081 |        34 | True                |
| BTCUSD   | follow_stressed  |          5 | 2026-05     |          -4.52   |      326.618 |        25 | True                |
| BTCUSD   | follow_stressed  |          5 | 2026-06     |           0.5924 |      328.553 |        28 | True                |
| BTCUSD   | follow_stressed  |          5 | 2026-07     |          -6.0684 |      308.616 |        22 | True                |
| BTCUSD   | follow_stressed  |          5 | 2026-08     |          -1.3893 |      304.328 |        28 | True                |
| BTCUSD   | follow_stressed  |          5 | 2026-09     |         -12.218  |      267.145 |        39 | True                |
| BTCUSD   | follow_stressed  |          5 | 2026-10     |          -3.3653 |      258.155 |        32 | True                |
| BTCUSD   | follow_stressed  |          5 | 2026-11     |           5.6883 |      272.84  |        13 | True                |
| ETHUSD   | follow           |          2 | 2025-01     |          -0.4    |      996     |        14 | True                |
| ETHUSD   | follow           |          2 | 2025-02     |           6.5341 |     1061.08  |        10 | True                |
| ETHUSD   | follow           |          2 | 2025-03     |          -1.8149 |     1041.82  |        33 | True                |
| ETHUSD   | follow           |          2 | 2025-04     |          -7.5578 |      963.083 |        38 | True                |
| ETHUSD   | follow           |          2 | 2025-05     |           2.3097 |      985.327 |        28 | True                |
| ETHUSD   | follow           |          2 | 2025-06     |          -4.1702 |      944.237 |        30 | True                |
| ETHUSD   | follow           |          2 | 2025-07     |          -3.3983 |      912.149 |        35 | True                |
| ETHUSD   | follow           |          2 | 2025-08     |           2.1604 |      931.855 |        38 | True                |
| ETHUSD   | follow           |          2 | 2025-09     |          -7.1627 |      865.109 |        28 | True                |
| ETHUSD   | follow           |          2 | 2025-10     |          13.2372 |      979.625 |        30 | True                |
| ETHUSD   | follow           |          2 | 2025-11     |          -3.2314 |      947.969 |        22 | True                |
| ETHUSD   | follow           |          2 | 2025-12     |          -6.4943 |      886.405 |        37 | True                |
| ETHUSD   | follow           |          2 | 2026-01     |           5.5766 |      935.836 |        32 | True                |
| ETHUSD   | follow           |          2 | 2026-02     |           4.013  |      973.391 |        29 | True                |
| ETHUSD   | follow           |          2 | 2026-03     |           0.1818 |      975.161 |        34 | True                |
| ETHUSD   | follow           |          2 | 2026-04     |          -2.1848 |      953.855 |        30 | True                |
| ETHUSD   | follow           |          2 | 2026-05     |          -9.6751 |      861.569 |        31 | True                |
| ETHUSD   | follow           |          2 | 2026-06     |          -4.9047 |      819.312 |        41 | True                |
| ETHUSD   | follow           |          2 | 2026-07     |          -7.5183 |      757.713 |        37 | True                |
| ETHUSD   | follow           |          2 | 2026-08     |          -7.3021 |      702.384 |        42 | True                |
| ETHUSD   | follow           |          2 | 2026-09     |          -9.3858 |      636.46  |        32 | True                |
| ETHUSD   | follow           |          2 | 2026-10     |           3.737  |      660.245 |        26 | True                |
| ETHUSD   | follow           |          2 | 2026-11     |           8.2427 |      714.667 |        19 | True                |
| ETHUSD   | opposite_control |          2 | 2025-01     |          -4.8592 |      951.408 |        15 | True                |
| ETHUSD   | opposite_control |          2 | 2025-02     |         -17.5818 |      784.133 |        47 | True                |
| ETHUSD   | opposite_control |          2 | 2025-03     |           0.0937 |      784.868 |        30 | True                |
| ETHUSD   | opposite_control |          2 | 2025-04     |           4.5599 |      820.657 |        35 | True                |
| ETHUSD   | opposite_control |          2 | 2025-05     |         -12.0051 |      722.136 |        36 | True                |
| ETHUSD   | opposite_control |          2 | 2025-06     |         -10.9546 |      643.029 |        42 | True                |
| ETHUSD   | opposite_control |          2 | 2025-07     |          -1.117  |      635.846 |        33 | True                |
| ETHUSD   | opposite_control |          2 | 2025-08     |          19.6644 |      760.882 |        21 | True                |
| ETHUSD   | opposite_control |          2 | 2025-09     |           4.4058 |      794.404 |        20 | True                |
| ETHUSD   | opposite_control |          2 | 2025-10     |          -3.5426 |      766.262 |        30 | True                |
| ETHUSD   | opposite_control |          2 | 2025-11     |           2.9038 |      788.513 |        20 | True                |
| ETHUSD   | opposite_control |          2 | 2025-12     |          -2.4294 |      769.357 |        28 | True                |
| ETHUSD   | opposite_control |          2 | 2026-01     |           8.0052 |      830.945 |        32 | True                |
| ETHUSD   | opposite_control |          2 | 2026-02     |          -1.9411 |      814.816 |        32 | True                |
| ETHUSD   | opposite_control |          2 | 2026-03     |          -9.7842 |      735.092 |        37 | True                |
| ETHUSD   | opposite_control |          2 | 2026-04     |          -2.9467 |      713.432 |        32 | True                |
| ETHUSD   | opposite_control |          2 | 2026-05     |           4.1295 |      742.893 |        22 | True                |
| ETHUSD   | opposite_control |          2 | 2026-06     |           6.2636 |      789.425 |        21 | True                |
| ETHUSD   | opposite_control |          2 | 2026-07     |          -5.9938 |      742.108 |        31 | True                |
| ETHUSD   | opposite_control |          2 | 2026-08     |          -0.1571 |      740.943 |        27 | True                |
| ETHUSD   | opposite_control |          2 | 2026-09     |          -6.5908 |      692.109 |        31 | True                |
| ETHUSD   | opposite_control |          2 | 2026-10     |          -4.4993 |      660.968 |        33 | True                |
| ETHUSD   | opposite_control |          2 | 2026-11     |          -4.9036 |      628.557 |        18 | True                |
| ETHUSD   | follow_stressed  |          5 | 2025-01     |          -0.7017 |      992.983 |        14 | True                |
| ETHUSD   | follow_stressed  |          5 | 2025-02     |           6.3588 |     1056.12  |        10 | True                |
| ETHUSD   | follow_stressed  |          5 | 2025-03     |          -2.5088 |     1029.63  |        33 | True                |
| ETHUSD   | follow_stressed  |          5 | 2025-04     |          -7.6468 |      950.895 |        38 | True                |
| ETHUSD   | follow_stressed  |          5 | 2025-05     |           0.3515 |      954.237 |        29 | True                |
| ETHUSD   | follow_stressed  |          5 | 2025-06     |          -4.9503 |      907     |        30 | True                |
| ETHUSD   | follow_stressed  |          5 | 2025-07     |          -4.2657 |      868.31  |        35 | True                |
| ETHUSD   | follow_stressed  |          5 | 2025-08     |           1.2401 |      879.078 |        38 | True                |
| ETHUSD   | follow_stressed  |          5 | 2025-09     |          -9.3727 |      796.685 |        30 | True                |
| ETHUSD   | follow_stressed  |          5 | 2025-10     |          11.4813 |      888.155 |        31 | True                |
| ETHUSD   | follow_stressed  |          5 | 2025-11     |          -3.6829 |      855.445 |        22 | True                |
| ETHUSD   | follow_stressed  |          5 | 2025-12     |          -8.0599 |      786.497 |        38 | True                |
| ETHUSD   | follow_stressed  |          5 | 2026-01     |           4.727  |      823.675 |        33 | True                |
| ETHUSD   | follow_stressed  |          5 | 2026-02     |           3.3454 |      851.23  |        29 | True                |
| ETHUSD   | follow_stressed  |          5 | 2026-03     |          -0.6728 |      845.503 |        34 | True                |
| ETHUSD   | follow_stressed  |          5 | 2026-04     |          -3.9394 |      812.195 |        31 | True                |
| ETHUSD   | follow_stressed  |          5 | 2026-05     |         -11.6278 |      717.755 |        32 | True                |
| ETHUSD   | follow_stressed  |          5 | 2026-06     |          -6.5022 |      671.085 |        42 | True                |
| ETHUSD   | follow_stressed  |          5 | 2026-07     |          -8.6919 |      612.755 |        37 | True                |
| ETHUSD   | follow_stressed  |          5 | 2026-08     |          -9.9884 |      551.551 |        44 | True                |
| ETHUSD   | follow_stressed  |          5 | 2026-09     |         -13.3397 |      477.975 |        34 | True                |
| ETHUSD   | follow_stressed  |          5 | 2026-10     |           2.6717 |      490.746 |        26 | True                |
| ETHUSD   | follow_stressed  |          5 | 2026-11     |           6.8485 |      524.354 |        20 | True                |

## High-return asymmetric qualification: 0
No qualifying strategy.

## Data and execution caveats
- OI fall does not uniquely prove liquidation; no real liquidation tape
- Historical Delta funding candles proxy, not verified executed funding payments
- 1minute OHLC fill stop is pessimistic open-through-gap but not order-book execution
- Pyramiding is deliberately NOT used; cannot manufacture +500% with leverage
- 2025 research-exposed; 2026 partial through November 17 and research-exposed
- Market microstructure hypothesis requires a placebo and future-forward validation
- EMA/ATR grid not used; 1h ATR used solely for risk management
- This analysis does not provide live execution or a trading recommendation

Full trade evidence in trades.csv.gz; script scripts/research_oi_deleveraging_event_20261119.py
