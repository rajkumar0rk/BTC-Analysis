# BTCUSD four-layer market-regime trading architecture: independently replayed 22-month 1M research

## What was built and what it is NOT
Four separate causal layers: **(1) last closed 1H+4H market-state observation → (2) predetermined strategy eligibility → (3) completed subsequent 15M directional confirmation → (4) independent stop-first native 1M exit with own $10k equity and one global position**. This experiment deliberately holds signals and exit rules fixed, comparing eligibility and confirmation ablations. Classification of past structure does not imply knowing the next price direction; no model or threshold was optimized against this run.

## Data, leakage and execution audits
~~~json
{
  "data": "Delta India native BTCUSD 1M, each source gzip SHA256 verified",
  "candles_native_1m": 992160,
  "source_partitions": 23,
  "complete_IST_months": 22,
  "first_utc": "2025-01-01 00:00:00+00:00",
  "last_utc": "2026-11-20 23:59:00+00:00",
  "full_1h_bars": 16536,
  "valid_current_1h_and_4h_states": 16337,
  "completed_4h_lookahead_violations": 0,
  "fifteen_minute_bars_verified_complete": true,
  "hourly_observation_no_repaint_prefixes": [
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
  "signal_hourly_decisions": 16536,
  "signals_with_state_strategy_eligibility": 1103,
  "signals_confirmed_by_first_future_15m": 513,
  "eligibility_confirmation_acceptance_pct": 46.51,
  "uncertain_current_state_share_pct": 58.187,
  "one_position_globally_per_model": true,
  "stop_target_uses_1m_conservative_stop_first": true,
  "fee_taker_each_side_plus_GST": 0.00059,
  "assumed_adverse_slippage_btc_price_points_each_leg": 5.0,
  "simulated_account_initial_usd": 10000.0,
  "stop_risk_frac_current_equity": 0.005,
  "max_notional_leverage": 3.0,
  "actual_funding_transfers_included": false,
  "historical_bid_ask_spread_available": false,
  "liquidation_and_margin_feasibility_modelled": false,
  "prospective_fresh_holdout": false,
  "after_cost_live_readiness": false
}
~~~

## Net after modeled taker fees, 18% GST and 5 BTC points slip per leg
| model                     |   candidate_events |   exclusive_position_rejections |   entry_unavailable |   executed_trades |   trades |   wins |   win_rate_pct |   profit_factor |   net_return_pct |   net_profit_usd |   ending_equity_usd |   max_trade_close_drawdown_pct |   fees_gst_usd |   slippage_usd |   profitable_months |   losing_months |   idle_months | passes_22_22   |
|:--------------------------|-------------------:|--------------------------------:|--------------------:|------------------:|---------:|-------:|---------------:|----------------:|-----------------:|-----------------:|--------------------:|-------------------------------:|---------------:|---------------:|--------------------:|----------------:|--------------:|:---------------|
| no_trade                  |                  0 |                               0 |                   0 |                 0 |        0 |      0 |          0     |        nan      |           0      |             0    |            10000    |                          0     |           0    |           0    |                   0 |               0 |            22 | False          |
| ungated_immediate         |               5776 |                            4547 |                   0 |              1229 |     1229 |    444 |         36.127 |          0.8167 |         -54.0446 |         -5404.46 |             4595.54 |                         55.08  |        6297.93 |         605.97 |                   6 |              16 |             0 | False          |
| regime_eligible_immediate |               1103 |                             564 |                   0 |               539 |      539 |    172 |         31.911 |          0.8159 |         -30.2622 |         -3026.22 |             6973.78 |                         31.558 |        3141.81 |         302.99 |                   7 |              15 |             0 | False          |
| four_layer_15m_confirmed  |                513 |                             176 |                   0 |               337 |      337 |    112 |         33.234 |          0.7996 |         -22.1561 |         -2215.61 |             7784.39 |                         24.335 |        2197.86 |         210.23 |                   9 |              13 |             0 | False          |

## 22 complete IST calendar months, actual compounded-account net percent
| month_ist   |   four_layer_15m_confirmed |   no_trade |   regime_eligible_immediate |   ungated_immediate |
|:------------|---------------------------:|-----------:|----------------------------:|--------------------:|
| 2025-01     |                      1.915 |          0 |                      -0.47  |              -6.779 |
| 2025-02     |                     -3.747 |          0 |                      -2.933 |              -0.555 |
| 2025-03     |                      2.814 |          0 |                      -0.085 |               3.997 |
| 2025-04     |                     -3.25  |          0 |                      -5.121 |              -2.436 |
| 2025-05     |                     -0.541 |          0 |                      -1.18  |              -4.448 |
| 2025-06     |                     -0.881 |          0 |                      -4.2   |              -9.728 |
| 2025-07     |                     -0.647 |          0 |                      -5.218 |             -12.266 |
| 2025-08     |                     -4.144 |          0 |                      -1.634 |              -3.211 |
| 2025-09     |                     -6.648 |          0 |                      -1.344 |              -8.863 |
| 2025-10     |                      1.036 |          0 |                       0.5   |               4.198 |
| 2025-11     |                      1.589 |          0 |                       2.62  |               2.553 |
| 2025-12     |                     -4.106 |          0 |                      -5.07  |              -7.219 |
| 2026-01     |                      1.945 |          0 |                       5.054 |               4.221 |
| 2026-02     |                      4.94  |          0 |                       0.737 |               5.059 |
| 2026-03     |                      1.466 |          0 |                       0.953 |              -3.348 |
| 2026-04     |                     -4.691 |          0 |                      -6.172 |              -9.056 |
| 2026-05     |                     -2.653 |          0 |                      -2.436 |              -9.335 |
| 2026-06     |                      2.265 |          0 |                       0.549 |               4.382 |
| 2026-07     |                     -5.707 |          0 |                      -0.583 |              -7.786 |
| 2026-08     |                     -1.862 |          0 |                       0.955 |              -1.611 |
| 2026-09     |                      0.836 |          0 |                      -5.231 |              -3.244 |
| 2026-10     |                     -3.777 |          0 |                      -4.512 |              -7.673 |

## Year-by-year account results
| model                     |   year |   months |   trades |   positive |   losing |   idle |   compounded_net_return_pct |
|:--------------------------|-------:|---------:|---------:|-----------:|---------:|-------:|----------------------------:|
| four_layer_15m_confirmed  |   2025 |       12 |      186 |          4 |        8 |      0 |                   -15.8211  |
| four_layer_15m_confirmed  |   2026 |       10 |      151 |          5 |        5 |      0 |                    -7.52558 |
| no_trade                  |   2025 |       12 |        0 |          0 |        0 |     12 |                     0       |
| no_trade                  |   2026 |       10 |        0 |          0 |        0 |     10 |                     0       |
| regime_eligible_immediate |   2025 |       12 |      293 |          2 |       10 |      0 |                   -21.9201  |
| regime_eligible_immediate |   2026 |       10 |      246 |          5 |        5 |      0 |                   -10.684   |
| ungated_immediate         |   2025 |       12 |      667 |          3 |        9 |      0 |                   -37.7488  |
| ungated_immediate         |   2026 |       10 |      562 |          3 |        7 |      0 |                   -26.1774  |

## Interpretation
- Market state is a description of already closed 1H+4H price data. MIXED/TRANSITION/COMPRESSION are deliberately abstentions, not predictive failures.
- First subsequent 15M candle is only inspected AFTER closing. Trade entry is its next minute OPEN, never the confirming candle's already-occurred high/low.
- The immediate and 15M-confirmed state-eligible variants have identical predefined 1H eligibility and identical 1M exit/position rules; the difference isolates 15M confirmation and entry latency.
- The ungated immediate reference uses same signal families and stop/TP per strategy with no MTF regime filter, NOT a separately tuned baseline.
- No-trade months FAIL the user's 22/22 net-positive-month target, just like losing months.
- This archive was previously investigated in many research iterations; it is NOT a pristine independent holdout. No funding cash flow, observed spread, order book, exchange contract rounding or liquidation model. These are hypothetical account results, not validated real-money trade fills.
- Time-based drawdown here samples trade closes, not intratrade mark-to-market equity. All capital/return figures should be interpreted with that limit.
- If both eligible versions lose, the correct finding is that adding layers has not created an edge. No live deployment or production change is authorized.
