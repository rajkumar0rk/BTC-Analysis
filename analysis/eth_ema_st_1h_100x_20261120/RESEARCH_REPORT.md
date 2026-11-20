# ETHUSD EMA20/ST 1h, ETH-scaled 100/50, isolated 100x

22 completed UTC months January 2025 through October 2026.
Underlying reference: earlier 1h screenshot backtest, unchanged signals and trailing percentages.

## Net portfolio results

{
  "starting_balance_usd": 100.0,
  "ending_balance_usd": 3926.8616,
  "net_profit_usd": 3826.8616,
  "total_return_on_initial_balance_pct": 3826.86,
  "trades": 1678,
  "win_rate_pct": 73.42,
  "profit_factor": 2.8541,
  "modeled_liquidations": 230,
  "scalper_eligible_trades": 0,
  "max_closed_equity_drawdown_pct": 23.2,
  "signals_on_bars": 2487,
  "signals_reached_while_flat": 1678,
  "skipped_insufficient_wallet": 0,
  "skipped_less_than_one_contract": 0,
  "has_open_position_at_cutoff": false,
  "gross_realized_usd": 5780.619,
  "entry_fees_usd": 827.9989,
  "exit_fees_usd": 714.222,
  "gst_usd": 298.0308,
  "liquidation_penalties_usd": 113.5056,
  "profitable_months": 22,
  "losing_months": 0,
  "flat_months": 0
}

## Monthly results

| month_utc   |   starting_balance_usd |   net_profit_usd |   monthly_return_pct |   ending_balance_usd |   trades |   wins |   losses |   liquidations |
|:------------|-----------------------:|-----------------:|---------------------:|---------------------:|---------:|-------:|---------:|---------------:|
| 2025-01     |                100     |         148.368  |               148.37 |              248.368 |       74 |     56 |       18 |             12 |
| 2025-02     |                248.368 |         210.899  |                84.91 |              459.267 |       65 |     48 |       17 |             12 |
| 2025-03     |                459.267 |         311.227  |                67.77 |              770.494 |       83 |     58 |       25 |             17 |
| 2025-04     |                770.494 |          49.1678 |                 6.38 |              819.662 |       75 |     49 |       26 |             14 |
| 2025-05     |                819.662 |         198.687  |                24.24 |             1018.35  |       70 |     56 |       14 |             12 |
| 2025-06     |               1018.35  |         113.068  |                11.1  |             1131.42  |       73 |     51 |       22 |             12 |
| 2025-07     |               1131.42  |         220.545  |                19.49 |             1351.96  |       72 |     55 |       17 |             11 |
| 2025-08     |               1351.96  |         315.625  |                23.35 |             1667.59  |       68 |     53 |       15 |              5 |
| 2025-09     |               1667.59  |         118.278  |                 7.09 |             1785.87  |       86 |     62 |       24 |             11 |
| 2025-10     |               1785.87  |         229.681  |                12.86 |             2015.55  |       86 |     65 |       21 |             11 |
| 2025-11     |               2015.55  |         211.018  |                10.47 |             2226.56  |       77 |     57 |       20 |             11 |
| 2025-12     |               2226.56  |         151.232  |                 6.79 |             2377.8   |       81 |     57 |       24 |             15 |
| 2026-01     |               2377.8   |         232.885  |                 9.79 |             2610.68  |       75 |     60 |       15 |              5 |
| 2026-02     |               2610.68  |         265.511  |                10.17 |             2876.19  |       73 |     54 |       19 |             13 |
| 2026-03     |               2876.19  |         274.22   |                 9.53 |             3150.41  |       85 |     68 |       17 |              8 |
| 2026-04     |               3150.41  |         103.916  |                 3.3  |             3254.33  |       83 |     62 |       21 |             12 |
| 2026-05     |               3254.33  |         164.463  |                 5.05 |             3418.79  |       81 |     61 |       20 |              6 |
| 2026-06     |               3418.79  |         129.022  |                 3.77 |             3547.81  |       69 |     52 |       17 |             11 |
| 2026-07     |               3547.81  |         134.655  |                 3.8  |             3682.47  |       63 |     49 |       14 |              7 |
| 2026-08     |               3682.47  |          59.7036 |                 1.62 |             3742.17  |       83 |     53 |       30 |             10 |
| 2026-09     |               3742.17  |         140.097  |                 3.74 |             3882.27  |       86 |     60 |       26 |              7 |
| 2026-10     |               3882.27  |          44.5928 |                 1.15 |             3926.86  |       70 |     46 |       24 |              8 |

## Method caveats

- 1-hour historical OHLC broker-emulator approximation, not verified exchange execution or TradingView broker tester exactness.
- Liquidation based on trade-price OHLC and constant 0.25% assumed maintenance; actual Delta mark-price liquidation not reconstructed.
- Exchange margin details, lot increments, and historical scalper entitlement not independently verified.
- Conservative 1-hour close timing yields no 27-minute eligible trades; true minute-of-touch not available in 1-hour OHLC.
- Funding charges, actual spread, slippage, order latency excluded per screenshot assumptions.
- Unrealized P&L on a final unclosed position is not recognized in ending balance.
- 100x leverage changes quantity and liquidation; unleveraged net is not multiplied by 100.
