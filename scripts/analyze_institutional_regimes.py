#!/usr/bin/env python3
"""Delta India BTCUSD: evidence-led OHLCV/OI/funding/mark regime discovery.

All primary signals use fully closed five-minute periods. The following 1m
open is the earliest possible entry. Historical order-book, individual-trade
and liquidation data are NOT assumed. OI is not a trader-direction label.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd

BASE=Path("data/delta_india/BTCUSD")
OUT=Path("analysis/institutional_regime_research")
TRAIN_END=pd.Timestamp("2026-01-01",tz="UTC")
VAL_END=pd.Timestamp("2026-07-01",tz="UTC")
FEE=0.0005*1.18
SLIP=5.0
EXIT_RULES={
    "tp300_sl250_2h":(300.,250.,120),
    "tp500_sl350_4h":(500.,350.,240),
    "tp1000_sl500_8h":(1000.,500.,480),
    "tp1500_sl650_8h":(1500.,650.,480),
    "time2h_sl400":(None,400.,120),
    "time4h_sl600":(None,600.,240)
}
MIN_GAP_BARS=24  # Signals of same strategy at least two hours apart
PRESELECT_MIN_TRAIN=45
PRESELECT_MIN_VAL=20
PRESELECT_MIN_HOLD=10

def load_folder(folder,pattern):
    fs=sorted(folder.glob(pattern))
    if not fs:raise RuntimeError(f"No input monthly partitions at {folder}")
    frames=[]
    for f in fs:
        cols=["time","open","high","low","close","volume"]
        a=pd.read_csv(f,compression="gzip")
        missing=set(cols).difference(a.columns)
        if missing:raise RuntimeError(f"Missing columns {missing}: {f}")
        a["time"]=pd.to_datetime(a.time.astype("int64"),unit="s",utc=True)
        frames.append(a[cols])
    df=pd.concat(frames,ignore_index=True).set_index("time").sort_index()
    if df.index.has_duplicates:raise RuntimeError(f"Duplicate timestamps in {folder}")
    if df[["open","high","low","close"]].isna().any().any():
        raise RuntimeError(f"Null OHLC data in {folder}")
    return df,len(fs)

def inputs():
    futures,fc=load_folder(BASE/"1m","20??-??.csv.gz")
    mark,mc=load_folder(BASE/"institutional/history/mark_1m","20??-??.csv.gz")
    oi,oc=load_folder(BASE/"institutional/history/open_interest_5m","20??-??.csv.gz")
    funding,uc=load_folder(BASE/"institutional/history/funding_1h","20??-??.csv.gz")
    if not futures.index.equals(mark.index):raise RuntimeError("Mark/futures 1m timestamps not aligned")
    for x,step,name in [(futures,60,"futures"),(oi,300,"OI"),(funding,3600,"funding")]:
        if not x.index.to_series().diff().iloc[1:].eq(pd.Timedelta(seconds=step)).all():
            raise RuntimeError(f"{name} series has timestamp gaps")
    return futures,mark,oi,funding,dict(
       future_minutes=len(futures),mark_minutes=len(mark),oi_5m=len(oi),
       funding_hours=len(funding),monthly_partitions=dict(
           futures=fc,mark=mc,oi=oc,funding=uc),
       first_utc=str(futures.index.min()),last_utc=str(futures.index.max()),
       zero_volume_futures_minutes=int((futures.volume==0).sum()))

def features(fut,mark,oi,funding):
    counts=fut.close.resample("5min").count()
    x=fut.resample("5min").agg(
      open=("open","first"),high=("high","max"),low=("low","min"),
      close=("close","last"),volume=("volume","sum"))
    if not counts.eq(5).all():raise RuntimeError("Incomplete 5min bars")
    x["mark_close"]=mark.close.resample("5min").last().reindex(x.index)
    x["oi_close"]=oi.close.reindex(x.index)
    if x[["mark_close","oi_close"]].isna().any().any():
        raise RuntimeError("Misaligned mark or open interest")
    if (x.oi_close<=0).any():raise RuntimeError("Nonpositive open interest, cannot compute changes")
    # Funding rate candle at H is NOT available until H+60m.
    completed_funding=funding.close.copy()
    completed_funding.index=completed_funding.index+pd.Timedelta(hours=1)
    # Align to *signal-known* time: 5m bar end.
    known=x.index+pd.Timedelta(minutes=5)
    x["last_funding"]=completed_funding.reindex(known,method="ffill").to_numpy()
    # Funding quantiles reference trailing COMPLETED hourly candles only.
    h=funding.close
    past90=h.rolling(24*14,min_periods=24*7).quantile(.90).shift(1)
    past10=h.rolling(24*14,min_periods=24*7).quantile(.10).shift(1)
    past90.index+=pd.Timedelta(hours=1)
    past10.index+=pd.Timedelta(hours=1)
    x["funding_q90"]=past90.reindex(known,method="ffill").to_numpy()
    x["funding_q10"]=past10.reindex(known,method="ffill").to_numpy()
    # 5m OI delta over last 30 minutes (known at end of current 5m).
    x["oi_delta30_pct"]=100*x.oi_close.pct_change(6,fill_method=None)
    x["oi_delta1h_pct"]=100*x.oi_close.pct_change(12,fill_method=None)
    trend=x["oi_delta30_pct"]
    baseline=trend.rolling(288,min_periods=144)
    x["oi_z30"]=(trend-baseline.mean().shift(1))/baseline.std().shift(1).replace(0,np.nan)
    x["basis_bp"]=10000*(x.close-x.mark_close)/x.mark_close.replace(0,np.nan)
    basis=x.basis_bp.rolling(288,min_periods=144)
    x["basis_z"]=(x.basis_bp-basis.mean().shift(1))/basis.std().shift(1).replace(0,np.nan)
    prevclose=x.close.shift()
    x["tr"]=pd.concat([
        x.high-x.low,(x.high-prevclose).abs(),(x.low-prevclose).abs()],axis=1).max(axis=1)
    x["atr"]=x.tr.rolling(24,min_periods=24).mean()
    x["range_ratio"]=(x.high-x.low)/(x.high-x.low).rolling(24,min_periods=24).median().shift(1).replace(0,np.nan)
    x["vol_ratio"]=x.volume/x.volume.rolling(24,min_periods=24).mean().shift(1).replace(0,np.nan)
    x["prev1h_high"]=x.high.rolling(12,min_periods=12).max().shift(1)
    x["prev1h_low"]=x.low.rolling(12,min_periods=12).min().shift(1)
    x["prev2h_high"]=x.high.rolling(24,min_periods=24).max().shift(1)
    x["prev2h_low"]=x.low.rolling(24,min_periods=24).min().shift(1)
    x["prev_price_close"]=x.close.shift()
    x["px_delta15"]=x.close-x.close.shift(3)
    x["px_delta30"]=x.close-x.close.shift(6)
    ny=x.index.tz_convert("America/New_York")
    dates=pd.Series([str(t) for t in ny.date],index=x.index)
    pdlevels=x.groupby(dates,sort=True).agg(prevday_high=("high","max"),prevday_low=("low","min")).shift(1)
    x["pd_high"]=dates.map(pdlevels.prevday_high)
    x["pd_low"]=dates.map(pdlevels.prevday_low)
    x["ny_day"]=dates
    minutes=ny.hour*60+ny.minute
    x["session"]=np.select([
       (minutes>=1140)|(minutes<180),
       (minutes>=180)&(minutes<570),
       (minutes>=570)&(minutes<960)],
       ["Asia_evening","London_preUS","US_regular"],default="NY_late")
    x["period"]=np.select([x.index<TRAIN_END,x.index<VAL_END],
         ["train","validation"],default="holdout")
    return x

def conditions(x):
    c=x.close;o=x.open;h=x.high;l=x.low
    bull=c>o;bear=c<o
    strong=(x.range_ratio>=1.45)&(x.vol_ratio>=1.15)
    oi_add=(x.oi_z30>=0.75)&(x.oi_delta30_pct>0)
    oi_reduce=(x.oi_z30<=-0.75)&(x.oi_delta30_pct<0)
    up=(x.px_delta30>0)&(c>x.prev_price_close)
    down=(x.px_delta30<0)&(c<x.prev_price_close)
    br_up=(c>x.prev2h_high)&bull&strong
    br_dn=(c<x.prev2h_low)&bear&strong
    sweep_hi=(h>x.prev2h_high)&(c<x.prev2h_high)
    sweep_lo=(l<x.prev2h_low)&(c>x.prev2h_low)
    pd_sweep_hi=(h>x.pd_high)&(c<x.pd_high)
    pd_sweep_lo=(l<x.pd_low)&(c>x.pd_low)
    near_break=(h>x.prev1h_high)&(c>x.prev1h_high)
    near_bear=(l<x.prev1h_low)&(c<x.prev1h_low)
    basis_stretched_hi=(x.basis_z>=1.5)
    basis_stretched_lo=(x.basis_z<=-1.5)
    funding_pos=(x.last_funding>=x.funding_q90)&(x.last_funding>0)
    funding_neg=(x.last_funding<=x.funding_q10)&(x.last_funding<0)
    # These are transparent market proxies, NOT verified institutional behavior.
    candidates={
      "oi_add_price_rise_breakout":(br_up&oi_add,False),
      "oi_add_price_fall_breakdown":(False,br_dn&oi_add),
      "oi_drop_up_squeeze_proxy":(br_up&oi_reduce,False),
      "oi_drop_down_squeeze_proxy":(False,br_dn&oi_reduce),
      "oi_add_bull_trend":(strong&up&oi_add,False),
      "oi_add_bear_trend":(False,strong&down&oi_add),
      "oi_drop_bull_trend":(strong&up&oi_reduce,False),
      "oi_drop_bear_trend":(False,strong&down&oi_reduce),
      "twohour_sweep_fade_oi_add":(sweep_lo&oi_add,sweep_hi&oi_add),
      "twohour_sweep_fade_oi_drop":(sweep_lo&oi_reduce,sweep_hi&oi_reduce),
      "prevday_sweep_fade_oi_add":(pd_sweep_lo&oi_add,pd_sweep_hi&oi_add),
      "prevday_sweep_fade_oi_drop":(pd_sweep_lo&oi_reduce,pd_sweep_hi&oi_reduce),
      "high_basis_sweep_fade":(False,sweep_hi&basis_stretched_hi),
      "low_basis_sweep_fade":(sweep_lo&basis_stretched_lo,False),
      "funding_crowded_long_fade":(False,funding_pos&sweep_hi),
      "funding_crowded_short_fade":(funding_neg&sweep_lo,False),
      "oi_add_break_1h":(near_break&bull&oi_add,near_bear&bear&oi_add),
      "oi_drop_break_1h":(near_break&bull&oi_reduce,near_bear&bear&oi_reduce),
      "benchmark_breakout_2h":(br_up,br_dn),
      "benchmark_sweep_2h":(sweep_lo,sweep_hi),
      "benchmark_volume_impulse":(strong&bull,strong&bear),
    }
    # Must not treat BOTH long/short signals in same bar as executable.
    return candidates

def events_from_conditions(x):
    out=[]
    for setup,(lmask,smask) in conditions(x).items():
        if isinstance(lmask,bool):lmask=pd.Series(False,index=x.index)
        if isinstance(smask,bool):smask=pd.Series(False,index=x.index)
        side=lmask.astype(int)-smask.astype(int)
        positions=np.flatnonzero(side.to_numpy()!=0)
        previous=-MIN_GAP_BARS
        for p in positions:
            if p-previous<MIN_GAP_BARS:continue
            signal_time=x.index[p]
            entry_time=signal_time+pd.Timedelta(minutes=5)
            if not np.isfinite(x.atr.iat[p]) or entry_time>x.index[-1]-pd.Timedelta(hours=8):
                continue
            out.append(dict(setup=setup,signal_time=str(signal_time),
                 entry_time=entry_time,side=int(side.iat[p]),
                 session=x.session.iat[p],ny_day=x.ny_day.iat[p],
                 period=x.period.iat[p],oi_z30=float(x.oi_z30.iat[p]) if pd.notna(x.oi_z30.iat[p]) else None,
                 oi_delta30_pct=float(x.oi_delta30_pct.iat[p]),
                 basis_z=float(x.basis_z.iat[p]) if pd.notna(x.basis_z.iat[p]) else None,
                 funding=float(x.last_funding.iat[p]) if pd.notna(x.last_funding.iat[p]) else None))
            previous=p
    if not out:raise RuntimeError("No signals discovered")
    return pd.DataFrame(out)

def replay(fut,signals):
    minute=fut.index
    op=fut.open.to_numpy(dtype=float)
    hi=fut.high.to_numpy(dtype=float)
    lo=fut.low.to_numpy(dtype=float)
    close=fut.close.to_numpy(dtype=float)
    alltr=[]
    for e in signals.itertuples():
        at=minute.searchsorted(e.entry_time)
        if at>=len(minute) or minute[at]!=e.entry_time:raise RuntimeError("Missing 1m entry")
        p=float(op[at])
        side=int(e.side)
        for name,(target,stop,hold) in EXIT_RULES.items():
            until=at+hold
            if until>len(minute):continue
            stop_level=p-side*stop
            if target is None:
                target_level=None
            else:
                target_level=p+side*target
            h=hi[at:until]
            l=lo[at:until]
            if side>0:
                bad=l<=stop_level
                good=h>=target_level if target_level is not None else np.zeros(len(h),bool)
            else:
                bad=h>=stop_level
                good=l<=target_level if target_level is not None else np.zeros(len(h),bool)
            fbad=np.flatnonzero(bad)
            fgood=np.flatnonzero(good)
            bi=int(fbad[0]) if len(fbad) else hold
            gi=int(fgood[0]) if len(fgood) else hold
            if bi<=gi and bi<hold:
                xp=stop_level;cause="stop";held=bi+1
            elif gi<hold:
                xp=target_level;cause="target";held=gi+1
            else:
                xp=close[until-1];cause="time";held=hold
            entryfill=p+side*SLIP
            exitfill=xp-side*SLIP
            gross=side*(exitfill-entryfill)
            fee=FEE*(entryfill+exitfill)
            net=gross-fee
            alltr.append(dict(setup=e.setup,period=e.period,
                signal_time=e.signal_time,entry_time=str(e.entry_time),
                ny_day=e.ny_day,session=e.session,side=side,exit_rule=name,
                outcome=cause,held_mins=held,entry_px=round(entryfill,2),
                exit_px=round(exitfill,2),gross_pts=round(gross,3),
                fee_pts=round(fee,3),net_pts=round(net,3)))
    return pd.DataFrame(alltr)

def summarize(tr):
    out=[]
    for (name,rule,period),g in tr.groupby(["setup","exit_rule","period"],observed=True):
        g=g.sort_values("entry_time")
        a=g.net_pts.to_numpy()
        rolling=np.cumsum(a)
        dd=np.max(np.maximum.accumulate(np.concatenate(([0],rolling)))[1:]-rolling)
        out.append(dict(setup=name,exit_rule=rule,period=period,
          trades=len(g),unique_days=g.ny_day.nunique(),
          target_hit_pct=round(100*(g.outcome=="target").mean(),2),
          net_win_pct=round(100*(a>0).mean(),2),
          net200_pct=round(100*(a>=200).mean(),2),
          mean_net=round(a.mean(),2),median_net=round(np.median(a),2),
          total_net=round(a.sum(),2),max_drawdown=round(float(dd),2)))
    return pd.DataFrame(out)

def block_bootstrap_lower(g,iterations=900,seed=20261018):
    # Unit of resampling is a NY CALENDAR DAY, not a highly correlated 5m trade.
    # Only run on independent final-holdout evaluation of preselected setups.
    byday=g.groupby("ny_day").net_pts.agg(["sum","count"])
    a=byday["sum"].to_numpy(float)
    n=byday["count"].to_numpy(float)
    if len(a)<15:return np.nan
    rng=np.random.default_rng(seed)
    samples=rng.integers(0,len(a),size=(iterations,len(a)))
    return float(np.quantile(a[samples].sum(axis=1)/n[samples].sum(axis=1),.025))

def analyze(signals,tr,summary,quality):
    fields=["trades","unique_days","mean_net","net_win_pct","net200_pct","max_drawdown"]
    p=summary.pivot(index=["setup","exit_rule"],columns="period",values=fields)
    p.columns=[f"{a}_{b}" for a,b in p.columns]
    p=p.reset_index()
    for col in ("trades_train","trades_validation","trades_holdout","mean_net_train","mean_net_validation","mean_net_holdout"):
        if col not in p:p[col]=np.nan
    eligible=p[(p.trades_train>=PRESELECT_MIN_TRAIN)&
               (p.trades_validation>=PRESELECT_MIN_VAL)&
               (p.trades_holdout>=PRESELECT_MIN_HOLD)].copy()
    eligible["preholdout_min_avg"]=np.minimum(eligible.mean_net_train,eligible.mean_net_validation)
    eligible["positive_both"]=(eligible.mean_net_train>0)&(eligible.mean_net_validation>0)
    eligible=eligible.sort_values("preholdout_min_avg",ascending=False)
    positive=eligible[eligible.positive_both].copy()
    chosen=(positive.head(15) if len(positive) else eligible.head(15)).copy()
    # Important: Jul-Oct dates appeared in prior research; this is a CHRONOLOGICAL
    # check, not a pristine holdout against all human exploratory decisions.
    lows=[]
    for r in chosen.itertuples():
        g=tr[(tr.setup==r.setup)&(tr.exit_rule==r.exit_rule)&(tr.period=="holdout")]
        lows.append(round(block_bootstrap_lower(g),2))
    chosen["holdout_day_bootstrap_lower95"]=lows
    overview=signals.groupby(["setup","period"]).agg(
         n_events=("side","size"),days=("ny_day","nunique"),
         avg_oi30_pct=("oi_delta30_pct","mean")).reset_index()
    overview.to_csv(OUT/"setup_signal_counts.csv",index=False)
    session=tr.groupby(["setup","exit_rule","period","session"],observed=True).net_pts.agg(
       n="size",mean_net="mean",win_pct=lambda s:100*(s>0).mean()).reset_index()
    session["mean_net"]=session.mean_net.round(2)
    session["win_pct"]=session.win_pct.round(2)
    session.to_csv(OUT/"session_results.csv",index=False)
    quality.update(
      signals=len(signals),replay_trades=len(tr),setups=signals.setup.nunique(),
      eligible_entry_exit_pairs=len(eligible),positive_both_early=len(positive),
      candidates_selected_by_early_periods=len(chosen))
    chosen.to_csv(OUT/"preselected_holdout_results.csv",index=False)
    eligible.to_csv(OUT/"full_train_validation_rank.csv",index=False)
    return chosen,positive,session

def report(quality,chosen,positive,session):
    def table(d,cols):
        return d[cols].to_markdown(index=False) if len(d) else "No eligible candidates."
    cols=["setup","exit_rule","trades_train","mean_net_train",
       "trades_validation","mean_net_validation","trades_holdout",
       "mean_net_holdout","holdout_day_bootstrap_lower95"]
    info=[
      "# Delta India BTCUSD positioning and structure: institutional-style proxies",
      "",
      "## Executive result",
      "Price/OI/mark/funding history is **not** identity-tagged institutional order flow; OI increases cannot label long/short aggressors; OHLCV does not reveal liquidations.",
      "The objective is to test if patterns with *positioning proxies* improve signal expectancy and entry quality relative to price-only breakout/sweep controls.",
      "",
      "## Data & chronology",
      json.dumps(quality,indent=2),
      "",
      "Native futures 1m plus mark 1m, OI 5m, funding 1h. Futures entry modeled at first available one-minute OPEN after completely closed five-minute signal bar.",
      "Funding H-hour candle is used only AFTER hour H+1 begins, without same-hour lookahead. Mark basis uses previous complete 1-minute candle.",
      "Signals use no future data; 2h cooldown independently per strategy. Independent setup rows may overlap; results are NOT an aggregated portfolio.",
      "A funding OHLC candle is not a realized individual funding payment, and the study's trading cost does not include position funding.",
      "",
      "## Fixed execution scenarios",
      "+300/-250 max2h, +500/-350 max4h, +1000/-500 max8h, +1500/-650 max8h, time2h/-400, time4h/-600.",
      "Taker 0.05% each side; 18% GST applied to fee; adverse 5 BTC-point slippage per side. No real L2 execution history, financing/funding cost, liquidation or account sizing.",
      "Same-minute conflicting stop/target takes stop (conservative); no intraminute order inferred.",
      "All outcomes are BTC PRICE POINTS per 1 BTC notional exposure, not account-dollar P&L.",
      "",
      "## Preselected candidates versus chronological holdout",
      "Select by greater of none: only train/validation minimum mean; never rank on holdout. Holdout periods have been examined in earlier unrelated studies, so NOT globally untouched.",
      table(chosen,cols),"",
      f"Pairs positive in BOTH training and validation, with sample requirements: **{len(positive)}**.",
      "",
      "The holdout 95% lower values use calendar-day block bootstrap of trade returns and are exploratory, not multiple-testing adjusted.",
      "",
      "## US/London/Asia session comparison for leading setup",
      table(session[(session.setup==chosen.iloc[0].setup)&(session.exit_rule==chosen.iloc[0].exit_rule)] if len(chosen) else session.head(0),
        ["period","session","n","mean_net","win_pct"]),"",
      "## Interpretation / audit",
      "- Regime names are market-behavior PROXIES. Rising OI + rising price does NOT establish institutional long accumulation; there is a long and a short in every derivatives contract.",
      "- Descending OI with big moves may reflect de-risking, closing of either side, expiration/venue effects; not proof of liquidations.",
      "- Positive historical mean is insufficient without fee stress, sample uncertainty and forward paper-trading on newer dates.",
      "- Baseline 2h breakout and 2h sweep are retained as price-only controls.",
      "- Avoid choosing a result only because it looks best in July-Oct: that is data snooping.",
      "",
      "Outputs: quality.json, feature_observations.csv, candidate_signals.csv, all_exit_trades.csv, all_results.csv, preselected_holdout_results.csv, full_train_validation_rank.csv, session_results.csv."
    ]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(info)+"\n",encoding="utf-8")

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    fut,mark,oi,funding,quality=inputs()
    x=features(fut,mark,oi,funding)
    # Pooled explanatory observations, no fabricated institutional labels.
    observed=x[["close","mark_close","oi_close","last_funding",
          "oi_delta30_pct","oi_z30","basis_bp","basis_z",
          "session","period"]]
    observed.iloc[::12].to_csv(OUT/"hourly_feature_observations.csv")
    quality["features"]={
      "oi30_pct_p01_p50_p99":[round(float(a),5) for a in np.nanpercentile(x.oi_delta30_pct,[1,50,99])],
      "basis_bp_p01_p50_p99":[round(float(a),4) for a in np.nanpercentile(x.basis_bp,[1,50,99])],
      "funding_p01_p50_p99":[round(float(a),8) for a in np.nanpercentile(funding.close,[1,50,99])],
      "non_null_funding_aligned":int(x.last_funding.notna().sum()),
      "positive_oi_readings":int(x.oi_close.gt(0).sum())}
    signals=events_from_conditions(x)
    signal_export=signals.copy()
    signal_export["entry_time"]=signal_export.entry_time.astype(str)
    signal_export.to_csv(OUT/"candidate_signals.csv",index=False)
    trades=replay(fut,signals)
    trades.to_csv(OUT/"all_exit_trades.csv",index=False)
    stat=summarize(trades)
    stat.to_csv(OUT/"all_results.csv",index=False)
    chosen,positive,session=analyze(signals,trades,stat,quality)
    (OUT/"quality.json").write_text(json.dumps(quality,indent=2)+"\n",encoding="utf-8")
    report(quality,chosen,positive,session)
    print("INSTITUTIONAL REGIME RESEARCH COMPLETED")
    print(json.dumps(quality,indent=2))
    cols=["setup","exit_rule","trades_train","mean_net_train",
      "trades_validation","mean_net_validation","trades_holdout",
      "mean_net_holdout","holdout_day_bootstrap_lower95"]
    if len(chosen):print(chosen[cols].to_string(index=False))
if __name__=="__main__":
    main()
