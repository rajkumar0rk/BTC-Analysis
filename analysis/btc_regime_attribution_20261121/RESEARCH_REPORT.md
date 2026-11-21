# BTCUSD 1H regime frequencies and conditional fixed-strategy backtest

## Method
Native 1M SHA256 and continuous timestamp audit passed. 1H state is determined only after signal-hour CLOSE. Entry at next native 1M OPEN. Every hour has one primary state; event flags may overlap.
Frozen baselines: EMA20/50 1H pullback; prior-24H closing Donchian breakout; Bollinger 20/2 reversion; failed prior-24H break. Fixed stop multiples/targets/timeouts documented in NOVELTY_CHECK.md. No parameter optimization.
One open trade per strategy, 1M stop-first OHLC replay, adverse stop gap fill, IST month-end flatten.
Hypothetical separate $10,000 account per strategy; risk 0.5% per trade capped at 3x notional; 0.05% taker each side + GST 18% and five price points adverse slippage each side.

## Data quality
{
  "exchange": "Delta Exchange India",
  "symbol": "BTCUSD",
  "minute_partitions": 23,
  "minute_bars": 992160,
  "first_utc": "2025-01-01 00:00:00+00:00",
  "last_utc": "2026-11-20 23:59:00+00:00",
  "verified_missing_minutes": 0,
  "hourly_bars": 16536,
  "classified_complete_month_hours": 15965,
  "fee_each_side_incl_gst": 0.00059,
  "slippage_each_side_btc_price_points": 5.0,
  "account_initial_usd": 10000.0,
  "stop_risk_fraction": 0.005,
  "leverage_cap": 3.0,
  "complete_IST_months": 22,
  "partial_Nov_2026_excluded": true,
  "is_2026_blind_holdout": false
}

## Share of available classified hours
| regime        |   hours |   pct_hours |
|:--------------|--------:|------------:|
| shock         |    1033 |       6.47  |
| breakout_up   |     217 |       1.359 |
| breakout_down |     259 |       1.622 |
| trend_up      |    1666 |      10.435 |
| trend_down    |    1781 |      11.156 |
| compression   |    1091 |       6.834 |
| range         |    2383 |      14.926 |
| mixed         |    7535 |      47.197 |

## Additional overlapping events
| event          |   hours |   pct_hours |
|:---------------|--------:|------------:|
| false_break    |    1375 |       8.613 |
| trend_pullback |    2505 |      15.691 |
| ema_reversal   |     315 |       1.973 |
| wick_rejection |    2589 |      16.217 |

## Separate baseline account results
| strategy            |   trades |   net_account_pct |   profitable_months |   losing_months |   idle_months |   max_trade_close_drawdown_pct |   profit_factor |
|:--------------------|---------:|------------------:|--------------------:|----------------:|--------------:|-------------------------------:|----------------:|
| trend_pullback      |      704 |           -49.342 |                   6 |              16 |             0 |                          51.04 |           0.738 |
| donchian_breakout   |      573 |           -13.23  |                   9 |              13 |             0 |                          18.92 |           0.931 |
| bollinger_reversion |     1523 |           -80.959 |                   1 |              21 |             0 |                          82.03 |           0.693 |
| failed_break_fade   |     1000 |           -54.307 |                   3 |              19 |             0 |                          56.98 |           0.774 |

## Entry regime conditional performance
| strategy            | regime        |   trades |   win_pct |   mean_net_R |   net_pnl_usd |   profit_factor |
|:--------------------|:--------------|---------:|----------:|-------------:|--------------:|----------------:|
| trend_pullback      | shock         |      110 |     32.73 |       -0.149 |       -611.14 |           0.799 |
| trend_pullback      | breakout_up   |        0 |    nan    |      nan     |          0    |         nan     |
| trend_pullback      | breakout_down |        0 |    nan    |      nan     |          0    |         nan     |
| trend_pullback      | trend_up      |       29 |     34.48 |       -0.189 |       -176.05 |           0.756 |
| trend_pullback      | trend_down    |       24 |     29.17 |       -0.278 |       -272.43 |           0.581 |
| trend_pullback      | compression   |       65 |     26.15 |       -0.355 |       -804.55 |           0.616 |
| trend_pullback      | range         |      124 |     27.42 |       -0.314 |      -1427.65 |           0.587 |
| trend_pullback      | mixed         |      352 |     34.09 |       -0.119 |      -1642.34 |           0.815 |
| donchian_breakout   | shock         |      233 |     37.77 |        0.094 |        932.69 |           1.13  |
| donchian_breakout   | breakout_up   |       82 |     20.73 |       -0.405 |      -1480.15 |           0.531 |
| donchian_breakout   | breakout_down |       82 |     28.05 |       -0.065 |       -298.03 |           0.896 |
| donchian_breakout   | trend_up      |       16 |     12.5  |       -0.871 |       -652.36 |           0.076 |
| donchian_breakout   | trend_down    |       17 |     41.18 |        0.185 |        129.73 |           1.26  |
| donchian_breakout   | compression   |        4 |     50    |       -0.071 |        -15.62 |           0.859 |
| donchian_breakout   | range         |       29 |     27.59 |       -0.05  |        -78.34 |           0.921 |
| donchian_breakout   | mixed         |      110 |     36.36 |        0.041 |        139.07 |           1.038 |
| bollinger_reversion | shock         |      171 |     43.86 |       -0.112 |       -242.24 |           0.911 |
| bollinger_reversion | breakout_up   |       22 |     36.36 |       -0.296 |       -245.42 |           0.531 |
| bollinger_reversion | breakout_down |       20 |     35    |       -0.278 |        -87.4  |           0.695 |
| bollinger_reversion | trend_up      |      195 |     37.95 |       -0.263 |      -1629.07 |           0.557 |
| bollinger_reversion | trend_down    |      223 |     41.7  |       -0.17  |       -788.88 |           0.791 |
| bollinger_reversion | compression   |       70 |     40    |       -0.322 |       -506.07 |           0.611 |
| bollinger_reversion | range         |      203 |     36.95 |       -0.298 |      -1862.93 |           0.535 |
| bollinger_reversion | mixed         |      619 |     41.52 |       -0.199 |      -2733.91 |           0.73  |
| failed_break_fade   | shock         |      133 |     46.62 |        0.068 |        431.2  |           1.152 |
| failed_break_fade   | breakout_up   |        0 |    nan    |      nan     |          0    |         nan     |
| failed_break_fade   | breakout_down |        0 |    nan    |      nan     |          0    |         nan     |
| failed_break_fade   | trend_up      |      163 |     42.94 |       -0.104 |       -810.25 |           0.782 |
| failed_break_fade   | trend_down    |      187 |     39.57 |       -0.179 |      -1123.19 |           0.755 |
| failed_break_fade   | compression   |       24 |     33.33 |       -0.372 |       -290.9  |           0.584 |
| failed_break_fade   | range         |       95 |     36.84 |       -0.184 |       -662.99 |           0.729 |
| failed_break_fade   | mixed         |      398 |     37.94 |       -0.214 |      -2974.62 |           0.694 |

## Every complete IST month, net account % per baseline
| month_ist   |   bollinger_reversion |   donchian_breakout |   failed_break_fade |   trend_pullback |
|:------------|----------------------:|--------------------:|--------------------:|-----------------:|
| 2025-01     |                 1.55  |              -0.899 |               2.677 |           -3.405 |
| 2025-02     |               -10.411 |              -0.712 |              -6.919 |            0.501 |
| 2025-03     |                -0.592 |              -0.729 |              -3.832 |           -3.378 |
| 2025-04     |                -8.524 |              -3.229 |               1.905 |           -3.727 |
| 2025-05     |                -5.941 |               1.18  |              -0.62  |           -6.462 |
| 2025-06     |                -2.443 |              -3.422 |              -0.257 |           -2.934 |
| 2025-07     |               -10.835 |              -6.5   |              -3.944 |           -8.201 |
| 2025-08     |               -10.871 |               1.805 |              -4.009 |            2.804 |
| 2025-09     |                -8.135 |               0.201 |              -0.113 |           -8.557 |
| 2025-10     |                -8.466 |               2.304 |              -4.857 |            4.457 |
| 2025-11     |                -5.732 |               0.3   |              -7.356 |            1.58  |
| 2025-12     |                -6.655 |              -5.357 |              -1.914 |           -8.007 |
| 2026-01     |                -8.381 |               8.485 |              -3.996 |            1.794 |
| 2026-02     |                -7.391 |               0.679 |              -3.222 |           -2.446 |
| 2026-03     |                -6.536 |               0.431 |              -3.889 |           -4.335 |
| 2026-04     |                -9.704 |              -0.915 |              -5.805 |           -3.205 |
| 2026-05     |                -9.626 |              -4.627 |               2.21  |           -6.61  |
| 2026-06     |                -6.549 |               5.522 |              -6.979 |            1.936 |
| 2026-07     |                -3.475 |              -0.018 |              -4.926 |           -7.971 |
| 2026-08     |                -6.218 |              -1.868 |              -7.906 |           -4.649 |
| 2026-09     |               -14.326 |              -3.251 |              -7.012 |           -3.132 |
| 2026-10     |                -9.056 |              -2.322 |              -5.077 |           -1.424 |

## Important limits
- Historical spreads/book depth, realized funding payments, financing, market impact and liquidation are not simulated. Tradeability not established.
- 2026 history was examined by earlier research and is not a pristine independent out-of-sample set.
- Price-action 'shock' is not proof of forced liquidations. 1H states depend on predeclared thresholds.
- Some regime-by-strategy cells have very small trade samples. Do not cherry-pick winner cells without independent testing.
- January 2025 begins at 00:00 UTC, so initial Jan 1 IST hours are not in the archive.
- November 2026 is incomplete and not counted as a full profitable or losing month.
