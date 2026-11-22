# Mean-reversion source screening — 2026-11-22 21:32 IST

Status: SOURCE TRIAGE ONLY. No new historical run, P&L, strategy implementation, or code fix verified this iteration. Existing MR003 run 45036174691 remains the latest successful branch replay (head 1656866d6234032a6d19d3a2bc1692807667efcd); MR003 rejected. This file is an append-only separate screening record, not a rewrite of the experiment ledger.

## Candidate A — KristijonasSim/trading-research, MeanReversion.py
- Source https://github.com/KristijonasSim/trading-research/blob/main/freqtrade/user_data/strategies/batchM15/MeanReversion.py ; exact inspected blob SHA 32c5971e638894e5bc0d7aa372f6f620c00c7d13. Original: 4h spot, 18 pairs. Publisher claims bear Oct2025-Jun2026 -5.3% and DD 7.77%; trade count/PF/costs not specified. NOT local BTC results.
- Entry long when RANGING regime, ADX 12..25, price within 15% EMA200, close below BB20 2std lower, RSI14 <32, volume > SMA20 volume. Stop -5%; ROI schedule 3% initially, 2% after 60m, 1% after 180m, 0.5% after 360m; no signal exit. Position size unspecified in source. Code imports regime_filter, which is not present alongside this source in batchM15; exact regime logic not recovered. No LICENSE at repository root was found. Candidate BLOCKED: missing dependency/verified license, and BB/RSI mean-reversion overlaps MR001/Stage19. Do not fabricate regime definition or backtest.

## Candidate B — almprmg/freqtrade_btc_bot
- Source lead https://github.com/almprmg/freqtrade_btc_bot (web indexed). Publisher describes BTC/USDT Binance spot 4h: RANGING when ADX14 <20 and ATR14 < ATR20-average*1.1, 3-bar whipsaw guard, RSI30/Stoch25 oversold and BB tolerance, 3% MR stop; trend regime is explicitly OUT OF SCOPE. Publisher no verified trades/PF/DD. GitHub connector repository lookup returned 404; exact executable rules and license not verified. NOT REPRODUCIBLE pending source access. Do not claim maker fills on Delta futures.

## Candidate C — A1-Systems-Integrators-LLC/A1SI-AITP
- Source lead https://freqle.org/strategy/73821eefab4c3207 ; original 1h spot, long BB lower breach, RSI<35, volume>1.5x20 SMA, ADX<30, exit middle band/RSI>65/tiered ROI, -4% fixed stop with custom stop. No independently confirmed performance or full execution semantics. GitHub repository API lookup 404, license and source commit not verified. Core BB/RSI signal is already researched. SKIP pending demonstrably novel differential and licensed source.

## Decision / next executable action
- No candidate passed source-fidelity, license, and novelty simultaneously; 0 distinct backtests, 0 variants, 0 verified fixes, 3 leads screened, 0 advanced. The accessible historical runner is not the blocker; candidate provenance and exact executable definitions are. Next iteration prioritize a materially different low-turnover, risk-capped mean-reversion mechanism with complete accessible licensed source; record novelty before replay. Do not repeat MR002 or MR003. Fee baseline remains 0.05% per side plus 18% GST, zero slippage; funding unmodeled.
