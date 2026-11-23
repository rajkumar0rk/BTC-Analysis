# Mean-reversion source execution audit — 2026-11-23 20:26 IST

Scope: isolated source-audit branch only; no historical BTC replay or code fix. Read codex/AGENTS.md, codex/STRATEGY_NOVELTY_GATE.md and previous 19:32 gate. Verified branch Actions list: 8 runs, latest historical MR003 45036174691 successful, SHA 1656866d6234032a6d19d3a2bc1692807667efcd; rejected PF 0.534, -99.92% NAV.

## Source examined — ojeology E14-Honest, follow-up to earlier VWAP screening
Repository https://github.com/ojeology/mean-reversion-vwap-lab ; original source https://github.com/ojeology/mean-reversion-vwap-lab/blob/main/backtest_v14_honest.py ; source blob e02274a927c841e1485f09538f796ac58e9e9aa2 ; result blob b7d56976d30a75bb8d9cfb2705285a1525fbe45f ; README blob 7c5885150e7b2bf2558e640b2df7b025234ab695. Root directory has no LICENSE file; permission to redistribute source is not established. Publisher originally tests 13 MEXC altcoin pairs, 1m, 30 days; no BTC in universe.

Original signal: session-reset VWAP on typical price (H+L+C)/3, weighted dispersion (but nonstandard accumulating squared residuals against changing current VWAP), low touches VWAP-2std and closes above band with green candle, body>0.5 ATR14 and RSI14<40; inverse short at upper band, RSI>60. Skip UTC hours 0,1,3,4,6,9,10,14,18,19,20,21. Next 1m open entry. Per-pair TP grid 1.2%-4%, SL grid 0.7%-1.8%, 15d rolling training / 5d OOS across 3 windows. Cooldown five candles after stop; daily guard $15. $5 margin, 20x, flat $0.08 per round trip.

Publisher result e14_honest_results.json dated 2026-06-21: 184 OOS trades across 15 days, win 43.48%, PF 1.7367, +$87.82, reported max drawdown -$8.17. **Not BTC results, not our verification.**

### Concrete execution/cost disproof
1. `simulate`: `if ti <= si` gives TP precedence if both TP and SL hit on same minute. For a long with entry=100, TP=102, SL=99, subsequent minute high=103 and low=98, it books TP even though order is unknown. Correct conservative BTC 1m replay must book SL first.
2. Gap stops are filled at configured stop price, not adverse opening price. Correct replay uses worse of stop/open for a stop crossed at open.
3. `FEE=0.08` is a flat dollar charge on $100 notional (0.08% round trip), versus required 0.118% ($0.118) round trip with GST. Difference $0.038/trade at constant $100 notional, about $6.992 over 184 trades, before gap/stop corrections. This arithmetic is a static comparison, NOT adjusted historical P&L.
4. Each pair is simulated independently with fixed $5 margin; no shared chronological NAV, overlap or capital allocation across 13 pairs. The publisher's reported portfolio PF and drawdown cannot be treated as sequential $5-account NAV.
5. Session dispersion is not the conventional weighted variance around a single fixed window mean: each squared deviation uses the time-varying VWAP at that minute. Preserve as original, label any conventional replacement a derivative.
6. Training and OOS data slices independently compute indicators globally before slicing (causal rolling/session indicators), but training simulation exits at slice end and no gap continuity checks are present. 15 OOS days cannot validate 22 IST months.

Novelty: PARTIAL OVERLAP / HOLD. VWAP 2sigma rejection with RSI and body confirmation differs from MR002 rolling VWAP z-score crossing, but resembles prior session-VWAP and BB/RSI families; need exact Stage19 and MR001 comparison. No source-faithful reproduction is eligible until source license and novelty are resolved. Even if eligible, publisher's altcoin claims must not be transferred to BTC.

## Run accounting
Newly discovered distinct sources: 0 (deep verification of previously screened source); substantive executable audits: 1; verified new BTC baselines: 0; variants: 0; new Actions launches: 0; new historical artifacts: 0. No fixes claimed. Next: seek source-complete licensed nonduplicate candidates; pre-register novelty and use existing historical runner for stop-first Delta India BTC 1m replay. Never overwrite this audit or mutate other branches.
