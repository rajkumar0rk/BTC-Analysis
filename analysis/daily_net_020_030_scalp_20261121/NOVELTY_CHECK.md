# Pre-run change record — lowered account P&L targets (2026-11-21)

**Decision: PARTIAL OVERLAP — user-directed sensitivity extension, no new alpha claim.**

This experiment reuses the exact entry signals already backtested in
`scripts/research_daily_1pct_scalp_20261121.py` on
`research/daily-one-percent-scalp-20261121` and only changes the economically
meaningful **net account return objective** from +1% to **+0.20% or +0.30%**.
The prior original +1% account scalp study, after all modeled fees/slippage,
was unprofitable (trend -53.80%; sweep -56.21%; first-valid -69.63%).

## Frozen comparison, before reading new outcomes

- BTCUSD Delta Exchange India native 1m bars 2025-01-01 through 2026-10-31.
- 15m trend continuation (1h EMA20/50, 15m RSI 58/42, 8-bar breakout,
  volume >=1.25x trailing 20 bars, close-location >=75%) / 15m liquidity
  sweep reversal (12-bar rejection, 15m RSI 38/62, relatively flat
  1h EMA spread), and first eligible combined.
- Only one position per IST day; entry 12:00–19:00 IST, next actual 1m
  candle open after a **completed** 15m signal. Trade maximum four hours,
  flatten at IST calendar day end; 1m stop-first ambiguity.
- **2x account notional**, account initial USD 10,000, fractional
  position sizing; standard 0.05% taker each side, 18% GST on fee,
  and $5 unfavorable slippage each side. Zero maker discount.
- Test two exact NET profit targets: **+0.20%**, **+0.30%** account equity.
  Protective stop at **-0.60% NET** account equity. This protective stop
  is deliberately wider than base round-trip cost (~0.25% at 2x).
  A -0.20% or -0.30% net stop would have little/no adverse price room.
- Calculate BTC price TP/SL levels with fees and slippage; do not
  confuse price percentage with net account return.
- **Six precommitted models**: 2 targets x (trend, sweep, combined).
  Do not select thresholds on 2026 and do not hide losers or no-trade
  calendar days. No subsequent parameter retuning in this run.

## Economic distinction from prior work

`analysis/one_daily_trade_200_points/` forced one trade daily and
used 200 BTC price points. The existing
`analysis/daily_1pct_scalp_20261121/` evaluated **net +1%/-1% account**
returns with the same signals. Here the user explicitly requested a
smaller **net daily account target**, which changes TP fill thresholds,
risk asymmetry, win rates, trade holding and realized trading expenses.
This is a parameter-sensitivity extension, **not independent signal
discovery**. Existing historical 2026 has been examined; no clean OOS
claim can be made.

## Evaluation

Report trade P&L, target hits, all 669 IST days including no-trade days,
monthly returns 2025 vs Jan–Oct 2026, full compounded account return,
max trade-close drawdown, winning/losing/no-trade days and total fee/GST
and slippage dollars. Separate outcome for each frozen target and entry
family. Reject strategies that have negative net P&L; never imply
risk-free daily profit. Real bid/ask spread, funding, minimum contract
size, margin/liquidations and liquidity impact unmodeled.
