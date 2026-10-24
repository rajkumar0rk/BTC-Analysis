# ChatGPT manual review prompt — Delta India RWA momentum scanner V2

This file is intended for **manual copy/paste into a new ChatGPT conversation** after a GitHub Actions scan. It does not place orders.

## What to give ChatGPT (choose one)

**Option A — GitHub connector connected (easiest):** Copy the prompt below. Optionally replace `<RUN_URL>` with the exact latest **completed** workflow run link. ChatGPT can attempt to read the connected **private** repository directly.

**Option B — ChatGPT cannot read your private GitHub artifact:** Open:
https://github.com/rajkumar0rk/BTC-Analysis/actions/workflows/scan-delta-rwa-momentum.yml

Select the relevant completed run → find **Artifacts** → download `rwa-momentum-scan-v2` → unzip → upload BOTH `results.json` and `summary.md` to ChatGPT along with the prompt below. Include the run URL. **Do not provide any account passwords or API keys.**

**Optional extra context:** If you want to evaluate an individual Delta futures entry, provide a timestamped Delta chart screenshot (1-minute and 5-minute) and order-book bid/ask screenshot, plus exact symbol. Screenshots and live quotes are optional and must not override timestamped source data silently.

**Before treating a report as current:** Confirm the report was generated during NYSE 09:30–11:30 America/New_York on a real trading day. GitHub can run late. A report from `MARKET_CLOSED_NO_SCAN`, `AFTER_HOURS_RESEARCH_ONLY`, or 20+ minutes ago is *not a fresh intraday setup*.

## COPY FROM HERE — manual analysis prompt

You are reviewing my **Delta Exchange India RWA stock futures momentum research scanner**, inspired by Ross Cameron's US-stock first-pullback strategy. I want a disciplined, evidence-backed analysis, **not an invented BUY/SELL tip**.

### Repository / data to inspect

- GitHub private repo: https://github.com/rajkumar0rk/BTC-Analysis
- Folder: `rwa_scanner/`
- Workflow: `Scan Delta RWA momentum`
- Workflow file: `.github/workflows/scan-delta-rwa-momentum.yml`
- Workflow runs: https://github.com/rajkumar0rk/BTC-Analysis/actions/workflows/scan-delta-rwa-momentum.yml
- Artifact: `rwa-momentum-scan-v2` containing `results.json` and `summary.md`
- Optional exact run link: `<RUN_URL>` (if absent, find the latest completed run relevant to today's NYSE session)
- My intended review time: `<REVIEW_TIME_IST_OR_NEW_YORK>` (if absent, use the current local date/time and disclose it)

**First:** use my connected GitHub integration to locate the latest completed run and obtain `results.json` and `summary.md`; inspect job logs for errors or gaps when useful. If those files are attached in this chat, read the attachments instead. If you cannot access the private repo or ZIP contents, **tell me exactly which file(s) are missing and ask for the artifact upload**; do not manufacture numeric results from a run-status page.

### 1. Validate run, session, and data freshness

Show the run URL/ID, Git commit SHA if available, workflow conclusion, scan generated timestamp in both **New York ET and IST**, session status, and whether the scanner actually evaluated stocks (`scanned`) versus exited because of `MARKET_CLOSED_NO_SCAN`.

- Verify NYSE trading day and holiday/early-close/DST rules. 9:30 AM ET is 7:00 PM IST during EDT or 8:00 PM IST during EST.
- A completed GitHub Action means the software executed; it **does not automatically mean stock/news/float data were successfully populated or a trade exists**.
- If scan age exceeds **20 minutes**, or it was not run during the relevant NYSE session, label it **STALE / RESEARCH ONLY**, not an active entry.
- A 9:45 AM ET ChatGPT review may only have a 9:35 AM ET scan. State the scanner's **actual data timestamp** rather than pretending it is a 9:45 AM snapshot.
- State how many mapped contracts were discovered, how many checked, and how many had complete market data.

### 2. Evaluate ALL checks on the *underlying US stock* versus Delta futures

Make a clear table with each screened Delta contract, its corresponding **actual US share symbol**, and these fields (display N/A when missing):

- US stock latest price and previous-close-based **current session** % change (not Delta futures 24h change).
- US stock **elapsed-time relative volume** (today's US share session-to-date volume / comparable elapsed-time volumes on prior NYSE sessions). Show baseline days used. Original strategy target >=5x.
- Actual US public-float shares, source and as-of date when known; filter <20 million. **Do not substitute circulating-token supply, futures open interest, or 24h derivatives volume for float.**
- Original Ross-style stock-price range USD 2–20 and underlying share price gain >=10%.
- Recent company news: headline, publisher, publication date/time, article URL, relevant company, and *provisional* catalyst assessment (positive / negative / mixed / unclear). Headline-keyword classification is **not proof** of positive news; review the article via reliable reporting if accessible.
- Delta RWA futures symbol, Delta 24h change and USD 24h turnover (clearly label as futures data, NOT underlying stock metrics).
- Delta L2 best bid/ask, spread percentage, best-level size, book timestamp/age, liquidity pass/fail and the reason for failure. Do not assume contract is liquid solely because the US stock is liquid.
- 1-minute first-pullback status, closed-candle timestamp, breakout trigger, pullback low/invalidating price, previous impulse high, theoretical reward/risk, and whether setup is already expired or invalid. A 1m **closed-candle** signal is different from an intrabar stop order and may arrive late.
- Every `checks` boolean/null, errors, and missing fields. Separate **true / false / unknown**; never convert unknown to a pass.

Current scanner hard filters: actual US stock price $2–$20; session gain >=10%; comparable US stock volume >=5x; float <20M; at least one potentially positive attributed news headline; Delta first pullback confirmed; Delta spread <=0.35%, fresh nonempty order book and Delta 24h USD turnover >=20,000. These are research heuristics, not established profitable rules.

### 3. Output format I want

A. **Run health** — success/failure, timestamp, NYSE market open/closed, fresh/stale, completeness and coverage.

B. **Ranked shortlist** — strongest research candidates first, with actual numbers and a table of pass/fail/unknown conditions. Rank by strongest *documented* evidence (underlying price movement, true stock RVOL, news catalyst quality, Delta liquidity and valid pullback); don't rank missing-data assets as confirmed matches.

C. **Per-candidate explanation** — why it qualified or failed, specific headline and source, risks (spread, order depth, false breakouts, gaps, leverage, and futures basis).

D. **Trade setup only when supported** — if a *fresh* and *complete* setup exists, describe **hypothetical** entry trigger, pullback invalidation/stop, previous-high target, reward/risk before and after estimated fees/slippage if known. If fees, contract value or slippage are unknown, don't invent net profitability. **No auto-orders, no guaranteed profits.**

E. **Bottom line** — clearly say one of: (1) qualifying watchlist candidates to review manually, (2) no candidates matched, (3) market closed/no active scan, or (4) incomplete/unavailable data. Give concrete next actions for any blockers.

F. **Sources** — link to exact GitHub run/artifact plus timestamps, and link to the actual financial news articles when accessible. If article contents weren't read, mark news as *headline only*.

### Critical rules

1. Do not confuse the **NYSE cash market** with Delta India's near-continuous crypto/RWA futures market; prices, volumes and liquidity can differ.
2. Do not describe a previously run scanner as live real-time market data.
3. **No forced trades:** zero-trade days are fine. If none qualify, say so.
4. Do not assume `FMP_API_KEY` is set or Yahoo/Google News data works. Missing or rate-limited sources must be called out.
5. Never request an API secret in chat; setup belongs in GitHub Actions secrets. Do not trigger a new run or place an order unless I explicitly ask.
6. Prefer accurate and auditable observations over optimistic trading advice.

## END MANUAL ANALYSIS PROMPT
