# Stage21 — Fixed-weight sparse portfolio search for monthly-positive BTC returns

The historical target is positive in EVERY one of the 23 observed IST months.
Uses original source net monthly returns from Stage16, 17, 18 and 19.
**Stage18 and Stage20 are preserved unchanged.**

## Valid research approach
Choose model constituents and fixed nonnegative weights from 2025 only.
Then hold exactly the same weights in the previously seen 2026 data.
Do not use future labels, historical month exclusions, or negative weights.

## Best sparse model selected on 2025 months
| method                       |   profitable_2025 |   losing_2025 |   no_profit_2025 |   profit_2026 |   loss_2026 |   no_profit_2026 |   modeled_return_2025 |   modeled_return_2026 |
|:-----------------------------|------------------:|--------------:|-----------------:|--------------:|------------:|-----------------:|----------------------:|----------------------:|
| 2025_train_anchor0.00_slots9 |                12 |             0 |                0 |             4 |           7 |                0 |                 8.827 |               -5.9697 |

## Selected strategy weights
| strategy                                                     | family   |   weight_pct |   component_return_2025_pct |
|:-------------------------------------------------------------|:---------|-------------:|----------------------------:|
| Stage19 failed_break_12h__4h_atr_ratio_le1__3R__240min       | stage19  |        4.077 |                       2.6   |
| Stage19 failed_break_12h__4h_atr_ratio_le1__3R__480min       | stage19  |       17.278 |                      11.744 |
| Stage19 overextension_reversal__4h_atr_ratio_le1__3R__480min | stage19  |       33.712 |                      11.341 |
| Stage17 4H_channel_24_ema50_agrees_trail_3atr                | stage17  |        9.933 |                       6.096 |
| Stage17 4H_channel_55_ema50_agrees_trail_3atr                | stage17  |       35     |                       6.022 |

## Monthly returns: Stage18 and 2025-only selected portfolio
| month_ist   |   stage18_reference_pct |   stage21_train_selected_pct | status   |
|:------------|------------------------:|-----------------------------:|:---------|
| 2025-01     |                 0       |                      0.71242 | Profit   |
| 2025-02     |                 1.50058 |                      0.39908 | Profit   |
| 2025-03     |                 0       |                      0.75803 | Profit   |
| 2025-04     |                -0.6557  |                      0.60438 | Profit   |
| 2025-05     |                 0.02553 |                      0.34288 | Profit   |
| 2025-06     |                -0.70561 |                      0.40251 | Profit   |
| 2025-07     |                 1.7274  |                      1.49687 | Profit   |
| 2025-08     |                 0       |                      1.207   | Profit   |
| 2025-09     |                -1.23895 |                      0.34288 | Profit   |
| 2025-10     |                -0.23852 |                      0.34288 | Profit   |
| 2025-11     |                 0       |                      1.54841 | Profit   |
| 2025-12     |                -0.3144  |                      0.34288 | Profit   |
| 2026-01     |                 0.72388 |                      0.8201  | Profit   |
| 2026-02     |                -0.20284 |                     -0.29607 | Loss     |
| 2026-03     |                 0.28994 |                     -4.24774 | Loss     |
| 2026-04     |                -0.6941  |                     -1.29002 | Loss     |
| 2026-05     |                 0.28393 |                      0.02565 | Profit   |
| 2026-06     |                 1.03214 |                      0.07757 | Profit   |
| 2026-07     |                -1.48801 |                     -0.67819 | Loss     |
| 2026-08     |                -2.1735  |                      2.36619 | Profit   |
| 2026-09     |                -0.13303 |                     -2.01771 | Loss     |
| 2026-10     |                 0.0132  |                     -0.3858  | Loss     |
| 2026-11     |                 0.06953 |                     -0.37226 | Loss     |

## Search diagnostics
2025-only unconstrained-sparse LP upper bound:
{'winners': 12, 'losers': 0, 'neutral': 0, 'min_month_pct': 0.3853, 'compounded_pct': 8.7182}
Its 2026 check:
{'winners': 3, 'losers': 8, 'neutral': 0, 'min_month_pct': -4.1043, 'compounded_pct': -5.1749}

23-month HINDSIGHT oracle LP (INVALID as a live strategy):
-0.0866
{'winners': 4, 'losers': 8, 'neutral': 0, 'min_month_pct': -0.0866, 'compounded_pct': 1.5031}
{'winners': 4, 'losers': 7, 'neutral': 0, 'min_month_pct': -0.0866, 'compounded_pct': 0.5872}

This full-history oracle is NOT an executable predictive strategy.

## Full selection runs
| name                         |   train_anchor |   max_sleeves | weights                                                                                                                                                                                                                                                                                                                                                                        |   positive_2025 |   losing_2025 |   neutral_2025 |   worst_2025_pct |   compound_2025_pct |   positive_2026 |   losing_2026 |   neutral_2026 |   worst_2026_pct |   compound_2026_pct |   max_month_end_dd |
|:-----------------------------|---------------:|--------------:|:-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------:|--------------:|---------------:|-----------------:|--------------------:|----------------:|--------------:|---------------:|-----------------:|--------------------:|-------------------:|
| 2025_train_anchor0.00_slots4 |           0    |             4 | Preserved Stage18 75/25 22.7% | Stage19 compression_expansion_12h__4h_adx_le20__2R__240min 35.0% | Stage19 compression_expansion_12h__4h_efficiency_ge30__2R__240min 32.9% | Stage19 failed_break_12h__4h_atr_ratio_le1__3R__240min 9.4%                                                                                                                                       |               4 |             8 |              0 |          -0.19   |              0.7878 |               4 |             7 |              0 |          -0.8534 |             -2.5947 |             2.9564 |
| 2025_train_anchor0.00_slots6 |           0    |             6 | Preserved Stage18 75/25 5.3% | Stage19 compression_expansion_12h__4h_adx_le20__2R__240min 35.0% | Stage19 compression_expansion_12h__4h_adx_le20__3R__240min 35.0% | Stage19 compression_expansion_12h__4h_efficiency_ge30__2R__240min 19.5% | Stage19 failed_break_12h__4h_atr_ratio_le1__3R__240min 3.5% | Stage19 overextension_reversal__4h_atr_ratio_le1__3R__480min 1.6% |               7 |             5 |              0 |          -0.0559 |              1.0578 |               3 |             8 |              0 |          -0.6891 |             -1.7075 |             2.0158 |
| 2025_train_anchor0.00_slots9 |           0    |             9 | Stage19 failed_break_12h__4h_atr_ratio_le1__3R__240min 4.1% | Stage19 failed_break_12h__4h_atr_ratio_le1__3R__480min 17.3% | Stage19 overextension_reversal__4h_atr_ratio_le1__3R__480min 33.7% | Stage17 4H_channel_24_ema50_agrees_trail_3atr 9.9% | Stage17 4H_channel_55_ema50_agrees_trail_3atr 35.0%                                                                     |              12 |             0 |              0 |           0.3429 |              8.827  |               4 |             7 |              0 |          -4.2477 |             -5.9697 |             6.7345 |
| 2025_train_anchor0.25_slots4 |           0.25 |             4 | Preserved Stage18 75/25 25.0% | Stage19 compression_expansion_12h__4h_adx_le20__2R__240min 29.4% | Stage19 compression_expansion_12h__4h_efficiency_ge30__2R__240min 35.0% | Stage19 failed_break_12h__4h_atr_ratio_le1__3R__240min 10.6%                                                                                                                                      |               4 |             8 |              0 |          -0.2068 |              0.7723 |               4 |             7 |              0 |          -0.869  |             -2.7861 |             3.1577 |
| 2025_train_anchor0.25_slots6 |           0.25 |             6 | Preserved Stage18 75/25 25.0% | Stage19 compression_expansion_12h__4h_adx_le20__2R__240min 29.8% | Stage19 failed_break_12h__4h_atr_ratio_le1__3R__240min 22.4% | Stage19 strong_momentum_6h__all__3R__240min 11.9% | Stage17 4H_channel_24_no_trend_filter_trail_4atr 10.9%                                                                                                   |               5 |             7 |              0 |          -0.1425 |              1.5938 |               3 |             8 |              0 |          -1.3641 |             -3.5314 |             4.5654 |
| 2025_train_anchor0.25_slots9 |           0.25 |             9 | Preserved Stage18 75/25 25.0% | Stage19 failed_break_12h__4h_atr_ratio_le1__3R__240min 19.1% | Stage19 overextension_reversal__4h_atr_ratio_le1__2R__480min 20.3% | Stage19 strong_momentum_6h__4h_efficiency_ge30__3R__480min 12.4% | Stage17 4H_channel_24_ema50_agrees_trail_3atr 23.3%                                                                                     |               8 |             4 |              0 |          -0.0077 |              3.7058 |               4 |             7 |              0 |          -2.4782 |             -3.0521 |             4.3646 |
| 2025_train_anchor0.50_slots4 |           0.5  |             4 | Preserved Stage18 75/25 50.0% | Stage19 compression_expansion_12h__4h_efficiency_ge30__2R__240min 31.6% | Stage19 failed_break_12h__4h_atr_ratio_le1__3R__240min 9.5% | Stage19 failed_break_12h__4h_atr_ratio_le1__3R__480min 8.8%                                                                                                                                            |               6 |             6 |              0 |          -0.3683 |              1.4575 |               3 |             8 |              0 |          -1.1764 |             -4.4169 |             4.8838 |
| 2025_train_anchor0.50_slots6 |           0.5  |             6 | Preserved Stage18 75/25 50.0% | Stage19 failed_break_12h__4h_atr_ratio_le1__3R__480min 20.0% | Stage19 overextension_reversal__4h_atr_ratio_le1__3R__480min 4.0% | Stage17 1D_channel_55_ema50_agrees_trail_3atr 26.0%                                                                                                                                                         |               7 |             5 |              0 |          -0.3208 |              3.4    |               3 |             8 |              0 |          -1.0994 |             -4.7013 |             5.4917 |
| 2025_train_anchor0.50_slots9 |           0.5  |             9 | Preserved Stage18 75/25 50.0% | Stage19 failed_break_12h__4h_adx_ge25__3R__480min 1.0% | Stage19 failed_break_12h__4h_atr_ratio_le1__3R__480min 19.7% | Stage19 overextension_reversal__4h_atr_ratio_le1__3R__480min 10.0% | Stage17 4H_channel_24_no_trend_filter_trail_3atr 4.2% | Stage17 4H_channel_55_ema50_agrees_trail_3atr 15.1%                                       |               6 |             6 |              0 |          -0.1864 |              4.6713 |               3 |             8 |              0 |          -1.8328 |             -5.1309 |             6.1189 |
| 2025_train_anchor0.65_slots4 |           0.65 |             4 | Preserved Stage18 75/25 65.0% | Stage19 failed_break_12h__4h_atr_ratio_le1__3R__240min 24.2% | Stage19 overextension_reversal__4h_adx_le20__3R__480min 6.5% | Stage17 4H_channel_24_no_trend_filter_trail_3atr 4.3%                                                                                                                                                            |               5 |             7 |              0 |          -0.4681 |              0.4249 |               2 |             9 |              0 |          -1.7597 |             -5.6612 |             6.5866 |
| 2025_train_anchor0.65_slots6 |           0.65 |             6 | Preserved Stage18 75/25 65.0% | Stage19 failed_break_12h__4h_adx_ge25__2R__240min 9.6% | Stage19 failed_break_12h__4h_atr_ratio_le1__3R__480min 13.7% | Stage19 overextension_reversal__4h_adx_le20__3R__480min 4.5% | Stage17 4H_channel_24_no_trend_filter_trail_3atr 7.2%                                                                                                   |               6 |             6 |              0 |          -0.4079 |              1.7946 |               3 |             8 |              0 |          -1.6124 |             -4.8225 |             5.9314 |
| 2025_train_anchor0.65_slots9 |           0.65 |             9 | Preserved Stage18 75/25 65.0% | Stage19 failed_break_12h__4h_adx_ge25__3R__480min 2.3% | Stage19 failed_break_12h__4h_atr_ratio_le1__3R__480min 19.4% | Stage19 overextension_reversal__4h_atr_ratio_le1__3R__480min 3.0% | Stage17 4H_channel_24_no_trend_filter_trail_3atr 2.4% | Stage17 4H_channel_55_ema50_agrees_trail_3atr 7.9%                                         |               6 |             6 |              0 |          -0.3713 |              3.3869 |               3 |             8 |              0 |          -1.2896 |             -5.0912 |             6.098  |
| 2025_train_anchor0.75_slots4 |           0.75 |             4 | Preserved Stage18 75/25 75.0% | Stage19 failed_break_12h__4h_adx_ge25__3R__480min 0.5% | Stage19 failed_break_12h__4h_atr_ratio_le1__3R__480min 20.9% | Stage17 4H_channel_55_ema50_agrees_trail_3atr 3.7%                                                                                                                                                                     |               6 |             6 |              0 |          -0.5127 |              2.7129 |               3 |             8 |              0 |          -1.4785 |             -5.3141 |             6.2713 |
| 2025_train_anchor0.75_slots6 |           0.75 |             6 | Preserved Stage18 75/25 75.0% | Stage19 failed_break_12h__4h_adx_ge25__3R__480min 0.5% | Stage19 failed_break_12h__4h_atr_ratio_le1__3R__480min 20.8% | Stage19 sweep_reclaim_12h__4h_atr_ratio_le1__3R__480min 0.0% | Stage17 4H_channel_55_ema50_agrees_trail_3atr 3.7%                                                                                                      |               6 |             6 |              0 |          -0.5127 |              2.7074 |               3 |             8 |              0 |          -1.4784 |             -5.3142 |             6.271  |
| 2025_train_anchor0.75_slots9 |           0.75 |             9 | Preserved Stage18 75/25 75.0% | Stage19 failed_break_12h__4h_adx_ge25__3R__480min 0.5% | Stage19 failed_break_12h__4h_atr_ratio_le1__3R__480min 20.8% | Stage19 sweep_reclaim_12h__4h_atr_ratio_le1__3R__480min 0.0% | Stage17 4H_channel_55_ema50_agrees_trail_3atr 3.7%                                                                                                      |               6 |             6 |              0 |          -0.5127 |              2.7074 |               3 |             8 |              0 |          -1.4784 |             -5.3142 |             6.271  |

## Limitations
- This is a fixed-weight blend of independently traded strategy ledgers, not a live tradable unified execution engine
- All underlying strategies and 2026 history have been inspected in previous research; not untouched forward data
- No future month labels enter train-only selector; full-history oracle is explicitly NOT deployable
- Fitting 2025 12 points with many models greatly overfits; sparse 4-8 sleeve selection is exploratory
- Month-end equity can mask severe intramonth drawdown, stops and risk gaps
- Spreads, funding payments, margin/contract step sizing, portfolio rebalance fees not modeled
- 2026 November has only first 16 days, Oct 31 source gap
- No strategy can assure a positive month in future
