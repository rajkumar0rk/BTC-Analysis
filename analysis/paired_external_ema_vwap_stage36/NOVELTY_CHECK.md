# Stage36 external strategy research — 2026-11-20
Status: SOURCE COMMITTED; zero-slippage BTC screening workflow pending.
Previous Stage35 CLOSED REJECT (run 44679315191, BTC PF 0.165, -3.31%, 8 trades). Other schedules read-only.

## Online discovery / attribution
Queries: Freqtrade strategy GitHub volatility breakout, TheoBrigitte momentum, Freqtrade EMA VWAP. Sources inspected:
- https://github.com/freqtrade/freqtrade-strategies (educational library; not an independently validated profitable strategy)
- https://github.com/TheoBrigitte/freqtrade/blob/main/strategies/momentum/momentum.py (3-bar momentum, duplicate of earlier momentum family, SKIP)
- https://github.com/xenoxavier/freqtrade-ema-vwap/blob/dbd1158cdd2e7014d7aaaabcd042ab4b4aef8450/user_data/strategies/EmaVwapLong.py (SELECT; public source, author xenoxavier, commit dbd1158c; published 382-trade/6-day/139-altcoin claims are NOT independently verified; published 20x leverage and maker limit fills NOT copied)
- https://github.com/zodboy/freqtrade-simple-mean-reversion (Bollinger/RSI candidate, skipped due overlap and unverifiable direct source via connector).
License of selected upstream source must be verified before copying source; this implementation independently expresses publicly described rules, not a source-code copy.

## Novelty gate
PARTIAL OVERLAP, differential: unlike Stage25 hourly momentum and Stage24 breakout, trigger requires UTC daily-anchored VWAP EMA9 crossover, close above both, and setup-high break within three hourly bars. Shared novelty gate warns that EMA pullback and 15m breakouts already exist. Treat novelty as conditional pending further overlap audit.

## Fixed screening rules
BTCUSD long-only, completed 1h EMA9 crossing above UTC daily VWAP, crossover close above both, 1.5x hourly ATR stop distance <3.8% of setup high. Arm three subsequent 1h candles while EMA>VWAP; detect first 1m high above setup high, fill NEXT minute open. Exit 1m stop-first, 3 ATR target (2R), 60h timeout. 0.5% account risk/trade, max 3x notional leverage. Taker fee 0.05% each side +18% GST on commission. ZERO slippage at both sides in FIRST screen. No ETH or slippage stress unless BTC screen shows credible positive expectancy and enough trades. Note this is a cautious approximation of external limit-entry system, NOT exact rule-for-rule execution parity; if promising, reconcile entry/exit differences before claiming success.
Falsifier: BTC screening net PF<=1, net NAV<=0, fewer than 30 independent trades, or invalid month-end reconciliation.
Funding UNMODELED; historical spread/order book/impact/lot sizing/liquidation unavailable; zero-slippage result is not all-in executable net. 2025-only selection, 2026 previously exposed, ETH frozen later. January IST start and October missing candles caveat. Preserve all 22 months.
Source: scripts/research_paired_external_ema_vwap_stage36.py commit 9d5b286bcaddc9638284b08c1067790a603a02ef.
Next: inspect GitHub Actions run ID, job and artifact, verify data/ledgers; only then decide REJECT / SCREEN PASS.
