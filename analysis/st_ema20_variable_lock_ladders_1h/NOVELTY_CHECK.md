# NOVELTY CHECK — BTCUSD EMA20/Supertrend variable stepped profit-lock ladders
**Decision: PARTIAL OVERLAP — approved user-requested exit differential.** Date 2026-11-22.

## User's exact five requested ladders
- 100 -> 200 -> 400 -> 800
- 100 -> 200 -> 300 -> 400 -> 500
- 100 -> 300 -> 600 -> 900
- 100 -> 400 -> 800
- 100 -> 500 -> 1000

Also explore 9 pre-specified additional irregular/accelerating/progressive ladders:
(100,200,500,1000), (100,300,500,700,1000), (100,200,400,600,1000), (100,250,500,1000), (100,400,800,1600), (100,500,1000,2000), (100,300,600,1200,2400), (100,150,200,300,500,800), (100,200,300,500,800,1300). All are BTCUSD price points, NOT dollars of PnL and not trade sizes.

## Explicit semantic ambiguity / two prospective interpretations
A sequence describes **profit milestones** and the associated protective lock:
1. **direct (aggressive):** after a full 1m candle trades up to (or through) favorable level L, the protective stop is raised to **entry +/- L** and becomes live starting the next 1m candle. If price has already reversed through that stop by then, fill at worse next-minute open (never claim impossible price). Example +100 reached -> lock +100; +200 reached -> lock +200.
2. **behind (conservative / giveback buffer):** first +100 is a checkpoint; when the second rung +200 is observed, protective stop moves to +100; on third rung +400, moves to +200; fourth rung +800, moves to +400. Lock starts only at second milestone. **This was the interpretation stated in user-visible pre-run plan**. Explicit side-by-side comparison prevents hiding the ambiguity or guessing a preferred interpretation.

Ladders continue beyond their last listed rung using last observed gap (or multiplicative 2x if every consecutive rung doubled), up to maximum price excursion >25,000; no cap and no fixed TP in this experiment. Lock only ratchets toward profit. No initial SL, no R-based protection, no separate TP or time exit.

If the active stop is touched, exit at active stop or worse minute open gap, subtract adverse 5 BTCUSD price points slippage. If a new rung is crossed in a minute, its updated lock starts **next minute**, never intra-minute or earlier. Exclude entry minute from favorable movement triggering locks. The only fallback exit is the next 1m open after completed 1H Supertrend reversal.

## Frozen entry, execution and accounting
Identical to `research/st-ema20-100pt-step-lock-20261122:scripts/backtest_supertrend_ema20_100pt_step_lock.py`: 1H Supertrend ATR10 mult3 + EMA20, completed 1H touch/reclaim or combined; breakout above last 1H high+0.5 for long or below low−0.5 for short during next 1H; gap-aware stop entry with 5-point adverse slippage. One filled trade per Supertrend cycle, no concurrent positions. Historical Delta India BTCUSD perpetual 1m OHLCV 2025-01-01 through 2026-11-20. Validate continuity and 60 completed 1m candles per hour.

$100 illustrative starting cash, fixed 0.001 BTC, 0.05% taker per side + GST18% (0.00059 per side) and 5 BTCUSD price points of adverse slippage per side. Use fully fee-inclusive P&L, realized account equity/monthly P&L by IST exit month and correct profit factor/win rates; mark open archive-end trades separately.

## Closest prior work
- `research/st-ema20-100pt-step-lock-20261122:analysis/st_ema20_step_lock_100_1h/` tested **strict +100 BTC point increments for lock and activation**, first lock at +150/+200/+300; did not test nonuniform user-requested ladders.
- `research/st-ema20-tp-profit-protection-20261122:analysis/ema20_st_fixed_tp_protection_1h/` tested **one-off** profit lock at TP-dependent activation, with fixed 200/500/1000 TP.
- `research/st-ema20-rr-grid-profit-protected-20261122:analysis/ema20_st_rr_grid_protected_1h/` tested initial SL100/200/300 vs fixed TP, not this no-initial-stop variable trailing profit lock.
- `research/st-ema20-reversal-only-20261122:analysis/ema20_st_reversal_only_1h/` tested Supertrend reversal-only exits, no lock.

## Validation and limitations
14 ladders × 2 explicit interpretations × 3 entry modes = **84 scenarios**, no hindsight optimization on future candles. 2025 / 2026 historical months already researched, so this is exploratory, NOT an untouched holdout; November 2026 partial. Revalidate October-minute continuity using archive (older global novelty note claimed a missing day before archive repair). Neither fees nor future funding nor liquidation is guaranteed; price OHLC are not mark price, trade ticks, bid/ask, exchange fills or order book. With NO initial SL, large drawdown and liquidation before any lock are possible. No promise of live profitability or risk safety.
