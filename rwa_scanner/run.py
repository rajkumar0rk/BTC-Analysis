#!/usr/bin/env python3
"""NYSE-session read-only RWA stock->Delta futures scanner v2."""
import argparse
import datetime as dt
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from scan import EQUITIES, delta, numeric, breakout
from quality import stock_session, scan_one

UTC = dt.timezone.utc

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="rwa_scanner/output")
    parser.add_argument("--max-symbols", type=int, default=0,
                        help="0=all explicitly mapped live RWA contracts")
    parser.add_argument("--force-after-hours-research", action="store_true",
                        help="Allows data check outside NYSE window, NEVER a trading alert")
    args = parser.parse_args()
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    now = int(time.time())
    session = stock_session(now)
    report = {"generated_utc": dt.datetime.fromtimestamp(now, UTC).isoformat(),
              "version": 2, "session": session, "status": "UNKNOWN",
              "candidates": [], "missing": [],
              "note": "No trade orders. Stock metrics use Yahoo (unofficial), float may use FMP. Data can be delayed.",
              "fmp_configured": bool(os.getenv("FMP_API_KEY", "").strip())}
    if not report["fmp_configured"]:
        report["missing"].append("FMP_API_KEY not set; Yahoo stock float used when available (as-of date unknown).")
    try:
        tickers = delta("/v2/tickers", {"contract_types": "perpetual_futures"})
        chosen = [t for t in tickers if t.get("symbol") in EQUITIES]
        chosen.sort(key=lambda t: numeric(t.get("turnover_usd")) or 0, reverse=True)
        report["discovered"] = len(chosen)
        if args.max_symbols > 0:
            chosen = chosen[:args.max_symbols]
        report["scanned"] = 0
        if not session["active"] and not args.force_after_hours_research:
            report["status"] = "MARKET_CLOSED_NO_SCAN"
            report["missing"].append(session["reason"] + "; rerun during 09:30-11:30 ET.")
        else:
            with ThreadPoolExecutor(max_workers=3) as pool:
                futures = {pool.submit(scan_one, t, *EQUITIES[t["symbol"]], now,
                                       os.getenv("FMP_API_KEY", "").strip(), delta, breakout): t["symbol"] for t in chosen}
                for future in as_completed(futures):
                    symbol = futures[future]
                    try:
                        report["candidates"].append(future.result())
                    except Exception as exc:
                        report["candidates"].append({"symbol": symbol, "status": "ERROR",
                                                     "errors": [type(exc).__name__ + ": " + str(exc)[:100]]})
            report["scanned"] = len(report["candidates"])
            report["candidates"].sort(key=lambda x: x.get("delta_turnover_usd") or 0, reverse=True)
            report["status"] = "SCAN_COMPLETED" if session["active"] else "AFTER_HOURS_RESEARCH_ONLY"
            if not session["active"]:
                report["missing"].append("Market closed: all pattern matches are RESEARCH ONLY (stale US stock bars possible).")
    except Exception as exc:
        report["status"] = "DELTA_API_FAILED"
        report["missing"].append("Delta API: " + type(exc).__name__ + ": " + str(exc)[:120])
    (output/"results.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    rows = ["# US-stock-first Delta India RWA Scanner", "", "Timestamp UTC: " + report["generated_utc"],
            "NYSE: " + session["time_ny"] + " — " + session["reason"], "Run status: **" + report["status"] + "**", "",
            "Only WATCHLIST_MANUAL_NEWS_REVIEW qualifies as a watchlist item, never an auto-order.", "",
            "| Delta futures | US stock | Stock session % | Stock elapsed RVOL | Float | News candidates | Delta liquidity | Pullback | Decision |",
            "|---|---|---:|---:|---:|---:|---|---|---|"]
    for c in report["candidates"]:
        stock = c.get("stock") or {}
        liq = c.get("liquidity") or {}
        def fmt(x):
            return "N/A" if x is None else str(x)
        rows.append("| " + " | ".join([
            c["symbol"], c.get("underlying", ""), fmt(stock.get("stock_change_session_pct")),
            fmt(stock.get("stock_rvol_elapsed")), fmt(stock.get("stock_float_shares")),
            str(len(c.get("positive_headlines") or [])),
            "pass" if liq.get("pass") else "fail", "yes" if (c.get("first_pullback") or {}).get("signal") else "no",
            c.get("status", "ERROR")]) + " |")
    rows += ["", "## Missing / caveats", ""]
    rows += ["- " + x for x in report["missing"]]
    rows += ["- Yahoo Finance through yfinance is an unofficial data source; quote delay, throttling and coverage can vary.",
             "- US stock RVOL compares 5-minute aggregated session-to-date volume against the SAME elapsed time across prior sessions.",
             "- Float from Yahoo may have unknown effective date; FMP is preferred when configured and available.",
             "- News keywords generate review candidates, not validated positive catalysts; review actual articles.",
             "- Delta L2 spread/turnover gate must pass; order-book snapshot age checked when provided.",
             "- NYSE holidays, US DST and configured 09:30–11:30 ET window are enforced.",
             "- No BUY recommendation or order is issued.",
             "", "## Links", "- https://docs.delta.exchange/",
             "- https://pandas-market-calendars.readthedocs.io/",
             "- https://site.financialmodelingprep.com/developer/docs/stable/shares-float"]
    (output/"summary.md").write_text("\n".join(rows)+"\n", encoding="utf-8")
    print("\n".join(rows))
    if report["status"] == "DELTA_API_FAILED":
        raise SystemExit(1)

if __name__=="__main__":
    main()
