# Stage18 70/30 daily-realized profitability audit

## Real monthly account NAV snapshot (source backtest)

- 22-month compounded net: **14.4381%**
- Profitable/loss/flat months: **19/2/1**

## Daily REALIZED-EXIT proxy (NOT daily account PnL)

- Total IST calendar dates: **669**
- Days with one or more trade exits: **56**
- Positive realized-exit days: **36**
- Negative realized-exit days: **20**
- No-exit days: **613**
- Positive-calendar-day frequency: **5.38%**
- Positive fraction of exit days: **64.29%**
- Source core and Donchian closed trades: **63** / **10**

## Monthly counts of daily realized exits

| month_ist   |   calendar_days |   trade_exit_days |   positive_exit_days |   negative_exit_days |   flat_exit_days |   no_exit_days |   core_exits |   swing_exits |
|:------------|----------------:|------------------:|---------------------:|---------------------:|-----------------:|---------------:|-------------:|--------------:|
| 2025-01     |              31 |                 0 |                    0 |                    0 |                0 |             31 |            0 |             0 |
| 2025-02     |              28 |                 4 |                    2 |                    2 |                0 |             24 |            5 |             0 |
| 2025-03     |              31 |                 4 |                    3 |                    1 |                0 |             27 |            4 |             0 |
| 2025-04     |              30 |                 3 |                    3 |                    0 |                0 |             27 |            3 |             0 |
| 2025-05     |              31 |                 1 |                    0 |                    1 |                0 |             30 |            1 |             0 |
| 2025-06     |              30 |                 3 |                    2 |                    1 |                0 |             27 |            2 |             1 |
| 2025-07     |              31 |                 7 |                    4 |                    3 |                0 |             24 |            8 |             0 |
| 2025-08     |              31 |                 3 |                    2 |                    1 |                0 |             28 |            1 |             2 |
| 2025-09     |              30 |                 2 |                    1 |                    1 |                0 |             28 |            3 |             0 |
| 2025-10     |              31 |                 1 |                    1 |                    0 |                0 |             30 |            3 |             0 |
| 2025-11     |              30 |                 1 |                    1 |                    0 |                0 |             29 |            2 |             0 |
| 2025-12     |              31 |                 5 |                    4 |                    1 |                0 |             26 |           11 |             1 |
| 2026-01     |              31 |                 4 |                    1 |                    3 |                0 |             27 |            3 |             1 |
| 2026-02     |              28 |                 3 |                    2 |                    1 |                0 |             25 |            5 |             0 |
| 2026-03     |              31 |                 2 |                    2 |                    0 |                0 |             29 |            1 |             1 |
| 2026-04     |              30 |                 4 |                    2 |                    2 |                0 |             26 |            5 |             0 |
| 2026-05     |              31 |                 4 |                    3 |                    1 |                0 |             27 |            3 |             1 |
| 2026-06     |              30 |                 1 |                    0 |                    1 |                0 |             29 |            1 |             0 |
| 2026-07     |              31 |                 2 |                    2 |                    0 |                0 |             29 |            2 |             1 |
| 2026-08     |              31 |                 0 |                    0 |                    0 |                0 |             31 |            0 |             0 |
| 2026-09     |              30 |                 1 |                    1 |                    0 |                0 |             29 |            0 |             1 |
| 2026-10     |              31 |                 1 |                    0 |                    1 |                0 |             30 |            0 |             1 |

## Important limitations

- No trading or realized exit on most days means no claim of daily income
- Realized-exit-day proxy is not mark-to-market NAV, cannot recreate combined daily account equity
- Daily55 long-hold positions can gain/lose on days with no exit
- 0.7/0.3 weighted daily net proxy uses standalone 0.5% risk-per-trade returns and does not model daily rebalancing
- Only pre-existing model parameters tested; no after-the-fact day filter
- Fees incl GST and $5/side slip were modeled upstream; funding and actual order book depth omitted
- All 2025 and 2026 data already researched; no untouched forward sample

Stage18 historical 70/30 results are retrospective and a synthetic MONTHLY blend.
It is NOT possible to infer profitable every day from profitable months or positive exit days.
