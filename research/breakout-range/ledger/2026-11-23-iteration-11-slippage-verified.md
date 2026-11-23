# Breakout-range iteration 11 — 2026-11-23 IST

State: VERIFIED_COMPLETED_HISTORICAL_SLIPPAGE_BATCH (not live-ready).

Source pinned: zty05070242/wavelet-2b commit 5d879b3d04031952f41d2b4d4c4a3cce43f04150. Runner commit dc97d30b235e2ecbbad9bd28b748222572be20a1. Branch research/breakout-range-source-audit-20261121. GitHub Actions completed SUCCESS: https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/45098672933 ; job 137444175376; archive audit https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/45098672897 ; artifact 14784333898 SHA256 7e386e5d6081fe34cc455af71ad782c50992cb0d655d3521537408d00a8ee3ed.

Artifact ZIP downloaded and all eight trade CSVs/monthly CSVs checked independently: trade counts match summary; sum(trade net) matches reported P&L; final monthly NAV matches ending cash within floating point. Source parity and prefix diagnostic JSONs retained in artifact.

| Configuration | Trades | Wins | Net USD on 10k | Return | PF | Max DD |
|---|---:|---:|---:|---:|---:|---:|
| wavelet_two_b zero-slip matched | 15 | 4 | 313.6308 | 3.1363% | 1.5357 | -4.6297% |
| wavelet_two_b matched 0.5 point/side | 15 | 4 | 313.2080 | 3.1321% | 1.5348 | -4.6297% |
| wavelet_two_b matched 5 points/side | 15 | 4 | 309.4136 | 3.0941% | 1.5274 | -4.6301% |
| wavelet_two_b zero-slip source sizing | 15 | 4 | 1140.6322 | 11.4063% | 1.4725 | -17.1380% |
| wavelet_two_b source 0.5 point/side | 15 | 4 | 1138.8901 | 11.3889% | 1.4717 | -17.1383% |
| wavelet_two_b source 5 points/side | 15 | 4 | 1123.2615 | 11.2326% | 1.4646 | -17.1410% |

Controls: two_b baseline 78 trades, -92.8845 USD, PF 0.9714, max DD -12.5507%; source sizing 78 trades, -990.8735 USD, PF 0.9205, max DD -41.5309%. All eight CSVs have 23 monthly rows including 2 partial IST months; only 21 complete months. Fee 0.05% each side plus 18% GST, funding unmodeled. No new distinct strategy baseline in this run, four sensitivity variants verified, no ETH, no spread/L2/real margin modeling. Further source stop/exit fidelity, 2025-only frozen variations and ETH verification pending. Do not interpret four winning trades as robust edge.
