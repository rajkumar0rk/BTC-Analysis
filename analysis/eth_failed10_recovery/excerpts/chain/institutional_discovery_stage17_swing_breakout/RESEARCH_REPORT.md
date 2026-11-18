# Stage17 — Distinct multi-day BTC swing Donchian breakout and ATR trailing

## Predeclared strategy
4H 24/55-bar channel or 1D 20/55-bar channel close-break. Only new
crossings count. Optional EMA50 confirmation, 2x ATR initial stop,
3x/4x ATR trailing after each completed signal-timeframe candle,
opposite breakout exit or 14-day time cap. One position at a time.

## Monthly account-style method
All trades sized at hypothetical 0.5% of account per initial 1R.
Monthly NAV marked to market on last observed minute IST,
including estimated round-trip liquidation fees and adverse slippage.
This prevents a multi-day open winner from appearing as an
artificial zero-trade month; monthly inactive means no position held.

**Monthly-profit criteria passed: 0/16**

## Full comparison
| model                                    | timeframe   |   channel_lookback | trend           |   trail_ATR |   signals_seen |   trades |   max_trade_to_trade_drawdown_pct |   total_return_pct |   last_month_valuation |   profit_2025 |   loss_2025 |   inactive_2025 |   active_2025 |   return_2025_pct |   profit_2026 |   loss_2026 |   inactive_2026 |   active_2026 |   return_2026_pct | monthly_gate_pass   |
|:-----------------------------------------|:------------|-------------------:|:----------------|------------:|---------------:|---------:|----------------------------------:|-------------------:|-----------------------:|--------------:|------------:|----------------:|--------------:|------------------:|--------------:|------------:|----------------:|--------------:|------------------:|:--------------------|
| 1D_channel_20_ema50_agrees_trail_3atr    | 1D          |                 20 | ema50_agrees    |           3 |             37 |       15 |                             1.125 |              3.818 |                103.818 |             2 |           3 |               7 |             5 |             1.092 |             9 |           1 |               1 |            10 |             2.696 | False               |
| 1D_channel_20_ema50_agrees_trail_4atr    | 1D          |                 20 | ema50_agrees    |           4 |             37 |       15 |                             1.125 |              4     |                104     |             2 |           3 |               7 |             5 |             1.092 |             9 |           1 |               1 |            10 |             2.876 | False               |
| 1D_channel_20_no_trend_filter_trail_3atr | 1D          |                 20 | no_trend_filter |           3 |             40 |       17 |                             1.446 |              2.957 |                102.957 |             3 |           3 |               6 |             6 |             0.765 |             9 |           2 |               0 |            11 |             2.176 | False               |
| 1D_channel_20_no_trend_filter_trail_4atr | 1D          |                 20 | no_trend_filter |           4 |             40 |       17 |                             1.627 |              2.948 |                102.948 |             3 |           3 |               6 |             6 |             0.58  |             9 |           2 |               0 |            11 |             2.355 | False               |
| 1D_channel_55_ema50_agrees_trail_3atr    | 1D          |                 55 | ema50_agrees    |           3 |             25 |        9 |                             0.666 |              3.868 |                103.868 |             2 |           1 |               9 |             3 |             2.285 |             7 |           2 |               2 |             9 |             1.548 | False               |
| 1D_channel_55_ema50_agrees_trail_4atr    | 1D          |                 55 | ema50_agrees    |           4 |             25 |        9 |                             0.666 |              4.05  |                104.05  |             2 |           1 |               9 |             3 |             2.285 |             7 |           2 |               2 |             9 |             1.726 | False               |
| 1D_channel_55_no_trend_filter_trail_3atr | 1D          |                 55 | no_trend_filter |           3 |             25 |        9 |                             0.666 |              3.868 |                103.868 |             2 |           1 |               9 |             3 |             2.285 |             7 |           2 |               2 |             9 |             1.548 | False               |
| 1D_channel_55_no_trend_filter_trail_4atr | 1D          |                 55 | no_trend_filter |           4 |             25 |        9 |                             0.666 |              4.05  |                104.05  |             2 |           1 |               9 |             3 |             2.285 |             7 |           2 |               2 |             9 |             1.726 | False               |
| 4H_channel_24_ema50_agrees_trail_3atr    | 4H          |                 24 | ema50_agrees    |           3 |            208 |       99 |                             8.915 |             14.533 |                114.533 |             7 |           5 |               0 |            12 |             6.096 |             4 |           7 |               0 |            11 |             7.952 | False               |
| 4H_channel_24_ema50_agrees_trail_4atr    | 4H          |                 24 | ema50_agrees    |           4 |            208 |       91 |                             7.551 |             13.806 |                113.806 |             7 |           5 |               0 |            12 |             3.453 |             5 |           6 |               0 |            11 |            10.008 | False               |
| 4H_channel_24_no_trend_filter_trail_3atr | 4H          |                 24 | no_trend_filter |           3 |            222 |      106 |                             8.915 |             14.154 |                114.154 |             7 |           5 |               0 |            12 |             5.206 |             4 |           7 |               0 |            11 |             8.505 | False               |
| 4H_channel_24_no_trend_filter_trail_4atr | 4H          |                 24 | no_trend_filter |           4 |            222 |       94 |                             7.551 |             13.937 |                113.937 |             7 |           5 |               0 |            12 |             4.277 |             4 |           7 |               0 |            11 |             9.264 | False               |
| 4H_channel_55_ema50_agrees_trail_3atr    | 4H          |                 55 | ema50_agrees    |           3 |            139 |       65 |                             5.926 |              8.343 |                108.344 |             5 |           7 |               0 |            12 |             6.022 |             4 |           7 |               0 |            11 |             2.19  | False               |
| 4H_channel_55_ema50_agrees_trail_4atr    | 4H          |                 55 | ema50_agrees    |           4 |            139 |       63 |                             6.649 |              5.474 |                105.474 |             5 |           7 |               0 |            12 |             2.284 |             6 |           5 |               0 |            11 |             3.119 | False               |
| 4H_channel_55_no_trend_filter_trail_3atr | 4H          |                 55 | no_trend_filter |           3 |            140 |       65 |                             5.926 |              8.958 |                108.958 |             5 |           7 |               0 |            12 |             6.022 |             4 |           7 |               0 |            11 |             2.769 | False               |
| 4H_channel_55_no_trend_filter_trail_4atr | 4H          |                 55 | no_trend_filter |           4 |            140 |       63 |                             6.649 |              6.011 |                106.011 |             5 |           7 |               0 |            12 |             2.284 |             6 |           5 |               0 |            11 |             3.643 | False               |

## Month-by-month top three 2025-ranked models
| model                                    | month_ist   |   signals_seen |   entries |   market_exposure |   month_return_pct |   month_end_equity | status   |
|:-----------------------------------------|:------------|---------------:|----------:|------------------:|-------------------:|-------------------:|:---------|
| 4H_channel_24_no_trend_filter_trail_3atr | 2025-01     |            222 |         2 |                 1 |            -0.2187 |            99.7813 | Loss     |
| 4H_channel_24_no_trend_filter_trail_3atr | 2025-02     |            222 |         4 |                 1 |             0.2739 |           100.055  | Profit   |
| 4H_channel_24_no_trend_filter_trail_3atr | 2025-03     |            222 |         5 |                 1 |            -0.9273 |            99.1268 | Loss     |
| 4H_channel_24_no_trend_filter_trail_3atr | 2025-04     |            222 |         5 |                 1 |            -1.8344 |            97.3084 | Loss     |
| 4H_channel_24_no_trend_filter_trail_3atr | 2025-05     |            222 |         6 |                 1 |             1.1607 |            98.4379 | Profit   |
| 4H_channel_24_no_trend_filter_trail_3atr | 2025-06     |            222 |         5 |                 1 |            -1.0405 |            97.4136 | Loss     |
| 4H_channel_24_no_trend_filter_trail_3atr | 2025-07     |            222 |         3 |                 1 |             4.9958 |           102.28   | Profit   |
| 4H_channel_24_no_trend_filter_trail_3atr | 2025-08     |            222 |         4 |                 1 |             1.1666 |           103.473  | Profit   |
| 4H_channel_24_no_trend_filter_trail_3atr | 2025-09     |            222 |         3 |                 1 |             1.2677 |           104.785  | Profit   |
| 4H_channel_24_no_trend_filter_trail_3atr | 2025-10     |            222 |         4 |                 1 |             2.2928 |           107.188  | Profit   |
| 4H_channel_24_no_trend_filter_trail_3atr | 2025-11     |            222 |         3 |                 1 |             1.2397 |           108.516  | Profit   |
| 4H_channel_24_no_trend_filter_trail_3atr | 2025-12     |            222 |         8 |                 1 |            -3.0504 |           105.206  | Loss     |
| 4H_channel_24_no_trend_filter_trail_3atr | 2026-01     |            222 |         5 |                 1 |             4.1771 |           109.601  | Profit   |
| 4H_channel_24_no_trend_filter_trail_3atr | 2026-02     |            222 |         5 |                 1 |            -1.6113 |           107.835  | Loss     |
| 4H_channel_24_no_trend_filter_trail_3atr | 2026-03     |            222 |         4 |                 1 |            -0.8077 |           106.964  | Loss     |
| 4H_channel_24_no_trend_filter_trail_3atr | 2026-04     |            222 |         7 |                 1 |            -2.4103 |           104.386  | Loss     |
| 4H_channel_24_no_trend_filter_trail_3atr | 2026-05     |            222 |         8 |                 1 |            -2.6822 |           101.586  | Loss     |
| 4H_channel_24_no_trend_filter_trail_3atr | 2026-06     |            222 |         4 |                 1 |             2.7915 |           104.422  | Profit   |
| 4H_channel_24_no_trend_filter_trail_3atr | 2026-07     |            222 |         6 |                 1 |            -1.8933 |           102.445  | Loss     |
| 4H_channel_24_no_trend_filter_trail_3atr | 2026-08     |            222 |         4 |                 1 |            12.5378 |           115.289  | Profit   |
| 4H_channel_24_no_trend_filter_trail_3atr | 2026-09     |            222 |         4 |                 1 |            -1.539  |           113.515  | Loss     |
| 4H_channel_24_no_trend_filter_trail_3atr | 2026-10     |            222 |         6 |                 1 |            -1.7227 |           111.559  | Loss     |
| 4H_channel_24_no_trend_filter_trail_3atr | 2026-11     |            222 |         2 |                 1 |             2.3262 |           114.154  | Profit   |
| 4H_channel_24_ema50_agrees_trail_3atr    | 2025-01     |            208 |         2 |                 1 |            -0.2187 |            99.7813 | Loss     |
| 4H_channel_24_ema50_agrees_trail_3atr    | 2025-02     |            208 |         3 |                 1 |             0.6629 |           100.443  | Profit   |
| 4H_channel_24_ema50_agrees_trail_3atr    | 2025-03     |            208 |         4 |                 1 |            -0.4192 |           100.022  | Loss     |
| 4H_channel_24_ema50_agrees_trail_3atr    | 2025-04     |            208 |         4 |                 1 |            -1.326  |            98.6954 | Loss     |
| 4H_channel_24_ema50_agrees_trail_3atr    | 2025-05     |            208 |         5 |                 1 |             1.6837 |           100.357  | Profit   |
| 4H_channel_24_ema50_agrees_trail_3atr    | 2025-06     |            208 |         5 |                 1 |            -1.0405 |            99.3129 | Loss     |
| 4H_channel_24_ema50_agrees_trail_3atr    | 2025-07     |            208 |         3 |                 1 |             4.9958 |           104.274  | Profit   |
| 4H_channel_24_ema50_agrees_trail_3atr    | 2025-08     |            208 |         4 |                 1 |             0.9426 |           105.257  | Profit   |
| 4H_channel_24_ema50_agrees_trail_3atr    | 2025-09     |            208 |         3 |                 1 |             1.0283 |           106.34   | Profit   |
| 4H_channel_24_ema50_agrees_trail_3atr    | 2025-10     |            208 |         5 |                 1 |             1.0433 |           107.449  | Profit   |
| 4H_channel_24_ema50_agrees_trail_3atr    | 2025-11     |            208 |         2 |                 1 |             1.5231 |           109.086  | Profit   |
| 4H_channel_24_ema50_agrees_trail_3atr    | 2025-12     |            208 |         7 |                 1 |            -2.7408 |           106.096  | Loss     |
| 4H_channel_24_ema50_agrees_trail_3atr    | 2026-01     |            208 |         5 |                 1 |             3.1455 |           109.433  | Profit   |
| 4H_channel_24_ema50_agrees_trail_3atr    | 2026-02     |            208 |         5 |                 1 |            -1.6113 |           107.67   | Loss     |
| 4H_channel_24_ema50_agrees_trail_3atr    | 2026-03     |            208 |         4 |                 1 |            -0.8077 |           106.8    | Loss     |
| 4H_channel_24_ema50_agrees_trail_3atr    | 2026-04     |            208 |         7 |                 1 |            -2.4103 |           104.226  | Loss     |
| 4H_channel_24_ema50_agrees_trail_3atr    | 2026-05     |            208 |         8 |                 1 |            -2.6822 |           101.43   | Loss     |
| 4H_channel_24_ema50_agrees_trail_3atr    | 2026-06     |            208 |         3 |                 1 |             2.7462 |           104.216  | Profit   |
| 4H_channel_24_ema50_agrees_trail_3atr    | 2026-07     |            208 |         5 |                 1 |            -1.3826 |           102.775  | Loss     |
| 4H_channel_24_ema50_agrees_trail_3atr    | 2026-08     |            208 |         4 |                 1 |            12.5483 |           115.671  | Profit   |
| 4H_channel_24_ema50_agrees_trail_3atr    | 2026-09     |            208 |         4 |                 1 |            -1.539  |           113.891  | Loss     |
| 4H_channel_24_ema50_agrees_trail_3atr    | 2026-10     |            208 |         6 |                 1 |            -1.7227 |           111.929  | Loss     |
| 4H_channel_24_ema50_agrees_trail_3atr    | 2026-11     |            208 |         2 |                 1 |             2.3262 |           114.533  | Profit   |
| 4H_channel_24_ema50_agrees_trail_4atr    | 2025-01     |            208 |         2 |                 1 |            -0.4964 |            99.5036 | Loss     |
| 4H_channel_24_ema50_agrees_trail_4atr    | 2025-02     |            208 |         3 |                 1 |             0.8786 |           100.378  | Profit   |
| 4H_channel_24_ema50_agrees_trail_4atr    | 2025-03     |            208 |         4 |                 1 |            -0.853  |            99.5216 | Loss     |
| 4H_channel_24_ema50_agrees_trail_4atr    | 2025-04     |            208 |         4 |                 1 |            -1.6374 |            97.892  | Loss     |
| 4H_channel_24_ema50_agrees_trail_4atr    | 2025-05     |            208 |         3 |                 1 |             2.1776 |           100.024  | Profit   |
| 4H_channel_24_ema50_agrees_trail_4atr    | 2025-06     |            208 |         5 |                 1 |            -1.67   |            98.3533 | Loss     |
| 4H_channel_24_ema50_agrees_trail_4atr    | 2025-07     |            208 |         3 |                 1 |             4.6925 |           102.969  | Profit   |
| 4H_channel_24_ema50_agrees_trail_4atr    | 2025-08     |            208 |         4 |                 1 |             0.2267 |           103.202  | Profit   |
| 4H_channel_24_ema50_agrees_trail_4atr    | 2025-09     |            208 |         3 |                 1 |             0.2886 |           103.5    | Profit   |
| 4H_channel_24_ema50_agrees_trail_4atr    | 2025-10     |            208 |         4 |                 1 |             1.9406 |           105.508  | Profit   |
| 4H_channel_24_ema50_agrees_trail_4atr    | 2025-11     |            208 |         2 |                 1 |             1.1257 |           106.696  | Profit   |
| 4H_channel_24_ema50_agrees_trail_4atr    | 2025-12     |            208 |         6 |                 1 |            -3.0399 |           103.453  | Loss     |
| 4H_channel_24_ema50_agrees_trail_4atr    | 2026-01     |            208 |         5 |                 1 |             2.3796 |           105.914  | Profit   |
| 4H_channel_24_ema50_agrees_trail_4atr    | 2026-02     |            208 |         4 |                 1 |            -0.389  |           105.502  | Loss     |
| 4H_channel_24_ema50_agrees_trail_4atr    | 2026-03     |            208 |         4 |                 1 |            -1.0898 |           104.353  | Loss     |
| 4H_channel_24_ema50_agrees_trail_4atr    | 2026-04     |            208 |         6 |                 1 |            -1.1456 |           103.157  | Loss     |
| 4H_channel_24_ema50_agrees_trail_4atr    | 2026-05     |            208 |         8 |                 1 |            -2.8274 |           100.24   | Loss     |
| 4H_channel_24_ema50_agrees_trail_4atr    | 2026-06     |            208 |         3 |                 1 |             2.9031 |           103.151  | Profit   |
| 4H_channel_24_ema50_agrees_trail_4atr    | 2026-07     |            208 |         3 |                 1 |             0.1305 |           103.285  | Profit   |
| 4H_channel_24_ema50_agrees_trail_4atr    | 2026-08     |            208 |         4 |                 1 |            11.7463 |           115.417  | Profit   |
| 4H_channel_24_ema50_agrees_trail_4atr    | 2026-09     |            208 |         4 |                 1 |            -1.3317 |           113.88   | Loss     |
| 4H_channel_24_ema50_agrees_trail_4atr    | 2026-10     |            208 |         6 |                 1 |            -1.9242 |           111.689  | Loss     |
| 4H_channel_24_ema50_agrees_trail_4atr    | 2026-11     |            208 |         2 |                 1 |             1.8955 |           113.806  | Profit   |

## Research caveats
- All 2025 and 2026 are research-exposed; no new forward holdout
- 2026-10-31 source missing; 2026-11 incomplete through Nov16
- Month-end marks on last available minute, not necessarily an executable liquidation
- Exact fractional position size assumed; real minimum contract, leverage and margin can differ
- Trading fees/GST and assumed slippage included, not actual quote spread/market depth/funding
- Losses may exceed initial risk in adverse gap fills; no guaranteed monthly profit
- No fixed monthly exit; month returns reflect mark-to-market unrealized PnL
- One position at a time across LONG and SHORT; no concurrent trades
- Signal on FULL completed 4H or Daily candle, next 1m open execution
- A missing source day triggers a conservative forced exit on last observed candle
- 16 configurations create multiple testing risk; any attractive result remains exploratory

Reproduce with scripts/research_swing_donchian_stage17.py.
