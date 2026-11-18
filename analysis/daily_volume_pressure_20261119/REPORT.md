# Independent signed-volume pressure daily-net backtest

symbol  year  window  pressure_threshold       mode  target  stop  hold_min  calendar_days  trades  profitable_days  losing_days  no_trade_days  profitable_calendar_days_pct  profit_factor  net_return_pct  median_daily_net_usd  mean_daily_net_usd  worst_day_usd  max_losing_day_streak  max_dayclose_drawdown_pct  fees_usd  funding_debit_usd  passes_2025_minimum
BTCUSD  2025      60                 0.4 divergence   0.003 0.005        90            365       7                2            5            358                         0.548         0.2966         -0.7677                   0.0             -0.0210        -6.3676                      1                    -0.8494    8.2534                0.0                False
BTCUSD  2026      60                 0.4 divergence   0.003 0.005        90            321      10                3            7            311                         0.935         0.1655         -2.3894                   0.0             -0.0739        -6.3270                      2                    -2.7049   11.5031                0.0                False
ETHUSD  2025      60                 0.6 divergence   0.006 0.003        90            365       4                3            1            361                         0.822        11.5687          1.7610                   0.0              0.0482        -1.6663                      1                    -0.1647    7.9240                0.0                False
ETHUSD  2026      60                 0.6 divergence   0.006 0.003        90            321       0                0            0            321                         0.000            NaN          0.0000                   0.0              0.0000         0.0000                      0                     0.0000    0.0000                0.0                False

{
  "hypothesis": "Candle-direction signed volume pressure versus same-window price direction",
  "novelty": "1-minute candle-volume pressure divergence/continuation, distinct from prior wick, VWAP, cross-asset and breakout tests",
  "models_per_market": 144,
  "data_quality": [
    {
      "symbol": "BTCUSD",
      "rows": 987840,
      "monthly_files": 23,
      "missing_minutes": 0
    },
    {
      "symbol": "ETHUSD",
      "rows": 987840,
      "monthly_files": 23,
      "missing_minutes": 0
    }
  ],
  "period": "2025-01-01 through 2026-11-17 UTC",
  "selection": "2025 PF>1, net return>0, trades>=50 then highest positive calendar day fraction; otherwise best net 2025. 2026 unchanged.",
  "costs": {
    "taker_fee_plus_GST_per_side": 0.00059,
    "adverse_slippage_per_side": 0.0002,
    "conservative_funding_debit_per_8h_boundary": 0.0001
  },
  "risk": {
    "stop_equity_risk": 0.005,
    "leverage_cap": 2
  },
  "limitations": [
    "Candle signed volume is not true taker aggressor volume or order-book imbalance",
    "2026 was previously exposed in earlier research; not a pristine out-of-sample",
    "No tick/lot, queue position, margin liquidation, real funding rate, depth or spread snapshots",
    "Intraminute OHLC stops always precede targets; overnight not allowed",
    "No strategy can guarantee daily profit"
  ]
}
