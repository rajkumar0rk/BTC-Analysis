#!/usr/bin/env python3
"""Step26: after-prior-month-equity giveback risk protection on Step25 BTC.

Exactly 108 predeclared causal monthly high-water SL caps plus original.
477 full IST weekday positions at 1x account notional, unchanged Ridge
entry and earlier-day conditional exits. Month state uses prior completed
trade returns ONLY. 2025-only selection; Jan2026 analysis hindsight.
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
import research_btc_net_return_factorial_step25 as step25

OUT=Path("analysis/btc_monthly_profit_peak_guard_step26")
N=len(base.DAYS)
TRAIN=base.NTRAIN
MONTHS=np.asarray(base.MONTH_LABELS)
PEAKS=(.5,1.,1.5)       # percentage points from starting equity 1x
GIVEBACKS=(.25,.5,.75)   # percentage points below earlier peak equity
SCOPES=("event_only","fallback_only","both")
CAPS=(.15,.20,.25,.30)  # pct-of-mid initial SL: can only narrow
assert N==477 and TRAIN==260
assert len(PEAKS)*len(GIVEBACKS)*len(SCOPES)*len(CAPS)==108

def replay_price(m,idx,sides,cfg,policies):
    return early.replay_with_nextbar_exits(
        m.open.to_numpy(float),m.high.to_numpy(float),
        m.low.to_numpy(float),m.close.to_numpy(float),
        idx,sides,cfg,policies,base.COST,base.SLIP)

def path_with_flags(unchanged,capped,policies,active,cost_index):
    d=np.arange(N)
    return tuple(
      np.where(active,
         capped[k][d,policies,cost_index] if k<2 else capped[k][d,policies],
         unchanged[k][d,policies,cost_index] if k<2 else unchanged[k][d,policies])
      for k in range(5)
    )

def causal_month_guard(unchanged,capped,isfallback,ids,peak_min,gb_min,scope):
    """Decisions use previous FINISHED trades' net under fee waiver only."""
    dpol=np.zeros(N,dtype=np.int16)
    guard=np.zeros(N,dtype=bool)
    prior_net=np.zeros(N)
    prior_giveback=np.zeros(N)
    prior_peak=np.zeros(N)
    month=None;equity=1.;peak=1.
    for d in range(N):
        if MONTHS[d]!=month:
            month=MONTHS[d];equity=1.;peak=1.
        net=equity-1.
        gb=peak-equity
        prior_net[d]=net
        prior_giveback[d]=gb
        prior_peak[d]=peak-1.
        eligible=(scope=="both" or
                  (scope=="event_only" and not isfallback[d]) or
                  (scope=="fallback_only" and isfallback[d]))
        should_cap=eligible and peak>=1.+peak_min/100. and gb>=gb_min/100.
        guard[d]=should_cap
        if isfallback[d]:
            # Frozen Step25: 20-minute profit close for MTD <= +0.25%,
            # otherwise no additional close (including >+1% MTD).
            exit_id=(ids["profit_close_at_0.1pct_after_20m"]
                     if net<=.0025 else 0)
        else:
            exit_id=(ids["adverse_cut_0.08pct_after_10m"]
                     if net<=0 else 0)
        dpol[d]=exit_id
        # Only the CURRENT day's result determines TOMORROW's state.
        today=float((capped if should_cap else unchanged)[0][d,exit_id,1])
        if not np.isfinite(today):
            raise AssertionError("Invalid trade PnL")
        equity*=1.+today
        peak=max(peak,equity)
    return dpol,guard,prior_net,prior_giveback,prior_peak

def month_numbers(p):
    return np.asarray([
       100.*(np.prod(1.+p[MONTHS==month])-1.)
       for month in list(dict.fromkeys(MONTHS.tolist()))
    ],dtype=float)

def report_months(path,model,fee):
    p,fees,gross,why,elapsed=path
    months=list(dict.fromkeys(MONTHS.tolist()))
    result=pd.DataFrame(dict(
       month_ist=months,
       trade_days=[int(np.sum(MONTHS==month)) for month in months],
       profitable_days=[int(np.sum(p[MONTHS==month]>0)) for month in months],
       losing_days=[int(np.sum(p[MONTHS==month]<0)) for month in months],
       account_net_compounded_pct=month_numbers(p),
       modeled_fee_gst_btc_quote_points=[
         float(np.sum(fees[MONTHS==month])) for month in months],
       model=model,cost_model=fee
    ))
    assert len(result)==22 and result.trade_days.sum()==477
    return result

def saved_model(model_name,variant,baseline_raw,alt_cached,ids,mask,idx,side,hours,cfg):
    peak_min,giveback_min,scope,cap=variant
    altered=baseline_raw if cap is None else alt_cached[cap]
    pol,active,prev_mtd,prev_gb,prev_peak=causal_month_guard(
       baseline_raw,altered,mask,ids,peak_min,giveback_min,scope
    )
    result={}
    for fee_index,fee in enumerate(base.MODES):
        path=path_with_flags(baseline_raw,altered,pol,active,fee_index)
        p,fees,gross,why,elapsed=path
        stop=min(0.0,0.0) # placeholder value not used
        day=pd.DataFrame(dict(
          day_ist=base.IST_DAYS,
          month_ist=MONTHS,
          year=np.asarray(base.DAYS.year),
          entry_hour_ist=hours,
          entry_side=np.where(side==1,"LONG","SHORT"),
          entry_category=np.where(mask,"FALLBACK","EVENT"),
          prior_compounded_month_net_pct=prev_mtd*100.,
          prior_completed_peak_month_net_pct=prev_peak*100.,
          previous_peak_to_equity_giveback_pct=prev_gb*100.,
          additional_risk_guard_active=active,
          previous_bar_exit_policy_index=pol,
          daily_account_net_pct=p*100.,
          gross_btc_quote_price_points=gross,
          modeled_fee_gst_quote_points=fees,
          adverse_slip_quote_points=2.*base.SLIP,
          exit_reason_code=why,
          hold_minutes=elapsed,
          model=model_name,
          cost_model=fee
        ))
        if len(day)!=477 or day.day_ist.nunique()!=477 or (
            pd.to_datetime(day.day_ist).dt.dayofweek>=5).any():
            raise AssertionError("Daily entries missing / weekend")
        month=report_months(path,model_name,fee)
        day.to_csv(OUT/(model_name+"_"+fee+"_477_daily.csv"),index=False)
        month.to_csv(OUT/(model_name+"_"+fee+"_22_months.csv"),index=False)
        score=step15.score(path)
        assert int((month.account_net_compounded_pct>0).sum())==score["win_months_all"]
        result[fee]=dict(
            metrics=score,
            January_2026_net_pct=float(month.loc[
                month.month_ist=="2026-01","account_net_compounded_pct"].iloc[0]),
            risk_guard_trades=int(np.sum(active)),
            losing_months=month.loc[
                month.account_net_compounded_pct<=0,
                ["month_ist","account_net_compounded_pct"]].to_dict("records"))
    return result

def run():
    OUT.mkdir(parents=True,exist_ok=True)
    m,ctx,mask,fb,original_side,hours,idx,starting_cfg=step13.create_path()
    policies,labels=early.build_exit_policies()
    ids={name:i for i,name in enumerate(labels)}
    feat=step25.risk.preentry_features(m,idx,original_side)
    # Ridge frozen Step22 original 120 fallback observation supervised side.
    normal={}
    for sign in (-1,1):
        side=np.full(N,sign,dtype=np.int8)
        cfg,_=step25.preentry_stop(starting_cfg,feat,mask,side,"baseline")
        normal[sign]=replay_price(m,idx,side,cfg,policies)
    X=step25.ridge.features_at_entry(m,idx)
    predictions,ncases=step25.ridge.shadow_predictions(
        X,normal[1][0][:,0,1],normal[-1][0][:,0,1],
        mask,"ridge",120,"basic")
    sides,different=step25.ridge.choose_sides(
        original_side,predictions,ncases,mask,.30,"fallback")
    if int(different.sum())!=4:
        raise AssertionError("Ridge baseline direction drift")
    cfg,_=step25.preentry_stop(
        starting_cfg,feat,mask,sides,"tight60_050_both_cap040")
    raw_orig=replay_price(m,idx,sides,cfg,policies)

    # Cold original stop cap replay for every trade before month is known.
    capped={}
    for cap in CAPS:
        cap_cfg=cfg.copy()
        cap_cfg[:,1]=np.minimum(cap_cfg[:,1],cap)
        assert np.all(cap_cfg[:,1]<=cfg[:,1]+1.e-12)
        capped[cap]=replay_price(m,idx,sides,cap_cfg,policies)

    default_variant=(0.,0.,"both",None)
    basic=causal_month_guard(raw_orig,raw_orig,mask,ids,*default_variant[:3])
    original_offer=step15.score(path_with_flags(raw_orig,raw_orig,basic[0],basic[1],1))
    original_standard=step15.score(path_with_flags(raw_orig,raw_orig,basic[0],basic[1],0))
    original_january=float(month_numbers(
        path_with_flags(raw_orig,raw_orig,basic[0],basic[1],1)[0])[12])
    if (original_offer["trades"]!=477 or
        abs(original_offer["net_total_pct"]-28.134367)>.00011 or
        original_offer["win_months_all"]!=21 or
        abs(original_offer["max_closed_dd_pct"]-2.617670)>.00011 or
        abs(original_january-.0874647363)>.00011 or
        abs(original_standard["net_total_pct"]+3.285672)>.00011):
        raise AssertionError("Step25 B/Ridge model exact baseline parity failed: "+str(original_offer)+" Jan:"+str(original_january))
    print("STEP26_PARITY "+json.dumps(dict(
        net_offer=original_offer["net_total_pct"],
        months=original_offer["win_months_all"],
        dd=original_offer["max_closed_dd_pct"],
        January_2026_net=original_january,
        standard_net=original_standard["net_total_pct"],
        exact_trades=477),sort_keys=True),flush=True)

    every_row=[]
    every_month=[]
    grid=[("baseline",default_variant,raw_orig,raw_orig)]
    for peak_min,gb_min,scope,cap in product(PEAKS,GIVEBACKS,SCOPES,CAPS):
        name=f"peak_{peak_min:g}_giveback_{gb_min:g}_{scope}_cap_{cap:g}"
        grid.append((name,(peak_min,gb_min,scope,cap),raw_orig,capped[cap]))
    assert len(grid)==109
    for i,(name,params,unchanged,altered) in enumerate(grid):
        trigger=causal_month_guard(
            unchanged,altered,mask,ids,params[0],params[1],params[2])
        policy,active,prior_mtd,prior_giveback,prior_peak=trigger
        for mi,fee in enumerate(base.MODES):
            path=path_with_flags(unchanged,altered,policy,active,mi)
            s=step15.score(path)
            monthly=report_months(path,name,fee)
            jan=float(monthly.loc[
                monthly.month_ist=="2026-01","account_net_compounded_pct"].iloc[0])
            record=dict(
               name=name,peak_min_month_pct=params[0],
               giveback_trigger_pct_points=params[1],scope=params[2],
               initial_stop_cap_pct=params[3],
               condition_days=int(np.sum(active)),
               condition_days_in_Jan2026=int(np.sum(active&(MONTHS=="2026-01"))),
               January_2026_account_net_pct=jan,
               January_2026_change_vs_baseline_pct_points=jan-original_january,
               cost_model=fee,**s)
            every_row.append(record)
            every_month.append(monthly)
        if i%18==0 or i==108:
            print("STEP26_PROGRESS "+json.dumps(dict(
                completed_models=i+1,full_models=109,
                last_checked=name)),flush=True)
    grid_result=pd.DataFrame(every_row)
    assert len(grid_result)==218 and grid_result.trades.eq(477).all()
    grid_result.to_csv(OUT/"all_108_month_peak_guards_2_fee_models.csv",index=False)
    pd.concat(every_month,ignore_index=True).to_csv(
        OUT/"all_109_models_22_months_each_2_fees.csv",index=False)

    offer=grid_result[grid_result.cost_model=="scalper_offer"]
    qualified=offer[(offer.name!="baseline")&
       (offer.win_months_2025>=11)&
       (offer.return_2025_pct>=original_offer["return_2025_pct"]-1.e-6)&
       (offer.profitable_days_2025>=original_offer["profitable_days_2025"])&
       (offer.max_dd_2025<=original_offer["max_dd_2025"]+1.e-4)]
    if len(qualified):
        winner=qualified.sort_values(
           ["return_2025_pct","win_months_2025",
            "profitable_days_2025","max_dd_2025"],
           ascending=[False,False,False,True]).iloc[0].to_dict()
    else:
        winner=offer[offer.name=="baseline"].iloc[0].to_dict()
    hindsight=offer[
        (offer.win_months_all>=21)&
        (offer.win_months_2026>=10)&
        (offer.max_closed_dd_pct<=original_offer["max_closed_dd_pct"]+1e-4)
    ].sort_values(["January_2026_account_net_pct","net_total_pct"],
                  ascending=[False,False])
    retrospect=(hindsight.iloc[0].to_dict() if len(hindsight) else winner)

    def parse_variant(row):
        if row["name"]=="baseline":
            return default_variant
        return (float(row["peak_min_month_pct"]),
                float(row["giveback_trigger_pct_points"]),
                row["scope"],float(row["initial_stop_cap_pct"]))

    selected_result={}
    for tag,row in (("selected_by_2025_only",winner),
                    ("January2026_best_hindsight_NOT_SELECTED",retrospect)):
        var=parse_variant(row)
        results=saved_model(
           tag,var,raw_orig,capped,ids,mask,idx,sides,hours,cfg)
        selected_result[tag]=dict(model=row["name"],both_fees=results)
        print("STEP26_REPORT_"+tag.upper()+" "+json.dumps(
           selected_result[tag],sort_keys=True),flush=True)

    report=dict(
        study="Causal prior-month-peak and peak-equity-giveback-conditioned protective initial SL",
        original_BTCUSD_Step25_ridge=dict(
            hypothetical_scalper_offer=original_offer,
            normal_taker=original_standard,
            January_2026_net_pct=original_january),
        exactly_one_full_1x_notional_trade_every_477_ist_weekday=True,
        grid_models=109,fee_mode_results=218,
        2025_only_qualified_count=int(len(qualified)),
        selected_2025_only=winner,
        selected_report=selected_result["selected_by_2025_only"],
        hindsight_best_January2026_NOT_SELECTED=retrospect,
        hindsight_full_report=selected_result["January2026_best_hindsight_NOT_SELECTED"],
        hindsight_best_Jan_historical_models_tested=int(len(hindsight)),
        limitations=[
            "January2026 already inspected; any higher Jan2026 outcome chosen on that month is retrospective and cannot be trusted forward",
            "2025 and 2026 also repeatedly researched in earlier strategies; Step25 family itself historically selected",
            "Historical Scalper closing fee waiver was only assumed, real opt-in unverified",
            "Orderbook spreads, real fills/latency, funding, margin, liquidation and intrabar ticks not modeled",
            "Fixed one-trade-per-weekday exposure can still produce losing months"]
    )
    (OUT/"summary.json").write_text(json.dumps(
        report,indent=2,default=lambda x:x.item() if isinstance(x,np.generic) else str(x))+"\n")
    md=[
        "# BTC Step26 — monthly high-water risk protection; full-size daily positions",
        "",
        "The 109 models each retain exactly one full 1x BTCUSD position every 477 IST Monday-Friday dates. The stop guard uses ONLY previously completed trade returns in the current IST month; no day-specific hindsight entry or trade skipped.",
        "",
        "## Exact baseline reproduction",json.dumps(report["original_BTCUSD_Step25_ridge"],indent=2),
        "",
        "## Policy selected using 2025 only",json.dumps(report["selected_report"],indent=2),
        "",
        "## January 2026 top retrospective — unselected hindsight",json.dumps(report["hindsight_full_report"],indent=2),
        "",
        "## Jan2026 month return across historical model grid",
        offer.sort_values("January_2026_account_net_pct",ascending=False).head(18)[[
          "name","January_2026_account_net_pct","net_total_pct","win_months_all",
          "max_closed_dd_pct","profitable_days"
        ]].to_markdown(index=False),
        "",
        "## Fee and model warnings",
        "All 2025–October2026 data are research-exposed and Step25 previously selected in hindsight. An improved January2026 cannot guarantee future January results. Hypothetical eligible fee waiver never independently verified."
    ]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(md)+"\n")
    print("STEP26_COMPLETE "+json.dumps(dict(
        models=109,qualified_2025=len(qualified),
        selected_2025=winner["name"],
        January_selected=selected_result["selected_by_2025_only"]["both_fees"]["scalper_offer"]["January_2026_net_pct"],
        January_hindsight=selected_result["January2026_best_hindsight_NOT_SELECTED"]["both_fees"]["scalper_offer"]["January_2026_net_pct"],
        winner_offer_net=selected_result["selected_by_2025_only"]["both_fees"]["scalper_offer"]["metrics"]["net_total_pct"],
        winner_months=selected_result["selected_by_2025_only"]["both_fees"]["scalper_offer"]["metrics"]["win_months_all"]
    ),sort_keys=True),flush=True)

if __name__=="__main__":
    run()
