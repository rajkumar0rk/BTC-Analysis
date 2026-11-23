# Breakout & Range — parity fail-closed verification handoff (2026-11-23 18:42 IST)

- Family branch: `research/breakout-range-source-audit-20261121` only; no live trading or protected branch changes.
- Existing historical run 45129514038 succeeded at 92326bf and logged 0/29 source signal mismatches; however a mismatch previously did not fail execution.
- Minimal fix commit: `dee2a0ad992a71f3981fbe07afbb1ccef1d9496e`; immediately after writing source_parity_diagnostic.json and printing the parity record, assert mismatch_count == 0. Original source, signals, fills, sizing, fees, GST and monthly outputs otherwise unchanged.
- Authentic Actions runs detected at the new SHA: 45181690568 (replay job 137716812026), 45181690557 (wavelet_daily_replay job 137716811759 and verify job 137716812233). At last check jobs IN_PROGRESS at checkout; **PENDING VERIFICATION**, not FIXED_AND_VERIFIED.
- Next: poll exact runs to completion; inspect job logs, artifacts, source_parity_diagnostic.json, causal_prefix_checks.json, summary.json, trade CSV and IST monthly CSV; compare every prior configuration with artifact 14796804344. Require zero parity mismatches, unchanged trade count/PF/NAV/DD, complete fee and GST, zero NAV reconciliation error. If failing, repair and rerun.
- New distinct strategies completed: 0; new historical P&L verified: 0. Funding and market impact remain unmodeled.
