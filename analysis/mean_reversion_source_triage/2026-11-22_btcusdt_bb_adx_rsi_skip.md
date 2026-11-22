# Mean Reversion source triage — 2026-11-22 — BTCUSDT BollingerADXRSI

Decision: **SKIP / DUPLICATE mechanism**. No historical replay authorized.

Source: https://github.com/wtfyyii/btcusdt-mean-reversion-backtest
Read-only source file: https://github.com/wtfyyii/btcusdt-mean-reversion-backtest/blob/main/final_b_01.py (Git blob SHA f1617fcab2500c5cacb5e1549ba6032ef94f2d08); variant final_r_01.py (blob SHA 469c44035daf404e9f183f290182ef035cb339c3). Upstream commit SHA not independently established. No LICENSE at root; code reuse permission unverified. No third-party code copied.

Publisher README describes BTCUSDT 5-minute historical backtests on SQLite databases not included in this inspection: B 2020–2024 +22.37%, 3008 trades, 58.58% win, -37.48% drawdown; R 2020–2023 +9.92%, 2386 trades, 59.05% win, -37.48% drawdown. These are publisher claims, not local Delta India futures findings. PF and fees/GST assumptions not supplied in README; implementation charges 0.02% commission per side, below research requirement of 0.05% plus GST.

Exact B source: 5m BB(13,2) sample-std, RSI(14) SMA gains/losses, ADX(14) SMA TR/DM/DX; gate ADX<=25 and BB bandwidth<=0.05; long when current low<=lower BB and RSI<30, short when current high>=upper BB and RSI>70; trade fraction 0.5; exit long if close>=upper BB or <=entry*(1-0.01), short if close<=lower BB or >=entry*(1+0.01). R differs in bandwidth gate: bandwidth>=0.05. Both use trade_on_close=True and a close-triggered stop, not intrabar protective stop. Their code comments claim midpoint exit but actual code targets the opposite band. The gate is evaluated before exits, so adverse high-ADX/high-bandwidth periods can prevent even a stop/target close, creating unbounded intrabar loss relative to the intended 1% threshold. Reproducing on Delta with 1m stop-first would materially alter original mechanics and may be safer but not source-faithful.

Closest prior art: MR-002 and Stage19/23/24 envelope/RSI/extreme reversion experiments (see codex/STRATEGY_NOVELTY_GATE.md and previous mean-reversion audit). Adding ADX and bandwidth filters is not sufficient evidence of a new causal mechanism. Therefore skip and do not use resources on an economically overlapping backtest. This note does not count as a completed historical backtest.

Next candidate should be distinct from BB/RSI envelopes, reproducible from genuine Delta India BTCUSD 1m OHLCV, have source-defined risk handling and a license/permission basis. The 2026-10-31 UTC minute gap must be disclosed in any subsequent validation.
