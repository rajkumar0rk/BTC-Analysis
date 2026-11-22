# 1H first EMA20 touch: NO fixed TP, ATR14 trailing stop 2× / 3× and Supertrend flip exit

BTCUSD and ETHUSD independently on 1H indicators, entry/exits monitored with 1m OHLC, Jan2025–Oct2026 (22 complete IST months).
Entry after ST(10,3) flip, ignore flip candle, FIRST subsequent EMA20 touch, both last-completed 1H volume >1.2×SMA20 and ATR14>SMA20(ATR14) required, max one entry per ST epoch.
No take-profit. At entry, freeze distance = multiplier×last completed Wilder ATR14. Initial protective stop from entry +/- distance; then follow favorable 1m price extremes using fixed distance, never moving stop backwards.
Confirmed opposite 1H Supertrend flip remains an independent exit at next 1H open; first of stop touch or flip executes. No exit simply on Supertrend LINE touch.

| Asset | ATR multiple | Assumed within-1m path | Trades | Wins | Losses | ATR stop exits | ST flip exits | Win% | PF | Net return | Profitable months | Max floating DD |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSD | 2.0× | O-H-L-C | 83 | 21 | 62 | 77 | 6 | 25.301% | 0.5623 | -19.1727% | 7/22 | 22.8909% |
| BTCUSD | 2.0× | O-L-H-C | 83 | 22 | 61 | 77 | 6 | 26.506% | 0.6312 | -16.0129% | 8/22 | 21.3746% |
| BTCUSD | 3.0× | O-H-L-C | 83 | 23 | 60 | 61 | 22 | 27.711% | 0.5236 | -27.3827% | 7/22 | 29.4196% |
| BTCUSD | 3.0× | O-L-H-C | 83 | 23 | 60 | 61 | 22 | 27.711% | 0.5238 | -27.3406% | 7/22 | 29.3947% |
| ETHUSD | 2.0× | O-H-L-C | 63 | 17 | 46 | 60 | 3 | 26.984% | 0.9571 | -2.4729% | 9/22 | 17.7677% |
| ETHUSD | 2.0× | O-L-H-C | 63 | 16 | 47 | 59 | 4 | 25.397% | 0.9535 | -2.6817% | 9/22 | 18.2499% |
| ETHUSD | 3.0× | O-H-L-C | 63 | 20 | 43 | 44 | 19 | 31.746% | 1.2399 | 16.9881% | 8/22 | 19.1111% |
| ETHUSD | 3.0× | O-L-H-C | 63 | 20 | 43 | 44 | 19 | 31.746% | 1.2479 | 17.4948% | 8/22 | 19.0834% |

## Reference / previous 1R TP baseline
Previous variant had a fixed 1R TP and exited losses only on Supertrend flip. THIS new variant has NO TP and a 2×/3×ATR trailing stop from entry, plus flip exit.
Previous baseline: analysis/st_firsttouch_1h_filtered_tp1r_20261122/summary.csv

## Limitations
- Volume and volatility both use only fully closed preceding 1H candle; no lookahead in filter or Supertrend flip.
- Execution tests two hypothetical within-1m paths, O-H-L-C and O-L-H-C, not true trades/ticks; order and stop fills may vary in reality.
- Trail distance uses ATR14 frozen at entry, not dynamically reset every hour; ATR stop updated at 1-minute favorable peaks in hypothetical sequence.
- Source SHA-verified Delta India BTC/ETH 1m OHLC, 22 IST months, initial $1000 1x model notional each test.
- Costs: 0.05% taker fee each side +18% GST on fees, 0.02% adverse slippage per side.
- Model excludes real spread, funding, margin/liquidation, actual order-book liquidity and latency; historical 2026 is not pristine OOS.
- Monthly returns include marked-to-market open positions; any sample-end forced close is accounting-only.

Artifacts: summary.csv, monthly_mark_to_market.csv, trades.csv.gz, quality.json, execution.log.
