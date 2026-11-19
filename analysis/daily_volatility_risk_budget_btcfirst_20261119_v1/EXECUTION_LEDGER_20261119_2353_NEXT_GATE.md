# 2026-11-19 23:53 IST — post-rejection novelty and execution gate

Previous study closed REJECTED; immutable source 625c3d1f5cde8a2b0c3d9b749e61031e87b72234, run https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/44558873365, decision 2b2dfbe4cc576f40e4e8bd101b10b922cf453707. No changes to rejected code or original artifacts.

Read codex/STRATEGY_NOVELTY_GATE.md (main, blob 87215853264cfbfd928421152e752ce106a685a7) and inspected existing daily research branches. Existing work already covers jump-aftershock, wick scalping, volume pressure, OI, funding-boundary drift, realized skew, volatility shock, BTC/ETH lead-lag, efficiency regimes and maker feasibility. These cannot be recycled by renaming thresholds.

Execution gate: the only verified successful historical run available from this task is 44558873365, and its negative BTC-first outcome is conclusive enough to reject the original hypothesis. No new causal mechanism has passed novelty + executable-data feasibility in this check; therefore no new backtest or return is claimed. A distinct candidate requires a genuine additional observable mechanism, not a cosmetic OHLCV rule. Historical bid/ask, settled funding or cross-venue spot/perpetual synchronized timestamps are not yet verified as available in the repo. Before using such a mechanism, verify data source and retention; otherwise mark INCONCLUSIVE and choose a testable distinct hypothesis.

No main/other task branches, automations, credentials, or live orders touched. Next run: inspect actual dataset inventory and select one economically distinct, observable hypothesis; commit preregistration + executable workflow and verify a run ID in the same iteration. Do not use 2026 or ETH to tune.
