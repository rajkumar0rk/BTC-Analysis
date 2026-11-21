# Stage32 — Improve BTC Mean Reversion and Range Trading using causal 1-minute exits

## Status

Successful initial [GitHub Actions run 44914817983](https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/44914817983); reproducibility and complete summary re-run [44914969974](https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/44914969974). Research branch only; no live actions.

**2000 independent exit-model tests**: Four frozen signal cohorts × five initial 1H ATR stops (2 / 2.5 / 3 / 3.5 / 4) × five target rules (1.5R, 2R, 3R, 4R, signal-frozen mean) × four maximum holding windows (8, 16, 32, 48 hours) × five profit-stop modes (none, breakeven at 1R, lock +0.5R after 1.5R, trail 1.5R at 1R, trail 2R at 1R).

- 989,280 actual BTCUSD 1-minute source bars, zero missing minutes in this archive, Jan 2025–Nov 18 2026. Backtest uses 22 *complete* months Jan 2025–Oct 2026. Partial November shown only as caution, not a complete monthly result.
- 1H signals and 4H trend/range conditions computed only from fully completed bars; fill next available 1m open.
- **Stops always check first** when 1m stop and profit-target levels both touch; trailing-stop updates based on a minute's favorable extreme only become active **the following minute**. No future low/high lookahead to claim favorable exits.
- Delta research cost: taker fee 0.05% each side plus 18% GST on fees, initial 5 BTC points adverse slip each side; all emphasized results **also add 5 basis points more adverse slippage EACH leg**.
- Nominal capital risk fraction up to 0.5%/initial-R, bounded by 5× notional per strategy. Does NOT model exchange lot rounding, margin, funding, observed spreads or bankruptcy in shared portfolio.
- Parameters of the *exit* only selected using 2025, requiring at least 15 trades and positive +5bps stressed returns in both six-month 2025 halves, then ranking net profit less drawdown. All 2026 outcomes are separately **historically research-exposed**, NOT pristine forward holdout.
- **Critical:** The frozen *post-hoc source entry templates* had already been selected after examining 2026, so the new 2025 exit selection cannot make their total strategy performance out-of-sample.

## Selected exit configurations — added 5bps adverse slippage per side

| Cohort | Prior rule | Previous 2025 / 2026 / overall | 2025-only selected exit | Updated 2025 / 2026 / overall | Decision |
|---|---|---|---|---|---|
| Mean Reversion, historically tuned entry | 3× ATR stop, frozen SMA20 target, 32h | +1.073% / +1.571% / +2.662% | **UNCHANGED** | **+1.073% / +1.571% / +2.662%** | No robust improvement in exit; retain original research hypothesis |
| Range Trading, historically tuned entry | 3× ATR stop, frozen range midpoint target, 32h | +4.056% / +4.043% / +8.263% | **Same, hold 48h** | **+4.057% / +4.556% / +8.798%** | Research-only improved historical result |
| Mean Reversion, *strict 2025-selected entry* | 3× ATR stop, 3R target, 32h | +4.775% / **−1.705%** / +2.988% | 2.5× ATR stop, 4R target, 48h | +7.704% / **−2.985%** / +4.489% | 2026 got WORSE; reject as robust |
| Range Trading, *strict 2025-selected entry* | 2× ATR stop, 3R target, 32h | +6.096% / **−3.060%** / +2.849% | Add 2R trailing stop activation after +1R | +7.655% / **−5.057%** / +2.211% | 2026 got WORSE; reject as robust |

**Takeaway:** Better 2025 in-sample exit performance does **not** reliably transfer to 2026. Explicit after-cost backtesting found one small gain on a prior post-hoc entry (Range 32h -> 48h) but did not solve genuine forward-validation for either family.

## Standalone vs 50/50 synthetic monthly blend

| 22 months, additional adverse 5bps each side | Old | Revised |
|---|---:|---:|
| Mean Reversion | +2.662% | **+2.662%** |
| Range Trading | +8.263% | **+8.798%** |
| Synthetic 50/50 monthly MR+Range blend | +5.445% | **+5.704%** |
| 50/50 profitable months | 16/22 | **16/22** |
| 50/50 calendar 2025 | +2.567% | +2.565% |
| 50/50 Jan–Oct 2026 | +2.806% | +3.060% |

These 50/50 figures result from fixed weights on independently modeled strategy month returns. They are NOT a shared BTC Futures margin / contract-level combined replay; concurrent positions and effective leverage could differ in practice.

## November diagnostic and independent verification

Previously frozen source replay exactly reproduced Stage30/31 baseline per-cohort returns as assertions. The source contains BTC candles only through November 18, 2026. Under +5bps/leg, the historically tuned Mean Reversion candidate has **one November trade, +0.279%**, and Range Trading has **one November trade, −0.553%**; the added hold did not change those two trade outcomes. This is too little genuinely recent data to validate either.

## Recommendations

1. **Do not allocate real money** or treat all 22 months as new out-of-sample evidence.
2. Keep Stage31 Mean Reversion rules (no 2025-only exit improvement found).
3. Archive the proposed **48h hold** Range Trading variant as a research hypothesis, alongside original 32h for independent prospective comparison.
4. Preserve at least one truly unseen period and collect enough new trades to estimate costs and edge. Do not repeatedly backfill future negative months with historical tuning.
5. Once prospective results exist, use an integrated shared-capital, exchange-cost simulation with funding, contract increments and liquidity before live deployment.

## Artifacts

Workflow artifact `btc-stage32-causal-mr-range-exit-comparison`: `full_exit_grid.csv`, `frozen_vs_2025selected_monthly.csv`, four winning-variant trade ledgers, and `summary.json`. Research code `scripts/research_stage32_causal_exit_20261121.py`, disabled config `config/strategies/stage32_mr_range_updated_research_only.json`.
