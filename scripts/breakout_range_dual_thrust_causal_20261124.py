#!/usr/bin/env python3
"""BR-DT-001 causal repair/adaptation of pinned Dual Thrust; NOT original-source parity."""
import csv, hashlib, json, math
from pathlib import Path
import numpy as np
import pandas as pd
from zoneinfo import ZoneInfo
from breakout_range_wavelet_daily_replay import load
OUT=Path("analysis/breakout_range_dual_thrust_causal_20261124")
FEE=.0005*1.18
NY=ZoneInfo("America/New_York")
IST=ZoneInfo("Asia/Kolkata")
def main():
    minute,hashes=load()
    minute=minute.loc[(minute.index>=pd.Timestamp("2025-01-01",tz="UTC"))&(minute.index<pd.Timestamp("2026-11-01",tz="UTC"))]
    ny=minute.index.tz_convert(NY)
    localdate=np.array(ny.date)
    clock=np.array(ny.hour*60+ny.minute)
    inside=(clock>=180)&(clock<720)
    sessions={}
    for date,part in minute.loc[inside].groupby(localdate[inside],sort=True):
        # NY DST session is always 03:00–11:59, 540 actual minute bars.
        if len(part)!=540 or not (part.index.to_series().diff().dropna()==pd.Timedelta(minutes=1)).all():continue
        sessions[date]=dict(open=float(part.open.iloc[0]),high=float(part.high.max()),low=float(part.low.min()),close=float(part.close.iloc[-1]),start=part.index[0])
    keys=sorted(sessions)
    thresholds={}
    for i in range(5,len(keys)):
        current=keys[i];prev=[sessions[x] for x in keys[i-5:i]]
        # Reject nonconsecutive calendar session history (BTC trades 7d).
        if any((keys[j]-keys[j-1]).days!=1 for j in range(i-4,i+1)):continue
        rng=max(max(x["high"] for x in prev)-min(x["close"] for x in prev),max(x["close"] for x in prev)-min(x["low"] for x in prev))
        anchor=sessions[current]["open"]
        if rng>0:thresholds[current]=(anchor+.5*rng,anchor-.5*rng,rng)
    cash=10000.;side=0;qty=0.;entry=0.;entry_fee=0.;entry_time=None;stop=0.
    pending=0;pending_date=None;trades=[];marks=[];active_date=None;used=0;last_time=None
    def close(t,px,why):
        nonlocal cash,side,qty,entry,entry_fee,entry_time,stop
        fee=qty*px*FEE;gross=side*qty*(px-entry)
        cash+=gross-fee
        trades.append(dict(entry_time=entry_time.isoformat(),exit_time=t.isoformat(),side=side,entry=entry,exit=px,qty=qty,gross=gross,entry_fee=entry_fee,exit_fee=fee,net=gross-entry_fee-fee,reason=why))
        side=0;qty=0.
    for t,row in minute.iterrows():
        date=t.tz_convert(NY).date();minute_of_day=t.tz_convert(NY).hour*60+t.tz_convert(NY).minute
        op=float(row.open);last_time=t
        # Session ends at 12:00 NY OPEN; do not hold through other hours.
        if side and (date!=active_date or minute_of_day>=720):close(t,op,"session_end")
        if pending and date==pending_date and 180<minute_of_day<720:
            if side and side!=pending:close(t,op,"reverse")
            if not side and date in thresholds:
                _,_,rng=thresholds[date]
                # Emergency structural stop is an explicitly labelled adaptation.
                dist=max(rng,op*.001)
                size=min(cash*.005/dist,cash/op)
                fee=size*op*FEE
                if size>0 and fee<cash:
                    cash-=fee;side=pending;qty=size;entry=op;entry_fee=fee;entry_time=t;active_date=date
                    stop=op-side*dist
            pending=0
        elif pending and (date!=pending_date or minute_of_day>=720):pending=0
        if side:
            if side==1 and float(row.low)<=stop:close(t,min(op,stop),"structural_stop")
            elif side==-1 and float(row.high)>=stop:close(t,max(op,stop),"structural_stop")
        # Signal on COMPLETED minute close; next minute OPEN only.
        if date in thresholds and 180<=minute_of_day<719:
            up,down,_=thresholds[date]
            direction=1 if float(row.close)>up else -1 if float(row.close)<down else 0
            if direction and direction!=side and direction!=pending:
                pending=direction;pending_date=date
        mark=cash+(side*qty*(float(row.close)-entry) if side else 0)
        marks.append((t,mark))
    if side:
        close(last_time,float(minute.close.iloc[-1]),"terminal")
        marks[-1]=(last_time,cash)
    OUT.mkdir(parents=True,exist_ok=True)
    trade=pd.DataFrame(trades,columns=["entry_time","exit_time","side","entry","exit","qty","gross","entry_fee","exit_fee","net","reason"])
    trade.to_csv(OUT/"trades.csv",index=False)
    nav=pd.DataFrame(marks,columns=["t","nav"]).set_index("t")
    m=nav.tz_convert(IST).nav.resample("MS").agg(["first","last","count"])
    m["prior_nav"]=m["last"].shift().fillna(10000.)
    m["net_pct"]=100*(m["last"]/m["prior_nav"]-1)
    m["expected"]=[int(((d+pd.DateOffset(months=1))-d)/pd.Timedelta(minutes=1)) for d in m.index]
    m["coverage"]=np.where(m["count"]==m["expected"],"complete","partial")
    if len(trade):
        exitmonths=pd.to_datetime(trade.exit_time,utc=True).dt.tz_convert(IST).dt.strftime("%Y-%m")
        counts=exitmonths.value_counts().to_dict()
        m["trades"]=[counts.get(d.strftime("%Y-%m"),0) for d in m.index]
    else:m["trades"]=0
    m.to_csv(OUT/"monthly_ist.csv")
    pnl=float(trade.net.sum());neg=float(-trade.loc[trade.net<0,"net"].sum());pos=float(trade.loc[trade.net>0,"net"].sum())
    summary=dict(candidate="BR-DT-001 causal adaptation, NOT original",source="https://github.com/je-suis-tm/quant-trading/blob/611b73f2c3f577ac5b28aaa19ac8c43d3236c7a5/Dual%20Thrust%20backtest.py",trades=len(trade),wins=int((trade.net>0).sum()),losses=int((trade.net<0).sum()),net_trade_pnl=pnl,ending_cash=cash,nav_reconciliation_error=cash-10000-pnl,profit_factor=pos/neg if neg else None,max_drawdown_pct=float((nav.nav/nav.nav.cummax()-1).min()*100),fees_gst=float(trade.entry_fee.sum()+trade.exit_fee.sum()),complete_positive_months=int(((m.net_pct>0)&(m.coverage=="complete")).sum()),complete_negative_months=int(((m.net_pct<0)&(m.coverage=="complete")).sum()),complete_flat_months=int(((m.net_pct==0)&(m.coverage=="complete")).sum()),session_count=len(thresholds),archive_hashes=hashes,funding="UNMODELED",slippage_per_side=0)
    assert abs(summary["nav_reconciliation_error"])<1e-6,summary
    (OUT/"summary.json").write_text(json.dumps(summary,indent=2,default=str))
    print(json.dumps({k:v for k,v in summary.items() if k!="archive_hashes"},indent=2))
if __name__=="__main__":main()
