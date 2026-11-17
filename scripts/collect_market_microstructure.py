#!/usr/bin/env python3
"""Read-only forward collection of real BTC quotes and funding observations.

Not a 2025 historical order-book reconstruction, maker fill replay, or proof of
profit. No API keys or accounts required. Never submits orders.

REST observations have finite polling latency. Delta depth SIZE is in venue-native
units (usually contracts); Binance Spot depth SIZE is BTC, so NEVER compare size
columns as if the units matched.

Usage:
  python scripts/collect_market_microstructure.py --once
  python scripts/collect_market_microstructure.py --self-test
"""
from __future__ import annotations
import argparse
import datetime as dt
import json
import math
import os
from pathlib import Path
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

USER_AGENT="BTC-Analysis-Forward-Research/1.0"
DELTA_ROOT="https://api.india.delta.exchange"
BINANCE_SPOT_ROOT="https://data-api.binance.vision"
BINANCE_FUTURES_ROOT="https://fapi.binance.com"

def now_utc():
    return dt.datetime.now(dt.timezone.utc)

def iso(x):
    return x.isoformat(timespec="milliseconds").replace("+00:00","Z")

def get_json(url,timeout=12):
    request=urllib.request.Request(url,headers={"Accept":"application/json","User-Agent":USER_AGENT})
    start=time.monotonic()
    try:
        with urllib.request.urlopen(request,timeout=timeout) as response:
            data=response.read(2_000_000)
        if len(data)>=2_000_000:
            raise ValueError("Response exceeds 2 MB safety limit")
        return json.loads(data),round((time.monotonic()-start)*1000),None
    except (urllib.error.URLError,TimeoutError,OSError,ValueError,json.JSONDecodeError) as error:
        return None,round((time.monotonic()-start)*1000),str(error)[:300]

def numeric(value):
    x=float(value)
    if not math.isfinite(x) or x<=0:
        raise ValueError("Invalid positive book price or size")
    return x

def parse_depth(venue,payload,limit=20):
    if venue=="delta_india_perp":
        if not isinstance(payload,dict) or payload.get("success") is not True:
            raise ValueError("Delta success != true")
        data=payload.get("result")
        if not isinstance(data,dict):raise ValueError("Missing Delta result")
        raw_bids=data.get("buy")
        raw_asks=data.get("sell")
        venue_timestamp=data.get("last_updated_at")
        size_unit="delta_native_contracts_not_BTC"
        def extract(level):
            return [numeric(level["price"]),numeric(level["size"])]
    elif venue=="binance_btcusdt_spot":
        data=payload
        if not isinstance(data,dict):raise ValueError("Invalid Binance depth")
        raw_bids=data.get("bids")
        raw_asks=data.get("asks")
        venue_timestamp=data.get("lastUpdateId")
        size_unit="BTC"
        def extract(level):
            return [numeric(level[0]),numeric(level[1])]
    else:raise ValueError("Unknown venue")
    if not isinstance(raw_bids,list) or not isinstance(raw_asks,list):
        raise ValueError("Missing bids/asks")
    bids=[extract(x) for x in raw_bids[:limit]]
    asks=[extract(x) for x in raw_asks[:limit]]
    if not bids or not asks:raise ValueError("Empty order book")
    bids.sort(key=lambda x:-x[0])
    asks.sort(key=lambda x:x[0])
    best_bid=bids[0][0]
    best_ask=asks[0][0]
    if best_bid>=best_ask:raise ValueError("Crossed/locked book snapshot")
    spread=best_ask-best_bid
    mid=(best_bid+best_ask)/2
    return {
        "market_native_size_unit":size_unit,
        "best_bid":best_bid,"best_ask":best_ask,
        "mid":round(mid,4),"spread_points":round(spread,4),
        "spread_bps":round(10000*spread/mid,5),
        "bid_top_level_native_size":bids[0][1],
        "ask_top_level_native_size":asks[0][1],
        "bid_depth_20_native_size":round(sum(x[1] for x in bids),8),
        "ask_depth_20_native_size":round(sum(x[1] for x in asks),8),
        "bids":bids,"asks":asks,
        "source_sequence_or_timestamp":venue_timestamp,
    }

def collect_snapshot():
    collected_at=now_utc()
    urls={
      "delta_india_perp":DELTA_ROOT+"/v2/l2orderbook/BTCUSD?depth=20",
      "binance_btcusdt_spot":BINANCE_SPOT_ROOT+"/api/v3/depth?symbol=BTCUSDT&limit=20",
    }
    books={}
    errors={}
    for venue,url in urls.items():
        started=now_utc()
        payload,latency,error=get_json(url)
        if error:
            errors[venue]=error
            continue
        try:
            parsed=parse_depth(venue,payload)
            parsed["requested_at_utc"]=iso(started)
            parsed["received_at_utc"]=iso(now_utc())
            parsed["http_latency_ms"]=latency
            parsed["source_url"]=url
            books[venue]=parsed
        except (KeyError,ValueError,TypeError,IndexError) as exc:
            errors[venue]="PARSE: "+str(exc)[:250]

    # Published exchange funding rate snapshots are NOT a user's actual cashflow.
    # Delta funding history is an hourly candle series, not a confirmed settlement.
    t=int(now_utc().timestamp())
    delta_fund_url=DELTA_ROOT+"/v2/history/candles?"+urllib.parse.urlencode({
        "resolution":"1h","symbol":"FUNDING:BTCUSD","start":t-4*3600,"end":t})
    b_fund_url=BINANCE_FUTURES_ROOT+"/fapi/v1/fundingRate?symbol=BTCUSDT&limit=3"
    funding={}
    for name,url in (
        ("delta_hourly_funding_rate_candles",delta_fund_url),
        ("binance_usdm_btcusdt_published_funding_events",b_fund_url)
    ):
        payload,latency,error=get_json(url)
        if error:
            errors[name]=error
            continue
        if name.startswith("delta"):
            if not isinstance(payload,dict) or payload.get("success") is not True or not isinstance(payload.get("result"),list):
                errors[name]="Unexpected Delta funding candle response"
                continue
            payload=payload["result"][-5:]
        elif not isinstance(payload,list):
            errors[name]="Unexpected Binance futures funding response"
            continue
        funding[name]={"observations":payload[-5:],"retrieved_at_utc":iso(now_utc()),
                       "http_latency_ms":latency,
                       "classification":("hourly_rate_proxy_not_settled_payment"
                           if name.startswith("delta") else "exchange_published_rate_not_account_payment")}

    quote={}
    if "delta_india_perp" in books and "binance_btcusdt_spot" in books:
        delta=books["delta_india_perp"]
        binance=books["binance_btcusdt_spot"]
        # Long spot at ask, short perp at bid: indicative starting premium.
        # USD vs USDT conversion, two-leg fees, fills and margin NOT accounted for.
        quote={
            "perp_bid_minus_spot_ask_points":round(delta["best_bid"]-binance["best_ask"],4),
            "perp_bid_minus_spot_ask_bps_of_spot_ask":
              round(10000*(delta["best_bid"]-binance["best_ask"])/binance["best_ask"],5),
            "note":"Not executable arbitrage: USD != USDT; fees, margin, queue, FX and synchronized fills missing"
        }
    return {
        "schema_version":1,
        "captured_at_utc":iso(collected_at),
        "snapshot_type":"forward_observed_rest_sample",
        "symbol_mapping":{"delta":"BTCUSD perpetual USD","binance":"BTCUSDT spot USDT"},
        "books":books,"funding":funding,"indicative_spread":quote,
        "errors":errors,
        "funding_settlement_cashflow_verified":False,
        "maker_fill_verified":False,
        "market_making_backtest_ready":False,
    }

def append_record(outdir,record):
    stamp=dt.datetime.fromisoformat(record["captured_at_utc"].replace("Z","+00:00"))
    date=stamp.strftime("%Y-%m-%d")
    folder=outdir/"snapshots"
    folder.mkdir(parents=True,exist_ok=True)
    path=folder/f"{date}.jsonl"
    # Every invocation adds a new real observation, including source errors.
    with path.open("a",encoding="utf8") as fp:
        fp.write(json.dumps(record,sort_keys=True,separators=(",",":"))+"\n")
    return path

def self_test():
    d={"success":True,"result":{"buy":[{"price":"100","size":3}],
        "sell":[{"price":"101","size":4}],"last_updated_at":12345}}
    b={"lastUpdateId":99,"bids":[["98","0.5"]],"asks":[["99","1.0"]]}
    x=parse_depth("delta_india_perp",d)
    y=parse_depth("binance_btcusdt_spot",b)
    assert x["best_bid"]==100 and x["best_ask"]==101
    assert x["market_native_size_unit"]!="BTC"
    assert y["best_bid"]==98 and y["best_ask"]==99
    assert y["market_native_size_unit"]=="BTC"
    try:parse_depth("binance_btcusdt_spot",{"bids":[["100","1"]],"asks":[["99","1"]]})
    except ValueError:pass
    else:raise AssertionError("crossed book should be rejected")
    print("SELF_TEST_PASSED")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--once",action="store_true")
    ap.add_argument("--self-test",action="store_true")
    ap.add_argument("--output-dir",type=Path,default=Path("analysis/forward_microstructure"))
    ap.add_argument("--require-books",action="store_true")
    args=ap.parse_args()
    if args.self_test:
        self_test()
        return
    if not args.once:
        ap.error("Pass --once or --self-test")
    record=collect_snapshot()
    path=append_record(args.output_dir,record)
    print("PUBLIC_MARKET_SNAPSHOT_SAVED",path)
    print("venues",sorted(record["books"]),"funding",sorted(record["funding"]),
          "errors",record["errors"])
    if args.require_books and len(record["books"])!=2:
        sys.exit("FAILED_REQUIRE_BOOKS: data stored for audit, at least one venue unavailable")

if __name__=="__main__":
    main()
