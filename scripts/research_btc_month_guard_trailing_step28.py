#!/usr/bin/env python3
"""Step28: 180 month-guard + event lock + fallback trailing combos.

Each candidate places one full-size 1x BTCUSD futures order on all 477
complete IST weekdays. Causal prior completed monthly equity determines
SL cap and trailing recipe before current entry; early close rules frozen.
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
import research_btc_net_return_factorial_step25 as step25
import research_btc_monthly_profit_peak_guard_step26 as step26

OUT=Path("analysis/btc_month_guard_trailing_step28")
N=len(base.DAYS)
TRAIN=base.NTRAIN
MONTHS=np.asarray(base.MONTH_LABELS)

GUARDS=((1.,.75),(1.,.5),(1.5,.75))
CAPS=(.18,.20,.25)
EVENT={
 "E0_original":(.25,.10),
 "E1_early_lock":(.20,.10),
 "E2_fast_small_lock":(.15,.05),
 "E3_later_larger_lock":(.30,.15)
}
FALL={
 "F0_original":(.35,.20),
 "F1_fast_tight":(.25,.15),
 "F2_fast_normal":(.25,.20),
 "F3_normal_tight":(.35,.15),
 "F4_later_wide":(.45,.25)
}
assert N==477 and TRAIN==260
assert len(GUARDS)*len(CAPS)*len(EVENT)*len(FALL)==180

def get_original(m,mask,original_side,idx,starting_cfg,policies):
    feat=step25.risk.preentry_features(m,idx,original_side)
    ordinary={}
    for direction in (-1,1):
        sides=np.full(N,direction,dtype=np.int8)
        cfg,_=step25.preentry_stop(
            starting_cfg,feat,mask,sides,"baseline")
        ordinary[direction]=step26.replay_price(m,idx,sides,cfg,policies)
    X=step25.ridge.features_at_entry(m,idx)
    forecasts,training=step25.ridge.shadow_predictions(
        X,ordinary[1][0][:,0,1],ordinary[-1][0][:,0,1],
        mask,"ridge",120,"basic")
    sides,differ=step25.ridge.choose_sides(
        original_side,forecasts,training,mask,.30,"fallback")
    assert int(differ.sum())==4 and np.all(abs(sides)==1)
    cfg,_=step25.preentry_stop(
        starting_cfg,feat,mask,sides,"tight60_050_both_cap040")
    assert np.all(cfg[~mask,0]==1) and np.all(cfg[mask,0]==2)
    raw0=step26.replay_price(m,idx,sides,cfg,policies)
    return sides,cfg,raw0

def change_trailing(cfg,mask,cap,event_name,fall_name):
    updated=cfg.copy()
    updated[:,1]=np.minimum(updated[:,1],cap)
    act,lock=EVENT[event_name]
    trailact,trail_dist=FALL[fall_name]
    updated[~mask,4]=act
    updated[~mask,5]=lock
    updated[mask,4]=trailact
    updated[mask,5]=trail_dist
    if np.any(updated[:,1]>cfg[:,1]+1.e-12):
        raise AssertionError("Stop cap may never widen initial SL")
    return updated

def draw(raw,alt,mask,ids,peak,gb):
    choice=step26.causal_month_guard(
        raw,alt,mask,ids,peak,gb,"both")
    return choice

def results(raw,alt,choice,mode):
    path=step26.path_with_flags(
        raw,alt,choice[0],choice[1],base.MODES.index(mode))
    score=step15.score(path)
    monthly=step26.month_numbers(path[0])
    assert score["trades"]==477 and len(monthly)==22
    assert int(np.sum(monthly>0))==score["win_months_all"]
    return score,monthly,path

def save_profile(tag,conf,choice,raw,alt,sides,hour,mask):
    reports={}
    for mode in base.MODES:
        score,month,p=results(raw,alt,choice,mode)
        pnl,fees,gross,reason,hold=p
        daily=pd.DataFrame(dict(
            date_ist=base.IST_DAYS,
            year=np.asarray(base.DAYS.year),
            month_ist=MONTHS,
            entry_hour_ist=hour,
            side=np.where(sides==1,"LONG","SHORT"),
            category=np.where(mask,"FALLBACK","EVENT"),
            prior_month_net_pct=choice[2]*100,
            prior_completed_peak_net_pct=choice[4]*100,
            earlier_month_peak_giveback_pp=choice[3]*100,
            month_guard_active=choice[1],
            SL_cap_pct_if_guard=conf["cap_pct"],
            event_lock=conf["event_lock"],
            fallback_trailer=conf["fallback_trailer"],
            original_closed_bar_exit_policy=choice[0],
            net_account_pct=pnl*100,
            gross_btc_points=gross,
            modeled_fee_gst_btc_points=fees,
            adverse_slip_quote_points=2*base.SLIP,
            exit_reason=reason,
            minutes_held=hold,
            cost_model=mode,
            model=tag
        ))
        if len(daily)!=477 or daily.date_ist.nunique()!=477 or (
            pd.to_datetime(daily.date_ist).dt.dayofweek>=5).any():
            raise AssertionError("One full BTC position each eligible IST weekday")
        monthly=pd.DataFrame(dict(
            month_ist=list(dict.fromkeys(MONTHS.tolist())),
            trade_days=[int(np.sum(MONTHS==v))
                        for v in list(dict.fromkeys(MONTHS.tolist()))],
            net_compounded_pct=month,
            model=tag,cost_model=mode
        ))
        assert len(monthly)==22 and monthly.trade_days.sum()==477
        daily.to_csv(OUT/(tag+"_"+mode+"_477_daily.csv"),index=False)
        monthly.to_csv(OUT/(tag+"_"+mode+"_22_months.csv"),index=False)
        reports[mode]=dict(
            metrics=score,
            January_2026_net_pct=float(month[12]),
            losing_months=monthly.loc[monthly.net_compounded_pct<=0,
                    ["month_ist","net_compounded_pct"]].to_dict("records"),
            protected_days=int(choice[1].sum()),
            protected_Jan2026_days=int(np.sum(choice[1]&(MONTHS=="2026-01"))))
    return reports

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    m,ctx,mask,fb,orig_side,hour,idx,starting_cfg=step13.create_path()
    policies,names=early.build_exit_policies()
    ids={name:i for i,name in enumerate(names)}
    sides,cfg,raw=get_original(m,mask,orig_side,idx,starting_cfg,policies)

    caches={}
    for cap,e,f in product(CAPS,EVENT,FALL):
        recipe=change_trailing(cfg,mask,cap,e,f)
        caches[(cap,e,f)]=step26.replay_price(
            m,idx,sides,recipe,policies)
        print("STEP28_1M_REPLAY "+json.dumps(dict(
            cap=cap,event=e,fallback=f,
            completed_replay_count=len(caches))),flush=True)

    canonical=(1.,.75,.20,"E0_original","F0_original")
    original_alt=caches[(.20,"E0_original","F0_original")]
    original_dec=draw(raw,original_alt,mask,ids,1.,.75)
    prior,prior_month,_=results(raw,original_alt,original_dec,"scalper_offer")
    standard,_,_=results(raw,original_alt,original_dec,"standard")
    assert prior["win_months_all"]==21 and prior["trades"]==477
    assert prior["profitable_days"]==285
    assert abs(prior["net_total_pct"]-28.332018)<.00011
    assert abs(prior_month[12]-.7796504733)<.00011
    assert abs(prior["max_closed_dd_pct"]-2.617670)<.00011
    assert abs(standard["net_total_pct"]+3.137181)<.00011
    print("STEP28_PREVIOUS_STAGE_PARITY "+json.dumps(dict(
        offer=prior,standard=standard,January2026=float(prior_month[12]),
        full_one_trade_weekdays=477)),flush=True)

    records=[]
    monthly_rows=[]
    for pg,gb in GUARDS:
        for cap,e,f in product(CAPS,EVENT,FALL):
            alt=caches[(cap,e,f)]
            choice=draw(raw,alt,mask,ids,pg,gb)
            code=f"peak{pg:g}_giveback{gb:g}_cap{cap:g}_{e}_{f}"
            for fee in base.MODES:
                s,month,p=results(raw,alt,choice,fee)
                records.append(dict(
                    name=code,prior_peak_threshold_pct=pg,
                    prior_giveback_threshold_pp=gb,cap_pct=cap,
                    event_lock=e,fallback_trailer=f,
                    protected_weekdays=int(choice[1].sum()),
                    protected_January2026=int(np.sum(choice[1]&(MONTHS=="2026-01"))),
                    January2026_net_pct=float(month[12]),
                    January2026_delta_vs_Step26_pp=float(month[12]-prior_month[12]),
                    cost_model=fee,**s))
                for j,month_label in enumerate(list(dict.fromkeys(MONTHS.tolist()))):
                    monthly_rows.append(dict(
                        name=code,cost_model=fee,month_ist=month_label,
                        account_month_net_pct=float(month[j]),
                        trade_days=int(np.sum(MONTHS==month_label))))
        print("STEP28_EQUITY_GUARD "+json.dumps(dict(
            peak_threshold=pg,giveback=gb,models_completed=len(records)//2)),flush=True)
    frame=pd.DataFrame(records)
    if len(frame)!=360 or not frame.trades.eq(477).all():
        raise AssertionError("Not all 180 model configs replayed")
    frame.to_csv(OUT/"all_180_guarded_trailing_configs_both_fee_models.csv",index=False)
    pd.DataFrame(monthly_rows).to_csv(
        OUT/"all_180_configs_22_month_returns_both_fee_models.csv",index=False)
    peer=frame[(frame.cost_model=="scalper_offer")&
        (frame.prior_peak_threshold_pct==1.)&
        (frame.prior_giveback_threshold_pp==.75)&
        (frame.cap_pct==.20)&
        (frame.event_lock=="E0_original")&
        (frame.fallback_trailer=="F0_original")].iloc[0]
    if abs(peer.net_total_pct-prior["net_total_pct"])>1.e-8:
        raise AssertionError("Original Step26 combination not exactly identical")
    print("STEP28_GRID_VERIFIED "+json.dumps(dict(
        model_variants=180,fee_results=360,weekday_positions_each=477)),flush=True)

    offer=frame[frame.cost_model=="scalper_offer"]
    qualified=offer[
        (offer.win_months_2025>=11)&
        (offer.return_2025_pct>=prior["return_2025_pct"]-1e-6)&
        (offer.profitable_days_2025>=prior["profitable_days_2025"])&
        (offer.max_dd_2025<=prior["max_dd_2025"]+1e-4)
    ]
    if len(qualified):
        selected=qualified.sort_values(
            ["return_2025_pct","win_months_2025",
             "profitable_days_2025","max_dd_2025"],
            ascending=[False,False,False,True]).iloc[0].to_dict()
    else:
        selected=peer.to_dict()

    pareto=offer[
        (offer.win_months_all>=21)&
        (offer.win_months_2026>=10)&
        (offer.max_closed_dd_pct<=prior["max_closed_dd_pct"]+1e-4)&
        (offer.net_total_pct>=prior["net_total_pct"])
    ].sort_values(
        ["January2026_net_pct","net_total_pct"],ascending=[False,False])
    pareto.to_csv(OUT/"HINDSIGHT_only_increased_January_keep_21months_net_DD.csv",index=False)
    retrospective=pareto.iloc[0].to_dict() if len(pareto) else selected
    all22=offer[offer.win_months_all==22]
    all22.to_csv(OUT/"HINDSIGHT_ONLY_22_of_22_months.csv",index=False)

    def combo(row):
        return (float(row["prior_peak_threshold_pct"]),
                float(row["prior_giveback_threshold_pp"]),
                float(row["cap_pct"]),row["event_lock"],row["fallback_trailer"])

    outputs={}
    for tag,row in (
        ("frozen_step26_baseline",peer.to_dict()),
        ("selected_on_2025_only",selected),
        ("hindsight_best_January2026_NOT_SELECTED",retrospective)
    ):
        pg,gb,cap,e,f=combo(row)
        choice=draw(raw,caches[(cap,e,f)],mask,ids,pg,gb)
        outputs[tag]=save_profile(tag,row,choice,raw,caches[(cap,e,f)],
                                  sides,hour,mask)
        print("STEP28_AUDIT_"+tag.upper()+" "+
              json.dumps(outputs[tag],sort_keys=True),flush=True)

    old=outputs["frozen_step26_baseline"]["scalper_offer"]
    new=outputs["selected_on_2025_only"]["scalper_offer"]
    legit=(new["metrics"]["net_total_pct"]>old["metrics"]["net_total_pct"]+1e-6
        and new["metrics"]["win_months_all"]>=21
        and new["metrics"]["win_months_2026"]>=10
        and new["metrics"]["max_closed_dd_pct"]<=old["metrics"]["max_closed_dd_pct"]+1.e-4
        and new["January_2026_net_pct"]>old["January_2026_net_pct"]+1e-6)
    report=dict(
        experiment="Causal prior-month-profit-giveback gated event lock activation and fallback trailing",
        historical_IST_weekdays_1x_full_account_notional=477,
        baseline_exact=outputs["frozen_step26_baseline"],
        comparisons=180,fee_sensitivity_models=360,
        qualified_on_2025_only=int(len(qualified)),
        selected_from_2025_only=selected,
        evaluated_2026_already_researched=outputs["selected_on_2025_only"],
        meets_all_5_month_profit_dd_criteria=bool(legit),
        strongest_Jan2026_hindsight_NOT_SELECTED=retrospective,
        hindsight_result=outputs["hindsight_best_January2026_NOT_SELECTED"],
        hindsight_22_out_of_22_count=int(len(all22)),
        costs="0.05% taker entry plus GST18%, 5 BTC quote points adverse slip each leg, hypothetical previously enabled regular <=30m Scalper exit fee waiver, standard both-leg fee sensitivity",
        caveats=[
          "January2026 and all other historical months researched repeatedly, not independent OOS",
          "Squeeze-fitting 2025 and viewing Jan2026 multiple times exaggerates expected returns",
          "Historical exchange Scalper Offer prior activation, real spreads/latency/funding/liquidation unverified",
          "Full weekday position may be losing in live trading; no real orders or master merge"
        ])
    (OUT/"summary.json").write_text(json.dumps(
        report,indent=2,default=lambda x:x.item() if isinstance(x,np.generic) else str(x))+"\n")
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join([
        "# BTC Step28 — month-high-water drawdown guarded trailing",
        "",
        "A grid of 180 combinations with all 477 full one-times-account-notional weekday positions, both fee models. Under trigger only, choose event profit lock activation and fallback trailing distance before entering; early exit and direction unchanged.",
        "",
        "## Frozen Step26 baseline (verified)",json.dumps(outputs["frozen_step26_baseline"],indent=2),
        "",
        "## Selected on 2025 only",json.dumps(selected,indent=2),
        "",
        "## January2026 2026-research-exposed check",json.dumps(outputs["selected_on_2025_only"],indent=2),
        "",
        "## Retrospective improved January (NOT SELECTED)",json.dumps(outputs["hindsight_best_January2026_NOT_SELECTED"],indent=2),
        "",
        "## Frozen selection, monthly outcomes",
        pd.read_csv(OUT/"selected_on_2025_only_scalper_offer_22_months.csv").to_markdown(index=False),
        "",
        "## Warnings",
        "Historical 2026 results have been mined many times, not fresh held-out data. Historical Scalper offer opt-in and market fills unknown; all normal-fee outcomes separately available."
    ])+"\n")
    print("STEP28_COMPLETE "+json.dumps(dict(
        models=180,qualified_2025=int(len(qualified)),
        original_jan2026=old["January_2026_net_pct"],
        selected_jan2026=new["January_2026_net_pct"],
        original_net=old["metrics"]["net_total_pct"],
        selected_net=new["metrics"]["net_total_pct"],
        selected_win_months=new["metrics"]["win_months_all"],
        selected_dd=new["metrics"]["max_closed_dd_pct"],
        full_promotion_criteria_met=bool(legit),
        hindsight_jan2026=outputs["hindsight_best_January2026_NOT_SELECTED"]["scalper_offer"]["January_2026_net_pct"]
    ),sort_keys=True),flush=True)

if __name__=="__main__":
    main()
