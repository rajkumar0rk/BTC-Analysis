# Novelty assessment — volume-normalized price impact residual (2026-11-19)

## Falsifiable mechanism
High hourly price displacement relative to reported traded volume may indicate temporarily thin liquidity, price impact, or a volatility jump. The test cannot identify institutional actors, aggressor side, liquidations, or actual depth from OHLCV; no such claim is made. If the impact event has a systematic continuation/reversal tendency, next-hour returns should compensate realistic execution costs. Matched event-free controls and depth/flow data would be needed before attribution.

## Distinction from existing branches
- `independent-vwap-twap-dislocation`: within-hour volume-weighted vs time-weighted *price level*, not return-per-unit-volume relative to lagged baseline.
- `independent-hourly-volume-backload`: intrahour temporal volume concentration, not price displacement per normalized volume.
- `independent-bipower-jump-fade`: realized-minus-bipower jump variance, no traded-volume normalization.
- Other prior volatility shock / trend efficiency branches may correlate strongly; results must not be claimed fully independent until empirical event overlap is measured.

## Frozen test
For each completed UTC hour, compute abs(log close/previous close) / sqrt(hourly volume / strictly lagged 48-hour median volume). Divide by strictly lagged 48-hour median of that impact proxy. Trigger at ratios 2 or 3; trade continuation or reversal of completed-hour return from the next 1m open. 1.5x hourly ATR stop, 2R target, 12h maximum hold; 1m stop-first execution, 0.5% equity risk, 3x notional cap. BTC 2025 only selects the configuration; same dimensionless rules and risk are frozen for BTC 2026 and ETH 2025–Oct 2026. No November performance. Fees 0.05% per side +18% GST, adverse BTC slip 5 points/side, ETH 0.02%/side. Funding, actual spreads, impact, margin and liquidation unmodeled. Data loader validates native partition SHA-256 and continuous minutes. 2026 is research-exposed, not blind OOS.

## Caveats
No pretrade book depth or matched control in this initial test; if the strategy looks compelling, these are mandatory before any deployment. Monthly PF uses realized exit-month net PnL; NAV returns mark open positions at IST month boundaries.
