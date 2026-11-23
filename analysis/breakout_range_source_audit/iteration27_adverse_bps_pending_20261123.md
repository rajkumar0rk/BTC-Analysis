# Breakout/Range iteration 11 — adverse bps replay (2026-11-23 IST)

Branch: research/breakout-range-source-audit-20261121. Commit a754910cb0c40bb0b57f84d271a738b0fbe251e1.

Immutable source: https://github.com/zty05070242/wavelet-2b/tree/5d879b3d04031952f41d2b4d4c4a3cce43f04150 (MIT), SI=F daily. Baselines preserved: TwoB and WaveletTwoB at matched 0.5% risk/3x cap and source 2% risk/20x cap. Existing 0.5 and 5 USD point slippage preserved. New preregistered robustness checks: WaveletTwoB matched-risk, 10 and 25 basis points adverse fill price per executed side, applied to entry and exit, fees 0.05% per side + 18% GST, zero funding assumed nowhere (funding unmodeled). This is price-scaled execution stress, not a new strategy and not a 2025 optimization. These large adverse stresses deliberately test whether rare winner profits survive materially worse fills.

Historical workflow run https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/45110977389, job 137483010968, initially IN_PROGRESS at checkout. Archive verification run https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/45110977382, jobs 137483011088 and 137483011550. Pending: poll to COMPLETED; retrieve artifact and compare prior six Wavelet baselines + TwoB controls unchanged; reconcile trade sums, monthly NAV and stop/gap fills. Do not report new profit until artifact verified. Earlier run 45098672933 success is previous commit only.

Causal caveat: upstream signal parity is an independent translation rather than execution of upstream library; stop/exit event-level parity and spread/funding/L2/lot granularity remain unresolved. No live orders or protected branch changes.
