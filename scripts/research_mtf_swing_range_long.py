#!/usr/bin/env python3
"""Long-only BTCUSD 30m uptrend and 1m swing/range breakout, timezone comparison."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path("data/delta_india/BTCUSD/1m")
OUT=Path("analysis/mtf_swing_range_long")
FEE=.0005*1.18
SLIP=5.
SESSIONS=["ALL_UTC","WEEKDAYS_ALL","NY_OPEN","LONDON_OPEN","ASIA_SINGAPORE","INDIA_MORNING"]
SETUPS=["range5_break","range24_break","swing_break","swing_range24_break","range24_low_reclaim"]
TRENDS=["bullish_candle","hhhl_structure"]
TARGET_R=(1.5,2.)
def load():
    frames=[]
    for p in sorted(ROOT.glob("20??-??.csv.gz")):
        a=pd.read_csv(p,compression="gzip",usecols=["time","open","high","low","close"])
        a["time"]=pd.to_datetime(a.time.astype("int64"),unit="s",utc=True)
        frames.append(a.set_index("time"))
    if not frames:raise RuntimeError("No Delta BTCUSD 1m candles")
    f=pd.concat(frames).sort_index()
    if f.index.has_duplicates or f.isna().any().any() or not f.index.to_series().diff().iloc[1:].eq(pd.Timedelta(minutes=1)).all():
        raise ValueError("Invalid 1m history, no fabrication")
    return f
def session_masks(idx):
    ny=idx.tz_convert("America/New_York")
    lon=idx.tz_convert("Europe/London")
    sg=idx.tz_convert("Asia/Singapore")
    ind=idx.tz_convert("Asia/Kolkata")
    def clocks(x,start,end):
        minute=x.hour*60+x.minute
        return (x.dayofweek<5)&(minute>=start)&(minute<end)
    return {
        "ALL_UTC":np.ones(len(idx),dtype=bool),
        "WEEKDAYS_ALL":np.asarray(idx.dayofweek<5),
        "NY_OPEN":np.asarray(clocks(ny,570,720)),
        "LONDON_OPEN":np.asarray(clocks(lon,480,660)),
        "ASIA_SINGAPORE":np.asarray(clocks(sg,540,720)),
        "INDIA_MORNING":np.asarray(clocks(ind,540,720))
    }
def prepare(f):
    idx=f.index; hi=f.high;lo=f.low;cl=f.close
    h=f.resample("30min",label="left",closed="left").agg({"open":"first","high":"max","low":"min","close":"last"})
    counts=cl.resample("30min").count()
    if not (counts==30).all():raise ValueError("partial 30m")
    b=(h.close>h.open)&(h.close>h.close.shift(1))
    st=(h.high>h.high.shift(1))&(h.low>h.low.shift(1))&(h.close>h.close.shift(1))&(h.close>h.open)
    # bar indexed at 30m opening t; map t+30m to first available 1m.
    tr={}
    for name,series in [("bullish_candle",b),("hhhl_structure",st)]:
        shifted=series.shift(1).reindex(idx,method="ffill").fillna(False)
        tr[name]=shifted.to_numpy(bool)
    levels={}
    for n in (5,24):
        levels[f"high{n}"]=hi.shift(1).rolling(n,min_periods=n).max().to_numpy(float)
        levels[f"low{n}"]=lo.shift(1).rolling(n,min_periods=n).min().to_numpy(float)
    # fractal pivot at i-3; confirmed after the third right candle i closed.
    # Maximum/minimum on 7 candles, avoiding future usage when signal tested.
    window_hi=hi.rolling(7,min_periods=7).max()
    window_lo=lo.rolling(7,min_periods=7).min()
    ph=hi.shift(3).where(hi.shift(3)==window_hi).ffill()
    pl=lo.shift(3).where(lo.shift(3)==window_lo).ffill()
    # at minute i, pivot output is known at END of that minute.
    levels["pivot_high"]=ph.to_numpy(float)
    levels["pivot_low"]=pl.to_numpy(float)
    op=f.open.to_numpy(float); close=f.close.to_numpy(float)
    bull=candle=(close>op)
    previous_close=np.r_[np.nan,close[:-1]]
    signals={}
    signals["range5_break"]=(close>levels["high5"])&(previous_close<=levels["high5"])
    signals["range24_break"]=(close>levels["high24"])&(previous_close<=levels["high24"])
    signals["swing_break"]=(close>levels["pivot_high"])&(previous_close<=levels["pivot_high"])
    combined=np.maximum(levels["pivot_high"],levels["high24"])
    signals["swing_range24_break"]=(close>combined)&(previous_close<=combined)
    signals["range24_low_reclaim"]=(lo.to_numpy(float)<levels["low24"])&(close>levels["low24"])&bull&(np.isfinite(levels["pivot_low"]))&(lo.to_numpy(float)<=levels["pivot_low"]+150)
    return tr,levels,signals
def sim(f,trends,levels,signals):
    idx=f.index; n=len(idx)
    op=f.open.to_numpy(float); hi=f.high.to_numpy(float); lo=f.low.to_numpy(float); close=f.close.to_numpy(float)
    sm=session_masks(idx)
    settlement=np.asarray((idx.hour%8==0)&(idx.minute==0),dtype=np.int32)
    cum=np.r_[0,np.cumsum(settlement)]
    ledger=[]
    for trend in TRENDS:
      for setup in SETUPS:
       valid=np.flatnonzero(signals[setup]&trends[trend])
       for session in SESSIONS:
        mask=sm[session]
        for r in TARGET_R:
          last_exit=-1
          for k in valid:
            ent=k+1
            if ent>=n-121 or not mask[ent] or ent<=last_exit:continue
            # Exclude expected settlements across the full possible 2-hour exposure.
            if cum[ent+121]-cum[ent]>0:continue
            support=levels["low24"][k]
            swing=levels["pivot_low"][k]
            if not np.isfinite(support):continue
            # Use nearest available support below entry.
            candidates=[x for x in (support,swing) if np.isfinite(x) and x<op[ent]]
            if not candidates:continue
            stop_base=max(candidates)
            if setup=="range24_low_reclaim":stop_base=min(lo[k],stop_base)
            stop=stop_base-5.
            fill_in=op[ent]+SLIP
            distance=fill_in-stop
            if distance<60 or distance>500:continue
            tp=fill_in+r*distance
            hit=None;exit_mid=None;kind=None
            for j in range(ent,ent+120):
                # gap through stop worsens exit; conservative OHLC stop before TP.
                if op[j]<=stop:
                    hit=j;exit_mid=op[j];kind="stop_gap";break
                if lo[j]<=stop:
                    hit=j;exit_mid=stop;kind="stop";break
                if hi[j]>=tp:
                    hit=j;exit_mid=tp;kind="target";break
            if hit is None:
                # 120 minutes elapsed; close at the following minute open
                hit=ent+120;exit_mid=op[hit];kind="timeout"
            fill_out=exit_mid-SLIP
            gross=exit_mid-op[ent]
            net=fill_out-fill_in-FEE*(fill_in+fill_out)
            last_exit=hit
            t=idx[ent]
            period="train" if t.year==2025 else ("validation" if t<pd.Timestamp("2026-07-01",tz="UTC") else "recheck_seen")
            ledger.append(dict(trend=trend,setup=setup,session=session,target_r=r,period=period,
                entry_utc=str(t),exit_utc=str(idx[hit]),duration_min=hit-ent,
                entry=round(fill_in,3),exit=round(fill_out,3),risk_pts=round(distance,2),
                exit_reason=kind,gross_pts=round(gross,3),net_pts=round(net,3),
                fee_slippage_pts=round(gross-net,3)))
    return pd.DataFrame(ledger)
def report(tr):
    rows=[]
    for trend in TRENDS:
     for setup in SETUPS:
      for session in SESSIONS:
       for r in TARGET_R:
        for period in ("train","validation","recheck_seen"):
         d=tr[(tr.trend==trend)&(tr.setup==setup)&(tr.session==session)&(tr.target_r==r)&(tr.period==period)]
         vals=d.net_pts.to_numpy(float)
         if len(vals):
          wins=vals[vals>0].sum();loss=-vals[vals<0].sum()
          cum=np.r_[0,vals.cumsum()]
          result=dict(trades=len(d),mean_net_pts=round(float(vals.mean()),2),
            win_pct=round(100*float(np.mean(vals>0)),2),
            profit_factor=round(float(wins/loss),3) if loss else None,
            max_drawdown_pts=round(float((np.maximum.accumulate(cum)-cum).max()),2),
            median_duration_min=round(float(d.duration_min.median()),1),
            mean_gross_pts=round(float(d.gross_pts.mean()),2),
            mean_cost_pts=round(float(d.fee_slippage_pts.mean()),2),
            trade_days=d.entry_utc.str[:10].nunique())
         else:result=dict(trades=0,mean_net_pts=None,win_pct=None,profit_factor=None,
            max_drawdown_pts=None,median_duration_min=None,mean_gross_pts=None,mean_cost_pts=None,trade_days=0)
         rows.append(dict(trend=trend,setup=setup,session=session,target_r=r,period=period,**result))
    return pd.DataFrame(rows)
def main():
 OUT.mkdir(parents=True,exist_ok=True)
 f=load()
 trends,levels,signals=prepare(f)
 tr=sim(f,trends,levels,signals)
 if tr.empty:raise RuntimeError("No eligible trades")
 stats=report(tr)
 stats.to_csv(OUT/"all_combinations.csv",index=False)
 tr.to_csv(OUT/"trade_ledger.csv.gz",index=False,compression="gzip")
 summary=dict(rows_1m=len(f),first_utc=str(f.index[0]),last_utc=str(f.index[-1]),
              all_trades_across_overlapping_scenarios=len(tr),combinations=len(stats),
              fee_each_side_including_gst=FEE,slippage_points_per_side=SLIP,
              mode="LONG BTCUSD futures, next-minute proxy fills, no real L1, no true independent holdout")
 (OUT/"quality.json").write_text(json.dumps(summary,indent=2)+"\n")
 baseline=stats[(stats.session=="ALL_UTC")&(stats.trades>=25)]
 val=baseline[baseline.period=="validation"].sort_values("mean_net_pts",ascending=False)
 summary_sessions=stats[(stats.period=="validation")&(stats.trades>=25)].sort_values("mean_net_pts",ascending=False)
 lines=["# 30m bullish regime / 1m swing + range long research",
 "","Research only. Levels formed using completed candles; confirmed swing pivots require three right-hand completed 1m candles. No invented market depth.",
 "","## Dataset, fees and execution",json.dumps(summary,indent=2),
 "","## Unfiltered (all trading hours) Jan-Jun 2026 validation, at least 25 trades",
 val.to_markdown(index=False) if len(val) else "No configurations with 25 trades.",
 "","## Session-based Jan-Jun 2026, at least 25 trades",
 summary_sessions.head(60).to_markdown(index=False) if len(summary_sessions) else "None.",
 "","## Every combination (includes zero-trade configurations)",stats.to_markdown(index=False),
 "","## Important limitations",
 "- Results overlap across strategies/sessions and cannot be summed.",
 "- Jul-Oct 2026 already exposed to previous research; NOT globally untouched holdout.",
 "- No historical bid/ask, queueing, live fill probability or margin liquidation model.",
 "- Realistic next 1m bar price is a proxy, gaps through stops handled adversely, intrabar SL hit before TP.",
 "- Stop level uses previously confirmed 1m pivot/range support; trailing is not tested.",
 "- Signals require a completed 30m regime condition. Signal timezone is UTC; NY and London session conversions automatically apply daylight saving.",
 "- Funding payments are not reconstructed; any trade possibly spanning a nominal settlement timestamp was excluded.",
 "- Multiple-hypothesis search risk; a result in one time window is not sufficient proof of edge."]
 (OUT/"RESEARCH_REPORT.md").write_text("\n".join(lines)+"\n")
 print("MTF_SWING_RANGE_COMPLETED",json.dumps(summary),flush=True)
 print("TOP_UNFILTERED_VALIDATION",val.head(20).to_string(index=False),flush=True)
 print("TOP_SESSIONS_VALIDATION",summary_sessions.head(20).to_string(index=False),flush=True)
if __name__=="__main__":main()
