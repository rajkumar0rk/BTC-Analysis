# Breakout & Range — iteration 12, 2026-11-21 IST — independent ORB+FVG candidate triage

**State: source triage only; no source-faithful historical BTC backtest launched or completed.** This is a negative/inconclusive research record, not a performance result.

## Recovery and execution status
- Recovered the isolated research branch `research/breakout-range-source-audit-20261121` and earlier source audit `ITERATION_11_NEFNOFAP_SOURCE_GATE.md`.
- Verified branch Actions list: only two archive-integrity workflow runs, most recent completed successfully at https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/44902737237. There is no pending/failed *strategy* run to repair. Archive validation is not a trading backtest.
- Read `codex/AGENTS.md` and `codex/STRATEGY_NOVELTY_GATE.md` before considering a new experiment.

## New published candidate and evidence
- Creator Bpmiller32, source https://github.com/Bpmiller32/SignalFlow, immutable observed latest source commit `48f999e98d450fab62495de9b3a148ec858e86f0` (verify exact source file hashes before reproduction).
- GitHub repository reports **no detected license**. Do not copy its code into BTC-Analysis without permission.
- Original mechanism described by publisher: 5-minute equity cash-session opening range; wait for a volume-confirmed range breakout (volume at least 1.2x opening-range average), then require a three-candle fair-value gap in breakout direction and additional candle/body/range/close filters. Position management includes partial exit at 1R and ATR trailing. Other restrictions include overnight gap and earnings filters that are equity-specific and cannot be translated to 24/7 BTC without changing the original strategy.
- Publisher's full deterministic filter thresholds, original market/timeframe settings, fill semantics, historical trade count, PF, return, drawdown and costs have **not** been recovered and verified from immutable executable code. **NOT REPRODUCIBLE yet**. No publisher gains are represented as local results.
- Potential novelty is a *post-breakout FVG creation confirmation* rather than a *FVG retest*; however Stage24 structure/retest and the earlier nefnofap FVG source must be compared at exact rule level. Current verdict **PARTIAL OVERLAP — NOT APPROVED**.

## Additional search negative control
- https://github.com/saurav-1980/ORB-strategy- presents illustrative (not observed) performance figures in its README; generic ORB volume confirmation is duplicate of previous studies, so **SKIP**.
- https://github.com/sam-bateman/trading-orb presents US equities volume-confirmed ORB and a claimed 10-year evaluation, but it is not a reproduced Delta BTC result and the core signal is previously studied; **SKIP**.
- https://github.com/pderer/orb_strategy uses cross-sectional US-stock relative volume selection, not directly reproducible on one BTC instrument; **NOT directly transferable**.

## Exact blocker / next executable remedy
Need a source with (1) immutable complete entry/exit/sizing rules, (2) a materially new causal boundary-event mechanism, (3) an approved `NOVELTY_CHECK.md` against Stage24 and other branch implementations, and (4) a runner on the verified Delta 1m archive. Once those are satisfied, commit source-faithful code and run a GitHub Actions backtest using next 1m open, zero assumed slippage, 0.05% notional fees each side plus 18% GST, mark-to-market NAV and full monthly IST ledger. Funding remains UNMODELED. Do not claim 22/22 profitability.

No protected branches, other schedules, VPS or trading were changed.
