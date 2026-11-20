# External discovery and execution checkpoint — 2026-11-21 02:20 IST

Latest branch SHA before this note: f7d96b80b09a6bc5560e617725a11596a7677d75. GitHub Actions runs 44803085638 and 44793133653 both completed success, but the original 2025 Keltner screen was REJECTED for only three trades, as documented in SCREEN_DECISION_20261120.md. No active run on this branch. No candidate was accepted this cycle, and no new native BTC backtest was executed; this note does not count as a completed experiment.

External queries: `github cryptocurrency intraday session breakout strategy python opening range BTC backtest code`; `site:tradingview.com/script/ bitcoin intraday time of day opening range strategy source code`.

External sources examined:
- https://github.com/ctrlaltprofit/simple_backtesting_example : 15m opening range 09:15-09:29, breakout on candle high/low, entry at candle close, opposite range stop, RR target and 15:15 exit; one trade per day. Rejected for this cycle: overlaps prior BTC opening-range and first-four-hour box studies; equities/Indian-market clock must not be silently transferred to BTC. No license verified; no source SHA pinned.
- https://github.com/SC4RECOIN/simple-crypto-breakout-strategy : previous-day range breakout with end-of-day exit; rejected as prior-day range strategy already researched; published ETH-PERP results are unverified and source has live order code. No license verified.
- https://github.com/MAKSAT-DEL/mtf-breakout-bot : 1H/4H/D trend alignment, ADX/volume, ATR stop; overlaps existing MTF breakout tests. Self-reported BTC/USDT PF 1.46 is not independent evidence. No license verified.
- https://www.tradingview.com/script/ddgvttDd-Time-of-Day-Volatility-Report/ : volatility report, not a complete executable entry/exit strategy; cannot be accepted for source-faithful screening.
- https://github.com/sam-bateman/trading-orb/blob/main/src/orb_strategy.py : 30m opening range, 1.2 relative volume, 1.5x range target, 0.75x range stop, 15:45 ET flatten. Equity session-specific and overlaps prior ORB; no BTC adaptation without a new hypothesis.

Decision: INCONCLUSIVE / NO NEW EXECUTABLE CANDIDATE. This is a genuine novelty/source-parity blocker for these examined sources, not a market-data or GitHub Actions outage. Next cycle must search a materially different externally specified economic mechanism (prefer session-clock or order-flow proxy), pin code and license, implement in this branch and trigger a real BTC2025 zero-slippage + two-sided fee/GST run. Only if credible positive screen then frozen 0.5/5 BTC point slippage stress. Historical funding UNMODELED. No main, other branch, automation or live account changes.
