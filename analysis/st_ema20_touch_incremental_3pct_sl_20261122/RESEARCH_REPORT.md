# EMA20 Touch: 3% initial stop plus incremental profit protection

BTCUSD 1H ST(10,3) first EMA20 Touch, volume ratio 1.25-2.5x; 1m stop updates.
Comparison: single 0.14% lock vs 0.14% -> 0.50% -> 1% -> 2% -> 5% locks.
The stop starts at -3% from entry and moves to the highest reached positive lock.
The Supertrend flip remains a fallback exit; one fill per ST cycle.

## Side-by-side across two simulated price paths

| variant                   | initial_stop   | lock_levels_pct                 |   profitable_months_min |   profitable_months_max |   losing_months_max |   net_usd_min |   net_usd_max |   net_2025_min |   net_2025_max |   net_2026_min |   net_2026_max |   wins |   losses |   stops_triggered |   max_realized_dd_pct |
|:--------------------------|:---------------|:--------------------------------|------------------------:|------------------------:|--------------------:|--------------:|--------------:|---------------:|---------------:|---------------:|---------------:|-------:|---------:|------------------:|----------------------:|
| increment_0p14_0p50_1_2_5 | 3%             | 0.14% -> 0.5% -> 1% -> 2% -> 5% |                      21 |                      21 |                   0 |      1.42551  |      2.08574  |        1.16581 |        1.59866 |         0.2597 |        0.48708 |     50 |        0 |                 0 |                     0 |
| single_0p14               | 3%             | 0.14%                           |                      21 |                      21 |                   0 |      0.723046 |      0.725036 |        0.46296 |        0.46334 |         0.2597 |        0.26208 |     50 |        0 |                 0 |                     0 |

## Yearly and path-level results

| variant                   | path                |   trades |   wins |   losses |   profitable_2025 |   profitable_2026 |   profitable_months |   losing_months |   flat_months |   net_2025 |   net_2026 |   total_net_usd |   stopped_trades |   max_realized_dd_pct |
|:--------------------------|:--------------------|---------:|-------:|---------:|------------------:|------------------:|--------------------:|----------------:|--------------:|-----------:|-----------:|----------------:|-----------------:|----------------------:|
| single_0p14               | open_high_low_close |       50 |     50 |        0 |                11 |                10 |                  21 |               0 |             1 |    0.46296 |    0.26208 |        0.725036 |                0 |                     0 |
| increment_0p14_0p50_1_2_5 | open_high_low_close |       50 |     50 |        0 |                11 |                10 |                  21 |               0 |             1 |    1.59866 |    0.48708 |        2.08574  |                0 |                     0 |
| single_0p14               | open_low_high_close |       50 |     50 |        0 |                11 |                10 |                  21 |               0 |             1 |    0.46334 |    0.2597  |        0.723046 |                0 |                     0 |
| increment_0p14_0p50_1_2_5 | open_low_high_close |       50 |     50 |        0 |                11 |                10 |                  21 |               0 |             1 |    1.16581 |    0.2597  |        1.42551  |                0 |                     0 |

Fees, GST and 5-point execution slippage each side included. No tick sequence, order latency, funding, margin or liquidation. The results are retrospective and are not live-trading proof.
