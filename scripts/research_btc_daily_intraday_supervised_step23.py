#!/usr/bin/env python3
"""Step23: intraday minute-labeled supervised BTC direction, every weekday.

Unlike Step22 daily shadow label training, this uses only PRIOR CLOSED
30m BTC price moves sampled each half-hour, available already from Jan 1
2025 and thus before January 2025 daily trading starts. No future returns.
Full 477 nonzero 1x BTC positions with frozen Step20 B stops/exits/costs.
"""
from pathlib import Path
from itertools import product
import json

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge, LogisticRegression
from sklearn.preprocessing import StandardScaler

import research_btc_every_weekday_reset_step1 as base
import research_btc_daily_monthly_exit_step13 as step13
import research_btc_daily_monthly_two_regime_step15 as step15
import research_btc_daily_month_start_direction_step17 as step17
import research_btc_daily_exit_invalidation_step7 as early
import research_btc_daily_supervised_side_step22 as prev
import audit_btc_daily_risk_crosscheck_step20 as step20

OUT=Path("analysis/btc_daily_intraday_supervised_step23")
N=len(base.DAYS);TRAIN=base.NTRAIN
MONTHS=np.asarray(base.MONTH_LABELS)
ALGORITHMS=("ridge","logistic")
DAYS_BACK=(1,3,7)
CONFIDENCES=(.20,.40,.60)
SCOPES=("event","fallback","both")
assert N==477 and TRAIN==260 and len(ALGORITHMS)*len(DAYS_BACK)*len(CONFIDENCES)*len(SCOPES)==54

def preentry_x(t,o,h,l,c,v):
    """All features use strictly candles before t. No current ohlc labels."""
    i=int(t)
    last=float(c[i-1])
    # Normalize exclusively by the previous COMPLETED close, not by the
    # still-opening trade candle; the signal is fully formed preentry.
    op=last
    r5=last/o[i-5]-1.
    r15=last/o[i-15]-1.
    r60=last/o[i-60]-1.
    r240=last/o[i-240]-1.
    own=float(v[i-5:i].sum())
    older=float(v[i-105:i-5].sum())
    volume_ratio=own*20./older if older>0 else 1.
    upper=float(np.max(h[i-60:i]))
    lower=float(np.min(l[i-60:i]))
    span=(upper-lower)/op
    pos=(last-lower)/(upper-lower) if upper>lower else .5
    sma20=float(np.mean(c[i-20:i]))
    sma60=float(np.mean(c[i-60:i]))
    gap=sma20/sma60-1.
    diff=np.diff(c[i-15:i])
    gains=float(np.mean(np.maximum(diff,0)))
    losses=float(np.mean(np.maximum(-diff,0)))
    rsi=gains/(gains+losses) if gains+losses>0 else .5
    range15=float(np.max(h[i-15:i])-np.min(l[i-15:i]))/op
    return np.clip(np.asarray([
       r5/.0015,r15/.003,r60/.007,r240/.015,
       volume_ratio-1.,span/.01,(pos-.5)*2.,
       gap/.002,(rsi-.5)*2.,range15/.004
    ],dtype=np.float64),-5.,5.)

def full_minute_training_catalog(m,indices):
    # Precompute features and future 30m OHLC label on all global 30min
    # time boundaries. At a given entry, select only rows with label
    # completed BEFORE that entry. Never share current/future label.
    o=m.open.to_numpy(float)
    h=m.high.to_numpy(float)
    l=m.low.to_numpy(float)
    c=m.close.to_numpy(float)
    v=m.volume.to_numpy(float)
    sample_times=np.arange(300,len(o)-30,30,dtype=np.int64)
    features=np.empty((len(sample_times),10),dtype=np.float32)
    for n,t in enumerate(sample_times):
        features[n]=preentry_x(t,o,h,l,c,v)
    price_return=(c[sample_times+29]/o[sample_times]-1.)*10000.
    if not np.isfinite(features).all() or not np.isfinite(price_return).all():
        raise AssertionError("Nonfinite completed-bar training features or label")
    if np.max(indices)>=len(o)-30:
        raise AssertionError("Incomplete 30m entry horizon")
    # All frozen hourly entries are on the same 30m UTC price grid.
    if not np.all(np.isin(indices,sample_times)):
        raise AssertionError("Historical 1m entry no longer matches 30m sampling grid")
    return sample_times,features.astype(np.float64),price_return

def train_predict(timestamps,features,returns,entry_times,algo,lookback):
    """Each prediction learns only fully completed 30m samples before entry."""
    N=len(entry_times)
    score=np.zeros(N,dtype=np.float64)
    count=np.zeros(N,dtype=np.int16)
    yclass=(returns>0).astype(np.int8)
    for d,i0 in enumerate(entry_times):
        i=int(i0)
        left=int(np.searchsorted(timestamps,i-lookback*1440,side="left"))
        # Last possible training label is 30m starting at i-30,
        # whose CLOSE is i-1 (already completed at trade entry i).
        right=int(np.searchsorted(timestamps,i-30,side="right"))
        num=right-left
        count[d]=num
        if num<24:continue
        pos=timestamps[left:right]
        if len(pos)!=num or pos.max()+29>=i:
            raise AssertionError("Label leakage: 30m future close after trade entry")
        xs=features[left:right,:]
        standard=StandardScaler()
        X=standard.fit_transform(xs)
        test=standard.transform(features[np.searchsorted(timestamps,i):np.searchsorted(timestamps,i)+1,:])
        if len(test)!=1:
            raise AssertionError("Missing independent current preentry features")
        if algo=="ridge":
            mod=Ridge(alpha=10.)
            mod.fit(X,returns[left:right])
            estimate=float(mod.predict(test)[0])
            denom=max(float(np.std(returns[left:right])),1.e-8)
            score[d]=float(np.clip(estimate/denom,-1.,1.))
        elif algo=="logistic":
            ys=yclass[left:right]
            if np.unique(ys).size<2:
                score[d]=1. if ys[0]==1 else -1.
            else:
                model=LogisticRegression(
                   C=.25,solver="liblinear",max_iter=180,random_state=17)
                model.fit(X,ys)
                score[d]=float(np.clip(2*model.predict_proba(test)[0,1]-1.,-1.,1.))
        else:
            raise KeyError(algo)
    return score,count

def evaluate(long,short,side,mask,ids):
    raw=step17.select_sign_arrays(long,short,side)
    choices=step15.replay_one(
        raw,mask,ids["profit_close_at_0.1pct_after_20m"],
        step20.PARAMS["B"],ids)
    results={}
    for mi,mode in enumerate(base.MODES):
        path=step15.getout(raw,choices[0],mi)
        results[mode]=step15.score(path)
    return raw,choices,results

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    m,ctx,mask,fb,baseline_side,hours,indices,cfg=step13.create_path()
    policy,names=early.build_exit_policies()
    ids={name:i for i,name in enumerate(names)}
    factor=step20.prev.preentry_features(m,indices,baseline_side)
    directions={}
    for sign in (1,-1):
        s=np.full(N,sign,dtype=np.int8)
        local_cfg,_,_=step20.build_capped(
            cfg,factor,s,mask,("with60","counter5"))
        directions[sign]=early.replay_with_nextbar_exits(
           m.open.to_numpy(float),m.high.to_numpy(float),
           m.low.to_numpy(float),m.close.to_numpy(float),
           indices,s,local_cfg,policy,base.COST,base.SLIP)
    long=directions[1]
    short=directions[-1]
    raw0,dec0,baseline=evaluate(long,short,baseline_side,mask,ids)
    bench=baseline["scalper_offer"]
    if (bench["trades"]!=477 or bench["win_months_all"]!=21 or
        abs(bench["net_total_pct"]-25.423847)>.00011 or
        abs(bench["max_closed_dd_pct"]-2.617670)>.00011 or
        bench["profitable_days"]!=292 or
        abs(baseline["standard"]["net_total_pct"]+5.332682)>.00011):
        raise AssertionError("Frozen Step20 B regression mismatch "+str(bench))
    print("STEP23_FROZEN_BASELINE "+json.dumps(baseline,sort_keys=True),flush=True)
    sample_times,X,returns=full_minute_training_catalog(m,indices)
    print("STEP23_SAMPLE_CATALOG "+json.dumps(dict(
        half_hour_historical_samples=len(sample_times),
        prior_training_labels_complete_before_each_current_entry=True,
        earliest_archive_utc=str(m.index[0]),
        last_archive_utc=str(m.index[-1])
    )),flush=True)
    rows=[]
    baseline_meta=dict(
        name="baseline",algorithm="baseline",lookback_days=0,
        confidence=None,scope="none",flipped_trades=0,
        flipped_2025=0,flipped_2026=0,
        flipped_event=0,flipped_fallback=0,
        January_2025_flipped=0)
    for mode in base.MODES:
        rows.append(dict(**baseline_meta,fee_model=mode,**baseline[mode]))
    prior={}
    selections={}
    for algorithm,lookback in product(ALGORITHMS,DAYS_BACK):
        prediction,amount=train_predict(
            sample_times,X,returns,indices,algorithm,lookback)
        prior[(algorithm,lookback)]=(prediction,amount)
        assert np.all(np.isfinite(prediction)) and len(prediction)==477
        for conf,scope in product(CONFIDENCES,SCOPES):
            valid_scope=(np.ones(N,dtype=bool) if scope=="both" else
                   (mask if scope=="fallback" else ~mask))
            enough_history=(amount>=24)
            sign=np.where(prediction>=0,1,-1).astype(np.int8)
            override=valid_scope&enough_history&(np.abs(prediction)>=conf)
            side=np.where(override,sign,baseline_side).astype(np.int8)
            changed=side!=baseline_side
            raw,choices,res=evaluate(long,short,side,mask,ids)
            key=(algorithm,lookback,conf,scope)
            selections[key]=(side,changed,choices)
            attrs=dict(
                name=f"{algorithm}__{lookback}d__conf{conf}__{scope}",
                algorithm=algorithm,lookback_days=lookback,
                confidence=conf,scope=scope,
                flipped_trades=int(changed.sum()),
                flipped_2025=int(changed[:TRAIN].sum()),
                flipped_2026=int(changed[TRAIN:].sum()),
                flipped_event=int(np.sum(changed&(~mask))),
                flipped_fallback=int(np.sum(changed&mask)),
                January_2025_flipped=int(np.sum(changed&(MONTHS=="2025-01")))
            )
            for mode in base.MODES:
                rows.append(dict(**attrs,fee_model=mode,**res[mode]))
        print("STEP23_WINDOW_TRAINED "+json.dumps(dict(
            algorithm=algorithm,lookback_days=lookback,
            samples_in_first_Jan2_entry=int(amount[0]),
            first_Jan2_model_score=float(prediction[0]),
            scenarios_completed=len(selections))),flush=True)

    df=pd.DataFrame(rows)
    if len(df)!=110 or not df.trades.eq(477).all():
        raise AssertionError("Missing 477 weekday trade in 54 scenarios")
    df.to_csv(OUT/"all_54_intraday_classifier_models_two_fee_schedules.csv",index=False)
    print("STEP23_GRID "+json.dumps(dict(
        models=55,fee_scenarios=110,
        mandatory_weekday_trades_each=477,year2025_days=260,
        last_2026_complete_month="2026-10")),flush=True)

    offer=df[df.fee_model=="scalper_offer"]
    qualified=offer[(offer.algorithm!="baseline")&
        (offer.win_months_2025>=12)&
        (offer.return_2025_pct>=bench["return_2025_pct"]-1.e-6)&
        (offer.profitable_days_2025>=bench["profitable_days_2025"])&
        (offer.max_dd_2025<=bench["max_dd_2025"]+1.e-4)]
    if len(qualified):
        selected=qualified.sort_values([
            "win_months_2025","return_2025_pct",
            "profitable_days_2025","max_dd_2025"],
            ascending=[False,False,False,True]).iloc[0].to_dict()
        key=(selected["algorithm"],
             int(selected["lookback_days"]),
             float(selected["confidence"]),selected["scope"])
        side,changed,choice=selections[key]
        score,training_n=prior[(key[0],key[1])]
    else:
        selected=offer[offer.algorithm=="baseline"].iloc[0].to_dict()
        side=baseline_side
        changed=np.zeros(N,dtype=bool)
        choice=dec0
        score=np.zeros(N,dtype=float)
        training_n=np.zeros(N,dtype=int)
    raw,decision,scored=evaluate(long,short,side,mask,ids)
    details={}
    for mi,mode in enumerate(base.MODES):
        path=step15.getout(raw,decision[0],mi)
        days,month=prev.monthly_ledger(
            path,side,decision,indices,hours,mask,
            mode,selected["name"],changed,training_n,score)
        days.to_csv(OUT/(mode+"_2025_selected_477_daily.csv"),index=False)
        month.to_csv(OUT/(mode+"_2025_selected_22_months.csv"),index=False)
        z=step15.score(path)
        details[mode]=dict(
            performance=z,
            positive_months=int(np.sum(month.monthly_net_compounded_pct>0)),
            negative_months=month.loc[month.monthly_net_compounded_pct<=0,
                ["month_ist","monthly_net_compounded_pct"]].to_dict("records"),
            change_vs_baseline_months=z["win_months_all"]-baseline[mode]["win_months_all"],
            change_vs_baseline_return_pct=round(
                z["net_total_pct"]-baseline[mode]["net_total_pct"],6),
            change_vs_baseline_drawdown_pct=round(
                z["max_closed_dd_pct"]-baseline[mode]["max_closed_dd_pct"],6),
            actual_direction_flips=int(changed.sum()),
            January_2025_direction_flips=int(np.sum(changed&(MONTHS=="2025-01"))))
        print("STEP23_SELECTED_"+mode.upper()+" "+
              json.dumps(details[mode],sort_keys=True),flush=True)
    retrospective_22=offer[offer.win_months_all==22].sort_values(
        ["net_total_pct","max_closed_dd_pct"],ascending=[False,True])
    retrospective_22.to_csv(OUT/"hindsight_only_22_profitable_months.csv",index=False)
    report=dict(
      task="30m minute-labeled supervised BTC futures directional learning to avoid daily model January cold start",
      training="Every 30m sampled completed price label available before actual entry, fit 1/3/7 past calendar days only",
      all_477_weekday_full_notional_positions=True,
      selected_only_using_2025=selected,
      eligible_training_2025_candidates=int(len(qualified)),
      benchmark=baseline,
      evaluated_2026_historical_recheck=details,
      hindsight_full_22_month_positive_candidates=int(len(retrospective_22)),
      hindsight_22_month_best_NOT_SELECTED=(
           retrospective_22.iloc[0].to_dict() if len(retrospective_22) else None),
      exact_cost_assumptions="1× account notional; taker 0.05% each side + GST18%; hypothetical regular Scalper Offer preactivated eligible <=30m zero close fee; 5 BTC quote points slippage per side",
      cautions=[
        "History Jan2025-Oct2026 repeatedly mined, NOT independent held-out test",
        "Minute-level past labels are price direction 30m ahead, not actual exchange fill-quality",
        "Real historical Scalper opt-in/eligibility unknown; normal fees make baseline net negative",
        "Funding, actual bid-ask orderbook, latency, tick-intraminute stop sequences and liquidation excluded",
        "22/22 backtested profitable months cannot guarantee future profitable months"]
    )
    (OUT/"summary.json").write_text(json.dumps(
        report,indent=2,default=lambda x:x.item() if isinstance(x,np.generic) else str(x))+"\n")
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join([
      "# Step23 — BTC minute-trained 30m direction predictor, all weekday trades",
      "",
      "One full-size BTCUSD 1× notional futures position every 477 IST Mon–Fri days at the ORIGINAL 18/19/20/21 IST schedule. A logistic or Ridge classifier learns from 30m minute-label price moves completely settled BEFORE each actual daily position. Jan2 has price training history from Jan1, unlike the previous daily-only classifier.",
      "",
      "## Frozen original per-trade parity",json.dumps(baseline,indent=2),
      "",
      "## Policy selected using 2025 only",json.dumps(selected,indent=2),
      "",
      "## 2026 research-exposed check",json.dumps(details,indent=2),
      "",
      "## Selected full 22 calendar month results",
      pd.read_csv(OUT/"scalper_offer_2025_selected_22_months.csv").to_markdown(index=False),
      "",
      "## Full history 22/22 hindsight-only scenarios",str(len(retrospective_22)),
      "",
      "## Caveats",
      "Model trained only using past completed candles, but years 2025–2026 and fee assumptions have been explored extensively. Previous monthly profits cannot independently validate live performance. Scalper fee waiver not historically proven; real spread, funding, latency and orderbook unknown."
    ])+"\n")
    print("STEP23_COMPLETE "+json.dumps(dict(
        model_count=55,qualified_2025=len(qualified),
        hindsight_22=int(len(retrospective_22)),selected=selected["name"],
        offer=details["scalper_offer"]["performance"],
        standard=details["standard"]["performance"]
    ),sort_keys=True),flush=True)

if __name__=="__main__":
    main()
