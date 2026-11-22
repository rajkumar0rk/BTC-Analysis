# UNFILTERED 1H EMA20 first touch: NO TP, 2× / 3×ATR14 trailing + Supertrend flip exit

**CORRECTED USER REQUIREMENT:** the volume and volatility ENTRY filters were only requested for the 15M strategy, NOT this 1H strategy. Both are now DISABLED.
BTCUSD and ETHUSD, 1H indicators and 1m monitoring, Jan2025-Oct2026 (22 complete IST months).
Entry: confirmed ST(ATR10, multiplier3) flip, ignore flip candle, FIRST subsequent EMA20 touch, max one trade per ST epoch. No volume or volatility gate at entry.
No fixed TP. Freeze 1H Wilder ATR14 from last CLOSED hour at entry. Initial protective stop entry±(2 or 3)*ATR14 and trail at fixed distance from favorable 1m extreme; never retreat.
Confirmed opposing 1H ST flip exits at next hourly open when earlier than ATR-stop. Touching ST line alone does NOT close trade.
ATR14 is used to size the trailing stop, not to exclude entries. No extra ST-line geometry check when TP is absent.

| Asset | ATR multiple | Hypothetical path | Trades | Winners | Losers | ATR stop exits | ST flip exits | Win% | Profit factor | Net return | Profitable months | Max floating DD |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSD | 2.0× | O-H-L-C | 396 | 115 | 281 | 381 | 14 | 29.04% | 0.6317 | -56.2917% | 6/22 | 57.5764% |
| BTCUSD | 2.0× | O-L-H-C | 396 | 116 | 280 | 381 | 14 | 29.293% | 0.6483 | -53.9552% | 7/22 | 55.6242% |
| BTCUSD | 3.0× | O-H-L-C | 396 | 121 | 275 | 306 | 89 | 30.556% | 0.6307 | -65.3714% | 5/22 | 66.2348% |
| BTCUSD | 3.0× | O-L-H-C | 396 | 121 | 275 | 309 | 86 | 30.556% | 0.6308 | -65.286% | 5/22 | 66.1724% |
| ETHUSD | 2.0× | O-H-L-C | 382 | 117 | 265 | 368 | 13 | 30.628% | 0.658 | -66.7599% | 5/22 | 70.8283% |
| ETHUSD | 2.0× | O-L-H-C | 382 | 116 | 266 | 367 | 14 | 30.366% | 0.6567 | -66.6926% | 6/22 | 70.2907% |
| ETHUSD | 3.0× | O-H-L-C | 382 | 123 | 259 | 290 | 91 | 32.199% | 0.808 | -55.2761% | 8/22 | 66.2483% |
| ETHUSD | 3.0× | O-L-H-C | 382 | 123 | 259 | 292 | 89 | 32.199% | 0.7816 | -60.1551% | 7/22 | 69.58% |

## Prior mistakenly filtered 1H comparison
Compare separately with analysis/st_firsttouch_1h_filtered_atrtrail2x3_20261122/summary.csv. That run was NOT the user's intended unfiltered 1H strategy.
This run disables both entry filters and removes the obsolete ST-line risk geometry gate (irrelevant because no TP).

## Caveats
- 1-minute candle O-H-L-C vs O-L-H-C paths are hypothetical. No true intraminute trades/ticks, execution fills or defensible worst/best bounds.
- ATR14 stop distance frozen at entry from last completed 1H bar, moved with favorable 1-minute prices. This variant does NOT recompute ATR multiplier hourly.
- Original Delta India BTCUSD ETHUSD 1-minute data SHA256-verified, 22 completed IST months, sample initial $1000 per asset, 1x changing equity notional.
- 0.05% taker each side + GST18% on fees, adverse 0.02% slippage each side.
- No actual spread, funding, margin, liquidation, order-book depth or execution latency. Research-exposed history not pristine OOS.
- Monthly equity MTM includes open positions; sample-end close only accounting.

Artifacts: summary.csv, monthly_mark_to_market.csv, trades.csv.gz, quality.json, execution.log.
