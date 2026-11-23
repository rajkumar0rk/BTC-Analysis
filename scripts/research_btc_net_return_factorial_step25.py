#!/usr/bin/env python3
"""Step25: optimize *net after costs* with 672 BTC daily factorial combinations.

Combine either Step20-B frozen side or Step22-Ridge (120d/basic/0.30
fallback) with eight preentry SL caps and causal earlier-month PnL-driven
event/fallback early exits. All 477 full IST weekdays have a 1x position.
2025-only model selection, prior-researched 2026 recheck, hindsight clear.
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
import research_btc_daily_preentry_risk_step18 as risk
import research_btc_daily_supervised_side_step22 as ridge
import research_btc_daily_month_start_direction_step17 as step17
import audit_btc_daily_risk_crosscheck_step20 as step20

OUT=Path("analysis/btc_net_return_factorial_step25")
N=len(base.DAYS)
TRAIN=base.NTRAIN
MONTHS=np.asarray(base.MONTH_LABELS)
SIDES=("original_B","ridge120_fallback")
STOPS=(
    "baseline",
    "edgeagainst20_cap025",
    "against60_015_cap030",
    "highvol125_cap030",
    "lowvol090_cap025",
    "wide60_050_cap030",
    "tight60_050_both_cap040",
    "event_highvol175_cap030",
)
EVENTS=(
    "baseline",
    "negative_mtd_cut008_after5",
    "negative_mtd_cut008_after15",
    "negative_mtd_cut012_after10",
    "positive_mtd_profit015_after20",
    "positive_mtd_timeout20",
)
FALLBACKS=(
    "baseline",
    "negative_mtd_profit010_after10",
    "negative_mtd_profit010_after15",
    "negative_mtd_profit010_after5",
    "negative_mtd_cut008_after5",
    "positive_mtd_no_extra_exit",
    "positive_mtd_profit010_after20",
)
assert N==477 and TRAIN==260
assert len(SIDES)*len(STOPS)*len(EVENTS)*len(FALLBACKS)==672

def preentry_stop(recipe,feat,mask,side,stop_name):
    cfg=recipe.copy()
    cfg,_,_=step20.build_capped(
        recipe,feat,np.asarray(side,dtype=np.int8),mask,
        ("with60","counter5")
    )
    r60=feat["r60"]
    v=feat["rvol5"]
    pos=feat["loc60"]
    extent=feat["range60"]
    if stop_name=="baseline":
        cond=np.zeros(N,dtype=bool)
        cap=None
    elif stop_name=="edgeagainst20_cap025":
        cond=mask & (((side<0)&(pos>=.80))|((side>0)&(pos<=.20)))
        cap=.25
    elif stop_name=="against60_015_cap030":
        cond=mask &(side*r60<=-.0015)
        cap=.30
    elif stop_name=="highvol125_cap030":
        cond=mask &(v>=1.25)
        cap=.30
    elif stop_name=="lowvol090_cap025":
        cond=mask &(v<=.90)
        cap=.25
    elif stop_name=="wide60_050_cap030":
        cond=mask &(extent>=.005)
        cap=.30
    elif stop_name=="tight60_050_both_cap040":
        cond=extent<=.005
        cap=.40
    elif stop_name=="event_highvol175_cap030":
        cond=(~mask)&(v>=1.75)
        cap=.30
    else:
        raise KeyError(stop_name)
    if cap is not None:
        cfg[cond,1]=np.minimum(cfg[cond,1],cap)
    if not np.all(cfg[:,1]<=recipe[:,1]+1.e-12):
        raise AssertionError("Invalid SL widening")
    if np.any(np.abs(side)!=1) or len(cfg)!=477:
        raise AssertionError("An entry side was not chosen")
    return cfg,int(np.sum(cfg[:,1]<recipe[:,1]-1e-12))

def replay(m,indices,side,recipe,policies):
    return early.replay_with_nextbar_exits(
        m.open.to_numpy(float),m.high.to_numpy(float),
        m.low.to_numpy(float),m.close.to_numpy(float),
        indices,side,recipe,policies,base.COST,base.SLIP)

def combine(long,short,side):
    return step17.select_sign_arrays(long,short,side)

def day_choices(raw,mask,event_policy,fallback_policy,ids):
    """Returns preentry-chosen extra exits; today's PnL updates TOMORROW."""
    idx=np.zeros(N,dtype=np.int16)
    before=np.zeros(N)
    peakgive=np.zeros(N)
    prevlosses=np.zeros(N,dtype=np.int8)
    month=None
    eq=1.
    peak=1.
    losing_streak=0
    extra_event=0
    extra_fall=0
    base_adverse=ids["adverse_cut_0.08pct_after_10m"]
    base_profit10=ids["profit_close_at_0.1pct_after_10m"]
    base_profit20=ids["profit_close_at_0.1pct_after_20m"]
    for d in range(N):
        if MONTHS[d]!=month:
            month=MONTHS[d]
            eq=1.
            peak=1.
            losing_streak=0
        mtd=eq-1.
        before[d]=mtd
        peakgive[d]=peak-eq
        prevlosses[d]=losing_streak
        if mask[d]:
            # Base Step15 B special early exit.
            if mtd>=.01:
                x=base_profit10
            elif mtd<=.0025:
                x=base_profit20
            else:
                x=0
            old=x
            if fallback_policy=="negative_mtd_profit010_after10" and mtd<=0:
                x=base_profit10
            elif fallback_policy=="negative_mtd_profit010_after15" and mtd<=0:
                x=ids["profit_close_at_0.1pct_after_15m"]
            elif fallback_policy=="negative_mtd_profit010_after5" and mtd<=0:
                x=ids["profit_close_at_0.1pct_after_5m"]
            elif fallback_policy=="negative_mtd_cut008_after5" and mtd<=0:
                x=ids["adverse_cut_0.08pct_after_5m"]
            elif fallback_policy=="positive_mtd_no_extra_exit" and mtd>=.01:
                x=0
            elif fallback_policy=="positive_mtd_profit010_after20" and mtd>=.01:
                x=base_profit20
            elif fallback_policy not in FALLBACKS:
                raise KeyError(fallback_policy)
            if old!=x:
                extra_fall+=1
        else:
            x=base_adverse if mtd<=0 else 0
            old=x
            if event_policy=="negative_mtd_cut008_after5" and mtd<=0:
                x=ids["adverse_cut_0.08pct_after_5m"]
            elif event_policy=="negative_mtd_cut008_after15" and mtd<=0:
                x=ids["adverse_cut_0.08pct_after_15m"]
            elif event_policy=="negative_mtd_cut012_after10" and mtd<=0:
                x=ids["adverse_cut_0.12pct_after_10m"]
            elif event_policy=="positive_mtd_profit015_after20" and mtd>=.005:
                x=ids["profit_close_at_0.15pct_after_20m"]
            elif event_policy=="positive_mtd_timeout20" and mtd>=.005:
                x=ids["hard_timeout_20m"]
            elif event_policy not in EVENTS:
                raise KeyError(event_policy)
            if old!=x:
                extra_event+=1
        idx[d]=x
        gain=float(raw[0][d,x,1])
        if not np.isfinite(gain):
            raise AssertionError("Nonfinite daily return")
        eq*=1.+gain
        peak=max(peak,eq)
        losing_streak=losing_streak+1 if gain<0 else 0
    return idx,before,peakgive,prevlosses,extra_event,extra_fall

def score(raw,choices,mode_idx):
    path=step15.getout(raw,choices,mode_idx)
    return step15.score(path)

def generate_ledger(tag,model_name,model,side,mask,indices,hours,fee,raw):
    choices,mtd,giveback,loss_streak,_,_=model
    mi=base.MODES.index(fee)
    return_path=step15.getout(raw,choices,mi)
    daily,monthly=step15.saved_ledger(
        return_path,choices,mtd,giveback,indices,hours,side,mask,fee
    )
    daily["previous_month_consecutive_losses"]=loss_streak
    daily["model"]=model_name
    assert len(daily)==477 and daily.day_ist.nunique()==477 and (
        pd.to_datetime(daily.day_ist).dt.dayofweek<5).all()
    assert len(monthly)==22 and monthly.trade_days.sum()==477
    daily.to_csv(OUT/(tag+"_"+fee+"_477_daily.csv"),index=False)
    monthly.to_csv(OUT/(tag+"_"+fee+"_22_months.csv"),index=False)
    z=step15.score(return_path)
    assert z["win_months_all"]==int(np.sum(monthly.net_compounded_pct>0))
    return z,monthly

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    m,ctx,mask,fb,original_side,hours,indices,base_cfg=step13.create_path()
    policies,policy_names=early.build_exit_policies()
    ids={label:i for i,label in enumerate(policy_names)}
    feat=risk.preentry_features(m,indices,original_side)
    raw_by_stop={}
    stop_changed={}
    for stop_name in STOPS:
        sides={}
        count=0
        for sign in (-1,1):
            sd=np.full(N,sign,dtype=np.int8)
            cfg,number=preentry_stop(base_cfg,feat,mask,sd,stop_name)
            sides[sign]=replay(m,indices,sd,cfg,policies)
            count+=number
        raw_by_stop[stop_name]=sides
        stop_changed[stop_name]=count
        print("STEP25_1M_PRICE_REPLAY "+json.dumps(dict(
            stop=stop_name,historical_sidewise_capped=count)),flush=True)

    # Replay exact Step20 B fallback + event original side, earlier models.
    base_raw=combine(raw_by_stop["baseline"][1],
                     raw_by_stop["baseline"][-1],original_side)
    step13.check_parity(replay(m,indices,original_side,base_cfg,policies),ctx,fb)
    base_choices=day_choices(base_raw,mask,"baseline","baseline",ids)
    base_offer=score(base_raw,base_choices[0],1)
    base_standard=score(base_raw,base_choices[0],0)
    if (base_offer["trades"]!=477 or
        base_offer["win_months_all"]!=21 or
        base_offer["profitable_days"]!=292 or
        abs(base_offer["net_total_pct"]-25.423847)>.00011 or
        abs(base_offer["max_closed_dd_pct"]-2.617670)>.00011 or
        abs(base_standard["net_total_pct"]+5.332682)>.00011):
        raise AssertionError("Step20 B regression failed "+str(base_offer))
    X=ridge.features_at_entry(m,indices)
    scores,train_n=ridge.shadow_predictions(
        X,raw_by_stop["baseline"][1][0][:,0,1],
        raw_by_stop["baseline"][-1][0][:,0,1],
        mask,"ridge",120,"basic")
    proposed,changed=ridge.choose_sides(
        original_side,scores,train_n,mask,.30,"fallback")
    assert int(changed.sum())==4
    candidate_sides=dict(
       original_B=original_side,
       ridge120_fallback=proposed)
    ridge_raw=combine(raw_by_stop["baseline"][1],
                      raw_by_stop["baseline"][-1],proposed)
    ridge_policy=day_choices(ridge_raw,mask,"baseline","baseline",ids)
    ridge_offer=score(ridge_raw,ridge_policy[0],1)
    ridge_standard=score(ridge_raw,ridge_policy[0],0)
    if (ridge_offer["win_months_all"]!=21 or
        ridge_offer["profitable_days"]!=294 or
        abs(ridge_offer["net_total_pct"]-26.468595)>.00011 or
        abs(ridge_offer["max_closed_dd_pct"]-2.617670)>.00011):
        raise AssertionError("Step22 Ridge model regression failed "+str(ridge_offer))
    print("STEP25_BASELINE_VERIFIED "+json.dumps(dict(
         Step20_B_offer=base_offer,Step20_B_standard=base_standard,
         Step22_Ridge_offer=ridge_offer,Step22_Ridge_standard=ridge_standard,
         ridge_actual_side_changes=int(changed.sum())
    ),sort_keys=True),flush=True)

    rows=[]
    for side_name,stop_name in product(SIDES,STOPS):
        s=candidate_sides[side_name]
        left=raw_by_stop[stop_name]
        raw=combine(left[1],left[-1],s)
        for event_name,fall_name in product(EVENTS,FALLBACKS):
            exits=day_choices(raw,mask,event_name,fall_name,ids)
            meta=dict(
                model="__".join([side_name,stop_name,event_name,fall_name]),
                direction=side_name,stop_policy=stop_name,
                event_exit=event_name,fallback_exit=fall_name,
                changed_fallback_sides=int(np.sum(s!=original_side)),
                changed_event_exits=exits[4],
                changed_fallback_exits=exits[5])
            for mi,fee in enumerate(base.MODES):
                performance=score(raw,exits[0],mi)
                rows.append(dict(**meta,cost_model=fee,**performance))
        print("STEP25_FACTORS "+json.dumps(dict(
            side=side_name,stop=stop_name,
            scenarios_completed=len(rows)//2)),flush=True)
    table=pd.DataFrame(rows)
    if len(table)!=1344 or not table.trades.eq(477).all():
        raise AssertionError("Missing full-size mandatory weekday trades")
    table.to_csv(OUT/"all_672_net_after_fee_factorial_candidates.csv",index=False)
    print("STEP25_GRID "+json.dumps(dict(
        models=672,fee_results=1344,each_weekday_trades=477,
        years="2025 and Jan-Oct 2026")),flush=True)

    offer=table[table.cost_model=="scalper_offer"].copy()
    valid=offer[
        (offer.win_months_2025>=11)&
        (offer.return_2025_pct>=base_offer["return_2025_pct"]-1e-6)&
        (offer.profitable_days_2025>=base_offer["profitable_days_2025"])&
        (offer.max_dd_2025<=base_offer["max_dd_2025"]+1.e-4)]
    if len(valid):
        selected=valid.sort_values(
            ["return_2025_pct","win_months_2025",
             "profitable_days_2025","max_dd_2025"],
            ascending=[False,False,False,True]).iloc[0].to_dict()
    else:
        selected=offer[
            (offer.direction=="original_B")&
            (offer.stop_policy=="baseline")&
            (offer.event_exit=="baseline")&
            (offer.fallback_exit=="baseline")].iloc[0].to_dict()
    # Full-period best strictly for DIAGNOSTIC. Never use these to select
    # a future trading policy, because 2026 is already research-exposed.
    eligible_all=offer[
        (offer.win_months_all>=21)&
        (offer.win_months_2026>=10)&
        (offer.max_closed_dd_pct<=2.617670+1.e-4)]
    peak=eligible_all.sort_values(
        ["net_total_pct","win_months_all","profitable_days"],
        ascending=[False,False,False])
    peak.to_csv(OUT/"HINDSIGHT_ONLY_best_net_with_21_months_and_dd_guard.csv",index=False)
    profit_all=offer.sort_values(
        ["net_total_pct","win_months_all"],ascending=[False,False])
    profit_all.head(50).to_csv(OUT/"HINDSIGHT_ONLY_all_max_net_top50.csv",index=False)
    if len(peak):
        hindsight=peak.iloc[0].to_dict()
    else:
        hindsight=selected

    out={}
    for tag,chosen in (
        ("selected_using_2025_only",selected),
        ("hindsight_net_guarded_NOT_SELECTED",hindsight)):
        side=candidate_sides[chosen["direction"]]
        stop=chosen["stop_policy"]
        raw=combine(raw_by_stop[stop][1],raw_by_stop[stop][-1],side)
        p=day_choices(raw,mask,chosen["event_exit"],chosen["fallback_exit"],ids)
        scores_by_cost={}
        for fee in base.MODES:
            z,month=generate_ledger(
                tag,chosen["model"],p,side,mask,indices,hours,fee,raw)
            src=table[(table.model==chosen["model"])&
                      (table.cost_model==fee)].iloc[0]
            if abs(src.net_total_pct-z["net_total_pct"])>1e-8:
                raise AssertionError("Selected re-simulation net drift")
            scores_by_cost[fee]=dict(
                metrics=z,losing_months=month.loc[
                   month.net_compounded_pct<=0,
                   ["month_ist","net_compounded_pct"]].to_dict("records"),
                fees_btc_quote_points=float(np.sum(
                    step15.getout(raw,p[0],base.MODES.index(fee))[1]))
            )
        out[tag]=dict(model=chosen["model"],results=scores_by_cost)
        print("STEP25_SELECTED_"+tag.upper()+" "+
            json.dumps(out[tag],sort_keys=True),flush=True)

    best_standard=table[table.cost_model=="standard"].sort_values(
          "net_total_pct",ascending=False).iloc[0].to_dict()
    result=dict(
        topic="BTC daily mandatory net after-fee optimization using causal Ridge, SL regimes and monthly early exits",
        controls=dict(Original_B=base_offer,Ridge_120_fallback=ridge_offer),
        original_477_ist_weekdays_full_1x_notional=True,
        unique_models=672,both_fee_scenarios=1344,
        qualifying_on_2025_only=int(len(valid)),
        frozen_2025_selected=selected,
        selected_results=out["selected_using_2025_only"],
        hindsight_ONLY_best_21months_lowDD=hindsight,
        hindsight_results=out["hindsight_net_guarded_NOT_SELECTED"],
        hindsight_candidate_count=int(len(eligible_all)),
        best_full_period_standard_fee_even_if_negative=best_standard,
        promotion_screen=dict(
           all_22month_net_gain_over_Ridge=(
               out["selected_using_2025_only"]["results"]["scalper_offer"]["metrics"]["net_total_pct"]>26.468595),
           all_22month_months_21plus=(
               out["selected_using_2025_only"]["results"]["scalper_offer"]["metrics"]["win_months_all"]>=21),
           2026_months_10of10=(
               out["selected_using_2025_only"]["results"]["scalper_offer"]["metrics"]["win_months_2026"]>=10),
           drawdown_no_worse_2p61767=(
               out["selected_using_2025_only"]["results"]["scalper_offer"]["metrics"]["max_closed_dd_pct"]<=2.617670+1.e-4)),
        costs="5 BTCUSD quote points adverse slippage each leg; 0.05% taker per leg plus18% GST; hypothetical preactivated regular <=30-minute Scalper closing fee waiver vs standard both-leg taker",
        limits=[
          "2025-2026 repeatedly researched; neither model selection nor 2026 historical check proves a live trading edge",
          "Ridge inherited 2026-exposed modeling decisions and only four fallback sides differ from original",
          "Scalper activation unknown historically, and normal taker costs produced losses in earlier models",
          "No L1/L2 spreads or live order fill/latency, funding, margin, liquidation, tick ordering model",
          "Even 21/22 positive historical months will not guarantee monthly profits"]
    )
    (OUT/"summary.json").write_text(json.dumps(
        result,indent=2,default=lambda x:x.item() if isinstance(x,np.generic) else str(x))+"\n")
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join([
       "# Step25 — BTC net-profit factorial optimization (all 477 weekdays)",
       "",
       "All 672 models retain one 1x-notional trade on all 477 full IST weekdays with same hourly event/fallback entry clock. Compare after actual modeled entry fee/GST, eligible assumed Scalper closing waiver, adverse quote-point slippage. Standard-fee scenario reprices SAME trades.",
       "",
       "## Validated exact existing baselines",json.dumps(result["controls"],indent=2),
       "",
       "## 2025-only selected model and researched 2026",
       json.dumps(result["selected_results"],indent=2),
       "",
       "## Hindsight ONLY maximum net with 21/22 months and DD guard",
       json.dumps(result["hindsight_results"],indent=2),
       "",
       "## Both models' 22 monthly returns",
       pd.read_csv(OUT/"selected_using_2025_only_scalper_offer_22_months.csv").to_markdown(index=False),
       "",
       "## Standard fees — maximum net among entire fixed grid",
       json.dumps(best_standard,indent=2),
       "",
       "## Caveats",
       "The years have been repeatedly searched. In-sample profit gains cannot establish a robust live edge, and regular Scalper Offer activation must be verified with actual live account settings and fills. No funding/spread/orderbook realism."
    ])+"\n")
    print("STEP25_COMPLETE "+json.dumps(dict(
        models=672,qualifying_2025=len(valid),
        selected=selected["model"],
        selected_offer=out["selected_using_2025_only"]["results"]["scalper_offer"]["metrics"],
        hindsight=hindsight["model"],
        hindsight_offer=out["hindsight_net_guarded_NOT_SELECTED"]["results"]["scalper_offer"]["metrics"],
        best_normal_taker_net=best_standard["net_total_pct"]
    ),sort_keys=True),flush=True)

if __name__=="__main__":
    main()
