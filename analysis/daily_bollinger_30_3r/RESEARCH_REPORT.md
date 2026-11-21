# BTCUSD daily Bollinger(30,2), 3R — genuine 1m execution replication

**Data:** genuine Delta India BTCUSD perpetual 1-minute bars, no reconstructed wick path.
**Signal:** completed UTC day close outside Bollinger(30, 2); stop 0.25 Wilder ATR14 beyond signal bar low/high.
**Fill:** next 1m OPEN; fixed 3R; stop wins ambiguous same-minute bar. No time exit, no trailing.
**Costs:** 0.05% futures taker fee per side and GST 18% on fee; 5 BTC points adverse slip each side; hourly historical funding rates only as a settlement proxy.
**Sizing:** 1% account initial stop-risk, maximum 2x notional/account equity, one position at once, continuous quantity proxy.
**Critical differences from published spot test:** Delta futures, later executable next-minute entry, no concurrent opposites, full Delta fee/tax assumptions.

## Summary
~~~json
{
  "source": "Delta Exchange India BTCUSD perpetual 1m actual OHLCV",
  "timeframe": "1D UTC close; next 1m OPEN entry, 1m stop/TP",
  "bars_1m": 990720,
  "period_start_utc": "2025-01-01 00:00:00+00:00",
  "period_end_utc": "2026-11-19 23:59:00+00:00",
  "initial_equity_usd": 10000.0,
  "final_marked_equity_usd": 10759.31,
  "raw_daily_signals": 91,
  "ignored_while_position_open": 74,
  "invalid_risk_signals": 0,
  "trades_closed": 16,
  "wins": 6,
  "losses": 10,
  "win_rate_pct": 37.5,
  "profit_factor_net": 1.697,
  "avg_R_net": 0.4494,
  "total_gross_usd": 796.18,
  "total_slippage_usd": 4.19,
  "total_fees_gst_usd": 42.41,
  "funding_proxy_usd": -35.75,
  "net_closed_usd": 713.83,
  "max_drawdown_month_end_pct": -2.84,
  "positive_complete_ist_months": 10,
  "total_complete_ist_months": 22,
  "funding_settlements_with_open_positions": 1344,
  "missing_funding_rate_proxy_events": 5,
  "remaining_position": {
    "side": -1,
    "entry_utc": "2026-11-15 00:00:00+00:00",
    "entry_fill": 64125.0,
    "stop": 69077.77980866873,
    "target": 49266.660573993824,
    "qty_btc": 0.02163195337562401
  },
  "caveats": [
    "Source is Delta BTCUSD perpetual not Binance BTCUSDT spot: cross-venue replication differs.",
    "Publisher permits concurrent opposite side positions; this uses only one total position.",
    "Simulated 5 USD adverse slippage per side, 0.05% taker fee each side plus 18% GST.",
    "Funding rates are hourly indicative proxies, not actual payments; not proven executable.",
    "No spread/L1 order book, impact, fill depth, liquidation, contract minimums or real margin.",
    "Month-end equity includes unrealized open position at pessimistic estimated exit cost.",
    "2026 is previously research-exposed, not a pristine out-of-sample validation."
  ],
  "days_complete": 688,
  "raw_daily_signals_computed": 92,
  "source_partitions": 23,
  "funding_proxy_partitions": 23
}
~~~

## Monthly marked-to-market IST account results
| month_ist   |   end_equity_usd |   net_return_pct |   trades_closed |   wins |   losses |   net_closed_usd | open_position_at_end   | complete   |
|:------------|-----------------:|-----------------:|----------------:|-------:|---------:|-----------------:|:-----------------------|:-----------|
| 2025-01     |         10000    |            0     |               0 |      0 |        0 |             0    | False                  | True       |
| 2025-02     |         10133.4  |            1.334 |               0 |      0 |        0 |             0    | True                   | True       |
| 2025-03     |         10141    |            0.074 |               0 |      0 |        0 |             0    | True                   | True       |
| 2025-04     |          9954.31 |           -1.84  |               0 |      0 |        0 |             0    | True                   | True       |
| 2025-05     |          9905.13 |           -0.494 |               1 |      0 |        1 |          -100.43 | True                   | True       |
| 2025-06     |          9930.86 |            0.26  |               0 |      0 |        0 |             0    | True                   | True       |
| 2025-07     |         10063.4  |            1.335 |               0 |      0 |        0 |             0    | True                   | True       |
| 2025-08     |          9925.08 |           -1.375 |               0 |      0 |        0 |             0    | True                   | True       |
| 2025-09     |          9973    |            0.483 |               0 |      0 |        0 |             0    | True                   | True       |
| 2025-10     |         10015.4  |            0.425 |               2 |      1 |        1 |           115.78 | False                  | True       |
| 2025-11     |         10216.7  |            2.01  |               2 |      1 |        1 |           201.36 | False                  | True       |
| 2025-12     |         10216.7  |            0     |               0 |      0 |        0 |             0    | False                  | True       |
| 2026-01     |         10116.4  |           -0.982 |               2 |      0 |        2 |          -214.55 | True                   | True       |
| 2026-02     |         10284.8  |            1.664 |               1 |      1 |        0 |           300.52 | True                   | True       |
| 2026-03     |         10098.8  |           -1.808 |               2 |      0 |        2 |          -203.93 | False                  | True       |
| 2026-04     |          9995.6  |           -1.022 |               1 |      0 |        1 |          -103.16 | False                  | True       |
| 2026-05     |          9992.83 |           -0.028 |               0 |      0 |        0 |             0    | True                   | True       |
| 2026-06     |         10465.9  |            4.734 |               1 |      1 |        0 |           300.25 | True                   | True       |
| 2026-07     |         10388.4  |           -0.74  |               0 |      0 |        0 |             0    | True                   | True       |
| 2026-08     |         10343.7  |           -0.431 |               1 |      0 |        1 |           -76.04 | True                   | True       |
| 2026-09     |         10459.5  |            1.12  |               1 |      1 |        0 |           287.71 | True                   | True       |
| 2026-10     |         10402.2  |           -0.549 |               1 |      0 |        1 |          -109.63 | True                   | True       |
| 2026-11     |         10759.3  |            3.433 |               1 |      1 |        0 |           315.95 | True                   | False      |

## Yearly account results
|   year |   return_pct |   trades_closed | complete   |
|-------:|-------------:|----------------:|:-----------|
|   2025 |        2.167 |               5 | True       |
|   2026 |        5.311 |              11 | False      |

## Important validity
- Nov 2026 is incomplete. 2025/2026 have prior research exposure; these are not blind validation months.
- Funding estimates do NOT equal reconciled settlement cashflows. Rates treated as percent per source conventions.
- One-minute bars still cannot resolve a stop/target hit order within the same minute; STOP wins ties, conservatively.
- Yearly/monthly marked equity subtracts hypothetical exit fees on positions open at month-end.
- No exchange bid/ask or liquidation modeling. Do not trade live from this study alone.

See trade_ledger.csv, monthly_ist.csv, yearly_ist.csv and summary.json.
