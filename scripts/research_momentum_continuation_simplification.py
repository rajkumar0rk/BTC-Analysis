"""Five independent higher-timeframe baselines, no grid or 2026 access."""
import csv,gzip,json,math
from pathlib import Path
import numpy as np
from numba import njit
from research_rsi14_depth_stability import y24,y25,q,candles25,checks,summarize,FEE,dt
OUT=Path("scratch/momentum_continuation_simplification")
NAMES=("reference-3-inside","1-inside","2-inside","3-close-inside","3-directional-hold","3-body-inside","flexible-1-to-3-inside")

@njit
def bracket(O,H,L,C,i,d,risk):
    ep=O[i];sl=ep-d*risk;tp=ep+d*2*risk;mfe=mae=0.
    for j in range(i,len(O)):
        o,h,l,c=O[j],H[j],L[j],C[j]
        if d*(o-sl)<=0:return j,o,1,mfe,max(mae,-d*(o-ep))
        if d*(o-tp)>=0:return j,tp,2,max(mfe,d*(tp-ep)),mae
        mfe=max(mfe,d*(o-ep));mae=max(mae,-d*(o-ep))
        seq=(o,l,h,c) if c>o or (c==o and o-l<=h-o) else (o,h,l,c)
        for k in range(3):
            a,z=seq[k],seq[k+1]
            if d*(z-a)<0:
                if d*(z-sl)<=0:return j,sl,1,mfe,max(mae,risk)
                mae=max(mae,-d*(z-ep))
            elif d*(z-a)>0:
                if d*(z-tp)>=0:return j,tp,2,max(mfe,2*risk),mae
                mfe=max(mfe,d*(z-ep))
    return len(O)-1,C[-1],3,mfe,mae

def unit_checks():
    o=np.array([100.]);h=np.array([125.]);l=np.array([85.])
    assert bracket(o,h,l,np.array([110.]),0,1,10.)[:3]==(0,90.,1)
    assert bracket(o,h,l,np.array([95.]),0,1,10.)[:3]==(0,120.,2)
    assert bracket(o,h,l,np.array([110.]),0,-1,7.)[:3]==(0,86.,2)
    assert bracket(o,h,l,np.array([95.]),0,-1,7.)[:3]==(0,107.,1)
    O=np.array([100.,85.]);H=np.array([105.,90.]);L=np.array([95.,80.]);C=np.array([102.,87.])
    assert bracket(O,H,L,C,0,1,10.)[:3]==(1,85.,1)

def ema(c,n):
    a=np.full(len(c),np.nan)
    if len(c)>=n:
        a[n-1]=np.mean(c[:n])
        for k in range(n,len(c)):a[k]=a[k-1]+2/(n+1)*(c[k]-a[k-1])
    return a

def aggregate(bars,tf):
    O,H,L,C=bars;n=len(O)//tf*tf
    o=O[:n:tf];h=H[:n].reshape(-1,tf).max(axis=1);l=L[:n].reshape(-1,tf).min(axis=1);c=C[tf-1:n:tf]
    prev=np.r_[np.nan,c[:-1]]
    tr=np.maximum(h-l,np.maximum(np.abs(h-prev),np.abs(l-prev)));tr[0]=h[0]-l[0]
    return o,h,l,c,q.wilder(tr)

def signal_lists(bars,ind,snapshots,extra,start,ev):
    assert start%3600==0
    o,h,l,c,a=aggregate(bars,60)
    out={n:[] for n in NAMES}
    for name in NAMES:
        # Impulse: body >= one prior ATR. Breakout: completed close beyond
        # impulse high/low. Each variant modifies consolidation only.
        lengths=(1,2,3) if name=="flexible-1-to-3-inside" else (1,) if name=="1-inside" else (2,) if name=="2-inside" else (3,)
        used=set()
        for k in range(40,len(c)):
            i=(k+1)*60
            if i>=len(bars[0]) or start+i*60<ev or not np.isfinite(a[k]) or a[k]<=0:continue
            found=[]
            for n in lengths:
                p=k-n-1
                if p in used or not np.isfinite(a[p-1]):continue
                d=1 if c[p]-o[p]>=a[p-1] and c[k]>h[p] else -1 if o[p]-c[p]>=a[p-1] and c[k]<l[p] else 0
                if not d:continue
                sl=slice(p+1,k)
                if name=="3-close-inside":
                    ok=np.max(c[sl])<=h[p] and np.min(c[sl])>=l[p]
                elif name=="3-body-inside":
                    ok=max(np.max(o[sl]),np.max(c[sl]))<=h[p] and min(np.min(o[sl]),np.min(c[sl]))>=l[p]
                elif name=="3-directional-hold":
                    # Allow wicks outside both sides; closes must hold the
                    # impulse midpoint without already breaking its high/low.
                    mid=(h[p]+l[p])/2
                    ok=np.min(c[sl])>=mid and np.max(c[sl])<=h[p] if d==1 else np.max(c[sl])<=mid and np.min(c[sl])>=l[p]
                else:
                    ok=np.max(h[sl])<=h[p] and np.min(l[sl])>=l[p]
                if ok:found.append((p,d))
            if found:
                # Single signal per completed hour. Reject opposing signals.
                used.update(p for p,d in found)
                if len({d for p,d in found})==1:out[name].append((i,found[0][1],float(a[k])))
    return out

def replay(bars,signals,start,end):
    O,H,L,C=bars;free=0;ts=[]
    for i,d,a in signals:
        if i<free:continue
        risk=max(.5,math.ceil(2*a*2)/2);ep=float(O[i])
        j,xp,reason,mfe,mae=bracket(O,H,L,C,i,d,risk)
        free=j+1;gross=d*(xp-ep);fee=(ep+xp)*FEE
        ts.append(dict(entry_utc=dt(start+i*60).isoformat(),exit_utc=dt(end if reason==3 else start+j*60).isoformat(),side=d,entry_price=ep,exit_price=float(xp),gross_points=float(gross),fee_points=float(fee),net_points=float(gross-fee),exit_reason={1:"Initial SL",2:"Fixed TP",3:"Evaluation end"}[reason],signal_context=dict(risk_points=float(risk),entry_atr=float(a),mfe=float(mfe),mae=float(mae))))
    return ts

def run():
    checks();unit_checks();OUT.mkdir(parents=True,exist_ok=True)
    results={name:dict(name=name,years={}) for name in NAMES}
    for year in (2024,2025):
        if year==2024:
            q.candles=y24.candles;bars,signals,snapshots,extra,rec=y24.load();start,end,ev=y24.START,y24.END,y24.EVAL
        else:
            q.candles=candles25;bars,signals,snapshots,extra,rec=y25.load();start,end,ev=y25.START,y25.END,y25.START
        ind=q.indicators(bars,snapshots);candidates=signal_lists(bars,ind,snapshots,extra,start,ev)
        for name in NAMES:
            ts=replay(bars,candidates[name],start,end);s=summarize(ts,year);st=summarize(ts,year,50)
            if name=="reference-3-inside":
                assert math.isclose(s["net"],{2024:3939.68544,2025:7956.80671}[year],abs_tol=1e-5),(year,s["net"])
                assert len(ts)=={2024:4,2025:7}[year]
            s["signals"]=len(candidates[name]);s["stress"]=dict(net=st["net"],months=st["profitable_months"],pf=st["profit_factor"],dd=st["realized_drawdown_points"])
            s["median_risk"]=float(np.median([t["signal_context"]["risk_points"] for t in ts])) if ts else None
            s["months_1000_points"]=sum(x>=1000 for x in s["monthly_entry_attribution"].values())
            results[name]["years"][year]=dict(summary=s,trades=ts)
        del bars,ind,snapshots,extra,rec
    rows=[]
    for name,v in results.items():
        a,b=[v["years"][y]["summary"] for y in (2024,2025)]
        blocks=[sum(p for m,p in s["monthly_entry_attribution"].items() if (int(m[-2:])>6)==bool(h)) for s in (a,b) for h in (0,1)]
        row=dict(key=name,net24=a["net"],net25=b["net"],net=a["net"]+b["net"],months24=a["profitable_months"],months25=b["profitable_months"],months=a["profitable_months"]+b["profitable_months"],dd24=a["realized_drawdown_points"],dd25=b["realized_drawdown_points"],dd=max(a["realized_drawdown_points"],b["realized_drawdown_points"]),trades24=a["trades"],trades25=b["trades"],pf24=a["profit_factor"],pf25=b["profit_factor"],win24=a["win_rate"],win25=b["win_rate"],stress24=a["stress"]["net"],stress25=b["stress"]["net"],stress_months=a["stress"]["months"]+b["stress"]["months"],positive_blocks=sum(p>0 for p in blocks),blocks=blocks,months_1000_points=a["months_1000_points"]+b["months_1000_points"],fees24=a["fees"],fees25=b["fees"],median_risk24=a["median_risk"],median_risk25=b["median_risk"],accepted=all(x["stress"]["net"]>0 and x["trades"]>=30 for x in (a,b)) and all(p>0 for p in blocks))
        rows.append(row);print("RESULT",json.dumps(row,allow_nan=False))
        print("DETAIL",json.dumps(dict(key=name,years={y:v["years"][y]["summary"] for y in (2024,2025)}),allow_nan=False))
    with (OUT/"results.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    with gzip.open(OUT/"all_results.json.gz","wt") as f:json.dump(results,f,allow_nan=False,separators=(",",":"))
    print("COUNTS",json.dumps(dict(total=len(rows),both_year_positive=sum(x["net24"]>0 and x["net25"]>0 for x in rows),accepted=sum(x["accepted"] for x in rows),max_months=max(x["months"] for x in rows))))
if __name__=="__main__":run()
