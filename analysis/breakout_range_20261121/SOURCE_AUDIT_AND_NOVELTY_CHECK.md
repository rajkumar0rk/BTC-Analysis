# Breakout & Range Research — source audit and novelty gate
Date: 2026-11-21 (IST)
Status: SOURCE DISCOVERY COMPLETE; NEW HISTORICAL BACKTEST NOT STARTED; NO PROFITABILITY CLAIM.
Scope: BTCUSD futures, range-boundary event entries only. This is the first independent run of this schedule.

## Repository and novelty preflight
Read `codex/AGENTS.md`, `codex/STRATEGY_NOVELTY_GATE.md`, `codex/DATA_CONVENTIONS.md`, and `codex/RESEARCH_CONTEXT.md` from main. Main reports initial archive as 5m bars 2025-12-31 to 2026-08-01 with unverified instrument/time-label semantics; other research branches contain newer 1m archives. DO NOT assume main 5m dataset is genuine Delta India 1m or covers all 22 IST months. October 2026 has known missing-minute caveat. Do not invent history.

Prior art to check before execution:
- `analysis/institutional_discovery_stage19_monthly_10pct/`, Stage23: compression/breakout/sweep, 1m stop-first.
- `analysis/institutional_discovery_stage24_structure_monthly10/` on `research/stage24-monthly10`: 15m breakout/retest/squeeze.
- `analysis/independent_stage25_hourly_trend/` on `research/stage25-new-trend`: hourly breakout/inside bar, 1m execution.
- `research/daily-compression-breakout-20261119`, `research/daily-failed-breakout-20261119`, `research/btc-eth-pf-failed-breakout-20261118`: independent breakout variants.
- `research/oi-accumulation-breakout-btcfirst-20261119-1640`: OI/volume structural breakout.
These are partial inventory from novelty gate and branch discovery; exact previous code comparison still pending.

## Public strategy source candidates (publisher claims NOT reproduced)
1. `3kpro/3K_Trading_Bot_V2` https://github.com/3kpro/3K_Trading_Bot_V2 — MIT licensed; Donchian highest/lowest of preceding 20 bars, ATR(14) 2x stop, optional RSI range, risk sizing 0.5% default, 1h Kraken SOL/USD default. Its own README admits candle-close-only fills and **no fees/slippage**. NOVELTY: SKIP, economically equivalent basic Donchian range break to prior research; not a trustworthy BTC Delta performance claim.
2. `JustACoder279/Donchian-Breakout-ATR-Risk-TradingView` https://github.com/JustACoder279/Donchian-Breakout-ATR-Risk-TradingView — published Pine v5 55-bar daily Donchian with EMA200, ATR14 versus ATR50 regime filter, 2x ATR stop, 2.5x ATR trail. Publisher reports approximately 410% for one window but no independent Delta replication. NOVELTY: SKIP generic channel/trend combination; investigate only if previously untested economic distinction is documented.
3. `MAKSAT-DEL/mtf-breakout-bot` https://github.com/MAKSAT-DEL/mtf-breakout-bot — publisher claims 209 BTC trades, 42.1% win, PF 1.46 and CAGR 7.4% over 3.2 years; 1H/4H/D1 ADX+volume trend breakout. Exact fills, costs, license, and 1m reproducibility not yet verified. NOVELTY: PARTIAL OVERLAP / BLOCKED until source and existing MTF study checked.
4. `JamesRPowell/Donchain-Breakout` https://github.com/JamesRPowell/Donchain-Breakout — educational Turtle Donchian 20-day entry/10-day exit, 5m version with 78/39 bars; explicitly acknowledges shifted prior channels and Sharpe scaling correction, but **no fees/slippage**. NOVELTY: SKIP basic channel system; useful independent lookahead test case.
5. `0xpg/crypto-breakouts` https://github.com/0xpg/crypto-breakouts — multi-horizon daily high (10/20/40/80) with next-open fills, long-only and 10 bps turnover, multi-coin portfolio. Distinct portfolio construction from single BTC range breakout; would require genuine point-in-time multi-asset universe and separate portfolio mandate, so do not misrepresent as BTC-only edge.
6. `yllvar/Donchain-Breakout` https://github.com/yllvar/Donchain-Breakout — 15m KuCoin BTC/USDT Donchian20+volume1.5x+EMA50/200, ATR stops and logistic-regression filter. Explicitly **unlicensed**, model training split/leakage risk; BLOCKED for reuse and source-faithful causal evaluation.
7. `EstebanSP23/crypto_systematic_research` https://github.com/EstebanSP23/crypto_systematic_research/blob/main/2_strategies/01_quattro_donchian/backtest.py — 4h Donchian20 with 10-bar exit, pyramiding, daily EMA200. Previously reviewed by another independent schedule. NOVELTY: SKIP duplicate research.
8. `MiltonTulli/trading-bot` https://github.com/MiltonTulli/trading-bot — BTC Donchian10 with claimed 2x volume and 1:2 RR; reported profitability and leverage not independently validated. Exact original source, license and no-lookahead fills must be audited before consideration.

## Decision
NO NEW CANDIDATE APPROVED YET. All immediately reproducible candidates overlap earlier breakout research; those claiming stronger performance require source-level verification or licensing/quality checks. Running a basic 20-bar Donchian with changed thresholds would violate the mandatory novelty gate. No new historical backtest, ledger, monthly NAV, PF or after-cost profitability can be reported.

## Next executable work
1. Read full Stage24, Stage19/23, and breakout branch code; identify a truly differential range-event mechanism, e.g. a session-anchored level with **causally known** pre-break compression plus subsequent failed-break acceptance rule, only if not already tested.
2. Locate and verify authentic Delta India BTCUSD 1m data through Oct 2026 and timestamp/coverage manifest. Resolve missing October UTC minutes and any warmup. Never substitute Binance or synthetic bars silently.
3. Commit an approved `NOVELTY_CHECK.md` with deterministic entry/exit/size/cost and data hashes BEFORE executing.
4. Implement no-lookahead 1m next-open replay, stop-first ambiguity, 0.05% per-side fee plus 18% GST and zero slippage initial screen; freeze BTC2025 selection, then BTC2026 and ETH. Funding unmodeled.
5. Use an actual completed GitHub Actions run and preserve immutable trade/monthly NAV artifacts. Do not claim a green unit test is a backtest.

No main/protected branch, live trading, other research task or VPS changed.
