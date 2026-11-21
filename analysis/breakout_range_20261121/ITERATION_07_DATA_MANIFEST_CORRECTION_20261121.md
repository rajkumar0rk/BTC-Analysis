# Iteration 07 — material data-availability correction (2026-11-21 IST)

## Read-only verification
Branch: research/breakout-range-source-audit-20261121; previous head 6109a7dc6e2744fe52c288d6ac1aed20564aab17.
Read codex/AGENTS.md, codex/STRATEGY_NOVELTY_GATE.md and iteration 06 handoff before any experiment.
GitHub contents API returned all 23 BTCUSD monthly compressed 1-minute files under data/delta_india/BTCUSD/1m/, January 2025 through November 2026, plus manifest.json. The manifest explicitly states source https://api.india.delta.exchange/v2/history/candles, BTC perpetual futures, UTC seconds, and partition gzip SHA256. This CORRECTS the previous statement that archive presence was unverified.

## Important contradiction
The manifest generated 2026-11-20T10:17:52Z reports 2026-10.csv.gz expected_minutes=44640, observed_candles=44640, missing_minutes=0, SHA256 118135c40c1ef97a325c85a6aace8ebe45de88cb723a4da624b4a4f5b31043e6. Older novelty guidance says October 31 UTC missing 1440 minutes. The newer manifest claims a repaired archive, but this inspection DID NOT download, decompress, independently hash or verify individual rows. Both cannot be accepted simultaneously without an actual archive validation job. Do not claim 22 complete IST months from a manifest alone; IST calendar boundaries also require November 1 UTC spillover for October.

## Status and next executable steps
Data discovery blocker is narrowed: files and checksums are accessible via repository contents, but runner file integrity and provenance are unverified. Novelty remains blocked: no source-faithful distinct rule has passed the gate. No branch-local historical backtest has been executed or claimed. Before testing: select and snapshot an externally published fully deterministic novel mechanism, commit per-candidate NOVELTY_CHECK.md; run SHA256 and row/timestamp/OHLC checks for all partitions including October and IST boundaries; then complete fee/GST zero-slippage NAV backtest with 1-minute next-open fills, preserve trade ledger and monthly returns. Funding unmodeled. No other branches or live systems touched.
