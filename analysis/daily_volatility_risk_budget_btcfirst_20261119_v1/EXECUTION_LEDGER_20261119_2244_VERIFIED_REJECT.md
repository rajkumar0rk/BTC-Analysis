# 2026-11-19 22:44 IST — verified completed experiment, REJECT

Source commit: 625c3d1f5cde8a2b0c3d9b749e61031e87b72234
Run: https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/44558873365 (completed success; job 135682339000)
Artifact ID 14547021093, digest sha256:7cd5005f11106aee59dd135c26319dd57678c14d5b1ad13b9737f195363f3cbe, includes original archive_audit.json, provenance.json (source hashes), daily.csv, monthly.csv, annual.csv, trades.csv. Artifact URL: https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/44558873365/artifacts/14547021093

Verified from downloaded original CSVs: BTC base 2025 return -13.677266%, realized PF 0.282527, 209 trades, 52 profitable / 157 losing / 149 flat / 7 data-gap days; 2026 Jan 1–Nov 17 -6.802354%, PF 0.563096, 207 trades, 82 profitable / 125 losing / 114 flat / 0 gap days. BTC stress 2025 -17.213968%, 2026 -10.583593%. ETH unchanged base 2025 -12.843601%, PF 0.405433, 231 trades, 71 profitable / 160 losing / 127 flat / 7 gap; 2026 -8.040650%, PF 0.520513, 207 trades, 79 profitable / 128 losing / 114 flat. ETH stress -16.781305% and -11.771884%.

BTC 2025 all 12 months negative. BTC 2026 positive January +0.493243% and May +0.436888%; all other reported months negative. 2026 November is partial, not part of comparable 22-month Jan 2025–Oct 2026 analysis. Both markets negative after costs; no plausible daily-consistency signal. REJECT: no parameter retuning based on later BTC or ETH. The data audit reports UTC-complete source files, but IST day completeness is separate and seven early IST days were excluded; Jan 1 2025 IST start boundary missing. Execution fills are OHLCV simulated, not historical executable bid/ask; funding cashflows, spread, lot/tick and liquidation details require further independent validation, so no live readiness claim. Annual reported 2026 figures cover through Nov 17, NOT a full year.

Next iteration: choose distinct mechanism only after reading shared novelty gate; preserve this original branch and artifact immutable.
