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
