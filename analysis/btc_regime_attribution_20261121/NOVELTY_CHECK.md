# Novelty gate — 1H regime map and conditional strategy attribution (2026-11-21)

## Decision: PARTIAL OVERLAP — approved differential

This is NOT a search for new strategy rules. The incremental research question is: across complete 1H BTCUSD candles, how often is each mutually exclusive market regime present, and how do four predeclared, fixed baseline trade rules perform conditional on the causally known regime at signal close? No parameter optimization is permitted. Report all outcomes, including negative results.

## Closest prior work reviewed
- scripts/analyze_institutional_regimes.py and analysis/institutional_regime_research/RESEARCH_REPORT.md: 5M OI/mark/funding positioning proxies and 21 setups; not an hourly exhaustive mutually exclusive market-state map.
- scripts/research_monthly_regime_stage14.py and analysis/institutional_discovery_stage14_monthly_regimes/RESEARCH_REPORT.md: regime-filtered structure signals; 0/428 passed; not 1H time-in-state distributions and conditional attribution of a fixed strategy panel.
- research/stage24-monthly10: scripts/research_structure_monthly10_stage24.py and analysis/institutional_discovery_stage24_structure_monthly10/RESEARCH_REPORT.md: 15M break/reversal with 1M exit.
- research/stage25-new-trend: scripts/research_independent_hourly_trend_stage25.py and analysis/independent_stage25_hourly_trend/RESEARCH_REPORT.md: 1H momentum/trend with 1M exit; 0/2880 meeting all-month objective.
- analysis/institutional_discovery_stage20_three_sleeve/RESEARCH_REPORT.md: multi-sleeve combination; not an exhaustive per-hour regime mapping.

## Fixed deterministic study design
Instrument: Delta Exchange India BTCUSD perpetual OHLCV; 1M stored 2025-01-01 UTC through 2026-11-20 23:59 UTC. Build aligned, complete 1H bars, require 60 original 1M bars each. Validate sha256, count and timestamps against latest native 1M manifest before calculating results. Separate 22 complete months Jan 2025-Oct 2026; partial Nov 2026 excluded from monthly performance claims.

For each completed hour compute only then-known rolling ATR14, EMA20/50, ADX14, signed DMI, 12H efficiency ratio, prior 24H high/low, and ATR ratio versus *prior* 72H median. Assign exactly one primary hourly regime with documented deterministic priority: shock, upside/downside breakout, uptrend/downtrend, compression, range, mixed. Overlapping event flags identify false-break, trend pullback, reversal and wick rejection. These are price proxies, not proof of liquidation or institutional identity.

Four frozen comparison baselines, deliberately overlapping earlier entry families but used here only for conditional attribution:
1. EMA20/EMA50 trend pullback + 1H touch/reclaim; stop 1.6 x ATR14, target 3R, max 24h.
2. Prior 24H high/low closing breakout; stop 1.8 x ATR14, target 3R, max 36h.
3. Bollinger 20 / 2 deviation excursion and return inside band; stop 1.2 x ATR14, target 1.5R, max 12h.
4. Failed prior 24H high/low sweep closed back inside; stop 1.3 x ATR14, target 2R, max 12h.
All entries first 1M OPEN after fully closed 1H bar. Stop-vs-target same-minute ambiguity resolves to stop. Stop gaps fill at worse open. Per strategy only one open position. Month-boundary flattening in IST. Hypothetical equity $10,000 per model, 0.5% risk each trade with leverage notional capped at 3x. Taker fee 0.05% per side plus 18% GST, 5 USD adverse slippage per leg. Missing L2 spreads, realized funding and liquidation make returns conditional simulations, not investable guarantees.

Publish exhaustive class frequencies, monthly shares, monthly complete-month account results (including idle), per-class expectancy and counts, trade ledger, validation diagnostics. Compare 2025 and 2026, but 2026 has already been researched and is NOT blind out-of-sample. Classifier parameters and baseline strategies are not tuned against either period.

## Why the overlap is allowed here
Entry/exit logic is intentionally fixed and similar to older studies. The **novel economic measurement** is per-hour regime occupancy and per-regime conditional profit/loss for multiple separately replayed unoptimized baselines on the now repaired continuous native 1M archive, not a claim that the strategy patterns are new. This is a differential diagnostic, not an additional optimized candidate search.

## Historical integrity caveat
An earlier Stage24/25 research archive reported a missing 2026-10-31 UTC. The current 2026-11-21 1M manifest reports all 1,440 candles for that date and zero missing across the archive. This run must independently verify the *actual* data, abort on any discrepancy, and never silently interpolate.

## Threshold
No model is declared live-ready absent spread, funding, queue/market-impact, position sizing and true liquidation simulation, and later prospective forward testing.