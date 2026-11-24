#!/usr/bin/env python3
"""Step29: 1200 causal losing-month rescue combinations for BTC Jan 2025.

Full 1x account-notional BTC trade on each of 477 IST Mon-Fri days.
Keep frozen Step28 Ridge+month-peak guarded trailing. If PRIOR finished
monthly trades show losses, precommit side (fallback), tighter initial SL,
and previously closed-bar early fallback exit; no current/future labels.
Historical 2025/2026 have been mined: 12/12/22/22 is NOT live validation.
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
import research_btc_month_guard_trailing_step28 as step28

OUT=Path("analysis/btc_january2025_loss_recovery_step29")
N=len(base.DAYS)
TRAIN=base.NTRAIN
MONTHS=np.asarray(base.MONTH_LABELS)
STATES=("mtd_nonpositive","mtd_below_minus025","mtd_below_minus050","loss_streak2")
DIRECTIONS=("keep_ridge","fade_last5m","follow_last60m","fade_last60m","invert_high_rvol")
CAPS=(.15,.20,.25,.30,.35)
SCOPES=("fallback_only","both")
EXITS=("base","profit010_after5","profit010_after10","adverse008_after5","adverse008_after10","timeout20")
assert len(STATES)*len(DIRECTIONS)*len(CAPS)*len(SCOPES)*len(EXITS)==1200
assert N==477 and TRAIN==260

def all_features_and_sides(m,mask,idx,orig_side,base_cfg,policies):
    features=step25.risk.preentry_features(m,idx,orig_side)
    # Exact frozen ridge direction model based on only previously completed
    # same-type fallback shadow returns; preserve Step28 training samples.
    shadows={}
    for sign in (-1,1):
        side=np.full(N,sign,dtype=np.int8)
        cfg,_=step25.preentry_stop(base_cfg,features,mask,side,"baseline")
        shadows[sign]=step28.step26.replay_price(m,idx,side,cfg,policies)
    X=step25.ridge.features_at_entry(m,idx)
    prediction,training=step25.ridge.shadow_predictions(
        X,shadows[1][0][:,0,1],shadows[-1][0][:,0,1],
        mask,"ridge",120,"basic")
    ridge_side,changed=step25.ridge.choose_sides(
        orig_side,prediction,training,mask,.30,"fallback")
    if int(changed.sum())!=4:
        raise AssertionError("Frozen Ridge direction parity drift")
    return features,ridge_side

def raw_cache(m,mask,idx,base_cfg,features,policies):
    """Only 24 fixed full 1m replays: sign×guard×{original,5 caps}.

    Peak guard reuses exact Step28 E3 / F3 +0.18% loss cap; extra
    month-loss caps are composed with min and never widen.
    """
    cache={}
    original_stops={}
    for side_sign in (-1,1):
        side=np.full(N,side_sign,dtype=np.int8)
        cfg,_=step25.preentry_stop(
            base_cfg,features,mask,side,"tight60_050_both_cap040")
        original_stops[side_sign]=cfg[:,1].copy()
        for peak_guard in (False,True):
            frozen=cfg.copy()
            if peak_guard:
                frozen=step28.change_trailing(
                    cfg,mask,.18,"E3_later_larger_lock","F3_normal_tight")
            for cap in (None,*CAPS):
                actual=frozen.copy()
                if cap is not None:
                    actual[:,1]=np.minimum(actual[:,1],cap)
                if not np.all(actual[:,1]<=cfg[:,1]+1e-12):
                    raise AssertionError("Initial stop width increased")
                cache[(side_sign,peak_guard,cap)]=step28.step26.replay_price(
                    m,idx,side,actual,policies)
        print("STEP29_PRICE_CACHE "+json.dumps({
            "side":side_sign,"num_arrays_so_far":len(cache)}),flush=True)
    assert len(cache)==24
    return cache,original_stops

def negative_month_state(kind,equity,streak):
    net=equity-1.
    if kind=="off":return False
    if kind=="mtd_nonpositive":return net<=0.
    if kind=="mtd_below_minus025":return net<=-.0025
    if kind=="mtd_below_minus050":return net<=-.005
    if kind=="loss_streak2":return streak>=2
    raise KeyError(kind)

def recovery_direction(kind,current,d,features):
    if kind=="keep_ridge":return int(current)
    r5=float(features["r5"][d])
    r60=float(features["r60"][d])
    rv=float(features["rvol5"][d])
    if kind=="fade_last5m":
        if abs(r5)>=.0005:return -1 if r5>0 else 1
    elif kind=="follow_last60m":
        if abs(r60)>=.0015:return 1 if r60>0 else -1
    elif kind=="fade_last60m":
        if abs(r60)>=.0015:return -1 if r60>0 else 1
    elif kind=="invert_high_rvol":
        if rv>=1.25:return -int(current)
    else:
        raise KeyError(kind)
    return int(current)

def entry_exit_id(mask_is_fallback,prior_mtd,loss_trigger,exit_name,ids):
    if mask_is_fallback:
        original=(ids["profit_close_at_0.1pct_after_20m"]
                  if prior_mtd<=.0025 else 0)
        if loss_trigger and exit_name!="base":
            names={
                "profit010_after5":"profit_close_at_0.1pct_after_5m",
                "profit010_after10":"profit_close_at_0.1pct_after_10m",
                "adverse008_after5":"adverse_cut_0.08pct_after_5m",
                "adverse008_after10":"adverse_cut_0.08pct_after_10m",
                "timeout20":"hard_timeout_20m"
            }
            return ids[names[exit_name]]
        return original
    return ids["adverse_cut_0.08pct_after_10m"] if prior_mtd<=0. else 0

def run_model(setting,cache,mask,ridge_sides,features,ids,baseline_mode=False):
    state_rule,dir_rule,cap,scope,exit_rule=setting
    pnl=np.empty((len(base.MODES),N),dtype=float)
    fee=np.empty((len(base.MODES),N),dtype=float)
    gross=np.empty(N,dtype=float)
    reason=np.empty(N,dtype=np.int8)
    hold=np.empty(N,dtype=np.int16)
    actual_side=np.empty(N,dtype=np.int8)
    chosen_policy=np.empty(N,dtype=np.int16)
    peak_triggered=np.zeros(N,dtype=bool)
    negative_triggered=np.zeros(N,dtype=bool)
    cap_triggered=np.zeros(N,dtype=bool)
    prior_account_mtd=np.zeros(N)
    prior_account_peak=np.zeros(N)
    prior_month_giveback=np.zeros(N)
    previous_losses=np.zeros(N,dtype=np.int8)
    month=None; equity=1.;peak=1.;loss_run=0
    for d in range(N):
        if MONTHS[d]!=month:
            month=MONTHS[d];equity=1.;peak=1.;loss_run=0
        prior_account_mtd[d]=equity-1.
        prior_account_peak[d]=peak-1.
        prior_month_giveback[d]=peak-equity
        previous_losses[d]=loss_run
        # Exact independently frozen Step28 high-water guard.
        highwater=(peak>=1.01 and peak-equity>=.0075)
        peak_triggered[d]=highwater
        bad_month=False if baseline_mode else negative_month_state(
            state_rule,equity,loss_run)
        negative_triggered[d]=bad_month
        current=int(ridge_sides[d])
        if bad_month and mask[d]:
            current=recovery_direction(dir_rule,current,d,features)
        actual_side[d]=current
        if abs(current)!=1:raise AssertionError("Mandatory BTC weekday side missing")
        needs_cap=(bad_month and (scope=="both" or
                        (scope=="fallback_only" and mask[d])))
        cap_triggered[d]=needs_cap
        current_cap=(cap if needs_cap else None)
        # Extra month-loss regime always acts on fallback extra exit only.
        policy=entry_exit_id(bool(mask[d]),equity-1.,
                             bad_month,exit_rule,ids)
        chosen_policy[d]=policy
        raw=cache[(current,highwater,current_cap)]
        # Repricing standard fees is across EXACT same chosen fills/exits:
        # no model setting or monthly-state decision based on normal-fee PnL.
        pnl[:,d]=raw[0][d,policy,:]
        fee[:,d]=raw[1][d,policy,:]
        gross[d]=raw[2][d,policy]
        reason[d]=raw[3][d,policy]
        hold[d]=raw[4][d,policy]
        today=float(pnl[base.MODES.index("scalper_offer"),d])
        if not np.isfinite(today) or today<=-1:
            raise AssertionError("Bad account return from 1m replay")
        equity*=1.+today
        peak=max(peak,equity)
        loss_run=loss_run+1 if today<0 else 0
    outputs={}
    for mode_index,fee_name in enumerate(base.MODES):
        path=(pnl[mode_index],fee[mode_index],gross,reason,hold)
        perf=step15.score(path)
        if perf["trades"]!=477:raise AssertionError("Missing 1× mandatory trading day")
        month_returns=step28.step26.month_numbers(path[0])
        if len(month_returns)!=22 or int((month_returns>0).sum())!=perf["win_months_all"]:
            raise AssertionError("Monthly return parity failed")
        outputs[fee_name]=dict(
            performance=perf,
            month_returns=month_returns,
            January_2025=float(month_returns[0]),
            January_2026=float(month_returns[12]))
    return dict(
        outcomes=outputs,pnl=pnl,fee=fee,gross=gross,reason=reason,hold=hold,
        sides=actual_side,policies=chosen_policy,
        monthly_mtd=prior_account_mtd,monthly_peak=prior_account_peak,
        month_giveback=prior_month_giveback,loss_streak=previous_losses,
        peak_guard=peak_triggered,negative_state=negative_triggered,
        loss_stop_cap=cap_triggered,
        changed_fallback_directions=int(np.sum((actual_side!=ridge_sides)&mask)))

def save_audit(tag,name,setting,result,ridge_sides,hours,mask):
    notes={}
    for i,fee_mode in enumerate(base.MODES):
        data=pd.DataFrame(dict(
            day_ist=base.IST_DAYS,
            year=np.asarray(base.DAYS.year),
            month_ist=MONTHS,
            entry_hour_ist=hours,
            trade_type=np.where(mask,"FALLBACK_21H","VOLUME_EVENT"),
            direction=np.where(result["sides"]>0,"LONG","SHORT"),
            Ridge_direction=np.where(ridge_sides>0,"LONG","SHORT"),
            prior_month_compounded_net_pct=result["monthly_mtd"]*100,
            prior_month_earlier_peak_pct=result["monthly_peak"]*100,
            prior_month_peak_giveback_pp=result["month_giveback"]*100,
            previous_month_loss_streak=result["loss_streak"],
            high_water_trailing_guard=result["peak_guard"],
            recovery_loss_condition=result["negative_state"],
            recovery_stop_cap=result["loss_stop_cap"],
            loss_recovery_side_rule=setting[1],
            loss_recovery_stop_cap_pct=setting[2],
            loss_recovery_exit_rule=setting[4],
            chosen_closed_bar_exit_policy=result["policies"],
            account_daily_net_pct=result["pnl"][i]*100.,
            gross_btc_quote_points=result["gross"],
            fee_gst_quote_points=result["fee"][i],
            modeled_adverse_slippage_quote_points=base.SLIP*2,
            exit_reason=result["reason"],
            minutes_in_trade=result["hold"],
            fee_model=fee_mode,
            model=name
        ))
        if (len(data)!=477 or data.day_ist.nunique()!=477 or
            (pd.to_datetime(data.day_ist).dt.dayofweek>=5).any()):
            raise AssertionError("No skipped or weekend positions allowed")
        monthly=pd.DataFrame(dict(
            month_ist=list(dict.fromkeys(MONTHS.tolist())),
            account_net_compounded_pct=result["outcomes"][fee_mode]["month_returns"],
            trading_days=[int(np.sum(MONTHS==m))
                          for m in list(dict.fromkeys(MONTHS.tolist()))],
            model=name,cost_model=fee_mode
        ))
        assert len(monthly)==22 and monthly.trading_days.sum()==477
        data.to_csv(OUT/(tag+"_"+fee_mode+"_477_daily.csv"),index=False)
        monthly.to_csv(OUT/(tag+"_"+fee_mode+"_22_months.csv"),index=False)
        notes[fee_mode]=dict(
            performance=result["outcomes"][fee_mode]["performance"],
            January_2025_net_pct=result["outcomes"][fee_mode]["January_2025"],
            January_2026_net_pct=result["outcomes"][fee_mode]["January_2026"],
            losing_months=monthly.loc[
                monthly.account_net_compounded_pct<=0,
                ["month_ist","account_net_compounded_pct"]].to_dict("records"),
            changes_to_fallback_side=result["changed_fallback_directions"],
            high_water_guard_days=int(result["peak_guard"].sum()),
            month_loss_condition_days=int(result["negative_state"].sum()),
            stop_recovery_days=int(result["loss_stop_cap"].sum()))
    return notes

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    m,ctx,mask,fb,orig_side,hours,idx,config=step13.create_path()
    policies,labels=early.build_exit_policies()
    ids={name:i for i,name in enumerate(labels)}
    features,ridge_sides=all_features_and_sides(
        m,mask,idx,orig_side,config,policies)
    cache,initial_stops=raw_cache(m,mask,idx,config,features,policies)
    baseline_setting=("off","keep_ridge",None,"both","base")
    baseline=run_model(
        baseline_setting,cache,mask,ridge_sides,features,ids,
        baseline_mode=True)
    old=baseline["outcomes"]["scalper_offer"]["performance"]
    normal=baseline["outcomes"]["standard"]["performance"]
    jan2025=baseline["outcomes"]["scalper_offer"]["January_2025"]
    jan2026=baseline["outcomes"]["scalper_offer"]["January_2026"]
    if (old["trades"]!=477 or old["win_months_all"]!=21 or
        old["profitable_days"]!=281 or
        abs(old["net_total_pct"]-28.574051)>.00011 or
        abs(old["max_closed_dd_pct"]-2.617670)>.00011 or
        abs(jan2025+1.04710143575)>.00011 or
        abs(jan2026-.91087191822)>.00011 or
        abs(normal["net_total_pct"]+2.954186)>.00011):
        raise AssertionError("FAIL: Step28 original per-candle parity / January target drift: "+
                             str(old)+", 2025 Jan:"+str(jan2025)+", 2026 Jan:"+str(jan2026))
    print("STEP29_BASELINE_VERIFIED "+json.dumps(dict(
        offer=old,normal=normal,
        january_2025_sole_loss_pct=jan2025,
        january_2026_already_profitable_pct=jan2026,
        all_477_ist_weekdays=True),sort_keys=True),flush=True)

    rows=[];variant_config={}
    all_months=list(dict.fromkeys(MONTHS.tolist()))
    for idxv,(state,direction,cap,scope,extra) in enumerate(product(
        STATES,DIRECTIONS,CAPS,SCOPES,EXITS),start=1):
        setting=(state,direction,cap,scope,extra)
        name="__".join([state,direction,("%.2f"%cap),scope,extra])
        variant_config[name]=setting
        results=run_model(setting,cache,mask,ridge_sides,features,ids)
        for fee_mode in base.MODES:
            z=results["outcomes"][fee_mode]
            rows.append(dict(
                name=name,month_loss_state=state,
                recovery_side=direction,cap_pct=cap,cap_scope=scope,
                fallback_early_close=extra,
                changed_fallback_directions=results["changed_fallback_directions"],
                loss_condition_trade_days=int(results["negative_state"].sum()),
                extra_cap_eligible_days=int(results["loss_stop_cap"].sum()),
                prior_highwater_protection_days=int(results["peak_guard"].sum()),
                January_2025_net_pct=z["January_2025"],
                January_2026_net_pct=z["January_2026"],
                fee_model=fee_mode,**z["performance"]))
        if idxv%200==0 or idxv==1200:
            print("STEP29_GRID_PROGRESS "+json.dumps(dict(
                configurations_done=idxv,
                expected=1200,example_last=name)),flush=True)
    grid=pd.DataFrame(rows)
    if len(grid)!=2400 or not grid.trades.eq(477).all():
        raise AssertionError("Missing models/trades")
    # Baseline is explicitly included in total 2402 comparison rows.
    for fee_mode in base.MODES:
        grid=pd.concat([grid,pd.DataFrame([dict(
            name="frozen_Step28",month_loss_state="off",
            recovery_side="keep_ridge",cap_pct=None,
            cap_scope="both",fallback_early_close="base",
            changed_fallback_directions=0,
            loss_condition_trade_days=0,extra_cap_eligible_days=0,
            prior_highwater_protection_days=int(baseline["peak_guard"].sum()),
            January_2025_net_pct=baseline["outcomes"][fee_mode]["January_2025"],
            January_2026_net_pct=baseline["outcomes"][fee_mode]["January_2026"],
            fee_model=fee_mode,**baseline["outcomes"][fee_mode]["performance"])])],
            ignore_index=True)
    assert len(grid)==2402
    grid.to_csv(OUT/"all_1200_January2025_loss_regime_combinations_both_fees.csv",index=False)
    offer=grid[grid.fee_model=="scalper_offer"]
    all_january_positive=offer[(offer.name!="frozen_Step28")&
                               (offer.January_2025_net_pct>0)]
    train12=offer[(offer.name!="frozen_Step28")&
                  (offer.win_months_2025==12)]
    strict=train12[
        (train12.return_2025_pct>=old["return_2025_pct"]-1e-6)&
        (train12.profitable_days_2025>=old["profitable_days_2025"])&
        (train12.max_dd_2025<=old["max_dd_2025"]+1e-4)]
    if len(strict):
        qualified=strict.sort_values(
            ["return_2025_pct","win_months_2025",
             "profitable_days_2025","max_dd_2025"],
            ascending=[False,False,False,True])
        selected=qualified.iloc[0].to_dict()
    else:
        selected=offer[offer.name=="frozen_Step28"].iloc[0].to_dict()
    retrospect22=offer[offer.win_months_all==22].sort_values(
        ["net_total_pct","max_closed_dd_pct"],
        ascending=[False,True])
    retrospect22.to_csv(
        OUT/"HINDSIGHT_ONLY_all_22_profitable_months.csv",index=False)
    retrospect_january=offer[offer.name!="frozen_Step28"].sort_values(
        ["January_2025_net_pct","win_months_all","net_total_pct"],
        ascending=[False,False,False])
    retrospect_january.head(30).to_csv(
        OUT/"HINDSIGHT_ONLY_highest_Jan2025_return_not_selected.csv",index=False)
    monthly_guard=offer[
        (offer.win_months_all>=21)&
        (offer.win_months_2026==10)&
        (offer.max_closed_dd_pct<=old["max_closed_dd_pct"]+1e-4)&
        (offer.net_total_pct>=old["net_total_pct"])
    ].sort_values(["January_2025_net_pct","net_total_pct"],ascending=[False,False])
    monthly_guard.head(30).to_csv(
        OUT/"HINDSIGHT_only_21plus_month_net_DD_guards.csv",index=False)
    retrospect_best=(
        retrospect22.iloc[0].to_dict() if len(retrospect22)
        else (monthly_guard.iloc[0].to_dict() if len(monthly_guard)
              else retrospect_january.iloc[0].to_dict()))
    sample_name=retrospect_january.iloc[0].to_dict()
    audits={}
    for tag,chosen in [
        ("frozen_Step28_baseline",dict(name="frozen_Step28")),
        ("selected_2025_only",selected),
        ("hindsight_best_January2025_NOT_SELECTED",sample_name),
        ("hindsight_best_overall_NOT_SELECTED",retrospect_best)
    ]:
        rule=(baseline_setting if chosen["name"]=="frozen_Step28"
              else variant_config[chosen["name"]])
        res=(baseline if chosen["name"]=="frozen_Step28"
             else run_model(rule,cache,mask,ridge_sides,features,ids))
        outcomes=save_audit(
            tag,chosen["name"],rule,res,ridge_sides,hours,mask)
        audits[tag]=dict(setting=rule,model=chosen["name"],costs=outcomes)
        print("STEP29_AUDIT_"+tag.upper()+" "+
              json.dumps(audits[tag],sort_keys=True),flush=True)
    chosen=audits["selected_2025_only"]["costs"]["scalper_offer"]["performance"]
    chosen_jan=audits["selected_2025_only"]["costs"]["scalper_offer"]["January_2025_net_pct"]
    goal=(chosen_jan>0 and chosen["win_months_all"]==22 and
          chosen["win_months_2026"]==10 and
          chosen["net_total_pct"]>=old["net_total_pct"] and
          chosen["max_closed_dd_pct"]<=old["max_closed_dd_pct"]+1e-4)
    info=dict(
       experiment="BTC Jan2025 losing-month recovery factorial (general previous-month-equity state, not January-specific rules)",
       baseline_step28=audits["frozen_Step28_baseline"],
       all_477_weekday_full_1x_notional_positions=True,
       total_extra_candidates=1200,both_fee_rows=2402,
       positive_Jan2025_candidates_not_validated=int(len(all_january_positive)),
       full_2025_12_of_12_positive_month_candidates=int(len(train12)),
       training_year_2025_strict_eligible_candidates=int(len(strict)),
       selected_using_only_2025=audits["selected_2025_only"],
       proposed_22_of_22_full_period_goal_met_historically=bool(goal),
       retrospective_all_22_month_candidate_count=int(len(retrospect22)),
       retrospective_hindsight_best=audits["hindsight_best_overall_NOT_SELECTED"],
       retrospective_highest_Jan2025=audits["hindsight_best_January2025_NOT_SELECTED"],
       fees="0.05% taker entry plus GST18%, 5 BTC quote-point adverse slippage per side, hypothetical previously activated <=30m Scalper closing-fee waiver, standard two-sided taker sensitivity",
       caveats=[
          "January2025 is PART OF historically selected 2025 training and cannot independently validate a fix",
          "2026 and prior history repeatedly mined in preceding 28 experiments, not independent OOS",
          "Extensive 1200-variant fitting may manufacture spurious profitable months",
          "Historic regular Scalper Offer opt-in, live spread/orderbook/funding/latency/tick order unverified",
          "No portfolio margin/liquidation/live real order execution model"
       ])
    (OUT/"summary.json").write_text(json.dumps(
        info,indent=2,default=lambda x:x.item() if isinstance(x,np.generic) else str(x))+"\n")
    readme=[
       "# BTC January 2025 recovery — 1200 mandatory weekday backtests",
       "",
       "**January2025 is the losing month; January2026 is already profitable.** All 1200 variants use the exact same 477 full-size 1x-notional BTC entries, each Monday–Friday IST. The Step28 original guard remains intact. Only causal prior-completed monthly account losses choose recovery fallback direction, narrower initial SL and earlier closed-1m-bar exits.",
       "",
       "## Step28 frozen baseline exact parity",
       json.dumps(audits["frozen_Step28_baseline"],indent=2),
       "",
       "## Full 2025 12/12 candidates and stricter selection count",
       str(len(train12)),str(len(strict)),
       "",
       "## Selected using only 2025",
       json.dumps(audits["selected_2025_only"],indent=2),
       "",
       "## January2025 best hindsight (NOT SELECTED)",
       json.dumps(audits["hindsight_best_January2025_NOT_SELECTED"],indent=2),
       "",
       "## All-history 22/22 hindsight candidates",
       str(len(retrospect22)),
       "",
       "## 22-month selected account net returns",
       pd.read_csv(OUT/"selected_2025_only_scalper_offer_22_months.csv").to_markdown(index=False),
       "",
       "## Critical execution / selection caveats",
       "Same historical months have been fitted many times; any 22/22 after retrospective selection may not generalize. The closing Scalper waiver is assumed, and normal taker fee results may be negative. Real funding, spreads and tick paths unavailable."
    ]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(readme)+"\n")
    print("STEP29_COMPLETE "+json.dumps(dict(
        all_candidates=1200,
        january_2025_positive_exploratory=int(len(all_january_positive)),
        twelve_2025_positive_months=int(len(train12)),
        strict_2025_qualified=int(len(strict)),
        historical_22_month_candidates=int(len(retrospect22)),
        benchmark_Jan2025=jan2025,
        selected_Jan2025=chosen_jan,
        selected_months=chosen["win_months_all"],
        selected_net=chosen["net_total_pct"],
        selected_drawdown=chosen["max_closed_dd_pct"],
        historical_complete_goal_met=bool(goal),
        January_hindsight=audits["hindsight_best_January2025_NOT_SELECTED"]["costs"]["scalper_offer"]["January_2025_net_pct"]
    ),sort_keys=True),flush=True)

if __name__=="__main__":
    main()
