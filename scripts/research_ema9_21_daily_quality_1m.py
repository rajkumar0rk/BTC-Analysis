#!/usr/bin/env python3
"""Causal EMA9/21 1m BTCUSD pullback-reclaim; one entry maximum per IST day."""
import json
from pathlib import Path
import numpy as np
import pandas as pd

SOURCE=Path("data/delta_india/BTCUSD/1m")
OUT=Path("analysis/ema9_21_daily_quality_1m")
MONTHS=pd.period_range("2025-01","2026-10",freq="M").astype(str).tolist()
FEE=0.0005*1.18
ALLOCATION=0.10

def load():
    chunks=[]
    for month in MONTHS+["2026-11"]:
        path=SOURCE/(month+".csv.gz")
        if not path.exists(): raise FileNotFoundError(path)
        z=pd.read_csv(path,compression="gzip",usecols=["time","open","high","low","close","volume"])
        z["time"]=pd.to_datetime(z.time.astype("int64"),unit="s",utc=True)
        chunks.append(z)
    m=pd.concat(chunks,ignore_index=True).set_index("time").sort_index()
    if m.index.has_duplicates or m.isna().any().any():raise ValueError("Duplicate/null source candles")
    if not m.index.to_series().diff().iloc[1:].eq(pd.Timedelta(minutes=1)).all():
        raise ValueError("Missing minute(s): refusing false continuity")
    if (m.high<m[["open","low","close"]].max(axis=1)).any() or (m.low>m[["open","high","close"]].min(axis=1)).any():
        raise ValueError("Malformed OHLC")
    return m

def ema(s,n):
    return s.ewm(span=n,adjust=False,min_periods=n).mean()

def rma(s,n):
    # Wilder smoothing with exponential warmup; 150+ bars before recorded entries.
    return s.ewm(alpha=1/n,adjust=False,min_periods=n).mean()

def signals(m):
    o,h,l,c,v=[m[k] for k in ("open","high","low","close","volume")]
    e9,e21=ema(c,9),ema(c,21)
    pc=c.shift(1)
    tr=pd.concat([h-l,(h-pc).abs(),(l-pc).abs()],axis=1).max(axis=1)
    atr=rma(tr,14)
    up=h.diff().clip(lower=0);dn=(-l.diff()).clip(lower=0)
    plus=rma(up.where(up>dn,0.0),14)
    minus=rma(dn.where(dn>up,0.0),14)
    di_plus=100*plus/rma(tr,14).replace(0,np.nan)
    di_minus=100*minus/rma(tr,14).replace(0,np.nan)
    dx=100*(di_plus-di_minus).abs()/(di_plus+di_minus).replace(0,np.nan)
    adx=rma(dx,14)
    # UTC 24h market session VWAP, including present bar.
    utcday=m.index.strftime("%Y-%m-%d")
    vwap=(((h+l+c)/3*v).groupby(utcday).cumsum()/
          v.groupby(utcday).cumsum().replace(0,np.nan))
    states=[]
    for freq,bars in (("5min",5),("15min",15)):
        r=c.resample(freq,closed="left",label="left")
        bar=r.last().where(r.count().eq(bars))
        states.append((ema(bar,9).shift(1).reindex(m.index,method="ffill"),
                       ema(bar,21).shift(1).reindex(m.index,method="ffill")))
    bull=(e9>e21)&(e21>e21.shift(3))
    bear=(e9<e21)&(e21<e21.shift(3))
    for a,b in states:
        bull &= (a>b)
        bear &= (a<b)
    touch_long=(l.shift(1)<=e21.shift(1))|(l.shift(2)<=e21.shift(2))|(l.shift(3)<=e21.shift(3))
    touch_short=(h.shift(1)>=e21.shift(1))|(h.shift(2)>=e21.shift(2))|(h.shift(3)>=e21.shift(3))
    reclaim_long=(c>e9)&(c.shift(1)<=e9.shift(1))&(c>o)
    reclaim_short=(c<e9)&(c.shift(1)>=e9.shift(1))&(c<o)
    stop_long=l.rolling(5,min_periods=5).min()-0.2*atr
    stop_short=h.rolling(5,min_periods=5).max()+0.2*atr
    risk_long=c-stop_long
    risk_short=stop_short-c
    ok_long=(risk_long>=0.5*atr)&(risk_long<=3*atr)&(risk_long*2.5/c*100>=0.18)
    ok_short=(risk_short>=0.5*atr)&(risk_short<=3*atr)&(risk_short*2.5/c*100>=0.18)
    shared=(v>=v.rolling(20,min_periods=20).mean()*1.1)&(adx>=18)
    ls=(bull&touch_long&reclaim_long&shared&(di_plus>di_minus)&(c>vwap)&ok_long).fillna(False)
    ss=(bear&touch_short&reclaim_short&shared&(di_minus>di_plus)&(c<vwap)&ok_short).fillna(False)
    return ls.to_numpy(bool),ss.to_numpy(bool),stop_long.to_numpy(float),stop_short.to_numpy(float),dict(raw_long_signals=int(ls.sum()),raw_short_signals=int(ss.sum()))

def replay(m,ind,slip):
    ls,ss,long_st,short_st,raw=ind
    o,hi,lo,cl=[m[k].to_numpy(float) for k in ("open","high","low","close")]
    dates=np.asarray(m.index.tz_convert("Asia/Kolkata").strftime("%Y-%m-%d"))
    i=0;n=len(m);used=set();rows=[]
    while i<n-1:
        day=dates[i]
        if day[:7] not in MONTHS or day in used or not (ls[i] or ss[i]):
            i+=1;continue
        side=1 if ls[i] else -1
        stop=float(long_st[i] if side>0 else short_st[i])
        if not np.isfinite(stop):
            i+=1;continue
        entry_i=i+1
        mid_entry=float(o[entry_i])
        fill_entry=mid_entry+side*slip
        distance=side*(fill_entry-stop)
        if distance<=0:
            i+=1;continue
        target=fill_entry+side*2.5*distance
        used.add(day)
        j=entry_i
        while j<n:
            sl_hit=lo[j]<=stop if side>0 else hi[j]>=stop
            tp_hit=hi[j]>=target if side>0 else lo[j]<=target
            if sl_hit:
                mid_exit=min(float(o[j]),stop) if side>0 else max(float(o[j]),stop)
                reason="stop";break
            if tp_hit:
                mid_exit=target
                reason="target";break
            j+=1
        if j>=n:
            j=n-1;mid_exit=float(cl[j]);reason="history_end"
        fill_exit=mid_exit-side*slip
        gross=side*(mid_exit-mid_entry)
        slipcost=side*(mid_exit-mid_entry)-side*(fill_exit-fill_entry)
        feecost=FEE*(fill_entry+fill_exit)
        net=side*(fill_exit-fill_entry)-feecost
        ret=ALLOCATION*net/fill_entry
        rows.append(dict(signal_utc=str(m.index[i]),entry_utc=str(m.index[entry_i]),
                         exit_utc=str(m.index[j]),entry_day_ist=day,
                         exit_month_ist=dates[j][:7],direction="LONG" if side>0 else "SHORT",
                         entry_fill=round(fill_entry,4),exit_fill=round(fill_exit,4),
                         stop=round(stop,4),target=round(target,4),reason=reason,
                         gross_points=round(gross,5),slippage_points=round(slipcost,5),
                         fee_gst_points=round(feecost,5),net_points=round(net,5),
                         account_return=ret,hold_min=j-entry_i+1))
        i=j+1
    return pd.DataFrame(rows),raw

def score(ledger,m,slip,raw):
    monthly=[];equity=1.;peak=1.;maxdd=0.
    for month in MONTHS:
        sub=ledger[ledger.exit_month_ist==month].sort_values("exit_utc")
        equity_start=equity
        for r in sub.account_return:
            equity*=1+float(r)
            peak=max(peak,equity)
            maxdd=max(maxdd,1-equity/peak)
        monthly.append(dict(month_ist=month,trades=len(sub),
            wins=int((sub.net_points>0).sum()),losses=int((sub.net_points<0).sum()),
            net_points=round(float(sub.net_points.sum()),2),
            net_account_return_pct=round(100*(equity/equity_start-1),5)))
    monthly=pd.DataFrame(monthly)
    gains=float(ledger.loc[ledger.net_points>0,"net_points"].sum())
    losses=-float(ledger.loc[ledger.net_points<0,"net_points"].sum())
    return monthly,dict(source="Delta India BTCUSD futures 1m compressed archive",
        first_utc=str(m.index[0]),last_utc=str(m.index[-1]),
        minutes=int(len(m)),evaluation_months=22,
        fee_gst_per_side=FEE,slippage_per_side_points=slip,
        notional_exposure_fraction=ALLOCATION,
        trades=int(len(ledger)),winning_trades=int((ledger.net_points>0).sum()),
        losing_trades=int((ledger.net_points<0).sum()),
        win_rate_pct=round(100*(ledger.net_points>0).mean(),3) if len(ledger) else 0,
        profit_factor=round(gains/losses,4) if losses else None,
        gross_points=round(float(ledger.gross_points.sum()),2),
        net_points=round(float(ledger.net_points.sum()),2),
        trading_fees_gst_points=round(float(ledger.fee_gst_points.sum()),2),
        slippage_points=round(float(ledger.slippage_points.sum()),2),
        net_account_return_pct=round((equity-1)*100,5),
        max_closed_trade_drawdown_pct=round(maxdd*100,5),
        winning_months=int((monthly.net_account_return_pct>0).sum()),
        losing_months=int((monthly.net_account_return_pct<0).sum()),
        flat_months=int((monthly.net_account_return_pct==0).sum()),
        average_trades_per_ist_day=round(len(ledger)/669,3),
        stop_exits=int(ledger.reason.eq("stop").sum()),
        target_exits=int(ledger.reason.eq("target").sum()),
        **raw)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    m=load();ind=signals(m)
    results={}
    for slip in (5.0,0.5):
        ledger,raw=replay(m,ind,slip)
        monthly,s=score(ledger,m,slip,raw)
        key="slip_5" if slip==5 else "slip_0_5"
        results[key]=s
        ledger.to_csv(OUT/(key+"_trades.csv.gz"),index=False,compression="gzip")
        monthly.to_csv(OUT/(key+"_monthly.csv"),index=False)
        print("EMA_RESULT "+key+" "+json.dumps(s,sort_keys=True),flush=True)
        print("EMA_MONTHS "+key+"\n"+monthly.to_string(index=False),flush=True)
    (OUT/"summary.json").write_text(json.dumps(results,indent=2)+"\n")
    lines=["# BTCUSD — 1m EMA9/21 daily quality trade results","",
           "One trade max per IST day; bullish/bearish EMA9-21 pullback-reclaim, 5m/15m confirmed alignment, VWAP, ADX/DI, volume; 5-bar swing ATR stop, 2.5R target. Signal close -> next minute open; stop-first on simultaneous fills.",
           "Taker 0.05% per side + 18% GST on fees, 10% notional equity allocation (no leverage), two slippage sensitivities.",
           "No funding, liquidation, actual book spread or market impact; closed-trade-only drawdown; 2026 not unseen holdout.",""]
    for key,s in results.items():
        lines.extend(["## "+key,"",json.dumps(s,indent=2),"",
                      pd.read_csv(OUT/(key+"_monthly.csv")).to_markdown(index=False),""])
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(lines)+"\n")
    print("EMA_BACKTEST_COMPLETED",flush=True)

if __name__=="__main__":
    main()
