# EMA20 second-touch intrabar backtest

Reproducible research on 1m Delta Exchange India OHLC. Not live fills.
2025-01 to 2026-10 inclusive, 22 IST calendar months; January 2025 first 5h30m IST unavailable.
2026 is prior-research-exposed rather than untouched holdout.

| Symbol | Entry TF | Trades | Win rate | Profit factor | Net % (1x) | Max closed-trade DD | Positive months |
|---|---|---:|---:|---:|---:|---:|---:|
| BTCUSD | 15m | 1977 | 25.04% | 0.6833 | -93.693% | 93.936% | 1/22 |
| BTCUSD | 60m | 699 | 24.32% | 0.6763 | -74.845% | 74.845% | 6/22 |
| ETHUSD | 15m | 2335 | 24.75% | 0.7168 | -97.377% | 97.400% | 1/22 |
| ETHUSD | 60m | 1020 | 23.04% | 0.6321 | -88.119% | 88.566% | 3/22 |

## Cost and execution caveats
- Assumed 0.05% taker fee per side plus 18% GST on fees; 0.02% adverse slippage per side.
- 1x evolving notional, initial 1000 USD model equity, no leverage, no funding, no actual spreads.
- Last completed HTF EMA and Supertrend; touches distinct HTF candles, entry in 1m candle.
- On same entry 1m candle, SL crossing is adverse-first; BE/trailing changes only effective next minute.
- There is no tick tape; a 1-minute high/low cannot establish exact touch ordering or stop trigger time.
- No optimization or selection against 2026. Exit-counted IST months, no-trade months included.

See summary.csv, monthly_results.csv, quality.json and trade_ledger.csv.gz.
