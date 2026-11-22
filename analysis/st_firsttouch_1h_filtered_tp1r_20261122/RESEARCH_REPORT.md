# 1H first EMA20 touch + completed-volume and ATR14 filters: TP1R, Supertrend-flip exit

BTCUSD and ETHUSD, 1H indicators, 1-minute execution, 22 IST months January 2025 to October 2026.
Entry: after fully confirmed Supertrend(ATR10, factor3) flips, skip the flip candle and enter at first subsequent 1H EMA20 touch.
Filters on PREVIOUS COMPLETED 1H candle: volume >1.2×SMA20(volume) AND Wilder ATR14>SMA20(ATR14). Reject full ST cycle if either fails at first eligible touch.
Freeze R=direction×(executed EMA20-touch entry - last completed 1H ST line). Take profit fixed 1R. Exit adverse only after CONFIRMED opposite 1H ST flip, execute first 1m open next hour.
No line-touch stop, hard-price stop, profit lock or trailing. No subsequent reentry same ST epoch.

| Asset | Hypothetical within-minute path | Trades | Wins | Losses | TP1R exits | Flip exits | Win rate | PF | Total net | Positive months | Floating drawdown |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSD | O-H-L-C | 83 | 42 | 41 | 43 | 40 | 50.602% | 0.5627 | -23.1593% | 8/22 | 24.6758% |
| BTCUSD | O-L-H-C | 83 | 41 | 42 | 43 | 40 | 49.398% | 0.5528 | -23.9117% | 8/22 | 25.1574% |
| ETHUSD | O-H-L-C | 63 | 37 | 26 | 37 | 26 | 58.73% | 0.9886 | -0.5762% | 10/22 | 10.4064% |
| ETHUSD | O-L-H-C | 63 | 37 | 26 | 37 | 26 | 58.73% | 0.9886 | -0.5762% | 10/22 | 10.473% |

## Matched 15M TP1R control
- Matched 15M results: analysis/st_firsttouch_15m_filtered_tp1r_20261122/summary.csv
- All volume, ATR14, ST10x3, first-touch, 1R, exit and cost settings unchanged; only TF changes to 1H.

## Caveats
- SHA256-checked Delta India 1-minute candles, 963030 minutes per instrument; 2025Jan through 2026Oct.
- Within-one-minute OHLC sequencing only hypothetical, not real tick-level execution or a proven bound.
- 0.05% taker fee each side + GST18% on fees; 0.02% adverse slippage each side; $1000 initial, 1x evolving notional.
- No real funding, margin/liquidation, spread/order-book/latency model; marked open equity included in monthly returns.
- Profit target reference R is NOT an actual capped loss; confirmed Supertrend flip may realize a larger loss than R.
- Historical 2026 data has already been researched; not pristine out-of-sample validation.

Artifacts: summary.csv, monthly_mark_to_market.csv, trades.csv.gz, quality.json, execution.log.
