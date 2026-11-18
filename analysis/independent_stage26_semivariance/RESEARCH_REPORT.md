# Stage26 — 15m realized semivariance exhaustion

This is exploratory, not an executable live edge. Original data checksum verified.
October 2026 UTC 1m is fully repaired on the isolated branch.
January 2025 IST lacks the first 5.5 hours; cannot assert fully observed 22 IST months.
Fees and GST included, 5 points adverse slippage each side; no funding, spread, market impact or lot granularity.
Sizing uses 1% equity stop-distance risk and 3x notional cap, not validated Delta margin.
2025-only model selection, 2026 already seen in prior research (not blind).

## All configurations

| key            |   train_positive |   recheck_positive |   train_ge10 |   recheck_ge10 |   train_total_pct |   worst_month_pct |   total_trades | all_22_positive   | all_22_ge10   |
|:---------------|-----------------:|-------------------:|-------------:|---------------:|------------------:|------------------:|---------------:|:------------------|:--------------|
| ratio3_stop2.5 |                0 |                  0 |            0 |              0 |          -139.122 |          -27.8746 |           1390 | False             | False         |
| ratio3_stop1.5 |                0 |                  0 |            0 |              0 |          -225.896 |          -38.2112 |           1759 | False             | False         |
| ratio2_stop2.5 |                0 |                  0 |            0 |              0 |          -294.138 |          -39.0854 |           2674 | False             | False         |
| ratio2_stop1.5 |                0 |                  0 |            0 |              0 |          -460.235 |          -50.2412 |           3499 | False             | False         |

## Chosen 2025-only configuration
ratio3_stop2.5

## Monthly net account returns

| month_ist   |   return_pct |   start_equity |   end_equity |   trades |   wins |   losses |    net_usd |
|:------------|-------------:|---------------:|-------------:|---------:|-------:|---------:|-----------:|
| 2025-01     |   -26.1393   |      1000      |     738.607  |       68 |     21 |       47 | -261.393   |
| 2025-02     |    -0.469641 |       738.607  |     735.138  |       52 |     25 |       27 |   -3.4688  |
| 2025-03     |    -3.82509  |       735.138  |     707.019  |       65 |     30 |       35 |  -28.1197  |
| 2025-04     |    -7.55222  |       707.019  |     653.623  |       45 |     16 |       29 |  -53.3956  |
| 2025-05     |   -12.5249   |       653.623  |     571.757  |       58 |     22 |       36 |  -81.866   |
| 2025-06     |   -13.8549   |       571.757  |     492.541  |       57 |     23 |       34 |  -79.2165  |
| 2025-07     |   -18.9229   |       492.541  |     399.338  |       55 |     19 |       36 |  -93.2028  |
| 2025-08     |   -10.5675   |       399.338  |     357.138  |       53 |     23 |       30 |  -42.1998  |
| 2025-09     |   -14.1231   |       357.138  |     306.699  |       59 |     24 |       35 |  -50.4388  |
| 2025-10     |   -25.7683   |       306.699  |     227.668  |       70 |     22 |       48 |  -79.0313  |
| 2025-11     |    -4.42077  |       227.668  |     217.603  |       45 |     16 |       29 |  -10.0647  |
| 2025-12     |    -0.953127 |       217.603  |     215.529  |       66 |     32 |       34 |   -2.07403 |
| 2026-01     |   -13.9836   |       215.529  |     185.39   |       70 |     29 |       41 |  -30.1388  |
| 2026-02     |    -1.72533  |       185.39   |     182.192  |       65 |     29 |       36 |   -3.1986  |
| 2026-03     |   -18.9711   |       182.192  |     147.628  |       81 |     36 |       45 |  -34.5638  |
| 2026-04     |   -12.9165   |       147.628  |     128.56   |       62 |     22 |       40 |  -19.0684  |
| 2026-05     |    -4.37615  |       128.56   |     122.934  |       66 |     28 |       38 |   -5.62596 |
| 2026-06     |   -12.568    |       122.934  |     107.483  |       66 |     29 |       37 |  -15.4502  |
| 2026-07     |   -25.346    |       107.483  |      80.2406 |       74 |     29 |       45 |  -27.2427  |
| 2026-08     |   -27.8746   |        80.2406 |      57.8738 |       85 |     25 |       60 |  -22.3668  |
| 2026-09     |   -13.0392   |        57.8738 |      50.3276 |       53 |     19 |       34 |   -7.5463  |
| 2026-10     |   -13.5082   |        50.3276 |      43.5292 |       75 |     29 |       46 |   -6.79837 |

## Audit
{
  "source": "Delta Exchange India original BTCUSD 1m",
  "input_months": 22,
  "source_minutes": 963360,
  "october_2026_complete": true,
  "selected_using": "2025 only, ranking positive months then sum of monthly net returns",
  "chosen": "ratio3_stop2.5",
  "all_22_positive": false,
  "all_22_ge10": false,
  "total_trades": 1390,
  "wins": 548,
  "losses": 842,
  "max_trade_close_drawdown_pct": -95.89207522269072,
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
