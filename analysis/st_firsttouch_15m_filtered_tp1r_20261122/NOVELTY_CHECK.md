# Preregistered 15M first-touch EMA20: TP=1R, volume/volatility filters, Supertrend flip-only loss exit

Request 2026-11-22: "backtest with 1R". Closest prior and control: `analysis/st_firsttouch_15m_vol12_atr14_filter_20261122/` from `research/st-firsttouch-15m-vol12-atr14-filter-20261122` (TP=2R). **The only changed trading parameter is TP multiplier 2 -> 1.**

- Asset/timeframe: BTCUSD and ETHUSD futures, independent 15-minute indicators with 1-minute execution/replay.
- Entry: *first* EMA20 touch AFTER confirmed Supertrend(ATR10, factor3) bullish/bearish flip, skipping flip candle; one trade per Supertrend regime. Touch detection and filters operate on last completed 15M bar (no lookahead). Rejected first touch is final for that regime, don't enter on second touch.
- Filters: **volume of last completed 15M > 1.2 × SMA20(volume)**; **Wilder ATR14 of last completed 15M > SMA20(ATR14)**, also last completed; both required.
- Freeze reference R = `direction * (executed EMA20-touch entry - last completed 15M Supertrend line)` and require R>0. LONG TP = entry+**1R**, SHORT TP = entry−**1R**.
- **Stop-loss remains confirmed opposite Supertrend flip**, not the ST line, and not a fixed 1R stop. Exit at next 15M candle open once flip is confirmed. No fixed hard stop, no profit lock, no trailing.
- Each instrument $1,000 initial model equity, 1x current-account notional sizing; taker 0.05% each side, GST 18% on fees, 0.02% adverse slippage each side. Full Jan 2025–Oct 2026 (22 complete IST months), 1m Delta India OHLC with source hashes/coverage verification.
- Run **O-H-L-C and O-L-H-C** hypothetical intraminute execution assumptions to check ambiguous entry/TP ordering; neither is proven actual tick path.
- Report wins, losses, exit reasons, PF, after-cost returns, monthly mark-to-market, floating drawdown and whether simulated equity falls below zero, comparing directly to 2R. No funding/margin/liquidation/real spread/depth/latency; historical 2026 not pristine out of sample.

Novelty status: **PARTIAL OVERLAP** with user-requested unique 1R exit condition; retain untouched baseline branch.
