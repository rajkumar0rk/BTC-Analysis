#!/usr/bin/env python3
"""Compare exit policies on identical genuine Delta India BTCUSD 1m entries."""
from pathlib import Path
import json
import numpy as np
import pandas as pd

DATA=Path("data/delta_india/BTCUSD/1m")
OUT=Path("analysis/delta_1m_exit_research")
HOLD=pd.Timestamp("2026-07-01",tz="UTC")
FEE=0.0005*1.18
SLIP=5.0
POLICIES={
 "time15_sl250":(15,250,None,"time"),
 "time30_sl250":(30,250,None,"time"),
 "time60_sl250":(60,250,None,"time"),
 "tp200_sl150":(120,150,200,"fixed"),
 "tp300_sl200":(120,200,300,"fixed"),
 "tp500_sl250":(120,250,500,"fixed"),
 "tp500_sl250_be200":(120,250,500,"be"),
 "tp500_sl250_trail150":(120,250,500,"trail"),
 "atr4_2R":(120,None,None,"atr"),
 "ema20_exit_sl250":(60,250,None,"ema")
}

def load():
 a=[]
 files=sorted(DATA.glob("20??-??.csv.gz"))
 if not files:raise RuntimeError("Delta data not found")
 for p in files:
  x=pd.read_csv(p,compression="gzip")
  x["time"]=pd.to_datetime(x.time.astype("int64"),unit="s",utc=True)
  a.append(x[["time","open","high","low","close","volume"]])
 d=pd.concat(a,ignore_index=True).set_index("time").sort_index()
 if d.index.has_duplicates or d.isna().any().any():raise RuntimeError("Invalid OHLCV")
 if not d.index.to_series().diff().iloc[1:].eq(pd.Timedelta(minutes=1)).all():raise RuntimeError("Missing minutes")
 return d,len(files)

def candidates(d):
 o,h,l,c,v=[d[k] for k in ("open","high","low","close","volume")]
 rng=h-l
 span=rng.replace(0,np.nan)
 med=rng.rolling(60).median().shift()
 vol=v.rolling(60).mean().shift()
 hi30=h.rolling(30).max().shift()
 lo30=l.rolling(30).min().shift()
 hi60=h.rolling(60).max().shift()
 lo60=l.rolling(60).min().shift()
 ema20=c.ewm(span=20,adjust=False).mean()
 ema30=c.ewm(span=30,adjust=False).mean()
 ema120=c.ewm(span=120,adjust=False).mean()
 tr=pd.concat((rng,(h-c.shift()).abs(),(l-c.shift()).abs()),axis=1).max(axis=1)
 atr=tr.ewm(alpha=1/60,adjust=False,min_periods=180).mean().shift()
 ny=d.index.tz_convert("America/New_York")
 clock=ny.hour*60+ny.minute
 session=(ny.dayofweek<5)&(clock>=570)&(clock<720)
 up=(ema30>ema120)&(ema30>ema30.shift(5))
 dn=(ema30<ema120)&(ema30<ema30.shift(5))
 body=(c-o).abs()/span
 strength=(rng>1.7*med)&(body>=0.65)&(v>=1.2*vol)
 seek_up=session&strength&(c>o)&up
 seek_dn=session&strength&(c<o)&dn
 break_up=session&(c>hi30)&(c.shift()<=hi30.shift())&up&(rng>1.2*med)&(v>=vol)
 break_dn=session&(c<lo30)&(c.shift()>=lo30.shift())&dn&(rng>1.2*med)&(v>=vol)
 wick_up=(h-np.maximum(o,c))/span
 wick_dn=(np.minimum(o,c)-l)/span
 sw_up=session&(l<lo60)&(c>lo60)&(wick_dn>=0.4)&(v>=1.2*vol)&(c>o)
 sw_dn=session&(h>hi60)&(c<hi60)&(wick_up>=0.4)&(v>=1.2*vol)&(c<o)
 green=c>o;red=c<o
 up3=green&green.shift().fillna(False)&green.shift(2).fillna(False)
 dn3=red&red.shift().fillna(False)&red.shift(2).fillna(False)
 exhaust=session&(rng>2*med)&(v>=1.4*vol)
 tests={
  "NY_open_1m":(session&(clock==570)&green,session&(clock==570)&red),
  "1m_trend_impulse":(seek_up,seek_dn),
  "1m_30m_range_break":(break_up,break_dn),
  "1m_60m_sweep_reject":(sw_up,sw_dn),
  "1m_3bar_exhaustion":(exhaust&dn3,exhaust&up3)
 }
 rec=[]
 days=np.array([str(x) for x in ny.date])
 for name,(longs,shorts) in tests.items():
  direction=(longs.astype("int8")-shorts.astype("int8")).to_numpy()
  used=set()
  for k in np.flatnonzero(direction):
   if k<240 or k+121>=len(d) or days[k] in used or np.isnan(atr.iat[k]):continue
   used.add(days[k])
   rec.append((name,int(k),int(direction[k]),days[k],float(atr.iat[k])))
 return pd.DataFrame(rec,columns=["strategy","signal_index","side","ny_date","atr"]).sort_values("signal_index"),ema20

def run_replay(d,e,ema):
 oo=d.open.to_numpy();hh=d.high.to_numpy();ll=d.low.to_numpy();cc=d.close.to_numpy()
 e20=ema.to_numpy()
 times=d.index
 out=[]
 for row in e.itertuples():
  j=int(row.signal_index)+1
  side=int(row.side)
  entry=float(oo[j])+side*SLIP
  split="discovery" if times[j]<HOLD else "holdout"
  for name,(maximum,base_stop,base_target,kind) in POLICIES.items():
   if kind=="atr":
    distance=float(np.clip(4*row.atr,120,350))
    stop_distance=distance
    target_distance=2*distance
   else:
    stop_distance=float(base_stop)
    target_distance=float(base_target) if base_target is not None else np.inf
   stop=entry-side*stop_distance
   target=entry+side*target_distance
   best=entry
   cause="timeout"
   exit_price=float(cc[j+maximum-1])
   held=maximum
   pending_ema=False
   for z in range(maximum):
    k=j+z
    if pending_ema:
     exit_price=float(oo[k]);held=z+1;cause="ema";break
    hit_stop=(ll[k]<=stop if side>0 else hh[k]>=stop)
    hit_target=(hh[k]>=target if side>0 else ll[k]<=target)
    if hit_stop:
     exit_price=stop;held=z+1;cause="stop";break
    if hit_target:
     exit_price=target;held=z+1;cause="target";break
    best=max(best,hh[k]) if side>0 else min(best,ll[k])
    favorable=side*(best-entry)
    # Every stop modification takes effect NEXT minute, not within current minute.
    if kind=="be" and favorable>=200:
     candidate=entry+side*10
     stop=max(stop,candidate) if side>0 else min(stop,candidate)
    if kind=="trail" and favorable>=200:
     candidate=best-side*150
     stop=max(stop,candidate) if side>0 else min(stop,candidate)
    if kind=="ema" and z>=4 and z+1<maximum and side*(cc[k]-e20[k])<0:
     pending_ema=True
   fill_exit=exit_price-side*SLIP
   gross=side*(fill_exit-entry)
   fee=FEE*(entry+fill_exit)
   net=gross-fee
   out.append((row.strategy,row.ny_date,str(times[j]),split,side,name,cause,held,
               round(gross,3),round(fee,3),round(net,3)))
 return pd.DataFrame(out,columns=["strategy","ny_date","entry_utc","split","side",
    "exit","cause","minutes_held","gross_points","fees_points","net_points"])

def statistics(trades):
 stats=[]
 for (strategy,policy,split),x in trades.sort_values("entry_utc").groupby(["strategy","exit","split"]):
  r=x.net_points.to_numpy()
  running=np.cumsum(r)
  draw=np.maximum.accumulate(np.concatenate(([0],running)))[1:]-running
  stats.append(dict(strategy=strategy,exit=policy,split=split,n=len(x),
      win_pct=round(100*(r>0).mean(),2),avg_gross=round(x.gross_points.mean(),2),
      avg_fee=round(x.fees_points.mean(),2),avg_net=round(r.mean(),2),
      median_net=round(np.median(r),2),net200_pct=round(100*(r>=200).mean(),2),
      net500_pct=round(100*(r>=500).mean(),2),
      target_pct=round(100*(x.cause=="target").mean(),2),
      stop_pct=round(100*(x.cause=="stop").mean(),2),
      max_dd=round(float(draw.max()),1),
      total_net=round(float(r.sum()),1)))
 return pd.DataFrame(stats).sort_values(["strategy","exit","split"])

def main():
 OUT.mkdir(parents=True,exist_ok=True)
 d,nfiles=load()
 entries,ema=candidates(d)
 if entries.empty:raise RuntimeError("No entry events")
 trades=run_replay(d,entries,ema)
 stats=statistics(trades)
 entries.to_csv(OUT/"entries.csv",index=False)
 trades.to_csv(OUT/"trades.csv",index=False)
 stats.to_csv(OUT/"exit_comparison.csv",index=False)
 discovery=stats[(stats.split=="discovery")&(stats.n>=30)]
 # Top two exit choices per entry based on discovery ONLY, then report holdout.
 chosen=discovery.sort_values("avg_net",ascending=False).groupby("strategy").head(2)
 paired=chosen.merge(stats[stats.split=="holdout"],on=["strategy","exit"],
       suffixes=("_discovery","_holdout"))
 paired.to_csv(OUT/"training_selected_exits_holdout.csv",index=False)
 quality=dict(months=nfiles,bars=len(d),start=str(d.index.min()),end=str(d.index.max()),
   zero_volume=int((d.volume==0).sum()),entry_events=len(entries),
   exit_simulations=len(trades),holdout_start="2026-07-01",taker_fee=0.0005,
   gst_on_fee=0.18,slippage_points_per_side=SLIP)
 (OUT/"quality.json").write_text(json.dumps(quality,indent=2)+"\n")
 lines=[
 "# Delta BTCUSD 1m: exit policy comparison",
 "",
 "This is a real-1m OHLCV, execution-aware research **simulation**, not a guarantee of daily 200–500 points.",
 "Source: actual Delta Exchange India BTCUSD 1m perpetual future; 5 one-minute entry types; 10 exit methods. Every exit on an entry uses the exact same entry timestamp.",
 "Holdout: July 1 through October 17 2026; train before this date. Only first eligible entry per NY weekday per strategy (no trades required every day).",
 "Entry price: next 1m open plus adverse $5 price points. Exit: stop/target touch or timed close, minus adverse $5 points.",
 "Both stop and target in same 1m bar = stop (pessimistic). Trailing/BE decisions update only for next 1m bar.",
 "Futures fee assumed 0.05% taker per side, plus GST 18% on fees, deducted from modeled fills. No bid/ask, funding, market impact, or guaranteed fills.",
 "Price points are per 1 BTC exposure; multiply by contract exposure (e.g. 0.001 BTC) for approximate dollar P&L.",
 "",
 "## Data quality","~~~json",json.dumps(quality,indent=2),"~~~","",
 "## Discovery-selected exits, evaluated on holdout",
 paired[["strategy","exit","n_discovery","avg_net_discovery",
     "win_pct_discovery","n_holdout","avg_net_holdout",
     "win_pct_holdout","net200_pct_holdout","max_dd_holdout"]].to_markdown(index=False) if len(paired) else "Insufficient discovery candidates.",
 "",
 "## Every exit in holdout",
 stats[stats.split=="holdout"][["strategy","exit","n","win_pct","avg_net",
     "net200_pct","net500_pct","max_dd"]].to_markdown(index=False),
 "",
 "## Exit policies",
 "- time15_sl250 / time30_sl250 / time60_sl250: time-based, $250 hard stop.",
 "- tp200_sl150 / tp300_sl200 / tp500_sl250: fixed target/stop; 120m max.",
 "- tp500_sl250_be200: move stop to +10 points after +200 favorable excursion; takes effect NEXT minute.",
 "- tp500_sl250_trail150: start trailing best price minus 150 points after +200 favorable excursion; next minute.",
 "- atr4_2R: past-only 60-minute 1m ATR; stop clipped 120–350, target 2x stop; maximum 120 minutes.",
 "- ema20_exit_sl250: after 5m, close below/above 1m EMA20 triggers next-minute open exit; 250 stop, 60m max.",
 "",
 "## Cautions",
 "OHLCV has no actual bid/ask and cannot establish real executable stop prices. Zero-volume candles require separate feed QA.",
 "Some variants have small samples and discovery bias; a positive holdout row is not by itself proof of sustained edge.",
 "Trading every day is not required; do not optimize exit rules solely to achieve daily frequency.",
 "",
 "See entries.csv, trades.csv, exit_comparison.csv, training_selected_exits_holdout.csv."
 ]
 (OUT/"RESEARCH_REPORT.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
 print("EXIT_RESEARCH_COMPLETE",json.dumps(quality))
 print(paired[["strategy","exit","n_discovery","avg_net_discovery","n_holdout","avg_net_holdout"]].to_string(index=False))
if __name__=="__main__":main()
