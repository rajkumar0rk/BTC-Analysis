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
| 1D_channel_20_ema50_agrees_trail_3atr    | 1D          |                 20 | ema50_agrees    |           3 |             32 |       20 |                             2.205 |              2.302 |               102.302  |             4 |           4 |               4 |             8 |            -0.209 |             6 |           4 |               1 |            10 |             2.516 | False               |
| 1D_channel_20_ema50_agrees_trail_4atr    | 1D          |                 20 | ema50_agrees    |           4 |             32 |       20 |                             2.432 |              2.159 |               102.159  |             4 |           4 |               4 |             8 |            -0.44  |             6 |           4 |               1 |            10 |             2.611 | False               |
| 1D_channel_20_no_trend_filter_trail_3atr | 1D          |                 20 | no_trend_filter |           3 |             39 |       24 |                             2.469 |              1.903 |               101.903  |             3 |           5 |               4 |             8 |            -1.23  |             6 |           4 |               1 |            10 |             3.172 | False               |
| 1D_channel_20_no_trend_filter_trail_4atr | 1D          |                 20 | no_trend_filter |           4 |             39 |       24 |                             2.695 |              1.761 |               101.761  |             3 |           5 |               4 |             8 |            -1.458 |             6 |           4 |               1 |            10 |             3.267 | False               |
| 1D_channel_55_ema50_agrees_trail_3atr    | 1D          |                 55 | ema50_agrees    |           3 |             20 |       13 |                             0.827 |              1.843 |               101.843  |             4 |           2 |               6 |             6 |             0.602 |             4 |           4 |               3 |             8 |             1.233 | False               |
| 1D_channel_55_ema50_agrees_trail_4atr    | 1D          |                 55 | ema50_agrees    |           4 |             20 |       13 |                             0.827 |              1.937 |               101.937  |             4 |           2 |               6 |             6 |             0.602 |             4 |           4 |               3 |             8 |             1.327 | False               |
| 1D_channel_55_no_trend_filter_trail_3atr | 1D          |                 55 | no_trend_filter |           3 |             20 |       13 |                             0.827 |              1.843 |               101.843  |             4 |           2 |               6 |             6 |             0.602 |             4 |           4 |               3 |             8 |             1.233 | False               |
| 1D_channel_55_no_trend_filter_trail_4atr | 1D          |                 55 | no_trend_filter |           4 |             20 |       13 |                             0.827 |              1.937 |               101.937  |             4 |           2 |               6 |             6 |             0.602 |             4 |           4 |               3 |             8 |             1.327 | False               |
| 4H_channel_24_ema50_agrees_trail_3atr    | 4H          |                 24 | ema50_agrees    |           3 |            226 |      110 |                             8.84  |              0.896 |               100.896  |             6 |           6 |               0 |            12 |            -2.532 |             3 |           7 |               1 |            10 |             3.517 | False               |
| 4H_channel_24_ema50_agrees_trail_4atr    | 4H          |                 24 | ema50_agrees    |           4 |            226 |       99 |                             9.064 |             -1.182 |                98.8178 |             4 |           8 |               0 |            12 |            -6.111 |             3 |           7 |               1 |            10 |             5.25  | False               |
| 4H_channel_24_no_trend_filter_trail_3atr | 4H          |                 24 | no_trend_filter |           3 |            239 |      116 |                             7.677 |              0.219 |               100.219  |             6 |           6 |               0 |            12 |            -3.263 |             3 |           7 |               1 |            10 |             3.599 | False               |
| 4H_channel_24_no_trend_filter_trail_4atr | 4H          |                 24 | no_trend_filter |           4 |            239 |      104 |                             9.769 |             -3.187 |                96.8131 |             4 |           8 |               0 |            12 |            -6.424 |             3 |           7 |               1 |            10 |             3.459 | False               |
| 4H_channel_55_ema50_agrees_trail_3atr    | 4H          |                 55 | ema50_agrees    |           3 |            145 |       71 |                             7.503 |             -5.103 |                94.8972 |             5 |           7 |               0 |            12 |            -5.138 |             5 |           5 |               1 |            10 |             0.037 | False               |
| 4H_channel_55_ema50_agrees_trail_4atr    | 4H          |                 55 | ema50_agrees    |           4 |            145 |       67 |                             7.826 |             -6.674 |                93.3261 |             4 |           8 |               0 |            12 |            -6.417 |             4 |           6 |               1 |            10 |            -0.275 | False               |
| 4H_channel_55_no_trend_filter_trail_3atr | 4H          |                 55 | no_trend_filter |           3 |            145 |       71 |                             7.503 |             -5.103 |                94.8972 |             5 |           7 |               0 |            12 |            -5.138 |             5 |           5 |               1 |            10 |             0.037 | False               |
| 4H_channel_55_no_trend_filter_trail_4atr | 4H          |                 55 | no_trend_filter |           4 |            145 |       67 |                             7.826 |             -6.674 |                93.3261 |             4 |           8 |               0 |            12 |            -6.417 |             4 |           6 |               1 |            10 |            -0.275 | False               |

## Month-by-month top three 2025-ranked models
| model                                    | month_ist   |   signals_seen |   entries |   market_exposure |   month_return_pct |   month_end_equity | status      |
|:-----------------------------------------|:------------|---------------:|----------:|------------------:|-------------------:|-------------------:|:------------|
| 4H_channel_24_no_trend_filter_trail_3atr | 2025-01     |            239 |         1 |                 1 |            -0.5272 |            99.4728 | Loss        |
| 4H_channel_24_no_trend_filter_trail_3atr | 2025-02     |            239 |         4 |                 1 |             2.4479 |           101.908  | Profit      |
| 4H_channel_24_no_trend_filter_trail_3atr | 2025-03     |            239 |         7 |                 1 |            -2.9358 |            98.9161 | Loss        |
| 4H_channel_24_no_trend_filter_trail_3atr | 2025-04     |            239 |         3 |                 1 |             0.7079 |            99.6163 | Profit      |
| 4H_channel_24_no_trend_filter_trail_3atr | 2025-05     |            239 |         7 |                 1 |            -1.9646 |            97.6593 | Loss        |
| 4H_channel_24_no_trend_filter_trail_3atr | 2025-06     |            239 |         7 |                 1 |            -2.0163 |            95.6902 | Loss        |
| 4H_channel_24_no_trend_filter_trail_3atr | 2025-07     |            239 |         5 |                 1 |             0.0965 |            95.7826 | Profit      |
| 4H_channel_24_no_trend_filter_trail_3atr | 2025-08     |            239 |         6 |                 1 |            -1.1932 |            94.6397 | Loss        |
| 4H_channel_24_no_trend_filter_trail_3atr | 2025-09     |            239 |         5 |                 1 |             0.5825 |            95.1909 | Profit      |
| 4H_channel_24_no_trend_filter_trail_3atr | 2025-10     |            239 |         4 |                 1 |             3.7094 |            98.7219 | Profit      |
| 4H_channel_24_no_trend_filter_trail_3atr | 2025-11     |            239 |         3 |                 1 |             2.6458 |           101.334  | Profit      |
| 4H_channel_24_no_trend_filter_trail_3atr | 2025-12     |            239 |         8 |                 1 |            -4.5358 |            96.7377 | Loss        |
| 4H_channel_24_no_trend_filter_trail_3atr | 2026-01     |            239 |         6 |                 1 |             2.723  |            99.3718 | Profit      |
| 4H_channel_24_no_trend_filter_trail_3atr | 2026-02     |            239 |         7 |                 1 |            -2.0486 |            97.3361 | Loss        |
| 4H_channel_24_no_trend_filter_trail_3atr | 2026-03     |            239 |         5 |                 1 |            -0.8523 |            96.5064 | Loss        |
| 4H_channel_24_no_trend_filter_trail_3atr | 2026-04     |            239 |         6 |                 1 |            -1.1471 |            95.3994 | Loss        |
| 4H_channel_24_no_trend_filter_trail_3atr | 2026-05     |            239 |         6 |                 1 |            -1.5796 |            93.8924 | Loss        |
| 4H_channel_24_no_trend_filter_trail_3atr | 2026-06     |            239 |         4 |                 1 |             3.3579 |            97.0453 | Profit      |
| 4H_channel_24_no_trend_filter_trail_3atr | 2026-07     |            239 |         6 |                 1 |            -2.6621 |            94.4619 | Loss        |
| 4H_channel_24_no_trend_filter_trail_3atr | 2026-08     |            239 |         4 |                 1 |            10.4107 |           104.296  | Profit      |
| 4H_channel_24_no_trend_filter_trail_3atr | 2026-09     |            239 |         4 |                 1 |            -1.0966 |           103.152  | Loss        |
| 4H_channel_24_no_trend_filter_trail_3atr | 2026-10     |            239 |         8 |                 1 |            -2.8436 |           100.219  | Loss        |
| 4H_channel_24_no_trend_filter_trail_3atr | 2026-11     |            239 |         0 |                 0 |             0      |           100.219  | No exposure |
| 4H_channel_24_ema50_agrees_trail_3atr    | 2025-01     |            226 |         1 |                 1 |            -0.5272 |            99.4728 | Loss        |
| 4H_channel_24_ema50_agrees_trail_3atr    | 2025-02     |            226 |         4 |                 1 |             2.4479 |           101.908  | Profit      |
| 4H_channel_24_ema50_agrees_trail_3atr    | 2025-03     |            226 |         6 |                 1 |            -2.7351 |            99.1205 | Loss        |
| 4H_channel_24_ema50_agrees_trail_3atr    | 2025-04     |            226 |         3 |                 1 |             0.7098 |            99.8241 | Profit      |
| 4H_channel_24_ema50_agrees_trail_3atr    | 2025-05     |            226 |         7 |                 1 |            -1.9646 |            97.8629 | Loss        |
| 4H_channel_24_ema50_agrees_trail_3atr    | 2025-06     |            226 |         6 |                 1 |            -1.4926 |            96.4023 | Loss        |
| 4H_channel_24_ema50_agrees_trail_3atr    | 2025-07     |            226 |         5 |                 1 |             0.0965 |            96.4953 | Profit      |
| 4H_channel_24_ema50_agrees_trail_3atr    | 2025-08     |            226 |         6 |                 1 |            -1.1932 |            95.3439 | Loss        |
| 4H_channel_24_ema50_agrees_trail_3atr    | 2025-09     |            226 |         5 |                 1 |             0.5825 |            95.8993 | Profit      |
| 4H_channel_24_ema50_agrees_trail_3atr    | 2025-10     |            226 |         3 |                 1 |             4.2517 |            99.9766 | Profit      |
| 4H_channel_24_ema50_agrees_trail_3atr    | 2025-11     |            226 |         3 |                 1 |             2.0271 |           102.003  | Profit      |
| 4H_channel_24_ema50_agrees_trail_3atr    | 2025-12     |            226 |         8 |                 1 |            -4.4459 |            97.4683 | Loss        |
| 4H_channel_24_ema50_agrees_trail_3atr    | 2026-01     |            226 |         5 |                 1 |             1.7785 |            99.2017 | Profit      |
| 4H_channel_24_ema50_agrees_trail_3atr    | 2026-02     |            226 |         7 |                 1 |            -2.0532 |            97.1649 | Loss        |
| 4H_channel_24_ema50_agrees_trail_3atr    | 2026-03     |            226 |         5 |                 1 |            -0.8523 |            96.3367 | Loss        |
| 4H_channel_24_ema50_agrees_trail_3atr    | 2026-04     |            226 |         6 |                 1 |            -1.3304 |            95.0551 | Loss        |
| 4H_channel_24_ema50_agrees_trail_3atr    | 2026-05     |            226 |         6 |                 1 |            -1.3913 |            93.7326 | Loss        |
| 4H_channel_24_ema50_agrees_trail_3atr    | 2026-06     |            226 |         4 |                 1 |             3.3579 |            96.8801 | Profit      |
| 4H_channel_24_ema50_agrees_trail_3atr    | 2026-07     |            226 |         6 |                 1 |            -2.6621 |            94.301  | Loss        |
| 4H_channel_24_ema50_agrees_trail_3atr    | 2026-08     |            226 |         3 |                 1 |            10.7803 |           104.467  | Profit      |
| 4H_channel_24_ema50_agrees_trail_3atr    | 2026-09     |            226 |         4 |                 1 |            -0.9514 |           103.473  | Loss        |
| 4H_channel_24_ema50_agrees_trail_3atr    | 2026-10     |            226 |         7 |                 1 |            -2.4908 |           100.896  | Loss        |
| 4H_channel_24_ema50_agrees_trail_3atr    | 2026-11     |            226 |         0 |                 0 |             0      |           100.896  | No exposure |
| 4H_channel_55_ema50_agrees_trail_3atr    | 2025-01     |            145 |         1 |                 1 |            -0.5272 |            99.4728 | Loss        |
| 4H_channel_55_ema50_agrees_trail_3atr    | 2025-02     |            145 |         2 |                 1 |             1.3729 |           100.839  | Profit      |
| 4H_channel_55_ema50_agrees_trail_3atr    | 2025-03     |            145 |         5 |                 1 |            -2.9041 |            97.9101 | Loss        |
| 4H_channel_55_ema50_agrees_trail_3atr    | 2025-04     |            145 |         2 |                 1 |             1.3191 |            99.2016 | Profit      |
| 4H_channel_55_ema50_agrees_trail_3atr    | 2025-05     |            145 |         4 |                 1 |            -1.0956 |            98.1148 | Loss        |
| 4H_channel_55_ema50_agrees_trail_3atr    | 2025-06     |            145 |         4 |                 1 |            -1.3616 |            96.7788 | Loss        |
| 4H_channel_55_ema50_agrees_trail_3atr    | 2025-07     |            145 |         3 |                 1 |             0.8888 |            97.639  | Profit      |
| 4H_channel_55_ema50_agrees_trail_3atr    | 2025-08     |            145 |         7 |                 1 |            -2.5394 |            95.1595 | Loss        |
| 4H_channel_55_ema50_agrees_trail_3atr    | 2025-09     |            145 |         3 |                 1 |            -1.0061 |            94.2022 | Loss        |
| 4H_channel_55_ema50_agrees_trail_3atr    | 2025-10     |            145 |         4 |                 1 |             0.2249 |            94.414  | Profit      |
| 4H_channel_55_ema50_agrees_trail_3atr    | 2025-11     |            145 |         2 |                 1 |             1.535  |            95.8633 | Profit      |
| 4H_channel_55_ema50_agrees_trail_3atr    | 2025-12     |            145 |         2 |                 1 |            -1.0447 |            94.8618 | Loss        |
| 4H_channel_55_ema50_agrees_trail_3atr    | 2026-01     |            145 |         4 |                 1 |             1.2642 |            96.061  | Profit      |
| 4H_channel_55_ema50_agrees_trail_3atr    | 2026-02     |            145 |         2 |                 1 |             0.5356 |            96.5754 | Profit      |
| 4H_channel_55_ema50_agrees_trail_3atr    | 2026-03     |            145 |         4 |                 1 |            -1.844  |            94.7945 | Loss        |
| 4H_channel_55_ema50_agrees_trail_3atr    | 2026-04     |            145 |         4 |                 1 |            -1.2545 |            93.6054 | Loss        |
| 4H_channel_55_ema50_agrees_trail_3atr    | 2026-05     |            145 |         4 |                 1 |            -0.7087 |            92.942  | Loss        |
| 4H_channel_55_ema50_agrees_trail_3atr    | 2026-06     |            145 |         2 |                 1 |             3.8246 |            96.4967 | Profit      |
| 4H_channel_55_ema50_agrees_trail_3atr    | 2026-07     |            145 |         6 |                 1 |            -3.0669 |            93.5372 | Loss        |
| 4H_channel_55_ema50_agrees_trail_3atr    | 2026-08     |            145 |         1 |                 1 |             2.2903 |            95.6795 | Profit      |
| 4H_channel_55_ema50_agrees_trail_3atr    | 2026-09     |            145 |         2 |                 1 |             0.1187 |            95.7931 | Profit      |
| 4H_channel_55_ema50_agrees_trail_3atr    | 2026-10     |            145 |         3 |                 1 |            -0.9352 |            94.8972 | Loss        |
| 4H_channel_55_ema50_agrees_trail_3atr    | 2026-11     |            145 |         0 |                 0 |             0      |            94.8972 | No exposure |

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
