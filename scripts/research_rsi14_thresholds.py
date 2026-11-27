"""72 predeclared RSI threshold variants. 2024/2025 only; same execution and fees."""
import csv,gzip,json,math
from itertools import product
from pathlib import Path
import research_rsi14_depth_stability as base
from research_rsi14_depth_stability import y24,y25,q,candles25,checks,replay,summarize
OUT=Path("scratch/rsi14_thresholds")
THRESHOLDS=(65,70,75,80)
DEPTHS=(0.,.25,.375)
BE=(0,750,1000)
PLAN=list(product(THRESHOLDS,DEPTHS,BE,(False,True)))
def key(p):
    hi,depth,be,ema=p
    return f"rsi{hi}-{100-hi}-depth{depth:g}-be{be}-ema{int(ema)}"
def signals_for(rec,extra,start,end,eval_start,upper):
    # Read the same indicator book's completed 15m RSI observations,
    # not a different implementation or partially formed candles.
    ids=[d["id"] for d in rec.definitions if d["name"]=="rsi" and d["timeframe_minutes"]==15]
    assert len(ids)==1
    out=[];prev=None
    for ts,value in rec.series[ids[0]]:
        if value is not None and prev is not None and eval_start<=ts<end:
            direction=1 if prev<=upper<value else -1 if prev>=100-upper>value else 0
            if direction:
                k=(ts-start)//60
                assert k in extra
                hi,lo=extra[k][3:5]
                out.append((k,direction,value,hi,lo))
        prev=value
    return out
def run():
    checks();OUT.mkdir(parents=True,exist_ok=True)
    assert len(PLAN)==72
    results={key(p):{"plan":p,"years":{}} for p in PLAN}
    for year in (2024,2025):
        if year==2024:
            q.candles=y24.candles;bars,signals,snapshots,extra,rec=y24.load();start,end,eval_start=y24.START,y24.END,y24.EVAL
        else:
            q.candles=candles25;bars,signals,snapshots,extra,rec=y25.load();start,end=y25.START,y25.END;eval_start=start
        ind=q.indicators(bars,snapshots)
        for hi in THRESHOLDS:
            ss=signals_for(rec,extra,start,end,eval_start,hi)
            if hi==80:
                assert len(ss)==len(signals) and all(a[:2]==b[:2] and a[3:]==b[3:] and math.isclose(a[2],b[2],abs_tol=1e-8) for a,b in zip(ss,signals)),(year,len(ss),len(signals))
                ss=signals
            setups=q.setup_rows(bars,ss,snapshots,extra)
            print("SIGNALS",json.dumps(dict(year=year,upper=hi,lower=100-hi,raw=len(ss),setups=len(setups))))
            for p in PLAN:
                if p[0]!=hi:continue
                _,depth,be,ema=p
                ts=replay(bars,ind,setups,start,end,("original",ema,depth,(be,False),3000.),snapshots)
                s=summarize(ts,year);st=summarize(ts,year,50)
                s["stress"]=dict(net=st["net"],months=st["profitable_months"],pf=st["profit_factor"],dd=st["realized_drawdown_points"])
                s["meaningful_wins_over_50"]=sum(t["net_points"]>50 for t in ts)
                if p==(80,.25,750,True):
                    assert math.isclose(s["net"],{2024:3517.781215,2025:15616.11716}[year],abs_tol=1e-5),(year,s)
                if p==(80,0.,0,False):
                    assert math.isclose(s["net"],{2024:-7143.8888,2025:38547.273445}[year],abs_tol=1e-5),(year,s)
                results[key(p)]["years"][year]=dict(summary=s,trades=ts)
        del bars,ind,snapshots,extra,rec
    def passes(p):
        return all(v["summary"]["stress"]["net"]>0 and v["summary"]["trades"]>=30 for v in results[key(p)]["years"].values())
    rows=[]
    for p in PLAN:
        k=key(p);hi,depth,be,ema=p
        a,b=[results[k]["years"][y]["summary"] for y in (2024,2025)]
        ns=[(h,depth,be,ema) for i,h in enumerate(THRESHOLDS) if abs(i-THRESHOLDS.index(hi))==1]
        dn=[(hi,d,be,ema) for i,d in enumerate(DEPTHS) if abs(i-DEPTHS.index(depth))==1]
        bn=[(hi,depth,x,ema) for i,x in enumerate(BE) if abs(i-BE.index(be))==1]
        npass=sum(passes(n) for n in ns);dpass=sum(passes(n) for n in dn);bpass=sum(passes(n) for n in bn)
        blocks=[sum(x for m,x in z["monthly_entry_attribution"].items() if (int(m[-2:])>6)==bool(half)) for z in (a,b) for half in (0,1)]
        row=dict(key=k,upper=hi,lower=100-hi,depth=depth,be=be,ema=ema,net24=a["net"],net25=b["net"],months24=a["profitable_months"],months25=b["profitable_months"],pf24=a["profit_factor"],pf25=b["profit_factor"],dd24=a["realized_drawdown_points"],dd25=b["realized_drawdown_points"],trades24=a["trades"],trades25=b["trades"],stress24=a["stress"]["net"],stress25=b["stress"]["net"],stress_months24=a["stress"]["months"],stress_months25=b["stress"]["months"],net=a["net"]+b["net"],months=a["profitable_months"]+b["profitable_months"],dd=max(a["realized_drawdown_points"],b["realized_drawdown_points"]),stress_pass=passes(p),threshold_neighbors=npass,depth_neighbors=dpass,protection_neighbors=bpass,positive_blocks=sum(x>0 for x in blocks),blocks=blocks,accepted=passes(p) and npass>0 and dpass>0 and bpass>0 and all(x>0 for x in blocks))
        rows.append(row)
    def rank(z):
        return (z["accepted"],z["stress_pass"],z["threshold_neighbors"]>0,z["depth_neighbors"]>0 and z["protection_neighbors"]>0,z["positive_blocks"],min(z["stress_months24"]/10,z["stress_months25"]/12),z["stress_months24"]+z["stress_months25"],z["months"],-z["dd"])
    rows.sort(key=rank,reverse=True)
    with (OUT/"results.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    with gzip.open(OUT/"all_results.json.gz","wt") as f:json.dump(results,f,allow_nan=False,separators=(",",":"))
    print("COUNTS",json.dumps(dict(total=len(rows),both_year_positive=sum(z["net24"]>0 and z["net25"]>0 for z in rows),stress_pass=sum(z["stress_pass"] for z in rows),threshold_pass=sum(z["stress_pass"] and z["threshold_neighbors"]>0 for z in rows),accepted=sum(z["accepted"] for z in rows),max_months=max(z["months"] for z in rows))))
    for hi in THRESHOLDS:
        group=[z for z in rows if z["upper"]==hi]
        print("FAMILY",json.dumps(dict(upper=hi,total=len(group),positive=sum(z["net24"]>0 and z["net25"]>0 for z in group),stress=sum(z["stress_pass"] for z in group),accepted=sum(z["accepted"] for z in group),max_months=max(z["months"] for z in group),best=group[0]),allow_nan=False))
        for z in group:
            if z["depth"]==.25 and z["be"]==750 and z["ema"]:print("CONTROL",json.dumps(z,allow_nan=False))
    for z in rows[:10]:print("TOP",json.dumps(z,allow_nan=False))
    for z in sorted(rows,key=lambda x:(x["months"],x["net"]),reverse=True)[:5]:print("MONTH",json.dumps(z,allow_nan=False))
    for z in rows[:3]:print("DETAIL",json.dumps(dict(key=z["key"],years={y:results[z["key"]]["years"][y]["summary"] for y in (2024,2025)}),allow_nan=False))
if __name__=="__main__":run()
