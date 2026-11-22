# Profit-protected BTCUSD Supertrend EMA20 fixed-target sweep — novelty gate

Date: 2026-11-22

Decision: **PARTIAL OVERLAP — approved user-requested incremental exit differential**.

## Baseline and distinct hypothesis

We keep the prior source `research/st-ema20-fixed-tp-200-500-1000-20261122:scripts/backtest_supertrend_ema20_fixed_tp_1h.py` unchanged as reference. Prior results for 200 / 500 / 1000 fixed TP included no initial SL, no trailing, no profit protection, and only 1H Supertrend flip as fallback.

User asks to add profit protections. New hypothesis: once price moves favorably toward fixed TP, a post-activation ratcheted profit-lock stop can prevent a profitable move from becoming a Supertrend-reversal loss. Do not treat this as a new independent discovery; 200, 500, 1000 point levels and the presence of MFE in losing trades were selected after studying historical results.

## Frozen entries and account assumptions

1H Supertrend ATR10 factor3 and EMA20. Modes TOUCH, RECLAIM, COMBINED exactly as existing baseline; price breakout following completed 1H setup on 1m historical highs/lows, gap-aware plus 5 BTC price points fill slippage. One filled trade per Supertrend cycle, no overlapping positions. Long and short symmetric.

Data Delta Exchange India BTCUSD perpetual price OHLCV archives from Jan 2025 to Nov 20 2026. Revalidate 1m continuity and full 1H bars. $100 indicative starting capital, 0.001 BTC fixed quantity, 0.05% taker per side + 18% GST = 0.00059, 5 BTC price points of slippage per side. No funding, mark, liquidation, book or margin feasibility model.

## Exact exit comparison

For each fixed TP=200, 500 and 1000 BTCUSD price points and each entry mode:
- Compare two mutually exclusive profit-protection profiles:
  - **early_75_lock50**: upon a completed 1m bar reaching +75% of TP favorable excursion, set a protective stop to entry fill plus/minus +50% of TP. The stop is live starting at the **next 1m bar**, not retroactively.
  - **late_90_lock75**: upon a completed 1m bar reaching +90% of TP favorable excursion, set stop at entry fill plus/minus +75% of TP, live next 1m bar.
- Fixed TP still exits at exact entry-fill +/- TP price points, subject to 5 price points adverse exit slippage. If already holding a profit-lock stop and both TP and lock are hit within the same 1m bar, **fill protective stop first** to avoid unearned optimistic ordering. On stops gapping through protective price, fill at worse open. On TP gaps, do not credit positive improvement.
- If neither TP nor protective stop hits, exit only on confirmed 1H Supertrend flip at next minute open. If archive ends first, report separate unrealized position.
- No initial stop, no 1R protection, no general trailing stop, no timeout. Profit lock moves only once and only after favorable threshold (never relaxes).
- Do not use high/low from entry minute to activate profit lock or TP; intra-minute order ambiguous. All activation from subsequent minute, live on next minute.
- 18 scenarios = 3 entry modes × 3 TP values × 2 profit-lock profiles.
- Report win rate, gross/net/fees, count of TP/profit-lock/ST exits, maximum realized DD and adverse marked equity, 22 complete IST monthly results plus Nov partial and all trades. Book realized P&L in trade exit month, not entry month.
- No untouched holdout; no optimized threshold should be described as a verified edge.

## Closest previous work

- `research/st-ema20-fixed-tp-200-500-1000-20261122:analysis/ema20_st_fixed_tp_sweep_1h/` fixed targets with **no profit lock**.
- `research/st-ema20-reversal-only-20261122:analysis/ema20_st_reversal_only_1h/` reversal-only exits without targets.
- `research/ema20-supertrend-1h-touch-reclaim-1m-20261122:scripts/backtest_supertrend_ema20_1h.py` prior swing stops / 1.5R risk lock / 2R trailing, non-equivalent because risk stop existed.

The only changed parameter family is the post-profit, non-R target-proportional stop. These are exploratory in-sample scenarios and may overfit.

## Warning

Without a protective initial SL, a real leveraged futures position can be liquidated before reaching either the profit-protection activation or the reversal exit. A positive backtest number would not establish tradability or performance at the assumed capital.
