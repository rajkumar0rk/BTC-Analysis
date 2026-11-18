# Stage28 — 15m relative price-impact shock fade

This is exploratory, not an executable live edge. Original data checksum verified.
Price impact is only an OHLCV-based displacement/volume proxy, not measured market impact.
October 2026 UTC 1m is fully repaired on the isolated branch.
January 2025 IST lacks the first 5.5 hours; cannot assert fully observed 22 IST months.
Fees and GST included, 5 points adverse slippage each side; no funding, spread, market impact or lot granularity.
Sizing uses 1% equity stop-distance risk and 3x notional cap, not validated Delta margin.
2025-only model selection, 2026 already seen in prior research (not blind).

## All configurations

| key             |   train_positive |   recheck_positive |   train_ge10 |   recheck_ge10 |   train_total_pct |   worst_month_pct |   total_trades | all_22_positive   | all_22_ge10   |
|:----------------|-----------------:|-------------------:|-------------:|---------------:|------------------:|------------------:|---------------:|:------------------|:--------------|
| impact5_stop2.5 |                2 |                  1 |            0 |              0 |          -62.8117 |          -16.4489 |            728 | False             | False         |
| impact5_stop1.5 |                1 |                  1 |            0 |              0 |         -129.136  |          -23.4189 |            827 | False             | False         |
| impact3_stop2.5 |                0 |                  0 |            0 |              0 |         -147.069  |          -25.0703 |           1318 | False             | False         |
| impact3_stop1.5 |                0 |                  1 |            0 |              0 |         -215.605  |          -33.8601 |           1519 | False             | False         |

## Chosen 2025-only configuration
impact5_stop2.5

## Monthly net account returns

| month_ist   |   return_pct |   start_equity |   end_equity |   trades |   wins |   losses |     net_usd |
|:------------|-------------:|---------------:|-------------:|---------:|-------:|---------:|------------:|
| 2025-01     |    -8.39819  |       1000     |      916.018 |       37 |     14 |       23 |  -83.9819   |
| 2025-02     |     2.96265  |        916.018 |      943.157 |       30 |     14 |       16 |   27.1384   |
| 2025-03     |     1.2874   |        943.157 |      955.299 |       32 |     17 |       15 |   12.1422   |
| 2025-04     |   -13.0511   |        955.299 |      830.622 |       35 |     14 |       21 | -124.677    |
| 2025-05     |    -0.172635 |        830.622 |      829.188 |       31 |     15 |       16 |   -1.43394  |
| 2025-06     |   -12.8516   |        829.188 |      722.624 |       35 |     12 |       23 | -106.564    |
| 2025-07     |    -2.14043  |        722.624 |      707.157 |       32 |     14 |       18 |  -15.4673   |
| 2025-08     |    -4.35981  |        707.157 |      676.327 |       35 |     13 |       22 |  -30.8307   |
| 2025-09     |    -5.02329  |        676.327 |      642.353 |       34 |     16 |       18 |  -33.9738   |
| 2025-10     |    -0.118336 |        642.353 |      641.593 |       31 |     15 |       16 |   -0.760136 |
| 2025-11     |   -16.4489   |        641.593 |      536.057 |       37 |      9 |       28 | -105.535    |
| 2025-12     |    -4.49747  |        536.057 |      511.948 |       38 |     13 |       25 |  -24.109    |
| 2026-01     |    -6.08872  |        511.948 |      480.777 |       37 |     13 |       24 |  -31.1711   |
| 2026-02     |    -6.63684  |        480.777 |      448.869 |       34 |     13 |       21 |  -31.9084   |
| 2026-03     |     5.2811   |        448.869 |      472.574 |       32 |     17 |       15 |   23.7052   |
| 2026-04     |    -1.08271  |        472.574 |      467.457 |       34 |     13 |       21 |   -5.1166   |
| 2026-05     |    -4.99533  |        467.457 |      444.106 |       33 |     13 |       20 |  -23.3511   |
| 2026-06     |   -10.4533   |        444.106 |      397.683 |       28 |      8 |       20 |  -46.4236   |
| 2026-07     |    -2.56889  |        397.683 |      387.467 |       29 |     15 |       14 |  -10.216    |
| 2026-08     |   -11.9094   |        387.467 |      341.322 |       32 |     10 |       22 |  -46.145    |
| 2026-09     |    -5.4587   |        341.322 |      322.69  |       31 |     14 |       17 |  -18.6317   |
| 2026-10     |   -12.0666   |        322.69  |      283.752 |       31 |      8 |       23 |  -38.9378   |

## Audit
{
  "source": "Delta Exchange India original BTCUSD 1m",
  "input_months": 22,
  "source_minutes": 963360,
  "october_2026_complete": true,
  "selected_using": "2025 only, ranking positive months then sum of monthly net returns",
  "chosen": "impact5_stop2.5",
  "all_22_positive": false,
  "all_22_ge10": false,
  "total_trades": 728,
  "wins": 290,
  "losses": 438,
  "max_trade_close_drawdown_pct": -72.89842541505459,
  "fee_per_side_with_gst": 0.00059,
  "slippage_points_per_side": 5.0,
  "missing": [
    "funding",
    "actual bid/ask spread",
    "actual order-book market impact",
    "lot size/margin/liquidation"
  ],
  "first_IST_month_missing_hours": 5.5,
  "warning": "2026 history was seen in previous studies; not pristine forward validation"
}

No guarantee of future profits. Never place orders from this research.
