# BTCUSD 15M Reclaim — adaptive sizing / drawdown search

This research varies **position sizing only** in the original proven engine, not signals/exits.
Original 5-losses-per-month pause, +8.25% activation / 0% lock, 3% SL/9% TP remain.
Jan2025–Oct2026, 22 IST calendar months, 1-minute price-path test; net includes taker fees +18% GST and 0.02% slippage per side; funding excluded.
**History is thoroughly in-sample; optimizing thresholds across it is not prospective evidence.**
IMPORTANT: models with size multiplier > 1 use additional leverage; they should NOT be directly considered a same-risk replacement.

## Baseline (re-verified in each shard and path)
72 trades, +151.787% net, 18/22 profitable months, maximum floating DD 19.948%.

## Counts: 38 models
Qualified strictly (net >=151.787%, >=18 profitable months, DD <19.948%): 2.
Of those with <=1x position sizing: 2.
Of those reaching <=12% DD: 0.

## Strict 1x-max sizing models (best DD first)
| size_mode   |   worst_dd |   min_profit |   min_positive_months |   max_size |   min_trades |   max_trades | qualifies_profit_and_months   | drawdown_better   | reaches_target_12pct   | reaches_target_10pct   | all_criteria   |
|:------------|-----------:|-------------:|----------------------:|-----------:|-------------:|-------------:|:------------------------------|:------------------|:-----------------------|:-----------------------|:---------------|
| DD05F       |     11.187 |      31.9169 |                    16 |          1 |           72 |           72 | False                         | True              | True                   | False                  | False          |
| DD03H       |     13.759 |      72.8125 |                    18 |          1 |           72 |           72 | False                         | True              | False                  | False                  | False          |
| ML02H       |     14.064 |     145.268  |                    17 |          1 |           72 |           72 | False                         | True              | False                  | False                  | False          |
| DD08F       |     14.793 |      19.8384 |                    15 |          1 |           72 |           72 | False                         | True              | False                  | False                  | False          |
| DD05H       |     15.135 |      78.9329 |                    17 |          1 |           72 |           72 | False                         | True              | False                  | False                  | False          |
| DD08H       |     15.143 |      81.1455 |                    17 |          1 |           72 |           72 | False                         | True              | False                  | False                  | False          |
| MM03H       |     16.295 |     112.066  |                    16 |          1 |           72 |           72 | False                         | True              | False                  | False                  | False          |
| ML03H       |     16.662 |     172.101  |                    18 |          1 |           72 |           72 | True                          | True              | False                  | False                  | True           |
| ML02Q       |     16.757 |     149.088  |                    18 |          1 |           72 |           72 | False                         | True              | False                  | False                  | False          |
| DD03Q       |     17.293 |     110.809  |                    18 |          1 |           72 |           72 | False                         | True              | False                  | False                  | False          |
| DD08Q       |     17.427 |     113.011  |                    18 |          1 |           72 |           72 | False                         | True              | False                  | False                  | False          |
| MM07H       |     17.628 |     149.441  |                    18 |          1 |           72 |           72 | False                         | True              | False                  | False                  | False          |
| MM05H       |     17.628 |     138.631  |                    17 |          1 |           72 |           72 | False                         | True              | False                  | False                  | False          |
| DD10H       |     17.828 |      67.1632 |                    17 |          1 |           72 |           72 | False                         | True              | False                  | False                  | False          |
| DD05Q       |     17.958 |     109.269  |                    18 |          1 |           72 |           72 | False                         | True              | False                  | False                  | False          |

## Up to 2x leveraged profiles (separate risk category)
| size_mode   |   worst_dd |   min_profit |   min_positive_months |   max_size |   min_trades |   max_trades | qualifies_profit_and_months   | drawdown_better   | reaches_target_12pct   | reaches_target_10pct   | all_criteria   |
|:------------|-----------:|-------------:|----------------------:|-----------:|-------------:|-------------:|:------------------------------|:------------------|:-----------------------|:-----------------------|:---------------|
| DD05B12     |     15.166 |      82.5632 |                    18 |        1.2 |           72 |           72 | False                         | True              | False                  | False                  | False          |
| DD05B15     |     16.633 |      41.8376 |                    17 |        1.5 |           72 |           72 | False                         | True              | False                  | False                  | False          |
| DD08B12     |     17.061 |      76.7141 |                    17 |        1.2 |           72 |           72 | False                         | True              | False                  | False                  | False          |
| DD05B12Q    |     19.17  |     125.457  |                    18 |        1.2 |           72 |           72 | False                         | True              | False                  | False                  | False          |
| DD10B15     |     19.865 |      72.6054 |                    17 |        1.5 |           72 |           72 | False                         | True              | False                  | False                  | False          |
| DD08B15     |     19.865 |      56.4764 |                    17 |        1.5 |           72 |           72 | False                         | True              | False                  | False                  | False          |
| DD05B18     |     20.065 |     133.278  |                    18 |        1.8 |           72 |           72 | False                         | False             | False                  | False                  | False          |
| DD05B13     |     20.092 |     123.971  |                    18 |        1.3 |           72 |           72 | False                         | False             | False                  | False                  | False          |
| DD08B13     |     20.092 |     122.025  |                    18 |        1.3 |           72 |           72 | False                         | False             | False                  | False                  | False          |
| DD08B12Q    |     20.34  |     117.461  |                    18 |        1.2 |           72 |           72 | False                         | False             | False                  | False                  | False          |
| DD05B20     |     20.79  |      52.2541 |                    16 |        2   |           72 |           72 | False                         | False             | False                  | False                  | False          |
| DD08B18     |     21.905 |     136.79   |                    18 |        1.8 |           72 |           72 | False                         | False             | False                  | False                  | False          |
| ATR03B15    |     23.651 |     101.269  |                    18 |        1.5 |           72 |           72 | False                         | False             | False                  | False                  | False          |
| MLOSS3B15   |     24.543 |     330.761  |                    18 |        1.5 |           72 |           72 | True                          | False             | False                  | False                  | False          |
| ATR04B15    |     26.217 |     122.375  |                    17 |        1.5 |           72 |           72 | False                         | False             | False                  | False                  | False          |

## Qualified on all three conditions
| size_mode   |   worst_dd |   min_profit |   min_positive_months |   max_size |   min_trades |   max_trades | qualifies_profit_and_months   | drawdown_better   | reaches_target_12pct   | reaches_target_10pct   | all_criteria   |
|:------------|-----------:|-------------:|----------------------:|-----------:|-------------:|-------------:|:------------------------------|:------------------|:-----------------------|:-----------------------|:---------------|
| ML03H       |     16.662 |      172.101 |                    18 |          1 |           72 |           72 | True                          | True              | False                  | False                  | True           |
| ML04H       |     18.855 |      157.575 |                    18 |          1 |           72 |           72 | True                          | True              | False                  | False                  | True           |

## Audit notes
All strict comparisons are on *max intratrade/floating equity drawdown*, not just closed-trade peaks.
Stop execution modeled via 1-minute OHLC path alternatives; real fill/gap/funding effects can be worse.
None of the results implies future performance.
