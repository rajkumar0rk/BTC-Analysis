#!/usr/bin/env python3
"""Step 8: causal nearest-neighbor direction/clock selection, one BTC trade/day.

Novelty: match continuous pre-entry price/volume features against only
previously completed EVENT or FALLBACK trading days. No current-day future
candle returns used for entry decisions. Step 6 exits are unchanged.
2025-only candidate selection; 2026 is research-exposed, not blind OOS.
"""
from pathlib import Path
from itertools import product
import json

import numpy as np
import pandas as pd

import research_btc_every_weekday_reset_step1 as base
import research_btc_every_weekday_adaptive_step2 as adaptive
import research_btc_daily_online_direction_step6 as old
import research_btc_daily_causal_regime_step5 as regime

OUT=Path("analysis/btc_daily_causal_neighbors_step8")
DAYS=base.DAYS
N=len(DAYS)
TRAIN=base.NTRAIN
WINDOWS=(45,90,180)
K_NEIGHBORS=(12,24,36)
SCORES=("net","win","risk")
MARGINS=("none","conservative")
FEATURES=("compact","extended")
EVENT_OPTIONS=("step6","neighbors")
FALL_OPTIONS=("fixed","neighbors")
ARM_SPACES=("21_only","21_or_22")
MODES=base.MODES
EXPECTED=len(WINDOWS)*len(K_NEIGHBORS)*len(SCORES)*len(MARGINS)*len(FEATURES)*len(EVENT_OPTIONS)*len(FALL_OPTIONS)*len(ARM_SPACES)
assert EXPECTED==864 and N==477 and TRAIN==260

def compute_preentry_context(m,starts,hours,day_signs):
    """Pure past-minute features evaluated at a planned minute OPEN."""
    op=m.open.to_numpy(float)
    close=m.close.to_numpy(float)
    hi=m.high.to_numpy(float)
    lo=m.low.to_numpy(float)
    vol=m.volume.to_numpy(float)
    out=np.zeros((N,10),dtype=float)
    for d in range(N):
        i=int(starts[d])
        last=float(close[i-1])
        # Every one of these observations ends at i-1, strictly before entry.
        r5=last/float(op[i-5])-1
        r15=last/float(op[i-15])-1
        r60=last/float(op[i-60])-1
        r240=last/float(op[i-240])-1
        cur=float(np.sum(vol[i-5:i]))
        prev=vol[i-105:i-5].reshape(20,5).sum(axis=1)
        mv=float(np.mean(prev))
        volume_ratio=cur/mv if mv>0 else 1.0
        span60=float(np.max(hi[i-60:i])-np.min(lo[i-60:i]))
        loc60=(last-float(np.min(lo[i-60:i])))/span60 if span60>0 else .5
        range60=span60/float(op[i])
        span15=float(np.max(hi[i-15:i])-np.min(lo[i-15:i]))
        oldspans=np.array([
            float(np.max(hi[i-15*(z+2):i-15*(z+1)])-
                  np.min(lo[i-15*(z+2):i-15*(z+1)]))
            for z in range(6)
        ])
        oldmedian=float(np.median(oldspans))
        range_ratio=span15/oldmedian if oldmedian>0 else 1.
        bside=float(day_signs[d])
        # The reference side (event fade5 / fallback follow5) sets a
        # direction-neutral viewpoint; raw signs never learned from future.
        out[d]=(
          bside*r5/.0015,
          bside*r15/.003,
          bside*r60/.007,
          bside*r240/.015,
          (volume_ratio-1.)/1.2,
          bside*(loc60-.5)*2,
          range60/.01,
          (range_ratio-1.0)/1.5,
          (hours[d]-20.)/2.,
          1. if np.sign(r5)==np.sign(r60) else -1.
        )
    if not np.isfinite(out).all():raise AssertionError("Nonfinite past-only feature")
    return np.clip(out,-3.,3.)

def feature_view(arr,kind):
    # Explicit, frozen Euclidean feature weights. NO global fitting.
    if kind=="compact":
        idx=[0,1,2,4,5]
    else:
        idx=[0,1,2,3,4,5,6,7,8,9]
    return arr[:,idx]

def causal_nearest(features,returns,active,window,k,scoring,margin,arm_count):
    """For each day, shadow-reward ranking over prior same-type weekdays only.

    Event / fallback outcomes from *other* current-day counterfactual arms are
    NEVER considered when making that day's choice.
    """
    n,arm_total=returns.shape
    assert features.shape[0]==n and active.shape==(n,)
    assert arm_count<=arm_total
    choices=np.zeros(n,dtype=np.int8)
    usable=np.zeros(n,dtype=np.int16)
    median_distance=np.full(n,np.nan)
    for d in range(n):
        if not active[d]:continue
        prior=np.flatnonzero(active[:d])[-window:]
        if len(prior)<12:continue
        # Similarity computed using fixed pre-entry feature map.
        dist=np.sqrt(np.sum((features[prior,:]-features[d,:])**2,axis=1))
        count=min(int(k),len(prior))
        chosen_nn=np.argsort(dist,kind="mergesort")[:count]
        hist=prior[chosen_nn]
        if np.any(hist>=d):raise AssertionError("Training included future day")
        weights=1./(.35+dist[chosen_nn])
        weights=weights/np.sum(weights)
        sample=returns[hist,:arm_count]
        mean=np.sum(sample*weights[:,None],axis=0)
        if scoring=="net":
            scores=mean
            threshold=.0003 if margin=="conservative" else 0.
        elif scoring=="win":
            scores=np.sum((sample>0.)*weights[:,None],axis=0)
            threshold=.05 if margin=="conservative" else 0.
        elif scoring=="risk":
            loss=np.sqrt(np.sum(np.minimum(sample,0.)**2*weights[:,None],axis=0))
            scores=mean-.30*loss
            threshold=.0003 if margin=="conservative" else 0.
        else:
            raise KeyError(scoring)
        best=int(np.argmax(scores))
        # If indistinguishable, choose the stable baseline arm zero.
        if best>0 and scores[best]>scores[0]+threshold:
            choices[d]=best
        usable[d]=count
        median_distance[d]=float(np.median(dist[chosen_nn]))
    return choices,usable,median_distance

def initial_dataset(m):
    f=old.retrieve(m)
    starts,_,_=base.prepare(m)
    mask=f["isfallback"]
    day=np.arange(N)
    # On the actual event minute the old FADE5 side gives canonical sign.
    event_idx=starts[day,f["event_hours"]]
    event_side=f["event_signs"].astype(np.int8)
    event_feats=compute_preentry_context(m,event_idx,f["event_hours"],event_side)
    # At fallback, choose arm and time using info available at 21:00.
    base21=starts[:,21]
    fallside=f["fall_signs"][:,0]   # 21 FOLLOW5 baseline
    fallback_feats=compute_preentry_context(
        m,base21,np.full(N,21),fallside)
    # EXACT Step6 selected event online policy, trained on modeled offer cost.
    e_idx,e_hist=old.prior_online_choices(
        f["event"][1][0],~mask,f["eventimpulse"],
        "online_impulse5",30,"net","conservative")
    f_idx=np.zeros(N,dtype=np.int8)
    ref={}
    for mode_i,mode in enumerate(MODES):
        path,c,g,why,hold=old.pick_path(
            f["event"][mode_i],e_idx,
            f["fallback"][mode_i,"E"],f_idx,mask)
        ref[mode]=(path,c,g,why,hold)
    if int(np.sum((e_idx==1)&(~mask)))!=20:
        raise AssertionError("Step6 event direction count changed")
    if int(np.sum(mask))!=217 or int(np.sum(~mask))!=260:
        raise AssertionError("Step6 source counts changed")
    return f,mask,event_feats,fallback_feats,e_idx,e_hist,ref

def aggregate(path,fees,gross,why,hold):
    x=base.score(path,fees,gross,np.full(N,2*base.SLIP),why)
    x["max_dd_2025_pct"]=float(
        old.adaptive.period_dd(path[:TRAIN]) if hasattr(old.adaptive,"period_dd") else np.nan)
    # known max-dd implementation in adaptive step2
    x["max_dd_2025_pct"]=old.adaptive.period_dd(path[:TRAIN])
    x["max_dd_2026_pct"]=old.adaptive.period_dd(path[TRAIN:])
    x["longest_losing_streak"]=base.max_loss_run(path<0)
    x["mean_held_minutes"]=round(float(np.mean(hold)),3)
    return x

def combine(f,mask,ev_choice,fall_choice,mode_i):
    return old.pick_path(
       f["event"][mode_i],ev_choice,
       f["fallback"][mode_i,"E"],fall_choice,mask)

def write_daily(path,fee,gross,why,hold,mask,f,ev_choice,fb_choice,ev_used,fb_used):
    labels=np.asarray(old.FALL_ARMS,dtype=str)
    hours=np.where(mask,np.array([int(old.FALL_ARMS[int(x)][:2]) for x in fb_choice]),
                   f["event_hours"])
    dirs=np.where(mask,f["fall_signs"][np.arange(N),fb_choice],
                  np.where(ev_choice==0,f["event_signs"],-f["event_signs"]))
    if np.any(dirs==0):raise AssertionError("Invalid pre-entry direction")
    d=pd.DataFrame(dict(
        day_ist=base.IST_DAYS,
        year=np.array(DAYS.year),
        month_ist=base.MONTH_LABELS,
        hour_ist=hours.astype(int),
        entry_side=np.where(dirs==1,"LONG","SHORT"),
        entry_kind=np.where(mask,"MANDATORY_FALLBACK","VOLUME_EVENT"),
        selected_arm=np.where(mask,labels[fb_choice],
                              np.where(ev_choice==0,"FADE5","FOLLOW5")),
        neighbors_used=np.where(mask,fb_used,ev_used),
        return_net_account_pct=path*100,
        gross_btc_points=gross,
        fee_gst_btc_points=fee,
        adverse_slippage_price_points=2*base.SLIP,
        exit_reason=np.where(why==1,"TP",
                    np.where(why==2,"PROTECTIVE_STOP","TIMEOUT")),
        hold_minutes=hold.astype(int)
    ))
    if d.day_ist.nunique()!=477:raise AssertionError("Missing daily trade")
    months=d.groupby("month_ist",sort=True).agg(
        trades=("day_ist","count"),
        win_days=("return_net_account_pct",lambda a:int(np.sum(a>0))),
        lose_days=("return_net_account_pct",lambda a:int(np.sum(a<0))),
        compounded_net_account_pct=("return_net_account_pct",
                   lambda a:float((np.prod(1+a.to_numpy()/100)-1.)*100.)),
        gross_points=("gross_btc_points","sum"),
        fees_gst_points=("fee_gst_btc_points","sum")
    ).reset_index()
    if len(months)!=22:raise AssertionError("Wrong month coverage")
    return d,months

def run():
    OUT.mkdir(parents=True,exist_ok=True)
    m=base.load()
    f,mask,event_data,fall_data,baseev,baseevhist,reference=initial_dataset(m)
    baseline={}
    for mode in MODES:
        baseline[mode]=aggregate(*reference[mode])
    if baseline["scalper_offer"]["profitable_days"]!=275 or abs(
       baseline["scalper_offer"]["net_total_pct"]-17.7862)>0.00011:
        raise AssertionError("Step6 benchmark parity failure "+str(baseline["scalper_offer"]))
    if abs(baseline["standard"]["net_total_pct"]+11.101745)>0.00011:
        raise AssertionError("Step6 standard fee sensitivity parity failure")
    print("STEP8_BASELINE "+json.dumps(baseline,sort_keys=True),flush=True)
    # Train all *selection* scores in hypothetical Scalper Offer model ONLY.
    event_offer=f["event"][1][0]
    fallback_offer=f["fallback"][1,"E"][0]
    choices_e={}
    choices_f={}
    for fm,w,k,score,margin in product(FEATURES,WINDOWS,K_NEIGHBORS,SCORES,MARGINS):
        key=(fm,w,k,score,margin)
        evfeats=feature_view(event_data,fm)
        fbfeats=feature_view(fall_data,fm)
        choices_e[key]=causal_nearest(
            evfeats,event_offer,~mask,w,k,score,margin,2)
        for space in ARM_SPACES:
            choices_f[key,space]=causal_nearest(
                fbfeats,fallback_offer,mask,w,k,score,margin,
                4 if space=="21_only" else 8)
    print("STEP8_CAUSAL_CHOICE_TABLES "+json.dumps(dict(
        event_tables=len(choices_e),fallback_tables=len(choices_f),
        each_table_days=N,training_only_from_days_before_current=True),
        sort_keys=True),flush=True)
    rows=[]
    for fm,w,k,score,margin,evmode,fbmode,armspace in product(
        FEATURES,WINDOWS,K_NEIGHBORS,SCORES,MARGINS,
        EVENT_OPTIONS,FALL_OPTIONS,ARM_SPACES):
        key=(fm,w,k,score,margin)
        eventev,evcnt,_=choices_e[key] if evmode=="neighbors" else (
            baseev,baseevhist,np.full(N,np.nan))
        if fbmode=="neighbors":
            fallbackarm,fbcnt,_=choices_f[key,armspace]
        else:
            fallbackarm=np.zeros(N,dtype=np.int8)
            fbcnt=np.zeros(N,dtype=np.int16)
        if np.any(eventev>1) or np.any(fallbackarm>=8):raise AssertionError("Unexpected arm")
        # Cost repricing is on identical choices; standard outcomes do not
        # influence the online selection of event or fallback arms.
        for mi,mode in enumerate(MODES):
            path,fee,gross,why,hold=combine(f,mask,eventev,fallbackarm,mi)
            z=aggregate(path,fee,gross,why,hold)
            z.update(
                features=fm,prior_window=w,k_neighbors=k,scoring=score,
                preference=margin,event_selector=evmode,
                fallback_selector=fbmode,fallback_arms=armspace,
                cost_model=mode,
                event_direction_changes=int(np.sum((eventev!=baseev)&(~mask))),
                event_follow5_days=int(np.sum((eventev==1)&(~mask))),
                fallback_nonbaseline_days=int(np.sum((fallbackarm!=0)&mask)),
                fallback_22h_days=int(np.sum((fallbackarm>=4)&mask)),
                event_minhistory_defaults=int(np.sum((evcnt<12)&(~mask))) if evmode=="neighbors" else 0,
                fallback_minhistory_defaults=int(np.sum((fbcnt<12)&mask)) if fbmode=="neighbors" else 0
            )
            rows.append(z)
    tab=pd.DataFrame(rows)
    if len(tab)!=EXPECTED*2 or not tab.trades.eq(477).all():
        raise AssertionError("Wrong candidate count or trade coverage")
    tab.to_csv(OUT/"all_864_policies_two_fee_models.csv",index=False)
    print("STEP8_GRID "+json.dumps(dict(
        actual_fee_scenarios=len(tab),policies=EXPECTED,
        exact_trade_days_per_policy=int(tab.trades.min()),
        event_days=int(np.sum(~mask)),mandatory_fallback_days=int(np.sum(mask))),
        sort_keys=True),flush=True)
    # Candidate ranking is entirely 2025-only, single chosen fee schedule.
    offer=tab[tab.cost_model=="scalper_offer"].copy()
    eligible=offer[(offer.return_2025_pct>=3.)&
        (offer.profitable_days_2025>=145)&
        (offer.max_dd_2025_pct<=4.)]
    if len(eligible):
        selected=eligible.sort_values(
            ["profitable_days_2025","return_2025_pct","max_dd_2025_pct"],
            ascending=[False,False,True]).iloc[0].to_dict()
    else:
        selected=offer.sort_values(
            ["return_2025_pct","profitable_days_2025"],
            ascending=[False,False]).iloc[0].to_dict()
    cfg=(selected["features"],int(selected["prior_window"]),
         int(selected["k_neighbors"]),selected["scoring"],selected["preference"])
    if selected["event_selector"]=="neighbors":
        ce,ne,_=choices_e[cfg]
    else:ce,ne=baseev,baseevhist
    if selected["fallback_selector"]=="neighbors":
        cf,nf,_=choices_f[cfg,selected["fallback_arms"]]
    else:cf,nf=np.zeros(N,dtype=np.int8),np.zeros(N,dtype=np.int16)

    reports={}
    for mi,mode in enumerate(MODES):
        path,fee,gross,why,hold=combine(f,mask,ce,cf,mi)
        daily,monthly=write_daily(path,fee,gross,why,hold,mask,f,ce,cf,ne,nf)
        daily.to_csv(OUT/(mode+"_selected_477_days.csv"),index=False)
        monthly.to_csv(OUT/(mode+"_selected_22_months.csv"),index=False)
        oldpath,oldfee,oldgross,oldwhy,oldhold=reference[mode]
        olddaily,oldmonthly=write_daily(oldpath,oldfee,oldgross,oldwhy,oldhold,
                 mask,f,baseev,np.zeros(N,dtype=np.int8),baseevhist,np.zeros(N,dtype=np.int16))
        olddaily.to_csv(OUT/(mode+"_Step6_baseline_477_days.csv"),index=False)
        oldmonthly.to_csv(OUT/(mode+"_Step6_baseline_22_months.csv"),index=False)
        z=aggregate(path,fee,gross,why,hold)
        reports[mode]=dict(selected_result=z,
             profitable_months=int(np.sum(monthly.compounded_net_account_pct>0)),
             worst_month_pct=round(float(monthly.compounded_net_account_pct.min()),5),
             year2025_win_change=int(z["profitable_days_2025"]-baseline[mode]["profitable_days_2025"]),
             year2026_win_change=int(z["profitable_days_2026"]-baseline[mode]["profitable_days_2026"]),
             year2025_profit_change_pct=round(float(z["return_2025_pct"]-baseline[mode]["return_2025_pct"]),5),
             year2026_profit_change_pct=round(float(z["return_2026_pct"]-baseline[mode]["return_2026_pct"]),5))
    allbest=offer.sort_values(["net_total_pct","profitable_days"],ascending=False).iloc[0].to_dict()
    both=(offer.return_2025_pct>0)&(offer.return_2026_pct>0)
    strict=(offer.profitable_days>baseline["scalper_offer"]["profitable_days"])&(
      offer.net_total_pct>baseline["scalper_offer"]["net_total_pct"])&(
      offer.max_closed_dd_pct<baseline["scalper_offer"]["max_closed_dd_pct"])
    summary=dict(
        purpose="One BTCUSD futures trade per full IST weekday, direction chosen solely from earlier comparable days",
        exact_trade_count=477,model_policies=EXPECTED,
        num_fee_scenarios=len(tab),selected_on_2025_only=selected,
        candidates_passing_precommitted_train_thresholds=int(len(eligible)),
        unchanged_step6_baseline=baseline,
        selected_fixed_policy_standard_fee_sensitivity=reports,
        hindsight_profitable_in_both_years_count=int(np.sum(both)),
        hindsight_all_metric_pareto_better_count=int(np.sum(strict)),
        full_sample_highest_net_hindsight_NOT_selected=allbest,
        finance_assumptions="1x account notional, 5 BTC price points adverse each side, 0.05% taker each side+18% GST; alternative assumes previously activated regular Scalper Offer <=30min closing waiver",
        limitations=["2026 has repeatedly been researched and is NOT pristine forward validation",
            "864 parameter combinations create severe multiple-comparison optimism",
            "Historical scalper activation cannot be verified from OHLCV",
            "No actual spread/orderbook depth, latency, funding, liquidations or tick-level intrabar ordering",
            "A mandatory trade each weekday does not guarantee a profitable day"])
    (OUT/"summary.json").write_text(json.dumps(summary,indent=2)+"\n")
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join([
        "# Step 8 — online nearest-neighbor mandatory BTC daily direction",
        "",
        "Causal match of PREENTRY volume/price conditions to PAST completed weekday events. 477/477 trading days; exits unchanged from Step6. Selection uses 2025 only; 2026 is already research-exposed.",
        "",
        "## Verified identical Step6 baseline",json.dumps(baseline,indent=2),
        "",
        "## 2025-selected nearest-neighbor rule",json.dumps(selected,indent=2),
        "",
        "## Its 2025 / 2026 performance and unchanged decisions under standard fees",json.dumps(reports,indent=2),
        "",
        "## Winning months (Scalper Offer)","",
        pd.read_csv(OUT/"scalper_offer_selected_22_months.csv").to_markdown(index=False),
        "",
        "## Prior Step6 baseline monthly results","",
        pd.read_csv(OUT/"scalper_offer_Step6_baseline_22_months.csv").to_markdown(index=False),
        "",
        "## Warnings","The online direction algorithm has no same-day future price access, but prior strategy optimization has already repeatedly examined 2026. The historical best-of-many result is NOT out-of-sample validation. Actual Scalper Offer activation and execution costs are unverified."
    ])+"\n")
    print("STEP8_SELECTED_SCALPER "+json.dumps(dict(selected=selected,reports=reports,
        hindsight_count=summary["hindsight_all_metric_pareto_better_count"],
        hindsight_full_best=allbest),sort_keys=True),flush=True)
    print("STEP8_COMPLETE",flush=True)

if __name__=="__main__":
    run()
