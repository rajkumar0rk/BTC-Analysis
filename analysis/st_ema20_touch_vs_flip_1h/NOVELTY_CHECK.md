# Novelty gate — 1H BTCUSD EMA20 Touch vs Supertrend Flip entry

Date: 2026-11-22. **PARTIAL OVERLAP**, user-directed differential comparison, not a new indicator. Prior `research/st-ema20-touch-volume-volatility-grid-20261122` studies Touch with 1H volume/volatility; `research/st-ema20-reclaim-volume-volatility-grid-20261122` studies Reclaim, not an entry on the actual ST flip. `research/st-ema20-large-percent-profit-locks-20261122` provides the common 1m replay and initial 253-touch baseline. Other 15m ST flip / second green tests are a different timeframe or entry/exit construction.

## Comparison — predetermined choices
Use the same 2025-01-01 to 2026-11-20 1m Delta BTCUSD perpetual OHLCV, 1H ST(10,3), EMA20, no initial stop-loss, one trade per ST cycle, same exit signal on confirmed 1H opposite ST flip, same percent-based immediate profit locks in two hypothetical 1m paths, same 0.001 BTC, taker fee 0.05% each side ×18% GST, 5 BTC point slippage each side, $100 illustrative starting equity. No futures funding/liquidation/margin.

**Touch**: exact prior signal definition and next-hour 1m signal-high+0.5 long / signal-low-0.5 short breakout fill; use prior separately replayed ledger and recompute 1H volume and volatility features only on completed signal bar. Preserve same first selected entry per ST cycle, skipping rejected cycle. This reuses 1m execution ledger rather than re-simulating the same position.

**Flip-next-open**: Completed 1H bar changes ST side; enter at next 1m open (first minute of following 1H), no lookahead. User means green bullish flip / red bearish flip: trade in flip's new side. Profit lock monitoring begins on that 1m candle. No initial SL, exit on another opposite completed flip if first lock never activates.

**Flip-breakout**: Additional conservative timing sensitivity: after completed flip, enter only if price breaks that flip candle's high+0.5 long or low−0.5 short in the following 1H. No fill = no trade for that cycle. This helps distinguish immediate flip vs breakout order.

**Filtering** on completed entry signal hour: (A) OFF, (B) prior Touch-volume/volatility balanced filter = 1H volume <=2.5x average previous 20 complete 1H candles AND 1H ATR10 <=1.25% of signal close, (C) 1H volume 0.5–2.5x and ATR <=1.25% as stricter variant, (D) 1H volume >=1.25x and ATR<=1.75% as momentum variant. These settings are frozen BEFORE Flip backtest, not mined from Flip outcomes. Invalid indicators reject filtered entries and do not affect unfiltered.

**Exits**: 0.75% single, 1→2→5% ladder, 2→3→5% ladder, 5% single. All percentages from actual modeled entry fill, not fixed BTC points. Each immediately locks stop at attained percent within assumed 1m path.

Report BOTH OHLC path assumptions O→H→L→C and O→L→H→C separately, trade counts, wins and losses, net after fees, PF, realized max drawdown, 22 complete monthly net P&L in IST (exit month), 2025 vs Jan–Oct 2026 split, and explicit Nov 2026 partial. Do not re-optimize after seeing results. The prior Touch baseline and filtered ledger sums MUST exactly match verified 2026-11-22 results.

**Caveats:** No tick ordering, true L1 stop fills, spread, latency, funding, margin or liquidation. Filtered comparisons conditional on a prior selected Touch candidate, not a fresh end-to-end strategy optimization. No independent holdout; no live claims, no master merge.
