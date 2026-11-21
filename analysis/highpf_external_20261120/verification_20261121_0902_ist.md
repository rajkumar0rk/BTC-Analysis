# High-PF research — 2026-11-21 09:02 IST verification

Scope: research/highpf-external-source-audit-20261120 only. No live execution.

Verified GitHub Actions run https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/44815513786, job 136562679886, commit 86194a4003547170ed813adf364809ae098c02f4. Job FAILED in step "Native BTC 2025 screen (fail closed on data gaps)". Error: INCOMPLETE_IST_COVERAGE; required 2024-12-31 18:30 UTC through 2025-12-31 18:29 UTC, available 2025-01-01 00:00 UTC through 2025-12-31 23:59 UTC. No artifact was produced.

Source inspection scripts/highpf_external_tsmom_screen_v1.py confirms a separate 60 *completed IST daily bar* warmup requirement for the original 60-day momentum rule. Fixing only the 5h30m IST Jan 1 boundary gap will NOT fix the 60-day warmup. Authentic contiguous BTC 1m history covering at least November–December 2024 is required, and must be validated for duplicate timestamps, gaps, and OHLC sanity. Never synthesize the missing observations or silently shorten lookback.

Decision: BLOCKED / INCONCLUSIVE, no valid BTC screening outcome and no cost sensitivity/ETH run. Funding UNMODELED. Exact next action: retrieve authentic Delta BTC 1m November–December 2024 candles, verify source provenance and minute continuity, then rerun zero-slippage BTC2025 screen with two-sided fees and GST. If provenance cannot be obtained, close this candidate as data-blocked and pursue a different externally sourced, reproducible mechanism with available history. No profitability claim.
