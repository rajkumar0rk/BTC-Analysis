# BTCUSD 15m Reclaim — 3% SL / 9% TP month-by-month

Exact re-run of the prior NOFLIP model, using the unmodified backtest engine.
15M Supertrend(10,3) + EMA20 for entry only; no Supertrend reversal exit;
fixed 3% SL of filled entry price and 9% TP (3R); profit protection OFF.
One trade open maximum; entry signals arriving while in position skipped.
Jan 2025–Oct 2026, 22 IST monthly periods; $1,000 initial, 1x evolving notional.
Fees 0.05% taker per side + 18% GST, slippage 0.02% adverse each side.
Monthly return calculated from end-of-month marked-to-market equity,
so monthly returns can include unrealized P&L on an open trade.
Number of trades shown is number EXITED in each month, not signal count.
Backtest does not model real spread, execution depth, funding or liquidation.
This same historical sample has been repeatedly studied; no out-of-sample verification.

## Exact 22 monthly returns

| month_ist   |   monthly_return_pct |   equity_usd |   exits |   winning_exits |   losing_exits | position_open   |
|:------------|---------------------:|-------------:|--------:|----------------:|---------------:|:----------------|
| 2025-01     |               -2.017 |      979.830 |       5 |               1 |              4 | True            |
| 2025-02     |                3.129 |     1010.486 |       2 |               1 |              1 | False           |
| 2025-03     |              -13.330 |      875.793 |       8 |               1 |              7 | True            |
| 2025-04     |                5.240 |      921.685 |       6 |               2 |              4 | True            |
| 2025-05     |               -5.966 |      866.701 |       5 |               1 |              4 | True            |
| 2025-06     |                6.737 |      925.090 |       2 |               1 |              1 | True            |
| 2025-07     |                3.889 |      961.065 |       3 |               1 |              2 | True            |
| 2025-08     |                4.368 |     1003.045 |       2 |               1 |              1 | True            |
| 2025-09     |                4.101 |     1044.175 |       0 |               0 |              0 | True            |
| 2025-10     |               11.747 |     1166.831 |       4 |               2 |              2 | True            |
| 2025-11     |                5.590 |     1232.062 |       5 |               2 |              3 | True            |
| 2025-12     |              -15.320 |     1043.315 |       4 |               0 |              4 | True            |
| 2026-01     |                8.708 |     1134.162 |       5 |               2 |              3 | False           |
| 2026-02     |               21.056 |     1372.969 |       5 |               3 |              2 | False           |
| 2026-03     |                6.820 |     1466.603 |       3 |               1 |              2 | True            |
| 2026-04     |               -4.876 |     1395.085 |       1 |               0 |              1 | True            |
| 2026-05     |               14.150 |     1592.496 |       2 |               2 |              0 | True            |
| 2026-06     |                1.593 |     1617.859 |       8 |               2 |              6 | True            |
| 2026-07     |               -3.744 |     1557.287 |       1 |               0 |              1 | True            |
| 2026-08     |                8.848 |     1695.077 |       1 |               1 |              0 | True            |
| 2026-09     |                8.397 |     1837.420 |       1 |               1 |              0 | True            |
| 2026-10     |                7.498 |     1975.183 |       2 |               2 |              0 | True            |

## Annual / full-window summary

2025 4.331% with 8/12 positive months.
Jan–Oct 2026 89.318% with 8/10 positive months.
Full Jan 2025–Oct 2026 97.5183%, 16/22 profitable months.
75 completed trades: 27 positive and 48 negative; 26 TP, 48 SL and 1 final sample close.
Alternate simulated 1m OHLC path reproduced identical net and monthly returns.
