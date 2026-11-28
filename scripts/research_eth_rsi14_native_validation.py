"""Frozen ETH RSI14 validation only. No parameter selection."""
import csv,gzip,json
from pathlib import Path
from research_eth_rsi14_native import PLAN,segment,entries,replay,summary,checks
OUT=Path("scratch/eth_rsi14_native_validation")
MONTHS=[f"2026-{m:02d}" for m in range(1,11)]
def run():
    checks();OUT.mkdir(parents=True,exist_ok=True)
    bars,start,end,ev=segment(MONTHS,"2025-12");atr,events=entries(bars,start,ev)
    print("EVENTS",len(events))
    rows=[];results={}
    for mode,m in PLAN:
        key=f"{mode}-{m:g}ATR"
        ts=replay(bars,start,end,atr,events,mode,m)
        v=summary(ts,MONTHS);results[key]=dict(summary=v,trades=ts)
        row=dict(key=key,**v);rows.append(row)
        print("RESULT",json.dumps(row,allow_nan=False))
    with (OUT/"results.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    with gzip.open(OUT/"all_results.json.gz","wt") as f:json.dump(results,f,allow_nan=False)
    print("COUNTS",json.dumps(dict(total=len(rows),positive=sum(x["net"]>0 for x in rows),stress_positive=sum(x["stress"]>0 for x in rows),max_months=max(x["months"] for x in rows))))
if __name__=="__main__":run()
