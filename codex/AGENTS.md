# Codex research guidelines

- Treat all findings as hypotheses, never live trading advice.
- Start with the original 5-minute data and validate derived bars and timestamp semantics.
- Use America/New_York with daylight-saving transitions for session analysis.
- Scan observed candle sequences and weekday/clock effects rather than only predefined indicators.
- Separate discovery/training from chronological holdout data.
- Correct for multiple testing, account for overlapping windows and report counts and effect sizes.
- Model bid/ask slippage, fees, funding and realistic stops before calling a setup profitable.
- Save reproducible scripts, raw output and negative findings in the analysis folders.

- **Mandatory before any strategy test:** read `codex/STRATEGY_NOVELTY_GATE.md`, compare proposed rules against all completed reports/scripts (including research branches), record a novelty decision, and skip duplicate/equivalent configurations. Do not run a backtest just because the name or parameter values changed.
