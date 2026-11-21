# Same 1H second-touch entry: TP200 reached before SL100?

**TP and SL are fixed price barriers, not 200-step ratchet and not trail.**
Two exit variants: barrier-only answers price-event race, and flip-exit applies the current mandatory confirmed 1H Supertrend flip rule.
All results rely on hypothetical 1m paths, not historical ticks; even 1m OHLC cannot always resolve which level was hit first.

| Mode | 1m hypothetical path | Asset | Trades | TP +200 first | SL -100 first | ST flip first | TP % all entries | TP % resolved barriers | Both levels in exit 1m |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| BARRIER_ONLY | O-H-L-C | BTCUSD | 361 | 83 | 278 | 0 | 22.992% | 22.992% | 3 |
| BARRIER_ONLY | O-H-L-C | ETHUSD | 344 | 98 | 246 | 0 | 28.488% | 28.488% | 18 |
| BARRIER_ONLY | O-L-H-C | BTCUSD | 361 | 81 | 280 | 0 | 22.438% | 22.438% | 3 |
| BARRIER_ONLY | O-L-H-C | ETHUSD | 344 | 96 | 248 | 0 | 27.907% | 27.907% | 17 |
| FLIP_EXIT | O-H-L-C | BTCUSD | 361 | 83 | 278 | 0 | 22.992% | 22.992% | 3 |
| FLIP_EXIT | O-H-L-C | ETHUSD | 344 | 98 | 246 | 0 | 28.488% | 28.488% | 18 |
| FLIP_EXIT | O-L-H-C | BTCUSD | 361 | 81 | 280 | 0 | 22.438% | 22.438% | 3 |
| FLIP_EXIT | O-L-H-C | ETHUSD | 344 | 96 | 248 | 0 | 27.907% | 27.907% | 17 |

## Caveats
- No fixed TP optimization, one entry per trend epoch exactly as present strategy; EMA touch within second 1H candle on 1m raw OHLC.
- ETH distances proportionally scaled to BTC at entry, not absolute ETH price points.
- O-H-L-C and O-L-H-C are invented hypothetical price sequences and are not rigorous bounds; actual 1m path is not known.
- Includes illustrative taker fees, 18% GST and 0.02% adverse slippage; excludes funding, real tick execution and liquidation.
- A Supertrend flip exit is **not** counted as TP nor SL; it is distinct in FLIP_EXIT variant.
- 2026 historical data was used in prior research and is not an out-of-sample validation.

Files: summary.csv, monthly_mark_to_market.csv, trade_ledger.csv.gz, quality.json.
