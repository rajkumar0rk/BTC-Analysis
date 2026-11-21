# Stage 28 — BTCUSD Mean Reversion and Range Trading: after-cost search

Verified successful [GitHub Actions run 44910378125](https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/44910378125), executed 21 November 2026, on **research-only branch** `research/stage28-reversion-range-new-signals-20261121-v1`.

## What was completed

- **10,116** historical 1m-executed strategy configurations across two independent families (**5,184 Mean Reversion and 4,932 Range Trading**).
- Original Stage27 strategies retained as benchmarks, plus new 1H RSI2 recovery, extreme deviation / Bollinger re-entry; 4H Bollinger/RSI2 recovery, and 4H 12/24-bar range-sweep/touch rejection.
- Complete 1H/4H signal bars only, next real 1-minute open entries, first-touch stop-first replay, no use of future candle data in features.
- Delta hypothetical taker 0.05% EACH side, 18% GST on fees, 5 BTC points adverse slippage EACH side. Additional +5bps/side stress applied to each modeled fill. Exact fractional position sizing assumed, 0.5% risk / trade and up to 5× leverage. Futures funding / quoted spread / orderbook / liquidation not modeled.
- Historical Jan 2025–Oct 2026 (22 months), with preselected 2025-only train winners. **2026 was previously researched, so it is NOT an untouched holdout.**
- The same 2025-only objective that preferred 2025 winners did **not** produce robust 2026 results for either family.

## Strict 2025-only selected results

| Family | Exact selected research model | 22m base | 22m +5bps/side | 2025 +5bps | Jan–Oct 2026 +5bps |
| --- | --- | ---: | ---: | ---: | ---: |
| MR | 1H RSI2 recovery, SHORT, aligned H4, 2×ATR SL, 3R, 32h | +1.412% | **−0.652%** | +5.197% | **−5.559%** |
| Range | 1H 48-bar touch, both directions, H4 quiet, 2×ATR SL, 3R, 32h | +4.202% | **+2.849%** | +6.096% | **−3.060%** |

These are the honest results of selection based **only on 2025**. They do **not** demonstrate forward robustness.

## Full-history observed positive cases — retrospective only

The following alternative configurations are **not** selected by the 2025-only ranking. They were identified by inspecting 2025 **and** 2026 outcomes among thousands of trials, i.e. **hindsight selection / data-snooping**. They may fail completely in new data. Configurations are frozen as disabled **BACKTEST_ONLY** JSON at `config/strategies/stage28_mr_range_historical_positive_research_only.json`.

| Hypothesis | Historical trades | 2025 +5bps | Jan–Oct 2026 +5bps | Full 22m +5bps | Positive/losing/flat months |
| --- | ---: | ---: | ---: | ---: | --- |
| **Mean Reversion:** 1H Bollinger reentry, LONG, 4H ADX<=45/eff<=.7, 3×ATR initial SL, target frozen SMA20, max 32h | 66 | +1.650% | +0.613% | **+2.274%** | **9 / 11 / 2** |
| **Range Trading:** 1H prior 48-bar support touch rejection, LONG, 4H ADX<=32/eff<=.5, structural stop, 3R, max 16h | 42 | +4.056% | +1.400% | **+5.513%** | **9 / 7 / 6** |

Mean Reversion's full22 base (without extra 5bps) is **+4.449%**. Range Trading's full22 base is **+9.048%**.

Across 5,184 MR models, **three** with at least 20 training trades had +5bps returns positive in both calendar windows; among 4,932 range models, **29** did. This makes full-history cherry-picking particularly risky. Most tested candidates, and both strictly 2025-selected candidates, failed some key check.

## Portfolio: original 90% Core + 10% Stage26 Donchian

| Synthetic fixed split | Base return / positive months | +5bps stress return / positive months |
| --- | --- | --- |
| **Keep original 90/10; 0% new sleeves** | **+18.785% / 18 of 22** | **+10.206% / 13 of 22** |
| 95% original 90/10 + 5% retrospective MR | +18.035% / 19 | +9.805% / 13 |
| 95% original 90/10 + 5% retrospective Range | +18.291% / 18 | +9.978% / 13 |
| 90% original 90/10 + 5% each retrospective MR/Range | +17.543% / 19 | +9.577% / 13 |

**No consistently better after-cost portfolio was identified**. Treat all such portfolio combinations as mathematically weighted monthly return streams, not full common-account margin/order simulations.

## Decision

- **Do NOT activate live Mean Reversion or Range.** No precommitted 2025-only selection survived the subsequent 2026 cost-stressed check.
- The two specific historical-positive examples are useful for new **forward paper tests**, not claims of a repeatable validated edge.
- The baseline Core + 4H Donchian portfolio remains unchanged. Both historical examples lower its total after-cost return when added.
- New test should use future data **not included in any prior search**, with precommitted entry/exit/stop parameters, minimum trade counts and true contract/margin/funding/mark-book costs.
- The user objective of all months profitable or consistently high monthly returns remains **unmet**.

## Artifacts

Workflow artifact **btc-stage28-new-meanreversion-range-aftercost** contains source-signal rows, all 10,116 config summaries, candidate monthly return streams, strict 2025-only selection, and 2025-only selected portfolio comparison. Source script `scripts/research_stage28_new_reversion_range_20261121.py`.
