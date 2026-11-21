# 1H EMA20 second touch — FIXED TP 1000 BTC points OR confirmed Supertrend reversal

**Exact exit setup: no profit lock, no trailing stop, no separate SL.**
First exit wins: fixed +1000 BTC-price points (percentage equivalent frozen for ETH), or confirmed 1H Supertrend flip at the following 1H candle's first 1m open.
Entry unchanged: second distinct 1H EMA20-touch candle after Supertrend(10,3) flip; one trade per trend cycle; entry at 1m crossing of last completed hourly EMA20.

| 1m assumed path | Asset | Trades | Fixed TP exits | Supertrend flip exits | Net wins | Net losses | Win rate | Profit factor | Net return | Profitable months | Max floating DD |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| O-H-L-C | BTCUSD | 361 | 181 | 179 | 181 | 180 | 50.1385% | 0.6732 | -56.55239% | 7/22 | 57.859% |
| O-H-L-C | ETHUSD | 344 | 205 | 138 | 205 | 139 | 59.593% | 0.705 | -57.59201% | 7/22 | 61.1016% |
| O-L-H-C | BTCUSD | 361 | 181 | 179 | 181 | 180 | 50.1385% | 0.6732 | -56.55239% | 7/22 | 57.859% |
| O-L-H-C | ETHUSD | 344 | 205 | 138 | 205 | 139 | 59.593% | 0.705 | -57.59201% | 7/22 | 61.1016% |

## Limitations
- 1-minute OHLC historical candles, two synthetic within-minute paths O-H-L-C and O-L-H-C ONLY to test ambiguous entry-minute sequence. Not measured historical ticks.
- 1H reversal only confirmed at hour close, exit at NEXT hour open. No future peeking.
- 1x account-sizing ($1000 starting each symbol), adverse 0.02% slippage each side, 0.05% taker each side, GST 18% on fees.
- No liquidation, real margin, bid/ask, funding, orderbook, latency, exchange marketable-order impact. Positive model is not a live guarantee.
- A final open position is closed for sample accounting only. 2026 was researched before and is not untouched out-of-sample.

Artifacts: summary.csv, monthly_mark_to_market.csv, trade_ledger.csv.gz, quality.json.
