#!/usr/bin/env python3
"""Adaptive exits after observable losses, preserving the 20-month entry logic."""
import os,sys,inspect,itertools
from pathlib import Path
import numpy as np
import pandas as pd
import research_btc15m_atr_month20_rsi_refine_20261124 as r
base=r.base;entry=r.entry;PROFILES=r.PROFILES;OUT=Path("analysis/btc15m_atr_month21_risk_combination_20261124")
RULES={}
SIZING={}
def add(trigger,value,sl,tp,lock,tiers=None):
    code=f"A{len(RULES):03d}"
    RULES[code]=(trigger,value,sl,tp,lock)
    SIZING[code]=tiers
add("none",0,3.,9.,r.LOCK)
add("losses",2,3.,9.,"LATE:4:1:1:0.25")
# Keep full exposure for the first trade; vary subsequent risk based on
# realized loss count. Use fractions of the original exposure profile.
for a,b,c,d in itertools.product([1.,.8,.6],[.35,.25,.15,.1],[.25,.15,.1,.05],[.1,.05,.025]):
    if a>=b>=c>=d:
        add("losses",2,3.,9.,"LATE:4:1:1:0.25",(a,b,c,d))
# Reduced initial exposure is not disguised as a full-exposure profile.
def parse(name):return RULES[name.split("__Q_",1)[1].split("_SL300",1)[0]]
def choose(name,losses,cash,mref):
    t,v,sl,tp,lk=parse(name)
    hit=(t=="losses" and losses>=v) or (t=="monthdd" and 100*max(0,1-cash/max(mref,1e-9))>=v)
    if not hit:sl,tp,lk=3.,9.,r.LOCK
    return sl,tp/sl,tuple(map(float,lk.split(":")[1:]))
def filter_entry(fil,side,j,ema,ind):
    z=entry.CACHE
    if j<32 or not np.isfinite(z["atr_pct"][j]) or z["atr_pct"][j]<.2:return False
    n=6 if side*(z["rsi"][j]-50)>=3 else 16
    return bool(side*(ema[j]-ema[j-n])>0)
def exposure(name,losses):
    p=name.split("__P_",1)[1].split("__Q_",1)[0];z=PROFILES[p]
    tiers=SIZING[name.split("__Q_",1)[1].split("_SL300",1)[0]] or z["tiers"]
    tier=1. if losses==0 else tiers[min(3,losses-1)]
    return z["scale"]*tier
def sim_factory():
    s=inspect.getsource(base.simulate)
    patches=[("if not check_filter(fil,side,j,ema,ind):","if not filter_entry(fil,side,j,ema,ind):"),
        ("qty=cash/entry","qty=(cash/entry)*exposure(name,losses_this_month)"),
        ("entry=raw_open*(1+side*SLIP)","riskmult,tpR,late=choose(name,losses_this_month,cash,month_reference)\n                entry=raw_open*(1+side*SLIP)")]
    for a,b in patches:
        assert s.count(a)==1,a
        s=s.replace(a,b)
    ns=dict(base.__dict__);ns.update(choose=choose,filter_entry=filter_entry,exposure=exposure)
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
    for j,(code,rule) in enumerate(RULES.items()):
        if j%n!=i:continue
        t,v,sl,tp,lk=rule
        for p in PROFILES:
            for path in base.PATHS:
                name=f"reclaim_NOFLIP_LATE825_MLOSS5__P_{p}__Q_{code}_SL300_TP3R"
                x,m,l=sim(df,ema,stline,trend,ind,name,cfg,sig,path)
                now=m.monthly_return_pct.to_numpy(float);old=before[p,path];drop=np.maximum(0,old[old>0]-now[old>0])
                x.update(profile=p,rule=code,kind=t,param=str(v),tiers=str(SIZING[code]),sl=sl,tp=tp,lock=lk,worst_month=float(now.min()),losing_months=int((now<0).sum()),preserved20=int((drop<=.00001).sum()),positive_month_drop=float(drop.sum()))
                m["profile"]=p;m["rule"]=code;rows.append(x);months.append(m)
                print("RESULT",p,code,path,x["profitable_months"],x["net_return_pct"],x["max_floating_drawdown_pct"],flush=True)
    d=OUT/f"shard_{i}";d.mkdir(parents=True,exist_ok=True)
    pd.DataFrame(rows).to_csv(d/"summary.csv",index=False);pd.concat(months,ignore_index=True).to_csv(d/"monthly.csv",index=False)
if __name__=="__main__":
    n=int(os.environ.get("SHARD_COUNT","12"))
    if len(sys.argv)>1 and sys.argv[1]=="aggregate":
        r.OUT=OUT;r.RULES=RULES;r.FLOOR={"80":(210.56,9.751),"100":(341.8214,11.929)};r.aggregate(n)
    else:run(int(os.environ.get("SHARD_INDEX","0")),n)
