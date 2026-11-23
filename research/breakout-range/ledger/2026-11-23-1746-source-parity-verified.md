# Breakout-range execution audit — 2026-11-23 17:46 IST

## Independently verified historical source parity
- Branch: research/breakout-range-source-audit-20261121 (read-only historical execution inspection).
- Successful run: https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/45129514038 ; job 137541541089; head SHA 92326bf18fef0e96e18f787f6a938c068e717d13; artifact 14796804344.
- Decoded completed job log explicitly prints: `SOURCE_PARITY {"upstream_commit":"5d879b3d04031952f41d2b4d4c4a3cce43f04150","mismatch_count":0,"first_mismatch_dates":[],"reference_signals":29,"local_signals":29}`.
- Thus the previously unresolved diagnostic is PASS for this pinned reference on this archive. It is a signal-array comparison, **not** an independent guarantee of upstream order execution, risk sizing, or future profitability. Existing workflow still does not assert mismatch_count == 0; a future change could silently regress. No code change claimed.
- Ten replay configurations completed successfully; job log NAV reconciliation errors are approximately floating-point epsilon (largest inspected absolute < 1e-11). Do not count this as a new strategy backtest.

## Additional execution and novelty review
- Existing code tests chronological prefix invariance for two_b and wavelet_two_b at 2025-06-30, 2025-12-31 and 2026-06-30, and replays minute fills; source_parity_reference is diagnostic only. The source-parity check compares final signal arrays, not full upstream trade ledgers.
- The novel volume-breakout candidate remains **NOT APPROVED FOR BACKTEST** until exact source snapshot/license, prior-art comparison against Stage23/24 and deterministic original stop/exit and order semantics are pinned. Avoid inventing a substitute implementation.
- Two existing leads (OBV-confirmed 20-bar break and five-minute maximum-volume break) are not counted as newly sourced or historically tested in this iteration. Distinguish signal/volume confirmation from generic trend following and prior Stage23/24 breakouts.

## Handoff
1. Add fail-closed source-parity assertion, preserve existing original baselines, commit only on family branch, and verify with a newly completed authentic archive workflow before marking fixed.
2. Screen 2–4 genuinely distinct source-pinned breakout/retest/rejection candidates and implement only those passing novelty/license gates; batch authentic historical execution with 0.05% per-side fees + 18% GST and zero initial slippage.
3. ETH remains unverified. No live trades, other schedules or protected branches touched.

Iteration: 0 new source discoveries; 0 distinct new backtests; 0 parameter variants; 1 previously unresolved historical diagnostic verified by completed job logs; no new P&L claims.
