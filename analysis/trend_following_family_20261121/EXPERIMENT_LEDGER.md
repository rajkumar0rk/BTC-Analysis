# Trend family experiment ledger — append only

## 2026-11-21 — TF-ICH-001 — launched, awaiting GitHub execution

- Candidate: 4H causal Ichimoku TK cross with 9/26/52/26 cloud and 26-period historical close confirmation, from https://github.com/sakshamverma2030/Algorithmic-Trading-Framework-in-Crypto-Python
- Original published implementation has NOT been copied. Source commit and license still need pinning; this is an independently written first-screen approximation, NOT yet certified source-faithful reproduction.
- Novelty: cloud displacement plus TK crossover and Chikou past-price filter is materially different from Stage13 EMA pullback and Stage17 Donchian. Compare source-level against Stage25 before treating as qualifying.
- Hypothesis: confirmation of multi-week directional persistence can offset frequent whipsaw losses. Disproof: negative BTC2025 fee-inclusive expectancy or too few trades.
- Execution: closed 4H bar at timestamp t, next eligible 1m open t; 2ATR initial stop is an independently disclosed risk overlay, not a claim about source's original stop.
- First-screen costs: 0 slippage; 0.05% notional fee each side and 18% GST; no funding data; capped 1x notional, 0.5% initial-stop risk.
- BTC2025 only. Workflow: .github/workflows/trend-family-ichimoku-screen.yml. Script: scripts/trend_family_ichimoku_first_screen.py.
- Script commit: 0a06063f50c2f2e60cdf5a55ffc92c07db103863; workflow commit eb46fed06fee802dd85a9f77f1a84ca5c22055c6.
- Status: workflow committed; no registered GitHub run observed immediately after push. DO NOT report profit or completed historical test until run/job/artifact verified.
- Next: verify workflow registration, repair any failure, pin source commit/license, audit output NAV reconciliation, archive source/data hashes and freeze baseline before 2026/ETH.

## 2026-11-21 — TF-ICH-001 execution recovery (iteration 8)

- Recovered pending TF-ICH-001 and its exact isolated workflow, rather than starting a new candidate.
- Fixed UTC-vs-IST 2025 cutoff, 2025 monthly end boundary, scheduled exit open before minute-bar stop evaluation, and recorded source-candle fingerprint SHA-256. Script repair commit `f8c2cbbdbde7188a58275a1a8a8310bccc7524b9`.
- Updated isolated workflow push paths to include script and ledger, commit `63ef31454e2b4e26ef14cfc46370511b64894779`. GitHub commit-associated Actions query for this commit returned ZERO registered workflow runs when checked. This is NOT a completed backtest.
- Exact execution blocker: no workflow run/job/artifact exists for the new workflow commit. GitHub Actions may not register push workflows from a branch until the workflow is recognized on the default branch; do NOT modify default branch to force this. Use an isolated-branch existing registered workflow runner or local execution against authentic data on next iteration.
- Audit warning: the independent Ichimoku overlay has not been matched against immutable publisher source/license; label as **independent Ichimoku variant**, not source-faithful reproduction. No claim of PF, NAV or profitability. No 2026/ETH tests until 2025 first-screen evidence is archived.

## 2026-11-21 — TF-ICH-001 recovery (iteration 9)

- Inspected pending BTC2025 Ichimoku script, workflow, novelty gate and archive loader. No completed Ichimoku historical run/artifact was established in this iteration.
- **Critical executable defect found:** an entire scheduled-exit block was stored as literal `\\n` sequences on a Python comment line; therefore `scheduled` and `x` were never assigned before the stop logic. This is a runtime blocker, not merely workflow registration. Corrected by restoring real Python newlines, retaining signal exits at the next eligible minute open and stop-first OHLC checks otherwise.
- Corrected historical end boundary to 2025-12-31 18:30 UTC (2026-01-01 00:00 IST), and prevented reading past the full IST 2025 research year. Source warmup still starts 2024-11-01 UTC.
- Repair commit: `e7779b85a1809c15bb3595f18602d3b50f5b028f`, on this isolated trend family branch only. Script change matches the existing workflow's `push.paths` trigger, but a successful GitHub run has NOT been verified. Do not claim completed backtest, positive months or profitability.
- Further audit needed before any result is trusted: source gap exit at last observed close can be optimistic; position MTM and equity NAV reconciliation, position closure at IST year end, publisher license/source SHA, true source-faithful rules, and monthly trade-level PF. Funding remains unmodeled.
- Execution environment blocker: local container has no mounted authentic Delta India 1m partitions and cannot resolve github.com for cloning. Must use an actual registered GitHub Actions job/artifact or authenticated local archive; no synthetic data substitutes.
- Next: recover actual workflow registration/job and execute full 2025 historical screen, inspect archived trade/monthly/NAV artifacts, then fix any accounting defects before considering a candidate result. No unrelated candidate launched.

## 2026-11-21 — TF-ICH-001 recovery (iteration 10)

- Continued pending TF-ICH-001 rather than starting a new candidate. Examined exact isolated workflow and script. No completed Ichimoku job/artifact established; commit-associated run lookup for repair commit f7c063c74145b91e2e5cf7287d532e71a5b6eb88 returned an empty list (note: connector only indexes PR-triggered runs, so absence is not definitive for push jobs).
- Historical replay repair commit `f7c063c74145b91e2e5cf7287d532e71a5b6eb88`: previously, a gap could force-close at the previous observed close, an unknowable and potentially optimistic fill. Now any intraperiod missing 1m bar fails the replay explicitly instead of fabricating stop execution. Added end-of-year monthly NAV adjustment after forced close, 12-month coverage assertion, final NAV-to-trade ledger reconciliation assertion.
- Workflow push trigger includes this script, so commit is a verifiable launch attempt; **not** a completed backtest. Workflow registration and actual run/job/artifact remain unverified; no PF, returns, trade count, or profitable months are reported.
- Outstanding correctness work: historical 1m data gaps in warmup, source-authentic Ichimoku rules and licensing, 4H bar coverage across IST year cutoff, accurate intrabar mark-to-market drawdown, 2025 frozen-selection process, and all historical fee/funding assumptions. No 2026/ETH or live orders.
- Next feasible remedy: obtain a registered branch-isolated workflow execution or authenticated checkout of the repository archive, then inspect artifact/trade ledger and repair any failed historical replay. If the new gap guard trips, repair the source archive or explicitly mark coverage incomplete; never interpolate or silently exit at stale price.

## 2026-11-21 — TF-ICH-001 entry-minute stop correctness rerun (iteration 11)

- Recovered completed baseline run https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/44914091290, successful at source commit 0e833c973a34e2369ff325e84297a44c8b9110b8; artifact 14710589580 (SHA-256 42cea3119e1e7a5089babe8983ee4098cb6b22e3d7fa155285ff9098caeb85e5). Previously reported 28 trades, PF 1.239, +1.70% NAV, 4.21% DD, 6/12 positive months remain provisional until artifact accounting audit.
- Found a material replay defect: the entry-minute OHLC low/high was never checked after filling an entry at the minute open. Stops touched on the entry minute were therefore deferred or omitted, creating optimistic historical execution. The baseline is NOT a reliable positive result until this is corrected.
- Fixed the entry-minute stop check using current 1m low/high after entry at its open, with stop-price exit, both fees and GST, no future candles. Code commit a70de4f0eef0e520cd1cabf1a6dcf63cb4f5ecba. Original baseline commit/artifact preserved.
- GitHub registered rerun https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/44925231993 (queued when checked). Await actual completion and artifact before reporting revised metrics.
- Additional limitations: publisher license/source commit not pinned; implementation is an independent Ichimoku variant; source-faithful claim in script docstring must not be relied on. Funding and realistic spread remain unmodeled. No BTC2026/ETH verification or live activity.
- Next: inspect completed rerun's trade/monthly artifact, compare immediate-stop trades against original, verify fee reconciliation and monthly PF, then decide rejection versus preregistered robustness work. Do not optimize based on 2026.


## 2026-11-21 — TF-ICH-001 corrected entry-minute replay verified (iteration 12)

- Verified completed GitHub Actions historical job: https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/44925231993/job/136909740974 ; conclusion success; source commit a70de4f0eef0e520cd1cabf1a6dcf63cb4f5ecba.
- Artifact: https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/44925231993/artifacts/14715293182 ; ZIP SHA-256 df0fccdf160adf1b56847811aefcf57fa88ab0c2e9b4ab157b9870bd507828d6. Job log confirms 3 files uploaded: trades.csv, monthly_nav.csv, summary.json.
- Actual logged corrected replay summary: 28 completed trades; realized PF 1.2387453630546115; final NAV 101.69975209984057 from 100 initial (+1.69975209984057%); maximum marked DD 4.211306785463211%; 6 positive, 6 losing, 0 flat IST months. Source reports zero missing 1m minutes and candle frame SHA-256 c6d8aa094646c66b17c092fd68d49ca35d30ff1385cc2b0deb1246d8a4ed9af2. Fees 0.05% notional each side plus GST 18%; zero slippage; funding unmodeled.
- Corrected summary matches prior baseline aggregate metrics exactly; this DOES NOT prove entry-minute stop events absent, because trade-ledger comparison was not performed. Artifact ZIP has not been independently parsed in this iteration. Original and corrected artifacts remain preserved.
- Decision: weak positive, NOT validated economic edge. 28 trades and PF 1.239 are below preferred robustness thresholds; 6/12 months negative. The referenced public Ichimoku repository is not yet pinned to a publisher commit/license, and strategy has independent 2ATR protective overlay; classify as independent variant, not source-faithful reproduction.
- Next: retrieve and compare CSV ledgers, count entry_minute_stop rows, audit fee/mark-to-market month calculations and exact source/license; if audit passes, reject or preregister narrowly motivated 2025-only tests. No BTC2026/ETH testing yet, no live trading or other-family modifications.

## 2026-11-21 — TF-ICH-001 original-versus-corrected artifact audit (iteration 13)

- Downloaded and independently parsed BOTH authentic GitHub Actions artifact ZIPs: original run 44914091290 artifact 14710589580; corrected run 44925231993 artifact 14715293182. Corrected run/job succeeded; the files are actual `trades.csv`, `monthly_nav.csv`, and `summary.json`, not just job-log assertions.
- **Exact trade-ledger comparison: 28/28 rows identical** (all eight columns including entry/exit timestamp, side, price, quantity, net P&L and exit reason). No row differences after the entry-minute stop correction. **Zero stop exits within the first 60 seconds of entry**; 10 stop exits, 18 signal exits. This demonstrates no effect on the observed baseline sample, not that the old simulator bug was harmless generally.
- Independently recomputed from unmodified corrected trades: 9 wins, 19 losses; gross winning NET-after-fee P&L +8.8192708963, absolute losing NET-after-fee P&L 7.1195187965, PF 1.238745363; net +1.69975209984 on initial NAV 100. Monthly compounded returns yield final NAV 101.69975209984, equal to initial NAV plus sum of net trade P&L to floating tolerance.
- Full IST monthly NAV returns (%), January–December: +0.211911, +0.030522, -0.552006, -0.244164, +0.732160, -0.416913, +1.466373, -0.703421, -0.942705, +0.441554, +3.560606, -1.796028. 6 positive / 6 negative; max reported DD 4.2113%.
- Caveats: monthly CSV has entries, not monthly realized PF; independently audited monthly PF and fee-by-fee cash ledger are still missing. Monthly NAV path can be arithmetically reconciled but intramonth MTM path has not been independently replayed from minute bars. Source license/commit not pinned and independent 2ATR stop overlay means NOT source-faithful. 2026/ETH untested; no funding, zero slippage. **No claim of credible edge** with 28 trades/PF 1.239.
- Decision: keep TF-ICH-001 as an audited weak-positive independent variant, NOT promoted. Next priority: source provenance and exit/fee audit, then either reject or preregister very small BTC2025-only regime tests. No main/other-family/live changes.

## 2026-11-22 — TF-ICH-001 realized-PF accounting rerun (iteration 14)

- Recovered the completed corrected historical replay and original-vs-corrected 28-trade ledger audit (iteration 13). No unrelated strategy started.
- Historical evidence remains the corrected completed job https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/44925231993/job/136909740974 with 28 trades, PF 1.238745, +1.699752% NAV, 4.2113% reported DD, 6/12 positive months. These are NOT new results.
- Found a reporting gap: monthly_nav.csv reports mark-to-market NAV return and entries but not realized PF or exit counts. Added exit-month realized net winning and losing sums, closed-trade count and realized PF to each IST month; explicitly separate realized trade PF from monthly MTM return. No strategy signals, sizing, fills or costs changed. Corrected misleading source-faithful script docstring to state independently implemented variant. Script commit 0ca4c400f64d902099be29e7057bd3cc1a87b1ed.
- Script change matches isolated branch push workflow trigger. Actual new run/job/artifact is NOT yet confirmed; no claim that this rerun completed. Next: inspect registered run and archived monthly_nav.csv, verify realized sums against the 28 original trades, preserve artifact hash. Then resolve publisher source/license or classify NOT REPRODUCIBLE and move to distinct trend persistence candidate.
- Limitations remain: 28 trades insufficient for robust edge, source commit/license unverified, 2026/ETH not run, funding unmodeled. No main, other-family or live changes.

## 2026-11-22 — TF-ICH-001 independent monthly realized-PF artifact audit (iteration 15)

- Retrieved and parsed the actual corrected-run GitHub Actions ZIP artifact 14715293182 from successful run https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/44925231993; verified ZIP SHA-256 `df0fccdf160adf1b56847811aefcf57fa88ab0c2e9b4ab157b9870bd507828d6`. This is a retrospective audit of the previously completed historical run, **not a newly completed backtest**.
- Calculated exit-month realized PF independently from the immutable 28-row `trades.csv`, and kept it distinct from the archived `monthly_nav.csv` mark-to-market returns. Columns below: IST month | NAV % | exits | realized PF | realized net USD:
  - 2025-01 | +0.2119 | 1 | +infinity (no losses) | +0.21191
  - 2025-02 | +0.0305 | 3 | 1.061 | +0.03059
  - 2025-03 | -0.5520 | 4 | 0.498 | -0.55334
  - 2025-04 | -0.2442 | 1 | 0.000 | -0.24341
  - 2025-05 | +0.7322 | 3 | 2.387 | +0.72810
  - 2025-06 | -0.4169 | 2 | 0.000 | -0.41764
  - 2025-07 | +1.4664 | 3 | 2.803 | +1.46280
  - 2025-08 | -0.7034 | 2 | 0.000 | -0.57569
  - 2025-09 | -0.9427 | 2 | 0.000 | -1.08380
  - 2025-10 | +0.4416 | 1 | +infinity (no losses) | +0.43961
  - 2025-11 | +3.5606 | 2 | +infinity (no losses) | +3.56058
  - 2025-12 | -1.7960 | 4 | 0.000 | -1.85996
- Accounting decomposition independently calculated from archived fill prices and quantities: gross before fees +2.4629726321 NAV USD units, two-sided exchange fees plus GST -0.7632205322, net +1.6997520998. Total exit-month realized P&L reconciles to final NAV 101.6997521 from 100 initial.
- Differences between exit-month realized P&L and monthly NAV returns (notably Aug/Sep) are expected when positions span calendar boundaries; do not conflate realized PF and mark-to-market performance.
- Current isolated script now includes monthly realized PF fields (commit 0ca4c40), but **no new run for that reporting change is independently verified**. Connector's commit-run lookup only indexes PR-triggered runs and returned empty for d48cf63; this is inconclusive for push workflows.
- Decision: TF-ICH-001 remains weak-positive, non-source-faithful and unpromoted (28 trades, 6/12 profitable months, PF 1.239). Publisher source/license and independent minute-level DD remain unresolved. Next action: verify actual latest workflow job/artifact for the reporting change; if unavailable, use a registered isolated runner rather than asserting it completed. No BTC2026/ETH, no live orders.

## 2026-11-22 — TF-ICH-001 source OHLC integrity replay (iteration 16)

- Recovered completed corrected BTC2025 baseline and the latest reporting-only script change; no unrelated strategy started. Original immutable baseline: 28 trades, PF 1.238745, net NAV +1.699752%, 6/12 positive IST months, zero slippage, two-sided fees+GST, funding unmodeled.
- Discovered a further source-quality validation gap: the replay checked missing minutes in the active 2025 period but did not explicitly reject duplicate/out-of-order timestamps, NaN/inf/non-positive OHLC, or logically impossible high/low bounds before 4H aggregation and minute stop evaluation. Such malformed rows could produce invalid stops or signals.
- Added fail-closed OHLC/timestamp checks in isolated script commit `f723b75f60a3135136eb8ca39f66ba69a67a640f`. Strategy logic, trade sizing, risk and fee assumptions unchanged. Script path matches the isolated workflow push trigger, constituting a new historical replay launch attempt, **not a confirmed completed run**.
- This is an independent research variant, not a source-faithful Ichimoku reproduction. Latest monthly-reporting change also still lacks a verified new job/artifact. Do not claim new PF, monthly numbers or data-quality pass until the actual GitHub Actions run and CSV/JSON artifacts are inspected.
- Next: locate the new registered push run and confirm its job, source commit, source-quality guard outcome and monthly realized-PF artifact; if run is not registered, execute via a registered isolated runner with the authentic archive. Verify 1m MTM drawdown and source provenance. No 2026/ETH, main/other-family edits or live trading.

## 2026-11-22 — source triage / branch-run recovery (run 11)

- Confirmed branch historical Actions listing has 18 runs, latest successful historical run 44952126471 at d5c667b; baseline unchanged. Screened 3 public leads: Freqtrade triple-Supertrend (novelty pending), Freqtrade Heracles (reject outside trend family), xy3293 Supertrend/EMA/ADX catalog (duplicate/source pin pending). Source definitions, license caveats and links in `SOURCE_TRIAGE_20261122_RUN11.md` (commit a075844).
- **0 new distinct historical strategy backtests; 0 variants; 0 new verified P&L.** Source commit/dependency pinning and authentic historical execution still required. No live trading or other-family changes.
