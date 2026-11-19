# Daily false-breakout research

symbol  year  reference_minutes  sweep_fraction  target_fraction  stop_fraction  hold_minutes  trades  profitable_days  losing_days  no_trade_days  calendar_days  positive_calendar_day_pct  profit_factor  net_return_pct  max_dayclose_drawdown_pct  max_consecutive_losing_days  worst_day_usd  avg_day_usd  median_day_usd  fees_usd  funding_debit_usd  train_pass
BTCUSD  2025                 60          0.0005            0.005          0.006           180     328              141          187             37            365                     38.630         0.4512        -34.6088                   -34.8052                            7        -6.1460      -0.9482         -0.1319  252.9242             1.3315       False
BTCUSD  2026                 60          0.0005            0.005          0.006           180     280              121          159             41            321                     37.695         0.5013        -25.9855                   -26.7324                            7        -4.0054      -0.5294          0.0000  154.1526             1.0127       False
ETHUSD  2025                 60          0.0005            0.005          0.006           180     341              178          163             24            365                     48.767         0.6142        -27.8689                   -28.9252                            9        -6.2310      -0.7635          0.0000  283.7394             0.7529       False
ETHUSD  2026                 60          0.0005            0.005          0.006           180     303              132          171             18            321                     41.121         0.4711        -34.0632                   -34.0632                            9        -4.4212      -0.7654         -0.4204  173.9347             0.6420       False

{
  "study": "UTC session opening-range FALSE breakout fade",
  "novelty": "Unlike opening-range continuation, this waits for a completed 5m sweep and CLOSE back inside the range, then fades it.",
  "parameters_per_symbol": 48,
  "data_quality": [
    {
      "symbol": "BTCUSD",
      "minute_rows": 987840,
      "source_files": 23,
      "missing_minutes": 0
    },
    {
      "symbol": "ETHUSD",
      "minute_rows": 987840,
      "source_files": 23,
      "missing_minutes": 0
    }
  ],
  "costs": {
    "taker_with_GST_per_side": 0.00059,
    "slippage_per_side": 0.0002,
    "assumed_funding_debit_per_8h": 0.0001
  },
  "selection": "2025 >=50 trades, PF>1, net>0; highest calendar positive days; 2026 unchanged",
  "caveats": [
    "2026 already research-exposed, not independent forward validation",
    "No exact funding, orderbook, tick-size, lot-size, exchange margin or liquidation replay",
    "Stop-first ambiguity; one trade max per UTC day; 2026 November partial",
    "Cannot promise daily profit"
  ]
}
