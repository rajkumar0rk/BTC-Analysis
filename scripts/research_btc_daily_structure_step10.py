#!/usr/bin/env python3
"""Step 10. BTCUSD mandatory weekday structural direction overlays, frozen exits.

Causal EMA/Donchian, rolling range edges, momentum, and anchored VWAP use
ONLY fully completed 1m OHLCV before the existing Step8 entry timestamp.
Every candidate places exactly 477 trades (no weekends, no abstentions).
2025-only selection; 2026 research-exposed recheck. No live claims.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd

import research_btc_every_weekday_reset_step1 as base
import research_btc_daily_online_direction_step6 as step6
import research_btc_daily_causal_neighbors_step8 as step8
import research_btc_every_weekday_adaptive_step2 as adaptive

OUT=Path("analysis/btc_daily_structure_step10")
DAYS=base.DAYS
N=477
TRAIN=260
TYPES=("event","fallback","both")
KIND=(
    "edge60_follow","edge60_fade",
    "edge240_follow","edge240_fade",
    "momentum60_follow","momentum60_fade",
    "momentum240_follow","momentum240_fade",
    "donchian120_follow","donchian120_fade",
    "sma20v60_follow","sma20v60_fade",
    "vwap0900_follow","vwap0900_fade"
)
ASSERT_MODELS=len(KIND)*2*len(TYPES)+1
assert ASSERT_MODELS==85

def close_sign(v):
    return 1 if v>=0 else -1

def build_structure(m,idx):
    op=m.open.to_numpy(float)
    hi=m.high.to_numpy(float);lo=m.low.to_numpy(float)
    cl=m.close.to_numpy(float)
    vol=m.volume.to_numpy(float)
    sess,_,_=base.prepare(m)
    day9=sess[:,9]
    data=[]
    for d in range(N):
        i=int(idx[d])
        y=float(cl[i-1]);p0=float(op[i])
        q={}
        q["r60"]=y/float(op[i-60])-1
        q["r240"]=y/float(op[i-240])-1
        for minutes in (60,240):
            upper=float(hi[i-minutes:i].max())
            lower=float(lo[i-minutes:i].min())
            q[f"position{minutes}"]=(y-lower)/(upper-lower) if upper>lower else .5
        prior_upper=float(hi[i-125:i-5].max())
        prior_lower=float(lo[i-125:i-5].min())
        q["donchian_up_margin"]=y/prior_upper-1
        q["donchian_dn_margin"]=prior_lower/y-1
        sma20=float(cl[i-20:i].mean())
        sma60=float(cl[i-60:i].mean())
        q["sma_gap"]=sma20/sma60-1.
        start=int(day9[d])
        # True historical exchange volume; only minutes with close < entry.
        assert start < i and i-start<=13*60
        tprice=(hi[start:i]+lo[start:i]+cl[start:i])/3.
        v=vol[start:i]
        total=float(v.sum())
        weighted=float(np.dot(tprice,v)/total) if total>0 else float(cl[start:i].mean())
        q["vwap_gap"]=y/weighted-1.
        for val in q.values():
            if not np.isfinite(val):
                raise AssertionError(f"Nonfinite preentry structure day {d}")
        data.append(q)
    return data

def desired_for(kind,level,q):
    """Return 0 when context does not justify an override, else {-1,+1}."""
    isfade=kind.endswith("_fade")
    if kind.startswith("edge60") or kind.startswith("edge240"):
        minutes=60 if kind.startswith("edge60") else 240
        edge=(.8,.9)[level]
        pos=q[f"position{minutes}"]
        side=1 if pos>=edge else (-1 if pos<=1-edge else 0)
    elif kind.startswith("momentum60") or kind.startswith("momentum240"):
        minutes=60 if kind.startswith("momentum60") else 240
        lim=(.002,.004)[level] if minutes==60 else (.0035,.007)[level]
        ret=q[f"r{minutes}"]
        side=close_sign(ret) if abs(ret)>=lim else 0
    elif kind.startswith("donchian120"):
        lim=(0.,.001)[level]
        up=q["donchian_up_margin"];dn=q["donchian_dn_margin"]
        side=1 if up>lim else (-1 if dn>lim else 0)
    elif kind.startswith("sma20v60"):
        lim=(.0003,.0008)[level]
        ret=q["sma_gap"]
        side=close_sign(ret) if abs(ret)>=lim else 0
    elif kind.startswith("vwap0900"):
        lim=(.0015,.003)[level]
        ret=q["vwap_gap"]
        side=close_sign(ret) if abs(ret)>=lim else 0
    else:
        raise KeyError(kind)
    return (-side if isfade else side) if side else 0

def baseline_context(m):
    f,mask,evdata,fbdata,baseev,evhist,reference=step8.initial_dataset(m)
    # The exact preselected Step8 *2025-only* fallback learner.
    knn,prior_count,_=step8.causal_nearest(
        step8.feature_view(fbdata,"extended"),
        f["fallback"][1,"E"][0],
        mask,45,36,"win","conservative",4)
    hours=np.where(mask,21,f["event_hours"]).astype(np.int16)
    starts,_,_=base.prepare(m)
    indices=starts[np.arange(N),hours]
    side_event=np.where(baseev==0,f["event_signs"],-f["event_signs"])
    side_fallback=f["fall_signs"][np.arange(N),knn]
    side=np.where(mask,side_fallback,side_event)
    expected={}
    for mode_i,mode in enumerate(base.MODES):
        ret=step6.pick_path(
            f["event"][mode_i],baseev,f["fallback"][mode_i,"E"],knn,mask)
        expected[mode]=ret
    old=step6.metrics(*expected["scalper_offer"])
    if old["profitable_days"]!=277 or abs(old["net_total_pct"]-21.423313)>.00011:
        raise AssertionError("Step8 2025-selected exact baseline changed")
    return f,mask,baseev,knn,indices,hours,side,expected,prior_count

def choose(kind,threshold,group,f,mask,be,bf,side,features):
    ev=be.copy()
    fall=bf.copy()
    applied=np.zeros(N,dtype=bool)
    for d in range(N):
        is_event=not mask[d]
        if (group=="event" and not is_event) or (
            group=="fallback" and is_event):
            continue
        wanted=desired_for(kind,threshold,features[d])
        if not wanted:continue
        if wanted==side[d]:continue
        if is_event:
            ev[d]=0 if wanted==int(f["event_signs"][d]) else 1
        else:
            fall[d]=0 if wanted==int(f["fall_signs"][d,0]) else 1
        applied[d]=True
    return ev,fall,applied

def one_metrics(p,fees,gross,reason,hold):
    stats=step6.metrics(p,fees,gross,reason,hold)
    return stats

def monthly(p,fee,gross,reason,hold,mode,hours,sides,mask,ev,fb,override):
    df=pd.DataFrame(dict(
        date_ist=base.IST_DAYS,
        month_ist=base.MONTH_LABELS,
        year=np.asarray(DAYS.year),
        hour_ist=hours,
        direction=np.where(sides>0,"LONG","SHORT"),
        entry_type=np.where(mask,"MANDATORY_FALLBACK","VOLUME_SIGNAL"),
        event_arm=ev,
        fallback_arm=fb,
        overridden_direction=override,
        net_account_pct=p*100.,
        gross_btc_points=gross,
        fee_gst_btc_points=fee,
        slip_points=np.full(N,2*base.SLIP),
        reason=np.where(reason==1,"TP",np.where(reason==2,"PROTECTIVE_STOP","TIMEOUT")),
        hold_minutes=hold,
        fee_model=mode
    ))
    assert len(df)==477 and df.date_ist.nunique()==477
    assert (pd.to_datetime(df.date_ist).dt.dayofweek<5).all()
    months=df.groupby("month_ist",sort=True).agg(
        trades=("date_ist","size"),
        win_days=("net_account_pct",lambda x:int((x>0).sum())),
        lose_days=("net_account_pct",lambda x:int((x<0).sum())),
        compounded_net_pct=("net_account_pct",lambda x:float(100*(np.prod(1+x.to_numpy()/100)-1))),
        fee_gst_points=("fee_gst_btc_points","sum"),
        gross_points=("gross_btc_points","sum")
    ).reset_index()
    assert len(months)==22
    return df,months

def run():
    OUT.mkdir(parents=True,exist_ok=True)
    m=base.load()
    f,mask,be,bf,indices,hours,bsides,reference,prevcount=baseline_context(m)
    structure=build_structure(m,indices)
    # Frozen reference measured before any candidate, per-trade equality for
    # every selected baseline configuration.
    baseline={}
    for mode in base.MODES:
        baseline[mode]=one_metrics(*reference[mode])
    print("STEP10_BASELINE "+json.dumps(baseline,sort_keys=True),flush=True)
    decisions=[("baseline",0,"none",be,bf,np.zeros(N,dtype=bool))]
    for kind in KIND:
        for strength in (0,1):
            for group in TYPES:
                e,b,changed=choose(kind,strength,group,f,mask,be,bf,bsides,structure)
                decisions.append((kind,strength,group,e,b,changed))
    assert len(decisions)==85
    allrows=[]
    for kind,level,group,e,b,changed in decisions:
        # Exactly one unchanged entry time for each of all 477 weekdays.
        assert e.shape==b.shape==(N,) and len(indices)==N
        for mi,mode in enumerate(base.MODES):
            x=step6.pick_path(f["event"][mi],e,
                   f["fallback"][mi,"E"],b,mask)
            s=one_metrics(*x)
            if kind=="baseline":
                if not np.allclose(x[0],reference[mode][0],atol=1e-14,rtol=0):
                    raise AssertionError("Per-day baseline parity failed")
            s.update(
                structure=kind,intensity=int(level),trade_type=group,
                scenario=f"{kind}__{level}__{group}",cost_model=mode,
                direction_changes_total=int(changed.sum()),
                direction_changes_2025=int(changed[:TRAIN].sum()),
                direction_changes_2026=int(changed[TRAIN:].sum()),
                changes_on_events=int((changed&(~mask)).sum()),
                changes_on_fallback=int((changed&mask).sum()))
            allrows.append(s)
    result=pd.DataFrame(allrows)
    if len(result)!=170 or not result.trades.eq(477).all():
        raise AssertionError("Failed full weekday model coverage")
    result.to_csv(OUT/"all_85_structure_direction_rules_two_fee_models.csv",index=False)
    print("STEP10_GRID "+json.dumps(dict(models=85,fee_scenarios=170,
        exact_weekday_trades=477,volume_events=int((~mask).sum()),
        forced_fallbacks=int(mask.sum())),sort_keys=True),flush=True)
    offer=result[result.cost_model=="scalper_offer"]
    eligible=offer[(offer.profitable_days_2025>=147)&
                   (offer.return_2025_pct>=8.10265)&
                   (offer.max_dd_2025<=3.00875)]
    # Select the best *2025* model; original baseline included, so never
    # promote a worse 2025 result just to beat 2026 hindsight.
    sort=eligible.sort_values(
        ["profitable_days_2025","return_2025_pct","max_dd_2025"],
        ascending=[False,False,True])
    chosen=sort.iloc[0].to_dict()
    target=[row for row in decisions
        if f"{row[0]}__{row[1]}__{row[2]}"==chosen["scenario"]][0]
    name,level,group,ce,cf,changed=target
    chosen_side=np.where(mask,
          f["fall_signs"][np.arange(N),cf],
          np.where(ce==0,f["event_signs"],-f["event_signs"]))
    summary={}
    for mi,mode in enumerate(base.MODES):
        x=step6.pick_path(f["event"][mi],ce,
            f["fallback"][mi,"E"],cf,mask)
        d,months=monthly(*x,mode,hours,chosen_side,mask,ce,cf,changed)
        d.to_csv(OUT/(mode+"_2025_selected_477_daily.csv"),index=False)
        months.to_csv(OUT/(mode+"_2025_selected_22_months.csv"),index=False)
        s=one_metrics(*x)
        summary[mode]=dict(result=s,profitable_months=int((months.compounded_net_pct>0).sum()),
            worst_month_pct=round(float(months.compounded_net_pct.min()),5),
            delta_winning_days_2025=int(s["profitable_days_2025"]-baseline[mode]["profitable_days_2025"]),
            delta_winning_days_2026=int(s["profitable_days_2026"]-baseline[mode]["profitable_days_2026"]),
            delta_net_pct_2025=round(float(s["return_2025_pct"]-baseline[mode]["return_2025_pct"]),5),
            delta_net_pct_2026=round(float(s["return_2026_pct"]-baseline[mode]["return_2026_pct"]),5),
            delta_max_dd_pct=round(float(s["max_closed_dd_pct"]-baseline[mode]["max_closed_dd_pct"]),5))
        print("STEP10_SELECTED_"+mode.upper()+" "+json.dumps(summary[mode],sort_keys=True),flush=True)
        print("STEP10_MONTHLY_"+mode.upper()+"\n"+months.to_string(index=False),flush=True)
    full_best=offer.sort_values(["net_total_pct","profitable_days"],ascending=False).iloc[0].to_dict()
    both=(offer.return_2025_pct>0)&(offer.return_2026_pct>0)
    strictly=(offer.profitable_days>=277)&(offer.net_total_pct>21.423313)&(
        offer.max_closed_dd_pct<=3.008746)&(offer.win_months_all>=15)
    wins_both_years=(offer.profitable_days_2025>=147)&(offer.profitable_days_2026>=130)
    improves2026=(offer.return_2026_pct>12.322236)&(
       offer.profitable_days_2026>=130)&(offer.max_dd_2026<=2.96468)
    report=dict(
      benchmark_step8=baseline,
      exact_daily_trades=477,
      models=85,
      2025_eligible_models=int(len(eligible)),
      chosen_by_2025_only=chosen,
      chosen_per_cost=summary,
      historical_pareto_better_than_step8_hindsight=int(strictly.sum()),
      historical_better_2026_profit_win_dd_hindsight=int(improves2026.sum()),
      historical_at_least_as_many_wins_each_year=int(wins_both_years.sum()),
      full_history_highest_net_hindsight_not_selected=full_best,
      both_year_net_positive_hindsight=int(both.sum()),
      limitations=[
        "2026 was repeatedly researched, not a pristine forward holdout",
        "Structural indicators have been tested in earlier Stage7/13/19/24/25; this is only a constrained overlay",
        "Historical Scalper Offer activation and live orderbook fills not validated",
        "No bid/ask depth, funding, slippage beyond 5 points/leg, latency or liquidation",
        "100% daily notional cannot guarantee net account profit on every weekday"
      ])
    (OUT/"summary.json").write_text(json.dumps(report,indent=2)+"\n")
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join([
       "# Step10 — structure-based direction overrides without reducing BTC trades",
       "",
       "All 85 causal structural policies enter exactly once on 477 IST Monday–Friday dates, at the PREVIOUS Step8 entry times and with exactly the PREVIOUS Step8 profit protection/stop/timing. The only difference may be the direction of some entries.",
       "",
       "## Exact Step8 baseline verification",
       json.dumps(baseline,indent=2),
       "",
       "## Policy selected on 2025 only",
       json.dumps(chosen,indent=2),
       "",
       "## 2026 recheck and net performance",
       json.dumps(summary,indent=2),
       "",
       "## Selected 22 monthly Scalper Offer returns",
       pd.read_csv(OUT/"scalper_offer_2025_selected_22_months.csv").to_markdown(index=False),
       "",
       "## Important constraints",
       "2026 has been studied in many prior optimization rounds, hence no independent OOS test. Long/short entry changes based only on completed past price action; the historical offer status is assumed and not verified."
    ])+"\n")
    print("STEP10_DONE "+json.dumps(report,sort_keys=True),flush=True)

if __name__=="__main__":
    run()
