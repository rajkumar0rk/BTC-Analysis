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
OUT=Path("scratch/rsi14_two_year")
ENTRIES={"original":(r.BASES["original"][0],False),"adx-only":(r.BASES["adx-only"][0],False),"current":(r.BASES["high-profit"][0],True)}
RISKS={"fixed":(500.,1000.,1500.),"percent":(.005,.01,.015),"atr":(2.,3.,4.)}
PLAN=list(product(ENTRIES,[(k,x) for k,vs in RISKS.items() for x in vs],(2.,3.),(.5,1.)))
@njit
def trade(O,H,L,C,i,d,risk,activation,trail):
    ep=O[i];stop=ep-d*risk;act=ep+d*activation*risk;best=ep;armed=-1
    distance=max(.5,math.ceil(trail*risk*2)/2)
    mfe=mae=0.
    for j in range(i,len(O)):
        o,h,l,c=O[j],H[j],L[j],C[j]
        if d*(o-stop)<=0:
            mae=max(mae,-d*(o-ep));return j,o,1 if armed<0 else 2,stop,armed,mfe,mae
        mfe=max(mfe,d*(o-ep));mae=max(mae,-d*(o-ep))
        if d*(o-best)>0:best=o
        if armed<0 and d*(o-act)>=0:armed=j
        if armed>=0 and d*(best-d*distance-stop)>0:stop=best-d*distance
        seq=(o,l,h,c) if c>o or (c==o and o-l<=h-o) else (o,h,l,c)
        for k in range(3):
            a,b=seq[k],seq[k+1]
            if d*(b-a)<0:
                if d*(a-stop)>=0 and d*(b-stop)<=0:
                    mae=max(mae,-d*(stop-ep))
                    return j,stop,1 if armed<0 else 2,stop,armed,mfe,mae
                mae=max(mae,-d*(b-ep))
            elif d*(b-a)>0:
                mfe=max(mfe,d*(b-ep))
                if d*(b-best)>0:best=b
                if armed<0 and d*(b-act)>=0:armed=j
                if armed>=0 and d*(best-d*distance-stop)>0:stop=best-d*distance
    return len(O)-1,C[-1],4,stop,armed,mfe,mae

def replay(bars,ind,setups,start,end,plan):
    entry,(mode,param),activation,trail=plan;old,dist=ENTRIES[entry]
    O,H,L,C=bars;atr=ind[-1];out=[];free=0
    def allowed(i,d,depth,level):
        return q.eligible(bars,ind,i,d,depth,old) and (not dist or 0<d*(C[i-1]-level)<=250)
    for first,d,rsi,trigger,level,pull,depth,until,retries in setups:
        if first<free or not allowed(first,d,depth,level):continue
        i=first
        for attempt in range(2 if old[-1] else 1):
            ep=float(O[i]);at=float(atr[i//15])
            raw=param if mode=="fixed" else ep*param if mode=="percent" else at*param
            if not math.isfinite(raw) or raw<=0:break
            risk=max(.5,math.ceil(raw*2)/2)
            j,xp,reason,stop,armed,mfe,mae=trade(O,H,L,C,i,d,risk,activation,trail)
            free=j+1;gross=d*(xp-ep);fee=(ep+xp)*FEE
            vals={"indicator_0":rsi}
            if math.isfinite(at):vals["indicator_1"]=at
            out.append(dict(entry_utc=dt(start+i*60).isoformat(),trigger_utc=dt(start+trigger*60).isoformat(),exit_utc=dt(end if reason==4 else start+j*60).isoformat(),side=d,entry_price=ep,exit_price=float(xp),stop_price=ep-d*risk,target_price=ep+d*activation*risk,final_stop_price=float(stop),gross_points=float(gross),fee_points=float(fee),net_points=float(gross-fee),assumed_slippage_points=0,entry_reason="pullback-breakout",exit_reason={1:"Initial SL",2:"Trailing SL",4:"Evaluation end"}[reason],signal_context=dict(rsi14=rsi,risk_points=risk,entry_atr=at,breakout_level=level,retry=bool(attempt),mfe=float(mfe),mae=float(mae),activation_utc=dt(start+armed*60).isoformat() if armed>=0 else None),indicator_values=vals))
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
    en,(mode,x),act,trail=p
    return f"{en}-{mode}{x:g}-activation{act:g}R-trail{trail:g}R"
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
            ts=replay(bars,ind,setups,start,end,p);s=summarize(ts,year);st=summarize(ts,year,50)
            s["stress"]=dict(net=st["net"],months=st["profitable_months"],pf=st["profit_factor"],dd=st["realized_drawdown_points"])
            if p[0] in refs and p[1]==("fixed",1000.) and p[2:]==(3.,1.):
                assert math.isclose(s["net"],refs[p[0]][year],abs_tol=1e-5),(p,year,s["net"])
                print("REFERENCE",json.dumps(dict(year=year,key=key(p),**s),allow_nan=False))
            results[key(p)]["years"][year]=dict(summary=s,trades=ts)
        del bars,ind,setups,snapshots,extra,rec
    rows=[]
    for k,v in results.items():
        a,b=[v["years"][y]["summary"] for y in (2024,2025)]
        en,(mode,x),act,trail=v["plan"]
        combined=a["net"]+b["net"];months=a["profitable_months"]+b["profitable_months"];dd=max(a["realized_drawdown_points"],b["realized_drawdown_points"])
        stress=a["stress"]["net"]+b["stress"]["net"];sm=a["stress"]["months"]+b["stress"]["months"]
        valid=all(z["stress"]["net"]>0 and z["trades"]>=30 for z in (a,b))
        # A neighboring risk setting must work in BOTH years without changing any other parameter.
        ns=[]
        for neighbor in RISKS[mode]:
            if neighbor==x:continue
            if abs(RISKS[mode].index(neighbor)-RISKS[mode].index(x))!=1:continue
            other=results[key((en,(mode,neighbor),act,trail))]["years"]
            ns.append(all(other[y]["summary"]["stress"]["net"]>0 for y in (2024,2025)))
        row=dict(key=k,entry=en,risk_mode=mode,risk_parameter=x,activation_r=act,trail_r=trail,
            net24=a["net"],net25=b["net"],months24=a["profitable_months"],months25=b["profitable_months"],pf24=a["profit_factor"],pf25=b["profit_factor"],dd24=a["realized_drawdown_points"],dd25=b["realized_drawdown_points"],trades24=a["trades"],trades25=b["trades"],stress24=a["stress"]["net"],stress25=b["stress"]["net"],stress_months24=a["stress"]["months"],stress_months25=b["stress"]["months"],net=combined,months=months,stress_net=stress,stress_months=sm,max_annual_dd=dd,worst_year=min(a["net"],b["net"]),worst_month=min(a["worst_month"],b["worst_month"]),both_year_stress_pass=valid,neighbor_pass=sum(ns),neighbor_count=len(ns))
        rows.append(row)
    # Prioritize profitability across BOTH years, a neighboring risk pass, stressed consistency, then drawdown.
    rows.sort(key=lambda a:(a["both_year_stress_pass"],a["neighbor_pass"]>0,min(a["stress_months24"]/10,a["stress_months25"]/12),a["stress_months"],a["months"],-a["max_annual_dd"],a["net"]),reverse=True)
    with (OUT/"results.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    with gzip.open(OUT/"all_results.json.gz","wt") as f:json.dump(results,f,allow_nan=False,separators=(",",":"))
    print("COUNTS",json.dumps(dict(total=len(rows),both_year_positive=sum(x["net24"]>0 and x["net25"]>0 for x in rows),stress_pass=sum(x["both_year_stress_pass"] for x in rows),stress_neighbor_pass=sum(x["both_year_stress_pass"] and x["neighbor_pass"]>0 for x in rows),max_months=max(x["months"] for x in rows))))
    for v in rows[:12]:
        print("TOP",json.dumps(v,allow_nan=False))
    # Record best raw monthly consistency and best simple baseline family separately.
    for v in sorted(rows,key=lambda a:(a["months"],a["net"]),reverse=True)[:3]:print("MONTH",json.dumps(v,allow_nan=False))
    for en in ENTRIES:
        v=next(x for x in rows if x["entry"]==en);print("FAMILY",json.dumps(v,allow_nan=False))
    for mode in RISKS:
        v=next(x for x in rows if x["risk_mode"]==mode);print("RISK",json.dumps(v,allow_nan=False))
    for v in rows[:3]:
        print("DETAIL",json.dumps(dict(key=v["key"],years={y:results[v["key"]]["years"][y]["summary"] for y in (2024,2025)}),allow_nan=False))
if __name__=="__main__":run()
