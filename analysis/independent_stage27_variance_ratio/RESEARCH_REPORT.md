# Stage27 — 15m variance-ratio serial dependence

This is exploratory, not an executable live edge. Original data checksum verified.
October 2026 UTC 1m is fully repaired on the isolated branch.
January 2025 IST lacks the first 5.5 hours; cannot assert fully observed 22 IST months.
Fees and GST included, 5 points adverse slippage each side; no funding, spread, market impact or lot granularity.
Sizing uses 1% equity stop-distance risk and 3x notional cap, not validated Delta margin.
2025-only model selection, 2026 already seen in prior research (not blind).

## All configurations

| key                   |   train_positive |   recheck_positive |   train_ge10 |   recheck_ge10 |   train_total_pct |   worst_month_pct |   total_trades | all_22_positive   | all_22_ge10   |
|:----------------------|-----------------:|-------------------:|-------------:|---------------:|------------------:|------------------:|---------------:|:------------------|:--------------|
| revert_vr0.6_stop2.5  |                3 |                  1 |            0 |              0 |          -65.1518 |          -16.2135 |            408 | False             | False         |
| persist_vr1.4_stop2.5 |                1 |                  4 |            0 |              0 |          -46.3133 |          -14.971  |            276 | False             | False         |
| persist_vr1.2_stop2.5 |                1 |                  3 |            1 |              1 |          -94.0339 |          -21.544  |            786 | False             | False         |
| revert_vr0.8_stop2.5  |                0 |                  1 |            0 |              0 |         -290.12   |          -44.2692 |           2285 | False             | False         |

## Chosen 2025-only configuration
revert_vr0.6_stop2.5

## Monthly net account returns

| month_ist   |   return_pct |   start_equity |   end_equity |   trades |   wins |   losses |    net_usd |
|:------------|-------------:|---------------:|-------------:|---------:|-------:|---------:|-----------:|
| 2025-01     |    -6.18611  |       1000     |      938.139 |       14 |      4 |       10 |  -61.8611  |
| 2025-02     |     2.61124  |        938.139 |      962.636 |       10 |      6 |        4 |   24.497   |
| 2025-03     |    -3.24102  |        962.636 |      931.437 |       10 |      3 |        7 |  -31.1992  |
| 2025-04     |    -7.68416  |        931.437 |      859.864 |       17 |      3 |       14 |  -71.5731  |
| 2025-05     |    -6.59584  |        859.864 |      803.148 |       13 |      4 |        9 |  -56.7152  |
| 2025-06     |   -13.207    |        803.148 |      697.077 |       33 |     11 |       22 | -106.072   |
| 2025-07     |     2.04594  |        697.077 |      711.338 |       16 |      8 |        8 |   14.2617  |
| 2025-08     |    -0.978985 |        711.338 |      704.375 |       11 |      6 |        5 |   -6.96389 |
| 2025-09     |    -9.13512  |        704.375 |      640.029 |       27 |      8 |       19 |  -64.3455  |
| 2025-10     |    -8.03534  |        640.029 |      588.601 |       18 |      6 |       12 |  -51.4285  |
| 2025-11     |     1.46805  |        588.601 |      597.241 |        3 |      2 |        1 |    8.64094 |
| 2025-12     |   -16.2135   |        597.241 |      500.408 |       55 |     19 |       36 |  -96.8336  |
| 2026-01     |   -10.153    |        500.408 |      449.601 |       34 |     13 |       21 |  -50.8066  |
| 2026-02     |    -3.22063  |        449.601 |      435.121 |       12 |      4 |        8 |  -14.48    |
| 2026-03     |     3.21443  |        435.121 |      449.108 |       13 |      8 |        5 |   13.9867  |
| 2026-04     |   -14.6159   |        449.108 |      383.467 |       26 |      5 |       21 |  -65.6412  |
| 2026-05     |    -6.10972  |        383.467 |      360.038 |       19 |      8 |       11 |  -23.4288  |
| 2026-06     |    -1.03815  |        360.038 |      356.3   |       10 |      3 |        7 |   -3.73772 |
| 2026-07     |    -4.36923  |        356.3   |      340.733 |       14 |      5 |        9 |  -15.5676  |
| 2026-08     |    -7.84333  |        340.733 |      314.008 |       19 |      8 |       11 |  -26.7248  |
| 2026-09     |    -2.52151  |        314.008 |      306.09  |       16 |      6 |       10 |   -7.91773 |
| 2026-10     |    -1.82013  |        306.09  |      300.519 |       18 |      9 |        9 |   -5.57124 |

## Audit
{
  "source": "Delta Exchange India original BTCUSD 1m",
  "input_months": 22,
  "source_minutes": 963360,
  "october_2026_complete": true,
  "selected_using": "2025 only, ranking positive months then sum of monthly net returns",
  "chosen": "revert_vr0.6_stop2.5",
  "all_22_positive": false,
  "all_22_ge10": false,
  "total_trades": 408,
  "wins": 149,
  "losses": 259,
  "max_trade_close_drawdown_pct": -71.02981111550268,
  "fee_per_side_with_gst": 0.00059,
  "slippage_points_per_side": 5.0,
  "missing": [
    "funding",
    "actual bid/ask spread",
    "impact",
    "lot size/margin/liquidation"
  ],
  "first_IST_month_missing_hours": 5.5,
  "warning": "2026 history was seen in previous studies; not pristine forward validation"
}

No guarantee of future profits. Never place orders from this research.
