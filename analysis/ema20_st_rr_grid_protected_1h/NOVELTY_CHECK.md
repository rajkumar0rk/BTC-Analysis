# NOVELTY_CHECK — 12 point-scaled risk/reward configurations with profit protection

Date: 2026-11-22. Decision: **PARTIAL OVERLAP — approved differential for explicitly requested risk/reward grid**.

## Exact requested combinations

Interpret 1:1, 1:2, 1:3, 1:4, 2:2, 2:4, 2:6, 2:8, 3:3, 3:6, 3:9, 3:12 as risk:reward units with **1 unit=100 BTCUSD price points**:

- SL100 / TP100,200,300,400;
- SL200 / TP200,400,600,800;
- SL300 / TP300,600,900,1200.

Fixed stop is measured from actual entry fill; the trade enters only after a completed 1H EMA20 pullback/reclaim setup with confirming breakout on 1m. Long and short symmetric. Supertrend ATR10 factor3; EMA20. All entry conditions cloned from `research/st-ema20-tp-profit-protection-20261122:scripts/backtest_supertrend_ema20_fixed_tp_profit_lock_1h.py`. One filled trade per Supertrend cycle and one open position maximum. Three independent entry modes: touch, reclaim, combined.

## Exit experiment

- **Baseline:** fixed SL, fixed TP, confirmed opposite 1H Supertrend flip at next hourly open, whichever comes first. No profit lock.
- **Early lock:** 1m price reaches 75% of TP, then on the next minute ratchet stop to entry fill +50% of TP (LONG) or −50% (SHORT).
- **Late lock:** 1m price reaches 90% of TP, then on the next minute ratchet stop to entry fill +75% of TP (LONG) or −75% (SHORT).
- Profit lock only improves existing stop, never relaxes it. Stop before target on same 1m bar; if a stop is gapped at open use worse open, TP is filled at its level without positive gap improvement; charge 5 BTC price points slippage per side.
- Entry minute is ambiguous: apply conservative stop touch on entry minute, but do not claim same-minute TP or profit-lock activation (later minutes only).
- Early/later activation based on completed 1m high/low, protective stop goes live on following minute.
- 3 entry methods × 12 risk:reward × 3 protections (none/early/late) = **108 distinct scenarios**. Report counts, stop/TP/lock/flip reasons, fee-inclusive and gross PnL, monthly IST (booked at exit), win %, max drawdown and chronology, MAE/MFE where possible, and data quality.

## Previous closest experiments

- `research/st-ema20-tp-profit-protection-20261122:analysis/ema20_st_fixed_tp_protection_1h`: fixed TP 200/500/1000 with early/late lock and **no initial SL**. Changed economic exposure: **new fixed stop and 12 deliberately requested stop:target combinations**, not equivalent.
- `research/st-ema20-fixed-tp-200-500-1000-20261122:analysis/ema20_st_fixed_tp_sweep_1h`: fixed TP with Supertrend reversal exit, no stop or protective lock.
- `research/st-ema20-reversal-only-20261122:analysis/ema20_st_reversal_only_1h`: no target/stop.
- `research/ema20-supertrend-1h-touch-reclaim-1m-20261122:scripts/backtest_supertrend_ema20_1h.py`: different *structure-derived* initial SL and R-based dynamic trailing, not this fixed-point risk/reward grid.
- `research/st-ema20-fixed-3r-20261122:analysis/ema20_st_fixed_3r_20261122/NOVELTY_CHECK.md`: related 3R pre-registration, no completed grid results visible when checked.

## Account assumptions and limitations

Delta Exchange India BTCUSD 1m price OHLCV Jan 2025 through 20 Nov 2026, independently verify consecutive timestamps and 60 bars per hour. Fixed 0.001 BTC exposure; starting illustrative cash $100; taker fee 0.05% per side plus 18% GST = 0.00059; additional adverse 5 BTC price points per side slippage. Funding, bid/ask, mark price, exchange latency, leverage/cross-margin liquidation, and exchange position sizing not modeled. An initial stop may not prevent liquidation in leveraged crypto markets. Prior research has already inspected all months, so no clean out-of-sample validation; November is partial. Older novelty gate October gap caveat conflicts with updated verified archive—validate actual data and make no claims of completeness without code check.
