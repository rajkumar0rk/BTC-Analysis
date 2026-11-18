# BTC ETH lead-lag daily-profit hypothesis

symbol  year leader  leader_move  follower_fraction  stop  target  hold_min  trades  days  profitable_days  losing_days  no_trade_days  profitable_calendar_day_pct  profit_factor  net_return_pct  net_usd  daily_mean_usd  daily_median_usd  mean_losing_day_usd  worst_day_usd  max_losing_streak  max_dayclose_drawdown_pct  fees_usd  funding_debit_usd  2025_criteria_pass
BTCUSD  2025 ETHUSD        0.008               0.15 0.005   0.007        30      88   365               34           54            277                        9.315         0.5786         -7.6594 -76.5939         -0.2098               0.0              -3.3661        -6.4301                  3                    -9.4509   99.5263             0.1938               False
BTCUSD  2026 ETHUSD        0.008               0.15 0.005   0.007        30      16   321                9            7            305                        2.804         1.4888          1.5045  13.8924          0.0433               0.0              -4.0599        -5.9332                  2                    -1.2711   17.4464             0.0000               False
ETHUSD  2025 BTCUSD        0.005               0.35 0.003   0.007        30      34   365               16           18            331                        4.384         1.1511          1.8987  18.9869          0.0520               0.0              -6.9807        -7.3592                  2                    -2.6938   66.1512             0.0000                True
ETHUSD  2026 BTCUSD        0.005               0.35 0.003   0.007        30      17   321                4           13            304                        1.246         0.3950         -5.6298 -57.3665         -0.1787               0.0              -7.2934        -7.4726                  2                    -6.0058   33.4089             0.0000                True

## Monthly

symbol   month  net_return_pct  profitable_days  losing_days  no_trade_days
BTCUSD 2025-01          0.1570                2            2             27
BTCUSD 2025-02         -0.7473                6            7             15
BTCUSD 2025-03         -0.9732                5            7             19
BTCUSD 2025-04         -2.1479                2            9             19
BTCUSD 2025-05         -2.1925                5            7             19
BTCUSD 2025-06         -1.6550                2            6             22
BTCUSD 2025-07         -0.0645                2            5             24
BTCUSD 2025-08         -0.3147                5            4             22
BTCUSD 2025-09         -1.1172                1            3             26
BTCUSD 2025-10          1.2491                3            3             25
BTCUSD 2025-11          0.5625                1            0             29
BTCUSD 2025-12         -0.6376                0            1             30
BTCUSD 2026-01         -0.6376                0            1             30
BTCUSD 2026-02          0.2925                3            2             23
BTCUSD 2026-03          0.4813                2            1             28
BTCUSD 2026-04          0.5615                1            0             29
BTCUSD 2026-05          0.0000                0            0             31
BTCUSD 2026-06         -0.7810                0            2             28
BTCUSD 2026-07          0.0000                0            0             31
BTCUSD 2026-08          0.4661                1            1             29
BTCUSD 2026-09          0.5615                1            0             29
BTCUSD 2026-10          0.0000                0            0             31
BTCUSD 2026-11          0.5615                1            0             16
ETHUSD 2025-01         -2.4998                2            6             23
ETHUSD 2025-02          1.8839                2            0             26
ETHUSD 2025-03         -1.1166                3            6             22
ETHUSD 2025-04          1.1406                2            1             27
ETHUSD 2025-05          0.0000                0            0             31
ETHUSD 2025-06          0.0000                0            0             30
ETHUSD 2025-07         -0.5317                1            2             28
ETHUSD 2025-08          0.2011                1            1             29
ETHUSD 2025-09          0.0000                0            0             30
ETHUSD 2025-10          1.0092                3            2             26
ETHUSD 2025-11          0.0000                0            0             30
ETHUSD 2025-12          1.8803                2            0             29
ETHUSD 2026-01          0.2011                1            1             29
ETHUSD 2026-02         -1.9803                1            4             23
ETHUSD 2026-03          0.0000                0            0             31
ETHUSD 2026-04          0.9358                1            0             29
ETHUSD 2026-05          0.0000                0            0             31
ETHUSD 2026-06         -1.4538                0            2             28
ETHUSD 2026-07         -0.7296                0            1             30
ETHUSD 2026-08         -0.5317                1            2             28
ETHUSD 2026-09         -0.7296                0            1             29
ETHUSD 2026-10         -0.7296                0            1             30
ETHUSD 2026-11         -0.7296                0            1             16

## Caveats
{
  "data": [
    {
      "symbol": "BTCUSD",
      "files": 23,
      "bars": 987840,
      "missing_minutes": 0,
      "first_utc": "2025-01-01 00:00:00+00:00",
      "last_utc": "2026-11-17 23:59:00+00:00"
    },
    {
      "symbol": "ETHUSD",
      "files": 23,
      "bars": 987840,
      "missing_minutes": 0,
      "first_utc": "2025-01-01 00:00:00+00:00",
      "last_utc": "2026-11-17 23:59:00+00:00"
    }
  ],
  "hypothesis": "Cross-asset BTC/ETH leader move and lagging follower continuation",
  "model_count": 144,
  "fee_per_side": 0.00059,
  "slippage_per_side": 0.0002,
  "funding_8h_debit": 0.0001,
  "selection": "2025 >=30 trades, positive net return, PF>1 then maximum calendar profit-day rate. No eligible model: best net return is diagnostic failure.",
  "limitations": [
    "No actual L1 quotes, depth or contract lot validation",
    "Funding is assumed debit not actual cashflow",
    "No exchange liquidation simulation; max 2x notional",
    "2026 research exposed, not a pristine holdout",
    "Daily zero trade counts as not profitable",
    "Minute OHLC uses pessimistic stop-first ordering; spread proxy only"
  ]
}