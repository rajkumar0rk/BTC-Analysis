#!/usr/bin/env python3
"""Path-aware profitable event selection after CONFIRMED 1H events: monthly causal meta-label,
native-1M stop-first trade replay; compares filtered vs all confirmed events.

Not a universal UP/DOWN oracle. Target = real modeled after-cost profitable
stop-first exit on the future native-1M path, learned only after exit completion.
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import accuracy_score, balanced_accuracy_score, roc_auc_score, brier_score_loss, log_loss

import research_btc_regime_attribution_20261121 as base
import research_btc_directional_diagnosis_20261121 as previous

OUT=Path("analysis/btc_path_aware_direction_20261121")
OUT.mkdir(parents=True,exist_ok=True)
MONTHS=[str(x) for x in pd.period_range("2025-01","2026-10",freq="M")]
EVAL_MONTHS=MONTHS[6:]
THRESHOLD=.50

def start_of_month(month):
    return pd.Timestamp(month+"-01",tz="Asia/Kolkata").tz_convert("UTC")

def causal_events(h):
    """Event price actions are defined from completed 1H + prior 24 hours."""
    n=len(h)
    event=np.full(n,"none",dtype=object)
    side=np.zeros(n,dtype=np.int8)
    above=(h.close>h.hi24).to_numpy(bool)
    below=(h.close<h.lo24).to_numpy(bool)
    both=above & below
    if np.any(both): raise RuntimeError("Both prior channel breaks on one close")
    side[above]=1;side[below]=-1
    event[above|below]="breakout"

    sweep_up=((h.high>h.hi24)&(h.close<h.hi24)).to_numpy(bool)
    sweep_dn=((h.low<h.lo24)&(h.close>h.lo24)).to_numpy(bool)
    # In a two-sided sweep, both sides are ambiguous; skip until next setup.
    sweeps=~(sweep_up & sweep_dn) & (side==0)
    short=sweeps & sweep_up
    long=sweeps & sweep_dn
    side[short]=-1;side[long]=1
    event[short|long]="failed_sweep"

    atr=h.atr.to_numpy(float)
    bar=(h.close-h.open).to_numpy(float)
    width=(h.high-h.low).to_numpy(float)
    dist_from_low=(h.close-h.low).to_numpy(float)
    distance_low_ratio=np.divide(dist_from_low,width,out=np.zeros(n),where=width>0)
    bullish=(bar>=.75*atr)&(distance_low_ratio>=.8)&(h.er12.to_numpy(float)>=.25)
    bearish=(-bar>=.75*atr)&(distance_low_ratio<=.2)&(h.er12.to_numpy(float)>=.25)
    long=(side==0)&bullish
    short=(side==0)&bearish
    side[long]=1;side[short]=-1
    event[long|short]="displacement"
    good=(h.valid.to_numpy(bool)&np.isfinite(atr)&(atr>0))
    side[~good]=0
    event[~good]="none"
    if np.any((side==0)&(event!="none")) or np.any((side!=0)&(event=="none")):
        raise RuntimeError("Invalid event/side mapping")
    return side,event

def inputs(h,side,event):
    f, valid, *_ = previous.prepare(h)
    if not f.index.equals(h.index):raise RuntimeError("Mismatched hourly indexes")
    f["event_side"]=side.astype(float)
    f["ema_spread_in_direction"]=f["ema_spread_atr"]*side
    f["last4h_momentum_in_direction"]=f["return_4h_atr"]*side
    f["current_body_in_direction"]=f["bar_body_atr"]*side
    f["event_breakout"]=np.asarray(event=="breakout",dtype=float)
    f["event_failed_sweep"]=np.asarray(event=="failed_sweep",dtype=float)
    f["event_displacement"]=np.asarray(event=="displacement",dtype=float)
    good=(valid.to_numpy(bool)&np.isfinite(f.to_numpy(float)).all(axis=1)&(side!=0))
    return f,good

def fit_model(kind,x,y):
    if kind=="logistic":
        model=make_pipeline(StandardScaler(),LogisticRegression(
            C=1.,max_iter=500,solver="lbfgs",random_state=0))
    else:
        model=HistGradientBoostingClassifier(
            learning_rate=.04,max_iter=100,max_leaf_nodes=9,min_samples_leaf=100,
            l2_regularization=5,max_bins=63,early_stopping=False,random_state=0)
    model.fit(x,y)
    return model


def native_1m_trade_outcomes(one,h,side):
    """An independent hypothetical trade for EVERY signal event (not a portfolio).

    Label is first-native-1M path outcome net of modeled fees and adverse slip;
    label becomes known only once the exit minute is completed. Actual portfolio
    execution is still separately replayed with global exclusive-position rules.
    """
    idx=one.index
    opens=one.open.to_numpy(float)
    highs=one.high.to_numpy(float)
    lows=one.low.to_numpy(float)
    closes=one.close.to_numpy(float)
    n=len(h)
    netr=np.full(n,np.nan)
    release=np.full(n,pd.NaT,dtype=object)
    evidence=[]
    for j in np.flatnonzero(side):
        entry=h.index[j]+pd.Timedelta(hours=1)
        month=entry.tz_convert("Asia/Kolkata").strftime("%Y-%m")
        if month>"2026-10":
            continue
        at=int(idx.searchsorted(entry))
        if at>=len(idx) or idx[at]!=entry:
            raise RuntimeError("Native 1M gap at setup entry")
        atr=float(h.atr.iat[j])
        if not np.isfinite(atr) or atr<=0:
            continue
        maxidx=min(at+12*60,len(idx),int(idx.searchsorted(base.next_month_utc(entry))))
        if maxidx<=at:
            continue
        sr=int(side[j])
        raw_entry=float(opens[at])
        stoppts=1.25*atr
        stop=raw_entry-sr*stoppts
        target=raw_entry+sr*(2*stoppts)
        hh=highs[at:maxidx]
        ll=lows[at:maxidx]
        bad=np.flatnonzero(ll<=stop if sr>0 else hh>=stop)
        good=np.flatnonzero(hh>=target if sr>0 else ll<=target)
        b=int(bad[0]) if len(bad) else len(hh)
        g=int(good[0]) if len(good) else len(hh)
        if b<=g and b<len(hh):
            k=at+b
            raw_exit=min(stop,opens[k]) if sr>0 else max(stop,opens[k])
            reason="stop"
        elif g<len(hh):
            k=at+g
            raw_exit=target
            reason="target"
        else:
            k=maxidx-1
            raw_exit=closes[k]
            reason="timeout_or_IST_month_end"
        entryfill=raw_entry+sr*base.SLIP
        exitfill=raw_exit-sr*base.SLIP
        fee=base.FEE*(entryfill+exitfill)
        netpts=sr*(exitfill-entryfill)-fee
        netr[j]=netpts/stoppts
        # Data for exit minute [k,k+60) is not known until k+60 seconds.
        release[j]=idx[k]+pd.Timedelta(minutes=1)
        if release[j]<entry:
            raise RuntimeError("A future outcome was released before entry")
        evidence.append(dict(signal_hour=str(h.index[j]),side=sr,
             entry_utc=str(entry),exit_utc=str(idx[k]),release_utc=str(release[j]),
             raw_entry=raw_entry,raw_exit=raw_exit,stop_points=stoppts,
             modeled_fee_price_points=fee,modeled_slippage_price_points=2*base.SLIP,
             net_price_points=netpts,net_R=netr[j],
             outcome_profitable=bool(netr[j]>0),exit_reason=reason))
    pd.DataFrame(evidence).to_csv(OUT/"isolated_event_outcome_training_labels.csv",index=False)
    return netr,pd.DatetimeIndex(release)

def forecast(h,side,events,profits,release):
    f,valid=inputs(h,side,events)
    # Supervised target is actual stop-first outcome from native 1M path,
    # known ONLY after this independent event's exit minute.
    known_future=np.isfinite(profits)
    labels=(profits>0).astype(int)
    released=release
    entry=h.index+pd.Timedelta(hours=1)
    entry_month=entry.tz_convert("Asia/Kolkata").strftime("%Y-%m")
    predictions=[]
    training=[]
    allowed=np.zeros(len(h),dtype=np.int8)
    eligible=np.zeros(len(h),dtype=np.int8)
    for month in EVAL_MONTHS:
        begin=start_of_month(month)
        fit=np.flatnonzero(valid & known_future & (released<=begin))
        test=np.flatnonzero(valid & (entry_month==month))
        if len(fit)<400:
            raise RuntimeError("Insufficient event history for "+month+": "+str(len(fit)))
        if len(test)<25:
            raise RuntimeError("Insufficient event candidates in "+month+": "+str(len(test)))
        if not np.all(released[fit]<=begin):
            raise RuntimeError("Leaked future label to training")
        xtrain=f.iloc[fit].to_numpy(float)
        ytrain=labels[fit]
        if len(np.unique(ytrain))!=2:
            raise RuntimeError("Only one outcome class in training")
        xtest=f.iloc[test].to_numpy(float)
        p={}
        for name in ["logistic","boosted"]:
            model=fit_model(name,xtrain,ytrain)
            probs=model.predict_proba(xtest)
            if probs.shape[1]!=2:raise RuntimeError("Broken probability mapping")
            p[name]=probs[:,1]
        prior=float(ytrain.mean())
        for ix,j in enumerate(test):
            prob=float(p["boosted"][ix])
            eligible[j]=side[j]
            if prob>=THRESHOLD: allowed[j]=side[j]
            predictions.append(dict(month_ist=month,year=month[:4],
                 signal_utc=str(h.index[j]),entry_utc=str(entry[j]),
                 bar_number=j,nonoverlap4h=bool(j%4==0),
                 family=events[j],side=int(side[j]),
                 realized_net_profitable=int(labels[j]) if known_future[j] else None,
                 simulated_trade_net_R=float(profits[j]) if known_future[j] else None,
                 probability_boosted=prob,probability_logistic=float(p["logistic"][ix]),
                 trained_prior_event_success=prior,
                 meta_accepted=bool(prob>=THRESHOLD)))
        training.append(dict(month_ist=month,training_completed_labels=len(fit),
                   training_last_released_utc=str(released[fit].max()),
                   month_open_utc=str(begin),heldout_events=len(test),
                   training_positive_fraction=round(prior,5),
                   accepted_events=int((p["boosted"]>=THRESHOLD).sum())))
    r=pd.DataFrame(predictions)
    r.to_csv(OUT/"event_direction_predictions.csv",index=False)
    audit=pd.DataFrame(training)
    audit.to_csv(OUT/"monthly_training_audit.csv",index=False)
    return r,audit,allowed,eligible

def evaluate(pred):
    r=pred[pred.nonoverlap4h & pred.realized_net_profitable.notna()]
    rows=[]
    for period in ("2025H2","2026JanOct","combined"):
        g=(r if period=="combined" else r[r.year==("2025" if period=="2025H2" else "2026")])
        if len(g)<65:raise RuntimeError("Too few directional event tests")
        y=g.realized_net_profitable.to_numpy(int)
        for name,field in [("boosted","probability_boosted"),
                           ("logistic","probability_logistic"),
                           ("trained_event_prior","trained_prior_event_success")]:
            p=g[field].to_numpy(float)
            mask=p>=THRESHOLD
            rows.append(dict(period=period,model=name,events=len(y),
                actual_net_win_rate_pct=round(100*y.mean(),3),
                model_accuracy_pct=round(100*accuracy_score(y,p>=.5),3),
                model_balanced_accuracy_pct=round(100*balanced_accuracy_score(y,p>=.5),3),
                direction_auc=round(float(roc_auc_score(y,p)),4) if len(np.unique(y))==2 else None,
                brier_score=round(float(brier_score_loss(y,p)),5),
                forecast_logloss=round(float(log_loss(y,np.clip(p,1e-8,1-1e-8))),5),
                acceptance_events=int(mask.sum()),
                acceptance_coverage_pct=round(100*mask.mean(),2),
                accepted_isolated_net_win_pct=round(100*y[mask].mean(),3) if mask.any() else None))
        rows.append(dict(period=period,model="always_follow_confirmed_event",
                         events=len(y),actual_net_win_rate_pct=round(100*y.mean(),3),
                         model_accuracy_pct=round(100*y.mean(),3),
                         acceptance_events=len(y),acceptance_coverage_pct=100,
                         accepted_isolated_net_win_pct=round(100*y.mean(),3)))
    out=pd.DataFrame(rows)
    out.to_csv(OUT/"conditional_direction_score.csv",index=False)
    group=r.groupby(["year","family"]).agg(
        events=("realized_net_profitable","size"),
        event_net_win_rate_pct=("realized_net_profitable",lambda x:round(100*x.mean(),3)),
        accepted=("meta_accepted","sum"),
    ).reset_index()
    group.to_csv(OUT/"family_direction_by_year.csv",index=False)
    calibration=[]
    for model,field in [("boosted","probability_boosted"),("logistic","probability_logistic")]:
        for lo,hi in [(0,.4),(.4,.5),(.5,.6),(.6,.7),(.7,1.00001)]:
            g=r[r[field].between(lo,hi,inclusive="left")]
            calibration.append(dict(model=model,p_low=lo,p_high=min(1,hi),
                samples=len(g),mean_probability=round(float(g[field].mean()),3) if len(g) else None,
                actual_continuation_pct=round(float(100*g.realized_net_profitable.mean()),2) if len(g) else None))
    pd.DataFrame(calibration).to_csv(OUT/"probability_calibration.csv",index=False)
    return out

def monthly_results(tr,model):
    eq=base.INITIAL
    rows=[]
    for mo in MONTHS:
        g=tr[tr.month_ist==mo] if len(tr) else tr
        pnl=float(g.pnl_usd.sum()) if len(g) else 0
        ret=100*pnl/eq
        eq+=pnl
        rows.append(dict(model=model,month_ist=mo,trades=len(g),
            wins=int((g.pnl_usd>0).sum()) if len(g) else 0,
            losses=int((g.pnl_usd<0).sum()) if len(g) else 0,
            net_pnl_usd=round(pnl,2),net_account_pct=round(ret,5),
            month_end_equity_usd=round(eq,4),
            total_fees_gst_usd=round(float(g.fee_gst_usd.sum()),2) if len(g) else 0,
            total_slippage_usd=round(float(g.slippage_usd.sum()),2) if len(g) else 0,
            status="Profit" if pnl>1e-9 else "Loss" if pnl < -1e-9 else "No trade"))
    if len(tr) and abs(eq-float(tr.equity_usd.iloc[-1]))>.001:
        raise RuntimeError("Account did not reconcile")
    return pd.DataFrame(rows)

def replay(one,h,signals):
    base.SPECS.update(dict(event_baseline=(1.25,2.,12),conditional_meta=(1.25,2.,12)))
    try:
        trades=base.run(one,h,signals)
    finally:
        del base.SPECS["event_baseline"]
        del base.SPECS["conditional_meta"]
    if len(trades):
        for name in signals:
            g=trades[trades.strategy==name].copy()
            if len(g)>1:
                a=pd.to_datetime(g.entry_utc,utc=True)
                b=pd.to_datetime(g.exit_utc,utc=True)
                if not (a.iloc[1:].to_numpy()>b.iloc[:-1].to_numpy()).all():
                    raise RuntimeError("Same-account overlapping positions")
            g.to_csv(OUT/(name+"_trade_ledger.csv"),index=False)
    return trades

def main():
    one,manifest=base.load()
    if len(one)!=992160:raise RuntimeError("Source native 1M archive changed")
    h=base.features(one)
    side,event=causal_events(h)
    profits,release=native_1m_trade_outcomes(one,h,side)
    probs,train,approved,candidate=forecast(h,side,event,profits,release)
    stats=evaluate(probs)
    if not np.all(approved[approved!=0]==candidate[approved!=0]):
        raise RuntimeError("Meta confirmation contradicted base event direction")
    trades=replay(one,h,dict(event_baseline=candidate,conditional_meta=approved))
    months=[]
    summaries=[]
    for model in ("event_baseline","conditional_meta"):
        g=trades[trades.strategy==model].copy()
        mr=monthly_results(g,model)
        months.append(mr)
        gains=float(g.loc[g.pnl_usd>0,"pnl_usd"].sum())
        losses=-float(g.loc[g.pnl_usd<0,"pnl_usd"].sum())
        equity=np.r_[base.INITIAL,g.equity_usd.to_numpy(float)]
        summary=dict(model=model,events_candidate=len(probs),
            trades=int(len(g)),wins=int((g.pnl_usd>0).sum()),
            win_rate_pct=round(float(100*(g.pnl_usd>0).mean()),2) if len(g) else 0.,
            profit_factor=round(gains/losses,4) if losses>0 else None,
            net_return_pct=round(float(100*(equity[-1]/base.INITIAL-1)),4),
            net_usd=round(float(equity[-1]-base.INITIAL),2),
            max_trade_close_drawdown_pct=round(float(100*(1-equity/np.maximum.accumulate(equity)).max()),3),
            fees_gst_usd=round(float(g.fee_gst_usd.sum()),2),
            slippage_usd=round(float(g.slippage_usd.sum()),2),
            profitable_months=int((mr.net_pnl_usd>0).sum()),
            losing_months=int((mr.net_pnl_usd<0).sum()),
            idle_months=int((mr.net_pnl_usd==0).sum()),
            is_22_of_22=bool((mr.net_pnl_usd>0).all()))
        summaries.append(summary)
    md=pd.concat(months,ignore_index=True)
    md.to_csv(OUT/"monthly_account_comparison.csv",index=False)
    pd.DataFrame(summaries).to_csv(OUT/"account_comparison.csv",index=False)
    quality=dict(source="Delta India BTCUSD futures, original SHA256 verified 1M candles",
                 native_minutes=len(one),source_partitions=len(manifest["partitions"]),
                 evaluated_complete_months=16,total_complete_ist_months=22,
                 training_months=6,model_threshold=THRESHOLD,
                 label_horizon="native 1M stop-first event exit and net-after-fee R, released after exit minute",
                 event_family_order=["24h_breakout","24h_failed_sweep","displacement"],
                 all_models_fitted_before_evaluation_month=True,
                 next_1m_open_no_lookahead=True,
                 stops_first_on_1m_both_touch=True,
                 real_orderbook_spread_available=False,
                 realized_funding_included=False,
                 exchange_contract_margin_accurate=False,
                 blind_holdout_2026=False)
    (OUT/"quality.json").write_text(json.dumps(quality,indent=2)+"\n")
    report=[
        "# BTC event-conditioned direction meta-forecast and 1M trade replay",
        "",
        "## Audit and hypothesis",
        "Prior unconditional 4H UP/DOWN predictor was no better than chance in 2026; event-conditional future-close direction showed a 58.33% hit rate on accepted evaluation events but still lost 27.32% after costs. This study fixes the **target mismatch**: past-only monthly classifier predicts whether a confirmed event side would have produced positive net R under conservative 1M stop-first fills, including fee/GST/slippage. Each hypothetical label is released ONLY after the exit minute is finished, never before monthly training cutoff. This is a precommitted differential, not an optimized TP/SL search.",
        "",
        "## Data integrity", "~~~json",json.dumps(quality,indent=2),"~~~","",
        "## Path-aware profitable exit prediction, event signals sampled nonoverlapping each 4 UTC hours",
        stats.to_markdown(index=False),"",
        "## Independently replayed account comparison (same 1M fills, global one position per account)",
        pd.DataFrame(summaries).to_markdown(index=False),"",
        "## Net returns for all 22 calendar months (including six first training idle)",
        md.pivot(index="month_ist",columns="model",values="net_account_pct").round(3).to_markdown(),"",
        "## Important limitations",
        "- Model observes only past hourly OHLCV indicators and the completed 1H setup, never the forward native 1M path or trade result. Training excludes events until their entire hypothetical exit is completed.",
        "- Isolated-event net-win probability is NOT the same as single-account portfolio win rate; blocked overlapping entries change the executed sample. Both are independently reported.",
        "- The all-event benchmark uses the same exclusive 1M execution and Jan-Jun 2025 initial idle period.",
        "- Historical 2025-2026 research has been explored; chronological monthly validation is not pristine untouched external holdout.",
        "- Excluded funding cash flows, real spreads/orderbook, liquidation, latency and contract rounding. Assumed taker .05% per side + GST 18%, $5 adverse price-point slip per leg.",
        "- No live trading or guarantees. A failed model must not be promoted or described as reliable by selecting only its best-looking historical month.",
    ]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")
    print("META_DIRECTION_SCORES")
    print(stats.to_string(index=False))
    print("ACCOUNT_COMPARISON")
    print(pd.DataFrame(summaries).to_string(index=False))
    print("MONTHLY_ACCOUNT")
    print(md.pivot(index="month_ist",columns="model",values="net_account_pct").round(3).to_string())
    print("COMPLETE")

if __name__=="__main__":
    main()
