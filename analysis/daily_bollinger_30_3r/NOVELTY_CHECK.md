# NOVELTY CHECK — Daily Bollinger(30,2), fixed 3R

Date: 2026-11-21. User-requested **external published strategy reproduction**, no fitted parameter search.

## Deterministic rules
- Venue/source: Delta Exchange India BTCUSD perpetual, genuine UTC 1m OHLCV from `data/delta_india/BTCUSD/1m`, aggregated into fully completed 00:00 UTC daily candles; no Binance spot data substituted.
- Signal at fully completed daily close: LONG when close > upper band SMA(close,30) + 2 * population_std(close,30); SHORT when close < lower band; bands include completed signal close. No separate crossover requirement.
- Wilder ATR14 (RMA of true range, starting with 14-SMA); LONG initial stop = signal low - 0.25*ATR14; SHORT = signal high + 0.25*ATR14.
- Entry = immediately following 1m OPEN, adverse 5 USD slippage on entry. Initial risk is entry to fixed stop; TP = entry +/- 3*risk. No trailing, BE, time-exit. Signal ignored unless its direction is actionable, one position total at a time (strict conservative restriction versus publisher's simultaneous directions).
- Intraminute exit: monitor genuine next 1m OHLC; same 1m TP/SL tie resolved STOP first; gap-through stops fill at worse open, not optimistic stop. Exit adverse 5 USD slippage.
- Risk model: USD notional limited to min(1% of cash equity / stop_fraction, 2x current equity); uses continuous BTC exposure (small-contract lot feasibility not established). Full taker fee 0.05% per side plus 18% GST. Funding: proxy from observed Delta 1h rate at 00:00/08:00/16:00 UTC, shifted to prior completed hour; no settlement ledger, report separately.
- No exchange L1, tick depth, market impact, liquidation simulation. Candle timestamp interpreted as OPEN in UTC.

## Closest earlier experiments / references
- `scripts/research_structure_rr_stage11.py`, `analysis/institutional_discovery_stage11_structure_rr/`: 5m sweep/inside-bar/range breakout; 1m fixed 3R exits. **Different signal** and structural stop (5m), not a daily Bollinger indicator.
- `scripts/research_mtf_swing_range_long_fixed3r.py` / `analysis/mtf_swing_range_fixed3r/`: 30m structure / 1m swing regime and fixed-price R, intraday. **Different signal.**
- `analysis/independent_stage25_hourly_trend/RESEARCH_REPORT.md` at `research/stage25-new-trend`: 1H momentum/Donchian/inside bar, atr stop, fixed 3R (1m replay). **Different timeframe and trigger.**
- `analysis/institutional_discovery_stage19_monthly_10pct/`, `analysis/institutional_discovery_stage23_broad_5m_monthly/`: intraday mean reversion/breakout; **different daily-Bollinger signal**.
- `codex/STRATEGY_NOVELTY_GATE.md` consulted. Default-branch GitHub code search of Bollinger, bb30 yielded no matching code.

## Novelty decision
**NEW — exact external daily Bollinger breakout reproduction.** No parameter tuning and no reuse of other stage output directories.

## Data and validation
- Monthly BTCUSD 1m manifest on main through 2026-11-19 UTC (Nov incomplete), 2025-01 through 2026-10 complete. Prior stage notes alleging Oct-31 2026 gap refer to older snapshot; validate current actual series afresh.
- 2025 is reporting/training reference, 2026 is a **previously research-exposed chronological check**, NOT pristine holdout; report per-month net returns including zero-trade months.
- Any result failing to exceed 30% win rate / positive net PF is still fully reported (no suppressing null).
- The published original tests BTCUSDT SPOT bars 2017-2026, includes 0.04% spread, and permits simultaneous side positions; this replication intentionally differs in venue and execution to reflect Delta India futures.
