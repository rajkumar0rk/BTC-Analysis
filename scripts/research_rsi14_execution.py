"""One-at-a-time structural tests, not a search for best numerical parameters."""
import csv,gzip,json,math
from pathlib import Path
import numpy as np
from numba import njit
import research_rsi14_depth_stability as b
from research_rsi14_nearby_thresholds import signals_for
from research_rsi14_consistency_risk_2025 import retest
from research_rsi14_depth_stability import y24,y25,q,candles25,checks,summarize,FEE,dt
OUT=Path("scratch/rsi14_execution")
BASES={80:(.25,750,True),83:(.375,0,False)}
IDEAS=("baseline","failure-exit","structure-sl","atr-trailing","signal-invalidation","volume-confirmation","progressive")
REF={80:{2024:13127.152335,2025:15661.81115},83:{2024:9472.755755,2025:16694.0351}}
@njit
def risk_trade(O,H,L,C,atr,i,d,be,initial_stop,level,mode):
    ep=O[i];stop=initial_stop;act=ep+d*3000;best=ep;armed=-1
    lock=ep*(d+FEE)/(d-FEE)
    lock=math.ceil(lock*2)/2 if d==1 else math.floor(lock*2)/2
    mfe=mae=0.
    for j in range(i,len(O)):
        o,h,l,c=O[j],H[j],L[j],C[j]
        if d*(o-stop)<=0:
            mae=max(mae,-d*(o-ep));return j,o,2 if armed>=0 else 3 if d*(stop-ep)>=0 else 1,stop,armed,mfe,mae
        if mode==1 and j>i and j%15==0 and d*(C[j-1]-level)<=0:
            return j,o,5,stop,armed,mfe,mae
        distance=1000.
        if mode==2 and np.isfinite(atr[j//15]) and atr[j//15]>0:
            distance=math.ceil(2*atr[j//15]*2)/2
        mfe=max(mfe,d*(o-ep));mae=max(mae,-d*(o-ep))
        if d*(o-best)>0:best=o
        stop=b.tighten(stop,best,ep,d,be,mode==3,lock)
        if armed<0 and d*(o-act)>=0:armed=j
        if armed>=0 and d*(best-d*distance-stop)>0:stop=best-d*distance
        if d*(o-stop)<=0:return j,o,2 if armed>=0 else 3,stop,armed,mfe,mae
        seq=(o,l,h,c) if c>o or (c==o and o-l<=h-o) else (o,h,l,c)
        for k in range(3):
            a,z=seq[k],seq[k+1]
            if d*(z-a)<0:
                if d*(a-stop)>=0 and d*(z-stop)<=0:
                    mae=max(mae,-d*(stop-ep))
                    return j,stop,2 if armed>=0 else 3 if d*(stop-ep)>=0 else 1,stop,armed,mfe,mae
                mae=max(mae,-d*(z-ep))
            elif d*(z-a)>0:
                mfe=max(mfe,d*(z-ep))
                if d*(z-best)>0:best=z
                stop=b.tighten(stop,best,ep,d,be,mode==3,lock)
                if armed<0 and d*(z-act)>=0:armed=j
                if armed>=0 and d*(best-d*distance-stop)>0:stop=best-d*distance
    return len(O)-1,C[-1],4,stop,armed,mfe,mae

def h4_ema(C):
    closes=C[239::240];out=np.full(len(closes)+1,np.nan)
    if len(closes)>=50:
        out[50]=np.mean(closes[:50])
        for k in range(51,len(out)):out[k]=out[k-1]+(2/51)*(closes[k-1]-out[k-1])
    return out

def replay(bars,ind,setups,start,end,hi,idea,snapshots,extra,h4,avg):
    dep,be,ema=BASES[hi]
    O,H,L,C=bars;atr=ind[-1];rsi=ind[2];vol,vm=ind[:2];out=[];free=0
    def eligible(i,d,depth):
        e=snapshots[(i//15)*15][1]
        return depth>=dep and (not ema or (e is not None and d*(C[i-1]-e)>0))
    for first,d,r,trigger,level,pull,depth,until,retries in setups:
        if first<free or not eligible(first,d,depth):continue
        i=first
        if hi==80:
            i=retest(bars,first,d,level,until)
            if i<free or i>=until or not eligible(i,d,depth):continue
        k=i//15
        if hi==83 and not atr[k]>avg[k]:continue
        if idea=="signal-invalidation" and np.any(d*(rsi[trigger//15:k+1]-50)<=0):continue
        if idea=="volume-confirmation" and not (vm[first-1]>0 and vol[first-1]>vm[first-1]):continue
        ep=float(O[i]);at=float(atr[k]);stop0=ep-d*1000
        if idea=="structure-sl":
            # Extreme of completed bars after signal through original breakout confirmation.
            # One tick beyond extreme; no future bars, no risk cap, no resizing.
            stop0=float(np.min(L[trigger:first])-.5 if d==1 else np.max(H[trigger:first])+.5)
            if d*(ep-stop0)<=0:continue
        risk=d*(ep-stop0)
        mode={"failure-exit":1,"atr-trailing":2,"progressive":3}.get(idea,0)
        be_used=1000 if idea=="progressive" else be
        if idea in ("failure-exit","atr-trailing","progressive","structure-sl"):
            j,xp,reason,stop,armed,mfe,mae=risk_trade(O,H,L,C,atr,i,d,be_used,stop0,level,mode)
        else:
            j,xp,reason,stop,armed,mfe,mae=b.trade(O,H,L,C,i,d,3000.,be,False)
        free=j+1;gross=d*(xp-ep);fee=(ep+xp)*FEE
        out.append(dict(entry_utc=dt(start+i*60).isoformat(),trigger_utc=dt(start+trigger*60).isoformat(),exit_utc=dt(end if reason==4 else start+j*60).isoformat(),side=d,entry_price=ep,exit_price=float(xp),gross_points=float(gross),fee_points=float(fee),net_points=float(gross-fee),exit_reason={1:"Initial SL",2:"Trailing SL",3:"Profit protection",4:"Evaluation end",5:"Breakout failure"}[reason],signal_context=dict(rsi14=r,risk_points=float(risk),initial_stop=float(stop0),entry_atr=at,depth=depth,breakout_level=level,mfe=float(mfe),mae=float(mae),partial_filled=False,activation_utc=dt(start+armed*60).isoformat() if armed>=0 else None)))
    return out

def run():
    checks();OUT.mkdir(parents=True,exist_ok=True)
    results={f"{hi}-{idea}":dict(upper=hi,idea=idea,years={}) for hi in BASES for idea in IDEAS}
    for year in (2024,2025):
        if year==2024:
            q.candles=y24.candles;bars,signals,snapshots,extra,rec=y24.load();start,end,ev=y24.START,y24.END,y24.EVAL
        else:
            q.candles=candles25;bars,signals,snapshots,extra,rec=y25.load();start,end=y25.START,y25.END;ev=start
        ind=q.indicators(bars,snapshots);atr=ind[-1];avg=np.full(len(atr),np.nan)
        for k in range(20,len(atr)):avg[k]=np.mean(atr[k-20:k])
        h4=h4_ema(bars[3])
        for hi in BASES:
            ss=signals if hi==80 else signals_for(rec,extra,start,end,ev,hi)
            setups=q.setup_rows(bars,ss,snapshots,extra)
            for idea in IDEAS:
                ts=replay(bars,ind,setups,start,end,hi,idea,snapshots,extra,h4,avg)
                s=summarize(ts,year);st=summarize(ts,year,50)
                s["stress"]=dict(net=st["net"],months=st["profitable_months"],pf=st["profit_factor"],dd=st["realized_drawdown_points"])
                s["meaningful_wins_over_50"]=sum(t["net_points"]>50 for t in ts)
                s["partial_fills"]=0
                s["median_initial_risk"]=float(np.median([t["signal_context"]["risk_points"] for t in ts])) if ts else 0.
                s["max_initial_risk"]=max((t["signal_context"]["risk_points"] for t in ts),default=0.)
                s["failure_exits"]=sum(t["exit_reason"]=="Breakout failure" for t in ts)
                if idea=="baseline":assert math.isclose(s["net"],REF[hi][year],abs_tol=1e-5),(hi,year,s)
                results[f"{hi}-{idea}"]["years"][year]=dict(summary=s,trades=ts)
        del bars,ind,snapshots,extra,rec
    rows=[]
    for k,v in results.items():
        hi=v["upper"];idea=v["idea"]
        a,c=[v["years"][y]["summary"] for y in (2024,2025)]
        x,z=[results[f"{hi}-baseline"]["years"][y]["summary"] for y in (2024,2025)]
        blocks=[sum(p for m,p in s["monthly_entry_attribution"].items() if (int(m[-2:])>6)==bool(h)) for s in (a,c) for h in (0,1)]
        row=dict(key=k,upper=hi,idea=idea,net24=a["net"],net25=c["net"],months24=a["profitable_months"],months25=c["profitable_months"],pf24=a["profit_factor"],pf25=c["profit_factor"],dd24=a["realized_drawdown_points"],dd25=c["realized_drawdown_points"],trades24=a["trades"],trades25=c["trades"],stress24=a["stress"]["net"],stress25=c["stress"]["net"],stress_months24=a["stress"]["months"],stress_months25=c["stress"]["months"],net=a["net"]+c["net"],months=a["profitable_months"]+c["profitable_months"],dd=max(a["realized_drawdown_points"],c["realized_drawdown_points"]),positive_blocks=sum(p>0 for p in blocks),blocks=blocks,stress_pass=all(s["stress"]["net"]>0 and s["trades"]>=30 for s in (a,c)),both_net_up=a["net"]>x["net"] and c["net"]>z["net"],both_months_nonworse=a["profitable_months"]>=x["profitable_months"] and c["profitable_months"]>=z["profitable_months"],both_dd_nonworse=a["realized_drawdown_points"]<=x["realized_drawdown_points"]+1e-7 and c["realized_drawdown_points"]<=z["realized_drawdown_points"]+1e-7,median_risk24=a["median_initial_risk"],median_risk25=c["median_initial_risk"],max_risk24=a["max_initial_risk"],max_risk25=c["max_initial_risk"],failure_exits24=a["failure_exits"],failure_exits25=c["failure_exits"])
        row["accepted"]=idea!="baseline" and row["stress_pass"] and row["both_net_up"] and row["both_months_nonworse"] and row["both_dd_nonworse"] and row["positive_blocks"]==4
        rows.append(row);print("RESULT",json.dumps(row,allow_nan=False))
    with (OUT/"results.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    with gzip.open(OUT/"all_results.json.gz","wt") as f:json.dump(results,f,allow_nan=False,separators=(",",":"))
    for hi in BASES:
        grp=[x for x in rows if x["upper"]==hi]
        print("COUNTS",json.dumps(dict(upper=hi,total=len(grp),accepted=sum(x["accepted"] for x in grp),stress_pass=sum(x["stress_pass"] for x in grp),max_months=max(x["months"] for x in grp))))
    for v in rows:
        print("DETAIL",json.dumps(dict(key=v["key"],years={y:results[v["key"]]["years"][y]["summary"] for y in (2024,2025)}),allow_nan=False))
if __name__=="__main__":run()
