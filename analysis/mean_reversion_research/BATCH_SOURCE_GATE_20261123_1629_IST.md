# Mean-reversion source gate — 2026-11-23 16:29 IST

Read codex/AGENTS.md, codex/STRATEGY_NOVELTY_GATE.md, prior source correction, experiment ledger and actual branch Actions runs. Latest completed historical run is MR003 45036174691 (success as a job, rejected strategy); no newer historical replay exists. Do not count MR002 vaultik again.

## 1. Patrick Sebastine — BB/RSI mean reversion, source-pinned
Source https://github.com/PatrickSebastine/mean-reversion-trading-bot/blob/c00091d34ad1ee10ede37996883934099bb533c9/strategies.py ; license MIT https://github.com/PatrickSebastine/mean-reversion-trading-bot/blob/c00091d34ad1ee10ede37996883934099bb533c9/LICENSE .
Original: 15m, BTC/ETH and six other USDT futures on OKX, 3x isolated. BB(20,2) on close, RSI14 below 25 and close <= lower BB => BUY; RSI above 75 and close >= upper BB => SELL; signal strength based on normalized band extension. Risk module default 2% stop, 4% TP, max 10% wallet per trade, 3% session loss guard. Historical README table: April 7–14 2026, 11 mean-reversion trades across eight assets, +3.56% combined reported, BTC alone one trade +0.03%; publisher explicitly says ORIGINAL backtest had **NO fees or slippage** and newer engine was not rerun. No publisher PF/DD for BTC, no 22-month period. No claim of reproduced returns. Potential signal-close fill and bar path risk requires separate executable engine audit; stop checks in risk.py use price comparisons, not proof of causal minute stop fills. **NOVELTY SKIP**: same economic BB+RSI extreme as MR001 and many earlier audits; changed thresholds and 2% stop do not qualify as new signal.

## 2. zodboy — simple BB/RSI Freqtrade
https://github.com/zodboy/freqtrade-simple-mean-reversion ; README says 1h long-only BB20/2σ close below lower band + RSI14<35; tiered ROI 5%/3%/1%/-1%, 15% stop; MIT declared. Original exact source commit could not be pinned with connector (404), and no verified publisher trade count/PF/DD. **NOVELTY SKIP** because near-identical to MR001 BB/RSI, different RSI threshold and ROI schedule only. No need to implement duplicate.

## 3. GoLukeEnviro — RSI mean reversion V11
Source indexed at https://freqle.org/strategy/a446f6ed5f7ae10a ; 15m spot RSI/Stochastic/Bollinger/EMA with 2.5% stop, Freqle reports 3,433 trades, PF 0.58, -87.9% net, -88.09% DD on its indexed evaluation (not Delta BTC). Exact pinned GitHub commit and license not retrieved (GitHub REST 404). **NOT REPRODUCIBLE** under source pin/license gate, and overlapping BB/RSI signal. This is publisher/index performance, not a locally reproduced result.

## Quantitative cost sanity gate
Research taker fee 0.05% notional per side, GST 18% on fees: 0.059% each side, 0.118% round trip before spread/slippage/funding. For a 2% stop and 4% TP at unchanged notional, fee-adjusted ideal payoff approximately +3.882% vs -2.118%, break-even win fraction 35.3% (2.118/6), ignoring position-dependent notional changes and gap fills. This is arithmetic only, NOT observed expectancy. At 0.10% gross mean reversion, even perfect price prediction loses roughly 0.018% before funding/spread.

## Session status
Three public source screens; 0 new distinct eligible candidates; 0 new historical BTC1m backtests, 0 variants, 0 launched Actions. No fabricated results. Next actionable research: prioritize source-complete materially distinct oscillator-distribution / excursion mechanism, complete license/novelty gate and write a pre-run novelty record BEFORE using archived runner. If unavailable, continue screening different mechanisms rather than relabeling BB/RSI or MR002.
