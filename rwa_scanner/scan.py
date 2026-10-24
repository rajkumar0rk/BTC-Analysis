#!/usr/bin/env python3
"""Read-only Delta India RWA futures momentum scan. No order APIs."""
import argparse
import datetime as dt
import json
import os
import statistics
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

DELTA = "https://api.india.delta.exchange"
FMP = "https://financialmodelingprep.com/stable"
# Explicit underlying equity mapping; do not infer equity names from suffixes.
EQUITIES = {
    "AAPLXUSD": ("AAPL", "Apple"),
    "AMDBUSD": ("AMD", "AMD"),
    "AMZNXUSD": ("AMZN", "Amazon"),
    "ARMBUSD": ("ARM", "Arm Holdings"),
    "BABABUSD": ("BABA", "Alibaba"),
    "COINXUSD": ("COIN", "Coinbase"),
    "CRCLXUSD": ("CRCL", "Circle"),
    "GOOGLXUSD": ("GOOGL", "Alphabet"),
    "HOODBUSD": ("HOOD", "Robinhood"),
    "INTCBUSD": ("INTC", "Intel"),
    "LITEBUSD": ("LITE", "Lumentum"),
    "METAXUSD": ("META", "Meta Platforms"),
    "MRVLBUSD": ("MRVL", "Marvell"),
    "MSTRBUSD": ("MSTR", "Strategy"),
    "MUBUSD": ("MU", "Micron"),
    "NBISBUSD": ("NBIS", "Nebius"),
    "NVDAXUSD": ("NVDA", "NVIDIA"),
    "PLTRBUSD": ("PLTR", "Palantir"),
    "RKLBBUSD": ("RKLB", "Rocket Lab"),
    "SNDKBUSD": ("SNDK", "Sandisk"),
    "TSLAXUSD": ("TSLA", "Tesla"),
    "TSMBUSD": ("TSM", "TSMC"),
    "WDCBUSD": ("WDC", "Western Digital"),
}
TRUSTED_PUBLISHERS = ("Reuters", "Associated Press", "AP News", "CNBC", "Bloomberg",
                      "Financial Times", "The Wall Street Journal", "MarketWatch", "Barron's")
UTC = dt.timezone.utc


def get_json(url, params=None):
    if params:
        url = url + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "RWA-research-scanner/1.0"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=18) as resp:
                return json.load(resp)
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
            if attempt < 2 and (not isinstance(exc, urllib.error.HTTPError) or exc.code in (429, 500, 502, 503, 504)):
                time.sleep(attempt + 1)
                continue
            raise


def delta(path, params=None):
    payload = get_json(DELTA + path, params)
    if not isinstance(payload, dict) or payload.get("success") is not True:
        raise RuntimeError("Delta endpoint returned unsuccessful/malformed response: " + path)
    return payload["result"]


def numeric(value):
    try:
        result = float(value)
        return result if result == result and abs(result) != float("inf") else None
    except (ValueError, TypeError):
        return None


def breakout(candles, now_s):
    """Confirmed *closed* 1m breakout after 1-3 bearish pullback candles."""
    bars = []
    for x in candles:
        stamp = numeric(x.get("time"))
        if stamp is None or stamp + 60 > now_s:
            continue
        record = {k: numeric(x.get(k)) for k in ("open", "high", "low", "close", "volume")}
        if any(record[k] is None for k in ("open", "high", "low", "close")):
            continue
        record["time"] = int(stamp)
        bars.append(record)
    bars = list({x["time"]: x for x in bars}.values())
    bars.sort(key=lambda b: b["time"])
    if len(bars) < 25:
        return {"signal": False, "reason": "insufficient_closed_candles", "rvol_1m": None}
    recent = bars[-1]
    baseline = [x["volume"] for x in bars[-21:-1] if x["volume"] is not None]
    rv = round(recent["volume"] / statistics.mean(baseline), 3) if len(baseline) == 20 and statistics.mean(baseline) > 0 and recent["volume"] is not None else None
    base = {"signal": False, "reason": "no_confirmed_first_pullback", "rvol_1m": rv,
            "candle_closed_at_utc": dt.datetime.fromtimestamp(recent["time"] + 60, UTC).isoformat()}
    if now_s - (recent["time"] + 60) > 600:
        base["reason"] = "candles_stale_over_10_minutes"
        return base
    if recent["close"] <= recent["open"]:
        return base
    i = len(bars) - 1
    for k in (1, 2, 3):
        pb = bars[i-k:i]
        impulse = bars[i-k-3:i-k]
        if len(impulse) != 3 or not all(c["close"] > c["open"] for c in impulse):
            continue
        if not all(c["close"] < c["open"] for c in pb):
            continue
        if recent["close"] <= pb[-1]["high"] or bars[-2]["close"] > pb[-1]["high"]:
            continue
        low = min(c["low"] for c in pb)
        peak = max(c["high"] for c in impulse)
        if low < impulse[0]["open"] or low >= peak:
            continue
        trigger = pb[-1]["high"]
        risk = trigger - low
        if risk <= 0:
            continue
        base.update(signal=True, reason="closed_candle_above_pullback_high", trigger=trigger,
                    pullback_low=low, previous_high=peak, theoretical_rr_to_high=round((peak-trigger)/risk, 2),
                    pullback_candles=k, note="Closed candle confirmation only; not a live intrabar fill.")
        return base
    return base


def google_news(company):
    """Publisher-attributed Google News RSS; headline is NOT verified positive."""
    query = '"' + company + '" stock when:2d'
    url = "https://news.google.com/rss/search?" + urllib.parse.urlencode(
        {"q": query, "hl": "en-US", "gl": "US", "ceid": "US:en"})
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 RWAResearch/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        raw = resp.read(500000)
    root = ET.fromstring(raw)
    items = []
    for node in root.findall("./channel/item"):
        publisher = node.findtext("source") or ""
        if not any(name.lower() in publisher.lower() for name in TRUSTED_PUBLISHERS):
            continue
        items.append({"title": node.findtext("title"), "publisher": publisher,
                      "published": node.findtext("pubDate"), "url": node.findtext("link"),
                      "source": "Google News RSS (publisher attribution; article not verified)"})
        if len(items) >= 3:
            break
    return items


def fmp_data(ticker, key):
    def request(path, **params):
        return get_json(FMP + path, {**params, "apikey": key})
    value = {"float_shares": None, "float_updated": None, "stock_price": None, "news": [], "errors": []}
    for name, path, params in (
        ("float", "/shares-float", {"symbol": ticker}),
        ("quote", "/quote", {"symbol": ticker}),
        ("news", "/news/stock", {"symbols": ticker, "limit": 5, "page": 0}),
    ):
        try:
            obj = request(path, **params)
            if not isinstance(obj, list):
                raise ValueError("non-list response; check API subscription or quota")
            if name == "float" and obj:
                x = obj[0]
                value["float_shares"] = numeric(x.get("floatShares"))
                value["float_updated"] = x.get("date")
                value["float_source"] = x.get("source") or "FMP /shares-float"
            elif name == "quote" and obj:
                value["stock_price"] = numeric(obj[0].get("price"))
            elif name == "news":
                value["news"] = [{"title": x.get("title"), "publisher": x.get("publisher"),
                                  "published": x.get("publishedDate"), "url": x.get("url"),
                                  "source": "FMP /news/stock (article not independently checked)"}
                                 for x in obj[:3]]
        except (ValueError, KeyError, urllib.error.URLError, TimeoutError) as exc:
            value["errors"].append(name + ": " + type(exc).__name__)
    return value


def analyze_one(ticker, now_s, key, with_news=True):
    symbol = ticker["symbol"]
    equity, company = EQUITIES[symbol]
    info = {"symbol": symbol, "underlying": equity, "company": company,
            "delta_last": numeric(ticker.get("close") or ticker.get("mark_price")),
            "delta_change_24h_pct": numeric(ticker.get("ltp_change_24h")),
            "delta_turnover_usd": numeric(ticker.get("turnover_usd")),
            "float_shares": None, "stock_price_usd": None, "news": [], "errors": []}
    quotes = ticker.get("quotes") or {}
    bid, ask = numeric(quotes.get("best_bid")), numeric(quotes.get("best_ask"))
    info["spread_pct"] = round(200 * (ask-bid)/(ask+bid), 4) if bid and ask and ask >= bid else None
    try:
        data = delta("/v2/history/candles", {"resolution": "1m", "symbol": symbol,
                                           "start": now_s - 90*60, "end": now_s})
        info["first_pullback"] = breakout(data, now_s)
    except (RuntimeError, urllib.error.URLError, TimeoutError, ValueError) as exc:
        info["first_pullback"] = {"signal": False, "reason": "candle_api_error"}
        info["errors"].append("delta_candles: " + type(exc).__name__)
    if key:
        f = fmp_data(equity, key)
        info["float_shares"] = f["float_shares"]
        info["float_asof"] = f["float_updated"]
        info["float_source"] = f.get("float_source")
        info["stock_price_usd"] = f["stock_price"]
        info["news"] = f["news"]
        info["errors"].extend(f["errors"])
    if with_news and not info["news"]:
        try:
            info["news"] = google_news(company)
        except (ET.ParseError, urllib.error.URLError, TimeoutError, ValueError) as exc:
            info["errors"].append("google_news: " + type(exc).__name__)
    # Use actual equity price/float, NOT Delta futures price/turnover as substitutes.
    checks = {
        "stock_price_2_to_20": None if info["stock_price_usd"] is None else 2 <= info["stock_price_usd"] <= 20,
        "stock_float_under_20m": None if info["float_shares"] is None else info["float_shares"] < 20_000_000,
        "delta_futures_change_10pct": None if info["delta_change_24h_pct"] is None else info["delta_change_24h_pct"] >= 10,
        "delta_1m_volume_5x": None if info["first_pullback"].get("rvol_1m") is None else info["first_pullback"]["rvol_1m"] >= 5,
        "delta_first_pullback_confirmed": info["first_pullback"]["signal"],
        "recent_trusted_publisher_headline": bool(info["news"]),
    }
    info["checks"] = checks
    info["status"] = ("MATCH_ALL_PROXY_CHECKS" if all(v is True for v in checks.values())
                      else "REJECTED" if any(v is False for v in checks.values())
                      else "INCOMPLETE")
    info["caveats"] = ["Delta futures 24h change/1m RVOL are NOT underlying US share change/daily RVOL.",
                       "News headline does not prove a positive catalyst or direct article verification.",
                       "Stock float and price are NOT assumed from Delta futures."]
    return info


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", default="rwa_scanner/output")
    ap.add_argument("--max-symbols", type=int, default=10, help="Most active mapped RWA equities to scan (0=all)")
    args = ap.parse_args()
    now = int(time.time())
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    report = {"generated_utc": dt.datetime.fromtimestamp(now, UTC).isoformat(),
              "market": "Delta Exchange India, RWA stock perpetual futures", "source": DELTA,
              "status": "UNKNOWN", "candidates": [], "missing": [],
              "method": "Ross Cameron-inspired RESEARCH; not original stock-scanner equivalence"}
    try:
        tickers = delta("/v2/tickers", {"contract_types": "perpetual_futures"})
        all_mapped = [t for t in tickers if t.get("symbol") in EQUITIES]
        all_mapped.sort(key=lambda t: numeric(t.get("turnover_usd")) or 0, reverse=True)
        chosen = all_mapped[:args.max_symbols] if args.max_symbols > 0 else all_mapped
        report["mapped_listed_count"] = len(all_mapped)
        report["scanned_count"] = len(chosen)
        key = os.environ.get("FMP_API_KEY", "").strip()
        report["fmp_configured"] = bool(key)
        if not key:
            report["missing"].append("FMP_API_KEY absent; share float & underlying stock price not available; configure repository Actions secret.")
        if not chosen:
            report["status"] = "NO_MATCHING_DELTA_RWA_TICKERS"
        else:
            with ThreadPoolExecutor(max_workers=3) as pool:
                tasks = {pool.submit(analyze_one, t, now, key): t["symbol"] for t in chosen}
                for fut in as_completed(tasks):
                    symbol = tasks[fut]
                    try:
                        report["candidates"].append(fut.result())
                    except Exception as exc:
                        report["candidates"].append({"symbol": symbol, "status": "ERROR", "errors": [type(exc).__name__]})
            report["candidates"].sort(key=lambda d: numeric(d.get("delta_turnover_usd")) or 0, reverse=True)
            report["status"] = "PARTIAL_SCAN" if not key else "SCAN_COMPLETE_WITH_POSSIBLE_PROVIDER_GAPS"
    except Exception as exc:
        report["status"] = "DELTA_API_FAILED"
        report["missing"].append("Delta API unavailable: " + type(exc).__name__ + ": " + str(exc)[:150])
    (output / "results.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    lines = ["# Delta India RWA Momentum Scan", "",
             "Generated: " + report["generated_utc"], "Scan status: **" + report["status"] + "**", "",
             "This is NOT a trade recommendation. Futures proxies do not validate the stock screener.", "",
             "| Delta futures | US stock | 24h Delta change | Delta 1m RVOL | Float shares | Recent news | Pullback | Status |",
             "|---|---|---:|---:|---:|---|---|---|"]
    def display(x):
        return "N/A" if x is None else str(x)
    for c in report["candidates"]:
        p = c.get("first_pullback", {})
        headlines = c.get("news") or []
        lines.append("| " + " | ".join([c["symbol"], c.get("underlying", "?"),
                     display(c.get("delta_change_24h_pct")), display(p.get("rvol_1m")),
                     display(c.get("float_shares")), "yes" if headlines else "no",
                     "YES" if p.get("signal") else "no", c.get("status", "ERROR")]) + " |")
    lines.extend(["", "## Missing / limitations", ""])
    lines.extend("- " + msg for msg in report["missing"])
    lines.extend(["- Stocks and futures are different markets; do not confuse their volume, price or liquidity.",
                  "- Float is only from FMP if permitted by the user's subscription.",
                  "- Headline presence is NOT a positive-news classification.",
                  "- Only closed 1m candles checked, so a live intra-candle trigger may be missed.",
                  "- Candidates are ranked by Delta turnover; not all listed equities are guaranteed to be scanned.",
                  "", "## Source links", "",
                  "- Delta API: https://docs.delta.exchange/",
                  "- FMP float: https://site.financialmodelingprep.com/developer/docs/stable/shares-float",
                  "- FMP stock news: https://site.financialmodelingprep.com/developer/docs/stable/search-stock-news",
                  "- Google News RSS (fallback), publisher names shown in results.json",
                  ""])
    (output / "summary.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    for c in report["candidates"]:
        if c.get("news"):
            print("\nNEWS " + c["symbol"] + ": " + "; ".join((h.get("title") or "")[:150] for h in c["news"][:2]))
    print("\nJSON: " + str(output / "results.json"))
    if report["status"] == "DELTA_API_FAILED":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
