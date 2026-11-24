#!/usr/bin/env python3
"""Recover original Delta India BTCUSD 1m artifact files, fill only absent
timestamps using public REST, retain originals and never synthesize candles.
IST monthly partitions; archive separate from UTC main archive."""
import concurrent.futures as cf
import csv,gzip,hashlib,json,time
from pathlib import Path
from datetime import datetime,timezone
import pandas as pd
from sync_delta_btcusd_1m import read_window,validate_bar,write_month,COLUMNS
OLD=Path("_existing_2024")
OUT=Path("data/delta_india/BTCUSD/2024_ist_gap_repair")
OUT.mkdir(parents=True,exist_ok=True)
REPORT=Path("analysis/btcusd_2024_gap_repair")
REPORT.mkdir(parents=True,exist_ok=True)
MONTHS=[str(m) for m in pd.period_range("2024-01","2024-12",freq="M")]
def ts(s):return datetime.fromtimestamp(s,timezone.utc).isoformat()
def runs(missing):
    if not missing:return []
    out=[];a=b=missing[0]
    for t in missing[1:]:
        if t==b+60:b=t
        else:out.append((a,b));a=b=t
    out.append((a,b))
    return out
def repair(month):
    meta=json.loads((OLD/(month+".json")).read_text())
    src=OLD/(month+".csv.gz")
    assert hashlib.sha256(src.read_bytes()).hexdigest()==meta["sha256"],month
    p=pd.Period(month,freq="M")
    start=int(p.start_time.tz_localize("Asia/Kolkata").tz_convert("UTC").timestamp())
    end=int((p+1).start_time.tz_localize("Asia/Kolkata").tz_convert("UTC").timestamp())
    expected=set(range(start,end,60))
    rows={}
    with gzip.open(src,"rt",newline="") as f:
        for bar in csv.DictReader(f):
            stamp=validate_bar(bar)
            assert stamp in expected and stamp not in rows
            rows[stamp]={k:bar[k] for k in COLUMNS}
    assert len(rows)==meta["observed"],month
    old_count=len(rows);missing=sorted(expected-rows.keys());initial_gap=len(missing)
    attempted=0;errors=[]
    # Retry still missing gaps only. Overlap by at most 1 minute for
    # tiny intervals to tolerate endpoint quirks; never overwrite old bars.
    for step in (1200,600,120):
        if not missing:break
        for a,b in runs(missing):
            for lo in range(a,b+60,step*60):
                hi=min(b,lo+(step-1)*60)
                query_lo=max(start,lo-60) if lo==hi else lo
                query_hi=min(end-60,hi+60) if lo==hi else hi
                attempted+=1
                try:
                    raw=read_window(query_lo,query_hi)
                    for bar in raw:
                        stamp=validate_bar(bar)
                        if lo<=stamp<=hi and stamp in expected and stamp not in rows:
                            rows[stamp]={k:bar[k] for k in COLUMNS}
                except Exception as exc:
                    errors.append(dict(start=ts(lo),end=ts(hi),error=str(exc)[:300]))
                time.sleep(.2)
        missing=sorted(expected-rows.keys())
        print(month,"window",step,"remaining",len(missing),flush=True)
    # Identical logical rows for already complete months; deterministic gzip.
    sha=write_month(OUT/(month+".csv.gz"),rows)
    gaps=[dict(start_utc=ts(a),end_utc_inclusive=ts(b),minutes=(b-a)//60+1) for a,b in runs(missing)]
    detail=dict(month=month,expected=len(expected),original_candles=old_count,original_missing=initial_gap,recovered=len(rows)-old_count,final_candles=len(rows),remaining_missing=len(missing),complete=not missing,requests=attempted,source_sha256=meta["sha256"],archive_sha256=sha,remaining_gaps=gaps,request_errors=errors)
    print("RESULT",json.dumps({k:v for k,v in detail.items() if k not in ("remaining_gaps","request_errors")}),flush=True)
    return detail
def main():
    with cf.ThreadPoolExecutor(max_workers=2) as pool:details=list(pool.map(repair,MONTHS))
    fields=["month","expected","original_candles","original_missing","recovered","final_candles","remaining_missing","complete","requests","source_sha256","archive_sha256"]
    pd.DataFrame(details)[fields].to_csv(REPORT/"coverage.csv",index=False)
    manifest=dict(source="Delta Exchange India BTCUSD 1m public history API",partition_timezone="Asia/Kolkata",prior_run=45374768673,synthetic_candles=0,original_preserved=True,expected=sum(x["expected"] for x in details),original_missing=sum(x["original_missing"] for x in details),recovered=sum(x["recovered"] for x in details),remaining_missing=sum(x["remaining_missing"] for x in details),complete_months=sum(x["complete"] for x in details),requests=sum(x["requests"] for x in details),months=details)
    (OUT/"manifest.json").write_text(json.dumps(manifest,indent=2))
    (REPORT/"quality.json").write_text(json.dumps({k:v for k,v in manifest.items() if k!="months"},indent=2))
    print("TOTAL",json.dumps({k:v for k,v in manifest.items() if k!="months"}),flush=True)
if __name__=="__main__":main()
