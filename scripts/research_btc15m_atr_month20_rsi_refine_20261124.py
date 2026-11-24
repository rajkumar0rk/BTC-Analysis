#!/usr/bin/env python3
"""Refine 20/22 BTC15m candidate, targeting 21 or 22 months.
Both profiles separately. Hard profit/DD floors are the preceding 19-month
slope6 candidates. No calendar-specific rules. All history is in-sample.
"""
import itertools,inspect,os,sys
from pathlib import Path
import numpy as np
import pandas as pd
import research_btc15m_atr_month20_regime_exit_20261124 as prev
base=prev.base
entry=prev.entry
old=prev.old
PROFILES=prev.PROFILES
OUT=Path("analysis/btc15m_atr_month20_rsi_refine_20261124")
FLOOR=prev.LATEST
CONTROL20={"80":(199.8369,9.846),"100":(294.9555,12.022)}
LOCK=prev.LOCK
RULES={}
def add(kind="rsi",param=(3,6,16),size=None,sl=3.,tp=9.,lock=LOCK):
    RULES[f"N{len(RULES):03d}"]=(kind,param,size,sl,tp,lock)
add()
# Causal directional RSI switch sensitivity; no month/calendar labels.
for x in [1.,2.,2.5,3.5,4.,4.5,5.]:
    add(param=(x,6,16))
for a,b in itertools.product([5,6,7,8],[12,14,15,16,17,18,20,24]):
    if (a,b)!=(6,16):add(param=(3,a,b))
# Keep the 20-month signal but change sizing only after observable realized losses.
# Values are fractions of the profile's maximum exposure.
for s2,s3,s4 in itertools.product([.20,.25,.30,.35,.40,.45],[.10,.15,.20,.25,.30],[.05,.10,.15]):
    if s2>=s3>=s4:add(size=(1.,s2,s3,s4))
for s1 in [.60,.70,.80,.90]:
    for s2,s3,s4 in [(.25,.15,.05),(.30,.20,.10),(.35,.25,.10),(.40,.30,.10)]:
        add(size=(s1,s2,s3,s4))
# Relax/tighten the slope gate AFTER realized losses or observed month decline.
# Compare to R055, not trade outcomes or the month name.
for count in [1,2,3]:
    for alt in [4,5,6,8,12,16,20,24,32]:
        add("loss_alt",(count,alt))
    for kind in ["loss_or","loss_and","loss_any"]:
        add(kind,count)
for threshold in [.25,.5,1.,2.,3.,4.]:
    for alt in [6,16,24]:
        add("month_alt",(threshold,alt))
# Full exit replays, not ex-post trade deletion.
for sl,tp in itertools.product([2.,2.5,2.75,3.,3.25,3.5,4.],[7.,8.,9.,10.,11.,12.]):
    if (sl,tp)!=(3.,9.):add(sl=sl,tp=tp)
for a,l in itertools.product([4.,5.,6.,7.,7.5,8.,8.5],[0.,1.,2.,3.,4.]):
    if l<=a and (a,l)!=(8.,2.):add(lock=f"LATE:{a}:{l}:1:0.25")
# Restrict exposure in already losing months WITHOUT increasing max notional.
for threshold in [.5,1.,2.,3.]:
    for factor in [.4,.6,.8]:
        add("dd_size",(threshold,factor))

def spec(name):return RULES[name.split("__Q_",1)[1].split("_SL300",1)[0]]
def check(fil,side,j,ema,ind,name,losses,cash,month_reference):
    z=entry.CACHE
    if j<32 or j>=len(z["close"]) or not np.isfinite(z["atr_pct"][j]) or z["atr_pct"][j]<.20:return False
    kind,p,_,_,_,_=spec(name)
    slope=lambda n:bool(side*(ema[j]-ema[j-int(n)])>0)
    if kind=="rsi":
        return slope(p[1] if side*(z["rsi"][j]-50)>=p[0] else p[2])
    standard=slope(6 if side*(z["rsi"][j]-50)>=3 else 16)
    if kind=="loss_alt":return slope(p[1]) if losses>=p[0] else standard
    if kind=="loss_or":return (slope(6) or slope(16)) if losses>=p else standard
    if kind=="loss_and":return (slope(6) and slope(16)) if losses>=p else standard
    if kind=="loss_any":return True if losses>=p else standard
    if kind=="month_alt":
        dd=100*max(0.,1-cash/max(month_reference,1e-9))
        return slope(p[1]) if dd>=p[0] else standard
    if kind=="dd_size":return standard
    raise ValueError(kind)
def size(name,losses,cash,mref):
    p=name.split("__P_",1)[1].split("__Q_",1)[0]
    z=PROFILES[p];kind,param,tiers,*_=spec(name)
    if tiers is None:tiers=z["tiers"]
    frac=1. if losses==0 else tiers[0] if losses==1 else tiers[1] if losses==2 else tiers[2] if losses==3 else tiers[3]
    if kind=="dd_size" and 100*max(0,1-cash/max(mref,1e-9))>=param[0]:frac*=param[1]
    return z["scale"]*frac
def sim_factory():
    src=inspect.getsource(base.simulate)
    a="if not check_filter(fil,side,j,ema,ind):";b="qty=cash/entry"
    assert src.count(a)==src.count(b)==1
    src=src.replace(a,"if not check(fil,side,j,ema,ind,name,losses_this_month,cash,month_reference):")
    src=src.replace(b,"qty=(cash/entry)*size(name,losses_this_month,cash,month_reference)")
    ns=dict(base.__dict__);ns.update(check=check,size=size)
    exec(compile(src,"<refinement_sim>","exec"),ns)
    return ns["simulate"]
def run(shard,total):
    df,quality=base.read_source("BTCUSD")
    ema,stline,trend,valid=base.st_and_ema(df,base.TF)
    ind=base.make_indicators(df);entry.enrich(df,ind,ema)
    sig=base.make_signals(df,ema,trend,valid,"reclaim",4)[0]
    sim=sim_factory();controls={};rows=[];months=[];ledgers=[]
    for p in PROFILES:
        for path in base.PATHS:
            name=f"reclaim_NOFLIP_LATE825_MLOSS5__P_{p}__Q_N000_SL300_TP3R"
            r,m,l=sim(df,ema,stline,trend,ind,name,(4,"ATRMIN_0p2","PCT",3.,3.,LOCK),sig,path)
            assert abs(r["net_return_pct"]-CONTROL20[p][0])<.005 and abs(r["max_floating_drawdown_pct"]-CONTROL20[p][1])<.005 and r["profitable_months"]==20 and r["trades"]==70,(p,path,r)
            controls[p,path]=m.monthly_return_pct.to_numpy(float)
            if shard==0:
                l["profile"]=p;ledgers.append(l)
    for i,(rule,s) in enumerate(RULES.items()):
        if i%total!=shard:continue
        kind,param,tiers,sl,tp,lock=s
        cfg=(4,"ATRMIN_0p2","PCT",sl,tp/sl,lock)
        for p in PROFILES:
            name=f"reclaim_NOFLIP_LATE825_MLOSS5__P_{p}__Q_{rule}_SL300_TP3R"
            for path in base.PATHS:
                r,m,l=sim(df,ema,stline,trend,ind,name,cfg,sig,path)
                now=m.monthly_return_pct.to_numpy(float);before=controls[p,path]
                drops=np.maximum(0,before[before>0]-now[before>0])
                r.update(profile=p,rule=rule,kind=kind,param=str(param),tiers=str(tiers),sl=sl,tp=tp,lock=lock,worst_month=float(now.min()),losing_months=int((now<0).sum()),preserved20=int((drops<=.00001).sum()),positive_month_drop=float(drops.sum()))
                m["profile"]=p;m["rule"]=rule;months.append(m);rows.append(r)
                print("RESULT",p,rule,path,r["profitable_months"],r["net_return_pct"],r["max_floating_drawdown_pct"],flush=True)
    d=OUT/f"shard_{shard}";d.mkdir(parents=True,exist_ok=True)
    pd.DataFrame(rows).to_csv(d/"summary.csv",index=False)
    pd.concat(months,ignore_index=True).to_csv(d/"monthly.csv",index=False)
    if ledgers:pd.concat(ledgers,ignore_index=True).to_csv(d/"control20_trade_ledger.csv",index=False)
def aggregate(n):
    s=pd.concat([pd.read_csv(OUT/f"shard_{i}"/"summary.csv",dtype={"profile":str}) for i in range(n)],ignore_index=True)
    m=pd.concat([pd.read_csv(OUT/f"shard_{i}"/"monthly.csv",dtype={"profile":str}) for i in range(n)],ignore_index=True)
    s.to_csv(OUT/"summary.csv",index=False);m.to_csv(OUT/"monthly.csv",index=False)
    a=s.groupby(["profile","rule","kind","param","tiers","sl","tp","lock"],as_index=False,dropna=False).agg(
      net=("net_return_pct","min"),dd=("max_floating_drawdown_pct","max"),winning_months=("profitable_months","min"),losing_months=("losing_months","max"),worst_month=("worst_month","min"),trades=("trades","min"),preserved20=("preserved20","min"),positive_month_drop=("positive_month_drop","max"))
    a["strict_floor"]=a.apply(lambda r:r.net>=FLOOR[r.profile][0]-.0001 and r.dd<=FLOOR[r.profile][1]+.0001,axis=1)
    a["original_floor"]=a.apply(lambda r:r.net>=PROFILES[r.profile]["net"]-.0001 and r.dd<=PROFILES[r.profile]["dd"]+.0001,axis=1)
    a["qual20"]=a.strict_floor&(a.winning_months>=20)
    a["qual21"]=a.strict_floor&(a.winning_months>=21)
    a.to_csv(OUT/"ranked.csv",index=False)
    lines=["# BTCUSD 15M RSI switch — 20 to 21 monthly wins","",f"{len(RULES)} rules/profile, {len(s)} actual path simulations.",
      "Jan2025–Oct2026, 22 IST months, repeated in-sample selection. No future month/date labels used.",
      "Baseline 20-month 80%: +199.8369% / 9.846% DD; 100%: +294.9555% /12.022% DD.",
      "Strict floors from preceding 19-month models: 80% +203.0718% /9.751%; 100% +297.7751% /12.090%.",
      "Identical 1m OHLC path replay, taker fee 0.05% per side +18% GST, price slippage 0.02% per side. No funding, liquidation, live spread or depth.",
      "Separate profiles, exposure never above 80% or 100% respectively.",""]
    for p in PROFILES:
        x=a[a.profile==p].sort_values(["winning_months","dd","net"],ascending=[False,True,False])
        x.to_csv(OUT/f"profile_{p}.csv",index=False)
        strict=x[x.qual20];better=x[x.qual21];loose=x[x.original_floor&(x.winning_months>=21)]
        lines.extend([f"## {p}% exposure",f"Strict 20+ candidates: {len(strict)}; strict 21+: {len(better)}; 21+ vs original floors: {len(loose)}.",
          "", "### Strict 20+ candidates",strict.head(25).to_markdown(index=False) if len(strict) else "None.",
          "", "### 21+ against original locked floors",loose.head(20).to_markdown(index=False) if len(loose) else "None.",
          "", "### Highest monthly consistency regardless of constraints",x.head(15).to_markdown(index=False),
          "", "### Preserving all 20 existing positive months plus strict floors",strict[strict.preserved20>=20].head(15).to_markdown(index=False),""])
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(lines)+"\n")
    print("\n".join(lines[:12]),flush=True)
if __name__=="__main__":
    n=int(os.environ.get("SHARD_COUNT","24"))
    if len(sys.argv)>1 and sys.argv[1]=="aggregate":aggregate(n)
    else:run(int(os.environ.get("SHARD_INDEX","0")),n)
