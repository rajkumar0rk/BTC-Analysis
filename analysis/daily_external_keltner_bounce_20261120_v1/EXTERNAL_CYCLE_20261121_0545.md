# External source checkpoint — 2026-11-21 05:45 IST

Scope: Independent Daily-Profit Strategy Hunt only. Latest relevant GitHub run 44814981143 on branch research/daily-external-keltner-bounce-screen-20261120-v1 completed success. Prior source-faithful KeltnerBounceV1 BTC2025 screen run 44710028523 had 3 closed trades; REJECT insufficient sample, no slippage stress authorized. No active newer daily study identified in latest 100 repo runs. This checkpoint is discovery/novelty work, NOT a backtest and NOT a positive expectancy claim.

Public web queries this cycle:
- site:github.com crypto intraday strategy time of day funding settlement reversal python backtest
- site:tradingview.com/script/ crypto session mean reversion strategy source

Sources inspected:
- https://github.com/MayurMalgear/Liquidity-Sweep-Reversal-System : liquidity sweeps, rolling equal highs/lows, RSI14 >55/<45, volume above SMA20, ATR1.5 stops and RR target. Potential lookahead from configurable sweep confirmation window, and possible overlap with previous failed auction / wick studies. License and exact commit not yet verified; DO NOT implement without source parity and causality audit.
- https://github.com/farrellh1/crypto-funding-rate-strategy : MIT-licensed Bybit funding z-score momentum/reversion (168 funding intervals, threshold 2.5); REJECT for current OHLC-only screen because genuine historical Delta funding/open-interest data unavailable. Do not substitute price proxy or fabricate funding.
- https://www.tradingview.com/script/2qjlEzOH-RSI-Mean-Reversion/ : protected RSI+BB crypto 15m; self-reported profits unverified; overlaps other schedule RSI/BB research and source unavailable; REJECT.
- https://github.com/gistrec/trade-lab : open research framework with walk-forward, no novel intraday executable clock edge identified; NOT ACCEPTED as candidate.

No new source passed source-code/novelty/causal-information gate; therefore no new native BTC screen was launched. Existing last executed Keltner screen remains rejected. Exact next action: inspect MayurMalgear repo pinned commit, license, detection.py and strategy.py for future-bar use and source-parity; compare against prior failed auction/wick studies. If source is novel and executable with only past data, implement faithful BTC2025 zero-slippage screening with 0.05% per-side commission + 18% GST, on isolated branch, trigger push workflow and audit actual run/trade/monthly artifacts. Stress 0.5 and 5 BTC price points/side ONLY if screening positive and sample adequate. Funding UNMODELED, spread/impact/rounding unavailable. No live changes.
