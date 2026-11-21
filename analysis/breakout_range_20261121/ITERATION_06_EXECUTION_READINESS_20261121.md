# Iteration 06 — executable research readiness check (2026-11-21 IST)

## Verified status
- Branch: `research/breakout-range-source-audit-20261121` (isolated from other families).
- GitHub Actions query `/actions/runs?branch=research%2Fbreakout-range-source-audit-20261121&per_page=10` returned `{"total_count":0,"workflow_runs":[]}` at inspection time. Therefore **no completed or pending actual backtest exists on this branch** to resume; previous iterations were source audits only.
- The source branch contains `codex/STRATEGY_NOVELTY_GATE.md`, which explicitly forbids running a duplicate strategy and requires a committed deterministic `NOVELTY_CHECK.md` before a new experiment.
- The branch's `codex/DATA_CONVENTIONS.md` describes **only** an original 61,206-row **5-minute** input with unverified exchange and timestamp alignment. It is **not** evidence of authentic Delta India BTC 1-minute availability.
- Stage24 code declares `data/delta_india/BTCUSD/1m/20??-??.csv.gz`, but no present GitHub Actions runner archive manifest/hash has been verified. The known 2026-10-31 UTC 1,440-minute hole means a full 22-month completeness claim is not currently supported.
- No workflow-dispatch action is exposed by the current GitHub connector. Existing workflows can be inspected, but no fresh run can be claimed launched from this interface.

## Novelty decision
A standard fixed-session false-breakout fade is a **duplicate** of `scripts/research_daily_failed_breakout_20261119.py` (branch `research/daily-failed-breakout-20261119`), which already sweeps a fixed opening range and closes back inside on completed 5-minute candles, with next-minute execution. Generic 15-minute squeeze/retest and Donchian breakouts overlap Stage24/25. No source-faithful *materially distinct* executable strategy has been approved, so do **not** invent entry rules or backtest a cosmetic variation.

## Source candidates considered and evidence boundaries
- `https://github.com/MAKSAT-DEL/mtf-breakout-bot`: source execution bugs documented in `MTF_BREAKOUT_EXECUTION_AUDIT_20261121.md`; publisher PF 1.46/209 trades cannot be reproduced faithfully without changing execution semantics and costs.
- `https://github.com/BatuhanGen/breakout-backtest-tool`: range-entry variants, but standard boundary/retest signals overlap prior research. This is an execution reference, not independently profitable BTC evidence.
- `https://github.com/sam-bateman/trading-orb`: equity opening auction mechanism cannot be assumed to transfer to 24/7 BTC.
- `https://github.com/SC4RECOIN/simple-crypto-breakout-strategy`: previous-day range breakout appears to overlap already researched daily levels; publisher ETH results are not Delta India BTC results.

## Required execution handoff (do not skip)
1. Recover a pinned licensed public source with complete deterministic rules and a *materially distinct* economic signal; compare exact source logic against Stage19, Stage23, Stage24, Stage25 and daily failed-breakout.
2. Commit a per-candidate `NOVELTY_CHECK.md` with source SHA, complete entry/exit/risk rules and rejection criteria. If none passes, reject the candidate rather than fabricate a backtest.
3. Verify runner access to authentic Delta India BTCUSD 1-minute monthly archive, partition hashes, timestamps, missing-minute coverage and 2025/2026 boundary; fail closed if unavailable.
4. Implement completed-bar signal generation, next eligible 1m open entry, stop-first/gap-aware exits, sequential NAV sizing, 0.05% taker per side + 18% GST, zero assumed slippage first; funding UNMODELED.
5. Execute actual workflow and retain completed job URL, immutable trade ledger, monthly IST NAV/PF table, data/code hashes and rejection/robustness decision. Only then consider frozen 2026 chronological recheck and ETH.

## Outcome
This iteration established that **no branch-local Actions run exists** and clarified the distinction between a documented 1-minute archive *path* and verified runner data access. No actual backtest was executed, no profitability claim is warranted, and no live trading or protected branches were touched. This is a blocked experiment handoff, not an edge discovery.
