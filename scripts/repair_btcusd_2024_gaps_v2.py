#!/usr/bin/env python3
"""Retry only missing trade candles with different API window alignment.
Persist mark/funding raw data (previous V26 run retained only reports).
Never replace an observed trade candle with another instrument or fill."""
import concurrent.futures as cf
import csv,gzip,hashlib,json,time,urllib.parse,urllib.request
from pathlib import Path
import pandas as pd
import numpy as np
from sync_delta_btcusd_1m import validate_bar,write_month,COLUMNS
ROOT=Path("data/delta_india/BTCUSD")
OLD=ROOT/"2024_ist_gap_repair"
OUT=ROOT/"2024_verified_archive"
REPORT=Path("analysis/btcusd_2024_gap_repair_v2")
REPORT.mkdir(parents=True,exist_ok=True)
URL="https://api.india.delta.exchange/v2/history/candles"
MONTHS=list(pd.period_range("2024-01","2024-12",freq="M"))
def fetch(symbol,res,a,b):
    url=URL+"?"+urllib.parse.urlencode(dict(symbol=symbol,resolution=res,start=a,end=b))
    for retry in range(6):
        try:
            req=urllib.request.Request(url,headers={"Accept":"application/json","User-Agent":"BTC-Analysis-research/1.0"})
            with urllib.request.urlopen(req,timeout=35) as resp:d=json.load(resp)
            if d.get("success") and isinstance(d.get("result"),list):return d["result"]
            raise ValueError(str(d)[:200])
        except Exception:
            if retry==5:raise
            time.sleep(2**retry)
def stamp(x):return int(pd.Timestamp(x).timestamp())
def bounds(m):
    return stamp(m.start_time.tz_localize("Asia/Kolkata")),stamp((m+1).start_time.tz_localize("Asia/Kolkata"))
def intervals(missing,step):
    if not missing:return []
    out=[];a=b=missing[0]
    for t in missing[1:]:
        if t==b+step:b=t
        else:out.append((a,b));a=b=t
    out.append((a,b));return out
def trade(m):
    a,b=bounds(m);expected=set(range(a,b,60))
    p=OLD/(str(m)+".csv.gz");meta=next(x for x in json.loads((OLD/"manifest.json").read_text())["months"] if x["month"]==str(m))
    assert hashlib.sha256(p.read_bytes()).hexdigest()==meta["archive_sha256"]
    with gzip.open(p,"rt") as f:rows={validate_bar(x):x for x in csv.DictReader(f)}
    assert set(rows)<=expected
    original=len(rows);requests=0;errors=[]
    # The old IST-aligned gap windows returned no bars for most gaps.
    # Query alternate UTC-anchored 24h / 12h windows containing missing
    # timestamps, discard all returned rows outside the remaining gaps.
    for width,offset in ((1440,0),(720,180),(1800,300)):
        missing=expected-rows.keys()
        if not missing:break
        w=width*60;o=offset*60
        windows=sorted({((t-o)//w)*w+o for t in missing})
        for lo in windows:
            hi=lo+w-1;requests+=1
            try:
                for r in fetch("BTCUSD","1m",lo,hi):
                    t=validate_bar(r)
                    if t in expected and t not in rows:rows[t]={k:r[k] for k in COLUMNS}
            except Exception as e:errors.append(str(e)[:200])
            time.sleep(.18)
    sha=write_month(OUT/"trade_1m"/(str(m)+".csv.gz"),rows)
    missing=sorted(expected-rows.keys())
    result=dict(series="trade_1m",month=str(m),expected=len(expected),original=original,recovered=len(rows)-original,observed=len(rows),missing=len(missing),requests=requests,sha256=sha,errors=errors,gaps=intervals(missing,60))
    print("TRADE",str(m),result["recovered"],result["missing"],flush=True);return result
def auxiliary(spec):
    name,symbol,res,step,m=spec
    a,b=bounds(m)
    # Funding partitions are UTC-hour aligned; include the last preceding
    # completed hour in January for causal funding at start of year.
    if step==3600:
        a=(a//step)*step;b=(b//step)*step
        if m.month==1:a-=step
    expected=set(range(a,b,step));rows={};requests=0;errors=[]
    # Fetch only absent observations in follow-up windows, with alternative
    # UTC alignment. First pass is a necessary raw archive download.
    for width,offset in ((1800,0),(1440,120),(720,180)):
        missing=expected-rows.keys()
        if not missing:break
        w=width*step;o=offset*step
        for lo in sorted({((t-o)//w)*w+o for t in missing}):
            requests+=1
            try:
                for r in fetch(symbol,res,lo,lo+w-1):
                    t=int(r["time"])
                    if t not in expected or t in rows:continue
                    vals=[float(r[k]) for k in ("open","high","low","close")]
                    if not np.isfinite(vals).all() or vals[1]<max(vals[0],vals[3]) or vals[2]>min(vals[0],vals[3]):raise ValueError("bad OHLC")
                    if name=="mark_1m" and min(vals)<=0:raise ValueError("bad mark")
                    rows[t]=vals
            except Exception as e:errors.append(str(e)[:200])
            time.sleep(.18)
    p=OUT/name/(str(m)+".csv.gz");p.parent.mkdir(parents=True,exist_ok=True)
    z=pd.DataFrame.from_dict(rows,orient="index",columns=["open","high","low","close"]).sort_index();z.index.name="time"
    z.to_csv(p,compression={"method":"gzip","mtime":0})
    missing=sorted(expected-rows.keys())
    result=dict(series=name,month=str(m),expected=len(expected),original=0,recovered=len(rows),observed=len(rows),missing=len(missing),requests=requests,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),errors=errors,gaps=intervals(missing,step))
    print("AUX",name,str(m),len(rows),len(missing),flush=True);return result
def main():
    with cf.ThreadPoolExecutor(max_workers=3) as pool:
        jobs=[pool.submit(trade,m) for m in MONTHS]
        jobs += [pool.submit(auxiliary,(name,sym,res,step,m)) for name,sym,res,step in (("mark_1m","MARK:BTCUSD","1m",60),("funding_1h","FUNDING:BTCUSD","1h",3600)) for m in MONTHS]
        rows=[j.result() for j in jobs]
    df=pd.DataFrame(rows)
    df.drop(columns=["errors","gaps"]).to_csv(REPORT/"coverage.csv",index=False)
    totals={}
    for name,g in df.groupby("series"):
        totals[name]={k:int(g[k].sum()) for k in ("expected","original","recovered","observed","missing","requests")}
        totals[name]["complete_months"]=int((g.missing==0).sum())
        totals[name]["request_errors"]=sum(map(len,g.errors))
    manifest=dict(source="Delta Exchange India public REST native instrument series",partition_timezone="Asia/Kolkata (funding UTC-hour boundaries)",synthetic_rows=0,original_trade_rows_preserved=True,totals=totals,months=rows)
    (OUT/"manifest.json").write_text(json.dumps(manifest,indent=2))
    (REPORT/"quality.json").write_text(json.dumps(totals,indent=2))
    print(json.dumps(totals),flush=True)
if __name__=="__main__":main()
