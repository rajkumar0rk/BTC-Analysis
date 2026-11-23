# BTCUSD 15M only — Reclaim entry quality and ATR risk scale

No 1H data or indicators. 15m ST(10,3), EMA20. 1m exit replay only.
Jan 2025-Oct 2026 inclusive (22 completed IST months); $1000 initial, 1x notional; taker fee .05% each side plus 18% GST, adverse slippage .02% each side.
Original first-touch closing across EMA20 then later reclaim, one trade per ST cycle; stop on 1R or next 15m confirmed ST reversal; fixed 2R/3R/4R TP.
Signal quality tests use completed 15m indicators only; no future candle filters. Optional EMA slope, reclaim candle strength, distance beyond EMA, and 15m volume are separate ablations.
Risk/ST = distance from entry to previous closed 15m ST line; ATR = ATR10 of latest completed 15m bar; CAP = min(ST R, multiple ATR).
1m intrabar OHLC paths O-H-L-C and O-L-H-C are hypothetical, not historical ticks.
ALL 2025/2026 data has already been inspected: best in-sample does not establish a repeatable forward edge.

## In-sample outcomes (O-H-L-C)

| config                     |   trades |   win_rate_pct |   profit_factor |   net_return_pct |   profitable_months |   profitable_2025_months |   profitable_2026_months |   return_2025_pct |   return_2026_pct |   max_floating_drawdown_pct |
|:---------------------------|---------:|---------------:|----------------:|-----------------:|--------------------:|-------------------------:|-------------------------:|------------------:|------------------:|----------------------------:|
| reclaim4_vol150_ST_3R      |       81 |         34.568 |          0.8565 |          -4.9002 |                  10 |                        7 |                        3 |             1.856 |            -6.634 |                       9.706 |
| reclaim4_vol120_ST_3R      |      136 |         32.353 |          0.8472 |          -8.8966 |                  11 |                        7 |                        4 |             5.515 |           -13.658 |                      16.974 |
| reclaim1_ST_3R             |      248 |         26.21  |          0.7225 |         -27.7307 |                   5 |                        4 |                        1 |           -16.815 |           -13.122 |                      32.391 |
| reclaim4_slope4_ST_3R      |      328 |         26.829 |          0.7636 |         -31.6904 |                   5 |                        3 |                        2 |            -9.559 |           -24.47  |                      37.96  |
| reclaim2_ST_3R             |      345 |         26.087 |          0.7399 |         -36.3313 |                   5 |                        4 |                        1 |           -11.907 |           -27.726 |                      42.265 |
| reclaim4_body55_ST_3R      |      279 |         25.806 |          0.6709 |         -37.4711 |                   6 |                        6 |                        0 |           -11.706 |           -29.181 |                      41.498 |
| reclaim4_margin20_ST_3R    |      289 |         25.606 |          0.6477 |         -41.0791 |                   4 |                        3 |                        1 |           -17.185 |           -28.853 |                      45.628 |
| reclaim4_ST_3R_BE1         |      434 |         22.35  |          0.7283 |         -41.4995 |                   5 |                        5 |                        0 |           -14.82  |           -31.321 |                      46.5   |
| reclaim4_ATR15_3R_slope4   |      328 |         24.085 |          0.6236 |         -42.0851 |                   2 |                        2 |                        0 |           -18.007 |           -29.366 |                      45.648 |
| reclaim4_slope8_ST_3R      |      409 |         26.161 |          0.7318 |         -42.7561 |                   4 |                        3 |                        1 |           -14.015 |           -33.425 |                      47.85  |
| reclaim4_ST_3R_STEP2       |      434 |         25.346 |          0.7036 |         -43.527  |                   5 |                        5 |                        0 |           -17.955 |           -31.169 |                      47.635 |
| reclaim4_body35_ST_3R      |      366 |         25.956 |          0.6814 |         -43.9065 |                   6 |                        5 |                        1 |           -21.994 |           -28.091 |                      47.335 |
| base_ST_3R                 |      434 |         26.498 |          0.7352 |         -44.5322 |                   5 |                        4 |                        1 |           -15.906 |           -34.041 |                      49.468 |
| reclaim4_margin10_ST_3R    |      352 |         25     |          0.6651 |         -44.7627 |                   2 |                        2 |                        0 |           -25.247 |           -26.107 |                      49.041 |
| reclaim4_CAP2_3R           |      434 |         25.806 |          0.709  |         -46.5723 |                   4 |                        4 |                        0 |           -14.979 |           -37.159 |                      50.599 |
| base_ST_2R                 |      434 |         29.954 |          0.6775 |         -49.743  |                   4 |                        4 |                        0 |           -23.7   |           -34.133 |                      53.325 |
| reclaim4_ATR15_3R_body35   |      366 |         22.678 |          0.5593 |         -50.7609 |                   2 |                        2 |                        0 |           -28.553 |           -31.083 |                      52.889 |
| reclaim4_ATR15_3R_margin10 |      352 |         21.591 |          0.5467 |         -50.9489 |                   2 |                        2 |                        0 |           -30.251 |           -29.675 |                      53.242 |
| reclaim4_ATR2_3R           |      434 |         24.885 |          0.667  |         -51.0607 |                   4 |                        4 |                        0 |           -23.887 |           -35.702 |                      54.854 |
| reclaim4_ATR2_2R           |      434 |         29.493 |          0.6496 |         -52.507  |                   4 |                        4 |                        0 |           -22.428 |           -38.776 |                      55.14  |
| reclaim4_ATR2_4R           |      434 |         23.272 |          0.6374 |         -53.7528 |                   1 |                        1 |                        0 |           -30.422 |           -33.532 |                      57.701 |
| reclaim4_ATR1_3R           |      434 |         20.968 |          0.517  |         -53.7794 |                   2 |                        2 |                        0 |           -25.911 |           -37.615 |                      55.9   |
| reclaim4_CAP15_3R          |      434 |         23.041 |          0.5918 |         -54.6596 |                   2 |                        2 |                        0 |           -28.514 |           -36.574 |                      57.567 |
| reclaim4_ATR15_2R          |      434 |         28.571 |          0.5756 |         -54.7177 |                   3 |                        3 |                        0 |           -26.493 |           -38.397 |                      56.77  |
| reclaim4_ATR15_3R          |      434 |         22.811 |          0.584  |         -55.9583 |                   2 |                        2 |                        0 |           -29.348 |           -37.664 |                      58.771 |
| reclaim4_ATR15_4R          |      434 |         20.046 |          0.5742 |         -56.1351 |                   2 |                        2 |                        0 |           -33.982 |           -33.556 |                      59.468 |
| reclaim4_ATR1_2R           |      434 |         26.498 |          0.4347 |         -56.4636 |                   1 |                        1 |                        0 |           -28.875 |           -38.789 |                      57.492 |
| reclaim4_ATR15_3R_BE1      |      434 |         15.668 |          0.4413 |         -61.1703 |                   1 |                        1 |                        0 |           -35.523 |           -39.777 |                      63.474 |
| reclaim4_ATR15_3R_STEP2    |      434 |         18.203 |          0.4261 |         -61.7687 |                   2 |                        2 |                        0 |           -35.316 |           -40.895 |                      64.037 |

Full monthly returns, trades ledger, alternate minute path and settings are in sidecar files.
