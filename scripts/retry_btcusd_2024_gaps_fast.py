#!/usr/bin/env python3
"""Bounded, resumable native Delta BTCUSD gap retry. One round per invocation."""
import csv,gzip,hashlib,json,os,random,time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
from pathlib import Path
import pandas as pd
from repair_btcusd_2024_gaps_v3 import fetch, intervals
from sync_delta_btcusd_1m import validate_bar,write_month,COLUMNS
ROOT=Path("data/delta_india/BTCUSD/2024_verified_archive")
REPORT=Path("analysis/btcusd_2024_gap_retry")
REPORT.mkdir(parents=True,exist_ok=True)
STATE=REPORT/"state.json"
MANIFEST=ROOT/"manifest.json"
def main():
    manifest=json.loads(MANIFEST.read_text())
    state=json.loads(STATE.read_text()) if STATE.exists() else dict(round=0,history=[],no_progress=0)
    before=manifest["totals"]["trade_1m"]["missing"]
    if not before:
        print("COMPLETE: no remaining requests",flush=True);return
    round_no=state["round"]+1
    # Deterministic rotation across wide and narrow windows. Different
    # alignments expose API boundary behavior without changing stored data.
    widths=(1999,1998,1997,1800,1440,1200,997,720,360,180,60,1995)
    width=widths[(round_no-1)%len(widths)]
    rng=random.Random(20240101+round_no)
    offset=rng.randrange(width)*60
    window=width*60
    cap=120;requests=errors=recovered=0
    start_time=time.monotonic()
    # Round-robin months; smaller February gap gets priority.
    for item in sorted(manifest["months"],key=lambda x:x["missing"]):
        if item["series"]!="trade_1m" or not item["missing"]:continue
        p=ROOT/"trade_1m"/(item["month"]+".csv.gz")
        assert hashlib.sha256(p.read_bytes()).hexdigest()==item["sha256"]
        month=pd.Period(item["month"],freq="M")
        a=int(month.start_time.tz_localize("Asia/Kolkata").timestamp())
        b=int((month+1).start_time.tz_localize("Asia/Kolkata").timestamp())
        expected=set(range(a,b,60))
        with gzip.open(p,"rt") as f:rows={validate_bar(x):x for x in csv.DictReader(f)}
        assert len(rows)==item["observed"] and set(rows)<=expected
        old=len(rows)
        missing=expected-rows.keys()
        # Alternate grid alignment with forward/backward gap-edge tiling.
        # Requests stay within Delta's documented 2,000-candle maximum.
        mode=(round_no-1)%4
        if mode==0:
            windows=[(lo-1,lo+window-59) for lo in sorted({((t-offset)//window)*window+offset for t in missing})]
        elif mode==1:
            windows=[(lo,lo+window-60) for ga,gb in intervals(sorted(missing)) for lo in range(ga,gb+60,window)]
        elif mode==2:
            windows=[(hi-window+60,hi) for ga,gb in intervals(sorted(missing)) for hi in range(gb,ga-60,-window)]
        else:
            windows=[(lo-1,lo+window-59) for ga,gb in intervals(sorted(missing)) for lo in range(ga-rng.randrange(width)*60,gb+60,max(60,window*3//4//60*60))]
        windows=list(dict.fromkeys(windows))
        rng.shuffle(windows)
        def request(w):
            lo,hi=w
            try:
                result=fetch("BTCUSD",lo,hi)
                verified=[]
                for r in result:
                    t=validate_bar(r)
                    if t in expected:verified.append((t,{k:r[k] for k in COLUMNS}))
                return verified,None
            except Exception as exc:return [],str(exc)[:200]
        with ThreadPoolExecutor(max_workers=3) as pool:
            for k in range(0,len(windows),3):
                if requests>=cap or errors>=4 or time.monotonic()-start_time>240:break
                batch=[]
                for lo,hi in windows[k:k+3]:
                    if requests+len(batch)>=cap:break
                    if any(t not in rows for t in range(max(a,((lo+59)//60)*60),min(b,hi+1),60)):batch.append((lo,hi))
                requests+=len(batch)
                for verified,error in pool.map(request,batch):
                    if error:
                        errors+=1
                        print("REQUEST_ERROR",error,flush=True)
                    for t,row in verified:
                        if t not in rows:rows[t]=row
                time.sleep(.35 if not errors else 2.)
        gain=len(rows)-old;recovered+=gain
        if gain:
            item.update(sha256=write_month(p,rows),observed=len(rows),missing=len(expected)-len(rows),gaps=intervals(sorted(expected-rows.keys())))
        print("MONTH",item["month"],"recovered",gain,"missing",item["missing"],flush=True)
        if errors>=4 or requests>=cap:break
    trade=[x for x in manifest["months"] if x["series"]=="trade_1m"]
    total=manifest["totals"]["trade_1m"]
    total.update(observed=sum(x["observed"] for x in trade),missing=sum(x["missing"] for x in trade),complete_months=sum(x["missing"]==0 for x in trade),recovered_this_run=recovered,requests_this_run=requests,request_errors=errors)
    assert before-total["missing"]==recovered
    record=dict(round=round_no,utc=datetime.now(timezone.utc).isoformat(),window=width,offset_seconds=offset,alignment_mode=(round_no-1)%4,workers=3,requests=requests,errors=errors,recovered=recovered,remaining=total["missing"])
    state.update(round=round_no,no_progress=0 if recovered else state["no_progress"]+1)
    state["history"].append(record)
    state["complete"]=total["missing"]==0
    state["remaining"]=total["missing"]
    state["status"]="complete" if state["complete"] else ("no_progress" if state["no_progress"]>=4 else "retryable")
    (MANIFEST).write_text(json.dumps(manifest,indent=2))
    STATE.write_text(json.dumps(state,indent=2))
    pd.DataFrame(manifest["months"])[["series","month","expected","observed","missing","sha256"]].to_csv(REPORT/"coverage.csv",index=False)
    print("ROUND",json.dumps(record),flush=True)
if __name__=="__main__":main()
