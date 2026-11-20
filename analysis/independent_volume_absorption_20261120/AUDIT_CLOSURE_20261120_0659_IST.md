# Volume absorption — verified rejection closure (2026-11-20 06:59 IST)

Research-only; immutable historical source. Branch: research/volume-absorption-convex-btcfirst-20261120-0348.

## Verified workflow
- Run: https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/44635317067
- Job 135952201713: completed/success; Python backtest and upload-artifact steps succeeded.
- Run head SHA: 7986cabc0aeeffb0024bdad281bb5320ee8174c7.
- Original artifact 14583656684, name volume-absorption-btc-eth-evidence, 67,038 bytes, SHA256 a25c694e6e8cf30d9c526143103ade97ce3e67748665cf148a8992dc85e95d33, not expired at check.

## Decision: REJECTED, not a positive-expectancy candidate
Reported completed-run summary from task handoff: BTC ~-16.05% after costs, PF ~0.49; frozen ETH ~-3.13%, PF ~0.89. Both below break-even. These figures are from the prior handoff, not independently recomputed from the artifact in this check. GitHub job and artifact metadata have been independently confirmed. No claim of a profitable mechanism or exceptional asymmetry is supported. Do not optimize this rejected configuration against BTC 2026 or ETH.

## Audit notes / limits
- Source computes fee 0.05% each side plus 18% GST and slippage with at least $5 BTC price-point adverse adjustment per side. No authentic historical funding settlements or L1 execution are incorporated.
- In the source, trailing stop is updated from the minute's favorable extreme only after testing the old stop, an appropriate stop-first ordering; however intrabar liquidity/market impact cannot be verified.
- Exact trade count, top-winner removal, monthly NAV reconciliation, full-year 2025 and Jan-Oct 2026 returns must be read from original evidence before citing numerical claims. They are not verified here.
- The 2025-2026 source coverage and first IST day gap require independent checking before asserting all 22 complete months.

## Next iteration
Perform novelty gate on a materially distinct observable mechanism, preregister BTC 2025 rules, implement a branch-scoped executable workflow and verify launch. Do not recycle volume absorption, spot lead-lag, OI breakout or variance end-loading. Keep other research branches, main, and live accounts unchanged.
