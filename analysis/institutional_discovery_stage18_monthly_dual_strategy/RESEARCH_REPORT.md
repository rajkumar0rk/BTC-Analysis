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
| quiet_1h_weekly_3R + 1D_channel_55_ema50_agrees_trail_3atr + swing_25pct | quiet_1h_weekly_3R | 1D_channel_55_ema50_agrees_trail_3atr |           0.25 |                      9 |                    1 |                         2 |                   10 |            4.7359 |                      6 |                    3 |                         2 |                    9 |            5.0762 |                       1.3244 |                            15 |                                8 | False                 |

## Selected portfolio every month
| month_ist   |   range_component_pct |   swing_component_pct |   portfolio_pct |   traded_or_held | status      |
|:------------|----------------------:|----------------------:|----------------:|-----------------:|:------------|
| 2025-01     |              0        |                0      |        0        |                0 | No exposure |
| 2025-02     |              1.53694  |                0      |        1.1527   |                1 | Profit      |
| 2025-03     |              0        |                0      |        0        |                0 | No exposure |
| 2025-04     |              1.80436  |                0      |        1.35327  |                1 | Profit      |
| 2025-05     |             -0.152482 |                0.5311 |        0.018413 |                1 | Profit      |
| 2025-06     |              0.729788 |                0.0962 |        0.571391 |                1 | Profit      |
| 2025-07     |              0.376417 |                0.2204 |        0.337413 |                1 | Profit      |
| 2025-08     |              0.920149 |               -0.5136 |        0.561712 |                1 | Profit      |
| 2025-09     |              0.510266 |                0      |        0.3827   |                1 | Profit      |
| 2025-10     |              0.794506 |                0      |        0.59588  |                1 | Profit      |
| 2025-11     |              0.834213 |                0.3093 |        0.702985 |                1 | Profit      |
| 2025-12     |             -1.34647  |               -0.0393 |       -1.01968  |                1 | Loss        |
| 2026-01     |             -0.23945  |               -0.5129 |       -0.307812 |                1 | Loss        |
| 2026-02     |              3.47239  |                0.6805 |        2.77441  |                1 | Profit      |
| 2026-03     |              2.668    |                0      |        2.001    |                1 | Profit      |
| 2026-04     |              0.353094 |               -0.0862 |        0.24327  |                1 | Profit      |
| 2026-05     |              0.328738 |               -0.2743 |        0.177978 |                1 | Profit      |
| 2026-06     |             -0.316307 |                0.1176 |       -0.20783  |                1 | Loss        |
| 2026-07     |              0        |                0      |        0        |                0 | No exposure |
| 2026-08     |              0        |                1.6952 |        0.4238   |                1 | Profit      |
| 2026-09     |              0        |               -0.5596 |       -0.1399   |                1 | Loss        |
| 2026-10     |              0        |                0.1854 |        0.04635  |                1 | Profit      |
| 2026-11     |              0        |                0      |        0        |                0 | No exposure |

## Top 2025-selected candidate pairings
| name                                                                             | stage15                 | stage17                                  |   swing_weight |   positive_months_2025 |   losing_months_2025 |   no_exposure_months_2025 |   return_2025_pct |   positive_months_2026 |   losing_months_2026 |   no_exposure_months_2026 |   return_2026_pct |   max_month_end_drawdown_pct |
|:---------------------------------------------------------------------------------|:------------------------|:-----------------------------------------|---------------:|-----------------------:|---------------------:|--------------------------:|------------------:|-----------------------:|---------------------:|--------------------------:|------------------:|-----------------------------:|
| quiet_1h_weekly_3R + 1D_channel_55_ema50_agrees_trail_3atr + swing_25pct         | quiet_1h_weekly_3R      | 1D_channel_55_ema50_agrees_trail_3atr    |           0.25 |                      9 |                    1 |                         2 |            4.7359 |                      6 |                    3 |                         2 |            5.0762 |                       1.3244 |
| quiet_1h_daily2_weekly3 + 1D_channel_55_ema50_agrees_trail_3atr + swing_25pct    | quiet_1h_daily2_weekly3 | 1D_channel_55_ema50_agrees_trail_3atr    |           0.25 |                      9 |                    1 |                         2 |            4.7359 |                      6 |                    3 |                         2 |            5.0762 |                       1.3244 |
| quiet_1h_weekly_3R + 1D_channel_20_ema50_agrees_trail_3atr + swing_25pct         | quiet_1h_weekly_3R      | 1D_channel_20_ema50_agrees_trail_3atr    |           0.25 |                      9 |                    1 |                         2 |            4.5274 |                      7 |                    3 |                         1 |            5.4128 |                       1.1332 |
| quiet_1h_daily2_weekly3 + 1D_channel_20_ema50_agrees_trail_3atr + swing_25pct    | quiet_1h_daily2_weekly3 | 1D_channel_20_ema50_agrees_trail_3atr    |           0.25 |                      9 |                    1 |                         2 |            4.5274 |                      7 |                    3 |                         1 |            5.4128 |                       1.1332 |
| quiet_1h_weekly_3R + 1D_channel_20_ema50_agrees_trail_4atr + swing_25pct         | quiet_1h_weekly_3R      | 1D_channel_20_ema50_agrees_trail_4atr    |           0.25 |                      9 |                    1 |                         2 |            4.4673 |                      7 |                    3 |                         1 |            5.4371 |                       1.1332 |
| quiet_1h_daily2_weekly3 + 1D_channel_20_ema50_agrees_trail_4atr + swing_25pct    | quiet_1h_daily2_weekly3 | 1D_channel_20_ema50_agrees_trail_4atr    |           0.25 |                      9 |                    1 |                         2 |            4.4673 |                      7 |                    3 |                         1 |            5.4371 |                       1.1332 |
| quiet_1h_weekly_3R + 1D_channel_20_no_trend_filter_trail_3atr + swing_25pct      | quiet_1h_weekly_3R      | 1D_channel_20_no_trend_filter_trail_3atr |           0.25 |                      9 |                    1 |                         2 |            4.2616 |                      8 |                    2 |                         1 |            5.587  |                       1.0197 |
| quiet_1h_daily2_weekly3 + 1D_channel_20_no_trend_filter_trail_3atr + swing_25pct | quiet_1h_daily2_weekly3 | 1D_channel_20_no_trend_filter_trail_3atr |           0.25 |                      9 |                    1 |                         2 |            4.2616 |                      8 |                    2 |                         1 |            5.587  |                       1.0197 |
| quiet_1h_weekly_3R + 1D_channel_20_no_trend_filter_trail_4atr + swing_25pct      | quiet_1h_weekly_3R      | 1D_channel_20_no_trend_filter_trail_4atr |           0.25 |                      9 |                    1 |                         2 |            4.2018 |                      8 |                    2 |                         1 |            5.6114 |                       1.0197 |
| quiet_1h_daily2_weekly3 + 1D_channel_20_no_trend_filter_trail_4atr + swing_25pct | quiet_1h_daily2_weekly3 | 1D_channel_20_no_trend_filter_trail_4atr |           0.25 |                      9 |                    1 |                         2 |            4.2018 |                      8 |                    2 |                         1 |            5.6114 |                       1.0197 |
| quiet_1h_weekly_3R + 1D_channel_55_ema50_agrees_trail_3atr + swing_50pct         | quiet_1h_weekly_3R      | 1D_channel_55_ema50_agrees_trail_3atr    |           0.5  |                      9 |                    1 |                         2 |            3.3469 |                      6 |                    3 |                         2 |            3.7912 |                       1.0665 |
| quiet_1h_daily2_weekly3 + 1D_channel_55_ema50_agrees_trail_3atr + swing_50pct    | quiet_1h_daily2_weekly3 | 1D_channel_55_ema50_agrees_trail_3atr    |           0.5  |                      9 |                    1 |                         2 |            3.3469 |                      6 |                    3 |                         2 |            3.7912 |                       1.0665 |

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
