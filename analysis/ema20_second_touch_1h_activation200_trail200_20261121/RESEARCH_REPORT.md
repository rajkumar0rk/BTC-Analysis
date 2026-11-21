# 1H EMA20 second touch — activate +200, trailing distance 200

BTCUSD/ETHUSD 22 IST months Jan 2025–Oct 2026, original 1m Delta India data. 1H EMA20 second distinct touch, Supertrend(10,3), one trade per trend epoch.
**No fixed TP. No fixed SL before trailing activation.** Trailing begins only once favorable price reaches +200 BTC points (ETH percent equivalent), then follows best price at 200 BTC-point distance.
Activation-minute ambiguity: if same 1m candle crosses favorable activation and newly computed stop, pessimistically assume immediate trailing exit. Already-active stops are checked before updates and tightened levels activate the next 1m.

| Asset | Trades | Trail exits | Activation-minute exits | Sample-end forced | Win rate | PF | Net return | Max floating DD | Profitable months |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSD | 113 | 112 | 41 | 1 | 56.64% | 1.1578 | 1.917% | 58.075% | 11/22 |
| ETHUSD | 164 | 164 | 67 | 0 | 50.00% | 3.1924 | 14.948% | 104.641% | 16/22 |

## Limitations and interpretation
- +200 is activation threshold, not a TP; there is NO fixed take profit.
- Before +200, exposure is unprotected by any stop; severely adverse trends and liquidation are not modeled.
- Once activated, the trailing stop starts about entry (gross breakeven before costs) when exactly +200, then moves with favorable prices. Never retreats.
- Ambiguous OHLC ordering on the activation minute uses a pessimistic activation-then-retrace stop-fill. Actual tick replay would be needed for live parity.
- 1x model equity sizing, taker fee 0.05% each side plus 18% GST, 0.02% adverse slippage each side.
- Funding, exact bid/ask spread, latency, exchange liquidation, tick sequence and real margin use not modeled.
- Sample-end forced close for reporting is not a live exit rule. Results in tested 2026 sample are not pristine OOS.

Results: summary.csv, trade_ledger.csv.gz, monthly_mark_to_market.csv, quality.json.
