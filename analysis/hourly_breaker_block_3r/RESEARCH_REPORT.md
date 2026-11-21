# 1H breaker-block failure proxy, fixed 3R, true 1m replay

This is a fully defined stateful breaker-block **hypothesis** inspired by a published 1H 5R strategy. It is **NOT** the publisher's exact entry detector or same 5R target. Do not compare its numerical outcome to their 30.7% / PF1.75 as if identical.
Rules: a displacement candle closes outside previous 12h high/low with a body >=0.5 ATR(14), after an opposite candle in past 3h; the last opposite candle BODY is the OB. Up to 48h later, a red close below bullish OB body bottom -0.10 ATR signals SHORT (opposite for LONG), given the previous close remained inside/above the boundary. Each block can fail once.
Entries only from finished hourly bars whose **opening** time lies 13:00–17:00 UTC (17 exclusive); fill next available genuine 1m open. SL signal wick +/-0.25 ATR(14), TP exactly 3 initial R. No trailing or time stop, one open position. 1m same-bar tie stop priority.
Modeled taker fee 0.05% each side + 18% GST, $5 adverse slip each side, funding historic rate proxy (not settled payments). $10,000 starting equity, 1% risk/entry, max 2x notional. Contract quantity continuous. IST month-end account equity marked at hypothetical closing cost.

## Detection diagnostics
{
  "complete_1h_bars": 16512,
  "raw_qualifying_breaker_signals": 134,
  "qualifying_displacement_blocks_created": 1202,
  "order_blocks_expired_or_consumed": 1201,
  "body_cross_events_all_sessions": 650,
  "events_rejected_outside_session": 405,
  "simultaneous_block_flip_collisions": 111,
  "market_session_utc": "candle OPEN hours 13,14,15,16",
  "measured_period": "2025-01-01 01:00:00+00:00 to 2026-11-20 00:00:00+00:00"
}

## Trade-period outcomes
| period                |   trades |   wins |   losses |   win_pct |   pf_net |   net_closed_USD |   targets |
|:----------------------|---------:|-------:|---------:|----------:|---------:|-----------------:|----------:|
| 2025                  |       60 |     15 |       45 |     25    |    0.833 |          -747.86 |        15 |
| 2026_Jan_Oct          |       46 |      9 |       37 |     19.57 |    0.634 |         -1344.96 |         9 |
| 2026_Nov_partial      |        2 |      1 |        1 |     50    |    2.72  |           148.86 |         1 |
| 2025_through_Oct_2026 |      106 |     24 |       82 |     22.64 |    0.743 |         -2092.82 |        24 |
| entire_period         |      108 |     25 |       83 |     23.15 |    0.764 |         -1943.96 |        25 |

## Monthly account PnL
| month_ist   |   end_equity_usd |   net_return_pct |   trades_closed |   wins |   losses |   net_closed_usd | open_position_at_end   | complete   |
|:------------|-----------------:|-----------------:|----------------:|-------:|---------:|-----------------:|:-----------------------|:-----------|
| 2025-01     |          9863.31 |           -1.367 |               5 |      1 |        4 |          -136.69 | False                  | True       |
| 2025-02     |          9388.58 |           -4.813 |               8 |      1 |        7 |          -474.73 | False                  | True       |
| 2025-03     |          8580.93 |           -8.602 |               8 |      0 |        8 |          -788.22 | True                   | True       |
| 2025-04     |          8309.9  |           -3.159 |               3 |      0 |        3 |          -290.46 | False                  | True       |
| 2025-05     |          8449.48 |            1.68  |               2 |      1 |        1 |           139.59 | False                  | True       |
| 2025-06     |          8836.01 |            4.575 |               3 |      2 |        1 |           386.53 | False                  | True       |
| 2025-07     |          8447.37 |           -4.398 |               4 |      0 |        4 |          -388.64 | False                  | True       |
| 2025-08     |          8794.74 |            4.112 |               7 |      3 |        4 |           347.37 | False                  | True       |
| 2025-09     |          8706.31 |           -1.006 |               1 |      0 |        1 |           -88.43 | False                  | True       |
| 2025-10     |          8516.73 |           -2.177 |               2 |      0 |        2 |          -162.84 | True                   | True       |
| 2025-11     |          9205.94 |            8.092 |              10 |      5 |        5 |           692.59 | True                   | True       |
| 2025-12     |          9235.56 |            0.322 |               7 |      2 |        5 |            16.09 | True                   | True       |
| 2026-01     |          9497.19 |            2.833 |               5 |      2 |        3 |           245.05 | False                  | True       |
| 2026-02     |          8885.13 |           -6.445 |               6 |      0 |        6 |          -612.06 | False                  | True       |
| 2026-03     |          8846.92 |           -0.43  |               4 |      1 |        3 |           -38.21 | False                  | True       |
| 2026-04     |          9443.37 |            6.742 |               5 |      3 |        2 |           563.61 | True                   | True       |
| 2026-05     |          9320.65 |           -1.3   |               4 |      1 |        3 |           -40.6  | True                   | True       |
| 2026-06     |          9328.94 |            0.089 |               4 |      1 |        3 |           -34.22 | True                   | True       |
| 2026-07     |          8710.54 |           -6.629 |               6 |      0 |        6 |          -625.17 | False                  | True       |
| 2026-08     |          8900.71 |            2.183 |               1 |      1 |        0 |           222.18 | True                   | True       |
| 2026-09     |          8342.37 |           -6.273 |               6 |      0 |        6 |          -590.36 | False                  | True       |
| 2026-10     |          7907.18 |           -5.217 |               5 |      0 |        5 |          -435.18 | False                  | True       |
| 2026-11     |          8056.04 |            1.883 |               2 |      1 |        1 |           148.86 | False                  | False      |

## All-period summary
{
  "source": "Delta Exchange India BTCUSD perpetual 1m actual OHLCV",
  "timeframe": "1H closed candle; next genuine 1m OPEN entry and 1m stop/TP",
  "bars_1m": 990720,
  "period_start_utc": "2025-01-01 00:00:00+00:00",
  "period_end_utc": "2026-11-19 23:59:00+00:00",
  "initial_equity_usd": 10000.0,
  "final_marked_equity_usd": 8056.04,
  "ignored_while_position_open": 26,
  "invalid_risk_signals": 0,
  "trades_closed": 108,
  "wins": 25,
  "losses": 83,
  "win_rate_pct": 23.15,
  "profit_factor_net": 0.764,
  "avg_R_net": -0.1972,
  "total_gross_usd": -773.7,
  "total_slippage_usd": 106.74,
  "total_fees_gst_usd": 1073.55,
  "funding_proxy_usd": 10.04,
  "net_closed_usd": -1943.96,
  "max_drawdown_month_end_pct": -20.93,
  "positive_complete_ist_months": 9,
  "total_complete_ist_months": 22,
  "funding_settlements_with_open_positions": 495,
  "missing_funding_rate_proxy_events": 0,
  "remaining_position": null,
  "caveats": [
    "Source is Delta BTCUSD perpetual not Binance BTCUSDT spot: cross-venue replication differs.",
    "Publisher permits concurrent opposite side positions; this uses only one total position.",
    "Simulated 5 USD adverse slippage per side, 0.05% taker fee each side plus 18% GST.",
    "Funding rates are hourly indicative proxies, not actual payments; not proven executable.",
    "No spread/L1 order book, impact, fill depth, liquidation, contract minimums or real margin.",
    "Month-end equity includes unrealized open position at pessimistic estimated exit cost.",
    "2026 is previously research-exposed, not a pristine out-of-sample validation."
  ],
  "raw_hourly_signals": 134,
  "strategy": "Failed 1H breakout displacement order-block body; subsequent decisive failure; fixed 3R",
  "published_strategy_exact_replica": false,
  "source_files": 23,
  "funding_proxy_files": 23,
  "detector": {
    "complete_1h_bars": 16512,
    "raw_qualifying_breaker_signals": 134,
    "qualifying_displacement_blocks_created": 1202,
    "order_blocks_expired_or_consumed": 1201,
    "body_cross_events_all_sessions": 650,
    "events_rejected_outside_session": 405,
    "simultaneous_block_flip_collisions": 111,
    "market_session_utc": "candle OPEN hours 13,14,15,16",
    "measured_period": "2025-01-01 01:00:00+00:00 to 2026-11-20 00:00:00+00:00"
  }
}

Caveats: raw 1m OHLC has no true bid/ask depth or intraminute tick path; funding rate proxy not settlement cashflow; 2026 already researched, not untouched validation. November incomplete.
