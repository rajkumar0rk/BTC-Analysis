#!/usr/bin/env python3
"""BTCUSD Step12: monthly-consistency recovery, one trade every IST weekday.

Every entry timestamp, setup and 1m exit is FROZEN from Step11. No
reduction in trade count/exposure. Changes only direction when current
calendar-month PnL to PREVIOUS completed trading day is weak, based on
PRIOR same-month or recent shadow results. Score choices using the assumed
Scalper Offer, then reprice exact same trades with standard taker+GST.
"""
from pathlib import Path
from itertools import product
import json

import numpy as np
import pandas as pd

import research_btc_every_weekday_reset_step1 as base
import research_btc_daily_online_direction_step6 as online
import research_btc_daily_online_structure_step11 as step11

OUT=Path("analysis/btc_daily_monthly_recovery_step12")
N=len(base.DAYS)
TRAIN=base.NTRAIN
MONTHS=np.asarray(base.MONTH_LABELS)
UNIQUE_MONTHS=list(dict.fromkeys(MONTHS.tolist()))
MTD_TRIGGER=(0.,-.0025,-.005)
EVENT_METHOD=("fixed","same_month_net","recent_net","recent_win")
FALL_METHOD=("fixed","same_month_net","recent_net","recent_win","recent_risk")
MIN_PAST=(2,4)
EXPECTED=len(MTD_TRIGGER)*len(EVENT_METHOD)*len(FALL_METHOD)*len(MIN_PAST)
assert N==477 and TRAIN==260 and len(UNIQUE_MONTHS)==22 and EXPECTED==120

def prep_paths():
    ctx=step11.shadow(base.load())
    f=ctx["f"]
    fallback=ctx["mask"]
    # The exact 2025-selected Step11 selector: prior60 completed fallback
    # days, all six fixed deterministic structural arms, mean offer net
    # return, margin zero, min 15.
    base_f_choice,base_priorn,_=step11.choose_online(
        ctx["returns"]["scalper_offer"][0],fallback,
        60,"all_6_arms","net","none")
    assert base_f_choice.shape==(N,) and int(fallback.sum())==217
    # Per-day event alternative arms are relative to the exact frozen
    # pre-entry online Step8 event choice, never its future outcome.
    ebase=ctx["base_event"]
    event={}
    for mi,mode in enumerate(base.MODES):
        fields=f["event"][mi] # each shape N,2: FADE5 / FOLLOW5
        d=np.arange(N)
        event[mode]=tuple(
            np.stack([field[d,ebase],field[d,1-ebase]],axis=1)
            for field in fields
        )
    fallback_paths=ctx["returns"] # N,6 per field, standard and offer
    for mode in base.MODES:
        assert event[mode][0].shape==(N,2)
        assert fallback_paths[mode][0].shape==(N,6)
    return ctx,event,base_f_choice,base_priorn


def weighted_score(prior,kind):
    """Only previous completed type-matched trading days in prior indices."""
    if kind.endswith("_net"):
        return np.mean(prior,axis=0),.0002
    if kind.endswith("_win"):
        return np.mean(prior>0,axis=0),.05
    if kind.endswith("_risk"):
        risk=np.sqrt(np.mean(np.minimum(prior,0.)**2,axis=0))
        return np.mean(prior,axis=0)-.30*risk,.0002
    raise KeyError(kind)


def maybe_override(method,day,base_arm,monthprior,allprior,shadow,minimum):
    if method=="fixed":
        return base_arm,0
    prior=monthprior if method.startswith("same_month") else allprior[-20:]
    if len(prior)<minimum:
        return base_arm,len(prior)
    indices=np.asarray(prior,dtype=np.int64)
    if indices.max()>=day:
        raise AssertionError("Look-ahead: today's or future shadow result")
    scores,margin=weighted_score(shadow[indices,:],method)
    best=int(np.argmax(scores))
    # Do not abandon current baseline on statistically marginal history;
    # same threshold is applied to every month and model.
    if best!=base_arm and scores[best]>scores[base_arm]+margin:
        return best,len(prior)
    return base_arm,len(prior)


def select_chronological(settings,event_offer,fall_offer,mask,baseline_fb):
    trigger,evmethod,fbmethod,minimum=settings
    event_arm=np.zeros(N,dtype=np.int8)
    fall_arm=np.asarray(baseline_fb,dtype=np.int8).copy()
    prev_group_ev=[];prev_group_fb=[]
    month_ev=[];month_fb=[]
    mtd=np.zeros(N,dtype=np.float64)
    consulted=np.zeros(N,dtype=np.int16)
    switches=np.zeros(N,dtype=bool)
    month=None
    month_equity=1.
    for d in range(N):
        if MONTHS[d]!=month:
            month=MONTHS[d]
            month_ev=[];month_fb=[]
            month_equity=1.
        before=month_equity-1.
        mtd[d]=before
        if bool(mask[d]):
            default=int(baseline_fb[d])
            if before<=trigger:
                arm,num=maybe_override(fbmethod,d,default,month_fb,
                                      prev_group_fb,fall_offer,minimum)
                consulted[d]=num
            else:
                arm=default
            fall_arm[d]=arm
            switches[d]=arm!=default
            dayret=float(fall_offer[d,arm])
            prev_group_fb.append(d)
            month_fb.append(d)
        else:
            if before<=trigger:
                arm,num=maybe_override(evmethod,d,0,month_ev,
                                      prev_group_ev,event_offer,minimum)
                consulted[d]=num
            else:
                arm=0
            event_arm[d]=arm
            switches[d]=arm!=0
            dayret=float(event_offer[d,arm])
            prev_group_ev.append(d)
            month_ev.append(d)
        if not np.isfinite(dayret):
            raise AssertionError("Invalid observed daily net account return")
        # Today's P&L affects ONLY *future* dates, not today's selection.
        month_equity*=1.+dayret
    assert len(prev_group_ev)==260 and len(prev_group_fb)==217
    assert np.all(event_arm[mask]==0)
    assert np.all((fall_arm>=0)&(fall_arm<6))
    return event_arm,fall_arm,mtd,consulted,switches


def merge_paths(event,fb,mask,e_choice,f_choice,mode):
    er=event[mode]
    fr=fb[mode]
    day=np.arange(N)
    return tuple(
        np.where(mask,b[day,f_choice],a[day,e_choice])
        for a,b in zip(er,fr)
    )


def stats(r):
    return online.metrics(*r)


def monthly_details(x):
    # All 22 months included; losing, zero and no-signal cases all count.
    return np.asarray([
       100.*(np.prod(1.+np.asarray(x)[MONTHS==name])-1.)
       for name in UNIQUE_MONTHS],dtype=float)


def write_ledger(path,ctx,choice_e,choice_f,mtd,consulted,switches,mode):
    r,fee,gross,reason,dur=path
    f=ctx["f"]
    mask=ctx["mask"]
    baseev=ctx["base_event"]
    effective_event_arm=np.where(choice_e==0,baseev,1-baseev)
    event_side=np.where(effective_event_arm==0,f["event_signs"],-f["event_signs"])
    fallback_side=f["fall_signs"][np.arange(N),ctx["fb_arms"][np.arange(N),choice_f]]
    side=np.where(mask,fallback_side,event_side)
    # Fallback arm refers to the six structural overlays, not the 4 raw
    # 21h follow/fade arms: ctx["fb_arms"] maps arm -> raw side id.
    if not np.all(np.abs(side)==1):raise AssertionError("Invalid side")
    q=pd.DataFrame(dict(
       date_ist=base.IST_DAYS,month_ist=MONTHS,year=np.asarray(base.DAYS.year),
       entry_hour_ist=ctx["entry_hour"],
       trigger_type=np.where(mask,"MANDATORY_FALLBACK","VOLUME_SIGNAL"),
       trade_side=np.where(side==1,"LONG","SHORT"),
       fallback_arm_label=[step11.ARMS[int(j)][0] if mask[i] else ""
                           for i,j in enumerate(choice_f)],
       event_opposite_override=choice_e.astype(bool),
       prior_month_to_date_net_pct=mtd*100.,
       prior_same_type_sample_count=consulted,
       chosen_arm_differs_from_step11=switches,
       net_account_return_pct=r*100.,
       gross_btc_price_points=gross,
       fee_gst_price_points=fee,
       adverse_slippage_points=2*base.SLIP,
       exit_type=np.where(reason==1,"TAKE_PROFIT",
                         np.where(reason==2,"STOP","TIMEOUT")),
       held_minutes=dur.astype(int),cost_model=mode
    ))
    if len(q)!=477 or q.date_ist.nunique()!=477 or (pd.to_datetime(q.date_ist).dt.dayofweek>=5).any():
        raise AssertionError("Model dropped weekday trade")
    monthly=q.groupby("month_ist",sort=True).agg(
        trade_days=("date_ist","size"),
        profitable_days=("net_account_return_pct",lambda x:int((x>0).sum())),
        losing_days=("net_account_return_pct",lambda x:int((x<0).sum())),
        compounded_return_pct=("net_account_return_pct",
              lambda a:float(100.*(np.prod(1.+a.to_numpy()/100.)-1.))),
        total_fee_gst_price_points=("fee_gst_price_points","sum"),
        gross_btc_price_points=("gross_btc_price_points","sum")
    ).reset_index()
    if len(monthly)!=22 or monthly.trade_days.sum()!=477:
        raise AssertionError("Monthly total missing days")
    return q,monthly


def run():
    OUT.mkdir(parents=True,exist_ok=True)
    ctx,event,default_fb,default_prior=prep_paths()
    mask=ctx["mask"]
    offer_event=event["scalper_offer"][0]
    offer_fallback=ctx["returns"]["scalper_offer"][0]
    expected={}
    zero=np.zeros(N,dtype=np.int8)
    for mode in base.MODES:
        expected[mode]=merge_paths(
            event,ctx["returns"],mask,zero,default_fb,mode)
    baseline={mode:stats(r) for mode,r in expected.items()}
    if baseline["scalper_offer"]["profitable_days"]!=279 or abs(
        baseline["scalper_offer"]["net_total_pct"]-22.141056)>.00011:
        raise AssertionError("Step11 baseline replay parity failed")
    if abs(baseline["standard"]["net_total_pct"]+7.812987)>.00011:
        raise AssertionError("Step11 standard-fee replay parity failed")
    print("STEP12_BASELINE "+json.dumps(baseline,sort_keys=True),flush=True)

    settingslist=[("baseline",0.,"fixed","fixed",2)]
    for combo in product(MTD_TRIGGER,EVENT_METHOD,FALL_METHOD,MIN_PAST):
        settingslist.append(("mtd_recovery",*combo))
    if len(settingslist)!=121:
        raise AssertionError("Expected 120 models + baseline")

    artifacts={};rows=[]
    for model,threshold,emethod,fmethod,minimum in settingslist:
        ce,cf,mtd,consulted,switched=select_chronological(
          (threshold,emethod,fmethod,minimum),
          offer_event,offer_fallback,mask,default_fb)
        artifacts[(model,threshold,emethod,fmethod,minimum)]=(
            ce,cf,mtd,consulted,switched)
        for mode in base.MODES:
            r=merge_paths(event,ctx["returns"],mask,ce,cf,mode)
            score=stats(r)
            if model=="baseline":
                if not np.allclose(r[0],expected[mode][0],rtol=0,atol=1.e-14):
                    raise AssertionError("Original daily returns not identical")
            score.update(
                model=model,mtd_trigger_pct=threshold*100.,
                event_method=emethod,fallback_method=fmethod,
                min_prior_type_days=minimum,cost_model=mode,
                event_direction_changes=int((switched&(~mask)).sum()),
                fallback_arm_changes=int((switched&mask).sum()),
                event_change_days_2025=int((switched[:TRAIN]&(~mask[:TRAIN])).sum()),
                fallback_change_days_2025=int((switched[:TRAIN]&mask[:TRAIN]).sum()),
                event_change_days_2026=int((switched[TRAIN:]&(~mask[TRAIN:])).sum()),
                fallback_change_days_2026=int((switched[TRAIN:]&mask[TRAIN:]).sum())
            rows.append(score)
    frame=pd.DataFrame(rows)
    if len(frame)!=242 or not frame.trades.eq(477).all():
        raise AssertionError("Not one trade per weekday per candidate")
    frame.to_csv(OUT/"all_120_month_recovery_policies_two_fee_schedules.csv",index=False)
    print("STEP12_GRID "+json.dumps(dict(
        models=121,cost_scenarios=242,each_trades=477,
        train_full_months=12,year2026_full_months=10),sort_keys=True),flush=True)

    offer=frame[frame.cost_model=="scalper_offer"]
    # This is the *only* selection phase: everything here is from 2025.
    qualified=offer[
        (offer.win_months_2025>=10)&
        (offer.return_2025_pct>=8.5)&
        (offer.profitable_days_2025>=147)&
        (offer.max_dd_2025<=3.05)]
    if len(qualified):
        selected=qualified.sort_values(
           ["win_months_2025","return_2025_pct","profitable_days_2025",
            "max_dd_2025"],ascending=[False,False,False,True]).iloc[0].to_dict()
        passes=True
    else:
        selected=offer[offer.model=="baseline"].iloc[0].to_dict()
        passes=False
    key=(selected["model"],
         round(float(selected["mtd_trigger_pct"])/100.,8),
         selected["event_method"],selected["fallback_method"],
         int(selected["min_prior_type_days"]))
    if key not in artifacts:
        raise AssertionError("Selected policy absent from frozen grid")
    ce,cf,mtd,consulted,switched=artifacts[key]
    details={}
    for mode in base.MODES:
        p=merge_paths(event,ctx["returns"],mask,ce,cf,mode)
        daily,months=write_ledger(p,ctx,ce,cf,mtd,consulted,switched,mode)
        daily.to_csv(OUT/(mode+"_2025_selected_477_daily.csv"),index=False)
        months.to_csv(OUT/(mode+"_2025_selected_22_months.csv"),index=False)
        result=stats(p)
        details[mode]=dict(
            result=result,
            positive_months=int((months.compounded_return_pct>0).sum()),
            positive_months_2025=int((months.compounded_return_pct[:12]>0).sum()),
            positive_months_2026=int((months.compounded_return_pct[12:]>0).sum()),
            negative_months=months.loc[months.compounded_return_pct<=0,
                                       ["month_ist","compounded_return_pct"]].to_dict("records"),
            delta_total_net_pct=round(float(result["net_total_pct"]-baseline[mode]["net_total_pct"]),6),
            delta_win_months=int(result["win_months_all"]-baseline[mode]["win_months_all"]),
            delta_win_days=int(result["profitable_days"]-baseline[mode]["profitable_days"]),
            delta_max_dd_pct=round(float(result["max_closed_dd_pct"]-baseline[mode]["max_closed_dd_pct"]),6))
        print("STEP12_SELECTED_"+mode.upper()+" "+json.dumps(details[mode],sort_keys=True),flush=True)
        print("STEP12_MONTHLY_"+mode.upper()+"\n"+months.to_string(index=False),flush=True)
    chosen_offer=details["scalper_offer"]["result"]
    promotion=(chosen_offer["win_months_all"]>=18 and
       chosen_offer["net_total_pct"]>=22.141056 and
       chosen_offer["max_closed_dd_pct"]<=3.008746 and
       chosen_offer["win_months_2026"]>=8)
    hindsight=offer.sort_values(["win_months_all","net_total_pct"],ascending=False).iloc[0].to_dict()
    hindsight_positive_18=int(((offer.win_months_all>=18)&(offer.net_total_pct>=22.141056)&
                                  (offer.max_closed_dd_pct<=3.008746)).sum())
    message={
       "experiment":"Month-to-date risk conditioned EVENT and FALLBACK direction, otherwise frozen Step11",
       "baseline":baseline,
       "all_477_ist_weekdays_each":True,
       "daily_notional_exposure":"1x 100% account",
       "models":121,"with_fee_sensitivity":242,
       "2025_qualified_monthly_candidates":int(len(qualified)),
       "primary_monthly_objective_passed_2025":passes,
       "selected_2025_rule":selected,
       "selected_results":details,
       "qualifies_for_promotion_2026_robustness":bool(promotion),
       "full_period_top_positive_months_hindsight_ONLY":hindsight,
       "hindsight_at_least18_months_total_profit_and_dd_not_worse":hindsight_positive_18,
       "fee_model":"taker0.05% per leg GST18%; hypothetical preactivated regular Scalper Offer closing leg fee waived if <=30minutes; 5 BTC quote points adverse each side",
       "limitations":[
          "All of 2025-2026 heavily researched; not pristine independent out-of-sample",
          "120 more variants add multiple-comparison risk",
          "No actual historic scalper activation or real orderbook/latency/funding simulation",
          "Prior completed day returns drive only subsequent orders; no MTD data leakage",
          "No guarantee monthly positive return with mandatory full-size daily positions"]
    }
    (OUT/"summary.json").write_text(json.dumps(message,indent=2)+"\n")
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join([
        "# Step12 — Monthly-win improvement without dropping BTC weekday trades",
        "",
        "Every one of 121 fixed policies executes precisely 477 BTCUSD trades on full IST Mon–Fri days at fixed 1x notional and original Step11 1m stop/target/lock/trailing. Only side may change on already losing months, using previous completed same-month/recent shadow outcomes.",
        "",
        "## Exact historical Step11 regression baseline",
        json.dumps(baseline,indent=2),
        "",
        "## 2025-only month-positive selection (2026 recheck, research-exposed)",
        json.dumps(selected,indent=2),
        "",
        "## Frozen selected annual and monthly summary",
        json.dumps(details,indent=2),
        "",
        "## All 22 monthly returns with hypothetical Scalper Offer",
        pd.read_csv(OUT/"scalper_offer_2025_selected_22_months.csv").to_markdown(index=False),
        "",
        "## Historical hindsight-only maximum monthly wins — NOT selected",
        json.dumps(hindsight,indent=2),
        "",
        "## Caveats",
        "Monthly direction overrides require preentry month-to-date PnL and shadow outcomes settled only on earlier calendar days. There is no genuine unseen historical 2026 test: many previous models have already used it. Real historical Scalper eligibility/fill quality, funding and bid/ask depth are not modeled."
    ])+"\n")
    print("STEP12_COMPLETE "+json.dumps(message,sort_keys=True),flush=True)

if __name__=="__main__":
    run()
