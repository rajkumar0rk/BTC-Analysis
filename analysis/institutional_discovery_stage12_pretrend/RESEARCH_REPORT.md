# Stage 12 — Before BTC's directional move: 1H/4H structure, volatility and participation

## Research design
- Keep the Stage 11 **8 entry patterns identical**: break-retest, sweep-reclaim,
  engulfing, inside-bar break, structure shift, compression breakout, etc.
- Test only market-state modifiers derived from completed higher-timeframe bars:
  4H or 1H trend agreement, countertrend pullback, volume/range participation,
  channel acceptance, 1H quiet-to-expansion transition, and 5m activity.
- Require >=16 fully complete consecutive 1H/4H candles for prior context.
- Entry = following 1m open; stop beyond completed structure; TP = 2R or 3R.
- One trade per configuration at a time, both LONG and SHORT.
- Compare each condition to the exact pattern with no condition.
- Standard taker + GST and adverse slippage included; separate conditional Scalper Offer study.
- Historical 2025 used for rankings, chronological 2026 already inspected, not pristine OOS.

## Best condition-specific 2025 models (research only)
| pattern                  | environment                  |   reward_R |   hold_minutes |   trades |   win_pct |   avg_net_pts |   profit_factor |   avg_risk_pts |
|:-------------------------|:-----------------------------|-----------:|---------------:|---------:|----------:|--------------:|----------------:|---------------:|
| 06_inside_bar_break      | 1h_directional_high_volume   |          3 |            240 |      221 |     36.65 |        -14.29 |           0.958 |         466.84 |
| 06_inside_bar_break      | dual_trend_plus_5m_activity  |          3 |            240 |       74 |     37.84 |        -35.1  |           0.9   |         506.19 |
| 06_inside_bar_break      | 1h_trend_5m_vol_acceleration |          3 |            240 |      192 |     36.98 |        -44.85 |           0.862 |         444.65 |
| 06_inside_bar_break      | 1h_directional_high_volume   |          2 |            240 |      226 |     39.82 |        -46.48 |           0.856 |         467.12 |
| 06_inside_bar_break      | 1h_regime_expansion          |          3 |            240 |      197 |     36.04 |        -47.23 |           0.868 |         482.9  |
| 06_inside_bar_break      | 1h_break_6bar_channel        |          3 |            240 |      248 |     33.47 |        -63.3  |           0.807 |         409.36 |
| 06_inside_bar_break      | dual_trend_plus_5m_activity  |          3 |            120 |       74 |     37.84 |        -65.15 |           0.78  |         506.19 |
| 06_inside_bar_break      | 1h_trend_5m_vol_acceleration |          3 |            120 |      195 |     33.33 |        -66.41 |           0.751 |         444.12 |
| 04_trend_pullback_engulf | 1h_quiet_then_5m_expansion   |          3 |            240 |      109 |     27.52 |        -66.72 |           0.768 |         301.1  |
| 06_inside_bar_break      | dual_trend_plus_5m_activity  |          2 |            120 |       75 |     41.33 |        -70.57 |           0.755 |         506.46 |
| 03_breakout_retest       | 1h_regime_expansion          |          2 |            120 |      109 |     44.04 |        -71.04 |           0.756 |         482.68 |
| 04_trend_pullback_engulf | 1h_quiet_then_5m_expansion   |          3 |            120 |      109 |     31.19 |        -71.11 |           0.71  |         301.1  |

## Those exact selections in the research-exposed 2026 periods
| pattern                  | environment                  |   reward_R |   hold_minutes | period                      |   trades |   win_pct |   avg_net_pts |   profit_factor |
|:-------------------------|:-----------------------------|-----------:|---------------:|:----------------------------|---------:|----------:|--------------:|----------------:|
| 03_breakout_retest       | 1h_regime_expansion          |          2 |            120 | 2026_H1_validation          |       42 |     28.57 |       -206.26 |           0.413 |
| 03_breakout_retest       | 1h_regime_expansion          |          2 |            120 | 2026_H2_seen_recheck        |       27 |     25.93 |        -89.99 |           0.566 |
| 03_breakout_retest       | 1h_regime_expansion          |          2 |            120 | 2026_Nov_recent_exploratory |        5 |     60    |        138.08 |           2.177 |
| 04_trend_pullback_engulf | 1h_quiet_then_5m_expansion   |          3 |            120 | 2026_H1_validation          |       42 |     30.95 |        -55.87 |           0.744 |
| 04_trend_pullback_engulf | 1h_quiet_then_5m_expansion   |          3 |            120 | 2026_H2_seen_recheck        |       20 |     40    |       -114.55 |           0.435 |
| 04_trend_pullback_engulf | 1h_quiet_then_5m_expansion   |          3 |            120 | 2026_Nov_recent_exploratory |        7 |     42.86 |        -13.22 |           0.925 |
| 04_trend_pullback_engulf | 1h_quiet_then_5m_expansion   |          3 |            240 | 2026_H1_validation          |       42 |     28.57 |        -37.58 |           0.843 |
| 04_trend_pullback_engulf | 1h_quiet_then_5m_expansion   |          3 |            240 | 2026_H2_seen_recheck        |       20 |     30    |       -117.82 |           0.487 |
| 04_trend_pullback_engulf | 1h_quiet_then_5m_expansion   |          3 |            240 | 2026_Nov_recent_exploratory |        7 |     28.57 |        -99.29 |           0.549 |
| 06_inside_bar_break      | 1h_break_6bar_channel        |          3 |            240 | 2026_H1_validation          |      118 |     25.42 |       -142.7  |           0.566 |
| 06_inside_bar_break      | 1h_break_6bar_channel        |          3 |            240 | 2026_H2_seen_recheck        |       57 |     31.58 |       -111.6  |           0.554 |
| 06_inside_bar_break      | 1h_break_6bar_channel        |          3 |            240 | 2026_Nov_recent_exploratory |        3 |     66.67 |        319.65 |           3.392 |
| 06_inside_bar_break      | 1h_directional_high_volume   |          2 |            240 | 2026_H1_validation          |      107 |     31.78 |       -121.77 |           0.582 |
| 06_inside_bar_break      | 1h_directional_high_volume   |          2 |            240 | 2026_H2_seen_recheck        |       56 |     48.21 |        -56.08 |           0.734 |
| 06_inside_bar_break      | 1h_directional_high_volume   |          2 |            240 | 2026_Nov_recent_exploratory |        3 |      0    |       -439.42 |           0     |
| 06_inside_bar_break      | 1h_directional_high_volume   |          3 |            240 | 2026_H1_validation          |      106 |     28.3  |       -106.26 |           0.649 |
| 06_inside_bar_break      | 1h_directional_high_volume   |          3 |            240 | 2026_H2_seen_recheck        |       54 |     44.44 |        -69.3  |           0.691 |
| 06_inside_bar_break      | 1h_directional_high_volume   |          3 |            240 | 2026_Nov_recent_exploratory |        3 |      0    |       -439.42 |           0     |
| 06_inside_bar_break      | 1h_regime_expansion          |          3 |            240 | 2026_H1_validation          |       92 |     30.43 |        -82.48 |           0.727 |
| 06_inside_bar_break      | 1h_regime_expansion          |          3 |            240 | 2026_H2_seen_recheck        |       50 |     42    |       -102.24 |           0.588 |
| 06_inside_bar_break      | 1h_regime_expansion          |          3 |            240 | 2026_Nov_recent_exploratory |        2 |      0    |       -358.66 |           0     |
| 06_inside_bar_break      | 1h_trend_5m_vol_acceleration |          3 |            120 | 2026_H1_validation          |      115 |     33.04 |       -120.43 |           0.552 |
| 06_inside_bar_break      | 1h_trend_5m_vol_acceleration |          3 |            120 | 2026_H2_seen_recheck        |       49 |     28.57 |       -152.78 |           0.356 |
| 06_inside_bar_break      | 1h_trend_5m_vol_acceleration |          3 |            120 | 2026_Nov_recent_exploratory |        4 |     25    |       -155.66 |           0.626 |
| 06_inside_bar_break      | 1h_trend_5m_vol_acceleration |          3 |            240 | 2026_H1_validation          |      115 |     30.43 |        -92    |           0.697 |
| 06_inside_bar_break      | 1h_trend_5m_vol_acceleration |          3 |            240 | 2026_H2_seen_recheck        |       49 |     22.45 |       -171.61 |           0.367 |
| 06_inside_bar_break      | 1h_trend_5m_vol_acceleration |          3 |            240 | 2026_Nov_recent_exploratory |        4 |     25    |       -126.52 |           0.673 |
| 06_inside_bar_break      | dual_trend_plus_5m_activity  |          2 |            120 | 2026_H1_validation          |       45 |     42.22 |        -17.41 |           0.924 |
| 06_inside_bar_break      | dual_trend_plus_5m_activity  |          2 |            120 | 2026_H2_seen_recheck        |       19 |     47.37 |        -22.98 |           0.877 |
| 06_inside_bar_break      | dual_trend_plus_5m_activity  |          2 |            120 | 2026_Nov_recent_exploratory |        4 |     25    |       -250.13 |           0.399 |
| 06_inside_bar_break      | dual_trend_plus_5m_activity  |          3 |            120 | 2026_H1_validation          |       44 |     43.18 |         31.49 |           1.137 |
| 06_inside_bar_break      | dual_trend_plus_5m_activity  |          3 |            120 | 2026_H2_seen_recheck        |       19 |     47.37 |         -9.82 |           0.947 |
| 06_inside_bar_break      | dual_trend_plus_5m_activity  |          3 |            120 | 2026_Nov_recent_exploratory |        4 |     25    |       -155.66 |           0.626 |
| 06_inside_bar_break      | dual_trend_plus_5m_activity  |          3 |            240 | 2026_H1_validation          |       44 |     40.91 |         44.67 |           1.172 |
| 06_inside_bar_break      | dual_trend_plus_5m_activity  |          3 |            240 | 2026_H2_seen_recheck        |       19 |     47.37 |        -28.82 |           0.873 |
| 06_inside_bar_break      | dual_trend_plus_5m_activity  |          3 |            240 | 2026_Nov_recent_exploratory |        4 |     25    |       -126.52 |           0.673 |

## Stable-positive filters (>=60/30/20 trades across 2025, H1 and H2)
No repeated positive setup at the chosen minimum sample sizes.

## How much did MTF filtering change net expectancy versus the same unfiltered entry?
| pattern                       | environment                  |   reward_R |   hold_minutes |   trades |   baseline_trades |   avg_net_pts |   baseline_net |   delta_net_pts |
|:------------------------------|:-----------------------------|-----------:|---------------:|---------:|------------------:|--------------:|---------------:|----------------:|
| 06_inside_bar_break           | 1h_directional_high_volume   |          3 |            240 |      221 |              1758 |        -14.29 |        -132.96 |          118.67 |
| 06_inside_bar_break           | dual_trend_plus_5m_activity  |          3 |            240 |       74 |              1758 |        -35.1  |        -132.96 |           97.86 |
| 06_inside_bar_break           | 1h_directional_high_volume   |          2 |            240 |      226 |              1867 |        -46.48 |        -140.98 |           94.5  |
| 06_inside_bar_break           | 1h_trend_5m_vol_acceleration |          3 |            240 |      192 |              1758 |        -44.85 |        -132.96 |           88.11 |
| 06_inside_bar_break           | 1h_regime_expansion          |          3 |            240 |      197 |              1758 |        -47.23 |        -132.96 |           85.73 |
| 06_inside_bar_break           | 1h_break_6bar_channel        |          3 |            240 |      248 |              1758 |        -63.3  |        -132.96 |           69.66 |
| 06_inside_bar_break           | dual_trend_plus_5m_activity  |          2 |            240 |       75 |              1867 |        -72.25 |        -140.98 |           68.73 |
| 06_inside_bar_break           | dual_trend_plus_5m_activity  |          3 |            120 |       74 |              1933 |        -65.15 |        -132.74 |           67.59 |
| 06_inside_bar_break           | 1h_trend_5m_vol_acceleration |          3 |            120 |      195 |              1933 |        -66.41 |        -132.74 |           66.33 |
| 06_inside_bar_break           | dual_trend_plus_5m_activity  |          2 |            120 |       75 |              1995 |        -70.57 |        -132.76 |           62.19 |
| 02_sweep_then_confirm         | 4h_break_6bar_channel        |          2 |            240 |      209 |              1786 |        -75.52 |        -135.42 |           59.9  |
| 06_inside_bar_break           | 1h_regime_expansion          |          2 |            240 |      201 |              1867 |        -81.48 |        -140.98 |           59.5  |
| 06_inside_bar_break           | 1h_quiet_then_5m_expansion   |          2 |            120 |      135 |              1995 |        -73.85 |        -132.76 |           58.91 |
| 06_inside_bar_break           | 1h_directional_high_volume   |          3 |            120 |      224 |              1933 |        -77.51 |        -132.74 |           55.23 |
| 06_inside_bar_break           | 1h_break_6bar_channel        |          2 |            240 |      254 |              1867 |        -86.19 |        -140.98 |           54.79 |
| 03_breakout_retest            | 1h_regime_expansion          |          2 |            120 |      109 |              1068 |        -71.04 |        -124.9  |           53.86 |
| 06_inside_bar_break           | 1h_trend_5m_vol_acceleration |          2 |            240 |      194 |              1867 |        -87.47 |        -140.98 |           53.51 |
| 04_trend_pullback_engulf      | 1h_quiet_then_5m_expansion   |          3 |            240 |      109 |              1761 |        -66.72 |        -119.98 |           53.26 |
| 07_failed_break_followthrough | 4h_trend_1h_pullback         |          3 |            240 |      108 |               871 |        -82.59 |        -134.73 |           52.14 |
| 06_inside_bar_break           | 1h_directional_high_volume   |          2 |            120 |      228 |              1995 |        -82.47 |        -132.76 |           50.29 |

## What cannot be claimed
- Unchanged Stage 11 structural 5m entry rules; only known-in-advance MTF market-state filters are added
- Completed 1H/4H candles, aligned to exact next-minute OPEN; prior 16 complete bars required to avoid stale gap joins
- 1H/4H structures, volume, slopes computed from historical completed candles only
- No time-of-day filter; entries can occur any day/hour
- Stops beyond confirmed setup levels, 2R/3R targets, <=4h holds
- Stop-first 1m OHLC tie; worse fill on stop gaps
- Separate strategy simulation per entry pattern/environment/R/hold; trades across models overlap
- 0.05% taker each side, 18% GST, 5-point adverse slippage per side
- Fee-offer sensitivity is conditional, not verified from historical executions
- No tick order book or realized bid/ask spread, market impact, margin, liquidation or funding cashflows
- Every 2026 period already investigated, not pristine independent validation
- Many comparisons cause selection bias; cannot guarantee positive expected results or no losses

Reproduce: scripts/research_pretrend_market_state_stage12.py; raw ledgers and
feature snapshots are stored as downloadable GitHub Actions artifacts.

