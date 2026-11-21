# MR-001 novelty decision — 2026-11-21

Decision: **SKIP** this source as a *new* strategy-family experiment; preserve its source audit, do not claim an independent profitable result.

## Exact proposed source
Gert Wohlgemuth / Freqtrade strategies BbandRsi:
https://github.com/freqtrade/freqtrade-strategies/blob/main/user_data/strategies/berlinguyinca/BbandRsi.py

Original long-only 1h strategy: RSI(14) < 30 AND close below lower BB(20,2) computed on typical price; RSI > 70 exit, 10% minimal ROI and -25% fixed stop. Spot strategy, not originally Delta perpetual futures. These are historical rules, not our results.

## Nearest previous mechanisms
- `scripts/research_wide_monthly_stage23.py`: explicitly reuses Stage19 5m mean-reversion/fade, sweep and RSI2 families, and Stage20 inversions; monthly portfolio fitting is not evidence of a new BB edge.
- `codex/STRATEGY_NOVELTY_GATE.md`: parameter changes or combinations with the same core causal signal are not new; requires a demonstrated economic differential before execution.
- Prior KeltnerBounceV1 and Strategy002 cited in `analysis/mean_reversion_research/EXPERIMENT_LEDGER.md`. The original source implementations have not been independently inspected to demonstrate an incremental mechanism.

## Economic novelty assessment
BB(20,2) plus oversold RSI14 is a standard volatility-envelope + oscillator fade. The causal thesis (buy downside price stretch expecting mean reversion) overlaps previous envelope/RSI fades; different thresholds and a wide 25% stop do not create an independent source mechanism. Without a defensible distinct hypothesis, executing this as a NEW research strategy would violate the novelty gate. It may still be used as a documented reference or benchmark in a specifically approved replication study.

## Next distinct candidate gate
Search for source-faithful **anchored VWAP residual z-score reversion with volatility-state filtering**, only if true BTC 1m volume is trustworthy and the anchor is knowable at trade time. Require a public exact executable rule set, a precommitted finite-risk exit, and a causal distinction from Stage19/20 before running. If no reproducible source exists, record NOT REPRODUCIBLE and seek another candidate. Never invent rules or pretend this is already backtested.

## Data and evaluation constraints
The manifest in `data/delta_india/BTCUSD/1m/manifest.json` reports a later October 2026 repair, whereas the novelty gate references an earlier incomplete snapshot. Verify actual compressed partition hashes, UTC timestamp semantics and IST month boundaries in the workflow. Initial screen: zero slippage, 0.05% taker fee per side + 18% GST, no funding data, next-1m-open entries and stop-first conservative execution. Monthly NAV results require actual trades and artifacts, not published publisher metrics.

**Outcome: No backtest launched, no PF or return calculated. This SKIP resolves the pending MR-001 novelty decision, rather than silently carrying it forward.**
