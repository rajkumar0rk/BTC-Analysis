# Stage20 — Add new hourly pattern to preserved Stage18

## Baseline frozen
Stage18 unchanged: 75% 1H quiet-volume pullback, 25% Daily 20 Donchian swing.

## New model search
140 Stage19 hourly strategies, combined with only 10%, 15%, or 20%
auxiliary capital (420 cases). All historical monthly net returns include
standard taker fees, GST and assumed 5-point adverse slippage per leg.

## Frozen original and best selected by 2025 (then 2026 recheck)
| model                     |   profitable_2025 |   losing_2025 |   idle_2025 |   return_2025_pct |   profitable_2026 |   losing_2026 |   idle_2026 |   return_2026_pct |   max_month_end_dd | variant                                                              | stage19_model                                        |   new_pattern_weight |   quiet_volume_weight |   daily20_weight |   month_end_max_drawdown_pct |   all23_positive |
|:--------------------------|------------------:|--------------:|------------:|------------------:|------------------:|--------------:|------------:|------------------:|-------------------:|:---------------------------------------------------------------------|:-----------------------------------------------------|---------------------:|----------------------:|-----------------:|-----------------------------:|-----------------:|
| Original Stage18          |                 3 |             5 |           4 |         0.0612637 |                 6 |             5 |           0 |          -2.29864 |            4.12124 | nan                                                                  | nan                                                  |                nan   |                 nan   |            nan   |                    nan       |              nan |
| New Stage20 2025 selected |                 9 |             3 |           0 |         1.62596   |                 5 |             6 |           0 |          -3.23403 |          nan       | overextension_reversal__4h_atr_ratio_le1__2R__480min + auxiliary 20% | overextension_reversal__4h_atr_ratio_le1__2R__480min |                  0.2 |                   0.6 |              0.2 |                      3.95564 |                0 |

## 2025 selected candidate monthly results
| month_ist   |   stage18_month_pct |   stage19_month_pct |   portfolio_month_pct | state   |
|:------------|--------------------:|--------------------:|----------------------:|:--------|
| 2025-01     |            0        |              0.6099 |              0.12198  | Profit  |
| 2025-02     |            1.50058  |             -1.6168 |              0.877105 | Profit  |
| 2025-03     |            0        |              0.8556 |              0.17112  | Profit  |
| 2025-04     |           -0.655695 |              3.1511 |              0.105664 | Profit  |
| 2025-05     |            0.025535 |             -0.8981 |             -0.159192 | Loss    |
| 2025-06     |           -0.705614 |              2.1227 |             -0.139951 | Loss    |
| 2025-07     |            1.7274   |             -1.6676 |              1.0484   | Profit  |
| 2025-08     |            0        |              0.101  |              0.0202   | Profit  |
| 2025-09     |           -1.23895  |             -1.4904 |             -1.28924  | Loss    |
| 2025-10     |           -0.238525 |              1.0975 |              0.02868  | Profit  |
| 2025-11     |            0        |              1.8335 |              0.3667   | Profit  |
| 2025-12     |           -0.314399 |              3.6647 |              0.481421 | Profit  |
| 2026-01     |            0.723883 |             -1.0782 |              0.363466 | Profit  |
| 2026-02     |           -0.202843 |              2.0347 |              0.244666 | Profit  |
| 2026-03     |            0.289942 |             -8.5105 |             -1.47015  | Loss    |
| 2026-04     |           -0.694104 |              1.5376 |             -0.247763 | Loss    |
| 2026-05     |            0.283927 |             -0.0252 |              0.222102 | Profit  |
| 2026-06     |            1.03214  |             -0.2012 |              0.785475 | Profit  |
| 2026-07     |           -1.48801  |             -0.9169 |             -1.37379  | Loss    |
| 2026-08     |           -2.1735   |              1.1372 |             -1.51136  | Loss    |
| 2026-09     |           -0.133025 |             -1.4884 |             -0.4041   | Loss    |
| 2026-10     |            0.0132   |              2.832  |              0.57696  | Profit  |
| 2026-11     |            0.069525 |             -2.4432 |             -0.43302  | Loss    |

**Historical all-month profitable models: 0/420**

## Top 2025-ranked alternatives
| variant                                                              | stage19_model                                        |   new_pattern_weight |   quiet_volume_weight |   daily20_weight |   profitable_2025 |   losing_2025 |   idle_2025 |   return_2025_pct |   profitable_2026 |   losing_2026 |   idle_2026 |   return_2026_pct |   month_end_max_drawdown_pct | all23_positive   |
|:---------------------------------------------------------------------|:-----------------------------------------------------|---------------------:|----------------------:|-----------------:|------------------:|--------------:|------------:|------------------:|------------------:|--------------:|------------:|------------------:|-----------------------------:|:-----------------|
| overextension_reversal__4h_atr_ratio_le1__2R__480min + auxiliary 20% | overextension_reversal__4h_atr_ratio_le1__2R__480min |                 0.2  |                0.6    |           0.2    |                 9 |             3 |           0 |           1.62596 |                 5 |             6 |           0 |          -3.23403 |                      3.95564 | False            |
| overextension_reversal__4h_atr_ratio_le1__3R__480min + auxiliary 20% | overextension_reversal__4h_atr_ratio_le1__3R__480min |                 0.2  |                0.6    |           0.2    |                 8 |             4 |           0 |           2.27237 |                 4 |             7 |           0 |          -4.1239  |                      4.66722 | False            |
| overextension_reversal__4h_atr_ratio_le1__3R__480min + auxiliary 15% | overextension_reversal__4h_atr_ratio_le1__3R__480min |                 0.15 |                0.6375 |           0.2125 |                 8 |             4 |           0 |           1.71742 |                 4 |             7 |           0 |          -3.66652 |                      4.33217 | False            |
| ema20_pullback_confirm__4h_atr_ratio_le1__3R__240min + auxiliary 20% | ema20_pullback_confirm__4h_atr_ratio_le1__3R__240min |                 0.2  |                0.6    |           0.2    |                 8 |             4 |           0 |           1.66389 |                 3 |             8 |           0 |          -4.39658 |                      5.20243 | False            |
| ema20_pullback_confirm__4h_atr_ratio_le1__3R__240min + auxiliary 15% | ema20_pullback_confirm__4h_atr_ratio_le1__3R__240min |                 0.15 |                0.6375 |           0.2125 |                 8 |             4 |           0 |           1.26271 |                 4 |             7 |           0 |          -3.8754  |                      4.82303 | False            |
| overextension_reversal__4h_atr_ratio_le1__3R__480min + auxiliary 10% | overextension_reversal__4h_atr_ratio_le1__3R__480min |                 0.1  |                0.675  |           0.225  |                 8 |             4 |           0 |           1.16392 |                 4 |             7 |           0 |          -3.20984 |                      4.25884 | False            |
| ema20_pullback_confirm__4h_atr_ratio_le1__3R__240min + auxiliary 10% | ema20_pullback_confirm__4h_atr_ratio_le1__3R__240min |                 0.1  |                0.675  |           0.225  |                 8 |             4 |           0 |           0.86188 |                 4 |             7 |           0 |          -3.35202 |                      4.44245 | False            |
| ema20_pullback_confirm__all__3R__240min + auxiliary 20%              | ema20_pullback_confirm__all__3R__240min              |                 0.2  |                0.6    |           0.2    |                 8 |             4 |           0 |           0.68991 |                 2 |             9 |           0 |          -5.71047 |                      6.7732  | False            |
| ema20_pullback_confirm__all__3R__240min + auxiliary 15%              | ema20_pullback_confirm__all__3R__240min              |                 0.15 |                0.6375 |           0.2125 |                 8 |             4 |           0 |           0.53403 |                 4 |             7 |           0 |          -4.86701 |                      6.00709 | False            |
| ema20_pullback_confirm__all__3R__240min + auxiliary 10%              | ema20_pullback_confirm__all__3R__240min              |                 0.1  |                0.675  |           0.225  |                 8 |             4 |           0 |           0.37729 |                 4 |             7 |           0 |          -4.01724 |                      5.23687 | False            |
| ema20_pullback_confirm__all__2R__240min + auxiliary 15%              | ema20_pullback_confirm__all__2R__240min              |                 0.15 |                0.6375 |           0.2125 |                 8 |             4 |           0 |          -0.15214 |                 3 |             8 |           0 |          -4.18294 |                      5.94583 | False            |
| ema20_pullback_confirm__all__2R__240min + auxiliary 20%              | ema20_pullback_confirm__all__2R__240min              |                 0.2  |                0.6    |           0.2    |                 8 |             4 |           0 |          -0.22452 |                 2 |             9 |           0 |          -4.80476 |                      6.69058 | False            |
| ema20_pullback_confirm__4h_adx_le20__3R__240min + auxiliary 20%      | ema20_pullback_confirm__4h_adx_le20__3R__240min      |                 0.2  |                0.6    |           0.2    |                 7 |             4 |           1 |           1.24403 |                 5 |             6 |           0 |          -3.81629 |                      4.49444 | False            |
| ema20_pullback_confirm__4h_adx_le20__3R__480min + auxiliary 20%      | ema20_pullback_confirm__4h_adx_le20__3R__480min      |                 0.2  |                0.6    |           0.2    |                 7 |             4 |           1 |           1.23655 |                 5 |             6 |           0 |          -4.18767 |                      4.79462 | False            |
| ema20_pullback_confirm__4h_adx_le20__3R__240min + auxiliary 15%      | ema20_pullback_confirm__4h_adx_le20__3R__240min      |                 0.15 |                0.6375 |           0.2125 |                 7 |             4 |           1 |           0.9491  |                 5 |             6 |           0 |          -3.43856 |                      4.39634 | False            |
| ema20_pullback_confirm__4h_adx_le20__3R__480min + auxiliary 15%      | ema20_pullback_confirm__4h_adx_le20__3R__480min      |                 0.15 |                0.6375 |           0.2125 |                 7 |             4 |           1 |           0.94359 |                 5 |             6 |           0 |          -3.71807 |                      4.59507 | False            |
| ema20_pullback_confirm__4h_adx_le20__2R__480min + auxiliary 20%      | ema20_pullback_confirm__4h_adx_le20__2R__480min      |                 0.2  |                0.6    |           0.2    |                 7 |             4 |           1 |           0.7231  |                 5 |             6 |           0 |          -3.7451  |                      4.99753 | False            |
| ema20_pullback_confirm__4h_adx_le20__3R__240min + auxiliary 10%      | ema20_pullback_confirm__4h_adx_le20__3R__240min      |                 0.1  |                0.675  |           0.225  |                 7 |             4 |           1 |           0.65366 |                 5 |             6 |           0 |          -3.05972 |                      4.29932 | False            |
| ema20_pullback_confirm__4h_adx_le20__3R__480min + auxiliary 10%      | ema20_pullback_confirm__4h_adx_le20__3R__480min      |                 0.1  |                0.675  |           0.225  |                 7 |             4 |           1 |           0.65005 |                 5 |             6 |           0 |          -3.2467  |                      4.43178 | False            |
| ema20_pullback_confirm__4h_adx_le20__2R__480min + auxiliary 15%      | ema20_pullback_confirm__4h_adx_le20__2R__480min      |                 0.15 |                0.6375 |           0.2125 |                 7 |             4 |           1 |           0.55834 |                 5 |             6 |           0 |          -3.38503 |                      4.77518 | False            |

## Caveats
- All 2025/2026 candles previously explored; 2026 not pristine out of sample
- Stage18 baseline was itself selected using 2026 historical performance
- Exploratory 420 trials are subject to substantial data-mining bias
- Portfolio uses separate concurrent sleeves, modelled by monthly return blends rather than portfolio-level order replay
- Rebalancing commissions, margin, funding, true bid ask, liquidation are not included
- Stage19 1H hourly pattern trade net R is booked at exit IST month while Stage18 daily swing marks open positions at month-end
- Month-end max drawdown excludes intraday peaks and troughs
- Fractional 0.5% risk per component requires compatible exchange contract granularity
- Zero or no exposure is not a winning month
- November 2026 data through 16th; 2026-10-31 source missing
- Historical 100% consistency would not imply guaranteed future profits

Never apply a monthly loser-exclusion label using hindsight.
