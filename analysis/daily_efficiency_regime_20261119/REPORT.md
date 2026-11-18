# Independent efficiency regime daily-profit test

symbol  year  lookback_5m  efficiency_threshold  mode    tp    sl  hold_minutes  days  trades  profitable_days  losing_days  no_trade_days  profitable_calendar_day_pct  win_rate_traded_pct  net_return_pct  net_profit_usd  mean_calendar_day_net_usd  median_calendar_day_net_usd  worst_day_usd  max_losing_day_streak  profit_factor  max_dayclose_drawdown_pct  fees_usd  funding_proxy_usd  passes_2025_selection
BTCUSD  2025           24                  0.65 trend 0.006 0.005           180   365      90               38           52            275                       10.411               42.222         -9.8184         -98.184                    -0.2690                          0.0        -6.6535                      3         0.6226                   -14.1386   103.354              1.465                  False
BTCUSD  2026           24                  0.65 trend 0.006 0.005           180   321      81               32           49            240                        9.969               39.506        -10.1566         -91.594                    -0.2853                          0.0        -5.7573                      2         0.5531                   -10.2292    81.054              1.262                  False
ETHUSD  2025           24                  0.65 trend 0.003 0.005           180   365      94               57           37            271                       15.616               60.638        -13.2714        -132.714                    -0.3636                          0.0        -6.4419                      3         0.3965                   -14.2025   104.795              0.290                  False
ETHUSD  2026           24                  0.65 trend 0.003 0.005           180   321      78               41           37            243                       12.773               52.564        -14.4660        -125.462                    -0.3908                          0.0        -5.5458                      2         0.2953                   -15.0188    73.457              0.631                  False

{
  "hypothesis": "Kaufman efficiency ratio intraday trend vs fade",
  "input": [
    {
      "symbol": "BTCUSD",
      "rows": 987840,
      "months": 23,
      "first": 1735689600,
      "last": 1794959940,
      "missing_minutes": 0,
      "signals_per_config": {
        "(6, 0.35, 'trend')": 686,
        "(6, 0.35, 'fade')": 686,
        "(6, 0.5, 'trend')": 686,
        "(6, 0.5, 'fade')": 686,
        "(6, 0.65, 'trend')": 686,
        "(6, 0.65, 'fade')": 686,
        "(12, 0.35, 'trend')": 686,
        "(12, 0.35, 'fade')": 686,
        "(12, 0.5, 'trend')": 686,
        "(12, 0.5, 'fade')": 686,
        "(12, 0.65, 'trend')": 660,
        "(12, 0.65, 'fade')": 660,
        "(24, 0.35, 'trend')": 685,
        "(24, 0.35, 'fade')": 685,
        "(24, 0.5, 'trend')": 520,
        "(24, 0.5, 'fade')": 520,
        "(24, 0.65, 'trend')": 171,
        "(24, 0.65, 'fade')": 171
      }
    },
    {
      "symbol": "ETHUSD",
      "rows": 987840,
      "months": 23,
      "first": 1735689600,
      "last": 1794959940,
      "missing_minutes": 0,
      "signals_per_config": {
        "(6, 0.35, 'trend')": 686,
        "(6, 0.35, 'fade')": 686,
        "(6, 0.5, 'trend')": 686,
        "(6, 0.5, 'fade')": 686,
        "(6, 0.65, 'trend')": 686,
        "(6, 0.65, 'fade')": 686,
        "(12, 0.35, 'trend')": 686,
        "(12, 0.35, 'fade')": 686,
        "(12, 0.5, 'trend')": 686,
        "(12, 0.5, 'fade')": 686,
        "(12, 0.65, 'trend')": 657,
        "(12, 0.65, 'fade')": 657,
        "(24, 0.35, 'trend')": 682,
        "(24, 0.35, 'fade')": 682,
        "(24, 0.5, 'trend')": 533,
        "(24, 0.5, 'fade')": 533,
        "(24, 0.65, 'trend')": 172,
        "(24, 0.65, 'fade')": 172
      }
    }
  ],
  "models_per_asset": 144,
  "train_selection": "positive 2025 net, PF>1, >=50 trades then highest positive calendar day fraction; otherwise highest 2025 net",
  "evaluation_check": "fixed params, research-exposed not untouched holdout",
  "costs": {
    "taker_fee_plus_GST_per_side": 0.00059,
    "adverse_slippage_per_side": 0.0002,
    "funding_debit_per_8h_boundary": 0.0001
  },
  "risk": {
    "stop_risk_per_trade": 0.005,
    "max_notional_leverage": 2.0,
    "one_trade_per_UTC_day": true
  },
  "limitations": [
    "No guaranteed daily net profit",
    "1m intrabar ambiguous stop-first",
    "No orderbook, real funding, precise lot/margin, or liquidation engine",
    "2026 through Nov 17 UTC only"
  ]
}