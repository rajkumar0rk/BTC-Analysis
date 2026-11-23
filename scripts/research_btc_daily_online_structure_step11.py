#!/usr/bin/env python3
"""Step 11 — prior-fallback-day-only online selection of structural BTC direction.

Exactly 477 entries on 477 full IST weekdays. All earlier Step8 event times,
event-side choices, 21h fallback times and exit recipes are unchanged.
Only which deterministic fallback direction rule to apply can change, using
results of strictly EARLIER completed fallback days (no look-ahead).
"""
from pathlib import Path
from itertools import product
import json

import numpy as np
import pandas as pd

import research_btc_every_weekday_reset_step1 as base
import research_btc_daily_online_direction_step6 as online
import research_btc_daily_structure_step10 as structural

OUT=Path("analysis/btc_daily_online_structure_step11")
N=len(base.DAYS)
TRAIN=base.NTRAIN
MODES=base.MODES
ARMS=(
    ("baseline",None,0),
    ("donchian120_fade1","donchian120_fade",1),
    ("edge60_follow0","edge60_follow",0),
    ("momentum60_fade1","momentum60_fade",1),
    ("sma20v60_follow0","sma20v60_follow",0),
    ("vwap0900_fade0","vwap0900_fade",0)
)
WINDOWS=(30,60,90)
POOL=("baseline_plus_donchian","all_6_arms")
SCORING=("net","win","risk")
PREFERENCE=("none","conservative")
EXPECTED=len(WINDOWS)*len(POOL)*len(SCORING)*len(PREFERENCE)
assert EXPECTED==36 and N==477 and TRAIN==260

def shadow(m):
    f,mask,be,bf,idx,hours,bsides,reference,_=structural.baseline_context(m)
    past=structural.build_structure(m,idx)
    outcomes={}
    fbarms=[]
    changes=[]
    for label,kind,level in ARMS:
        if kind is None:
            fb=bf.copy()
            changed=np.zeros(N,dtype=bool)
        else:
            _,fb,changed=structural.choose(kind,level,"fallback",
                      f,mask,be,bf,bsides,past)
        fbarms.append(fb)
        changes.append(changed)
    fb_indices=np.stack(fbarms,axis=1).astype(np.int8)
    changed=np.stack(changes,axis=1)
    arrays={}
    for mode_i,mode in enumerate(MODES):
        arms=[]
        for ai in range(len(ARMS)):
            result=online.pick_path(f["event"][mode_i],be,
                         f["fallback"][mode_i,"E"],fb_indices[:,ai],mask)
            arms.append(result)
        arrays[mode]=tuple(np.stack([arm[j] for arm in arms],axis=1)
                           for j in range(5))
    # Exact Step8 per-trade return parity on both fee schedules.
    for mi,mode in enumerate(MODES):
        r=arrays[mode][0][:,0]
        if not np.allclose(r,reference[mode][0],atol=1.e-14,rtol=0):
            raise AssertionError("Baseline Step8 per-trade fee parity drift")
    return dict(
        f=f,mask=mask,base_event=be,baseline_fb=bf,
        priceside=bsides,entry_hour=hours,fb_arms=fb_indices,
        changed=changed,returns=arrays)

def score_for(past,metric):
    if metric=="net":
        return past.mean(axis=0)
    if metric=="win":
        return (past>0).mean(axis=0)
    if metric=="risk":
        risk=np.sqrt(np.mean(np.minimum(past,0)**2,axis=0))
        return past.mean(axis=0)-.3*risk
    raise KeyError(metric)

def choose_online(returns,mask,window,pool,scoring,preference):
    # Score EVERY option as if taken on past days only; never consult
    # current/future counterfactual P&L to decide an order.
    choices=np.zeros(N,dtype=np.int8)
    prior_n=np.zeros(N,dtype=np.int16)
    diff=np.full(N,np.nan)
    narm=2 if pool=="baseline_plus_donchian" else 6
    for d in range(N):
        if not mask[d]:continue
        prior=np.flatnonzero(mask[:d])[-window:]
        prior_n[d]=len(prior)
        if len(prior)<15:continue
        if int(prior[-1])>=d:raise AssertionError("Future daily outcome leakage")
        score=score_for(returns[prior,:narm],scoring)
        winner=int(np.argmax(score))
        threshold=(.05 if scoring=="win" else .0003) if preference=="conservative" else 0.
        if winner>0 and score[winner]>score[0]+threshold:
            choices[d]=winner
            diff[d]=score[winner]-score[0]
    assert choices.shape==(477,) and np.all(choices<narm)
    return choices,prior_n,diff

def chosen_results(arr,choice):
    days=np.arange(N)
    return tuple(x[days,choice] for x in arr)

def summary(p,fee,gross,reason,hold):
    return online.metrics(p,fee,gross,reason,hold)

def ledger(p,fee,gross,reason,hold,selection,prior,ctx,mode):
    mask=ctx["mask"]
    f=ctx["f"]
    fb_arm=ctx["fb_arms"][np.arange(N),selection]
    side=np.where(mask,f["fall_signs"][np.arange(N),fb_arm],
                  np.where(ctx["base_event"]==0,
                           f["event_signs"],-f["event_signs"]))
    traded_side=np.where(side>0,"LONG","SHORT")
    df=pd.DataFrame(dict(
        day_ist=base.IST_DAYS,
        year=np.asarray(base.DAYS.year),
        month_ist=base.MONTH_LABELS,
        entry_hour_ist=ctx["entry_hour"],
        trade_side=traded_side,
        entry_type=np.where(mask,"MANDATORY_FALLBACK","VOLUME_SIGNAL"),
        selected_rule=[ARMS[int(i)][0] for i in selection],
        prior_completed_fallback_days=prior,
        direction_changed_from_step8=np.where(
            mask,ctx["changed"][np.arange(N),selection],False),
        net_account_pct=p*100,
        gross_btc_price_points=gross,
        fee_gst_price_points=fee,
        adverse_slip_points=base.SLIP*2,
        exit_type=np.where(reason==1,"TP",np.where(reason==2,"STOP","TIMEOUT")),
        hold_min=hold,fee_mode=mode))
    assert df.day_ist.nunique()==477 and (pd.to_datetime(df.day_ist).dt.dayofweek<5).all()
    month=df.groupby("month_ist",sort=True).agg(
        trades=("day_ist","size"),
        winning_days=("net_account_pct",lambda s:int(np.sum(s>0))),
        losing_days=("net_account_pct",lambda s:int(np.sum(s<0))),
        compounded_return_pct=("net_account_pct",lambda s:float(
            100*(np.prod(1+s.to_numpy()/100)-1))),
        fees_gst_price_points=("fee_gst_price_points","sum"),
        gross_btc_price_points=("gross_btc_price_points","sum")
    ).reset_index()
    assert len(month)==22
    return df,month

def run():
    OUT.mkdir(parents=True,exist_ok=True)
    m=base.load()
    ctx=shadow(m)
    assert int(ctx["mask"].sum())==217 and int((~ctx["mask"]).sum())==260
    benchmark={}
    for mode in MODES:
        benchmark[mode]=summary(*tuple(a[:,0] for a in ctx["returns"][mode]))
    assert benchmark["scalper_offer"]["profitable_days"]==277
    assert abs(benchmark["scalper_offer"]["net_total_pct"]-21.423313)<.00011
    assert abs(benchmark["standard"]["net_total_pct"]+8.354948)<.00011
    print("STEP11_BASELINE "+json.dumps(benchmark,sort_keys=True),flush=True)
    # Fixed ARM P&L is historical counterfactual data only: used AFTER each
    # respective completed prior day, NEVER current day decision leakage.
    offer_ret=ctx["returns"]["scalper_offer"][0]
    policychoices={("baseline",):(
       np.zeros(N,dtype=np.int8),np.zeros(N,dtype=np.int16),np.full(N,np.nan))}
    for win,pool,score,margin in product(WINDOWS,POOL,SCORING,PREFERENCE):
        policychoices[win,pool,score,margin]=choose_online(
            offer_ret,ctx["mask"],win,pool,score,margin)
    records=[]
    for setting,(choice,prior,diff) in policychoices.items():
        for mi,mode in enumerate(MODES):
            res=chosen_results(ctx["returns"][mode],choice)
            stat=summary(*res)
            stat.update(
                policy="baseline" if setting==("baseline",) else "online",
                prior_window=0 if setting==("baseline",) else setting[0],
                arm_pool="baseline" if setting==("baseline",) else setting[1],
                learning_score="none" if setting==("baseline",) else setting[2],
                preference="none" if setting==("baseline",) else setting[3],
                cost_model=mode,
                fallback_alternate_selected_days=int(np.sum((choice>0)&ctx["mask"])),
                fallback_alternate_2025_days=int(np.sum((choice[:TRAIN]>0)&ctx["mask"][:TRAIN])),
                fallback_alternate_2026_days=int(np.sum((choice[TRAIN:]>0)&ctx["mask"][TRAIN:])),
                actual_different_direction_days=int(np.sum(
                   ctx["changed"][np.arange(N),choice]&ctx["mask"]))
            )
            records.append(stat)
    df=pd.DataFrame(records)
    if len(df)!=2*(EXPECTED+1) or not df.trades.eq(477).all():
        raise AssertionError("Expected 477 daily entries for every policy")
    df.to_csv(OUT/"all_36_online_structure_models_plus_baseline_two_fees.csv",index=False)
    print("STEP11_GRID "+json.dumps(dict(
        policies=EXPECTED+1,fee_scenarios=len(df),daily_entries=477,
        train_2025_days=TRAIN,check_2026_days=N-TRAIN),sort_keys=True),flush=True)
    offer=df[df.cost_model=="scalper_offer"].copy()
    qualified=offer[(offer.profitable_days_2025>=147)&
        (offer.return_2025_pct>=8.10265)&(offer.max_dd_2025<=3.00875)]
    if len(qualified):
        ranked=qualified.sort_values(
            ["profitable_days_2025","return_2025_pct","max_dd_2025",
             "fallback_alternate_selected_days"],
            ascending=[False,False,True,True],kind="mergesort")
    else:
        ranked=offer[offer.policy=="baseline"]
    chosen=ranked.iloc[0].to_dict()
    key=("baseline",) if chosen["policy"]=="baseline" else (
        int(chosen["prior_window"]),chosen["arm_pool"],
        chosen["learning_score"],chosen["preference"])
    choice,prior,diff=policychoices[key]
    report={}
    for mode in MODES:
        res=chosen_results(ctx["returns"][mode],choice)
        day,month=ledger(*res,choice,prior,ctx,mode)
        day.to_csv(OUT/(mode+"_selected_477_daily.csv"),index=False)
        month.to_csv(OUT/(mode+"_selected_22_months.csv"),index=False)
        stats=summary(*res)
        report[mode]=dict(
            result=stats,positive_months=int((month.compounded_return_pct>0).sum()),
            worst_month_pct=round(float(month.compounded_return_pct.min()),5),
            delta_win_days_2025=stats["profitable_days_2025"]-benchmark[mode]["profitable_days_2025"],
            delta_win_days_2026=stats["profitable_days_2026"]-benchmark[mode]["profitable_days_2026"],
            delta_net_2025_pct=round(stats["return_2025_pct"]-benchmark[mode]["return_2025_pct"],5),
            delta_net_2026_pct=round(stats["return_2026_pct"]-benchmark[mode]["return_2026_pct"],5))
        print("STEP11_SELECTED_"+mode.upper()+" "+json.dumps(report[mode],sort_keys=True),flush=True)
        print("STEP11_MONTHLY_"+mode.upper()+"\n"+month.to_string(index=False),flush=True)
    both=(offer.return_2025_pct>0)&(offer.return_2026_pct>0)
    improve=(offer.profitable_days>277)&(offer.net_total_pct>21.423313)&(
        offer.max_closed_dd_pct<=3.008746)&(offer.win_months_all>=15)
    hindsight=offer.sort_values(
        ["net_total_pct","profitable_days"],ascending=False).iloc[0].to_dict()
    results=dict(
      purpose="Realistically choose alternate BTC daily fallback direction from prior completed day PnL only",
      mandatory_477_ist_weekday_trades=True,model_policies=EXPECTED+1,
      cost_scenarios=len(df),original_step8_benchmark=benchmark,
      eligible_2025_only_models=int(len(qualified)),
      selected_from_2025_only=chosen,selected_results=report,
      full_sample_hindsight_max_profit_NOT_selected=hindsight,
      historical_improved_all_metrics_vs_step8_hindsight=int(np.sum(improve)),
      positive_both_years_count_hindsight=int(np.sum(both)),
      exact_event_entries=260,exact_mandatory_fallbacks=217,
      historic_fee_models="0.05% taker each leg+18% GST, hypothetical prior activated Scalper Offer waives <=30m closing fee; 5 quote BTC points slippage each leg, 1x account notional",
      limitations=["2026 previously researched extensively, NOT a blind independent holdout",
        "No historical proof of Scalper Offer activation; real L1/L2 spreads, funding, latency, fills and liquidations excluded",
        "Scoring past hypothetical counterfactual returns is not executing those arms live",
        "Many prior trials and choosing a model after examining 2025 history create selection optimism"])
    (OUT/"summary.json").write_text(json.dumps(results,indent=2)+"\n")
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join([
      "# BTCUSD Step11 — online structural fallback policy selector with mandatory 477 weekdays",
      "",
      "Every candidate trades ONE BTCUSD futures position on EACH full IST Mon–Fri date. Event entry and side and all stop/target/trailing rules frozen from Step8; only 21h fallback direction may differ.",
      "",
      "## Step8 regression baseline",json.dumps(benchmark,indent=2),
      "",
      "## 2025-selected online selector",json.dumps(chosen,indent=2),
      "",
      "## 2026 research-exposed historical recheck",json.dumps(report,indent=2),
      "",
      "## Selected monthly report (Scalper)",pd.read_csv(
        OUT/"scalper_offer_selected_22_months.csv").to_markdown(index=False),
      "",
      "## Cautions","2026 is research-exposed, not a blind holdout. Real offer activation, execution, funding and tick-level order effects are unmodeled. Forward paper trading needed before any real order."
    ])+"\n")
    print("STEP11_COMPLETE "+json.dumps(results,sort_keys=True),flush=True)

if __name__=="__main__":
    run()
