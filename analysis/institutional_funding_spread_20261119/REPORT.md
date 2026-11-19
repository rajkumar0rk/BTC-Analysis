# Institutional mechanism-first BTC/ETH funding spread study

## PREDECLARED hypothesis
When persistent funding rate difference is large enough to amortize two-leg roundtrip execution cost, a short-high / long-low same-exchange perp pair may collect net funding without needing BTC's absolute direction. This is NOT guaranteed delta-neutral or risk-free.

## Base and diagnostics: years 2025, 2026
                            scenario  year  calendar_days  profitable_calendar_days  losing_calendar_days  no_position_days  positive_calendar_day_pct  new_entries  realized_trades  realized_positive_trades  average_daily_net_usd  median_daily_net_usd  worst_daily_net_usd  max_dayclose_drawdown_pct  daily_net_profit_factor  net_return_pct  profitable_months  year_months
               primary_2x_cost_taker  2025            365                         0                     0               365                      0.000            0                0                         0                0.00000                   0.0              0.00000                     0.0000                      NaN         0.00000                  0           12
               primary_2x_cost_taker  2026            321                         7                     8               306                      2.181            1                1                         1                0.05645                   0.0             -4.49910                    -1.2515                   1.7957         1.81189                  1           11
            diagnostic_1x_cost_taker  2025            365                        30                    27               308                      8.219            6                6                         2                0.07193                   0.0            -35.67281                    -4.6316                   1.1232         2.62543                  3           12
            diagnostic_1x_cost_taker  2026            321                        46                    42               233                     14.330            7                7                         5                0.37110                   0.0            -14.73422                    -2.2913                   1.7798        11.60749                  5           11
       diagnostic_no_cost_gate_taker  2025            365                       124                   129               115                     33.973           57               57                        24               -0.04443                   0.0            -57.01282                   -22.2586                   0.9839        -1.62158                  7           12
       diagnostic_no_cost_gate_taker  2026            321                       156                   152                13                     48.598           46               46                        28                0.36029                   0.0            -28.14543                    -7.3216                   1.1708        11.75609                  6           11
       stress_2x_cost_taker_5bp_slip  2025            365                         0                     0               365                      0.000            0                0                         0                0.00000                   0.0              0.00000                     0.0000                      NaN         0.00000                  0           12
       stress_2x_cost_taker_5bp_slip  2026            321                         0                     0               321                      0.000            0                0                         0                0.00000                   0.0              0.00000                     0.0000                      NaN         0.00000                  0           11
optimistic_maker_envelope_UNVERIFIED  2025            365                        51                    41               273                     13.973            9                9                         7                0.47997                   0.0            -25.43178                    -4.1107                   1.7190        17.51895                  5           12
optimistic_maker_envelope_UNVERIFIED  2026            321                        75                    77               169                     23.364           17               17                        12                0.24579                   0.0            -31.97954                    -5.6158                   1.2031         6.71357                  6           11

## Data and capital integrity
Source: Delta India 1-minute traded BTCUSD/ETHUSD prices, MARK: 1-minute and FUNDING: 1-hour price/rate observations, 2025-01-01 to 2026-11-17 UTC, no missing candles. Historical funding rate is not a settlement receipt.

## Mandatory caveats
- No historical orderbook; fills at 1h OPEN with 2bp adverse slippage are only a proxy
- Funding 1h close series does NOT establish actual settlement cashflows or transfer timing
- Two crypto assets are imperfect hedge; BTC-ETH correlation and beta change
- No exact exchange settlement/contract denominations, tick/lot, maker fill certainty, maintenance margin, liquidation model
- 1h entry/exit and risk stops can miss intrahour adverse excursion
- Fees and slippage on both legs BOTH sides; stress 5bp each; all calendar days included
- No independent forward data; 2026 previously research exposed
- No model is qualified for live trade without verified reconciled settlement cashflows, margin and actual fill confirmation
