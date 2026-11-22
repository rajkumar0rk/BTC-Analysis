# First touch EMA20 + Supertrend flip stop + fixed 2R TP

BTCUSD/ETHUSD, independent 1H and 15M tests, full 22 completed IST months Jan 2025–Oct 2026.
True Supertrend Wilder ATR **10** factor **3**, EMA20; previous fully CLOSED signal timeframe features.
First touch after flip (flip candle excluded). No Supertrend line-touch stop. Exit after opposite ST flip confirmation at next HTF open or TP=2×abs(entry - ST line fixed at entry).
No separate hard stop or profit lock. One trade per Supertrend regime. 1m execution with both path assumptions; historical ticks unavailable.

| Asset | TF | Hypothetical 1m path | Trades | Net wins | Net losses | TP2R exits | ST flip exits | Win% | PF | Net% | Positive months | Max floating DD |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSD | 15m | O-H-L-C | 1554 | 550 | 1004 | 522 | 1031 | 35.393% | 0.6163 | -93.5378% | 1/22 | 93.7421% |
| BTCUSD | 15m | O-L-H-C | 1554 | 549 | 1005 | 522 | 1031 | 35.328% | 0.6162 | -93.5441% | 1/22 | 93.7552% |
| BTCUSD | 60m | O-H-L-C | 396 | 152 | 244 | 143 | 252 | 38.384% | 0.6809 | -64.3553% | 9/22 | 66.4537% |
| BTCUSD | 60m | O-L-H-C | 396 | 152 | 244 | 144 | 251 | 38.384% | 0.6826 | -64.0476% | 9/22 | 66.164% |
| ETHUSD | 15m | O-H-L-C | 1422 | 523 | 899 | 499 | 922 | 36.779% | 0.7367 | -92.6031% | 2/22 | 93.0282% |
| ETHUSD | 15m | O-L-H-C | 1422 | 522 | 900 | 498 | 923 | 36.709% | 0.7362 | -92.7268% | 2/22 | 93.1447% |
| ETHUSD | 60m | O-H-L-C | 381 | 138 | 243 | 134 | 246 | 36.22% | 0.7333 | -72.8303% | 8/22 | 79.9016% |
| ETHUSD | 60m | O-L-H-C | 381 | 138 | 243 | 134 | 246 | 36.22% | 0.7333 | -72.8303% | 8/22 | 79.9016% |

## Assumptions and caveats
- Delta India 1m candles checked against archive SHA256, no missing 1m records in selected period.
- Synthetic O-H-L-C and O-L-H-C within-minute continuous paths are sensitivity hypotheses, not actual trades. No guarantee target or exact touch order inside 1m candle.
- TP 2R is based on reference ST line at entry; because ST flips are stop triggers, actual monetary loss can differ materially from R and reward/risk is **not guaranteed 1:2**.
- Charge adverse slippage 0.02% and taker fee 0.05% each direction plus GST 18% on fees.
- $1000 initial per symbol per TF, 1x evolving notional; no actual spread, market depth, funding, exchange liquidation, margin, latency or partial fills.
- September and other months measured using mark-to-market including OPEN positions. Historical 2026 has already been researched; not untouched out-of-sample.
- End-of-sample closure is accounting only, not user-defined exit.
- Some older research used ATR14 despite labeling ST10x3; THIS backtest uses ATR10 explicitly.

Artifacts: summary.csv, monthly_mark_to_market.csv, trades.csv.gz, quality.json.
