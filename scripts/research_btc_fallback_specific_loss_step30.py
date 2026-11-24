#!/usr/bin/env python3
"""Step30: 1200 fallback-only prior-loss-memory BTC recovery strategies.

Unlike Step29's whole-month loss state, the guard here uses only
COMPLETED FALLBACK trade outcomes earlier in same IST calendar month.
All 477 IST weekdays trade full 1x account notional, no skipping.
History repeatedly researched: even a found 22/22 is exploratory.
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
import research_btc_january2025_loss_recovery_step29 as previous

OUT=Path("analysis/btc_fallback_specific_loss_step30")
N=len(base.DAYS)
TRAIN=base.NTRAIN
MONTHS=np.asarray(base.MONTH_LABELS)
GATES=(
    "last_fallback_lost",
    "last_fallback_lost025",
    "last_two_fallback_losses",
    "last_two_fallback_sum_negative025",
    "two_of_last_three_fallback_losses",
    "fallback_month_cumulative_negative",
    "fallback_month_cumulative_below025",
    "fallback_month_cumulative_below050"
)
DIRECTIONS=("keep_ridge","invert_high_rvol","invert_always",
            "follow60","fade5")
CAPS=(.15,.20,.25,.30,.35)
EXITS=("base","profit010_after5","profit010_after10",
       "adverse008_after5","adverse008_after10","timeout20")
assert N==477 and TRAIN==260
assert len(GATES)*len(DIRECTIONS)*len(CAPS)*len(EXITS)==1200

def fallback_is_losing(rule,past,equity):
    n=len(past)
    if rule=="off":return False
    if n==0:return False
    if rule=="last_fallback_lost":
        return past[-1]<0.
    if rule=="last_fallback_lost025":
        return past[-1]<=-.0025
    if rule=="last_two_fallback_losses":
        return n>=2 and past[-1]<0. and past[-2]<0.
    if rule=="last_two_fallback_sum_negative025":
        return n>=2 and past[-1]+past[-2]<=-.0025
    if rule=="two_of_last_three_fallback_losses":
        return n>=3 and sum(v<0 for v in past[-3:])>=2
    if rule=="fallback_month_cumulative_negative":
        return equity<1.
    if rule=="fallback_month_cumulative_below025":
        return equity<=.9975
    if rule=="fallback_month_cumulative_below050":
        return equity<=.995
    raise KeyError(rule)

def choose_fallback(kind,orig,day,info):
    if kind=="invert_always":return -int(orig)
    if kind=="follow60":return previous.recovery_direction(
        "follow_last60m",orig,day,info)
    if kind=="fade5":return previous.recovery_direction(
        "fade_last5m",orig,day,info)
    return previous.recovery_direction(kind,orig,day,info)

def simulate(setting,cache,mask,ridge_sides,info,ids):
    state,dir_name,cap,exit_name=setting
    pnl=np.empty((len(base.MODES),N),dtype=float)
    fee=np.empty((len(base.MODES),N),dtype=float)
    gross=np.empty(N)
    reason=np.empty(N,dtype=np.int8)
    hold=np.empty(N,dtype=np.int16)
    side=np.empty(N,dtype=np.int8)
    exit_policy=np.empty(N,dtype=np.int16)
    prior_mtd=np.zeros(N)
    prior_highwater=np.zeros(N)
    prior_month_giveback=np.zeros(N)
    prior_fallback_equity=np.zeros(N)
    prior_fallback_count=np.zeros(N,dtype=np.int16)
    prior_fallback_lost=np.zeros(N,dtype=np.int16)
    fallback_loss_trigger=np.zeros(N,dtype=bool)
    month_highwater_trigger=np.zeros(N,dtype=bool)
    month=None
    equity=1.;peak=1.;fallback_equity=1.;fb_previous=[]
    for d in range(N):
        if MONTHS[d]!=month:
            month=MONTHS[d]
            equity=1.;peak=1.;fallback_equity=1.;fb_previous=[]
        mtd=equity-1.
        prior_mtd[d]=mtd
        prior_highwater[d]=peak-1.
        prior_month_giveback[d]=peak-equity
        prior_fallback_equity[d]=fallback_equity-1.
        prior_fallback_count[d]=len(fb_previous)
        prior_fallback_lost[d]=sum(v<0 for v in fb_previous)
        # Step28 high-water guard: independent of fallback regime.
        peakguard=(peak>=1.01 and peak-equity>=.0075)
        month_highwater_trigger[d]=peakguard
        # Trigger only if this day is the mandatory fallback entry.
        fallback_trigger=(bool(mask[d]) and
                          fallback_is_losing(state,fb_previous,
                                             fallback_equity))
        fallback_loss_trigger[d]=fallback_trigger
        trade_side=int(ridge_sides[d])
        if fallback_trigger:
            trade_side=choose_fallback(dir_name,trade_side,d,info)
        side[d]=trade_side
        if abs(trade_side)!=1:raise AssertionError("Zero position side")
        chosen_cap=(cap if fallback_trigger else None)
        eid=previous.entry_exit_id(
            bool(mask[d]),mtd,fallback_trigger,exit_name,ids)
        exit_policy[d]=eid
        source=cache[(trade_side,peakguard,chosen_cap)]
        pnl[:,d]=source[0][d,eid,:]
        fee[:,d]=source[1][d,eid,:]
        gross[d]=source[2][d,eid]
        reason[d]=source[3][d,eid]
        hold[d]=source[4][d,eid]
        outcome=float(pnl[base.MODES.index("scalper_offer"),d])
        if not np.isfinite(outcome) or outcome<=-1.:
            raise AssertionError("Invalid realized return")
        equity*=1.+outcome
        peak=max(peak,equity)
        if mask[d]:
            fb_previous.append(outcome)
            fallback_equity*=1.+outcome
    out={}
    for i,fee_mode in enumerate(base.MODES):
        path=(pnl[i],fee[i],gross,reason,hold)
        monthly=previous.step28.step26.month_numbers(path[0])
        stats=step15.score(path)
        if len(monthly)!=22 or stats["trades"]!=477 or stats["win_months_all"]!=int(np.sum(monthly>0)):
            raise AssertionError("Month count or missing 477 weekday trades")
        out[fee_mode]=dict(
            performance=stats,monthly=monthly,
            january2025=float(monthly[0]),
            january2026=float(monthly[12]))
    return dict(
        out=out,pnl=pnl,fee=fee,gross=gross,reason=reason,hold=hold,
        side=side,policy=exit_policy,
        mtd=prior_mtd,prior_peak=prior_highwater,
        giveback=prior_month_giveback,
        fallback_mtd=prior_fallback_equity,
        fallback_history_n=prior_fallback_count,
        fallback_history_losers=prior_fallback_lost,
        fallback_loss_trigger=fallback_loss_trigger,
        highwater_guard=month_highwater_trigger,
        sides_changed=int(np.sum((side!=ridge_sides)&mask))
    )

def export(tag,setting,result,ridge,hours,mask):
    report={}
    for mi,fee_model in enumerate(base.MODES):
        p=result["pnl"][mi]
        daily=pd.DataFrame(dict(
            day_ist=base.IST_DAYS,
            year=np.asarray(base.DAYS.year),
            month_ist=MONTHS,
            entry_hour_ist=hours,
            trade_type=np.where(mask,"FALLBACK_21H","EVENT_VOLUME_SIGNAL"),
            actual_side=np.where(result["side"]>0,"LONG","SHORT"),
            frozen_ridge_side=np.where(ridge>0,"LONG","SHORT"),
            prior_total_month_mtd_pct=result["mtd"]*100.,
            prior_month_account_peak_pct=result["prior_peak"]*100.,
            prior_month_peak_giveback_pp=result["giveback"]*100.,
            prior_fallbacks_this_month=result["fallback_history_n"],
            prior_fallback_losing_trades=result["fallback_history_losers"],
            prior_compounded_fallback_month_net_pct=result["fallback_mtd"]*100.,
            fallback_only_loss_memory_active=result["fallback_loss_trigger"],
            Step28_peak_guard_active=result["highwater_guard"],
            fallback_loss_gate_name=setting[0],
            fallback_direction_on_loss=setting[1],
            fallback_extra_stop_cap_pct_if_loss=setting[2],
            fallback_extra_exit_if_loss=setting[3],
            selected_closed_bar_exit_index=result["policy"],
            account_net_daily_pct=p*100.,
            gross_btc_quote_points=result["gross"],
            modeled_fee_gst_points=result["fee"][mi],
            slippage_quote_points=2.*base.SLIP,
            reason=result["reason"],
            minutes_held=result["hold"],
            cost_model=fee_model,
            model=tag
        ))
        if (len(daily)!=477 or daily.day_ist.nunique()!=477 or
            (pd.to_datetime(daily.day_ist).dt.dayofweek>=5).any()):
            raise AssertionError("Unfilled/weekend trade count")
        monthly=pd.DataFrame(dict(
            month_ist=list(dict.fromkeys(MONTHS.tolist())),
            net_compounded_pct=result["out"][fee_model]["monthly"],
            trades=[int(np.sum(MONTHS==month))
                    for month in list(dict.fromkeys(MONTHS.tolist()))],
            model=tag,cost_model=fee_model
        ))
        if len(monthly)!=22 or monthly.trades.sum()!=477:
            raise AssertionError("Month representation mismatch")
        daily.to_csv(OUT/(tag+"_"+fee_model+"_477_daily.csv"),index=False)
        monthly.to_csv(OUT/(tag+"_"+fee_model+"_22_months.csv"),index=False)
        report[fee_model]=dict(
            performance=result["out"][fee_model]["performance"],
            January_2025_net_pct=result["out"][fee_model]["january2025"],
            January_2026_net_pct=result["out"][fee_model]["january2026"],
            losing_months=monthly.loc[monthly.net_compounded_pct<=0,
                ["month_ist","net_compounded_pct"]].to_dict("records"),
            fallback_loss_guard_days=int(np.sum(result["fallback_loss_trigger"])),
            fallback_sides_changed=result["sides_changed"])
    return report

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    m,ctx,mask,fb,orig_side,hours,idx,base_cfg=step13.create_path()
    policies,labels=early.build_exit_policies()
    ids={name:i for i,name in enumerate(labels)}
    features,ridge=previous.all_features_and_sides(
        m,mask,idx,orig_side,base_cfg,policies)
    cache,original_stop=previous.raw_cache(
        m,mask,idx,base_cfg,features,policies)
    baseline_setting=("off","keep_ridge",None,"base")
    baseline=simulate(baseline_setting,cache,mask,ridge,features,ids)
    old=baseline["out"]["scalper_offer"]["performance"]
    oldstd=baseline["out"]["standard"]["performance"]
    j25=baseline["out"]["scalper_offer"]["january2025"]
    j26=baseline["out"]["scalper_offer"]["january2026"]
    if (old["trades"]!=477 or old["win_months_all"]!=21 or
        old["profitable_days"]!=281 or
        abs(old["net_total_pct"]-28.574051)>.00011 or
        abs(old["max_closed_dd_pct"]-2.617670)>.00011 or
        abs(j25+1.04710143575)>.00011 or
        abs(j26-.91087191822)>.00011 or
        abs(oldstd["net_total_pct"]+2.954186)>.00011):
        raise AssertionError("Step28 exact baseline regression failure "+str(old)+str(j25))
    print("STEP30_PARITY "+json.dumps(dict(
        verified_net=old["net_total_pct"],months=old["win_months_all"],
        January2025=j25,January2026=j26,standard_net=oldstd["net_total_pct"],
        mandatory_weekdays=477)),flush=True)

    rows=[];rulemap={}
    for it,(gate,direction,cap,extra) in enumerate(
        product(GATES,DIRECTIONS,CAPS,EXITS),start=1):
        key=(gate,direction,cap,extra)
        name=f"{gate}__{direction}__{cap:.2f}__{extra}"
        rulemap[name]=key
        result=simulate(key,cache,mask,ridge,features,ids)
        for fee_mode in base.MODES:
            sc=result["out"][fee_mode]
            rows.append(dict(
                model=name,fallback_loss_gate=gate,
                fallback_direction_rule=direction,
                fallback_initial_SL_cap_pct=cap,
                fallback_early_exit=extra,
                fallback_guard_trade_days=int(np.sum(result["fallback_loss_trigger"])),
                changed_fallback_direction_days=int(result["sides_changed"]),
                January2025_net_pct=sc["january2025"],
                January2026_net_pct=sc["january2026"],
                fee_mode=fee_mode,**sc["performance"]))
        if it%200==0 or it==1200:
            print("STEP30_PROGRESS "+json.dumps(dict(
                done=it,total=1200,last=name)),flush=True)
    allrows=pd.DataFrame(rows)
    for fee_mode in base.MODES:
        result=baseline["out"][fee_mode]
        allrows=pd.concat([
            allrows,pd.DataFrame([dict(
                model="frozen_step28",fallback_loss_gate="off",
                fallback_direction_rule="keep_ridge",
                fallback_initial_SL_cap_pct=None,
                fallback_early_exit="base",
                fallback_guard_trade_days=0,
                changed_fallback_direction_days=0,
                January2025_net_pct=result["january2025"],
                January2026_net_pct=result["january2026"],
                fee_mode=fee_mode,**result["performance"])])
            ],ignore_index=True)
    if len(allrows)!=2402 or not allrows.trades.eq(477).all():
        raise AssertionError("Incomplete 1200 models or missing calendar weekdays")
    allrows.to_csv(OUT/"all_1200_fallback_specific_memory_models_both_fees.csv",index=False)
    offer=allrows[allrows.fee_mode=="scalper_offer"]
    january_positive=offer[(offer.model!="frozen_step28")&
                           (offer.January2025_net_pct>0)]
    training12=offer[(offer.model!="frozen_step28")&
                    (offer.win_months_2025==12)]
    strict=training12[
        (training12.return_2025_pct>=old["return_2025_pct"]-1e-6)&
        (training12.profitable_days_2025>=old["profitable_days_2025"])&
        (training12.max_dd_2025<=old["max_dd_2025"]+1e-4)]
    if len(strict):
        selected=strict.sort_values(
            ["return_2025_pct","profitable_days_2025","max_dd_2025"],
            ascending=[False,False,True]).iloc[0].to_dict()
    else:
        selected=offer[offer.model=="frozen_step28"].iloc[0].to_dict()
    retrospective22=offer[(offer.model!="frozen_step28")&
                          (offer.win_months_all==22)].sort_values(
        ["net_total_pct","max_closed_dd_pct"],ascending=[False,True])
    retrospective22.to_csv(OUT/"HINDSIGHT_ONLY_22_of_22_full_months.csv",index=False)
    janbest=january_positive.sort_values(
        ["January2025_net_pct","win_months_all","net_total_pct"],
        ascending=[False,False,False]) if len(january_positive) else offer.sort_values(
        "January2025_net_pct",ascending=False)
    janbest.head(30).to_csv(OUT/"HINDSIGHT_ONLY_January2025_best.csv",index=False)
    guarded=offer[
        (offer.win_months_all>=21)&
        (offer.win_months_2026>=10)&
        (offer.net_total_pct>=old["net_total_pct"])&
        (offer.max_closed_dd_pct<=old["max_closed_dd_pct"]+1e-4)
    ].sort_values(["January2025_net_pct","net_total_pct"],ascending=[False,False])
    guarded.head(25).to_csv(OUT/"HINDSIGHT_ONLY_month_net_dd_guard.csv",index=False)
    diagnostic=(retrospective22.iloc[0].to_dict() if len(retrospective22) else
                (guarded.iloc[0].to_dict() if len(guarded) else janbest.iloc[0].to_dict()))
    audited={}
    for tag,row in (
        ("Step28_frozen_original",dict(model="frozen_step28")),
        ("selected_from_2025_only",selected),
        ("hindsight_January2025_NOT_SELECTED",janbest.iloc[0].to_dict()),
        ("hindsight_historical_best_NOT_SELECTED",diagnostic)):
        name=row["model"]
        config=(baseline_setting if name=="frozen_step28" else rulemap[name])
        res=(baseline if name=="frozen_step28" else
             simulate(config,cache,mask,ridge,features,ids))
        audited[tag]=dict(
            model=name,settings=config,
            fee_scenarios=export(tag,config,res,ridge,hours,mask))
        print("STEP30_AUDIT_"+tag.upper()+" "+
            json.dumps(audited[tag],sort_keys=True),flush=True)
    selected_stats=audited["selected_from_2025_only"]["fee_scenarios"]["scalper_offer"]
    p=selected_stats["performance"]
    target=(
        selected_stats["January_2025_net_pct"]>0 and
        p["win_months_all"]==22 and p["win_months_2026"]==10 and
        p["net_total_pct"]>=old["net_total_pct"] and
        p["max_closed_dd_pct"]<=old["max_closed_dd_pct"]+1e-4)
    report=dict(
        experiment="Fallback-specific prior completed monthly losses and full-size 477 weekday entries",
        correct_failure_month="2025-01",
        frozen_Step28_baseline=audited["Step28_frozen_original"],
        total_tested_policies=1200,total_fee_model_rows=2402,
        all_477_weekday_positions_full_1x_account_notional=True,
        positive_January2025_hindsight_candidates=int(len(january_positive)),
        positive_all_12_months_in_2025_candidates=int(len(training12)),
        qualified_2025_only_rules=int(len(strict)),
        22_out_of_22_all_history_hindsight_candidate_count=int(len(retrospective22)),
        selected_using_2025_only=audited["selected_from_2025_only"],
        meets_all_full_year_month_profit_drawdown_conditions=bool(target),
        best_January2025_hindsight_UNSELECTED=audited["hindsight_January2025_NOT_SELECTED"],
        best_whole_history_hindsight_UNSELECTED=audited["hindsight_historical_best_NOT_SELECTED"],
        cost_assumptions="0.05% taker each side+18% GST; hypothetical preactivated regular <=30m Scalper exit waiver, adverse 5 BTCUSD quote points per side, all 1x notional",
        caveats=[
          "2025 January is in sample and 2026 has been seen in many previous optimization rounds",
          "1200 candidate hypotheses add extreme multiple-comparisons and overfitting",
          "Actual historical Scalper opt-in status, market spread, liquidity, funding, latency and intraminute tick trajectory not confirmed",
          "No guarantee of positive monthly live results, no production orders or main merge"])
    (OUT/"summary.json").write_text(json.dumps(
        report,indent=2,default=lambda v:v.item() if isinstance(v,np.generic) else str(v))+"\n")
    md=[
        "# Step30 — January2025 BTC futures fallback-only losing-trade memory",
        "",
        "January2025 (not January2026) was the sole losing historical month. Every strategy enters exactly once on all 477 IST weekdays with full 1x account notional. Use only previously completed same-month fallback trade results to choose direction, SL cap and next-open early close.",
        "",
        "## Exact original Step28 parity",json.dumps(audited["Step28_frozen_original"],indent=2),
        "",
        "## 2025-only selection results",json.dumps(audited["selected_from_2025_only"],indent=2),
        "",
        "## 12/12 in 2025 / 22/22 all-history candidate counts",
        str(len(training12)),str(len(retrospective22)),
        "",
        "## Hindsight Jan2025 only (NOT SELECTED)",
        json.dumps(audited["hindsight_January2025_NOT_SELECTED"],indent=2),
        "",
        "## All 22 months retained strategy",
        pd.read_csv(OUT/"selected_from_2025_only_scalper_offer_22_months.csv").to_markdown(index=False),
        "",
        "## Warnings",
        "The same market history has been mined for many attempts and historical regular Scalper activation not independently verified. Standard fees may be negative. No live edge claim."
    ]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(md)+"\n")
    print("STEP30_COMPLETE "+json.dumps(dict(
        models=1200,
        positive_January2025=int(len(january_positive)),
        all2025_12_positive_months=int(len(training12)),
        qualified_2025=int(len(strict)),
        full_22_positive_months_hindsight=int(len(retrospective22)),
        original_Jan2025=float(j25),
        selected_Jan2025=float(selected_stats["January_2025_net_pct"]),
        selected_months=p["win_months_all"],
        selected_net=p["net_total_pct"],
        selected_DD=p["max_closed_dd_pct"],
        meets_full_target=bool(target),
        best_Jan2025_hindsight=float(
            audited["hindsight_January2025_NOT_SELECTED"]["fee_scenarios"]["scalper_offer"]["January_2025_net_pct"])
    ),sort_keys=True),flush=True)

if __name__=="__main__":
    main()
