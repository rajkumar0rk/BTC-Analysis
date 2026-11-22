# BTCUSD EMA9/21 (1H + 15M + 5M): Fixed 100-point stop / 200-point target

## Complete 1-minute execution results

| case                     |   trades |   wins |   losses |   win_rate_pct |   targets_hit |   stops_hit |   2025_return_pct |   2026_JanOct_return_pct |   total_1x_account_return_pct |   max_trade_close_drawdown_pct |   positive_months |
|:-------------------------|---------:|-------:|---------:|---------------:|--------------:|------------:|------------------:|-------------------------:|------------------------------:|-------------------------------:|------------------:|
| weekdays_IST_SL100_TP200 |     1130 |    359 |      771 |          31.77 |           359 |         771 |            -55.47 |                   -48.21 |                        -76.94 |                          76.97 |                 0 |
| all_days_SL100_TP200     |     1549 |    482 |     1067 |          31.12 |           482 |        1067 |            -67.32 |                   -60.58 |                        -87.12 |                          87.13 |                 0 |

## IST calendar month net 1x account returns (%)

| month_ist   |   all_days_SL100_TP200 |   weekdays_IST_SL100_TP200 |
|:------------|-----------------------:|---------------------------:|
| 2025-01     |                 -10.29 |                      -8.25 |
| 2025-02     |                  -7.58 |                      -5.64 |
| 2025-03     |                  -9.42 |                      -5.69 |
| 2025-04     |                  -6.42 |                      -5.15 |
| 2025-05     |                 -10.03 |                      -7.48 |
| 2025-06     |                  -5.59 |                      -3.75 |
| 2025-07     |                  -8.67 |                      -6.41 |
| 2025-08     |                  -8.33 |                      -5.90 |
| 2025-09     |                 -12.94 |                     -10.61 |
| 2025-10     |                 -10.23 |                      -7.78 |
| 2025-11     |                  -8.23 |                      -5.13 |
| 2025-12     |                  -8.82 |                      -6.26 |
| 2026-01     |                  -8.94 |                      -6.46 |
| 2026-02     |                 -11.35 |                      -8.52 |
| 2026-03     |                 -11.17 |                      -6.94 |
| 2026-04     |                  -7.53 |                      -5.59 |
| 2026-05     |                  -9.65 |                      -6.06 |
| 2026-06     |                  -6.73 |                      -6.55 |
| 2026-07     |                  -7.42 |                      -4.40 |
| 2026-08     |                  -9.54 |                      -7.06 |
| 2026-09     |                  -9.64 |                      -7.47 |
| 2026-10     |                  -6.76 |                      -4.54 |

## Exact execution and caveats
- Reuses the already-verified signal generator from the previous 2R/3R experiment.
- **100-point SL and 200-point TP are measured from slippage-adjusted entry fill**.
- Confirm 1H and 15M bars are fully closed, confirm 5M close crossover, enter at next available 1m open.
- On 1m stop+target ties, **stop executes first**; stop gaps use adverse opening price.
- No timeout and no trailing; one open trade per case; IST month boundary flattened.
- Entries compared on IST Monday-Friday only vs unrestricted 7 days; existing open trades can exit on weekends.
- Includes 0.05% taker fee per side, 18% GST on fees, and $5 adverse execution per side.
- 1× notional compounding at trade close; maximum drawdown based only on trade-close equity.
- Data: 992,160 source 1m bars, 2025-01-01 00:00:00+00:00 to 2026-11-20 23:59:00+00:00.
- Historical data gaps: [].
- Partial IST month: [('2025-01', 330)]
- 2025 and 2026 previously researched, **not blind forward-tested**. November 2026 excluded.
- No funding, order book spread/impact, maker fills, margin/lot feasibility or liquidation.
- Do not describe a negative/positive return as guaranteed future performance.

## Reproducible artifacts
- NOVELTY_CHECK.md, trade_ledger.csv, monthly_results.csv, summary.csv, quality.json
