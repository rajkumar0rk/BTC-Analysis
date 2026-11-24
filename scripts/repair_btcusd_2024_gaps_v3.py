#!/usr/bin/env python3
"""Third targeted recovery: preserve all existing native rows, only retry
remaining 2024 gaps. No synthetic OHLC or proxy substitution."""
import concurrent.futures as cf
import csv,gzip,hashlib,json,time,urllib.parse,urllib.request
from pathlib import Path
import pandas as pd
import numpy as np
from sync_delta_btcusd_1m import validate_bar,write_month,COLUMNS
ROOT=Path("data/delta_india/BTCUSD/2024_verified_archive")
REPORT=Path("analysis/btcusd_2024_gap_repair_v3")
REPORT.mkdir(parents=True,exist_ok=True)
URL="https://api.india.delta.exchange/v2/history/candles"
def fetch(symbol,a,b):
    url=URL+"?"+urllib.parse.urlencode(dict(symbol=symbol,resolution="1m",start=a,end=b))
    for retry in range(6):
        try:
            req=urllib.request.Request(url,headers={"Accept":"application/json","User-Agent":"BTC-Analysis-research/1.0"})
            with urllib.request.urlopen(req,timeout=35) as resp:d=json.load(resp)
            if d.get("success") and isinstance(d.get("result"),list):return d["result"]
            raise ValueError(str(d)[:200])
        except Exception:
            if retry==5:raise
            time.sleep(2**retry)
def intervals(missing):
    if not missing:return []
    out=[];a=b=missing[0]
    for t in missing[1:]:
        if t==b+60:b=t
        else:out.append([a,b]);a=b=t
    out.append([a,b]);return out
def repair(item):
    z=dict(item);name=z["series"];mon=z["month"]
    p=ROOT/name/(mon+".csv.gz")
    assert hashlib.sha256(p.read_bytes()).hexdigest()==z["sha256"]
    month=pd.Period(mon,freq="M")
    start=int(month.start_time.tz_localize("Asia/Kolkata").timestamp())
    end=int((month+1).start_time.tz_localize("Asia/Kolkata").timestamp())
    expected=set(range(start,end,60))
    istrade=name=="trade_1m"
    symbol="BTCUSD" if istrade else "MARK:BTCUSD"
    with gzip.open(p,"rt") as f:rows={int(r["time"]):r for r in csv.DictReader(f)}
    assert set(rows)<=expected and len(rows)==z["observed"]
    original=len(rows);requests=0;errors=[];passes=[]
    # Try new alignments, exact gaps with neighboring bars, and small
    # requests. Each round recomputes remaining missing timestamps.
    plans=[(1998,17,"grid"),(997,43,"grid"),(360,11,"grid"),
           (180,71,"grid"),(960,0,"padded"),(60,29,"grid"),
           (1200,137,"grid")]
    for width,offset,kind in plans:
        missing=expected-rows.keys()
        if not missing:break
        w=width*60;o=offset*60
        if kind=="grid":
            windows=[(lo-1,lo+w+1) for lo in sorted({((t-o)//w)*w+o for t in missing})]
        else:
            windows=[]
            for a,b in intervals(sorted(missing)):
                for lo in range(a,b+60,w):
                    windows.append((lo-120,min(b+120,lo+w+120)))
        before=len(rows)
        for lo,hi in windows:
            requests+=1
            try:
                for r in fetch(symbol,lo,hi):
                    t=int(r["time"])
                    if t not in expected or t in rows:continue
                    if istrade:
                        assert validate_bar(r)==t
                        rows[t]={k:r[k] for k in COLUMNS}
                    else:
                        vals=[float(r[k]) for k in ("open","high","low","close")]
                        if not np.isfinite(vals).all() or min(vals)<=0 or vals[1]<max(vals[0],vals[3]) or vals[2]>min(vals[0],vals[3]):continue
                        rows[t]={"time":t,**dict(zip(("open","high","low","close"),vals))}
            except Exception as e:errors.append(dict(start=lo,end=hi,error=str(e)[:250]))
            time.sleep(.12)
        passes.append(dict(width=width,offset=offset,kind=kind,requests=len(windows),recovered=len(rows)-before,remaining=len(expected)-len(rows)))
        print("PASS",name,mon,json.dumps(passes[-1]),flush=True)
    if len(rows)>original:
        if istrade:sha=write_month(p,rows)
        else:
            df=pd.DataFrame([rows[k] for k in sorted(rows)],columns=["time","open","high","low","close"])
            df.to_csv(p,index=False,compression={"method":"gzip","mtime":0})
            sha=hashlib.sha256(p.read_bytes()).hexdigest()
    else:sha=z["sha256"]
    z.update(original=original,recovered=len(rows)-original,observed=len(rows),missing=len(expected)-len(rows),requests=requests,sha256=sha,errors=errors,gaps=intervals(sorted(expected-rows.keys())),passes=passes)
    return z
def main():
    manifest=json.loads((ROOT/"manifest.json").read_text())
    prior=manifest["totals"]
    missing=[x for x in manifest["months"] if x["missing"]]
    with cf.ThreadPoolExecutor(max_workers=3) as pool:
        repaired=list(pool.map(repair,missing))
    update={(r["series"],r["month"]):r for r in repaired}
    rows=[update.get((x["series"],x["month"]),x) for x in manifest["months"]]
    totals={}
    for name in prior:
        group=[x for x in rows if x["series"]==name]
        extra=[x for x in repaired if x["series"]==name]
        totals[name]=dict(expected=sum(x["expected"] for x in group),observed=sum(x["observed"] for x in group),missing=sum(x["missing"] for x in group),complete_months=sum(x["missing"]==0 for x in group),recovered_this_run=sum(x["recovered"] for x in extra),requests_this_run=sum(x["requests"] for x in extra),request_errors=sum(len(x["errors"]) for x in extra))
    manifest.update(totals=totals,months=rows,prior_totals=prior,synthetic_rows=0,original_trade_rows_preserved=True)
    (ROOT/"manifest.json").write_text(json.dumps(manifest,indent=2))
    (REPORT/"quality.json").write_text(json.dumps(totals,indent=2))
    (REPORT/"passes.json").write_text(json.dumps(repaired,indent=2))
    pd.DataFrame(rows)[["series","month","expected","observed","missing","sha256"]].to_csv(REPORT/"coverage.csv",index=False)
    print("TOTAL",json.dumps(totals),flush=True)
if __name__=="__main__":main()
