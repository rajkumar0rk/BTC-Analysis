#!/usr/bin/env python3
"""Adaptive exits after observable losses, preserving the 20-month entry logic."""
import os,sys,inspect,itertools
from pathlib import Path
import numpy as np
import pandas as pd
import research_btc15m_atr_month20_rsi_refine_20261124 as r
base=r.base;entry=r.entry;PROFILES=r.PROFILES;OUT=Path("analysis/btc15m_atr_month21_fine_risk_20261124")
RULES={}
SIZING={}
CAPS={}
RECOVERY={}
MINIMUM={}
def add(trigger,value,sl,tp,lock,tiers=None,cap=None,buffer=0.,recovery=None,minsize=0.):
    code=f"A{len(RULES):03d}"
    RULES[code]=(trigger,value,sl,tp,lock)
    SIZING[code]=tiers
    CAPS[code]=(cap,buffer)
    RECOVERY[code]=recovery
    MINIMUM[code]=minsize
add("none",0,3.,9.,r.LOCK)
add("losses",2,3.,9.,"LATE:4:1:1:0.25")
add("losses",2,3.,9.,"LATE:4:2:1:0.25",(.8,.1,.1,.1),1.,.01,(1,0,.2))
add("losses",2,3.,9.,"LATE:4:2:1:0.25",(.8,.1,.1,.1),1.03,.015,None)
add("losses",2,3.,9.,"LATE:4:2:1:0.25",None,1.05,.01,(1,0,.2))
# Candidate risk budgets using causal observed account equity.
# Skip orders below 1% of current account equity, rather than keeping phantom micropositions.
for tiers,cap,buffer,recovery in itertools.product(
    [None,(.8,.1,.1,.1),(.9,.15,.1,.05),(1.,.2,.1,.05)],
    [.985,1.,1.015,1.03],
    [.008,.012,.015],
    [None,(1,0,.2)]):
    add("losses",2,3.,9.,"LATE:4:2:1:0.25",tiers,cap,buffer,recovery,.01)
# Alternative recovery exits, with the exact same entry generator and risk cap.
for act,locked,recovery in itertools.product([3.,3.5,4.5,5.],[1.5,2.,2.5],[None,(1,0,.2)]):
    add("losses",2,3.,9.,f"LATE:{act}:{locked}:1:0.25",(.8,.1,.1,.1),1.,.01,recovery,.01)
for sl,tp,recovery in itertools.product([2.,2.5,3.5],[8.,9.,10.],[None,(1,0,.2)]):
    add("losses",1,sl,tp,"LATE:4:2:1:0.25",(.8,.1,.1,.1),1.,.01,recovery,.01)
def parse(name):return RULES[name.split("__Q_",1)[1].split("_SL300",1)[0]]
def choose(name,losses,cash,mref):
    t,v,sl,tp,lk=parse(name)
    hit=(t=="losses" and losses>=v) or (t=="monthdd" and 100*max(0,1-cash/max(mref,1e-9))>=v)
    if not hit:sl,tp,lk=3.,9.,r.LOCK
    return sl,tp/sl,tuple(map(float,lk.split(":")[1:]))
def filter_entry(fil,side,j,ema,ind,name,losses):
    z=entry.CACHE
    if j<32 or not np.isfinite(z["atr_pct"][j]):return False
    n=6 if side*(z["rsi"][j]-50)>=3 else 16
    minimum=.20
    recovery=RECOVERY[name.split("__Q_",1)[1].split("_SL300",1)[0]]
    if recovery is not None and losses>=recovery[0]:
        n,minimum=recovery[1:]
    return bool(z["atr_pct"][j]>=minimum and (n==0 or side*(ema[j]-ema[j-n])>0))
def exposure(name,losses,cash,peak,side,entry,stop):
    p=name.split("__P_",1)[1].split("__Q_",1)[0];z=PROFILES[p]
    tiers=SIZING[name.split("__Q_",1)[1].split("_SL300",1)[0]] or z["tiers"]
    tier=1. if losses==0 else tiers[min(3,losses-1)]
    ordinary=z["scale"]*tier
    code=name.split("__Q_",1)[1].split("_SL300",1)[0]
    cap,buffer=CAPS[code]
    if cap is None:return ordinary
    ddlim={"80":.09731,"100":.11929}[p]*cap
    exit_fill=stop*(1-side*base.SLIP)
    loss_per_unit=side*(entry-exit_fill)+base.FEE*(entry+exit_fill)+buffer*entry
    headroom=max(0.,cash-peak*(1-ddlim))
    budget_fraction=headroom*entry/(max(cash,1e-9)*max(loss_per_unit,1e-9))
    # A tiny size rather than an invalid zero-quantity order retains event order.
    # Any such near-zero position is explicitly a modeling limitation, not a live order.
    return min(ordinary,max(1e-6,budget_fraction))
def minimum(name):
    return MINIMUM[name.split("__Q_",1)[1].split("_SL300",1)[0]]
def sim_factory():
    s=inspect.getsource(base.simulate)
    patches=[("if not check_filter(fil,side,j,ema,ind):","if not filter_entry(fil,side,j,ema,ind,name,losses_this_month):"),
        ("if not (np.isfinite(R) and R>0 and stop>0 and valid_target and R_ST>0):",
         "fraction=exposure(name,losses_this_month,cash,eq_high,side,entry,stop)\n                if not (np.isfinite(R) and R>0 and stop>0 and valid_target and R_ST>0 and fraction>=minimum(name)):"),
        ("qty=cash/entry","qty=(cash/entry)*fraction"),
        ("entry=raw_open*(1+side*SLIP)","riskmult,tpR,late=choose(name,losses_this_month,cash,month_reference)\n                entry=raw_open*(1+side*SLIP)")]
    for a,b in patches:
        assert s.count(a)==1,a
        s=s.replace(a,b)
    ns=dict(base.__dict__);ns.update(choose=choose,filter_entry=filter_entry,exposure=exposure,minimum=minimum)
    exec(compile(s,"<causal_adaptive_exit>","exec"),ns)
    return ns["simulate"]
def run(i,n):
    df,q=base.read_source("BTCUSD");ema,stline,trend,valid=base.st_and_ema(df,base.TF)
    ind=base.make_indicators(df);entry.enrich(df,ind,ema);sig=base.make_signals(df,ema,trend,valid,"reclaim",4)[0]
    sim=sim_factory();cfg=(4,"ATRMIN_0p2","PCT",3.,3.,r.LOCK)
    before={};rows=[];months=[]
    for p in PROFILES:
        for path in base.PATHS:
            name=f"reclaim_NOFLIP_LATE825_MLOSS5__P_{p}__Q_A000_SL300_TP3R"
            x,m,l=sim(df,ema,stline,trend,ind,name,cfg,sig,path)
            assert abs(x["net_return_pct"]-r.CONTROL20[p][0])<.005 and abs(x["max_floating_drawdown_pct"]-r.CONTROL20[p][1])<.005 and x["profitable_months"]==20 and x["trades"]==70,(p,path,x)
            before[p,path]=m.monthly_return_pct.to_numpy(float)
            name=f"reclaim_NOFLIP_LATE825_MLOSS5__P_{p}__Q_A001_SL300_TP3R"
            x,m,l=sim(df,ema,stline,trend,ind,name,cfg,sig,path)
            expected={"80":(257.8791,13.283),"100":(384.6740,16.253)}[p]
            assert abs(x["net_return_pct"]-expected[0])<.005 and abs(x["max_floating_drawdown_pct"]-expected[1])<.005 and x["profitable_months"]==21,(p,path,x)
            name=f"reclaim_NOFLIP_LATE825_MLOSS5__P_{p}__Q_A002_SL300_TP3R"
            x,m,l=sim(df,ema,stline,trend,ind,name,cfg,sig,path)
            expected={"80":(236.5723,9.596),"100":(346.8948,11.771)}[p]
            assert abs(x["net_return_pct"]-expected[0])<.005 and abs(x["max_floating_drawdown_pct"]-expected[1])<.005 and x["profitable_months"]==20,(p,path,x)
    for j,(code,rule) in enumerate(RULES.items()):
        if j%n!=i:continue
        t,v,sl,tp,lk=rule
        for p in PROFILES:
            for path in base.PATHS:
                name=f"reclaim_NOFLIP_LATE825_MLOSS5__P_{p}__Q_{code}_SL300_TP3R"
                x,m,l=sim(df,ema,stline,trend,ind,name,cfg,sig,path)
                now=m.monthly_return_pct.to_numpy(float);old=before[p,path];drop=np.maximum(0,old[old>0]-now[old>0])
                x.update(profile=p,rule=code,kind=t,param=str(v),tiers=str((SIZING[code],CAPS[code],RECOVERY[code],MINIMUM[code])),sl=sl,tp=tp,lock=lk,worst_month=float(now.min()),losing_months=int((now<0).sum()),preserved20=int((drop<=.00001).sum()),positive_month_drop=float(drop.sum()))
                m["profile"]=p;m["rule"]=code;rows.append(x);months.append(m)
                print("RESULT",p,code,path,x["profitable_months"],x["net_return_pct"],x["max_floating_drawdown_pct"],flush=True)
    d=OUT/f"shard_{i}";d.mkdir(parents=True,exist_ok=True)
    pd.DataFrame(rows).to_csv(d/"summary.csv",index=False);pd.concat(months,ignore_index=True).to_csv(d/"monthly.csv",index=False)
if __name__=="__main__":
    n=int(os.environ.get("SHARD_COUNT","12"))
    if len(sys.argv)>1 and sys.argv[1]=="aggregate":
        r.OUT=OUT;r.RULES=RULES;r.FLOOR={"80":(236.5723,9.596),"100":(346.8948,11.771)};r.aggregate(n)
    else:run(int(os.environ.get("SHARD_INDEX","0")),n)
