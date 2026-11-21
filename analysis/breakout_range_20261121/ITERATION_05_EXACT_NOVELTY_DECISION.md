# Iteration 05 — exact false-breakout novelty decision (2026-11-21 IST)

## Decision: SKIP proposed fixed-session false-breakout fade (duplicate economic mechanism)

The previously proposed "session-anchored failed breakout, confirmed return inside" is **not** a novel strategy simply because its anchor is New York instead of UTC. The source-faithful economic mechanism already exists in `scripts/research_daily_failed_breakout_20261119.py` on `research/daily-failed-breakout-20261119`:
- Fixed 00:00–01:00 / 00:00–02:00 / 00:00–03:00 UTC opening reference high and low;
- After the reference, completed 5-minute candle sweeps the fixed boundary by 0.02% or 0.05% and closes back inside;
- Fade at the **next 1-minute open**, maximum one trade per UTC day;
- Fixed fraction target 0.25% or 0.5%, stop 0.3% or 0.6%, timeout 60 or 180 minutes;
- 0.5% NAV nominal risk, 2x max notional; stop-first one-minute exit, gap-aware stop, taker fees and GST, adverse slippage and funding proxy.

Stage24 `scripts/research_structure_monthly10_stage24.py` (`research/stage24-monthly10`) independently contains a rolling 15-minute **failed_break** pattern: wick outside preceding 8/24-bar high/low then close back inside with candle-direction and volume filters, next-minute execution. This is a different reference construction but the same rejection/reversion causal family.

Therefore **SKIP** a generic failed-session-boundary trade, do not merely swap UTC 00:00 to New York opening range or tune stop/target. Such a change alone is parameter/session optimization, not evidence of novelty. The earlier source's explicit full 2025–2026 load demands 686 complete UTC days and may fail on the known October 2026 gap; no positive return or completed run can be inferred from the script.

## Data path established, execution still unverified

Stage24 code identifies `data/delta_india/BTCUSD/1m/20??-??.csv.gz` as its source. `read_archive()` validates strict increasing Unix minute timestamps, OHLC consistency and gap segmentation. Its own report states the 2026-10-31 UTC 1,440-minute gap. This establishes the **declared path and loader**, not that the archived partition files are presently accessible to a new GitHub Actions runner. Do not invent source hashes or claim complete October IST.

## Remaining genuinely differential questions

An anchored range's **subsequent acceptance and failed retest over multiple closed candles**, rather than one 5-minute sweep-and-return, might differ economically; however no source-faithful published rule set has yet been pinned, and novelty must be checked against Stage19's sweep/confirmation patterns before coding. No ungrounded invented rule should be treated as sourced. A different market session alone is not a sufficient distinction.

## Outcome

Exact source code comparison completed; generic false-breakout hypothesis **rejected as duplicate**. No backtest launched or profitable result claimed. Next task: recover a fully specified third-party strategy with an objectively distinct range-acceptance/retest mechanism, verify prior art, then check actual 1m archive accessibility and launch a new first-screen workflow. Funding remains unmodeled for the prescribed first-screen baseline.
