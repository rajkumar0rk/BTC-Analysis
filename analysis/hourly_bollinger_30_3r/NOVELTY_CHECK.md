# Novelty gate — 1H Bollinger(30,2), ATR14 stop, 3R

Date: 2026-11-21. Requested differential backtest relative to the reproducible daily Bollinger(30,2) 3R setup.

## Fixed strategy (no optimization)
- Data: genuine Delta Exchange India BTCUSD perpetual 1-minute candles, UTC timestamps with 1-minute OPEN labels, 2025-01-01 through 2026-11-19; complete 1h candles constructed from 60 consecutive 1-minute bars; never interpolate missing data.
- On the **completed 1H candle**: enter LONG if close > rolling SMA30(close) + 2*rolling population STD30(close); SHORT if close < SMA30 - 2*STD30. The closing candle is included in the band calculations, same as the daily study; every qualifying close is a signal, not only first crossover.
- Wilder ATR14 on 1H true range, seed from simple average of first 14 1H true ranges.
- LONG SL = signal 1H candle low - 0.25*ATR14; SHORT SL = signal 1H candle high + 0.25*ATR14.
- Entry at next 1-minute OPEN, assuming $5 adverse entry slippage. Risk = filled entry to fixed SL. TP = 3x initial risk. No trailing or maximum hold (same as daily study).
- Every minute SL / TP touch replay, pessimistic SL first for ambiguous simultaneous hit; gaps through stop filled at worse open. $5 adverse slippage on exit, 0.05% taker fee per side plus GST 18%. Funding modeled only using past hourly funding-rate proxy at 00:00, 08:00, 16:00 UTC (no settlement reconciliation).
- Two independent portfolio scenarios: strictly one open position; and overlapping signals with shared 2x notional exposure cap. Both target 1% initial stop-risk per trade and start with $10,000 equity. 1m continuous BTC quantity approximation; margin, exact lot size, L1 depth not modeled.
- Account monthly figures use IST, month-end equity includes estimated open-position mark-to-market and close costs. No forward leakage in signal formation.

## Closest known prior work
1. `scripts/research_daily_bollinger_30_3r.py`, `scripts/research_daily_bollinger_30_3r_concurrent.py`, `analysis/daily_bollinger_30_3r/`, branch `research/btc-daily-bb30-3r-20261121`. **Same indicator/exit thesis**; 1H bars are not economically equivalent to daily: 24x higher sampling, smaller per-signal ATR and stops, more signal events, sharply different futures fee-to-risk ratio and funding exposure. This is a deliberately controlled timeframe ablation, not a claim of a newly discovered trading edge.
2. `analysis/independent_stage25_hourly_trend/` at `research/stage25-new-trend`: 1H momentum, Donchian and inside-bar 3R, rather than 1H Bollinger(30,2) close breakout.
3. `scripts/research_structure_rr_stage11.py`: 5m structure signals, 1m 3R, rather than Bollinger-based hourly breakout.
4. `analysis/institutional_discovery_stage19_monthly_10pct`, Stage23: shorter timeframe entries and cost-aware research; not an exact reproduction of these 1H BB rules.
5. `codex/STRATEGY_NOVELTY_GATE.md`: reviewed. Code search for 'Bollinger' on default branch returned no exact match.

## Novelty decision
**PARTIAL OVERLAP — approved user-directed differential** comparing hourly vs daily fixed-parameter signals, with genuinely altered holding/risk economics. Keep identical execution costs and portfolio models for controlled comparison. Do not claim new strategy family.

## Evaluation
Use the full range 2025-01-01 through 2026-11-19, with 2025 and 2026 separately; prior research exposed both periods, so there is **no pristine holdout**. Do not tune based on results. Report trades, win %, PF net, realized closed P&L, mark-to-market account return and IST monthly table, including losing and flat months. Nov 2026 is partial. Audit current 1m archive rather than relying on older reports alleging Oct31 gap.
