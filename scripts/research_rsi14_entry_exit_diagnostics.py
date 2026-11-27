"""One-at-a-time structural tests, not a search for best numerical parameters."""
import csv,gzip,json,math
from pathlib import Path
import numpy as np
from numba import njit
import research_rsi14_depth_stability as b
from research_rsi14_nearby_thresholds import signals_for
from research_rsi14_consistency_risk_2025 import retest
from research_rsi14_depth_stability import y24,y25,q,candles25,checks,summarize,FEE,dt
OUT=Path("scratch/rsi14_entry_exit_diagnostics")
BASES={"80-retest-invalidation":(80,.25,750,True),"80-chandelier":(80,.25,750,True)}
IDEAS=("baseline","second-chance","limit-entry","atr-activation","continuation-exit")
REF={"80-retest-invalidation":{2024:10619.81256,2025:13943.95523},"80-chandelier":{2024:9644.735195,2025:12787.68496}}
from research_rsi14_trade_management import execute as reference_execute

@njit
def path(o,h,l,c):
    return (o,l,h,c) if c>o or (c==o and o-l<=h-o) else (o,h,l,c)

@njit
def sim(O,H,L,C,atr,i,d,ep,be,trail_mult,activation,limit_fill,continuation):
    stop=ep-d*1000;act=ep+d*activation;best=ep;armed=-1;mfe=mae=0.
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

def replay(bars,ind,setups,start,end,name,idea,snapshots,extra,avg,ST,LINE,v15,vavg):
    hi,dep,be,ema=BASES[name]
    O,H,L,C=bars;atr=ind[-1];rsi=ind[2];out=[];free=0
    def eligible(i,d,depth):
        e=snapshots[(i//15)*15][1]
        return depth>=dep and (not ema or (e is not None and d*(C[i-1]-e)>0))
    def valid(trigger,i,d):
        return not np.any(d*(rsi[trigger//15:i//15+1]-50)<=0)
    for first,d,r,trigger,level,pull,depth,until,retries in setups:
        if first<free or not eligible(first,d,depth):continue
        i=retest(bars,first,d,level,until)
        if i<free or i>=until or not eligible(i,d,depth) or not valid(trigger,i,d):continue
        confirm=i
        for attempt in range(2 if idea=="second-chance" else 1):
            ep=float(O[i])
            if idea=="limit-entry":
                # After confirmed retest, submit resting limit at level.
                # Require trade-through by one tick, not mere touch. Cancel
                # at next threshold, RSI invalidation or failed trend filter.
                filled=False
                for k in range(i,until):
                    if not valid(trigger,k,d) or not eligible(k,d,depth):break
                    if (L[k]<level if d==1 else H[k]>level):
                        i=k;ep=float(level);filled=True;break
                if not filled:break
            at=float(atr[i//15]);trail_mult=3. if name=="80-chandelier" else 0.
            activation=3000.
            if idea=="atr-activation":
                if not np.isfinite(at) or at<=0:break
                activation=math.ceil(6*at*2)/2
            if idea in ("limit-entry","atr-activation","continuation-exit"):
                j,xp,reason,stop,armed,mfe,mae=sim(O,H,L,C,atr,i,d,ep,be,trail_mult,activation,idea=="limit-entry",idea=="continuation-exit")
            elif trail_mult:
                j,xp,reason,stop,armed,mfe,mae,_,_=reference_execute(O,H,L,C,atr,ST,LINE,i,d,be,trail_mult,0,0)
            else:
                j,xp,reason,stop,armed,mfe,mae=b.trade(O,H,L,C,i,d,3000.,be,False)
            free=j+1;gross=d*(xp-ep);fee=(ep+xp)*FEE
            recovery=0.
            # Descriptive post-exit diagnostic only. Never used for entries.
            if reason==1 and free<until:
                for k in range(free,until):
                    if not valid(trigger,k,d):break
                    recovery=max(recovery,d*((H[k] if d==1 else L[k])-ep))
            out.append(dict(entry_utc=dt(start+i*60).isoformat(),trigger_utc=dt(start+trigger*60).isoformat(),exit_utc=dt(end if reason==4 else start+j*60).isoformat(),side=d,entry_price=ep,exit_price=float(xp),gross_points=float(gross),fee_points=float(fee),net_points=float(gross-fee),exit_reason={1:"Initial SL",2:"Trailing SL",3:"Profit protection",4:"Evaluation end",5:"Continuation exit"}[reason],signal_context=dict(rsi14=r,risk_points=1000.,size_multiplier=1.,entry_atr=at,atr_ratio=float(at/avg[i//15]) if np.isfinite(avg[i//15]) and avg[i//15]>0 else None,depth=depth,breakout_level=level,mfe=float(mfe),mae=float(mae),entry_premium=float(d*(ep-level)),retest_delay_minutes=int(confirm-first),recovery=float(recovery),retry=bool(attempt),activation_points=float(activation),giveback=float(mfe-gross),partial_price=None,activation_utc=dt(start+armed*60).isoformat() if armed>=0 else None)))
            if idea!="second-chance" or attempt or reason!=1 or free>=until:break
            nxt=-1
            for raw in retries:
                raw=int(raw)
                # Fresh breakout crossing must be observed after the SL minute.
                if raw<=free or not eligible(raw,d,depth) or not valid(trigger,raw,d):continue
                cand=retest(bars,raw,d,level,until)
                if cand>=free and cand<until and eligible(cand,d,depth) and valid(trigger,cand,d):
                    nxt=cand;confirm=cand;break
            if nxt<0:break
            i=nxt
    return out

def diagnostics(ts):
    stopped=[t for t in ts if t["exit_reason"]=="Initial SL"]
    runners=[t for t in ts if t["signal_context"]["activation_utc"] is not None]
    ctx=lambda t:t["signal_context"]
    med=lambda x:float(np.median(x)) if x else None
    groups={}
    for label,cond in (("low_or_normal",lambda x:x<=1),("high",lambda x:x>1)):
        a=[t for t in ts if ctx(t)["atr_ratio"] is not None and cond(ctx(t)["atr_ratio"])]
        groups[label]=dict(trades=len(a),net=sum(t["net_points"] for t in a),activated=sum(ctx(t)["activation_utc"] is not None for t in a),median_entry_atr=med([ctx(t)["entry_atr"] for t in a]))
    return dict(trades=len(ts),initial_stops=len(stopped),recover_entry=sum(ctx(t)["recovery"]>0 for t in stopped),recover_1r=sum(ctx(t)["recovery"]>=1000 for t in stopped),recover_3r=sum(ctx(t)["recovery"]>=3000 for t in stopped),median_entry_premium=med([ctx(t)["entry_premium"] for t in ts]),positive_premium=sum(ctx(t)["entry_premium"]>0 for t in ts),median_retest_delay=med([ctx(t)["retest_delay_minutes"] for t in ts]),activated=len(runners),median_runner_giveback=med([ctx(t)["giveback"] for t in runners]),total_runner_giveback=sum(ctx(t)["giveback"] for t in runners),volatility=groups,retries=sum(ctx(t)["retry"] for t in ts))

def stressed(ts,year):
    copies=[dict(t,net_points=t["net_points"]-50*t["signal_context"]["size_multiplier"]) for t in ts]
    return summarize(copies,year)

def run():
    checks();OUT.mkdir(parents=True,exist_ok=True)
    results={f"{name}-{idea}":dict(candidate=name,upper=BASES[name][0],idea=idea,years={}) for name in BASES for idea in IDEAS}
    assert len(results)==10
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
                s["failure_exits"]=sum(t["exit_reason"]=="Continuation exit" for t in ts)
                s["diagnostics"]=diagnostics(ts)
                if idea=="baseline":print("DIAGNOSTIC",json.dumps(dict(candidate=name,year=year,**s["diagnostics"]),allow_nan=False))
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
        row=dict(key=k,candidate=name,upper=hi,idea=idea,net24=a["net"],net25=c["net"],months24=a["profitable_months"],months25=c["profitable_months"],pf24=a["profit_factor"],pf25=c["profit_factor"],dd24=a["realized_drawdown_points"],dd25=c["realized_drawdown_points"],trades24=a["trades"],trades25=c["trades"],stress24=a["stress"]["net"],stress25=c["stress"]["net"],stress_months24=a["stress"]["months"],stress_months25=c["stress"]["months"],net=a["net"]+c["net"],months=a["profitable_months"]+c["profitable_months"],dd=max(a["realized_drawdown_points"],c["realized_drawdown_points"]),positive_blocks=sum(p>0 for p in blocks),blocks=blocks,stress_pass=all(s["stress"]["net"]>0 and s["trades"]>=30 for s in (a,c)),both_net_up=a["net"]>x["net"] and c["net"]>z["net"],both_months_nonworse=a["profitable_months"]>=x["profitable_months"] and c["profitable_months"]>=z["profitable_months"],both_dd_nonworse=a["realized_drawdown_points"]<=x["realized_drawdown_points"]+1e-7 and c["realized_drawdown_points"]<=z["realized_drawdown_points"]+1e-7,median_risk24=a["median_initial_risk"],median_risk25=c["median_initial_risk"],max_risk24=a["max_initial_risk"],max_risk25=c["max_initial_risk"],failure_exits24=a["failure_exits"],failure_exits25=c["failure_exits"],max_size24=a["max_size"],max_size25=c["max_size"],mean_size24=a["mean_size"],mean_size25=c["mean_size"],partial24=a["partial_fills"],partial25=c["partial_fills"],retries24=a["diagnostics"]["retries"],retries25=c["diagnostics"]["retries"])
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
