# BTCUSD ONLY — Touch-close vs break-and-reclaim vs combined entry (15M Supertrend + EMA20)

First touch only per ST cycle, flip candle excluded. Entry at next 15m open AFTER closed confirmation. Fixed 1R stop and 2R/3R targets; 1m stop/TP simulation. Includes both long and short; weekends on.

Touch-close: after flip, first EMA20 interaction CLOSES on trend side; trade next open.
Reclaim: after flip, first EMA20 interaction CLOSES on WRONG side; later separate 15m bar CLOSES back on trend side; trade next open.
Combined: use Touch when first touched candle closes on trend side, else use Reclaim if it closes on wrong side and later returns. Only one entry per Supertrend cycle.
Both refer to prior frozen EMA20 and completed candle EMA20 to prevent ambiguous closes. No repaint.

Data Jan 2025–Oct 2026 IST, Delta India historical 1m; 1x notional, $1000 starting capital, 0.05% taker fee each side + 18% GST and 0.02% slippage each side.
No funding, liquidation, spread, depth, tick-order guarantee, or genuine 2026 out-of-sample.

## O-H-L-C 1m path comparison

| symbol   | config              |   trades |   win_rate_pct |   profit_factor |   net_return_pct |   profitable_months |   return_2025_pct |   return_2026_pct |   max_floating_dd_pct |
|:---------|:--------------------|---------:|---------------:|----------------:|-----------------:|--------------------:|------------------:|------------------:|----------------------:|
| BTCUSD   | touch_close_2R      |      809 |         31.15  |          0.6743 |         -66.4683 |                   4 |           -56.262 |           -23.336 |                66.891 |
| BTCUSD   | touch_close_2R_1hST |      406 |         31.773 |          0.679  |         -43.1999 |                   2 |           -34.722 |           -12.987 |                44.339 |
| BTCUSD   | reclaim4_3R         |      434 |         26.498 |          0.7352 |         -44.5322 |                   5 |           -15.906 |           -34.041 |                49.468 |
| BTCUSD   | reclaim4_3R_1hST    |      206 |         23.786 |          0.6391 |         -32.108  |                   3 |           -12.689 |           -22.241 |                36.764 |
| BTCUSD   | combined4_2R        |     1243 |         30.732 |          0.6823 |         -83.1479 |                   2 |           -66.627 |           -49.503 |                84.307 |
| BTCUSD   | combined4_3R        |     1243 |         25.744 |          0.6906 |         -83.0515 |                   1 |           -67.148 |           -48.409 |                85.237 |
| BTCUSD   | combined4_2R_1hST   |      612 |         30.392 |          0.6453 |         -64.2687 |                   2 |           -45.65  |           -34.257 |                65.671 |
| BTCUSD   | combined4_3R_1hST   |      612 |         24.837 |          0.6163 |         -66.5551 |                   2 |           -51.667 |           -30.803 |                68.828 |
| BTCUSD   | combined8_3R        |     1302 |         25.73  |          0.6917 |         -83.9837 |                   1 |           -68.578 |           -49.028 |                86.247 |
| BTCUSD   | combined8_3R_1hST   |      638 |         24.765 |          0.6225 |         -67.025  |                   2 |           -52.104 |           -31.152 |                69.266 |

All path variants and monthly mark-to-market in summary.csv / monthly_mark_to_market.csv.
This is retrospective in-sample research, not a validated live edge.
