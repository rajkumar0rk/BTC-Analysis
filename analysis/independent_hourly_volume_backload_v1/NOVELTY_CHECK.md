# Novelty check: completed-hour volume backloading
Decision: NEW (distinct intrahour temporal concentration), subject to empirical rejection.

## Rules
Use native 1m UTC bars. For each completed 60-minute UTC hour, compute volume share traded in minutes 45–59 divided by all 60 minutes; require share >= 0.40 or 0.55, and completed hourly absolute log(open/close) >= 0.30 ATR14/close. At the next minute's open, either continue or fade the completed hourly direction (mode +1/-1). Stop = 1.5 hourly ATR, target 2R, timeout 12h, one position at a time, risk 0.5% of NAV, notional capped at 3x. Stops before targets on ambiguous 1m candles, adverse fills, fees and GST.

## Nearest prior work
- scripts/research_time_day_volume_200.py and analysis/institutional_discovery_stage7_time_volume/: high volume, time-of-day and direction; NOT *within-hour* late-volume concentration conditional on displacement.
- scripts/research_anytime_volume_volatility_patterns.py: overall volume intensity and price behavior; NOT distribution of volume across four 15m hour quarters.
- research/independent-stage28-impact-shock: price impact shock; NOT timing of hourly traded volume.
- scripts/independent_range_close_divergence_v1.py on research/independent-range-close-divergence-20261119-v1: OHLC range/close divergence, no within-hour volume timing.
This tests temporal clustering as a proxy for late-arriving participation, NOT proven forced order flow.

## Quality and split
Original native BTC/ETH 1m SHA-256 partition checked, 2025-01 through 2026-10 UTC, 22 IST month-end NAV marks. ETH initial 2025 IST 5.5h unavailable, BTC 2026-10-31 partition hash validated by loader. BTC 2025 ONLY selects mode/share, frozen for ETH and BTC/ETH 2026; previously inspected 2026 is not blind OOS. 0.05% taker each side + 18% GST, BTC 5 points each side, ETH 0.02% each side. Funding, real spread, impact, liquidation, lots not modeled. This is exploratory research, no live trading.
