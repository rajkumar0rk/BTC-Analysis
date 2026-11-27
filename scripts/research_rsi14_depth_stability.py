"""Predeclared coarse cross-year robustness study; 2026 candles never opened."""
import csv,gzip,json,math,hashlib
from itertools import product
from pathlib import Path
from datetime import datetime,timezone
import numpy as np
from numba import njit
import research_rsi14_original_2024_gapfree as y24
import research_rsi14_simple_robustness_2025 as y25
import research_rsi14_entry_quality_2025 as q
import research_rsi14_consistency_risk_2025 as r
from research_rsi14_80_20_2025 import candles as candles25,FEE,dt
from research_rsi14_runner_refinements_2025 import checks
OUT=Path("scratch/rsi14_depth_stability")
ENTRIES={"original":(r.BASES["original"][0],False),"current":(r.BASES["high-profit"][0],True)}
# Protection is fee-inclusive break-even after 0.5R or 1R, optionally
# followed by +1R lock after +2R. Initial SL and trail stay fixed.
DEPTHS=(0.,.125,.25,.375,.5)
BE=(0,500,750,1000,1250,1500)
PROTECT=tuple((x,False) for x in BE)
# Keep only the original entry and one exit mechanism. EMA50 is an ablation.
PLAN=list(product(("original",),(False,True),DEPTHS,PROTECT,(2000.,3000.)))
@njit
def tighten(stop,best,ep,d,be,progressive,lock):
    if be>0 and d*(best-ep)>=be and d*(lock-stop)>0:stop=lock
    if progressive and d*(best-ep)>=2000 and d*(ep+d*1000-stop)>0:stop=ep+d*1000
    return stop
@njit
def trade(O,H,L,C,i,d,activation,be,progressive):
    ep=O[i];stop=ep-d*1000;act=ep+d*activation;best=ep;armed=-1
    lock=ep*(d+FEE)/(d-FEE)
    lock=math.ceil(lock*2)/2 if d==1 else math.floor(lock*2)/2
    distance=1000.
    mfe=mae=0.
    for j in range(i,len(O)):
        o,h,l,c=O[j],H[j],L[j],C[j]
        if d*(o-stop)<=0:
            mae=max(mae,-d*(o-ep));return j,o,2 if armed>=0 else 3 if d*(stop-ep)>=0 else 1,stop,armed,mfe,mae
        mfe=max(mfe,d*(o-ep));mae=max(mae,-d*(o-ep))
        if d*(o-best)>0:best=o
        stop=tighten(stop,best,ep,d,be,progressive,lock)
        if armed<0 and d*(o-act)>=0:armed=j
        if armed>=0 and d*(best-d*distance-stop)>0:stop=best-d*distance
        seq=(o,l,h,c) if c>o or (c==o and o-l<=h-o) else (o,h,l,c)
        for k in range(3):
            a,b=seq[k],seq[k+1]
            if d*(b-a)<0:
                if d*(a-stop)>=0 and d*(b-stop)<=0:
                    mae=max(mae,-d*(stop-ep))
                    return j,stop,2 if armed>=0 else 3 if d*(stop-ep)>=0 else 1,stop,armed,mfe,mae
                mae=max(mae,-d*(b-ep))
            elif d*(b-a)>0:
                mfe=max(mfe,d*(b-ep))
                if d*(b-best)>0:best=b
                stop=tighten(stop,best,ep,d,be,progressive,lock)
                if armed<0 and d*(b-act)>=0:armed=j
                if armed>=0 and d*(best-d*distance-stop)>0:stop=best-d*distance
    return len(O)-1,C[-1],4,stop,armed,mfe,mae

def replay(bars,ind,setups,start,end,plan,snapshots):
    entry,trend,min_depth,(be,progressive),activation=plan;old,dist=ENTRIES[entry]
    O,H,L,C=bars;atr=ind[-1];out=[];free=0
    def allowed(i,d,depth,level):
        ema=snapshots[(i//15)*15][1]
        return q.eligible(bars,ind,i,d,depth,old) and (not dist or 0<d*(C[i-1]-level)<=250) and (not min_depth or depth>=min_depth) and (not trend or (ema is not None and d*(C[i-1]-ema)>0))
    for first,d,rsi,trigger,level,pull,depth,until,retries in setups:
        if first<free or not allowed(first,d,depth,level):continue
        i=first
        for attempt in range(2 if old[-1] else 1):
            ep=float(O[i]);at=float(atr[i//15])
            risk=1000.
            j,xp,reason,stop,armed,mfe,mae=trade(O,H,L,C,i,d,activation,be,progressive)
            free=j+1;gross=d*(xp-ep);fee=(ep+xp)*FEE
            vals={"indicator_0":rsi}
            if math.isfinite(at):vals["indicator_1"]=at
            out.append(dict(entry_utc=dt(start+i*60).isoformat(),trigger_utc=dt(start+trigger*60).isoformat(),exit_utc=dt(end if reason==4 else start+j*60).isoformat(),side=d,entry_price=ep,exit_price=float(xp),stop_price=ep-d*risk,target_price=ep+d*activation,final_stop_price=float(stop),gross_points=float(gross),fee_points=float(fee),net_points=float(gross-fee),assumed_slippage_points=0,entry_reason="pullback-breakout",exit_reason={1:"Initial SL",2:"Trailing SL",3:"Profit protection",4:"Evaluation end"}[reason],signal_context=dict(rsi14=rsi,risk_points=risk,entry_atr=at,breakout_level=level,retry=bool(attempt),mfe=float(mfe),mae=float(mae),activation_utc=dt(start+armed*60).isoformat() if armed>=0 else None),indicator_values=vals))
            if attempt or not old[-1] or reason!=1 or free>=until:break
            nxt=next((int(k) for k in retries if k>=free and allowed(int(k),d,depth,level)),-1)
            if nxt<0:break
            i=nxt
    return out

def summarize(trades,year,cost=0):
    tz=y24.IST if year==2024 else timezone.utc
    months={f"{year}-{m:02d}":0. for m in range(3 if year==2024 else 1,13)}
    p=[];eq=peak=dd=0.
    for t in trades:
        n=t["net_points"]-cost;p.append(n);months[datetime.fromisoformat(t["entry_utc"]).astimezone(tz).strftime("%Y-%m")]+=n
        eq+=n;peak=max(peak,eq);dd=max(dd,peak-eq)
    gain=math.fsum(max(n,0) for n in p);loss=-math.fsum(min(n,0) for n in p)
    wins=sum(n>0 for n in p)
    return dict(accounting="realized",open_position=None,net=math.fsum(p),trades=len(p),wins=wins,win_rate=100*wins/len(p) if p else 0.,profit_factor=gain/loss if loss else None,realized_drawdown_points=dd,monthly_entry_attribution=months,profitable_months=sum(x>0 for x in months.values()),worst_month=min(months.values()),gross=math.fsum(t["gross_points"] for t in trades),fees=math.fsum(t["fee_points"] for t in trades),mean_win=gain/wins if wins else 0.,mean_loss=loss/(len(p)-wins) if len(p)>wins else 0.,mfe_reach={str(x):sum(t["signal_context"]["mfe"]>=x for t in trades) for x in (500,1000,2000,3000)},median_sl_atr=float(np.median([t["signal_context"]["risk_points"]/t["signal_context"]["entry_atr"] for t in trades])) if trades else None,long_net=math.fsum(n for n,t in zip(p,trades) if t["side"]==1),short_net=math.fsum(n for n,t in zip(p,trades) if t["side"]==-1))
def key(p):
    en,trend,depth,(be,prog),act=p
    return f"{en}-ema{int(trend)}-depth{depth:g}-be{be}-progressive{int(prog)}-act{act:g}"
def run():
    checks();OUT.mkdir(parents=True,exist_ok=True)
    results={key(p):{"plan":p,"years":{}} for p in PLAN}
    refs={"original":{2024:-7143.8888,2025:38547.273445},"current":{2024:-1493.54274,2025:42597.871415}}
    for year in (2024,2025):
        if year==2024:
            q.candles=y24.candles;bars,signals,snapshots,extra,rec=y24.load();start,end=y24.START,y24.END
        else:
            q.candles=candles25;bars,signals,snapshots,extra,rec=y25.load();start,end=y25.START,y25.END
        ind=q.indicators(bars,snapshots);setups=q.setup_rows(bars,signals,snapshots,extra)
        for p in PLAN:
            ts=replay(bars,ind,setups,start,end,p,snapshots);s=summarize(ts,year);st=summarize(ts,year,50)
            s["stress"]=dict(net=st["net"],months=st["profitable_months"],pf=st["profit_factor"],dd=st["realized_drawdown_points"])
            if p[0] in refs and p[1:]==(False,0.,(0,False),3000.):
                assert math.isclose(s["net"],refs[p[0]][year],abs_tol=1e-5),(p,year,s["net"])
                print("REFERENCE",json.dumps(dict(year=year,key=key(p),**s),allow_nan=False))
            if p==("original",False,.25,(1000,False),3000.):
                assert math.isclose(s["net"],{2024:3786.537795,2025:15108.251455}[year],abs_tol=1e-5)
            results[key(p)]["years"][year]=dict(summary=s,trades=ts)
        del bars,ind,setups,snapshots,extra,rec
    rows=[]
    for k,v in results.items():
        a,b=[v["years"][y]["summary"] for y in (2024,2025)]
        en,trend,depth,(be,prog),act=v["plan"]
        pass_stress=all(z["stress"]["net"]>0 and z["trades"]>=30 for z in (a,b))
        # Require adjacent values on both axes, not just one lucky threshold.
        def passes(p):
            other=results[key(p)]["years"]
            return all(other[y]["summary"]["stress"]["net"]>0 and other[y]["summary"]["trades"]>=30 for y in (2024,2025))
        dn=[(en,trend,x,(be,prog),act) for i,x in enumerate(DEPTHS) if abs(i-DEPTHS.index(depth))==1]
        bn=[(en,trend,depth,(x,prog),act) for i,x in enumerate(BE) if abs(i-BE.index(be))==1]
        depth_pass=sum(passes(p) for p in dn)
        be_pass=sum(passes(p) for p in bn)
        n_pass=depth_pass+be_pass
        # All four chronological half-year blocks, without monthly reset.
        blocks=[]
        for year,z in ((2024,a),(2025,b)):
            for half in (0,1):
                blocks.append(sum(x for m,x in z["monthly_entry_attribution"].items() if (int(m[-2:])>6)==bool(half)))
        row=dict(key=k,entry=en,ema50=trend,depth=depth,protection=be,progressive=prog,activation=act,net24=a["net"],net25=b["net"],months24=a["profitable_months"],months25=b["profitable_months"],pf24=a["profit_factor"],pf25=b["profit_factor"],dd24=a["realized_drawdown_points"],dd25=b["realized_drawdown_points"],trades24=a["trades"],trades25=b["trades"],stress24=a["stress"]["net"],stress25=b["stress"]["net"],stress_months24=a["stress"]["months"],stress_months25=b["stress"]["months"],net=a["net"]+b["net"],months=a["profitable_months"]+b["profitable_months"],stress_months=a["stress"]["months"]+b["stress"]["months"],dd=max(a["realized_drawdown_points"],b["realized_drawdown_points"]),positive_blocks=sum(x>0 for x in blocks),blocks=blocks,pass_stress=pass_stress,neighbor_pass=n_pass,depth_neighbor_pass=depth_pass,protection_neighbor_pass=be_pass,accepted=pass_stress and depth_pass>0 and be_pass>0 and all(x>0 for x in blocks))
        rows.append(row)
    rows.sort(key=lambda z:(z["accepted"],z["pass_stress"],z["neighbor_pass"],z["positive_blocks"],min(z["stress_months24"]/10,z["stress_months25"]/12),z["stress_months"],z["months"],-z["dd"]),reverse=True)
    with (OUT/"results.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    with gzip.open(OUT/"all_results.json.gz","wt") as f:json.dump(results,f,allow_nan=False,separators=(",",":"))
    print("COUNTS",json.dumps(dict(total=len(rows),both_year_positive=sum(z["net24"]>0 and z["net25"]>0 for z in rows),stress_pass=sum(z["pass_stress"] for z in rows),stress_neighbor_pass=sum(z["pass_stress"] and z["depth_neighbor_pass"]>0 and z["protection_neighbor_pass"]>0 for z in rows),accepted=sum(z["accepted"] for z in rows),max_months=max(z["months"] for z in rows))))
    for v in rows[:10]:print("TOP",json.dumps(v,allow_nan=False))
    for v in sorted(rows,key=lambda z:(z["months"],z["net"]),reverse=True)[:3]:print("MONTH",json.dumps(v,allow_nan=False))
    for v in rows[:3]:
        print("DETAIL",json.dumps(dict(key=v["key"],years={y:results[v["key"]]["years"][y]["summary"] for y in (2024,2025)}),allow_nan=False))
    for v in rows:
        if not v["ema50"] and v["activation"]==3000:print("GRID",json.dumps(v,allow_nan=False))
if __name__=="__main__":run()
