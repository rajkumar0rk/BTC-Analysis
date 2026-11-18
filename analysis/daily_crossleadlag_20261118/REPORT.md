# Independent 1m cross-asset lead-lag daily net research

## Predeclared mechanics
A completed 1m BTC/ETH impulse with own market not yet catching up triggers trade in lagging market at next 1m OPEN. One trade per UTC day, time-capped, stop-first.

## 2025-selected models replayed unchanged in 2026

symbol  year  lookback_min  leader_threshold lag_type  target_fraction  stop_fraction  max_hold_min  days  trades  profitable_days  losing_days  no_trade_days  calendar_positive_day_pct  traded_win_rate_pct  profit_factor  net_return_pct  net_profit_usd  avg_net_per_calendar_day_usd  max_dayclose_drawdown_pct  worst_day_usd  fees_usd  funding_debit_usd  passes_2025_minimum
BTCUSD  2025            30             0.005     flat            0.003          0.004            60   365     361              137          224              4                     37.534               37.950         0.3182        -41.7201        -417.201                       -1.1430                   -41.7201        -6.6547  415.2820             1.5548                False
BTCUSD  2026            30             0.005     flat            0.003          0.004            60   321     287              124          163             34                     38.629               43.206         0.3246        -38.1781        -222.502                       -0.6932                   -38.1781        -3.9005  191.7207             1.1666                False
ETHUSD  2025             3             0.005  aligned            0.006          0.004            60   365      61               32           29            304                      8.767               52.459         0.8848         -2.1972         -21.972                       -0.0602                    -6.1699        -6.7531   87.6740             0.1203                False
ETHUSD  2026             3             0.005  aligned            0.006          0.004            60   321      56               26           30            265                      8.100               46.429         0.6849         -6.1464         -60.113                       -0.1873                    -7.7543        -6.6193   77.7453             0.1198                False

## Evidence caveats
- No guarantee of any positive daily net PnL
- 2026 already inspected by other prior research; not pristine OOS
- No orderbook, true funding settlements, lot sizes, liquidation engine or precise queue priority
- 1m OHLC stop-first pessimistic when target and stop touch
- Notional liquidity/slippage simplified; 1m BTC/ETH different volatility
- 2026 November incomplete
