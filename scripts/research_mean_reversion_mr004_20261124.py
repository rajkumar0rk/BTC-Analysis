#!/usr/bin/env python3
"""MR004 Freqtrade CombinedBinHAndCluc source SIGNAL transfer; causal Delta 1m replay."""
import json, hashlib
from pathlib import Path
import numpy as np
import pandas as pd
from research_every_candle_200 import read_archive

OUT=Path("analysis/mean_reversion_research/MR004/results")
FEE=0.0005*1.18
MONTHS=pd.period_range("2025-01","2026-10",freq="M").astype(str).tolist()

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    raw,starts,ends,quality=read_archive()
    raw=raw.loc[raw.index<pd.Timestamp("2026-11-01",tz="Asia/Kolkata").tz_convert("UTC")].copy()
    # Complete 5m source candles; no indicators across archive gaps.
    bars=raw.resample("5min",label="left",closed="left").agg(
        {"open":"first","high":"max","low":"min","close":"last","volume":"sum","time":"count"})
    complete=bars.time.eq(5)
    grp=(~complete).cumsum()
    events={}
    for _,part in bars[complete].groupby(grp[complete]):
        if len(part)<55:continue
        c=part.close; typical=(part.high+part.low+c)/3
        mid40=c.rolling(40,min_periods=40).mean()
        lower40=mid40-2*c.rolling(40,min_periods=40).std(ddof=1)
        bbdelta=(mid40-lower40).abs()
        closedelta=c.diff().abs()
        tail=(c-part.low).abs()
        bbmid=typical.rolling(20,min_periods=20).mean()
        bblower=bbmid-2*typical.rolling(20,min_periods=20).std(ddof=0)
        ema50=c.ewm(span=50,adjust=False,min_periods=50).mean()
        volmean=part.volume.rolling(30,min_periods=30).mean().shift(1)
        binh=(lower40.shift(1)>0)&(bbdelta>c*.008)&(closedelta>c*.0175)&(tail<bbdelta*.25)&(c<lower40.shift(1))&(c<=c.shift(1))
        cluc=(c<ema50)&(c<.985*bblower)&(part.volume<volmean*20)
        enter=(binh|cluc).fillna(False)
        exitmid=(c>bbmid).fillna(False)
        for t in part.index:
            ts=t+pd.Timedelta(minutes=5)
            if bool(enter.loc[t]):events[ts]=("enter",1,0.)
            elif bool(exitmid.loc[t]):events[ts]=("exit",1,0.)
    op=raw.open.to_numpy(float);hi=raw.high.to_numpy(float)
    lo=raw.low.to_numpy(float);cl=raw.close.to_numpy(float)
    times=raw.index
    nav=np.full(len(raw),np.nan)
    cash=1.;peak=1.;maxdd=0.;position=None;trades=[]
    # A signal timestamp corresponds exactly to the next eligible minute open.
    # Only one action per minute; stop takes priority over exit signal.
    for j,ts in enumerate(times):
        if position is not None:
            p=position
            side=p["side"];stop=p["stop"];entry=p["entry"];qty=p["qty"]
            stop_hit=(lo[j]<=stop if side==1 else hi[j]>=stop)
            signal=events.get(ts)
            target=entry*1.05
            segment_end=(j==len(raw)-1 or (j+1<len(raw) and (times[j+1]-ts).total_seconds()!=60))
            reason=None;px=None
            if stop_hit:
                reason="stop";px=min(op[j],stop) if side==1 else max(op[j],stop)
            elif hi[j]>=target:
                reason="roi_5pct";px=max(op[j],target)
            elif signal and signal[0]=="exit" and signal[1]==side and op[j]>entry:
                reason="profit_only_midline";px=op[j]
            elif segment_end:
                reason="archive_gap_or_end";px=cl[j]
            if reason:
                gross=side*qty*(px-entry)
                feeout=qty*px*FEE
                cash+=gross-feeout
                trades.append(dict(entry_utc=str(times[p["entry_idx"]]),exit_utc=str(ts),
                    side=side,entry_price=entry,exit_price=px,stop_initial=p["stop"],
                    quantity=qty,gross_pnl=gross,entry_fee=p["entry_fee"],
                    exit_fee=feeout,net_pnl=gross-p["entry_fee"]-feeout,
                    nav_before=p["nav_before"],nav_after=cash,reason=reason))
                position=None
        # Entry at minute OPEN after completed 5m close, not if exit on this minute.
        if position is None and (not trades or trades[-1]["exit_utc"]!=str(ts)):
            signal=events.get(ts)
            if signal and signal[0]=="enter":
                _,side,_=signal
                entry=op[j];stop=entry*.95
                if entry>0 and (j+1<len(raw)) and (times[j+1]-ts).total_seconds()==60:
                    # Matched 1% NAV stop risk; 1x notional cap.
                    qty=min(cash/entry,.01*cash/(entry-stop))
                    if qty>0:
                        before=cash;fee=qty*entry*FEE;cash-=fee
                        position=dict(side=side,entry=entry,stop=stop,qty=qty,
                                      entry_idx=j,entry_fee=fee,nav_before=before)
                        # Entry-minute stop-first, then ROI target.
                        if lo[j]<=stop or hi[j]>=entry*1.05:
                            px=min(op[j],stop) if lo[j]<=stop else max(op[j],entry*1.05)
                            gross=side*qty*(px-entry);feeout=qty*px*FEE
                            cash+=gross-feeout
                            trades.append(dict(entry_utc=str(ts),exit_utc=str(ts),
                                side=side,entry_price=entry,exit_price=px,stop_initial=stop,
                                quantity=qty,gross_pnl=gross,entry_fee=fee,
                                exit_fee=feeout,net_pnl=gross-fee-feeout,
                                nav_before=before,nav_after=cash,reason="entry_minute_stop" if lo[j]<=stop else "entry_minute_roi"))
                            position=None
        mark=cash if position is None else cash+position["side"]*position["qty"]*(cl[j]-position["entry"])
        nav[j]=mark;peak=max(peak,mark);maxdd=max(maxdd,1-mark/peak)
    if position is not None:
        raise RuntimeError("Position unexpectedly remains open")
    ledger=pd.DataFrame(trades)
    if ledger.empty:raise RuntimeError("No completed trades; inspect source signals")
    assert abs(1+ledger.net_pnl.sum()-cash)<1e-8
    navs=pd.Series(nav,index=times,name="nav")
    # Monthly IST month-end mark-to-market, including any open trade.
    ends_ist=navs.tz_convert("Asia/Kolkata").resample("ME").last()
    monthly=[];previous=1.
    for month in MONTHS:
        values=[float(v) for t,v in ends_ist.items() if t.strftime("%Y-%m")==month]
        if not values:raise RuntimeError("Missing month "+month)
        value=values[0]
        monthly.append(dict(month_ist=month,end_nav=value,net_return_pct=100*(value/previous-1),
            trade_entries=sum(pd.Timestamp(x).tz_convert("Asia/Kolkata").strftime("%Y-%m")==month for x in ledger.entry_utc)))
        previous=value
    m=pd.DataFrame(monthly)
    ledger.to_csv(OUT/"trade_ledger.csv",index=False)
    m.to_csv(OUT/"monthly_ist_nav.csv",index=False)
    navs.to_csv(OUT/"minute_nav.csv.gz",compression="gzip")
    pf=float(ledger.loc[ledger.net_pnl>0,"net_pnl"].sum()/(-ledger.loc[ledger.net_pnl<0,"net_pnl"].sum())) if (ledger.net_pnl<0).any() else None
    result=dict(source_commit="eff78d3ce3456b52c68a4e9a33cc055a56b801ff",
        source_signal="Combined BinHV45 capitulation OR Cluc EMA50 lower BB excursion, 5% ROI/stop, profit-only middle-band exit",
        transfer="Original 5m long-only signals to BTC futures 1m execution; archive-gap liquidation",
        data_quality=quality,trades=len(ledger),net_return_pct=100*(cash-1),
        profit_factor_net=pf,max_minute_close_dd_pct=100*maxdd,
        positive_months=int((m.net_return_pct>0).sum()),
        losing_months=int((m.net_return_pct<0).sum()),
        flat_months=int((m.net_return_pct==0).sum()),
        gross_pnl=float(ledger.gross_pnl.sum()),fees_gst=float(ledger.entry_fee.sum()+ledger.exit_fee.sum()),
        funding="UNMODELED",slippage_points_per_side=0)
    (OUT/"summary.json").write_text(json.dumps(result,indent=2,default=str))
    print(json.dumps({k:v for k,v in result.items() if k!="data_quality"},indent=2))
if __name__=="__main__":main()
