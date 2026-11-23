# 15M Supertrend EMA20 FIRST TOUCH — entry filters ON, NO TP, 2× / 3×ATR14 trailing stop

**Fixed take-profit OFF** per user correction. Both 15M ENTRY filters remain ON: volume >1.2×SMA20(volume); ATR14 >SMA20(ATR14), using previous completed 15M candle only.
BTCUSD and ETHUSD independent simulations with 15M signal candles and 1m execution, 22 complete IST months Jan2025–Oct2026.
LONG: confirmed ST(10,3) flips green; ignore flip candle; first subsequent 15M candle that touches preceding closed EMA20 enters long, if both previous-completed-candle filters pass. SHORT reversed.
At first touch reject entire ST cycle if either filter fails; one trade per ST regime.
NO FIXED TAKE PROFIT. Freeze trailing distance at entry = (2× or 3×) Wilder ATR14 of the preceding fully completed 15M candle. Initial stop immediately entry∓distance; ratchet on favorable 1m price extremes only, never backward.
Whichever comes first exits: 1m ATR trailing stop hit, or confirmed opposite 15M ST flip at next 15M candle open. Touching Supertrend LINE does NOT exit, but ATR trail may exit before flip.
Supertrend line is logged only as diagnostic; no entry-to-ST-line R geometry gate is imposed because R-based TP is OFF.

| Asset | Trail | Hypothetical 1m path | Trades | Wins | Losses | ATR trail exits | ST flip exits | Win% | PF | Net return | Profitable months | Max floating drawdown |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSD | 2.0× | O-H-L-C | 323 | 81 | 242 | 302 | 21 | 25.077% | 0.5432 | -40.2633% | 4/22 | 41.0705% |
| BTCUSD | 2.0× | O-L-H-C | 323 | 81 | 242 | 302 | 21 | 25.077% | 0.5129 | -42.6921% | 2/22 | 43.4665% |
| BTCUSD | 3.0× | O-H-L-C | 323 | 86 | 237 | 244 | 79 | 26.625% | 0.641 | -39.0757% | 7/22 | 40.4494% |
| BTCUSD | 3.0× | O-L-H-C | 323 | 87 | 236 | 240 | 83 | 26.935% | 0.6808 | -35.5966% | 6/22 | 37.0487% |
| ETHUSD | 2.0× | O-H-L-C | 270 | 82 | 188 | 252 | 18 | 30.37% | 0.7399 | -28.683% | 7/22 | 35.2957% |
| ETHUSD | 2.0× | O-L-H-C | 270 | 83 | 187 | 253 | 17 | 30.741% | 0.917 | -10.3175% | 7/22 | 23.2678% |
| ETHUSD | 3.0× | O-H-L-C | 270 | 91 | 179 | 200 | 69 | 33.704% | 0.9178 | -12.8489% | 10/22 | 29.4487% |
| ETHUSD | 3.0× | O-L-H-C | 270 | 92 | 178 | 202 | 67 | 34.074% | 0.9693 | -4.9977% | 11/22 | 26.023% |

## Direct comparisons to earlier 15M versions
- Previous 15M 1R and 2R variants had FIXED TAKE PROFIT, NO ATR trailing stop. Those are separate controls. Their entry filters remain ON in this run.
- Prior 1R: analysis/st_firsttouch_15m_filtered_tp1r_20261122/summary.csv
- Prior 2R: analysis/st_firsttouch_15m_vol12_atr14_filter_20261122/summary.csv
- Another earlier branch combined 1R/2R TP plus ATR trailing; it does NOT implement the final user requirement and must not be confused with this study.

## Model caveats
- SHA256-verified 1m historical Delta India OHLC Jan2025–Oct2026 for BTC/ETH, 22 IST months. No missing minutes.
- 1m O-H-L-C vs O-L-H-C paths are hypothetical price order, not tick/realtime stop fills or mathematical min/max bounds.
- Frozen prior 15M ATR14 at entry; 1-minute intrabar stop monitoring and ratcheting; no subsequent remeasurement of distance.
- Taker fee 0.05% each side + GST18% on fees, 0.02% adverse slippage both sides; initial equity $1000, dynamic 1× notional.
- No exchange funding, actual order book/spread, margin, liquidation, slippage tail risks, partial fills or latency. 2026 history already researched; not untouched out of sample.
- Monthly mark-to-market includes open positions; forced sample-end close for accounting only.

Artifacts: summary.csv, monthly_mark_to_market.csv, trades.csv.gz, quality.json, execution.log.
