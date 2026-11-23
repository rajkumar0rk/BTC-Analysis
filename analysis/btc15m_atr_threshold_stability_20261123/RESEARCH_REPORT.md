# BTCUSD 15m — ATR threshold sensitivity around 0.20%

153 threshold × fractional-exposure variants; two original 1m OHLC price path assumptions; 22 IST months Jan2025–Oct2026.
Source comparator verified each shard: ATR>=0.20%, +229.037% return, 14.740% max floating DD, 18 profitable months /71 trades.
Current target: DD <12%, net >=+162.964%, >=18/22 positive months, never >1x position sizing.
Original 15M ST/EMA20 reclaim, SL3%, TP9%, +8.25%/BE protection, five-loss month guard, tiered post-loss sizes all unchanged.
Fees 0.05% taker each side+18% GST, 0.02% per-side adverse price slippage modeled; real funding, spread and liquidation unmodeled.
**In-sample parameter sensitivity study, not independent validation or a forward performance expectation.**

Passing threshold-size pairs below 12% DD: 1
Passing below 14.74% DD with net >=+162.964%: 5

## ATR threshold robustness (filter applies at completed 15M reclaim signal)
|   threshold_pct |   best_dd |   max_net |   best_positive_months |   count_pass_12 |
|----------------:|----------:|----------:|-----------------------:|----------------:|
|           0.16  |    11.783 |  177.432  |                     17 |               0 |
|           0.165 |    11.783 |  177.429  |                     17 |               0 |
|           0.17  |    10.432 |  170.683  |                     18 |               0 |
|           0.175 |    10.432 |  170.683  |                     18 |               0 |
|           0.18  |    10.432 |  170.683  |                     18 |               0 |
|           0.185 |    10.432 |  170.683  |                     18 |               0 |
|           0.19  |    10.432 |  170.683  |                     18 |               0 |
|           0.195 |    10.432 |  170.683  |                     18 |               0 |
|           0.2   |    10.432 |  229.037  |                     18 |               1 |
|           0.205 |    14.816 |  205.583  |                     17 |               0 |
|           0.21  |    14.816 |  206.544  |                     17 |               0 |
|           0.215 |    14.816 |  207.508  |                     17 |               0 |
|           0.22  |    14.816 |  207.508  |                     17 |               0 |
|           0.225 |    22.387 |   78.9964 |                     13 |               0 |
|           0.23  |    22.387 |   74.7336 |                     12 |               0 |
|           0.24  |    22.388 |   69.2425 |                     12 |               0 |
|           0.25  |    22.388 |   69.2425 |                     12 |               0 |

## Below-12% qualifying combinations
|   threshold_pct |   global_size |   worst_path_dd |   worst_path_profit |   min_profitable_months |   ntrades | passes_target12   | passes_original   |
|----------------:|--------------:|----------------:|--------------------:|------------------------:|----------:|:------------------|:------------------|
|             0.2 |           0.8 |          11.879 |             163.492 |                      18 |        71 | True              | True              |

## Lowest drawdown while preserving original target
|   threshold_pct |   global_size |   worst_path_dd |   worst_path_profit |   min_profitable_months |   ntrades | passes_target12   | passes_original   |
|----------------:|--------------:|----------------:|--------------------:|------------------------:|----------:|:------------------|:------------------|
|             0.2 |         0.8   |          11.879 |             163.492 |                      18 |        71 | True              | True              |
|             0.2 |         0.825 |          12.24  |             171.026 |                      18 |        71 | False             | True              |
|             0.2 |         0.85  |          12.599 |             178.741 |                      18 |        71 | False             | True              |
|             0.2 |         0.875 |          12.958 |             186.642 |                      18 |        71 | False             | True              |
|             0.2 |         0.9   |          13.316 |             194.73  |                      18 |        71 | False             | True              |

## Notes
Profit/drawdown may be driven by a small number of excluded historical entries; tiny threshold changes are a critical overfit check.
No claim of production readiness; test forward, include funding/order-book execution/latency before live orders.
