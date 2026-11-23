# Trend-family source triage — 2026-11-23, next mechanism after KAMA rejection

Scope: READ-ONLY inspection of other family work; no claim of historical execution. Existing KAMA baseline rejected on authentic BTC2025 (-7.52% net, PF 0.814); TSMOM 90D rejected on BTC2026 (-5.20%). These are NOT rerun.

## Candidate A — continuous volatility-normalized return EMA
- Creator: Kali-Uga; immutable GitHub commit d562ec7a42d2727975b7076a6413fbb2d452579d; https://github.com/Kali-Uga/trend-following-futures/tree/d562ec7a42d2727975b7076a6413fbb2d452579d ; MIT license according to repository.
- Published rule: position = EMA(log returns) / (signal_vol * asset_vol) * scale, capped at +/- position limit; signal_vol is EMA absolute returns; asset_vol double-smoothed EMA absolute returns. Published universe NQ/JY/BTC, data not bundled. Exit by shrinking or reversing continuous target. This is not the same as binary 90D TSMOM, but overlap with Sepp continuous EWMA requires novelty check before implementation.
- Reproducibility gate: notebook must disclose exact spans, volatility smoothing, scale and cap; do not invent them. Disproof: after fees/GST, no positive matched-risk BTC2025 expectancy, or NAV reconciliation failure. High turnover is a particular threat. No published BTC-specific trade count/PF verified.

## Candidate B — ADX gated SMA-volume trend with trailing ATR
- Creator: IssacWong0103; immutable commit f80abb5075d3eab77f9d23d5f5d6ce90d210ef38; https://github.com/IssacWong0103/Regime-Aware-Algo-Trading-Python-Project/tree/f80abb5075d3eab77f9d23d5f5d6ce90d210ef38 ; license NOT VERIFIED.
- Source rule: ADX14 >25, SMA10 > SMA50, volume >1.5 x rolling 20 volume, long-only; exit highest high since entry minus 3 ATR. Publisher reported SBUX 1H Oct2025-Feb2026 +5.8%, PF 5.1, 18 trades, no costs/slippage. NOT transferable to BTC. Overlaps ATR Chandelier and MA crossover prior art; fast reject as independent baseline unless novelty gate confirms distinct source-defined signal. Publisher's hybrid mean-reversion part is out of this family.

## Candidate C — cross-sectional crypto CTA trend ensemble
- Creator: OctopusTakopi; immutable commit 804eb428705c913988371c28a57ca051bb3a7f9c; https://github.com/OctopusTakopi/crypto-trend-following/tree/804eb428705c913988371c28a57ca051bb3a7f9c ; license NOT VERIFIED.
- Publisher claims multi-market 2020-2026 net Sharpe 1.04, return +242.1%, max DD -30.1%, 10bp transaction cost and measured funding. A portfolio-wide strategy cannot be faithfully reproduced as a single BTCUSD contract without changing its economic mechanism; classify NOT ELIGIBLE for BTC-only faithful baseline. Potential read-only methodological reference for portfolio research, not this family baseline.

## Next actual execution gate
1. Inspect branch AGENTS.md and novelty ledger plus Candidate A notebook at pinned commit; extract exact defaults and confirm license and overlap. Preserve original notebook/source hash.
2. If eligible, adapt ONLY causal completed daily signals to existing authentic Delta India 1m historical runner, next 1m open, 0.05%/side + GST, zero slippage, sequential NAV, risk-matched cap; run BTC2025 workflow, retrieve actual trade/monthly artifacts, independently reconcile.
3. Do not report profitability from publisher claims, synthetic bars, unit tests, a queued run or a commit. If A duplicates prior EWMA, move to different sourced persistence mechanism.
