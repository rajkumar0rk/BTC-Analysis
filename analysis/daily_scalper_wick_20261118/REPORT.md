# Independent short-window daily scalping research

Train-ranked on 2025 only; 2026 is research-exposed historical replay.

## Selected models

symbol  year pattern   session     tp     sl  hold_min                 cost  net_return_pct  trades  profitable_days  losing_days  no_trade_days  profitable_calendar_days_pct  win_rate_traded_pct  profit_factor  fees_usd  funding_debit_usd  max_dayclose_drawdown_pct  passes_2025_minimum
BTCUSD  2025   sweep utc_12_20 0.0025 0.0045        30 offer_counterfactual        -21.2838     299              136          163             66                        37.260               45.485         0.5031   177.212              0.681                    -22.031                False
BTCUSD  2026   sweep utc_12_20 0.0025 0.0045        30 offer_counterfactual        -26.5447     276              117          159             45                        36.449               42.391         0.3714   122.537              0.208                    -26.707                False
ETHUSD  2025 confirm utc_00_08 0.0025 0.0045        15 offer_counterfactual        -21.3103     295              141          154             70                        38.630               47.797         0.4716   170.796              0.380                    -21.587                False
ETHUSD  2026 confirm utc_00_08 0.0025 0.0045        15 offer_counterfactual        -32.0322     296               94          202             25                        29.283               31.757         0.2543   127.635              0.211                    -32.032                False

## Assumptions

{
  "data": [
    {
      "symbol": "BTCUSD",
      "minute_bars": 987840,
      "first_utc": "2025-01-01 00:00:00+00:00",
      "last_utc": "2026-11-17 23:59:00+00:00",
      "missing_minutes": 0,
      "source_files": 23,
      "signal_counts": {
        "wick": 11905,
        "sweep": 3833,
        "confirm": 5877,
        "impulse": 19678
      },
      "tested_models": 288
    },
    {
      "symbol": "ETHUSD",
      "minute_bars": 987840,
      "first_utc": "2025-01-01 00:00:00+00:00",
      "last_utc": "2026-11-17 23:59:00+00:00",
      "missing_minutes": 0,
      "source_files": 23,
      "signal_counts": {
        "wick": 11812,
        "sweep": 4379,
        "confirm": 5744,
        "impulse": 15422
      },
      "tested_models": 288
    }
  ],
  "models_per_symbol": 288,
  "date_start": "2025-01-01 00:00:00+00:00",
  "date_end_exclusive": "2026-11-18 00:00:00+00:00",
  "selection_rule": "Choose 2025 trade count >=50, PF>1 and net profit >0, then maximize profitable calendar days; replay unchanged 2026",
  "trading_costs": {
    "standard_taker_entry_exit": 0.00059,
    "scalper_counterfactual_entry": 0.00059,
    "scalper_counterfactual_exit": 0.0,
    "slippage_each_fill": 0.0002,
    "funding_8h_crossing_debit": 0.0001
  },
  "caveats": [
    "No strategy guaranteed positive daily net PnL",
    "Offer scenario assumes opt-in and eligible 30m close; NOT valid historical offer availability for all 2025",
    "2026 previously research exposed, cannot claim untouched holdout",
    "1m candle cannot resolve order book liquidity or intrabar sequences; stop-first ambiguity",
    "Funding proxy, leverage/margin/lots and slippage are approximations",
    "Profit day count includes no-trade days as zero, not profit",
    "2026 through November 17 UTC, not full year"
  ]
}
