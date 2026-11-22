# Iteration 18 — source-faithful batch triage (2026-11-22 IST)

Status: SOURCE SCREEN ONLY; no historical trading backtest. Existing branch Actions run 44902737237 is archive integrity only. Historical archive is available to GitHub Actions; lack of local mount is not a reason to call archive unavailable.

## Source leads, pinned by exact public URL (commit hashes not yet independently verified)

1. https://github.com/sam-bateman/trading-orb/blob/main/src/orb_strategy.py — first 30m opening range; relative volume >=1.2; 10:00–14:30 ET entries; target 1.5 opening ranges; stop 0.75 opening ranges; flatten 15:45 ET. Original market equities; copyright/license and source SHA require verification. **SKIP: DUPLICATE** of opening-range and volume-filter research; no distinct boundary event. NY daylight-saving conversion must use America/New_York, never fixed UTC offset. Published BTC PF/returns/trades: unavailable.
2. https://github.com/3kpro/3K_Trading_Bot_V2 — MIT; previous N-bar Donchian high/low close break, RSI gate, 2x ATR stop, risk sizing; original crypto; published backtest explicitly omits fees/slippage and stop intrabar fills. **SKIP: DUPLICATE** of Stage17 swing Donchian and Stage24 structure breakout; no credible BTC after-cost performance. Commit SHA not pinned.
3. https://github.com/Yigit-H/atr-breakout-backtest — highest/lowest 14 bars plus ATR buffer, next bar threshold touch; source claims commissions/spread/slippage; original yfinance instrument unspecified in fetched overview. **SKIP: PARTIAL OVERLAP NOT APPROVED**: generic ATR buffered channel break duplicates Stage17/24 and its next-bar threshold-touch may conceal OHLC intrabar ordering. License and commit SHA not verified; no BTC Delta result.
4. https://github.com/PineGen-AI/liquidity-sweep-market-structure-strategy — sweep/reclaim then market-structure break, ATR exits; **SKIP: DUPLICATE** Stage24 failed auction and prior sweep/reclaim; confirm pivots only when observable, not retroactively at extreme. License/commit unverified.

## Cross-family / novelty decision

Relevant existing coverage: codex/STRATEGY_NOVELTY_GATE.md; analysis/institutional_discovery_stage17_swing_breakout/; analysis/institutional_discovery_stage24_failed_auction/; analysis/previous_day_range_swing/. Other family branches read-only. No new strategy approved, so no strategy implementation or workflow was launched. No claimed profitable months, NAV, trade count, or PF. Existing archive-integrity run: https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/44902737237.

## Next executable action

Find a materially distinct, fully licensed and source-complete boundary event; pin exact source SHA and rules; commit NOVELTY_CHECK.md with a NEW or approved differential decision; add a push-triggered workflow that runs authentic Delta BTCUSD one-minute history, next-minute entries, stop-first fills, 0.05% per-side fees plus 18% GST, account NAV and monthly IST outputs; poll run/job and inspect actual trade/monthly artifacts before reporting a backtest. No main/master or trading writes permitted.
