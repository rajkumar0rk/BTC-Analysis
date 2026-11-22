# M26 — VAMO publisher-fee falsification and execution gate (2026-11-23 IST)

## Recovery
Read codex/AGENTS.md, codex/STRATEGY_NOVELTY_GATE.md, M25 and append-only ledger. GitHub Actions branch listing returned 9 historical runs, latest M14 run 45008927897 completed SUCCESS at c71c783; no pending historical repair.

## Immutable primary evidence
NicolasBohn (formerly TPTBusiness), VAMOStrategy source commit 96da7a5aa4c03c83d55b019760e66bc91d6120b0:
- https://github.com/NicolasBohn/VAMOStrategy/blob/96da7a5aa4c03c83d55b019760e66bc91d6120b0/Strategy.pine
- https://github.com/NicolasBohn/VAMOStrategy/blob/96da7a5aa4c03c83d55b019760e66bc91d6120b0/README.md
- https://github.com/NicolasBohn/VAMOStrategy/blob/96da7a5aa4c03c83d55b019760e66bc91d6120b0/LICENSE

**New independent finding:** original Pine `strategy(...)` has NO `commission_type` or `commission_value` and README does not specify the TradingView commission/slippage settings. Thus publisher PF 1.301, 660 trades and +5.65% (Oct27–Nov2 2025), and PF 1.146, 594 trades and +1.48% (Sept15–20 2025) cannot be assumed net of Delta fees. These are publisher figures only. Pine default is 100% of equity per trade, with opposite signals potentially reversing; round-trip equivalent count may understate execution legs if reversal mechanics are not handled.

## Pre-replay economic disproof screen
Research taker fees 0.05% per side plus GST18% => 0.059% per executed side; 0.118% per conventional round trip. At 100%-NAV notional and constant notional, 660 trades imply 77.88% initial-equity-equivalent turnover costs, and 594 imply 70.092%, **not** realized NAV loss estimates. In reality fees are charged on changing notional and reversals may alter leg count. The 660-trade sample spans 7 days: 94.3 trades/day, ~3.93 trades/hour; 594 trades across 6 days: 99/day. Those rates are economically incompatible with simply assuming the reported +5.65%/+1.48% survives the mandated cost model; exact after-cost P&L is UNVERIFIED and must be replayed. No fabricated NAV.

## Fidelity and novelty decisions
The exact source uses ROC14 / ATR14 * 100, EMA9 crossover, ATR14 < ATR28*1.5, close-anchored 1ATR stop / 2ATR target, 100% equity size, unused riskPerTrade input. The Strategy.pine header says 'MIT modified no selling', conflicting with repo LICENSE MIT. Hold code reuse pending license resolution. Re-implementing general mathematical ideas independently still requires novelty gate against Stage25 and existing MACD/RSI momentum. Current status: HOLD, not eligible for a source-faithful historical launch. No source code executed or copied.

## Work counts and next action
One pinned primary source re-audited (strategy + README + license), one independently derived fee-turnover falsification screen, 0 new distinct authentic Delta historical baselines, 0 variants, 0 Actions launches, 0 new verified P&L. Next session should prioritize licensed, complete, lower-turnover momentum acceleration models rather than another VAMO audit, then commit NEW novelty gate and run BTC2025 archived 1m replay to completed artifacts. Funding remains unmodeled. No main, other-family, VPS or live writes.
