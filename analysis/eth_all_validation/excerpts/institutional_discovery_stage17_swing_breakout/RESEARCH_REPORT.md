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
| 1D_channel_20_ema50_agrees_trail_3atr    | 1D          |                 20 | ema50_agrees    |           3 |             37 |       22 |                             2.138 |              2.534 |               102.534  |             3 |           5 |               4 |             8 |             0.282 |             9 |           1 |               1 |            10 |             2.246 | False               |
| 1D_channel_20_ema50_agrees_trail_4atr    | 1D          |                 20 | ema50_agrees    |           4 |             37 |       22 |                             1.68  |              3.764 |               103.764  |             4 |           4 |               4 |             8 |             1.308 |             9 |           1 |               1 |            10 |             2.425 | False               |
| 1D_channel_20_no_trend_filter_trail_3atr | 1D          |                 20 | no_trend_filter |           3 |             40 |       24 |                             2.197 |              1.648 |               101.648  |             3 |           5 |               4 |             8 |            -0.058 |             9 |           2 |               0 |            11 |             1.707 | False               |
| 1D_channel_20_no_trend_filter_trail_4atr | 1D          |                 20 | no_trend_filter |           4 |             40 |       24 |                             1.919 |              2.679 |               102.678  |             4 |           4 |               4 |             8 |             0.779 |             9 |           2 |               0 |            11 |             1.885 | False               |
| 1D_channel_55_ema50_agrees_trail_3atr    | 1D          |                 55 | ema50_agrees    |           3 |             25 |       15 |                             1.262 |              2.306 |               102.306  |             2 |           6 |               4 |             8 |             0.93  |             7 |           2 |               2 |             9 |             1.364 | False               |
| 1D_channel_55_ema50_agrees_trail_4atr    | 1D          |                 55 | ema50_agrees    |           4 |             25 |       15 |                             0.8   |              3.534 |               103.534  |             3 |           5 |               4 |             8 |             1.962 |             7 |           2 |               2 |             9 |             1.541 | False               |
| 1D_channel_55_no_trend_filter_trail_3atr | 1D          |                 55 | no_trend_filter |           3 |             25 |       15 |                             1.262 |              2.306 |               102.306  |             2 |           6 |               4 |             8 |             0.93  |             7 |           2 |               2 |             9 |             1.364 | False               |
| 1D_channel_55_no_trend_filter_trail_4atr | 1D          |                 55 | no_trend_filter |           4 |             25 |       15 |                             0.8   |              3.534 |               103.534  |             3 |           5 |               4 |             8 |             1.962 |             7 |           2 |               2 |             9 |             1.541 | False               |
| 4H_channel_24_ema50_agrees_trail_3atr    | 4H          |                 24 | ema50_agrees    |           3 |            208 |       41 |                             3.229 |              0.374 |               100.374  |             6 |           6 |               0 |            12 |             0.39  |             2 |           5 |               4 |             7 |            -0.016 | False               |
| 4H_channel_24_ema50_agrees_trail_4atr    | 4H          |                 24 | ema50_agrees    |           4 |            208 |       39 |                             3.897 |             -1.392 |                98.608  |             5 |           7 |               0 |            12 |            -2.434 |             2 |           5 |               4 |             7 |             1.068 | False               |
| 4H_channel_24_no_trend_filter_trail_3atr | 4H          |                 24 | no_trend_filter |           3 |            222 |       46 |                             4.353 |             -0.648 |                99.3516 |             5 |           7 |               0 |            12 |            -0.076 |             2 |           5 |               4 |             7 |            -0.573 | False               |
| 4H_channel_24_no_trend_filter_trail_4atr | 4H          |                 24 | no_trend_filter |           4 |            222 |       41 |                             5.107 |             -1.375 |                98.6251 |             5 |           7 |               0 |            12 |            -1.871 |             2 |           5 |               4 |             7 |             0.505 | False               |
| 4H_channel_55_ema50_agrees_trail_3atr    | 4H          |                 55 | ema50_agrees    |           3 |            139 |       35 |                             4.412 |             -2.829 |                97.171  |             3 |           9 |               0 |            12 |            -3.035 |             2 |           5 |               4 |             7 |             0.212 | False               |
| 4H_channel_55_ema50_agrees_trail_4atr    | 4H          |                 55 | ema50_agrees    |           4 |            139 |       35 |                             6.553 |             -5.104 |                94.896  |             2 |          10 |               0 |            12 |            -5.685 |             2 |           5 |               4 |             7 |             0.615 | False               |
| 4H_channel_55_no_trend_filter_trail_3atr | 4H          |                 55 | no_trend_filter |           3 |            140 |       35 |                             4.412 |             -2.829 |                97.171  |             3 |           9 |               0 |            12 |            -3.035 |             2 |           5 |               4 |             7 |             0.212 | False               |
| 4H_channel_55_no_trend_filter_trail_4atr | 4H          |                 55 | no_trend_filter |           4 |            140 |       35 |                             6.553 |             -5.104 |                94.896  |             2 |          10 |               0 |            12 |            -5.685 |             2 |           5 |               4 |             7 |             0.615 | False               |

## Month-by-month top three 2025-ranked models
| model                                    | month_ist   |   signals_seen |   entries |   market_exposure |   month_return_pct |   month_end_equity | status      |
|:-----------------------------------------|:------------|---------------:|----------:|------------------:|-------------------:|-------------------:|:------------|
| 4H_channel_24_no_trend_filter_trail_3atr | 2025-01     |            222 |         2 |                 1 |            -0.3032 |            99.6968 | Loss        |
| 4H_channel_24_no_trend_filter_trail_3atr | 2025-02     |            222 |         4 |                 1 |             0.1342 |            99.8306 | Profit      |
| 4H_channel_24_no_trend_filter_trail_3atr | 2025-03     |            222 |         2 |                 1 |            -0.4392 |            99.3921 | Loss        |
| 4H_channel_24_no_trend_filter_trail_3atr | 2025-04     |            222 |         1 |                 1 |            -0.5556 |            98.8399 | Loss        |
| 4H_channel_24_no_trend_filter_trail_3atr | 2025-05     |            222 |         4 |                 1 |            -1.3875 |            97.4686 | Loss        |
| 4H_channel_24_no_trend_filter_trail_3atr | 2025-06     |            222 |         4 |                 1 |            -1.5477 |            95.9601 | Loss        |
| 4H_channel_24_no_trend_filter_trail_3atr | 2025-07     |            222 |         2 |                 1 |             1.7672 |            97.6558 | Profit      |
| 4H_channel_24_no_trend_filter_trail_3atr | 2025-08     |            222 |         4 |                 1 |             1.0544 |            98.6855 | Profit      |
| 4H_channel_24_no_trend_filter_trail_3atr | 2025-09     |            222 |         3 |                 1 |            -0.2755 |            98.4137 | Loss        |
| 4H_channel_24_no_trend_filter_trail_3atr | 2025-10     |            222 |         4 |                 1 |             2.1687 |           100.548  | Profit      |
| 4H_channel_24_no_trend_filter_trail_3atr | 2025-11     |            222 |         3 |                 1 |             1.149  |           101.703  | Profit      |
| 4H_channel_24_no_trend_filter_trail_3atr | 2025-12     |            222 |         5 |                 1 |            -1.7496 |            99.9239 | Loss        |
| 4H_channel_24_no_trend_filter_trail_3atr | 2026-01     |            222 |         3 |                 1 |             1.2095 |           101.132  | Profit      |
| 4H_channel_24_no_trend_filter_trail_3atr | 2026-02     |            222 |         1 |                 1 |             0.3832 |           101.52   | Profit      |
| 4H_channel_24_no_trend_filter_trail_3atr | 2026-03     |            222 |         1 |                 1 |            -0.547  |           100.965  | Loss        |
| 4H_channel_24_no_trend_filter_trail_3atr | 2026-04     |            222 |         0 |                 0 |             0      |           100.965  | No exposure |
| 4H_channel_24_no_trend_filter_trail_3atr | 2026-05     |            222 |         0 |                 0 |             0      |           100.965  | No exposure |
| 4H_channel_24_no_trend_filter_trail_3atr | 2026-06     |            222 |         1 |                 1 |            -0.1873 |           100.776  | Loss        |
| 4H_channel_24_no_trend_filter_trail_3atr | 2026-07     |            222 |         0 |                 0 |             0      |           100.776  | No exposure |
| 4H_channel_24_no_trend_filter_trail_3atr | 2026-08     |            222 |         1 |                 1 |            -0.5437 |           100.228  | Loss        |
| 4H_channel_24_no_trend_filter_trail_3atr | 2026-09     |            222 |         0 |                 0 |             0      |           100.228  | No exposure |
| 4H_channel_24_no_trend_filter_trail_3atr | 2026-10     |            222 |         1 |                 1 |            -0.5617 |            99.6647 | Loss        |
| 4H_channel_24_no_trend_filter_trail_3atr | 2026-11     |            222 |         1 |                 1 |            -0.3142 |            99.3516 | Loss        |
| 4H_channel_24_no_trend_filter_trail_4atr | 2025-01     |            222 |         2 |                 1 |            -0.5809 |            99.4191 | Loss        |
| 4H_channel_24_no_trend_filter_trail_4atr | 2025-02     |            222 |         3 |                 1 |             0.6067 |           100.022  | Profit      |
| 4H_channel_24_no_trend_filter_trail_4atr | 2025-03     |            222 |         2 |                 1 |            -0.8731 |            99.1491 | Loss        |
| 4H_channel_24_no_trend_filter_trail_4atr | 2025-04     |            222 |         1 |                 1 |            -0.5556 |            98.5982 | Loss        |
| 4H_channel_24_no_trend_filter_trail_4atr | 2025-05     |            222 |         4 |                 1 |            -1.6503 |            96.9711 | Loss        |
| 4H_channel_24_no_trend_filter_trail_4atr | 2025-06     |            222 |         4 |                 1 |            -1.7052 |            95.3175 | Loss        |
| 4H_channel_24_no_trend_filter_trail_4atr | 2025-07     |            222 |         2 |                 1 |             1.2005 |            96.4618 | Profit      |
| 4H_channel_24_no_trend_filter_trail_4atr | 2025-08     |            222 |         4 |                 1 |             0.1127 |            96.5705 | Profit      |
| 4H_channel_24_no_trend_filter_trail_4atr | 2025-09     |            222 |         3 |                 1 |            -0.6793 |            95.9145 | Loss        |
| 4H_channel_24_no_trend_filter_trail_4atr | 2025-10     |            222 |         3 |                 1 |             3.0051 |            98.7969 | Profit      |
| 4H_channel_24_no_trend_filter_trail_4atr | 2025-11     |            222 |         2 |                 1 |             1.2892 |           100.071  | Profit      |
| 4H_channel_24_no_trend_filter_trail_4atr | 2025-12     |            222 |         4 |                 1 |            -1.9398 |            98.1295 | Loss        |
| 4H_channel_24_no_trend_filter_trail_4atr | 2026-01     |            222 |         3 |                 1 |             1.0432 |            99.1532 | Profit      |
| 4H_channel_24_no_trend_filter_trail_4atr | 2026-02     |            222 |         0 |                 1 |             1.7043 |           100.843  | Profit      |
| 4H_channel_24_no_trend_filter_trail_4atr | 2026-03     |            222 |         1 |                 1 |            -0.547  |           100.291  | Loss        |
| 4H_channel_24_no_trend_filter_trail_4atr | 2026-04     |            222 |         0 |                 0 |             0      |           100.291  | No exposure |
| 4H_channel_24_no_trend_filter_trail_4atr | 2026-05     |            222 |         0 |                 0 |             0      |           100.291  | No exposure |
| 4H_channel_24_no_trend_filter_trail_4atr | 2026-06     |            222 |         1 |                 1 |            -0.2521 |           100.039  | Loss        |
| 4H_channel_24_no_trend_filter_trail_4atr | 2026-07     |            222 |         0 |                 0 |             0      |           100.039  | No exposure |
| 4H_channel_24_no_trend_filter_trail_4atr | 2026-08     |            222 |         1 |                 1 |            -0.5437 |            99.4948 | Loss        |
| 4H_channel_24_no_trend_filter_trail_4atr | 2026-09     |            222 |         0 |                 0 |             0      |            99.4948 | No exposure |
| 4H_channel_24_no_trend_filter_trail_4atr | 2026-10     |            222 |         1 |                 1 |            -0.5617 |            98.936  | Loss        |
| 4H_channel_24_no_trend_filter_trail_4atr | 2026-11     |            222 |         1 |                 1 |            -0.3142 |            98.6251 | Loss        |
| 4H_channel_24_ema50_agrees_trail_3atr    | 2025-01     |            208 |         2 |                 1 |            -0.3032 |            99.6968 | Loss        |
| 4H_channel_24_ema50_agrees_trail_3atr    | 2025-02     |            208 |         3 |                 1 |             0.5585 |           100.254  | Profit      |
| 4H_channel_24_ema50_agrees_trail_3atr    | 2025-03     |            208 |         1 |                 1 |             0.1023 |           100.356  | Profit      |
| 4H_channel_24_ema50_agrees_trail_3atr    | 2025-04     |            208 |         1 |                 1 |            -0.5556 |            99.7987 | Loss        |
| 4H_channel_24_ema50_agrees_trail_3atr    | 2025-05     |            208 |         3 |                 1 |            -0.8354 |            98.965  | Loss        |
| 4H_channel_24_ema50_agrees_trail_3atr    | 2025-06     |            208 |         4 |                 1 |            -1.5477 |            97.4333 | Loss        |
| 4H_channel_24_ema50_agrees_trail_3atr    | 2025-07     |            208 |         2 |                 1 |             1.7672 |            99.1551 | Profit      |
| 4H_channel_24_ema50_agrees_trail_3atr    | 2025-08     |            208 |         4 |                 1 |             0.8346 |            99.9827 | Profit      |
| 4H_channel_24_ema50_agrees_trail_3atr    | 2025-09     |            208 |         3 |                 1 |            -0.5094 |            99.4734 | Loss        |
| 4H_channel_24_ema50_agrees_trail_3atr    | 2025-10     |            208 |         5 |                 1 |             0.8856 |           100.354  | Profit      |
| 4H_channel_24_ema50_agrees_trail_3atr    | 2025-11     |            208 |         2 |                 1 |             1.4634 |           101.823  | Profit      |
| 4H_channel_24_ema50_agrees_trail_3atr    | 2025-12     |            208 |         4 |                 1 |            -1.4069 |           100.39   | Loss        |
| 4H_channel_24_ema50_agrees_trail_3atr    | 2026-01     |            208 |         2 |                 1 |             1.7762 |           102.173  | Profit      |
| 4H_channel_24_ema50_agrees_trail_3atr    | 2026-02     |            208 |         1 |                 1 |             0.3832 |           102.565  | Profit      |
| 4H_channel_24_ema50_agrees_trail_3atr    | 2026-03     |            208 |         1 |                 1 |            -0.547  |           102.004  | Loss        |
| 4H_channel_24_ema50_agrees_trail_3atr    | 2026-04     |            208 |         0 |                 0 |             0      |           102.004  | No exposure |
| 4H_channel_24_ema50_agrees_trail_3atr    | 2026-05     |            208 |         0 |                 0 |             0      |           102.004  | No exposure |
| 4H_channel_24_ema50_agrees_trail_3atr    | 2026-06     |            208 |         1 |                 1 |            -0.1873 |           101.813  | Loss        |
| 4H_channel_24_ema50_agrees_trail_3atr    | 2026-07     |            208 |         0 |                 0 |             0      |           101.813  | No exposure |
| 4H_channel_24_ema50_agrees_trail_3atr    | 2026-08     |            208 |         1 |                 1 |            -0.5437 |           101.259  | Loss        |
| 4H_channel_24_ema50_agrees_trail_3atr    | 2026-09     |            208 |         0 |                 0 |             0      |           101.259  | No exposure |
| 4H_channel_24_ema50_agrees_trail_3atr    | 2026-10     |            208 |         1 |                 1 |            -0.5617 |           100.691  | Loss        |
| 4H_channel_24_ema50_agrees_trail_3atr    | 2026-11     |            208 |         1 |                 1 |            -0.3142 |           100.374  | Loss        |

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
