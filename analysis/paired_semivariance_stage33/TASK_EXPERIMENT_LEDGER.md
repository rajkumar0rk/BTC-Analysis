# BTC & ETH Consistent Monthly Returns Search — append-only Stage33 ledger

## 2026-11-20 05:04 IST — Stage33 execution handoff
- Stage32 closed and rejected, verified run 44622026119 and artifact 14575314681. BTC 5/22 positive, PF 0.672, -23.604% net; ETH 6/22 positive, PF 0.695, -27.607% net. No open study at iteration start.
- Focused novelty gate read from main. New causal differential: full-day downside/upside realized semivariance imbalance and reversal, distinct from prior hourly volume/impact displacement, weekend-liquidity, and breakout studies. See NOVELTY_CHECK.md; partial overlap with broad reversal family explicitly disclosed.
- Isolated branch: research/btc-first-semivariance-stage33-20261120 (forked from Stage32 branch only to reuse authenticated data utilities). No Stage32 files changed.
- Fixed source scripts/research_paired_semivariance_stage33.py commit 5c41b0b18ae80c85750181cbd4ef6ce3cbadbf5a.
- Preregistration analysis/paired_semivariance_stage33/NOVELTY_CHECK.md commit 816410cab75158479ef224f93ddb1f24f135e7af.
- Dedicated branch-scoped push workflow .github/workflows/stage33-btc-first-semivariance.yml created LAST in commit b18507ea9a7a06823e18c06fdd355bb5eae3d79e. GitHub accepted workflow creation. This should trigger a push workflow but **run ID and execution not confirmed**. The connector fetch_commit_workflow_runs for this SHA returned [] because its endpoint only filters PR-triggered runs, not branch push runs. Do not interpret [] as a failed or absent job.
- Next exact step: inspect https://github.com/rajkumar0rk/BTC-Analysis/actions/workflows/stage33-btc-first-semivariance.yml and branch research/btc-first-semivariance-stage33-20261120 for latest push run, capture ID and jobs, read logs, download stage33-original-ledgers artifact; repair same branch if failed. Validate 22 IST monthly NAV rows and original trades, after-cost PF, drawdown, cost stress, quality coverage and BTC-first split before decision. Never claim backtest completed based on accepted push alone.
- No live orders, no other schedule edits, no main changes. Not a qualifying alert.
