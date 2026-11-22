# BTCUSD 15m: Highest profitable month count, three ST strategies

Data from the verified three-way grid, 36,036 settings, 22 complete
entry months Jan 2025 through Oct 2026. Prior ST closing exit retained.
Fixed % SL/TP, no profit protection; 1m stop-first OHLC replay.
Net BTC price points after 0.05% taker each way, 18% GST and 5 points
adverse slippage each way. No liquidation or margin modeled.

IMPORTANT: Monthly P&L is credited to ENTRY month in this historic
grid, even if a position closes in a later month. It does not establish
monthly realized cash P&L.

## Highest positive months with SAME filters, >=20 trades
| entry_type               | constraint   |   positive_months |   losing_months |   flat_months |   sl_pct |   tp_pct |   trades |   wins |   losses |   win_rate_pct |   net_pts |   max_drawdown_pts | volume_filter   | atr_filter     |
|:-------------------------|:-------------|------------------:|----------------:|--------------:|---------:|---------:|---------:|-------:|---------:|---------------:|----------:|-------------------:|:----------------|:---------------|
| after_line_touch         | any_net      |                14 |               8 |             0 |      0.2 |      1.5 |      108 |     24 |       84 |          22.22 |   4060.14 |            3055.27 | vol_ge_1p0      | atrpct_ge_0p20 |
| after_line_touch         | net_positive |                14 |               8 |             0 |      0.2 |      1.5 |      108 |     24 |       84 |          22.22 |   4060.14 |            3055.27 | vol_ge_1p0      | atrpct_ge_0p20 |
| after_bullish_flip       | any_net      |                10 |              12 |             0 |      3   |      1.5 |      197 |     78 |      119 |          39.59 | -16829.5  |           23011.6  | vol_ge_1p0      | atrpct_ge_0p20 |
| flip_plus_green_breakout | any_net      |                10 |              12 |             0 |      3   |      1.5 |      132 |     52 |       80 |          39.39 | -11063.7  |           17013.9  | vol_ge_1p0      | atrpct_ge_0p20 |

## Highest positive months across all 42 filters, >=50 trades
| entry_type               | constraint   |   positive_months |   losing_months |   flat_months |   sl_pct |   tp_pct |   trades |   wins |   losses |   win_rate_pct |   net_pts |   max_drawdown_pts | volume_filter   | atr_filter     |
|:-------------------------|:-------------|------------------:|----------------:|--------------:|---------:|---------:|---------:|-------:|---------:|---------------:|----------:|-------------------:|:----------------|:---------------|
| after_line_touch         | any_net      |                14 |               8 |             0 |      0.2 |     1.5  |      108 |     24 |       84 |          22.22 |   4060.14 |            3055.27 | vol_ge_1p0      | atrpct_ge_0p20 |
| after_line_touch         | net_positive |                14 |               8 |             0 |      0.2 |     1.5  |      108 |     24 |       84 |          22.22 |   4060.14 |            3055.27 | vol_ge_1p0      | atrpct_ge_0p20 |
| after_bullish_flip       | any_net      |                15 |               5 |             2 |      3   |     0.2  |       61 |     54 |        7 |          88.52 |  -5813.02 |            7203.86 | vol_ge_1p25     | atrrel_ge_1p25 |
| after_bullish_flip       | net_positive |                13 |               7 |             2 |      3   |     0.75 |       61 |     39 |       22 |          63.93 |    658.88 |            5546.45 | vol_ge_1p25     | atrrel_ge_1p25 |
| flip_plus_green_breakout | any_net      |                15 |               6 |             1 |      3   |     0.2  |       63 |     56 |        7 |          88.89 |  -7163.96 |            8388.99 | vol_ge_1p25     | atrpct_ge_0p30 |
| flip_plus_green_breakout | net_positive |                 8 |              11 |             3 |      3   |     6    |       50 |     16 |       34 |          32    |   2794.17 |            8880.67 | vol_ge_1p0      | atrrel_ge_1p25 |

## Entire benchmark settings with top monthly positive months
| entry_type               | vol_filter   | atr_filter     |   sl_pct |   tp_pct |   trades |   wins |   net_pts |   profitable_months |   losing_months |   flat_months |
|:-------------------------|:-------------|:---------------|---------:|---------:|---------:|-------:|----------:|--------------------:|----------------:|--------------:|
| after_bullish_flip       | vol_ge_2p0   | atrrel_ge_1p25 |      3   |      0.2 |       39 |     34 |  -4598.79 |                  15 |               4 |             3 |
| after_bullish_flip       | vol_ge_2p0   | atrrel_ge_1p25 |      4   |      0.2 |       39 |     34 |  -5164.65 |                  15 |               4 |             3 |
| after_bullish_flip       | vol_ge_2p0   | atrrel_ge_1p25 |      5   |      0.2 |       39 |     34 |  -5164.65 |                  15 |               4 |             3 |
| after_bullish_flip       | vol_ge_1p25  | atrrel_ge_1p25 |      3   |      0.2 |       61 |     54 |  -5813.02 |                  15 |               5 |             2 |
| after_bullish_flip       | vol_ge_1p5   | atrrel_ge_1p25 |      3   |      0.2 |       56 |     49 |  -6173.66 |                  15 |               5 |             2 |
| after_bullish_flip       | vol_ge_1p25  | atrrel_ge_1p25 |      4   |      0.2 |       61 |     54 |  -6378.87 |                  15 |               5 |             2 |
| after_bullish_flip       | vol_ge_1p25  | atrrel_ge_1p25 |      5   |      0.2 |       61 |     54 |  -6378.87 |                  15 |               5 |             2 |
| after_bullish_flip       | vol_ge_1p5   | atrrel_ge_1p25 |      4   |      0.2 |       56 |     49 |  -6739.51 |                  15 |               5 |             2 |
| after_bullish_flip       | vol_ge_1p5   | atrrel_ge_1p25 |      5   |      0.2 |       56 |     49 |  -6739.51 |                  15 |               5 |             2 |
| flip_plus_green_breakout | vol_ge_1p5   | atrpct_ge_0p30 |      3   |      0.2 |       49 |     43 |  -7019.4  |                  15 |               6 |             1 |
| flip_plus_green_breakout | vol_ge_1p25  | atrpct_ge_0p30 |      3   |      0.2 |       63 |     56 |  -7163.96 |                  15 |               6 |             1 |
| flip_plus_green_breakout | vol_ge_1p5   | atrpct_ge_0p30 |      4   |      0.2 |       49 |     43 |  -7585.26 |                  15 |               6 |             1 |
| flip_plus_green_breakout | vol_ge_1p5   | atrpct_ge_0p30 |      5   |      0.2 |       49 |     43 |  -7585.26 |                  15 |               6 |             1 |
| flip_plus_green_breakout | vol_ge_1p25  | atrpct_ge_0p30 |      4   |      0.2 |       63 |     56 |  -7729.82 |                  15 |               6 |             1 |
| flip_plus_green_breakout | vol_ge_1p25  | atrpct_ge_0p30 |      5   |      0.2 |       63 |     56 |  -7729.82 |                  15 |               6 |             1 |
| after_line_touch         | vol_ge_1p0   | atrpct_ge_0p20 |      0.2 |      1.5 |      108 |     24 |   4060.14 |                  14 |               8 |             0 |
| after_bullish_flip       | vol_le_0p8   | atrpct_ge_0p20 |      3   |      0.5 |       42 |     33 |   3401.08 |                  14 |               5 |             3 |
| after_bullish_flip       | vol_le_0p8   | atrpct_ge_0p20 |      4   |      0.5 |       42 |     33 |   3401.08 |                  14 |               5 |             3 |
| after_bullish_flip       | vol_le_0p8   | atrpct_ge_0p20 |      5   |      0.5 |       42 |     33 |   3401.08 |                  14 |               5 |             3 |
| flip_plus_green_breakout | vol_ge_1p5   | atrpct_ge_0p30 |      3   |      0.5 |       49 |     39 |  -1188.63 |                  14 |               7 |             1 |

## Warning
Maximizing winning months across 36,036 previously viewed configurations
is in-sample optimization. A config with many positive months may lose
overall (the few bad months can erase many small winning months).
To claim durable consistency, require out-of-sample and exit-month
cashflow/equity mark-to-market audit with liquidation and funding.
