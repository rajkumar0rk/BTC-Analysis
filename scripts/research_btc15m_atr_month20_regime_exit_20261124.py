#!/usr/bin/env python3
"""Causal regime and risk/exit search for >=20 profitable months, separately.

Require no drop from the improved slope6 profile's compounded return and
no increase in its maximum floating equity DD, BOTH minute OHLC paths.
Also report original locked floors and per-positive-month preservation.
Jan 2025–Oct 2026 in-sample, extensively mined, no forward validation.
"""
import os,sys,inspect,itertools
from pathlib import Path
import numpy as np
import pandas as pd
import research_btc15m_atr_monthly_win_improvement_20261124 as old

base=old.base
entry=old.entry
PROFILES=old.PROFILES
OUT=Path("analysis/btc15m_atr_month20_regime_exit_20261124")
LATEST={"80":(203.0718,9.751),"100":(297.7751,12.090)}
LOCK="LATE:8:2:1:0.25"
RULES={}
def add(kind,param,sl=3.,tp=9.,lock=LOCK):
    RULES[f"R{len(RULES):03d}"]=(kind,param,sl,tp,lock)
add("none",0)
add("slope",6)
add("slope",16)
for n in [4,5,7,8,10,12,14,16,18,20,24]:
    add("or",(6,n))
    add("and",(6,n))
for x in [.20,.25,.30,.35,.40,.50,.65,.80]:
    add("atr_switch",(x,6,16))
    add("atr_switch",(x,16,6))
for x in [0.5,0.75,1.,1.25,1.5,2.]:
    add("vol_switch",(x,6,16))
    add("vol_switch",(x,16,6))
for x in [0,3,5,8,10,15]:
    add("rsi_switch",(x,6,16))
    add("rsi_switch",(x,16,6))
for loss in [1,2,3]:
    add("loss_switch",(loss,6,16))
    add("loss_switch",(loss,16,6))
    add("loss_relax",loss)
    add("loss_tighten",loss)
for x in [.25,.5,1.,1.5,2.,3.]:
    add("monthloss_switch",(x,6,16))
    add("monthloss_switch",(x,16,6))
for n in [6,16]:
    for sl,tp in itertools.product([2.,2.5,2.75,3.,3.25,3.5,4.],[7.,8.,9.,10.,11.,12.]):
        if sl!=3 or tp!=9:
            add("slope",n,sl,tp)
    for activation,first in itertools.product([4.,5.,6.,7.,7.5,8.,8.5],[0.,1.,2.,3.]):
        if (activation,first)!=(8.,2.):
            add("slope",n,lock=f"LATE:{activation}:{first}:1:0.25")
    for act in [5.,6.,7.,8.]:
        for locked in [-1.,0.,1.]:
            add("slope",n,lock=f"LATE:{act}:{locked}:0.5:0.5")

def get_rule(name):
    return RULES[name.split("__Q_",1)[1].split("_SL300",1)[0]]

def check(fil,side,j,ema,ind,name,losses,cash,month_reference):
    z=entry.CACHE
    if j<32 or j>=len(z["close"]) or not np.isfinite(z["atr_pct"][j]) or z["atr_pct"][j]<.20:
        return False
    kind,p,sl,tp,lock=get_rule(name)
    slope=lambda n: bool(side*(ema[j]-ema[j-int(n)])>0)
    if kind=="none":return True
    if kind=="slope":return slope(p)
    if kind=="or":return slope(p[0]) or slope(p[1])
    if kind=="and":return slope(p[0]) and slope(p[1])
    if kind=="atr_switch":return slope(p[1] if z["atr_pct"][j]>=p[0] else p[2])
    if kind=="vol_switch":return slope(p[1] if z["vol"][j]>=p[0] else p[2])
    if kind=="rsi_switch":return slope(p[1] if side*(z["rsi"][j]-50)>=p[0] else p[2])
    if kind=="loss_switch":return slope(p[1] if losses>=p[0] else p[2])
    if kind=="loss_relax":return (slope(6) or slope(16)) if losses>=p else slope(6)
    if kind=="loss_tighten":return (slope(6) and slope(16)) if losses>=p else slope(6)
    if kind=="monthloss_switch":
        dd=100*max(0,1-cash/max(month_reference,1e-9))
        return slope(p[1] if dd>=p[0] else p[2])
    raise ValueError(kind)

def simulator():
    src=inspect.getsource(base.simulate)
    a="if not check_filter(fil,side,j,ema,ind):"
    b="qty=cash/entry"
    assert src.count(a)==src.count(b)==1
    src=src.replace(a,"if not check(fil,side,j,ema,ind,name,losses_this_month,cash,month_reference):")
    src=src.replace(b,"qty=(cash/entry)*profile_size(name,losses_this_month)")
    ns=dict(base.__dict__);ns.update(check=check,profile_size=old.profile_size)
    exec(compile(src,"<verified_regime_exit>","exec"),ns)
    return ns["simulate"]

def run(shard,total):
    OUT.mkdir(parents=True,exist_ok=True)
    sim=simulator()
    df,quality=base.read_source("BTCUSD")
    ema,stline,trend,valid=base.st_and_ema(df,base.TF)
    ind=base.make_indicators(df)
    entry.enrich(df,ind,ema)
    sig=base.make_signals(df,ema,trend,valid,"reclaim",4)[0]
    baselines={}
    for p,z in PROFILES.items():
        for path in base.PATHS:
            for code,expected,nm,tr in [("R000",(z["net"],z["dd"]),18,73),("R001",LATEST[p],19,70)]:
                name=f"reclaim_NOFLIP_LATE825_MLOSS5__P_{p}__Q_{code}_SL300_TP3R"
                r,m,led=sim(df,ema,stline,trend,ind,name,(4,"ATRMIN_0p2","PCT",3.,3.,LOCK),sig,path)
                assert abs(r["net_return_pct"]-expected[0])<.005 and abs(r["max_floating_drawdown_pct"]-expected[1])<.005 and r["profitable_months"]==nm and r["trades"]==tr,(p,path,code,r)
                baselines[p,path,code]=m.monthly_return_pct.to_numpy(float)
    rows=[];months=[]
    for i,(code,spec) in enumerate(RULES.items()):
        if i%total!=shard:continue
        kind,param,sl,tp,lock=spec
        cfg=(4,"ATRMIN_0p2","PCT",sl,tp/sl,lock)
        for p in PROFILES:
            name=f"reclaim_NOFLIP_LATE825_MLOSS5__P_{p}__Q_{code}_SL300_TP3R"
            for path in base.PATHS:
                r,mo,led=sim(df,ema,stline,trend,ind,name,cfg,sig,path)
                now=mo.monthly_return_pct.to_numpy(float)
                r.update(profile=p,rule=code,kind=kind,parameter=str(param),sl=sl,tp=tp,lock=lock,
                    worst_month=now.min(),negative_months=int((now<0).sum()),
                    sum_negative_months=np.minimum(now,0).sum())
                for source,label in [("R000","original"),("R001","latest")]:
                    before=baselines[p,path,source]
                    prevpositive=before>0
                    drops=np.maximum(0,before[prevpositive]-now[prevpositive])
                    r[f"{label}_positive_months_preserved"]=int((drops<=.00001).sum())
                    r[f"{label}_positive_months_total_drop"]=float(drops.sum())
                mo["profile"]=p;mo["rule"]=code
                rows.append(r);months.append(mo)
                print("RESULT",p,code,path,r["profitable_months"],r["net_return_pct"],r["max_floating_drawdown_pct"],flush=True)
    dest=OUT/f"shard_{shard}";dest.mkdir(parents=True,exist_ok=True)
    pd.DataFrame(rows).to_csv(dest/"summary.csv",index=False)
    pd.concat(months,ignore_index=True).to_csv(dest/"monthly.csv",index=False)

def aggregate(n):
    s=pd.concat([pd.read_csv(OUT/f"shard_{i}"/"summary.csv",dtype={"profile":str}) for i in range(n)],ignore_index=True)
    m=pd.concat([pd.read_csv(OUT/f"shard_{i}"/"monthly.csv",dtype={"profile":str}) for i in range(n)],ignore_index=True)
    s.to_csv(OUT/"summary.csv",index=False);m.to_csv(OUT/"monthly.csv",index=False)
    a=s.groupby(["profile","rule","kind","parameter","sl","tp","lock"],as_index=False).agg(
        net=("net_return_pct","min"),dd=("max_floating_drawdown_pct","max"),
        winning_months=("profitable_months","min"),losing_months=("negative_months","max"),
        worst_month=("worst_month","min"),sum_loss_months=("sum_negative_months","min"),trades=("trades","min"),
        original_good_months_preserved=("original_positive_months_preserved","min"),
        latest_good_months_preserved=("latest_positive_months_preserved","min"),
        latest_winner_month_drop=("latest_positive_months_total_drop","max"))
    a["latest_floor"]=a.apply(lambda r:r.net>=LATEST[r.profile][0]-.0001 and r.dd<=LATEST[r.profile][1]+.0001,axis=1)
    a["original_floor"]=a.apply(lambda r:r.net>=PROFILES[r.profile]["net"]-.0001 and r.dd<=PROFILES[r.profile]["dd"]+.0001,axis=1)
    a["qualifies20"]=a.latest_floor&(a.winning_months>=20)
    a["qualifies20_original"]=a.original_floor&(a.winning_months>=20)
    a["strict20"]=a.qualifies20&(a.latest_good_months_preserved>=19)
    a.to_csv(OUT/"ranked.csv",index=False)
    lines=["# BTCUSD 15m regime/exit sweep for 20 profitable months",
           "",f"{len(RULES)} rules per profile; {len(s)} complete simulations; two hypothetical 1m OHLC price paths.",
           "Historical data Jan 2025–Oct 2026, 22 IST months, repeatedly tuned/in sample.",
           "Causal ATR/volume/RSI/slope and realized loss switches; no calendar-specific optimization logic.",
           "Baseline 80%: +203.0718%, DD 9.751%, 19 months; 100%: +297.7751%, DD 12.090%, 19 months.",
           "Hard acceptance: >=20 months, net >= latest candidate, floating max DD <= latest candidate, on both paths.",
           "Secondary benchmark: original 80% +185.0292%/10.465%; original locked 100% +266.1034%/12.916%.",
           "Fees 0.05% taker per side +18% GST and 0.02% adverse price slippage per side; funding, liquidation and actual live execution excluded.",
           ""]
    for p in PROFILES:
        x=a[a.profile==p].sort_values(["winning_months","dd","net"],ascending=[False,True,False])
        valid=x[x.qualifies20];oldok=x[x.qualifies20_original];preserve=x[x.strict20]
        x.to_csv(OUT/f"profile_{p}.csv",index=False)
        lines.extend([f"## {p}% maximum exposure",f"Strict latest-floor winners: {len(valid)}; original-floor winners: {len(oldok)}; preserving every latest profitable month's return: {len(preserve)}.",
                      "", "### Strict 20+ month candidates",valid.head(20).to_markdown(index=False) if len(valid) else "None.",
                      "", "### 20+ months preserving ORIGINAL floor",oldok.head(20).to_markdown(index=False) if len(oldok) else "None.",
                      "", "### Best candidates retaining latest profit/DD",x[x.latest_floor].head(12).to_markdown(index=False),
                      "", "### Highest monthly consistency regardless of tradeoff",x.head(12).to_markdown(index=False),""])
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(lines)+"\n")
    print("\n".join(lines[:12]))
    for p in PROFILES:
        print("STRICT",p,a[(a.profile==p)&a.qualifies20].to_dict("records"),flush=True)

if __name__=="__main__":
    n=int(os.environ.get("SHARD_COUNT","24"))
    if len(sys.argv)>1 and sys.argv[1]=="aggregate":aggregate(n)
    else:run(int(os.environ.get("SHARD_INDEX","0")),n)
