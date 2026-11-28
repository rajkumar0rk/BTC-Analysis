"""Evaluate only the six previously reported ETH grid winners on 2026."""
import csv,gzip,json
from pathlib import Path
from research_eth_rsi14_native_combinations import segment,entries,replay,summary,key,stress_months,checks
OUT=Path("scratch/eth_rsi14_combinations_validation")
MONTHS=[f"2026-{m:02d}" for m in range(1,11)]
PLAN=[
("highest-profit",("fixed",4.,1.,4.,1.),610.8727300000011,2319.4216645000033,10),
("highest-profit",("chandelier",4.,1.,4.,4.),460.36158400000113,2314.0197370000024,10),
("highest-profit",("continuation",4.,1.,4.,.75),390.4028840000011,2023.380254375002,10),
("stable",("fixed",3.,.75,2.,1.5),350.10366850000025,977.403902750003,12),
("stable",("chandelier",3.,.75,3.,2.),226.7533465000006,1456.5705535000034,12),
("stable",("continuation",3.,.75,3.,1.),243.04343450000079,1087.3910795000027,12)]
def run():
    checks();OUT.mkdir(parents=True,exist_ok=True)
    bars,start,end,ev=segment(MONTHS,"2025-12");atr,events=entries(bars,start,ev)
    print("EVENTS",len(events))
    rows=[];results={}
    for group,cfg,n24,n25,m in PLAN:
        ts=replay(bars,start,end,atr,events,*cfg);v=summary(ts,MONTHS)
        row=dict(group=group,key=key(cfg),net24=n24,net25=n25,total=n24+n25+v["net"],total_months=m+v["months"],stress_months=stress_months(ts,MONTHS),**v)
        rows.append(row);results[key(cfg)]=dict(summary=row,trades=ts)
        print("RESULT",json.dumps(row,allow_nan=False))
    with (OUT/"results.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    with gzip.open(OUT/"all_results.json.gz","wt") as f:json.dump(results,f,allow_nan=False)
    print("COUNTS",json.dumps(dict(total=len(rows),positive=sum(x["net"]>0 for x in rows),stress_positive=sum(x["stress"]>0 for x in rows))))
if __name__=="__main__":run()
