#!/usr/bin/env python3
"""Independent daily failed-auction / false-breakout backtest, not a breakout trade.
First UTC 00:00-02:00 high/low is prior completed session reference.
After 02:00 wait for a 5-minute candle to sweep outside the reference
and CLOSE back inside. Fade sweep at next minute open. One trade/day.
Conservative standard Delta India taker 0.05% each side + GST 18%;
2bps per-side slippage, conservative 1bp funding debit per 8h boundary.
Fixed nominal 0.5% equity risk, max 2x notional; intraminute stop-first.
2025 parameter selection, 2026 research-exposed chronological check.
"""
from pathlib import Path
import pandas as pd
import numpy as np
import itertools,json
ROOT=Path("data/delta_india")
OUT=Path("analysis/daily_failed_breakout_20261119")
OUT.mkdir(parents=True,exist_ok=True)
START=1735689600
END=1794960000
FEE=.0005*1.18;SLIP=.0002;FUND=.0001
GRID=list(itertools.product((60,120,180),(.0002,.0005),(.0025,.005),(.003,.006),(60,180)))
def load(sym):
    paths=sorted((ROOT/sym/"1m").glob("20??-??.csv.gz"))
    d=pd.concat([pd.read_csv(p,compression="gzip",usecols=["time","open","high","low","close","volume"]) for p in paths],ignore_index=True)
    d=d[(d.time>=START)&(d.time<END)].sort_values("time").reset_index(drop=True)
    t=d.time.to_numpy(np.int64)
    if len(t)!=686*1440 or t[0]!=START or t[-1]!=END-60 or not np.all(np.diff(t)==60):
        raise ValueError(sym+" missing minute history: "+str(len(t)))
    for col in ("open","high","low","close","volume"):
        if not np.isfinite(d[col].to_numpy(float)).all():raise ValueError("nonfinite "+col)
    if (d.high<d.low).any() or (d.open<d.low).any() or (d.close<d.low).any() or (d.open>d.high).any() or (d.close>d.high).any():raise ValueError("invalid OHLC")
    return d,{"symbol":sym,"minute_rows":len(d),"source_files":len(paths),"missing_minutes":0}
def make_events(d):
    h=d.high.to_numpy(float).reshape(-1,1440)
    l=d.low.to_numpy(float).reshape(-1,1440)
    c=d.close.to_numpy(float).reshape(-1,1440)
    events={}
    for reference,penetration in itertools.product((60,120,180),(.0002,.0005)):
        rhi=h[:,:reference].max(axis=1);rlo=l[:,:reference].min(axis=1)
        byday={}
        for day in range(len(h)):
            # Completed 5-minute candle, then NEXT 1m open entry.
            for end in range(reference+5,1201,5):
                hi=float(h[day,end-5:end].max());lo=float(l[day,end-5:end].min())
                close=float(c[day,end-1])
                if hi>rhi[day]*(1+penetration) and rlo[day]<close<rhi[day]:
                    byday[day]=(day*1440+end,-1);break
                if lo<rlo[day]*(1-penetration) and rlo[day]<close<rhi[day]:
                    byday[day]=(day*1440+end,1);break
        events[(reference,penetration)]=byday
    return events
def replay(d,ev,config):
    ref,penetration,tp,sl,hold=config
    o=d.open.to_numpy(float);h=d.high.to_numpy(float);l=d.low.to_numpy(float);c=d.close.to_numpy(float);t=d.time.to_numpy(np.int64)
    eq=1000.;out=[]
    for day in range(len(d)//1440):
        before=eq;net=fee=fund=0.;traded=0
        if day in ev:
            k,side=ev[day]
            en=o[k]*(1+side*SLIP)
            qty=min(eq*.005/(en*sl),eq*2/en)
            stop=en*(1-side*sl);target=en*(1+side*tp)
            end=min(k+hold,(day+1)*1440)
            ex=c[end-1];j=end-1
            for v in range(k,end):
                if side==1:
                    if l[v]<=stop:ex=min(o[v],stop);j=v;break
                    if h[v]>=target:ex=target;j=v;break
                else:
                    if h[v]>=stop:ex=max(o[v],stop);j=v;break
                    if l[v]<=target:ex=target;j=v;break
            fill=ex*(1-side*SLIP)
            fee=qty*FEE*(en+fill)
            fund=qty*fill*FUND*sum(1 for v in range(k,j+1) if t[v]%28800==0)
            net=side*qty*(fill-en)-fee-fund
            eq+=net;traded=1
        out.append((day,before,eq,net,fee,fund,traded))
    return np.asarray(out,float)
def summary(sym,config,x,year):
    a=x[:365] if year==2025 else x[365:]
    pnl=a[:,3];wins=pnl[pnl>1e-7];losses=pnl[pnl<-1e-7]
    nav=np.r_[a[0,1],a[:,2]]
    ref,pen,tp,sl,hold=config
    streak=0;worst=0
    for v in pnl:
        streak=streak+1 if v<0 else 0;worst=max(streak,worst)
    return dict(symbol=sym,year=year,reference_minutes=ref,sweep_fraction=pen,
      target_fraction=tp,stop_fraction=sl,hold_minutes=hold,
      trades=int(a[:,6].sum()),profitable_days=len(wins),losing_days=len(losses),
      no_trade_days=int(len(a)-a[:,6].sum()),calendar_days=len(a),
      positive_calendar_day_pct=round(100*len(wins)/len(a),3),
      profit_factor=round(float(wins.sum()/-losses.sum()),4) if len(losses) else None,
      net_return_pct=round(100*(a[-1,2]/a[0,1]-1),4),
      max_dayclose_drawdown_pct=round(100*float(np.min(nav/np.maximum.accumulate(nav)-1)),4),
      max_consecutive_losing_days=worst,
      worst_day_usd=round(float(pnl.min()),4),
      avg_day_usd=round(float(pnl.mean()),4),
      median_day_usd=round(float(np.median(pnl)),4),
      fees_usd=round(float(a[:,4].sum()),4),
      funding_debit_usd=round(float(a[:,5].sum()),4))
def main():
    rows=[];selected=[];months=[];quality=[]
    for sym in ("BTCUSD","ETHUSD"):
        print("LOAD",sym,flush=True)
        d,q=load(sym);quality.append(q)
        events=make_events(d)
        candidates=[]
        for config in GRID:
            x=replay(d,events[config[:2]],config)
            a=summary(sym,config,x,2025)
            b=summary(sym,config,x,2026)
            rows.extend((a,b));candidates.append((config,x,a,b))
        eligible=[z for z in candidates if z[2]["net_return_pct"]>0 and z[2]["profit_factor"] is not None and z[2]["profit_factor"]>1 and z[2]["trades"]>=50]
        if eligible:
            chosen=max(eligible,key=lambda z:(z[2]["positive_calendar_day_pct"],z[2]["net_return_pct"]))
        else:
            chosen=max(candidates,key=lambda z:(z[2]["net_return_pct"],z[2]["positive_calendar_day_pct"]))
        config,x,a,b=chosen
        selected.extend((dict(a,train_pass=bool(eligible)),dict(b,train_pass=bool(eligible))))
        for year,yearrows in ((2025,x[:365]),(2026,x[365:])):
            dates=pd.date_range(f"{year}-01-01",periods=len(yearrows),freq="D",tz="UTC")
            for month in pd.unique(dates.strftime("%Y-%m")):
                sub=yearrows[dates.strftime("%Y-%m")==month]
                months.append(dict(symbol=sym,month_utc=month,net_return_pct=round(100*(sub[-1,2]/sub[0,1]-1),4),
                 trades=int(sub[:,6].sum()),profitable_days=int((sub[:,3]>0).sum()),
                 losing_days=int((sub[:,3]<0).sum()),no_trade_days=int((sub[:,6]==0).sum())))
        print("SELECTED",sym,config,"train passed",bool(eligible),a,b,flush=True)
    pd.DataFrame(rows).to_csv(OUT/"summary.csv",index=False)
    pd.DataFrame(selected).to_csv(OUT/"selected.csv",index=False)
    pd.DataFrame(months).to_csv(OUT/"selected_monthly.csv",index=False)
    meta=dict(study="UTC session opening-range FALSE breakout fade",
      novelty="Unlike opening-range continuation, this waits for a completed 5m sweep and CLOSE back inside the range, then fades it.",
      parameters_per_symbol=len(GRID),data_quality=quality,
      costs=dict(taker_with_GST_per_side=FEE,slippage_per_side=SLIP,assumed_funding_debit_per_8h=FUND),
      selection="2025 >=50 trades, PF>1, net>0; highest calendar positive days; 2026 unchanged",
      caveats=["2026 already research-exposed, not independent forward validation",
       "No exact funding, orderbook, tick-size, lot-size, exchange margin or liquidation replay",
       "Stop-first ambiguity; one trade max per UTC day; 2026 November partial",
       "Cannot promise daily profit"])
    (OUT/"quality.json").write_text(json.dumps(meta,indent=2)+"\n")
    (OUT/"REPORT.md").write_text("# Daily false-breakout research\n\n"+pd.DataFrame(selected).to_string(index=False)+"\n\n"+json.dumps(meta,indent=2)+"\n")
if __name__=="__main__":main()
