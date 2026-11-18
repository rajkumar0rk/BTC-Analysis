# New independent intraday calendar drift research

## 2025 selected and 2026 unchanged

symbol  year  start_minute       mode    tp    sl  hold  days  trades  profitable_days  losing_days  no_trade_days  profitable_calendar_day_pct  profit_factor  net_return_pct  median_daily_net_usd  mean_daily_net_usd  worst_day_usd  max_losing_streak  max_dayclose_drawdown_pct  fees_usd  funding_proxy_debit_usd  avg_hold_min  train_positive
BTCUSD  2025           840 contrarian 0.006 0.004    30   365     365              127          238              0                       34.795         0.4570        -42.3643               -1.3201             -1.1607        -6.7291                 10                   -42.3643  423.2976                      0.0         23.35           False
BTCUSD  2026           840 contrarian 0.006 0.004    30   321     321               91          230              0                       28.349         0.2736        -53.3833               -1.0012             -0.9585        -3.8633                 23                   -53.7602  192.2335                      0.0         23.19           False
ETHUSD  2025           120       long 0.006 0.004    90   365     365              167          198              0                       45.753         0.6763        -30.0267               -1.1379             -0.8226        -6.7451                  7                   -33.0161  429.6071                      0.0         42.48           False
ETHUSD  2026           120       long 0.006 0.004    90   321     321               97          224              0                       30.218         0.3734        -51.4657               -1.5892             -1.1219        -4.7037                 15                   -51.7049  231.9659                      0.0         51.64           False

## Monthly

symbol month_utc  net_return_pct  positive_days  negative_days  trades
BTCUSD   2025-01         -4.1179             11             20      31
BTCUSD   2025-02         -6.3090              9             19      28
BTCUSD   2025-03         -5.8427             13             18      31
BTCUSD   2025-04         -0.3890             13             17      30
BTCUSD   2025-05         -1.4012             13             18      31
BTCUSD   2025-06         -3.3658             12             18      30
BTCUSD   2025-07         -7.4108              8             23      31
BTCUSD   2025-08         -1.2586             14             17      31
BTCUSD   2025-09         -4.3519              8             22      30
BTCUSD   2025-10         -5.2272              9             22      31
BTCUSD   2025-11         -8.9558              7             23      30
BTCUSD   2025-12         -4.8474             10             21      31
BTCUSD   2026-01         -6.4335              8             23      31
BTCUSD   2026-02         -2.9251             12             16      28
BTCUSD   2026-03         -9.2809              8             23      31
BTCUSD   2026-04        -11.1182              4             26      30
BTCUSD   2026-05         -5.0438             11             20      31
BTCUSD   2026-06         -5.8517             10             20      30
BTCUSD   2026-07         -6.7460              9             22      31
BTCUSD   2026-08         -7.2006              7             24      31
BTCUSD   2026-09         -7.6547             10             20      30
BTCUSD   2026-10         -8.3400              7             24      31
BTCUSD   2026-11         -2.8016              5             12      17
ETHUSD   2025-01         -4.2613             13             18      31
ETHUSD   2025-02         -6.0334             10             18      28
ETHUSD   2025-03         -3.8551             14             17      31
ETHUSD   2025-04         -6.2126             11             19      30
ETHUSD   2025-05         -1.8495             15             16      31
ETHUSD   2025-06         -6.2315              9             21      30
ETHUSD   2025-07          1.4010             19             12      31
ETHUSD   2025-08          2.3839             18             13      31
ETHUSD   2025-09         -3.7044             13             17      30
ETHUSD   2025-10         -5.9267             11             20      31
ETHUSD   2025-11         -3.0709             15             15      30
ETHUSD   2025-12          2.8134             19             12      31
ETHUSD   2026-01         -7.4570             11             20      31
ETHUSD   2026-02         -4.8672             12             16      28
ETHUSD   2026-03         -5.9963             12             19      31
ETHUSD   2026-04         -9.9985              5             25      30
ETHUSD   2026-05         -4.8091             10             21      31
ETHUSD   2026-06        -11.3219              5             25      30
ETHUSD   2026-07         -6.5527              8             23      31
ETHUSD   2026-08         -6.9622              7             24      31
ETHUSD   2026-09         -4.0378             11             19      30
ETHUSD   2026-10         -5.7958             10             21      31
ETHUSD   2026-11         -1.7862              6             11      17

## Assumptions

{
  "hypothesis": "Calendar-fixed intraday drift around UTC funding boundary windows, conditional or unconditional direction",
  "distinct_from": [
    "VWAP exhaustion",
    "wick reversals",
    "cross-asset 1m lead lag",
    "market neutral carry",
    "4H cross asset confirmation"
  ],
  "source_quality": [
    {
      "symbol": "BTCUSD",
      "rows": 987840,
      "source_files": 23,
      "missing_minutes": 0,
      "first_utc": "2025-01-01 00:00:00+00:00",
      "last_utc": "2026-11-17 23:59:00+00:00"
    },
    {
      "symbol": "ETHUSD",
      "rows": 987840,
      "source_files": 23,
      "missing_minutes": 0,
      "first_utc": "2025-01-01 00:00:00+00:00",
      "last_utc": "2026-11-17 23:59:00+00:00"
    }
  ],
  "models_per_symbol": 448,
  "cost_model": {
    "fee_with_GST_each_side": 0.00059,
    "adverse_slippage_each_side": 0.0002,
    "funding_boundary_debit": 0.0001
  },
  "execution": "one position per UTC day, fixed minute OPEN, momentum from 15 previously completed minutes, stop-first intraminute, flat before day end",
  "equity": "1000 USD starting, risk 0.5% nominal stop, 2x max notional",
  "selection": "Only 2025: profitable PF>1; choose highest calendar profitable-day fraction, otherwise least negative net return. 2026 unchanged",
  "caveats": [
    "2026 historically exposed, not pristine out-of-sample",
    "No guaranteed daily return",
    "No order book, lot sizes, margin liquidation, actual funding settlements",
    "Simplified 2bp per-side adverse slippage",
    "Every calendar day has a trade even if edge absent"
  ]
}
