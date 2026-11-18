# Stage 18 — Find a monthly-profitable dual-pattern portfolio

## Preserved strategies
Stage14 unchanged and Stage14 + monthly +3R profit lock remain untouched.

## New distinct pattern
Run two *different* strategies in capital-separated sleeves:
(A) 4H range / 1H quiet participation / 15M pullback breakout,
(B) Daily Donchian directional swing breakout. Combine monthly returns
with preallocated capital and monthly rebalance.

## Selection
105 fixed pairings: 7 range/volume controls x 5 daily swing models x 3
weights. Rank ONLY Jan-Dec 2025 profitability (and losing months),
then inspect Jan-Nov 2026 as previously researched chronology.

**2026 is not a pristine OOS period; earlier work already exposed it.**

## Best 2025-ranked mix and chronological 2026 outcome
| name                                                                     | stage15            | stage17                               |   swing_weight |   positive_months_2025 |   losing_months_2025 |   no_exposure_months_2025 |   active_months_2025 |   return_2025_pct |   positive_months_2026 |   losing_months_2026 |   no_exposure_months_2026 |   active_months_2026 |   return_2026_pct |   max_month_end_drawdown_pct |   months_with_positive_return |   months_with_nonpositive_return | perfect_every_month   |
|:-------------------------------------------------------------------------|:-------------------|:--------------------------------------|---------------:|-----------------------:|---------------------:|--------------------------:|---------------------:|------------------:|-----------------------:|---------------------:|--------------------------:|---------------------:|------------------:|-----------------------------:|------------------------------:|---------------------------------:|:----------------------|
| quiet_1h_weekly_3R + 1D_channel_55_ema50_agrees_trail_3atr + swing_75pct | quiet_1h_weekly_3R | 1D_channel_55_ema50_agrees_trail_3atr |           0.75 |                      3 |                    4 |                         5 |                    7 |            1.6714 |                      7 |                    4 |                         0 |                   11 |            0.2122 |                       1.0927 |                            10 |                               13 | False                 |

## Selected portfolio every month
| month_ist   |   range_component_pct |   swing_component_pct |   portfolio_pct |   traded_or_held | status      |
|:------------|----------------------:|----------------------:|----------------:|-----------------:|:------------|
| 2025-01     |              0        |                0      |        0        |                0 | No exposure |
| 2025-02     |              2.00077  |                0      |        0.500194 |                1 | Profit      |
| 2025-03     |              0        |                0      |        0        |                0 | No exposure |
| 2025-04     |             -0.87426  |                0      |       -0.218565 |                1 | Loss        |
| 2025-05     |             -0.37712  |                1.2335 |        0.830845 |                1 | Profit      |
| 2025-06     |             -0.657719 |               -0.5069 |       -0.544605 |                1 | Loss        |
| 2025-07     |              1.72096  |                1.5537 |        1.59552  |                1 | Profit      |
| 2025-08     |              0        |                0      |        0        |                0 | No exposure |
| 2025-09     |             -1.69304  |                0      |       -0.42326  |                1 | Loss        |
| 2025-10     |              0        |                0      |        0        |                0 | No exposure |
| 2025-11     |              0        |                0      |        0        |                0 | No exposure |
| 2025-12     |             -0.250566 |                0      |       -0.062641 |                1 | Loss        |
| 2026-01     |              0.63921  |                0.5385 |        0.563678 |                1 | Profit      |
| 2026-02     |             -0.380323 |                0.6101 |        0.362494 |                1 | Profit      |
| 2026-03     |              0.55539  |                0      |        0.138847 |                1 | Profit      |
| 2026-04     |             -0.950771 |               -0.36   |       -0.507693 |                1 | Loss        |
| 2026-05     |              0.201669 |                0.0861 |        0.114992 |                1 | Profit      |
| 2026-06     |              1.36439  |                0.0354 |        0.367648 |                1 | Profit      |
| 2026-07     |             -2.01319  |                0      |       -0.503296 |                1 | Loss        |
| 2026-08     |             -3.17673  |                0.8362 |       -0.167033 |                1 | Loss        |
| 2026-09     |              0        |               -0.5321 |       -0.399075 |                1 | Loss        |
| 2026-10     |              0        |                0.0528 |        0.0396   |                1 | Profit      |
| 2026-11     |              0        |                0.2781 |        0.208575 |                1 | Profit      |

## Top 2025-selected candidate pairings
| name   | stage15   | stage17   | swing_weight   | positive_months_2025   | losing_months_2025   | no_exposure_months_2025   | return_2025_pct   | positive_months_2026   | losing_months_2026   | no_exposure_months_2026   | return_2026_pct   | max_month_end_drawdown_pct   |
|--------|-----------|-----------|----------------|------------------------|----------------------|---------------------------|-------------------|------------------------|----------------------|---------------------------|-------------------|------------------------------|

## Research caveats
- 2026 has been researched repeatedly before, so not a pristine unseen holdout
- Independent portfolios can hold positions simultaneously; needs capital and margin for both
- Stage15 swing-independent trade ledger is compounded on EXIT IST month, Stage17 marks active exposure at IST month end
- Blended NAV assumes monthly rebalancing and exact fractional risk sizing, without cross margin constraints or transaction costs of rebalancing
- The Stage15 input uses historical Stage14-derived condition and weekly loss gate; selection is exploratory
- Portfolio trading fees/GST/slippage are taken from underlying simulations, not separately charged
- Historical 2026-10-31 missing, November 2026 partial
- Historical data reused; rank selection among 105 candidates is susceptible to multiple comparison bias
- Never interpret a profitable historical month as guaranteed future monthly profit
- No real order-book slippage, funding payments, liquidation or margin modeled

Reproduction: python scripts/research_monthly_portfolio_stage18.py
--stage15-ledger <original Stage15 artifact CSV.gz>.
