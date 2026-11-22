# Iteration 15 — source triage, 2026-11-22 IST

Status: STATIC SOURCE SCREEN ONLY. No historical strategy backtest, no performance claim.

Recovery: branch Actions list contains 2 completed archive-integrity runs, latest https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/44902737237 SUCCESS. It is NOT a strategy replay. Existing novelty gate covers Stage24 squeeze/breakout/retest, Stage25 hourly structure and earlier Donchian/failed-auction. Read codex/AGENTS.md and codex/STRATEGY_NOVELTY_GATE.md.

New source candidates screened:

1. https://github.com/rollroyces/vcp-signals — creator rollroyces, source branch main, pushed 2026-10-15. VCP contraction waves + volume dry-up and breakout pivot, with stage-2 trend template and relative strength vs SPY. GitHub repository metadata has no declared license. Primarily US-equity universe; SPY-relative strength cannot transfer source-faithfully to BTC futures without changing inputs. **NOT REPRODUCIBLE AS BTC TRANSFER**, license unverified. Publisher's forward-return reports are not our P&L.
2. https://github.com/blacckbeard4/VCPBot — creator blacckbeard4, main, pushed 2026-04-21; long-only daily US-equity VCP breakout with bracket order and volume confirmation. No declared repository license. **NOT APPROVED**: license unverified, daily equity selection and existing squeeze overlap.
3. https://github.com/anaysharma1717-svg/Volatility-Persistence-Trading-Strategy — creator anaysharma1717-svg, MIT license, main, pushed 2026-10-08. Published V2 explicitly fixes a prior backtest error that dropped out-of-session candles and left positions unmanaged. NY-session momentum/color-change + 4H EMA200 + volatility gate. **SKIP**: predominantly momentum/trend family and overlaps intraday time/volatility and Stage25. Publisher's claimed BTC +97% and ETH +182% are unverified and not Delta India results.
4. https://github.com/PineGen-AI/volatility-expansion-fake-breakout-strategy — ATR expansion, range break, strong close, ATR bracket; **SKIP** per iteration14, duplicate source was encountered again, not counted as a newly distinct candidate.

Static fee hurdle: 0.05% notional per side + 18% GST on each fee = 0.059% per side; 0.118% round trip at unchanged notional, before spread, slippage, funding. A BTC strategy must earn more than this before net expectancy turns positive. This is arithmetic, NOT an observed backtest.

Counts: 3 new distinct repositories screened, 1 repeat, 0 approved novelty decisions, 0 new backtests, 0 variants, 0 after-cost PF/monthly NAV results. Next task: identify a licensed, source-complete, causally new boundary event; commit a candidate-specific NOVELTY_CHECK.md before a historical replay. Authenticated archive exists in Actions; local mount absence is not a reason to stop research. No third-party code executed, no protected branches or trading accounts touched.
