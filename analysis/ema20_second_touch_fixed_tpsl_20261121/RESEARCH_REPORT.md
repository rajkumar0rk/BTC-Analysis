# Fixed TP/SL 200/100 BTC-equivalent — second EMA20 touch

Historical 1-minute Delta Exchange India OHLC research. 22 IST calendar months Jan 2025–Oct 2026. No tuning.
ETH distances dynamically scaled to ex-ante BTC percentage at each entry; NEVER 200/100 ETH dollars.

| Asset | Signal TF | Trades | Wins | Win rate | TP hit | SL hit | PF | Net return | Drawdown | Positive months |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSD | 15m | 6397 | 1715 | 26.81% | 1715 | 4682 | 0.09679 | -99.996% | 100.00% | 0/22 |
| BTCUSD | 60m | 1941 | 506 | 26.07% | 506 | 1435 | 0.09722 | -95.824% | 95.82% | 0/22 |
| ETHUSD | 15m | 7409 | 1789 | 24.15% | 1789 | 5620 | 0.08677 | -100.000% | 100.00% | 0/22 |
| ETHUSD | 60m | 2055 | 453 | 22.04% | 453 | 1602 | 0.07548 | -97.332% | 97.33% | 0/22 |

- 1× notional evolving account exposure with $1000 initial equity.
- 0.05% taker fee each side, 18% GST on fee; 0.02% adverse slippage each side.
- Stop first whenever stop and target touched within the same 1-minute candle.
- No TP credit on entry minute because touch ordering is unknowable; adverse stop honored.
- No trailing or breakeven. Funding, spreads, real tick order sequence and latency unavailable.
- 2026 period already explored in other studies; not a pristine out-of-sample check.
- Early Jan 2025 IST first 5.5h unavailable; all other scored minutes contiguous.

See monthly_results.csv, summary.csv, trade_ledger.csv.gz, quality.json, NOVELTY_CHECK.md.
