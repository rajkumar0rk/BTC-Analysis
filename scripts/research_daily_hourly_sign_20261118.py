#!/usr/bin/env python3
"""Novel family: fixed UTC clock-hour directional sign persistence vs reversal,
conditional on PREVIOUS completed hour realized range, with one entry/day.
Not breakout, VWAP, wick, carry or cross-asset. Train 2025, replay 2026.
"""
from pathlib import Path
import numpy as np,pandas as pd,itertools,json
ROOT=Path("data/delta_india"); OUT=Path("analysis/daily_hourly_sign_20261118")
OUT.mkdir(parents=True,exist_ok=True)
START=1735689600;END=1794960000 # 2025-01-01 to 2026-11-18 UTC
FEE=.0005*1.18;SLIP=.0002;FUND=.0001
RISK=.005;LEVERAGE=2.;CAP=1000.
HOURS=tuple(range(1,24))
MODES=("follow","fade")
REGIMES=("all","range_high","range_low")
TARGETS=(.003,.006)
STOPS=(.003,.006)
HOLDS=(30,120)
def load(sym):
    files=sorted((ROOT/sym/"1m").glob("20??-??.csv.gz"))
    if len(files)<22:raise ValueError("Insufficient "+sym+" files")
    d=pd.concat((pd.read_csv(p,compression="gzip",usecols=["time","open","high","low","close","volume"]) for p in files),ignore_index=True)
    d=d[(d.time>=START)&(d.time<END)].sort_values("time").reset_index(drop=True)
    t=d.time.to_numpy(np.int64)
    assert len(d)==(END-START)//60 and t[0]==START and t[-1]==END-60 and np.all(np.diff(t)==60)
    assert np.isfinite(d[["open","high","low","close","volume"]].to_numpy(float)).all()
    assert (d.high>=d.low).all() and (d.open<=d.high).all() and (d.open>=d.low).all()
    return d,dict(symbol=sym,rows=len(d),source_months=len(files),missing_minutes=0)
def make_signals(d):
    o=d.open.to_numpy(float);h=d.high.to_numpy(float);l=d.low.to_numpy(float);c=d.close.to_numpy(float)
    n=len(d); assert n%1440==0
    hours=n//60
    # hourly candles start at 00 UTC; hour h entry uses only completed h-1.
    hourly_open=o[::60];hourly_close=c[59::60]
    hourly_high=h.reshape(-1,60).max(axis=1)
    hourly_low=l.reshape(-1,60).min(axis=1)
    sign=np.sign(hourly_close-hourly_open)
    rng=(hourly_high-hourly_low)/hourly_open
    prior_median=pd.Series(rng).shift(1).rolling(48,min_periods=48).median().to_numpy()
    events={}
    for hr,mode,reg in itertools.product(HOURS,MODES,REGIMES):
        byday={}
        for day in range(n//1440):
            houridx=day*24+hr
            prev=houridx-1
            if prev<48 or sign[prev]==0:continue
            if reg=="range_high" and not(rng[prev]>prior_median[prev]):continue
            if reg=="range_low" and not(rng[prev]<=prior_median[prev]):continue
            side=int(sign[prev])*(1 if mode=="follow" else -1)
            byday[day]=(houridx*60,side)
        events[(hr,mode,reg)]=byday
    return events
def run(d,ev,params):
    hr,mode,reg,tp,sl,hold=params
    o=d.open.to_numpy(float);h=d.high.to_numpy(float);l=d.low.to_numpy(float);c=d.close.to_numpy(float);t=d.time.to_numpy(np.int64)
    equity=CAP;records=[]
    for day in range(len(d)//1440):
        before=equity;pnl=0.;fees=0.;fund=0.;trade=0
        if day in ev:
            k,side=ev[day];entry=float(o[k])*(1+side*SLIP)
            qty=min(equity*RISK/(sl*entry),equity*LEVERAGE/entry)
            target=entry*(1+side*tp);stop=entry*(1-side*sl)
            end=min(k+hold,(day+1)*1440)
            j=end-1;px=float(c[j])
            for i in range(k,end):
                if side==1:
                    if l[i]<=stop:j=i;px=min(float(o[i]),stop);break
                    if h[i]>=target:j=i;px=target;break
                else:
                    if h[i]>=stop:j=i;px=max(float(o[i]),stop);break
                    if l[i]<=target:j=i;px=target;break
            exitfill=px*(1-side*SLIP)
            fees=qty*FEE*(entry+exitfill)
            fund=qty*FUND*exitfill*sum(1 for i in range(k,j+1) if t[i]%28800==0)
            pnl=side*qty*(exitfill-entry)-fees-fund
            equity+=pnl;trade=1
        records.append((day,before,equity,pnl,fees,fund,trade))
    return np.asarray(records,float)
def metric(sym,params,arr,year):
    a=arr[:365] if year==2025 else arr[365:]
    wins=a[:,3][a[:,3]>1e-8];loss=a[:,3][a[:,3]<-1e-8]
    nav=np.r_[a[0,1],a[:,2]]
    lossamt=-loss.sum();pf=float(wins.sum()/lossamt) if lossamt>0 else None
    hr,mode,reg,tp,sl,hold=params
    streak=0;maxstreak=0
    for p in a[:,3]:
        streak=streak+1 if p<-1e-8 else 0;maxstreak=max(maxstreak,streak)
    return dict(symbol=sym,year=year,entry_hour_utc=hr,direction=mode,volatility_regime=reg,
      take_pct=tp*100,stop_pct=sl*100,max_hold_minutes=hold,
      days=len(a),trades=int(a[:,6].sum()),profitable_days=len(wins),losing_days=len(loss),
      no_trade_days=int(len(a)-a[:,6].sum()),
      positive_calendar_days_pct=round(100*len(wins)/len(a),3),
      net_profit_factor=round(pf,4) if pf is not None else None,
      net_return_pct=round(100*(a[-1,2]/a[0,1]-1),4),
      avg_daily_net_usd=round(float(a[:,3].mean()),4),
      median_daily_net_usd=round(float(np.median(a[:,3])),4),
      avg_losing_day_usd=round(float(loss.mean()),4) if len(loss) else 0.,
      worst_day_usd=round(float(a[:,3].min()),4),
      max_consecutive_losing_days=maxstreak,
      max_dayclose_drawdown_pct=round(100*float((nav/np.maximum.accumulate(nav)-1).min()),4),
      fees_usd=round(float(a[:,4].sum()),4),funding_debit_usd=round(float(a[:,5].sum()),4))
def main():
    allrows=[];selected=[];monthly=[];quality=[]
    for sym in ("BTCUSD","ETHUSD"):
        d,q=load(sym);quality.append(q);ev=make_signals(d)
        configs=list(itertools.product(HOURS,MODES,REGIMES,TARGETS,STOPS,HOLDS))
        best=None;bestkey=None;eligible=0
        for k,params in enumerate(configs):
            arr=run(d,ev[params[:3]],params)
            a=metric(sym,params,arr,2025);b=metric(sym,params,arr,2026)
            allrows.extend((a,b))
            good=a["trades"]>=100 and a["net_return_pct"]>0 and (a["net_profit_factor"] or 0)>1
            eligible+=int(good)
            key=(int(good),a["positive_calendar_days_pct"] if good else a["net_return_pct"],a["net_return_pct"])
            if bestkey is None or key>bestkey:bestkey=key;best=(params,arr,a,b)
            if k%250==0:print(sym,k,len(configs),flush=True)
        params,arr,a,b=best
        selected.extend([{**a,"train_criteria_pass":bool(eligible)},{**b,"train_criteria_pass":bool(eligible)}])
        dates=pd.date_range("2025-01-01",periods=len(arr),freq="D",tz="UTC")
        groups=dates.strftime("%Y-%m")
        for month in pd.unique(groups):
            g=arr[groups==month]
            monthly.append(dict(symbol=sym,month_utc=month,net_return_pct=round(100*(g[-1,2]/g[0,1]-1),4),
                trades=int(g[:,6].sum()),profitable_days=int((g[:,3]>1e-8).sum()),
                losing_days=int((g[:,3]<-1e-8).sum()),no_trade_days=int((g[:,6]==0).sum()),
                fees_usd=round(float(g[:,4].sum()),3)))
        print("SELECTED",sym,params,a,b,"eligible_2025",eligible,flush=True)
    pd.DataFrame(allrows).to_csv(OUT/"summary.csv",index=False)
    pd.DataFrame(selected).to_csv(OUT/"selected.csv",index=False)
    pd.DataFrame(monthly).to_csv(OUT/"selected_monthly.csv",index=False)
    info=dict(hypothesis="fixed-hour prior completed hour sign persistence/fade conditioned on 48-hour range regime",
      novelty="No candle-pattern breakout, VWAP, carry, cross-asset, wick or volume thresholds",
      data=quality,models_per_asset=len(configs),
      split="2025 train, unchanged 2026 research-exposed historical check, not pristine OOS",
      fee_each_side_including_GST=FEE,adverse_slippage_each_side=SLIP,
      funding_debit_per_8h_crossing=FUND,stop_risk_per_trade=RISK,max_notional_leverage=LEVERAGE,
      limitations=["No verified spread/order book, liquidation engine, margin/lot sizes, or exact funding",
                   "1m OHLC stop-first where ambiguous",
                   "No strategy can guarantee daily profits",
                   "2026 is not a pristine holdout",
                   "2026 ends Nov 17 UTC; includes no-trade calendar days"])
    (OUT/"quality.json").write_text(json.dumps(info,indent=2)+"\n")
    (OUT/"REPORT.md").write_text("# Fixed-hour prior-hour sign daily futures research\n\n"+
      pd.DataFrame(selected).to_string(index=False)+"\n\n"+
      "## Caveats\n\n"+"\n".join("- "+x for x in info["limitations"])+"\n")
    print("COMPLETE",len(allrows),flush=True)
if __name__=="__main__":main()
