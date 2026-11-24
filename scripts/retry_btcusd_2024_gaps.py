#!/usr/bin/env python3
"""Bounded, resumable native Delta BTCUSD gap retry. One round per invocation."""
import csv,gzip,hashlib,json,os,random,time
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
    widths=(1997,1799,1439,1199,997,719,479,239)
    width=widths[(round_no-1)%len(widths)]
    rng=random.Random(20240101+round_no)
    offset=rng.randrange(width)*60
    window=width*60
    cap=180;requests=errors=recovered=0
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
        windows=sorted({((t-offset)//window)*window+offset for t in expected-rows.keys()})
        rng.shuffle(windows)
        for lo in windows:
            if requests>=cap or time.monotonic()-start_time>240:break
            # Skip requests whose gaps were already repaired.
            if all(t in rows for t in range(max(a,lo),min(b,lo+window),60)):continue
            requests+=1
            try:
                for r in fetch("BTCUSD",lo-1,lo+window+1):
                    t=validate_bar(r)
                    if t in expected and t not in rows:rows[t]={k:r[k] for k in COLUMNS}
            except Exception as exc:
                errors+=1
                print("REQUEST_ERROR",lo,str(exc)[:200],flush=True)
                if errors>=4:break
            time.sleep(.2)
        gain=len(rows)-old;recovered+=gain
        if gain:
            item.update(sha256=write_month(p,rows),observed=len(rows),missing=len(expected)-len(rows),gaps=intervals(sorted(expected-rows.keys())))
        print("MONTH",item["month"],"recovered",gain,"missing",item["missing"],flush=True)
        if errors>=4 or requests>=cap:break
    trade=[x for x in manifest["months"] if x["series"]=="trade_1m"]
    total=manifest["totals"]["trade_1m"]
    total.update(observed=sum(x["observed"] for x in trade),missing=sum(x["missing"] for x in trade),complete_months=sum(x["missing"]==0 for x in trade),recovered_this_run=recovered,requests_this_run=requests,request_errors=errors)
    assert before-total["missing"]==recovered
    record=dict(round=round_no,utc=datetime.now(timezone.utc).isoformat(),window=width,offset_seconds=offset,requests=requests,errors=errors,recovered=recovered,remaining=total["missing"])
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
