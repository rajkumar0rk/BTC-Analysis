#!/usr/bin/env python3
"""Step14: conditional month-equity protection of frozen BTC Step13.

All 477 IST weekday trades, exact frozen Step11 entry price/time/side and
Step13 profit-close baseline; only EXIT subpolicy may change based on
previously completed trades in the current calendar month. All comparisons
using 2025 selection; 2026 is already research-exposed, not pristine.
"""
from itertools import product
from pathlib import Path
import json

import numpy as np
import pandas as pd

import research_btc_every_weekday_reset_step1 as base
import research_btc_daily_monthly_exit_step13 as previous
import research_btc_daily_exit_invalidation_step7 as bar
import research_btc_daily_online_direction_step6 as online

OUT=Path("analysis/btc_daily_monthly_equity_step14")
N=len(base.DAYS)
TRAIN=base.NTRAIN
MONTHS=np.asarray(base.MONTH_LABELS)
TRIGGERS=(
    "mtd_not_positive","mtd_below_minus025",
    "peak_giveback_ge030","peak_giveback_ge060",
    "peak_ge_plus1_and_giveback050",
    "two_losses","three_losses","first_five_weekdays",
    "after10_days_giveback050","mtd_at_least_plus1"
)
SCOPES=("event","fallback","both")
EXITS=(
    "adverse_cut_0.08pct_after_5m",
    "adverse_cut_0.12pct_after_5m",
    "adverse_cut_0.08pct_after_10m",
    "adverse_cut_0.2pct_after_10m",
    "stall_if_mfe_below_0.1pct_at_10m",
    "profit_close_at_0.1pct_after_10m",
    "profit_close_at_0.15pct_after_20m",
    "hard_timeout_10m","hard_timeout_15m","hard_timeout_20m"
)
assert N==477 and TRAIN==260 and len(TRIGGERS)*len(SCOPES)*len(EXITS)==300

def fired(name,mtd,peak_giveback,peak,losses,prior_days):
    if name=="mtd_not_positive":return mtd<=0.
    if name=="mtd_below_minus025":return mtd<=-.0025
    if name=="peak_giveback_ge030":return peak_giveback>=.003
    if name=="peak_giveback_ge060":return peak_giveback>=.006
    if name=="peak_ge_plus1_and_giveback050":
        return peak>=1.01 and peak_giveback>=.005
    if name=="two_losses":return losses>=2
    if name=="three_losses":return losses>=3
    if name=="first_five_weekdays":return prior_days<5
    if name=="after10_days_giveback050":return prior_days>=10 and peak_giveback>=.005
    if name=="mtd_at_least_plus1":return mtd>=.01
    raise KeyError(name)

def selected_path(raw,mask,base_index,trigger,scope,overlay_index):
    choices=np.zeros(N,dtype=np.int16)
    mtd_before=np.zeros(N)
    giveback_before=np.zeros(N)
    overlays=0
    month=None
    equity=1.
    peak=1.
    streak=0
    prior_days=0
    for d in range(N):
        if MONTHS[d]!=month:
            month=MONTHS[d]
            equity=1.
            peak=1.
            streak=0
            prior_days=0
        mtd=equity-1.
        giveback=peak-equity
        mtd_before[d]=mtd
        giveback_before[d]=giveback
        # Frozen Step13 offer-selected fallback +0.1% after20m exit
        # if prior calendar-month account return <= +0.25%.
        current=int(base_index) if mask[d] and mtd<=.0025 else 0
        match_scope=(scope=="both" or
                     (scope=="event" and not mask[d]) or
                     (scope=="fallback" and mask[d]))
        if trigger!="baseline" and match_scope and fired(
             trigger,mtd,giveback,peak,streak,prior_days):
            current=int(overlay_index)
            overlays+=1
        choices[d]=current
        dayreturn=float(raw[0][d,current,1])
        # No decision may use today's future PnL. Add current outcome
        # only after current trade has already been determined.
        equity*=1.+dayreturn
        peak=max(peak,equity)
        streak=streak+1 if dayreturn<0 else 0
        prior_days+=1
    return choices,mtd_before,giveback_before,overlays

def outcome(raw,choices,mode_i):
    d=np.arange(N)
    return tuple(x[d,choices,mode_i] if i<2 else x[d,choices]
                 for i,x in enumerate(raw))

def evaluate(path):
    p,c,g,why,t=path
    z=online.metrics(p,c,g,why,t)
    z["early_close_exits"]=int(np.sum(why==4))
    return z

def monthly_csv(path,choices,mtd,giveback,mask,hours,side,mode):
    p,c,g,why,t=path
    details=pd.DataFrame(dict(
        date_ist=base.IST_DAYS,year=np.asarray(base.DAYS.year),month_ist=MONTHS,
        hour_ist=hours,side=np.where(side>0,"LONG","SHORT"),
        trade_type=np.where(mask,"MANDATORY_FALLBACK","VOLUME_EVENT"),
        prior_completed_month_net_pct=mtd*100,
        prior_month_peak_giveback_pct=giveback*100,
        chosen_exit_index=choices,
        net_account_pct=p*100,
        gross_btc_points=g,fees_gst_btc_points=c,
        adverse_slippage_btc_points=2*base.SLIP,
        exit_type=np.where(why==1,"TARGET",np.where(why==2,"STOP",
                    np.where(why==3,"TIMEOUT","PRIOR_CANDLE_EARLY_EXIT"))),
        hold_minutes=t,fee_schedule=mode))
    assert len(details)==477 and details.date_ist.nunique()==477
    assert not (pd.to_datetime(details.date_ist).dt.dayofweek>=5).any()
    month=details.groupby("month_ist",sort=True).agg(
        trading_days=("date_ist","size"),
        positive_days=("net_account_pct",lambda x:int(np.sum(x>0))),
        negative_days=("net_account_pct",lambda x:int(np.sum(x<0))),
        compounded_net_pct=("net_account_pct",
              lambda x:float(100*(np.prod(1+x.to_numpy()/100)-1))),
        gross_points=("gross_btc_points","sum"),
        fees_gst_points=("fees_gst_btc_points","sum")
    ).reset_index()
    assert len(month)==22 and month.trading_days.sum()==477
    return details,month

def run():
    OUT.mkdir(parents=True,exist_ok=True)
    m,ctx,mask,fb,side,hours,idx,cfg=previous.create_path()
    policies,names=bar.build_exit_policies()
    ids={n:i for i,n in enumerate(names)}
    for x in EXITS:
        if x not in ids:raise AssertionError("Unrecognized existing exit "+x)
    raw=bar.replay_with_nextbar_exits(
        m.open.to_numpy(float),m.high.to_numpy(float),
        m.low.to_numpy(float),m.close.to_numpy(float),
        idx,side,cfg,policies,base.COST,base.SLIP
    )
    priorstep11=previous.check_parity(raw,ctx,fb)
    baseid=ids["profit_close_at_0.1pct_after_20m"]
    default=selected_path(raw,mask,baseid,"baseline","both",0)
    baseline={mode:evaluate(outcome(raw,default[0],i))
              for i,mode in enumerate(base.MODES)}
    base_offer=baseline["scalper_offer"]
    assert base_offer["win_months_all"]==19 and base_offer["profitable_days"]==290
    assert abs(base_offer["net_total_pct"]-23.261256)<.00011
    assert abs(baseline["standard"]["net_total_pct"]+6.967115)<.00011
    print("STEP14_BASELINE_VERIFIED "+json.dumps(baseline,sort_keys=True),flush=True)
    scenarios=[("baseline","both","baseline")]
    scenarios.extend(product(TRIGGERS,SCOPES,EXITS))
    choices={}
    result=[]
    for name,scope,extra in scenarios:
        addon=ids[extra] if name!="baseline" else 0
        if name=="baseline":
            decision=default
        else:
            decision=selected_path(raw,mask,baseid,name,scope,addon)
        key=(name,scope,extra)
        choices[key]=decision
        for mi,mode in enumerate(base.MODES):
            z=evaluate(outcome(raw,decision[0],mi))
            z.update(trigger=name,scope=scope,extra_exit=extra,
                     cost_model=mode,overlay_activated_days=decision[3],
                     changed_exit_choices=int(np.sum(decision[0]!=default[0])),
                     changed_exit_choices_2025=int(np.sum(decision[0][:TRAIN]!=default[0][:TRAIN])),
                     changed_exit_choices_2026=int(np.sum(decision[0][TRAIN:]!=default[0][TRAIN:])))
            result.append(z)
    df=pd.DataFrame(result)
    if len(df)!=602 or not df.trades.eq(477).all():
        raise AssertionError("Violation: every strategy must execute all 477 full weekdays")
    df.to_csv(OUT/"all_300_peak_equity_exit_overlays_two_fee_schedules.csv",index=False)
    print("STEP14_GRID "+json.dumps(dict(
        scenarios=301,fee_schedules=602,trades_each=477,
        train_months=12,2026_months=10)),flush=True)
    offer=df[df.cost_model=="scalper_offer"]
    qualified=offer[(offer.win_months_2025>=11)&
                    (offer.return_2025_pct>=9.5)&
                    (offer.profitable_days_2025>=157)&
                    (offer.max_dd_2025<=3.05)]
    if len(qualified):
        selected=qualified.sort_values(
           ["win_months_2025","return_2025_pct","profitable_days_2025","max_dd_2025"],
           ascending=[False,False,False,True]).iloc[0].to_dict()
    else:
        selected=offer[offer.trigger=="baseline"].iloc[0].to_dict()
    key=(selected["trigger"],selected["scope"],selected["extra_exit"])
    chosen,mtd,giveback,num=choices[key]
    reports={}
    for mi,mode in enumerate(base.MODES):
        p=outcome(raw,chosen,mi)
        day,month=monthly_csv(p,chosen,mtd,giveback,mask,hours,side,mode)
        day.to_csv(OUT/(mode+"_selected_477_daily.csv"),index=False)
        month.to_csv(OUT/(mode+"_selected_22_months.csv"),index=False)
        z=evaluate(p)
        reports[mode]=dict(
            account=z,
            positive_months=int((month.compounded_net_pct>0).sum()),
            negative_months=month.loc[month.compounded_net_pct<=0,
                 ["month_ist","compounded_net_pct"]].to_dict("records"),
            delta_vs_step13_total_pct=round(float(z["net_total_pct"]-baseline[mode]["net_total_pct"]),6),
            delta_vs_step13_positive_months=z["win_months_all"]-baseline[mode]["win_months_all"],
            delta_vs_step13_profitable_days=z["profitable_days"]-baseline[mode]["profitable_days"],
            delta_vs_step13_max_dd=round(float(z["max_closed_dd_pct"]-baseline[mode]["max_closed_dd_pct"]),6))
        print("STEP14_SELECTED_"+mode.upper()+" "+json.dumps(reports[mode],sort_keys=True),flush=True)
        print("STEP14_MONTHLY_"+mode.upper()+"\n"+month.to_string(index=False),flush=True)
    sc=reports["scalper_offer"]["account"]
    retrospective_promotion=(sc["win_months_all"]>=20 and sc["win_months_2026"]>=9
      and sc["net_total_pct"]>=23.261256 and sc["max_closed_dd_pct"]<=3.008746)
    hindsight=offer.sort_values(["win_months_all","net_total_pct"],ascending=False).iloc[0].to_dict()
    results=dict(
        topic="Improve BTC daily strategy 19/22 monthly win frequency using causal monthly peak loss regime",
        selection="2025-only, 2026 already researched and not genuine untouched OOS",
        mandatory_weekdays=477,
        full_notional_1x=True,
        original_step11_parity=priorstep11,
        original_step13_verified=baseline,
        candidate_models=301,scenarios_with_cost_sensitivity=602,
        eligible_2025_eleven_of_twelve_months=int(len(qualified)),
        selected_rule=selected,
        selected_results=reports,
        promotes_based_on_historical_check=bool(retrospective_promotion),
        highest_all_22_months_hindsight_NOT_SELECTED=hindsight,
        historical_count_with_at_least20_months=int(np.sum(offer.win_months_all>=20)),
        assumptions="1x account notional, 0.05% taker each leg GST18%, hypothetical preactivated <=30min Scalper closing waiver and 5 BTC price point adverse slip each side",
        limitations=[
           "2026 and November already explored extensively, not independent forward test",
           "300 additional variants raise overfit risk",
           "Cannot verify historic Scalper activation, actual live fills/spreads, funding, latency, orderbook or tick-level stop sequence",
           "One trade per weekday cannot guarantee each month is profitable"])
    (OUT/"summary.json").write_text(json.dumps(results,indent=2)+"\n")
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join([
        "# Step14 — BTC 19/22 monthly recovery with peak giveback and loss streak",
        "","Exactly 477 BTC weekday entries at 1x notional; unchanged Step11 side/time and baseline Step13 exit. One optional alternate exit selected based only on earlier days' within-month state.",
        "","## Step13 original baseline",json.dumps(baseline,indent=2),
        "","## 2025-only selected candidate",json.dumps(selected,indent=2),
        "","## 2026 history check and standard fee sensitivity",json.dumps(reports,indent=2),
        "","## Full 22 months",pd.read_csv(OUT/"scalper_offer_selected_22_months.csv").to_markdown(index=False),
        "","## Pure-hindsight highest monthly variant (never selected)",json.dumps(hindsight,indent=2),
        "","## Limitations","2026 is research-exposed and actual historical Scalper offer conditions/fees cannot be certified from OHLCV. A stronger 2025 selection is not proof of live reliability."
    ])+"\n")
    print("STEP14_COMPLETE "+json.dumps(results,sort_keys=True),flush=True)

if __name__=="__main__":
    run()
