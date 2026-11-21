# 1H EMA20 second-touch with no TP, no SL, no other exit

No position can close normally; after first entry, the next exit is an accounting-only mark at 2026-10-31.
One-per-Supertrend gate technically active but never tested for re-entry (position remains open).
2025-01 through 2026-10, BTC/ETH Delta India 1m OHLC, mark-to-market returns include estimated hypothetical exit costs.

| Symbol | Direction | Entry UTC | Hypothetical net return | Peak-to-trough floating drawdown | Held days | Negative MTM months |
|---|---|---|---:|---:|---:|---:|
| BTCUSD | LONG | 2025-01-05T13:33:00+00:00 | -20.834% | 54.215% | 664.21 | 11/22 |
| ETHUSD | LONG | 2025-01-05T06:01:00+00:00 | -37.994% | 69.668% | 664.52 | 14/22 |

## Interpretation
- The return is **not realized trading PnL**: no TP, SL, flip, or time exit exists. Only a hypothetical forced end-of-sample sale/cover.
- A single trade cannot measure a win rate or profit factor meaningfully.
- Marked 1m price extremes approximate floating risk conservatively; there is no true tick-level entry/exit data.
- No actual liquidation margin, funding, bid/ask spread, or overnight exposure costs; data history evaluated repeatedly and not untouched.
- ETH and BTC remain independent accounts with 1x notional as an illustrative cash exposure. No leverage used.

See summary.csv, monthly_mark_to_market.csv, entries.csv, quality.json.
