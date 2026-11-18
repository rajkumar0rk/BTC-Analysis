# Stage20 — Add new hourly pattern to preserved Stage18

## Baseline frozen
Stage18 unchanged: 75% 1H quiet-volume pullback, 25% Daily 20 Donchian swing.

## New model search
140 Stage19 hourly strategies, combined with only 10%, 15%, or 20%
auxiliary capital (420 cases). All historical monthly net returns include
standard taker fees, GST and assumed 5-point adverse slippage per leg.

## Frozen original and best selected by 2025 (then 2026 recheck)
| model                     |   profitable_2025 |   losing_2025 |   idle_2025 |   return_2025_pct |   profitable_2026 |   losing_2026 |   idle_2026 |   return_2026_pct |   max_month_end_dd | variant                                                     | stage19_model                               |   new_pattern_weight |   quiet_volume_weight |   daily20_weight |   month_end_max_drawdown_pct |   all23_positive |
|:--------------------------|------------------:|--------------:|------------:|------------------:|------------------:|--------------:|------------:|------------------:|-------------------:|:------------------------------------------------------------|:--------------------------------------------|---------------------:|----------------------:|-----------------:|-----------------------------:|-----------------:|
| Original Stage18          |                 9 |             1 |           2 |           4.26162 |                 8 |             2 |           1 |           5.58703 |            1.01968 | nan                                                         | nan                                         |                nan   |               nan     |          nan     |                    nan       |              nan |
| New Stage20 2025 selected |                10 |             1 |           1 |           3.41315 |                 8 |             2 |           1 |           4.2994  |          nan       | strong_momentum_6h__4h_adx_le20__3R__480min + auxiliary 10% | strong_momentum_6h__4h_adx_le20__3R__480min |                  0.1 |                 0.675 |            0.225 |                      0.97456 |                0 |

## 2025 selected candidate monthly results
| month_ist   |   stage18_month_pct |   stage19_month_pct |   portfolio_month_pct | state     |
|:------------|--------------------:|--------------------:|----------------------:|:----------|
| 2025-01     |            0        |              0      |              0        | No profit |
| 2025-02     |            1.1527   |             -2.9282 |              0.744613 | Profit    |
| 2025-03     |            0        |              0.5917 |              0.05917  | Profit    |
| 2025-04     |            1.35327  |              2.1405 |              1.43199  | Profit    |
| 2025-05     |            0.018413 |              1.3193 |              0.148502 | Profit    |
| 2025-06     |            0.443366 |             -0.8907 |              0.309959 | Profit    |
| 2025-07     |            0.503388 |             -3.5551 |              0.097539 | Profit    |
| 2025-08     |            0.451187 |              0.0925 |              0.415318 | Profit    |
| 2025-09     |            0.07085  |              0.5341 |              0.117175 | Profit    |
| 2025-10     |            0.524855 |              0.8528 |              0.55765  | Profit    |
| 2025-11     |            0.702985 |             -2.109  |              0.421787 | Profit    |
| 2025-12     |           -1.01968  |             -0.0855 |             -0.926262 | Loss      |
| 2026-01     |            0.078613 |             -1.195  |             -0.048748 | Loss      |
| 2026-02     |            2.79689  |             -1.9199 |              2.32521  | Profit    |
| 2026-03     |            1.7479   |             -0.9219 |              1.48092  | Profit    |
| 2026-04     |            0.337995 |             -0.9755 |              0.206645 | Profit    |
| 2026-05     |            0.187828 |             -0.9528 |              0.073765 | Profit    |
| 2026-06     |            0.16027  |             -1.1175 |              0.032493 | Profit    |
| 2026-07     |           -0.037475 |              2.373  |              0.203573 | Profit    |
| 2026-08     |            0.4238   |              0.3389 |              0.41531  | Profit    |
| 2026-09     |           -0.267025 |             -2.5247 |             -0.492793 | Loss      |
| 2026-10     |            0.063425 |             -0.0388 |              0.053202 | Profit    |
| 2026-11     |            0        |              0      |              0        | No profit |

**Historical all-month profitable models: 0/420**

## Top 2025-ranked alternatives
| variant                                                                 | stage19_model                                           |   new_pattern_weight |   quiet_volume_weight |   daily20_weight |   profitable_2025 |   losing_2025 |   idle_2025 |   return_2025_pct |   profitable_2026 |   losing_2026 |   idle_2026 |   return_2026_pct |   month_end_max_drawdown_pct | all23_positive   |
|:------------------------------------------------------------------------|:--------------------------------------------------------|---------------------:|----------------------:|-----------------:|------------------:|--------------:|------------:|------------------:|------------------:|--------------:|------------:|------------------:|-----------------------------:|:-----------------|
| strong_momentum_6h__4h_adx_le20__3R__480min + auxiliary 10%             | strong_momentum_6h__4h_adx_le20__3R__480min             |                 0.1  |                0.675  |           0.225  |                10 |             1 |           1 |           3.41315 |                 8 |             2 |           1 |           4.2994  |                      0.97456 | False            |
| strong_momentum_6h__4h_adx_le20__2R__480min + auxiliary 10%             | strong_momentum_6h__4h_adx_le20__2R__480min             |                 0.1  |                0.675  |           0.225  |                10 |             1 |           1 |           3.41166 |                 8 |             2 |           1 |           4.46313 |                      0.95003 | False            |
| strong_momentum_6h__4h_efficiency_ge30__3R__480min + auxiliary 10%      | strong_momentum_6h__4h_efficiency_ge30__3R__480min      |                 0.1  |                0.675  |           0.225  |                10 |             2 |           0 |           3.76194 |                 7 |             4 |           0 |           4.04785 |                      0.92626 | False            |
| compression_expansion_12h__4h_adx_le20__3R__240min + auxiliary 10%      | compression_expansion_12h__4h_adx_le20__3R__240min      |                 0.1  |                0.675  |           0.225  |                10 |             2 |           0 |           3.75415 |                 8 |             2 |           1 |           4.82595 |                      0.92728 | False            |
| compression_expansion_12h__4h_adx_le20__2R__240min + auxiliary 10%      | compression_expansion_12h__4h_adx_le20__2R__240min      |                 0.1  |                0.675  |           0.225  |                10 |             2 |           0 |           3.70236 |                 8 |             2 |           1 |           4.82595 |                      0.92728 | False            |
| strong_momentum_6h__4h_efficiency_ge30__2R__480min + auxiliary 10%      | strong_momentum_6h__4h_efficiency_ge30__2R__480min      |                 0.1  |                0.675  |           0.225  |                10 |             2 |           0 |           3.60114 |                 6 |             5 |           0 |           4.01211 |                      0.91263 | False            |
| compression_expansion_12h__4h_atr_ratio_le1__2R__240min + auxiliary 10% | compression_expansion_12h__4h_atr_ratio_le1__2R__240min |                 0.1  |                0.675  |           0.225  |                10 |             2 |           0 |           3.56873 |                 8 |             2 |           1 |           5.12453 |                      0.95376 | False            |
| compression_expansion_12h__4h_atr_ratio_le1__3R__240min + auxiliary 10% | compression_expansion_12h__4h_atr_ratio_le1__3R__240min |                 0.1  |                0.675  |           0.225  |                10 |             2 |           0 |           3.54533 |                 8 |             2 |           1 |           5.17594 |                      0.95376 | False            |
| strong_momentum_6h__4h_efficiency_ge30__3R__480min + auxiliary 15%      | strong_momentum_6h__4h_efficiency_ge30__3R__480min      |                 0.15 |                0.6375 |           0.2125 |                10 |             2 |           0 |           3.51157 |                 7 |             4 |           0 |           3.28464 |                      1.09598 | False            |
| compression_expansion_12h__4h_adx_le20__3R__240min + auxiliary 15%      | compression_expansion_12h__4h_adx_le20__3R__240min      |                 0.15 |                0.6375 |           0.2125 |                10 |             2 |           0 |           3.50093 |                 8 |             2 |           1 |           4.44692 |                      0.88108 | False            |
| compression_expansion_12h__4h_adx_le20__2R__240min + auxiliary 15%      | compression_expansion_12h__4h_adx_le20__2R__240min      |                 0.15 |                0.6375 |           0.2125 |                10 |             2 |           0 |           3.42347 |                 8 |             2 |           1 |           4.44692 |                      0.88108 | False            |
| strong_momentum_6h__4h_efficiency_ge30__2R__480min + auxiliary 15%      | strong_momentum_6h__4h_efficiency_ge30__2R__480min      |                 0.15 |                0.6375 |           0.2125 |                10 |             2 |           0 |           3.27106 |                 5 |             6 |           0 |           3.23173 |                      0.98593 | False            |
| strong_momentum_6h__4h_efficiency_ge30__3R__480min + auxiliary 20%      | strong_momentum_6h__4h_efficiency_ge30__3R__480min      |                 0.2  |                0.6    |           0.2    |                10 |             2 |           0 |           3.26087 |                 6 |             5 |           0 |           2.52565 |                      1.39287 | False            |
| compression_expansion_12h__4h_adx_le20__3R__240min + auxiliary 20%      | compression_expansion_12h__4h_adx_le20__3R__240min      |                 0.2  |                0.6    |           0.2    |                10 |             2 |           0 |           3.24805 |                 8 |             2 |           1 |           4.06889 |                      0.83488 | False            |
| compression_expansion_12h__4h_atr_ratio_le1__2R__240min + auxiliary 15% | compression_expansion_12h__4h_atr_ratio_le1__2R__240min |                 0.15 |                0.6375 |           0.2125 |                10 |             2 |           0 |           3.22339 |                 8 |             2 |           1 |           4.89378 |                      0.9208  | False            |
| compression_expansion_12h__4h_atr_ratio_le1__3R__240min + auxiliary 15% | compression_expansion_12h__4h_atr_ratio_le1__3R__240min |                 0.15 |                0.6375 |           0.2125 |                10 |             2 |           0 |           3.18837 |                 8 |             2 |           1 |           4.97079 |                      0.9208  | False            |
| compression_expansion_12h__4h_adx_le20__2R__240min + auxiliary 20%      | compression_expansion_12h__4h_adx_le20__2R__240min      |                 0.2  |                0.6    |           0.2    |                10 |             2 |           0 |           3.14509 |                 8 |             2 |           1 |           4.06889 |                      0.83488 | False            |
| ema20_pullback_confirm__4h_efficiency_ge30__3R__480min + auxiliary 10%  | ema20_pullback_confirm__4h_efficiency_ge30__3R__480min  |                 0.1  |                0.675  |           0.225  |                10 |             2 |           0 |           3.06357 |                 8 |             3 |           0 |           4.909   |                      1.13821 | False            |
| ema20_pullback_confirm__4h_efficiency_ge30__3R__240min + auxiliary 10%  | ema20_pullback_confirm__4h_efficiency_ge30__3R__240min  |                 0.1  |                0.675  |           0.225  |                10 |             2 |           0 |           2.96569 |                 6 |             5 |           0 |           4.63763 |                      1.04679 | False            |
| strong_momentum_6h__4h_efficiency_ge30__2R__480min + auxiliary 20%      | strong_momentum_6h__4h_efficiency_ge30__2R__480min      |                 0.2  |                0.6    |           0.2    |                10 |             2 |           0 |           2.9411  |                 5 |             6 |           0 |           2.45604 |                      1.24608 | False            |

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
