# Trend family — 2026-11-23 continuous normalized EMA provenance gate (run 11)

## Recovery (read-only)
- Queried the exact GitHub Actions branch-run collection; 28 total runs, newest run 45077740957 completed successfully for the already-rejected KAMA BTC2025 baseline. No newer historical strategy execution found.
- Read codex/AGENTS.md and codex/STRATEGY_NOVELTY_GATE.md on the isolated branch. Closest prior mechanisms: the 30/90-day TSMOM components in this family, Stage25 hourly trend, and Sepp continuous EWMA previously screened. No new test is authorized until a precise parameter/novelty record exists.
- Preserved KAMA -7.52% net/PF 0.814 and 90D TSMOM 2026 -5.20% as rejected; no retuning.

## Pinned upstream evidence
- Author: Nikita Konev (Kali-Uga). GitHub source https://github.com/Kali-Uga/trend-following-futures/tree/d562ec7a42d2727975b7076a6413fbb2d452579d
- MIT license at that exact revision: https://github.com/Kali-Uga/trend-following-futures/blob/d562ec7a42d2727975b7076a6413fbb2d452579d/LICENSE (copyright 2026 Nikita Konev).
- README at that revision: https://github.com/Kali-Uga/trend-following-futures/blob/d562ec7a42d2727975b7076a6413fbb2d452579d/README.md
- Notebook: https://github.com/Kali-Uga/trend-following-futures/blob/d562ec7a42d2727975b7076a6413fbb2d452579d/notebooks/01_trend_following_research.ipynb
- Published mechanism: target position = EMA(log returns)/(signal_vol * asset_vol)*scale, bounded by +/- pos_limit. signal_vol = EMA absolute returns, asset_vol = twice-smoothed EMA absolute returns. Position reductions/reversals are exits; not fixed TP/SL. README claims shifted features, cost assumptions and 2018–mid-2022 development with later checks, NQ/JY/BTC, but does not supply a verified BTC-only fee-inclusive trade count/PF or full dataset.
- Publisher's reported parameter stability near period 263 and 5m Sharpe >1.40 are **publisher claims**, not local BTC findings. Publisher also reports unstable walk-forward optimal periods and weak diversified performance; no performance portability assumed.

## Exact blocker and novelty decision
The GitHub connector fetched README and LICENSE but could not return the large notebook (fetch returned unsupported/too-large, line-range fetch empty). Consequently the actual default EMA period, signal/asset-vol spans, scale, cap, resampling, and rebalance convention are **not yet independently recovered**. No guessed defaults are permitted.
- Novelty status: **PENDING**, not approved. Continuous volatility-normalized position sizing is economically different from binary direction, but the overlap with Sepp continuous EWMA and the prior TSMOM volatility targeting requires exact comparison.
- Source-fidelity status: **NOT YET REPRODUCIBLE** until notebook constants/implementation can be extracted. Do not fabricate a baseline or call an arbitrary configuration source-faithful.
- Specific remedy: obtain the pinned notebook via GitHub blob/API in a runner with appropriate file-size support; extract exact code/constants and notebook SHA; compare against Stage25, family TSMOM and Sepp; record a deterministic novelty decision. If approved, use the existing Delta India 1m runner with completed-candle signal, next 1m open, 0.05%/side + GST, zero first-screen slippage, sequential NAV and reconciliation. Run actual workflow and inspect completed artifacts before claiming any P&L.

## Session counts
One prior sourced candidate advanced through license/provenance checks; zero new distinct historical backtests, zero variants, zero verified new P&L. This is a source-access blocker, not a completed experiment. No main, other-family, VPS or live-trading changes.
