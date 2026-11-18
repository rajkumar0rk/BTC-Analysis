# Stage24 — two-hour failed auction, 22 completed IST months

Select parameters by 2025 only; replay fixed on Jan-Oct 2026. This is research-exposed history, not independent validation.

## Ranked candidates
|   mult |   rr |   hold |   positive_2025 |   positive_2026 |   min_2025_pct |   max_closed_trade_drawdown_pct |   total_trades |
|-------:|-----:|-------:|----------------:|----------------:|---------------:|--------------------------------:|---------------:|
|    1.5 |    2 |    720 |               5 |               2 |       -5.45607 |                         19.8963 |            285 |
|    1.5 |    3 |    360 |               4 |               2 |       -2.63312 |                         16.4435 |            294 |
|    1.5 |    2 |    360 |               4 |               2 |       -2.69961 |                         19.5967 |            294 |
|    2.5 |    2 |    360 |               4 |               2 |       -2.80417 |                         14.454  |            289 |
|    2.5 |    3 |    360 |               4 |               2 |       -2.8897  |                         12.8386 |            287 |
|    1.5 |    3 |    720 |               4 |               2 |       -4.62496 |                         20.1921 |            282 |
|    2.5 |    2 |    720 |               4 |               1 |       -5.38989 |                         18.6965 |            277 |
|    2.5 |    3 |    720 |               3 |               3 |       -4.76758 |                         19.392  |            273 |

## Selected model, net account returns after taker/GST/slippage
|   mult |   rr |   hold | month_ist   |   trades |   winning_trades |   losing_trades |   breakeven_trades |   net_account_return_pct |
|-------:|-----:|-------:|:------------|---------:|-----------------:|----------------:|-------------------:|-------------------------:|
|    1.5 |    2 |    720 | 2025-01     |       12 |                6 |               6 |                  0 |                -0.551085 |
|    1.5 |    2 |    720 | 2025-02     |       14 |                4 |              10 |                  0 |                -2.8249   |
|    1.5 |    2 |    720 | 2025-03     |        6 |                6 |               0 |                  0 |                 3.51194  |
|    1.5 |    2 |    720 | 2025-04     |       11 |                4 |               7 |                  0 |                 0.438288 |
|    1.5 |    2 |    720 | 2025-05     |       13 |                4 |               9 |                  0 |                -1.19054  |
|    1.5 |    2 |    720 | 2025-06     |       12 |                5 |               7 |                  0 |                -0.245948 |
|    1.5 |    2 |    720 | 2025-07     |       17 |                9 |               8 |                  0 |                 0.76358  |
|    1.5 |    2 |    720 | 2025-08     |       22 |                5 |              17 |                  0 |                -5.45607  |
|    1.5 |    2 |    720 | 2025-09     |       13 |                5 |               8 |                  0 |                -1.49964  |
|    1.5 |    2 |    720 | 2025-10     |       17 |                7 |              10 |                  0 |                -0.528449 |
|    1.5 |    2 |    720 | 2025-11     |       13 |                6 |               7 |                  0 |                 3.1035   |
|    1.5 |    2 |    720 | 2025-12     |       11 |                6 |               5 |                  0 |                 2.82692  |
|    1.5 |    2 |    720 | 2026-01     |       11 |                6 |               5 |                  0 |                 0.809416 |
|    1.5 |    2 |    720 | 2026-02     |       12 |                5 |               7 |                  0 |                -1.89488  |
|    1.5 |    2 |    720 | 2026-03     |       12 |                4 |               8 |                  0 |                -1.63579  |
|    1.5 |    2 |    720 | 2026-04     |       14 |                2 |              12 |                  0 |                -4.29482  |
|    1.5 |    2 |    720 | 2026-05     |       11 |                5 |               6 |                  0 |                -1.03456  |
|    1.5 |    2 |    720 | 2026-06     |       13 |                3 |              10 |                  0 |                -3.91678  |
|    1.5 |    2 |    720 | 2026-07     |       14 |                4 |              10 |                  0 |                -3.29121  |
|    1.5 |    2 |    720 | 2026-08     |       10 |                6 |               4 |                  0 |                 0.797908 |
|    1.5 |    2 |    720 | 2026-09     |       15 |                4 |              11 |                  0 |                -2.56448  |
|    1.5 |    2 |    720 | 2026-10     |       12 |                5 |               7 |                  0 |                -1.20694  |

## Audit and limitations
```json
{
  "positive_months": 7,
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
    "mult": 1.5,
    "rr": 2.0,
    "hold": 720.0,
    "positive_2025": 5.0,
    "positive_2026": 2.0,
    "min_2025_pct": -5.456072179495464,
    "max_closed_trade_drawdown_pct": 19.89626,
    "total_trades": 285.0
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
