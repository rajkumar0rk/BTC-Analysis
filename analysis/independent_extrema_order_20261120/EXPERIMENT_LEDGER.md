# Append-only experiment ledger — Independent Big-Winner Strategy Hunt

## 2026-11-20 07:40 IST — novel causal experiment implemented; push-run verification blocked
Previous same-task volume-absorption study: corrected GitHub Actions run 44635317067, BTC ~-16.05%, PF .49; ETH ~-3.13%, PF .89; REJECTED. Do not retune. No newer same-task pending experiment was identified in prior handoff. Read codex/STRATEGY_NOVELTY_GATE.md and closest prior families; see NOVELTY_CHECK.md for overlap caveats.

Hypothesis: ordering of true 1-minute hourly extrema (low before high vs high before low) predicts directional continuation after intrahour sweep and range expansion; hourly OHLC cannot distinguish this. Preregistered script scripts/research_independent_extrema_order_20261120.py committed at 6f1b432fd2b7d3f937c0085c10321ae0bdedaa10; novelty gate at 9c1ae1fec0a5b8a9c4bb4f7dadc9c47b79ea9268; branch-specific push workflow commit 886468840af24c8217ed78f6663bfe439ac536c8.
Workflow URL: https://github.com/rajkumar0rk/BTC-Analysis/actions/workflows/independent-extrema-order-20261120.yml

Execution verification: GitHub commit combined status returned [], commit-scoped workflow-run lookup returned [] BUT connector only exposes PR-triggered runs; external workflow webpage fetch failed DisabledError. These responses DO NOT establish that push run did not launch. No run ID or backtest outcome can be asserted. Precise next action: inspect push-triggered workflow runs in GitHub Actions UI/API; if missing, repair workflow registration on this branch; if failed inspect job logs; if succeeded download original artifact, audit raw trades, monthly NAV, 2025-only signal, missing bar coverage, fees, stop sequencing, funding uncertainty and top-winner-removal before deciding REJECT/PROMISING/VALIDATED. Never treat mere green workflow as evidence of profitability.

This run left executable new research code, a preregistered novelty check and a dedicated push-triggered workflow. No main, other task branch, automation or live account changed.
