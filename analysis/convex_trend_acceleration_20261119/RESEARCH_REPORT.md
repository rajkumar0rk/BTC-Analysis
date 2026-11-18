# Independent trend-acceleration impulse strategy research

**Predeclared qualifying models: 0/64**

## Qualifying results
None

## Top models by 2025 performance (2026 reported without selecting on it)
| symbol   | model                                                 |   signals |   trades |   wins |   losses |   win_rate_pct |   profit_factor |   avg_win_loss_ratio |   biggest_winner_R |   winners_over_10R |   net_return_pct |   max_drawdown_pct |   fees_usd |   funding_proxy_usd |   return_2025_pct |   return_2026_pct |   profit_months |   loss_months |   active_months |
|:---------|:------------------------------------------------------|----------:|---------:|-------:|---------:|---------------:|----------------:|---------------------:|-------------------:|-------------------:|-----------------:|-------------------:|-----------:|--------------------:|------------------:|------------------:|----------------:|--------------:|----------------:|
| BTCUSD   | accel2.5_consistency0.75_vol1_init2atr_trail8atr      |       186 |       77 |     19 |       58 |         24.675 |          1.135  |               3.4646 |             12.847 |                  1 |            4.048 |             -9.793 |     42.995 |              -1.662 |             2.613 |             1.399 |              10 |            13 |              23 |
| BTCUSD   | accel2.5_consistency0.67_vol1_init2atr_trail8atr      |       186 |       77 |     19 |       58 |         24.675 |          1.135  |               3.4646 |             12.847 |                  1 |            4.048 |             -9.793 |     42.995 |              -1.662 |             2.613 |             1.399 |              10 |            13 |              23 |
| BTCUSD   | accel2.5_consistency0.67_vol1.5_init2atr_trail8atr    |       124 |       59 |     14 |       45 |         23.729 |          1.1256 |               3.618  |             12.847 |                  1 |            2.895 |            -11.053 |     31.162 |              -0.66  |             2.245 |             0.636 |               9 |            13 |              22 |
| BTCUSD   | accel2.5_consistency0.75_vol1.5_init2atr_trail8atr    |       124 |       59 |     14 |       45 |         23.729 |          1.1256 |               3.618  |             12.847 |                  1 |            2.895 |            -11.053 |     31.162 |              -0.66  |             2.245 |             0.636 |               9 |            13 |              22 |
| ETHUSD   | accel1.5_consistency0.75_vol1.5_init1.25atr_trail8atr |       225 |      109 |     13 |       96 |         11.927 |          0.9842 |               7.2681 |             21.257 |                  4 |           -0.846 |            -16.582 |     60.801 |               1.067 |             0.426 |            -1.267 |               9 |            14 |              23 |
| ETHUSD   | accel1.5_consistency0.67_vol1.5_init1.25atr_trail8atr |       225 |      109 |     13 |       96 |         11.927 |          0.9842 |               7.2681 |             21.257 |                  4 |           -0.846 |            -16.582 |     60.801 |               1.067 |             0.426 |            -1.267 |               9 |            14 |              23 |
| BTCUSD   | accel2.5_consistency0.75_vol1_init2atr_trail12atr     |       186 |       67 |     15 |       52 |         22.388 |          1.2429 |               4.3088 |             13.729 |                  2 |            6.835 |            -10.389 |     39.275 |              -1.692 |            -0.106 |             6.948 |              10 |            13 |              23 |
| BTCUSD   | accel2.5_consistency0.67_vol1_init2atr_trail12atr     |       186 |       67 |     15 |       52 |         22.388 |          1.2429 |               4.3088 |             13.729 |                  2 |            6.835 |            -10.389 |     39.275 |              -1.692 |            -0.106 |             6.948 |              10 |            13 |              23 |
| BTCUSD   | accel1.5_consistency0.67_vol1.5_init2atr_trail8atr    |       195 |       82 |     21 |       61 |         25.61  |          1.284  |               3.7297 |             18.411 |                  1 |            8.881 |            -13.235 |     44.53  |              -0.583 |            -0.142 |             9.035 |              13 |            10 |              23 |
| BTCUSD   | accel1.5_consistency0.75_vol1.5_init2atr_trail8atr    |       195 |       82 |     21 |       61 |         25.61  |          1.284  |               3.7297 |             18.411 |                  1 |            8.881 |            -13.235 |     44.53  |              -0.583 |            -0.142 |             9.035 |              13 |            10 |              23 |
| BTCUSD   | accel1.5_consistency0.75_vol1_init1.25atr_trail8atr   |       306 |      117 |     24 |       93 |         20.513 |          1.2682 |               4.9141 |             29.458 |                  5 |           14.43  |            -19.959 |    101.728 |              -0.019 |            -0.242 |            14.708 |              10 |            13 |              23 |
| BTCUSD   | accel1.5_consistency0.67_vol1_init1.25atr_trail8atr   |       306 |      117 |     24 |       93 |         20.513 |          1.2682 |               4.9141 |             29.458 |                  5 |           14.43  |            -19.959 |    101.728 |              -0.019 |            -0.242 |            14.708 |              10 |            13 |              23 |

## Promising exploratory candidates (not validated)
None

## Candidate trade concentration
None

## Caution
- Open source historical data already research-exposed; 2026 is not independent untouched holdout
- Monthly NAV and unrealized liquidation fee at IST calendar boundary
- 1min bar OHLC cannot provide order book, spread, or exact intrabar order
- The same-minute entry candle stop check deferred to next 1min open
- True settled funding cashflows and liquidation margin not independently verified
- 2026 November partial; no 2022-2024 Delta history in repository
- No qualifying model is NOT evidence all asymmetric strategies fail
