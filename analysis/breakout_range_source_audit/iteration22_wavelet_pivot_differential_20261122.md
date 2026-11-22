# Breakout & Range — source triage, 2026-11-22 (late session)

Branch: research/breakout-range-source-audit-20261121. Read codex/AGENTS.md and codex/STRATEGY_NOVELTY_GATE.md; existing overlap includes Stage24 failed auctions, Stage23 compression and prior range-breakout studies. Prior successful Actions 44902737237 is archive validation only; **no strategy replay completed this session**.

## Candidate A — Wavelet-2B
- Creator: zty05070242; source https://github.com/zty05070242/wavelet-2b/tree/5d879b3d04031952f41d2b4d4c4a3cce43f04150 ; commit 5d879b3d04031952f41d2b4d4c4a3cce43f04150 ; MIT license reported by GitHub API.
- Original market: ten commodity futures, daily bars; pre-2018 development and 2018+ evaluation. Publisher reports fewer trades in 10/10 markets, lower max drawdown in 9/10; median drawdown reduction 11.1 percentage points. **Not BTC/Delta results.** Publisher return/PF/cost assumptions not independently checked.
- Mechanism: causal rolling wavelet reconstruction, fixed-lag ATR-prominent pivots; wick beyond last confirmed pivot followed by closing back inside within confirmation_days. The original TwoB rolling-extreme baseline uses lookback=20 and confirmation_days=3. Pivot detection dates a candidate at k+confirm_bars, not k. See pivot_detector.py, wavelet_denoiser.py, strategy_folder/two_b.py and two_b_rule.py.
- Integrity gate: wavelet_denoise() uses full-series future information and MUST NOT be used for trading; rolling_wavelet_denoise() only uses trailing windows. Original daily confirmation_days cannot silently be converted to 1m confirmation; use source's original daily specification first, or label a separately preregistered intraday adaptation. No same-close fill; signals require next eligible 1m open.
- Novelty: PARTIAL OVERLAP with Stage24 failed-auction/rejection; candidate incremental hypothesis is fixed-lag wavelet-confirmed pivots versus rolling extremes. **Not approved yet**: requires exact original wavelet parameter retrieval, comparison with Stage24 pivot rules and original source trade sizing/exits, plus evidence that signal construction is causal in the full runner.

## Candidate B — EMA9 × daily anchored VWAP crossover with high break
- Creator xenoxavier; https://github.com/xenoxavier/freqtrade-ema-vwap ; GitHub reports MIT. Source commit and full exit rules not pinned in this session.
- Publisher advertises 382-trade forward-test dataset; unverified and not Delta BTC historical evidence. 1h EMA9 crossing daily VWAP (00:00 UTC anchor), close above both, then price breaking crossover candle high, with ATR stop/liquidation prefilter.
- Novelty: overlap with existing trend pullback/breakout, VWAP and retest studies. **SKIP pending exact source comparison**; cannot count as distinct historical baseline.

## Candidate C — VibeTrading consolidation breakout
- Source https://github.com/VibeTradingLabs/vibetrading/blob/main/strategies/breakout_consolidation.py ; license and source commit not pinned.
- 1h Bollinger width squeeze, volume spike, ATR stop and partial profit; publisher provides example backtest command, not verified return/PF/DD/trade count.
- Novelty: DUPLICATE of Stage23 compression and earlier squeeze+volume research. **SKIP**.

## Execution and falsification gate
- No new historical job or P&L artifacts. New source screens 3; distinct BTC backtests 0; variants 0; winners/losers unknown.
- Required next: retrieve Wavelet-2B full pinned original strategy/exit/position rules; compare against Stage24 read-only. If approved, commit NOVELTY_CHECK.md and a source-faithful baseline before any Actions launch. Use authentic Delta BTC 1m archive, completed bars and next-minute opens, stop-first intraminute accounting, 0.05% per-side fees + 18% GST, no assumed funding, sequential NAV and complete IST monthly marks. Only after a completed job and reconciled artifacts report P&L.
