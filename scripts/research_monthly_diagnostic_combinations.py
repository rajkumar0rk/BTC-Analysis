"""Factorial ablations of five predefined diagnostic ideas; separate strategies; 2026 excluded."""
import csv,gzip,json,math
from itertools import product
from pathlib import Path
import numpy as np
from numba import njit
import research_rsi14_depth_stability as b
import research_rsi14_entry_exit_diagnostics as r
import research_momentum_continuation_frequency as m
from research_rsi14_consistency_risk_2025 import retest
from research_rsi14_depth_stability import y24,y25,q,candles25,checks,summarize,FEE,dt
OUT=Path("scratch/monthly_diagnostic_combinations")
RULES={"rsi":("strength","expansion","structure","early-protection"),"momentum":("strength","expansion","structure","early-protection","efficiency")}
PLAN=[(n,flags) for n,labels in RULES.items() for flags in product((False,True),repeat=len(labels))]
REF={"rsi":{2024:9644.735195,2025:12787.68496},"momentum":{2024:3185.70309,2025:12141.56828}}
def key(n,flags):return n+":"+("+".join(k for k,v in zip(RULES[n],flags) if v) or "baseline")
@njit
def path(o,h,l,c):
    return (o,l,h,c) if c>o or (c==o and o-l<=h-o) else (o,h,l,c)

@njit
def sim(O,H,L,C,atr,i,d,ep,be,trail_mult,activation,limit_fill,continuation,risk):
    stop=ep-d*risk;act=ep+d*activation;best=ep;armed=-1;mfe=mae=0.
    lock=ep*(d+FEE)/(d-FEE)
    lock=math.ceil(lock*2)/2 if d==1 else math.floor(lock*2)/2
    for j in range(i,len(O)):
        o,h,l,c=O[j],H[j],L[j],C[j]
        seq=path(o,h,l,c);a0=o;k0=0
        if j==i and limit_fill and d*(o-ep)>0:
            # Limit was resting before this minute. Ignore the path before
            # the first adverse crossing of the limit.
            hit=False
            for k in range(3):
                if d*(seq[k]-ep)>0 and d*(seq[k+1]-ep)<=0:
                    a0=ep;k0=k;hit=True;break
            if not hit:raise ValueError("limit not crossed")
        if d*(a0-stop)<=0:
            mae=max(mae,-d*(a0-ep));return j,a0,2 if armed>=0 else 3 if d*(stop-ep)>=0 else 1,stop,armed,mfe,mae
        if continuation and armed>=0 and j>i and j%15==0 and j>=30:
            adverse=np.min(L[j-30:j-15]) if d==1 else np.max(H[j-30:j-15])
            if d*(C[j-1]-adverse)<0:return j,o,5,stop,armed,mfe,mae
        distance=1000.
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


@njit
def momentum_exit(O,H,L,C,i,d,risk,protect):
    ep=O[i];stop=ep-d*risk;target=ep+d*2*risk;best=ep;mfe=mae=0.
    lock=ep*(d+FEE)/(d-FEE)
    lock=math.ceil(lock*2)/2 if d==1 else math.floor(lock*2)/2
    activation=max(.5*risk,d*(lock-ep)+.5)
    for j in range(i,len(O)):
        o,h,l,c=O[j],H[j],L[j],C[j]
        if d*(o-stop)<=0:return j,o,1,mfe,max(mae,-d*(o-ep))
        if d*(o-target)>=0:return j,target,2,max(mfe,2*risk),mae
        mfe=max(mfe,d*(o-ep));mae=max(mae,-d*(o-ep))
        if d*(o-best)>0:best=o
        if protect and d*(best-ep)>=activation and d*(lock-stop)>0:stop=lock
        seq=path(o,h,l,c)
        for k in range(3):
            a,z=seq[k],seq[k+1]
            if d*(z-a)<0:
                if d*(z-stop)<=0:return j,stop,1,mfe,max(mae,-d*(stop-ep))
                mae=max(mae,-d*(z-ep))
            elif d*(z-a)>0:
                if d*(z-target)>=0:return j,target,2,max(mfe,2*risk),mae
                mfe=max(mfe,d*(z-ep))
                if d*(z-best)>0:best=z
                if protect and d*(best-ep)>=activation and d*(lock-stop)>0:stop=lock
    return len(O)-1,C[-1],3,mfe,mae

def rsi_replay(bars,ind,setups,start,end,flags,snapshots,extra,avg,ST,LINE):
    strength,expansion,structure,early=flags
    O,H,L,C=bars;atr=ind[-1];rsi=ind[2];out=[];free=0
    def eligible(i,d,depth):
        e=snapshots[(i//15)*15][1]
        return depth>=.25 and e is not None and d*(C[i-1]-e)>0
    for first,d,rv,trigger,level,pull,depth,until,retries in setups:
        if first<free or not eligible(first,d,depth):continue
        i=retest(bars,first,d,level,until)
        if i<free or i>=until or not eligible(i,d,depth):continue
        k=i//15
        if np.any(d*(rsi[trigger//15:k+1]-50)<=0):continue
        z=i-1;span=H[z]-L[z];at=float(atr[k]);ep=float(O[i])
        if strength and not(span>0 and d*(C[z]-O[z])>=.5*span):continue
        if expansion and not(at>avg[k]):continue
        risk=1000.
        if structure:
            # Known confirmed 15m pullback extreme. Never widen original risk.
            _,_,_,ph,pl,_=extra[pull]
            stop=(pl-.5) if d==1 else (ph+.5)
            if d*(ep-stop)<=0:continue
            risk=min(risk,d*(ep-stop))
        be=500. if early else 750.
        # Do not arm protection before the fee-inclusive stop is attainable.
        if early:be=max(be,d*(ep*(d+FEE)/(d-FEE)-ep)+1.)
        if not any(flags):
            j,xp,reason,stop,armed,mfe,mae,_,_=r.reference_execute(O,H,L,C,atr,ST,LINE,i,d,750.,3.,0,0)
        else:
            j,xp,reason,stop,armed,mfe,mae=sim(O,H,L,C,atr,i,d,ep,be,3.,3000.,False,False,risk)
        free=j+1;gross=d*(xp-ep);fee=(ep+xp)*FEE
        out.append(dict(entry_utc=dt(start+i*60).isoformat(),exit_utc=dt(end if reason==4 else start+j*60).isoformat(),side=d,entry_price=ep,exit_price=float(xp),gross_points=float(gross),fee_points=float(fee),net_points=float(gross-fee),exit_reason={1:"Initial SL",2:"Trailing SL",3:"Profit protection",4:"Evaluation end",5:"Continuation exit"}[reason],signal_context=dict(risk_points=float(risk),entry_atr=at,mfe=float(mfe),mae=float(mae))))
    return out

def momentum_signals(bars,start,ev):
    o,h,l,c,a=m.aggregate(bars,60);_,_,_,c4,_=m.aggregate(bars,240);e4=m.ema(c4,50)
    used=set();out=[]
    for k in range(40,len(c)):
        i=(k+1)*60
        if i>=len(bars[0]) or start+i*60<ev or not np.isfinite(a[k]) or a[k]<=0:continue
        found=[]
        for n in (1,2,3):
            p=k-n-1
            if p in used or not np.isfinite(a[p-1]):continue
            d=1 if c[p]-o[p]>=a[p-1] and c[k]>h[p] else -1 if o[p]-c[p]>=a[p-1] and c[k]<l[p] else 0
            if d and np.max(h[p+1:k])<=h[p] and np.min(l[p+1:k])>=l[p]:found.append((p,d))
        if not found:continue
        used.update(p for p,d in found)
        if len({d for p,d in found})!=1:continue
        p,d=found[0];ix=i//240-1
        if ix<0 or not np.isfinite(e4[ix]) or d*(c[k]-e4[ix])<=0:continue
        span=h[k]-l[k];strong=span>0 and d*(c[k]-o[k])>=.5*span
        expansion=a[k]>np.mean(a[k-20:k])
        window=c[k-20:k+1];den=np.sum(np.abs(np.diff(window)))
        er=abs(window[-1]-window[0])/den if den>0 else 0.
        stop=np.min(l[p+1:k])-.5 if d==1 else np.max(h[p+1:k])+.5
        out.append((i,d,float(a[k]),float(stop),strong,expansion,er>=.3))
    return out

def momentum_replay(bars,signals,start,end,flags):
    strength,expansion,structure,early,efficiency=flags
    O,H,L,C=bars;out=[];free=0
    for i,d,a,stop,strong,expand,efficient in signals:
        if i<free or (strength and not strong) or (expansion and not expand) or (efficiency and not efficient):continue
        ep=float(O[i]);risk=max(.5,math.ceil(2*a*2)/2)
        if structure:
            if d*(ep-stop)<=0:continue
            risk=min(risk,d*(ep-stop))
        j,xp,reason,mfe,mae=momentum_exit(O,H,L,C,i,d,risk,early)
        free=j+1;gross=d*(xp-ep);fee=(ep+xp)*FEE
        out.append(dict(entry_utc=dt(start+i*60).isoformat(),exit_utc=dt(end if reason==3 else start+j*60).isoformat(),side=d,entry_price=ep,exit_price=float(xp),gross_points=float(gross),fee_points=float(fee),net_points=float(gross-fee),exit_reason={1:"Protective SL",2:"Fixed TP",3:"Evaluation end"}[reason],signal_context=dict(risk_points=float(risk),entry_atr=a,mfe=float(mfe),mae=float(mae))))
    return out

def run():
    checks();m.unit_checks();OUT.mkdir(parents=True,exist_ok=True)
    results={key(n,f):dict(strategy=n,flags=f,years={}) for n,f in PLAN}
    for year in (2024,2025):
        if year==2024:
            q.candles=y24.candles;bars,signals,snapshots,extra,rec=y24.load();start,end,ev=y24.START,y24.END,y24.EVAL
        else:
            q.candles=candles25;bars,signals,snapshots,extra,rec=y25.load();start,end,ev=y25.START,y25.END,y25.START
        ind=q.indicators(bars,snapshots);atr=ind[-1];avg=np.full(len(atr),np.nan)
        for k in range(20,len(atr)):avg[k]=np.mean(atr[k-20:k])
        ST=np.full(len(atr),np.nan);LINE=ST.copy()
        for minute,v in extra.items():
            if minute%15==0:
                if v[1] is not None:ST[minute//15]=v[1]
                if v[2] is not None:LINE[minute//15]=v[2]
        setups=q.setup_rows(bars,signals,snapshots,extra);ms=momentum_signals(bars,start,ev)
        for n,f in PLAN:
            ts=rsi_replay(bars,ind,setups,start,end,f,snapshots,extra,avg,ST,LINE) if n=="rsi" else momentum_replay(bars,ms,start,end,f)
            s=summarize(ts,year);st=summarize(ts,year,50)
            if not any(f):
                assert math.isclose(s["net"],REF[n][year],abs_tol=1e-5),(n,year,s["net"])
                assert len(ts)=={"rsi":{2024:44,2025:47},"momentum":{2024:29,2025:29}}[n][year]
                if n=="rsi":
                    # Compare generalized execution against frozen reference, trade by trade.
                    compare=r.replay(bars,ind,setups,start,end,"80-chandelier","baseline",snapshots,extra,avg,ST,LINE,None,None)
                    assert [x["net_points"] for x in ts]==[x["net_points"] for x in compare]
            s["stress_net"]=st["net"];s["stress_months"]=st["profitable_months"]
            s["no_trade_months"]=sum(1 for month in s["monthly_entry_attribution"] if not any(__import__("datetime").datetime.fromisoformat(t["entry_utc"]).astimezone(y24.IST if year==2024 else __import__("datetime").timezone.utc).strftime("%Y-%m")==month for t in ts))
            results[key(n,f)]["years"][year]=dict(summary=s,trades=ts)
        del bars,ind,snapshots,extra,rec
    rows=[]
    for k,v in results.items():
        a,c=[v["years"][y]["summary"] for y in (2024,2025)]
        blocks=[sum(p for mo,p in s["monthly_entry_attribution"].items() if (int(mo[-2:])>6)==bool(h)) for s in (a,c) for h in (0,1)]
        row=dict(key=k,net24=a["net"],net25=c["net"],net=a["net"]+c["net"],months24=a["profitable_months"],months25=c["profitable_months"],months=a["profitable_months"]+c["profitable_months"],trades24=a["trades"],trades25=c["trades"],pf24=a["profit_factor"],pf25=c["profit_factor"],dd=max(a["realized_drawdown_points"],c["realized_drawdown_points"]),dd24=a["realized_drawdown_points"],dd25=c["realized_drawdown_points"],stress24=a["stress_net"],stress25=c["stress_net"],stress_months=a["stress_months"]+c["stress_months"],zero_months=a["no_trade_months"]+c["no_trade_months"],positive_blocks=sum(p>0 for p in blocks),worst_month=min(a["worst_month"],c["worst_month"]))
        row["robust"]=all(s["stress_net"]>0 and s["trades"]>=30 for s in (a,c)) and row["positive_blocks"]==4
        rows.append(row);print("RESULT",json.dumps(row,allow_nan=False))
    with (OUT/"results.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    with gzip.open(OUT/"all_results.json.gz","wt") as f:json.dump(results,f,allow_nan=False,separators=(",",":"))
    for n in RULES:
        group=[x for x in rows if x["key"].startswith(n+":")]
        print("COUNTS",json.dumps(dict(strategy=n,total=len(group),both_year_positive=sum(x["net24"]>0 and x["net25"]>0 for x in group),robust=sum(x["robust"] for x in group),max_months=max(x["months"] for x in group))))
if __name__=="__main__":run()
