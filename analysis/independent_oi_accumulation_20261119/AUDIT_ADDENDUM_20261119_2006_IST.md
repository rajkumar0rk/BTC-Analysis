# Append-only audit addendum — 2026-11-19 20:06 IST

Study: BTC-first open-interest accumulation/breakout.
Verified successful run: https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/44522204998 (source SHA 61425c080bdb0ca60b8109380b31253ca201f61c).
Evidence artifact: 14527824142, sha256 5572a100ea26685d92e918b4b1bd53775a455abebc5f5ba3fe746bb90260fe0f.
Existing persisted decision: DECISION_20261119.md, REJECT; BTC 2025-labeled -1.112% PF .917; BTC 2026-labeled -2.753% PF .734. ETH frozen 2025 +14.294%, 2026 -6.037%. Not qualifying.

NEW SOURCE-LEVEL DATA-QUALITY FINDING: scripts/research_independent_oi_accumulation_20261119.py lines 35–39 reindex hourly OI to hourly price bars and then **drop every hour missing OI**. Subsequent lookback and holding periods operate on the compressed row index, so 24 rows need not be 24 consecutive hours and 168 rows need not be 168 elapsed hours. This is a causal/time-scale defect: exclusion avoids fabricated OI, but silently bridges unavailable observations. The historical strategy must not be labeled fully time-consistent or validated. Do NOT repair by forward-filling unknown OI. A future clean implementation must retain continuous hourly timestamps, invalidate signals across OI gaps, and measure holding limits in elapsed time; audit price hour completeness and OI freshness. Because primary BTC is already loss-making and below asymmetric thresholds, reject rather than retune or promote.

Additional unresolved audit defects confirmed from original persisted output: BTC_2025_training monthly exits include 2026-01, and BTC_2026_evaluation begins 2026-02; monthly 'sum' is realized currency PnL, not month-end marked-to-market account NAV return. Monthly no-trade rows absent; JSON contains NaN PF for win-only months rather than explicit Infinity with count warning. Full calendar-year 2025 and Jan–Oct 2026 account returns cannot be inferred from these segment labels. Funding and intratrade MTM drawdown unavailable.

Decision remains REJECTED, with execution-integrity caveat. Do not choose parameters based on ETH or later BTC. No new study was launched in this audit iteration. Main and other schedules untouched.
