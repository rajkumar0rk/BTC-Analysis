# Append-only experiment ledger — Independent Big-Winner Strategy Hunt

## 2026-11-20 03:48 IST — new differential hypothesis, execution pending verification
Previous same-task variance end-loading study: GitHub Actions 44600868061, BTC -2.63% after modeled costs, PF 0.569, largest winner 5.43R; REJECTED. OI accumulation and spot lead-lag previously rejected. Do not retune those.

New hypothesis: volume absorption despite limited hourly displacement with close-location directional confirmation. Novelty check: PARTIAL OVERLAP, distinguishing turnover-to-displacement from ordinary high-volume breakout; preregistration in NOVELTY_CHECK.md. Immutable initial rule configuration is in scripts/research_independent_volume_absorption_20261120.py, commit 5c975a60251e56df1364db3b137356e26faa3fc4. Branch workflow created at commit 6dbbf7ef4e9df47f7e0037dc4a8a5bd18787d81e.

Workflow: https://github.com/rajkumar0rk/BTC-Analysis/actions/workflows/independent-volume-absorption-20261120.yml . A commit-scoped connector check returned zero runs, but the connector filters to PR-triggered runs and CANNOT establish absence of push runs. Thus execution is **NOT VERIFIED**, no results exist to audit yet. Next iteration: verify actual push run via GitHub Actions UI/API; if no run, diagnose workflow recognition and trigger on isolated branch; if failed, inspect job logs and repair same study. Do not start a different hypothesis before verified outcome. Artifact expected: volume-absorption-btc-eth-evidence.

Required audit if completed: exact 2025 and 2026 BTC segments and monthly IST NAV, trade-level R, top-winner removal, risk/fees/GST/slippage sensitivity, 2026 October coverage, missing-minute forced exits, historical funding unavailable, ETH unchanged secondary. Funding and L2 execution remain unmodeled, so no result can be declared fully validated without caveats.

No main, other schedule branch, or live trading changes.
