"""Predefined post-target exit study on the two frozen 2025 reference candidates."""
import json,math,hashlib
from pathlib import Path
import numpy as np
from numba import njit
from research_rsi14_simple_robustness_2025 import load,entry_list,sensitivity
from research_rsi14_improvements_2025 import ROOT,START,END,FEE,dt,export_bundle,replay,verify

CANDIDATES=(("pullback",750,3000),("pullback-breakout",1000,3000))
MODES=("fixed","extend-one-R","trail-one-R")

@njit
def runner(O,H,L,C,i,d,risk,tp,mode):
    ep=O[i];stop=ep-d*risk;activation=ep+d*tp
    extended=activation+d*risk
    armed=False;best=ep;armed_at=-1
    for j in range(i,len(O)):
        o,h,l,c=O[j],H[j],L[j],C[j]
        # Stops already resting before the open are eligible at the open.
        if d*(o-stop)<=0:
            return j,o,2 if armed else 1,stop,armed_at
        # A favorable gap is observed at the open; it can activate the runner.
        if not armed and d*(o-activation)>=0:
            armed=True;armed_at=j;best=o
            stop=activation-d*risk
            if mode==1 and d*(o-extended)>=0:
                return j,extended,3,stop,armed_at
        if armed:
            if mode==1 and d*(o-extended)>=0:
                return j,extended,3,stop,armed_at
            if mode==2:
                if d*(o-best)>0:best=o
                stop=best-d*risk
        if c>o or (c==o and o-l<=h-o):
            seq=(o,l,h,c)
        else:
            seq=(o,h,l,c)
        for k in range(3):
            a,b=seq[k],seq[k+1]
            if d*(b-a)<0:
                if d*(a-stop)>=0 and d*(b-stop)<=0:
                    return j,stop,2 if armed else 1,stop,armed_at
            elif d*(b-a)>0:
                if not armed and d*(b-activation)>=0:
                    armed=True;armed_at=j;best=activation
                    stop=activation-d*risk
                if armed:
                    if mode==1 and d*(b-extended)>=0:
                        return j,extended,3,stop,armed_at
                    if mode==2 and d*(b-best)>0:
                        best=b;stop=best-d*risk
    return len(O)-1,C[-1],4,stop,armed_at

def test():
    verify()
    a=np.array([10000.]);hi=np.array([14000.]);lo=np.array([9900.])
    r=runner(a,hi,lo,np.array([12000.]),0,1,1000,3000,1)
    assert r[1]==14000 and r[2]==3 and r[4]==0
    r=runner(a,np.array([13500.]),lo,np.array([12000.]),0,1,1000,3000,2)
    assert r[1]==12500 and r[2]==2 and r[4]==0
    r=runner(a,np.array([10050.]),np.array([6500.]),np.array([8000.]),0,-1,1000,3000,2)
    assert r[1]==7500 and r[2]==2
    r=runner(a,np.array([13500.]),np.array([8900.]),np.array([13000.]),0,1,1000,3000,2)
    assert r[1]==9000 and r[2]==1 and r[4]==-1
    r=runner(np.array([10000.,11000.]),np.array([13500.,11100.]),np.array([9900.,10900.]),np.array([13200.,11000.]),0,1,1000,3000,2)
    assert r[1]==11000 and r[2]==2 and r[0]==1
    # Target activation followed by adverse excursion in same minute.
    r=runner(a,np.array([13200.]),np.array([9900.]),np.array([9900.]),0,1,1000,3000,1)
    assert r[1]==12000 and r[2]==2

REASONS={1:"Initial stop loss",2:"Post-target profit stop",3:"Extended take profit",4:"End of 2025 evaluation"}
def summary(trades):
    p=[t["net_points"] for t in trades]
    gain=math.fsum(max(0,n) for n in p);loss=-math.fsum(min(0,n) for n in p)
    monthly={f"2025-{m:02d}":0. for m in range(1,13)}
    eq=peak=dd=0.
    for t,n in zip(trades,p):
        monthly[t["entry_utc"][:7]]+=n
        eq+=n;peak=max(peak,eq);dd=max(dd,peak-eq)
    activated=[t for t in trades if t.get("signal_context",{}).get("activation_utc") is not None]
    wins=sum(n>0 for n in p)
    return dict(accounting="realized",open_position=None,trades=len(p),net=math.fsum(p),wins=wins,
        win_rate=100*wins/len(p) if p else 0,profit_factor=gain/loss if loss else None,
        realized_drawdown_points=dd,monthly_entry_attribution=monthly,profitable_months=sum(n>0 for n in monthly.values()),
        target_activations=len(activated),
        post_target_vs_original_gross_points=math.fsum(t["gross_points"]-t["signal_context"]["original_tp_points"] for t in activated),
        stress_extra_50_points_roundtrip=sensitivity(trades,50))
def variant(bars,entries,entry,sl,tp,mode):
    if mode=="fixed":
        empty={1:np.array([],dtype=np.int64),-1:np.array([],dtype=np.int64)}
        v=replay(bars,entries,empty,entry,False,"fixed",sl,tp,0,False)
        for t in v["trades"]:
            if t["exit_reason"]=="Take profit":
                t["signal_context"]["activation_utc"]=t["exit_utc"]
                t["signal_context"]["original_tp_points"]=tp
        v["summary"]=summary(v["trades"])
    else:
        O,H,L,C=bars;trades=[];free=0
        for i,d,r,trigger,atr,ema in entries:
            if i<free:continue
            ep=float(O[i])
            j,xp,reason,stop,activated=runner(O,H,L,C,i,d,sl,tp,1 if mode=="extend-one-R" else 2)
            free=j+1;gross=d*(xp-ep);fee=(ep+xp)*FEE
            vals={"indicator_0":r}
            if atr is not None:vals["indicator_1"]=atr
            if ema is not None:vals["indicator_2"]=ema
            trades.append(dict(entry_utc=dt(START+i*60).isoformat(),trigger_utc=dt(START+trigger*60).isoformat(),
                exit_utc=dt(END if reason==4 else START+j*60).isoformat(),side=d,entry_price=ep,exit_price=float(xp),
                stop_price=ep-d*sl,target_price=ep+d*tp,final_stop_price=float(stop),
                gross_points=float(gross),fee_points=float(fee),net_points=float(gross-fee),
                assumed_slippage_points=0,entry_reason=entry,exit_reason=REASONS[reason],
                signal_context={"rsi14":r,"original_tp_points":tp,"initial_risk_points":sl,
                    "activation_utc":dt(START+activated*60).isoformat() if activated>=0 else None,
                    "original_tp_is_activation_not_limit":True,"extended_tp_points":tp+sl if mode=="extend-one-R" else None},
                indicator_values=vals))
        v=dict(trades=trades,summary=summary(trades))
    v.update(key=f"{entry}-{sl}-{tp}-{mode}",name=f"RSI14 {entry} | SL {sl} TP {tp} | {mode}",
        parameters=dict(entry=entry,stop_loss=sl,original_take_profit=tp,post_target_exit=mode,
            activation_points=tp if mode!="fixed" else None,trail_points=sl if mode=="trail-one-R" else None,
            extended_target_points=tp+sl if mode=="extend-one-R" else None,
            initial_profit_lock_points=tp-sl if mode!="fixed" else None,rsi_period=14,long_threshold=80,short_threshold=20))
    return v
def run():
    test()
    bars,signals,snapshots,extra,rec=load()
    variants=[]
    for entry,sl,tp in CANDIDATES:
        entries=entry_list(bars,signals,snapshots,extra,entry)
        for mode in MODES:
            variants.append(variant(bars,entries,entry,sl,tp,mode))
    assert math.isclose(variants[0]["summary"]["net"],22643.81961,abs_tol=1e-5)
    assert math.isclose(variants[3]["summary"]["net"],26107.58048,abs_tol=1e-5)
    export_bundle(Path("scratch/rsi14_extend/backtest.json"),family="rsi14-post-target-2025",symbol="BTCUSD",unit="price points",
        start_utc=dt(START).isoformat(),end_utc=dt(END).isoformat(),execution_timeframe_minutes=1,signal_timeframe_minutes=15,
        costs="0.05% taker fee per side plus 18% GST; no Scalper Offer; zero extra slippage; funding and liquidation not modeled. Color paths; stop gaps at open. Extended target gap at limit conservatively. No guarantee of locked profit during gaps.",
        variants=variants,recorder=rec,data_provenance=dict(manifest=str(ROOT/"manifest.json"),
            manifest_sha256=hashlib.sha256((ROOT/"manifest.json").read_bytes()).hexdigest(),
            input_minutes=len(bars[0]),timestamp_label="assumed open UTC",selection="two previously selected candidates, three fixed exit policies each, no search or 2026 data",
            intraminute_timestamp="bar open label; exact tick time unknown",months="entry-month attribution"))
    for v in variants:
        print("RUNNER",json.dumps(dict(key=v["key"],**v["parameters"],**v["summary"]),separators=(",",":"),allow_nan=False))
if __name__=="__main__":run()
