#!/usr/bin/env python3
"""Step18: preentry volatility/volume conditioned SL caps, mandatory BTC weekdays.

Regressive exact Step13, Step15 A/B at 1m, then 180 fixed causal masks x
three frozen families. Selection uses 2025 ONLY. 2026 has been researched
already and is not independent forward OOS. No skipped/extra/smaller trades.
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

OUT=Path("analysis/btc_daily_preentry_risk_step18")
N=len(base.DAYS)
TRAIN=base.NTRAIN
MONTHS=np.asarray(base.MONTH_LABELS)
RULES={
 "low_rvol5":(.65,.90),
 "high_rvol5":(1.25,1.75),
 "wide_range60":(.005,.009),
 "tight_range60":(.003,.005),
 "against60":(.0015,.003),
 "with60":(.0015,.003),
 "big_abs5":(.001,.002),
 "counter5":(.0005,.0015),
 "edge_against":(.80,.90),
}
SCOPES=("fallback","both")
CAPS=(.15,.20,.25,.30,.40)
FAMILIES={
 "Step13_official":("none","baseline","none","baseline"),
 "A_20months_hindsight":(
   "mtd_not_positive","adverse_cut_0.08pct_after_10m",
   "peak_ge_plus1_and_giveback050","profit_close_at_0.1pct_after_10m"),
 "B_21months_hindsight":(
   "mtd_not_positive","adverse_cut_0.08pct_after_10m",
   "mtd_at_least_plus1","profit_close_at_0.1pct_after_10m")
}
assert N==477 and TRAIN==260 and len(RULES)*2*len(SCOPES)*len(CAPS)==180

def preentry_features(m,starts,sides):
    op=m.open.to_numpy(float)
    close=m.close.to_numpy(float)
    hi=m.high.to_numpy(float)
    lo=m.low.to_numpy(float)
    vol=m.volume.to_numpy(float)
    r5=np.zeros(N)
    r60=np.zeros(N)
    r240=np.zeros(N)
    volume_ratio=np.zeros(N)
    range60=np.zeros(N)
    loc60=np.zeros(N)
    for d,index in enumerate(starts):
        i=int(index)
        latest=float(close[i-1])
        mid=float(op[i])
        r5[d]=latest/op[i-5]-1
        r60[d]=latest/op[i-60]-1
        r240[d]=latest/op[i-240]-1
        earlier=vol[i-105:i-5].reshape(20,5).sum(axis=1)
        mean=float(np.mean(earlier))
        volume_ratio[d]=float(np.sum(vol[i-5:i])/mean) if mean>0 else 0.
        high=float(np.max(hi[i-60:i]))
        low=float(np.min(lo[i-60:i]))
        range60[d]=(high-low)/mid
        loc60[d]=(latest-low)/(high-low) if high>low else .5
    info=dict(r5=r5,r60=r60,r240=r240,rvol5=volume_ratio,
              range60=range60,loc60=loc60)
    for name,x in info.items():
        if len(x)!=477 or not np.isfinite(x).all():
            raise AssertionError(f"Noncausal/nonfinite preentry feature {name}")
    return info

def risk_trigger(rule,level,features,side):
    threshold=RULES[rule][level]
    rv=features["rvol5"]
    rt=features["r60"]
    rr=features["range60"]
    r5=features["r5"]
    loc=features["loc60"]
    if rule=="low_rvol5":condition=rv<=threshold
    elif rule=="high_rvol5":condition=rv>=threshold
    elif rule=="wide_range60":condition=rr>=threshold
    elif rule=="tight_range60":condition=rr<=threshold
    elif rule=="against60":condition=(side*rt)<=-threshold
    elif rule=="with60":condition=(side*rt)>=threshold
    elif rule=="big_abs5":condition=np.abs(r5)>=threshold
    elif rule=="counter5":condition=(side*r5)<=-threshold
    elif rule=="edge_against":
        condition=((side<0)&(loc>=threshold)) | (
                     (side>0)&(loc<=1-threshold))
    else:raise KeyError(rule)
    if condition.dtype!=bool or condition.shape!=(N,):
        raise AssertionError("Wrong pretrade condition")
    return condition

def evaluate_family(raw,mask,baselineid,params,ids):
    choices=step15.replay_one(raw,mask,baselineid,params,ids)
    by_fee={}
    for i,mode in enumerate(base.MODES):
        p=step15.getout(raw,choices[0],i)
        by_fee[mode]=step15.score(p)
    return choices,by_fee

def monthly_details(path,choice,ctx,m,side,mask,hour,index,mode):
    ledger,months=step15.saved_ledger(
        path,choice[0],choice[1],choice[2],
        index,hour,side,mask,mode)
    assert len(ledger)==477 and len(months)==22
    return ledger,months

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    m,ctx,mask,fb,side,hour,index,cfg=step13.create_path()
    policy,policy_names=early.build_exit_policies()
    ids={name:i for i,name in enumerate(policy_names)}
    baseid=ids["profit_close_at_0.1pct_after_20m"]
    raw_original=early.replay_with_nextbar_exits(
        m.open.to_numpy(float),m.high.to_numpy(float),
        m.low.to_numpy(float),m.close.to_numpy(float),
        index,side,cfg,policy,base.COST,base.SLIP)
    original_step11=step13.check_parity(raw_original,ctx,fb)
    original={family:evaluate_family(raw_original,mask,baseid,params,ids)
              for family,params in FAMILIES.items()}
    baseline={family:tupled[1] for family,tupled in original.items()}
    for family,expected,expected_months in (
        ("Step13_official",23.261256,19),
        ("A_20months_hindsight",24.648136,20),
        ("B_21months_hindsight",22.480405,21)
    ):
        z=baseline[family]["scalper_offer"]
        if z["win_months_all"]!=expected_months or (
            abs(z["net_total_pct"]-expected)>0.00011):
            raise AssertionError(f"Baseline parity failed for {family}")
    print("STEP18_BASELINES "+json.dumps(baseline,sort_keys=True),flush=True)
    feat=preentry_features(m,index,side)
    rows=[]
    # Exactly three baseline variants, included in 2025 family selection.
    for family in FAMILIES:
        for mode in base.MODES:
            rows.append(dict(family=family,rule="baseline",threshold_level=-1,
                threshold_value=None,scope="none",initial_stop_cap_pct=None,
                risk_condition_days=0,actual_stops_shrunk=0,cost_model=mode,
                **baseline[family][mode]))
    results={}
    condition_counts={}
    for rule,level,scope,cap in product(RULES,(0,1),SCOPES,CAPS):
        condition=risk_trigger(rule,level,feat,side)
        selected=condition&mask if scope=="fallback" else condition
        cfg_variant=cfg.copy()
        cfg_variant[selected,1]=np.minimum(cfg_variant[selected,1],cap)
        assert np.all(cfg_variant[:,1]<=cfg[:,1]+1e-12)
        shrunk=int(np.sum(cfg_variant[:,1]<cfg[:,1]-1e-12))
        valid=int(np.sum(selected))
        if shrunk==0:
            # Record even duplicates so the PREdeclared grid is exhaustive.
            raw=raw_original
        else:
            raw=early.replay_with_nextbar_exits(
                m.open.to_numpy(float),m.high.to_numpy(float),
                m.low.to_numpy(float),m.close.to_numpy(float),
                index,side,cfg_variant,policy,base.COST,base.SLIP)
        setting=(rule,level,scope,cap)
        condition_counts[str(setting)]=dict(matched=valid,narrowed=shrunk)
        for family,params in FAMILIES.items():
            dec,sc=evaluate_family(raw,mask,baseid,params,ids)
            results[(family,rule,level,scope,cap)]=sc
            for mode in base.MODES:
                z=sc[mode]
                rows.append(dict(
                    family=family,rule=rule,threshold_level=level,
                    threshold_value=RULES[rule][level],
                    scope=scope,initial_stop_cap_pct=cap,
                    risk_condition_days=valid,actual_stops_shrunk=shrunk,
                    cost_model=mode,
                    **z))
        print("STEP18_PROGRESS "+json.dumps(dict(
           rule=rule,level=level,scope=scope,cap=cap,
           scenarios_completed=len(results)//3)),flush=True)
    matrix=pd.DataFrame(rows)
    if len(matrix)!=1086 or not matrix.trades.eq(477).all():
        raise AssertionError("Missing mandatory weekday data")
    matrix.to_csv(OUT/"all_540_causal_risk_mask_overlays_two_fee_models.csv",index=False)
    print("STEP18_GRID "+json.dumps(dict(
        family_baselines=3,risk_masks=180,backtests=540,
        both_fee_scenarios=1086,weekdays_per_policy=477)),flush=True)
    selected_reports={}
    for family in FAMILIES:
        basez=baseline[family]["scalper_offer"]
        subset=matrix[(matrix.family==family)&
                      (matrix.rule!="baseline")&
                      (matrix.cost_model=="scalper_offer")]
        required_2025_months=11 if family=="Step13_official" else 12
        eligible=subset[
           (subset.win_months_2025>=required_2025_months)&
           (subset.return_2025_pct>=basez["return_2025_pct"]-1e-6)&
           (subset.profitable_days_2025>=basez["profitable_days_2025"])&
           (subset.max_dd_2025<=basez["max_dd_2025"]+1e-4)]
        if len(eligible):
            picked=eligible.sort_values([
                "win_months_2025","return_2025_pct","profitable_days_2025",
                "max_dd_2025"],ascending=[False,False,False,True]
            ).iloc[0].to_dict()
            key=(family,picked["rule"],int(picked["threshold_level"]),
                 picked["scope"],float(picked["initial_stop_cap_pct"]))
            pickedcfg=cfg.copy()
            triggered=risk_trigger(key[1],key[2],feat,side)
            triggered=triggered&mask if key[3]=="fallback" else triggered
            pickedcfg[triggered,1]=np.minimum(pickedcfg[triggered,1],key[4])
            raw=early.replay_with_nextbar_exits(
                m.open.to_numpy(float),m.high.to_numpy(float),
                m.low.to_numpy(float),m.close.to_numpy(float),
                index,side,pickedcfg,policy,base.COST,base.SLIP)
            chooser,selected_by_fee=evaluate_family(
                raw,mask,baseid,FAMILIES[family],ids)
            frozen=dict(rule=key[1],threshold=RULES[key[1]][key[2]],
                scope=key[3],SL_cap_pct=key[4],
                train_2025_months=int(picked["win_months_2025"]),
                changed_stop_days=int(np.sum(pickedcfg[:,1]<cfg[:,1]-1e-12)))
        else:
            raw=raw_original
            chooser,selected_by_fee=original[family]
            frozen=dict(rule="baseline",scope="none",SL_cap_pct=None,
                        train_2025_months=basez["win_months_2025"],
                        changed_stop_days=0)
        summaryfee={}
        for mi,mode in enumerate(base.MODES):
            path=step15.getout(raw,chooser[0],mi)
            led,month=monthly_details(
                path,chooser,ctx,m,side,mask,hour,index,mode)
            led.to_csv(OUT/(family+"_"+mode+"_selected_477_daily.csv"),index=False)
            month.to_csv(OUT/(family+"_"+mode+"_selected_22_months.csv"),index=False)
            z=step15.score(path)
            summaryfee[mode]=dict(
                metrics=z,
                winning_months=int(np.sum(month.net_compounded_pct>0)),
                negative_months=month.loc[month.net_compounded_pct<=0,
                    ["month_ist","net_compounded_pct"]].to_dict("records"),
                profit_delta_pct=round(z["net_total_pct"]-
                        baseline[family][mode]["net_total_pct"],6),
                month_delta=int(z["win_months_all"]-
                          baseline[family][mode]["win_months_all"]),
                drawdown_delta_pct=round(z["max_closed_dd_pct"]-
                        baseline[family][mode]["max_closed_dd_pct"],6))
        selected_reports[family]=dict(
            admissible_2025_models=int(len(eligible)),
            frozen_policy_selected_by_2025_only=frozen,
            both_fee_scenarios=summaryfee)
        print("STEP18_SELECTED_"+family.upper()+" "+
            json.dumps(selected_reports[family],sort_keys=True),flush=True)

    offer=matrix[matrix.cost_model=="scalper_offer"]
    full22=offer[offer.win_months_all==22].sort_values(
        ["net_total_pct","max_closed_dd_pct"],ascending=[False,True])
    full22.to_csv(OUT/"hindsight_22_of_22_full_period_not_selected.csv",index=False)
    result=dict(
       experiment="Preentry 5m volume, 60m range, momentum contradiction and range-edge risk-conditioned initial stop caps",
       trade_contract="477 IST Mon–Fri trades per policy at full 1x account notional, no skips/weekends, unchanged entry directions/time and exact Step13/A/B exit",
       exact_original_step11_parity=original_step11,
       baseline_after_cost=baseline,
       models=540,fee_scenarios=1086,
       family_2025_only_selected=selected_reports,
       hindsight_22_of_22_models_NOT_eligible_for_posthoc_selection=int(len(full22)),
       hindsight_22_of_22_highest_net_NOT_SELECTED=(
           full22.iloc[0].to_dict() if len(full22) else None),
       fee_cost_assumptions="0.05% taker per leg+18% GST, historical hypothetical preactivated <=30m Scalper closing fee waiver; 5 BTCUSD adverse quote points per leg",
       limitations=[
         "2026 is heavily researched and not independent holdout, nor is November",
         "A/B families were selected using Jan2025-Oct2026 hindsight",
         "540 extra comparisons heighten data-snooping and overfit",
         "Cannot authenticate real historical Scalper offer opt-in, actual fills, orderbook, funding, latency or intrabar tick path",
         "No guarantee of 22 profitable months or one profitable day every weekday"])
    (OUT/"summary.json").write_text(json.dumps(result,indent=2)+"\n")
    text_lines=[
      "# Step18 — BTC full-weekday causal volatility stops",
      "",
      "Every policy enters one 1x account-notional trade on all 477 complete IST weekdays, same Step11 entry and Step13/A/B exit state. Only initial SL can shrink, based on preentry completed OHLCV.",
      "",
      "## Frozen original benchmarks",json.dumps(baseline,indent=2),
      "",
      "## 2025-only selections and 2026 research-exposed check",
      json.dumps(selected_reports,indent=2),
      "",
      "## Hindsight-only 22/22 models:",str(len(full22)),
      "",
      "## 22-month selected model B account returns",pd.read_csv(
          OUT/"B_21months_hindsight_scalper_offer_selected_22_months.csv").to_markdown(index=False),
      "",
      "## Caveats","2026 and earlier data are research-exposed; overfitting is likely when trying hundreds of variants. Historical scalper fee waiver status, actual live fills/latency, funding and tick ordering were not validated."
    ]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(text_lines)+"\n")
    print("STEP18_COMPLETE "+json.dumps(dict(
        candidate_count=540,full22_count=len(full22),
        selected={k:v["both_fee_scenarios"]["scalper_offer"] for k,v in selected_reports.items()}),
        sort_keys=True),flush=True)

if __name__=="__main__":
    main()
