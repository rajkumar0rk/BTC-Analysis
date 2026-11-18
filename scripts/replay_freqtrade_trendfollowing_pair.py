#!/usr/bin/env python3
"""Independent, fixed-rule 5m futures replay of freqtrade TrendFollowingStrategy.
Source pinned: freqtrade/freqtrade-strategies f3340ce11f5bdf62f598522e64d1f5638eaa13f5
user_data/strategies/futures/TrendFollowingStrategy.py
EMA20 + OBV crossover signal exactly; futures-safe explicit ATR2 protective stop
and opposite-cross/OBV exit; risk 1% equity, max 2x gross exposure.
CAUTION: exit/risk overlay differs from original Freqtrade trailing ROI implementation.
"""
import json, hashlib
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"analysis"/"external_github_profit_hunt"/"freqtrade_trendfollowing_20261118"
MONTHS=pd.period_range("2025-01","2026-10",freq="M").astype(str).tolist()
INITIAL=10000.
FEE=0.0005*1.18
SOURCE="https://github.com/freqtrade/freqtrade-strategies/blob/f3340ce11f5bdf62f598522e64d1f5638eaa13f5/user_data/strategies/futures/TrendFollowingStrategy.py"
def candles(sym):
    base=ROOT/"data"/"delta_india"/sym/"1m"
    m=json.loads((base/"manifest.json").read_text())
    partitions=[x for x in m["partitions"] if "2025-01"<=x["file"][:7]<="2026-11"]
    if len(partitions)<22:raise ValueError("Too few 1m archive partitions")
    frames=[]
    for p in partitions:
        f=base/p["file"]
        if hashlib.sha256(f.read_bytes()).hexdigest()!=p["sha256_gzip"]:raise ValueError("SHA mismatch "+str(f))
        if p["missing_minutes"]:raise ValueError("Incomplete UTC month "+str(f))
        d=pd.read_csv(f,compression="gzip",usecols=["time","open","high","low","close","volume"])
        if len(d)!=p["observed_candles"]:raise ValueError("Count mismatch")
        frames.append(d)
    d=pd.concat(frames,ignore_index=True)
    if not np.all(np.diff(d.time.to_numpy(np.int64))==60):raise ValueError("Noncontinuous minute candles")
    d.index=pd.to_datetime(d.time,unit="s",utc=True)
    a=d.resample("5min",label="left",closed="left").agg({"open":"first","high":"max","low":"min","close":"last","volume":"sum"})
    count=d.close.resample("5min").count()
    a=a[count==5].copy()
    a["ema"]=a.close.ewm(span=20,adjust=False).mean()
    # OBV direction is determined by prior vs current close, with volume > 0.
    prev=a.close.shift(1)
    a["long"]=((a.close>a.ema)&(prev<=a.ema.shift(1))&(a.close>prev)&(a.volume>0))
    a["short"]=((a.close<a.ema)&(prev>=a.ema.shift(1))&(a.close<prev)&(a.volume>0))
    a["exit_long"]=((a.close<a.ema)&(prev>=a.ema.shift(1))&(a.close>prev))
    a["exit_short"]=((a.close>a.ema)&(prev<=a.ema.shift(1))&(a.close<prev))
    tr=pd.concat([a.high-a.low,(a.high-prev).abs(),(a.low-prev).abs()],axis=1).max(axis=1)
    a["atr"]=tr.ewm(alpha=1/14,adjust=False,min_periods=14).mean()
    return a
def replay(sym):
    a=candles(sym)
    o=a.open.to_numpy(float);h=a.high.to_numpy(float);l=a.low.to_numpy(float);c=a.close.to_numpy(float)
    atr=a.atr.to_numpy(float)
    longs=a.long.to_numpy(bool);shorts=a.short.to_numpy(bool)
    exl=a.exit_long.to_numpy(bool);exs=a.exit_short.to_numpy(bool)
    times=a.index
    equity=INITIAL;position=0;entry=stop=qty=entryfee=0.;entrytime=None
    rows=[];month_equity={};max_equity=INITIAL;maxdd=0.
    slip=0.0005 if sym=="BTCUSD" else 0.0002
    def close_trade(i,px,reason):
        nonlocal equity,position,entry,stop,qty,entryfee,entrytime,max_equity,maxdd
        fill=px*(1-slip*position)
        gross=position*(fill-entry)*qty
        exitfee=fill*qty*FEE
        pnl=gross-exitfee-entryfee
        equity+=gross-exitfee
        rows.append(dict(symbol=sym,entry_utc=entrytime.isoformat(),exit_utc=times[i].isoformat(),direction=position,entry_price=entry,exit_price=fill,quantity=qty,gross_pnl=gross,entry_fee_gst=entryfee,exit_fee_gst=exitfee,net_pnl=pnl,exit_reason=reason,exit_month_ist=times[i].tz_convert("Asia/Kolkata").strftime("%Y-%m")))
        position=0;qty=0
    for i in range(30,len(a)-1):
        # Month-end mark-to-market on 5m bar close. Cash already paid entry fee.
        month=times[i].tz_convert("Asia/Kolkata").strftime("%Y-%m")
        if position:
            marked=equity+position*(c[i]-entry)*qty-c[i]*qty*FEE
        else:marked=equity
        month_equity[month]=marked
        max_equity=max(max_equity,marked)
        maxdd=max(maxdd,100*(max_equity-marked)/max_equity)
        if position:
            # Intrabar stop: conservative adverse fill at stop or worse at bar open
            if (position==1 and l[i]<=stop) or (position==-1 and h[i]>=stop):
                px=min(o[i],stop) if position==1 else max(o[i],stop)
                close_trade(i,px,"ATR2_STOP")
            elif (position==1 and exl[i-1]) or (position==-1 and exs[i-1]):
                close_trade(i,o[i],"EMA_OBV_EXIT")
        if not position and np.isfinite(atr[i-1]) and equity>0:
            signal=1 if longs[i-1] else -1 if shorts[i-1] else 0
            if signal:
                fill=o[i]*(1+signal*slip)
                distance=2*atr[i-1]
                if distance>0:
                    qty=min(equity*0.01/distance,equity*2/fill)
                    entryfee=qty*fill*FEE
                    if equity>entryfee:
                        equity-=entryfee;position=signal;entry=fill
                        stop=entry-signal*distance;entrytime=times[i]
        if equity<=0:raise ValueError("Account depleted")
    # Force close at end of 2026-10 IST rather than including November data.
    if position:
        i=min(len(a)-1,next((j for j in range(1,len(a)) if times[j].tz_convert("Asia/Kolkata").strftime("%Y-%m")>"2026-10"),len(a)-1))
        close_trade(i,o[i],"PERIOD_END")
    trades=pd.DataFrame(rows)
    monthly=[];prior=INITIAL
    for month in MONTHS:
        eq=month_equity.get(month,prior)
        subset=trades[trades.exit_month_ist==month] if len(trades) else pd.DataFrame(columns=["net_pnl"])
        p=subset.net_pnl.to_numpy(float)
        pos=p[p>0].sum();neg=-p[p<0].sum()
        pf=round(float(pos/neg),5) if neg else ("Infinity" if pos>0 else "N/A")
        ret=100*(eq/prior-1) if prior>0 else None
        monthly.append(dict(symbol=sym,month_ist=month,trades=len(subset),wins=int((p>0).sum()),losses=int((p<0).sum()),profit_factor=pf,net_account_return_pct=round(ret,5),month_end_equity=round(eq,5),gross_positive_trade_pnl=round(float(pos),5),abs_negative_trade_pnl=round(float(neg),5),high_pf_month=bool(isinstance(pf,float) and pf>=1.5 and ret>0)))
        prior=eq
    df=pd.DataFrame(monthly)
    df.to_csv(OUT/(sym+"_monthly.csv"),index=False)
    trades.to_csv(OUT/(sym+"_trades.csv.gz"),index=False,compression="gzip")
    pos=trades.loc[trades.net_pnl>0,"net_pnl"].sum() if len(trades) else 0
    neg=-trades.loc[trades.net_pnl<0,"net_pnl"].sum() if len(trades) else 0
    y25=float(np.prod(1+df.iloc[:12].net_account_return_pct.to_numpy()/100)-1)*100
    y26=float(np.prod(1+df.iloc[12:].net_account_return_pct.to_numpy()/100)-1)*100
    return dict(symbol=sym,source=SOURCE,source_commit="f3340ce11f5bdf62f598522e64d1f5638eaa13f5",months=22,monthly_high_pf=int(df.high_pf_month.sum()),positive_months=int((df.net_account_return_pct>0).sum()),negative_months=int((df.net_account_return_pct<0).sum()),median_monthly_return_pct=round(float(df.net_account_return_pct.median()),5),year_2025_net_pct=round(y25,4),year_2026_jan_oct_ytd_pct=round(y26,4),overall_net_pct=round(100*(prior/INITIAL-1),4),aggregate_pf=round(float(pos/neg),4) if neg else None,max_drawdown_pct=round(maxdd,4),trades=int(len(trades)),wins=int((trades.net_pnl>0).sum()) if len(trades) else 0,losses=int((trades.net_pnl<0).sum()) if len(trades) else 0,passes_monthly=bool(df.high_pf_month.sum()>=12 and prior>INITIAL),passes_2025_500=bool(y25>500),limitations=["January 2025 IST lacks prior Dec 2024 UTC evening","No settled funding or order book impact modeled","ATR2 stop and risk overlay are conservative research adaptations, not exact upstream Freqtrade exit/ROI engine","Monthly mark-to-market uses 5m closes; closed trade PF by exit month; boundary positions can create PF/return mismatch","2026 already research-exposed"])
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    results=[replay(sym) for sym in ("BTCUSD","ETHUSD")]
    (OUT/"verdict.json").write_text(json.dumps(results,indent=2)+"\n")
    print("MONTHLY_PF_NEW_SOURCE_RESULTS "+json.dumps(results),flush=True)
if __name__=="__main__":main()
