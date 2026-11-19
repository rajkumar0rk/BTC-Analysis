# Pre-registered realized-skew tail-risk continuation

Hypothesis: trailing 24h 1m return third moment reveals persistent asymmetric tail-risk pressure, predicting same-sign 2h drift. Test independently for BTCUSD and ETHUSD; no optimization.
Signal at 00:00 UTC based solely on 1439 within-previous-day completed 1m returns; long if skew > +0.5, short if skew < -0.5; otherwise no trade. Enter 00:00 minute open, stop 0.6%, target 0.9%, 120-minute time exit, first touched stop wins ambiguity. One position/day, fixed $1,000 notional on $1,000 equity, no averaging.
Costs: taker each side 0.05% +18% GST, plus 0.02% slippage each side, total 0.158% of notional roundtrip; stress adds 0.04% roundtrip. Funding assumed zero for <=2h (unverified settlement timing); spread is represented only by slippage, so actual execution may be worse. This is NOT an executable quote/fee/funding replay; no orderbook queue, liquidation path or exchange minimums verified. No leverage, no borrowing. 2026 is research-exposed, not pristine holdout.
Archive completeness is strict for entry signal and hold; missing minutes become DATA_GAP, never winning or losing days.

## Data integrity
[
  {
    "symbol": "BTCUSD",
    "archive_first": "2025-01-01 00:00:00+00:00",
    "archive_last": "2026-11-17 23:59:00+00:00",
    "bars": 987840,
    "expected_minutes": 987840,
    "missing_minutes": 0
  },
  {
    "symbol": "ETHUSD",
    "archive_first": "2025-01-01 00:00:00+00:00",
    "archive_last": "2026-11-17 23:59:00+00:00",
    "bars": 987840,
    "expected_minutes": 987840,
    "missing_minutes": 0
  }
]

## Calendar-year results
| symbol   |   year |   days |   profit_days |   loss_days |   no_trade_days |   data_gap_days |   trades |   profit_calendar_pct |   median_day_usd |   mean_day_usd |   worst_day_usd |   net_usd |   return_pct |     pf |   max_drawdown_pct |   max_loss_day_streak |   fees_gst_usd |   slippage_usd |   stress_net_usd |
|:---------|-------:|-------:|--------------:|------------:|----------------:|----------------:|---------:|----------------------:|-----------------:|---------------:|----------------:|----------:|-------------:|-------:|-------------------:|----------------------:|---------------:|---------------:|-----------------:|
| BTCUSD   |   2025 |    364 |            34 |          71 |             259 |               0 |      105 |                  9.34 |                0 |        -0.4141 |           -7.58 |  -150.748 |      -15.075 | 0.5371 |             16.521 |                     4 |         123.9  |           42   |         -192.748 |
| BTCUSD   |   2026 |    321 |            46 |          82 |             193 |               0 |      128 |                 14.33 |                0 |        -0.5918 |           -7.58 |  -189.961 |      -18.996 | 0.487  |             20.752 |                     4 |         151.04 |           51.2 |         -241.161 |
| ETHUSD   |   2025 |    364 |            47 |          98 |             219 |               0 |      145 |                 12.91 |                0 |        -0.9366 |           -7.58 |  -340.91  |      -34.091 | 0.4576 |             34.642 |                     4 |         171.1  |           58   |         -398.91  |
| ETHUSD   |   2026 |    321 |            62 |          99 |             160 |               0 |      161 |                 19.31 |                0 |        -0.7919 |           -7.58 |  -254.199 |      -25.42  | 0.5326 |             26.904 |                     4 |         189.98 |           64.4 |         -318.599 |

## Every calendar month
| symbol   | month   |    net_usd |   profit_days |   loss_days |   trades |   net_return_pct |
|:---------|:--------|-----------:|--------------:|------------:|---------:|-----------------:|
| BTCUSD   | 2025-01 |   7.52503  |             5 |           4 |        9 |        0.752503  |
| BTCUSD   | 2025-02 | -13.7822   |             0 |           5 |        5 |       -1.37822   |
| BTCUSD   | 2025-03 |   5.97251  |             3 |           3 |        6 |        0.597251  |
| BTCUSD   | 2025-04 |   1.47855  |             5 |           6 |       11 |        0.147855  |
| BTCUSD   | 2025-05 |  -5.6004   |             2 |           2 |        4 |       -0.56004   |
| BTCUSD   | 2025-06 | -21.7022   |             0 |           7 |        7 |       -2.17022   |
| BTCUSD   | 2025-07 | -26.9068   |             0 |           8 |        8 |       -2.69068   |
| BTCUSD   | 2025-08 | -25.5307   |             5 |           7 |       12 |       -2.55307   |
| BTCUSD   | 2025-09 | -20.2042   |             3 |           6 |        9 |       -2.02042   |
| BTCUSD   | 2025-10 |   8.25458  |             7 |           4 |       11 |        0.825458  |
| BTCUSD   | 2025-11 | -24.9559   |             1 |           5 |        6 |       -2.49559   |
| BTCUSD   | 2025-12 | -35.2959   |             3 |          14 |       17 |       -3.52959   |
| BTCUSD   | 2026-01 |  12.3482   |             7 |           5 |       12 |        1.23482   |
| BTCUSD   | 2026-02 |  -6.51984  |             6 |           6 |       12 |       -0.651984  |
| BTCUSD   | 2026-03 |  -8.11332  |             6 |           8 |       14 |       -0.811332  |
| BTCUSD   | 2026-04 | -33.8991   |             4 |           8 |       12 |       -3.38991   |
| BTCUSD   | 2026-05 | -13.8419   |             3 |           6 |        9 |       -1.38419   |
| BTCUSD   | 2026-06 | -32.4276   |             3 |           9 |       12 |       -3.24276   |
| BTCUSD   | 2026-07 | -37.954    |             1 |           9 |       10 |       -3.7954    |
| BTCUSD   | 2026-08 | -13.3887   |             6 |           9 |       15 |       -1.33887   |
| BTCUSD   | 2026-09 | -14.0969   |             3 |           7 |       10 |       -1.40969   |
| BTCUSD   | 2026-10 | -13.2438   |             4 |          10 |       14 |       -1.32438   |
| BTCUSD   | 2026-11 | -28.8242   |             3 |           5 |        8 |       -2.88242   |
| ETHUSD   | 2025-01 | -25.6376   |             4 |           7 |       11 |       -2.56376   |
| ETHUSD   | 2025-02 |  -6.44751  |             4 |           6 |       10 |       -0.644751  |
| ETHUSD   | 2025-03 | -54.4095   |             2 |          10 |       12 |       -5.44095   |
| ETHUSD   | 2025-04 | -37.1698   |             4 |           8 |       12 |       -3.71698   |
| ETHUSD   | 2025-05 | -38.06     |             1 |           6 |        7 |       -3.806     |
| ETHUSD   | 2025-06 | -23.6016   |             6 |           9 |       15 |       -2.36016   |
| ETHUSD   | 2025-07 | -12.9035   |             4 |           5 |        9 |       -1.29035   |
| ETHUSD   | 2025-08 |  -0.504829 |             7 |           7 |       14 |       -0.0504829 |
| ETHUSD   | 2025-09 | -35.8004   |             4 |          11 |       15 |       -3.58004   |
| ETHUSD   | 2025-10 | -21.2395   |             5 |           9 |       14 |       -2.12395   |
| ETHUSD   | 2025-11 | -47.5134   |             2 |           8 |       10 |       -4.75134   |
| ETHUSD   | 2025-12 | -37.6225   |             4 |          12 |       16 |       -3.76225   |
| ETHUSD   | 2026-01 | -39.1759   |             5 |          11 |       16 |       -3.91759   |
| ETHUSD   | 2026-02 |   7.87016  |             9 |           6 |       15 |        0.787016  |
| ETHUSD   | 2026-03 |  23.1792   |             9 |           7 |       16 |        2.31792   |
| ETHUSD   | 2026-04 | -52.6428   |             6 |          13 |       19 |       -5.26428   |
| ETHUSD   | 2026-05 |  11.6661   |             8 |           6 |       14 |        1.16661   |
| ETHUSD   | 2026-06 | -56.713    |             3 |          12 |       15 |       -5.6713    |
| ETHUSD   | 2026-07 | -50.8577   |             5 |          11 |       16 |       -5.08577   |
| ETHUSD   | 2026-08 | -28.4296   |             4 |          11 |       15 |       -2.84296   |
| ETHUSD   | 2026-09 | -30.5792   |             1 |           8 |        9 |       -3.05792   |
| ETHUSD   | 2026-10 | -17.4291   |             8 |           8 |       16 |       -1.74291   |
| ETHUSD   | 2026-11 | -21.0872   |             4 |           6 |       10 |       -2.10872   |

If the signal fails across both years after costs, REJECT rather than tune. No daily-profit strategy is claimed.
