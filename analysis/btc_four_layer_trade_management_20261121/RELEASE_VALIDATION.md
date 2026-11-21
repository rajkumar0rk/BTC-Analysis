# BTC 4-layer 1M exit improvements: independent release gate

**Research execution and all reconciliation checks passed; real-money trading remains BLOCKED.**

## Critical OHLC intrabar timing fixtures
~~~json
{
  "same_minute_activation_and_initial_stop": "PASS_STOP_FIRST",
  "next_minute_protected_stop": "PASS",
  "next_minute_atr_runner": "PASS",
  "runner_does_not_fill_removed_3R_target": "PASS"
}
~~~

## Net return and no-go decision
~~~json
{
  "research_integrity": "PASS",
  "real_money_trading": "BLOCKED",
  "synthetic_stop_first_next_bar_timing_checks": {
    "same_minute_activation_and_initial_stop": "PASS_STOP_FIRST",
    "next_minute_protected_stop": "PASS",
    "next_minute_atr_runner": "PASS",
    "runner_does_not_fill_removed_3R_target": "PASS"
  },
  "exact_6m_and_12m_baseline_replay_parity_verified": true,
  "entry_same_as_fully_closed_15m_confirmation": true,
  "all_five_models_months_and_cash_reconciled": true,
  "no_overlap_and_no_trailing_stop_loosening": true,
  "original_12m_net_return_pct": 8.9446,
  "protected_12m_net_return_pct": 9.207,
  "protected_12m_delta_percentage_points": 0.2624,
  "ATR_runner_12m_net_return_pct": 3.5734,
  "original_6m_net_return_pct": 3.9621,
  "protected_6m_net_return_pct": 4.8154,
  "protected_6m_delta_percentage_points": 0.8533,
  "profitable_22_of_22_calendar_months_achieved": false,
  "no_untouched_external_holdout": true,
  "realized_funding_historical_spreads_liquidation_not_modelled": true,
  "selected_exit_configuration_not_promoted": true,
  "reason": "Profit protection improved 22-month historical returns slightly but failed 22/22; research archive repeatedly examined; costs and live broker feasibility incomplete."
}
~~~

The 1.5R activation rule updates the stop ONLY at the end of the triggering 1M candle, effective the next minute. A same-minute stop and activation resolves to the pre-existing stop; it never retroactively captures a known high/low. Both baseline equity paths exactly matched published historical 51 and 55 trades.

The historically favorable exit alteration is an EXPLORATORY insight on an already researched historical dataset. It is not a pristine out-of-sample improvement. Both cases still have only seven positive months of 22; initial 2025 months are training-only. Keep no-live-trading decision until prospective months, actual order-book spread, funding settlement, margin and liquidation/contract feasibility are independently validated.
