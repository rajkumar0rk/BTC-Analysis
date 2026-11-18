# Stage 13 — 4H trend + 1H EMA20 pullback + 15M breakout

Rules predeclared: two pullback strictness choices, optional 15M breakout volume,
2R/3R target and 4h/8h maximum hold, 16 strategy configurations.
Every signal uses completed candles, next 1M OPEN execution, and structural stop.
No fixed trading time. Historical 2026 has already been researched.

## Monthly research consistency
| pullback      | volume      |   target_R |   max_hold_min |   trades_2025 |   profitable_2025 |   losing_2025 |   no_trade_2025 |   net_2025 |   trades_2026 |   profitable_2026 |   losing_2026 |   no_trade_2026 |   net_2026 | sufficient_samples   | positive_2025_H1_H2   | passes_monthly_gate   |
|:--------------|:------------|-----------:|---------------:|--------------:|------------------:|--------------:|----------------:|-----------:|--------------:|------------------:|--------------:|----------------:|-----------:|:---------------------|:----------------------|:----------------------|
| near_half_atr | any         |          2 |            240 |            11 |                 4 |             1 |               7 |     455.91 |             1 |                 0 |             1 |              10 |     -16.28 | False                | False                 | False                 |
| near_half_atr | any         |          2 |            480 |            11 |                 4 |             1 |               7 |     641.52 |             1 |                 1 |             0 |              10 |      39.2  | False                | False                 | False                 |
| near_half_atr | any         |          3 |            240 |            11 |                 4 |             1 |               7 |     455.91 |             1 |                 0 |             1 |              10 |     -16.28 | False                | False                 | False                 |
| near_half_atr | any         |          3 |            480 |            11 |                 4 |             1 |               7 |     733.78 |             1 |                 1 |             0 |              10 |      39.2  | False                | False                 | False                 |
| near_half_atr | volume_1p2x |          2 |            240 |            10 |                 5 |             0 |               7 |     553.52 |             1 |                 0 |             1 |              10 |     -16.28 | False                | False                 | False                 |
| near_half_atr | volume_1p2x |          2 |            480 |            10 |                 5 |             0 |               7 |     801.57 |             1 |                 1 |             0 |              10 |      39.2  | False                | False                 | False                 |
| near_half_atr | volume_1p2x |          3 |            240 |            10 |                 5 |             0 |               7 |     553.52 |             1 |                 0 |             1 |              10 |     -16.28 | False                | False                 | False                 |
| near_half_atr | volume_1p2x |          3 |            480 |            10 |                 5 |             0 |               7 |     893.83 |             1 |                 1 |             0 |              10 |      39.2  | False                | False                 | False                 |
| touch         | any         |          2 |            240 |             8 |                 4 |             1 |               7 |     477.98 |             0 |                 0 |             0 |              11 |       0    | False                | False                 | False                 |
| touch         | any         |          2 |            480 |             8 |                 4 |             1 |               7 |     713.43 |             0 |                 0 |             0 |              11 |       0    | False                | False                 | False                 |
| touch         | any         |          3 |            240 |             8 |                 4 |             1 |               7 |     477.98 |             0 |                 0 |             0 |              11 |       0    | False                | False                 | False                 |
| touch         | any         |          3 |            480 |             8 |                 4 |             1 |               7 |     805.69 |             0 |                 0 |             0 |              11 |       0    | False                | False                 | False                 |
| touch         | volume_1p2x |          2 |            240 |             7 |                 4 |             0 |               8 |     575.59 |             0 |                 0 |             0 |              11 |       0    | False                | False                 | False                 |
| touch         | volume_1p2x |          2 |            480 |             7 |                 4 |             0 |               8 |     873.48 |             0 |                 0 |             0 |              11 |       0    | False                | False                 | False                 |
| touch         | volume_1p2x |          3 |            240 |             7 |                 4 |             0 |               8 |     575.59 |             0 |                 0 |             0 |              11 |       0    | False                | False                 | False                 |
| touch         | volume_1p2x |          3 |            480 |             7 |                 4 |             0 |               8 |     965.74 |             0 |                 0 |             0 |              11 |       0    | False                | False                 | False                 |

## Full standard after-fee period results
| pullback      | volume      |   target_R |   max_hold_min | period             | fee            |   trades |   longs |   shorts |   wins |   losses |   win_rate |   mean_net |   net_total |   profit_factor |   worst_trade |   max_drawdown |
|:--------------|:------------|-----------:|---------------:|:-------------------|:---------------|---------:|--------:|---------:|-------:|---------:|-----------:|-----------:|------------:|----------------:|--------------:|---------------:|
| near_half_atr | any         |          2 |            240 | 2025_train         | standard_taker |       11 |       2 |        9 |      8 |        3 |      72.73 |      41.45 |      455.91 |           4.079 |        -97.61 |          97.61 |
| near_half_atr | any         |          2 |            240 | 2026_H1_validation | standard_taker |        1 |       0 |        1 |      0 |        1 |       0    |     -16.28 |      -16.28 |           0     |        -16.28 |          16.28 |
| near_half_atr | any         |          2 |            480 | 2025_train         | standard_taker |       11 |       2 |        9 |      6 |        5 |      54.55 |      58.32 |      641.52 |           2.907 |       -160.05 |         160.05 |
| near_half_atr | any         |          2 |            480 | 2026_H1_validation | standard_taker |        1 |       0 |        1 |      1 |        0 |     100    |      39.2  |       39.2  |         nan     |         39.2  |           0    |
| near_half_atr | any         |          3 |            240 | 2025_train         | standard_taker |       11 |       2 |        9 |      8 |        3 |      72.73 |      41.45 |      455.91 |           4.079 |        -97.61 |          97.61 |
| near_half_atr | any         |          3 |            240 | 2026_H1_validation | standard_taker |        1 |       0 |        1 |      0 |        1 |       0    |     -16.28 |      -16.28 |           0     |        -16.28 |          16.28 |
| near_half_atr | any         |          3 |            480 | 2025_train         | standard_taker |       11 |       2 |        9 |      6 |        5 |      54.55 |      66.71 |      733.78 |           3.181 |       -160.05 |         160.05 |
| near_half_atr | any         |          3 |            480 | 2026_H1_validation | standard_taker |        1 |       0 |        1 |      1 |        0 |     100    |      39.2  |       39.2  |         nan     |         39.2  |           0    |
| near_half_atr | volume_1p2x |          2 |            240 | 2025_train         | standard_taker |       10 |       2 |        8 |      8 |        2 |      80    |      55.35 |      553.52 |          11.969 |        -35.84 |          50.46 |
| near_half_atr | volume_1p2x |          2 |            240 | 2026_H1_validation | standard_taker |        1 |       0 |        1 |      0 |        1 |       0    |     -16.28 |      -16.28 |           0     |        -16.28 |          16.28 |
| near_half_atr | volume_1p2x |          2 |            480 | 2025_train         | standard_taker |       10 |       2 |        8 |      6 |        4 |      60    |      80.16 |      801.57 |           5.546 |        -89.79 |          89.79 |
| near_half_atr | volume_1p2x |          2 |            480 | 2026_H1_validation | standard_taker |        1 |       0 |        1 |      1 |        0 |     100    |      39.2  |       39.2  |         nan     |         39.2  |           0    |
| near_half_atr | volume_1p2x |          3 |            240 | 2025_train         | standard_taker |       10 |       2 |        8 |      8 |        2 |      80    |      55.35 |      553.52 |          11.969 |        -35.84 |          50.46 |
| near_half_atr | volume_1p2x |          3 |            240 | 2026_H1_validation | standard_taker |        1 |       0 |        1 |      0 |        1 |       0    |     -16.28 |      -16.28 |           0     |        -16.28 |          16.28 |
| near_half_atr | volume_1p2x |          3 |            480 | 2025_train         | standard_taker |       10 |       2 |        8 |      6 |        4 |      60    |      89.38 |      893.83 |           6.069 |        -89.79 |          89.79 |
| near_half_atr | volume_1p2x |          3 |            480 | 2026_H1_validation | standard_taker |        1 |       0 |        1 |      1 |        0 |     100    |      39.2  |       39.2  |         nan     |         39.2  |           0    |
| touch         | any         |          2 |            240 | 2025_train         | standard_taker |        8 |       2 |        6 |      7 |        1 |      87.5  |      59.75 |      477.98 |           5.897 |        -97.61 |          97.61 |
| touch         | any         |          2 |            480 | 2025_train         | standard_taker |        8 |       2 |        6 |      5 |        3 |      62.5  |      89.18 |      713.43 |           3.836 |       -160.05 |         160.05 |
| touch         | any         |          3 |            240 | 2025_train         | standard_taker |        8 |       2 |        6 |      7 |        1 |      87.5  |      59.75 |      477.98 |           5.897 |        -97.61 |          97.61 |
| touch         | any         |          3 |            480 | 2025_train         | standard_taker |        8 |       2 |        6 |      5 |        3 |      62.5  |     100.71 |      805.69 |           4.203 |       -160.05 |         160.05 |
| touch         | volume_1p2x |          2 |            240 | 2025_train         | standard_taker |        7 |       2 |        5 |      7 |        0 |     100    |      82.23 |      575.59 |         nan     |         23.38 |           0    |
| touch         | volume_1p2x |          2 |            480 | 2025_train         | standard_taker |        7 |       2 |        5 |      5 |        2 |      71.43 |     124.78 |      873.48 |          10.547 |        -89.79 |          89.79 |
| touch         | volume_1p2x |          3 |            240 | 2025_train         | standard_taker |        7 |       2 |        5 |      7 |        0 |     100    |      82.23 |      575.59 |         nan     |         23.38 |           0    |
| touch         | volume_1p2x |          3 |            480 | 2025_train         | standard_taker |        7 |       2 |        5 |      5 |        2 |      71.43 |     137.96 |      965.74 |          11.556 |        -89.79 |          89.79 |

## Baseline monthly table: strict touch + volume + 2R + 8h
| pullback   | volume      |   target_R |   max_hold_min | month_ist   |   trades |   net_pts | status   |
|:-----------|:------------|-----------:|---------------:|:------------|---------:|----------:|:---------|
| touch      | volume_1p2x |          2 |            480 | 2025-01     |        0 |      0    | No trade |
| touch      | volume_1p2x |          2 |            480 | 2025-02     |        0 |      0    | No trade |
| touch      | volume_1p2x |          2 |            480 | 2025-03     |        0 |      0    | No trade |
| touch      | volume_1p2x |          2 |            480 | 2025-04     |        0 |      0    | No trade |
| touch      | volume_1p2x |          2 |            480 | 2025-05     |        0 |      0    | No trade |
| touch      | volume_1p2x |          2 |            480 | 2025-06     |        0 |      0    | No trade |
| touch      | volume_1p2x |          2 |            480 | 2025-07     |        0 |      0    | No trade |
| touch      | volume_1p2x |          2 |            480 | 2025-08     |        1 |    172.89 | Profit   |
| touch      | volume_1p2x |          2 |            480 | 2025-09     |        0 |      0    | No trade |
| touch      | volume_1p2x |          2 |            480 | 2025-10     |        2 |    432.86 | Profit   |
| touch      | volume_1p2x |          2 |            480 | 2025-11     |        2 |    218.05 | Profit   |
| touch      | volume_1p2x |          2 |            480 | 2025-12     |        2 |     49.68 | Profit   |
| touch      | volume_1p2x |          2 |            480 | 2026-01     |        0 |      0    | No trade |
| touch      | volume_1p2x |          2 |            480 | 2026-02     |        0 |      0    | No trade |
| touch      | volume_1p2x |          2 |            480 | 2026-03     |        0 |      0    | No trade |
| touch      | volume_1p2x |          2 |            480 | 2026-04     |        0 |      0    | No trade |
| touch      | volume_1p2x |          2 |            480 | 2026-05     |        0 |      0    | No trade |
| touch      | volume_1p2x |          2 |            480 | 2026-06     |        0 |      0    | No trade |
| touch      | volume_1p2x |          2 |            480 | 2026-07     |        0 |      0    | No trade |
| touch      | volume_1p2x |          2 |            480 | 2026-08     |        0 |      0    | No trade |
| touch      | volume_1p2x |          2 |            480 | 2026-09     |        0 |      0    | No trade |
| touch      | volume_1p2x |          2 |            480 | 2026-10     |        0 |      0    | No trade |
| touch      | volume_1p2x |          2 |            480 | 2026-11     |        0 |      0    | No trade |

## Interpretation
A passed research gate requires >=70% profitable active months in each year,
at least 9 active months 2025 and 8 in 2026, and positive expectancy in
2025, 2026 H1 and 2026 H2 with >=50/25/15 trades.
Passing historical rules does NOT establish live profitability.

## Caveats
- All tested historical periods already used in previous research, not a pristine out-of-sample test
- 2026-10-31 is missing from source; 2026-11 ends Nov 16
- Fees 0.05% taker/side, 18% GST, adverse 5 BTC points slippage per side; included in standard net
- Scalper Offer closing fee waiver is hypothetical and not assumed for standard PnL
- Funding, order-book spreads, margin, liquidation and impact not modeled
- Stops resolved first when OHLC bar touches stop and target; gap stop can fill worse
- All months with zero trades included; no guarantee of monthly profitability
- Aggregate BTC price points are not account profit or capital returns
- One open trade at a time within a model, LONG and SHORT mutually exclusive

Reproduce using scripts/research_trend_pullback_breakout_stage13.py.
Detailed events/trades saved in the associated GitHub Actions artifact.
