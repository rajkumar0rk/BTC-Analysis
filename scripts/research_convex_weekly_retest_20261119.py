#!/usr/bin/env python3
"""Independent multi-day breakout with a post-breakout retest and convex exit.
Predeclared grid: 72/168h channel, 6/12h retest timeout, 0.25/0.50 ATR
retest tolerance, 2/3 ATR stop, 72/168h trailing channel. One trade,
1h confirmed signal -> next minute open, 1m wick stop. Research only.
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from numba import njit

ROOT=Path("data/delta_india")
OUT=Path("analysis/convex_weekly_range_retest_20261119")
START=1000.; RISK=.005; FEE=.0005*1.18; SLIP=.0002; LEV=10.

def load(sym):
    files=sorted((ROOT/sym/"1m").glob("20??-??.csv.gz"))
    d=pd.concat([pd.read_csv(f,compression="gzip",usecols=["time","open","high","low","close","volume"]) for f in files],ignore_index=True)
    d=d[(d.time>=1735689600)&(d.time<1794960000)].sort_values("time").reset_index(drop=True)
    t=d.time.to_numpy(np.int64)
    if len(t)<900000 or np.any(np.diff(t)!=60):raise ValueError("noncontinuous minute data")
    if not np.isfinite(d[["open","high","low","close","volume"]]).all().all():raise ValueError("NaN prices")
    if ((d.low<=0)|(d.high<d.low)|(d.open<d.low)|(d.close<d.low)|(d.open>d.high)|(d.close>d.high)).any():raise ValueError("bad OHLC")
    d.index=pd.to_datetime(t,unit="s",utc=True)
    return d

def funding(sym,t):
    root=ROOT/sym/"institutional/history/funding_1h"
    files=sorted(root.glob("20??-??.csv.gz"))
    if not files:raise ValueError("funding absent")
    d=pd.concat([pd.read_csv(f,compression="gzip",usecols=["time","close"]) for f in files],ignore_index=True).drop_duplicates("time",keep="last")
    d=d[np.isfinite(d.close)&(d.close.abs()<=5)]
    m={int(ts)+3600:float(rate)/100 for ts,rate in zip(d.time,d.close)}
    x=np.zeros(len(t))
    missing=0
    for i in np.flatnonzero(t%28800==0):
        x[i]=m.get(int(t[i]),np.nan)
        if np.isnan(x[i]):missing+=1
    return x,dict(funding_observations=len(d),missing_funding_settlements=missing)

def prepare(d,lookback,wait,tol,stop,trail):
    h=d[["open","high","low","close","volume"]].resample("1h").agg({"open":"first","high":"max","low":"min","close":"last","volume":"sum"})
    count=d.close.resample("1h").count()
    if not count.eq(60).all():raise ValueError("incomplete hours")
    prev=h.close.shift(1)
    tr=pd.concat([h.high-h.low,(h.high-prev).abs(),(h.low-prev).abs()],axis=1).max(axis=1)
    atr=tr.ewm(alpha=1/24,adjust=False,min_periods=24).mean()
    ema=h.close.ewm(span=200,adjust=False,min_periods=200).mean()
    high=h.high.shift(1).rolling(lookback,min_periods=lookback).max()
    low=h.low.shift(1).rolling(lookback,min_periods=lookback).min()
    vol=h.volume.shift(1).rolling(48,min_periods=48).median()
    # Breakout candle must close beyond channel; wait for controlled retest.
    bull=(h.close>high)&(h.close>ema)&(ema>ema.shift(24))&(h.volume>vol)
    bear=(h.close<low)&(h.close<ema)&(ema<ema.shift(24))&(h.volume>vol)
    n=len(d);sig=np.zeros(n,np.int8);entryatr=np.zeros(n);tl=np.zeros(n);th=np.zeros(n)
    # Arm only AFTER breakout hour closes. Retest within wait hours and close
    # back above breakout price (or below for short); no use of future candles.
    armed=0;remaining=0;level=0.;a=0.
    for j in range(200,len(h)-1):
        k=(j+1)*60
        if k>=n:break
        # Signal derived from completed hour j, executed next hour open.
        if armed:
            remaining-=1
            if armed==1 and h.low.iloc[j]<=level+tol*a and h.close.iloc[j]>level and h.close.iloc[j]>h.open.iloc[j]:
                sig[k]=1;entryatr[k]=float(atr.iloc[j]);armed=0
            elif armed==-1 and h.high.iloc[j]>=level-tol*a and h.close.iloc[j]<level and h.close.iloc[j]<h.open.iloc[j]:
                sig[k]=-1;entryatr[k]=float(atr.iloc[j]);armed=0
            if remaining<=0:armed=0
        if not armed and sig[k]==0 and np.isfinite(atr.iloc[j]) and atr.iloc[j]>0:
            if bool(bull.iloc[j]):
                armed=1;remaining=wait;level=float(high.iloc[j]);a=float(atr.iloc[j])
            elif bool(bear.iloc[j]):
                armed=-1;remaining=wait;level=float(low.iloc[j]);a=float(atr.iloc[j])
        if j>=trail:
            # trailing stop based on completed hours, never intrabar
            tl[k]=float(h.low.iloc[j-trail+1:j+1].min())
            th[k]=float(h.high.iloc[j-trail+1:j+1].max())
    return sig,entryatr,tl,th

@njit(cache=True)
def run(t,o,hi,lo,cl,sig,atr,tl,th,fr,months,stopmul):
    cash=START;side=0;qty=0.;ep=0.;st=0.;startcash=0.;risk=0.;entryidx=0
    fees=0.;funds=0.;tradefee=0.;tradefund=0.;peak=START;dd=0.
    logs=np.zeros((2000,10));nlog=0;nav=np.full(23,np.nan)
    for i in range(len(t)):
        if side:
            if side==1 and tl[i]>0:st=max(st,tl[i])
            if side==-1 and th[i]>0:st=min(st,th[i])
            if t[i]%28800==0:
                pay=abs(qty*o[i])*.0001 if np.isnan(fr[i]) else side*qty*o[i]*fr[i]
                cash-=pay;tradefund+=pay;funds+=pay
            if (side==1 and lo[i]<=st) or (side==-1 and hi[i]>=st):
                p=min(o[i],st) if side==1 else max(o[i],st)
                fill=p*(1-side*SLIP)
                fee=abs(qty*fill)*FEE
                cash+=side*(fill-ep)*qty-fee
                fees+=fee;tradefee+=fee
                if nlog<len(logs):
                    logs[nlog,0]=t[entryidx];logs[nlog,1]=t[i];logs[nlog,2]=side
                    logs[nlog,3]=cash-startcash;logs[nlog,4]=(cash-startcash)/risk
                    logs[nlog,5]=tradefee;logs[nlog,6]=tradefund;logs[nlog,7]=ep;logs[nlog,8]=fill
                    logs[nlog,9]=stopmul;nlog+=1
                side=0;qty=0.
        if side==0 and sig[i]!=0 and atr[i]>0 and cash>0:
            sd=int(sig[i]);fill=o[i]*(1+sd*SLIP);dist=atr[i]*stopmul
            q=cash*RISK/dist
            if q>0 and q*fill<=cash*LEV:
                side=sd;ep=fill;qty=q;st=fill-sd*dist
                entryidx=i;startcash=cash;risk=cash*RISK
                fee=q*fill*FEE;cash-=fee;fees+=fee;tradefee=fee;tradefund=0.
        eq=cash+side*qty*(cl[i]*(1-side*SLIP)-ep)-side*0 if side else cash
        if eq>peak:peak=eq
        if eq/peak-1<dd:dd=eq/peak-1
        if i==len(t)-1 or months[i+1]!=months[i]:nav[months[i]]=eq
    if side:
        i=len(t)-1;fill=cl[i]*(1-side*SLIP);fee=qty*fill*FEE
        cash+=side*(fill-ep)*qty-fee;fees+=fee;tradefee+=fee
        if nlog<len(logs):
            logs[nlog,0]=t[entryidx];logs[nlog,1]=t[i];logs[nlog,2]=side
            logs[nlog,3]=cash-startcash;logs[nlog,4]=(cash-startcash)/risk
            logs[nlog,5]=tradefee;logs[nlog,6]=tradefund;logs[nlog,7]=ep;logs[nlog,8]=fill
            logs[nlog,9]=stopmul;nlog+=1
        nav[months[-1]]=cash
    return cash,nav,logs[:nlog],fees,funds,dd

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    summary=[];ledger=[];monthly=[];quality=[]
    # Fixed month boundaries in IST, 23 months Jan 2025-Nov 2026
    bounds=pd.date_range("2025-01-01","2026-12-01",freq="MS",tz="Asia/Kolkata")
    stamps=(bounds.tz_convert("UTC").astype("int64")//10**9).to_numpy()
    labels=bounds.strftime("%Y-%m").tolist()[:-1]
    for sym in ("BTCUSD","ETHUSD"):
        d=load(sym);t=d.time.to_numpy(np.int64);fr,q=funding(sym,t)
        mid=np.searchsorted(stamps,t,side="right")-1
        if mid.min()<0 or mid.max()>22:raise ValueError(f"out-of-range IST month {mid.min()}..{mid.max()}, first/last {pd.to_datetime(t[0],unit='s',utc=True)}..{pd.to_datetime(t[-1],unit='s',utc=True)}, bounds {stamps[0]}..{stamps[-1]}, labels {len(labels)}")
        quality.append(dict(symbol=sym,minutes=len(t),first=str(d.index[0]),last=str(d.index[-1]),**q))
        for look in (72,168):
            for wait in (6,12):
                for tol in (.25,.50):
                    for stop in (2.,3.):
                        for trail in (72,168):
                            model=f"channel{look}_wait{wait}_tol{tol:g}_stop{stop:g}_trail{trail}"
                            sig,a,tl,th=prepare(d,look,wait,tol,stop,trail)
                            cash,nav,log,fees,funds,dd=run(t,d.open.to_numpy(float),
                                d.high.to_numpy(float),d.low.to_numpy(float),
                                d.close.to_numpy(float),sig,a,tl,th,fr,mid,stop)
                            p=log[:,3];wins=p[p>0];losses=p[p<0]
                            pf=wins.sum()/-losses.sum() if len(losses) else np.nan
                            wl=wins.mean()/-losses.mean() if len(wins) and len(losses) else np.nan
                            big=float(log[:,4].max()) if len(log) else 0
                            row=dict(symbol=sym,model=model,signals=int((sig!=0).sum()),trades=len(log),
                                wins=len(wins),losses=len(losses),win_rate=round(len(wins)/len(log),4) if len(log) else None,
                                pf=round(float(pf),4) if np.isfinite(pf) else None,
                                win_loss_ratio=round(float(wl),4) if np.isfinite(wl) else None,
                                max_winner_R=round(big,3),winners_over_10R=int((log[:,4]>=10).sum()) if len(log) else 0,
                                return_total_pct=round((cash/START-1)*100,3),
                                return_2025_pct=round((nav[11]/START-1)*100,3),
                                return_2026_partial_pct=round((nav[-1]/nav[11]-1)*100,3),
                                max_drawdown_pct=round(dd*100,3),
                                fees_usd=round(fees,3),funding_proxy_usd=round(funds,3))
                            summary.append(row)
                            previous=START
                            for j,label in enumerate(labels):
                                pct=100*(nav[j]/previous-1);previous=nav[j]
                                monthly.append(dict(symbol=sym,model=model,month_ist=label,return_pct=round(pct,4),nav=round(nav[j],4)))
                            for rec in log:
                                ledger.append(dict(symbol=sym,model=model,entry_utc=pd.to_datetime(int(rec[0]),unit="s",utc=True),
                                    exit_utc=pd.to_datetime(int(rec[1]),unit="s",utc=True),side=int(rec[2]),
                                    net_pnl_usd=round(rec[3],5),net_R=round(rec[4],5),fees=round(rec[5],5),
                                    funding_proxy=round(rec[6],5),entry_fill=round(rec[7],4),exit_fill=round(rec[8],4)))
        print("COMPLETE",sym,flush=True)
    s=pd.DataFrame(summary);m=pd.DataFrame(monthly);l=pd.DataFrame(ledger)
    s.to_csv(OUT/"all_models.csv",index=False)
    m.to_csv(OUT/"monthly_ist.csv.gz",index=False,compression="gzip")
    l.to_csv(OUT/"trade_ledger.csv.gz",index=False,compression="gzip")
    # Strict threshold: full 2025 year must exceed 500%; 2026 is partial.
    passed=s[(s.trades>=30)&(s.win_rate<=.40)&(s.win_loss_ratio>=5)&
        (s.max_winner_R>=10)&(s.pf>=1.5)&(s.return_2025_pct>500)&
        (s.return_2026_partial_pct>0)&(s.max_drawdown_pct>-30)]
    passed.to_csv(OUT/"strict_qualifiers.csv",index=False)
    top=s.sort_values("return_2025_pct",ascending=False).head(12)
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join([
        "# Independent weekly-channel breakout retest asymmetry study",
        "",f"**Strict qualifiers: {len(passed)} / {len(s)}**","",
        "## Best 2025 returns (not recommendations)",top.to_markdown(index=False),"",
        "## Data and model limitations",
        "- Both markets use continuous Delta India one-minute data; signals on closed 1h bars",
        "- One position, 0.5% initial equity risk, 10x notional leverage cap",
        "- Taker fee 0.05% each side + 18% GST, 2bps slippage each execution",
        "- Delta 1h funding rate proxy, missing settlement 1bp charged to position",
        "- No intraminute path, spread, liquidation, or true portfolio margin simulation",
        "- 2026 is partial, not a full-year 500% return test",
        "- In-sample comparisons only; no untouched holdout or prospective validation",
        "- Trail uses completed hourly range; gaps through stops use worse opening price",
        "- Signal entered next hour open; stop checks at same minute are approximate",
        "- Robustness tests only meaningful for passing candidates, none assumed"
    ])+"\n")
    (OUT/"quality.json").write_text(json.dumps(dict(quality=quality,models=len(s),strict_qualifiers=len(passed),
        start_capital=START,risk_fraction=RISK,leverage_cap=LEV,
        fee_per_side=.00059,slippage_per_side=.0002,
        model_family="72/168h breakout, 6/12h controlled retest, 72/168h trailing channel"),indent=2))
    print("QUALIFIERS",len(passed));print(top.to_string(index=False))
if __name__=="__main__":main()
