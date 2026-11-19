#!/usr/bin/env python3
"""Fail-closed audit for 1m BTC/ETH futures archives before a causal daily backtest.
Usage: python analysis/daily_volatility_risk_budget_btcfirst_20261119_v1/audit_archive.py BTC.csv ETH.csv
This is a data eligibility check, NOT a profitable-strategy backtest.
"""
import csv, gzip, hashlib, json, sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

def timestamp(v):
    s=str(v).strip()
    try:
        f=float(s)
        if f>1e14: f/=1e6
        elif f>1e11: f/=1e3
        return int(f)
    except ValueError:
        return int(datetime.fromisoformat(s.replace("Z","+00:00")).replace(tzinfo=timezone.utc).timestamp()) if "+" not in s and "Z" not in s else int(datetime.fromisoformat(s.replace("Z","+00:00")).timestamp())

def audit(path):
    p=Path(path); digest=hashlib.sha256(); seen=set(); days=Counter(); gaps=0; duplicates=0; reversed_rows=0; invalid=0; prev=None; n=0
    with p.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""): digest.update(chunk)
    with (gzip.open(p,"rt",newline="") if p.suffix==".gz" else p.open(newline="")) as f:
        reader=csv.DictReader(f)
        names={k.lower().strip():k for k in (reader.fieldnames or [])}
        tcol=next((names[x] for x in ("timestamp","time","datetime","start","open_time","unix") if x in names),None)
        required=["open","high","low","close"]
        if not tcol or any(k not in names for k in required):
            raise ValueError("Missing timestamp or OHLC columns; refuse to infer schema")
        for row in reader:
            n+=1
            try:
                t=timestamp(row[tcol])
                o,h,l,c=[float(row[names[k]]) for k in required]
                if t%60 or min(o,h,l,c)<=0 or h<max(o,c,l) or l>min(o,c,h): raise ValueError()
            except (ValueError,TypeError,OverflowError):
                invalid+=1;continue
            if t in seen: duplicates+=1
            seen.add(t)
            if prev is not None:
                if t<prev: reversed_rows+=1
                elif t>prev+60: gaps+=(t-prev)//60-1
            prev=t
            days[datetime.fromtimestamp(t,timezone.utc).strftime("%Y-%m-%d")]+=1
    complete=sum(v==1440 for v in days.values())
    return {"file":str(p),"sha256":digest.hexdigest(),"rows":n,"valid_unique_minutes":len(seen),
            "invalid_ohlc_or_time":invalid,"duplicate_timestamps":duplicates,
            "out_of_order_rows":reversed_rows,"missing_minutes_between_rows":gaps,
            "observed_utc_days":len(days),"complete_1440_minute_days":complete,
            "partial_days":sum(v!=1440 for v in days.values()),
            "first_utc_day":min(days) if days else None,"last_utc_day":max(days) if days else None,
            "eligible_for_causal_test":bool(days and not(invalid or duplicates or reversed_rows or gaps))}

if __name__=="__main__":
    if len(sys.argv)<2: raise SystemExit("Pass BTC archive CSV and optionally ETH archive CSV")
    results=[audit(p) for p in sys.argv[1:]]
    print(json.dumps(results,indent=2))
    if any(not r["eligible_for_causal_test"] for r in results):
        raise SystemExit("INCONCLUSIVE: archive integrity failed; do not publish PnL")
