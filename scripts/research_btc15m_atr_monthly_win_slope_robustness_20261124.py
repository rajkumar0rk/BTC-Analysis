#!/usr/bin/env python3
"""EMA slope duration robustness and 19-20 positive month attempts.

Strictly causal 15-minute signal filters. Two separate research profiles:
80%-max exposure and 100%-max exposure. No locking/deployment.
Preserve at least the historical net profits and max floating drawdowns
of the locked and shortlisted configs. Also score *monthly positive returns
that do not decrease* as a separate, stricter diagnostic. The 22 months
Jan2025-Oct2026 are entirely in sample and heavily mined.
"""
import itertools,os,sys
from pathlib import Path
import numpy as np
import pandas as pd
import research_btc15m_atr_monthly_win_improvement_20261124 as orig

base=orig.base
entry=orig.entry
PROFILES=orig.PROFILES
OUT=Path("analysis/btc15m_atr_monthly_win_slope_robustness_20261124")
LOCK=orig.LOCK
SPECS={"S000":("none",0)}
def add(kind,vals):
    for v in vals:
        SPECS[f"S{len(SPECS):03d}"]=(kind,v)
lengths=[4,6,8,10,12,13,14,15,16,17,18,19,20,21,22,23,24,26,28,32]
add("slope",lengths)
for k,v in itertools.product([10,12,14,15,16,17,18,20,22,24,28],[.2,.4,.6,.8,1.]):
    SPECS[f"S{len(SPECS):03d}"]=("slope_volmin",(k,v))
for k,v in itertools.product([12,14,16,18,20,24],[0,2,5,10]):
    SPECS[f"S{len(SPECS):03d}"]=("slope_rsi_min",(k,v))
for k,v in itertools.product([12,14,16,18,20,24],[.05,.1,.2,.3]):
    SPECS[f"S{len(SPECS):03d}"]=("slope_dist_min",(k,v))
for k,v in itertools.product([12,14,16,18,20,24],["no_monday","no_friday","weekday"]):
    SPECS[f"S{len(SPECS):03d}"]=("slope_time",(k,v))
for k in [4,8,10,12,18,20,24,28]:
    SPECS[f"S{len(SPECS):03d}"]=("slope_16_and_other",k)
for atr in [.25,.3,.35,.4,.5,.6,.8]:
    SPECS[f"S{len(SPECS):03d}"]=("slope_16_atr_max",atr)
for minbody in [.1,.2,.3,.4,.5]:
    SPECS[f"S{len(SPECS):03d}"]=("slope_16_body_min",minbody)
for vmax in [1.,1.5,2.,3.,5.]:
    SPECS[f"S{len(SPECS):03d}"]=("slope_16_vol_max",vmax)
for minabs in [.05,.1,.15,.2,.3]:
    SPECS[f"S{len(SPECS):03d}"]=("slope_16_min_rise_atr",minabs)

def name_code(name):
    return name.split("__Q_",1)[1].split("_SL300",1)[0]

def filtered(fil,side,j,ema,ind,name):
    z=entry.CACHE
    if j<32 or j>=len(z["close"]) or not np.isfinite(z["atr_pct"][j]) or z["atr_pct"][j]<.20:
        return False
    rule=name_code(name)
    if rule not in SPECS:raise ValueError(rule)
    kind,v=SPECS[rule]
    slope=lambda n:side*(ema[j]-ema[j-int(n)])
    if kind=="none":return True
    if kind=="slope":return bool(slope(v)>0)
    if kind=="slope_volmin":return bool(slope(v[0])>0 and z["vol"][j]>=v[1])
    if kind=="slope_rsi_min":return bool(slope(v[0])>0 and side*(z["rsi"][j]-50)>=v[1])
    if kind=="slope_dist_min":return bool(slope(v[0])>0 and side*z["dist_atr"][j]>=v[1])
    if kind=="slope_time":
        k,tm=v;d=int(z["weekday"][j])
        return bool(slope(k)>0 and ((tm=="no_monday" and d!=0) or (tm=="no_friday" and d!=4) or (tm=="weekday" and d<5)))
    if kind=="slope_16_and_other":return bool(slope(16)>0 and slope(v)>0)
    if kind=="slope_16_atr_max":return bool(slope(16)>0 and z["atr_pct"][j]<=v)
    if kind=="slope_16_body_min":return bool(slope(16)>0 and side*z["body"][j]>=v)
    if kind=="slope_16_vol_max":return bool(slope(16)>0 and z["vol"][j]<=v)
    if kind=="slope_16_min_rise_atr":return bool(slope(16)>=v*z["atr"][j])
    raise ValueError((kind,v))

def run(shard,total):
    OUT.mkdir(parents=True,exist_ok=True)
    orig.candidate_entry_filter=filtered
    sim=orig.modified_simulator()
    df,quality=base.read_source("BTCUSD")
    ema,stline,trend,valid=base.st_and_ema(df,base.TF)
    ind=base.make_indicators(df)
    entry.enrich(df,ind,ema)
    signals=base.make_signals(df,ema,trend,valid,"reclaim",4)[0]
    cfg=(4,"ATRMIN_0p2","PCT",3.,3.,LOCK)
    baselines={}
    for profile,z in PROFILES.items():
        for path in base.PATHS:
            name=f"reclaim_NOFLIP_LATE825_MLOSS5__P_{profile}__Q_S000_SL300_TP3R"
            r,mo,led=sim(df,ema,stline,trend,ind,name,cfg,signals,path)
            assert abs(r["net_return_pct"]-z["net"])<.005 and abs(r["max_floating_drawdown_pct"]-z["dd"])<.005 and r["profitable_months"]==18 and r["trades"]==73, ("ORIGINAL DRIFT",profile,path,r)
            baselines[profile,path]=mo
            slope16=next(k for k,v in SPECS.items() if v==("slope",16))
            name=f"reclaim_NOFLIP_LATE825_MLOSS5__P_{profile}__Q_{slope16}_SL300_TP3R"
            r,mo,led=sim(df,ema,stline,trend,ind,name,cfg,signals,path)
            ex={"80":(194.215,10.239),"100":(284.004,12.451)}[profile]
            assert abs(r["net_return_pct"]-ex[0])<.006 and abs(r["max_floating_drawdown_pct"]-ex[1])<.006 and r["profitable_months"]==19 and r["trades"]==71, ("SLOPE16 DRIFT",profile,path,r)
            print("CONTROLS_VERIFIED",profile,path,flush=True)
    rows=[];months=[]
    for i,(rule,spec) in enumerate(SPECS.items()):
        if i%total!=shard:continue
        for profile in PROFILES:
            for path in base.PATHS:
                name=f"reclaim_NOFLIP_LATE825_MLOSS5__P_{profile}__Q_{rule}_SL300_TP3R"
                row,mo,led=sim(df,ema,stline,trend,ind,name,cfg,signals,path)
                old=baselines[profile,path].monthly_return_pct.to_numpy(float)
                now=mo.monthly_return_pct.to_numpy(float)
                positive=old>0
                declines=old[positive]-now[positive]
                row.update(profile=profile,rule=rule,kind=spec[0],parameter=str(spec[1]),
                    positive_months_without_decrease=int(np.sum(declines<=.00001)),
                    total_positive_month_drop_pct=round(float(np.maximum(0,declines).sum()),5),
                    max_previous_positive_month_drop_pct=round(float(np.maximum(0,declines).max()),5),
                    negative_months=int((now<0).sum()),worst_month=round(float(now.min()),5),
                    net_negative_months_sum=round(float(np.minimum(now,0).sum()),5))
                mo["profile"]=profile;mo["rule"]=rule
                rows.append(row);months.append(mo)
                print(f"RESULT prof={profile} {rule} {spec} {path} ret={row['net_return_pct']} dd={row['max_floating_drawdown_pct']} posmonths={row['profitable_months']} prevpospreserved={row['positive_months_without_decrease']}",flush=True)
    path=OUT/f"shard_{shard}"
    path.mkdir(parents=True,exist_ok=True)
    pd.DataFrame(rows).to_csv(path/"summary.csv",index=False)
    pd.concat(months,ignore_index=True).to_csv(path/"monthly.csv",index=False)
    print("SHARD_COMPLETE",shard,len(rows),flush=True)

def aggregate(count):
    out=pd.concat([pd.read_csv(OUT/f"shard_{i}"/"summary.csv",dtype={"profile":str,"rule":str}) for i in range(count)],ignore_index=True)
    monthly=pd.concat([pd.read_csv(OUT/f"shard_{i}"/"monthly.csv",dtype={"profile":str,"rule":str}) for i in range(count)],ignore_index=True)
    out.to_csv(OUT/"summary.csv",index=False)
    monthly.to_csv(OUT/"monthly.csv",index=False)
    agg=out.groupby(["profile","rule","kind","parameter"],as_index=False).agg(
       worst_dd=("max_floating_drawdown_pct","max"),
       min_profit=("net_return_pct","min"),
       min_profitable_months=("profitable_months","min"),
       max_losing_months=("negative_months","max"),
       worst_month=("worst_month","min"),
       worst_sum_negative_months=("net_negative_months_sum","min"),
       min_prev_winning_months_unreduced=("positive_months_without_decrease","min"),
       max_total_prev_winning_month_drop=("total_positive_month_drop_pct","max"),
       max_single_prev_winning_month_drop=("max_previous_positive_month_drop_pct","max"),
       min_trades=("trades","min"))
    agg["net_floor"]=agg.profile.map({p:z["net"] for p,z in PROFILES.items()})
    agg["dd_ceiling"]=agg.profile.map({p:z["dd"] for p,z in PROFILES.items()})
    agg["meets_locked_floor"]=(agg.min_profit>=agg.net_floor-.0001)&(agg.worst_dd<=agg.dd_ceiling+.0001)
    agg["month_19"]=agg.meets_locked_floor & (agg.min_profitable_months>=19)
    agg["month_20"]=agg.meets_locked_floor & (agg.min_profitable_months>=20)
    agg["preserves_all_prev_good_months"]=agg.min_prev_winning_months_unreduced>=18
    agg["strict_all"]=agg.month_19 & agg.preserves_all_prev_good_months
    agg["meets_prior_slope16_result"]=agg.apply(lambda r:r.min_profit>=({"80":194.215,"100":284.004}[r.profile]-.01) and r.worst_dd<=({"80":10.239,"100":12.451}[r.profile]+.001),axis=1)
    agg.to_csv(OUT/"ranked.csv",index=False)
    txt=["# BTCUSD 15m ATR >=0.20% — 15m EMA20 slope stability vs MONTHLY consistency",
         "",f"{len(agg)} profile/slope combinations, checked in both 1m price orderings; Jan 2025–Oct 2026 (22 IST months, in sample).",
         "Locked base profiles: 80% +185.0292% / 10.465% max floating DD / 18 months; 100% +266.1034% /12.916% DD/18 months.",
         "New prior slope16 candidates: 80% +194.215% /10.239% DD/19 months; 100% +284.004%/12.451% DD/19 months.",
         "All signals use 15m close and earlier only, 1m OHLC simulated two bar paths; fixed SL3% TP9%, +8% activate +2% lock, original tiered sizing.",
         "Trading fees 0.05% taker per side +GST18%, slippage 0.02% price per side. Not including funding/real depth/liquidation.",
         "HARD FLOORS: Never lower total compounded return or raise floating DD versus each original profile. Report separate harsher requirement to preserve the returns of EACH originally profitable month.",
         "Data mined repeatedly, so the tuned lookback values may be fitting specific past months. NOT a forward edge.",
         ""]
    for prof in PROFILES:
        z=agg[agg.profile==prof]
        best20=z[z.month_20].sort_values(["min_profitable_months","worst_dd","min_profit"],ascending=[False,True,False])
        best19=z[z.month_19].sort_values(["worst_dd","min_profit"],ascending=[True,False])
        strict=z[z.strict_all].sort_values(["min_profitable_months","worst_dd"],ascending=[False,True])
        candidate=z[z.month_19 & z.meets_prior_slope16_result].sort_values(["min_profitable_months","worst_dd","min_profit"],ascending=[False,True,False])
        z.to_csv(OUT/f"profile_{prof}.csv",index=False)
        txt.extend([f"## {prof}% maximum exposure separately","",
          f">=20 profitable months and no overall profit/DD regression: {len(best20)}",
          best20.head(30).to_markdown(index=False) if len(best20) else "**None**.",
          f">=19 profitable months and no profit/DD regression: {len(best19)}",
          best19.head(30).to_markdown(index=False) if len(best19) else "**None**.",
          f"Preserves EVERY previously profitable month's absolute monthly return (>=18) while reaching >=19 and preserving total profit/DD: {len(strict)}",
          strict.head(20).to_markdown(index=False) if len(strict) else "**None**.",
          f"Better or equal to the slope16 candidate's new profit/DD, with >=19 months: {len(candidate)}",
          candidate.head(20).to_markdown(index=False) if len(candidate) else "**None**.",
          ""])
    txt.extend(["## Caveat","This is another parameter sweep on the same repeatedly reused 22 months. Use unseen forward validation, 1m path-sensitive fills and real fees/funding before real money."])
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(txt)+"\n")
    print("\n".join(txt[:11]))
    for p in PROFILES:
        z=agg[agg.profile==p]
        print("SUMMARY",p,"19+",len(z[z.month_19]),"20+",len(z[z.month_20]),"strict_win_months",len(z[z.strict_all]),flush=True)

if __name__=="__main__":
    n=int(os.environ.get("SHARD_COUNT","16"))
    if len(sys.argv)>1 and sys.argv[1]=="aggregate":aggregate(n)
    else:run(int(os.environ.get("SHARD_INDEX","0")),n)
