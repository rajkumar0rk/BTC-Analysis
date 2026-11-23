# Touch-close vs break-and-reclaim (15M Supertrend + EMA20)

First touch only per ST cycle, flip candle excluded. Entry at next 15m open AFTER closed confirmation. Fixed 1R stop and 2R/3R targets; 1m stop/TP simulation. Includes both long and short; weekends on.

Touch-close: after flip, first EMA20 interaction CLOSES on trend side; trade next open.
Reclaim: after flip, first EMA20 interaction CLOSES on WRONG side; later separate 15m bar CLOSES back on trend side; trade next open.
Both refer to prior frozen EMA20 and completed candle EMA20 to prevent ambiguous closes. No repaint.

Data Jan 2025–Oct 2026 IST, Delta India historical 1m; 1x notional, $1000 starting capital, 0.05% taker fee each side + 18% GST and 0.02% slippage each side.
No funding, liquidation, spread, depth, tick-order guarantee, or genuine 2026 out-of-sample.

## O-H-L-C 1m path comparison

| symbol   | config              |   trades |   win_rate_pct |   profit_factor |   net_return_pct |   profitable_months |   return_2025_pct |   return_2026_pct |   max_floating_dd_pct |
|:---------|:--------------------|---------:|---------------:|----------------:|-----------------:|--------------------:|------------------:|------------------:|----------------------:|
| BTCUSD   | touch_close_2R      |      809 |         31.15  |          0.6743 |         -66.4683 |                   4 |           -56.262 |           -23.336 |                66.891 |
| BTCUSD   | touch_close_3R      |      809 |         25.34  |          0.6512 |         -69.4444 |                   3 |           -60.934 |           -21.784 |                71.041 |
| BTCUSD   | touch_close_2R_1hST |      406 |         31.773 |          0.679  |         -43.1999 |                   2 |           -34.722 |           -12.987 |                44.339 |
| BTCUSD   | touch_close_3R_1hST |      406 |         25.369 |          0.5968 |         -50.738  |                   2 |           -44.643 |           -11.011 |                52.061 |
| BTCUSD   | reclaim4_2R         |      434 |         29.954 |          0.6775 |         -49.743  |                   4 |           -23.7   |           -34.133 |                53.325 |
| BTCUSD   | reclaim4_3R         |      434 |         26.498 |          0.7352 |         -44.5322 |                   5 |           -15.906 |           -34.041 |                49.468 |
| BTCUSD   | reclaim4_2R_1hST    |      206 |         27.67  |          0.5579 |         -37.093  |                   3 |           -16.741 |           -24.444 |                41.279 |
| BTCUSD   | reclaim4_3R_1hST    |      206 |         23.786 |          0.6391 |         -32.108  |                   3 |           -12.689 |           -22.241 |                36.764 |
| BTCUSD   | reclaim8_3R_1hST    |      232 |         23.707 |          0.659  |         -33.062  |                   5 |           -13.479 |           -22.634 |                37.187 |
| BTCUSD   | reclaim8_3R         |      493 |         26.369 |          0.7372 |         -47.583  |                   4 |           -19.567 |           -34.831 |                52.924 |
| ETHUSD   | touch_close_2R      |      793 |         31.274 |          0.7862 |         -70.3008 |                   4 |           -40.436 |           -50.139 |                71.901 |
| ETHUSD   | touch_close_3R      |      793 |         27.112 |          0.7368 |         -76.2096 |                   5 |           -50.287 |           -52.144 |                78.439 |
| ETHUSD   | touch_close_2R_1hST |      390 |         29.231 |          0.7165 |         -54.1844 |                   5 |           -23.166 |           -40.371 |                54.476 |
| ETHUSD   | touch_close_3R_1hST |      390 |         23.59  |          0.6715 |         -58.7383 |                   3 |           -31.724 |           -39.566 |                59.975 |
| ETHUSD   | reclaim4_2R         |      366 |         34.699 |          0.8966 |         -22.848  |                   8 |             9.856 |           -29.77  |                34.548 |
| ETHUSD   | reclaim4_3R         |      366 |         30.874 |          0.9213 |         -18.0612 |                  10 |             8.456 |           -24.45  |                34.167 |
| ETHUSD   | reclaim4_2R_1hST    |      186 |         35.484 |          0.8712 |         -13.1021 |                  10 |            -7.604 |            -5.951 |                22.282 |
| ETHUSD   | reclaim4_3R_1hST    |      186 |         29.57  |          0.861  |         -14.0424 |                   9 |           -12.743 |            -1.489 |                22.613 |
| ETHUSD   | reclaim8_3R_1hST    |      207 |         31.401 |          0.9211 |          -8.8163 |                   8 |            -7.561 |            -1.358 |                21.954 |
| ETHUSD   | reclaim8_3R         |      412 |         31.068 |          0.9002 |         -24.9239 |                  10 |             6.215 |           -29.317 |                39     |

All path variants and monthly mark-to-market in summary.csv / monthly_mark_to_market.csv.
This is retrospective in-sample research, not a validated live edge.
