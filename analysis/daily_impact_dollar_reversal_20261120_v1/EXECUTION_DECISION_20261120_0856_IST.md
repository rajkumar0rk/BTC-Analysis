# Completed GitHub run and economic decision — 2026-11-20 08:56 IST

## Evidence
- Source branch: research/daily-impact-per-dollar-reversal-20261120-v1
- Source commit: b0075345b254a364c457a40e8804024354a63521
- Workflow: https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/44659654221
- Job 136034458123: success, backtest and artifact uploads completed.
- Summary artifact 14595166569; SHA256 1b3a35f38506098238926cc062db60eb1d5a50153c064fb78b6fb87fafe6a9c8
- Original trades artifact 14594169629; SHA256 c3302c64a94f8e03f002be2811674aabb8a1ac08601e05c61a4d8a3ec988f9db

## Original program stdout (NOT independently reconciled ledgers)
- BTC base: 389 trades, 468 signals, terminal closed NAV 0.9515648711 (−4.8435%); 135 positive / 191 negative / 343 flat days; reported 22 monthly records.
- BTC stress: 389 trades, terminal closed NAV 0.9478052252 (−5.2195%); 135 positive / 191 negative / 343 flat days.
- ETH base, unchanged rules: 521 trades, 603 signals, terminal closed NAV 0.9179255533 (−8.2074%); 159 positive / 236 negative / 274 flat days.
- ETH stress: 522 trades, terminal closed NAV 0.8969818639 (−10.3018%); 150 positive / 245 negative / 274 flat days.
- Both market day totals are 669. Program claims zero gap/unmeasured days, but full Jan 2025–Oct 2026 is 669 days only if date boundaries and coverage are reconciled; known start and October data issues still require independent audit.
- Program itself reports INCONCLUSIVE_EXECUTION_FUNDING_AND_DATA_COVERAGE. Historical executable spread, settled funding, volume units, lot/tick validation and coverage remain unverified.

## Decision
REJECT the economic hypothesis as a candidate for this schedule: negative after-modeled-cost BTC performance with 389 trades, deteriorating under worse fills, and similarly negative frozen ETH validation. This is NOT a verified executable/live result. Do not tune this losing mechanism on 2026 or ETH. Preserve original artifacts and source unchanged. The next iteration should verify the raw ledgers and monthly NAV reconciliation and choose a genuinely distinct BTC-2025 observable-data mechanism, without reusing this hypothesis.

## Audit limitations
This decision is based on the actual completed GitHub job and its stdout, artifact IDs and digests. ZIP contents and individual monthly/transaction rows were not independently downloaded or reconciled in this iteration; consequently no monthly PF, account drawdown, data-hash validation or fully audited daily-rate claim is made.
