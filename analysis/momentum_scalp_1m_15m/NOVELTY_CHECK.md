# Momentum scalping 1M/15M — novelty decision (2026-11-21)

**Decision: PARTIAL OVERLAP — approved differential for this explicitly requested fixed-rule test.** This is an incremental hypothesis, not a novel core family.

## Fixed, causal hypothesis

BTCUSD Delta India futures, native UTC 1-minute OHLCV, entire archive January 2025 to November 20, 2026. Long on *closed* one-minute bar: last complete 15-minute EMA(20) > EMA(50), Wilder RSI(14) > 55, signal-minute volume > 1.5 times mean of *preceding* 20 completed 1-minute candle volumes, signal close > high of the preceding 10 completed 1-minute candles. Short mirrors conditions (EMA20 < EMA50, RSI < 45, close below preceding 10 lows). Entry next minute OPEN (not same signal close). One open trade across both directions. Initial stop 1.0 times Wilder ATR(14) measured at signal close; gross target 2.0 times stop distance. Stop-first for ambiguous 1m OHLC, worse-than-stop gap fills; exit after 60 one-minute bars or at complete IST monthly boundary. No hindsight/trailing or retuning. No entries spanning missing source candle gaps. One time-in-market at once; no Saturday/Sunday restrictions.

Execution: reference next open plus adverse 5 USD per BTC per side, 0.05% taker per side + 18% GST. Fees charged on both executed notional legs. Compounded 1x notional/equity sizing for monthly net account returns. No funding, bid/ask reconstruction, liquidations or order book impact. Reject missing or corrupt input; never fill missing candles. Count no-trade months as 0%; November 2026 incomplete.

## Earlier work — economic comparison

- `scripts/research_every_candle_200.py`, `analysis/institutional_discovery_stage6_every_candle_200/RESEARCH_REPORT.md`: 1m 20-candle acceptance breakout with volume >=1.25 and fixed 200/100 point exits. Shares breakout/volume causal family. **Differential**: fixed 10m breakout crossed with 15m EMA20/50 trend + RSI regime, ATR-scaled 1:2 exits and 60m time limit.
- `scripts/research_time_day_volume_200.py`, `analysis/institutional_discovery_stage7_time_volume/RESEARCH_REPORT.md`: 1m high-volume shock and time/weekday stratifications with fixed-point horizons. **Differential**: joint causal trend + RSI + local breakout, not standalone time or volume event.
- `analysis/institutional_discovery_stage24_structure_monthly10/RESEARCH_REPORT.md` on `research/stage24-monthly10`: 15m closed-bar squeezes, retests and structural breakouts with optional 1h filter. **Differential**: 1m signal/entry and independent 15m EMA regime, different signal/stop/hold.
- `analysis/independent_stage25_hourly_trend/RESEARCH_REPORT.md` on `research/stage25-new-trend`: 1H momentum, breakout, inside-bar and optional 4H trend. **Differential**: 1m breakout and 15m EMA/RSI filter with 1m execution.

## Validation / prior-exposure caveat

2025 and 2026 were already examined in project research, so the chronological 2025 vs 2026 comparison is a **seen historical recheck**, not an untouched holdout. Do not tune and imply forward performance. Report all 22 complete calendar months Jan 2025–Oct 2026 in IST, plus Nov 2026 as partial. Historical reports stated a 1,440-minute 2026-10-31 gap; current `data/delta_india/BTCUSD/1m/manifest.json` claims 0 gaps. Recompute gap integrity from actual files; do not resolve discrepancy by guessing.

## Novelty status

Run exactly ONE predeclared 1m configuration with monthly account PnL, net fees, win/loss/trade counts and drawdown. Do not search parameter combinations or claim that a profitable month implies a tradable edge.
