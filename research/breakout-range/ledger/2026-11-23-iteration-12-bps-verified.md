# Breakout-range iteration 12 — 2026-11-23 IST

State: VERIFIED_COMPLETED_HISTORICAL_BPS_STRESS; no new distinct strategy and not live-ready.

Source zty05070242/wavelet-2b pinned at 5d879b3d04031952f41d2b4d4c4a3cce43f04150. Isolated research branch research/breakout-range-source-audit-20261121; replay commit a754910cb0c40bb0b57f84d271a738b0fbe251e1. Historical run https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/45110977389 completed SUCCESS; job 137483010968 completed SUCCESS; archive audit https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/45110977382 completed SUCCESS. Artifact 14789910968, GitHub digest sha256:1331a39a1a6d34ad7ebb336f68ba5d55c16af3fa0d7ccfcb0c26eef1af26d66f. Downloaded artifact ZIP and independently parsed summary, all 10 trade CSVs and 10 monthly NAV CSVs. Across all 10, trade count, sum of net trade P&L, fee+GST total and final monthly NAV reconcile to summary to floating-point precision. Original 8 control configurations reproduce prior results.

| Matched-risk Wavelet-2B configuration | Trades | Winners | Net USD / 10000 | Net return | PF | Max DD |
|---|---:|---:|---:|---:|---:|---:|
| Zero slippage | 15 | 4 | +313.6308 | +3.1363% | 1.5357 | -4.6297% |
| $0.50 per side | 15 | 4 | +313.2080 | +3.1321% | 1.5348 | -4.6297% |
| $5.00 per side | 15 | 4 | +309.4136 | +3.0941% | 1.5274 | -4.6301% |
| 10 bps adverse per side | 15 | 4 | +244.9602 | +2.4496% | 1.4050 | -4.6241% |
| 25 bps adverse per side | 15 | 4 | +152.9397 | +1.5294% | 1.2428 | -4.6174% |

All results include 0.05% per-side trading fee plus 18% GST; funding, spread, L2, lot/tick, margin/liquidation remain unmodeled. Source sizing zero-slip +11.4063% and -17.1380% DD is a sizing sensitivity, not an improved signal. Both original TwoB controls are net negative. 23 monthly IST rows with two partial months: only 21 complete; 6 positive, 6 negative, 9 flat for Wavelet. No frozen ETH test. 2026 data previously researched and not pristine. The four winners make the result fragile; higher bps slippage reduces PF materially. Stop/exit fidelity still needs dedicated validation.

This iteration: 0 new sources, 0 new distinct strategies, 2 newly completed slippage variants, 0 new parameter-search variants, 1 completed historical run and 1 archive audit; no live trading or protected branch edits. Next: source-faithful stop/exit audit and frozen ETH if archive available; source-screen novel candidates in separate preregistered batches. Do not infer 22/22 profitable months or live viability.
