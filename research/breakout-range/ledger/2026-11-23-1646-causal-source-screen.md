# Breakout & Range — source and causal screening (2026-11-23, 16:46 IST)

Scope: source screening only. **No historical backtest executed; no new BTC/ETH P&L.** Existing Wavelet source baseline and verified 45129514038 are unchanged. Research branch only.

## Candidate BR-NEW-01 — Daniel Bachs Lobo 5-minute volume-max breakout
- Immutable source: https://github.com/danibachsl/Breakout_Strategy/blob/4cee938ca5dccf9b2679909e4d24e01f2a377b7b/breakout.py ; author Daniel Bachs Lobo; original 5m US equities, regular session 09:35–16:00, multiple tickers; no license file verified (do not copy upstream code).
- Exact signal: High >= rolling 20-bar high and volume > 1.5 * PRIOR 20-bar maximum volume => long; low <= rolling 20-bar low and same volume threshold => short. Original 20-bar ATR from prior completed bar; long exits when current low < prior close - prior ATR; short mirror; opposite signal may flip. Publisher's code prints portfolio CAGR/Sharpe/DD but provides no fixed audited BTC period, PF, trades or fees.
- Causality flaw: same-bar High and completed-bar Volume cannot be known at the first high touch. Original code marks position open without debiting fees or actual entry price and can use current bar low to trigger an ATR stop without intrabar ordering. 252*78 annualization assumes equity sessions, not BTC.
- Novelty: partial overlap with Stage 6–9 volume breakout and Stage23/24 structure; distinctive volume **above 1.5 times PRIOR 20-bar maximum**, rather than volume/SMA, requires differential comparison. Do not claim NEW until overlap verified. Adaptation to BTC 24/7 and completed 5m -> next 1m open is economically different and must be labeled adaptation.
- Gate: DEFER — license, closest prior code, original signal timing and fill adaptation unresolved.

## Candidate BR-NEW-02 — Group09 Opening Range Breakout
- Source pinned https://github.com/algotrade-education/Group09-BuyHighSellLow/tree/6cc057bda6fecd4eea37f2dc51d842d00ee35f13 ; original ORB 15 minutes, 15m resample, ATR14, 3 ATR target / 1.5 ATR stop, breakout buffer 0.5, max one trade/session, range 0.5–3 ATR, ADX20, volume filter, long-only default. Full execution and license require file-level verification.
- US market opening range is not a native 24/7 BTC session. Choosing 00:00 UTC (05:30 IST) is a new research hypothesis, not faithful reproduction. Do not transplant US equities results to BTC.
- Novelty: prior-day range, intraday box, Stage24 breakout overlap. DEFER until source session, gap, stop precedence and licensing confirmed.

## Candidate BR-NEW-03 — Nirmit Sachde vol_breakout
- Source pinned project https://github.com/NirmitSachde/algo-trader ; source discussion https://github.com/NirmitSachde/algo-trader/blob/main/docs/strategy_book.md . Original: US equities, first 30m 09:30–10:00 ET opening range, long/short with volume > opening-range average, VIX >18, 16:00 ET mandatory flat.
- Published OOS Sharpe ~0.28, max DD ~-16%, hit rate ~48%; not BTC evidence. Requires VIX and DST-correct US exchange calendar; a BTC-only OHLCV archive cannot reproduce the original filter. A BTC volatility substitute would invent a new strategy.
- Gate: NOT REPRODUCIBLE with current BTC-only archive; do not run or mislabel BTC adaptation as original.

## Critical execution audit of existing Wavelet runner (read-only)
- `scripts/breakout_range_wavelet_daily_replay.py` currently prints `source_parity_diagnostic.json` with `mismatch_count`, but does not assert it is zero. Thus completed workflow success alone **does not establish source parity**. Retrieve and inspect this exact artifact before describing Wavelet as source-faithful.
- Historical NAV excludes funding, L2 spread/impact, lot/tick and liquidation. Original source sizing 20x notional cap is not proof of realizable margin.
- Data coverage: authenticated 2026-10 UTC partition is complete; the novelty gate text asserting 1,440 missing October candles is stale and must not be used to invalidate actual archive.

## Next executable actions
1. Fetch completed Wavelet run 45129514038 artifact 14796804344 and read `source_parity_diagnostic.json`. If mismatch_count>0, mark source-fidelity failure, diagnose and rerun before promoting.
2. Check exact Stage23/24 volume-max semantics against BR-NEW-01, and source license. Only if novel, implement complete-bar 5m signal / next eligible 1m open, 1m stop-first/gap fills, fee/GST and sequential NAV with source baseline preserved.
3. Screen an independently defined fake-out/retest model instead of tuning Wavelet further. No live orders.
