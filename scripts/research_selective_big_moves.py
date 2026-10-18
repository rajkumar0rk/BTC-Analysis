#!/usr/bin/env python3
"""Research candidate BTCUSD 1m execution with completed 5m/15m/1h context.
Truly unseen final holdout: 2026-07-01 onward. Research only, not advice.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd

INPUT=Path("data/delta_india/BTCUSD/1m")
OUT=Path("analysis/selective_big_move_research")
UTC_HOLD=pd.Timestamp("2026-07-01",tz="UTC")
UTC_VAL=pd.Timestamp("2026-01-01",tz="UTC")
FEE=0.0005*1.18
SLIP=5.
CASES={
 "fixed800_400_4h":("fixed",800.,400.,240),
 "fixed1200_500_8h":("fixed",1200.,500.,480),
 "fixed1600_600_8h":("fixed",1600.,600.,480),
 "fixed2000_800_12h":("fixed",2000.,800.,720),
 "atr_2r_8h":("atr2",0.,0.,480),
 "atr_3r_8h":("atr3",0.,0.,480),
 "trail500_after500_8h":("trail",1600.,500.,480),
 "time4h_stop500":("time",0.,500.,240),
 "time8h_stop700":("time",0.,700.,480)
}
# Maximum look-forward is 720 minutes; no overlapping within each model.
NY="America/New_York"

def load():
 files=sorted(INPUT.glob("20??-??.csv.gz"))
 if not files:raise RuntimeError("No downloaded Delta 1m files")
 z=[]
 for f in files:
  a=pd.read_csv(f,compression="gzip")
  a["time"]=pd.to_datetime(a.time.astype("int64"),unit="s",utc=True)
  z.append(a[["time","open","high","low","close","volume"]])
 d=pd.concat(z,ignore_index=True).set_index("time").sort_index()
 if d.index.has_duplicates or d.isna().any().any():raise RuntimeError("Invalid OHLCV")
 if not d.index.to_series().diff().iloc[1:].eq(pd.Timedelta(minutes=1)).all():raise RuntimeError("Gaps in data")
 return d,len(files)

def aggregate(d,n):
 size=d.close.resample(f"{n}min",closed="left",label="left").count()
 x=d.resample(f"{n}min",closed="left",label="left").agg(
   {"open":"first","high":"max","low":"min","close":"last","volume":"sum"})
 return x[size==n].dropna()

def indicators(d):
 c=d.close
 high=d.high
 low=d.low
 rng=high-low
 tr=pd.concat((rng,(high-c.shift()).abs(),(low-c.shift()).abs()),axis=1).max(axis=1)
 d["ema20"]=c.ewm(span=20,adjust=False,min_periods=50).mean()
 d["ema50"]=c.ewm(span=50,adjust=False,min_periods=100).mean()
 d["ema100"]=c.ewm(span=100,adjust=False,min_periods=150).mean()
 d["atr"]=tr.ewm(alpha=1/14,adjust=False,min_periods=50).mean()
 d["vol_ratio"]=d.volume/d.volume.rolling(24,min_periods=24).mean().shift()
 d["range_ratio"]=rng/rng.rolling(24,min_periods=24).median().shift().replace(0,np.nan)
 d["hi12"]=high.rolling(12,min_periods=12).max().shift()
 d["lo12"]=low.rolling(12,min_periods=12).min().shift()
 d["hi24"]=high.rolling(24,min_periods=24).max().shift()
 d["lo24"]=low.rolling(24,min_periods=24).min().shift()
 d["body"]=((c-d.open).abs()/rng.replace(0,np.nan)).fillna(0)
 d["upper_wick"]=((high-np.maximum(c,d.open))/rng.replace(0,np.nan)).fillna(0)
 d["lower_wick"]=((np.minimum(c,d.open)-low)/rng.replace(0,np.nan)).fillna(0)
 d["mid"]=(high+low)/2
 return d

def signal_engine(d):
 b5=indicators(aggregate(d,5))
 b15=indicators(aggregate(d,15))
 h1=indicators(aggregate(d,60))
 # A bar stamped 09:30 is only observable from 09:35. Shift HTF index to close time.
 closed_15=b15[["open","close","ema20","ema50","atr","hi12","lo12"]].copy()
 closed_15.index+=pd.Timedelta(minutes=15)
 closed_h=h1[["close","ema20","ema50","ema100","atr","hi12","lo12"]].copy()
 closed_h.index+=pd.Timedelta(minutes=60)
 observed=b5.index+pd.Timedelta(minutes=5)
 # Completed higher-timeframe bars only (no repainting).
 x=b5.copy()
 for prefix,tbl in [("h15_",closed_15),("h1_",closed_h)]:
  for col in tbl.columns:
   x[prefix+col]=tbl[col].reindex(observed,method="ffill").to_numpy()
 ny=x.index.tz_convert(NY)
 tod=ny.hour*60+ny.minute
 session=(ny.dayofweek<5)&(tod>=540)&(tod<960)
 open_window=(ny.dayofweek<5)&(tod>=570)&(tod<720)
 c=x.close
 green=c>x.open;red=c<x.open
 h_bull=(x.h1_ema20>x.h1_ema50)&(x.h1_ema50>x.h1_ema100)&(x.h1_close>x.h1_ema50)
 h_bear=(x.h1_ema20<x.h1_ema50)&(x.h1_ema50<x.h1_ema100)&(x.h1_close<x.h1_ema50)
 h_weak_bull=(x.h1_ema20>x.h1_ema50)&(x.h1_close>x.h1_ema50)
 h_weak_bear=(x.h1_ema20<x.h1_ema50)&(x.h1_close<x.h1_ema50)
 mid_bull=(x.h15_close>x.h15_ema20)
 mid_bear=(x.h15_close<x.h15_ema20)
 imp=(x.body>0.60)&(x.range_ratio>1.5)&(x.vol_ratio>1.2)
 breakout_up=(c>x.hi12)&green&imp
 breakout_down=(c<x.lo12)&red&imp
 liquid_sweep_up=(x.high>x.hi24)&(c<x.hi24)&red&(x.upper_wick>=0.35)&(x.vol_ratio>1)
 liquid_sweep_dn=(x.low<x.lo24)&(c>x.lo24)&green&(x.lower_wick>=0.35)&(x.vol_ratio>1)
 pb_up=(x.low<x.ema20)&(c>x.ema20)&green&(x.ema20>x.ema20.shift(3))
 pb_down=(x.high>x.ema20)&(c<x.ema20)&red&(x.ema20<x.ema20.shift(3))
 # approximate session VWAP, reset every New York calendar date; prior periods only.
 local_dates=pd.Series([str(z) for z in ny.date],index=x.index)
 weighted=x.mid*x.volume
 group=local_dates
 cp=weighted.groupby(group).cumsum()
 cv=x.volume.groupby(group).cumsum()
 vw=cp/cv.replace(0,np.nan)
 vw_up=(c>vw)&(c.shift(1)<=vw.shift(1))&green
 vw_down=(c<vw)&(c.shift(1)>=vw.shift(1))&red
 # Only completed 5-minute reference bars; all signal masks causal.
 policies={
   "trend_12bar_break_strict":(session&breakout_up&h_bull&mid_bull,session&breakout_down&h_bear&mid_bear),
   "trend_12bar_break_weak":(session&breakout_up&h_weak_bull,session&breakout_down&h_weak_bear),
   "trend_24bar_break":(session&(c>x.hi24)&green&imp&h_weak_bull,session&(c<x.lo24)&red&imp&h_weak_bear),
   "trend_pullback_ema20":(session&pb_up&h_bull&mid_bull,session&pb_down&h_bear&mid_bear),
   "trend_pullback_weak":(session&pb_up&h_weak_bull,session&pb_down&h_weak_bear),
   "session_vwap_reclaim":(session&vw_up&h_bull&mid_bull,session&vw_down&h_bear&mid_bear),
   "session_vwap_weak":(session&vw_up&h_weak_bull,session&vw_down&h_weak_bear),
   "sweep_24bar_trend":(session&liquid_sweep_dn&h_weak_bull,session&liquid_sweep_up&h_weak_bear),
   "sweep_24bar_countertrend":(session&liquid_sweep_dn&h_weak_bear,session&liquid_sweep_up&h_weak_bull),
   "sweep_24bar_opening":(open_window&liquid_sweep_dn,open_window&liquid_sweep_up),
   "opening_break_strict":(open_window&breakout_up&h_bull,open_window&breakout_down&h_bear),
   "opening_break_weak":(open_window&breakout_up&h_weak_bull,open_window&breakout_down&h_weak_bear),
   "impulse_trend_strict":(session&imp&green&h_bull&mid_bull,session&imp&red&h_bear&mid_bear),
   "impulse_fade_open":(open_window&imp&red,open_window&imp&green),
   "h1_trend_15m_reclaim":(session&vw_up&h_bull&mid_bull,session&vw_down&h_bear&mid_bear)
 }
 idx=d.index
 signals=[]
 for name,(longs,shorts) in policies.items():
  sides=(longs.astype(int)-shorts.astype(int)).to_numpy()
  fired=np.flatnonzero(sides)
  last_date=None
  for q in fired:
   at=observed[q]
   loc=at.tz_convert(NY)
   day=str(loc.date())
   if last_date==day:continue
   if at not in idx or at>idx[-1]-pd.Timedelta(minutes=721):continue
   atr=float(x.atr.iat[q])
   if not np.isfinite(atr) or atr<=0:continue
   signals.append(dict(setup=name,entry_utc=at,side=int(sides[q]),
     ny_date=day,atr5=atr,signal_close=float(x.close.iat[q]),
     h1_atr=float(x.h1_atr.iat[q])))
   last_date=day
 return pd.DataFrame(signals).sort_values("entry_utc"),len(b5),len(b15),len(h1)

def replay(d,entries):
 index=d.index
 op=d.open.to_numpy()
 hi=d.high.to_numpy()
 lo=d.low.to_numpy()
 cl=d.close.to_numpy()
 outputs=[]
 for row in entries.itertuples():
  pos=int(index.searchsorted(row.entry_utc))
  if pos>=len(index) or index[pos]!=row.entry_utc:continue
  price=float(op[pos])
  side=int(row.side)
  for name,(kind,goal,stop,horizon) in CASES.items():
   if kind in ("atr2","atr3"):
    stop=float(np.clip(row.atr5*4,250,800))
    goal=stop*(2 if kind=="atr2" else 3)
   stop_level=price-side*stop
   target=price+side*goal if goal>0 else np.nan
   terminal=float(cl[pos+horizon-1])
   cause="time";held=horizon
   best=price
   for j in range(horizon):
    k=pos+j
    hard_hit=(lo[k]<=stop_level) if side>0 else (hi[k]>=stop_level)
    take_hit=(hi[k]>=target if side>0 else lo[k]<=target) if goal>0 else False
    # Same-minute stop and target => stop (worst-case sequence)
    if hard_hit:
     terminal=stop_level;cause="stop";held=j+1;break
    if take_hit:
     terminal=target;cause="takeprofit";held=j+1;break
    if kind=="trail":
     best=max(best,hi[k]) if side>0 else min(best,lo[k])
     if side*(best-price)>=500:
      new=best-side*500
      stop_level=max(stop_level,new) if side>0 else min(stop_level,new)
   # $5 per side adverse slippage, plus taker fee and GST both legs.
   entry=price+side*SLIP
   exit=terminal-side*SLIP
   gross=side*(exit-entry)
   cost=FEE*(entry+exit)
   net=gross-cost
   outputs.append(dict(setup=row.setup,entry_utc=str(row.entry_utc),
       ny_date=row.ny_date,side=side,exit_policy=name,
       period="train" if row.entry_utc<UTC_VAL else "validation" if row.entry_utc<UTC_HOLD else "holdout",
       stop_dist=round(stop,1),target_dist=round(goal,1),cause=cause,hold_minutes=held,
       entry_price=round(entry,2),gross_points=round(gross,2),
       fee_points=round(cost,2),net_points=round(net,2)))
 return pd.DataFrame(outputs)

def aggregates(x):
 out=[]
 for (setup,ep,period),g in x.groupby(["setup","exit_policy","period"],observed=True):
  g=g.sort_values("entry_utc")
  v=g.net_points.to_numpy()
  c=np.cumsum(v)
  dd=np.max(np.maximum.accumulate(np.concatenate(([0],c)))[1:]-c)
  out.append(dict(setup=setup,exit_policy=ep,period=period,
       n=len(g),n_days=g.ny_date.nunique(),win_pct=round(100*(v>0).mean(),2),
       take_pct=round(100*(g.cause=="takeprofit").mean(),2),
       net200_pct=round(100*(v>=200).mean(),2),
       net500_pct=round(100*(v>=500).mean(),2),
       mean_net=round(v.mean(),2),median_net=round(np.median(v),2),
       total_net=round(v.sum(),1),max_drawdown=round(float(dd),1),
       median_hold_min=round(float(g.hold_minutes.median()),1)))
 return pd.DataFrame(out)

def evaluate(stats,entries,quality):
 pivot=stats.pivot(index=["setup","exit_policy"],columns="period",
      values=["n","mean_net","win_pct","net200_pct","max_drawdown"])
 pivot.columns=[f"{metric}_{period}" for metric,period in pivot.columns]
 pivot=pivot.reset_index()
 # Train supports -> validation selection; never select by holdout.
 required=["n_train","n_validation","n_holdout","mean_net_train","mean_net_validation","mean_net_holdout"]
 for key in required:
  if key not in pivot:pivot[key]=np.nan
 eligible=pivot[(pivot.n_train>=50)&(pivot.n_validation>=25)&(pivot.n_holdout>=20)].copy()
 # Rank by minimal in-sample mean to prefer consistency, no holdout used.
 eligible["robust_score"]=np.minimum(eligible.mean_net_train,eligible.mean_net_validation)
 ranked=eligible.sort_values("robust_score",ascending=False)
 passed=ranked[(ranked.mean_net_train>0)&(ranked.mean_net_validation>0)]
 selected=passed.head(10) if len(passed) else ranked.head(10)
 quality["train_validation_positive_candidates"]=len(passed)
 quality["eligible_entry_exit_combinations"]=len(eligible)
 quality["selection_note"]="Ranking uses train and validation only; holdout not used for selection"
 report=["# BTC Futures 1m execution, 5m/15m/1h structure — extended discovery",
   "",
   "**Outcome cannot be promised:** A predictable 200–500 BTC-point profit every day may not exist; zero-trade days are permitted.",
   "",
   "## Research design",
   "- Genuine Delta India BTCUSD perpetual 1-minute OHLCV, without inventing fills or candles.",
   "- Only completed 5m/15m/1h candles are used. Signals on 5m close, orders at next 1m open.",
   "- Train: Jan–Dec 2025; intermediate validation: Jan–Jun 2026; final untouched holdout: Jul–Oct 17 2026.",
   "- Up to one event per strategy per New York day, not one event across strategies. Portfolio correlation is NOT modeled.",
   "- 15 candidate directions/entry conditions and 9 objective exits, including bigger targets of 800–2000 price points, ATR stops, trailing stops and up to 12h holds.",
   "- Stop wins same-minute target/stop ambiguity. Trailing stop decisions apply only after a completed 1m bar.",
   "- Simulated taker fee 0.05% per side with 18% GST on fee, and adverse 5-point slippage per side; no funding, bid/ask or liquidation information.",
   "- All profits are BTC price points per 1 BTC exposure, NOT account USD profit. At 0.001 BTC, a 200-point BTC move produces $0.20 gross, not $200.",
   "",
   "## Data quality",
   json.dumps(quality,indent=2),
   "",
   "## Ranked entry/exit pairs (selection independent of final holdout)",
   "Ranking by WORSE of train and validation average net profit; rank deliberately excludes holdout.",
   selected[["setup","exit_policy","n_train","n_validation","n_holdout","mean_net_train",
      "mean_net_validation","mean_net_holdout","robust_score"]].to_markdown(index=False) if len(selected) else "No strategy reached minimum sample requirements.",
   "",
   "## All train/validation supported setups",
   ranked[["setup","exit_policy","n_train","n_validation","n_holdout",
      "mean_net_train","mean_net_validation","mean_net_holdout"]].to_markdown(index=False) if len(ranked) else "None.",
   "",
   "## Main interpretation",
   "- A profitable historical train+validation combination is a candidate hypothesis, not evidence that daily income is guaranteed.",
   "- Holdout mean and maximum drawdown must be assessed jointly and with transaction-cost sensitivity and weekly block confidence intervals.",
   "- Repeated testing of many candidates creates selection risk; do not tune a losing holdout to make it win, then call the same dates out-of-sample.",
   "- OHLCV does not prove resting liquidity or actual institutional execution.",
   "",
   "See candidate_entries.csv, all_trade_replays.csv, all_summary.csv and ranked_candidates.csv."
  ]
 (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n",encoding="utf-8")
 ranked.to_csv(OUT/"ranked_candidates.csv",index=False)
 return ranked,selected

def main():
 OUT.mkdir(parents=True,exist_ok=True)
 d,files=load()
 entries,n5,n15,n60=signal_engine(d)
 entries.to_csv(OUT/"candidate_entries.csv",index=False)
 results=replay(d,entries)
 results.to_csv(OUT/"all_trade_replays.csv",index=False)
 stats=aggregates(results)
 stats.to_csv(OUT/"all_summary.csv",index=False)
 quality=dict(files=files,one_minute_candles=len(d),five_minute_candles=n5,
   fifteen_minute_candles=n15,hourly_candles=n60,
   first_utc=str(d.index.min()),last_utc=str(d.index.max()),
   zero_volume=int((d.volume==0).sum()),
   entry_events=len(entries),trade_simulations=len(results),entries_by_setup=entries.groupby("setup").size().to_dict())
 ranked,selected=evaluate(stats,entries,quality)
 (OUT/"quality.json").write_text(json.dumps(quality,indent=2)+"\n",encoding="utf-8")
 print("RESEARCH COMPLETE",json.dumps(quality))
 print("RANKED",selected.to_string(index=False))
 print("FINAL HOLDOUT: these are exploratory outcomes, not guarantees")

if __name__=="__main__":main()
