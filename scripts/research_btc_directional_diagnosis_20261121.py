#!/usr/bin/env python3
"""Fix misleading majority-RANGE prediction: test next-4H direction directly.

Forecast UP-v-DOWN and expansion as separate outcomes, using fixed monthly
chronological fitting and a fully separate native-1M execution replay.
All decision thresholds/models are preregistered in NOVELTY_CHECK.md.
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (accuracy_score, balanced_accuracy_score,
    roc_auc_score, brier_score_loss, log_loss, confusion_matrix)

import research_btc_regime_attribution_20261121 as base

OUT = Path("analysis/btc_directional_diagnosis_20261121")
OUT.mkdir(parents=True, exist_ok=True)
MONTHS = [str(p) for p in pd.period_range("2025-01","2026-10",freq="M")]
EVALUATION_MONTHS = MONTHS[6:]
MIN_P_DIRECTION = .62
MIN_P_EXPANSION = .35

def month_begin_utc(month):
    return pd.Timestamp(month+"-01",tz="Asia/Kolkata").tz_convert("UTC")

def prepare(h):
    atr=h.atr.replace(0,np.nan)
    close=h.close
    span=(h.hi24-h.lo24).replace(0,np.nan)
    f=pd.DataFrame(index=h.index)
    f["ema_spread_atr"]=(h.ema20-h.ema50)/atr
    f["close_ema20_atr"]=(close-h.ema20)/atr
    f["sma200_distance_atr"]=(close-close.rolling(200,min_periods=200).mean())/atr
    f["adx14"]=h.adx/100
    f["di_spread"]=(h.plus_di-h.minus_di)/100
    f["er12"]=h.er12
    f["atr_ratio72"]=h.atr_ratio
    f["channel_loc24"]=(close-h.lo24)/span
    f["channel_break24_up_atr"]=(close-h.hi24)/atr
    f["channel_break24_dn_atr"]=(h.lo24-close)/atr
    f["bar_body_atr"]=(close-h.open)/atr
    f["bar_range_atr"]=(h.high-h.low)/atr
    f["upper_wick_atr"]=(h.high-h[["open","close"]].max(axis=1))/atr
    f["lower_wick_atr"]=(h[["open","close"]].min(axis=1)-h.low)/atr
    for lag in (1,2,4,8,12,24,48):
        f["return_%sh_atr"%lag]=(close-close.shift(lag))/atr
    f["return_vol_24h_atr"]=(close.diff().rolling(24,min_periods=24).std(ddof=0))/atr
    dh=close.diff()
    gain=dh.clip(lower=0).ewm(alpha=1/14,adjust=False,min_periods=14).mean()
    loss=(-dh.clip(upper=0)).ewm(alpha=1/14,adjust=False,min_periods=14).mean()
    f["rsi14"]=1-1/(1+gain/loss.replace(0,np.nan))
    hr=h.index.hour
    wd=h.index.dayofweek
    f["utc_hour_sin"]=np.sin(2*np.pi*hr/24)
    f["utc_hour_cos"]=np.cos(2*np.pi*hr/24)
    f["weekday_sin"]=np.sin(2*np.pi*wd/7)
    f["weekday_cos"]=np.cos(2*np.pi*wd/7)
    f=f.replace([np.inf,-np.inf],np.nan)
    valid=(h.valid & np.isfinite(f.to_numpy(float)).all(axis=1))
    future_change=(close.shift(-4)-close)
    ydirection=(future_change>0).astype(float)
    ydirection=ydirection.where(future_change.ne(0)&future_change.notna())
    yexp=(future_change.abs()>=atr).astype(float)
    yexp=yexp.where(future_change.notna())
    # Hour at index t is known after bar t..t+59m; its t+4 bar
    # becomes finalized only at t+5h.
    target_available=h.index+pd.Timedelta(hours=5)
    entry_month=(h.index+pd.Timedelta(hours=1)).tz_convert("Asia/Kolkata").strftime("%Y-%m")
    return f, valid, future_change, ydirection, yexp, target_available, entry_month

def build_models():
    return {
      "logistic":make_pipeline(StandardScaler(),LogisticRegression(
          C=1.,max_iter=500,solver="lbfgs",random_state=0)),
      "boosted":HistGradientBoostingClassifier(
          learning_rate=.04,max_iter=100,max_leaf_nodes=9,min_samples_leaf=100,
          l2_regularization=5.,max_bins=63,early_stopping=False,random_state=0)
    }

def forecast(h):
    f,valid,change,yd,ye,released,entry_month=prepare(h)
    pred_rows=[]
    audit=[]
    sides=np.zeros(len(h),dtype=int)
    for month in EVALUATION_MONTHS:
        begin=month_begin_utc(month)
        fit=valid & yd.notna() & ye.notna() & (released<=begin)
        test=valid & (entry_month==month)
        j=np.flatnonzero(test.to_numpy())
        training=np.flatnonzero(fit.to_numpy())
        if len(training)<2500 or len(j)<500:
            raise RuntimeError("Not enough causal data for month: "+month)
        if not np.all(released[fit]<=begin):
            raise RuntimeError("Future label leaked into training")
        if len(np.unique(yd.iloc[training]))!=2 or len(np.unique(ye.iloc[training]))!=2:
            raise RuntimeError("Binary target did not have both outcomes")
        last_release=released[fit].max()
        if last_release>begin: raise RuntimeError("Training label release beyond month boundary")
        xtrain=f.iloc[training].to_numpy(float)
        xtest=f.iloc[j].to_numpy(float)
        p={}
        for model_id in ("logistic","boosted"):
            dm=build_models()[model_id]
            em=build_models()[model_id]
            dm.fit(xtrain,yd.iloc[training].to_numpy(int))
            em.fit(xtrain,ye.iloc[training].to_numpy(int))
            if not (np.array_equal(dm.classes_,[0,1]) if model_id=="boosted" else np.array_equal(dm.named_steps["logisticregression"].classes_,[0,1])):
                raise RuntimeError("Direction model inverted target probability")
            p[model_id+"_up"]=dm.predict_proba(xtest)[:,1]
            p[model_id+"_exp"]=em.predict_proba(xtest)[:,1]
        prior_up=float(yd.iloc[training].mean())
        prior_exp=float(ye.iloc[training].mean())
        for k,loc in enumerate(j):
            bprob=float(p["boosted_up"][k])
            xprob=float(p["boosted_exp"][k])
            side=(1 if bprob>=MIN_P_DIRECTION and xprob>=MIN_P_EXPANSION
                else -1 if bprob<=1-MIN_P_DIRECTION and xprob>=MIN_P_EXPANSION
                else 0)
            sides[loc]=side
            momentum=int(h.close.iat[loc]>h.close.iat[loc-4])
            actual=yd.iat[loc]
            pred_rows.append(dict(month_ist=month,year=month[:4],
              signal_hour_start_utc=str(h.index[loc]),
              entry_utc=str(h.index[loc]+pd.Timedelta(hours=1)),
              nonoverlapping_4h_sample=bool(loc%4==0),
              true_future4h_up=int(actual) if pd.notna(actual) else None,
              true_future4h_delta_atr=float(change.iat[loc]/h.atr.iat[loc]) if pd.notna(change.iat[loc]) else None,
              true_future4h_expansion=int(ye.iat[loc]) if pd.notna(ye.iat[loc]) else None,
              p_up_logistic=float(p["logistic_up"][k]),
              p_up_boosted=bprob,
              p_expansion_logistic=float(p["logistic_exp"][k]),
              p_expansion_boosted=xprob,
              p_up_prior=prior_up,
              p_expansion_prior=prior_exp,
              momentum4h_up=momentum,
              boosted_trade_side=side))
        audit.append(dict(month_ist=month,
            month_start_utc=str(begin),
            train_direction_examples=len(training),
            train_positive_fraction=round(prior_up,4),
            train_expansion_fraction=round(prior_exp,4),
            training_max_future_target_available_utc=str(last_release),
            test_hours=len(j),
            boosted_signal_hours=int((sides[j]!=0).sum()),
            new_label_fit_within_month=False))
    a=pd.DataFrame(audit)
    a.to_csv(OUT/"monthly_training_audit.csv",index=False)
    pred=pd.DataFrame(pred_rows)
    pred.to_csv(OUT/"hourly_forecast_ledger.csv",index=False)
    return pred,sides,a

def metrics_for(y,p,baseline=False):
    y=np.array(y,dtype=int)
    p=np.asarray(p,dtype=float)
    yp=(p>=.5).astype(int)
    out=dict(accuracy_pct=round(100*accuracy_score(y,yp),3),
       balanced_accuracy_pct=round(100*balanced_accuracy_score(y,yp),3))
    if not baseline:
        out.update(dict(auc=round(float(roc_auc_score(y,p)),4),
             brier=round(float(brier_score_loss(y,p)),5),
             logloss=round(float(log_loss(y,np.clip(p,1e-6,1-1e-6),labels=[0,1])),5)))
    return out

def evaluate(p):
    scored=p[p.nonoverlapping_4h_sample & p.true_future4h_up.notna()].copy()
    if len(scored)<2500: raise RuntimeError("Not enough nonoverlapping evaluation labels")
    results=[]
    for period in ["2025H2","2026JanOct","overall"]:
        g=scored if period=="overall" else scored[scored.year==("2025" if period=="2025H2" else "2026")]
        y=g.true_future4h_up.to_numpy(int)
        if len(np.unique(y))!=2: raise RuntimeError("Unbalanced validation month")
        for model,field in (("boosted","p_up_boosted"),("logistic","p_up_logistic"),
                            ("training_prior","p_up_prior")):
            prob=g[field].to_numpy(float)
            m=metrics_for(y,prob)
            strong=((prob>=.62)|(prob<=.38))
            m.update(dict(period=period,model=model,n=len(g),
                actual_up_pct=round(100*y.mean(),2),
                confident_hours=int(strong.sum()),
                confident_direction_hit_pct=round(100*(y[strong]==(prob[strong]>=.5)).mean(),2) if strong.any() else None,
                boosted_move_gated_signal_hours=int((g.boosted_trade_side!=0).sum()) if model=="boosted" else None))
            results.append(m)
        m=metrics_for(y,g.momentum4h_up.to_numpy(float),baseline=True)
        m.update(dict(period=period,model="previous4h_momentum",n=len(g),
               actual_up_pct=round(100*y.mean(),2),
               confident_hours=None,confident_direction_hit_pct=None,
               boosted_move_gated_signal_hours=None))
        results.append(m)
    out=pd.DataFrame(results)
    out.to_csv(OUT/"directional_score.csv",index=False)
    # Hourly history-based class imbalance diagnostic.
    counts=scored.groupby("year").agg(total=("true_future4h_up","size"),
            up=("true_future4h_up","sum"))
    counts["up_pct"]=(100*counts.up/counts.total).round(2)
    counts.to_csv(OUT/"forward_direction_distribution.csv")
    conf=[]
    for model,field in (("boosted","p_up_boosted"),("logistic","p_up_logistic"),
                        ("training_prior","p_up_prior")):
        data=scored
        pp=data[field].to_numpy(float)
        yc=data.true_future4h_up.to_numpy(int)
        for lb,ub in zip([0,.2,.4,.6,.8],[.2,.4,.6,.8,1.00001]):
            mm=(pp>=lb)&(pp<ub)
            conf.append(dict(model=model,bin_low=lb,bin_high=min(ub,1),count=int(mm.sum()),
              average_forecast_up_prob=round(float(pp[mm].mean()),3) if mm.any() else None,
              actual_up_rate=round(float(yc[mm].mean()),3) if mm.any() else None))
    pd.DataFrame(conf).to_csv(OUT/"direction_calibration.csv",index=False)
    for model,field in (("boosted","p_up_boosted"),("logistic","p_up_logistic"),
                        ("training_prior","p_up_prior")):
        predlabel=(scored[field].to_numpy(float)>=.5).astype(int)
        mat=confusion_matrix(scored.true_future4h_up.to_numpy(int),predlabel,labels=[0,1])
        pd.DataFrame(mat,index=["actual_down","actual_up"],columns=["pred_down","pred_up"]).to_csv(OUT/(model+"_confusion.csv"))
    # A separate expansion prediction diagnostic. This uses data from all
    # future outcomes but never to trigger a trade.
    exp=scored[scored.true_future4h_expansion.notna()]
    exrows=[]
    for model,field in (("boosted","p_expansion_boosted"),("logistic","p_expansion_logistic"),
                        ("training_prior","p_expansion_prior")):
        yy=exp.true_future4h_expansion.to_numpy(int)
        pp=exp[field].to_numpy(float)
        exrows.append(dict(model=model,n=len(exp),
          actual_expansion_pct=round(100*yy.mean(),3),
          brier=round(float(brier_score_loss(yy,pp)),5),
          auc=round(float(roc_auc_score(yy,pp)),4),
          logloss=round(float(log_loss(yy,np.clip(pp,1e-6,1-1e-6))),5)))
    pd.DataFrame(exrows).to_csv(OUT/"expansion_probability_score.csv",index=False)
    # Big-move only directional score is explicitly ex-post diagnostic, NOT
    # an investable strategy that anticipates large movements perfectly.
    big=scored[scored.true_future4h_expansion.eq(1)]
    bigrows=[]
    for model,field in (("boosted","p_up_boosted"),("logistic","p_up_logistic"),
                        ("training_prior","p_up_prior")):
        pp=big[field].to_numpy(float);yy=big.true_future4h_up.to_numpy(int)
        bigrows.append(dict(model=model,n=len(big),
          directional_accuracy_pct=round(100*accuracy_score(yy,(pp>=.5).astype(int)),3)))
    pd.DataFrame(bigrows).to_csv(OUT/"large_move_ex_post_diagnostic.csv",index=False)
    return out

def report_account(tr):
    monthly=[]
    equity=base.INITIAL
    for month in MONTHS:
        g=tr[tr.month_ist==month] if len(tr) else tr
        pnl=float(g.pnl_usd.sum()) if len(g) else 0.
        monthly.append(dict(month_ist=month,trades=len(g),wins=int((g.pnl_usd>0).sum()) if len(g) else 0,
            losses=int((g.pnl_usd<0).sum()) if len(g) else 0,
            account_net_pct=round(100*pnl/equity,5),
            net_profit_usd=round(pnl,2),
            fee_gst_usd=round(float(g.fee_gst_usd.sum()),2) if len(g) else 0.,
            slippage_usd=round(float(g.slippage_usd.sum()),2) if len(g) else 0.,
            status="Profit" if pnl>0 else "Loss" if pnl<0 else "No trade"))
        equity+=pnl
    mr=pd.DataFrame(monthly)
    mr.to_csv(OUT/"monthly_account_net.csv",index=False)
    if len(tr) and abs(equity-float(tr.equity_usd.iloc[-1]))>.001:
        raise RuntimeError("Account month reconciliation failed")
    eqs=np.r_[base.INITIAL,tr.equity_usd.to_numpy(float)] if len(tr) else np.array([base.INITIAL])
    gain=float(tr.pnl_usd[tr.pnl_usd>0].sum()) if len(tr) else 0.
    loss=-float(tr.pnl_usd[tr.pnl_usd<0].sum()) if len(tr) else 0.
    s=dict(trades=len(tr),
           wins=int((tr.pnl_usd>0).sum()) if len(tr) else 0,
           win_rate_pct=round(100*(tr.pnl_usd>0).mean(),3) if len(tr) else 0,
           profitable_months=int((mr.net_profit_usd>0).sum()),
           losing_months=int((mr.net_profit_usd<0).sum()),
           no_trade_months=int((mr.net_profit_usd==0).sum()),
           account_net_return_pct=round(100*(equity/base.INITIAL-1),4),
           account_net_usd=round(equity-base.INITIAL,2),
           profit_factor=round(gain/loss,4) if loss>0 else None,
           max_trade_close_drawdown_pct=round(float((100*(1-eqs/np.maximum.accumulate(eqs))).max()),3),
           fees_gst_usd=round(float(tr.fee_gst_usd.sum()),2) if len(tr) else 0.,
           slippage_usd=round(float(tr.slippage_usd.sum()),2) if len(tr) else 0.,
           passes_22_22=bool((mr.net_profit_usd>0).all()))
    (OUT/"trading_summary.json").write_text(json.dumps(s,indent=2)+"\n")
    return mr,s

def main():
    one,manifest=base.load()
    if len(one)!=992160: raise RuntimeError("Native BTCUSD archive changed")
    h=base.features(one)
    prev=json.loads(Path("analysis/btc_multiregime_audit_20261121/classifier_audit.json").read_text())
    if prev["history_revision_detected"]:
        raise RuntimeError("History-prefix classifier bug")
    pred,side,training=forecast(h)
    scores=evaluate(pred)
    base.SPECS["direct4h_boosted"]=(1.,2.,4)
    try:
        tr=base.run(one,h,{"direct4h_boosted":side})
    finally:
        del base.SPECS["direct4h_boosted"]
    if len(tr):
        ts=pd.to_datetime(tr.entry_utc,utc=True)
        te=pd.to_datetime(tr.exit_utc,utc=True)
        if len(tr)>1 and not (ts.iloc[1:].to_numpy()>te.iloc[:-1].to_numpy()).all():
            raise RuntimeError("Overlapping trades")
        if tr.entry_utc.str[:4].eq("2025").any() and tr.month_ist.lt("2025-07").any():
            raise RuntimeError("Traded during initial training")
        tr.to_csv(OUT/"boosted_trades.csv",index=False)
    else:
        (OUT/"boosted_trades.csv").write_text("entry_utc,exit_utc,month_ist,pnl_usd\n")
    monthly,s=report_account(tr)
    qual=dict(source="Delta India BTCUSD native 1M",
        native_minutes=len(one),partitions=len(manifest["partitions"]),
        complete_ist_months=22,training_only_months=6,
        evaluated_months=16,model_selection_on_test=False,
        training_target_available_before_month=True,
        no_lookahead_prefix_classifier_test=True,
        direction_target="sign(close[t+4]-close[t]) on completed 1H; future outcome release t+5h",
        expansion_target="abs(next4h move) >= ATR14 at signal hour",
        signal="boosted p(up)>=.62 or <=.38 and p(expansion)>=.35",
        initial_equity_usd=base.INITIAL,
        risk_fraction=base.RISK,max_leverage=base.LEV_CAP,
        maker_fee_assumed=False,taker_fee_plus_gst_each_side=base.FEE,
        adverse_slip_points_each_side=base.SLIP,
        funding_settlement_spread_and_liquidation_missing=True,
        all_histories_previously_explored=True,
        external_blind_holdout=False)
    (OUT/"quality.json").write_text(json.dumps(qual,indent=2)+"\n")
    report=[
      "# BTC 4H direction model repair — separate sign from expansion / range",
      "",
      "## Fix implemented",
      "Previous 3-class predictor achieved 64.515% accuracy versus 64.583% training-majority baseline mainly by predicting the dominant RANGE class. This study forecasts next-4H **UP versus DOWN explicitly** and **>=1 ATR movement probability separately**, with fixed two model families and no test-period hyperparameter sweeps. A market label cannot be objectively declared correct absent independently labeled regimes; we measure future directional skill only.",
      "",
      "## Training, data and execution audit","~~~json",json.dumps(qual,indent=2),"~~~","",
      "All feature hours are closed. Next4H label released only after four later fully closed 1H candles. Each IST month has its own model trained exclusively on prior-released labels; no same-month outcome used for that month's model. Jan-Jun 2025 initial training-only months; July 2025 to Oct 2026 tested by chronological month. 2026 history is previously researched; NOT a genuinely untouched holdout.",
      "",
      "## 4H nonoverlapping directional forecasts vs last4H momentum and historical-prior baselines",
      scores.to_markdown(index=False),"",
      "## Frozen boosted directional trade rule, independently 1M replayed",
      "Stop 1x ATR14, TP 2R, max hold 4H, high-confidence p(up)>=.62 or <=.38 AND p(move)>=.35; no force trading. Next 1M open after closed 1H, same-minute stop before target, 0.5% current equity stop risk, max 3x notional, IST month-end flatten, taker 0.05% per side plus 18% GST and 5 BTCUSD points adverse slippage per leg.",
      "~~~json",json.dumps(s,indent=2),"~~~","",
      "## Every one of 22 months, net account performance",
      monthly.to_markdown(index=False),"",
      "## Additional files",
      "hourly_forecast_ledger.csv, directional_score.csv, expansion_probability_score.csv, monthly_training_audit.csv, direction_calibration.csv, three confusion matrices, large_move_ex_post_diagnostic.csv, monthly_account_net.csv and boosted_trades.csv.",
      "",
      "## Disqualifiers and cautions",
      "- A meaningful predictive system must outperform strong chronological baselines in direction and probability scores, and demonstrate positive independent after-cost expectancy. A code repair does not guarantee such an edge.",
      "- Large-move-only future diagnostic uses ex-post realized future movement; it is NOT a tradable condition.",
      "- This simulation omits historical order-book bid/ask spreads, realized funding settlements, latency, exchange contract granularity and liquidation/margin rules. Not live-ready.",
      "- Static thresholds and model families were predeclared BEFORE this run. Never pick the best model or tweak threshold using the same tested months and call it independently validated.",
      "- Drawdown is measured at trade closes, not intratrade margin extremes.",
    ]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")
    print("DIRECTION_SCORES")
    print(scores.to_string(index=False))
    print("TRADING",json.dumps(s))
    print("DONE")

if __name__=="__main__":
    main()
