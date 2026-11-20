# High-PF TSMOM boundary audit — 2026-11-20

Status: BLOCKED / INCONCLUSIVE, no valid backtest, no positive expectancy claim.

Verified Actions run: https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/44735120702 completed FAILURE. The `screen` job failed at `Native BTC 2025 screen (fail closed on data gaps)`; the run has zero published artifacts. No step stderr was recovered, so the exact runtime exception is unconfirmed.

Read-only listing of `data/delta_india/BTCUSD/1m` on this branch shows UTC-monthly `2025-01.csv.gz` through `2026-11.csv.gz` and manifest, but **no `2024-12.csv.gz`**. The script only loads `2025-*.csv.gz` and explicitly requires first timestamp no later than 2024-12-31 18:30 UTC to cover the first 2025 IST day. Assuming filenames correspond to UTC monthly data, this condition cannot be satisfied by its current loader. This is a demonstrable implementation/data-boundary blocker independent of the unobserved step stderr. The 60-day momentum warmup also currently begins inside 2025 and does not reproduce full-history upstream signals for January/February. Fix requires authentic 2024-10..12 daily history or a clearly labeled partial-period screen; do not synthesize bars or advertise full 2025 coverage.

Next step: acquire authentic Delta India 2024 boundary and warmup candles, extend loader with verified data and timestamp coverage, then rerun **zero slippage** with both-sided 0.05% fees plus 18% GST. Do not perform 0.5/5-point stress, BTC2026 or ETH until an adequate positive BTC2025 screen. Funding UNMODELED. No other branch, automation, or live trading account changed.
