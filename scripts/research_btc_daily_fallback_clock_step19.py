#!/usr/bin/env python3
"""Step19: causal forced BTC daily 21h fallback micro-delay entry test.

All event trades unchanged; any fallback time shift is decided at 21:00 IST
using PRE-21:00 completed 1m candles, with frozen Step11 side and unchanged
Step13/A/B exit recipes. One full 1x BTCUSD trade every 477 IST weekdays.
Select rules on 2025 ONLY. 2026 already heavily research-exposed.
"""
from pathlib import Path
from itertools import product
import json
import numpy as np
import pandas as pd

import research_btc_every_weekday_reset_step1 as base
import research_btc_daily_monthly_exit_step13 as step13
import research_btc_daily_monthly_two_regime_step15 as step15
import research_btc_daily_exit_invalidation_step7 as early

OUT=Path("analysis/btc_daily_fallback_clock_step19")
N=len(base.DAYS);TRAIN=base.NTRAIN
MONTHS=np.asarray(base.MONTH_LABELS)
DELAYS=(5,10,15,20,30,45,60)
RULES={
 "always":(None,),
 "low_vol":(.75,1.),
 "high_vol":(1.25,1.75),
 "against_60m":(.0015,.003),
 "with_60m":(.0015,.003),
 "wide60":(.005,.009),
 "large5":(.001,.002),
 "range_edge":(.8,.9),
 "against5":(.0005,.0015),
}
FAMILIES={
 "Step13_official":("none","baseline","none","baseline"),
 "A_20months_hindsight":(
   "mtd_not_positive","adverse_cut_0.08pct_after_10m",
   "peak_ge_plus1_and_giveback050","profit_close_at_0.1pct_after_10m"),
 "B_21months_hindsight":(
   "mtd_not_positive","adverse_cut_0.08pct_after_10m",
   "mtd_at_least_plus1","profit_close_at_0.1pct_after_10m")
}
ALL_GATES=[(rule,level,value) for rule,values in RULES.items()
               for level,value in enumerate(values)]
assert len(ALL_GATES)==17 and 17*len(DELAYS)==119 and N==477 and TRAIN==260

def info_at_21(m,idx,side):
    op=m.open.to_numpy(float)
    cl=m.close.to_numpy(float)
    hi=m.high.to_numpy(float)
    lo=m.low.to_numpy(float)
    vol=m.volume.to_numpy(float)
    data=dict(r5=np.zeros(N),r60=np.zeros(N),rv=np.zeros(N),
              span=np.zeros(N),pos=np.zeros(N))
    for d,i0 in enumerate(idx):
        i=int(i0)
        last=float(cl[i-1])
        data["r5"][d]=last/op[i-5]-1
        data["r60"][d]=last/op[i-60]-1
        prev5=vol[i-105:i-5].reshape(20,5).sum(axis=1)
        avg=float(prev5.mean())
        data["rv"][d]=float(np.sum(vol[i-5:i])/avg) if avg>0 else 0.
        up=float(np.max(hi[i-60:i]))
        low=float(np.min(lo[i-60:i]))
        data["span"][d]=(up-low)/op[i]
        data["pos"][d]=(last-low)/(up-low) if up>low else .5
    if any(not np.isfinite(v).all() for v in data.values()):
        raise AssertionError("Invalid prior complete minute indicator")
    return data

def trigger(rule,level,data,side):
    threshold=RULES[rule][level]
    r60=data["r60"]
    r5=data["r5"]
    if rule=="always":return np.ones(N,dtype=bool)
    if rule=="low_vol":return data["rv"]<=threshold
    if rule=="high_vol":return data["rv"]>=threshold
    if rule=="against_60m":return side*r60<=-threshold
    if rule=="with_60m":return side*r60>=threshold
    if rule=="wide60":return data["span"]>=threshold
    if rule=="large5":return np.abs(r5)>=threshold
    if rule=="range_edge":
        return (data["pos"]<=1-threshold)|(data["pos"]>=threshold)
    if rule=="against5":return side*r5<=-threshold
    raise KeyError(rule)

def replay(m,start,side,cfg,policies):
    return early.replay_with_nextbar_exits(
        m.open.to_numpy(float),m.high.to_numpy(float),
        m.low.to_numpy(float),m.close.to_numpy(float),
        start,side,cfg,policies,base.COST,base.SLIP
    )

def family(raw,mask,params,ids):
    dec=step15.replay_one(raw,mask,ids["profit_close_at_0.1pct_after_20m"],params,ids)
    metrics={}
    for mi,mode in enumerate(base.MODES):
        p=step15.getout(raw,dec[0],mi)
        metrics[mode]=step15.score(p)
    return dec,metrics

def save_full(family_label,raw,choice,idx,base_idx,hh,sd,mask):
    summary={}
    for mi,mode in enumerate(base.MODES):
        p=step15.getout(raw,choice[0],mi)
        # Save entry minute, explicit year month and exit timeline, no
        # skipped dates permitted.
        shifted_minutes=(idx-base_idx).astype(int)
        actual_hours=hh+shifted_minutes//60
        led,month=step15.saved_ledger(
           p,choice[0],choice[1],choice[2],idx,actual_hours,sd,mask,mode
        )
        led["entry_minute_ist"]=(shifted_minutes%60).astype(int)
        led["delayed_fallback_entry"]=mask&(idx!=base_idx)
        if len(led)!=477 or led.day_ist.nunique()!=477:
            raise AssertionError("Missing daily trade")
        led.to_csv(OUT/(family_label+"_"+mode+"_selected_477_daily.csv"),index=False)
        month.to_csv(OUT/(family_label+"_"+mode+"_selected_22_months.csv"),index=False)
        z=step15.score(p)
        summary[mode]=dict(
            metrics=z,
            winning_months=int(np.sum(month.net_compounded_pct>0)),
            losing_months=month.loc[month.net_compounded_pct<=0,
                 ["month_ist","net_compounded_pct"]].to_dict("records"))
    return summary

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    m,ctx,mask,fb,sd,hh,base_idx,cfg=step13.create_path()
    policies,names=early.build_exit_policies()
    ids={name:i for i,name in enumerate(names)}
    originalraw=replay(m,base_idx,sd,cfg,policies)
    step13.check_parity(originalraw,ctx,fb)
    baseline={fam:family(originalraw,mask,params,ids)
              for fam,params in FAMILIES.items()}
    for fam,net,winmonths in (
       ("Step13_official",23.261256,19),
       ("A_20months_hindsight",24.648136,20),
       ("B_21months_hindsight",22.480405,21)
    ):
        z=baseline[fam][1]["scalper_offer"]
        if abs(z["net_total_pct"]-net)>.00011 or z["win_months_all"]!=winmonths:
            raise AssertionError("Exact unchanged family baseline parity failure")
    print("STEP19_BASELINES "+json.dumps({k:v[1] for k,v in baseline.items()},sort_keys=True),flush=True)

    features=info_at_21(m,base_idx,sd)
    rows=[]
    for fam in FAMILIES:
        for mode in base.MODES:
            rows.append(dict(
              family=fam,rule="baseline",threshold_level=-1,
              threshold_value=None,delay_minutes=0,
              fallback_positions_delayed=0,cost_model=mode,
              **baseline[fam][1][mode]))
    candidates={}
    for rule,lev,lim in ALL_GATES:
        matched=trigger(rule,lev,features,sd)&mask
        nmatch=int(matched.sum())
        for lag in DELAYS:
            start=base_idx.copy()
            start[matched]+=lag
            if len(start)!=477 or np.any(start-base_idx>60):
                raise AssertionError("Fallback missed mandatory weekday")
            current=replay(m,start,sd,cfg,policies) if nmatch else originalraw
            for fam,params in FAMILIES.items():
                dec,z=family(current,mask,params,ids)
                candidates[(fam,rule,lev,lag)]=z
                for mode in base.MODES:
                    rows.append(dict(
                        family=fam,rule=rule,
                        threshold_level=lev,threshold_value=lim,
                        delay_minutes=lag,
                        fallback_positions_delayed=nmatch,
                        cost_model=mode,
                        **z[mode]))
            print("STEP19_PROGRESS "+json.dumps(dict(
                trigger=rule,level=lev,delay_minutes=lag,
                affected=nmatch,scenarios_completed=len(candidates)//3)),flush=True)

    matrix=pd.DataFrame(rows)
    if len(matrix)!=720 or not matrix.trades.eq(477).all():
        raise AssertionError("One BTC weekday trade missing")
    matrix.to_csv(OUT/"all_119_fallback_clock_policies_three_families_two_fee_models.csv",index=False)
    print("STEP19_GRID "+json.dumps(dict(
       clock_policies=119,total_backtests=360,both_fee_results=720,
       trades_per_model=477)),flush=True)

    offer=matrix[matrix.cost_model=="scalper_offer"]
    selected={}
    for fam in FAMILIES:
        original=baseline[fam][1]["scalper_offer"]
        samples=offer[(offer.family==fam)&(offer.rule!="baseline")]
        want=11 if fam=="Step13_official" else 12
        qualified=samples[(samples.win_months_2025>=want)&
           (samples.return_2025_pct>=original["return_2025_pct"]-1.e-6)&
           (samples.profitable_days_2025>=original["profitable_days_2025"])&
           (samples.max_dd_2025<=original["max_dd_2025"]+1e-4)]
        if len(qualified):
            rank=qualified.sort_values(["win_months_2025",
              "return_2025_pct","profitable_days_2025","max_dd_2025"],
              ascending=[False,False,False,True]).iloc[0].to_dict()
            rule=rank["rule"]
            lev=int(rank["threshold_level"])
            lag=int(rank["delay_minutes"])
            affected=mask&trigger(rule,lev,features,sd)
            idx=base_idx.copy()
            idx[affected]+=lag
            raw=replay(m,idx,sd,cfg,policies)
            dec,score=family(raw,mask,FAMILIES[fam],ids)
            frozen=dict(rule=rule,threshold=RULES[rule][lev],
                delay_minutes=lag,
                delayed_fallback_trades=int(affected.sum()),
                months_2025_selected=int(rank["win_months_2025"]))
        else:
            idx=base_idx.copy()
            raw=originalraw
            dec,score=baseline[fam]
            frozen=dict(rule="baseline",threshold=None,delay_minutes=0,
                delayed_fallback_trades=0,
                months_2025_selected=int(original["win_months_2025"]))
        metrics=save_full(fam,raw,dec,idx,base_idx,hh,sd,mask)
        selected[fam]=dict(
           eligible_2025_models=int(len(qualified)),
           frozen_2025_rule=frozen,
           evaluated_with_2026_research_exposed=metrics,
           delta_months_vs_baseline=int(metrics["scalper_offer"]["metrics"]["win_months_all"]-
                                          original["win_months_all"]),
           delta_net_vs_baseline=round(metrics["scalper_offer"]["metrics"]["net_total_pct"]-
                                          original["net_total_pct"],6))
        print("STEP19_SELECTED_"+fam.upper()+" "+
            json.dumps(selected[fam],sort_keys=True),flush=True)

    hindsight=offer[offer.win_months_all==22].sort_values(
      ["net_total_pct","max_closed_dd_pct"],ascending=[False,True])
    hindsight.to_csv(OUT/"hindsight_only_22_of_22_clock_variants.csv",index=False)
    results=dict(
       experiment="BTCUSD 21 IST fallback delay scheduled using only information known at 21 IST",
       calendar="Jan2025-Oct2026, exactly 477 full IST Mon-Fri dates",
       entry_direction="Frozen Step11 side learned only from prior completed weekdays, no future lookahead",
       full_daily_1x_notional=True,
       model_count=360,fee_scenarios=720,
       original_baselines={k:v[1] for k,v in baseline.items()},
       official_2025_only_selection=selected,
       retrospectively_hindsight_22_month_positive_count=int(len(hindsight)),
       hindsight_22_month_highest_net_NOT_SELECTED=(
           hindsight.iloc[0].to_dict() if len(hindsight) else None),
       economics="0.05% taker per side plus GST18% / assumed prior-activated regular Scalper <=30m closing fee waiver; 5 BTCUSD price points adverse slip per leg",
       caveats=[
           "2026 has been repeatedly research-exposed; NOT independent holdout",
           "A/B original policy families were also found via 2026 hindsight",
           "Many strategy optimizations lead to selection bias; 22/22 past months would not guarantee future",
           "Real historical fee offer, spread, market impact, funding and tick sequence unavailable"])
    (OUT/"summary.json").write_text(json.dumps(results,indent=2)+"\n")
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join([
      "# BTCUSD Step19— predeclared mandatory fallback entry micro-delays",
      "",
      "Every variant trades exactly once on every 477 full IST weekday with full account notional and original historical direction. Fallback timing is decided at 21:00 using COMPLETED pre-21:00 candles. Any delayed entry is mandatory regardless of later price action.",
      "",
      "## Original parity benchmarks",json.dumps({k:v[1] for k,v in baseline.items()},indent=2),
      "",
      "## 2025-only selections, Jan–Oct2026 historical check",json.dumps(selected,indent=2),
      "",
      "## Full-period retrospective 22/22 count",str(len(hindsight)),
      "",
      "## Model B 22-month ledger",
      pd.read_csv(OUT/"B_21months_hindsight_scalper_offer_selected_22_months.csv").to_markdown(index=False),
      "",
      "## Research warnings",
      "Prior attempts mined same 22 months many times. This is historical research under a hypothetical historical fee offer, not robust proven forward results."
    ])+"\n")
    print("STEP19_COMPLETE "+json.dumps(dict(
        clock_policies=119,total_22_month_hindsight=len(hindsight),
        selected={k:v["evaluated_with_2026_research_exposed"]["scalper_offer"] for k,v in selected.items()}),
        sort_keys=True),flush=True)

if __name__=="__main__":
    main()
