"""US equity screening and Delta liquidity gate for read-only RWA scanner."""
import datetime as dt
import email.utils
import os
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from zoneinfo import ZoneInfo

import pandas_market_calendars as mcal
import yfinance as yf

NY = ZoneInfo("America/New_York")
UTC = dt.timezone.utc
NYSE = mcal.get_calendar("NYSE")
TRUSTED = {"Reuters", "Associated Press", "AP News", "CNBC", "Bloomberg",
           "Financial Times", "The Wall Street Journal", "MarketWatch", "Barron's"}
POSITIVE = (
    r"\b(?:beats?|beat estimates|surges?|soars?|jumps?|rallies|record (?:revenue|profit|sales|orders)|"
    r"raises? (?:guidance|outlook|forecast)|upgrades?|wins? (?:contract|approval)|"
    r"FDA approval|strong (?:earnings|sales)|profit (?:rises|jumps)|new (?:contract|partnership))\b"
)
NEGATIVE = (
    r"\b(?:misses?|falls?|slumps?|plunges?|downgrades?|lawsuit|investigation|"
    r"cuts? (?:guidance|forecast|outlook)|warning|recall|fraud|"
    r"profit (?:falls|drops)|losses widen|weak (?:earnings|demand)|tariff concerns)\b"
)
ALIASES = {"NVDA": ("nvidia",), "TSLA": ("tesla",), "META": ("meta platforms", "meta"),
           "GOOGL": ("alphabet", "google"), "AAPL": ("apple",),
           "SNDK": ("sandisk",), "MU": ("micron",), "AMD": ("advanced micro devices", "amd"),
           "AMZN": ("amazon",), "PLTR": ("palantir",), "WDC": ("western digital",),
           "NBIS": ("nebius",), "LITE": ("lumentum",)}


def number(x):
    try:
        v = float(x)
        return v if -float("inf") < v < float("inf") else None
    except (TypeError, ValueError):
        return None


def stock_session(now_s, start_hour=9, start_minute=30, end_hour=11, end_minute=30):
    """Uses real NYSE sessions, including US DST, holidays and half days."""
    instant = dt.datetime.fromtimestamp(now_s, UTC)
    et = instant.astimezone(NY)
    schedule = NYSE.schedule(start_date=et.date(), end_date=et.date())
    value = {"date_ny": et.date().isoformat(), "time_ny": et.strftime("%H:%M %Z"),
             "active": False, "reason": "NYSE closed (weekend/holiday)",
             "window": "09:30–11:30 America/New_York, capped at early close"}
    if schedule.empty:
        return value
    trading_start = max(schedule.iloc[0]["market_open"].to_pydatetime(),
                        dt.datetime.combine(et.date(), dt.time(start_hour, start_minute), tzinfo=NY).astimezone(UTC))
    trading_end = min(schedule.iloc[0]["market_close"].to_pydatetime(),
                      dt.datetime.combine(et.date(), dt.time(end_hour, end_minute), tzinfo=NY).astimezone(UTC))
    value["active"] = trading_start <= instant < trading_end
    value["reason"] = "NYSE active" if value["active"] else "Outside configured NYSE momentum window"
    return value


def us_stock_metrics(ticker, now_s, minimum_prior_days=3):
    """Actual share-market intraday volume ratio at SAME elapsed NYSE time.

    Data: Yahoo Finance through yfinance (unofficial, rate-limited).
    Float fallback: Yahoo Finance ticker info, with unknown as-of date.
    """
    details = {"source": "Yahoo Finance (yfinance, unofficial/availability not guaranteed)",
               "stock_price_usd": None, "stock_change_session_pct": None,
               "stock_rvol_elapsed": None, "stock_float_shares": None,
               "float_source": None, "float_asof": None,
               "prior_sessions_used": 0, "errors": []}
    now = dt.datetime.fromtimestamp(now_s, UTC).astimezone(NY)
    try:
        stock = yf.Ticker(ticker)
        candles = stock.history(period="10d", interval="5m", prepost=False, auto_adjust=False, raise_errors=True)
        if candles is None or candles.empty:
            raise ValueError("empty Yahoo chart")
        if candles.index.tz is None:
            raise ValueError("timezone-less Yahoo bars")
        candles = candles.copy()
        candles.index = candles.index.tz_convert(NY)
        # NYSE regular session; 5m timestamps label bar start
        candles = candles[(candles.index.time >= dt.time(9,30)) & (candles.index.time < dt.time(16,0))]
        candles = candles[candles.index <= now]
        if candles.empty:
            raise ValueError("no current Yahoo bars")
        today = candles[candles.index.date == now.date()]
        if today.empty or (now - today.index[-1]).total_seconds() > 1200:
            raise ValueError("US stock 5m bars missing/stale")
        previous = candles[candles.index.date < now.date()]
        if previous.empty:
            raise ValueError("no earlier stock sessions")
        dates = sorted(set(previous.index.date))
        prior_date = dates[-1]
        prev_close = number(previous[previous.index.date == prior_date]["Close"].iloc[-1])
        stock_price = number(today["Close"].iloc[-1])
        if prev_close is None or prev_close <= 0 or stock_price is None:
            raise ValueError("invalid underlying stock prices")
        details["stock_price_usd"] = round(stock_price, 4)
        details["stock_change_session_pct"] = round((stock_price / prev_close - 1) * 100, 3)
        # 5m bars are compared by clock-time cut-off, not futures volume.
        cutoff = today.index[-1].time()
        today_vol = number(today["Volume"].sum())
        baselines = []
        for day in dates[-5:]:
            prior = previous[previous.index.date == day]
            prior = prior[prior.index.time <= cutoff]
            volume = number(prior["Volume"].sum())
            # skip a truncated previous session instead of inflating RVOL
            if len(prior) >= len(today) - 1 and volume is not None and volume > 0:
                baselines.append(volume)
        details["prior_sessions_used"] = len(baselines)
        if len(baselines) >= minimum_prior_days and today_vol is not None:
            base = sum(baselines) / len(baselines)
            details["stock_rvol_elapsed"] = round(today_vol / base, 3) if base > 0 else None
        else:
            details["errors"].append("insufficient comparable prior NYSE sessions for volume")
    except Exception as exc:
        details["errors"].append("yahoo_price_volume: " + type(exc).__name__ + ": " + str(exc)[:100])
    try:
        info = yf.Ticker(ticker).get_info()
        shares = number(info.get("floatShares")) if isinstance(info, dict) else None
        if shares is not None and shares > 0:
            details["stock_float_shares"] = int(shares)
            details["float_source"] = "Yahoo Finance via yfinance (as-of not supplied)"
    except Exception as exc:
        details["errors"].append("yahoo_float: " + type(exc).__name__)
    return details


def fmp_float(ticker, key):
    if not key:
        return None
    url = "https://financialmodelingprep.com/stable/shares-float?" + urllib.parse.urlencode(
        {"symbol": ticker, "apikey": key})
    request = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "RWA-Research/2"})
    import json
    with urllib.request.urlopen(request, timeout=14) as response:
        data = json.load(response)
    if not isinstance(data, list) or not data:
        return None
    row = next((r for r in data if r.get("symbol") == ticker), None)
    if not row:
        return None
    value = number(row.get("floatShares"))
    if value is None or value <= 0:
        return None
    return {"shares": int(value), "source": "Financial Modeling Prep /stable/shares-float",
            "asof": row.get("date"), "reference": row.get("source")}


def classify_headline(title, company, ticker):
    """Conservative, explainable headline-only catalyst classification."""
    low = (title or "").lower()
    aliases = ALIASES.get(ticker, (company.lower(), ticker.lower()))
    relevant = any(re.search(r"(?<![a-z])" + re.escape(name) + r"(?![a-z])", low) for name in aliases)
    positive = bool(re.search(POSITIVE, low, re.I))
    negative = bool(re.search(NEGATIVE, low, re.I))
    if not relevant:
        return "unrelated"
    if positive and not negative:
        return "positive_candidate"
    if negative:
        return "negative_or_mixed"
    return "neutral_or_unclear"


def news_candidates(ticker, company, now_s):
    """Publisher-attributed RSS. Positive candidate is NOT verified factual impact."""
    term = '"' + company + '" stock when:2d'
    params = urllib.parse.urlencode({"q": term, "hl": "en-US", "gl": "US", "ceid": "US:en"})
    request = urllib.request.Request("https://news.google.com/rss/search?" + params,
                                     headers={"User-Agent": "Mozilla/5.0 RWAResearch/2"})
    with urllib.request.urlopen(request, timeout=14) as r:
        xml = r.read(400000)
    root = ET.fromstring(xml)
    articles = []
    for item in root.findall("./channel/item"):
        publisher = (item.findtext("source") or "").strip()
        if not any(v.lower() == publisher.lower() for v in TRUSTED):
            continue
        stamp = item.findtext("pubDate")
        try:
            published = email.utils.parsedate_to_datetime(stamp).astimezone(UTC)
        except (TypeError, ValueError, IndexError):
            continue
        hours_old = (dt.datetime.fromtimestamp(now_s, UTC) - published).total_seconds() / 3600
        if not 0 <= hours_old <= 48:
            continue
        title = item.findtext("title") or ""
        articles.append({"title": title, "publisher": publisher, "published_utc": published.isoformat(),
                         "url": item.findtext("link"), "classification": classify_headline(title, company, ticker),
                         "source": "Google News RSS publisher-attributed; HEADLINE ONLY"})
        if len(articles) >= 8:
            break
    return articles


def liquidity(symbol, turnover, delta_func, max_spread_pct=0.35, min_turnover_usd=20000):
    out = {"pass": False, "spread_pct": None, "turnover_usd": turnover, "book_age_seconds": None,
           "best_bid": None, "best_ask": None, "reasons": [],
           "source": "Delta India /v2/l2orderbook/{symbol} (REST snapshot)"}
    try:
        book = delta_func("/v2/l2orderbook/" + symbol, {"depth": 5})
        bids, asks = book.get("buy") or [], book.get("sell") or []
        bid = number(bids[0].get("price")) if bids else None
        ask = number(asks[0].get("price")) if asks else None
        out.update(best_bid=bid, best_ask=ask)
        if bid is None or ask is None or bid <= 0 or ask <= bid:
            out["reasons"].append("missing/crossed/zero bid-ask book")
        else:
            out["spread_pct"] = round(200*(ask-bid)/(ask+bid), 4)
            if out["spread_pct"] > max_spread_pct:
                out["reasons"].append("spread exceeds " + str(max_spread_pct) + "%")
        if not bids or not asks or number(bids[0].get("size")) is None or number(asks[0].get("size")) is None or number(bids[0].get("size")) <= 0 or number(asks[0].get("size")) <= 0:
            out["reasons"].append("empty top-of-book depth")
        # REST L2 book time may be microseconds or milliseconds.
        timestamp = number(book.get("last_updated_at"))
        if timestamp:
            if timestamp > 1e14:
                timestamp /= 1e6
            elif timestamp > 1e11:
                timestamp /= 1000
            out["book_age_seconds"] = round(dt.datetime.now(UTC).timestamp() - timestamp, 1)
            if not -5 <= out["book_age_seconds"] <= 60:
                out["reasons"].append("order book stale")
        else:
            out["reasons"].append("order book timestamp unavailable")
    except Exception as exc:
        out["reasons"].append("orderbook_api_error: " + type(exc).__name__)
    if turnover is None or turnover < min_turnover_usd:
        out["reasons"].append("24h Delta turnover below " + str(min_turnover_usd) + " USD/unknown")
    out["pass"] = not out["reasons"]
    return out


def scan_one(t, ticker, company, now_s, key, delta_func, breakout_func, config=None):
    config = config or {}
    symbol = t["symbol"]
    metrics = us_stock_metrics(ticker, now_s)
    errors = list(metrics["errors"])
    if key:
        try:
            f = fmp_float(ticker, key)
            if f:
                metrics.update(stock_float_shares=f["shares"], float_source=f["source"], float_asof=f["asof"],
                               float_reference=f["reference"])
            else:
                errors.append("FMP shares-float unavailable (retained Yahoo fallback if present)")
        except Exception as exc:
            errors.append("FMP_float: " + type(exc).__name__)
    try:
        articles = news_candidates(ticker, company, now_s)
    except Exception as exc:
        articles = []
        errors.append("trusted_news: " + type(exc).__name__)
    turnover = number(t.get("turnover_usd"))
    liquidity_result = liquidity(symbol, turnover, delta_func,
                                 config.get("max_spread_pct", 0.35), config.get("min_turnover_usd", 20000))
    try:
        data = delta_func("/v2/history/candles",
                          {"resolution": "1m", "symbol": symbol, "start": now_s-5400, "end": now_s})
        pattern = breakout_func(data, now_s)
    except Exception as exc:
        pattern = {"signal": False, "reason": "Delta 1m candle unavailable"}
        errors.append("delta_candles: " + type(exc).__name__)
    stock_float = metrics["stock_float_shares"]
    stock_price = metrics["stock_price_usd"]
    move = metrics["stock_change_session_pct"]
    rvol = metrics["stock_rvol_elapsed"]
    positive_news = [n for n in articles if n["classification"] == "positive_candidate"]
    checks = {
        "underlying_stock_2_to_20_usd": None if stock_price is None else 2 <= stock_price <= 20,
        "underlying_stock_gain_at_least_10pct": None if move is None else move >= 10,
        "underlying_stock_elapsed_rvol_at_least_5x": None if rvol is None else rvol >= 5,
        "underlying_float_below_20m": None if stock_float is None else stock_float < 20000000,
        "relevant_positive_headline_candidate": bool(positive_news),
        "delta_first_pullback_confirmed": bool(pattern.get("signal")),
        "delta_liquidity_pass": liquidity_result["pass"],
    }
    status = ("WATCHLIST_MANUAL_NEWS_REVIEW" if all(c is True for c in checks.values())
              else "REJECTED" if any(c is False for c in checks.values())
              else "INCOMPLETE")
    return {
        "symbol": symbol, "underlying": ticker, "company": company,
        "stock": metrics, "delta_change_24h_pct": number(t.get("ltp_change_24h")),
        "delta_turnover_usd": turnover, "liquidity": liquidity_result,
        "news": articles, "positive_headlines": positive_news,
        "first_pullback": pattern, "checks": checks, "status": status, "errors": errors,
        "caveat": "Headline polarity is lexical only; manually verify news source, timing and relevance before trading.",
    }
