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
| pattern                  | environment                 |   reward_R |   hold_minutes |   trades |   win_pct |   avg_net_pts |   profit_factor |   avg_risk_pts |
|:-------------------------|:----------------------------|-----------:|---------------:|---------:|----------:|--------------:|----------------:|---------------:|
| 03_breakout_retest       | 1h_directional_high_volume  |          3 |            120 |       83 |     40.96 |         67.75 |           1.185 |         619.64 |
| 03_breakout_retest       | 1h_4h_slope_agrees          |          2 |            240 |      105 |     45.71 |         67.6  |           1.186 |         584.47 |
| 06_inside_bar_break      | dual_trend_plus_5m_activity |          2 |            240 |       87 |     45.98 |         62.67 |           1.175 |         639.66 |
| 03_breakout_retest       | 1h_directional_high_volume  |          3 |            240 |       82 |     37.8  |         61.56 |           1.147 |         613.11 |
| 03_breakout_retest       | 1h_directional_high_volume  |          2 |            120 |       84 |     44.05 |         47.01 |           1.134 |         621.23 |
| 06_inside_bar_break      | dual_trend_plus_5m_activity |          3 |            240 |       87 |     39.08 |         40.37 |           1.105 |         639.66 |
| 06_inside_bar_break      | dual_trend_plus_5m_activity |          2 |            120 |       88 |     45.45 |         33.23 |           1.102 |         636.46 |
| 03_breakout_retest       | 1h_directional_high_volume  |          2 |            240 |       84 |     41.67 |         29.53 |           1.074 |         621.23 |
| 03_breakout_retest       | 1h_4h_slope_agrees          |          2 |            120 |      108 |     43.52 |         25.09 |           1.077 |         579.73 |
| 03_breakout_retest       | 1h_4h_slope_agrees          |          3 |            240 |      102 |     38.24 |         21.02 |           1.052 |         577.57 |
| 04_trend_pullback_engulf | dual_trend_plus_5m_activity |          3 |            240 |       91 |     32.97 |         18.35 |           1.043 |         576.51 |
| 04_trend_pullback_engulf | dual_trend_plus_5m_activity |          3 |            120 |       91 |     36.26 |         12.09 |           1.031 |         576.51 |

## Those exact selections in the research-exposed 2026 periods
| pattern                  | environment                 |   reward_R |   hold_minutes | period                      |   trades |   win_pct |   avg_net_pts |   profit_factor |
|:-------------------------|:----------------------------|-----------:|---------------:|:----------------------------|---------:|----------:|--------------:|----------------:|
| 03_breakout_retest       | 1h_4h_slope_agrees          |          2 |            120 | 2026_H1_validation          |       28 |     21.43 |       -176.17 |           0.469 |
| 03_breakout_retest       | 1h_4h_slope_agrees          |          2 |            120 | 2026_H2_seen_recheck        |       20 |     30    |       -120.07 |           0.528 |
| 03_breakout_retest       | 1h_4h_slope_agrees          |          2 |            120 | 2026_Nov_recent_exploratory |        3 |      0    |       -316.38 |           0     |
| 03_breakout_retest       | 1h_4h_slope_agrees          |          2 |            240 | 2026_H1_validation          |       27 |     18.52 |       -172.55 |           0.501 |
| 03_breakout_retest       | 1h_4h_slope_agrees          |          2 |            240 | 2026_H2_seen_recheck        |       20 |     25    |       -126.91 |           0.507 |
| 03_breakout_retest       | 1h_4h_slope_agrees          |          2 |            240 | 2026_Nov_recent_exploratory |        3 |      0    |       -529.38 |           0     |
| 03_breakout_retest       | 1h_4h_slope_agrees          |          3 |            240 | 2026_H1_validation          |       27 |     18.52 |       -144.1  |           0.583 |
| 03_breakout_retest       | 1h_4h_slope_agrees          |          3 |            240 | 2026_H2_seen_recheck        |       20 |     25    |       -100.37 |           0.61  |
| 03_breakout_retest       | 1h_4h_slope_agrees          |          3 |            240 | 2026_Nov_recent_exploratory |        3 |      0    |       -529.38 |           0     |
| 03_breakout_retest       | 1h_directional_high_volume  |          2 |            120 | 2026_H1_validation          |       29 |     37.93 |        -93.56 |           0.675 |
| 03_breakout_retest       | 1h_directional_high_volume  |          2 |            120 | 2026_H2_seen_recheck        |       15 |     33.33 |       -129.82 |           0.454 |
| 03_breakout_retest       | 1h_directional_high_volume  |          2 |            120 | 2026_Nov_recent_exploratory |        2 |     50    |        196.09 |           2.366 |
| 03_breakout_retest       | 1h_directional_high_volume  |          2 |            240 | 2026_H1_validation          |       29 |     24.14 |       -136.5  |           0.598 |
| 03_breakout_retest       | 1h_directional_high_volume  |          2 |            240 | 2026_H2_seen_recheck        |       15 |     33.33 |       -122.05 |           0.526 |
| 03_breakout_retest       | 1h_directional_high_volume  |          2 |            240 | 2026_Nov_recent_exploratory |        2 |     50    |        196.09 |           2.366 |
| 03_breakout_retest       | 1h_directional_high_volume  |          3 |            120 | 2026_H1_validation          |       28 |     32.14 |       -212.91 |           0.359 |
| 03_breakout_retest       | 1h_directional_high_volume  |          3 |            120 | 2026_H2_seen_recheck        |       15 |     33.33 |       -149.6  |           0.371 |
| 03_breakout_retest       | 1h_directional_high_volume  |          3 |            120 | 2026_Nov_recent_exploratory |        2 |     50    |        -96.52 |           0.328 |
| 03_breakout_retest       | 1h_directional_high_volume  |          3 |            240 | 2026_H1_validation          |       28 |     14.29 |       -292.98 |           0.257 |
| 03_breakout_retest       | 1h_directional_high_volume  |          3 |            240 | 2026_H2_seen_recheck        |       15 |     33.33 |       -126.21 |           0.509 |
| 03_breakout_retest       | 1h_directional_high_volume  |          3 |            240 | 2026_Nov_recent_exploratory |        2 |      0    |       -334.97 |           0     |
| 04_trend_pullback_engulf | dual_trend_plus_5m_activity |          3 |            120 | 2026_H1_validation          |       40 |     50    |        109.65 |           1.51  |
| 04_trend_pullback_engulf | dual_trend_plus_5m_activity |          3 |            120 | 2026_H2_seen_recheck        |       22 |     27.27 |       -131.34 |           0.495 |
| 04_trend_pullback_engulf | dual_trend_plus_5m_activity |          3 |            240 | 2026_H1_validation          |       39 |     51.28 |        150.99 |           1.627 |
| 04_trend_pullback_engulf | dual_trend_plus_5m_activity |          3 |            240 | 2026_H2_seen_recheck        |       22 |     31.82 |        -96.87 |           0.631 |
| 06_inside_bar_break      | dual_trend_plus_5m_activity |          2 |            120 | 2026_H1_validation          |       38 |     42.11 |         74.67 |           1.306 |
| 06_inside_bar_break      | dual_trend_plus_5m_activity |          2 |            120 | 2026_H2_seen_recheck        |       18 |     44.44 |         29.08 |           1.126 |
| 06_inside_bar_break      | dual_trend_plus_5m_activity |          2 |            120 | 2026_Nov_recent_exploratory |        2 |      0    |       -469.88 |           0     |
| 06_inside_bar_break      | dual_trend_plus_5m_activity |          2 |            240 | 2026_H1_validation          |       38 |     42.11 |         86.56 |           1.327 |
| 06_inside_bar_break      | dual_trend_plus_5m_activity |          2 |            240 | 2026_H2_seen_recheck        |       18 |     44.44 |          9.66 |           1.04  |
| 06_inside_bar_break      | dual_trend_plus_5m_activity |          2 |            240 | 2026_Nov_recent_exploratory |        2 |      0    |       -551.84 |           0     |
| 06_inside_bar_break      | dual_trend_plus_5m_activity |          3 |            240 | 2026_H1_validation          |       37 |     35.14 |         86.91 |           1.304 |
| 06_inside_bar_break      | dual_trend_plus_5m_activity |          3 |            240 | 2026_H2_seen_recheck        |       18 |     33.33 |       -156.66 |           0.472 |
| 06_inside_bar_break      | dual_trend_plus_5m_activity |          3 |            240 | 2026_Nov_recent_exploratory |        2 |      0    |       -551.84 |           0     |

## Stable-positive filters (>=60/30/20 trades across 2025, H1 and H2)
No repeated positive setup at the chosen minimum sample sizes.

## How much did MTF filtering change net expectancy versus the same unfiltered entry?
| pattern                  | environment                 |   reward_R |   hold_minutes |   trades |   baseline_trades |   avg_net_pts |   baseline_net |   delta_net_pts |
|:-------------------------|:----------------------------|-----------:|---------------:|---------:|------------------:|--------------:|---------------:|----------------:|
| 03_breakout_retest       | 1h_4h_slope_agrees          |          2 |            240 |      105 |               859 |         67.6  |        -119.9  |          187.5  |
| 03_breakout_retest       | 1h_directional_high_volume  |          3 |            120 |       83 |               878 |         67.75 |        -113.67 |          181.42 |
| 03_breakout_retest       | 1h_directional_high_volume  |          2 |            120 |       84 |               887 |         47.01 |        -118.57 |          165.58 |
| 03_breakout_retest       | 1h_directional_high_volume  |          3 |            240 |       82 |               840 |         61.56 |        -102.11 |          163.67 |
| 06_inside_bar_break      | dual_trend_plus_5m_activity |          2 |            240 |       87 |              1938 |         62.67 |         -94.54 |          157.21 |
| 03_breakout_retest       | 1h_directional_high_volume  |          2 |            240 |       84 |               859 |         29.53 |        -119.9  |          149.43 |
| 06_inside_bar_break      | dual_trend_plus_5m_activity |          3 |            240 |       87 |              1798 |         40.37 |        -104.78 |          145.15 |
| 03_breakout_retest       | 1h_4h_slope_agrees          |          2 |            120 |      108 |               887 |         25.09 |        -118.57 |          143.66 |
| 06_inside_bar_break      | dual_trend_plus_5m_activity |          2 |            120 |       88 |              2085 |         33.23 |         -98.55 |          131.78 |
| 03_breakout_retest       | 1h_4h_slope_agrees          |          3 |            240 |      102 |               840 |         21.02 |        -102.11 |          123.13 |
| 04_trend_pullback_engulf | dual_trend_plus_5m_activity |          3 |            240 |       91 |              2002 |         18.35 |        -102.14 |          120.49 |
| 03_breakout_retest       | 1h_4h_slope_agrees          |          3 |            120 |      107 |               878 |          2.25 |        -113.67 |          115.92 |
| 06_inside_bar_break      | 1h_regime_expansion         |          3 |            240 |      156 |              1798 |          4.1  |        -104.78 |          108.88 |
| 04_trend_pullback_engulf | dual_trend_plus_5m_activity |          3 |            120 |       91 |              2055 |         12.09 |         -96.07 |          108.16 |
| 03_breakout_retest       | 1h_regime_expansion         |          2 |            120 |       65 |               887 |        -30.58 |        -118.57 |           87.99 |
| 06_inside_bar_break      | 1h_regime_expansion         |          2 |            240 |      159 |              1938 |        -13.58 |         -94.54 |           80.96 |
| 06_inside_bar_break      | dual_trend_plus_5m_activity |          3 |            120 |       88 |              2012 |        -26    |        -106.93 |           80.93 |
| 03_breakout_retest       | 1h_regime_expansion         |          3 |            120 |       64 |               878 |        -33.65 |        -113.67 |           80.02 |
| 02_sweep_then_confirm    | 1h_directional_high_volume  |          3 |            120 |       78 |              2015 |        -35.31 |        -114.42 |           79.11 |
| 01_sweep_rejection       | 1h_directional_high_volume  |          3 |            120 |      130 |              2996 |        -36.32 |        -111.79 |           75.47 |

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

