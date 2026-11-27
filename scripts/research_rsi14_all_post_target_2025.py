"""Apply two predefined post-TP policies to every distinct earlier bracket configuration."""
import csv,gzip,hashlib,json,math
from itertools import product
from pathlib import Path
import numpy as np
from numba import njit
from research_rsi14_simple_robustness_2025 import load,entry_list,PLAN,sensitivity
from research_rsi14_improvements_2025 import (
    ROOT,START,END,FEE,dt,export_bundle,replay,verify,candidates,ENTRIES,BRACKETS,PROTECTIONS,
)

OUT=Path("scratch/rsi14_all_post_target")
@njit
def execute(O,H,L,C,i,d,risk,tp,be,mid,mode):
    ep=O[i];stop=ep-d*risk;activation=ep+d*tp;extended=activation+d*risk
    armed=False;protected=False;best=ep;armed_at=-1
    lock=(ep*(d+FEE))/(d-FEE)
    lock=math.ceil(lock*2)/2 if d==1 else math.floor(lock*2)/2
    for j in range(i,len(O)):
        o,h,l,c=O[j],H[j],L[j],C[j]
        if d*(o-stop)<=0:
            return j,o,2 if armed else (5 if protected else 1),stop,armed_at
        if j==mid:
            return j,o,6,stop,armed_at
        if not armed and d*(o-activation)>=0:
            armed=True;armed_at=j;best=o
            stop=activation-d*risk if d*(activation-d*risk-stop)>0 else stop
        if armed:
            if mode==1 and d*(o-extended)>=0:
                return j,extended,3,stop,armed_at
            if mode==2:
                if d*(o-best)>0:best=o
                if d*(best-d*risk-stop)>0:stop=best-d*risk
        elif be>0 and not protected and d*(o-ep)>=be:
            if d*(lock-stop)>0:stop=lock
            protected=True
        if c>o or (c==o and o-l<=h-o):seq=(o,l,h,c)
        else:seq=(o,h,l,c)
        for k in range(3):
            a,b=seq[k],seq[k+1]
            if d*(b-a)<0:
                if d*(a-stop)>=0 and d*(b-stop)<=0:
                    return j,stop,2 if armed else (5 if protected else 1),stop,armed_at
            elif d*(b-a)>0:
                if not armed and d*(b-activation)>=0:
                    armed=True;armed_at=j;best=activation
                    # Preserve any already-active fee stop even if the new
                    # post-target initial lock would be less protective.
                    if be>0 and not protected and be<=tp:
                        if d*(lock-stop)>0:stop=lock
                        protected=True
                    if d*(activation-d*risk-stop)>0:stop=activation-d*risk
                if armed:
                    if mode==1 and d*(b-extended)>=0:return j,extended,3,stop,armed_at
                    if mode==2 and d*(b-best)>0:
                        best=b
                        if d*(best-d*risk-stop)>0:stop=best-d*risk
                elif be>0 and not protected and d*(b-ep)>=be:
                    if d*(lock-stop)>0:stop=lock
                    protected=True
    return len(O)-1,C[-1],4,stop,armed_at
REASONS={1:"Initial stop loss",2:"Post-target profit stop",3:"Extended take profit",4:"End of 2025 evaluation",5:"Fee protection stop",6:"RSI midpoint exit"}
def check():
    verify()
    a=np.array([10000.]);l=np.array([9900.])
    r=execute(a,np.array([14000.]),l,np.array([12000.]),0,1,1000,3000,0,-1,1)
    assert r[1]==14000 and r[2]==3
    r=execute(a,np.array([13500.]),l,np.array([12000.]),0,1,1000,3000,0,-1,2)
    assert r[1]==12500 and r[2]==2
    r=execute(a,np.array([10050.]),np.array([6500.]),np.array([8000.]),0,-1,1000,3000,0,-1,2)
    assert r[1]==7500 and r[2]==2
    r=execute(a,np.array([10800.]),np.array([9800.]),np.array([9990.]),0,1,1000,3000,500,-1,2)
    assert r[2]==5 and r[1]>10000
    r=execute(a,np.array([13500.]),np.array([8900.]),np.array([13000.]),0,1,1000,3000,0,-1,2)
    assert r[1]==9000 and r[2]==1
    r=execute(a,np.array([10200.]),np.array([9900.]),np.array([10100.]),0,1,1000,3000,0,0,2)
    assert r[2]==6
def plan():
    p=set((entry,trend,kind,sl,tp,be,mid) for entry,trend,(kind,sl,tp),be,mid in product(ENTRIES,(False,True),BRACKETS,PROTECTIONS,(False,True)))
    p.update(("direct",False,"fixed",sl,tp,0,False) for sl,tp in product((100,200,300,500,1000),(200,500,600,1000,2000)))
    p.update((entry,False,kind,sl,tp,be,False) for entry,kind,sl,tp,be,_ in PLAN)
    assert len(p)==1627,len(p)
    return sorted(p)
def midpoint(bars):
    # Reproduce exact original 15m RSI midpoint crosses from the same
    # completed candle series, not rounded snapshots.
    from research_rsi14_80_20_2025 import TF,INSTRUMENT,Candle,IndicatorBook,spec,candles
    book=IndicatorBook((spec("rsi",TF,period=14),),history_limit=2)
    group=[];prev=None;out={1:[],-1:[]}
    for t,o,h,l,c,v in candles():
        group.append((o,h,l,c,v))
        if len(group)==15:
            end=t+60
            ca=Candle(INSTRUMENT,TF,dt(end-900),dt(end),group[0][0],max(x[1] for x in group),min(x[2] for x in group),group[-1][3],sum(x[4] for x in group))
            book.update(ca);group.clear()
            r=book.get("rsi",TF,{"period":14})[-1]
            if prev is not None and r is not None and end<END:
                if prev>=50>r:out[1].append((end-START)//60)
                if prev<=50<r:out[-1].append((end-START)//60)
            prev=r
    return {k:np.array(v,dtype=np.int64) for k,v in out.items()}
def summary(trades):
    p=[t["net_points"] for t in trades];gain=math.fsum(max(0,n) for n in p);loss=-math.fsum(min(0,n) for n in p)
    monthly={f"2025-{m:02d}":0. for m in range(1,13)}
    eq=peak=dd=0.
    for t,n in zip(trades,p):
        monthly[t["entry_utc"][:7]]+=n
        eq+=n;peak=max(peak,eq);dd=max(dd,peak-eq)
    wins=sum(n>0 for n in p)
    return dict(accounting="realized",open_position=None,trades=len(p),net=math.fsum(p),wins=wins,
        win_rate=100*wins/len(p) if p else 0,profit_factor=gain/loss if loss else None,
        realized_drawdown_points=dd,monthly_entry_attribution=monthly,profitable_months=sum(n>0 for n in monthly.values()),
        target_activations=sum(t.get("signal_context",{}).get("activation_utc") is not None for t in trades),
        stress_extra_50_points_roundtrip=sensitivity(trades,50))
def variant(bars,entries,mid,config,policy,baseline):
    entry,trend,kind,sl,tp,be,rsi_exit=config
    if policy=="fixed":
        v=replay(bars,entries,mid,entry,trend,kind,sl,tp,be,rsi_exit)
        for t in v["trades"]:
            if t["exit_reason"]=="Take profit":t["signal_context"]["activation_utc"]=t["exit_utc"]
        v["summary"]=summary(v["trades"])
    else:
        O,H,L,C=bars;trades=[];free=0
        for i,d,r,trigger,atr,ema in entries:
            if i<free or (kind=="atr" and (atr is None or atr<=0)):continue
            ep=float(O[i])
            risk=float(sl if kind=="fixed" else max(.5,math.ceil(sl*atr*2)/2))
            target=float(tp if kind=="fixed" else max(.5,math.ceil(tp*atr*2)/2))
            m=-1
            if rsi_exit:
                ix=np.searchsorted(mid[d],i,side="right")
                if ix<len(mid[d]):m=int(mid[d][ix])
            j,xp,reason,stop,activated=execute(O,H,L,C,i,d,risk,target,be,m,1 if policy=="extend-1r" else 2)
            free=j+1;gross=d*(xp-ep);fee=(ep+xp)*FEE
            vals={"indicator_0":r}
            if atr is not None:vals["indicator_1"]=atr
            if ema is not None:vals["indicator_2"]=ema
            trades.append(dict(entry_utc=dt(START+i*60).isoformat(),trigger_utc=dt(START+trigger*60).isoformat(),
                exit_utc=dt(END if reason==4 else START+j*60).isoformat(),side=d,entry_price=ep,exit_price=float(xp),
                stop_price=ep-d*risk,target_price=ep+d*target,final_stop_price=float(stop),
                gross_points=float(gross),fee_points=float(fee),net_points=float(gross-fee),
                assumed_slippage_points=0,entry_reason=entry,exit_reason=REASONS[reason],
                signal_context={"rsi14":r,"initial_risk_points":risk,"original_tp_points":target,
                    "activation_utc":dt(START+activated*60).isoformat() if activated>=0 else None,
                    "original_tp_is_activation_not_limit":True,"extended_tp_points":target+risk if policy=="extend-1r" else None},
                indicator_values=vals))
        v=dict(trades=trades,summary=summary(trades))
    key=f"{entry}-ema{int(trend)}-{kind}-{sl}-{tp}-be{be}-mid{int(rsi_exit)}"
    s=v["summary"]
    s["net_change_vs_fixed"]=s["net"]-baseline["net"] if baseline is not None else 0.
    s["month_change_vs_fixed"]=s["profitable_months"]-baseline["profitable_months"] if baseline is not None else 0
    v.update(key=key+"-"+policy,name=f"RSI14 {key} | {policy}",parameters=dict(entry=entry,trend_h1_ema50=trend,bracket=kind,
        stop_loss=sl,take_profit=tp,profit_protection_points=be,rsi_midpoint_exit=rsi_exit,
        post_target_exit=policy,post_target_risk_multiple=1 if policy!="fixed" else None,
        rsi_period=14,long_threshold=80,short_threshold=20))
    return v

def run():
    check();configs=plan()
    bars,signals,snapshots,extra,rec=load();mid=midpoint(bars)
    entries={}
    for entry,trend,*_ in configs:
        if (entry,trend) not in entries:
            entries[(entry,trend)]=entry_list(bars,signals,snapshots,extra,entry) if entry in ("ema-reclaim","supertrend") else candidates(bars,signals,snapshots,entry,trend)
    OUT.mkdir(parents=True,exist_ok=True)
    rows=[];chosen={};top={};refs={};unique={}
    counts={k:dict(total=0,positive=0,improved=0,months_improved=0,both=0) for k in ("fixed","extend-1r","trail-1r")}
    with gzip.open(OUT/"all_ledgers.jsonl.gz","wt") as f:
        for cfg in configs:
            e=entries[cfg[:2]];baseline=None
            for policy in counts:
                v=variant(bars,e,mid,cfg,policy,baseline)
                s=v["summary"]
                if policy=="fixed":baseline=s
                f.write(json.dumps(v,allow_nan=False,separators=(",",":"))+"\n")
                p=v["parameters"];row=dict(key=v["key"],**p,**{k:x for k,x in s.items() if k not in ("monthly_entry_attribution","stress_extra_50_points_roundtrip","open_position")},**s["monthly_entry_attribution"],
                    stress50_net=s["stress_extra_50_points_roundtrip"]["net"],stress50_months=s["stress_extra_50_points_roundtrip"]["months"])
                rows.append(row);c=counts[policy];c["total"]+=1;c["positive"]+=s["net"]>0;c["improved"]+=s["net_change_vs_fixed"]>1e-7;c["months_improved"]+=s["month_change_vs_fixed"]>0;c["both"]+=s["net_change_vs_fixed"]>1e-7 and s["month_change_vs_fixed"]>0
                # Rank all outcomes but keep only leading ledgers in memory.
                # Deduplicate identical summary outcomes to avoid redundant EMA variants.
                ident=(policy,round(s["net"],6),s["trades"],s["profitable_months"],round(s["realized_drawdown_points"],6))
                if ident not in unique:
                    unique[ident]=True
                    for label,score in (("net",(s["net"],)),("month",(s["profitable_months"],s["net"])),("dd",(-s["realized_drawdown_points"],s["net"]))):
                        if label=="dd" and s["net"]<=0:continue
                        group=top.setdefault((policy,label),[])
                        group.append((score,v["key"],v))
                        group.sort(key=lambda a:(a[0],a[1]),reverse=True)
                        del group[3:]
                if cfg in (("pullback",False,"fixed",750,3000,0,False),("pullback-breakout",False,"fixed",1000,3000,0,False)):
                    refs[v["key"]]=v
    assert len(rows)==4881
    assert math.isclose(refs["pullback-breakout-ema0-fixed-1000-3000-be0-mid0-trail-1r"]["summary"]["net"],38547.273445,abs_tol=1e-5)
    with (OUT/"all_results.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    chosen.update(refs)
    for group in top.values():
        for _,key,v in group[:2]:chosen[key]=v
    # Also publish matched original baseline for each leading extension.
    matched={v["key"].rsplit("-",2)[0]+"-fixed" for v in chosen.values() if v["parameters"]["post_target_exit"]!="fixed"}
    with gzip.open(OUT/"all_ledgers.jsonl.gz","rt") as f:
        for line in f:
            v=json.loads(line)
            if v["key"] in matched:chosen[v["key"]]=v
    export_bundle(OUT/"backtest.json",family="rsi14-all-post-target-2025",symbol="BTCUSD",unit="price points",
        start_utc=dt(START).isoformat(),end_utc=dt(END).isoformat(),execution_timeframe_minutes=1,signal_timeframe_minutes=15,
        costs="0.05% taker each side +18% GST; zero additional slippage; funding and liquidation excluded; 50 point/trade accounting stress only; Color execution; adverse gap at open.",
        variants=list(chosen.values()),recorder=rec,data_provenance=dict(manifest=str(ROOT/"manifest.json"),manifest_sha256=hashlib.sha256((ROOT/"manifest.json").read_bytes()).hexdigest(),
            input_minutes=len(bars[0]),timestamp_label="assumed open UTC",selection="1627 distinct earlier bracket configs x 3 policies; no new parameter search; 2025 in-sample only",
            full_archive="rsi14-all-post-target-full",total_variants=len(rows),published_variants=len(chosen),
            note="RSI midpoint exit stays active after TP; pre-target fee stop never loosened; target activation is not resting limit."))
    print("COUNTS",json.dumps(counts),"PUBLISHED",len(chosen))
    for (policy,label),group in top.items():
        for _,key,v in group:
            print("TOP",json.dumps(dict(rank=label,key=key,**v["parameters"],**v["summary"]),separators=(",",":"),allow_nan=False))
    for v in refs.values():print("REF",json.dumps(dict(key=v["key"],**v["summary"]),separators=(",",":"),allow_nan=False))
if __name__=="__main__":run()
