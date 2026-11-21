# Second EMA20 touch — 15m volume and volatility filters

Same 200/100 BTC points and ETH equivalent percent exits as previous baseline.
Data: BTCUSD/ETHUSD Delta India 1m; January 2025–October 2026 (22 IST calendar months).
Volume: last completed 15m volume >= 1.2x mean of PRECEDING 20 bars.
Volatility: last completed 15m ATR14 >= mean of PRECEDING 20 ATR14 readings.
Both checked only upon second EMA20 touch, using closed candles; no future leakage.

| Asset | Filters | Trades | TP exits | SL exits | Win % | PF | Net return % | Max DD % | Profitable months |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSD | none | 6397 | 1715 | 4682 | 26.81% | 0.09679 | -99.996% | 100.00% | 0/22 |
| BTCUSD | volume | 1916 | 479 | 1437 | 25.00% | 0.09923 | -95.894% | 95.90% | 0/22 |
| BTCUSD | volatility | 2415 | 591 | 1824 | 24.47% | 0.09484 | -98.294% | 98.30% | 0/22 |
| BTCUSD | both | 983 | 230 | 753 | 23.40% | 0.10059 | -81.730% | 81.77% | 0/22 |
| ETHUSD | none | 7409 | 1789 | 5620 | 24.15% | 0.08677 | -100.000% | 100.00% | 0/22 |
| ETHUSD | volume | 2044 | 499 | 1545 | 24.41% | 0.09022 | -96.743% | 96.75% | 0/22 |
| ETHUSD | volatility | 2549 | 610 | 1939 | 23.93% | 0.08389 | -98.676% | 98.68% | 0/22 |
| ETHUSD | both | 1006 | 236 | 770 | 23.46% | 0.09843 | -82.172% | 82.17% | 0/22 |

## Cautions
- Both filters are applied *only on second touch*, not to the initial touch.
- 0.05% taker fees per side plus 18% GST; 0.02% adverse slippage per side.
- 1x notional; a stopped position is valued with adverse stop-first 1m OHLC.
- 2026 has been examined historically and is not an untouched holdout.
- No verified actual spreads, funding, tick-by-tick touch sequencing or live fills.
- Not investment advice; negative results retained alongside positives.

Evidence: summary.csv, monthly_results.csv, trade_ledger.csv.gz, quality.json.
