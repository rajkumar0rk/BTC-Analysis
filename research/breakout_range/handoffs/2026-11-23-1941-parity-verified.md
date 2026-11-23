# Breakout & Range verification — 2026-11-23 19:41 IST

Existing isolated branch: research/breakout-range-source-audit-20261121.

Fail-closed source-parity change dee2a0ad992a71f3981fbe07afbb1ccef1d9496e: historical run https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/45181690568 completed SUCCESS; job 137716812026 completed SUCCESS; archive-integrity run 45181690557 completed SUCCESS. Historical artifact 14821004988 (24 files), ZIP SHA256 252527c4f1d074eaa00171197f8223376577cc3d2c88450efd4f3734e5e73d42. Verified SOURCE_PARITY upstream 5d879b3d04031952f41d2b4d4c4a3cce43f04150, reference_signals=29, local_signals=29, mismatch_count=0.

Independently opened artifact ZIP and recomputed sum(trade.net), sum(entry_fee+exit_fee), trade count, and starting cash 10000 + trade net against each of all 10 published configuration summaries. Maximum absolute reconciliation error 7.86e-12 USD. All 10 trade CSV files and corresponding monthly CSV files present. Wavelet-2B matched zero slippage: 15 trades, net +313.630782086646 USD (+3.1363% of starting cash), PF 1.5356756898, max DD -4.6296816099%. These are historical simulations with 0.05%/side fees plus GST, no funding/spread/L2, not live-ready. TwoB baseline: 78 trades, -92.88447669394327 USD, PF 0.9714039628. Zero newly distinct strategy backtests this run; 1 historical repair verified end-to-end. No protected branches, trading or other schedules changed.

Next: source/novelty/license qualification and authentic one-minute replay of distinct OBV/volume-confirmed boundary-break mechanism; do not relabel prior source screens as new backtests. Preserve 2025-only selection and frozen 2026/ETH verification.
