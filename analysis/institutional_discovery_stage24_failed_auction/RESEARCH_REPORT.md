# Stage24 — two-hour failed auction, 22 completed IST months

Select parameters by 2025 only; replay fixed on Jan-Oct 2026. This is research-exposed history, not independent validation.

## Ranked candidates
|   mult |   rr |   hold |   positive_2025 |   positive_2026 |   min_2025_pct |   max_closed_trade_drawdown_pct |   total_trades |
|-------:|-----:|-------:|----------------:|----------------:|---------------:|--------------------------------:|---------------:|
|    1.5 |    2 |    720 |               7 |               4 |       -5.04044 |                         19.4902 |            292 |
|    2.5 |    2 |    720 |               6 |               3 |       -4.17612 |                         20.5305 |            272 |
|    2.5 |    3 |    720 |               6 |               3 |       -4.17612 |                         20.9105 |            272 |
|    1.5 |    2 |    360 |               6 |               4 |       -4.74709 |                         20.5987 |            301 |
|    1.5 |    3 |    720 |               5 |               2 |       -5.04044 |                         29.7022 |            287 |
|    2.5 |    2 |    360 |               2 |               2 |       -3.94602 |                         19.0195 |            290 |
|    2.5 |    3 |    360 |               2 |               2 |       -3.94602 |                         19.1612 |            290 |
|    1.5 |    3 |    360 |               1 |               3 |       -4.74709 |                         26.8141 |            299 |

## Selected model, net account returns after taker/GST/slippage
|   mult |   rr |   hold | month_ist   |   trades |   winning_trades |   losing_trades |   breakeven_trades |   net_account_return_pct |
|-------:|-----:|-------:|:------------|---------:|-----------------:|----------------:|-------------------:|-------------------------:|
|    1.5 |    2 |    720 | 2025-01     |       15 |                3 |              12 |                  0 |                -5.04044  |
|    1.5 |    2 |    720 | 2025-02     |       10 |                4 |               6 |                  0 |                 0.586938 |
|    1.5 |    2 |    720 | 2025-03     |       18 |                6 |              12 |                  0 |                -4.65701  |
|    1.5 |    2 |    720 | 2025-04     |       12 |                6 |               6 |                  0 |                 0.390863 |
|    1.5 |    2 |    720 | 2025-05     |       11 |                2 |               9 |                  0 |                -3.61649  |
|    1.5 |    2 |    720 | 2025-06     |       11 |                7 |               4 |                  0 |                 2.33943  |
|    1.5 |    2 |    720 | 2025-07     |       17 |               10 |               7 |                  0 |                -0.057702 |
|    1.5 |    2 |    720 | 2025-08     |       15 |               11 |               4 |                  0 |                 2.06331  |
|    1.5 |    2 |    720 | 2025-09     |       10 |                6 |               4 |                  0 |                 1.57004  |
|    1.5 |    2 |    720 | 2025-10     |       14 |                5 |               9 |                  0 |                -2.95524  |
|    1.5 |    2 |    720 | 2025-11     |       18 |               10 |               8 |                  0 |                 1.49714  |
|    1.5 |    2 |    720 | 2025-12     |        9 |                6 |               3 |                  0 |                 2.59333  |
|    1.5 |    2 |    720 | 2026-01     |       13 |                5 |               8 |                  0 |                -2.01042  |
|    1.5 |    2 |    720 | 2026-02     |       11 |                6 |               5 |                  0 |                 1.18739  |
|    1.5 |    2 |    720 | 2026-03     |       16 |                4 |              12 |                  0 |                -3.16671  |
|    1.5 |    2 |    720 | 2026-04     |        9 |                5 |               4 |                  0 |                 1.24488  |
|    1.5 |    2 |    720 | 2026-05     |       11 |                6 |               5 |                  0 |                 0.130217 |
|    1.5 |    2 |    720 | 2026-06     |       24 |                6 |              18 |                  0 |                -5.74732  |
|    1.5 |    2 |    720 | 2026-07     |       11 |                2 |               9 |                  0 |                -4.01253  |
|    1.5 |    2 |    720 | 2026-08     |       11 |                3 |               8 |                  0 |                -1.57335  |
|    1.5 |    2 |    720 | 2026-09     |       15 |                7 |               8 |                  0 |                 0.412724 |
|    1.5 |    2 |    720 | 2026-10     |       11 |                6 |               5 |                  0 |                -0.200383 |

## Audit and limitations
```json
{
  "positive_months": 11,
  "total_months": 22,
  "all_22_positive": false,
  "october_31_utc_complete": false,
  "oct31_utc_candles": 0,
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
    "2026-10": 43530
  },
  "chosen_model": {
    "mult": 1.5,
    "rr": 2.0,
    "hold": 720.0,
    "positive_2025": 7.0,
    "positive_2026": 4.0,
    "min_2025_pct": -5.04044013079088,
    "max_closed_trade_drawdown_pct": 19.49019,
    "total_trades": 292.0
  },
  "source_quality": {
    "source": "Delta Exchange India BTCUSD 1m compressed API candles",
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
    "observed_candles": 984960,
    "first_utc": "2025-01-01 00:00:00+00:00",
    "last_utc": "2026-11-16 23:59:00+00:00",
    "expected_dense_candles": 986400,
    "missing_minutes": 1440,
    "continuous_segments": 2,
    "gaps": [
      {
        "after_utc": "2026-10-30 23:59:00+00:00",
        "before_utc": "2026-11-01 00:00:00+00:00",
        "missing_minutes": 1440
      }
    ]
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
