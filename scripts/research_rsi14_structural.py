"""One-at-a-time structural tests, not a search for best numerical parameters."""
import csv,gzip,json,math
from pathlib import Path
import numpy as np
from numba import njit
import research_rsi14_depth_stability as b
from research_rsi14_nearby_thresholds import signals_for
from research_rsi14_consistency_risk_2025 import retest
from research_rsi14_depth_stability import y24,y25,q,candles25,checks,summarize,FEE,dt
OUT=Path("scratch/rsi14_structural")
BASES={80:(.25,750,True),83:(.375,0,False)}
IDEAS=("baseline","h4-trend","retest","rsi-recovery","market-structure","atr-expansion","partial-50")
REF={80:{2024:3517.781215,2025:15616.11716},83:{2024:10492.1397,2025:20702.36849}}
@njit
def partial_trade(O,H,L,C,i,d,be):
    # Book half at a fixed 2R limit. Retain the baseline stop and trailing
    # rules for the runner; no reset or re-entry after partial.
    ep=O[i];stop=ep-d*1000;act=ep+d*3000;target=ep+d*2000;best=ep;armed=-1;paid=False
    lock=ep*(d+FEE)/(d-FEE)
    lock=math.ceil(lock*2)/2 if d==1 else math.floor(lock*2)/2
    mfe=mae=0.
    for j in range(i,len(O)):
        o,h,l,c=O[j],H[j],L[j],C[j]
        if d*(o-stop)<=0:
            mae=max(mae,-d*(o-ep));return j,(o+target)/2 if paid else o,2 if armed>=0 else 3 if d*(stop-ep)>=0 else 1,stop,armed,mfe,mae,paid,o
        mfe=max(mfe,d*(o-ep));mae=max(mae,-d*(o-ep))
        if d*(o-best)>0:best=o
        if d*(best-target)>=0:paid=True
        stop=b.tighten(stop,best,ep,d,be,False,lock)
        if armed<0 and d*(o-act)>=0:armed=j
        if armed>=0 and d*(best-d*1000-stop)>0:stop=best-d*1000
        seq=(o,l,h,c) if c>o or (c==o and o-l<=h-o) else (o,h,l,c)
        for k in range(3):
            a,z=seq[k],seq[k+1]
            if d*(z-a)<0:
                if d*(a-stop)>=0 and d*(z-stop)<=0:
                    mae=max(mae,-d*(stop-ep))
                    return j,(stop+target)/2 if paid else stop,2 if armed>=0 else 3 if d*(stop-ep)>=0 else 1,stop,armed,mfe,mae,paid,stop
                mae=max(mae,-d*(z-ep))
            elif d*(z-a)>0:
                mfe=max(mfe,d*(z-ep))
                if d*(z-best)>0:best=z
                if d*(best-target)>=0:paid=True
                stop=b.tighten(stop,best,ep,d,be,False,lock)
                if armed<0 and d*(z-act)>=0:armed=j
                if armed>=0 and d*(best-d*1000-stop)>0:stop=best-d*1000
    x=C[-1]
    return len(O)-1,(x+target)/2 if paid else x,4,stop,armed,mfe,mae,paid,x

def h4_ema(C):
    closes=C[239::240];out=np.full(len(closes)+1,np.nan)
    if len(closes)>=50:
        out[50]=np.mean(closes[:50])
        for k in range(51,len(out)):out[k]=out[k-1]+(2/51)*(closes[k-1]-out[k-1])
    return out

def replay(bars,ind,setups,start,end,hi,idea,snapshots,extra,h4,avg):
    dep,be,ema=BASES[hi]
    O,H,L,C=bars;atr=ind[-1];rsi=ind[2];out=[];free=0
    def eligible(i,d,depth):
        e=snapshots[(i//15)*15][1]
        return depth>=dep and (not ema or (e is not None and d*(C[i-1]-e)>0))
    for first,d,r,trigger,level,pull,depth,until,retries in setups:
        if first<free or not eligible(first,d,depth):continue
        i=first
        if idea=="retest":
            i=retest(bars,first,d,level,until)
            if i<free or i>=until or not eligible(i,d,depth):continue
        k=i//15
        if idea=="h4-trend":
            h=i//240
            if h<1 or not d*(h4[h]-h4[h-1])>0:continue
        if idea=="rsi-recovery" and not (k>=1 and d*(rsi[k]-rsi[k-1])>0):continue
        if idea=="market-structure":
            # Entire pullback after the signal through the last completed
            # pre-breakout minute must stay above the signal low (long)
            # or below the signal high (short). No future pivot bars.
            if d==1 and not np.min(L[trigger:i])>extra[trigger][4]:continue
            if d==-1 and not np.max(H[trigger:i])<extra[trigger][3]:continue
        if idea=="atr-expansion" and not atr[k]>avg[k]:continue
        ep=float(O[i]);at=float(atr[k]);paid=False;runner=None
        if idea=="partial-50":
            j,xp,reason,stop,armed,mfe,mae,paid,runner=partial_trade(O,H,L,C,i,d,be)
        else:
            j,xp,reason,stop,armed,mfe,mae=b.trade(O,H,L,C,i,d,3000.,be,False)
        free=j+1;gross=d*(xp-ep);fee=(ep+xp)*FEE
        out.append(dict(entry_utc=dt(start+i*60).isoformat(),trigger_utc=dt(start+trigger*60).isoformat(),exit_utc=dt(end if reason==4 else start+j*60).isoformat(),side=d,entry_price=ep,exit_price=float(xp),gross_points=float(gross),fee_points=float(fee),net_points=float(gross-fee),exit_reason={1:"Initial SL",2:"Trailing SL",3:"Profit protection",4:"Evaluation end"}[reason],signal_context=dict(rsi14=r,risk_points=1000.,entry_atr=at,depth=depth,breakout_level=level,mfe=float(mfe),mae=float(mae),partial_filled=bool(paid),partial_price=ep+d*2000 if paid else None,runner_exit=float(runner) if runner is not None else None,activation_utc=dt(start+armed*60).isoformat() if armed>=0 else None)))
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
                s["partial_fills"]=sum(t["signal_context"]["partial_filled"] for t in ts)
                if idea=="baseline":assert math.isclose(s["net"],REF[hi][year],abs_tol=1e-5),(hi,year,s)
                results[f"{hi}-{idea}"]["years"][year]=dict(summary=s,trades=ts)
        del bars,ind,snapshots,extra,rec
    rows=[]
    for k,v in results.items():
        hi=v["upper"];idea=v["idea"]
        a,c=[v["years"][y]["summary"] for y in (2024,2025)]
        x,z=[results[f"{hi}-baseline"]["years"][y]["summary"] for y in (2024,2025)]
        blocks=[sum(p for m,p in s["monthly_entry_attribution"].items() if (int(m[-2:])>6)==bool(h)) for s in (a,c) for h in (0,1)]
        row=dict(key=k,upper=hi,idea=idea,net24=a["net"],net25=c["net"],months24=a["profitable_months"],months25=c["profitable_months"],pf24=a["profit_factor"],pf25=c["profit_factor"],dd24=a["realized_drawdown_points"],dd25=c["realized_drawdown_points"],trades24=a["trades"],trades25=c["trades"],stress24=a["stress"]["net"],stress25=c["stress"]["net"],stress_months24=a["stress"]["months"],stress_months25=c["stress"]["months"],net=a["net"]+c["net"],months=a["profitable_months"]+c["profitable_months"],dd=max(a["realized_drawdown_points"],c["realized_drawdown_points"]),positive_blocks=sum(p>0 for p in blocks),blocks=blocks,stress_pass=all(s["stress"]["net"]>0 and s["trades"]>=30 for s in (a,c)),both_net_up=a["net"]>x["net"] and c["net"]>z["net"],both_months_nonworse=a["profitable_months"]>=x["profitable_months"] and c["profitable_months"]>=z["profitable_months"],both_dd_nonworse=a["realized_drawdown_points"]<=x["realized_drawdown_points"]+1e-7 and c["realized_drawdown_points"]<=z["realized_drawdown_points"]+1e-7,partial24=a["partial_fills"],partial25=c["partial_fills"])
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
