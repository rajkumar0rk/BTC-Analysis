# M15 — momentum source triage (2026-11-22 IST)

Research only. No historical replay or profitability claim in this document. Source snapshots pinned by Git commits; all publisher metrics are unverified locally.

## A — Farhan Arshad, daily time-series momentum
- Source: https://github.com/farhanarshad00/crypto-momentum-backtest/blob/415045a1d1da78fae95f77bdbdd92f6ab10031fd/strategy.py ; commit 415045a1d1da78fae95f77bdbdd92f6ab10031fd; license not established (no license in repository metadata). Do not copy/relicense source.
- Original signal: daily returns; rolling 20-day mean minus rolling 120-day mean, divided by 120-day standard deviation, transformed with tanh; previous day's signal determines next day's exposure; original portfolio equal weights across assets. Publisher README claims Sharpe ~0.54 over 2,837 days; costs not specified in inspected code; trade count/PF/DD not provided.
- Novelty: potentially NEW **daily velocity differential** vs Stage25 hourly candle impulse, but continuous variable sizing and daily rebalancing require faithful position-size and cost accounting. Cannot faithfully claim original multi-asset portfolio using BTC alone. Candidate BTC sleeve is a clearly labeled adaptation, not publisher reproduction. Status: HOLD for source/license and exact daily turnover handling; test only if novelty gate confirms no equivalent Stage25 time-series momentum.

## B — Matias Jarnal, cross-sectional crypto relative momentum
- Source: https://github.com/matiasjarnal/crypto-momentum-strategy/tree/38a216a5dddf7b35908478273e4d6216bea712ab ; MIT repository license; source notebook and README.
- Publisher reports 35-asset long/short ranking on 10/20/60-day momentum, BTC regime, inverse-vol scaling, 20bps per trade, 2023-24 Sharpe 1.12 and +24.1% annualized; these are publisher assertions, not Delta reproduced results. Trade count/PF not established.
- Mechanism genuinely different from BTC-only directional momentum; however authentic historical multi-asset Delta OHLCV universe and consistent contracts unavailable in established BTC-only runner. BTC-only proxy would be **NOT REPRODUCIBLE**. Status: DATA BLOCKED, do not fake cross-section with BTC/ETH.

## C — Sahi Magupta, SMA20/50 + ROC14 + volume
- Source: https://github.com/sahimagupta/crypto-momentum-strategy/tree/7381fd9d5ce220c23fa8ad4308b8899c6888cb90 ; license not established in repo metadata.
- Reported rules: 20/50-day SMA bullish state, ROC14 positive, daily volume >= 0.8x volume SMA20; exit on SMA reversal (other exit details must be verified in source before reproduction). Original described as daily crypto trend plus momentum confirmation; reported trade count/PF/DD/costs not established.
- Novelty: SKIP; primarily persistent-direction SMA crossover, belongs trend-following family and overlaps previously tested crossover mechanisms.

## M14 inherited correctness finding (not repaired)
- `scripts/research_momentum_macd_rsi_m14.py` calculates `monthly_nav.csv` `trades_exited` with `trades.exit.str.startswith(m)`, where `exit` is UTC timestamps and `m` is IST month. At UTC/IST boundaries monthly trade counts can be misallocated. The NAV month-end boundary is IST-based and remains separate. A fix requires an authentic rerun, completed job and artifact verification before marking FIXED; do not silently edit a historical result or claim corrected monthly counts.
- M14 baseline remains an *engine approximation* (not source-faithful): 27 trades, -15.119442%, PF 0.472802; run 45004443283, artifact 14746894266.

## Throughput / next action
3 new source families screened; 0 new distinct historical replays, 0 variants, 1 concrete reporting issue identified but UNFIXED. Next eligible candidate should be a fully specified, licensed, BTC-compatible momentum source with fixed trade exits and low turnover; implement against existing authentic Delta runner and verify complete Actions artifacts. Never extrapolate publisher returns to Delta.
