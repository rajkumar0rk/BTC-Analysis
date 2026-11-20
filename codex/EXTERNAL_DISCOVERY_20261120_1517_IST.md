# External discovery handoff — 2026-11-20 15:17 IST

## Verified prior study
Run 44682789117 was completed and its artifact recovered in previous iteration. Path efficiency rejected: BTC 6 trades, PF 0.608, 2025 -0.44%, Jan-Oct 2026 -0.54%; ETH 5 trades PF 0.352. Do not optimize this weak sample. Its old $5/side slippage model is not compliant with newly mandated zero-slip-first sequence; rejection is based on negative expectancy and insufficient trades, not a valid zero-slip screen.

## External online discovery performed this iteration
Queries: site:github.com/aurelien-gentile/turtle-strategy-backtest turtle strategy backtest rules; site:github.com/pooriag/crypto-strategy-backtest strategy.
- https://github.com/pooriag/crypto-strategy-backtest : public MIT code, Coin Metrics data CC BY-NC 4.0. Daily long-only time-series momentum, MA crossover, volatility targeting, walk-forward. Reported 2018-May 2026 momentum+vol targeting 25.5% CAGR, 0.91 Sharpe, -50.7% max DD on BTC/ETH equal-weight, fragile to doubled costs/one-day delay. NOT an independently verified Delta India result. Candidate for further rule-level inspection, commit pinning, and zero-slippage native BTC screening. Need inspect signals.py/backtest.py to extract exact parameters, and check novelty against existing BTC-Analysis tests. Not selected or executed.
- https://github.com/aurelien-gentile/turtle-strategy-backtest : hourly long-only Donchian breakout, opposite-channel exit, 2x ATR initial stop, 1% fixed risk unit, optional pyramiding; published 343 combinations failed to outperform BTC buy-and-hold mid-2023–early 2024. Prior BTC-Analysis Donchian research makes duplication likely; deprioritized pending novelty check. License not established.
- https://github.com/JuRose99/turtle_strategy : long-only 20/10 breakout and ATR trailing stop, sample CSI300 ETF 32 trades and 31.2% win rate; not BTC evidence; deprioritized. License not established.

## Cost protocol for any new candidate
Stage 1 BTC-2025 only: zero entry/exit slippage, 0.05% commission per side plus 18% GST, genuine Delta India candles, full trade and month ledgers, no funding assumption. Reject negative or underpowered screen. Stage 2 only for credible positive screen: freeze same rules and compare 0.5 and 5 BTC USD/side and adverse bps. Then frozen BTC 2026 and ETH validation; funding UNMODELED; no all-in or live claims.

## Execution state and limitation
No new backtest was launched in this iteration. External source rule-level verification, license and commit pinning, native Delta data integration and dedicated push-triggered workflow remain outstanding. This is a discovery-only handoff, NOT durable execution completion, and must not be called a screened strategy. Next check should prioritize extracting the third-party exact executable rules and running a native BTC-2025 zero-slip screen on this isolated research branch. Do not alter main or other schedules.
