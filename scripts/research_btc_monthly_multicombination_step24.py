#!/usr/bin/env python3
"""Step24: 816 factorial causal BTC fallback direction × stop × exit tests.

All models execute exactly ONE full-size BTCUSD 1x notional position for
EVERY one of 477 IST Mon–Fri days. Training/selection is 2025-only;
2026 has already been researched extensively, and therefore is not blind.
The full-history 22-month winner, if any, is HINDSIGHT ONLY.
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
import research_btc_daily_structure_step10 as structural
import audit_btc_daily_risk_crosscheck_step20 as step20

OUT=Path("analysis/btc_monthly_multicombination_step24")
N=len(base.DAYS)
TRAIN=base.NTRAIN
MONTHS=np.asarray(base.MONTH_LABELS)

DIRECTIONS=(
  "baseline",
  "fade5_005","follow5_005",
  "fade60_015","follow60_015",
  "fade240_035","follow240_035",
  "edge60_fade20","edge60_follow20",
  "donchian120_fade010","donchian120_follow010",
  "sma_fade003","sma_follow003",
  "invert_highvol125","invert_lowvol090",
  "zscore60_fade1","vwap0900_fade015",
)
STOPS=(
  "baseline",
  "lowvol090_cap025",
  "highvol125_cap030",
  "against60_015_cap030",
  "wide60_050_cap030",
  "edgeagainst20_cap025",
)
EXITS=(
  "baseline",
  "negative_mtd_profit010_after10",
  "negative_mtd_profit010_after15",
  "negative_mtd_cut008_after5",
  "negative_mtd_timeout20",
  "negative_mtd_stall010_after10",
  "two_losses_cut008_after10",
  "negative_mtd_two_losses_profit010_after5"
)
assert len(DIRECTIONS)==17 and len(STOPS)==6 and len(EXITS)==8
assert len(DIRECTIONS)*len(STOPS)*len(EXITS)==816 and N==477 and TRAIN==260

def compute_features(m,idx,base_side):
    info=risk.preentry_features(m,idx,base_side)
    structure=structural.build_structure(m,idx)
    closed=m.close.to_numpy(float)
    high=m.high.to_numpy(float)
    low=m.low.to_numpy(float)
    q=np.empty(N)
    wide=np.empty(N)
    for d,k in enumerate(idx):
        i=int(k)
        window=closed[i-60:i]
        v=float(np.std(window))
        q[d]=(closed[i-1]-float(np.mean(window)))/v if v>0 else 0.
        wide[d]=(float(np.max(high[i-60:i]))-
                 float(np.min(low[i-60:i])))/float(closed[i-1])
    if not np.isfinite(q).all() or not np.isfinite(wide).all():
        raise AssertionError("Non-finite fully-completed 60m preentry features")
    info["zscore60"]=q
    info["range60_closed"]=wide
    return info,structure

def direction_policy(kind,original,mask,info,structure):
    output=np.asarray(original,dtype=np.int8).copy()
    if kind=="baseline":return output
    for d in np.flatnonzero(mask):
        z=structure[d]
        r5=float(info["r5"][d])
        r60=float(info["r60"][d])
        r240=float(info["r240"][d])
        rvol=float(info["rvol5"][d])
        pos=float(info["loc60"][d])
        current=int(original[d])
        desired=0
        if kind=="fade5_005":
            desired=-np.sign(r5) if abs(r5)>=.0005 else 0
        elif kind=="follow5_005":
            desired=np.sign(r5) if abs(r5)>=.0005 else 0
        elif kind=="fade60_015":
            desired=-np.sign(r60) if abs(r60)>=.0015 else 0
        elif kind=="follow60_015":
            desired=np.sign(r60) if abs(r60)>=.0015 else 0
        elif kind=="fade240_035":
            desired=-np.sign(r240) if abs(r240)>=.0035 else 0
        elif kind=="follow240_035":
            desired=np.sign(r240) if abs(r240)>=.0035 else 0
        elif kind=="edge60_fade20":
            desired=-1 if pos>=.8 else (1 if pos<=.2 else 0)
        elif kind=="edge60_follow20":
            desired=1 if pos>=.8 else (-1 if pos<=.2 else 0)
        elif kind=="donchian120_fade010":
            desired=-1 if z["donchian_up_margin"]>=.001 else (
                      1 if z["donchian_dn_margin"]>=.001 else 0)
        elif kind=="donchian120_follow010":
            desired=1 if z["donchian_up_margin"]>=.001 else (
                      -1 if z["donchian_dn_margin"]>=.001 else 0)
        elif kind=="sma_fade003":
            gap=float(z["sma_gap"])
            desired=-np.sign(gap) if abs(gap)>=.0003 else 0
        elif kind=="sma_follow003":
            gap=float(z["sma_gap"])
            desired=np.sign(gap) if abs(gap)>=.0003 else 0
        elif kind=="invert_highvol125":
            desired=-current if rvol>=1.25 else 0
        elif kind=="invert_lowvol090":
            desired=-current if rvol<=.90 else 0
        elif kind=="zscore60_fade1":
            zz=float(info["zscore60"][d])
            desired=-np.sign(zz) if abs(zz)>=1 else 0
        elif kind=="vwap0900_fade015":
            gap=float(z["vwap_gap"])
            desired=-np.sign(gap) if abs(gap)>=.0015 else 0
        else:
            raise KeyError(kind)
        if desired:
            output[d]=np.int8(desired)
    if np.any(np.abs(output)!=1) or np.any(output[~mask]!=original[~mask]):
        raise AssertionError("Direction changes must only affect real fallback days")
    return output

def stop_condition(name,side,mask,info):
    if name=="baseline":
        return np.zeros(N,dtype=bool),None
    rv=info["rvol5"]
    r60=info["r60"]
    edge=info["loc60"]
    if name=="lowvol090_cap025":
        cond=rv<=.90;cap=.25
    elif name=="highvol125_cap030":
        cond=rv>=1.25;cap=.30
    elif name=="against60_015_cap030":
        cond=side*r60<=-.0015;cap=.30
    elif name=="wide60_050_cap030":
        cond=info["range60_closed"]>=.005;cap=.30
    elif name=="edgeagainst20_cap025":
        cond=((side<0)&(edge>=.8))|((side>0)&(edge<=.2))
        cap=.25
    else:raise KeyError(name)
    return np.asarray(cond&mask,dtype=bool),cap

def per_side_raw(m,indices,base_cfg,info,mask,policies):
    """Replay exact 1m prices separately with side-dependent historical SL.

    Additionals are simulated globally, then applied ONLY on the completed
    preentry feature gate for a particular candidate trading day.
    """
    cached={}
    original_stops={}
    for side in (-1,1):
        one_side=np.full(N,side,dtype=np.int8)
        cfg,_,_=step20.build_capped(
            base_cfg,info,one_side,mask,("with60","counter5"))
        original_stops[side]=cfg[:,1].copy()
        for cap in (None,.25,.30):
            adjusted=cfg.copy()
            if cap is not None:
                adjusted[:,1]=np.minimum(adjusted[:,1],cap)
            raw=early.replay_with_nextbar_exits(
                m.open.to_numpy(float),m.high.to_numpy(float),
                m.low.to_numpy(float),m.close.to_numpy(float),
                indices,one_side,adjusted,policies,base.COST,base.SLIP)
            cached[(side,cap)]=raw
    return cached,original_stops

def merge_side_and_stop(side,trigger,cap,cached):
    """N ×67×2 fee outcomes, one direction and stop for each actual date."""
    n=np.arange(N)
    # Each day uses exactly one side as provided in the preentry policy.
    rows={}
    for sign in (-1,1):
        index=np.flatnonzero(side==sign)
        if len(index)==0:continue
        rows[sign]=index
    base_arrays=[]
    for k in range(5):
        shape=cached[(1,None)][k].shape
        x=np.empty(shape,dtype=cached[(1,None)][k].dtype)
        for sign,index in rows.items():
            normal=cached[(sign,None)][k][index]
            if cap is None:
                x[index]=normal
            else:
                narrow=cached[(sign,cap)][k][index]
                mask_local=trigger[index]
                maskshape=(len(index),)+(1,)*(x.ndim-1)
                x[index]=np.where(mask_local.reshape(maskshape),narrow,normal)
        base_arrays.append(x)
    return tuple(base_arrays)

def choose_exits(raw,mask,condition,ids):
    """Already-settled month PnL drives today's exit; update AFTER each trade."""
    n=N
    chosen=np.zeros(n,dtype=np.int16)
    before=np.zeros(n)
    previous_peak_giveback=np.zeros(n)
    streak_before=np.zeros(n,dtype=np.int8)
    month=None;equity=1.;peak=1.;losses=0
    baseline_profit20=ids["profit_close_at_0.1pct_after_20m"]
    baseline_profit10=ids["profit_close_at_0.1pct_after_10m"]
    event_cut10=ids["adverse_cut_0.08pct_after_10m"]
    for d in range(n):
        if MONTHS[d]!=month:
            month=MONTHS[d];equity=1.;peak=1.;losses=0
        mtd=equity-1.
        before[d]=mtd
        previous_peak_giveback[d]=peak-equity
        streak_before[d]=losses
        if mask[d]:
            if mtd>=.01:
                policy=baseline_profit10
            elif mtd<=.0025:
                policy=baseline_profit20
            else:
                policy=0
            if condition=="negative_mtd_profit010_after10" and mtd<=0:
                policy=baseline_profit10
            elif condition=="negative_mtd_profit010_after15" and mtd<=0:
                policy=ids["profit_close_at_0.1pct_after_15m"]
            elif condition=="negative_mtd_cut008_after5" and mtd<=0:
                policy=ids["adverse_cut_0.08pct_after_5m"]
            elif condition=="negative_mtd_timeout20" and mtd<=0:
                policy=ids["hard_timeout_20m"]
            elif condition=="negative_mtd_stall010_after10" and mtd<=0:
                policy=ids["stall_if_mfe_below_0.1pct_at_10m"]
            elif condition=="two_losses_cut008_after10" and losses>=2:
                policy=event_cut10
            elif condition=="negative_mtd_two_losses_profit010_after5" and mtd<=0 and losses>=2:
                policy=ids["profit_close_at_0.1pct_after_5m"]
            elif condition not in EXITS:
                raise KeyError(condition)
        else:
            policy=event_cut10 if mtd<=0 else 0
        chosen[d]=policy
        # Absolutely no current-day outcome used before today's choice.
        day_return=float(raw[0][d,policy,1]) # hypothetical offer
        equity*=1.+day_return
        peak=max(peak,equity)
        losses=(losses+1) if day_return<0 else 0
    return chosen,before,previous_peak_giveback,streak_before

def select_path(raw,policies,mode):
    days=np.arange(N)
    return tuple(
       a[days,policies,mode] if k<2 else a[days,policies]
       for k,a in enumerate(raw))

def one_score(p):
    return step15.score(p)

def simulation(side,stop_name,exit_name,raw_cache,info,mask,ids):
    trigger,cap=stop_condition(stop_name,side,mask,info)
    raw=merge_side_and_stop(side,trigger,cap,raw_cache)
    policy,mtd,giveback,streak=choose_exits(raw,mask,exit_name,ids)
    offer=one_score(select_path(raw,policy,1))
    standard=one_score(select_path(raw,policy,0))
    return offer,standard,(raw,policy,mtd,giveback,streak,trigger,cap)

def save_ledger(label,model,side,mask,hours,info,base_stops,filename_tag):
    raw,policy,mtd,giveback,streak,trigger,cap=model
    initial=np.asarray([base_stops[int(s)][i] for i,s in enumerate(side)])
    narrowed=trigger & (cap is not None) & (initial>float(cap) if cap is not None else False)
    newstop=np.minimum(initial,cap) if cap is not None else initial.copy()
    newstop=np.where(trigger,newstop,initial)
    for fee_i,fee in enumerate(base.MODES):
        path=select_path(raw,policy,fee_i)
        pnl,fees,gross,why,held=path
        daily=pd.DataFrame(dict(
           date_ist=base.IST_DAYS,year=np.asarray(base.DAYS.year),
           month_ist=MONTHS,entry_hour_ist=hours,
           entry_category=np.where(mask,"FORCED_FALLBACK","VOLUME_EVENT"),
           side=np.where(side==1,"LONG","SHORT"),
           original_stop_pct=initial,chosen_stop_pct=newstop,
           narrower_initial_stop=narrowed,
           previous_month_net_pct=mtd*100.,
           previous_month_peak_giveback_pct=giveback*100.,
           earlier_month_consecutive_losses=streak,
           exit_policy_index=policy,
           daily_account_net_pct=pnl*100.,
           gross_btc_quote_points=gross,fee_gst_btc_quote_points=fees,
           adverse_slip_quote_points=base.SLIP*2,
           exit_reason=np.where(why==1,"TP",np.where(why==2,"STOP",
                         np.where(why==3,"TIMEOUT","NEXT_1M_OPEN_EARLY_EXIT"))),
           hold_minutes=held,
           model=label,fee_model=fee
        ))
        if len(daily)!=477 or daily.date_ist.nunique()!=477 or (
                pd.to_datetime(daily.date_ist).dt.dayofweek>=5).any():
            raise AssertionError("Daily trade contract violated")
        monthly=daily.groupby("month_ist",sort=True).agg(
            trades=("date_ist","size"),
            profitable_days=("daily_account_net_pct",lambda x:int(np.sum(x>0))),
            losing_days=("daily_account_net_pct",lambda x:int(np.sum(x<0))),
            compounded_net_pct=("daily_account_net_pct",
                lambda x:float(100*(np.prod(1+x.to_numpy()/100)-1))),
            net_fee_gst_btc_points=("fee_gst_btc_quote_points","sum"),
            gross_btc_points=("gross_btc_quote_points","sum"),
            stops_narrowed=("narrower_initial_stop","sum")
        ).reset_index()
        assert len(monthly)==22 and monthly.trades.sum()==477
        score=one_score(path)
        if int((monthly.compounded_net_pct>0).sum())!=score["win_months_all"]:
            raise AssertionError("Reported monthly score and 477 trade ledger disagree")
        daily.to_csv(OUT/(filename_tag+"_"+fee+"_477_daily.csv"),index=False)
        monthly.to_csv(OUT/(filename_tag+"_"+fee+"_22_months.csv"),index=False)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    m,ctx,mask,fb,original,hours,indices,base_cfg=step13.create_path()
    policies,names=early.build_exit_policies()
    ids={name:i for i,name in enumerate(names)}
    info,structure=compute_features(m,indices,original)
    cached,stops=per_side_raw(m,indices,base_cfg,info,mask,policies)

    # Baseline daily parity is a CRITICAL correctness gate. Do not report any
    # improvement unless Step20 B was reconstructed using correct long/short
    # dynamic protective stops, closed 1m profits and historical fee model.
    base_offer,base_standard,base_data=simulation(
        original,"baseline","baseline",cached,info,mask,ids)
    assert base_offer["trades"]==477 and base_offer["win_months_all"]==21
    assert base_offer["profitable_days"]==292
    assert abs(base_offer["net_total_pct"]-25.423847)<.00011
    assert abs(base_offer["max_closed_dd_pct"]-2.617670)<.00011
    assert abs(base_standard["net_total_pct"]+5.332682)<.00011
    print("STEP24_PARITY_VERIFIED "+json.dumps({
       "offer":base_offer,"standard":base_standard},sort_keys=True),flush=True)

    records=[]
    base_metadata=dict(
        model="baseline",direction_rule="baseline",stop_rule="baseline",
        exit_rule="baseline",fallback_sides_changed=0,
        fallback_changes_2025=0,fallback_changes_2026=0,
        additional_stop_condition_days=0)
    for cost,perf in (("scalper_offer",base_offer),("standard",base_standard)):
        records.append(dict(**base_metadata,cost_model=cost,**perf))

    short_table=[]
    direction_cache={}
    for direction in DIRECTIONS:
        side=direction_policy(direction,original,mask,info,structure)
        direction_cache[direction]=side
        changed=(side!=original)&mask
        for stop in STOPS:
            trigger,cap=stop_condition(stop,side,mask,info)
            raw=merge_side_and_stop(side,trigger,cap,cached)
            for exit_rule in EXITS:
                policy,mtd,giveback,streak=choose_exits(raw,mask,exit_rule,ids)
                price=one_score(select_path(raw,policy,1))
                std=one_score(select_path(raw,policy,0))
                metadata=dict(
                   model=f"{direction}__{stop}__{exit_rule}",
                   direction_rule=direction,stop_rule=stop,exit_rule=exit_rule,
                   fallback_sides_changed=int(changed.sum()),
                   fallback_changes_2025=int(changed[:TRAIN].sum()),
                   fallback_changes_2026=int(changed[TRAIN:].sum()),
                   additional_stop_condition_days=int(trigger.sum()))
                for fee,perf in (("scalper_offer",price),("standard",std)):
                    records.append(dict(**metadata,cost_model=fee,**perf))
        print("STEP24_COMBINATIONS "+json.dumps(dict(
            completed_directions=len(direction_cache),
            completed_models=len(records)//2,
            last_direction=direction)),flush=True)

    frame=pd.DataFrame(records)
    assert len(frame)==1634 and frame.trades.eq(477).all()
    frame.to_csv(OUT/"all_816_factorial_combinations_two_cost_models.csv",index=False)
    offer=frame[frame.cost_model=="scalper_offer"].copy()
    # Strict selection from 2025 ONLY, not from 2026 or losing Jan2025 alone.
    eligible=offer[(offer.model!="baseline")&
       (offer.win_months_2025>=12)&
       (offer.return_2025_pct>=base_offer["return_2025_pct"]-1.e-6)&
       (offer.profitable_days_2025>=base_offer["profitable_days_2025"])&
       (offer.max_dd_2025<=base_offer["max_dd_2025"]+1.e-4)]
    if len(eligible):
        winner=eligible.sort_values(
           ["win_months_2025","return_2025_pct",
            "profitable_days_2025","max_dd_2025"],
           ascending=[False,False,False,True]).iloc[0].to_dict()
    else:
        winner=offer[offer.model=="baseline"].iloc[0].to_dict()

    retrospective=offer.sort_values(
       ["win_months_all","net_total_pct","max_closed_dd_pct"],
       ascending=[False,False,True])
    hindsight22=retrospective[retrospective.win_months_all==22]
    hindsight22.to_csv(OUT/"hindsight_22_of_22_not_selected.csv",index=False)
    top21=offer[offer.win_months_all>=21].sort_values(
       ["net_total_pct","max_closed_dd_pct"],ascending=[False,True]).head(20)
    top21.to_csv(OUT/"top_21plus_month_models_hindsight.csv",index=False)
    top_months=retrospective.head(20)
    top_months.to_csv(OUT/"top_monthly_consistency_hindsight.csv",index=False)
    train12=offer[offer.win_months_2025==12]
    train12.sort_values("return_2025_pct",ascending=False).to_csv(
        OUT/"positive_12_of_12_train_candidates.csv",index=False)

    # Replay freeze 2025 selected policy, plus highest monthly full-history
    # example as DIAGNOSTIC ONLY. Neither is a real held-out 2026 test.
    for tag,record in (("2025_selected",winner),
                       ("hindsight_monthly_best_NOT_SELECTED",retrospective.iloc[0].to_dict()),
                       ("hindsight_high_net_21plus",top21.iloc[0].to_dict() if len(top21) else retrospective.iloc[0].to_dict())):
        s=direction_cache[record["direction_rule"]]
        p,o,d=simulation(
            s,record["stop_rule"],record["exit_rule"],cached,info,mask,ids)
        if (abs(p["net_total_pct"]-record["net_total_pct"])>.000001 or
            p["win_months_all"]!=record["win_months_all"]):
            raise AssertionError("Top scenario recomputation drift")
        save_ledger(record["model"],d,s,mask,hours,info,stops,tag)
        print("STEP24_REPLAY_"+tag.upper()+" "+
            json.dumps(dict(model=record["model"],offer=p,standard=o),
                       sort_keys=True),flush=True)

    result=dict(
        experiment="Factorial market structure fallback direction x initial stop x causal loss-month early exits",
        full_ist_weekday_dates=477,
        full_1x_notional_each_trade=True,
        baseline=dict(offer=base_offer,standard=base_standard),
        factor_levels=dict(directions=len(DIRECTIONS),stops=len(STOPS),exits=len(EXITS)),
        unique_candidates=816,with_baseline=817,both_cost_rows=1634,
        qualified_2025_only_12_month_models=int(len(eligible)),
        selected_using_only_2025=winner,
        2026_research_exposed_result=dict(
            profitable_months_2026=winner["win_months_2026"],
            return_2026_pct=winner["return_2026_pct"],
            overall_win_months=winner["win_months_all"],
            total_net_pct=winner["net_total_pct"],
            max_closed_drawdown_pct=winner["max_closed_dd_pct"]),
        full_history_hindsight_22_month_count=int(len(hindsight22)),
        full_history_hindsight_highest_month_score_NOT_SELECTED=retrospective.iloc[0].to_dict(),
        historical_21plus_highest_return_NOT_SELECTED=top21.iloc[0].to_dict() if len(top21) else None,
        source="Delta BTCUSD 1m historical Jan2025–Oct2026",
        fee_model="5 BTC quote points adverse each leg; 0.05% taker per leg plus GST 18%; hypothetical preactivated Scalper regular offer closing fee waived for qualified <=30m positions; standard fully charged comparison",
        limitations=[
            "2025 and 2026 extensively researched; 2026 IS NOT independent future validation",
            "816 variants increase data snooping/overfit risk and any 22/22 past months cannot prove future",
            "Baseline B itself was selected with full-period hindsight in earlier steps",
            "Historic Scalper Offer activation, live spread/depth, fill latency, funding and liquidation are unverified"
        ])
    (OUT/"summary.json").write_text(json.dumps(
        result,indent=2,default=lambda v:v.item() if isinstance(v,np.generic) else str(v))+"\n")
    report=[
      "# Step24 BTCUSD — 816 causal direction/stop/exit combinations",
      "",
      "Every model places a full 1x notional trade on ALL 477 full IST Monday-Friday days. Only preentry closed-bar fallback direction, initial SL caps, and prior-trade-month-dependent early exit may change. Results with hypothetical historical fee waiver and separately standard fees/GST/slippage.",
      "",
      "## Verified baseline exact parity",json.dumps(result["baseline"],indent=2),
      "",
      "## 2025 ONLY selected; 2026 research-exposed historical recheck",json.dumps(winner,indent=2),
      "",
      "## Highest full-history winning months (HINDSIGHT ONLY)",
      retrospective.head(10)[["model","win_months_all","win_months_2025","win_months_2026","net_total_pct","profitable_days","max_closed_dd_pct","worst_month_pct"]].to_markdown(index=False),
      "",
      "## Positive 12/12 2025 month model count",str(len(train12)),
      "",
      "## Full historical 22/22 models, NOT SELECTED",str(len(hindsight22)),
      "",
      "## 22-month returns for strictly 2025-selected model",
      pd.read_csv(OUT/"2025_selected_scalper_offer_22_months.csv").to_markdown(index=False),
      "",
      "## Caution",
      "Any retrospective 22/22 or high return is in-sample after dozens of prior experiments. These data cannot validate out-of-sample edge. Historical Scalper Offer waiver, actual orderbook fills/latency/funding and intraminute path unverified."
    ]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")
    print("STEP24_COMPLETE "+json.dumps(dict(
        models=817,matched_2025_train=int(len(eligible)),
        train_12month_count=int(len(train12)),
        retrospective_22month_count=int(len(hindsight22)),
        selected_model=winner["model"],
        selected_net=winner["net_total_pct"],
        selected_months=winner["win_months_all"],
        best_retrospective=retrospective.iloc[0][["model","win_months_all","net_total_pct","max_closed_dd_pct"]].to_dict()
    ),sort_keys=True,default=lambda v:v.item() if isinstance(v,np.generic) else str(v)),flush=True)

if __name__=="__main__":
    main()
