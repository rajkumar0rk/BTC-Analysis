#!/usr/bin/env python3
"""Explore actual Delta India BTCUSD 1-minute OHLCV: time, session levels, candle shapes."""
from pathlib import Path
import gzip, json
import numpy as np
import pandas as pd

BASE=Path("data/delta_india/BTCUSD/1m")
OUT=Path("analysis/delta_1m_5m_15m")
HOLD=pd.Timestamp("2026-07-01",tz="UTC")
NY="America/New_York"

def load():
    chunks=[]
    for fp in sorted(BASE.glob("20??-??.csv.gz")):
        d=pd.read_csv(fp,compression="gzip")
        d["time"]=pd.to_datetime(d["time"].astype("int64"),unit="s",utc=True)
        chunks.append(d[["time","open","high","low","close","volume"]])
    if not chunks: raise RuntimeError("1m monthly Delta files missing")
    d=pd.concat(chunks,ignore_index=True).set_index("time").sort_index()
    if d.index.has_duplicates: raise ValueError("Duplicate times")
    if d.isna().any().any(): raise ValueError("Missing OHLCV values")
    missing=int((d.index.to_series().diff().dropna()/pd.Timedelta(minutes=1)-1).clip(lower=0).sum())
    return d,dict(source_months=len(chunks),source_candles=len(d),missing_minutes=missing,
        first_utc=str(d.index.min()),last_utc=str(d.index.max()),
        zero_volume=int((d.volume==0).sum()))

def bars(d,m):
    if m==1:return d.copy()
    n=d.close.resample(f"{m}min",closed="left",label="left").count()
    res=d.resample(f"{m}min",closed="left",label="left").agg(
        {"open":"first","high":"max","low":"min","close":"last","volume":"sum"})
    return res[n==m].dropna()

def feature(d,m):
    a=d.copy()
    local=a.index.tz_convert(NY)
    a["dow"]=local.dayofweek
    a["clock"]=local.hour*60+local.minute
    a["split"]=np.where(a.index<HOLD,"discovery","holdout")
    a["range_bp"]=(a.high-a.low)/a.open*1e4
    a["red"]=a.close<a.open
    a["flat"]=a.close==a.open
    a["range_mult"]=a.range_bp/a.range_bp.rolling(120//m,min_periods=120//m).median().shift(1).replace(0,np.nan)
    return a

def scan(a,m):
    x=a.copy()
    x["over2"]=(x.range_mult>=2)
    q=x.groupby(["dow","clock","split"],observed=True).agg(
        n=("close","size"),red_rate=("red","mean"),median_range_bp=("range_bp","median"),
        median_mult=("range_mult","median"),over2_rate=("over2","mean"),
        median_volume=("volume","median")).reset_index()
    q["tf"]=m
    q["ny_time"]=q.clock.map(lambda x:f"{x//60:02d}:{x%60:02d}")
    for s in ["red_rate","over2_rate"]:q[s]=(100*q[s]).round(2)
    for s in ["median_range_bp","median_mult","median_volume"]:q[s]=q[s].round(3)
    return q

def prem_table(d):
    x=d.copy()
    ny=x.index.tz_convert(NY)
    x["day"]=list(ny.date)
    clock=ny.hour*60+ny.minute
    mask=(ny.dayofweek<5)&(clock<570)
    return x[mask].groupby("day").agg(hi=("high","max"),lo=("low","min"),cnt=("close","size"))

def event_trades(d,frames):
    prem=prem_table(d)
    rows=[]
    for tf,f in frames.items():
        ny=f.index.tz_convert(NY)
        ticks=f[(ny.dayofweek<5)&(ny.hour==9)&(ny.minute==30)]
        for t,b in ticks.iterrows():
            day=t.tz_convert(NY).date()
            if day not in prem.index:continue
            p=prem.loc[day]
            if p.cnt<530:continue
            enter=t+pd.Timedelta(minutes=tf)
            leave=enter+pd.Timedelta(minutes=29)
            if enter not in d.index or leave not in d.index: continue
            bp=1e4*(d.at[leave,"close"]/d.at[enter,"open"]-1)
            cases={"opening_direction":int(b.close>b.open)-int(b.close<b.open),
                "close_above_premarket_high":int(b.close>p.hi),
                "close_below_premarket_low":-int(b.close<p.lo),
                "upper_sweep_close_inside":-int(b.high>p.hi and b.close<p.hi),
                "lower_sweep_close_inside":int(b.low<p.lo and b.close>p.lo)}
            for k,side in cases.items():
                if side==0:continue
                ret=side*bp
                rows.append(dict(tf=tf,setup=k,split="discovery" if t<HOLD else "holdout",
                    ny_day=str(day),trigger=str(t),direction="LONG" if side>0 else "SHORT",
                    entry=str(enter),gross_bp=round(ret,5),net_2bp=round(ret-2,5)))
    # 5m two-candle confirmation separately; execution at 09:40 ET
    f=frames[5]
    ny=f.index.tz_convert(NY)
    for t,b in f[(ny.dayofweek<5)&(ny.hour==9)&(ny.minute==30)].iterrows():
        second=t+pd.Timedelta(minutes=5)
        enter=t+pd.Timedelta(minutes=10)
        leave=enter+pd.Timedelta(minutes=29)
        if second not in f.index or enter not in d.index or leave not in d.index:continue
        c=f.loc[second]
        side=int((b.close>b.open)and(c.close>c.open))-int((b.close<b.open)and(c.close<c.open))
        if side==0:continue
        ret=side*1e4*(d.at[leave,"close"]/d.at[enter,"open"]-1)
        rows.append(dict(tf=5,setup="second_opening_5m_confirms",split="discovery" if t<HOLD else "holdout",
                    ny_day=str(t.tz_convert(NY).date()),trigger=str(t),
                    direction="LONG" if side>0 else "SHORT",entry=str(enter),
                    gross_bp=round(ret,5),net_2bp=round(ret-2,5)))
    x=pd.DataFrame(rows)
    if x.empty:raise RuntimeError("No NY open session events; check API candle timestamps")
    x["gross_win"]=x.gross_bp>0
    x["net_win"]=x.net_2bp>0
    summary=x.groupby(["tf","setup","split"],observed=True).agg(
        n=("gross_bp","size"),win_pct=("gross_win","mean"),
        net_win_pct=("net_win","mean"),mean_gross_bp=("gross_bp","mean"),
        median_gross_bp=("gross_bp","median"),mean_net_bp=("net_2bp","mean")).reset_index()
    for s in ["win_pct","net_win_pct"]:summary[s]=(summary[s]*100).round(2)
    for s in ["mean_gross_bp","median_gross_bp","mean_net_bp"]:summary[s]=summary[s].round(3)
    return x,summary

def sequences(d,m):
    rng=(d.high-d.low).clip(lower=1e-9)
    body=(d.close-d.open).abs()/rng
    upper=(d.high-np.maximum(d.open,d.close))/rng
    lower=(np.minimum(d.open,d.close)-d.low)/rng
    f=feature(d,m)
    v=np.select([
        (f.range_mult>1.8)&(body>0.6)&(d.close>d.open),
        (f.range_mult>1.8)&(body>0.6)&(d.close<d.open),
        (f.range_mult>=1)&(upper>=0.52),
        (f.range_mult>=1)&(lower>=0.52),
        f.range_mult<0.65,
        d.close>d.open,d.close<d.open],
        ["impulse_green","impulse_red","upper_wick","lower_wick","compression","green","red"],default="flat")
    cat=pd.Series(v,index=d.index)
    future=1e4*(d.close.shift(-30//m)/d.close-1)
    rows=[]
    for length in [2,3]:
        key=cat.copy()
        for k in range(1,length):
            key=cat.shift(k).fillna("?")+"|"+key
        z=pd.DataFrame({"pattern":key,"future":future}).dropna()
        z=z[~z.pattern.str.contains("?",regex=False)]
        train=z[z.index<HOLD]
        test=z[z.index>=HOLD]
        desc=train.groupby("pattern").future.agg(["size","mean",lambda x:(x>0).mean()])
        desc.columns=["n","mean","up_rate"]
        good=desc[(desc.n>=max(80,200//m))&
            (((desc.up_rate>=0.58)&(desc["mean"]>2))|
            ((desc.up_rate<=0.42)&(desc["mean"]< -2)))].copy()
        good["score"]=good["mean"].abs()*np.sqrt(good["n"])
        for pattern,r in good.nlargest(15,"score").iterrows():
            hold=test[test.pattern==pattern].future
            if not len(hold):continue
            side=1 if r["mean"]>0 else -1
            rows.append(dict(tf=m,sequence_bars=length,pattern=pattern,
                train_n=int(r["n"]),direction="LONG" if side>0 else "SHORT",
                train_win_pct=round(100*(r.up_rate if side==1 else 1-r.up_rate),2),
                train_mean_bp=round(side*r["mean"],2),holdout_n=len(hold),
                holdout_win_pct=round(100*(side*hold>0).mean(),2),
                holdout_mean_bp=round(side*hold.mean(),2)))
    return pd.DataFrame(rows)

def run():
    OUT.mkdir(parents=True,exist_ok=True)
    d,quality=load()
    frames={m:bars(d,m) for m in (1,5,15)}
    quality["bars_by_resolution"]={str(k):len(v) for k,v in frames.items()}
    quality["train_last_utc"]="2026-06-30"
    quality["holdout_start_utc"]="2026-07-01"
    clock=pd.concat([scan(feature(f,m),m) for m,f in frames.items()],ignore_index=True)
    wanted=clock[((clock.dow<=4)&clock.ny_time.isin(["08:30","09:30","09:31","09:35","09:45","10:00","17:00"]))|
                 ((clock.dow==6)&clock.ny_time.isin(["18:00","18:05","18:15"]))].copy()
    trades,events=event_trades(d,frames)
    seq=pd.concat([sequences(f,m) for m,f in frames.items()],ignore_index=True)
    for name,x in [("all_weekday_time_slots.csv",clock),("session_clock_events.csv",wanted),
                   ("session_event_trades.csv",trades),("session_event_summary.csv",events),
                   ("new_candle_sequences.csv",seq)]:
        x.to_csv(OUT/name,index=False)
    (OUT/"quality.json").write_text(json.dumps(quality,indent=2)+"\n")
    notes=[
        "# Delta Exchange India BTCUSD: 1m, 5m, 15m empirical institutional-style study",
        "",
        "**Source**: public Delta India BTCUSD perpetual 1-minute OHLCV (NOT the original uploaded 5m source).",
        "**Research horizon**: Jan 2025 - Oct 17 2026. Discovery: before 2026-07-01 UTC; holdout: July-Oct 17.",
        "**Candle labeling**: API 1m time assumed bar start; converted UTC-start-aligned 5m/15m bars. Confirm with live chart before using clock rules.",
        "**Institutional caution**: OHLCV does not identify institutional orders, stops, liquidations, order book or resting liquidity.",
        "**Execution**: trade signal observed at close of 1/5/15-minute opening bar, enter next REAL 1m open, exit 30 minutes later.",
        "Gross bp is direction-adjusted close-to-close-price return. Net 2bp is only an illustrative assumed round-trip fee/slippage, not validated executable P&L.",
        "",
        "## Data quality", "", "~~~json",json.dumps(quality,indent=2),"~~~","",
        "## New York 09:30 opening event hypotheses", "", events.to_markdown(index=False),
        "",
        "## Clock-time volatility and red/green tendencies",
        "See session_clock_events.csv, all_weekday_time_slots.csv. Range multiplier uses preceding 2h of completed same-timeframe bars.",
        "New York clock time uses daylight saving; values refer to assumed candle OPEN times, unlike prior reports which sometimes used close-time labels.",
        "Clock-time scan includes thousands of candidate cells: apparent extreme red/green rates are subject to severe multiple-testing bias.",
        "",
        "## Automatically mined 2-3 candle-shape sequences",
        "Patterns encode relative range, body, upper/lower wick and color; selected solely by DISCOVERY training, then evaluated on HOLDOUT.",
        "Correlated/overlapping samples; no independent-trade inference. See new_candle_sequences.csv.",
        "",(seq.sort_values("holdout_mean_bp",ascending=False).head(12).to_markdown(index=False) if len(seq) else "No candidate passed training thresholds."),"",
        "## Interpretation and next controls",
        "A recurring volatility window is not a known BUY/SHORT edge. Bid/ask, funding, market order slippage, size constraints and stops remain unmodeled.",
        "Do not deploy without a further untouched period, realistic bid/ask replay and date-blocked tests.",""]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(notes),encoding="utf-8")
    print(json.dumps(quality,indent=2))
    print(events.to_string(index=False))
    print("Selected sequences:",len(seq))
    print("ANALYSIS COMPLETE")

if __name__=="__main__": run()
