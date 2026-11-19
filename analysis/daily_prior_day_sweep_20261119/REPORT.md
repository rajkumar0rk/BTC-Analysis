# Independent prior-day extreme liquidity sweep

symbol  year    mode  buffer  target  stop  hold_min  days  trades  profitable_days  losing_days  no_trade_days  profitable_calendar_day_pct  win_rate_traded_pct  net_profit_usd  net_return_pct  profit_factor  mean_daily_usd  median_daily_usd  worst_day_usd  max_consecutive_losing_days  max_dayclose_drawdown_pct  fees_usd  funding_debit_usd  train_pass
BTCUSD  2025 reclaim  0.0015   0.003 0.006       180   365     138               84           54            227                       23.014               60.870        -178.765        -17.8765         0.3681         -0.4898               0.0        -6.1540                            3                   -17.9874  124.9733             1.2209       False
BTCUSD  2026 reclaim  0.0015   0.003 0.006       180   321     123               86           37            198                       26.791               69.919         -65.683         -7.9981         0.5800         -0.2046               0.0        -5.1626                            2                    -9.9328   96.5394             1.5937       False
ETHUSD  2025 reclaim  0.0015   0.008 0.006       180   365     188               85          103            177                       23.288               45.213        -160.945        -16.0945         0.7034         -0.4409               0.0        -6.2379                            5                   -18.4868  165.6996             1.3461       False
ETHUSD  2026 reclaim  0.0015   0.008 0.006       180   321     144               50           94            177                       15.576               34.722        -194.674        -23.2016         0.4655         -0.6065               0.0        -5.1838                            6                   -23.2016  102.5058             1.0730       False

## Caveats
- 2026 is research-exposed, not pristine forward validation
- Funding proxy, no actual funding rates
- No order book or precise margin/liquidation model
- No exchange lot-size or tick-size rounding
- Calendar days with no trade are NOT counted as profitable
- No guarantee of positive daily profit
