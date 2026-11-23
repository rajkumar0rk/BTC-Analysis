#!/usr/bin/env python3
"""Step22: walk-forward supervised LONG/SHORT model for every BTC weekday.

Strictly prior completed same-entry-type weekdays provide shadow LONG/SHORT
30m net-exit labels. Every prediction uses historical preentry OHLCV only;
actual exit uses frozen Step15 B month-equity policy. 477 nonzero full-size
trades per candidate, unchanged entry times, standard+Scalper fee sensitivity.
2026 previously researched: NOT blind independent holdout.
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
import audit_btc_daily_risk_crosscheck_step20 as step20

OUT=Path("analysis/btc_daily_supervised_side_step22")
N=len(base.DAYS)
TRAIN=base.NTRAIN
MONTHS=np.asarray(base.MONTH_LABELS)
ALGORITHMS=("ridge","logistic")
WINDOWS=(60,120,240)
FEATURE_SETS=("basic","context")
CONFIDENCES=(.10,.20,.30)
SCOPES=("event","fallback","both")
assert N==477 and TRAIN==260
assert len(ALGORITHMS)*len(WINDOWS)*len(FEATURE_SETS)*len(CONFIDENCES)*len(SCOPES)==108

def features_at_entry(m,idx):
    o=m.open.to_numpy(float)
    h=m.high.to_numpy(float)
    l=m.low.to_numpy(float)
    c=m.close.to_numpy(float)
    v=m.volume.to_numpy(float)
    X=np.zeros((N,10),dtype=np.float64)
    for d,k in enumerate(idx):
        i=int(k)
        if i<300:raise AssertionError("Incomplete prior 240m preentry history")
        close=float(c[i-1])
        ret5=close/float(o[i-5])-1.
        ret15=close/float(o[i-15])-1.
        ret60=close/float(o[i-60])-1.
        ret240=close/float(o[i-240])-1.
        volume_prev=v[i-105:i-5].reshape(20,5).sum(axis=1)
        mean=float(volume_prev.mean())
        relvol=float(v[i-5:i].sum()/mean) if mean>0 else 1.
        hi60=float(np.max(h[i-60:i]))
        lo60=float(np.min(l[i-60:i]))
        range60=(hi60-lo60)/float(o[i])
        pos60=(close-lo60)/(hi60-lo60) if hi60>lo60 else .5
        ma20=float(np.mean(c[i-20:i]))
        ma60=float(np.mean(c[i-60:i]))
        ma_gap=ma20/ma60-1.
        past_close=c[i-15:i]
        increments=np.diff(past_close)
        gains=float(np.maximum(increments,0).mean())
        losses=float(np.maximum(-increments,0).mean())
        rsi=(gains/(gains+losses) if gains+losses>0 else .5)
        hi15=float(np.max(h[i-15:i]))
        lo15=float(np.min(l[i-15:i]))
        range15=(hi15-lo15)/float(o[i])
        X[d,:]=(
            ret5/.0015,ret15/.003,ret60/.007,ret240/.015,
            relvol-1.,range60/.01,(pos60-.5)*2,
            ma_gap/.002,(rsi-.5)*2,range15/.004
        )
    if not np.isfinite(X).all():
        raise AssertionError("Model preentry feature invalid")
    return np.clip(X,-5.,5.)

def model_features(X,feature_set):
    if feature_set=="basic":
        return X[:,[0,1,2,3,4,6]]
    if feature_set=="context":
        return X
    raise KeyError(feature_set)

def shadow_predictions(X,pnl_long,pnl_short,mask,algo,window,feature_set):
    """At day d fit with <d earlier COMPLETE same-type shadow outcomes."""
    data=model_features(X,feature_set)
    advantage=(np.asarray(pnl_long)-np.asarray(pnl_short))*10000. # basis points
    targets=(advantage>0).astype(np.int8)
    scores=np.zeros(N,dtype=float)
    training_count=np.zeros(N,dtype=np.int16)
    for d in range(N):
        pool=np.flatnonzero(mask[:d]==mask[d])[-window:]
        training_count[d]=len(pool)
        if len(pool)<40:
            continue
        if np.max(pool)>=d:raise AssertionError("Current/future day train leakage")
        xs=data[pool]
        yn=advantage[pool]
        scaler=StandardScaler()
        xs_norm=scaler.fit_transform(xs)
        target=scaler.transform(data[d:d+1])
        if algo=="ridge":
            mod=Ridge(alpha=10.)
            mod.fit(xs_norm,yn)
            predicted=float(mod.predict(target)[0])
            spread=float(np.std(yn))
            scores[d]=np.clip(predicted/max(spread,1.e-8),-1.,1.)
        elif algo=="logistic":
            y=targets[pool]
            if len(np.unique(y))<2:
                scores[d]=float(1 if y[0]==1 else -1)
            else:
                mod=LogisticRegression(C=.25,solver="liblinear",
                                       max_iter=200,random_state=17)
                mod.fit(xs_norm,y)
                scores[d]=float(np.clip(2*mod.predict_proba(target)[0,1]-1,-1,1))
        else:
            raise KeyError(algo)
    return scores,training_count

def choose_sides(original,scores,train_n,mask,confidence,scope):
    scope_mask=np.ones(N,dtype=bool) if scope=="both" else (
        mask.copy() if scope=="fallback" else ~mask
    )
    confidence_gate=(np.abs(scores)>=confidence)&(train_n>=40)&scope_mask
    proposal=np.where(scores>=0,1,-1).astype(np.int8)
    side=np.where(confidence_gate,proposal,original).astype(np.int8)
    if not np.all(np.abs(side)==1):
        raise AssertionError("Zero-size/missing daily direction")
    return side,confidence_gate&(side!=original)

def scored_path(long,short,side,mask,policies,ids):
    raw=step17.select_sign_arrays(long,short,side)
    selection=step15.replay_one(
        raw,mask,ids["profit_close_at_0.1pct_after_20m"],
        step20.PARAMS["B"],ids)
    stats={}
    for mi,mode in enumerate(base.MODES):
        path=step15.getout(raw,selection[0],mi)
        stats[mode]=step15.score(path)
    return raw,selection,stats

def monthly_ledger(path,side,choice,idx,hour,mask,fee,model,changed,train_n,scores):
    p,fees,gross,reason,hold=path
    df=pd.DataFrame(dict(
        date_ist=base.IST_DAYS,month_ist=MONTHS,year=np.asarray(base.DAYS.year),
        entry_hour_ist=hour,
        entry_type=np.where(mask,"MANDATORY_FALLBACK","VOLUME_SIGNAL"),
        chosen_side=np.where(side>0,"LONG","SHORT"),
        side_changed_from_original=changed,
        historical_training_cases=train_n,
        preentry_supervised_signed_score=scores,
        frozen_exit_choice=choice[0],
        prior_month_net_pct=choice[1]*100.,
        prior_peak_giveback_pct=choice[2]*100.,
        compounded_account_daily_net_pct=p*100.,
        gross_btc_quote_price_points=gross,
        modeled_fee_gst_btc_quote_points=fees,
        adverse_slippage_points=2*base.SLIP,
        exit_reason=np.where(reason==1,"TAKE_PROFIT",
                np.where(reason==2,"PROTECTIVE_STOP",
                np.where(reason==3,"TIMEOUT","NEXT_OPEN_EARLY_EXIT"))),
        hold_minutes=hold,
        model=model,fee_model=fee
    ))
    if len(df)!=477 or df.date_ist.nunique()!=477 or (
          pd.to_datetime(df.date_ist).dt.dayofweek>=5).any():
        raise AssertionError("One trade each IST weekday violated")
    month=df.groupby("month_ist",sort=True).agg(
        trading_days=("date_ist","size"),
        positive_days=("compounded_account_daily_net_pct",lambda x:int(np.sum(x>0))),
        negative_days=("compounded_account_daily_net_pct",lambda x:int(np.sum(x<0))),
        monthly_net_compounded_pct=("compounded_account_daily_net_pct",
          lambda x:float(100*(np.prod(1+x.to_numpy()/100)-1))),
        direction_changes=("side_changed_from_original","sum"),
        modeled_fees_gst_points=("modeled_fee_gst_btc_quote_points","sum")
    ).reset_index()
    if len(month)!=22 or month.trading_days.sum()!=477:
        raise AssertionError("Missing monthly entries")
    return df,month

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    m,ctx,mask,fb,original_side,hours,indices,base_cfg=step13.create_path()
    policies,labels=early.build_exit_policies()
    ids={name:i for i,name in enumerate(labels)}
    ctxfeature=step20.prev.preentry_features(m,indices,original_side)
    # For direction-changing candidates each direction's STOP cap depends on
    # that CURRENT hypothetical side; don't wrongly reuse original-side risk.
    raw_direction={}
    for sign in (1,-1):
        cand_sides=np.full(N,sign,dtype=np.int8)
        cfg,meta,narrowed=step20.build_capped(
            base_cfg,ctxfeature,cand_sides,mask,("with60","counter5"))
        raw_direction[sign]=early.replay_with_nextbar_exits(
            m.open.to_numpy(float),m.high.to_numpy(float),
            m.low.to_numpy(float),m.close.to_numpy(float),
            indices,cand_sides,cfg,policies,base.COST,base.SLIP)
    long=raw_direction[1]
    short=raw_direction[-1]
    original_raw,original_selection,baseline=scored_path(
        long,short,original_side,mask,policies,ids)
    # Exact regression against already verified full 477 1m executions.
    b=baseline["scalper_offer"]
    if (b["trades"]!=477 or b["win_months_all"]!=21 or
        abs(b["net_total_pct"]-25.423847)>.00011 or
        abs(b["max_closed_dd_pct"]-2.617670)>.00011 or
        b["profitable_days"]!=292):
        raise AssertionError("Step20 B frozen baseline mismatch: "+str(b))
    std=baseline["standard"]
    if abs(std["net_total_pct"]+5.332682)>.00011:
        raise AssertionError("Frozen standard fee baseline mismatch")
    print("STEP22_BASELINE_VERIFIED "+json.dumps(baseline,sort_keys=True),flush=True)
    X=features_at_entry(m,indices)
    # Shadow labels reveal PREVIOUS hypothetical 1m returns of both directions;
    # never the current/future day's outcomes in the current predictor's fit.
    long_shadow=long[0][:,0,1]
    short_shadow=short[0][:,0,1]
    assert len(long_shadow)==477 and len(short_shadow)==477
    baseline_ref={
      "model":"baseline","algorithm":"baseline",
      "window":0,"feature_set":"none","confidence":None,
      "scope":"none","changed_trading_days":0,
      "changed_2025_days":0,"changed_2026_days":0,
      "changed_events":0,"changed_fallbacks":0
    }
    records=[]
    choices={}
    for mi,fee in enumerate(base.MODES):
        records.append(dict(**baseline_ref,cost_model=fee,
                            **baseline[fee]))
    pred_cache={}
    for algo,window,feature_set in product(
            ALGORITHMS,WINDOWS,FEATURE_SETS):
        score,train_n=shadow_predictions(
            X,long_shadow,short_shadow,mask,algo,window,feature_set)
        pred_cache[(algo,window,feature_set)]=(score,train_n)
        assert len(score)==477 and np.isfinite(score).all()
        for confidence,scope in product(CONFIDENCES,SCOPES):
            chosen_sides,different=choose_sides(
                original_side,score,train_n,mask,confidence,scope)
            raw,dec,stats=scored_path(long,short,chosen_sides,mask,policies,ids)
            key=(algo,window,feature_set,confidence,scope)
            choices[key]=dict(
                side=chosen_sides,different=different,
                selection=dec,score=score,training_count=train_n)
            metadata=dict(
                model="__".join(map(str,key)),
                algorithm=algo,window=window,feature_set=feature_set,
                confidence=confidence,scope=scope,
                changed_trading_days=int(different.sum()),
                changed_2025_days=int(different[:TRAIN].sum()),
                changed_2026_days=int(different[TRAIN:].sum()),
                changed_events=int(np.sum(different&(~mask))),
                changed_fallbacks=int(np.sum(different&mask)))
            for mi,fee in enumerate(base.MODES):
                records.append(dict(**metadata,cost_model=fee,
                                    **stats[fee]))
        print("STEP22_PREDICTIONS "+json.dumps(dict(
            algorithm=algo,training_days=window,
            feature_set=feature_set,
            trained_on_2025_trades=int(np.sum(train_n[:TRAIN]>=40)),
            trained_on_2026_trades=int(np.sum(train_n[TRAIN:]>=40)),
            completed_scenarios=len(choices))),flush=True)
    grid=pd.DataFrame(records)
    if len(grid)!=218 or not grid.trades.eq(477).all():
        raise AssertionError("Failed complete 108+1 weekday model grid")
    grid.to_csv(OUT/"all_108_supervised_direction_models_two_fee_models.csv",index=False)
    print("STEP22_GRID "+json.dumps(dict(
        models=109,fee_scenarios=218,weekdays_each=477,
        previous_data_training_only=True)),flush=True)
    offer=grid[grid.cost_model=="scalper_offer"]
    eligible=offer[(offer.algorithm!="baseline")&
       (offer.win_months_2025>=12)&
       (offer.return_2025_pct>=baseline["scalper_offer"]["return_2025_pct"]-1.e-6)&
       (offer.profitable_days_2025>=baseline["scalper_offer"]["profitable_days_2025"])&
       (offer.max_dd_2025<=baseline["scalper_offer"]["max_dd_2025"]+1.e-4)]
    if len(eligible):
        best=eligible.sort_values([
            "win_months_2025","return_2025_pct",
            "profitable_days_2025","max_dd_2025"],
            ascending=[False,False,False,True]).iloc[0].to_dict()
        key=(best["algorithm"],int(best["window"]),
             best["feature_set"],float(best["confidence"]),best["scope"])
        chosen=choices[key]
        name=best["model"]
    else:
        best=offer[offer.algorithm=="baseline"].iloc[0].to_dict()
        chosen=dict(side=original_side,
             different=np.zeros(N,dtype=bool),
             selection=original_selection,
             score=np.zeros(N),training_count=np.zeros(N,dtype=np.int16))
        name="baseline"
    raw,selection,stats=scored_path(
        long,short,chosen["side"],mask,policies,ids)
    chosen_fee={}
    for mi,fee in enumerate(base.MODES):
        path=step15.getout(raw,selection[0],mi)
        days,month=monthly_ledger(
            path,chosen["side"],selection,indices,hours,mask,
            fee,name,chosen["different"],
            chosen["training_count"],chosen["score"])
        days.to_csv(OUT/(fee+"_2025_selected_477_daily_trades.csv"),index=False)
        month.to_csv(OUT/(fee+"_2025_selected_22_months.csv"),index=False)
        z=step15.score(path)
        chosen_fee[fee]=dict(
           metrics=z,
           profitable_months=int(np.sum(month.monthly_net_compounded_pct>0)),
           losing_months=month.loc[month.monthly_net_compounded_pct<=0,
                 ["month_ist","monthly_net_compounded_pct"]].to_dict("records"),
           month_change_vs_B=z["win_months_all"]-baseline[fee]["win_months_all"],
           net_change_vs_B=round(z["net_total_pct"]-baseline[fee]["net_total_pct"],6),
           dd_change_vs_B=round(z["max_closed_dd_pct"]-baseline[fee]["max_closed_dd_pct"],6),
           changed_daily_directions=int(chosen["different"].sum()))
        print("STEP22_SELECTED_"+fee.upper()+" "+
              json.dumps(chosen_fee[fee],sort_keys=True),flush=True)
    full22=offer[offer.win_months_all==22].sort_values(
        ["net_total_pct","max_closed_dd_pct"],ascending=[False,True])
    full22.to_csv(OUT/"hindsight_22_profitable_months_NOT_SELECTED.csv",index=False)
    research=dict(
        project="Causal supervised BTC direction at all 477 mandatory weekday entries",
        count_models=109,fee_scenarios=218,
        exact_trades=477,frozen_original=baseline,
        eligible_2025_training_models=int(len(eligible)),
        2025_selected_best=best if False else None,
        candidate_selected_by_2025_only=best,
        full_22months_recheck=chosen_fee,
        hindsight_22_profitable_month_variants=int(len(full22)),
        highest_return_22_22_hindsight_NOT_SELECTED=(
            full22.iloc[0].to_dict() if len(full22) else None),
        promotion_as_verified_forward_strategy=False,
        limitations=[
            "2025/2026 heavily mined in prior steps; supervised model on them not independent confirmation",
            "Long/short labels are historical counterfactual exit results, not actual live crossed-spread fills",
            "Historical regular Scalper Offer activation unverified; full standard fee baseline net negative",
            "Funding, real bid/ask, depth, latency, fill chronology and liquidation not modeled"])
    (OUT/"summary.json").write_text(json.dumps(
       research,indent=2,default=lambda v:v.item() if isinstance(v,np.generic) else str(v))+"\n")
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join([
        "# Step22: walk-forward BTC supervised direction, 477 daily trades",
        "",
        "All candidates take exactly one full 1x-notional BTCUSD position every complete IST weekday at frozen Step11 time. At each position, a regularized logistic classifier or Ridge predictor learns the historical price-action-to-direction relationship from ONLY earlier fully settled same-type weekday shadow trade results.",
        "",
        "## Frozen Step20 B baseline parity",
        json.dumps(baseline,indent=2),
        "",
        "## 2025-only selected policy / 2026 research-exposed results",
        json.dumps(best,indent=2),
        json.dumps(chosen_fee,indent=2),
        "",
        "## Full 22 monthly assumed-offer results",
        pd.read_csv(OUT/"scalper_offer_2025_selected_22_months.csv").to_markdown(index=False),
        "",
        "## Hindsight-only 22/22 model count",
        str(len(full22)),
        "",
        "## Caution",
        "Neither 2025 nor 2026 is a pristine independent holdout after extensive strategy searches. Previous shadow direction labels rely on simulated historical 1m returns and assumed fee waiver. Actual order-book spreads and Scalper participation, funding and fill slippage cannot be validated from OHLCV."
    ])+"\n")
    print("STEP22_COMPLETE "+json.dumps(dict(
        models=109,qualified_2025=len(eligible),hindsight_22=len(full22),
        chosen=best["model"],
        chosen_scalper=chosen_fee["scalper_offer"]["metrics"],
        chosen_standard=chosen_fee["standard"]["metrics"]
    ),sort_keys=True),flush=True)

if __name__=="__main__":
    main()
