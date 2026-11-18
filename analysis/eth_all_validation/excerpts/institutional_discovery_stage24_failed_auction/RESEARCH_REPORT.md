# Stage24 — two-hour failed auction, 22 completed IST months

Select parameters by 2025 only; replay fixed on Jan-Oct 2026. This is research-exposed history, not independent validation.

## Ranked candidates
|   mult |   rr |   hold |   positive_2025 |   positive_2026 |   min_2025_pct |   max_closed_trade_drawdown_pct |   total_trades |
|-------:|-----:|-------:|----------------:|----------------:|---------------:|--------------------------------:|---------------:|
|    2.5 |    2 |    720 |               4 |               0 |       -2.87027 |                         11.6125 |            254 |
|    2.5 |    3 |    720 |               4 |               0 |       -2.87027 |                         11.5739 |            254 |
|    1.5 |    2 |    720 |               4 |               0 |       -2.88121 |                         11.591  |            254 |
|    1.5 |    3 |    720 |               4 |               0 |       -2.88121 |                         11.5524 |            254 |
|    2.5 |    2 |    360 |               3 |               0 |       -1.3904  |                         13.176  |            285 |
|    2.5 |    3 |    360 |               3 |               0 |       -1.3904  |                         13.176  |            285 |
|    1.5 |    2 |    360 |               3 |               0 |       -1.43396 |                         13.2987 |            285 |
|    1.5 |    3 |    360 |               3 |               0 |       -1.43396 |                         13.2987 |            285 |

## Selected model, net account returns after taker/GST/slippage
|   mult |   rr |   hold | month_ist   |   trades |   winning_trades |   losing_trades |   breakeven_trades |   net_account_return_pct |
|-------:|-----:|-------:|:------------|---------:|-----------------:|----------------:|-------------------:|-------------------------:|
|    2.5 |    2 |    720 | 2025-01     |       11 |                3 |               8 |                  0 |                -0.358813 |
|    2.5 |    2 |    720 | 2025-02     |       12 |                5 |               7 |                  0 |                -1.08151  |
|    2.5 |    2 |    720 | 2025-03     |        6 |                5 |               1 |                  0 |                 0.410793 |
|    2.5 |    2 |    720 | 2025-04     |       10 |                5 |               5 |                  0 |                 0.205324 |
|    2.5 |    2 |    720 | 2025-05     |       12 |                4 |               8 |                  0 |                -0.267865 |
|    2.5 |    2 |    720 | 2025-06     |       10 |                3 |               7 |                  0 |                -1.22579  |
|    2.5 |    2 |    720 | 2025-07     |       14 |                7 |               7 |                  0 |                -1.37917  |
|    2.5 |    2 |    720 | 2025-08     |       20 |                5 |              15 |                  0 |                -2.87027  |
|    2.5 |    2 |    720 | 2025-09     |       13 |                5 |               8 |                  0 |                -0.790126 |
|    2.5 |    2 |    720 | 2025-10     |       14 |                9 |               5 |                  0 |                 2.02995  |
|    2.5 |    2 |    720 | 2025-11     |       12 |                4 |               8 |                  0 |                 0.04171  |
|    2.5 |    2 |    720 | 2025-12     |        9 |                2 |               7 |                  0 |                -0.299637 |
|    2.5 |    2 |    720 | 2026-01     |       11 |                3 |               8 |                  0 |                -0.686359 |
|    2.5 |    2 |    720 | 2026-02     |       12 |                5 |               7 |                  0 |                -1.18822  |
|    2.5 |    2 |    720 | 2026-03     |       10 |                4 |               6 |                  0 |                -0.156404 |
|    2.5 |    2 |    720 | 2026-04     |       13 |                2 |              11 |                  0 |                -0.59164  |
|    2.5 |    2 |    720 | 2026-05     |        9 |                1 |               8 |                  0 |                -0.493863 |
|    2.5 |    2 |    720 | 2026-06     |       12 |                2 |              10 |                  0 |                -0.604812 |
|    2.5 |    2 |    720 | 2026-07     |       10 |                3 |               7 |                  0 |                -0.690175 |
|    2.5 |    2 |    720 | 2026-08     |        9 |                0 |               9 |                  0 |                -0.420225 |
|    2.5 |    2 |    720 | 2026-09     |       14 |                4 |              10 |                  0 |                -1.22466  |
|    2.5 |    2 |    720 | 2026-10     |       11 |                4 |               7 |                  0 |                -0.214069 |

## Audit and limitations
```json
{
  "positive_months": 4,
  "total_months": 22,
  "all_22_positive": false,
  "october_31_utc_complete": true,
  "oct31_utc_candles": 1440,
  "month_observation_counts": {
    "2025-01": 44310,
    "2025-02": 40320,
    "2025-03": 44640,
    "2025-04": 43200,
    "2025-05": 44640,
    "2025-06": 43200,
    "2025-07": 44640,
    "2025-08": 44640,
    "2025-09": 43200,
    "2025-10": 44640,
    "2025-11": 43200,
    "2025-12": 44640,
    "2026-01": 44640,
    "2026-02": 40320,
    "2026-03": 44640,
    "2026-04": 43200,
    "2026-05": 44640,
    "2026-06": 43200,
    "2026-07": 44640,
    "2026-08": 44640,
    "2026-09": 43200,
    "2026-10": 44640
  },
  "chosen_model": {
    "mult": 2.5,
    "rr": 2.0,
    "hold": 720.0,
    "positive_2025": 4.0,
    "positive_2026": 0.0,
    "min_2025_pct": -2.87026940083136,
    "max_closed_trade_drawdown_pct": 11.61252,
    "total_trades": 254.0
  },
  "source_quality": {
    "source": "Delta Exchange India ETHUSD 1m compressed API candles",
    "months": 23,
    "partitions": [
      "2025-01.csv.gz",
      "2025-02.csv.gz",
      "2025-03.csv.gz",
      "2025-04.csv.gz",
      "2025-05.csv.gz",
      "2025-06.csv.gz",
      "2025-07.csv.gz",
      "2025-08.csv.gz",
      "2025-09.csv.gz",
      "2025-10.csv.gz",
      "2025-11.csv.gz",
      "2025-12.csv.gz",
      "2026-01.csv.gz",
      "2026-02.csv.gz",
      "2026-03.csv.gz",
      "2026-04.csv.gz",
      "2026-05.csv.gz",
      "2026-06.csv.gz",
      "2026-07.csv.gz",
      "2026-08.csv.gz",
      "2026-09.csv.gz",
      "2026-10.csv.gz",
      "2026-11.csv.gz"
    ],
    "observed_candles": 987840,
    "first_utc": "2025-01-01 00:00:00+00:00",
    "last_utc": "2026-11-17 23:59:00+00:00",
    "expected_dense_candles": 987840,
    "missing_minutes": 0,
    "continuous_segments": 1,
    "gaps": []
  },
  "caveats": [
    "2026 is previously exposed, not pristine forward validation",
    "October 31 UTC incomplete means October must not be called fully verified",
    "Funding, order book spread, market impact, liquidation and discrete lots unmodeled",
    "One position per model; risk capped at 0.5% equity and 5x notional",
    "Stop wins same-minute ambiguous OHLC; gap stops use adverse open",
    "Drawdown at trade closes only; intratrade drawdown can be larger",
    "No-trade months are zero, not positive",
    "November 2026 excluded entirely"
  ]
}
```
