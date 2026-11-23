# M39 — Independent downloaded M14 artifact audit (2026-11-23 IST)

## Provenance
- Existing completed run: https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/45141426585
- Run commit: e4e9fa8b2c142297622f37e6a484f1e1d8a2b24f; artifact ID 14802102496.
- Downloaded ZIP SHA256: 88fc556ecca035173453bf1a6ef5f87aa38efc33cabfc6974b9df27754a29d71.
- Files directly opened: trades.csv (27 rows), monthly_nav.csv (12 rows), summary.json.
- This is an independent audit of an EXISTING historical replay, NOT a new baseline or newly run strategy. No trading-code changes.

## Independent calculations
- Starting NAV 10000; sum of all 27 net_usd trade rows = -1511.9442031960436; final NAV = 8488.055796803954; reconciliation residual 2.50e-12 USD.
- Wins 9, losses 18, zero flat; realized PF recomputed from positive/negative trade net = 0.4728016995918179.
- 23 indicator_exit, 4 stop_first; average holding duration 1328.111111 minutes (minimum 240, maximum 3660).
- Monthly file: 12 IST rows, sum trades_exited=27; final monthly NAV = 8488.055796803954. Maximum absolute difference between recomputed sequential month-on-month NAV percentage changes and CSV net_return_pct = 4.44e-16 percentage points.
- Months: Jan -4.033600% (3), Feb 0% (0), Mar -10.133422% (4), Apr +2.611336% (4), May +1.309794% (3), Jun +0.008587% (2), Jul -2.056231% (2), Aug -5.265434% (3), Sep 0% (0), Oct +3.477184% (2), Nov -0.558487% (2), Dec -0.846251% (2).
- 4 positive, 6 negative, 2 flat months; final net return -15.119442%; summary maximum drawdown -18.036842% (not independently reconstructible from trade/monthly rows without full minute equity path).
- ZIP matches uploader-reported hash. No negative holding durations.

## Limitations and decision
- Freqtrade exit parity explicitly UNVERIFIED; not a source-faithful reproduced baseline. 2025 January IST is partial, no 2024 warmup; funding, L2, spread and liquidation not modeled. Zero assumed slippage, modeled fee 0.05% each side + 18% GST.
- The trade CSV has net_usd but no separate gross P&L and fee columns; cannot independently reconstruct fee breakdown, intra-month max drawdown or mark-to-market equity path. Monthly NAV is numerically consistent but not independently reconstructed minute-by-minute.
- REJECT as profitable. No 2026/ETH optimization or slippage stress justified. Preserve original artifact. Next work: distinct source-complete momentum acceleration mechanism, novelty gate and actual new BTC2025 replay.
