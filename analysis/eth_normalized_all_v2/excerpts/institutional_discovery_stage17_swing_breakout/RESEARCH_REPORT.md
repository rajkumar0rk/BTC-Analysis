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
| 1D_channel_20_ema50_agrees_trail_3atr    | 1D          |                 20 | ema50_agrees    |           3 |             34 |       14 |                             1.125 |              3.532 |                103.531 |             2 |           3 |               7 |             5 |             1.092 |             9 |           1 |               1 |            10 |             2.413 | False               |
| 1D_channel_20_ema50_agrees_trail_4atr    | 1D          |                 20 | ema50_agrees    |           4 |             34 |       14 |                             1.125 |              3.713 |                103.713 |             2 |           3 |               7 |             5 |             1.092 |             9 |           1 |               1 |            10 |             2.592 | False               |
| 1D_channel_20_no_trend_filter_trail_3atr | 1D          |                 20 | no_trend_filter |           3 |             37 |       16 |                             1.446 |              2.673 |                102.673 |             3 |           3 |               6 |             6 |             0.765 |             9 |           2 |               0 |            11 |             1.894 | False               |
| 1D_channel_20_no_trend_filter_trail_4atr | 1D          |                 20 | no_trend_filter |           4 |             37 |       16 |                             1.627 |              2.665 |                102.665 |             3 |           3 |               6 |             6 |             0.58  |             9 |           2 |               0 |            11 |             2.073 | False               |
| 1D_channel_55_ema50_agrees_trail_3atr    | 1D          |                 55 | ema50_agrees    |           3 |             22 |        8 |                             0.507 |              3.582 |                103.582 |             2 |           1 |               9 |             3 |             2.285 |             7 |           2 |               2 |             9 |             1.268 | False               |
| 1D_channel_55_ema50_agrees_trail_4atr    | 1D          |                 55 | ema50_agrees    |           4 |             22 |        8 |                             0.507 |              3.764 |                103.764 |             2 |           1 |               9 |             3 |             2.285 |             7 |           2 |               2 |             9 |             1.445 | False               |
| 1D_channel_55_no_trend_filter_trail_3atr | 1D          |                 55 | no_trend_filter |           3 |             22 |        8 |                             0.507 |              3.582 |                103.582 |             2 |           1 |               9 |             3 |             2.285 |             7 |           2 |               2 |             9 |             1.268 | False               |
| 1D_channel_55_no_trend_filter_trail_4atr | 1D          |                 55 | no_trend_filter |           4 |             22 |        8 |                             0.507 |              3.764 |                103.764 |             2 |           1 |               9 |             3 |             2.285 |             7 |           2 |               2 |             9 |             1.445 | False               |
| 4H_channel_24_ema50_agrees_trail_3atr    | 4H          |                 24 | ema50_agrees    |           3 |            201 |       97 |                             8.915 |             11.933 |                111.933 |             7 |           5 |               0 |            12 |             6.096 |             4 |           7 |               0 |            11 |             5.502 | False               |
| 4H_channel_24_ema50_agrees_trail_4atr    | 4H          |                 24 | ema50_agrees    |           4 |            201 |       89 |                             7.551 |             11.693 |                111.693 |             7 |           5 |               0 |            12 |             3.453 |             5 |           6 |               0 |            11 |             7.965 | False               |
| 4H_channel_24_no_trend_filter_trail_3atr | 4H          |                 24 | no_trend_filter |           3 |            215 |      104 |                             8.915 |             11.563 |                111.563 |             7 |           5 |               0 |            12 |             5.206 |             4 |           7 |               0 |            11 |             6.042 | False               |
| 4H_channel_24_no_trend_filter_trail_4atr | 4H          |                 24 | no_trend_filter |           4 |            215 |       92 |                             7.551 |             11.822 |                111.822 |             7 |           5 |               0 |            12 |             4.277 |             4 |           7 |               0 |            11 |             7.236 | False               |
| 4H_channel_55_ema50_agrees_trail_3atr    | 4H          |                 55 | ema50_agrees    |           3 |            132 |       63 |                             5.926 |              6.217 |                106.216 |             5 |           7 |               0 |            12 |             6.022 |             4 |           7 |               0 |            11 |             0.183 | False               |
| 4H_channel_55_ema50_agrees_trail_4atr    | 4H          |                 55 | ema50_agrees    |           4 |            132 |       61 |                             6.649 |              3.52  |                103.52  |             5 |           7 |               0 |            12 |             2.284 |             6 |           5 |               0 |            11 |             1.209 | False               |
| 4H_channel_55_no_trend_filter_trail_3atr | 4H          |                 55 | no_trend_filter |           3 |            133 |       63 |                             5.926 |              6.819 |                106.819 |             5 |           7 |               0 |            12 |             6.022 |             4 |           7 |               0 |            11 |             0.751 | False               |
| 4H_channel_55_no_trend_filter_trail_4atr | 4H          |                 55 | no_trend_filter |           4 |            133 |       61 |                             6.649 |              4.047 |                104.047 |             5 |           7 |               0 |            12 |             2.284 |             6 |           5 |               0 |            11 |             1.723 | False               |

## Month-by-month top three 2025-ranked models
| model                                    | month_ist   |   signals_seen |   entries |   market_exposure |   month_return_pct |   month_end_equity | status   |
|:-----------------------------------------|:------------|---------------:|----------:|------------------:|-------------------:|-------------------:|:---------|
| 4H_channel_24_no_trend_filter_trail_3atr | 2025-01     |            215 |         2 |                 1 |            -0.2187 |            99.7813 | Loss     |
| 4H_channel_24_no_trend_filter_trail_3atr | 2025-02     |            215 |         4 |                 1 |             0.2739 |           100.055  | Profit   |
| 4H_channel_24_no_trend_filter_trail_3atr | 2025-03     |            215 |         5 |                 1 |            -0.9273 |            99.1268 | Loss     |
| 4H_channel_24_no_trend_filter_trail_3atr | 2025-04     |            215 |         5 |                 1 |            -1.8344 |            97.3084 | Loss     |
| 4H_channel_24_no_trend_filter_trail_3atr | 2025-05     |            215 |         6 |                 1 |             1.1607 |            98.4379 | Profit   |
| 4H_channel_24_no_trend_filter_trail_3atr | 2025-06     |            215 |         5 |                 1 |            -1.0405 |            97.4136 | Loss     |
| 4H_channel_24_no_trend_filter_trail_3atr | 2025-07     |            215 |         3 |                 1 |             4.9958 |           102.28   | Profit   |
| 4H_channel_24_no_trend_filter_trail_3atr | 2025-08     |            215 |         4 |                 1 |             1.1666 |           103.473  | Profit   |
| 4H_channel_24_no_trend_filter_trail_3atr | 2025-09     |            215 |         3 |                 1 |             1.2677 |           104.785  | Profit   |
| 4H_channel_24_no_trend_filter_trail_3atr | 2025-10     |            215 |         4 |                 1 |             2.2928 |           107.188  | Profit   |
| 4H_channel_24_no_trend_filter_trail_3atr | 2025-11     |            215 |         3 |                 1 |             1.2397 |           108.516  | Profit   |
| 4H_channel_24_no_trend_filter_trail_3atr | 2025-12     |            215 |         8 |                 1 |            -3.0504 |           105.206  | Loss     |
| 4H_channel_24_no_trend_filter_trail_3atr | 2026-01     |            215 |         5 |                 1 |             4.1771 |           109.601  | Profit   |
| 4H_channel_24_no_trend_filter_trail_3atr | 2026-02     |            215 |         5 |                 1 |            -1.6113 |           107.835  | Loss     |
| 4H_channel_24_no_trend_filter_trail_3atr | 2026-03     |            215 |         4 |                 1 |            -0.8077 |           106.964  | Loss     |
| 4H_channel_24_no_trend_filter_trail_3atr | 2026-04     |            215 |         7 |                 1 |            -2.4103 |           104.386  | Loss     |
| 4H_channel_24_no_trend_filter_trail_3atr | 2026-05     |            215 |         8 |                 1 |            -2.6822 |           101.586  | Loss     |
| 4H_channel_24_no_trend_filter_trail_3atr | 2026-06     |            215 |         4 |                 1 |             2.7915 |           104.422  | Profit   |
| 4H_channel_24_no_trend_filter_trail_3atr | 2026-07     |            215 |         6 |                 1 |            -1.8933 |           102.445  | Loss     |
| 4H_channel_24_no_trend_filter_trail_3atr | 2026-08     |            215 |         4 |                 1 |            12.5378 |           115.289  | Profit   |
| 4H_channel_24_no_trend_filter_trail_3atr | 2026-09     |            215 |         4 |                 1 |            -1.539  |           113.515  | Loss     |
| 4H_channel_24_no_trend_filter_trail_3atr | 2026-10     |            215 |         6 |                 1 |            -1.7227 |           111.559  | Loss     |
| 4H_channel_24_no_trend_filter_trail_3atr | 2026-11     |            215 |         0 |                 1 |             0.0036 |           111.563  | Profit   |
| 4H_channel_24_ema50_agrees_trail_3atr    | 2025-01     |            201 |         2 |                 1 |            -0.2187 |            99.7813 | Loss     |
| 4H_channel_24_ema50_agrees_trail_3atr    | 2025-02     |            201 |         3 |                 1 |             0.6629 |           100.443  | Profit   |
| 4H_channel_24_ema50_agrees_trail_3atr    | 2025-03     |            201 |         4 |                 1 |            -0.4192 |           100.022  | Loss     |
| 4H_channel_24_ema50_agrees_trail_3atr    | 2025-04     |            201 |         4 |                 1 |            -1.326  |            98.6954 | Loss     |
| 4H_channel_24_ema50_agrees_trail_3atr    | 2025-05     |            201 |         5 |                 1 |             1.6837 |           100.357  | Profit   |
| 4H_channel_24_ema50_agrees_trail_3atr    | 2025-06     |            201 |         5 |                 1 |            -1.0405 |            99.3129 | Loss     |
| 4H_channel_24_ema50_agrees_trail_3atr    | 2025-07     |            201 |         3 |                 1 |             4.9958 |           104.274  | Profit   |
| 4H_channel_24_ema50_agrees_trail_3atr    | 2025-08     |            201 |         4 |                 1 |             0.9426 |           105.257  | Profit   |
| 4H_channel_24_ema50_agrees_trail_3atr    | 2025-09     |            201 |         3 |                 1 |             1.0283 |           106.34   | Profit   |
| 4H_channel_24_ema50_agrees_trail_3atr    | 2025-10     |            201 |         5 |                 1 |             1.0433 |           107.449  | Profit   |
| 4H_channel_24_ema50_agrees_trail_3atr    | 2025-11     |            201 |         2 |                 1 |             1.5231 |           109.086  | Profit   |
| 4H_channel_24_ema50_agrees_trail_3atr    | 2025-12     |            201 |         7 |                 1 |            -2.7408 |           106.096  | Loss     |
| 4H_channel_24_ema50_agrees_trail_3atr    | 2026-01     |            201 |         5 |                 1 |             3.1455 |           109.433  | Profit   |
| 4H_channel_24_ema50_agrees_trail_3atr    | 2026-02     |            201 |         5 |                 1 |            -1.6113 |           107.67   | Loss     |
| 4H_channel_24_ema50_agrees_trail_3atr    | 2026-03     |            201 |         4 |                 1 |            -0.8077 |           106.8    | Loss     |
| 4H_channel_24_ema50_agrees_trail_3atr    | 2026-04     |            201 |         7 |                 1 |            -2.4103 |           104.226  | Loss     |
| 4H_channel_24_ema50_agrees_trail_3atr    | 2026-05     |            201 |         8 |                 1 |            -2.6822 |           101.43   | Loss     |
| 4H_channel_24_ema50_agrees_trail_3atr    | 2026-06     |            201 |         3 |                 1 |             2.7462 |           104.216  | Profit   |
| 4H_channel_24_ema50_agrees_trail_3atr    | 2026-07     |            201 |         5 |                 1 |            -1.3826 |           102.775  | Loss     |
| 4H_channel_24_ema50_agrees_trail_3atr    | 2026-08     |            201 |         4 |                 1 |            12.5483 |           115.671  | Profit   |
| 4H_channel_24_ema50_agrees_trail_3atr    | 2026-09     |            201 |         4 |                 1 |            -1.539  |           113.891  | Loss     |
| 4H_channel_24_ema50_agrees_trail_3atr    | 2026-10     |            201 |         6 |                 1 |            -1.7227 |           111.929  | Loss     |
| 4H_channel_24_ema50_agrees_trail_3atr    | 2026-11     |            201 |         0 |                 1 |             0.0036 |           111.933  | Profit   |
| 4H_channel_24_ema50_agrees_trail_4atr    | 2025-01     |            201 |         2 |                 1 |            -0.4964 |            99.5036 | Loss     |
| 4H_channel_24_ema50_agrees_trail_4atr    | 2025-02     |            201 |         3 |                 1 |             0.8786 |           100.378  | Profit   |
| 4H_channel_24_ema50_agrees_trail_4atr    | 2025-03     |            201 |         4 |                 1 |            -0.853  |            99.5216 | Loss     |
| 4H_channel_24_ema50_agrees_trail_4atr    | 2025-04     |            201 |         4 |                 1 |            -1.6374 |            97.892  | Loss     |
| 4H_channel_24_ema50_agrees_trail_4atr    | 2025-05     |            201 |         3 |                 1 |             2.1776 |           100.024  | Profit   |
| 4H_channel_24_ema50_agrees_trail_4atr    | 2025-06     |            201 |         5 |                 1 |            -1.67   |            98.3533 | Loss     |
| 4H_channel_24_ema50_agrees_trail_4atr    | 2025-07     |            201 |         3 |                 1 |             4.6925 |           102.969  | Profit   |
| 4H_channel_24_ema50_agrees_trail_4atr    | 2025-08     |            201 |         4 |                 1 |             0.2267 |           103.202  | Profit   |
| 4H_channel_24_ema50_agrees_trail_4atr    | 2025-09     |            201 |         3 |                 1 |             0.2886 |           103.5    | Profit   |
| 4H_channel_24_ema50_agrees_trail_4atr    | 2025-10     |            201 |         4 |                 1 |             1.9406 |           105.508  | Profit   |
| 4H_channel_24_ema50_agrees_trail_4atr    | 2025-11     |            201 |         2 |                 1 |             1.1257 |           106.696  | Profit   |
| 4H_channel_24_ema50_agrees_trail_4atr    | 2025-12     |            201 |         6 |                 1 |            -3.0399 |           103.453  | Loss     |
| 4H_channel_24_ema50_agrees_trail_4atr    | 2026-01     |            201 |         5 |                 1 |             2.3796 |           105.914  | Profit   |
| 4H_channel_24_ema50_agrees_trail_4atr    | 2026-02     |            201 |         4 |                 1 |            -0.389  |           105.502  | Loss     |
| 4H_channel_24_ema50_agrees_trail_4atr    | 2026-03     |            201 |         4 |                 1 |            -1.0898 |           104.353  | Loss     |
| 4H_channel_24_ema50_agrees_trail_4atr    | 2026-04     |            201 |         6 |                 1 |            -1.1456 |           103.157  | Loss     |
| 4H_channel_24_ema50_agrees_trail_4atr    | 2026-05     |            201 |         8 |                 1 |            -2.8274 |           100.24   | Loss     |
| 4H_channel_24_ema50_agrees_trail_4atr    | 2026-06     |            201 |         3 |                 1 |             2.9031 |           103.151  | Profit   |
| 4H_channel_24_ema50_agrees_trail_4atr    | 2026-07     |            201 |         3 |                 1 |             0.1305 |           103.285  | Profit   |
| 4H_channel_24_ema50_agrees_trail_4atr    | 2026-08     |            201 |         4 |                 1 |            11.7463 |           115.417  | Profit   |
| 4H_channel_24_ema50_agrees_trail_4atr    | 2026-09     |            201 |         4 |                 1 |            -1.3317 |           113.88   | Loss     |
| 4H_channel_24_ema50_agrees_trail_4atr    | 2026-10     |            201 |         6 |                 1 |            -1.9242 |           111.689  | Loss     |
| 4H_channel_24_ema50_agrees_trail_4atr    | 2026-11     |            201 |         0 |                 1 |             0.0036 |           111.693  | Profit   |

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
