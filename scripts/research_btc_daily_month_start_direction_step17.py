#!/usr/bin/env python3
"""Step17: causal first-N-weekdays BTC direction confirmations, fixed exits.

All 477 Mon–Fri IST trades retain original Step11 time, full 1x notional,
Step13/A/B monthly early-exit logic. Only direction may change based on
pre-entry 60m/240m momentum / 60m range structure. 2025-only selection,
2026 is research-exposed (not blind).
"""
from itertools import product
from pathlib import Path
import json
import numpy as np
import pandas as pd

import research_btc_every_weekday_reset_step1 as base
import research_btc_daily_monthly_exit_step13 as step13
import research_btc_daily_monthly_two_regime_step15 as step15
import research_btc_daily_exit_invalidation_step7 as early
import research_btc_daily_online_direction_step6 as online

OUT=Path("analysis/btc_daily_month_start_direction_step17")
N=len(base.DAYS)
TRAIN=base.NTRAIN
MONTHS=np.asarray(base.MONTH_LABELS)
FIRST_N=(2,5,8)
SCOPES=("fallback","both")
RULES=("invert_existing","follow60","fade60","follow240",
       "fade240","edge60_follow","edge60_fade")
FAMILIES={
 "Step13_official":("none","baseline","none","baseline"),
 "A_20months_hindsight":("mtd_not_positive","adverse_cut_0.08pct_after_10m",
    "peak_ge_plus1_and_giveback050","profit_close_at_0.1pct_after_10m"),
 "B_21months_hindsight":("mtd_not_positive","adverse_cut_0.08pct_after_10m",
    "mtd_at_least_plus1","profit_close_at_0.1pct_after_10m")
}
assert N==477 and TRAIN==260 and len(FAMILIES)*len(FIRST_N)*len(SCOPES)*len(RULES)==126

def ordinal():
    months=np.asarray(MONTHS)
    result=np.empty(N,dtype=np.int16)
    past=None
    k=0
    for d,month in enumerate(months):
        if month!=past:
            k=0
            past=month
        result[d]=k
        k+=1
    return result

def features(m,starts):
    op=m.open.to_numpy(float)
    close=m.close.to_numpy(float)
    hi=m.high.to_numpy(float)
    lo=m.low.to_numpy(float)
    i=starts.astype(np.int64)
    if np.any(i<240):
        raise AssertionError("Not enough preentry completed OHLC")
    r60=close[i-1]/op[i-60]-1.
    r240=close[i-1]/op[i-240]-1.
    pos60=np.empty(N)
    for d,j in enumerate(i):
        high=np.max(hi[j-60:j])
        low=np.min(lo[j-60:j])
        pos60[d]=(close[j-1]-low)/(high-low) if high>low else .5
    if not (np.isfinite(r60).all() and np.isfinite(r240).all() and
            np.isfinite(pos60).all()):
        raise AssertionError("Bad preentry feature")
    return r60,r240,pos60

def choose_side(original,mask,first_ordinal,window,scope,rule,pre):
    allowed=(first_ordinal<window)
    if scope=="fallback":
        allowed &= mask
    result=original.copy()
    r60,r240,pos60=pre
    if rule=="invert_existing":
        result[allowed]=-original[allowed]
    elif rule in ("follow60","fade60","follow240","fade240"):
        longterm=rule.endswith("240")
        v=r240 if longterm else r60
        threshold=.004 if longterm else .002
        active=allowed & (np.abs(v)>=threshold)
        target=np.where(v>=0,1,-1).astype(np.int8)
        if rule.startswith("fade"):
            target=-target
        result[active]=target[active]
    elif rule in ("edge60_follow","edge60_fade"):
        active=allowed & ((pos60>=.80)|(pos60<=.20))
        target=np.where(pos60>=.80,1,-1).astype(np.int8)
        if rule.endswith("fade"):
            target=-target
        result[active]=target[active]
    else:
        raise KeyError(rule)
    if not np.all((result==1)|(result==-1)):
        raise AssertionError("Side must be nonzero on all 477 weekdays")
    return result

def select_sign_arrays(long,short,side):
    use_long=side==1
    return tuple(
      np.where(use_long[:,None,None],long[j],short[j])
        if j<2 else np.where(use_long[:,None],long[j],short[j])
      for j in range(5)
    )

def metrics(path):
    return step15.score(path)

def monthly_report(path,choice,mtdeq,giveback,idx,hours,side,mask,mode):
    return step15.saved_ledger(path,choice,mtdeq,giveback,
                             idx,hours,side,mask,mode)

def family_stats(raw,mask,base_exit,policy_params,ids):
    selection=step15.replay_one(raw,mask,base_exit,policy_params,ids)
    metrics_by_fee={}
    for mi,mode in enumerate(base.MODES):
        p=step15.getout(raw,selection[0],mi)
        metrics_by_fee[mode]=metrics(p)
    return selection,metrics_by_fee

def run():
    OUT.mkdir(parents=True,exist_ok=True)
    m,ctx,mask,fb,base_side,hour,idx,cfg=step13.create_path()
    policies,labels=early.build_exit_policies()
    ids={name:i for i,name in enumerate(labels)}
    zeros=np.ones(N,dtype=np.int8)
    rawlong=early.replay_with_nextbar_exits(
       m.open.to_numpy(float),m.high.to_numpy(float),
       m.low.to_numpy(float),m.close.to_numpy(float),
       idx,zeros,cfg,policies,base.COST,base.SLIP)
    rawshort=early.replay_with_nextbar_exits(
       m.open.to_numpy(float),m.high.to_numpy(float),
       m.low.to_numpy(float),m.close.to_numpy(float),
       idx,-zeros,cfg,policies,base.COST,base.SLIP)
    frozen=select_sign_arrays(rawlong,rawshort,base_side)
    # Required exact regression on historical Step11 and Step13 daily
    # execution using full 1m stop-first replay for E and fallback.
    step13.check_parity(frozen,ctx,fb)
    baseline={}
    origin={}
    ruleid=ids["profit_close_at_0.1pct_after_20m"]
    for family,params in FAMILIES.items():
        selection,year=family_stats(frozen,mask,ruleid,params,ids)
        origin[family]=selection
        baseline[family]=year
    for name,ret in (
        ("Step13_official",23.261256),
        ("A_20months_hindsight",24.648136),
        ("B_21months_hindsight",22.480405)
    ):
        s=baseline[name]["scalper_offer"]
        if s["trades"]!=477 or abs(s["net_total_pct"]-ret)>.00011:
            raise AssertionError("Historical per-trade baseline drift "+name)
    print("STEP17_VERIFIED_BASELINES "+json.dumps(baseline,sort_keys=True),flush=True)

    ordinaldays=ordinal()
    pre=features(m,idx)
    rows=[]
    generated={}
    for family in FAMILIES:
        for mi,mode in enumerate(base.MODES):
            z=baseline[family][mode]
            rows.append(dict(family=family,rule="baseline",scope="none",
                first_weekdays=0,changed_longshort=0,cost_model=mode,**z))
    for span,scope,rule in product(FIRST_N,SCOPES,RULES):
        side=choose_side(base_side,mask,ordinaldays,span,scope,rule,pre)
        raw=select_sign_arrays(rawlong,rawshort,side)
        switched=int(np.sum(side!=base_side))
        for family,params in FAMILIES.items():
            select,z=family_stats(raw,mask,ruleid,params,ids)
            generated[(family,span,scope,rule)]=(side,select,z)
            for mi,mode in enumerate(base.MODES):
                rows.append(dict(
                   family=family,rule=rule,scope=scope,
                   first_weekdays=span,changed_longshort=switched,
                   cost_model=mode,
                   change_direction_2025=int(np.sum(side[:TRAIN]!=base_side[:TRAIN])),
                   change_direction_2026=int(np.sum(side[TRAIN:]!=base_side[TRAIN:])),
                   **z[mode]))
        print("STEP17_PROGRESS "+json.dumps(dict(
            first_weekdays=span,scope=scope,rule=rule,
            completed_unique_conditions=len(generated)//3)),flush=True)

    df=pd.DataFrame(rows)
    if len(df)!=258 or not df.trades.eq(477).all():
        raise AssertionError("Failed to replay all 477 weekday BTC orders")
    df.to_csv(OUT/"all_126_monthstart_direction_scenarios_two_fee_models.csv",index=False)
    print("STEP17_GRID "+json.dumps(dict(
       scenarios=129,reprices=258,every_candidate_trades=477)),flush=True)

    offer=df[df.cost_model=="scalper_offer"]
    chosen_results={}
    for family in FAMILIES:
        seed=baseline[family]["scalper_offer"]
        family_data=offer[(offer.family==family)&(offer.rule!="baseline")]
        required_months=11 if family=="Step13_official" else 12
        eligible=family_data[
          (family_data.win_months_2025>=required_months)&
          (family_data.return_2025_pct>=seed["return_2025_pct"]-1e-6)&
          (family_data.profitable_days_2025>=seed["profitable_days_2025"])&
          (family_data.max_dd_2025<=seed["max_dd_2025"]+1e-4)]
        if len(eligible):
            best=eligible.sort_values(
               ["win_months_2025","return_2025_pct",
                "profitable_days_2025","max_dd_2025"],
               ascending=[False,False,False,True]).iloc[0].to_dict()
            key=(family,int(best["first_weekdays"]),best["scope"],best["rule"])
            side,selection,model=generated[key]
            chosen_rule={field:best[field] for field in
                ("first_weekdays","scope","rule","return_2025_pct",
                 "win_months_2025","profitable_days_2025")}
        else:
            side=base_side
            selection=origin[family]
            chosen_rule={"first_weekdays":0,"scope":"none","rule":"baseline"}
        raw=select_sign_arrays(rawlong,rawshort,side)
        year={}
        for mi,mode in enumerate(base.MODES):
            path=step15.getout(raw,selection[0],mi)
            daily,monthly=monthly_report(
                path,selection[0],selection[1],selection[2],
                idx,hour,side,mask,mode)
            daily.to_csv(OUT/(family+"_"+mode+"_selected_477_daily.csv"),index=False)
            monthly.to_csv(OUT/(family+"_"+mode+"_selected_22_months.csv"),index=False)
            z=metrics(path)
            year[mode]=dict(
                performance=z,
                winning_months=int(np.sum(monthly.net_compounded_pct>0)),
                losing_months=monthly.loc[monthly.net_compounded_pct<=0,
                  ["month_ist","net_compounded_pct"]].to_dict("records"),
                change_vs_family_months=int(z["win_months_all"]-baseline[family][mode]["win_months_all"]),
                change_vs_family_net=round(float(z["net_total_pct"]-baseline[family][mode]["net_total_pct"]),6),
                change_vs_family_dd=round(float(z["max_closed_dd_pct"]-baseline[family][mode]["max_closed_dd_pct"]),6))
        chosen_results[family]=dict(
            qualified_training_models=int(len(eligible)),
            policy_frozen_from_2025_only=chosen_rule,
            results=year,
            achieved_all_22_months=bool(year["scalper_offer"]["performance"]["win_months_all"]==22))
        print("STEP17_SELECTED_"+family.upper()+" "+
              json.dumps(chosen_results[family],sort_keys=True),flush=True)
    all22=offer[offer.win_months_all==22].sort_values("net_total_pct",ascending=False)
    all22.to_csv(OUT/"hindsight_only_22_profitable_months.csv",index=False)
    report=dict(
       task="Causal first-month-week direction confirmation, full BTCUSD weekday trades",
       calendar="Jan 2025-Oct 2026, exactly 477 IST weekdays",
       tested_direction_models=129,model_fee_reprices=258,
       baseline=baseline,selected_from_2025_only=chosen_results,
       unselected_22_month_hindsight_count=int(len(all22)),
       highest_net_22_month_hindsight_NOT_SELECTED=(
         all22.iloc[0].to_dict() if len(all22) else None),
       constraints="Original full 1x daily notional and entry hour; 5 BTC points adverse slip each side; taker0.05% per side+GST18%; hypothetical prior opt-in Scalper Offer closing fee waived <=30min; same early-exit rules",
       caveats=["A/B base configurations themselves were identified by inspecting 2026, hence not independent",
          "2026 and November were previously studied; cannot claim future validation",
          "Many strategy tests increase in-sample selection bias",
          "Actual historical Scalper Offer activation, real spreads/orderbook fills, latency, funding and liquidation not available"])
    (OUT/"summary.json").write_text(json.dumps(report,indent=2)+"\n")
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join([
       "# Step17 — BTC month-start direction confirmation, full 477 weekday coverage",
       "",
       "At every first-2/5/8 weekday entry, optionally apply a deterministic 60m/240m momentum or 60m range-edge rule based on completed preentry 1m bars. Keep the existing 21h fallback/volume event clock and freeze all exit code. Actual month-to-date early exit state updates only after a previously completed trade.",
       "",
       "## Historical base results",json.dumps(baseline,indent=2),
       "",
       "## 2025-selected model family results, 2026 research-exposed check",
       json.dumps(chosen_results,indent=2),
       "",
       "## Hindsight-only 22-month count",str(len(all22)),
       "",
       "## Warnings","Jan 2025–Oct 2026 has been previously mined for many strategies; selecting a positive 2025 model does not establish a repeatable edge, especially if the baseline family was hindsight-selected. Real fee waiver and execution remain unverified."
    ])+"\n")
    print("STEP17_COMPLETE "+json.dumps(report,sort_keys=True),flush=True)

if __name__=="__main__":
    run()
