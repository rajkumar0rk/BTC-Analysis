# One BTCUSD futures trade EVERY day — can it capture 200 points?

**Exact rule:** one entry on every complete America/New_York calendar day, 7 days/week. A target +200 points from that *one* trade. Both a raw +200 point BTC move and actual +200 net points after modeled fees are tested separately.
A day with a failed target still counts as a trade and a failed day. Never exclude weekends, down days, or unprofitable sessions. Each price-action rule contains a deterministic midday fallback so that each date receives one trade.

## Execution assumptions
- True Delta India BTCUSD perpetual 1m OHLCV, completed 5m price-action events or past-only closed 5/15/60/240 minute trend.
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
  "full_ny_days": 654,
  "first_full_ny_day": "2025-01-01",
  "last_full_ny_day": "2026-10-16",
  "entry_rules": 88,
  "daily_entry_events": 57552,
  "months": 22,
  "source_bars": 943200,
  "first_utc": "2025-01-01 00:00:00+00:00",
  "last_utc": "2026-10-17 23:59:00+00:00",
  "zero_volume_minutes": 1819,
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
  "simulated_trades": 1035936,
  "compared_exit_combinations": 1584,
  "eligible_daily_rule_exit_combinations": 1584,
  "net200_both_earlier_periods_positive": 0,
  "min_daily_coverage": "One entry per full New York day per rule"
}

## Fixed example benchmark (pre-registered, no optimization)
At 09:35 NY, follow the prior completed 15min direction; require +200 NET, $250 raw stop, max 3h.
| rule                      | target   |   stop |   max_hold_min | period     |   days |   trades |   targets |   success_pct |   net200_days |   net200_pct |   profitable_days |   profitable_pct |   mean_net |   median_net |   cumulative_net |   mean_hold_min |
|:--------------------------|:---------|-------:|---------------:|:-----------|-------:|---------:|----------:|--------------:|--------------:|-------------:|------------------:|-----------------:|-----------:|-------------:|-----------------:|----------------:|
| clock_09:35_last15_follow | net200   |    250 |            180 | holdout    |    108 |      108 |        36 |         33.33 |            36 |        33.33 |                40 |            37.04 |    -125.38 |      -333    |         -13541.1 |           52.84 |
| clock_09:35_last15_follow | net200   |    250 |            180 | train      |    365 |      365 |       142 |         38.9  |           142 |        38.9  |               146 |            40    |    -141.95 |      -361.51 |         -51813.1 |           27.64 |
| clock_09:35_last15_follow | net200   |    250 |            180 | validation |    181 |      181 |        83 |         45.86 |            83 |        45.86 |                84 |            46.41 |     -88.43 |      -329.01 |         -16006.7 |           33.92 |

## Daily candidate results (selected before unseen holdout)
| rule                                       | target   |   stop |   max_hold_min |   days_train |   success_pct_train |   mean_net_train |   days_validation |   success_pct_validation |   mean_net_validation |   days_holdout |   success_pct_holdout |   mean_net_holdout |   selection_score |
|:-------------------------------------------|:---------|-------:|---------------:|-------------:|--------------------:|-----------------:|------------------:|-------------------------:|----------------------:|---------------:|----------------------:|-------------------:|------------------:|
| clock_14:05_last60_fade                    | net200   |    400 |            180 |          365 |               53.97 |           -91.12 |               181 |                    44.75 |                -76.38 |            108 |                 33.33 |             -66.75 |            -91.12 |
| clock_09:35_last240_fade                   | net200   |    250 |            480 |          365 |               48.22 |           -92.83 |               181 |                    49.17 |                -77.04 |            108 |                 44.44 |             -92.87 |            -92.83 |
| clock_09:35_last240_fade                   | net200   |    250 |            180 |          365 |               47.12 |           -93.13 |               181 |                    46.96 |                -72.29 |            108 |                 37.96 |             -97.88 |            -93.13 |
| clock_09:35_last240_fade                   | net200   |    250 |             60 |          365 |               41.64 |           -93.44 |               181 |                    38.12 |                -77.84 |            108 |                 35.19 |             -84.86 |            -93.44 |
| clock_14:05_last60_fade                    | net200   |    400 |            480 |          365 |               58.63 |           -88.21 |               181 |                    54.7  |                -96.17 |            108 |                 52.78 |             -64.49 |            -96.17 |
| clock_09:35_last60_fade                    | net200   |    250 |             60 |          365 |               41.1  |           -97.65 |               181 |                    35.91 |                -94.12 |            108 |                 33.33 |             -97.13 |            -97.65 |
| clock_09:35_last60_fade                    | net200   |    250 |            180 |          365 |               46.03 |           -98.06 |               181 |                    42.54 |                -94.93 |            108 |                 37.04 |            -100.08 |            -98.06 |
| clock_09:35_last5_fade                     | net200   |    250 |            180 |          365 |               46.3  |           -98.16 |               181 |                    45.86 |                -86.13 |            108 |                 38.89 |             -87.28 |            -98.16 |
| clock_09:35_last60_fade                    | net200   |    250 |            480 |          365 |               47.12 |           -98.17 |               181 |                    45.86 |                -94.85 |            108 |                 44.44 |             -93.41 |            -98.17 |
| clock_06:05_last5_follow                   | net200   |    400 |            180 |          365 |               47.4  |           -98.19 |               181 |                    48.07 |                -51.62 |            108 |                 37.96 |             -77.82 |            -98.19 |
| clock_03:05_last5_fade                     | net200   |    400 |            480 |          365 |               58.08 |           -98.26 |               181 |                    55.25 |                -83.79 |            108 |                 59.26 |             -48.28 |            -98.26 |
| clock_14:05_last60_fade                    | net200   |    400 |             60 |          365 |               39.18 |           -98.74 |               181 |                    27.07 |                -91.54 |            108 |                 12.04 |             -92.45 |            -98.74 |
| clock_09:35_last5_fade                     | net200   |    250 |            480 |          365 |               47.12 |           -99.1  |               181 |                    46.96 |                -89.59 |            108 |                 45.37 |             -87.63 |            -99.1  |
| clock_09:35_last15_fade                    | net200   |    250 |            180 |          365 |               46.58 |           -97.33 |               181 |                    41.99 |                -99.19 |            108 |                 38.89 |             -93.81 |            -99.19 |
| first_opening_24bar_sweep_follow_else_1205 | net200   |    400 |             60 |          365 |               49.04 |           -78.15 |               181 |                    41.44 |                -99.4  |            108 |                 34.26 |             -66.08 |            -99.4  |
| first_opening_24bar_sweep_follow_else_1205 | net200   |    150 |            180 |          365 |               36.16 |           -99.62 |               181 |                    32.6  |                -95.01 |            108 |                 29.63 |             -93.36 |            -99.62 |
| first_opening_24bar_sweep_follow_else_1205 | net200   |    150 |            480 |          365 |               37.53 |           -99.92 |               181 |                    33.7  |                -94.93 |            108 |                 32.41 |             -95.83 |            -99.92 |
| clock_14:05_last15_fade                    | net200   |    150 |             60 |          365 |               29.59 |          -100.04 |               181 |                    24.31 |                -84.95 |            108 |                  9.26 |            -118.34 |           -100.04 |
| clock_14:05_last60_fade                    | net200   |    150 |            180 |          365 |               35.07 |          -100.07 |               181 |                    29.28 |                -85.56 |            108 |                 26.85 |             -84.23 |           -100.07 |
| clock_14:05_last60_fade                    | net200   |    150 |            480 |          365 |               36.71 |          -101.06 |               181 |                    34.81 |                -90.2  |            108 |                 32.41 |             -89.33 |           -101.06 |

## Interpretation
- The important metric is how often one daily trade NETS 200 points, alongside net expectancy and drawdown.
- It is mathematically impossible for gross TP=200 to produce net +200 if brokerage fees and slippage are positive.
- A 200 BTC-point price change is NOT $200 account profit: 0.001 BTC exposure yields about $0.20 gross.
- A guarantee of +200 every calendar day cannot be established from finite historical data. Any historically lucky strategy needs forward paper validation.

## Reproducible output
See one_entry_per_day_rules.csv; all_daily_rule_exit_summary.csv; ranked_daily_rules_preholdout.csv; preselected_daily_candidates.csv; daily_trade_ledger_selected.csv.
