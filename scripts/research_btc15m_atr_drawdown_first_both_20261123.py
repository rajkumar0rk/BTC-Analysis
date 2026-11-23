#!/usr/bin/env python3
"""Drawdown-first BTCUSD 15M ATR-Reclaim: optimize 80%/100% separately.

Do not score higher profit as an improvement if max floating DD is unchanged.
Preserve 18+ positive months and >= each profile's already improved net return.
Candidate guards use only causal information available by the entry time.
22-month repeatedly selected historical sample; NOT forward validation.
"""
import os, sys, inspect, itertools
from pathlib import Path
import numpy as np
import pandas as pd
import research_btc15m_regime_entry_dd_20261123 as entry
base=entry.base
OUT=Path("analysis/btc15m_atr_drawdown_first_both_20261123")
PROFILES={"80":(.8,180.6308,11.879),"100":(1.,255.8336,14.740)}
CONTROL=("LATE:8:2:1:0.25","BASE",5)

def grid(mode):
    if mode=="TRAIL":
        # Independent nonlinear/fast protective-stop sensitivity.
        a=[2.,3.,4.,5.,6.,7.,7.5,8.,8.25]
        l=[-1.,0.,1.,2.,3.,4.,5.]
        steps=[(.25,.25),(.5,.5),(1.,1.),(.5,.25)]
        return [(f"LATE:{act:g}:{first:g}:{step:g}:{increment:g}","BASE",5)
                for act,first,(step,increment) in itertools.product(a,l,steps)
                if first<=act]
    if mode=="SIZE":
        # 0–1x causal position size based on number of net losing exits
        # already realized this IST month.
        second=[.40,.55,.65,.75,.90,1.]
        third=[.15,.25,.30,.40,.50,.65]
        fourth=[.05,.10,.20,.30,.40]
        res=[(CONTROL[0],f"T{int(round(s2*1000))}x{int(round(s3*1000))}x{int(round(s4*1000))}",5)
          for s2,s3,s4 in itertools.product(second,third,fourth) if s2>=s3>=s4]
        # Continue with baseline position tiers, but after 3/4 losses, pause.
        res.extend([(CONTROL[0],"BASE",cap) for cap in (3,4,6,7)])
        # Drawdown of current closed equity from most recent *floating* peak
        # is known before entry. Reduce future entries only when observed.
        for trigger in (2.,4.,6.,8.,10.):
            for risk_floor in (.3,.5,.7):
                res.append((CONTROL[0],f"D{int(trigger)}x{int(risk_floor*1000)}",5))
        return res
    raise ValueError(mode)

def size_rule(name,losses,cash,peak):
    profile=name.split("__P_",1)[1].split("__R_",1)[0]
    config=name.split("__R_",1)[1].split("_SL300",1)[0]
    assert profile in PROFILES
    top=PROFILES[profile][0]
    if config.startswith("T"):
        s2,s3,s4=[float(x)/1000 for x in config[1:].split("x")]
    else:
        s2,s3,s4=.65,.30,.10
    tier=1 if losses<2 else s2 if losses==2 else s3 if losses==3 else s4
    if config.startswith("D"):
        trig,floor=[int(x) for x in config[1:].split("x")]
        eqdd=100*max(0.,peak-cash)/max(peak,1e-9)
        if eqdd>=trig:
            tier*=floor/1000
    return max(0.,min(1.,top*tier))

def make_simulator():
    source=inspect.getsource(base.simulate)
    previous="if not check_filter(fil,side,j,ema,ind):"
    before="qty=cash/entry"
    assert source.count(previous)==1 and source.count(before)==1
    source=source.replace(previous,"if not causal_entry_filter(fil,side,j,ema,ind):")
    source=source.replace(before,"qty=(cash/entry)*size_rule(name,losses_this_month,cash,eq_high)")
    ns=dict(base.__dict__)
    ns["causal_entry_filter"]=entry.market_filter
    ns["size_rule"]=size_rule
    exec(compile(source,"<validated_dd_first_sim>","exec"),ns)
    return ns["simulate"]

def simulate_shard(idx,total,mode):
    OUT.mkdir(parents=True,exist_ok=True)
    df,quality=base.read_source("BTCUSD")
    ema,stline,trend,valid=base.st_and_ema(df,base.TF)
    indicators=base.make_indicators(df)
    entry.enrich(df,indicators,ema)
    signals=base.make_signals(df,ema,trend,valid,"reclaim",4)[0]
    sim=make_simulator()
    for profile, (globalex, target_profit, dd) in PROFILES.items():
        name=f"reclaim_NOFLIP_LATE825_MLOSS5__P_{profile}__R_BASE_SL300_TP3R"
        cfg=(4,"ATRMIN_0p2","PCT",3,3.0,CONTROL[0])
        for path in base.PATHS:
            row,mon,trades=sim(df,ema,stline,trend,indicators,name,cfg,signals,path)
            assert abs(row["net_return_pct"]-target_profit)<.025, ("control return mismatch",profile,row)
            assert abs(row["max_floating_drawdown_pct"]-dd)<.025, ("control dd mismatch",profile,row)
            assert int(row["profitable_months"])==18 and int(row["trades"])==73, ("control trades/months mismatch",profile,row)
    rule_specs=grid(mode)
    rows=[];monthrows=[]
    for ix,(lock,rule,cap) in enumerate(rule_specs):
        if ix%total!=idx:continue
        for profile in PROFILES:
            name=f"reclaim_NOFLIP_LATE825_MLOSS{cap}__P_{profile}__R_{rule}_SL300_TP3R"
            cfg=(4,"ATRMIN_0p2","PCT",3.,3.0,lock)
            for path in base.PATHS:
                r,mon,trades=sim(df,ema,stline,trend,indicators,name,cfg,signals,path)
                monthly=mon.monthly_return_pct.to_numpy(float)
                r.update(sweep_mode=mode,profile=profile,rule=rule,monthly_loss_cap=cap,lock_rule=lock,
                    losing_months=int((monthly<0).sum()),worst_month_pct=round(float(np.min(monthly)),4),
                    sum_negative_months_pct=round(float(np.minimum(monthly,0).sum()),4))
                mon["profile"]=profile;mon["rule"]=rule;mon["monthly_loss_cap"]=cap;mon["lock_rule"]=lock
                monthrows.append(mon)
                rows.append(r)
                print(f"RESULT {mode} {profile} {rule} {cap} {lock} {path} net={r['net_return_pct']} dd={r['max_floating_drawdown_pct']} winmonths={r['profitable_months']}",flush=True)
    path=OUT/mode/f"shard_{idx}"
    path.mkdir(parents=True,exist_ok=True)
    pd.DataFrame(rows).to_csv(path/"summary.csv",index=False)
    pd.concat(monthrows,ignore_index=True).to_csv(path/"monthly.csv",index=False)
    print("DONE",mode,idx,len(rows),flush=True)

def aggregate(total):
    parts=[];mons=[]
    for mode in ("TRAIL","SIZE"):
        for i in range(total):
            p=OUT/mode/f"shard_{i}"
            parts.append(pd.read_csv(p/"summary.csv",dtype={"profile":str}))
            mons.append(pd.read_csv(p/"monthly.csv",dtype={"profile":str}))
    df=pd.concat(parts,ignore_index=True)
    mo=pd.concat(mons,ignore_index=True)
    df["profile"]=df["profile"].astype(str)
    mo["profile"]=mo["profile"].astype(str)
    df.to_csv(OUT/"full_summary.csv",index=False)
    mo.to_csv(OUT/"full_monthly.csv",index=False)
    rank=df.groupby(["sweep_mode","profile","rule","monthly_loss_cap","lock_rule"],as_index=False).agg(
        max_floating_dd=("max_floating_drawdown_pct","max"),
        min_net_profit=("net_return_pct","min"),
        min_profitable_months=("profitable_months","min"),
        max_losing_months=("losing_months","max"),
        worst_month_pct=("worst_month_pct","min"),
        min_negative_months_sum=("sum_negative_months_pct","min"),
        trades_min=("trades","min"),
        trades_max=("trades","max"))
    rank["minimum_net_required"]=rank.profile.map({p:vals[1] for p,vals in PROFILES.items()})
    rank["original_dd"]=rank.profile.map({p:vals[2] for p,vals in PROFILES.items()})
    rank["passes_profit_months"]=(rank.min_net_profit>=rank.minimum_net_required-.001)&(rank.min_profitable_months>=18)
    rank["strictly_lower_dd"]=rank.passes_profit_months & (rank.max_floating_dd<rank.original_dd-.002)
    rank["below_10_dd"]=rank.passes_profit_months & (rank.max_floating_dd<10)
    rank["below_12_dd"]=rank.passes_profit_months & (rank.max_floating_dd<12)
    rank.sort_values(["profile","max_floating_dd","min_net_profit"],ascending=[True,True,False]).to_csv(OUT/"ranked.csv",index=False)
    report=["# BTCUSD 15M ATR>=0.2% — DRAWDOWN-FIRST independent 80% and 100% sweeps","",
       "Historical 22 IST months January 2025–October 2026, 15m signal / 1m hypothetical OHLC execution (both price orderings).",
       "Exact same entry, 3% initial price SL / 9% TP, unchanged fee+GST+0.02% slippage on both legs, 5-monthly-loss pause except specified variations.",
       "ALL 2025–2026 sample heavily explored in prior research; NO true out-of-sample test, funding and live execution not modeled.",
       "A 'win' requires STRICTLY REDUCING floating max DD while retaining 18+ positive months and **at least the existing improved return** (not just higher profit).",
       "",f"Analyzed {len(rank)} configuration x exposure pairs x both intrabar paths.",
       ""]
    for profile,(exposure,profit,dd) in PROFILES.items():
        subset=rank[rank.profile==profile].copy()
        passes=subset[subset.strictly_lower_dd].sort_values(["max_floating_dd","min_net_profit"],ascending=[True,False])
        partial=subset[subset.passes_profit_months].sort_values(["max_floating_dd","min_net_profit"],ascending=[True,False])
        potential=subset[subset.max_floating_dd<dd-.002].sort_values(["max_floating_dd","min_net_profit"],ascending=[True,False])
        subset.to_csv(OUT/f"profile_{profile}_ranked.csv",index=False)
        report.extend([f"## {profile}% original exposure profile", "",
            f"Reproduced original: +{profit}% net return / {dd}% max FLOATING DD /18/22 winning months /73 trades, for BOTH OHLC paths.",
            f"Strict winners that reduce drawdown without reducing profit/months: {len(passes)}.",
            f"Winners with <10% max floating DD: {int(subset.below_10_dd.sum())}; below 12%: {int(subset.below_12_dd.sum())}.",
            "", "### Valid drawdown improvements",
            passes.head(35).to_markdown(index=False) if len(passes) else "**NONE**: keep original candidate.",
            "", "### Best drawdown among candidates maintaining returns and 18+ positive months",
            partial.head(15).to_markdown(index=False) if len(partial) else "No candidates preserve baseline profit/months.",
            "", "### Drawdown lower but profit/month threshold failed (NOT recommended)",
            potential.head(12).to_markdown(index=False) if len(potential) else "None.",
            ""])
    report.extend(["## Audit limitations","All results are in-sample and overfitting-prone; no independent forward holdout.",
       "Floating DD tracks every 1m OHLC path segment, not close-only drawdown.",
       "Futures funding, real spread/orderbook, liquidation, gap/latency not included; estimated live max DD can be higher.",
       "No live trades, deployments, master merges or production config modifications."])
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")
    print("\n".join(report[:12]),flush=True)
    for p in PROFILES:
        z=rank[(rank.profile==p)&rank.strictly_lower_dd].sort_values(["max_floating_dd","min_net_profit"],ascending=[True,False])
        print("VALID_DD_IMPROVEMENTS",p,len(z),z.head(7).to_dict(orient="records"),flush=True)

if __name__=="__main__":
    count=int(os.environ.get("SHARD_COUNT","16"))
    if len(sys.argv)>1 and sys.argv[1]=="aggregate":aggregate(count)
    else:simulate_shard(int(os.environ.get("SHARD_INDEX","0")),count,os.environ.get("SWEEP_MODE","TRAIL"))
