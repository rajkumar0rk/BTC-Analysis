# BTCUSD 15M ONLY: Touch-close vs Reclaim vs Combined

BTCUSD ONLY. Every signal and indicator exclusively 15m. No 1h indicators/filters. First touch only per ST cycle; flip candle excluded. Next 15m open entry. Fixed 1R stop and 2R/3R targets; 1m stop/TP simulation. Includes both long and short; weekends on.

Touch-close: after flip, first EMA20 interaction CLOSES on trend side; trade next open.
Reclaim: after flip, first EMA20 interaction CLOSES on WRONG side; later separate 15m bar CLOSES back on trend side; trade next open.
Combined: use Touch when first touched candle closes on trend side, else use Reclaim if it closes on wrong side and later returns. Only one entry per Supertrend cycle.
Both refer to prior frozen EMA20 and completed candle EMA20 to prevent ambiguous closes. No repaint.

BTCUSD data Jan 2025–Oct 2026 IST, Delta India historical 1m ONLY for intrabar TP/SL monitoring; 1x notional, $1000 starting capital, 0.05% taker fee each side + 18% GST and 0.02% slippage each side.
No funding, liquidation, spread, depth, tick-order guarantee, or genuine 2026 out-of-sample.

## O-H-L-C 1m path comparison

| symbol   | config         |   trades |   win_rate_pct |   profit_factor |   net_return_pct |   profitable_months |   return_2025_pct |   return_2026_pct |   max_floating_dd_pct |
|:---------|:---------------|---------:|---------------:|----------------:|-----------------:|--------------------:|------------------:|------------------:|----------------------:|
| BTCUSD   | touch_close_2R |      809 |         31.15  |          0.6743 |         -66.4683 |                   4 |           -56.262 |           -23.336 |                66.891 |
| BTCUSD   | touch_close_3R |      809 |         25.34  |          0.6512 |         -69.4444 |                   3 |           -60.934 |           -21.784 |                71.041 |
| BTCUSD   | reclaim4_2R    |      434 |         29.954 |          0.6775 |         -49.743  |                   4 |           -23.7   |           -34.133 |                53.325 |
| BTCUSD   | reclaim4_3R    |      434 |         26.498 |          0.7352 |         -44.5322 |                   5 |           -15.906 |           -34.041 |                49.468 |
| BTCUSD   | reclaim8_3R    |      493 |         26.369 |          0.7372 |         -47.583  |                   4 |           -19.567 |           -34.831 |                52.924 |
| BTCUSD   | combined4_2R   |     1243 |         30.732 |          0.6823 |         -83.1479 |                   2 |           -66.627 |           -49.503 |                84.307 |
| BTCUSD   | combined4_3R   |     1243 |         25.744 |          0.6906 |         -83.0515 |                   1 |           -67.148 |           -48.409 |                85.237 |
| BTCUSD   | combined8_3R   |     1302 |         25.73  |          0.6917 |         -83.9837 |                   1 |           -68.578 |           -49.028 |                86.247 |

All path variants and monthly mark-to-market in summary.csv / monthly_mark_to_market.csv.
This is retrospective in-sample research, not a validated live edge.
