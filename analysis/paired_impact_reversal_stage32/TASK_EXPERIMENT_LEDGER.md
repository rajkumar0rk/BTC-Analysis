# Task-specific append-only experiment ledger — BTC & ETH Consistent Monthly Returns Search

## 2026-11-20 03:14 IST — Stage32 new mechanism, branch-scoped workflow push
- Stage31 source run 44605726717 and original artifact 14569702420 previously audited: BTC 5/22 positive, PF 0.791, -33.31% net; REJECT. Stage30 REJECT; Stage25/26 REJECT. No unfinished study known from this task at iteration start.
- Pre-registered novel differential and falsifier: analysis/paired_impact_reversal_stage32/NOVELTY_CHECK.md (SHA 676b394b862cf0ff61d04246dca50407d6780bbf).
- New isolated branch research/btc-first-impact-reversal-stage32-20261120 based on Stage31 branch for already verified native data loader; no changes to Stage31 files.
- Fixed BTC-first causal implementation: scripts/research_paired_impact_reversal_stage32.py SHA 81d278570343166a4fa15676a4005d88c948fd00.
- Branch-restricted push-trigger workflow created LAST: .github/workflows/stage32-btc-first-impact-reversal.yml SHA 10815503db03d31ad16947473881f667d8fec54a. This is a GitHub-accepted workflow push, NOT a confirmed Actions run.
- Exact verification blocker: GitHub connector fetch_commit_workflow_runs filters PR-triggered runs and cannot enumerate push runs. Direct GitHub REST Actions listing via web returned inaccessible; container requests to api.github.com failed DNS resolution. Checked expected summary.csv and all_22_months.csv on branch; 404 as of this iteration, which is not proof no job ran. Actual run ID, job completion, artifacts and backtest profitability NOT VERIFIED.
- Next exact step: GitHub Actions GET /repos/rajkumar0rk/BTC-Analysis/actions/runs?branch=research/btc-first-impact-reversal-stage32-20261120, inspect newest run for commit 10815503..., jobs/logs, artifact stage32-original-ledgers. If failed, repair SAME isolated branch. If successful, audit BTC 2025 first, then BTC 2026 and frozen ETH; reconcile full original trade ledger, 22 monthly mark-to-market NAV, PF and cost stress before deciding. Do not claim 22/22 or alert without evidence.
- Modeled fee 0.05% each side plus 18% GST, BTC 5-point slip each side, ETH 0.02% per side, worse-cost stress. Real funding, order-book impact, spreads, lot minima, liquidation maintenance omitted; must disclose.
- No live orders, main changes, other schedule changes or deployment.
