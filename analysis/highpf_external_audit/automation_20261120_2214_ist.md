# High-PF independent research check — 2026-11-20 22:14 IST

Scope: THIS schedule only. No backtest claimed, no live execution.

## Checked
- Connected GitHub branch search found `research/highpf-external-source-audit-20261120`.
- Read `codex/STRATEGY_NOVELTY_GATE.md` from this branch; existing research covers trend pullbacks and multiple other families. Do not treat Turtle as novel without comparing the detailed rules and previous work.
- GitHub connector exposes job/artifact retrieval by known run ID but does not expose repository-wide workflow run listing; public GitHub Actions API URL could not be accessed via web tool. Consequently the newest workflow run, its jobs, and any open study could NOT be reliably established in this iteration. Do not start a competing backtest before resolving this priority.
- Public external search query: `github aurelien-gentile turtle-strategy-backtest strategy rules`.
- Source https://github.com/aurelien-gentile/turtle-strategy-backtest : hourly BTC long-only Donchian breakout, opposite-channel exit, 2 ATR stop, 1% capital risk unit, optional pyramiding. Author aurelien-gentile; source reports 343 configurations underperform buy-and-hold mid-2023 to early-2024. License, exact commit SHA, and code execution parity NOT YET VERIFIED. This is a discovery lead, NOT an accepted or backtested candidate. No installation scripts executed.
- Source https://github.com/pplonski/turtle-trading-python : historical BTCUSDT Turtle code; must inspect license/commit and novelty before selecting. Neither public performance nor third-party screenshots establish an edge.

## Next required action
1. Retrieve the latest actual GitHub Actions run/status for this schedule branch via a connector/API action that supports listing runs (or known run ID from existing ledger), then audit artifacts and settle any pending study.
2. Read isolated source ledger and identify whether Turtle/Donchian was already tested; reject duplicate mechanisms.
3. Only if no pending study, select a genuinely novel externally sourced strategy and run a native BTC 2025 ZERO-slippage screen with 0.05% taker fee each side and 18% GST on fees. Do not claim a screen result without raw trades and actual Actions completion.
4. Only after positive screening, freeze settings and run adverse BTC 0.5 and 5 USD points/fill side; funding UNMODELED when historical records missing. BTC 2026 and ETH only after BTC2025 selection lock.

Outcome: INCONCLUSIVE — workflow status and native backtest evidence unavailable in this check. No profit claim. No changes to main, other research branches, other schedules or exchange accounts.
