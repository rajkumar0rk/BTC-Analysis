# 1H EMA20 second touch — TP200 plus 200-point trailing stop

One entry per Supertrend 10,3 cycle. Second distinct post-flip EMA20 touch enters immediately on 1m OHLC.
Fixed take profit +200 BTC price points; trailing distance 200 BTC price points, active immediately. ETH both distances scaled as 200*ETHentry/precedingBTCclose and frozen. NO ATR trailing, no separate fixed SL.
Stop-first if 1m candle crosses both exit levels; trailing updates on completed 1m candles become active next minute.
22 months 2025-01–2026-10 (IST) using SHA-verified Delta India BTCUSD and ETHUSD 1m data. 1x evolving notional, $1000 starting account, fees+GST and adverse slippage.

| Asset | Trades | TP exits | Trailing-stop exits | Win rate after fees | Profit factor | Net return | Max floating DD | Profitable months |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSD | 361 | 108 | 253 | 29.92% | 0.1239 | -48.117% | 48.331% | 0/22 |
| ETHUSD | 344 | 102 | 242 | 29.65% | 0.1271 | -47.220% | 47.489% | 0/22 |

## Cautions
- The trailing stop is initially at ±200 points, so it IS a protective stop. There is no ATR-based trail or extra stop.
- Ambiguous 1m candle that reaches TP and trailing stop counts stop FIRST. Do not backfill a candle's new high/low into its already-active trail.
- On the entry minute no TP or favorable trail update is credited. Initial stop touched on entry minute is filled at its stop level; tick ordering is unknown.
- Gross/model net equity and 22-month monthly returns count fees (0.05% each side + 18% GST) and 0.02% adverse slippage both sides.
- Not a live execution guarantee: funding, exact fills, actual bid/ask spread, margin/liquidation, and real tick ordering missing.
- Historic 2026 already extensively explored and cannot be considered a pristine out-of-sample validation.
- 2025 archive begins UTC Jan 1 and excludes first 5.5 IST hours of Jan 2025.

Outputs: summary.csv, monthly_mark_to_market.csv, trade_ledger.csv.gz, quality.json.
