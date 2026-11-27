"""Coarse, predefined entry-price percentage grid, 2024–2025 only."""
import csv,gzip,json,math
from pathlib import Path
import numpy as np
from numba import njit
import research_rsi14_depth_stability as b
from research_rsi14_nearby_thresholds import signals_for
from research_rsi14_consistency_risk_2025 import retest
from research_rsi14_depth_stability import y24,y25,q,candles25,checks,summarize,FEE,dt
OUT=Path("scratch/rsi14_price_percent")
BASES=("fixed-trailing","chandelier","continuation-exit")
from itertools import product
GRID=list(product((.0075,.01,.0125),(.5,.75,1.),(2.,3.,4.)))
CONFIGS=[None]+GRID
REF={"fixed-trailing":{2024:10619.81256,2025:13943.95523},"chandelier":{2024:9644.735195,2025:12787.68496},"continuation-exit":{2024:11211.696845,2025:15782.86963}}
from research_rsi14_trade_management import execute as reference_execute

@njit
def path(o,h,l,c):
    return (o,l,h,c) if c>o or (c==o and o-l<=h-o) else (o,h,l,c)

@njit
def sim(O,H,L,C,atr,i,d,ep,be,trail_mult,activation,risk,trail_distance,continuation):
    stop=ep-d*risk;act=ep+d*activation;best=ep;armed=-1;mfe=mae=0.
    lock=ep*(d+FEE)/(d-FEE)
    lock=math.ceil(lock*2)/2 if d==1 else math.floor(lock*2)/2
    for j in range(i,len(O)):
        o,h,l,c=O[j],H[j],L[j],C[j]
        seq=path(o,h,l,c);a0=o;k0=0
        if d*(a0-stop)<=0:
            mae=max(mae,-d*(a0-ep));return j,a0,2 if armed>=0 else 3 if d*(stop-ep)>=0 else 1,stop,armed,mfe,mae
        if continuation and armed>=0 and j>i and j%15==0 and j>=30:
            adverse=np.min(L[j-30:j-15]) if d==1 else np.max(H[j-30:j-15])
            if d*(C[j-1]-adverse)<0:return j,o,5,stop,armed,mfe,mae
        distance=trail_distance
        if trail_mult>0 and np.isfinite(atr[j//15]) and atr[j//15]>0:distance=math.ceil(trail_mult*atr[j//15]*2)/2
        mfe=max(mfe,d*(a0-ep));mae=max(mae,-d*(a0-ep))
        if d*(a0-best)>0:best=a0
        stop=b.tighten(stop,best,ep,d,be,False,lock)
        if armed<0 and d*(a0-act)>=0:armed=j
        if armed>=0 and d*(best-d*distance-stop)>0:stop=best-d*distance
        if d*(a0-stop)<=0:return j,a0,2 if armed>=0 else 3,stop,armed,mfe,mae
        for k in range(k0,3):
            a=a0 if k==k0 else seq[k];z=seq[k+1]
            if d*(z-a)<0:
                if d*(a-stop)>=0 and d*(z-stop)<=0:
                    mae=max(mae,-d*(stop-ep));return j,stop,2 if armed>=0 else 3 if d*(stop-ep)>=0 else 1,stop,armed,mfe,mae
                mae=max(mae,-d*(z-ep))
            elif d*(z-a)>0:
                mfe=max(mfe,d*(z-ep))
                if d*(z-best)>0:best=z
                stop=b.tighten(stop,best,ep,d,be,False,lock)
                if armed<0 and d*(z-act)>=0:armed=j
                if armed>=0 and d*(best-d*distance-stop)>0:stop=best-d*distance
    return len(O)-1,C[-1],4,stop,armed,mfe,mae

def key(name,cfg):
    return name+"-baseline" if cfg is None else name+f"-sl{cfg[0]*100:g}-be{cfg[1]:g}R-act{cfg[2]:g}R"

def replay(bars,ind,setups,start,end,name,cfg,snapshots,ST,LINE):
    O,H,L,C=bars;atr=ind[-1];rsi=ind[2];out=[];free=0
    def eligible(i,d,depth):
        e=snapshots[(i//15)*15][1]
        return depth>=.25 and e is not None and d*(C[i-1]-e)>0
    for first,d,r,trigger,level,pull,depth,until,retries in setups:
        if first<free or not eligible(first,d,depth):continue
        i=retest(bars,first,d,level,until)
        if i<free or i>=until or not eligible(i,d,depth):continue
        k=i//15
        if np.any(d*(rsi[trigger//15:k+1]-50)<=0):continue
        ep=float(O[i]);at=float(atr[k]);trail_mult=3. if name=="chandelier" else 0.
        if cfg is None:
            risk=1000.;be=750.;activation=3000.;trail_distance=1000.
        else:
            sl,ber,ar=cfg
            risk=max(.5,math.ceil(ep*sl*2)/2)
            be=math.ceil(ep*sl*ber*2)/2
            activation=math.ceil(ep*sl*ar*2)/2
            trail_distance=risk
        if cfg is None and name=="fixed-trailing":
            j,xp,reason,stop,armed,mfe,mae=b.trade(O,H,L,C,i,d,3000.,750.,False)
        elif cfg is None and name=="chandelier":
            j,xp,reason,stop,armed,mfe,mae,_,_=reference_execute(O,H,L,C,atr,ST,LINE,i,d,750.,3.,0,0)
        else:
            j,xp,reason,stop,armed,mfe,mae=sim(O,H,L,C,atr,i,d,ep,be,trail_mult,activation,risk,trail_distance,name=="continuation-exit")
        free=j+1;gross=d*(xp-ep);fee=(ep+xp)*FEE
        out.append(dict(entry_utc=dt(start+i*60).isoformat(),trigger_utc=dt(start+trigger*60).isoformat(),exit_utc=dt(end if reason==4 else start+j*60).isoformat(),side=d,entry_price=ep,exit_price=float(xp),gross_points=float(gross),fee_points=float(fee),net_points=float(gross-fee),exit_reason={1:"Initial SL",2:"Trailing SL",3:"Profit protection",4:"Evaluation end",5:"Continuation exit"}[reason],signal_context=dict(rsi14=r,risk_points=risk,entry_atr=at,depth=depth,mfe=float(mfe),mae=float(mae),protection_points=be,activation_points=activation,trail_distance=trail_distance,activation_utc=dt(start+armed*60).isoformat() if armed>=0 else None)))
    return out

def run():
    checks();OUT.mkdir(parents=True,exist_ok=True)
    results={key(n,cfg):dict(candidate=n,config=cfg,years={}) for n in BASES for cfg in CONFIGS}
    assert len(results)==84
    for year in (2024,2025):
        if year==2024:
            q.candles=y24.candles;bars,signals,snapshots,extra,rec=y24.load();start,end=y24.START,y24.END
        else:
            q.candles=candles25;bars,signals,snapshots,extra,rec=y25.load();start,end=y25.START,y25.END
        ind=q.indicators(bars,snapshots);atr=ind[-1]
        ST=np.full(len(atr),np.nan);LINE=ST.copy()
        setups=q.setup_rows(bars,signals,snapshots,extra)
        for name in BASES:
            for cfg in CONFIGS:
                ts=replay(bars,ind,setups,start,end,name,cfg,snapshots,ST,LINE)
                a=summarize(ts,year);st=summarize(ts,year,50)
                stp=summarize([dict(t,net_points=t["net_points"]-.0005*t["entry_price"]) for t in ts],year)
                a["stress50"]=st["net"];a["stress_pct"]=stp["net"];a["stress_months"]=st["profitable_months"]
                a["median_risk"]=float(np.median([t["signal_context"]["risk_points"] for t in ts])) if ts else 0.
                a["sum_trade_returns_pct"]=sum(100*t["net_points"]/t["entry_price"] for t in ts)
                if cfg is None:
                    assert math.isclose(a["net"],REF[name][year],abs_tol=1e-5),(name,year,a)
                    # New generic kernel must also reproduce each fixed reference.
                    for t in ts:assert t["signal_context"]["risk_points"]==1000
                results[key(name,cfg)]["years"][year]=dict(summary=a,trades=ts)
        del bars,ind,snapshots,extra,rec
    rows=[]
    def passes(v):
        return all(s["net"]>0 and s["stress50"]>0 and s["stress_pct"]>0 and s["trades"]>=30 for s in [v["years"][y]["summary"] for y in (2024,2025)])
    for k,v in results.items():
        name=v["candidate"];cfg=v["config"]
        a,c=[v["years"][y]["summary"] for y in (2024,2025)]
        x,z=[results[key(name,None)]["years"][y]["summary"] for y in (2024,2025)]
        blocks=[sum(p for m,p in s["monthly_entry_attribution"].items() if (int(m[-2:])>6)==bool(h)) for s in (a,c) for h in (0,1)]
        near=[]
        if cfg is not None:
            axes=((.0075,.01,.0125),(.5,.75,1.),(2.,3.,4.))
            for axis,opts in enumerate(axes):
                idx=opts.index(cfg[axis]);ns=[]
                for off in (-1,1):
                    if 0<=idx+off<len(opts):
                        n=list(cfg);n[axis]=opts[idx+off];ns.append(passes(results[key(name,tuple(n))]))
                near.append(any(ns))
        row=dict(key=k,candidate=name,sl_pct=cfg[0]*100 if cfg else None,be_pct=cfg[0]*cfg[1]*100 if cfg else None,act_pct=cfg[0]*cfg[2]*100 if cfg else None,trail_pct=cfg[0]*100 if cfg and name!="chandelier" else None,net24=a["net"],net25=c["net"],net=a["net"]+c["net"],months24=a["profitable_months"],months25=c["profitable_months"],months=a["profitable_months"]+c["profitable_months"],dd24=a["realized_drawdown_points"],dd25=c["realized_drawdown_points"],dd=max(a["realized_drawdown_points"],c["realized_drawdown_points"]),pf24=a["profit_factor"],pf25=c["profit_factor"],trades24=a["trades"],trades25=c["trades"],stress24=a["stress50"],stress25=c["stress50"],stress_pct24=a["stress_pct"],stress_pct25=c["stress_pct"],return_sum24=a["sum_trade_returns_pct"],return_sum25=c["sum_trade_returns_pct"],median_risk24=a["median_risk"],median_risk25=c["median_risk"],positive_blocks=sum(p>0 for p in blocks),stress_pass=passes(v),neighbor_axes=sum(near),both_net_up=a["net"]>x["net"] and c["net"]>z["net"],both_months_nonworse=a["profitable_months"]>=x["profitable_months"] and c["profitable_months"]>=z["profitable_months"],both_dd_nonworse=a["realized_drawdown_points"]<=x["realized_drawdown_points"]+1e-7 and c["realized_drawdown_points"]<=z["realized_drawdown_points"]+1e-7)
        row["robust"]=cfg is not None and row["stress_pass"] and row["neighbor_axes"]==3 and row["positive_blocks"]==4
        row["accepted"]=row["robust"] and row["both_net_up"] and row["both_months_nonworse"] and row["both_dd_nonworse"]
        rows.append(row);print("RESULT",json.dumps(row,allow_nan=False))
    with (OUT/"results.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    with gzip.open(OUT/"all_results.json.gz","wt") as f:json.dump(results,f,allow_nan=False,separators=(",",":"))
    for name in BASES:
        grp=[x for x in rows if x["candidate"]==name and x["sl_pct"] is not None]
        print("COUNTS",json.dumps(dict(candidate=name,total=len(grp),both_positive=sum(x["net24"]>0 and x["net25"]>0 for x in grp),stress_pass=sum(x["stress_pass"] for x in grp),robust=sum(x["robust"] for x in grp),accepted=sum(x["accepted"] for x in grp),max_months=max(x["months"] for x in grp))))
    selected=sorted(rows,key=lambda r:(r["robust"],r["months"],r["net"]),reverse=True)[:12]
    for row in selected:
        v=results[row["key"]];print("DETAIL",json.dumps(dict(key=row["key"],years={y:v["years"][y]["summary"] for y in (2024,2025)}),allow_nan=False))
if __name__=="__main__":run()
