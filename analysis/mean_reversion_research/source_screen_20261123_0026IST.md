# Mean reversion source screen — 2026-11-23 00:26 IST

This is a READ-ONLY source/novelty gate; NOT a new historical backtest. Source URLs pinned where possible. No trading/deployment.

## A. vaultik/algo-trading-system — DUPLICATE, SKIP
- Source: https://github.com/vaultik/algo-trading-system/tree/7f9bcd24d0e1cf7258699f4835ecd80dcb684a84 ; MIT; original Bybit 5m, 24h rolling VWAP z-score crossback at ±3 with RVOL >=2.5, TP1 VWAP ±1SD / TP2 VWAP, frozen SD stop, time stop; 3x published leverage.
- Publisher paper test Mar7–Apr5 2026: 23 completed positions, -2.04% account PnL, max DD -2.72%, win rate 30.4%; six altcoins, NOT BTC Delta. Its WFO table approves TON/LTC; no BTC return claim.
- Exact same source commit and core mechanism ALREADY tested as MR002, recorded in analysis/mean_reversion_research/MR002/NOVELTY_CHECK.md. Completed run 44911975169: 204 BTC trades, -30.5503268% NAV, max DD 33.5514%, 6/22 positive months. No duplicate run.

## B. ojeology/mean-reversion-vwap-lab — NOT ELIGIBLE
- Source: https://github.com/ojeology/mean-reversion-vwap-lab/tree/5ae2853d729b6761d4be3c2ccb7602beb32665cf ; author Ojeology. No LICENSE in root tree; license unverified, so do not copy code.
- MEXC 1m, 13 altcoins excluding BTC: lower VWAP-2SD wick touch and close reclaim, green body >0.5 ATR, RSI<40; mirrored short RSI>60; next candle open. Stops and profit targets per-pair optimized, trading hours excluded; no single frozen BTC stop/target specification in README.
- Publisher E14 30-day IS +$261.94 PF 2.013, OOS +$18.05, 44–47% OOS win rate; NOT a BTC performance claim. Strong asset transfer and missing license/fully frozen settings: NOT REPRODUCIBLE as BTC source-faithful baseline. Possible novelty is session-VWAP wick reclaim vs MR002 rolling-VWAP z crossback, but must pass Stage19 sweep overlap and recover frozen rules/license first.

## C. mengrenman/btcusdt-perp-signals — DATA BLOCKED
- Source: https://github.com/mengrenman/btcusdt-perp-signals ; MIT, Binance BTCUSDT perps, OFI / order-book and VWAP composite from tick/aggTrades/L2. Source commit not yet pinned, full executable trade/risk rules not yet recovered.
- Authentic Delta BTCUSD 1m OHLCV alone cannot reconstruct L2 order-flow imbalance; fabricating OFI from candle volume would change the source hypothesis. No baseline or profit claim.

## Execution and evidence
- Read codex/AGENTS.md and codex/STRATEGY_NOVELTY_GATE.md; compared MR002 and MR003 preregistrations, avoiding duplication.
- Latest branch historical run: 45036174691, completed success, MR003 6,550 trades, -99.9158% NAV, PF .5343, 0/22 positive months; verified artifact 14759488684. No new historical job launched. 2026 October has 1,440 missing UTC minutes per novelty policy; 22 IST NAV records are not proof of complete source coverage.
- Session count: 3 source mechanisms screened; 0 distinct eligible new baselines; 0 new backtests; 0 variants; 1 duplicate rejected, 2 blocked/not eligible. Next actionable direction: locate licensed, BTC-native single-asset mean reversion with distinct entry, frozen stops and larger expected gross excursion than 11.8bps round-trip fee+GST. No source claims are locally reproduced profits.
