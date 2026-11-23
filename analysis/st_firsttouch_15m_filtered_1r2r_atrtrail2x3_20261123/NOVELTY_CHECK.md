# Preregistered: add ATR trailing to 15M filtered first EMA20 touch, preserve 1R / 2R TP

Date: November 23, 2026. Request: "ATR trailing stop 2× / 3× Add this to 15m" after discussion of 15M fixed 1R / 2R take profit and enabled 15M volume + volatility entry filters.

**Interpretation: ADD the trailing stop, do not remove the existing fixed TP.** Test 4 independent combinations: TP 1R & 2R, each with 2×ATR(14) and 3×ATR(14) trailing stop.

- Signal 15M, Supertrend Wilder ATR(10) factor3, EMA20; BTCUSD, ETHUSD.
- Entry first subsequent 15M EMA20 touch AFTER confirmed opposite ST flip; ignore flip candle, only one attempt per ST cycle, even if filters fail.
- Both 15M entry gates remain **ON**: previous fully CLOSED 15M volume >1.2×20-bar SMA volume AND previous fully CLOSED 15M Wilder ATR14 >20-bar SMA of ATR14.
- Last COMPLETED 15M ST line at entry defines R=side*(filled entry-ST line). R>0 required as in earlier 15M TP runs. TP=filled entry+side*(1 or 2)R.
- ATR trailing starts immediately: freeze distance = 2 or 3 × previous CLOSED 15M Wilder ATR14 at entry. LONG initial stop entry-distance; SHORT entry+distance; ratchet on favorable 1-minute intrabar price extremes only; never retreat. Monitor stop during first minute following entry as well, only after actual EMA entry instant. Favorable price reaching fixed TP wins ahead of a later stop; adverse stop before a later TP wins; intraminute ordering follows assumed path.
- Confirmed opposite 15M Supertrend flip exits at the first 1-minute OPEN of following 15M candle when no previous TP/trailing exit.
- Replay with both hypothetical O-H-L-C and O-L-H-C path assumptions per minute; unknown true tick path. Conservative adverse gap fill at opening price through trailing stop, favorable TP gap not improved beyond TP. No same-epoch reentry.
- 22 complete IST months Jan2025-Oct2026, same original SHA256-verified Delta India 1-minute OHLC; separate $1000 starting model equity each symbol × parameter combo; 1× dynamically sized notional, 0.05% taker each side +18% GST on fee, 0.02% adverse slippage each side.
- Outputs: report, monthly mark-to-market, full trade ledger, execution log, summary, SHA quality. No margin/liquidation/funding/orderbook/spread/latency; 2026 researched previously, not untouched OOS.
- Compare against original 15M filtered TP1R and TP2R without trailing, and against separate 1H research only with clear labels.

Novelty: PARTIAL OVERLAP, user explicitly asks incremental ATR trailing mechanism on the 15M strategy. Work only on branch; no master merge.
