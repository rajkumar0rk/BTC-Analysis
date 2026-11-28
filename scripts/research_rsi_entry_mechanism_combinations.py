"""All 32 additive entry combinations; identical frozen RSI Chandelier exit; no 2026 data."""
import csv,gzip,json,math
from itertools import product
from pathlib import Path
from datetime import datetime,timezone
import numpy as np
import research_rsi14_entry_exit_diagnostics as r
from research_rsi14_consistency_risk_2025 import retest
from research_rsi14_depth_stability import y24,y25,q,candles25,checks,summarize,FEE,dt
OUT=Path("scratch/rsi_entry_mechanism_combinations")
RULES=("rsi-recross","ema-reclaim","swing-breakout","second-breakout","trend-reentry")
PLAN=list(product((False,True),repeat=5))
REF={2024:9644.735195,2025:12787.68496}
def key(f):return "+".join(k for k,v in zip(RULES,f) if v) or "baseline"

def build(bars,ind,signals,snapshots,extra):
    O,H,L,C=bars;rs=ind[2]
    h=H.reshape(-1,15).max(axis=1);l=L.reshape(-1,15).min(axis=1);c=C[14::15]
    setup=q.setup_rows(bars,signals,snapshots,extra)
    lookup={s[3]:s for s in setup}
    def eligible(i,d):
        e=snapshots[(i//15)*15][1]
        return e is not None and d*(C[i-1]-e)>0
    def valid(trigger,i,d):return not np.any(d*(rs[trigger//15:i//15+1]-50)<=0)
    cycles=[]
    for index,(trigger,d,rv,hi,lo) in enumerate(signals):
        until=signals[index+1][0] if index+1<len(signals) else len(O)
        old=lookup.get(trigger);base=None
        if old is not None:
            first,_,_,_,level,pull,depth,_,retries=old
            if depth>=.25 and eligible(first,d):
                i=retest(bars,first,d,level,until)
                if i>=first and i<until and eligible(i,d) and valid(trigger,i,d):base=(i,first)
        # Alternative initial triggers use all original threshold cycles, even
        # those without an original pullback-breakout. Depth is measured only
        # from completed subsequent 15m candles.
        events=[];continuation=[];extreme=hi if d==1 else lo;pivot=None
        intact=d*(rs[trigger//15]-50)>0
        for i in range(trigger+15,until,15):
            if i>=len(O):break
            k=i//15-1
            extreme=min(extreme,l[k]) if d==1 else max(extreme,h[k])
            depth=(hi-extreme if d==1 else extreme-lo)/(hi-lo) if hi>lo else 0.
            intact=intact and d*(rs[k+1]-50)>0
            # Pivot with two bars either side; confirmed before current bar.
            p=k-3
            if p-2>=trigger//15 and p+2<k:
                if d==1 and h[p]>max(h[p-2:p]) and h[p]>max(h[p+1:p+3]):pivot=float(h[p])
                if d==-1 and l[p]<min(l[p-2:p]) and l[p]<min(l[p+1:p+3]):pivot=float(l[p])
            if depth<.25 or not eligible(i,d):continue
            if d*(rs[k]-50)<=0 and d*(rs[k+1]-50)>0:events.append((i,0))
            # Existing midpoint invalidation retained for non-RSI alternatives.
            if not intact:continue
            e=extra[i-15][0] if i-15 in extra else None
            if e is not None and ((d==1 and l[k]<=e<c[k]) or (d==-1 and h[k]>=e>c[k])):events.append((i,1))
            if pivot is not None and d*(c[k-1]-pivot)<=0 and d*(c[k]-pivot)>0:events.append((i,2))
            # New directional breakout after a completed adverse close.
            if k>=2 and d*(c[k-1]-c[k-2])<0 and d*(c[k]-(h[k-1] if d==1 else l[k-1]))>0:
                continuation.append((i,(k-1)*15))
        cycles.append((trigger,d,rv,until,old,base,events,continuation))
    return cycles

def replay(bars,ind,cycles,start,end,flags,ST,LINE,snapshots):
    O,H,L,C=bars;atr=ind[-1];rs=ind[2];out=[];free=0
    def eligible(i,d):
        e=snapshots[(i//15)*15][1]
        return e is not None and d*(C[i-1]-e)>0
    def valid(t,i,d):return not np.any(d*(rs[t//15:i//15+1]-50)<=0)
    def enter(i,d,trigger,source):
        ep=float(O[i]);at=float(atr[i//15])
        j,xp,reason,stop,armed,mfe,mae,_,_=r.reference_execute(O,H,L,C,atr,ST,LINE,i,d,750.,3.,0,0)
        gross=d*(xp-ep);fee=(ep+xp)*FEE
        out.append(dict(entry_utc=dt(start+i*60).isoformat(),trigger_utc=dt(start+trigger*60).isoformat(),exit_utc=dt(end if reason==4 else start+j*60).isoformat(),side=d,entry_price=ep,exit_price=float(xp),gross_points=float(gross),fee_points=float(fee),net_points=float(gross-fee),exit_reason={1:"Initial SL",2:"Trailing SL",3:"Profit protection",4:"Evaluation end"}[reason],signal_context=dict(risk_points=1000.,entry_atr=at,mfe=float(mfe),mae=float(mae),entry_source=source)))
        return j+1,reason,gross-fee
    for trigger,d,rv,until,old,base,events,continuation in cycles:
        if free>=until:continue
        options=[]
        if base and base[1]>=free:options.append((base[0],-1))
        options.extend((i,idx) for i,idx in events if flags[idx] and i>=free)
        if not options:continue
        i,idx=min(options)
        free,reason,net=enter(i,d,trigger,"original" if idx<0 else RULES[idx])
        if free>=until:continue
        # At most one extra entry per cycle; never simultaneously open two positions.
        if flags[3] and reason==1 and old is not None:
            first,_,_,_,level,pull,depth,_,retries=old
            if depth>=.25:
                for raw in retries:
                    raw=int(raw)
                    if raw<=free or not eligible(raw,d) or not valid(trigger,raw,d):continue
                    cand=retest(bars,raw,d,level,until)
                    if cand>=free and cand<until and eligible(cand,d) and valid(trigger,cand,d):
                        free,_,_=enter(cand,d,trigger,"second-breakout");break
        elif flags[4] and reason==2 and net>0:
            # A meaningful profitable trailing exit, then a new completed
            # pullback and breakout wholly after the exit.
            for cand,pull_start in continuation:
                if pull_start>=free and cand<until and valid(trigger,cand,d):
                    free,_,_=enter(cand,d,trigger,"trend-reentry");break
    return out

def run():
    checks();OUT.mkdir(parents=True,exist_ok=True)
    results={key(f):dict(flags=f,years={}) for f in PLAN}
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
        cycles=build(bars,ind,signals,snapshots,extra)
        for f in PLAN:
            ts=replay(bars,ind,cycles,start,end,f,ST,LINE,snapshots)
            s=summarize(ts,year);st=summarize(ts,year,50)
            if not any(f):
                assert math.isclose(s["net"],REF[year],abs_tol=1e-5),(year,s["net"])
                assert len(ts)=={2024:44,2025:47}[year]
                old=r.replay(bars,ind,q.setup_rows(bars,signals,snapshots,extra),start,end,"80-chandelier","baseline",snapshots,extra,avg,ST,LINE,None,None)
                assert [(t["entry_utc"],t["exit_utc"],t["net_points"]) for t in ts]==[(t["entry_utc"],t["exit_utc"],t["net_points"]) for t in old]
            s["stress_net"]=st["net"];s["stress_months"]=st["profitable_months"]
            s["source_counts"]={name:sum(t["signal_context"]["entry_source"]==name for t in ts) for name in ("original",)+RULES}
            tz=y24.IST if year==2024 else timezone.utc
            s["no_trade_months"]=len(set(s["monthly_entry_attribution"])-{datetime.fromisoformat(t["entry_utc"]).astimezone(tz).strftime("%Y-%m") for t in ts})
            s["months_gt_1000"]=sum(p>1000 for p in s["monthly_entry_attribution"].values())
            results[key(f)]["years"][year]=dict(summary=s,trades=ts)
        del bars,ind,snapshots,extra,rec,cycles
    rows=[]
    for k,v in results.items():
        a,c=[v["years"][y]["summary"] for y in (2024,2025)]
        blocks=[sum(p for mo,p in s["monthly_entry_attribution"].items() if (int(mo[-2:])>6)==bool(h)) for s in (a,c) for h in (0,1)]
        row=dict(key=k,net24=a["net"],net25=c["net"],net=a["net"]+c["net"],months24=a["profitable_months"],months25=c["profitable_months"],months=a["profitable_months"]+c["profitable_months"],trades24=a["trades"],trades25=c["trades"],pf24=a["profit_factor"],pf25=c["profit_factor"],dd=max(a["realized_drawdown_points"],c["realized_drawdown_points"]),dd24=a["realized_drawdown_points"],dd25=c["realized_drawdown_points"],stress24=a["stress_net"],stress25=c["stress_net"],stress_months=a["stress_months"]+c["stress_months"],zero_months=a["no_trade_months"]+c["no_trade_months"],positive_blocks=sum(p>0 for p in blocks),worst_month=min(a["worst_month"],c["worst_month"]),months_gt_1000=a["months_gt_1000"]+c["months_gt_1000"],sources={n:a["source_counts"][n]+c["source_counts"][n] for n in ("original",)+RULES})
        row["robust"]=all(s["stress_net"]>0 and s["trades"]>=30 for s in (a,c)) and row["positive_blocks"]==4
        row["improved"]=row["robust"] and row["months"]>17 and row["stress_months"]>=12 and row["dd"]<6804.08 and row["trades24"]+row["trades25"]>91
        rows.append(row);print("RESULT",json.dumps(row,allow_nan=False))
    with (OUT/"results.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    with gzip.open(OUT/"all_results.json.gz","wt") as f:json.dump(results,f,allow_nan=False,separators=(",",":"))
    print("COUNTS",json.dumps(dict(total=len(rows),both_year_positive=sum(x["net24"]>0 and x["net25"]>0 for x in rows),robust=sum(x["robust"] for x in rows),improved=sum(x["improved"] for x in rows),max_months=max(x["months"] for x in rows))))
if __name__=="__main__":run()
