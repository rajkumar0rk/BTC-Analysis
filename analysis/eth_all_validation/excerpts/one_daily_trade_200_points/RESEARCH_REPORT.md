# One ETHUSD futures trade EVERY day — can it capture 200 points?

**Exact rule:** one entry on every complete America/New_York calendar day, 7 days/week. A target +200 points from that *one* trade. Both a raw +200 point BTC move and actual +200 net points after modeled fees are tested separately.
A day with a failed target still counts as a trade and a failed day. Never exclude weekends, down days, or unprofitable sessions. Each price-action rule contains a deterministic midday fallback so that each date receives one trade.

## Execution assumptions
- True Delta India ETHUSD perpetual 1m OHLCV, completed 5m price-action events or past-only closed 5/15/60/240 minute trend.
- Three protective **raw price-point** stops: 150/250/400. Three time-outs: 1h/3h/8h (capped at 23:59 New York to prevent overlapping next-day positions).
- Profit target either **gross200** BTC market move or **net200** (gross target enlarged using entry price to compensate expected entry/exit taker fees, 18% GST on fees, and $5 slippage each side).
- Same-minute TP+SL counts as SL. No lookahead. OHLCV stop/target fills approximate executable orders; funding, book spread beyond slippage, price jumps, liquidation and funding are not simulated.
- Entry direction may be long or short; one opening per NY date. Direction determined by past market movement or 5m structure. Fallback entry uses price data available before 12:05 NY.
- Test time-of-day rules and event-driven price action with a forced daily fallback separately; do not add their results together.

## Chronological selection
Training: 2025. Intermediate validation: Jan-Jun 2026. FINAL unseen holdout: July-Oct 2026.
Ranking and candidate selection use only first two periods. Many rules => heavy multiple-testing risk. A small positive holdout is not proof of robustness.

## Quality
{
  "calendar": "America/New_York includes DST",
  "full_ny_days": 685,
  "first_full_ny_day": "2025-01-01",
  "last_full_ny_day": "2026-11-16",
  "entry_rules": 88,
  "daily_entry_events": 60280,
  "months": 23,
  "source_bars": 987840,
  "first_utc": "2025-01-01 00:00:00+00:00",
  "last_utc": "2026-11-17 23:59:00+00:00",
  "zero_volume_minutes": 1887,
  "stop_points": [
    150,
    250,
    400
  ],
  "hold_minutes": [
    60,
    180,
    480
  ],
  "targets": [
    "gross200",
    "net200"
  ],
  "fee_model": "0.05% taker each side + GST18%; slippage 5 BTC points each side",
  "selection": "2025 training plus Jan-Jun 2026 validation; Jul-Oct 2026 reserved",
  "simulated_trades": 1085040,
  "compared_exit_combinations": 1584,
  "eligible_daily_rule_exit_combinations": 1584,
  "net200_both_earlier_periods_positive": 0,
  "min_daily_coverage": "One entry per full New York day per rule"
}

## Fixed example benchmark (pre-registered, no optimization)
At 09:35 NY, follow the prior completed 15min direction; require +200 NET, $250 raw stop, max 3h.
| rule                      | target   |   stop |   max_hold_min | period     |   days |   trades |   targets |   success_pct |   net200_days |   net200_pct |   profitable_days |   profitable_pct |   mean_net |   median_net |   cumulative_net |   mean_hold_min |
|:--------------------------|:---------|-------:|---------------:|:-----------|-------:|---------:|----------:|--------------:|--------------:|-------------:|------------------:|-----------------:|-----------:|-------------:|-----------------:|----------------:|
| clock_09:35_last15_follow | net200   |    250 |            180 | holdout    |    139 |      139 |         0 |           0   |             0 |          0   |                33 |            23.74 |     -15.39 |       -12.42 |         -2138.61 |          180    |
| clock_09:35_last15_follow | net200   |    250 |            180 | train      |    365 |      365 |         4 |           1.1 |             4 |          1.1 |               136 |            37.26 |     -13.57 |       -12.43 |         -4954.21 |          178.68 |
| clock_09:35_last15_follow | net200   |    250 |            180 | validation |    181 |      181 |         0 |           0   |             0 |          0   |                57 |            31.49 |     -11.96 |       -13.97 |         -2164.18 |          180    |

## Daily candidate results (selected before unseen holdout)
| rule                                           | target   |   stop |   max_hold_min |   days_train |   success_pct_train |   mean_net_train |   days_validation |   success_pct_validation |   mean_net_validation |   days_holdout |   success_pct_holdout |   mean_net_holdout |   selection_score |
|:-----------------------------------------------|:---------|-------:|---------------:|-------------:|--------------------:|-----------------:|------------------:|-------------------------:|----------------------:|---------------:|----------------------:|-------------------:|------------------:|
| clock_10:05_last240_follow                     | net200   |    150 |            480 |          365 |                3.29 |            -7.72 |               181 |                     1.1  |                 -6.74 |            139 |                  0.72 |             -12.16 |             -7.72 |
| clock_10:05_last240_follow                     | net200   |    250 |            480 |          365 |                3.29 |            -8    |               181 |                     1.1  |                 -6.74 |            139 |                  0.72 |             -11.83 |             -8    |
| first_opening_impulse_follow_else_1205         | net200   |    150 |            480 |          365 |                3.56 |            -8.42 |               181 |                     1.66 |                 -7.5  |            139 |                  0    |             -14.77 |             -8.42 |
| first_opening_strong_reversal_follow_else_1205 | net200   |    150 |            180 |          365 |                1.1  |            -8.79 |               181 |                     0    |                 -9    |            139 |                  0    |             -15.79 |             -9    |
| first_opening_strong_reversal_follow_else_1205 | net200   |    400 |            180 |          365 |                1.1  |            -9.01 |               181 |                     0    |                 -9    |            139 |                  0    |             -15.93 |             -9.01 |
| first_opening_strong_reversal_follow_else_1205 | net200   |    250 |            180 |          365 |                1.1  |            -9.07 |               181 |                     0    |                 -9    |            139 |                  0    |             -15.93 |             -9.07 |
| clock_10:05_last240_follow                     | net200   |    400 |            480 |          365 |                3.29 |            -9.14 |               181 |                     1.1  |                 -6.74 |            139 |                  0.72 |             -11.83 |             -9.14 |
| clock_06:05_last5_follow                       | net200   |    150 |            480 |          365 |                3.01 |            -7.69 |               181 |                     0.55 |                 -9.23 |            139 |                  0    |             -14.4  |             -9.23 |
| clock_06:05_last5_follow                       | net200   |    250 |            480 |          365 |                3.01 |            -8.9  |               181 |                     0.55 |                 -9.24 |            139 |                  0    |             -14.75 |             -9.24 |
| clock_06:05_last5_follow                       | net200   |    400 |            480 |          365 |                3.01 |            -9.19 |               181 |                     0.55 |                 -9.24 |            139 |                  0    |             -14.75 |             -9.24 |
| first_opening_24bar_break_follow_else_1205     | net200   |    150 |            480 |          365 |                4.11 |            -5.62 |               181 |                     0.55 |                 -9.57 |            139 |                  0.72 |             -10.87 |             -9.57 |
| clock_11:05_last5_follow                       | net200   |    150 |            480 |          365 |                3.01 |            -3.31 |               181 |                     0.55 |                 -9.68 |            139 |                  0.72 |              -4.68 |             -9.68 |
| clock_11:05_last5_follow                       | net200   |    250 |            480 |          365 |                3.01 |            -2.73 |               181 |                     0.55 |                 -9.7  |            139 |                  0.72 |              -4.68 |             -9.7  |
| clock_11:05_last5_follow                       | net200   |    400 |            480 |          365 |                3.01 |            -3.14 |               181 |                     0.55 |                 -9.7  |            139 |                  0.72 |              -4.68 |             -9.7  |
| first_opening_impulse_follow_else_1205         | net200   |    150 |            180 |          365 |                0.55 |            -9.43 |               181 |                     0    |                 -9.7  |            139 |                  0    |             -15.27 |             -9.7  |
| clock_12:05_last240_follow                     | net200   |    250 |            180 |          365 |                0    |            -6.92 |               181 |                     0.55 |                 -9.76 |            139 |                  0    |             -14.02 |             -9.76 |
| clock_12:05_last240_follow                     | net200   |    400 |            180 |          365 |                0    |            -6.92 |               181 |                     0.55 |                 -9.76 |            139 |                  0    |             -14.02 |             -9.76 |
| clock_08:35_last15_follow                      | net200   |    150 |            480 |          365 |                3.01 |            -9.12 |               181 |                     0.55 |                 -9.86 |            139 |                  0    |              -8.51 |             -9.86 |
| clock_09:35_last60_follow                      | net200   |    150 |            480 |          365 |                4.11 |            -5.56 |               181 |                     1.1  |                 -9.87 |            139 |                  0.72 |             -11.01 |             -9.87 |
| clock_12:05_last240_follow                     | net200   |    150 |            180 |          365 |                0    |            -7    |               181 |                     0.55 |                 -9.88 |            139 |                  0    |             -14.02 |             -9.88 |

## Interpretation
- The important metric is how often one daily trade NETS 200 points, alongside net expectancy and drawdown.
- It is mathematically impossible for gross TP=200 to produce net +200 if brokerage fees and slippage are positive.
- A 200 BTC-point price change is NOT $200 account profit: 0.001 BTC exposure yields about $0.20 gross.
- A guarantee of +200 every calendar day cannot be established from finite historical data. Any historically lucky strategy needs forward paper validation.

## Reproducible output
See one_entry_per_day_rules.csv; all_daily_rule_exit_summary.csv; ranked_daily_rules_preholdout.csv; preselected_daily_candidates.csv; daily_trade_ledger_selected.csv.
