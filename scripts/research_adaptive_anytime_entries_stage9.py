#!/usr/bin/env python3
"""Stage 9: time-independent BTCUSD 200pt entry classification from candle features.

A classifier uses ONLY closed 5-minute OHLCV candles and earlier data, no time
of day features. Train Jan-Sept 2025, select probability thresholds Oct-Dec
2025, evaluate on already-researched Jan-Jun, Jul-Oct, Nov 2026 separately.
No temporal split is an untouched holdout: historical research exposed it.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score, average_precision_score
from research_every_candle_200 import (
    read_archive, first_passage, STOP, MAX_MINUTES, FEE, SLIPPAGE
)

OUT=Path("analysis/institutional_discovery_stage9_adaptive_direction")
TRAIN_STOP=pd.Timestamp("2025-10-01",tz="UTC")
SELECT_STOP=pd.Timestamp("2026-01-01",tz="UTC")
EVAL_H1=pd.Timestamp("2026-07-01",tz="UTC")
EVAL_H2=pd.Timestamp("2026-11-01",tz="UTC")
HORIZON=30
SIDE_NAME={1:"LONG",-1:"SHORT"}
THRESHOLD_GRID=(0.20,0.25,0.30,0.35,0.40,0.45,0.50,0.60,0.70)
SEED=20261117

def features(f):
    """Right-labeled 5m candles are known at exactly their closing timestamp."""
    x=f[["open","high","low","close","volume"]].resample(
        "5min",label="right",closed="left").agg({
        "open":"first","high":"max","low":"min","close":"last",
        "volume":"sum"})
    x["complete"]=f.close.resample(
        "5min",label="right",closed="left").count().eq(5)
    x["r"]=x.high-x.low
    x["body"]=x.close-x.open
    x["loc"]=(x.close-x.low)/x.r.replace(0,np.nan)
    r_med=x.r.rolling(24,min_periods=24).median().shift(1)
    v_mean=x.volume.rolling(24,min_periods=24).mean().shift(1)
    r_med72=x.r.rolling(72,min_periods=72).median().shift(1)
    frame=pd.DataFrame(index=x.index)
    frame["range_ratio"]=x.r/r_med.replace(0,np.nan)
    frame["volume_ratio"]=x.volume/v_mean.replace(0,np.nan)
    frame["range_regime"]=r_med/r_med72.replace(0,np.nan)
    frame["candle_body_frac"]=x.body/x.r.replace(0,np.nan)
    frame["close_location"]=x["loc"]
    frame["wick_up_frac"]=(x.high-np.maximum(x.open,x.close))/x.r.replace(0,np.nan)
    frame["wick_down_frac"]=(np.minimum(x.open,x.close)-x.low)/x.r.replace(0,np.nan)
    frame["ret_1"]=x.close.diff()/r_med.replace(0,np.nan)
    for n in (2,3,6,12,24):
        frame[f"trend_{n}"]=x.close.diff(n)/r_med.replace(0,np.nan)
        frame[f"range_{n}"]=(x.high.rolling(n).max()-x.low.rolling(n).min())/r_med.replace(0,np.nan)
        frame[f"volume_{n}"]=x.volume.rolling(n).mean()/v_mean.replace(0,np.nan)
    frame["distance_h12"]=(x.close-x.high.rolling(12).max().shift(1))/r_med.replace(0,np.nan)
    frame["distance_l12"]=(x.close-x.low.rolling(12).min().shift(1))/r_med.replace(0,np.nan)
    frame["distance_h24"]=(x.close-x.high.rolling(24).max().shift(1))/r_med.replace(0,np.nan)
    frame["distance_l24"]=(x.close-x.low.rolling(24).min().shift(1))/r_med.replace(0,np.nan)
    frame["volume_accel"]=x.volume/x.volume.shift(1).replace(0,np.nan)
    frame["range_accel"]=x.r/x.r.shift(1).replace(0,np.nan)
    frame["prior_body"]=x.body.shift(1)/r_med.replace(0,np.nan)
    frame["prior_close_loc"]=x["loc"].shift(1)
    frame["prior_volume_ratio"]=frame.volume_ratio.shift(1)
    frame["prior_range_ratio"]=frame.range_ratio.shift(1)
    frame["abs_ret_12"]=x.close.diff(12).abs()/r_med.replace(0,np.nan)
    complete=x.complete.rolling(90,min_periods=90).sum().eq(90)
    # Clip ratios determined a priori to reduce outlier influence.
    frame=frame.replace([np.inf,-np.inf],np.nan).clip(-50,50)
    valid=complete & frame.notna().all(axis=1)
    return frame,valid


def simulate(op,cl,k,side,t200,tnet,tstop,target,stop=100,horizon=30):
    """Stop-first, fee inclusive; only outcome known after signal."""
    d=0 if side==1 else 1
    entry=float(op[k])
    if target=="net200":
        move=(200+2*SLIPPAGE+2*FEE*entry)/(1-FEE*side)
        tg=int(tnet[k,d])
    else:
        move=200.
        tg=int(t200[k,d])
    st=int(tstop[k,d,int(np.flatnonzero(STOP==stop)[0])])
    if tg>=horizon:tg=-1
    if st>=horizon:st=-1
    if st>=0 and (tg<0 or st<=tg):
        exit_idx=k+st
        exitmid=min(float(op[exit_idx]),entry-stop) if side==1 else max(float(op[exit_idx]),entry+stop)
        reason="stop"
    elif tg>=0:
        exit_idx=k+tg
        exitmid=entry+side*move
        reason="target"
    else:
        exit_idx=k+horizon-1
        exitmid=float(cl[exit_idx])
        reason="timeout"
    entryfill=entry+side*SLIPPAGE
    exitfill=exitmid-side*SLIPPAGE
    net=side*(exitfill-entryfill)-FEE*(entryfill+exitfill)
    offer=side*(exitfill-entryfill)-FEE*entryfill # <=30m
    return exit_idx,net,offer,reason


def metrics(y,p):
    if len(np.unique(y))<2:
        return dict(n=len(y),hit_rate=float(y.mean())*100,auc=None,average_precision=None)
    return dict(n=len(y),hit_rate=round(100*float(y.mean()),2),
                auc=round(float(roc_auc_score(y,p)),4),
                average_precision=round(float(average_precision_score(y,p)),4))


def model_signals(f,seg_start,seg_end):
    feature,valid=features(f)
    ix=f.index
    ends=np.asarray(feature.index)
    ii=ix.get_indexer(feature.index)
    # Entries only where source minute exists, 4h future is present,
    # no historical gaps, and past aggregation is complete.
    good=(ii>=0)
    idx=ii[good]
    final=np.zeros(len(ii),dtype=bool)
    inside=(idx>=0)&(idx<len(f))
    idx=idx[inside]
    ixpos=np.flatnonzero(good)[inside]
    final[ixpos]=(idx-seg_start[idx]>=450)&(seg_end[idx]-idx>=MAX_MINUTES)
    final &= valid.to_numpy(bool)
    selection=feature.iloc[np.flatnonzero(final)].copy()
    k=ii[final]
    # Explicit purge around train/threshold selection / validation boundaries.
    ts=selection.index
    boundary=[TRAIN_STOP,SELECT_STOP,EVAL_H1,EVAL_H2]
    for b in boundary:
        cond=(ts >= b-pd.Timedelta(hours=4))&(ts < b+pd.Timedelta(hours=4))
        keep=~cond
        selection=selection.loc[keep]
        k=k[np.asarray(keep)]
        ts=selection.index
    return selection,k


def eval_net(key,side,threshold,proba,indices,op,cl,t200,tnet,tstop,mode):
    chosen=np.flatnonzero(proba>=threshold)
    last=-1
    records=[]
    for z in chosen:
        k=int(indices[z])
        if k<=last:continue
        end,net,offer,reason=simulate(op,cl,k,side,t200,tnet,tstop,mode)
        last=end
        records.append(dict(k=k,probability=float(proba[z]),gross_case=mode,
            exit_idx=end,standard_net=net,offer_if_eligible=offer,reason=reason))
    if not records:
        return [],dict(trades=0,mean_net_pts=None,profit_factor=None,
                       wins=0,losses=0)
    frame=pd.DataFrame(records)
    v=frame.standard_net.to_numpy(float)
    return records,dict(trades=len(frame),mean_net_pts=round(float(v.mean()),2),
        profit_factor=round(float(v[v>0].sum()/-v[v<0].sum()),3)
            if (v<0).any() else None,
        wins=int((v>0).sum()),losses=int((v<=0).sum()),
        win_pct=round(100*float((v>0).mean()),2),
        sum_net_pts=round(float(v.sum()),2),
        whatif_avg_pts=round(float(frame.offer_if_eligible.mean()),2))


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    f,seg_start,seg_end,q=read_archive()
    featureset,k=model_signals(f,seg_start,seg_end)
    ti=featureset.index
    op=f.open.to_numpy(np.float64)
    hi=f.high.to_numpy(np.float64)
    lo=f.low.to_numpy(np.float64)
    cl=f.close.to_numpy(np.float64)
    t200,tnet,tstop,mae=first_passage(op,hi,lo,seg_end,STOP,MAX_MINUTES)
    train=(ti<TRAIN_STOP)
    selection=(ti>=TRAIN_STOP)&(ti<SELECT_STOP)
    splits=dict(train=train,select_2025Q4=selection,
                check_2026H1=(ti>=SELECT_STOP)&(ti<EVAL_H1),
                recheck_2026H2=(ti>=EVAL_H1)&(ti<EVAL_H2),
                november_recent=(ti>=EVAL_H2))
    X=featureset.to_numpy(np.float32)
    importance=[]
    forecasts=[]
    thresholds=[]
    model_results=[]
    for side in (1,-1):
        d=0 if side==1 else 1
        # Training objective NET +200 before -100; equal-minute ambiguity is loss.
        target=tnet[k,d]
        stop=tstop[k,d,3]
        labels=((target>=0)&(target<HORIZON)&
                ((stop<0)|(target<stop))).astype(np.int8)
        clf=HistGradientBoostingClassifier(
            max_depth=3,max_iter=110,learning_rate=.05,
            min_samples_leaf=120,l2_regularization=10.0,
            random_state=SEED,early_stopping=False)
        clf.fit(X[train],labels[train])
        probs=clf.predict_proba(X)[:,1]
        for label,mask in splits.items():
            forecasts.append(dict(side=SIDE_NAME[side],period=label,
                                  **metrics(labels[mask],probs[mask]),
                                  mean_pred=round(float(probs[mask].mean()),4),
                                  top_decile_label_rate=round(float(
                                      labels[mask][probs[mask]>=np.quantile(probs[train],.9)].mean()*100),2)
                                      if np.any(mask&(probs>=np.quantile(probs[train],.9))) else None))
        # Choose threshold on 2025 Q4 only, requiring >=30 actual independent trades.
        choose=[]
        for threshold in THRESHOLD_GRID:
            rec,score=eval_net("selection",side,threshold,probs[selection],k[selection],
                               op,cl,t200,tnet,tstop,"net200")
            choose.append(dict(threshold=threshold,**score))
        eligible=[v for v in choose if v["trades"]>=30]
        best=max(eligible,key=lambda v:v["mean_net_pts"]) if eligible else {"threshold":.5}
        threshold=best["threshold"]
        thresholds.append(dict(side=SIDE_NAME[side],selected_threshold=threshold,
                               selection_trades=best.get("trades",0),
                               selection_net=best.get("mean_net_pts"),
                               scored_grid=choose))
        for label,mask in splits.items():
            for cutname,cut in (("trained_threshold",threshold),
                                ("baseline_top10pct",float(np.quantile(probs[train],.9)))):
                for target_mode in ("gross200","net200"):
                    rec,score=eval_net(label,side,cut,probs[mask],k[mask],
                                       op,cl,t200,tnet,tstop,target_mode)
                    model_results.append(dict(side=SIDE_NAME[side],period=label,
                                              cutoff_model=cutname,
                                              threshold=round(float(cut),5),
                                              tp_model=target_mode,**score))
        # No time/day features: feature influence using SHAP not available;
        # rank coarse relative changes by feature permutation only on 2025 Q4.
        # Limit 20,000 samples and keep deterministic: indicative, not causal.
        select_idx=np.flatnonzero(selection)[::3][:20000]
        if len(select_idx)>0:
            baseline_auc=average_precision_score(labels[select_idx],probs[select_idx])
            rng=np.random.default_rng(SEED+side)
            for col,name in enumerate(featureset.columns):
                hold=X[select_idx].copy()
                hold[:,col]=hold[rng.permutation(len(hold)),col]
                perm=clf.predict_proba(hold)[:,1]
                importance.append(dict(side=SIDE_NAME[side],feature=name,
                    AP_drop=round(float(baseline_auc-average_precision_score(
                        labels[select_idx],perm)),5)))
    pd.DataFrame(forecasts).to_csv(OUT/"model_skill.csv",index=False)
    pd.DataFrame(model_results).to_csv(OUT/"strategy_performance.csv",index=False)
    pd.DataFrame(importance).to_csv(OUT/"feature_importance.csv",index=False)
    (OUT/"selected_thresholds.json").write_text(json.dumps(thresholds,indent=2)+"\n")
    meta=dict(source=q["source"],observed_candles=len(f),
        model_feature_rows=len(featureset),features=list(featureset.columns),
        splits={key:int(m.sum()) for key,m in splits.items()},
        objective="first NET200 before -100 within 30m (stop first)",
        model="HistGradientBoostingClassifier depth3, 110 iters, 120 minimum leaf",
        model_count=2,thresholds=THRESHOLD_GRID,
        no_clock_time_features=True,training="2025 Jan-Sep",
        threshold_selection="2025 Oct-Dec, target chosen by 2025 net expectancy only",
        chronological_reporting="2026 H1, H2, Nov inspected previously",
        cost_per_side=FEE,slippage_each_side=SLIPPAGE,
        limitations=[
          "2026 periods are research-exposed, not independent virgin holdouts",
          "Target labels of 5m signals overlap and overstate effective sample size",
          "1m OHLC stop-first; no historical spread, fills, impact or funding",
          "Threshold selection among nine alternatives creates selection bias",
          "Model probabilities can drift with changes in BTC price/volatility",
          "No guarantee of profitability or zero losses"])
    (OUT/"quality.json").write_text(json.dumps(meta,indent=2)+"\n")
    scores=pd.DataFrame(forecasts)
    results=pd.DataFrame(model_results)
    report=[
        "# Stage 9 — Adaptive entry discovery from closed BTC candles",
        "",
        "## Method",
        "Any-time model with NO hour, weekday or session inputs. 33 completed-bar",
        "price/volume/volatility features from 5m BTCUSD futures candles.",
        "Train Jan-Sep 2025; select cutoff Oct-Dec 2025; report 2026",
        "chronologically without adjusting decisions after seeing later results.",
        "Classification goal: net +200 before -100 within 30m, stop-first.",
        "",
        "## Prediction skill",
        scores.to_markdown(index=False),"",
        "## Chosen probability cutoff",
        pd.DataFrame([{k:v for k,v in d.items() if k!="scored_grid"} for d in thresholds]).to_markdown(index=False),"",
        "## Independently replayed net trading outcomes",
        results.to_markdown(index=False),"",
        "## Exploratory feature importance by 2025 selection permutation",
        pd.DataFrame(importance).sort_values("AP_drop",ascending=False).head(20).to_markdown(index=False),"",
        "## Interpretation",
        "- More frequent +200 gross excursions do NOT guarantee a positive net result.",
        "- Any positive results with tiny independent trade counts are not validated.",
        "- All trades have known-at-entry features; zero next-bar lookahead.",
        "- 0.05% taker per side, GST 18%, adverse 5 pts per side included.",
        "- Scalper offer sensitivity is separate, not assumed qualified.",
        "- No 2026 result should be treated as an untouched holdout.",
        *["- "+x for x in meta["limitations"]]
    ]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")
    print("STAGE9_DONE "+json.dumps({k:meta[k] for k in ("observed_candles","model_feature_rows","splits","objective")}))
    print("SKILL\n"+scores.to_string(index=False))
    print("PERFORMANCE\n"+results.to_string(index=False))

if __name__=="__main__":
    main()
