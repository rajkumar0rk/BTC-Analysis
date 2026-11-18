#!/usr/bin/env python3
"""Cloud-only Delta India market microstructure data acquisition.

Historical supported by /v2/history/candles:
  MARK:ETHUSD   1m (mark price candles, *not* executions)
  OI:ETHUSD     5m (open-interest candles, *not* individual positions)
  FUNDING:ETHUSD 1h (funding-rate observations, *not* realized payments)

Real-time REST snapshots only:
  /v2/l2orderbook/ETHUSD (point-in-time L2 order book)
  /v2/trades/ETHUSD     (RECENT prints, not full history/stream)
  /v2/tickers/ETHUSD    (current ticker)

No purported historical L2/trade/liquidation archive is generated.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime, timedelta, timezone
import csv
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import random
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

API="https://api.india.delta.exchange"
ROOT=Path("data/delta_india/ETHUSD/institutional")
START=datetime(2025,1,1,tzinfo=timezone.utc)
SYMBOL="ETHUSD"
HISTORY={
    "mark_1m":{"symbol":"MARK:ETHUSD","resolution":"1m","seconds":60},
    "open_interest_5m":{"symbol":"OI:ETHUSD","resolution":"5m","seconds":300},
    "funding_1h":{"symbol":"FUNDING:ETHUSD","resolution":"1h","seconds":3600},
}
FIELDS=("time","open","high","low","close","volume")
MAX_BARS_PER_REQ=1400
HTTP_TIMEOUT=35
MAX_ATTEMPTS=6
API_INTERVAL=0.20

def iso(t):
    return t.astimezone(timezone.utc).isoformat().replace("+00:00","Z")

def parse_iso(z):
    return datetime.fromisoformat(str(z).replace("Z","+00:00")).astimezone(timezone.utc)

def http_get(path, params=None):
    url=API+path
    if params:url+="?"+urlencode(params)
    for attempt in range(MAX_ATTEMPTS):
        try:
            request=Request(url,headers={"Accept":"application/json","User-Agent":"btc-analysis-institutional-history/1.0"})
            with urlopen(request,timeout=HTTP_TIMEOUT) as res:
                raw=res.read()
                if len(raw)>12_000_000:raise RuntimeError("Unexpected oversized JSON response")
                data=json.loads(raw)
            if not isinstance(data,dict) or data.get("success") is not True or "result" not in data:
                raise RuntimeError("Non-success API response for "+path+": "+repr(data)[:500])
            return data["result"]
        except (HTTPError,URLError,TimeoutError,OSError,json.JSONDecodeError) as ex:
            code=getattr(ex,"code",None)
            if code is not None and code not in (408,429,500,502,503,504):
                raise RuntimeError(f"Permanent HTTP {code} at {path}: {ex}") from ex
            if attempt+1==MAX_ATTEMPTS:raise RuntimeError(f"{url}: after {MAX_ATTEMPTS} tries: {ex}") from ex
            pause=min(25.,2.**attempt+random.random())
            print(f"WARN retry {attempt+1}/{MAX_ATTEMPTS} {path} after {type(ex).__name__} {pause:.1f}s",flush=True)
            time.sleep(pause)

def read_csv_gzip(path):
    if not path.exists():return {}
    with gzip.open(path,"rt",newline="",encoding="utf-8") as file:
        return {int(r["time"]):r for r in csv.DictReader(file)}

def write_csv_gzip(path,rows):
    """Stable gzip bytes on repeated runs; do not rewrite unchanged archives."""
    path.parent.mkdir(parents=True,exist_ok=True)
    buf=io.StringIO(newline="")
    writer=csv.DictWriter(buf,fieldnames=FIELDS,lineterminator="\n")
    writer.writeheader()
    for t in sorted(rows):
        writer.writerow({k:rows[t][k] for k in FIELDS})
    tmp=path.with_name(path.name+".tmp")
    with open(tmp,"wb") as target:
        with gzip.GzipFile(filename="",fileobj=target,mode="wb",mtime=0,compresslevel=6) as archive:
            archive.write(buf.getvalue().encode("utf-8"))
    if path.exists() and hashlib.sha256(path.read_bytes()).digest()==hashlib.sha256(tmp.read_bytes()).digest():
        tmp.unlink()
    else:
        os.replace(tmp,path)

def validate_ohlc(z,seconds,start_ts,end_ts):
    if not isinstance(z,list):raise RuntimeError("Historical candles response is not list")
    rows={}
    for raw in z:
        if not isinstance(raw,dict):raise RuntimeError("Bad candle row")
        t=int(raw["time"])
        if not (start_ts<=t<end_ts):continue
        # Do not guess timestamps or fill missing candles.
        if t%seconds:raise RuntimeError(f"Unexpected timestamp alignment {t} interval={seconds}")
        values={"time":str(t)}
        for k in FIELDS[1:]:
            value=raw.get(k)
            if value is None and k=="volume":
                values[k]=""  # Non-traded MARK/OI/FUNDING candles have no volume; do not fabricate zero.
                continue
            if value is None:raise RuntimeError(f"Missing {k} at {t}")
            f=float(value)
            if not math_isfinite(f):raise RuntimeError(f"Nonfinite {k} at {t}")
            values[k]=str(value)
        if t in rows and rows[t]!=values:raise RuntimeError(f"Inconsistent duplicate candle {t}")
        rows[t]=values
    return rows

def math_isfinite(x):
    return x!=float("inf") and x!=-float("inf") and x==x

def backfill(until_exclusive,force=False):
    stop=int(until_exclusive.timestamp())
    if stop<=int(START.timestamp()):raise RuntimeError("Invalid range")
    manifest={
        "source":"Delta Exchange India public REST v2/history/candles",
        "base_url":API,"symbol":SYMBOL,"generated_utc":iso(datetime.now(timezone.utc)),
        "requested_start_utc":iso(START),"requested_end_exclusive_utc":iso(until_exclusive),
        "real_orderbook_history_available":False,
        "real_trade_tape_history_available":False,
        "liquidation_history_available":False,
        "series":{}}
    for label,config in HISTORY.items():
        frequency=config["seconds"]
        name=config["symbol"]
        directory=ROOT/"history"/label
        stored={}
        if directory.exists() and not force:
            for p in sorted(directory.glob("????-??.csv.gz")):stored.update(read_csv_gzip(p))
        cursor=int(START.timestamp())
        # Only request missing 1,400-candle slices. Rerunning is incremental
        # based on true observed data, but sparse funding may require refetch.
        fetched=0
        requests=0
        errors=[]
        while cursor<stop:
            endpoint_end=min(stop,cursor+MAX_BARS_PER_REQ*frequency)
            # Avoid gaps on resumption: skip only when complete every expected
            # candle exists, not on funding sparse observations.
            block_complete=all(t in stored for t in range(cursor,endpoint_end,frequency))
            if block_complete and not force:
                cursor=endpoint_end
                continue
            params={"symbol":name,"resolution":config["resolution"],"start":cursor,
                    "end":endpoint_end-1}
            try:
                response=http_get("/v2/history/candles",params)
                rows=validate_ohlc(response,frequency,cursor,endpoint_end)
            except Exception as exc:
                # Never imply silent completeness. Fail and retain any already
                # successful series in memory; runner exits nonzero to show red.
                raise RuntimeError(f"Failed {label} at {iso(datetime.fromtimestamp(cursor,timezone.utc))}: {exc}") from exc
            for t,bar in rows.items():
                stored[t]=bar
            fetched+=len(rows)
            requests+=1
            if requests%40==0:
                print(f"PROGRESS {label} requests={requests} fetched={fetched} cursor={cursor}",flush=True)
            cursor=endpoint_end
            time.sleep(API_INTERVAL)
        permonth=defaultdict(dict)
        for ts,row in stored.items():
            if int(START.timestamp())<=ts<stop:
                month=datetime.fromtimestamp(ts,timezone.utc).strftime("%Y-%m")
                permonth[month][ts]=row
        partition_meta=[]
        for month,rows in sorted(permonth.items()):
            path=directory/(month+".csv.gz")
            write_csv_gzip(path,rows)
            times=sorted(rows)
            partition_meta.append({
                "partition":str(path),
                "rows":len(rows),
                "first_utc":iso(datetime.fromtimestamp(times[0],timezone.utc)),
                "last_utc":iso(datetime.fromtimestamp(times[-1],timezone.utc)),
                "compressed_bytes":path.stat().st_size})
        all_t=sorted(t for p in permonth.values() for t in p)
        total_expected=(stop-int(START.timestamp()))//frequency
        total_actual=len(all_t)
        info={"native_source_symbol":name,"resolution":config["resolution"],
            "path_prefix":str(directory),"api_requests":requests,
            "rows_fetched_this_run":fetched,"rows_saved":total_actual,
            "expected_dense_intervals":total_expected,
            "coverage_pct":round(100*total_actual/total_expected,4) if total_expected else 0,
            "missing_dense_intervals":max(total_expected-total_actual,0),
            "earliest_utc":iso(datetime.fromtimestamp(all_t[0],timezone.utc)) if all_t else None,
            "latest_utc":iso(datetime.fromtimestamp(all_t[-1],timezone.utc)) if all_t else None,
            "partitions":partition_meta,
            "note":"Sparse funding observations are not forward-filled. Empty intervals do NOT mean zero funding." if label.startswith("funding") else
                   "Any gaps remain gaps: no fabricated rows or interpolation."}
        manifest["series"][label]=info
        print("SERIES",label,"rows",total_actual,"coverage",info["coverage_pct"],"requests",requests,flush=True)
    ROOT.mkdir(parents=True,exist_ok=True)
    (ROOT/"history_manifest.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    return manifest

def snapshot():
    now=datetime.now(timezone.utc)
    day=now.strftime("%Y-%m-%d")
    d=ROOT/"live_snapshots"
    d.mkdir(parents=True,exist_ok=True)
    file=d/(day+".jsonl.gz")
    request_data={}
    urls={
        "level2_book":("/v2/l2orderbook/ETHUSD",{"depth":30}),
        "recent_trades":("/v2/trades/ETHUSD",None),
        "ticker":("/v2/tickers/ETHUSD",None)}
    failures={}
    for category,(path,params) in urls.items():
        try:
            data=http_get(path,params)
            if category=="level2_book":
                if not isinstance(data,dict) or "buy" not in data or "sell" not in data:
                    raise ValueError("L2 response lacks buy/sell")
            elif category=="recent_trades":
                # Public API versions may expose a list rather than a dict
                # with "trades". Preserve actual records only.
                if isinstance(data,list):
                    data={"trades":data,"response_shape":"raw_list"}
                elif isinstance(data,dict) and isinstance(data.get("trades"),list):
                    data={"trades":data["trades"],"response_shape":"trades_object"}
                elif isinstance(data,dict) and isinstance(data.get("result"),list):
                    data={"trades":data["result"],"response_shape":"nested_result"}
                else:
                    detail=(sorted(data.keys()) if isinstance(data,dict) else type(data).__name__)
                    raise ValueError(f"Unrecognized public trades response shape: {detail}")
            request_data[category]=data
        except Exception as exc:
            failures[category]=str(exc)[:500]
        time.sleep(API_INTERVAL)
    record={
        "requested_utc":iso(now),
        "completed_utc":iso(datetime.now(timezone.utc)),
        "venue":"Delta Exchange India","symbol":SYMBOL,
        "source":"Public REST snapshots, NOT a historical or complete streaming feed",
        "data":request_data,"failures":failures,
        "limitations":{"level2_book":"Point-in-time 30 levels per side; historical depth between captures unknown.",
           "recent_trades":"Only trades returned by recent-trades API at this poll; deduplicate; gaps possible.",
           "liquidations":"No complete public market-wide liquidation history; intentionally not fabricated."}}
    # gzip archive append streams is supported and avoids rewriting every
    # previous hourly snapshot; GitHub retains diff of compressed archive.
    with gzip.open(file,"at",encoding="utf-8") as handle:
        handle.write(json.dumps(record,separators=(",",":"),allow_nan=False)+"\n")
    summary={
        "last_snapshot_utc":record["completed_utc"],"archived_path":str(file),
        "available":sorted(request_data),"failed":failures,
        "trade_count_latest_poll":len(request_data.get("recent_trades",{}).get("trades",[])) if isinstance(request_data.get("recent_trades",{}),dict) else 0,
        "orderbook_buy_levels":len(request_data.get("level2_book",{}).get("buy",[])) if isinstance(request_data.get("level2_book",{}),dict) else 0,
        "orderbook_sell_levels":len(request_data.get("level2_book",{}).get("sell",[])) if isinstance(request_data.get("level2_book",{}),dict) else 0}
    (d/"status.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    print("SNAPSHOT",json.dumps(summary),flush=True)
    if len(request_data)==0:raise RuntimeError("All snapshot sources failed; retained error record")
    return summary

def yesterday_utc():
    now=datetime.now(timezone.utc)
    return datetime(now.year,now.month,now.day,tzinfo=timezone.utc)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("mode",choices=["backfill","snapshot","both"])
    p.add_argument("--end-exclusive",help="UTC ISO date, e.g. 2026-10-18; defaults to UTC today")
    p.add_argument("--force",action="store_true")
    a=p.parse_args()
    if a.mode in ("backfill","both"):
        end=parse_iso(a.end_exclusive) if a.end_exclusive else yesterday_utc()
        backfill(end,force=a.force)
    if a.mode in ("snapshot","both"):
        snapshot()

if __name__=="__main__":main()
