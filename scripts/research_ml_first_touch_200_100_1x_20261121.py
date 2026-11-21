#!/usr/bin/env python3
"""One-shot chronological BTCUSD first-touch ML: 1x, 200 TP, 100 SL.

Train Jan-Jun 2025, select threshold from Jul-Dec 2025, verify unchanged 2026.
No future candle, year-label or intraminute path may enter classifier features.
NO forced daily trades; one entry maximum per IST day and exit before midnight.
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from numba import njit
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score, brier_score_loss
import research_btc_daily_200tp_100sl_1x_20261121 as core

OUT=Path("analysis/btc_ml_first_touch_200_100_1x_20261121")
BASE_INITIAL_NAV=10000.0
TRAIN_END="2025-06-30"
CAL_START="2025-07-01"
CAL_END="2025-12-31"
VAL_END="2026-06-30"
FULL_END="2026-10-30"
THRESHOLDS=(0.55,0.60,0.65,0.70,0.75,0.80,0.85)
MIN_CAL_TRADES=40
MIN_POSITIVE_CAL_MONTHS=4
MIN_CONFIDENCE_MARGIN=0.025
MODEL_SETTINGS=dict(max_iter=125,learning_rate=0.04,max_leaf_nodes=15,
  min_samples_leaf=180,l2_regularization=4.0,early_stopping=False,random_state=20261121)

@njit(cache=True)
def label_every_candidate(k_arr,day_end,op,hi,lo,cl):
    """Independent true 1m target-first labels for every 15m candidate, both sides."""
    n=len(k_arr)
    outcome=np.empty((n,2),np.int8)
    chart_points=np.empty((n,2),np.float64)
    net_points=np.empty((n,2),np.float64)
    duration=np.empty((n,2),np.int16)
    for ii in range(n):
        k=k_arr[ii]
        ent=op[k]
        final=min(k+240-1, day_end[k])
        for dd in range(2):
            side=1. if dd==0 else -1.
            goal=ent+side*200.0
            stop=ent-side*100.0
            closep=cl[final]
            reason=0  # 1=TP, -1=SL, 0=timeout
            exj=final
            for j in range(k,final+1):
                stop_hit=lo[j]<=stop if side==1 else hi[j]>=stop
                tp_hit=hi[j]>=goal if side==1 else lo[j]<=goal
                if stop_hit:
                    closep=min(stop,op[j]) if side==1 else max(stop,op[j])
                    reason=-1
                    exj=j
                    break
                if tp_hit:
                    closep=goal
                    reason=1
                    exj=j
                    break
            entryfill=ent+side*5.0
            exitfill=closep-side*5.0
            gross=side*(closep-ent)
            feepts=0.00059*(entryfill+exitfill)
            net=gross-2*5.0-feepts
            outcome[ii,dd]=reason
            chart_points[ii,dd]=gross
            net_points[ii,dd]=net
            duration[ii,dd]=exj-k+1
    return outcome,chart_points,net_points,duration

def wilder(x,n=14):
    return x.ewm(alpha=1/n,min_periods=n,adjust=False).mean()

def features_events(f):
    b=f.resample("15min",label="left",closed="left").agg(
       open=("open","first"),high=("high","max"),low=("low","min"),
       close=("close","last"),volume=("volume","sum"),n=("close","size"))
    h=f.resample("1h",label="right",closed="left").agg(
       open=("open","first"),high=("high","max"),low=("low","min"),
       close=("close","last"),volume=("volume","sum"),n=("close","size"))
    good15=b.n.eq(15)
    valid15=good15.rolling(50,min_periods=50).sum().eq(50)
    goodh=h.n.eq(60)
    validh=goodh.rolling(55,min_periods=55).sum().eq(55)
    c=b.close.where(good15)
    v=b.volume.where(good15)
    hi=b.high.where(good15);lo=b.low.where(good15)
    hc=h.close.where(goodh);hh=h.high.where(goodh);hl=h.low.where(goodh)
    eps=1e-9
    prev=hc.shift(1)
    htr=pd.concat([hh-hl,(hh-prev).abs(),(hl-prev).abs()],axis=1).max(axis=1)
    hatr=wilder(htr)
    h20=hc.ewm(span=20,min_periods=50,adjust=False).mean()
    h50=hc.ewm(span=50,min_periods=50,adjust=False).mean()
    u=hh.diff();d=-hl.diff()
    updm=u.where((u>d)&(u>0),0.)
    downdm=d.where((d>u)&(d>0),0.)
    pdi=100*wilder(updm)/hatr.replace(0,np.nan)
    mdi=100*wilder(downdm)/hatr.replace(0,np.nan)
    adx=wilder(100*(pdi-mdi).abs()/(pdi+mdi).replace(0,np.nan))
    hevent=pd.DataFrame({
        "h1_adx":adx.where(validh),
        "h1_ema_spread_atr":((h20-h50)/hatr.replace(0,np.nan)).where(validh),
        "h1_close_ema_atr":((hc-h20)/hatr.replace(0,np.nan)).where(validh),
        "h1_roc1":((hc/hc.shift(1)-1)*100).where(validh),
        "h1_roc4":((hc/hc.shift(4)-1)*100).where(validh),
        "h1_roc12":((hc/hc.shift(12)-1)*100).where(validh),
        "h1_atr_ratio":(hatr/hc).where(validh),
        "h1_range_atr":((hh-hl)/hatr.replace(0,np.nan)).where(validh),
    })
    end=b.index+pd.Timedelta(minutes=15)
    aligned=hevent.reindex(end,method="ffill")
    diff=c.diff()
    up=wilder(diff.clip(lower=0)); dn=wilder(-diff.clip(upper=0))
    rsi=100-100/(1+up/dn.replace(0,np.nan))
    shortup=wilder(diff.clip(lower=0),2)
    shortdn=wilder(-diff.clip(upper=0),2)
    rsi2=100-100/(1+shortup/shortdn.replace(0,np.nan))
    c15=c.ewm(span=20,min_periods=20,adjust=False).mean()
    c50=c.ewm(span=50,min_periods=50,adjust=False).mean()
    prevc=c.shift(1)
    atr=wilder(pd.concat([hi-lo,(hi-prevc).abs(),(lo-prevc).abs()],axis=1).max(axis=1))
    unit=atr.replace(0,np.nan)
    mid=c.rolling(20,min_periods=20).mean()
    sd=c.rolling(20,min_periods=20).std().replace(0,np.nan)
    cbody=c-b.open
    range_now=hi-lo
    vol20=v.rolling(20,min_periods=20).mean().shift(1)
    volratio=v/vol20.replace(0,np.nan)
    prevhigh=hi.rolling(8,min_periods=8).max().shift(1)
    prevlow=lo.rolling(8,min_periods=8).min().shift(1)
    candleposition=(c-lo)/range_now.replace(0,np.nan)
    recentret=c.pct_change(fill_method=None)
    ist=end.tz_convert("Asia/Kolkata")
    hour=ist.hour.to_numpy(float)+ist.minute.to_numpy(float)/60.
    weekday=ist.dayofweek.to_numpy(float)
    feat=pd.DataFrame(index=b.index)
    for name,vec in {
       "price_100k":c/100000.,
       "atr15_relative":atr/c,
       "atr15_in_points":atr/200.,
       "rsi14":rsi/100.,
       "rsi2":rsi2/100.,
       "close_vs_ema20_atr":(c-c15)/unit,
       "close_vs_ema50_atr":(c-c50)/unit,
       "ema20_vs_ema50_atr":(c15-c50)/unit,
       "ema20_slope_4_atr":(c15-c15.shift(4))/unit,
       "bollinger_z":(c-mid)/sd,
       "volume_ratio":volratio,
       "volume_ratio4":(v.rolling(4,min_periods=4).sum()/
          (4*vol20.replace(0,np.nan))),
       "candle_body_atr":cbody/unit,
       "candle_range_atr":range_now/unit,
       "upper_wick_atr":(hi-pd.concat([c,b.open],axis=1).max(axis=1))/unit,
       "lower_wick_atr":(pd.concat([c,b.open],axis=1).min(axis=1)-lo)/unit,
       "candle_close_position":candleposition,
       "breakup_8_atr":(c-prevhigh)/unit,
       "breakdown_8_atr":(prevlow-c)/unit,
       "return15_atr":(c-c.shift(1))/unit,
       "return30_atr":(c-c.shift(2))/unit,
       "return60_atr":(c-c.shift(4))/unit,
       "return240_atr":(c-c.shift(16))/unit,
       "realvol_8":recentret.rolling(8,min_periods=8).std(),
       "realvol_24":recentret.rolling(24,min_periods=24).std(),
       "hour_sin":np.sin(2*np.pi*hour/24.),
       "hour_cos":np.cos(2*np.pi*hour/24.),
       "day_sin":np.sin(2*np.pi*weekday/7.),
       "day_cos":np.cos(2*np.pi*weekday/7.),
    }.items():
        feat[name]=np.asarray(vec,dtype=float)
    for name in hevent.columns:
        feat[name]=aligned[name].to_numpy(float)
    # Time of *the entry* (15m bar ends), never before its complete close.
    ts=f.time.to_numpy(np.int64)
    endsec=end.to_numpy(dtype="datetime64[s]").astype(np.int64)
    i=np.searchsorted(ts,endsec,side="left")
    goodi=np.minimum(i,len(ts)-1)
    exists=(i<len(ts))&(ts[goodi]==endsec)
    ist_dates=np.asarray(ist.strftime("%Y-%m-%d"))
    usable=(valid15.to_numpy(bool)&np.isfinite(aligned.h1_adx.to_numpy(float))&
       exists&(ist_dates>=core.FULL_DAY_START)&(ist_dates<=FULL_END))
    # Select rows where every model feature is defined and finite.
    finite=np.isfinite(feat.to_numpy(float)).all(axis=1)
    usable=usable&finite
    if not usable.any():
        raise AssertionError("No valid 15m events after feature engineering")
    sig=np.flatnonzero(usable)
    times=ist_dates[sig]
    events=i[sig].astype(np.int32)
    x=feat.to_numpy(dtype=np.float32)[sig]
    columns=list(feat.columns)
    return events,times,x,columns,{"minute_rows":len(f),
        "complete_15m_bars":int(good15.sum()),"complete_1h_bars":int(goodh.sum()),
        "valid_candidate_event_count":int(len(sig)),
        "valid_long_short_candidate_rows":int(2*len(sig)),
        "first_entry_date":str(times[0]),"last_entry_date":str(times[-1]),
        "n_input_features":len(columns),"feature_names":columns,
        "first_signal_utc":str(end[sig[0]]),"last_signal_utc":str(end[sig[-1]])}

def candidate_rows(events,dates,x):
    # Single common training/evaluation frame; each time has long & short
    # independent labels. Direction signed features are never based on future OHLC.
    n=len(events)
    side=np.tile(np.array([1.,-1.],dtype=np.float32),n)
    feat=np.repeat(x,2,axis=0)
    signed_cols=[
       "close_vs_ema20_atr","close_vs_ema50_atr","ema20_vs_ema50_atr",
       "ema20_slope_4_atr","candle_body_atr","return15_atr","return30_atr",
       "return60_atr","return240_atr","h1_ema_spread_atr",
       "h1_close_ema_atr","h1_roc1","h1_roc4","h1_roc12"
    ]
    return side,feat,signed_cols

def predict_rows(events,dates,x,columns,label):
    side,frame,signed_cols=candidate_rows(events,dates,x)
    # Direction features let same model learn continuation and reversal,
    # with the market state represented symmetrically for long/short.
    newcols=list(columns)
    newcols.append("candidate_side")
    parts=[frame,side.reshape(-1,1)]
    for name in signed_cols:
        idx=columns.index(name)
        parts.append((frame[:,idx]*side).reshape(-1,1))
        newcols.append("dir_"+name)
    final=np.column_stack(parts).astype(np.float32)
    labels=(label.reshape(-1)==1).astype(np.int8)
    return final,labels,newcols

def daily_ends(f):
    d=f.index.tz_convert("Asia/Kolkata")
    ids=(d.year.to_numpy()*10000+d.month.to_numpy()*100+d.day.to_numpy())
    ends=np.empty(len(ids),dtype=np.int32)
    change=np.r_[0,np.flatnonzero(ids[1:]!=ids[:-1])+1,len(ids)]
    for a,b in zip(change[:-1],change[1:]):
        ends[a:b]=int(b-1)
    return ends

def pick_daily(events,dates,x,prob,chart_points,net_points,exit_kind,hold,
               threshold,period_start,period_end,valid_dates):
    """Only signal scores in chronological order; first gated event each IST day."""
    out=[]
    used=set()
    for event_ix,(k,date) in enumerate(zip(events,dates)):
        if date<period_start or date>period_end or date in used:
            continue
        # Score both LONG and SHORT now and take higher only if profitable
        # *conditional* chance exceeds assumed fee-aware stop/target BE rate.
        p_long=float(prob[event_ix*2])
        p_short=float(prob[event_ix*2+1])
        dd=0 if p_long>=p_short else 1
        p=max(p_long,p_short)
        entry=float(x[event_ix,0])*100000.
        # precise entry price comes from original f.open[k], passed separately below
        price=float(valid_dates[event_ix])
        cost_est=2*core.SLIP_POINTS+2*core.TAKER_FEE_WITH_GST*price
        breakeven=(core.SL+cost_est)/(core.TP+core.SL)
        gate=max(float(threshold),breakeven+MIN_CONFIDENCE_MARGIN)
        if p<gate:
            continue
        used.add(date)
        outcome=int(exit_kind[event_ix,dd])
        ppoints=float(net_points[event_ix,dd])
        raw=float(chart_points[event_ix,dd])
        out.append({"date_ist":str(date),"month_ist":str(date)[:7],
            "entry_minute_index":int(k),"side":"LONG" if dd==0 else "SHORT",
            "predicted_tp_first_probability":p,
            "required_probability_gate":gate,"model_threshold":threshold,
            "cost_adjusted_breakeven_probability":breakeven,
            "chart_price_entry":price,
            "outcome":"TP" if outcome==1 else ("SL" if outcome==-1 else "TIME"),
            "gross_chart_points":raw,"net_points":ppoints,
            "holding_minutes":int(hold[event_ix,dd])})
    return pd.DataFrame(out)

def calc_metrics(trades,period_start,period_end):
    start=pd.Timestamp(period_start,tz="Asia/Kolkata")
    end=pd.Timestamp(period_end,tz="Asia/Kolkata")
    all_days=pd.date_range(start,end,freq="D")
    monthcount=len(all_days.to_period("M").unique()) if False else len(pd.PeriodIndex(
         [x.strftime("%Y-%m") for x in all_days],freq="M").unique())
    if trades.empty:
        return {"entries":0,"tp_count":0,"sl_count":0,"timeout_count":0,
            "net_wins":0,"net_losses":0,
            "positive_days":0,"negative_days":0,"no_trade_days":len(all_days),
            "net_win_pct":0,"tp_first_pct":0,"mean_net_points":None,
            "std_net_points":None,"mean_net_points_lower95":None,
            "net_profit_factor":None,"months_positive":0,
            "months_negative":0,"months_flat":monthcount,
            "net_account_return_pct":0.,"ending_nav":BASE_INITIAL_NAV,
            "drawdown_pct":0.,"monthlies":[]}
    cur=BASE_INITIAL_NAV
    account_pnls=[]
    account_pct=[]
    balances=[cur]
    for v in trades.itertuples():
        qty=cur/v.chart_price_entry
        net=qty*v.net_points
        if cur+net<=0: raise RuntimeError("equity depleted")
        account_pnls.append(net)
        account_pct.append(100*net/cur)
        cur+=net
        balances.append(cur)
    r=trades.copy()
    r["net_usd"]=account_pnls
    r["nav_before"]=balances[:-1]
    r["nav_after"]=balances[1:]
    r["daily_pct"]=account_pct
    pos=r.net_usd>0
    profit=float(r.loc[pos,"net_usd"].sum())
    losses=float(-r.loc[r.net_usd<0,"net_usd"].sum())
    dates_set=set(r.date_ist)
    days=pd.DataFrame({"date_ist":all_days.strftime("%Y-%m-%d")})
    days["month_ist"]=days.date_ist.str[:7]
    vals=r.set_index("date_ist")["daily_pct"]
    if vals.index.duplicated().any():raise AssertionError("More than one per IST day")
    days["pct"]=days.date_ist.map(vals).fillna(0.)
    month=days.groupby("month_ist",sort=True).agg(
        calendar_days=("date_ist","size"),
        trades=("pct",lambda x:int((x!=0).sum())),
        net_profit_days=("pct",lambda x:int((x>0).sum())),
        net_loss_days=("pct",lambda x:int((x<0).sum())),
        no_trade_days=("pct",lambda x:int((x==0).sum())),
        compounded_net_pct=("pct",lambda x:float(100*(np.prod(1+x.to_numpy(float)/100)-1)))
    ).reset_index()
    monthly=month.to_dict("records")
    net_points=r.net_points.to_numpy(float)
    n=len(r)
    ret={
       "entries":n,
       "tp_count":int((r.outcome=="TP").sum()),
       "sl_count":int((r.outcome=="SL").sum()),
       "timeout_count":int((r.outcome=="TIME").sum()),
       "net_wins":int(pos.sum()),"net_losses":int((r.net_usd<0).sum()),
       "positive_days":int((days.pct>0).sum()),
       "negative_days":int((days.pct<0).sum()),
       "no_trade_days":int((days.pct==0).sum()),
       "net_win_pct":round(float(100*pos.mean()),3),
       "tp_first_pct":round(float(100*(r.outcome=="TP").mean()),3),
       "mean_net_points":round(float(net_points.mean()),3),
       "std_net_points":round(float(net_points.std(ddof=1)),3) if n>1 else None,
       "mean_net_points_lower95":round(float(net_points.mean()-1.96*net_points.std(ddof=1)/np.sqrt(n)),3) if n>1 else None,
       "net_profit_factor":round(profit/losses,4) if losses>0 else None,
       "months_positive":int((month.compounded_net_pct>1e-9).sum()),
       "months_negative":int((month.compounded_net_pct< -1e-9).sum()),
       "months_flat":int((abs(month.compounded_net_pct)<=1e-9).sum()),
       "net_account_return_pct":round(100*(cur/BASE_INITIAL_NAV-1),4),
       "ending_nav":round(cur,2),
       "drawdown_pct":round(100*(1-np.asarray(balances)/np.maximum.accumulate(balances)).max(),4),
       "monthlies":monthly}
    # Equity PnL should equal product of daily PnL
    comp=100*(np.prod(1+days.pct.to_numpy(float)/100)-1)
    if abs(comp-ret["net_account_return_pct"])>0.001:
        raise AssertionError("Compounded daily NAV mismatch")
    return ret

def run():
    OUT.mkdir(parents=True,exist_ok=True)
    f,quality=core.load_1m()
    ix,dates,feature,cols,feature_q=features_events(f)
    ends=daily_ends(f)
    o=f.open.to_numpy(float);h=f.high.to_numpy(float)
    l=f.low.to_numpy(float);c=f.close.to_numpy(float)
    reason,chart,net,hold=label_every_candidate(ix,ends,o,h,l,c)
    X,y,colnames=predict_rows(ix,dates,feature,cols,reason)
    train_event=(dates<="2025-06-30")
    train_rows=np.repeat(train_event,2)
    if train_rows.sum()<30000:
        raise AssertionError("Unexpected low training rows")
    model=HistGradientBoostingClassifier(**MODEL_SETTINGS)
    model.fit(X[train_rows],y[train_rows])
    # No held-out feature normalization. No model fitting on 2025 H2 or 2026.
    proba=model.predict_proba(X)[:,1]
    # Economic selection uses actual f.open for fee price, not 15m closing quote.
    entry_actual=o[ix]
    probability_diagnostics={}
    for name,(sdate,edate) in {"2025_CAL":(CAL_START,CAL_END),
            "2026_H1_SEEN":("2026-01-01",VAL_END),
            "2026_H2_SEEN":("2026-07-01",FULL_END)}.items():
        mask=(dates>=sdate)&(dates<=edate)
        cand_prob=np.maximum(proba[::2],proba[1::2])[mask]
        prices=entry_actual[mask]
        be=(core.SL+2*core.SLIP_POINTS+2*core.TAKER_FEE_WITH_GST*prices)/\
           (core.SL+core.TP)
        fee_aware=be+MIN_CONFIDENCE_MARGIN
        probability_diagnostics[name]={"candidate_15m_events":int(mask.sum()),
          "max_model_probability":round(float(np.max(cand_prob)),5),
          "p95_model_probability":round(float(np.percentile(cand_prob,95)),5),
          "p99_model_probability":round(float(np.percentile(cand_prob,99)),5),
          "p50_fee_aware_required_probability":round(float(np.median(fee_aware)),5),
          "number_qualifying_fee_aware_before_daily_cap":int((cand_prob>=fee_aware).sum())}
    periods={
       "2025_CAL":(CAL_START,CAL_END),
       "2026_H1_SEEN":("2026-01-01",VAL_END),
       "2026_H2_SEEN":("2026-07-01",FULL_END),
       "2026_ALL_SEEN":("2026-01-01",FULL_END)}
    gates=[]
    per_gate={}
    for threshold in THRESHOLDS:
        tag=f"p_{threshold:.2f}"
        row={"gate":tag,"raw_threshold":threshold}
        periods_ledger={}
        periods_metrics={}
        for name,(start,end) in periods.items():
            ledger=pick_daily(ix,dates,feature,proba,chart,net,reason,hold,
               threshold,start,end,entry_actual)
            periods_ledger[name]=ledger
            met=calc_metrics(ledger,start,end)
            periods_metrics[name]=met
            row.update({name+"_"+k:v for k,v in met.items() if k!="monthlies"})
        selected_metric=periods_metrics["2025_CAL"]
        cal_ok=(selected_metric["entries"]>=MIN_CAL_TRADES
          and selected_metric["months_positive"]>=MIN_POSITIVE_CAL_MONTHS
          and selected_metric["net_profit_factor"] is not None
          and selected_metric["net_profit_factor"]>1.0
          and selected_metric["net_account_return_pct"]>0.
          and selected_metric["mean_net_points_lower95"] is not None
          and selected_metric["mean_net_points_lower95"]>0)
        row["qualifies_on_2025_calibration"]=bool(cal_ok)
        per_gate[tag]=(periods_ledger,periods_metrics)
        gates.append(row)
        print("GATE_COMPLETE",tag,"eligible_2025",cal_ok,
           "CAL",selected_metric["entries"],
           selected_metric["net_account_return_pct"],
           "2026H1",periods_metrics["2026_H1_SEEN"]["net_account_return_pct"],
           "2026H2",periods_metrics["2026_H2_SEEN"]["net_account_return_pct"],
           flush=True)
    results=pd.DataFrame(gates)
    eligible=results[results.qualifies_on_2025_calibration]
    # Predefined 2025 calibration selection metric only, never 2026 columns.
    approved=None
    if not eligible.empty:
        eligible=eligible.sort_values(
            ["2025_CAL_mean_net_points_lower95","2025_CAL_entries"],
            ascending=[False,False],kind="stable")
        approved=str(eligible.iloc[0].gate)
    # Exploratory (NOT approved) 2025-calibration leader, even if negative.
    ranked=results.sort_values(
          ["2025_CAL_mean_net_points_lower95","2025_CAL_entries"],
          ascending=[False,False],na_position="last",kind="stable")
    exploratory=str(ranked.iloc[0].gate)
    tag=approved or exploratory
    ledgers,met=per_gate[tag]
    results.to_csv(OUT/"all_probability_gates.csv",index=False)
    for p,ledger in ledgers.items():
        ledger.to_csv(OUT/f"{p}_leader_ledger.csv",index=False)
    months=pd.DataFrame([{"period":p,**rec} for p,m in met.items()
             for rec in m["monthlies"]])
    months.to_csv(OUT/"leader_monthly.csv",index=False)
    result={
       "decision":"QUALIFIED_2025_CALIBRATION_NOT_FORWARD_VALIDATED" if approved
            else "NO_PROFITABLE_2025_CALIBRATION_GATE",
       "approved_2025_only_gate":approved,
       "exploratory_2025_calibration_leader_not_approved":None if approved else exploratory,
       "gate_shown_for_reporting":tag,
       "training_period":"2025-01-02 through 2025-06-30 (model fit only)",
       "calibration_period":"2025-07-01 through 2025-12-31 (gate selection only)",
       "2026_history":"Previously researched and thus not untouched independent OOS",
       "source":quality,
       "feature":feature_q,
       "model":MODEL_SETTINGS,
       "class_balance_train":round(float(y[train_rows].mean()),4),
       "class_balance_cal":round(float(y[np.repeat((dates>=CAL_START)&(dates<=CAL_END),2)].mean()),4),
       "probability_diagnostics":probability_diagnostics,
       "features":colnames,
       "probability_thresholds":list(THRESHOLDS),
       "additional_fee_gate_margin":MIN_CONFIDENCE_MARGIN,
       "gate_acceptance":{"min_cal_trades":MIN_CAL_TRADES,
          "min_positive_months_of_six":MIN_POSITIVE_CAL_MONTHS,
          "positive_net_NAV":True,"net_profit_factor_gt":1,
          "net_points_lower95_gt":0},
       "gate_summary":gates,
       "leader_period_metrics":met,
       "caveats":[
          "Hourly trend inputs are ONLY completed hours, not forming hours",
          "Each 15m signal enters the next raw 1m OPEN, fully fee-adjusted net returns; stop first on same minute",
          "Model trained on two competing LONG/SHORT candidate outcomes from same timestamps; overlapping 4h labels imply correlation",
          "1× NAV notional; one first passing trade per IST day, 4h timeout or flatten by midnight",
          "Economic probability threshold uses TP/SL and estimated fees at actual entry open plus 2.5 percentage point safety margin",
          "No funding, actual spread, orderbook, maker queue/partial fills, exchange rounding or price-mark liquidation",
          "Predictive classifier probabilities may be miscalibrated, especially in 2026",
          "Historical 2026 already researched in this repository; not a pristine holdout",
          "Jan1 2025 and Oct31 2026 IST are missing full-day coverage; no claim 22 fully complete months",
          "Zero profitable gate means no credible deployment candidate, not a reason to re-tune 2026 thresholds",
          "Gross 200 BTC price points differ from net account profitability",
       ]}
    (OUT/"summary.json").write_text(json.dumps(result,indent=2,default=str)+"\n")
    compact=["gate","qualifies_on_2025_calibration",
       "2025_CAL_entries","2025_CAL_tp_first_pct","2025_CAL_net_win_pct",
       "2025_CAL_mean_net_points","2025_CAL_mean_net_points_lower95",
       "2025_CAL_net_account_return_pct","2025_CAL_months_positive",
       "2026_H1_SEEN_entries","2026_H1_SEEN_net_account_return_pct",
       "2026_H2_SEEN_entries","2026_H2_SEEN_net_account_return_pct"]
    report=[
        "# BTCUSD 1× +200/−100 — chronological ML first-touch probability",
        "",
        "**Decision: "+result["decision"]+"**",
        "",
        "## Strict chronological protocol",
        "",
        "- Train HistGradientBoostingClassifier on Jan–Jun 2025 ONLY, using completed 15m and completed prior 1h features. Both sides labelled separately from native 1m first touch.",
        "- Select a predetermined probability threshold exclusively on Jul–Dec 2025 calibration, only if >=40 independent trades, >=4 positive months, net profit factor >1, positive compounded NAV and mean net point 95%-style lower bound >0.",
        "- Apply fee-aware minimum break-even threshold +2.5 percentage points per entry, subject to strict threshold.",
        "- 1× current net-account notional, $10,000 start; +200 BTC chart points / −100 raw chart points, 4h timeout or IST day close.",
        "- Actual execution replay on 1-minute OHLC, stop wins target ambiguity. Taker fee 0.05% each side, GST 18%, adverse slip 5 points each side.",
        "- 2026 H1 and H2 are chronological checks never seen by this model, but globally **historically researched** in this repository; no truly fresh OOS claims.",
        "- Max one opened trade per IST day; zero-trade days count against daily income target.",
        "",
        "## Fixed probability-gate comparison",
        "",
        results[compact].to_markdown(index=False),
        "",
        "## Model confidence versus cost-adjusted required probability",
        "",
        pd.DataFrame([{"period":k,**v} for k,v in probability_diagnostics.items()]).to_markdown(index=False),
        "",
        "## Gate used in the diagnostic account replay",
        "",
        "Approved gate: "+str(approved),
        "",
        "Exploratory unqualified gate, if no approval: "+str(exploratory),
        "",
        "## Period account audits",
        "",
        pd.DataFrame([{k:v for k,v in m.items() if k!="monthlies"}|{"period":name}
           for name,m in met.items()]).to_markdown(index=False),
        "",
        "## Monthly account results for above diagnostic gate",
        "",
        months.to_markdown(index=False),
        "",
        "## Source integrity",
        "",
        "Source 1m rows: "+str(quality["native_1m_rows"]),
        "",
        "## Caveats",
        ""
    ]+["- "+c for c in result["caveats"]]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")
    print("MODEL_COMPLETE",json.dumps({
      "decision":result["decision"],"training_candidates":int(train_rows.sum()),
      "candidate_15m_events":len(ix),"class_balance_train":result["class_balance_train"],
      "approved_gate":approved,"exploratory_gate":exploratory,
      "leader_period":{k:{a:b for a,b in v.items() if a!="monthlies"} for k,v in met.items()}
      },default=str),flush=True)
    print("GATES\n"+results[compact].to_string(index=False),flush=True)

if __name__=="__main__":
    run()
