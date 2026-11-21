# Second EMA20 touch 1H — one trade per Supertrend — ATR trailing exit

BTCUSD and ETHUSD Delta Exchange India original SHA-verified 1m candles, Jan 2025–Oct 2026 (22 IST months).
**No fixed TP**. Stop is ATR-only: initialized 3× ATR14, tightened by completed 1m highs/lows at last completed 1h ATR; stop never retreats.
One entry in each confirmed Supertrend direction epoch, 1H EMA20 second distinct touch. No 1H volume/volatility filter.

| Asset | Trades | Wins | Win rate | Profit factor | Net return | Max floating drawdown | Profitable months |
|---|---:|---:|---:|---:|---:|---:|---:|
| BTCUSD | 347 | 110 | 31.70% | 0.5847 | -65.621% | 66.18% | 5/22 |
| ETHUSD | 332 | 106 | 31.93% | 0.8406 | -49.444% | 66.48% | 9/22 |

## Execution model and limitations
- The ATR trailing stop includes an initial 3×ATR protective distance; it is the ONLY stop, not a separate fixed SL.
- Existing stop triggers at the unfavorable of stop or 1m open, with 0.02% adverse slippage; new highs/lows update trailing for the NEXT minute only.
- Upon entry, do not credit favorable first-minute wick for tightening. The adverse wick can trigger an exit; the 1m price path is not known.
- Full model with 1× compounding starting $1000, 0.05% taker fees on both sides + 18% GST; no funding, bid/ask depth, or actual liquidation/margin.
- Month-by-month values include floating mark-to-market equity. 2026 previously explored, so not pristine out-of-sample data.
- Source archive Jan 2025 begins UTC midnight, 5h30 IST missing. No interpolation of subsequent missing candles.

See summary.csv, monthly_mark_to_market.csv, trade_ledger.csv.gz, quality.json and preregistration.
