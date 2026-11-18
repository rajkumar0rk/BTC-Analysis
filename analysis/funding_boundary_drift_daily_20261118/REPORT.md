# Independent funding-boundary drift daily net study

symbol  year  pre_min  post_min   mode  threshold    tp    sl  hold_min  calendar_days  trades  profitable_days  losing_days  no_trade_days  positive_calendar_day_pct  win_rate_traded_pct  net_return_pct  profit_factor  max_dayclose_dd_pct  max_consecutive_losing_days  median_calendar_day_usd  mean_calendar_day_usd  mean_losing_day_usd  worst_day_usd  fees_usd  funding_debit_usd  passes_train
BTCUSD  2025       15        15 follow     0.0025 0.005 0.005        90            365      59               33           26            306                      9.041               55.932         -3.7030         0.7387              -6.8344                            2                      0.0                -0.1015              -5.4495        -6.4357   67.0775                0.0         False
BTCUSD  2026       15        15 follow     0.0025 0.005 0.005        90            321      53               19           34            268                      5.919               35.849        -11.2123         0.3588             -11.9020                            3                      0.0                -0.3364              -4.9528        -6.1398   55.7179                0.0         False
ETHUSD  2025       15        15 follow     0.0025 0.003 0.005        30            365     121               75           46            244                     20.548               61.983        -11.0791         0.4978             -12.1386                            4                      0.0                -0.3035              -4.7962        -6.4171  133.6673                0.0         False
ETHUSD  2026       15        15 follow     0.0025 0.003 0.005        30            321      68               33           35            253                     10.280               48.529        -11.8199         0.2851             -12.1049                            3                      0.0                -0.3274              -4.2006        -5.6781   66.8236                0.0         False

## Assumptions and limitations

{
  "hypothesis": "post-8h-funding-boundary directional drift/fade conditional on completed pre and post settlement price impulses",
  "novelty": "Specific funding-boundary event study, distinct from broad clock-only entry and unrelated funding carry; no funding-rate prediction",
  "data_quality": [
    {
      "symbol": "BTCUSD",
      "bars": 987840,
      "months": 23,
      "missing_minutes": 0,
      "first_utc": "2025-01-01 00:00:00+00:00",
      "last_utc": "2026-11-17 23:59:00+00:00"
    },
    {
      "symbol": "ETHUSD",
      "bars": 987840,
      "months": 23,
      "missing_minutes": 0,
      "first_utc": "2025-01-01 00:00:00+00:00",
      "last_utc": "2026-11-17 23:59:00+00:00"
    }
  ],
  "models_per_symbol": 192,
  "selection": "2025 positive PF>1, net>0 and >=50 trades, then calendar positive-day rate; otherwise least negative 2025; unchanged 2026",
  "fee_each_side": 0.00059,
  "slippage_each_side": 0.0002,
  "funding_debit_each_crossing": 0.0001,
  "risk_fraction_per_trade": 0.005,
  "leverage_notional_cap": 2.0,
  "caveats": [
    "No verified historical funding-rate inputs; study tests boundary timing, NOT actual carry",
    "2026 previously research-exposed, not a pristine holdout",
    "Funding debit is conservative proxy, not actual settlement",
    "No order book, lot-size, liquidation/margin or intraminute tick-path simulation",
    "Stop wins tie against target, conservative",
    "2026 Nov partial through Nov 17 UTC",
    "No-trade days count against positive calendar-day frequency",
    "No strategy guarantees daily profits"
  ]
}
