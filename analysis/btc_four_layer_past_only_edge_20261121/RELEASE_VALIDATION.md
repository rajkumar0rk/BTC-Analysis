# Past-only four-layer multi-regime improvements — independent release validation

**Backtest integrity: passed. Live approval: BLOCKED.** All 264 distinct pair/month/model decisions re-derived from prior completed shadow trades and checked before each month start. Separate account 1M trades and net cash outcomes reconciled; no entry before 15M confirmation. The historical 2025–2026 data was researched before this selector was conceived, so a genuinely untouched out-of-sample result is unavailable.

## Validation evidence
~~~json
{
  "research_validation": "PASS",
  "strategy_trading_release": "BLOCKED",
  "train_decisions_verified": 264,
  "first_hour_and_completed_15m_entry_causal": true,
  "monthly_selector_uses_only_prior_complete_trades": true,
  "past_only_monthly_qualification_recomputed": true,
  "all_model_trade_ledger_pnl_fees_slippage_reconciled": true,
  "all_variants_one_exclusive_position": true,
  "baseline_full_history_parity": true,
  "no_replay_smuggling_current_month_outcomes": true,
  "target_22_profitable_months_met": false,
  "original_after_cost_return_pct": -22.1561,
  "primary_6m_return_pct": 3.9621,
  "robustness_12m_return_pct": 8.9446,
  "2025_2026_was_previously_researched": true,
  "new_unseen_holdout_exists": false,
  "actual_bid_ask_spreads_known": false,
  "funding_cash_flows_known": false,
  "real_time_liquidation_feasibility_known": false,
  "confirmed_positive_after_extra_costs_not_assumed": true,
  "models": {
    "old_four_layer_baseline": {
      "trades": 337,
      "net_return_pct": -22.1561,
      "profitable_months": 9,
      "win_rate": 33.234,
      "pf": 0.7996,
      "trade_close_drawdown_pct": 24.335
    },
    "past6m_edge": {
      "trades": 55,
      "net_return_pct": 3.9621,
      "profitable_months": 7,
      "win_rate": 34.545,
      "pf": 1.203,
      "trade_close_drawdown_pct": 4.857
    },
    "past12m_robustness": {
      "trades": 51,
      "net_return_pct": 8.9446,
      "profitable_months": 7,
      "win_rate": 41.176,
      "pf": 1.5211,
      "trade_close_drawdown_pct": 4.857
    }
  },
  "reason": "Historical after-cost improvement on a previously explored archive is not a genuine new future holdout or 22/22 result. Keep all live trading disabled until prospective and real execution checks."
}
~~~

## Extra hypothetical spread-like roundtrip cost stress
These increments come ON TOP of the existing assumed taker fees/GST and 5 BTC points adverse slip on each leg. They are hypothetical; no observed exchange L1 bid/ask spread or funding cash settlements are available.
| model                   |   extra_roundtrip_bps |   net_account_return_pct |   extra_spread_like_cost_usd |   profitable_months |   losing_months |   zero_trade_months |
|:------------------------|----------------------:|-------------------------:|-----------------------------:|--------------------:|----------------:|--------------------:|
| old_four_layer_baseline |                     0 |                 -22.1561 |                         0    |                   9 |              13 |                   0 |
| old_four_layer_baseline |                     2 |                 -25.3287 |                       365.43 |                   9 |              13 |                   0 |
| old_four_layer_baseline |                     5 |                 -29.8477 |                       887.09 |                   9 |              13 |                   0 |
| old_four_layer_baseline |                    10 |                 -36.7818 |                      1690.53 |                   8 |              14 |                   0 |
| past6m_edge             |                     0 |                   3.9621 |                         0    |                   7 |               5 |                  10 |
| past6m_edge             |                     2 |                   3.4016 |                        55.07 |                   7 |               5 |                  10 |
| past6m_edge             |                     5 |                   2.5664 |                       137.12 |                   7 |               5 |                  10 |
| past6m_edge             |                    10 |                   1.189  |                       272.42 |                   7 |               5 |                  10 |
| past12m_robustness      |                     0 |                   8.9446 |                         0    |                   7 |               3 |                  12 |
| past12m_robustness      |                     2 |                   8.404  |                        53.15 |                   7 |               3 |                  12 |
| past12m_robustness      |                     5 |                   7.598  |                       132.38 |                   7 |               3 |                  12 |
| past12m_robustness      |                    10 |                   6.2676 |                       263.14 |                   7 |               3 |                  12 |

## Decision
The predeclared monthly 6M and 12M eligibility gate may show improvement over the all-eligible baseline, but zero-trade training months and negative months are not wins. Sample 2026 has been repeatedly inspected. Do NOT deploy or automatically promote a best-looking comparator after comparing their 2026 returns. Require independent forward testing plus actual funding, spreads, size/rounding and liquidation constraints.
