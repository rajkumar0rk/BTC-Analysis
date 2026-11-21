# Breakout & Range — source-faithfulness gate, iteration 11 (2026-11-21 IST)

Status: **SOURCE AUDITED; NOT APPROVED FOR BTC HISTORICAL REPRODUCTION; NO BACKTEST EXECUTED**. This is a negative candidate result, not a performance finding.

## Immutable upstream
- Author: nefnofap; repository https://github.com/nefnofap/orb
- Source commit: b473b38f435e8468ea4f1cb2b17bd2bd64854134 (2026-06-06)
- Code: https://github.com/nefnofap/orb/blob/b473b38f435e8468ea4f1cb2b17bd2bd64854134/backtest/strategy.py
- README: https://github.com/nefnofap/orb/blob/b473b38f435e8468ea4f1cb2b17bd2bd64854134/README.md
- License: **no license established from inspected repository file listing**; do not copy/relicense upstream code.
- Original markets: NY cash-session NQ/ES/YM concept; supplied historical test is XAU 5m, not BTC/ETH. Session 09:30–09:45 America/New_York; Python uses EET/EEST broker-clock approximation. For Delta UTC data, convert NY zone using timezone database (IST is UTC+05:30); never use fixed IST clock through DST.
- Publisher's *unverified* Model A XAU 2004–2026: 3197 trades, 40.9% wins, PF 1.03, +38.9% return, 26.9% max DD. XAU 2018–2026: 1363 trades, PF 1.04, +18.1%, 26.7% max DD. Original code has commission_per_unit=0 and bar-close entry; neither result includes Delta fees/GST.
- Rules: 15m OR; distribute each OR bar's volume uniformly across high-low price bins to compute POC/70% value area; session VWAP; three-bar FVG; bullish/bearish engulfing; breakout beyond VAH/VAL with FVG retest and VWAP agreement (Model A), sweep/reclaim outside OR swing (Model B), or VWAP bounce beyond OR (Model C). Stops: OR/POC, swing, or VWAP, respectively; targets 2R/3R/2R; optional BE at 1R, EOD close; 1% equity risk per trade.
- Distinguish true exchange volume-at-price profile from **estimated OHLCV-uniform profile**: source only approximates distribution within each bar.

## Source-code correctness / reproducibility blockers
1. `run()` appends the current bar to the rolling window, computes same-bar VWAP and FVG, then `_maybe_enter(bar)` enters at **that same bar's closing price**. A Delta-reproducible adaptation must defer to next eligible 1m open, recompute quantity and risk from actual entry, and handle missing minutes.
2. `_manage(bar)` checks intrabar SL/TP and can close a position; `_maybe_enter(bar)` may then open a new position on the same bar close. The code's original 5m fills are not directly equivalent to a causal 1m replay.
3. The FVG state is overwritten when a new gap appears; no explicit guarantee that a distinct earlier breakout gap remains valid through a later retest. An alleged breakout-gap retest could be same-candle geometry; must specify signal-state lifetime and verify on completed bars.
4. The `_manage()` break-even rule changes stop when the bar reaches 1R but does not check whether the same bar subsequently touches the new BE stop. Correct ordering needs 1m replay and conservative ambiguity handling.
5. `_close()` has placeholder risk variables and reconstructs original R from TP. Reconciliation must be independent and preserve entry-time initial risk; cannot accept publisher's R ledger uncritically.
6. No Delta fees/GST/funding/slippage modeled by default. Required screen: 0.05% notional each side + 18% GST on fees, zero slippage first, funding UNMODELED.
7. Source README calls its default broker time 16:30 EET/EEST as an NY 09:30 approximation; verify actual DST transitions from timestamp-aware source before using any Delta session boundaries.
8. The author provides no reproducible Delta BTCUSD/ETHUSD performance, and PF 1.03–1.04 on XAU before Delta trading costs is not credible evidence of positive BTC after-cost expectancy.

## Novelty decision
Read `codex/AGENTS.md`, `codex/STRATEGY_NOVELTY_GATE.md`, and earlier Breakout & Range audits. Model B overlaps `research/daily-failed-breakout-20261119`; Model C overlaps generic breakout/pullback; Model A adds a distinct *approximated* value-area/FVG/engulf conjunction, but is **PARTIAL OVERLAP — NOT APPROVED** pending precise comparison with Stage24 squeeze/retest and Stage19/23. Source-faithful reproduction is also blocked by original same-close fill semantics and unlicensed source code. Do not execute this as a new purported source-faithful BTC backtest or copy code.

## Next feasible executable step
Choose a properly licensed, genuinely distinct rule with no same-bar entry assumptions; precommit a NOVELTY_CHECK.md with data hashes and fixed rules, then launch an actual Actions BTC 1m historical backtest and archive trade ledger, monthly IST NAV and costs. The previously completed BTC archive validation is run https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/44902737237 ; **this is NOT a strategy backtest**. No trading or protected branches modified.
