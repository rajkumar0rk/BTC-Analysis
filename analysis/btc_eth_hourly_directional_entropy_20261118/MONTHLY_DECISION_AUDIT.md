# Stage: BTC and ETH hourly directional-entropy paired audit — 18 November 2026

## Decision: no qualifying discovery; no notification

New predeclared causal filter: prior 48 fully closed 1-hour candles' direction-flip fraction from 0.35 through 0.55, shifted one complete hourly close before entries. Applied identically to the existing 52 entry families and 205 parameter combinations per market. 410 paired-market simulations completed. This is a NEW FILTER, not a new entry family.

No candidate reached >+500% in the full 2025 year. The strongest monthly-consistency candidate with at least 80 trades had only 8 of 22 high-PF/positive months, and no months with +5% net account return. Not enough for a high-monthly-PF/high-return claim or an independent promising-candidate alert.

## Illustrative candidate, not validated or worth live deployment

**4H engulfing reversal; 1.5 ATR(14) stop; 3R target; 72-hour maximum hold; 0.5% equity risk per stop, 3x notional cap; one open position; stop-first 1m execution.** Identical BTC and ETH rules.

| Metric | BTCUSD | ETHUSD |
|---|---:|---:|
| Overall PF | 0.623 | 1.175 |
| Total net account return, 22 months | -20.42% | 7.09% |
| Full 2025 net compounded return | -11.17% | 4.38% |
| 2026 Jan–Oct YTD net compounded return (NOT annual) | -10.41% | 2.60% |
| Positive / negative months | 6 / 16 | 14 / 8 |
| Strong PF >=1.5, positive, >=3 trades | 3 | 8 |
| Months net >=5%, >=10%, >=20% | 0, 0, 0 | 0, 0, 0 |
| Trades / wins / losses | 173 / 48 / 125 | 148 / 63 / 85 |
| Max closed-trade drawdown | -21.67% | -5.12% |

## Every IST month: net return / PF / trades (wins/losses)

| Month | BTCUSD | ETHUSD |
|---|---|---|
| 2025-01 | -0.98% / 0.39 / 6 (2W/4L) | 0.61% / 1.51 / 5 (2W/3L) |
| 2025-02 | -0.39% / 0.88 / 9 (2W/7L) | 0.61% / 1.46 / 6 (3W/3L) |
| 2025-03 | 2.65% / 7.33 / 5 (3W/2L) | 0.69% / 1.67 / 5 (3W/2L) |
| 2025-04 | -1.87% / 0.24 / 8 (1W/7L) | -1.45% / 0.34 / 8 (3W/5L) |
| 2025-05 | -0.75% / 0.80 / 12 (5W/7L) | -2.39% / 0.23 / 9 (3W/6L) |
| 2025-06 | -4.04% / 0.06 / 10 (2W/8L) | -0.18% / 0.94 / 10 (4W/6L) |
| 2025-07 | -2.09% / 0.45 / 10 (3W/7L) | 2.17% / 2.36 / 7 (3W/4L) |
| 2025-08 | -1.08% / 0.66 / 8 (2W/6L) | 0.87% / 1.33 / 9 (4W/5L) |
| 2025-09 | -0.52% / 0.79 / 7 (2W/5L) | 0.71% / 1.60 / 6 (3W/3L) |
| 2025-10 | 1.90% / 1.59 / 11 (5W/6L) | 1.86% / 2.14 / 7 (4W/3L) |
| 2025-11 | -0.49% / 0.69 / 5 (2W/3L) | 1.11% / 9.07 / 4 (2W/2L) |
| 2025-12 | -3.91% / 0.00 / 8 (0W/8L) | -0.23% / 0.89 / 7 (3W/4L) |
| 2026-01 | -3.69% / 0.00 / 9 (1W/8L) | 1.38% / 1.64 / 8 (4W/4L) |
| 2026-02 | 0.43% / 1.23 / 7 (3W/4L) | 3.33% / ∞ / 4 (4W/0L) |
| 2026-03 | -3.86% / 0.02 / 9 (1W/8L) | -0.23% / 0.90 / 7 (2W/5L) |
| 2026-04 | -0.96% / 0.29 / 6 (2W/4L) | -0.98% / 0.07 / 3 (1W/2L) |
| 2026-05 | -1.20% / 0.51 / 7 (1W/6L) | -1.92% / 0.11 / 5 (1W/4L) |
| 2026-06 | 0.38% / 1.12 / 11 (4W/7L) | 0.47% / 1.15 / 11 (5W/6L) |
| 2026-07 | 2.01% / 2.19 / 7 (4W/3L) | 0.66% / 1.37 / 7 (3W/4L) |
| 2026-08 | 0.48% / 1.17 / 9 (3W/6L) | -1.04% / 0.11 / 5 (1W/4L) |
| 2026-09 | -1.15% / 0.00 / 3 (0W/3L) | 0.79% / 1.37 / 7 (2W/5L) |
| 2026-10 | -3.19% / 0.00 / 6 (0W/6L) | 0.20% / 1.09 / 8 (3W/5L) |

Monthly PF is the ratio of the sum of positive after-cost trade USD PnLs to the absolute sum of negative after-cost trade USD PnLs. A no-loss month has infinite PF; PF below one indicates net losing trades. All results are modeled, not real fills.

## Data and execution caveats

Source native BTC and ETH 1m Delta India history; Jan 2025 IST first 5.5h absent, October 2026 source repair is in the existing archive and manifest checks. No Nov 2026. 2026 has previously been inspected and is not pristine out-of-sample. 0.05% taker each side plus 18% GST, BTC 5 points adverse slippage each side, ETH 0.02% price-relative slippage each side. Funding, actual spreads, order impact, lot size, margin and liquidation are NOT modeled. Drawdown is based on closed trades and may understate intratrade risk. Model-selection and repeated research create multiple-testing bias. No live trading was changed.

Full machine-readable results: paired_all_model_summary.csv, paired_all_model_monthly.csv, monthly_milestones.csv, yearly_2025_and_ytd_2026.csv, candidate_trade_ledgers.csv, quality.json. GitHub Actions run: https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/44304600764
