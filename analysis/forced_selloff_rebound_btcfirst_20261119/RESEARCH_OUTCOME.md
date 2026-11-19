# BTC-first forced-selloff rebound — completed negative experiment (2026-11-19)

Run: https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/44475734603
Artifact: https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/44475734603/artifacts/14505609562

Hypothesis fixed before test: a >=2.5% BTC hourly decline on >=3x preceding 720-hour rolling median volume reflects transient forced-selling inventory; next-hour LONG, 1.5% stop, 5% trailing, 72-hour time exit, 25% allocation. Reverse SHORT placebo. Same parameters frozen for ETH secondary validation. Taker 0.05% per side +18% GST, 0.05% adverse slippage each side. Funding omitted, hourly execution approximated, no historical L2 or observed liquidations.

| Market | Variant | Trades | Win rate | Average win/loss | PF | Biggest R | 2025 net | 2026 partial net | Total net | Max DD |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| BTC | rebound | 14 | 35.7% | 2.50 | 1.387 | 5.01 | +0.11% | +1.33% | +1.45% | 2.58% |
| BTC | continuation placebo | 13 | 23.1% | 2.21 | 0.662 | 3.81 | -0.87% | -0.47% | -1.33% | 2.37% |
| ETH | frozen rebound | 71 | 28.2% | 3.27 | 1.281 | 11.04 | +5.33% | +0.91% | +6.29% | 7.91% |
| ETH | frozen continuation placebo | 60 | 23.3% | 1.90 | 0.578 | 5.39 | -5.17% | -3.61% | -8.59% | 9.98% |

BTC positive months 4/8 months with exits; removing largest winner turns BTC total net negative (-0.42%). ETH positive months 10/18 months with exits; removing largest winner leaves +2.06%. These are exit-month statistics, NOT a complete marked-to-market monthly equity return series. The BTC test was not split into a clean untouched 2026 holdout for parameter discovery because parameters were predeclared and not optimized. No retuning on ETH. The hypothesis FAILS the requested thresholds: BTC <30 trades, win/loss <5, PF <1.5, no >=10R winner, far below >500% annual return. Reject as qualifying strategy; do not alert. Further research should explore a different economic mechanism rather than tweak thresholds to fit this sample.
