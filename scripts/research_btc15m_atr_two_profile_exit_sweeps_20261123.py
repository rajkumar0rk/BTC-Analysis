#!/usr/bin/env python3
"""Independent objective-constrained exit improvements for BTCUSD 15M ATR >= .20%.

Two distinctly ranked research profiles: global exposure .80 and 1.00.
All 15m signals and ATR filter unchanged. Same 1m original fills/fees/GST/
slippage, 5-losing-exit IST month pause and tiered after-loss sizing.
All 22 months Jan 2025–Oct 2026 are in-sample, extensively reused.
"""
import os, sys
from pathlib import Path
import numpy as np
import pandas as pd
import research_btc15m_regime_entry_dd_20261123 as entry

base=entry.base
OUT=Path("analysis/btc15m_atr_two_profile_exit_sweeps_20261123")
BASE_TIER=entry.tiered_size
BASELINES={"80":(163.492,11.879), "100":(229.037,14.740)}
PROFILES={"80":0.80,"100":1.0}
FILTER="ATRMIN_0p2"
NAME_FORMAT="reclaim_NOFLIP_LATE825_MLOSS5__U_{scale}__SZ_T65_30_10_SL300_TP3R"

def sized(name,losses):
    scale=int(name.split("__U_",1)[1].split("__SZ_",1)[0])/1000.0
    assert 0<scale<=1.0
    return scale*BASE_TIER(name,losses)

def combo_grid(kind):
    if kind=="SLTP":
        # Stop loss and target are independently varied, NOT fixed 1:3 R.
        return [(f"SL{s:g}_TP{t:g}",float(s),float(t),8.25,0.,2.,.5)
                for s in [2.,2.25,2.5,2.75,3.,3.25,3.5,3.75,4.]
                for t in [6.,7.,8.,9.,10.,11.,12.,13.]]
    if kind=="LOCK":
        # Fixed 3% initial SL, 9% TP; vary early trade profit protection.
        return [(f"A{a:g}_L{lock:g}_D{step:g}_I{inc:g}",3.,9.,float(a),float(lock),float(step),float(inc))
                for a in [3.,4.,5.,6.,7.,7.5,8.,8.25,8.5]
                for lock in [0.,.5,1.,2.,3.]
                for step,inc in [(1.,.25),(2.,.5)]
                if lock<=a]
    raise ValueError(kind)

def cfg_of(rule):
    key,sl,tp,activate,lock,distance,step=rule
    assert sl>0 and tp>0 and 0<=lock<=activate and distance>0 and step>0
    return (4,FILTER,"PCT",sl,tp/sl,f"LATE:{activate}:{lock}:{distance}:{step}")

def enrich_metrics(row,mon,kind,profile,rule):
    r=dict(row)
    monthly=mon.monthly_return_pct.to_numpy(float)
    assert len(monthly)==22
    r.update(
      sweep=kind,exposure_profile=profile,
      rule=rule[0],stop_pct=rule[1],tp_pct=rule[2],
      protection_activate_pct=rule[3],protection_first_lock_pct=rule[4],
      protection_step_distance_pct=rule[5],protection_increment_pct=rule[6],
      negative_months=int((monthly<0).sum()),
      zero_months=int((monthly==0).sum()),
      worst_month_pct=round(float(np.min(monthly)),5),
      worst_month_name=mon.month_ist.iloc[int(np.argmin(monthly))],
      sum_losing_months_pct=round(float(np.minimum(monthly,0).sum()),5),
      mean_positive_month_pct=round(float(monthly[monthly>0].mean()),5) if np.any(monthly>0) else np.nan,
    )
    return r

def run(shard,count,sweep):
    OUT.mkdir(parents=True,exist_ok=True)
    entry.tiered_size=sized
    sim=entry.modified_simulator()
    df,quality=base.read_source("BTCUSD")
    ema,stline,trend,valid=base.st_and_ema(df,base.TF)
    ind=base.make_indicators(df)
    entry.enrich(df,ind,ema)
    signals=base.make_signals(df,ema,trend,valid,"reclaim",4)[0]
    # Fail closed if original backtest changes; test BOTH baseline profiles and BOTH paths.
    control=( "BASE_SL3_TP9_A825_L0",3.,9.,8.25,0.,2.,.5)
    for profile in PROFILES:
        for path in base.PATHS:
            name=NAME_FORMAT.format(scale=int(round(PROFILES[profile]*1000)))
            row,mon,ledger=sim(df,ema,stline,trend,ind,name,cfg_of(control),signals,path)
            want_net,want_dd=BASELINES[profile]
            assert abs(row["net_return_pct"]-want_net)<.02, ("baseline profit",profile,path,row)
            assert abs(row["max_floating_drawdown_pct"]-want_dd)<.02, ("baseline drawdown",profile,path,row)
            assert int(row["trades"])==71 and int(row["profitable_months"])==18, (profile,path,row)
    rules=combo_grid(sweep)
    result=[];months=[]
    for n,rule in enumerate(rules):
        if n%count!=shard: continue
        for profile,ratio in PROFILES.items():
            name=NAME_FORMAT.format(scale=int(round(ratio*1000)))
            cfg=cfg_of(rule)
            for path in base.PATHS:
                row,mon,ledger=sim(df,ema,stline,trend,ind,name,cfg,signals,path)
                result.append(enrich_metrics(row,mon,sweep,profile,rule))
                mon["sweep"]=sweep;mon["exposure_profile"]=profile;mon["rule"]=rule[0]
                months.append(mon)
                print(f"RESULT sweep={sweep} profile={profile} rule={rule[0]} path={path} net={row['net_return_pct']} dd={row['max_floating_drawdown_pct']} month={row['profitable_months']}",flush=True)
    p=OUT/sweep/f"shard_{shard}"
    p.mkdir(parents=True,exist_ok=True)
    pd.DataFrame(result).to_csv(p/"summary.csv",index=False)
    pd.concat(months,ignore_index=True).to_csv(p/"monthly.csv",index=False)
    print(f"SWEEP_SHARD_DONE {sweep} {shard} {len(result)}",flush=True)

def aggregate(count):
    allsummary=[];allmonths=[]
    for sweep in ["SLTP","LOCK"]:
        for i in range(count):
            p=OUT/sweep/f"shard_{i}"
            allsummary.append(pd.read_csv(p/"summary.csv"))
            allmonths.append(pd.read_csv(p/"monthly.csv"))
    s=pd.concat(allsummary,ignore_index=True)
    # CSV inference converts string profile labels '80'/'100' to ints; normalize before grouping.
    s['exposure_profile']=s['exposure_profile'].astype(str)
    months=pd.concat(allmonths,ignore_index=True)
    months['exposure_profile']=months['exposure_profile'].astype(str)
    s.to_csv(OUT/"all_summaries.csv",index=False)
    months.to_csv(OUT/"all_months.csv",index=False)
    score=s.groupby(["sweep","exposure_profile","rule","stop_pct","tp_pct",
                     "protection_activate_pct","protection_first_lock_pct",
                     "protection_step_distance_pct","protection_increment_pct"],as_index=False).agg(
        worst_path_max_dd=("max_floating_drawdown_pct","max"),
        worse_path_profit=("net_return_pct","min"),
        min_winning_months=("profitable_months","min"),
        max_losing_months=("negative_months","max"),
        worst_month_pct=("worst_month_pct","min"),
        worst_sum_losing_months_pct=("sum_losing_months_pct","min"),
        min_trades=("trades","min"),
        max_trades=("trades","max"),
        min_profit_factor=("profit_factor","min"),
        max_fees_gst=("fees_gst_usd","max"),
    )
    targets=score.exposure_profile.map({"80":BASELINES["80"][0],"100":BASELINES["100"][0]})
    ddtargets=score.exposure_profile.map({"80":BASELINES["80"][1],"100":BASELINES["100"][1]})
    score["dominates"]=(score.worse_path_profit>=targets-.001)&(score.worst_path_max_dd<=ddtargets+.001)&(score.min_winning_months>=18)&(
      (score.worse_path_profit>targets+.01)|(score.worst_path_max_dd<ddtargets-.01)|(score.min_winning_months>18))
    score["strict_both"]=(score.worse_path_profit>targets+.01)&(score.worst_path_max_dd<ddtargets-.01)&(score.min_winning_months>=18)
    score["profit_not_lower_dd_lower"]=(score.worse_path_profit>=targets-.001)&(score.worst_path_max_dd<ddtargets-.01)&(score.min_winning_months>=18)
    score["more_win_months"]=(score.worse_path_profit>=targets-.001)&(score.worst_path_max_dd<=ddtargets+.001)&(score.min_winning_months>18)
    score.sort_values(["exposure_profile","worst_path_max_dd","worse_path_profit"],ascending=[True,True,False]).to_csv(OUT/"ranked.csv",index=False)
    lines=[
      "# BTCUSD 15M, ATR>=0.20% — INDEPENDENT 80% and 100% strategy improvements",
      "",
      f"Two distinct profiles; {len(score)} profile-specific configurations = {len(score)//2} exit rules across two simulated intraminute OHLC order paths.",
      "Fully confirmed BTCUSD 15M entries, with 1m exit replay, ST(10,3)/EMA20 reclaim, ATR>=0.20%.",
      "5-loss monthly entry pause, exposure-based tiering, modeled 0.05% taker fee per side+18% GST, adverse 0.02% per side.",
      "Jan 2025–Oct 2026 22 IST months ALREADY REPEATEDLY MINED; this is in-sample optimization, NOT independent evidence.",
      "Funding, live spread, latency, orderbook impact and liquidation are NOT modeled.",
      "SLTP: independently adjust % stop and % target while holding profit-lock definition fixed. LOCK: adjust activation/lock/step while keeping SL3%/TP9%.",
      "",
    ]
    for profile,exposure in PROFILES.items():
        ret,dd=BASELINES[profile]
        sub=score[score.exposure_profile==profile].copy()
        winners=sub[sub.dominates].sort_values(["worst_path_max_dd","worse_path_profit"],ascending=[True,False])
        both=sub[sub.strict_both].sort_values(["worst_path_max_dd","worse_path_profit"],ascending=[True,False])
        win_month=sub[sub.more_win_months].sort_values(["min_winning_months","worst_path_max_dd","worse_path_profit"],ascending=[False,True,False])
        atleast=sub[(sub.min_winning_months>=18)&(sub.worse_path_profit>=ret-.001)].sort_values(["worst_path_max_dd","worse_path_profit"],ascending=[True,False])
        sub.to_csv(OUT/f"profile_{profile}_ranked.csv",index=False)
        lines.extend([
          f"## Separate profile: {profile}% global notional",
          "",
          f"BASELINE verified in every shard and both paths: {ret:.3f}% net, {dd:.3f}% floating DD, 18/22 winning months, 71 trades.",
          f"Dominates baseline (no worse profit, DD, months): {len(winners)}; STRICT profit + DD improvement: {len(both)}.",
          f"Meets no-degradation requirement and improves winning-month count: {len(win_month)}.",
          "",
          "### Profitable and lower-drawdown solutions (best DD first)",
          winners.head(30).to_markdown(index=False) if len(winners) else "No qualifying result.",
          "",
          "### Improves profit AND drawdown",
          both.head(25).to_markdown(index=False) if len(both) else "No qualifying result.",
          "",
          "### More positive months without profit/drawdown deterioration",
          win_month.head(15).to_markdown(index=False) if len(win_month) else "None.",
          "",
          "### Lowest-DD models retaining baseline profit and >=18 positive months",
          atleast.head(20).to_markdown(index=False) if len(atleast) else "None.",
          "",
        ])
    lines.extend(["## Audit notes",
      "Stats use worst observed drawdown and minimum observed net profit across both price-path approximations.",
      "More positive months from repeatedly tuning on the same months is especially overfit-prone.",
      "No outcome is an actionable forward performance prediction. Verify on unseen data and realistic fills before risking money."])
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(lines)+"\n")
    print("\n".join(lines[:9]))
    for profile in PROFILES:
        sub=score[(score.exposure_profile==profile)&(score.dominates)].sort_values(["worst_path_max_dd","worse_path_profit"],ascending=[True,False])
        print("QUALIFIED",profile,len(sub))
        print(sub.head(6).to_string(index=False))

if __name__=="__main__":
    count=int(os.environ.get("SHARD_COUNT","16"))
    if len(sys.argv)>1 and sys.argv[1]=="aggregate":aggregate(count)
    else:run(int(os.environ.get("SHARD_INDEX","0")),count,os.environ.get("SWEEP_TYPE","SLTP"))
