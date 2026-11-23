#!/usr/bin/env python3
"""BTC Step16 — strictly pre-entry month-start SL cap tests, 477 weekday trades.

All entries, sides, 1m stop-first handling, plus Step13/A/B causal
previous-month PnL exit gates stay frozen. Only INITIAL stop width on a
general month-start day may shrink. 2025 selection only, 2026 exposed.
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
import research_btc_daily_online_direction_step6 as online

OUT=Path("analysis/btc_daily_month_start_stop_step16")
DAYS=base.DAYS
N=len(DAYS)
TRAIN=base.NTRAIN
MONTHS=np.asarray(base.MONTH_LABELS)
WINDOW=(2,3,5,8)
SCOPE=("fallback","both")
CAP=(.15,.20,.25,.30,.35,.40,.50)
FAMILIES={
    "Step13_official":("none","baseline","none","baseline"),
    "A_20months_hindsight":(
        "mtd_not_positive","adverse_cut_0.08pct_after_10m",
        "peak_ge_plus1_and_giveback050","profit_close_at_0.1pct_after_10m"),
    "B_21months_hindsight":(
        "mtd_not_positive","adverse_cut_0.08pct_after_10m",
        "mtd_at_least_plus1","profit_close_at_0.1pct_after_10m")
}
assert N==477 and TRAIN==260 and len(FAMILIES)*len(WINDOW)*len(SCOPE)*len(CAP)==168

def month_ordinals():
    dates=np.empty(N,dtype=np.int16)
    month=""
    dayno=0
    for i,v in enumerate(MONTHS):
        if v!=month:
            month=v
            dayno=0
        dates[i]=dayno
        dayno+=1
    return dates

def raw_for(m,indices,sides,recipes,policy,cap,window,scope,ordinals):
    cfg=np.array(recipes,copy=True)
    limit=ordinals<window
    if scope=="fallback":
        limit &= MASK
    # Use absolute percentage cap, NEVER increasing baseline initial SL.
    cfg[limit,1]=np.minimum(cfg[limit,1],cap)
    if np.any(cfg[:,1]>recipes[:,1]+1e-12):
        raise AssertionError("Initial stop may not widen")
    return early.replay_with_nextbar_exits(
        m.open.to_numpy(float),m.high.to_numpy(float),
        m.low.to_numpy(float),m.close.to_numpy(float),
        indices,sides,cfg,policy,base.COST,base.SLIP
    ),int(np.sum(cfg[:,1]<recipes[:,1]-1.e-12))

def winmonth(p):
    return np.asarray([100*(np.prod(1+p[MONTHS==m])-1)
        for m in list(dict.fromkeys(MONTHS.tolist()))],dtype=float)

def evaluate(raw,mask,family,rule_id):
    # Uses earlier COMPLETE real offer trades for causal within-month
    # trade selection, never future-day trade returns.
    decision=step15.replay_one(raw,mask,rule_id,FAMILIES[family],POLICY_IDS)
    scored={}
    for mi,mode in enumerate(base.MODES):
        path=step15.getout(raw,decision[0],mi)
        s=step15.score(path)
        scored[mode]=s
    return decision,scored

def write_family(family,selected,raw,mask,m,side,hour,idx):
    chosen,mtd,giveback,changed_ev,changed_fb=selected
    stats={}
    for mi,mode in enumerate(base.MODES):
        path=step15.getout(raw,chosen,mi)
        ledger,monthly=step15.saved_ledger(
            path,chosen,mtd,giveback,idx,hour,side,mask,mode
        )
        ledger.to_csv(OUT/(family+"_"+mode+"_2025_selected_477_trades.csv"),index=False)
        monthly.to_csv(OUT/(family+"_"+mode+"_2025_selected_22_months.csv"),index=False)
        s=step15.score(path)
        stats[mode]=dict(
            scores=s,
            winning_months=int((monthly.net_compounded_pct>0).sum()),
            losing_months=monthly.loc[monthly.net_compounded_pct<=0,
                ["month_ist","net_compounded_pct"]].to_dict("records"),
            overlay_event_early_exit_days=changed_ev,
            overlay_fallback_early_exit_days=changed_fb)
    return stats

def run():
    global MASK,POLICY_IDS
    OUT.mkdir(parents=True,exist_ok=True)
    m,ctx,mask,fb,side,hour,idx,origcfg=step13.create_path()
    MASK=mask
    policy,names=early.build_exit_policies()
    POLICY_IDS={label:i for i,label in enumerate(names)}
    unchanged=early.replay_with_nextbar_exits(
        m.open.to_numpy(float),m.high.to_numpy(float),
        m.low.to_numpy(float),m.close.to_numpy(float),
        idx,side,origcfg,policy,base.COST,base.SLIP)
    step13.check_parity(unchanged,ctx,fb)
    family_baseline={}
    orig_decisions={}
    for family in FAMILIES:
        d,sc=evaluate(unchanged,mask,family,
                      POLICY_IDS["profit_close_at_0.1pct_after_20m"])
        family_baseline[family]=sc
        orig_decisions[family]=d
    for family,expected in (
        ("Step13_official",23.261256),
        ("A_20months_hindsight",24.648136),
        ("B_21months_hindsight",22.480405)
    ):
        s=family_baseline[family]["scalper_offer"]
        if abs(s["net_total_pct"]-expected)>.00011 or s["trades"]!=477:
            raise AssertionError("Historic baseline full trade parity mismatch "+family)
    assert family_baseline["Step13_official"]["scalper_offer"]["win_months_all"]==19
    assert family_baseline["A_20months_hindsight"]["scalper_offer"]["win_months_all"]==20
    assert family_baseline["B_21months_hindsight"]["scalper_offer"]["win_months_all"]==21
    print("STEP16_VERIFIED_BASELINES "+json.dumps(family_baseline,sort_keys=True),flush=True)

    record=[]
    candidates={}
    # All baseline rows exist in records and are always eligible as fallbacks.
    for family in FAMILIES:
        for mi,mode in enumerate(base.MODES):
            s=family_baseline[family][mode]
            record.append(dict(
              family=family,scope="none",first_weekdays=0,
              initial_stop_cap_pct=np.nan,cost_model=mode,
              days_with_narrower_initial_stop=0,
              event_or_fallback_early_exit_changed=0,
              **s))
    ordinals=month_ordinals()
    for window,scope,cap in product(WINDOW,SCOPE,CAP):
        raw,changed=raw_for(m,idx,side,origcfg,policy,cap,window,scope,ordinals)
        for family in FAMILIES:
            decision,sc=evaluate(raw,mask,family,
                                POLICY_IDS["profit_close_at_0.1pct_after_20m"])
            candidates[(family,window,scope,cap)]=(decision,sc)
            for mi,mode in enumerate(base.MODES):
                record.append(dict(
                    family=family,scope=scope,first_weekdays=window,
                    initial_stop_cap_pct=cap,cost_model=mode,
                    days_with_narrower_initial_stop=changed,
                    event_or_fallback_early_exit_changed=int(np.sum(
                      decision[0]!=orig_decisions[family][0])),
                    **sc[mode]
                ))
        print("STEP16_CHECKPOINT "+json.dumps(dict(
            first_weekdays=window,scope=scope,cap=cap,
            total_completed_scopes=len(candidates)//3)),flush=True)
    result=pd.DataFrame(record)
    if len(result)!=342 or not result.trades.eq(477).all():
        raise AssertionError("Not all candidate 477 weekdays replayed")
    result.to_csv(OUT/"all_168_month_start_sl_overlays_3_baselines_both_fees.csv",index=False)
    print("STEP16_GRID "+json.dumps(dict(
        family_baselines=3,overlays=168,model_cost_scenarios=342,
        trades_each=477,calendar_months=22)),flush=True)
    offer=result[result.cost_model=="scalper_offer"]
    family_results={}
    for family in FAMILIES:
        seed=family_baseline[family]["scalper_offer"]
        familyrows=offer[(offer.family==family)&(offer.scope!="none")]
        admissible=familyrows[
            (familyrows.win_months_2025>=11)&
            (familyrows.return_2025_pct>=seed["return_2025_pct"]-1.e-6)&
            (familyrows.profitable_days_2025>=seed["profitable_days_2025"])&
            (familyrows.max_dd_2025<=seed["max_dd_2025"]+1e-4)]
        if len(admissible):
            best=admissible.sort_values(
              ["win_months_2025","return_2025_pct",
               "profitable_days_2025","max_dd_2025"],
              ascending=[False,False,False,True]).iloc[0].to_dict()
            key=(family,int(best["first_weekdays"]),best["scope"],
                 float(best["initial_stop_cap_pct"]))
            decision,sc=candidates[key]
            # reconstruct exactly one selected original-SL modified replay.
            raw,_=raw_for(m,idx,side,origcfg,policy,key[3],key[1],key[2],ordinals)
            chosen_rule={k:best[k] for k in ("scope","first_weekdays",
                          "initial_stop_cap_pct","return_2025_pct",
                          "win_months_2025","profitable_days_2025")}
        else:
            best=None
            decision=orig_decisions[family]
            raw=unchanged
            chosen_rule={"scope":"none","first_weekdays":0,
                         "initial_stop_cap_pct":None}
        details=write_family(family,decision,raw,mask,m,side,hour,idx)
        actual=details["scalper_offer"]["scores"]
        base_value=seed
        family_results[family]=dict(
            fully_2025_qualified_options=int(len(admissible)),
            chosen_using_2025_only=chosen_rule,
            selected_all_costs=details,
            delta_months=int(actual["win_months_all"]-base_value["win_months_all"]),
            delta_compound_net_pct=round(float(actual["net_total_pct"]-base_value["net_total_pct"]),6),
            delta_max_dd_pct=round(float(actual["max_closed_dd_pct"]-base_value["max_closed_dd_pct"]),6),
            twenty_two_month_win_retrospective=bool(actual["win_months_all"]==22))
        print("STEP16_SELECTED_"+family.upper()+" "+
              json.dumps(family_results[family],sort_keys=True),flush=True)
    all22=offer[offer.win_months_all==22].sort_values(
        ["net_total_pct","max_closed_dd_pct"],ascending=[False,True])
    all22.to_csv(OUT/"twenty_two_month_hindsight_only.csv",index=False)
    report=dict(
       study="Month-start BTC protective stop caps, one 1x BTCUSD future order every IST weekday",
       mandatory_days=477,positive_calendar_months_target=22,
       baseline_historical=family_baseline,
       families=family_results,
       hindsight_22_of_22_candidate_count=int(len(all22)),
       hindsight_22_of_22_best_NOT_SELECTED=(
           all22.iloc[0].to_dict() if len(all22) else None),
       selection="2025-only separately within each family; A/B baseline family choices are themselves hindsight-derived",
       model_costs="0.05% taker on each side plus GST18%; hypothetical preactivated <=30min Scalper Offer closing fee waiver; adverse 5 BTC quote points each side; 100% notional 1x",
       caveats=["Entire Jan2025-Oct2026 was repeatedly researched; NO independent clean held-out validation",
          "A and B were chosen with prior 2026 hindsight, not genuine 2025-only family selection",
          "Historic scalper offer activation, real fills/orderbook latency/funding and intraminute path unavailable",
          "An optimized backtest with 22/22 months positive would not imply guaranteed live profits"])
    (OUT/"summary.json").write_text(json.dumps(report,indent=2)+"\n")
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join([
        "# BTCUSD Step16: can first-week-of-month SL tightening improve 21/22 historical months?",
        "",
        "All 171 models place one BTCUSD position on exactly every one of 477 IST Mon–Fri dates. Every entry retains original Step11 direction and 100% 1x account notional. The only change is narrower initial stops on a general, predetermined window of early-month weekdays. Trade exits still use the previously causally defined Step13/A/B rule.",
        "",
        "## Three verified family baselines",json.dumps(family_baseline,indent=2),
        "",
        "## 2025-selected rules checked on 2026 (already research-exposed)",json.dumps(family_results,indent=2),
        "",
        "## Historical 22/22 variants must be treated as hindsight only",str(len(all22)),
        "",
        "## Limitations","Prior research repeatedly examined all 2026 dates; multiple-comparison bias, hypothetical Scalper Offer and coarse OHLC execution assumptions prevent live claims."
    ])+"\n")
    print("STEP16_COMPLETE "+json.dumps(report,sort_keys=True),flush=True)

if __name__=="__main__":
    run()
