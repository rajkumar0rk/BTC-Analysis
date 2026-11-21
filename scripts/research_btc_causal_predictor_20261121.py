#!/usr/bin/env python3
"""Chronological 1H-to-next-4H BTCUSD directional outcome forecast and a frozen,
high-confidence 1M execution test. NO in-sample hyperparameter tuning.
"""
import json
from pathlib import Path
from math import pi
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, f1_score, log_loss, confusion_matrix

import research_btc_regime_attribution_20261121 as base

OUT = Path("analysis/btc_causal_predictor_20261121")
OUT.mkdir(parents=True, exist_ok=True)
MONTHS = [str(x) for x in pd.period_range("2025-01", "2026-10", freq="M")]
EVAL_MONTHS = MONTHS[6:]
CATS = ["DOWN", "RANGE", "UP"]
THRESHOLD = 0.55
SEPARATION = 0.15

def month_start_utc(month):
    return pd.Timestamp(month+"-01",tz="Asia/Kolkata").tz_convert("UTC")

def make_features(h):
    atr=h.atr.replace(0,np.nan)
    hi=h.hi24
    lo=h.lo24
    span=(hi-lo).replace(0,np.nan)
    hr=h.index.hour+h.index.minute/60
    f=pd.DataFrame(index=h.index)
    f["ema_spread_atr"]=(h.ema20-h.ema50)/atr
    f["close_ema_atr"]=(h.close-h.ema20)/atr
    f["adx14"]=h.adx/100
    f["di_spread"]=(h.plus_di-h.minus_di)/100
    f["efficiency12"]=h.er12
    f["atr_ratio72"]=h.atr_ratio
    f["channel_location"]=(h.close-lo)/span
    f["candle_body_atr"]=(h.close-h.open)/atr
    f["close_change_1h_atr"]=h.close.diff()/atr
    f["close_change_4h_atr"]=(h.close-h.close.shift(4))/atr
    f["close_change_12h_atr"]=(h.close-h.close.shift(12))/atr
    f["range_atr"]=(h.high-h.low)/atr
    f["hour_sin"]=np.sin(2*pi*hr/24)
    f["hour_cos"]=np.cos(2*pi*hr/24)
    f=f.replace([np.inf,-np.inf],np.nan)
    valid=(h.valid & np.isfinite(f.to_numpy(float)).all(axis=1))
    future_atr=(h.close.shift(-4)-h.close)/atr
    labels=pd.Series(index=h.index,dtype="object")
    labels.loc[future_atr>=1.0]="UP"
    labels.loc[future_atr<=-1.0]="DOWN"
    labels.loc[future_atr.between(-1,1,inclusive="neither")]="RANGE"
    labels=labels.where(future_atr.notna())
    # Hour h.index[j] starts at t and closes at t+1h.
    # Future +4h close is at t+5h, so it cannot be fit until then.
    released=h.index+pd.Timedelta(hours=5)
    entry_month=(h.index+pd.Timedelta(hours=1)).tz_convert("Asia/Kolkata").strftime("%Y-%m")
    return f,valid,labels,released,entry_month

def confidence_side(probs):
    pdown,prange,pup=probs
    if pup>=THRESHOLD and pup>=pdown+SEPARATION and pup>=prange+SEPARATION:
        return 1
    if pdown>=THRESHOLD and pdown>=pup+SEPARATION and pdown>=prange+SEPARATION:
        return -1
    return 0

def train_and_predict(h):
    f,valid,labels,released,entry_month=make_features(h)
    pred=np.zeros(len(h),dtype=int)
    prediction_records=[]
    model_month_records=[]
    training_max_dates=[]
    for month in EVAL_MONTHS:
        start=month_start_utc(month)
        train=(valid & labels.notna() & (released<=start))
        test=(valid & (entry_month==month))
        n=int(train.sum())
        if n<2500:
            raise RuntimeError("Insufficient past-only training: "+month+" count="+str(n))
        if not (released[train]<=start).all():
            raise RuntimeError("Future outcome leaked into fit: "+month)
        xtrain=f.loc[train].to_numpy(float)
        ytrain=labels.loc[train].to_numpy()
        monthscores=f.loc[test].to_numpy(float)
        idx=np.flatnonzero(test.to_numpy())
        if len(idx)==0:
            raise RuntimeError("No monthly predictions")
        model=make_pipeline(StandardScaler(),
            LogisticRegression(C=1.0,max_iter=500,solver="lbfgs",random_state=0))
        model.fit(xtrain,ytrain)
        classes=model.named_steps["logisticregression"].classes_
        if set(classes)!=set(CATS):
            raise RuntimeError("Missing target class in training")
        probraw=model.predict_proba(monthscores)
        probs=np.zeros((len(idx),len(CATS)))
        for ppos,c in enumerate(CATS):
            probs[:,ppos]=probraw[:,np.flatnonzero(classes==c)[0]]
        prior_prob=np.array([(ytrain==c).mean() for c in CATS])
        majority=CATS[int(np.argmax(prior_prob))]
        chosen=[confidence_side(x) for x in probs]
        pred[idx]=chosen
        for k,j in enumerate(idx):
            truth=labels.iat[j]
            # The predicted label is known after the 4h horizon and ONLY used to score.
            prediction_records.append(dict(
                month_ist=month,year=month[:4],h_utc=str(h.index[j]),
                next_minute_entry_utc=str(h.index[j]+pd.Timedelta(hours=1)),
                score_sample=bool(j%4==0),
                true_next4h_state=truth if isinstance(truth,str) else None,
                predicted_state=CATS[int(np.argmax(probs[k]))],
                baseline_majority=majority,
                p_down=float(probs[k,0]),p_range=float(probs[k,1]),
                p_up=float(probs[k,2]),
                climatology_down=float(prior_prob[0]),
                climatology_range=float(prior_prob[1]),
                climatology_up=float(prior_prob[2]),
                trade_side=int(chosen[k])))
        released_train_max=str(released[train].max())
        if pd.Timestamp(released_train_max)>start:
            raise RuntimeError("Training used a future next4H target")
        training_max_dates.append(released_train_max)
        model_month_records.append(dict(month_ist=month,
            training_labels=n,train_max_target_available_utc=released_train_max,
            month_start_utc=str(start),
            majority_prior_class=majority,
            class_train_down=int((ytrain=="DOWN").sum()),
            class_train_range=int((ytrain=="RANGE").sum()),
            class_train_up=int((ytrain=="UP").sum()),
            monthly_closed_hour_predictions=len(idx),
            monthly_allowed_long=int(np.sum(np.array(chosen)==1)),
            monthly_allowed_short=int(np.sum(np.array(chosen)==-1))))
    records=pd.DataFrame(prediction_records)
    records.to_csv(OUT/"hourly_predictions.csv",index=False)
    log=pd.DataFrame(model_month_records)
    log.to_csv(OUT/"monthly_training_audit.csv",index=False)
    return pred, records,log

def scores(preds):
    subset=preds[(preds.score_sample)&preds.true_next4h_state.notna()].copy()
    if len(subset)<1000:
        raise RuntimeError("Not enough independent scored hours")
    out=[]
    for period in ["2025-Jul-Dec","2026-Jan-Oct","combined"]:
        q=subset if period=="combined" else subset[
            subset.year==("2025" if period.startswith("2025") else "2026")]
        y=q.true_next4h_state.to_numpy()
        pred=q.predicted_state.to_numpy()
        baseline=q.baseline_majority.to_numpy()
        probs=q[["p_down","p_range","p_up"]].to_numpy(float)
        clim=q[["climatology_down","climatology_range","climatology_up"]].to_numpy(float)
        out.append(dict(
            period=period,scored_nonoverlapping_4h_hours=len(q),
            model_accuracy_pct=round(100*accuracy_score(y,pred),3),
            train_majority_accuracy_pct=round(100*accuracy_score(y,baseline),3),
            model_macro_f1=round(f1_score(y,pred,labels=CATS,average="macro",zero_division=0),4),
            train_majority_macro_f1=round(f1_score(y,baseline,labels=CATS,average="macro",zero_division=0),4),
            model_logloss=round(log_loss(y,probs,labels=CATS),5),
            train_climatology_logloss=round(log_loss(y,clim,labels=CATS),5),
            model_confident_direction_signal_hours=int((q.trade_side!=0).sum())))
    pd.DataFrame(out).to_csv(OUT/"forward_prediction_score.csv",index=False)
    conf=confusion_matrix(subset.true_next4h_state,subset.predicted_state,labels=CATS)
    pd.DataFrame(conf,index=["true_"+i for i in CATS],
                 columns=["pred_"+i for i in CATS]).to_csv(OUT/"prediction_confusion_matrix.csv")
    mon=[]
    for month,g in subset.groupby("month_ist"):
        y=g.true_next4h_state.to_numpy()
        p=g.predicted_state.to_numpy()
        b=g.baseline_majority.to_numpy()
        mon.append(dict(month_ist=month,n=len(g),
           model_accuracy_pct=round(100*accuracy_score(y,p),3),
           train_majority_accuracy_pct=round(100*accuracy_score(y,b),3),
           model_macro_f1=round(f1_score(y,p,labels=CATS,average="macro",zero_division=0),4),
           high_confidence_hours=int((g.trade_side!=0).sum())))
    pd.DataFrame(mon).to_csv(OUT/"monthly_prediction_score.csv",index=False)
    return pd.DataFrame(out)

def account(trades):
    m=[]
    eq=base.INITIAL
    for month in MONTHS:
        g=trades[trades.month_ist==month] if len(trades) else trades
        pnl=float(g.pnl_usd.sum()) if len(g) else 0
        start=eq
        eq+=pnl
        m.append(dict(month_ist=month,trades=len(g),
            wins=int((g.pnl_usd>0).sum()) if len(g) else 0,
            losses=int((g.pnl_usd<0).sum()) if len(g) else 0,
            net_return_pct=round(float(100*pnl/start),5),
            pnl_usd=round(pnl,2),
            fee_gst_usd=round(float(g.fee_gst_usd.sum()),2) if len(g) else 0.,
            slippage_usd=round(float(g.slippage_usd.sum()),2) if len(g) else 0.,
            end_equity_usd=round(eq,2),
            status="Profit" if pnl>0 else "Loss" if pnl<0 else "No trade"))
    result=pd.DataFrame(m)
    result.to_csv(OUT/"monthly_account_returns.csv",index=False)
    if len(trades) and abs(eq-float(trades.equity_usd.iloc[-1]))>0.001:
        raise RuntimeError("Failed account reconciliation")
    gain=float(trades.pnl_usd[trades.pnl_usd>0].sum()) if len(trades) else 0
    loss=-float(trades.pnl_usd[trades.pnl_usd<0].sum()) if len(trades) else 0
    ecurve=np.r_[base.INITIAL,trades.equity_usd.to_numpy(float)] if len(trades) else np.array([base.INITIAL])
    dd=100*(1-ecurve/np.maximum.accumulate(ecurve))
    s=dict(trades=len(trades),win_rate_pct=round(100*(trades.pnl_usd>0).mean(),2) if len(trades) else 0,
        net_return_pct=round(100*(eq/base.INITIAL-1),4),
        net_profit_usd=round(eq-base.INITIAL,2),
        ending_equity_usd=round(eq,2),
        profit_factor=round(gain/loss,4) if loss>0 else None,
        max_trade_close_drawdown_pct=round(float(dd.max()),3),
        profitable_months=int((result.pnl_usd>0).sum()),
        losing_months=int((result.pnl_usd<0).sum()),
        idle_months=int((result.pnl_usd==0).sum()),
        evaluation_profitable_months=int((result.loc[result.month_ist>="2025-07","pnl_usd"]>0).sum()),
        fee_gst_usd=round(float(trades.fee_gst_usd.sum()),2) if len(trades) else 0.,
        slippage_usd=round(float(trades.slippage_usd.sum()),2) if len(trades) else 0.,
        passes_22_positive_months=bool((result.pnl_usd>0).all()))
    (OUT/"trading_summary.json").write_text(json.dumps(s,indent=2)+"\n")
    return result,s

def main():
    one,manifest=base.load()
    h=base.features(one)
    previous=json.loads(Path("analysis/btc_multiregime_audit_20261121/classifier_audit.json").read_text())
    if previous["history_revision_detected"]:
        raise RuntimeError("Past regime labels revised; abort")
    trade_signals,predictions,train_audit=train_and_predict(h)
    quality=dict(
       data="BTCUSD 1M Delta India, SHA and minute continuity verified",
       native_minutes=len(one),expected_minutes=992160,
       source_partitions=len(manifest["partitions"]),
       hourly_bars=len(h),features_known_at_1H_close=True,
       monthly_training_only_available_released_labels=True,
       first_replayed_month=EVAL_MONTHS[0],
       initial_training_only_months=MONTHS[:6],
       target="forward 4H close difference / ATR14 at signal close; UP >1, DOWN <-1, else RANGE",
       model="fixed L2 logistic regression with StandardScaler, C=1, max_iter=500, past-only fit",
       signal_threshold="prob_up/down >=0.55 AND 0.15 margin over both other classes",
       fees="taker 0.05% each side plus GST 18%",
       assumed_slippage_price_points_each_side=base.SLIP,
       historical_spreads_real_funding_liquidation_missing=True,
       truly_blind_external_holdout=False)
    if len(one)!=992160: raise RuntimeError("Archive parity failed")
    scoresout=scores(predictions)
    base.SPECS["ml_directional"]=(1.,2.,4)
    try:
        trades=base.run(one,h,{"ml_directional":trade_signals})
    finally:
        del base.SPECS["ml_directional"]
    if len(trades):
        if not trades.entry_utc.is_monotonic_increasing:
            raise RuntimeError("Unexpected trade order")
        if not trades.regime.isin(base.STATES).all():
            raise RuntimeError("Missing causal regime labels")
        entries=pd.to_datetime(trades.entry_utc,utc=True)
        exits=pd.to_datetime(trades.exit_utc,utc=True)
        if len(entries)>1 and not (entries.iloc[1:].to_numpy()>exits.iloc[:-1].to_numpy()).all():
            raise RuntimeError("Overlapping trades")
        trades.to_csv(OUT/"trade_ledger.csv",index=False)
    else:
        (OUT/"trade_ledger.csv").write_text("entry_utc,exit_utc,month_ist,pnl_usd\n")
    monthly,s=account(trades)
    (OUT/"quality.json").write_text(json.dumps(quality,indent=2)+"\n")
    report=[
       "# BTC next-4H predictive market-state model: monthly walk-forward 1M backtest",
       "",
       "## Objective",
       "Measure whether a monthly past-only logistic model can improve prediction of whether BTC moves up > 1 ATR, down >1 ATR, or neither in the NEXT 4H, beyond training-prior majority and climatology controls. Trade only the frozen >=0.55 high-confidence directional predictions. The 22-month research target remains positive net performance in every complete month.",
       "",
       "## Data quality, causal features and limits","~~~json",json.dumps(quality,indent=2),"~~~","",
       "UTC 1H bar must be completed before features are used. Target released only after four later complete hours: monthly training excludes the last 5h label embargo. StandardScaler and logistic model are fit separately on only training rows prior to month start. 2025 Jan-Jun training only; 2026 has already been researched globally and is NOT a pristine unseen independent holdout.",
       "",
       "## Directional prediction vs past-only baselines (non-overlapping 4H origins)",
       scoresout.to_markdown(index=False),"",
       "## Frozen directional strategy account summary",
       "~~~json",json.dumps(s,indent=2),"~~~","",
       "## All 22 monthly actual account net returns",
       monthly.to_markdown(index=False),"",
       "## Before live use",
       "- Prediction accuracy is not necessarily trading profitability. Confidence thresholds were fixed before backtest; not tuned to results.",
       "- STOP=1 ATR14, TP=2R, 4H max hold, entry next native 1M open, stop-before-target same minute, IST month-end flatten, 0.5% stop-risk and 3x notional cap.",
       "- Simulated taker 0.05% each side +18% GST and $5 price-point slip each side. Real spreads, funding, realized settlements, liquidation, contract quantities and depth unavailable.",
       "- Win rate / drawdown samples on closed trades do NOT guarantee live fills or investor safety.",
       "- Historical backtest selection context is already researched; prospective paper trading is needed to validate any positive score.",
    ]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")
    print("PREDICTOR_SCORE")
    print(scoresout.to_string(index=False))
    print("TRADE_SUMMARY",json.dumps(s))
    print("MONTHLY_RESULTS")
    print(monthly.to_string(index=False))
    print("DONE")

if __name__=="__main__":
    main()
