# BTC & ETH Consistent Monthly Returns Search — append-only experiment ledger

## 2026-11-19 Stage31 — EXECUTION PENDING VERIFICATION
- Previous task-specific Stage30: REJECT based on BTC PF 0.527, 1/22 profitable months, 57.83% drawdown. See inherited Stage30 DECISION_20261119.md. Stage25/26 rejected and not recycled.
- New mechanism: high-volume directional 1h volatility shocks may propagate via delayed rebalancing/forced flows; falsifier is poor BTC 2025 monthly after-cost PF and account returns, or excessive drawdown/cost sensitivity.
- Fixed causal rule: completed 1h candle range >=2x prior 24 completed hours' median range, volume >=1.5x prior 168 hours' median, directional body >=1.25x prior 24h median ATR, close in outer 20% of candle. Enter next minute open in direction. Stop 1.5x native ATR, TP 3R, timeout 24h, one position; 0.5% account risk, 3x cap. Same rules for BTC and ETH, no ETH tuning.
- Source revision: c4fd1b34b4f75533a8537c66bd498c0043cb12f9; workflow trigger revision: 2ce98b1e5568fd2a40c50649552afd168340697f. Workflow: .github/workflows/stage31-btc-first-shock-drift.yml.
- Launch: branch-scoped workflow YAML committed last. Direct workflow-run listing inaccessible from available connector; fetch_commit_workflow_runs returned [] but that endpoint explicitly filters PR runs, so this is NOT proof of no push-triggered run.
- Results: PENDING. No backtest completion, log, original trade ledger or monthly return verified in this iteration. No claim of profitability.
- Next action: inspect GitHub Actions branch run and its logs, fix errors on this branch, confirm complete original ledgers and 22-month BTC/ETH summaries; reject or retain using BTC evidence only.
- Modeled fee 0.05% each side +18% GST, BTC 5 points slip each side, ETH 0.02% each side, cost stress; real funding, spread/depth/impact, contract minimums and liquidation maintenance not modeled.
- Scope: other automations and live trading untouched; main untouched.

## 2026-11-19 Stage31 — FAILED SETUP DIAGNOSED / REPAIRED
- Actual push-triggered run: https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/44534258208, job 135595390515, FAILED at actions/setup-python@v5 before dependency install or backtest.
- Exact error: `No file ... matched to [**/requirements.txt or **/pyproject.toml]`; caused by `cache: pip` without a dependency manifest. No trades or results were produced; artifact uploader found no files.
- Repaired ONLY Stage31 isolated workflow by removing `cache: pip`, preserving Python 3.11, dependency installation, original strategy and cost rules. Repair commit: `0efe6a08ae93d7d02149144b4badb879c6e32975`.
- The workflow is restricted to pushes modifying its YAML or Stage31 script. GitHub accepted repair push. A new run ID and successful completion were not yet confirmed at this check; re-query branch-scoped Actions runs, inspect job/logs, then reconcile original ledgers before any new hypothesis. Status: REPAIR / RETEST, not a verified backtest.

## 2026-11-19 Stage31 — RETRIGGERED / RUN IDENTIFIER NOT EXPOSED
- Verified historical run 44534258208 job 135595390515 failed during setup-python pip-cache manifest lookup; no strategy step executed in that attempt.
- Confirmed workflow on branch now has no `cache: pip`; confirmed Stage31 source and dependency exist. Re-triggered the SAME study with workflow-only commit `8090cdd762c8c7d45e3972b7e1eaeb4b73ab1fc7` (source-SHA audit step and serialized concurrency); push-trigger paths include the changed workflow.
- Connector `fetch_commit_workflow_runs` returns only pull-request-triggered runs, so it cannot establish push-triggered run ID. Public GitHub Actions branch-run API could not be reached from the available network route. This is an exact verification blocker, NOT evidence of a completed run or a missing run.
- No Stage31 result artifacts or original trade ledger are committed as of this check. State: RETEST TRIGGERED, COMPLETION UNVERIFIED. Next: GET `/repos/rajkumar0rk/BTC-Analysis/actions/runs?branch=research/btc-first-shock-drift-stage31-20261119`, inspect newest run/jobs/logs/artifacts, then audit all 22 months before accepting/rejecting. Do not switch hypothesis or retune based on ETH/2026.
- Potential audit issue to check after completion: Stage31 monthly NAV is calculated from realized exits; it does not mark open positions at month boundaries, so monthly NAV claims must be corrected/reconciled before any validation. Preserve raw ledger and baseline settings.
