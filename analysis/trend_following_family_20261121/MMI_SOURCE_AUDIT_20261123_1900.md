# MMI trend-persistence source audit — 2026-11-23 19:00 IST

## Recovery and boundaries
Read codex/AGENTS.md and codex/STRATEGY_NOVELTY_GATE.md. Canonical GitHub Actions branch runs endpoint reports 30 runs; latest historical run 45131335895 succeeded on 371e291, but it is the already-rejected Kali-Uga baseline, not a new MMI replay. No third-party code executed. Only this trend-family branch is written.

## Pinned upstream
Creator: minggnim. GPL-3.0 repository: https://github.com/minggnim/crypto-strategy/tree/c43c6ae106133a52bca4561611359dce7232870a .
Exact implementation:
- https://github.com/minggnim/crypto-strategy/blob/c43c6ae106133a52bca4561611359dce7232870a/src/crypto_strategy/strategies/base.py
- https://github.com/minggnim/crypto-strategy/blob/c43c6ae106133a52bca4561611359dce7232870a/src/crypto_strategy/strategies/ma_strategy.py
- https://github.com/minggnim/crypto-strategy/blob/c43c6ae106133a52bca4561611359dce7232870a/README.md

Original advertised market: BTCUSDT/ETHUSDT, 1h/4h; no source-pinned published fixed sample return, trade count, PF, DD or realistic Delta India fees/GST established. Do not infer them.

## Actual rules recovered
@Strategy(name='sma', n1=20, n2=40): fast MA crossing above slow MA gives LONG entry, reverse crossing exits; default strategy is long-only. Optional filter @Filter(timeperiod=20) computes:
median_t = rolling_median(close, 20)_t
p1_t = close_t > median_t
p2_t = close_(t-1) > median_t  (NOTE: **current** median, not median_(t-1))
mmi_t = rolling_mean(int(p1_t AND p2_t), 20)
pass_t = mmi_t >= 0.5.
Thus this is NOT the conventional Market Meanness Index; it measures consecutive closes above a current rolling median. It can preferentially admit sustained upward regimes but its name must not be mistaken for a canonical Hurst/MMI measure. It uses completed current bar only and must execute no earlier than next minute open.

Grid search is not a single immutable strategy: MA windows 30..290 step 10, MMI periods 10..45 step 5; source's default decorator 20/40/20 exists but published optimization procedure chooses different settings by Sharpe. Optional stops are a separate grid 0.1..0.55 step 0.05. No complete fixed optimized output or original costs found. No right to invent an 'original winning' configuration.

## Novelty and disposition
Closest prior art: codex/STRATEGY_NOVELTY_GATE.md Stage13/25 multi-timeframe trend/MA, and prior family EMA/ADX/MA screens. A long-only SMA cross with above-median persistence is a PARTIAL OVERLAP. Distinct conditional persistence filter is testable as a *new adaptation*, but no frozen creator-selected baseline with trustworthy cost/fill assumptions is available. **Decision SKIP as source-faithful published winning strategy; no backtest authorized under source fidelity requirement.** Do not optimize 2026 or relabel the noncanonical MMI as an independently validated signal.

## Causal concerns and disproof
Source checks crossovers on completed bar; any Delta replay must use next 1m open, stop-first minute fill, both sides fees 0.05% plus GST18%, NAV reconciliation, 2025-only discovery, then frozen 2026/ETH. Conventional MMI identity is not supported by the implementation. Creator's result period, PF, drawdown, trade count, fees are unavailable, so no local profitability inference.

## Work units and next action
1. Read exact fixed entry/exit code and confirmed nonstandard MMI formula.
2. Audited parameter grid and absence of fixed published optimized settings.
3. Compared novelty against existing trend and cross-family gates; rejected source-faithful reproduction without inventing settings.
New distinct historical backtests 0; variants 0; verified P&L 0. Blocker is candidate eligibility, not historical data runner. Next: screen a DIFFERENT complete, lower-turnover source with immutable settings; do not spend another session tuning this wrapper. No main/master, VPS, live trading, or other-family mutation.
