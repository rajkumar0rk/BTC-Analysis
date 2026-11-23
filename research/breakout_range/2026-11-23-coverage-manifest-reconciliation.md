# Breakout & Range — 2026-11-23 coverage reconciliation (append-only)

## Evidence and conclusion

At branch research/breakout-range-source-audit-20261121, commit 92326bf18fef0e96e18f787f6a938c068e717d13, the authenticated data/delta_india/BTCUSD/1m/manifest.json declares UTC 2026-10 partition start 2026-10-01T00:00:00+00:00, end-exclusive 2026-11-01T00:00:00+00:00, expected_minutes=44640, observed_candles=44640, missing_minutes=0, SHA256 gzip 118135c40c1ef97a325c85a6aace8ebe45de88cb723a4da624b4a4f5b31043e6. UTC September also has all 43200/43200 minutes. Thus the earlier claim in codex/STRATEGY_NOVELTY_GATE.md that 2026-10-31 UTC is missing 1440 candles is STALE for this particular authenticated Delta 1m archive. Do not conflate it with a different dataset or older snapshot.

October 2026 IST comprises 2026-09-30T18:30:00Z through 2026-10-31T18:29:00Z inclusive. Both UTC partitions are complete. Hence the observed October 2026 IST month being labeled 'complete' is CORRECT for the available archive; the earlier pending issue was an incorrect premise, not evidence that the new coverage counting code failed. November 2026 IST is partial because replay stops before 2026-11-01T00:00:00Z; January 2025 IST is partial because replay starts at 2025-01-01T00:00:00Z. The October UTC partition is 44640 rows, not 43200. This finding does not imply every strategy is profitable in October.

Historical replay Actions run https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/45129514038 completed success with evidence artifact 14796804344. Archive-integrity Actions run https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/45129514033 completed success; artifact 14796873099. Its validator logged pass=true, partition_count=23, failures=[]. Both runs used commit 92326bf. The code explicitly counts observed minute NAV values against calendar IST minutes and marks any short month partial_missing_ist_minutes. This resolves the coverage-label investigation without changing historical execution or retroactively altering any trade ledger. No new strategy or PnL claim.

## Scope / next steps

This is a correction of the previous handoff's assertion, not a new fix requiring rerun. Future research should update stale novelty text only in its own isolated branch and preserve this immutable record. Next substantive work: source-defined nonduplicate candidate discovery and authentic BTC 1m baseline tests; frozen ETH after 2025 BTC selection. Funding, L2, and spread remain unmodeled.
