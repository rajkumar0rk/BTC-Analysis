# Novelty preflight — requested screenshot reproduction (2026-11-19)

**Decision: PARTIAL OVERLAP — approved differential (exact user configuration replication)**

## Deterministic hypothesis and setting
- Delta India BTCUSD perpetual, 1 contract = 0.001 BTC, no pyramiding.
- Entry 15m and historical stop monitoring 15m (no 1m stop fills despite availability of 1m source).
- Supertrend ATR10 factor3 established bullish/bearish (not initial flip); EMA20 candle wick touch + close across EMA20.
- Pine Supertrend candle-shape and wick-only toggles are ON but **do not apply** when Entry Pullback Mode is **EMA20**.
- Entry filters both: current 15m ATR14 >= previous 20 ATR14 mean (min volatility multiplier 1.0) AND current 15m volume >= previous 20 volume mean * 1.5. Maximum filters disabled.
- Initial SL: auto ATR14 x2 from entry on EMA20 mode, tick=0.5.
- Fixed-point native trailing: master ON, fixed distance ON, activate at +150 favorable BTC price points, offset 50; additional trailing stop points OFF; ATR and Supertrend trailing modes not selected.
- Confirmed 15m opposite Supertrend flip closes open position. Signal close fill; a position at a time.
- Fee assumptions (user screenshots, not independently verified live offer entitlement): 0.05% taker entry, 0.05% taker exit waived for offers deemed eligible, 18% GST on nonwaived trading fees, no funding (0% assumption), no slippage (not shown), voucher *not* cash.
- Scalper qualifying window set to 100000 minutes in screenshot, offer assumed active for ALL history. This is a **model input**, not a claim that the exchange actually honors such a window.

## Most similar existing experiments
1. `scripts/research_trend_pullback_breakout_stage13.py` — 4H/1H/15m multi-timeframe trend + pullback + breakout, unlike same-candle EMA touch entry with active established Supertrend and ATR/volume conjunctive gates.
2. `scripts/research_monthly_10pct_stage19.py` — 5m EMA pullback variants; different 15m signal construction, Supertrend flip exits and native 150/50 trailing.
3. `scripts/research_anytime_volume_volatility_patterns.py` — high-volume/volatility entry studies; does not reproduce this specific already-configured TradingView system or its broker emulator.

This run tests *reproduction of the user's supplied rules*, not a novel strategy discovery or an independent holdout. All historical months have already been research-exposed. Do not tune on month-level results and claim out-of-sample robustness.

## Dataset integrity
`data/delta_india/BTCUSD/1m/manifest.json` says every partition from 2025-01 to 2026-11-18 UTC has missing_minutes=0. The script checks every gzip SHA256 and continuity before backtesting. The older novelty document's October missing-data warning is superseded by the latest committed manifest and will be rejected if validation fails.

## Reporting
Evaluate both full available history and last 10000 15m bars (Pine `calc_bars_count=10000`). Include per-exit-month IST trade counts, gross/net points, USD P&L per 0.001 BTC contract, net PF, drawdown, explicit date coverage, cost assumptions, exclusions, and source ledger. Treat 2026-11 as incomplete.

## Exactness limitations
Pasted Pine source predates the screenshot's optional min/max UI but max filters are OFF, so filtering is economically equivalent. It also defaults to a 5m stop TF, overridden by the screenshot to 15m. No TradingView Property-tab screenshot, symbol mapping, bar magnifier preference, live spread, or real historical fee waiver audit is provided; assumed strategy defaults and 4-tick historical path are documented. Backtester is a *broker-emulator approximation*, not an audited parity claim.
