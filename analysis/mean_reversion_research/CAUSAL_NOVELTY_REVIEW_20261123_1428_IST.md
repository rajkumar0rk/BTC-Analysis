# Mean reversion causal source-fidelity and novelty decision — 2026-11-23 14:28 IST

Status: **HOLD / NO NEW HISTORICAL TEST**. This is a new static audit, not a completed BTC replay. Read `codex/AGENTS.md`, `codex/STRATEGY_NOVELTY_GATE.md`, Stage19 report and 13:29 audit; branch Actions runs list still contains 8 runs, most recent historical success MR003 45036174691 at 1656866d6234032a6d19d3a2bc1692807667efcd.

## Pinned candidate and closest prior art
vaultik MIT source `src/wfo.py` commit `7f9bcd24d0e1cf7258699f4835ecd80dcb684a84`, blob `1adc9d2e41ac9fb7f854dfa6a5ed145ee142d95e`: https://github.com/vaultik/algo-trading-system/blob/7f9bcd24d0e1cf7258699f4835ecd80dcb684a84/src/wfo.py . Original Bybit 5m multi-altcoin walk-forward; 24h rolling VWAP/SD Z-score inward crossing at +/-3, prior RVOL >=2.5, next bar open; staged half exit at VWAP +/-1SD, rest at VWAP, stop at VWAP +/- (3+buffer) SD, timeout 2/4/8/12h; 3x leverage, 0.04% commission model. Published TON/LTC positive windows and paper -2.04% are NOT Delta BTC outcomes. Stage19 `analysis/institutional_discovery_stage19_monthly_10pct/RESEARCH_REPORT.md` covers sweep reversals, RSI2, EMA pullbacks and 1m stop-first exits; MR003 covers Keltner crossback. A *volume-weighted standardized 24h deviation plus RVOL and staged equilibrium target* is economically distinct from a Keltner crossback and price-level sweep, but code/runner search for other VWAP variants is not yet complete. Decision **PARTIAL OVERLAP — NOT APPROVED FOR RUN** until exhaustive novelty check.

## Additional independently inspected executable defects
1. **Entry-bar exit blindness**: `if in_position == 0` enters at current open but `elif in_position == 1/-1` management does not execute until the following 5m candle. An immediate stop breach in the entry candle is ignored.
2. **Optimistic TP-before-stop**: on long bars `high >= tp1` is processed before `low <= sl`; the stop is moved to breakeven before checking the same candle's low. The short path mirrors this. A candle hitting both must not assume TP1 first.
3. **Gap fill optimism**: long stop exits at `sl_price` even when the candle opens below it (short symmetrically above), rather than at adverse open.
4. **Partial-exit cost inconsistency**: each 50% tranche subtracts a full round-trip commission before multiplying by its fraction. This happens to allocate total modeled round-trip commission across the two halves but does not debit entry fees when opening or reconcile cash NAV during partial positions; any new implementation must book actual fee cashflows at each fill, with GST.
5. **Parameter provenance**: original executable runs a 12-combination optimization (3 stop buffers × 4 timeouts), not one frozen baseline. Must preserve each original combination and choose 2025-only before 2026 chronology; no cherry-picked 2026 settings.
6. **Signal timing**: `z_curr` uses current completed 5m close and `prev_rvol` references prior 5m bar; the pending signal enters the next bar open. On Delta 1m replay, compute 5m features only after 5 complete minute bars, with entry on the next eligible 1m open. Rolling VWAP and SD construction must be recovered from pinned preprocessing code, not guessed.
7. **Monthly integrity**: 2026-10 contains 1,440 missing UTC 1m candles in repository documentation; no complete 22/22 IST claim without independently resolving boundary coverage.

## Concrete causal disproof test vectors to add before historical replay
- Long entry 100, stop 98, TP1 102, candle O100 H103 L97 C101: conservative STOP at 98 for full position; never book TP1 then BE.
- Long entry 100, stop 98, candle O97 H101 L96 C100: fill stop at 97 (gap), not 98.
- Long entry 100, stop 98, TP1 102, **entry** minute O100 H101 L97 C99: stop must execute on entry minute, not next 5m bar.
- Short entry 100, stop 102, TP1 98, candle O100 H103 L97 C99: conservative STOP at 102 before TP1.
- Fees: research assumption 0.05% per side plus 18% GST = 0.059% each side, 0.118% round-trip notional before funding, spread and slippage. Partial exit must debit entry fee once, exit fee per filled tranche, GST on both, and reconcile NAV.

## Execution gate and handoff
New source-faithful BTC baselines completed **0**, variants **0**, new workflow launches **0**. No code fix or successful rerun is claimed. Next: fetch pinned indicator-preprocessing source; compare Stage19/other VWAP implementations and write separate pre-run NOVELTY_CHECK; implement a **publisher-original reference** and clearly labeled **causal correction** with unit vectors above; run authentic Delta India BTC 1m workflow and inspect completed trade/monthly artifacts. Do not touch main, other families, VPS or trading accounts.
