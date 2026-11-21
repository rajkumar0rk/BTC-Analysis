# BTC four-layer multi-regime: strictly past-only after-cost eligibility improvement

## Hypothesis and no-hindsight control
The previous MTF regime -> strategy -> 15M confirmation -> independent native 1M exit lost 22.16% and earned only 9/22 positive IST months. Instead of deleting losers using hindsight, a **monthly past-only eligibility gate** checks each exact regime-strategy pair's CLOSED after-cost shadow trades in the previous 6 or 12 complete months. Models, parameters and alternatives were written to NOVELTY_CHECK.md BEFORE this test. No tuning or in-sample 'best' choice is authorized.

## Audited data and scenario limitations
~~~json
{
  "data": "Delta India native BTCUSD 1M, verified SHA256 + contiguity",
  "native_1m_candles": 992160,
  "source_partitions": 23,
  "all_IST_months": 22,
  "base_shadow_ledger_pnl_entry_exit_parity_verified": true,
  "previous_1H_4H_no_repaint_prefixes": [
    {
      "prefix_exclusive_utc": "2025-05-17T00:00:00Z",
      "hours": 3264,
      "revised_state_labels": 0,
      "revised_validity_flags": 0
    },
    {
      "prefix_exclusive_utc": "2025-12-19T00:00:00Z",
      "hours": 8448,
      "revised_state_labels": 0,
      "revised_validity_flags": 0
    },
    {
      "prefix_exclusive_utc": "2026-08-17T00:00:00Z",
      "hours": 14232,
      "revised_state_labels": 0,
      "revised_validity_flags": 0
    }
  ],
  "original_confirmed_signal_events": 513,
  "original_shadow_executed_trades": 337,
  "sample_model_count": 2,
  "sample_models_pre_registered_before_output": true,
  "training_on_prior_exited_shadow_trades_only": true,
  "training_window_at_month_open_only": true,
  "no_train_outcome_after_month_begin": true,
  "native_1m_stop_first_replay": true,
  "next_1m_open_after_15m_confirmation": true,
  "all_models_separate_compounded_account": true,
  "actual_spreads_funding_liquidation_and_rounding_missing": true,
  "globally_untouched_holdout_available": false,
  "live_trade_approved": false
}
~~~

## Full 22-month separate-account net comparison
| model                   |   candidate_events |   exclusive_position_rejections |   entry_unavailable |   executed_trades |   trades |   wins |   win_rate_pct |   profit_factor |   net_return_pct |   net_profit_usd |   ending_equity_usd |   max_trade_close_drawdown_pct |   fees_gst_usd |   slippage_usd |   profitable_months |   losing_months |   idle_months | passes_22_22   |
|:------------------------|-------------------:|--------------------------------:|--------------------:|------------------:|---------:|-------:|---------------:|----------------:|-----------------:|-----------------:|--------------------:|-------------------------------:|---------------:|---------------:|--------------------:|----------------:|--------------:|:---------------|
| old_four_layer_baseline |                513 |                             176 |                   0 |               337 |      337 |    112 |         33.234 |          0.7996 |         -22.1561 |         -2215.61 |             7784.39 |                         24.335 |        2197.86 |         210.23 |                   9 |              13 |             0 | False          |
| past6m_edge             |                 85 |                              30 |                   0 |                55 |       55 |     19 |         34.545 |          1.203  |           3.9621 |           396.21 |            10396.2  |                          4.857 |         325.3  |          36.28 |                   7 |               5 |            10 | False          |
| past12m_robustness      |                 80 |                              29 |                   0 |                51 |       51 |     21 |         41.176 |          1.5211 |           8.9446 |           894.46 |            10894.5  |                          4.857 |         313.71 |          36.19 |                   7 |               3 |            12 | False          |

## Net monthly account return % including all zero-trade warmup months
| month_ist   |   old_four_layer_baseline |   past12m_robustness |   past6m_edge |
|:------------|--------------------------:|---------------------:|--------------:|
| 2025-01     |                     1.915 |                0     |         0     |
| 2025-02     |                    -3.747 |                0     |         0     |
| 2025-03     |                     2.814 |                0     |         0     |
| 2025-04     |                    -3.25  |                0     |         0     |
| 2025-05     |                    -0.541 |                0     |         0     |
| 2025-06     |                    -0.881 |                0     |         0     |
| 2025-07     |                    -0.647 |                0     |         0     |
| 2025-08     |                    -4.144 |                0     |        -2.292 |
| 2025-09     |                    -6.648 |                0     |         0     |
| 2025-10     |                     1.036 |                0     |         0     |
| 2025-11     |                     1.589 |                0     |         0     |
| 2025-12     |                    -4.106 |                0     |        -1.092 |
| 2026-01     |                     1.945 |                2.518 |         1.23  |
| 2026-02     |                     4.94  |                4.224 |         4.224 |
| 2026-03     |                     1.466 |                3.322 |         3.322 |
| 2026-04     |                    -4.691 |               -3.15  |        -3.15  |
| 2026-05     |                    -2.653 |                1.326 |         1.326 |
| 2026-06     |                     2.265 |                1.166 |         1.166 |
| 2026-07     |                    -5.707 |               -1.342 |        -1.342 |
| 2026-08     |                    -1.862 |                1.686 |         1.686 |
| 2026-09     |                     0.836 |                1.446 |         1.446 |
| 2026-10     |                    -3.777 |               -2.331 |        -2.331 |

## Annual net results
| model                   |   year |   months |   trades |   profitable_months |   losing_months |   idle_months |   net_compounded_return_pct |
|:------------------------|-------:|---------:|---------:|--------------------:|----------------:|--------------:|----------------------------:|
| old_four_layer_baseline |   2025 |       12 |      186 |                   4 |               8 |             0 |                   -15.8211  |
| old_four_layer_baseline |   2026 |       10 |      151 |                   5 |               5 |             0 |                    -7.52558 |
| past6m_edge             |   2025 |       12 |       10 |                   0 |               2 |            10 |                    -3.35893 |
| past6m_edge             |   2026 |       10 |       45 |                   7 |               3 |             0 |                     7.57547 |
| past12m_robustness      |   2025 |       12 |        0 |                   0 |               0 |            12 |                     0       |
| past12m_robustness      |   2026 |       10 |       51 |                   7 |               3 |             0 |                     8.94464 |

## Trade attribution by pair
| strategy            | state                |   trades |   wins |   net_usd |   sum_net_R | model                   |
|:--------------------|:---------------------|---------:|-------:|----------:|------------:|:------------------------|
| range_fade          | range                |       66 |     21 | -1424.27  |     -31.682 | old_four_layer_baseline |
| shock_breakout      | shock                |       43 |     18 |   440.914 |      10.896 | old_four_layer_baseline |
| structured_breakout | breakout_down        |       94 |     35 |   591.183 |      13.405 | old_four_layer_baseline |
| structured_breakout | breakout_up          |      103 |     29 | -1364.88  |     -30.562 | old_four_layer_baseline |
| trend_pullback      | confirmed_trend_down |       15 |      4 |  -245.385 |      -5.363 | old_four_layer_baseline |
| trend_pullback      | confirmed_trend_up   |       16 |      5 |  -213.172 |      -4.931 | old_four_layer_baseline |
| shock_breakout      | shock                |       27 |      8 |  -151.954 |      -2.779 | past6m_edge             |
| structured_breakout | breakout_down        |       28 |     11 |   548.163 |      10.971 | past6m_edge             |
| shock_breakout      | shock                |       29 |     11 |   210.52  |       4.425 | past12m_robustness      |
| structured_breakout | breakout_down        |       22 |     10 |   683.945 |      13.134 | past12m_robustness      |

## Causal eligibility details
6M rule: >=8 fully closed shadow trades, >=3 distinct active past months, PF(net normalized R)>=1.10, total 6M netR>0 and last 3M netR>0. 12M robustness: >=16 trades, >=5 active months, same PF/netR criteria. Every decision is frozen at IST month open; no current-month results are read. Prior shadow account trades omit events blocked by other shadow positions, so training evidence may be selection-biased. No trade is preferable to evidence-free allocation but zero months fail the user's target.

## Decision
The new gated account must be judged by 22 independently replayed IST month outcomes, not by hindsight per-state performance of the original strategy. Even if one alternative has a positive backtest, the studied 2025–2026 period is not an externally untouched holdout; live trading remains BLOCKED. Historical L1 spreads, actual funding payments, exchange contract size, queue/impact and liquidation are unavailable.
