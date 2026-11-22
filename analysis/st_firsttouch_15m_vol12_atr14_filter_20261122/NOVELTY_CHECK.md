# Preregistered differential — add volume and ATR volatility filters to 15M first-touch 2R/ST flip

Requested 2026-11-22. **No parameter tuning.** Direct baseline: `analysis/st_firsttouch_ema20_tp2r_stflip_1h15m_20261122/` in `research/st-firsttouch-ema20-tp2r-flip-1h15m-20261122` (15M BTC −93.54%, ETH −92.60 to −92.73%); only change is gating entry with two filters.

## Exact filters and anti-lookahead rule
- **Volume**: sum of exchange volume for the last *fully closed* 15M candle, `V[done]`, must be **strictly greater than 1.2 × SMA(V,20)[done]**. The volume average includes that most recently completed bar, not the in-progress candidate entry bar. No use of incomplete 15M volume and no use of future bars.
- **Volatility**: 15M Wilder **ATR(14)[done] > SMA(ATR(14),20)[done]**, strictly. ATR(14) seeded with SMA of first 14 true ranges and recursively smoothed, independent of **Supertrend(ATR10, multiplier3)**. Only closed 15M candles used.
- Both conditions must hold at the *first EMA20 touch* after a confirmed Supertrend direction flip. If either fails, **reject that trend cycle's first-touch entry**; don't promote a later touch to 'first' and don't enter again in the same cycle. A failed risk geometry check also rejects the cycle.
- Keep previous signal and execution rules unchanged: 15M first EMA20 touch, flip candle excluded, last closed 15M ST10/3 and EMA20, one entry per trend cycle, TP = 2×(entry execution to frozen completed ST line) in trend direction, no fixed stop, **only confirmed opposite 15M Supertrend flip** exits loss at next 15M candle's first 1m open, no line-touch exit, no profit lock, no trailing.
- Both BTCUSD and ETHUSD; 22 completed IST months Jan2025–Oct2026; execution via 1-minute OHLC with O-H-L-C vs O-L-H-C hypothetical in-minute paths. Same fees (0.05% taker each side, GST18% on fees), adverse slippage (0.02% each side), 1x notional on $1000 initial modeled equity, funding/spread/liquidation not modeled. 2026 prior-research exposed (not pristine OOS).

## Outputs
- Summary, monthly mark-to-market, compressed trade ledger, quality metadata and report for BTC and ETH under both 1m intrabar assumptions.
- Report entry events, excluded by volume, excluded by volatility, passed both, trades, win/loss, TP2R and confirmed ST flip exits, PF, 22-month net, positive/negative month counts, floating max DD, insolvency.
- Compare to unchanged 15M baseline. Do not claim improved performance before independently observing.
- This is a variation of earlier first-touch test, novelty gate **PARTIAL OVERLAP — user explicitly requested these two filters**.
