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
  "full_ny_days": 668,
  "first_full_ny_day": "2025-01-01",
  "last_full_ny_day": "2026-10-30",
  "entry_rules": 88,
  "daily_entry_events": 58784,
  "months": 22,
  "source_bars": 963360,
  "first_utc": "2025-01-01 00:00:00+00:00",
  "last_utc": "2026-10-31 23:59:00+00:00",
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
  "simulated_trades": 1058112,
  "compared_exit_combinations": 1584,
  "eligible_daily_rule_exit_combinations": 1584,
  "net200_both_earlier_periods_positive": 0,
  "min_daily_coverage": "One entry per full New York day per rule"
}

## Fixed example benchmark (pre-registered, no optimization)
At 09:35 NY, follow the prior completed 15min direction; require +200 NET, $250 raw stop, max 3h.
| rule                      | target   |   stop |   max_hold_min | period     |   days |   trades |   targets |   success_pct |   net200_days |   net200_pct |   profitable_days |   profitable_pct |   mean_net |   median_net |   cumulative_net |   mean_hold_min |
|:--------------------------|:---------|-------:|---------------:|:-----------|-------:|---------:|----------:|--------------:|--------------:|-------------:|------------------:|-----------------:|-----------:|-------------:|-----------------:|----------------:|
| clock_09:35_last15_follow | net200   |    250 |            180 | holdout    |    122 |      122 |        51 |         41.8  |            51 |        41.8  |                54 |            44.26 |     -87.66 |      -248.73 |         -10695   |           41.97 |
| clock_09:35_last15_follow | net200   |    250 |            180 | train      |    365 |      365 |       159 |         43.56 |           159 |        43.56 |               162 |            44.38 |    -111.79 |      -320.31 |         -40803.8 |           16.28 |
| clock_09:35_last15_follow | net200   |    250 |            180 | validation |    181 |      181 |        98 |         54.14 |            98 |        54.14 |                99 |            54.7  |     -36.44 |       200    |          -6595.7 |           29.17 |

## Daily candidate results (selected before unseen holdout)
| rule                       | target   |   stop |   max_hold_min |   days_train |   success_pct_train |   mean_net_train |   days_validation |   success_pct_validation |   mean_net_validation |   days_holdout |   success_pct_holdout |   mean_net_holdout |   selection_score |
|:---------------------------|:---------|-------:|---------------:|-------------:|--------------------:|-----------------:|------------------:|-------------------------:|----------------------:|---------------:|----------------------:|-------------------:|------------------:|
| clock_11:05_last240_follow | net200   |    400 |            480 |          365 |               62.19 |           -68.55 |               181 |                    64.64 |                -32.83 |            122 |                 59.84 |             -40.47 |            -68.55 |
| clock_11:05_last240_follow | net200   |    400 |            180 |          365 |               60.27 |           -69.73 |               181 |                    56.91 |                -47.71 |            122 |                 54.1  |             -26.85 |            -69.73 |
| clock_10:05_last15_fade    | net200   |    250 |            180 |          365 |               49.86 |           -78.52 |               181 |                    48.07 |                -65.89 |            122 |                 42.62 |             -87.07 |            -78.52 |
| clock_10:05_last15_fade    | net200   |    400 |            180 |          365 |               59.18 |           -79.66 |               181 |                    56.35 |                -62.44 |            122 |                 48.36 |            -111.54 |            -79.66 |
| clock_11:05_last240_follow | net200   |    400 |             60 |          365 |               52.88 |           -80.26 |               181 |                    46.41 |                -57.56 |            122 |                 40.98 |             -39.24 |            -80.26 |
| clock_10:05_last15_fade    | net200   |    250 |            480 |          365 |               49.86 |           -81.05 |               181 |                    50.83 |                -60.14 |            122 |                 45.08 |             -83.09 |            -81.05 |
| clock_10:05_last15_fade    | net200   |    150 |            180 |          365 |               38.9  |           -81.45 |               181 |                    35.91 |                -73.8  |            122 |                 34.43 |             -75.38 |            -81.45 |
| clock_10:05_last15_fade    | net200   |    250 |             60 |          365 |               46.58 |           -81.66 |               181 |                    41.99 |                -63.53 |            122 |                 35.25 |             -88.39 |            -81.66 |
| clock_10:05_last15_fade    | net200   |    150 |            480 |          365 |               38.9  |           -82.03 |               181 |                    37.57 |                -69.97 |            122 |                 36.07 |             -72.03 |            -82.03 |
| clock_18:05_last60_follow  | net200   |    400 |             60 |          365 |               47.4  |           -64.01 |               181 |                    33.15 |                -82.7  |            122 |                 23.77 |             -86.47 |            -82.7  |
| clock_10:05_last15_fade    | net200   |    400 |             60 |          365 |               55.07 |           -83.64 |               181 |                    46.41 |                -64.5  |            122 |                 37.7  |            -110.11 |            -83.64 |
| clock_10:05_last15_fade    | net200   |    150 |             60 |          365 |               36.16 |           -84.33 |               181 |                    32.04 |                -75.25 |            122 |                 29.51 |             -78.18 |            -84.33 |
| clock_09:35_last240_fade   | net200   |    400 |             60 |          365 |               54.25 |           -84.98 |               181 |                    46.96 |                -77.73 |            122 |                 47.54 |             -49.62 |            -84.98 |
| clock_10:05_last15_fade    | net200   |    400 |            480 |          365 |               59.73 |           -85.58 |               181 |                    60.22 |                -64.46 |            122 |                 53.28 |             -98.04 |            -85.58 |
| clock_08:35_last15_fade    | net200   |    150 |            480 |          365 |               39.18 |           -80.31 |               181 |                    33.7  |                -86.08 |            122 |                 39.34 |             -57.74 |            -86.08 |
| clock_08:35_last5_fade     | net200   |    150 |            480 |          365 |               38.9  |           -82.45 |               181 |                    33.15 |                -86.2  |            122 |                 40.98 |             -51.01 |            -86.2  |
| clock_18:05_last60_follow  | net200   |    150 |             60 |          365 |               32.88 |           -86.63 |               181 |                    27.62 |                -66.69 |            122 |                 19.67 |             -86.43 |            -86.63 |
| clock_08:35_last15_fade    | net200   |    250 |             60 |          365 |               43.84 |           -84.1  |               181 |                    34.25 |                -87.1  |            122 |                 30.33 |             -89.42 |            -87.1  |
| clock_08:35_last15_fade    | net200   |    150 |            180 |          365 |               39.18 |           -78.64 |               181 |                    32.6  |                -88.06 |            122 |                 37.7  |             -58.87 |            -88.06 |
| clock_18:05_last60_follow  | net200   |    250 |             60 |          365 |               39.73 |           -88.29 |               181 |                    30.39 |                -80.66 |            122 |                 22.95 |             -82.59 |            -88.29 |

## Interpretation
- The important metric is how often one daily trade NETS 200 points, alongside net expectancy and drawdown.
- It is mathematically impossible for gross TP=200 to produce net +200 if brokerage fees and slippage are positive.
- A 200 BTC-point price change is NOT $200 account profit: 0.001 BTC exposure yields about $0.20 gross.
- A guarantee of +200 every calendar day cannot be established from finite historical data. Any historically lucky strategy needs forward paper validation.

## Reproducible output
See one_entry_per_day_rules.csv; all_daily_rule_exit_summary.csv; ranked_daily_rules_preholdout.csv; preselected_daily_candidates.csv; daily_trade_ledger_selected.csv.
