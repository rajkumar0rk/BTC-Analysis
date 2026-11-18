#!/usr/bin/env python3
"""Independent family: 1h volatility-expansion + 4h trend, 1m protective replay.
Predeclared rules. No parameter search. BTC and ETH independently.
Signals: closed 1h candle breaks preceding 48h range, range >1.5x median
prior 48 ranges, closes in extreme 20% of bar, 4h EMA50 direction,
ATR14 (Wilder) 1h. Enter next 1m open. Initial 1.5ATR stop.
After 3R favorable excursion, trail 3ATR from most favorable 1m high/low.
Stop moves only in favorable direction. No profit cap, no pyramiding.
0.5% equity initial risk, 5x max leverage, one position at a time.
Conservative stop-first intraminute, adverse 2bps slippage, taker 0.05%
per fill plus GST 18%; Delta funding 1h proxy previous hour, missing
settlement 0.01% charged on longs and shorts as conservative approximation.
"""
from pathlib import Path
import numpy as np, pandas as pd, json
BASE=Path("data/delta_india")
OUT=Path("analysis/independent_convex_volatility_20261118_01")
FEE=.0005*1.18;SLIP=.0002;RISK=.005
def load(sym):
    fs=sorted((BASE/sym/"1m").glob("20??-??.csv.gz"))
    assert len(fs)>=22,(sym,len(fs))
    x=pd.concat((pd.read_csv(f,compression="gzip",usecols=["time","open","high","low","close","volume"]) for f in fs),ignore_index=True)
    x=x.sort_values("time").reset_index(drop=True)
    x=x[(x.time>=1735689600)&(x.time<1794960000)].copy()
    t=x.time.to_numpy(np.int64)
    assert len(x)>900000 and np.all(np.diff(t)==60),(sym,len(x))
    x.index=pd.to_datetime(x.time,unit="s",utc=True)
    return x
def funding(sym):
    fs=sorted((BASE/sym/"institutional/history/funding_1h").glob("20??-??.csv.gz"))
    if not fs:return {}
    x=pd.concat((pd.read_csv(f,compression="gzip",usecols=["time","close"]) for f in fs),ignore_index=True)
    return {int(t)+3600:float(v)/100 for t,v in zip(x.time,x.close) if np.isfinite(v) and abs(v)<5}
def signals(x):
    h=x[["open","high","low","close"]].resample("1h").agg({"open":"first","high":"max","low":"min","close":"last"})
    h["count"]=x.close.resample("1h").count()
    p=h.close.shift(1)
    tr=pd.concat([h.high-h.low,(h.high-p).abs(),(h.low-p).abs()],axis=1).max(axis=1)
    atr=tr.ewm(alpha=1/14,adjust=False,min_periods=14).mean()
    med=(h.high-h.low).shift(1).rolling(48,min_periods=48).median()
    hh=h.high.shift(1).rolling(48,min_periods=48).max()
    ll=h.low.shift(1).rolling(48,min_periods=48).min()
    count=h["count"].rolling(49,min_periods=49).min().eq(60)
    # 4h trend must be known at the signal CLOSE, never forward look
    four=x.close.resample("4h",label="right",closed="left").last()
    four_n=x.close.resample("4h",label="right",closed="left").count()
    ema=four.ewm(span=50,adjust=False,min_periods=50).mean().where(four_n.eq(240))
    t=h.index+pd.Timedelta(hours=1)
    trend=ema.reindex(t,method="ffill").to_numpy()
    span=(h.high-h.low).to_numpy()
    loc=np.divide((h.close-h.low).to_numpy(),span,out=np.full(len(h),.5),where=span>0)
    valid=count.to_numpy()&np.isfinite(trend)&np.isfinite(atr.to_numpy())
    bull=valid&(h.close.to_numpy()>hh.to_numpy())&(span>1.5*med.to_numpy())&(loc>=.8)&(h.close.to_numpy()>trend)
    bear=valid&(h.close.to_numpy()<ll.to_numpy())&(span>1.5*med.to_numpy())&(loc<=.2)&(h.close.to_numpy()<trend)
    n=len(x);side=np.zeros(n,np.int8);natr=np.zeros(n)
    ts=x.time.to_numpy(np.int64)
    for j in np.flatnonzero(bull|bear):
        i=int(np.searchsorted(ts,int(t[j].timestamp())))
        if i<n and ts[i]==int(t[j].timestamp()):
            side[i]=1 if bull[j] else -1;natr[i]=atr.iloc[j]
    return side,natr,{"long_signals":int(bull.sum()),"short_signals":int(bear.sum())}
def run(sym,x,s,a,rates):
    T=x.time.to_numpy(np.int64);O=x.open.to_numpy(float);H=x.high.to_numpy(float);L=x.low.to_numpy(float);C=x.close.to_numpy(float)
    equity=1000.;q=0.;side=0;entry=0.;stop=0.;extreme=0.;atr=0.;entry_eq=0.;entry_i=0
    fee_trade=0.;fund_trade=0.;fund_total=0.;fees_total=0.;fund_missing=0
    trades=[];marks=[];peak=1000.;maxdd=0.;month_end={}
    def close(i,price,why):
        nonlocal equity,q,side,fees_total,fee_trade
        fill=price*(1-SLIP*side)
        gross=side*(fill-entry)*q
        fee=FEE*fill*q
        equity+=gross-fee;fee_trade+=fee;fees_total+=fee
        net=equity-entry_eq
        trades.append(dict(symbol=sym,entry_utc=str(pd.to_datetime(T[entry_i],unit="s",utc=True)),exit_utc=str(pd.to_datetime(T[i],unit="s",utc=True)),side=side,entry_price=round(entry,5),exit_price=round(fill,5),net_usd=round(net,5),net_R=round(net/(entry_eq*RISK),5),gross_usd=round(gross,5),fees_usd=round(fee_trade,5),funding_usd=round(fund_trade,5),exit_reason=why))
        side=0;q=0.
    for i in range(len(T)):
        if side==0 and s[i]!=0 and a[i]>0 and equity>0:
            candidate=O[i]*(1+SLIP*s[i]);quantity=equity*RISK/(1.5*a[i])
            if candidate*quantity/equity<=5:
                side=int(s[i]);q=quantity;entry=candidate;atr=float(a[i]);entry_i=i;entry_eq=equity;fee_trade=0.;fund_trade=0.
                extreme=entry;stop=entry-side*1.5*atr
                fee=FEE*entry*q;equity-=fee;fee_trade+=fee;fees_total+=fee
        if side:
            if T[i]%28800==0:
                rate=rates.get(int(T[i]))
                if rate is None:rate=.0001;fund_missing+=1
                charge=side*rate*O[i]*q
                equity-=charge;fund_trade+=charge;fund_total+=charge
            if (side==1 and L[i]<=stop) or (side==-1 and H[i]>=stop):
                px=min(O[i],stop) if side==1 else max(O[i],stop)
                close(i,px,"protective_stop")
            else:
                extreme=max(extreme,H[i]) if side==1 else min(extreme,L[i])
                if side*(extreme-entry)>=3*1.5*atr:
                    candidate=extreme-side*3*atr
                    stop=max(stop,candidate) if side==1 else min(stop,candidate)
                    # unknown high/low sequencing within minute: conservative exit
                    if (side==1 and L[i]<=stop) or (side==-1 and H[i]>=stop):
                        px=min(O[i],stop) if side==1 else max(O[i],stop)
                        close(i,px,"same_minute_trailing_stop")
        mark=equity+(side*(C[i]*(1-SLIP*side)-entry)*q-FEE*C[i]*q if side else 0.)
        peak=max(peak,mark);maxdd=min(maxdd,mark/peak-1)
        mon=str(pd.to_datetime(T[i],unit="s",utc=True).tz_convert("Asia/Kolkata").strftime("%Y-%m"))
        month_end[mon]=mark
    if side:close(len(T)-1,C[-1],"end_of_data")
    month_end[mon]=equity
    prev=1000.;monthly=[]
    for m,e in sorted(month_end.items()):
        sub=[t for t in trades if t["exit_utc"][:7]==m] # UTC close month proxy; monthly returns use IST MTM
        wins=sum(t["net_usd"] for t in sub if t["net_usd"]>0)
        losses=-sum(t["net_usd"] for t in sub if t["net_usd"]<0)
        monthly.append(dict(symbol=sym,month_ist=m,net_return_pct=round((e/prev-1)*100,4),month_profit_factor=round(wins/losses,4) if losses else None,closed_trades=len(sub),end_equity=round(e,4)))
        prev=e
    w=[t["net_usd"] for t in trades if t["net_usd"]>0];l=[t["net_usd"] for t in trades if t["net_usd"]<0]
    streak=0;maxstreak=0
    for t in trades:
        streak=streak+1 if t["net_usd"]<=0 else 0;maxstreak=max(maxstreak,streak)
    sortedw=sorted(w,reverse=True)
    total=sum(t["net_usd"] for t in trades)
    summary=dict(symbol=sym,initial=1000,final=round(equity,3),net_return_pct=round((equity/1000-1)*100,3),trades=len(trades),wins=len(w),losses=len(l),win_rate_pct=round(len(w)/len(trades)*100,3) if trades else None,profit_factor=round(sum(w)/-sum(l),3) if l else None,avg_win_to_avg_loss=round(np.mean(w)/-np.mean(l),3) if w and l else None,biggest_R=round(max((t["net_R"] for t in trades),default=0),3),max_drawdown_pct=round(maxdd*100,3),max_losing_streak=maxstreak,fees_usd=round(fees_total,3),funding_proxy_usd=round(fund_total,3),funding_missing=fund_missing,profit_without_biggest=round(total-(sortedw[0] if sortedw else 0),3),profit_without_top3=round(total-sum(sortedw[:3]),3),positive_months=sum(z["net_return_pct"]>0 for z in monthly),negative_months=sum(z["net_return_pct"]<0 for z in monthly))
    return summary,monthly,trades
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    ss=[];mm=[];tt=[];quality=[]
    for sym in ("BTCUSD","ETHUSD"):
        print("RUN",sym,flush=True)
        x=load(sym);s,a,info=signals(x);rates=funding(sym)
        z,m,t=run(sym,x,s,a,rates);ss.append(z);mm+=m;tt+=t
        quality.append(dict(symbol=sym,rows=len(x),missing_minutes=int((x.time.iloc[-1]-x.time.iloc[0])//60+1-len(x)),funding_rows=len(rates),**info))
        print(json.dumps(z,default=lambda o: o.item() if hasattr(o,"item") else str(o)),flush=True)
    pd.DataFrame(ss).to_csv(OUT/"summary.csv",index=False)
    pd.DataFrame(mm).to_csv(OUT/"monthly.csv",index=False)
    pd.DataFrame(tt).to_csv(OUT/"trades.csv",index=False)
    (OUT/"quality.json").write_text(json.dumps(dict(data=quality,settings=dict(risk_per_trade=.005,fee_per_fill=.00059,slippage_per_fill=.0002,funding_proxy="previous hour Delta FUNDING, assumed 0.01% debit if missing",start="2025-01-01",end_exclusive="2026-11-18",warning="2025 is research exposed; 2026 is NOT an untouched holdout; margin/liquidation not simulated; signal 4h EMA uses last completed 4h close")),indent=2,default=lambda o: o.item() if hasattr(o,"item") else str(o)))
    print("COMPLETE",flush=True)
if __name__=="__main__":main()
