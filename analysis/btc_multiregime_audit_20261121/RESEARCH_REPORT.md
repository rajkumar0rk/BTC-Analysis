# BTCUSD multi-regime classifier + causal strategy-selector correctness audit

## Distinction
Indicator-based regime labels can be checked for causal correctness and empirical *forward utility*, but not definitive factual correctness without independent ground-truth market labels. Selection correctness means decisions are based on past-only data; profitability is a separate measured question.

## Quality and no-repainting audit
~~~json
{
  "native_minutes": 992160,
  "total_hours": 16536,
  "eligible_hours": 16451,
  "warmup_hours": 85,
  "primary_states": 8,
  "disallowed_labels": [],
  "mutually_exclusive_primary_state": true,
  "label_and_validity_history_prefix_invariance": [
    {
      "cutoff": "2025-04-15T00:00:00Z",
      "historical_hours": 2496,
      "label_mismatches": 0,
      "validity_mismatches": 0
    },
    {
      "cutoff": "2025-12-15T00:00:00Z",
      "historical_hours": 8352,
      "label_mismatches": 0,
      "validity_mismatches": 0
    },
    {
      "cutoff": "2026-08-15T00:00:00Z",
      "historical_hours": 14184,
      "label_mismatches": 0,
      "validity_mismatches": 0
    }
  ],
  "history_revision_detected": false,
  "mixed_hours": 7743,
  "mixed_share_pct": 47.067,
  "all_hours_nonmixed_share_pct": 52.933,
  "one_hour_label_change_pct": 27.343,
  "four_hour_diagnostic_nonoverlapping_samples": 4111,
  "classifier_objective_ground_truth_accuracy_measurable": false,
  "ground_truth_explanation": "Regime names are deterministic technical proxies; independent manually labeled true market regimes are unavailable. Future results measure predictive utility, NOT actual state-label accuracy."
}
~~~

Classifier audit passed if history-prefix mismatch counts were zero. Markets can still change regime rapidly; labels are known only AFTER each 1H candle closes.

## Non-overlapping forward 4H diagnostics (NOT market-label accuracy)
| regime        |   sampled_nonoverlapping_4h |   average_next4h_net_ATR |   next4h_up_pct |   next4h_range_ATR |
|:--------------|----------------------------:|-------------------------:|----------------:|-------------------:|
| shock         |                         229 |                   0.1779 |           53.71 |              2.596 |
| breakout_up   |                          52 |                  -0.2408 |           34.62 |              2.189 |
| breakout_down |                          63 |                  -0.2606 |           55.56 |              2.651 |
| trend_up      |                         418 |                   0.0264 |           46.41 |              2.189 |
| trend_down    |                         460 |                  -0.014  |           55.43 |              2.181 |
| compression   |                         277 |                  -0.0004 |           53.07 |              2.148 |
| range         |                         639 |                  -0.0443 |           48.98 |              2.095 |
| mixed         |                        1973 |                  -0.0138 |           49.32 |              2.066 |

## Fixed monthly training-only strategy selection
For every new IST month after 6 months warmup, select among four UNCHANGED baselines for each regime using only the PREVIOUS six COMPLETE months' CLOSED trades; >=15, >=3 active months, PF on normalized net R >=1.15, mean net R >0.05 and last three-month total net R >0; otherwise skip trading that regime.
Selection does not know current month's results. A single exclusive-position account then trades the chosen strategy's future signals, with native 1M stop-first replay, 36/24/12h original timeouts, 0.5% stop-risk, 3x notional cap, hypothetical initial $10k equity, fees/GST/slippage and IST month-end flatten.

## Selector summary
~~~json
{
  "target_profitable_months": 22,
  "months_total": 22,
  "first_evaluation_month": "2025-07",
  "warmup_months": 6,
  "evaluation_months": 16,
  "months_profitable": 2,
  "months_losing": 12,
  "months_idle": 8,
  "evaluation_months_profitable": 2,
  "evaluation_months_losing": 12,
  "evaluation_months_idle": 2,
  "passes_22_of_22": false,
  "trades": 221,
  "wins": 68,
  "losses": 153,
  "win_rate_pct": 30.769,
  "net_account_return_pct": -24.0037,
  "net_account_pnl_usd": -2400.37,
  "ending_account_usd": 7599.63,
  "max_trade_close_drawdown_pct": 24.635,
  "profit_factor": 0.6763,
  "fee_gst_usd": 1386.46,
  "slippage_usd": 148.81,
  "gross_before_costs_usd": -865.1,
  "non_no_trade_choices": 29,
  "candidate_signal_hours": 6418,
  "selected_signal_hours": 401,
  "blocked_due_exclusive_position": 180,
  "actually_executed_trades": 221
}
~~~

## Count of regime choices by strategy
| regime        | strategy            |   size |
|:--------------|:--------------------|-------:|
| breakout_down | NO_TRADE            |     17 |
| breakout_down | donchian_breakout   |      5 |
| breakout_up   | NO_TRADE            |     22 |
| compression   | NO_TRADE            |     19 |
| compression   | trend_pullback      |      3 |
| mixed         | NO_TRADE            |     19 |
| mixed         | donchian_breakout   |      2 |
| mixed         | trend_pullback      |      1 |
| range         | NO_TRADE            |     19 |
| range         | failed_break_fade   |      1 |
| range         | trend_pullback      |      2 |
| shock         | NO_TRADE            |     12 |
| shock         | bollinger_reversion |      1 |
| shock         | donchian_breakout   |      5 |
| shock         | failed_break_fade   |      3 |
| shock         | trend_pullback      |      1 |
| trend_down    | NO_TRADE            |     21 |
| trend_down    | failed_break_fade   |      1 |
| trend_up      | NO_TRADE            |     18 |
| trend_up      | failed_break_fade   |      4 |

## Annual net account return
|   year |   months |   trades |   positive |   losing |   idle |   compounded_net_return_pct |
|-------:|---------:|---------:|-----------:|---------:|-------:|----------------------------:|
|   2025 |       12 |       78 |          0 |        5 |      7 |                    -10.1118 |
|   2026 |       10 |      143 |          2 |        7 |      1 |                    -15.4546 |

## Actual complete monthly returns including training-only idle months
| month_ist   |   trades |   wins |   losses |   net_return_pct |   net_pnl_usd |   gross_before_costs_usd |   fee_gst_usd |   slippage_usd |   end_equity_usd | status   |
|:------------|---------:|-------:|---------:|-----------------:|--------------:|-------------------------:|--------------:|---------------:|-----------------:|:---------|
| 2025-01     |        0 |      0 |        0 |         0        |          0    |                     0    |          0    |           0    |         10000    | No trade |
| 2025-02     |        0 |      0 |        0 |         0        |          0    |                     0    |          0    |           0    |         10000    | No trade |
| 2025-03     |        0 |      0 |        0 |         0        |          0    |                     0    |          0    |           0    |         10000    | No trade |
| 2025-04     |        0 |      0 |        0 |         0        |          0    |                     0    |          0    |           0    |         10000    | No trade |
| 2025-05     |        0 |      0 |        0 |         0        |          0    |                     0    |          0    |           0    |         10000    | No trade |
| 2025-06     |        0 |      0 |        0 |         0        |          0    |                     0    |          0    |           0    |         10000    | No trade |
| 2025-07     |        2 |      0 |        2 |        -1.22637  |       -122.64 |                   -99.68 |         21.34 |           1.62 |          9877.36 | Loss     |
| 2025-08     |        0 |      0 |        0 |         0        |          0    |                     0    |          0    |           0    |          9877.36 | No trade |
| 2025-09     |       12 |      3 |        9 |        -2.62677  |       -259.46 |                  -146.01 |        105.46 |           7.98 |          9617.91 | Loss     |
| 2025-10     |       18 |      8 |       10 |        -0.052227 |         -5.02 |                   152.04 |        146.35 |          10.72 |          9612.88 | Loss     |
| 2025-11     |       17 |      7 |       10 |        -0.136003 |        -13.07 |                    76.38 |         82.44 |           7.01 |          9599.81 | Loss     |
| 2025-12     |       29 |      5 |       24 |        -6.36465  |       -610.99 |                  -416.58 |        177.44 |          16.98 |          8988.82 | Loss     |
| 2026-01     |        2 |      0 |        2 |        -1.13181  |       -101.74 |                   -72.91 |         26.36 |           2.47 |          8887.08 | Loss     |
| 2026-02     |       28 |     10 |       18 |         0.792727 |         70.45 |                   174.42 |         92.52 |          11.45 |          8957.53 | Profit   |
| 2026-03     |       11 |      4 |        7 |        -0.226658 |        -20.3  |                    24.18 |         39.65 |           4.84 |          8937.23 | Loss     |
| 2026-04     |       21 |      9 |       12 |         2.57681  |        230.3  |                   354.91 |        111.8  |          12.82 |          9167.52 | Profit   |
| 2026-05     |       15 |      2 |       13 |        -3.62381  |       -332.21 |                  -207.35 |        112.52 |          12.35 |          8835.31 | Loss     |
| 2026-06     |       10 |      3 |        7 |        -2.54314  |       -224.69 |                  -161.11 |         56.14 |           7.45 |          8610.61 | Loss     |
| 2026-07     |       27 |     13 |       14 |        -2.03704  |       -175.4  |                    48.47 |        197.67 |          26.2  |          8435.21 | Loss     |
| 2026-08     |       23 |      3 |       20 |        -8.72317  |       -735.82 |                  -527.9  |        184.46 |          23.46 |          7699.4  | Loss     |
| 2026-09     |        6 |      1 |        5 |        -1.2958   |        -99.77 |                   -63.97 |         32.32 |           3.47 |          7599.63 | Loss     |
| 2026-10     |        0 |      0 |        0 |         0        |          0    |                     0    |          0    |           0    |          7599.63 | No trade |

## Limitations / correctness gates
- The selector is a causal research test, not evidence of optimal strategy choices. Four historical strategy families cannot guarantee all regimes have profitable trades.
- 2025–2026 histories already influenced the choice to research regime switching, so chronological walk-forward checks are not pristine independent holdouts.
- Primary regime classifier has mixed state; do not force assignment of a strategy when the past signal is weak.
- Assumed taker 0.05% each side plus GST 18%, adverse 5 BTC points slippage per leg. Historical spreads, realized funding payments, queue priority, depth, liquidation and actual contract rounding are not modeled.
- Drawdown sampled on completed trades, not an intratrade equity excursion. Paper/forward trading required before live usage.
- Target 22/22 includes no-trade months as failures. Rolling six-month training makes Jan–Jun 2025 idle; do not hide them in a headline claim.
- Shock/reversal/volatility are OHLCV-based proxies; do not imply institutional intent or liquidations from candles.
