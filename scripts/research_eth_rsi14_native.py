"""ETH-native RSI80/20 transfer. No BTC prices, no 2026 candles, no synthetic bars."""
import csv,gzip,json,math,hashlib
from pathlib import Path
from datetime import datetime,timezone
import numpy as np
from numba import njit
from research_rsi14_depth_stability import q,FEE,dt,checks
from research_five_higher_timeframe_strategies import aggregate,ema
from research_rsi14_consistency_risk_2025 import retest
OUT=Path("scratch/eth_rsi14_native")
P24=Path("data/delta_india/2024_recovery_candidates/ETHUSD")
P25=Path("data/delta_india/ETHUSD/1m")
MONTHS24=["2024-05","2024-10","2024-11","2024-12"]
MONTHS25=[f"2025-{m:02d}" for m in range(1,13)]
PLAN=[(mode,m) for mode in ("fixed","chandelier","continuation") for m in (2.,3.,4.)]
TICK=.05 # simulation assumption; historical tick schedule not verified
STRESS=.0005 # additional round-trip cost as fraction of entry notional

def loadmonth(m):
    if m.startswith("2024"):
        root=P24/m;meta=json.loads((root/"manifest.json").read_text());p=next(x for x in meta["series"] if x["series"]=="trade_1m");path=root/p["file"];sha=p["sha256"];expected=p["observed"]
        assert p["synthetic_rows"]==0
    else:
        p=next(x for x in json.loads((P25/"manifest.json").read_text())["partitions"] if x["file"]==m+".csv.gz");path=P25/p["file"];sha=p["sha256_gzip"];expected=p["observed_candles"];assert p["missing_minutes"]==0
    assert hashlib.sha256(path.read_bytes()).hexdigest()==sha
    with gzip.open(path,"rt") as f:
        rows=[(int(x["time"]),*[float(x[k]) for k in ("open","high","low","close")]) for x in csv.DictReader(f)]
    a=np.asarray(rows,dtype=float);assert len(a)==expected and np.all(np.isfinite(a))
    t=a[:,0].astype(np.int64);assert np.all(np.diff(t)>0) and np.all(t%60==0)
    O,H,L,C=a[:,1:].T
    assert np.all((L>0)&(L<=O)&(O<=H)&(L<=C)&(C<=H))
    return a

def segment(months,prior):
    a=np.concatenate([loadmonth(m) for m in months]);t=a[:,0].astype(np.int64);ev=int(t[0]);assert np.all(np.diff(t)==60)
    assert dt(ev).strftime("%Y-%m-%dT%H:%M") == months[0]+"-01T00:00"
    p=loadmonth(prior);p=p[p[:,0]>=ev-7*86400]
    gaps=np.flatnonzero(np.diff(p[:,0])!=60)
    if len(gaps):p=p[gaps[-1]+1:]
    if len(p) and p[-1,0]==ev-60:
        p=p[p[:,0]>=math.ceil(p[0,0]/3600)*3600]
        if len(p):a=np.concatenate([p,a])
    start=int(a[0,0]);end=int(a[-1,0])+60
    assert start%3600==0 and len(a)%15==0 and np.all(np.diff(a[:,0])==60)
    print("DATA",json.dumps(dict(months=months,scored_minutes=len(t),warmup_minutes=(ev-start)//60,start=dt(start).isoformat(),end=dt(end).isoformat())))
    return a[:,1:].T.copy(),start,end,ev

def entries(bars,start,ev):
    O,H,L,C=bars;o,h,l,c,at=aggregate(bars,15);_,_,_,hclose,_=aggregate(bars,60)
    r=np.r_[np.nan,q.rsi(c)];atr=np.r_[np.nan,at];e=np.r_[np.nan,ema(hclose,50)]
    snapshots={};extra={};signals=[]
    for k in range(1,len(c)+1):
        i=k*15;evma=e[i//60]
        snapshots[i]=(float(atr[k]) if np.isfinite(atr[k]) else None,float(evma) if np.isfinite(evma) else None,float(o[k-1]),float(c[k-1]))
        extra[i]=(None,None,None,float(h[k-1]),float(l[k-1]),float(c[k-1]))
        d=1 if r[k-1]<=80<r[k] else -1 if r[k-1]>=20>r[k] else 0
        if d and i<len(O) and start+i*60>=ev:signals.append((i,d,float(r[k]),float(h[k-1]),float(l[k-1])))
    setups=q.setup_rows(bars,signals,snapshots,extra)
    out=[]
    def allowed(i,d):
        v=snapshots[(i//15)*15][1];return v is not None and d*(C[i-1]-v)>0
    for first,d,rs,trigger,level,pull,depth,until,retries in setups:
        if depth<.25 or not allowed(first,d):continue
        i=retest(bars,first,d,level,until)
        if i<0 or i>=until or not allowed(i,d):continue
        if np.any(d*(r[trigger//15:i//15+1]-50)<=0):continue
        if not np.isfinite(atr[i//15]) or atr[i//15]<=0:continue
        out.append((first,i,d,trigger,level,depth,float(atr[i//15])))
    return atr,out

@njit
def sim(O,H,L,C,atr,i,d,risk,style):
    ep=O[i];stop=ep-d*risk;act=ep+d*3*risk;best=ep;armed=False;mfe=mae=0.
    lock=ep*(d+FEE)/(d-FEE)
    lock=math.ceil(lock/TICK)*TICK if d==1 else math.floor(lock/TICK)*TICK
    for j in range(i,len(O)):
        o,h,l,c=O[j],H[j],L[j],C[j]
        if d*(o-stop)<=0:return j,o,2 if armed else 1,mfe,max(mae,-d*(o-ep))
        if style==2 and armed and j>i and j%15==0 and j>=30:
            adverse=np.min(L[j-30:j-15]) if d==1 else np.max(H[j-30:j-15])
            if d*(C[j-1]-adverse)<0:return j,o,3,mfe,mae
        dist=risk
        if style==1 and np.isfinite(atr[j//15]) and atr[j//15]>0:dist=math.ceil(3*atr[j//15]/TICK)*TICK
        mfe=max(mfe,d*(o-ep));mae=max(mae,-d*(o-ep))
        if d*(o-best)>0:best=o
        if d*(best-ep)>=.75*risk and d*(best-lock)>=0 and d*(lock-stop)>0:stop=lock
        if d*(best-act)>=0:armed=True
        if armed and d*(best-d*dist-stop)>0:stop=best-d*dist
        if d*(o-stop)<=0:return j,o,2 if armed else 1,mfe,mae
        seq=(o,l,h,c) if c>o or (c==o and o-l<=h-o) else (o,h,l,c)
        for k in range(3):
            a,z=seq[k],seq[k+1]
            if d*(z-a)<0:
                if d*(z-stop)<=0:return j,stop,2 if armed else 1,mfe,max(mae,-d*(stop-ep))
                mae=max(mae,-d*(z-ep))
            elif d*(z-a)>0:
                mfe=max(mfe,d*(z-ep))
                if d*(z-best)>0:best=z
                if d*(best-ep)>=.75*risk and d*(best-lock)>=0 and d*(lock-stop)>0:stop=lock
                if d*(best-act)>=0:armed=True
                if armed and d*(best-d*dist-stop)>0:stop=best-d*dist
    return len(O)-1,C[-1],4,mfe,mae

def replay(bars,start,end,atr,events,mode,m):
    O,H,L,C=bars;free=0;ts=[]
    for first,i,d,trigger,level,depth,a in events:
        if first<free or i<free:continue
        ep=float(O[i]);risk=math.ceil(m*a/TICK)*TICK
        j,xp,reason,mfe,mae=sim(O,H,L,C,atr,i,d,risk,("fixed","chandelier","continuation").index(mode))
        free=j+1;gross=d*(xp-ep);fee=(ep+xp)*FEE
        ts.append(dict(entry_utc=dt(start+i*60).isoformat(),exit_utc=dt(end if reason==4 else start+j*60).isoformat(),side=d,entry_price=ep,exit_price=float(xp),gross=float(gross),fee=float(fee),net=float(gross-fee),risk=float(risk),atr=a,mfe=float(mfe),mae=float(mae),reason=int(reason)))
    return ts

def summary(ts,months):
    ms=dict.fromkeys(months,0.);eq=peak=dd=0.;g=l=0.;stress=0.;returns=0.;wins=0
    for t in ts:
        n=t["net"];ms[t["entry_utc"][:7]]+=n;eq+=n;peak=max(peak,eq);dd=max(dd,peak-eq);g+=max(n,0);l+=max(-n,0);wins+=n>0;stress+=n-t["entry_price"]*STRESS;returns+=n/t["entry_price"]*100
    return dict(net=eq,pf=g/l if l else None,dd=dd,months=sum(v>0 for v in ms.values()),monthly=ms,trades=len(ts),win=100*wins/len(ts) if ts else 0.,stress=stress,mean_return_pct=returns/len(ts) if ts else 0.,median_sl=float(np.median([t["risk"] for t in ts])) if ts else None,median_sl_pct=float(np.median([100*t["risk"]/t["entry_price"] for t in ts])) if ts else None)

def run():
    checks();OUT.mkdir(parents=True,exist_ok=True)
    results={f"{mode}-{m:g}ATR":{2024:[],2025:[]} for mode,m in PLAN}
    for year,months,prior in [(2024,["2024-05"],"2024-04"),(2024,["2024-10","2024-11","2024-12"],"2024-09"),(2025,MONTHS25,"2024-12")]:
        bars,start,end,ev=segment(months,prior);atr,events=entries(bars,start,ev)
        print("EVENTS",year,len(events))
        for mode,m in PLAN:results[f"{mode}-{m:g}ATR"][year].extend(replay(bars,start,end,atr,events,mode,m))
    rows=[]
    for key,ts in results.items():
        a=summary(ts[2024],MONTHS24);b=summary(ts[2025],MONTHS25)
        row=dict(key=key,net24=a["net"],net25=b["net"],net=a["net"]+b["net"],months24=a["months"],months25=b["months"],months=a["months"]+b["months"],trades24=a["trades"],trades25=b["trades"],pf24=a["pf"],pf25=b["pf"],dd24=a["dd"],dd25=b["dd"],dd=max(a["dd"],b["dd"]),stress24=a["stress"],stress25=b["stress"],median_sl24=a["median_sl"],median_sl25=b["median_sl"],median_sl_pct24=a["median_sl_pct"],median_sl_pct25=b["median_sl_pct"],win24=a["win"],win25=b["win"],mean_return24=a["mean_return_pct"],mean_return25=b["mean_return_pct"])
        rows.append(row);print("RESULT",json.dumps(row,allow_nan=False));print("DETAIL",json.dumps(dict(key=key,year24=a,year25=b),allow_nan=False))
    with (OUT/"results.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    with gzip.open(OUT/"all_results.json.gz","wt") as f:json.dump(results,f,allow_nan=False)
    print("COUNTS",json.dumps(dict(total=len(rows),both_positive=sum(x["net24"]>0 and x["net25"]>0 for x in rows),both_stress_positive=sum(x["stress24"]>0 and x["stress25"]>0 for x in rows),max_months=max(x["months"] for x in rows))))
if __name__=="__main__":run()
