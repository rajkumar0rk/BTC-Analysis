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
| 2025_train_anchor0.00_slots9 |                12 |             0 |                0 |             4 |           7 |                0 |                1.4092 |                0.0656 |

## Selected strategy weights
| strategy                                                        | family   |   weight_pct |   component_return_2025_pct |
|:----------------------------------------------------------------|:---------|-------------:|----------------------------:|
| Stage19 compression_expansion_12h__4h_atr_ratio_le1__2R__240min | stage19  |        8.738 |                      -2.536 |
| Stage19 ema20_pullback_confirm__4h_adx_le20__3R__240min         | stage19  |        6.4   |                      -4.229 |
| Stage19 strong_momentum_6h__4h_atr_ratio_le1__2R__480min        | stage19  |        7.801 |                      -5.517 |
| Stage19 strong_momentum_6h__4h_efficiency_ge30__3R__240min      | stage19  |        2.074 |                      -1.372 |
| Stage16 stage14_unchanged : month_profit_lock_plus3R            | stage16  |       21.564 |                       9.789 |
| Stage17 1D_channel_55_ema50_agrees_trail_3atr                   | stage17  |       18.423 |                       0.602 |
| Stage17 1D_channel_55_ema50_agrees_trail_4atr                   | stage17  |       35     |                       0.602 |

## Monthly returns: Stage18 and 2025-only selected portfolio
| month_ist   |   stage18_reference_pct |   stage21_train_selected_pct | status   |
|:------------|------------------------:|-----------------------------:|:---------|
| 2025-01     |                 0       |                      0.0146  | Profit   |
| 2025-02     |                 1.1527  |                      0.19413 | Profit   |
| 2025-03     |                 0       |                      0.02779 | Profit   |
| 2025-04     |                 1.35327 |                      0.44112 | Profit   |
| 2025-05     |                 0.01841 |                      0.0146  | Profit   |
| 2025-06     |                 0.44337 |                      0.28383 | Profit   |
| 2025-07     |                 0.50339 |                      0.34666 | Profit   |
| 2025-08     |                 0.45119 |                      0.0146  | Profit   |
| 2025-09     |                 0.07085 |                      0.02046 | Profit   |
| 2025-10     |                 0.52485 |                      0.0146  | Profit   |
| 2025-11     |                 0.70298 |                      0.0146  | Profit   |
| 2025-12     |                -1.01968 |                      0.0146  | Profit   |
| 2026-01     |                 0.07861 |                     -0.58306 | Loss     |
| 2026-02     |                 2.79689 |                      1.02949 | Profit   |
| 2026-03     |                 1.7479  |                      0.49864 | Profit   |
| 2026-04     |                 0.33799 |                     -0.21324 | Loss     |
| 2026-05     |                 0.18783 |                     -0.14841 | Loss     |
| 2026-06     |                 0.16027 |                     -0.39553 | Loss     |
| 2026-07     |                -0.03748 |                     -0.05104 | Loss     |
| 2026-08     |                 0.4238  |                      0.87063 | Profit   |
| 2026-09     |                -0.26703 |                     -0.77636 | Loss     |
| 2026-10     |                 0.06342 |                     -0.19272 | Loss     |
| 2026-11     |                 0       |                      0.04349 | Profit   |

## Search diagnostics
2025-only unconstrained-sparse LP upper bound:
{'winners': 12, 'losers': 0, 'neutral': 0, 'min_month_pct': 0.0351, 'compounded_pct': 0.817}
Its 2026 check:
{'winners': 4, 'losers': 7, 'neutral': 0, 'min_month_pct': -0.6551, 'compounded_pct': 0.5896}

23-month HINDSIGHT oracle LP (INVALID as a live strategy):
-0.1629
{'winners': 6, 'losers': 6, 'neutral': 0, 'min_month_pct': -0.1629, 'compounded_pct': 1.3307}
{'winners': 4, 'losers': 7, 'neutral': 0, 'min_month_pct': -0.1629, 'compounded_pct': 1.1696}

This full-history oracle is NOT an executable predictive strategy.

## Full selection runs
| name                         |   train_anchor |   max_sleeves | weights                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |   positive_2025 |   losing_2025 |   neutral_2025 |   worst_2025_pct |   compound_2025_pct |   positive_2026 |   losing_2026 |   neutral_2026 |   worst_2026_pct |   compound_2026_pct |   max_month_end_dd |
|:-----------------------------|---------------:|--------------:|:-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------:|--------------:|---------------:|-----------------:|--------------------:|----------------:|--------------:|---------------:|-----------------:|--------------------:|-------------------:|
| 2025_train_anchor0.00_slots4 |           0    |             4 | Preserved Stage18 75/25 41.5% | Stage19 ema20_pullback_confirm__4h_adx_le20__3R__240min 11.9% | Stage19 strong_momentum_6h__4h_atr_ratio_le1__2R__480min 11.6% | Stage17 1D_channel_55_ema50_agrees_trail_3atr 35.0%                                                                                                                                                                                                                                                     |               6 |             6 |              0 |          -0.0954 |              0.8028 |               5 |             6 |              0 |          -1.0811 |              0.372  |             1.4021 |
| 2025_train_anchor0.00_slots6 |           0    |             6 | Preserved Stage18 75/25 29.1% | Stage19 compression_expansion_12h__4h_efficiency_ge30__2R__480min 21.4% | Stage19 ema20_pullback_confirm__4h_adx_le20__3R__240min 5.7% | Stage19 strong_momentum_6h__4h_atr_ratio_le1__2R__480min 2.6% | Stage19 strong_momentum_6h__4h_efficiency_ge30__3R__240min 6.2% | Stage17 1D_channel_55_ema50_agrees_trail_3atr 35.0%                                                                                                           |               4 |             8 |              0 |          -0.0404 |              0.5185 |               4 |             7 |              0 |          -0.7266 |              1.4535 |             0.761  |
| 2025_train_anchor0.00_slots9 |           0    |             9 | Stage19 compression_expansion_12h__4h_atr_ratio_le1__2R__240min 8.7% | Stage19 ema20_pullback_confirm__4h_adx_le20__3R__240min 6.4% | Stage19 strong_momentum_6h__4h_atr_ratio_le1__2R__480min 7.8% | Stage19 strong_momentum_6h__4h_efficiency_ge30__3R__240min 2.1% | Stage16 stage14_unchanged : month_profit_lock_plus3R 21.6% | Stage17 1D_channel_55_ema50_agrees_trail_3atr 18.4% | Stage17 1D_channel_55_ema50_agrees_trail_4atr 35.0%                           |              12 |             0 |              0 |           0.0146 |              1.4092 |               4 |             7 |              0 |          -0.7764 |              0.0656 |             0.9676 |
| 2025_train_anchor0.25_slots4 |           0.25 |             4 | Preserved Stage18 75/25 41.5% | Stage19 ema20_pullback_confirm__4h_adx_le20__3R__240min 11.9% | Stage19 strong_momentum_6h__4h_atr_ratio_le1__2R__480min 11.6% | Stage17 1D_channel_55_ema50_agrees_trail_3atr 35.0%                                                                                                                                                                                                                                                     |               6 |             6 |              0 |          -0.0954 |              0.8028 |               5 |             6 |              0 |          -1.0811 |              0.372  |             1.4021 |
| 2025_train_anchor0.25_slots6 |           0.25 |             6 | Preserved Stage18 75/25 29.1% | Stage19 compression_expansion_12h__4h_efficiency_ge30__2R__480min 21.4% | Stage19 ema20_pullback_confirm__4h_adx_le20__3R__240min 5.7% | Stage19 strong_momentum_6h__4h_atr_ratio_le1__2R__480min 2.6% | Stage19 strong_momentum_6h__4h_efficiency_ge30__3R__240min 6.2% | Stage17 1D_channel_55_ema50_agrees_trail_3atr 35.0%                                                                                                           |               4 |             8 |              0 |          -0.0404 |              0.5185 |               4 |             7 |              0 |          -0.7266 |              1.4535 |             0.761  |
| 2025_train_anchor0.25_slots9 |           0.25 |             9 | Preserved Stage18 75/25 25.0% | Stage19 compression_expansion_12h__4h_efficiency_ge30__2R__480min 7.7% | Stage19 ema20_pullback_confirm__4h_adx_le20__3R__240min 7.9% | Stage19 strong_momentum_6h__4h_adx_le20__2R__480min 3.3% | Stage19 strong_momentum_6h__4h_atr_ratio_le1__2R__480min 10.8% | Stage16 stage14_unchanged : month_profit_lock_plus3R 7.1% | Stage17 1D_channel_55_ema50_agrees_trail_3atr 3.3% | Stage17 1D_channel_55_ema50_agrees_trail_4atr 35.0% |               4 |             8 |              0 |          -0.0158 |              0.7145 |               5 |             6 |              0 |          -0.9869 |              0.1458 |             1.2106 |
| 2025_train_anchor0.50_slots4 |           0.5  |             4 | Preserved Stage18 75/25 50.0% | Stage19 ema20_pullback_confirm__4h_adx_le20__3R__240min 14.1% | Stage19 strong_momentum_6h__4h_atr_ratio_le1__2R__480min 9.7% | Stage17 1D_channel_55_ema50_agrees_trail_3atr 26.3%                                                                                                                                                                                                                                                      |               6 |             6 |              0 |          -0.1213 |              1.1286 |               6 |             5 |              0 |          -1.086  |              0.8347 |             1.3703 |
| 2025_train_anchor0.50_slots6 |           0.5  |             6 | Preserved Stage18 75/25 50.0% | Stage19 compression_expansion_12h__4h_adx_le20__2R__480min 13.7% | Stage19 ema20_pullback_confirm__4h_adx_le20__3R__240min 14.1% | Stage19 strong_momentum_6h__4h_atr_ratio_le1__3R__240min 10.4% | Stage17 1D_channel_55_ema50_agrees_trail_3atr 11.9%                                                                                                                                                                                  |               5 |             7 |              0 |          -0.1017 |              1.0209 |               5 |             6 |              0 |          -1.0322 |              0.6556 |             1.4026 |
| 2025_train_anchor0.50_slots9 |           0.5  |             9 | Preserved Stage18 75/25 50.0% | Stage19 compression_expansion_12h__4h_adx_le20__2R__480min 6.3% | Stage19 compression_expansion_12h__4h_efficiency_ge30__2R__480min 8.8% | Stage19 ema20_pullback_confirm__4h_adx_le20__3R__240min 13.9% | Stage19 strong_momentum_6h__4h_atr_ratio_le1__3R__240min 10.6% | Stage17 1D_channel_55_ema50_agrees_trail_3atr 10.5%                                                                                                          |               6 |             6 |              0 |          -0.0984 |              0.9633 |               5 |             6 |              0 |          -1.0558 |              0.914  |             1.3007 |
| 2025_train_anchor0.65_slots4 |           0.65 |             4 | Preserved Stage18 75/25 65.0% | Stage19 ema20_pullback_confirm__4h_adx_le20__3R__240min 17.3% | Stage19 strong_momentum_6h__4h_atr_ratio_le1__2R__480min 10.0% | Stage17 1D_channel_55_ema50_agrees_trail_3atr 7.6%                                                                                                                                                                                                                                                      |               6 |             6 |              0 |          -0.177  |              1.4909 |               6 |             5 |              0 |          -1.1575 |              1.1508 |             1.5417 |
| 2025_train_anchor0.65_slots6 |           0.65 |             6 | Preserved Stage18 75/25 65.0% | Stage19 ema20_pullback_confirm__4h_adx_le20__3R__240min 17.8% | Stage19 strong_momentum_6h__4h_adx_ge25__3R__240min 2.3% | Stage19 strong_momentum_6h__4h_atr_ratio_le1__2R__480min 9.1% | Stage19 strong_momentum_6h__4h_atr_ratio_le1__3R__240min 0.2% | Stage17 1D_channel_55_ema50_agrees_trail_3atr 5.7%                                                                                                                            |               6 |             6 |              0 |          -0.1673 |              1.4648 |               6 |             5 |              0 |          -1.1604 |              1.0551 |             1.6585 |
| 2025_train_anchor0.65_slots9 |           0.65 |             9 | Preserved Stage18 75/25 65.0% | Stage19 compression_expansion_12h__4h_adx_le20__2R__480min 5.3% | Stage19 ema20_pullback_confirm__4h_adx_le20__3R__240min 18.4% | Stage19 strong_momentum_6h__4h_adx_ge25__3R__240min 1.8% | Stage19 strong_momentum_6h__4h_atr_ratio_le1__2R__480min 2.8% | Stage19 strong_momentum_6h__4h_atr_ratio_le1__3R__240min 6.8%                                                                                                               |               6 |             6 |              0 |          -0.1628 |              1.4736 |               5 |             6 |              0 |          -1.1616 |              1.0577 |             1.6118 |
| 2025_train_anchor0.75_slots4 |           0.75 |             4 | Preserved Stage18 75/25 75.0% | Stage19 ema20_pullback_confirm__4h_adx_le20__3R__240min 19.2% | Stage19 inside_bar_breakout__4h_adx_ge25__3R__480min 1.5% | Stage19 strong_momentum_6h__4h_efficiency_ge30__2R__480min 4.3%                                                                                                                                                                                                                                              |               7 |             5 |              0 |          -0.2354 |              2.0872 |               6 |             5 |              0 |          -1.0458 |              1.9867 |             1.2951 |
| 2025_train_anchor0.75_slots6 |           0.75 |             6 | Preserved Stage18 75/25 75.0% | Stage19 ema20_pullback_confirm__4h_adx_le20__3R__240min 18.0% | Stage19 inside_bar_breakout__4h_adx_ge25__3R__480min 0.7% | Stage19 overextension_reversal__4h_adx_le20__2R__480min 2.6% | Stage19 strong_momentum_6h__4h_efficiency_ge30__2R__480min 3.7%                                                                                                                                                                               |               6 |             6 |              0 |          -0.2324 |              1.6871 |               5 |             6 |              0 |          -1.0574 |              2.0376 |             1.2641 |
| 2025_train_anchor0.75_slots9 |           0.75 |             9 | Preserved Stage18 75/25 75.0% | Stage19 ema20_pullback_confirm__4h_adx_le20__3R__240min 18.0% | Stage19 inside_bar_breakout__4h_adx_ge25__3R__480min 0.7% | Stage19 overextension_reversal__4h_adx_le20__2R__480min 2.6% | Stage19 strong_momentum_6h__4h_efficiency_ge30__2R__480min 3.7%                                                                                                                                                                               |               6 |             6 |              0 |          -0.2324 |              1.6871 |               5 |             6 |              0 |          -1.0574 |              2.0376 |             1.2641 |

## Limitations
- This is a fixed-weight blend of independently traded strategy ledgers, not a live tradable unified execution engine
- All underlying strategies and 2026 history have been inspected in previous research; not untouched forward data
- No future month labels enter train-only selector; full-history oracle is explicitly NOT deployable
- Fitting 2025 12 points with many models greatly overfits; sparse 4-8 sleeve selection is exploratory
- Month-end equity can mask severe intramonth drawdown, stops and risk gaps
- Spreads, funding payments, margin/contract step sizing, portfolio rebalance fees not modeled
- 2026 November has only first 16 days, Oct 31 source gap
- No strategy can assure a positive month in future
