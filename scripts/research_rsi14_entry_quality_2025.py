"""Coarse factorial entry quality research. All results are in-sample."""
import csv,gzip,hashlib,json,math
from pathlib import Path
from itertools import product
import numpy as np
from research_rsi14_runner_refinements_2025 import load,entry_list,checks,execute
from research_rsi14_improvements_2025 import ROOT,START,END,FEE,dt,candles,export_bundle
from research_rsi14_simple_robustness_2025 import sensitivity

OUT=Path("scratch/rsi14_entry_quality")
BASELINE=38547.273445
def wilder(x,n=14):
    out=np.full(len(x),np.nan)
    valid=np.flatnonzero(np.isfinite(x))
    if len(valid)<n:return out
    k=int(valid[n-1]);out[k]=np.mean(x[valid[:n]])
    for i in range(k+1,len(x)):
        if np.isfinite(x[i]):out[i]=(out[i-1]*(n-1)+x[i])/n
    return out

def rsi(c):
    delta=np.r_[np.nan,np.diff(c)]
    up=wilder(np.maximum(delta,0));down=wilder(np.maximum(-delta,0))
    with np.errstate(divide="ignore",invalid="ignore"):
        return np.where(np.isnan(up)|np.isnan(down),np.nan,np.where(down==0,np.where(up==0,50.,100.),100-100/(1+up/down)))

def adx(h,l,c):
    up=np.r_[np.nan,np.diff(h)];down=np.r_[np.nan,-np.diff(l)]
    tr=np.maximum(h-l,np.maximum(np.abs(h-np.r_[np.nan,c[:-1]]),np.abs(l-np.r_[np.nan,c[:-1]])))
    p=wilder(np.where(np.isnan(up),np.nan,np.where((up>down)&(up>0),up,0)))
    m=wilder(np.where(np.isnan(down),np.nan,np.where((down>up)&(down>0),down,0)))
    a=wilder(tr)
    with np.errstate(divide="ignore",invalid="ignore"):
        plus=100*p/a;minus=100*m/a
        dx=np.where(np.isnan(plus)|np.isnan(minus),np.nan,np.where(plus+minus==0,0.,100*np.abs(plus-minus)/(plus+minus)))
    return wilder(dx)
def indicators(bars,snapshots):
    O,H,L,C=bars
    volume=np.fromiter((float(v) for _,o,h,l,c,v in candles()),dtype=float,count=len(O))
    assert len(volume)==len(O)
    h=H.reshape(-1,15).max(axis=1);l=L.reshape(-1,15).min(axis=1);c=C[14::15]
    # prepend missing so index j//15 refers to last completed bar.
    r15=np.r_[np.nan,rsi(c)];a15=np.r_[np.nan,adx(h,l,c)]
    r60=np.r_[np.nan,rsi(C[59::60])]
    atr=np.full(len(c)+1,np.nan)
    for k,v in snapshots.items():
        if v[0] is not None:atr[k//15]=v[0]
    sums=np.r_[0.,np.cumsum(volume)]
    vmean=np.full(len(volume),np.nan)
    vmean[20:]=(sums[20:-1]-sums[:-21])/20
    return volume,vmean,r15,a15,r60,atr

def setup_rows(bars,signals,snapshots,extra):
    O,H,L,C=bars
    baseline=entry_list(bars,signals,snapshots,extra,"pullback-breakout",False,0)
    by_signal={v[3]:v for v in baseline};out=[]
    for q,(trigger,d,r,hi,lo) in enumerate(signals):
        if trigger not in by_signal:continue
        i,_,_,_,_,_,_,level,pull=by_signal[trigger]
        until=signals[q+1][0] if q+1<len(signals) else len(O)
        _,_,_,ph,pl,_=extra[pull]
        depth=(hi-pl if d==1 else ph-lo)/(hi-lo) if hi>lo else 0.
        # First breakout identical to existing candidate; subsequent attempts require fresh crossing.
        k=np.arange(i,until-1)
        retry=k[(d*(C[k]-level)>0)&(d*(C[k-1]-level)<=0)]+1
        out.append((i,d,r,trigger,level,pull,depth,until,retry))
    return out

def eligible(bars,ind,i,d,depth,cfg):
    strength,min_depth,rsif,volf,adxf,htf,atrisk,retry=cfg
    O,H,L,C=bars;vol,vm,r15,a15,r60,atr=ind
    k=i-1;span=H[k]-L[k]
    if strength and not (span>0 and d*(C[k]-O[k])>=.5*span):return False
    if min_depth and depth<min_depth:return False
    if rsif and not d*(r15[i//15]-50)>0:return False
    if volf and not (vm[k]>0 and vol[k]>vm[k]):return False
    if adxf and not a15[i//15]>25:return False
    if htf and not d*(r60[i//60]-50)>0:return False
    if atrisk and not atr[i//15]>0:return False
    return True

def replay(bars,ind,setups,cfg):
    O,H,L,C=bars;vol,vm,r15,a15,r60,atr=ind
    dummy=np.full(len(atr),np.nan);trades=[];free=0
    for first,d,r,trigger,level,pull,depth,until,attempts in setups:
        if first<free or not eligible(bars,ind,first,d,depth,cfg):continue
        i=first
        for attempt in range(2 if cfg[-1] else 1):
            ep=float(O[i]);risk=max(.5,math.ceil(2*atr[i//15]*2)/2) if cfg[-2] else 1000.
            tp=3*risk
            j,xp,reason,stop,act,pp=execute(O,H,L,C,atr,dummy,dummy,i,d,risk,tp,0,0,False,False,-1)
            free=j+1;gross=d*(xp-ep);fee=(ep+xp)*FEE
            vals={"indicator_0":r}
            if np.isfinite(atr[i//15]):vals["indicator_1"]=float(atr[i//15])
            trades.append(dict(entry_utc=dt(START+i*60).isoformat(),trigger_utc=dt(START+trigger*60).isoformat(),
                exit_utc=dt(END if reason==4 else START+j*60).isoformat(),side=d,entry_price=ep,exit_price=float(xp),
                stop_price=ep-d*risk,target_price=ep+d*tp,final_stop_price=float(stop),gross_points=float(gross),
                fee_points=float(fee),net_points=float(gross-fee),assumed_slippage_points=0,entry_reason="pullback-breakout" if attempt==0 else "one fresh breakout retry",
                exit_reason={1:"Initial stop loss",2:"Post-target trailing stop",4:"End of 2025 evaluation"}[reason],
                signal_context={"rsi14":r,"depth":depth,"risk_points":risk,"retry":bool(attempt),
                    "breakout_level":level,"pullback_utc":dt(START+pull*60).isoformat(),
                    "activation_utc":dt(START+act*60).isoformat() if act>=0 else None},indicator_values=vals))
            if not cfg[-1] or attempt or reason!=1 or free>=until:break
            # Retry once, only following actual SL and a fresh crossing in original setup.
            options=[int(k) for k in attempts if k>=free and eligible(bars,ind,int(k),d,depth,cfg)]
            if not options:break
            i=options[0]
    p=[t["net_points"] for t in trades];gain=math.fsum(max(0,n) for n in p);loss=-math.fsum(min(0,n) for n in p)
    months={f"2025-{m:02d}":0. for m in range(1,13)}
    eq=peak=dd=0.
    for t,n in zip(trades,p):
        months[t["entry_utc"][:7]]+=n;eq+=n;peak=max(peak,eq);dd=max(dd,peak-eq)
    wins=sum(n>0 for n in p)
    s=dict(accounting="realized",open_position=None,trades=len(p),net=math.fsum(p),wins=wins,
        win_rate=100*wins/len(p) if p else 0,profit_factor=gain/loss if loss else None,
        realized_drawdown_points=dd,monthly_entry_attribution=months,profitable_months=sum(n>0 for n in months.values()),
        stress_extra_50_points_roundtrip=sensitivity(trades,50),retry_trades=sum(t["signal_context"]["retry"] for t in trades),
        h1_net=sum(list(months.values())[:6]),h2_net=sum(list(months.values())[6:]))
    strength,depth,rsif,volf,adxf,htf,atrisk,retry=cfg
    params=dict(entry="pullback-breakout",breakout_body_50=strength,min_pullback_depth=depth,rsi_midline_filter=rsif,
        volume_above_previous20=volf,adx14_above25=adxf,h1_rsi_midline=htf,atr_risk_2x=atrisk,one_retry=retry,
        rsi_period=14,long_threshold=80,short_threshold=20,stop_loss_points=None if atrisk else 1000,
        activation_r=3,trail_r=1)
    key=f"body{int(strength)}-depth{depth:g}-rsi{int(rsif)}-vol{int(volf)}-adx{int(adxf)}-h1{int(htf)}-atr{int(atrisk)}-retry{int(retry)}"
    return dict(key=key,name="RSI14 entry quality "+key,parameters=params,summary=s,trades=trades)

def run():
    checks()
    bars,signals,snapshots,extra,rec=load();ind=indicators(bars,snapshots);setups=setup_rows(bars,signals,snapshots,extra)
    base=(False,0.,False,False,False,False,False,False)
    b=replay(bars,ind,setups,base)
    assert math.isclose(b["summary"]["net"],BASELINE,abs_tol=1e-5),b["summary"]
    assert b["summary"]["trades"]==83
    variants=[]
    for cfg in product((False,True),(0.,.25,.5),*((False,True),)*6):
        v=replay(bars,ind,setups,cfg);s=v["summary"];bs=b["summary"]
        s["net_change_vs_baseline"]=s["net"]-bs["net"]
        s["dd_change_vs_baseline"]=s["realized_drawdown_points"]-bs["realized_drawdown_points"]
        s["months_change_vs_baseline"]=s["profitable_months"]-bs["profitable_months"]
        s["new_rules"]=sum(bool(x) for x in cfg)
        variants.append(v)
    assert len(variants)==384
    OUT.mkdir(parents=True,exist_ok=True)
    rows=[]
    for v in variants:
        s=v["summary"];rows.append(dict(key=v["key"],**v["parameters"],**{k:x for k,x in s.items() if k not in ("monthly_entry_attribution","stress_extra_50_points_roundtrip","open_position")},**s["monthly_entry_attribution"],stress50_net=s["stress_extra_50_points_roundtrip"]["net"],stress50_months=s["stress_extra_50_points_roundtrip"]["months"]))
    with (OUT/"all_results.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    with gzip.open(OUT/"all_ledgers.json.gz","wt") as f:json.dump(variants,f,separators=(",",":"),allow_nan=False)
    pos=[v for v in variants if v["summary"]["net"]>0]
    strong=[v for v in pos if v["summary"]["trades"]>=40]
    chosen={}
    groups={"net":sorted(variants,key=lambda v:v["summary"]["net"],reverse=True),
            "month":sorted(variants,key=lambda v:(v["summary"]["profitable_months"],v["summary"]["net"]),reverse=True),
            "dd":sorted(strong,key=lambda v:v["summary"]["realized_drawdown_points"]),
            "both":sorted([v for v in variants if v["summary"]["net_change_vs_baseline"]>1e-7 and v["summary"]["dd_change_vs_baseline"]<-1e-7],key=lambda v:v["summary"]["net"],reverse=True)}
    for label,group in groups.items():
        seen=set()
        for v in group:
            s=v["summary"];ident=(round(s["net"],6),s["trades"],s["profitable_months"],round(s["realized_drawdown_points"],6))
            if ident in seen:continue
            seen.add(ident);chosen[v["key"]]=v
            print("TOP",json.dumps(dict(rank=label,key=v["key"],**v["parameters"],**s),separators=(",",":"),allow_nan=False))
            if len(seen)==5:break
    for v in variants:
        if v["summary"]["new_rules"]<=1:
            chosen[v["key"]]=v
            print("SINGLE",json.dumps(dict(key=v["key"],**v["parameters"],**v["summary"]),separators=(",",":"),allow_nan=False))
    counts=dict(total=len(variants),profitable=len(pos),net_improved=sum(v["summary"]["net_change_vs_baseline"]>1e-7 for v in variants),
        dd_reduced=sum(v["summary"]["dd_change_vs_baseline"]<-1e-7 for v in variants),
        both=len(groups["both"]),best_months=max(v["summary"]["profitable_months"] for v in variants),published=len(chosen))
    print("COUNTS",json.dumps(counts))
    export_bundle(OUT/"backtest.json",family="rsi14-entry-quality-2025",symbol="BTCUSD",unit="price points",
        start_utc=dt(START).isoformat(),end_utc=dt(END).isoformat(),execution_timeframe_minutes=1,signal_timeframe_minutes=15,
        costs="0.05% taker each side +18% GST, no additional slippage or Scalper Offer, funding/liquidation excluded. 1m Color execution; stop gaps at open. Extra 50 points/trade accounting stress.",
        variants=list(chosen.values()),recorder=rec,data_provenance=dict(manifest=str(ROOT/"manifest.json"),manifest_sha256=hashlib.sha256((ROOT/"manifest.json").read_bytes()).hexdigest(),
            input_minutes=len(bars[0]),timestamp_label="assumed open UTC",full_archive="rsi14-entry-quality-full",total_variants=len(variants),published_variants=len(chosen),
            selection="384 coarse 2025 factorial; not independent validation",entry_filter="evaluate first breakout only, skip rejected setup",
            depth="minimum 25% or 50% of signal range, measured at first opposite-color completed pullback",
            volume="breakout 1m volume > mean previous 20 completed 1m volumes",strength="directional body >=50% of 1m breakout range",
            adx="Wilder ADX14 on completed 15m bars",rsi="Wilder RSI14 on completed 15m or 1h bars",
            atr="2x last completed 15m ATR14, 3R activation, 1R trail; variable point risk, not equal dollar risk",
            retry="one fresh close crossing of original level after initial SL and before next threshold crossing; all filters rechecked",
            dd_rank="positive net and at least 40 trades; all results archived"))
if __name__=="__main__":run()
