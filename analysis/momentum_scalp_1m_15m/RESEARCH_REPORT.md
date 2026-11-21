# BTCUSD 1-minute momentum scalp with closed 15-minute EMA regime

## Predeclared settings
- Long: EMA20>EMA50 on last closed 15M, RSI14>55 on 1M, volume>1.5x prior20 1M mean, close above prior10 1M highs; short reverse.
- Entry next 1M open; initial stop=1x 1M ATR14; gross take-profit=2x ATR14; stop first if ambiguity.
- One open position, 60-minute max, force flat at IST month boundary.
- Taker 0.05% each leg + 18% GST; 5 USD BTC price slippage each leg; 1x account exposure compounded.

## Summary

```json
{
  "strategy": "BTCUSD_1m_volume_RSI_10bar_breakout_15m_EMA",
  "total_trades": 37638,
  "net_win_rate_pct": 11.935,
  "profit_factor": 0.0763,
  "total_compounded_return_pct": -100.0,
  "max_closed_trade_drawdown_pct": 100.0,
  "year2025_compounded_return_pct": -100.0,
  "year2026_through_nov20_compounded_return_pct": -100.0,
  "fully_covered_IST_months": 21,
  "positive_full_IST_months": 0,
  "negative_full_IST_months": 21,
  "zero_full_IST_months": 0,
  "full_IST_months_at_least_10_pct": 0,
  "initial_reference_equity_usd": 1000.0,
  "final_reference_equity_usd": 0.0
}
```

## Monthly realized NET account returns (IST)

| month_ist   | coverage          |   trades |   wins |   losses |   win_rate_pct |   monthly_net_return_pct |   total_fee_pct_of_trade_notional |   total_slippage_pct_of_trade_notional |   gross_trade_return_pct_sum |   profit_factor |
|:------------|:------------------|---------:|-------:|---------:|---------------:|-------------------------:|----------------------------------:|---------------------------------------:|-----------------------------:|----------------:|
| 2025-01     | partial_start_IST |     1664 |    266 |     1398 |         15.986 |                 -89.1872 |                           196.353 |                                16.6741 |                     -9.1199  |          0.1049 |
| 2025-02     | full_IST          |     1563 |    235 |     1328 |         15.035 |                 -86.8451 |                           184.435 |                                16.3945 |                     -1.7066  |          0.1354 |
| 2025-03     | full_IST          |     1644 |    277 |     1367 |         16.849 |                 -89.4624 |                           194     |                                19.363  |                    -11.2887  |          0.1396 |
| 2025-04     | full_IST          |     1590 |    231 |     1359 |         14.528 |                 -88.0754 |                           187.619 |                                18.5402 |                     -6.2161  |          0.1021 |
| 2025-05     | full_IST          |     1690 |    203 |     1487 |         12.012 |                 -88.0131 |                           199.421 |                                16.4248 |                      3.91719 |          0.0496 |
| 2025-06     | full_IST          |     1583 |    111 |     1472 |          7.012 |                 -87.1267 |                           186.793 |                                14.9998 |                     -3.02595 |          0.0313 |
| 2025-07     | full_IST          |     1696 |    122 |     1574 |          7.193 |                 -87.9997 |                           200.128 |                                14.7837 |                      3.06843 |          0.0272 |
| 2025-08     | full_IST          |     1722 |    111 |     1611 |          6.446 |                 -89.2741 |                           203.204 |                                14.9998 |                     -4.85015 |          0.0273 |
| 2025-09     | full_IST          |     1605 |     64 |     1541 |          3.988 |                 -86.9844 |                           189.39  |                                14.2229 |                     -0.12935 |          0.0124 |
| 2025-10     | full_IST          |     1738 |    230 |     1508 |         13.234 |                 -89.4342 |                           205.089 |                                15.2726 |                     -4.11513 |          0.0734 |
| 2025-11     | full_IST          |     1667 |    379 |     1288 |         22.735 |                 -87.7931 |                           196.712 |                                17.3367 |                      4.01837 |          0.124  |
| 2025-12     | full_IST          |     1727 |    195 |     1532 |         11.291 |                 -90.1507 |                           203.788 |                                19.4044 |                     -8.32001 |          0.0792 |
| 2026-01     | full_IST          |     1711 |    162 |     1549 |          9.468 |                 -88.9125 |                           201.902 |                                18.9211 |                      1.11344 |          0.0603 |
| 2026-02     | full_IST          |     1527 |    367 |     1160 |         24.034 |                 -87.4457 |                           180.183 |                                22.1203 |                     -4.80128 |          0.1957 |
| 2026-03     | full_IST          |     1643 |    325 |     1318 |         19.781 |                 -89.2202 |                           193.878 |                                23.6254 |                     -4.93946 |          0.1152 |
| 2026-04     | full_IST          |     1534 |    171 |     1363 |         11.147 |                 -87.3728 |                           181.01  |                                20.9578 |                     -4.75293 |          0.05   |
| 2026-05     | full_IST          |     1686 |    101 |     1585 |          5.991 |                 -89.1651 |                           198.946 |                                21.6231 |                     -1.47875 |          0.0183 |
| 2026-06     | full_IST          |     1652 |    262 |     1390 |         15.86  |                 -89.7053 |                           194.934 |                                26.0656 |                     -6.04106 |          0.115  |
| 2026-07     | full_IST          |     1761 |    132 |     1629 |          7.496 |                 -90.578  |                           207.793 |                                27.6501 |                     -0.5512  |          0.0287 |
| 2026-08     | full_IST          |     1744 |    141 |     1603 |          8.085 |                 -90.0147 |                           205.788 |                                25.4073 |                      1.01529 |          0.0495 |
| 2026-09     | full_IST          |     1640 |    123 |     1517 |          7.5   |                 -87.9172 |                           193.521 |                                20.4628 |                      2.84882 |          0.0424 |
| 2026-10     | full_IST          |     1697 |     99 |     1598 |          5.834 |                 -89.9959 |                           200.249 |                                20.6359 |                     -9.12772 |          0.0188 |
| 2026-11     | partial_end_IST   |     1154 |    185 |      969 |         16.031 |                 -77.3449 |                           136.17  |                                16.1237 |                      4.00813 |          0.116  |

## Important caveats

- 1x notional/equity at each entry and compounded
- Full 15M bars only, strictly causal trend filter
- 1m Wilder RSI14 and ATR14 computed on closed signal bar
- next 1m open plus 5 USD adverse slip per side
- 0.05 percent taker per side plus 18 percent GST
- 60 minute timeout, one position shared by both directions
- stop-first on same minute target and stop; stop gaps fill worse
- IST month boundary flat; Jan 2025 starts 05:30 IST (partial); Nov 2026 partial
- No funding, spread, actual bid-ask, order book liquidity, liquidation, market impact
- All 2025-2026 historical data previously exposed, not pristine out-of-sample

## Data quality

```json
{
  "data_source": "Delta Exchange India BTCUSD 1-minute OHLCV archive",
  "source_files": [
    "2025-01.csv.gz",
    "2025-02.csv.gz",
    "2025-03.csv.gz",
    "2025-04.csv.gz",
    "2025-05.csv.gz",
    "2025-06.csv.gz",
    "2025-07.csv.gz",
    "2025-08.csv.gz",
    "2025-09.csv.gz",
    "2025-10.csv.gz",
    "2025-11.csv.gz",
    "2025-12.csv.gz",
    "2026-01.csv.gz",
    "2026-02.csv.gz",
    "2026-03.csv.gz",
    "2026-04.csv.gz",
    "2026-05.csv.gz",
    "2026-06.csv.gz",
    "2026-07.csv.gz",
    "2026-08.csv.gz",
    "2026-09.csv.gz",
    "2026-10.csv.gz",
    "2026-11.csv.gz"
  ],
  "rows": 992160,
  "first_utc": "2025-01-01 00:00:00+00:00",
  "last_utc": "2026-11-20 23:59:00+00:00",
  "missing_utc_minutes": 0,
  "gaps": []
}
```

Historical optimization exposure and uncertain API candle label convention require forward validation.
Backtest is not an executable fill guarantee.
