#!/usr/bin/env python3
"""Step27: 324 preregistered causal month-peak SL + extra exit combinations.

Exactly one 1x BTCUSD futures order on EACH 477 complete IST weekday.
Ridge fallback prediction, fixed entry hour/side, TP/lock/trailer retained.
Only past complete month trades decide the stop cap and 1m exit overlay.
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

OUT=Path("analysis/btc_month_guard_exits_step27")
N=len(base.DAYS)
TRAIN=base.NTRAIN
MONTHS=np.asarray(base.MONTH_LABELS)
GUARDS=((1.,.75),(1.,.50),(1.5,.75),(.5,.75))
CAPS=(.15,.20,.25)
SCOPES=("event_only","fallback_only","both")
EXITS=(
    "baseline",
    "guard_profit010_after5","guard_profit010_after10",
    "guard_profit010_after15","guard_profit015_after15",
    "guard_profit015_after20","guard_adverse008_after5",
    "guard_adverse008_after10","guard_hard_timeout20"
)
assert N==477 and TRAIN==260
assert len(GUARDS)*len(CAPS)*len(SCOPES)*len(EXITS)==324

def named_exit_id(kind,ids):
    if kind=="baseline":return None
    names={
        "guard_profit010_after5":"profit_close_at_0.1pct_after_5m",
        "guard_profit010_after10":"profit_close_at_0.1pct_after_10m",
        "guard_profit010_after15":"profit_close_at_0.1pct_after_15m",
        "guard_profit015_after15":"profit_close_at_0.15pct_after_15m",
        "guard_profit015_after20":"profit_close_at_0.15pct_after_20m",
        "guard_adverse008_after5":"adverse_cut_0.08pct_after_5m",
        "guard_adverse008_after10":"adverse_cut_0.08pct_after_10m",
        "guard_hard_timeout20":"hard_timeout_20m"
    }
    return ids[names[kind]]

def replay_guard(base_raw,alt_raw,mask,ids,guard,cap,scope,extra):
    """Candidate day's stop+exit determined exclusively from earlier trades.

    Even when an adverse exit becomes eligible after N minutes, actual
    fill occurs NEXT 1m OPEN, per exact original 1m stop-first engine.
    """
    peak_threshold,giveback_threshold=guard
    override=named_exit_id(extra,ids)
    selected=np.zeros(N,dtype=np.int16)
    active=np.zeros(N,dtype=bool)
    prior_month=np.zeros(N)
    prior_peak=np.zeros(N)
    prior_giveback=np.zeros(N)
    month=None
    eq=1.;eqmax=1.
    n_diff_exit=0
    for d in range(N):
        if MONTHS[d]!=month:
            month=MONTHS[d]
            eq=1.;eqmax=1.
        mtd=eq-1.
        gb=eqmax-eq
        prior_month[d]=mtd
        prior_peak[d]=eqmax-1.
        prior_giveback[d]=gb
        allowed=(scope=="both" or
                 (scope=="event_only" and not mask[d]) or
                 (scope=="fallback_only" and mask[d]))
        triggered=(allowed and
                   eqmax>=1.+peak_threshold/100. and
                   gb>=giveback_threshold/100.)
        active[d]=triggered
        if mask[d]:
            # Frozen Stage25 conditional fallback early exit:
            # +0.1% previous 1m close after20m if prior MTD<=+.25%,
            # NO extra exit for higher MTD (including >=+1%).
            original_exit=(ids["profit_close_at_0.1pct_after_20m"]
                           if mtd<=.0025 else 0)
        else:
            original_exit=(ids["adverse_cut_0.08pct_after_10m"]
                           if mtd<=0 else 0)
        selection=(override if triggered and override is not None
                   else original_exit)
        selected[d]=selection
        if selection!=original_exit:
            n_diff_exit+=1
        # Daily *assumed offer* realized net updates ONLY the next day.
        today=float((alt_raw if triggered else base_raw)[0][d,selection,1])
        if not np.isfinite(today) or today<=-1.:
            raise AssertionError("Bad realized return in monthly state")
        eq*=1.+today
        eqmax=max(eqmax,eq)
    return selected,active,prior_month,prior_peak,prior_giveback,n_diff_exit

def score_and_month(base_raw,alt_raw,dec,mode):
    policy,active=dec[:2]
    p=step26.path_with_flags(base_raw,alt_raw,policy,active,
                             base.MODES.index(mode))
    s=step15.score(p)
    month=step26.month_numbers(p[0])
    assert s["trades"]==477 and len(month)==22
    assert int(np.sum(month>0))==s["win_months_all"]
    return s,month,p

def build_model_data(m,ctx,mask,idx,starting_cfg,policies,labels):
    feat=step25.risk.preentry_features(m,idx,ctx)
    shadows={}
    for sign in (-1,1):
        sides=np.full(N,sign,dtype=np.int8)
        cfg,_=step25.preentry_stop(starting_cfg,feat,mask,sides,"baseline")
        shadows[sign]=step26.replay_price(m,idx,sides,cfg,policies)
    X=step25.ridge.features_at_entry(m,idx)
    confidence,nobs=step25.ridge.shadow_predictions(
        X,shadows[1][0][:,0,1],shadows[-1][0][:,0,1],
        mask,"ridge",120,"basic")
    sides,different=step25.ridge.choose_sides(
        ctx,confidence,nobs,mask,.30,"fallback")
    assert np.sum(different)==4
    cfg,_=step25.preentry_stop(
        starting_cfg,feat,mask,sides,"tight60_050_both_cap040")
    raw=step26.replay_price(m,idx,sides,cfg,policies)
    caps={}
    for stop in CAPS:
        copy=cfg.copy()
        copy[:,1]=np.minimum(copy[:,1],stop)
        assert np.all(copy[:,1]<=cfg[:,1]+1e-12)
        caps[stop]=step26.replay_price(m,idx,sides,copy,policies)
    return sides,cfg,raw,caps,different

def detail_csv(tag,configuration,dec,raw,cap_raw,sides,idx,hour,mask,cap_value):
    output={}
    name=configuration
    pol,active,mtd,peak,gb,changed_exit=dec
    for mi,mode in enumerate(base.MODES):
        metrics,monthly,p=score_and_month(raw,cap_raw,dec,mode)
        pnl,fees,gross,reason,minutes=p
        daily=pd.DataFrame(dict(
            date_ist=base.IST_DAYS,
            month_ist=MONTHS,
            year=np.asarray(base.DAYS.year),
            entry_hour_ist=hour,
            entry_type=np.where(mask,"FALLBACK","EVENT"),
            side=np.where(sides>0,"LONG","SHORT"),
            prior_completed_mtd_pct=mtd*100.,
            previous_completed_month_peak_pct=peak*100.,
            previous_peak_giveback_percentage_points=gb*100.,
            month_profit_guard_active=active,
            applied_initial_stop_cap_pct=np.where(active,cap_value,np.nan),
            selected_previous_bar_early_exit_policy=pol,
            net_account_daily_pct=pnl*100.,
            gross_quote_points=gross,
            fee_gst_quote_points=fees,
            adverse_slip_quote_points=base.SLIP*2,
            exit_reason_code=reason,
            minutes_held=minutes,
            model=name,cost_model=mode
        ))
        if (len(daily)!=477 or daily.date_ist.nunique()!=477 or
            (pd.to_datetime(daily.date_ist).dt.dayofweek>=5).any()):
            raise AssertionError("Not exactly one completed IST weekday trade")
        report=pd.DataFrame(dict(
            month_ist=list(dict.fromkeys(MONTHS.tolist())),
            trading_days=[int(np.sum(MONTHS==month))
                          for month in list(dict.fromkeys(MONTHS.tolist()))],
            net_account_month_pct=monthly,
            model=name,cost_model=mode
        ))
        assert len(report)==22 and report.trading_days.sum()==477
        daily.to_csv(OUT/(tag+"_"+mode+"_477_trades.csv"),index=False)
        report.to_csv(OUT/(tag+"_"+mode+"_22_months.csv"),index=False)
        output[mode]=dict(
            metrics=metrics,
            January_2026=float(monthly[12]),
            losing_months=report.loc[
                report.net_account_month_pct<=0,
                ["month_ist","net_account_month_pct"]].to_dict("records"),
            guard_activated_days=int(active.sum()),
            guard_activated_January2026=int(np.sum(active&(MONTHS=="2026-01"))),
            exit_overrides=int(changed_exit))
    return output

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    m,ctx,mask,fb,original_side,hour,idx,start_cfg=step13.create_path()
    policy,names=early.build_exit_policies()
    ids={value:i for i,value in enumerate(names)}
    sides,cfg,raw,cap_cache,diff=build_model_data(
        m,original_side,mask,idx,start_cfg,policy,names)
    # Step26 verified model, selected using 2025 only.
    original_cfg=((1.,.75),.20,"both","baseline")
    original_dec=replay_guard(raw,cap_cache[.20],mask,ids,*original_cfg)
    base_offer,base_mo,_=score_and_month(
        raw,cap_cache[.20],original_dec,"scalper_offer")
    base_std,_,_=score_and_month(
        raw,cap_cache[.20],original_dec,"standard")
    if not (
        base_offer["trades"]==477 and
        base_offer["win_months_all"]==21 and
        abs(base_offer["net_total_pct"]-28.332018)<.00011 and
        abs(base_offer["max_closed_dd_pct"]-2.617670)<.00011 and
        abs(base_offer["profitable_days"]-285)<1e-4 and
        abs(base_mo[12]-.7796504733)<.00011 and
        abs(base_std["net_total_pct"]+3.137181)<.00011
    ):
        raise AssertionError("Verified Step26 exact baseline failed: "+
                             str(base_offer)+" January "+str(base_mo[12]))
    print("STEP27_BASELINE_VERIFIED "+json.dumps(dict(
        offer=base_offer,normal_taker=base_std,
        january2026=float(base_mo[12]),
        all_positions_full_size=477,
        previous_month_state_only=True)),flush=True)

    records=[]
    month_rows=[]
    variants=[]
    for peak,gb in GUARDS:
        for cap,scope,extra in product(CAPS,SCOPES,EXITS):
            model=f"peak_{peak:g}_giveback_{gb:g}_cap_{cap:g}_{scope}_{extra}"
            cfg_variant=((peak,gb),cap,scope,extra)
            alternatives=cap_cache[cap]
            dec=replay_guard(raw,alternatives,mask,ids,
                             cfg_variant[0],cfg_variant[1],
                             cfg_variant[2],cfg_variant[3])
            variants.append((model,cfg_variant))
            for fee in base.MODES:
                performance,month,p=score_and_month(raw,alternatives,dec,fee)
                records.append(dict(
                    model=model,guard_min_peak_pct=peak,
                    guard_min_giveback_pp=gb,cap_pct=cap,
                    scope=scope,guard_exit_overlay=extra,
                    guard_days=int(dec[1].sum()),
                    guard_days_Jan2026=int(np.sum(dec[1]&(MONTHS=="2026-01"))),
                    changed_early_exit_days=int(dec[5]),
                    January2026_net_pct=float(month[12]),
                    January2026_delta_vs_Step26_pp=float(month[12]-base_mo[12]),
                    cost_model=fee,**performance
                ))
                months=list(dict.fromkeys(MONTHS.tolist()))
                for k,month_id in enumerate(months):
                    month_rows.append(dict(model=model,cost_model=fee,
                        month_ist=month_id,net_account_compounded_pct=float(month[k]),
                        positions=int(np.sum(MONTHS==month_id))))
        print("STEP27_PEAK_GRID "+json.dumps(dict(
            month_peak_threshold=peak,giveback_threshold=gb,
            checked_models=len(variants))),flush=True)
    table=pd.DataFrame(records)
    if len(table)!=648 or not table.trades.eq(477).all():
        raise AssertionError("One or more of 324 mandatory weekday configurations missing")
    table.to_csv(OUT/"all_324_month_guard_exit_combinations_both_fees.csv",index=False)
    pd.DataFrame(month_rows).to_csv(
        OUT/"all_324_models_22_months_both_fees.csv",index=False)
    guard_peer=table[(table.cost_model=="scalper_offer")&
         (table.guard_min_peak_pct==1.)&
         (table.guard_min_giveback_pp==.75)&
         (table.cap_pct==.20)&
         (table.scope=="both")&
         (table.guard_exit_overlay=="baseline")].iloc[0]
    if abs(guard_peer.net_total_pct-base_offer["net_total_pct"])>.000001:
        raise AssertionError("In-grid Step26 guard control did not reproduce exact PnL")

    offer=table[table.cost_model=="scalper_offer"].copy()
    admissible=offer[
        (offer.win_months_2025>=11)&
        (offer.return_2025_pct>=base_offer["return_2025_pct"]-1e-6)&
        (offer.profitable_days_2025>=base_offer["profitable_days_2025"])&
        (offer.max_dd_2025<=base_offer["max_dd_2025"]+1e-4)
    ]
    if len(admissible):
        selected=admissible.sort_values(
            ["return_2025_pct","win_months_2025",
            "profitable_days_2025","max_dd_2025"],
            ascending=[False,False,False,True]).iloc[0].to_dict()
    else:
        selected=dict(model="Step26_frozen",guard_min_peak_pct=1.,
                      guard_min_giveback_pp=.75,
                      cap_pct=.20,scope="both",
                      guard_exit_overlay="baseline")
    retrospective=offer[
        (offer.win_months_all>=21)&
        (offer.win_months_2026>=10)&
        (offer.max_closed_dd_pct<=base_offer["max_closed_dd_pct"]+1e-4)&
        (offer.net_total_pct>=base_offer["net_total_pct"])
    ].sort_values(
        ["January2026_net_pct","net_total_pct"],ascending=[False,False])
    candidates22=offer[offer.win_months_all==22]
    candidates22.to_csv(OUT/"hindsight_only_22_positive_months.csv",index=False)
    retrospective.head(40).to_csv(
        OUT/"hindsight_only_january_better_with_full_net_and_DD_guard.csv",index=False)

    def cfg_from_row(row):
        return ((float(row["guard_min_peak_pct"]),
                 float(row["guard_min_giveback_pp"])),
                float(row["cap_pct"]),row["scope"],
                row["guard_exit_overlay"])

    records_for_audit={
        "frozen_Step26_control":(
            original_cfg,original_dec,raw,cap_cache[.20]),
        "selected_2025_only":None,
        "highest_January2026_hindsight_NOT_SELECTED":None
    }
    selected_cfg=cfg_from_row(selected)
    selected_dec=replay_guard(raw,cap_cache[selected_cfg[1]],mask,ids,
                               selected_cfg[0],selected_cfg[1],
                               selected_cfg[2],selected_cfg[3])
    records_for_audit["selected_2025_only"]=(
        selected_cfg,selected_dec,raw,cap_cache[selected_cfg[1]])
    if len(retrospective):
        hindsight=retrospective.iloc[0].to_dict()
        hindsight_cfg=cfg_from_row(hindsight)
        hindsight_dec=replay_guard(raw,cap_cache[hindsight_cfg[1]],mask,ids,
                              hindsight_cfg[0],hindsight_cfg[1],
                              hindsight_cfg[2],hindsight_cfg[3])
    else:
        hindsight=dict(selected)
        hindsight_cfg=selected_cfg
        hindsight_dec=selected_dec
    records_for_audit["highest_January2026_hindsight_NOT_SELECTED"]=(
        hindsight_cfg,hindsight_dec,raw,cap_cache[hindsight_cfg[1]])

    audited={}
    for tag,(cfg_key,decision,baseline,alternative) in records_for_audit.items():
        audited[tag]=detail_csv(
            tag,tag,decision,baseline,alternative,
            sides,idx,hour,mask,cfg_key[1])
        print("STEP27_RESULT_"+tag.upper()+" "+
            json.dumps(audited[tag],sort_keys=True),flush=True)

    chosen=audited["selected_2025_only"]["scalper_offer"]["metrics"]
    jan=audited["selected_2025_only"]["scalper_offer"]["January_2026"]
    admitted_forward_like=(chosen["win_months_all"]>=21 and
      chosen["win_months_2026"]>=10 and
      chosen["net_total_pct"]>base_offer["net_total_pct"]+1e-6 and
      chosen["max_closed_dd_pct"]<=base_offer["max_closed_dd_pct"]+1e-4 and
      jan>float(base_mo[12])+1e-6)
    report=dict(
        research="BTC Step27 monthly high-water stop and 1m closed-bar early exit factorial",
        full_1x_account_exposure_477_weekdays=True,
        baseline_step26_hypothetical_offer=base_offer,
        baseline_step26_Jan2026_pct=float(base_mo[12]),
        baseline_step26_standard=base_std,
        grid_candidates=324,
        both_fee_results=648,
        qualified_2025_only_count=int(len(admissible)),
        2025_selected_rule=selected,
        2025_selected_2026_research_exposed=audited["selected_2025_only"],
        meets_all_profit_January_month_drawdown_conditions=bool(admitted_forward_like),
        retrospective_Jan2026_best_NOT_SELECTED=hindsight,
        retrospective_result=audited["highest_January2026_hindsight_NOT_SELECTED"],
        hindsight_full_22_profitable_months_count=int(len(candidates22)),
        fee_assumptions="0.05% taker/GST18%, 5 BTC quote points adverse per side, hypothetical <=30min previously opted-in Scalper closing waiver",
        cautions=[
            "Historical Jan2026 repeatedly examined and only retrospective selection for it is invalid OOS",
            "Both 2025 and 2026 extensively researched; frozen prior family historically selected",
            "True historic Scalper Offer opt-in and real bid/ask/executions/funding/latency/margin unverified",
            "Normal fees often produce negative net returns; historical backtest is not forward validated"
        ])
    (OUT/"summary.json").write_text(json.dumps(
        report,indent=2,default=lambda v:v.item() if isinstance(v,np.generic) else str(v))+"\n")
    md=[
        "# BTC Step27 — previous monthly high-water guard + early exit optimization",
        "",
        "All 324 policies have one full-size BTCUSD 1x-notional trade on each of 477 IST weekdays. Never use today's trade outcome before setting today's stop or exit. January2026 and the entire history have been seen repeatedly, so this cannot validate forward profitability.",
        "",
        "## Step26 exact baseline parity",json.dumps({
            "offer":base_offer,"normal":base_std,
            "January_2026_net":float(base_mo[12])},indent=2),
        "",
        "## 2025-only selection",json.dumps(selected,indent=2),
        "",
        "## 2025-selected 2026 research-exposed test",
        json.dumps(audited["selected_2025_only"],indent=2),
        "",
        "## January 2026 hindsight only, full profit-month-DD constraints",
        json.dumps(audited["highest_January2026_hindsight_NOT_SELECTED"],indent=2),
        "",
        "## 2025-selected monthly ledger",
        pd.read_csv(OUT/"selected_2025_only_scalper_offer_22_months.csv").to_markdown(index=False),
        "",
        "## Disclosures",
        "Historical fee waiver entitlement and actual execution quality cannot be established. Normal taker fees lose money in many variants. No main-branch merge or live deployment."
    ]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(md)+"\n")
    print("STEP27_COMPLETE "+json.dumps(dict(
        models=324,qualified_on_2025=int(len(admissible)),
        retrospective_all22=int(len(candidates22)),
        January_2026_old=float(base_mo[12]),
        January_2026_selected=float(jan),
        net_old=base_offer["net_total_pct"],
        net_selected=chosen["net_total_pct"],
        DD_selected=chosen["max_closed_dd_pct"],
        months_selected=chosen["win_months_all"],
        meets_full_conditions=bool(admitted_forward_like),
        hindsight_best_January2026=float(audited["highest_January2026_hindsight_NOT_SELECTED"]["scalper_offer"]["January_2026"])
    ),sort_keys=True),flush=True)

if __name__=="__main__":
    main()
