# Independent daily net-profit strategy research

Hypothesis: small mean-reversion moves around UTC day-anchored VWAP, after exhaustion and a 5m reversal candle.

Selection uses only 2025. 2026 research-exposed historical check, not a live-forward validation.

## Selected models — 2025 and 2026
symbol  year   dev     tp    sl  hold_min  volume_ratio_min  trades  days  profit_days  loss_days  no_trade_days  positive_calendar_day_pct  win_rate_traded_pct  profit_factor  net_return_pct  net_profit_usd  avg_calendar_day_usd  fees_usd  assumed_funding_usd  worst_day_usd  max_consecutive_losing_days  max_close_day_drawdown_pct  train_criteria_pass
BTCUSD  2025 0.007 0.0035 0.005        90              1.00     270   365          132        138             95                     36.164               48.889         0.4135        -31.4252       -314.2523               -0.8610  263.8224               1.9747        -6.3841                            6                    -31.7873                False
BTCUSD  2026 0.007 0.0035 0.005        90              1.00     239   321          108        131             82                     33.645               45.188         0.3511        -33.3875       -228.9543               -0.7133  160.8616               0.9313        -4.3933                            8                    -34.0824                False
ETHUSD  2025 0.005 0.0075 0.005       180              1.25     360   365          137        223              5                     37.534               38.056         0.5439        -43.7657       -437.6569               -1.1991  307.9346               2.4732        -6.4100                           10                    -44.1074                False
ETHUSD  2026 0.005 0.0075 0.005       180              1.25     298   321           98        200             23                     30.530               32.886         0.4277        -47.0483       -264.5731               -0.8242  150.5762               3.1527        -3.5900                            9                    -47.3545                False

## Interpretation
A winning backtest cannot guarantee daily net profit. No-trade days count against calendar-day coverage.

## Caveats
- Not every day has a signal; no forced trades
- 2026 previously viewed, not a genuine forward holdout
- No order book, spread model, exact intraminute sequence or exchange lot constraints
- Liquidation and margin risk not simulated
- Per-day drawdown uses day-close NAV, not intraday high water
- 2026 November only partial through 17 November UTC
