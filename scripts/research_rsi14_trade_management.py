"""One-at-a-time structural tests, not a search for best numerical parameters."""
import csv,gzip,json,math
from pathlib import Path
import numpy as np
from numba import njit
import research_rsi14_depth_stability as b
from research_rsi14_nearby_thresholds import signals_for
from research_rsi14_consistency_risk_2025 import retest
from research_rsi14_depth_stability import y24,y25,q,candles25,checks,summarize,FEE,dt
OUT=Path("scratch/rsi14_trade_management")
BASES={"80-retest-invalidation":(80,.25,750,True),"80-chandelier":(80,.25,750,True)}
IDEAS=("baseline","stagnation","supertrend","time-reduce","pullback-volume","volatility-exposure")
REF={"80-retest-invalidation":{2024:10619.81256,2025:13943.95523},"80-chandelier":{2024:9644.735195,2025:12787.68496}}
@njit
def ratchet(stop,best,d,distance,style,st,line):
    if style==1:
        if st!=d or not np.isfinite(line) or d*(best-line)<=0:return stop
        new=math.floor(line*2)/2 if d==1 else math.ceil(line*2)/2
    else:new=best-d*distance
    return new if d*(new-stop)>0 else stop

@njit
def execute(O,H,L,C,atr,ST,LINE,i,d,be,trail_mult,style,mode):
    ep=O[i];stop=ep-d*1000;act=ep+d*3000;best=ep;armed=-1;partial=0.;part_j=-1
    due=((i+14)//15)*15+120
    lock=ep*(d+FEE)/(d-FEE)
    lock=math.ceil(lock*2)/2 if d==1 else math.floor(lock*2)/2
    mfe=mae=0.
    for j in range(i,len(O)):
        o,h,l,c=O[j],H[j],L[j],C[j]
        if d*(o-stop)<=0:
            mae=max(mae,-d*(o-ep));return j,o,2 if armed>=0 else 3 if d*(stop-ep)>=0 else 1,stop,armed,mfe,mae,partial,part_j
        if j==due:
            if mode==1 and max(mfe,d*(o-ep))<500:return j,o,5,stop,armed,mfe,mae,partial,part_j
            if mode==2 and d*(o-ep)<0:partial=o;part_j=j
        k=j//15;distance=1000.
        if trail_mult>0 and np.isfinite(atr[k]) and atr[k]>0:distance=math.ceil(trail_mult*atr[k]*2)/2
        mfe=max(mfe,d*(o-ep));mae=max(mae,-d*(o-ep))
        if d*(o-best)>0:best=o
        stop=b.tighten(stop,best,ep,d,be,False,lock)
        if armed<0 and d*(o-act)>=0:armed=j
        if armed>=0:stop=ratchet(stop,best,d,distance,style,ST[k],LINE[k])
        if d*(o-stop)<=0:return j,o,2 if armed>=0 else 3,stop,armed,mfe,mae,partial,part_j
        seq=(o,l,h,c) if c>o or (c==o and o-l<=h-o) else (o,h,l,c)
        for k2 in range(3):
            a,z=seq[k2],seq[k2+1]
            if d*(z-a)<0:
                if d*(a-stop)>=0 and d*(z-stop)<=0:
                    mae=max(mae,-d*(stop-ep))
                    return j,stop,2 if armed>=0 else 3 if d*(stop-ep)>=0 else 1,stop,armed,mfe,mae,partial,part_j
                mae=max(mae,-d*(z-ep))
            elif d*(z-a)>0:
                mfe=max(mfe,d*(z-ep))
                if d*(z-best)>0:best=z
                stop=b.tighten(stop,best,ep,d,be,False,lock)
                if armed<0 and d*(z-act)>=0:armed=j
                if armed>=0:stop=ratchet(stop,best,d,distance,style,ST[k],LINE[k])
    return len(O)-1,C[-1],4,stop,armed,mfe,mae,partial,part_j

def replay(bars,ind,setups,start,end,name,idea,snapshots,extra,avg,ST,LINE,v15,vavg):
    hi,dep,be,ema=BASES[name]
    O,H,L,C=bars;atr=ind[-1];rsi=ind[2];out=[];free=0
    def eligible(i,d,depth):
        e=snapshots[(i//15)*15][1]
        return depth>=dep and (not ema or (e is not None and d*(C[i-1]-e)>0))
    for first,d,r,trigger,level,pull,depth,until,retries in setups:
        if first<free or not eligible(first,d,depth):continue
        i=retest(bars,first,d,level,until)
        if i<free or i>=until or not eligible(i,d,depth):continue
        k=i//15
        if np.any(d*(rsi[trigger//15:k+1]-50)<=0):continue
        if idea=="pullback-volume":
            pk=pull//15-1
            if pk<0 or not v15[pk]<vavg[pk]:continue
        ep=float(O[i]);at=float(atr[k])
        size=1.
        if idea=="volatility-exposure":
            if not np.isfinite(at) or at<=0 or not np.isfinite(avg[k]) or avg[k]<=0:continue
            size=min(1.,avg[k]/at)
        trail_mult=3. if name=="80-chandelier" else 0.
        mode={"stagnation":1,"time-reduce":2}.get(idea,0)
        style=1 if idea=="supertrend" else 0
        partial=0.;part_j=-1
        if trail_mult or mode or style:
            j,xp,reason,stop,armed,mfe,mae,partial,part_j=execute(O,H,L,C,atr,ST,LINE,i,d,be,trail_mult,style,mode)
        else:
            j,xp,reason,stop,armed,mfe,mae=b.trade(O,H,L,C,i,d,3000.,be,False)
        free=j+1
        effective=(xp+partial)/2 if part_j>=0 else xp
        gross=d*(effective-ep)*size;fee=(ep+effective)*FEE*size
        out.append(dict(entry_utc=dt(start+i*60).isoformat(),trigger_utc=dt(start+trigger*60).isoformat(),exit_utc=dt(end if reason==4 else start+j*60).isoformat(),side=d,entry_price=ep,exit_price=float(xp),gross_points=float(gross),fee_points=float(fee),net_points=float(gross-fee),exit_reason={1:"Initial SL",2:"Trailing SL",3:"Profit protection",4:"Evaluation end",5:"Stagnation"}[reason],signal_context=dict(rsi14=r,risk_points=1000.,size_multiplier=float(size),entry_atr=at,depth=depth,breakout_level=level,mfe=float(mfe),mae=float(mae),partial_price=float(partial) if part_j>=0 else None,partial_utc=dt(start+part_j*60).isoformat() if part_j>=0 else None,activation_utc=dt(start+armed*60).isoformat() if armed>=0 else None)))
    return out

def stressed(ts,year):
    copies=[dict(t,net_points=t["net_points"]-50*t["signal_context"]["size_multiplier"]) for t in ts]
    return summarize(copies,year)

def run():
    checks();OUT.mkdir(parents=True,exist_ok=True)
    results={f"{name}-{idea}":dict(candidate=name,upper=BASES[name][0],idea=idea,years={}) for name in BASES for idea in IDEAS}
    assert len(results)==12
    for year in (2024,2025):
        if year==2024:
            q.candles=y24.candles;bars,signals,snapshots,extra,rec=y24.load();start,end,ev=y24.START,y24.END,y24.EVAL
        else:
            q.candles=candles25;bars,signals,snapshots,extra,rec=y25.load();start,end=y25.START,y25.END;ev=start
        ind=q.indicators(bars,snapshots);atr=ind[-1];avg=np.full(len(atr),np.nan)
        for k in range(20,len(atr)):avg[k]=np.mean(atr[k-20:k])
        ST=np.full(len(atr),np.nan);LINE=ST.copy()
        for minute,v in extra.items():
            if minute%15==0:
                if v[1] is not None:ST[minute//15]=v[1]
                if v[2] is not None:LINE[minute//15]=v[2]
        v15=ind[0].reshape(-1,15).sum(axis=1);vavg=np.full(len(v15),np.nan)
        for k in range(20,len(v15)):vavg[k]=np.mean(v15[k-20:k])
        for name in BASES:
            hi=BASES[name][0]
            ss=signals if hi==80 else signals_for(rec,extra,start,end,ev,hi)
            setups=q.setup_rows(bars,ss,snapshots,extra)
            for idea in IDEAS:
                ts=replay(bars,ind,setups,start,end,name,idea,snapshots,extra,avg,ST,LINE,v15,vavg)
                s=summarize(ts,year);st=stressed(ts,year)
                s["stress"]=dict(net=st["net"],months=st["profitable_months"],pf=st["profit_factor"],dd=st["realized_drawdown_points"])
                s["meaningful_wins_over_50"]=sum(t["net_points"]>50 for t in ts)
                s["partial_fills"]=sum(t["signal_context"]["partial_price"] is not None for t in ts)
                s["median_initial_risk"]=float(np.median([t["signal_context"]["risk_points"] for t in ts])) if ts else 0.
                s["max_initial_risk"]=max((t["signal_context"]["risk_points"] for t in ts),default=0.)
                s["failure_exits"]=sum(t["exit_reason"]=="Stagnation" for t in ts)
                s["mean_size"]=float(np.mean([t["signal_context"]["size_multiplier"] for t in ts])) if ts else 0.
                s["max_size"]=max((t["signal_context"]["size_multiplier"] for t in ts),default=0.)
                if idea=="baseline":assert math.isclose(s["net"],REF[name][year],abs_tol=1e-5),(hi,year,s)
                results[f"{name}-{idea}"]["years"][year]=dict(summary=s,trades=ts)
        del bars,ind,snapshots,extra,rec
    rows=[]
    for k,v in results.items():
        hi=v["upper"];name=v["candidate"];idea=v["idea"]
        a,c=[v["years"][y]["summary"] for y in (2024,2025)]
        x,z=[results[f"{name}-baseline"]["years"][y]["summary"] for y in (2024,2025)]
        blocks=[sum(p for m,p in s["monthly_entry_attribution"].items() if (int(m[-2:])>6)==bool(h)) for s in (a,c) for h in (0,1)]
        row=dict(key=k,candidate=name,upper=hi,idea=idea,net24=a["net"],net25=c["net"],months24=a["profitable_months"],months25=c["profitable_months"],pf24=a["profit_factor"],pf25=c["profit_factor"],dd24=a["realized_drawdown_points"],dd25=c["realized_drawdown_points"],trades24=a["trades"],trades25=c["trades"],stress24=a["stress"]["net"],stress25=c["stress"]["net"],stress_months24=a["stress"]["months"],stress_months25=c["stress"]["months"],net=a["net"]+c["net"],months=a["profitable_months"]+c["profitable_months"],dd=max(a["realized_drawdown_points"],c["realized_drawdown_points"]),positive_blocks=sum(p>0 for p in blocks),blocks=blocks,stress_pass=all(s["stress"]["net"]>0 and s["trades"]>=30 for s in (a,c)),both_net_up=a["net"]>x["net"] and c["net"]>z["net"],both_months_nonworse=a["profitable_months"]>=x["profitable_months"] and c["profitable_months"]>=z["profitable_months"],both_dd_nonworse=a["realized_drawdown_points"]<=x["realized_drawdown_points"]+1e-7 and c["realized_drawdown_points"]<=z["realized_drawdown_points"]+1e-7,median_risk24=a["median_initial_risk"],median_risk25=c["median_initial_risk"],max_risk24=a["max_initial_risk"],max_risk25=c["max_initial_risk"],failure_exits24=a["failure_exits"],failure_exits25=c["failure_exits"],max_size24=a["max_size"],max_size25=c["max_size"],mean_size24=a["mean_size"],mean_size25=c["mean_size"],partial24=a["partial_fills"],partial25=c["partial_fills"])
        row["accepted"]=idea!="baseline" and row["stress_pass"] and row["both_net_up"] and row["both_months_nonworse"] and row["both_dd_nonworse"] and row["positive_blocks"]==4
        rows.append(row);print("RESULT",json.dumps(row,allow_nan=False))
    with (OUT/"results.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    with gzip.open(OUT/"all_results.json.gz","wt") as f:json.dump(results,f,allow_nan=False,separators=(",",":"))
    for name in BASES:
        grp=[x for x in rows if x["candidate"]==name]
        print("COUNTS",json.dumps(dict(candidate=name,total=len(grp),accepted=sum(x["accepted"] for x in grp),stress_pass=sum(x["stress_pass"] for x in grp),max_months=max(x["months"] for x in grp))))
    for v in rows:
        print("DETAIL",json.dumps(dict(key=v["key"],years={y:results[v["key"]]["years"][y]["summary"] for y in (2024,2025)}),allow_nan=False))
if __name__=="__main__":run()
