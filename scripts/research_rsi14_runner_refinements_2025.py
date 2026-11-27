"""Predefined factorial of seven runner refinements; 2025 in-sample only."""
import csv,gzip,hashlib,json,math
from itertools import product
from pathlib import Path
import numpy as np
from numba import njit
from research_rsi14_simple_robustness_2025 import load,sensitivity
from research_rsi14_improvements_2025 import ROOT,START,END,FEE,dt,export_bundle,verify,candidates

OUT=Path("scratch/rsi14_runner_refinements")
BASES=(("pullback-breakout",False,1000,3000,0),("pullback",True,1000,2000,1000))
TRAILS=("fixed-1r","atr-2","atr-3","supertrend")
EXPIRIES=(0,4,8)

def entry_list(bars,signals,snapshots,extra,entry,trend,expiry):
    O,H,L,C=bars
    out=[]
    for q,(i,d,r,hi,lo) in enumerate(signals):
        until=signals[q+1][0] if q+1<len(signals) else len(O)
        if expiry:until=min(until,i+expiry*15+1)
        j=-1
        for k in range(i+15,until,15):
            _,_,o,c=snapshots[k]
            if d*(c-o)<0:j=k;break
        if j<0:continue
        pull=j;level=hi if d==1 else lo
        if entry=="pullback-breakout":
            hits=np.flatnonzero(d*(C[j:until-1]-level)>0)
            if not len(hits):continue
            j+=int(hits[0])+1
        if j>=until or j>=len(O):continue
        at,ema,_,_=snapshots[(j//15)*15]
        if trend and (ema is None or d*(C[j-1]-ema)<=0):continue
        _,_,_,ph,pl,_=extra[pull]
        structure=pl-.5 if d==1 else ph+.5
        out.append((j,d,r,i,at,ema,structure,level,pull))
    return out

@njit
def ratchet(d,stop,new):
    return new if d*(new-stop)>0 else stop

@njit
def trail_stop(d,stop,best,risk,style,atr,st,stline):
    if style==0:new=best-d*risk
    elif style==1 or style==2:
        dist=(2 if style==1 else 3)*atr
        if not np.isfinite(dist) or dist<=0:return stop
        new=best-d*max(.5,math.ceil(dist*2)/2)
    else:
        if st!=d or not np.isfinite(stline):return stop
        # A confirmed ST line must be on the protective side of the best.
        if d*(best-stline)<=0:return stop
        new=math.floor(stline*2)/2 if d==1 else math.ceil(stline*2)/2
    return ratchet(d,stop,new)

@njit
def protection(d,stop,best,ep,risk,be,prog,lock):
    excursion=d*(best-ep)
    if (be>0 and excursion>=be) or (prog and excursion>=risk):
        # A fee stop cannot become a resting order beyond observed price.
        if d*(best-lock)>=0:stop=ratchet(d,stop,lock)
    if prog and excursion>=2*risk:stop=ratchet(d,stop,ep+d*risk)
    return stop

@njit
def execute(O,H,L,C,ATR,ST,STL,i,d,risk,tp,be,style,partial,prog,fail_at):
    ep=O[i];stop=ep-d*risk;act=ep+d*tp;best=ep
    lock=ep*(d+FEE)/(d-FEE)
    lock=math.ceil(lock*2)/2 if d==1 else math.floor(lock*2)/2
    activated=-1;part_price=0.;trail_active=False
    for j in range(i,len(O)):
        o,h,l,c=O[j],H[j],L[j],C[j]
        if d*(o-stop)<=0:return j,o,2 if activated>=0 else 1,stop,activated,part_price
        if j==fail_at:return j,o,3,stop,activated,part_price
        # Completed indicator values as of this minute's open only.
        ix=j//15;atr=ATR[ix];st=ST[ix];stline=STL[ix]
        if d*(o-best)>0:best=o
        stop=protection(d,stop,best,ep,risk,be,prog,lock)
        if activated<0 and d*(o-act)>=0:
            activated=j;part_price=act
            if style==3:stop=ratchet(d,stop,act-d*risk)
            elif prog:stop=ratchet(d,stop,act-d*risk)
        if activated>=0 and (not prog or d*(best-ep)>=3*risk):
            trail_active=True
        if trail_active:stop=trail_stop(d,stop,best,risk,style,atr,st,stline)
        if d*(o-stop)<=0:return j,o,2 if activated>=0 else 1,stop,activated,part_price
        if c>o or (c==o and o-l<=h-o):seq=(o,l,h,c)
        else:seq=(o,h,l,c)
        for k in range(3):
            a,b=seq[k],seq[k+1]
            if d*(b-a)<0:
                if d*(a-stop)>=0 and d*(b-stop)<=0:
                    return j,stop,2 if activated>=0 else 1,stop,activated,part_price
            elif d*(b-a)>0:
                if d*(b-best)>0:best=b
                stop=protection(d,stop,best,ep,risk,be,prog,lock)
                if activated<0 and d*(b-act)>=0:
                    activated=j;part_price=act
                    if style==3 or prog:stop=ratchet(d,stop,act-d*risk)
                if activated>=0 and (not prog or d*(best-ep)>=3*risk):
                    trail_active=True
                if trail_active:stop=trail_stop(d,stop,best,risk,style,atr,st,stline)
    return len(O)-1,C[-1],4,stop,activated,part_price

def checks():
    verify()
    a=np.array([10000.]);nan=np.array([np.nan]);atr=np.array([500.])
    r=execute(a,np.array([13500.]),np.array([9900.]),np.array([12000.]),atr,nan,nan,0,1,1000,3000,0,0,False,False,-1)
    assert r[1]==12500 and r[4]==0
    r=execute(a,np.array([10050.]),np.array([6500.]),np.array([8000.]),atr,nan,nan,0,-1,1000,3000,0,1,True,False,-1)
    assert r[1]==7500 and r[5]==7000
    r=execute(a,np.array([12100.]),np.array([9900.]),np.array([10000.]),atr,nan,nan,0,1,1000,3000,0,0,False,True,-1)
    assert r[1]==11000 and r[4]==-1
    r=execute(a,np.array([13500.]),np.array([8900.]),np.array([13000.]),atr,nan,nan,0,1,1000,3000,0,0,False,False,-1)
    assert r[1]==9000 and r[4]==-1
    r=execute(a,np.array([13500.]),np.array([9900.]),np.array([12000.]),atr,np.array([1.]),np.array([12400.]),0,1,1000,3000,0,3,False,False,-1)
    assert r[1]==12400 and r[4]==0
    assert execute(a,a,a,a,atr,nan,nan,0,1,1000,3000,0,0,False,False,0)[2]==3

REASONS={1:"Initial or pre-target protection stop",2:"Post-target trailing stop",3:"Failed breakout exit",4:"End of 2025 evaluation"}
def replay(bars,entries,ind,base,partial,style,structure,failed,prog,expiry):
    entry,trend,sl,tp,be=base
    O,H,L,C=bars;ATR,ST,STL=ind
    trades=[];free=0
    for i,d,r,trigger,atr,ema,struct,level,pull in entries:
        if i<free:continue
        ep=float(O[i])
        risk=float(d*(ep-struct) if structure else sl)
        if risk<=0:continue
        fail=-1
        if failed:
            # first subsequent completed 15m candle closing on wrong side
            # of the broken signal-candle boundary; exit next minute open.
            close_indices=np.arange((i//15+1)*15,len(O),15)
            hits=np.flatnonzero(d*(C[close_indices-1]-level)<0)
            if len(hits):fail=int(close_indices[hits[0]])
        j,xp,reason,stop,act,pp=execute(O,H,L,C,ATR,ST,STL,i,d,risk,tp,be,TRAILS.index(style),partial,prog,fail)
        free=j+1
        fraction=.5 if partial and act>=0 else 0.
        effective=float(fraction*pp+(1-fraction)*xp)
        gross=d*(effective-ep);fee=(ep+effective)*FEE
        vals={"indicator_0":r}
        if atr is not None:vals["indicator_1"]=atr
        if ema is not None:vals["indicator_2"]=ema
        trades.append(dict(entry_utc=dt(START+i*60).isoformat(),trigger_utc=dt(START+trigger*60).isoformat(),
            exit_utc=dt(END if reason==4 else START+j*60).isoformat(),side=d,entry_price=ep,exit_price=effective,
            stop_price=ep-d*risk,target_price=ep+d*tp,final_stop_price=float(stop),
            gross_points=gross,fee_points=fee,net_points=gross-fee,assumed_slippage_points=0,
            entry_reason=entry,exit_reason=REASONS[reason],
            signal_context={"rsi14":r,"risk_points":risk,"pullback_utc":dt(START+pull*60).isoformat(),
                "breakout_level":level,"activation_utc":dt(START+act*60).isoformat() if act>=0 else None,
                "partial_fraction":fraction,"partial_exit_price":float(pp) if fraction else None,
                "final_leg_exit_price":float(xp),"exit_price_is_weighted":fraction>0},
            indicator_values=vals))
    p=[t["net_points"] for t in trades];gain=math.fsum(max(0,n) for n in p);loss=-math.fsum(min(0,n) for n in p)
    months={f"2025-{m:02d}":0. for m in range(1,13)};eq=peak=dd=0.
    for t,n in zip(trades,p):
        months[t["entry_utc"][:7]]+=n;eq+=n;peak=max(peak,eq);dd=max(dd,peak-eq)
    wins=sum(n>0 for n in p)
    s=dict(accounting="realized",open_position=None,trades=len(p),net=math.fsum(p),wins=wins,
        win_rate=100*wins/len(p) if p else 0,profit_factor=gain/loss if loss else None,
        realized_drawdown_points=dd,monthly_entry_attribution=months,profitable_months=sum(n>0 for n in months.values()),
        stress_extra_50_points_roundtrip=sensitivity(trades,50),
        h1_net=sum(list(months.values())[:6]),h2_net=sum(list(months.values())[6:]))
    key=f"{entry}-ema{int(trend)}-sl{sl}-tp{tp}-partial{int(partial)}-{style}-struct{int(structure)}-fail{int(failed)}-prog{int(prog)}-expiry{expiry}"
    params=dict(entry=entry,trend_h1_ema50=trend,stop_loss=sl,take_profit_activation=tp,fee_protection_points=be,
        partial_fraction=.5 if partial else 0,trail=style,structure_stop=structure,failed_breakout_exit=failed,
        progressive_protection=prog,expiry_15m_bars=expiry,rsi_period=14,long_threshold=80,short_threshold=20)
    return dict(key=key,name="RSI14 "+key,parameters=params,summary=s,trades=trades)

def run():
    checks()
    bars,signals,snapshots,extra,rec=load()
    n=len(bars[0])//15+1
    atr=np.full(n,np.nan);st=np.full(n,np.nan);line=np.full(n,np.nan)
    for k,v in snapshots.items():
        atr[k//15]=v[0] if v[0] is not None else np.nan
        _,s,l,_,_,_=extra[k];st[k//15]=s if s is not None else np.nan;line[k//15]=l if l is not None else np.nan
    OUT.mkdir(parents=True,exist_ok=True)
    variants=[];baselines={}
    for base in BASES:
        entry,trend,*_=base
        base_entries=entry_list(bars,signals,snapshots,extra,entry,trend,0)
        old=candidates(bars,signals,snapshots,entry,trend)
        assert [v[:6] for v in base_entries]==old
        b=replay(bars,base_entries,(atr,st,line),base,False,"fixed-1r",False,False,False,0)
        expected=38547.273445 if entry=="pullback-breakout" else 20298.546545
        assert math.isclose(b["summary"]["net"],expected,abs_tol=1e-5),(entry,b["summary"]["net"],expected)
        baselines[entry]=b
        cache={expiry:entry_list(bars,signals,snapshots,extra,entry,trend,expiry) for expiry in EXPIRIES}
        for partial,style,structure,failed,prog,expiry in product((False,True),TRAILS,(False,True),(False,True) if entry=="pullback-breakout" else (False,),(False,True),EXPIRIES):
            v=replay(bars,cache[expiry],(atr,st,line),base,partial,style,structure,failed,prog,expiry)
            s=v["summary"];bs=b["summary"]
            s["net_change_vs_baseline"]=s["net"]-bs["net"]
            s["dd_change_vs_baseline"]=s["realized_drawdown_points"]-bs["realized_drawdown_points"]
            s["months_change_vs_baseline"]=s["profitable_months"]-bs["profitable_months"]
            variants.append(v)
    assert len(variants)==288,len(variants)
    rows=[]
    for v in variants:
        s=v["summary"];rows.append(dict(key=v["key"],**v["parameters"],**{k:x for k,x in s.items() if k not in ("monthly_entry_attribution","stress_extra_50_points_roundtrip","open_position")},**s["monthly_entry_attribution"],stress50_net=s["stress_extra_50_points_roundtrip"]["net"],stress50_months=s["stress_extra_50_points_roundtrip"]["months"]))
    with (OUT/"all_results.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    with gzip.open(OUT/"all_ledgers.json.gz","wt") as f:json.dump(variants,f,separators=(",",":"),allow_nan=False)
    chosen={};counts={}
    for base in BASES:
        entry=base[0];vs=[v for v in variants if v["parameters"]["entry"]==entry]
        pos=[v for v in vs if v["summary"]["net"]>0]
        counts[entry]=dict(total=len(vs),profitable=len(pos),net_improved=sum(v["summary"]["net_change_vs_baseline"]>1e-7 for v in vs),
            dd_reduced=sum(v["summary"]["dd_change_vs_baseline"]<-1e-7 for v in vs),
            net_up_dd_down=sum(v["summary"]["net_change_vs_baseline"]>1e-7 and v["summary"]["dd_change_vs_baseline"]<-1e-7 for v in vs),
            best_months=max(v["summary"]["profitable_months"] for v in vs))
        groups={"net":sorted(vs,key=lambda v:v["summary"]["net"],reverse=True),
                "month":sorted(vs,key=lambda v:(v["summary"]["profitable_months"],v["summary"]["net"]),reverse=True),
                "dd":sorted(pos,key=lambda v:v["summary"]["realized_drawdown_points"])}
        for label,group in groups.items():
            for v in group[:3]:
                chosen[v["key"]]=v
                print("TOP",json.dumps(dict(rank=label,key=v["key"],**v["parameters"],**v["summary"]),separators=(",",":"),allow_nan=False))
        # All one-factor changes vs baseline, including failures.
        for v in vs:
            p=v["parameters"];nchanges=sum((p["partial_fraction"]>0,p["trail"]!="fixed-1r",p["structure_stop"],p["failed_breakout_exit"],p["progressive_protection"],p["expiry_15m_bars"]>0))
            if nchanges<=1:
                chosen[v["key"]]=v
                print("SINGLE",json.dumps(dict(key=v["key"],**p,**v["summary"]),separators=(",",":"),allow_nan=False))
    print("COUNTS",json.dumps(counts),"PUBLISHED",len(chosen))
    export_bundle(OUT/"backtest.json",family="rsi14-runner-refinements-2025",symbol="BTCUSD",unit="price points",
        start_utc=dt(START).isoformat(),end_utc=dt(END).isoformat(),execution_timeframe_minutes=1,signal_timeframe_minutes=15,
        costs="0.05% taker each side +18% GST; partial exit weighted by quantity, one entry and two fractional exits. Zero extra slippage; funding/liquidation excluded. Color execution; stops gap at open. Extra 50 points/trade accounting sensitivity only.",
        variants=list(chosen.values()),recorder=rec,data_provenance=dict(manifest=str(ROOT/"manifest.json"),manifest_sha256=hashlib.sha256((ROOT/"manifest.json").read_bytes()).hexdigest(),
            input_minutes=len(bars[0]),timestamp_label="assumed open UTC",total_variants=len(variants),published_variants=len(chosen),full_archive="rsi14-runner-refinements-full",
            selection="two previously selected 2025 references, full factorial of coarse seven ideas; no 2026 validation",
            partial="50% at original TP, remaining 50% runner; exit_price is weighted effective price, final leg in signal_context; DD is trade-close accounting",
            progressive="fee lock at 1R, +1R at 2R, trail after max(original TP,3R); existing fee stop retained",
            structure="one tick beyond confirmed opposite-color pullback extreme; actual entry risk used as R; original TP unchanged",
            failed="first completed 15m close back across original signal-candle breakout boundary, next 1m open",
            supertrend="completed 15m line with directional confirmation; initial 1R fallback; never loosen",
            expiry="0 unlimited until next threshold crossing; 4/8 completed 15m intervals from signal; next 1m execution"))
if __name__=="__main__":run()
