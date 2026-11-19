#!/usr/bin/env python3
"""Preregistered OI accumulation / price compression -> directional expansion.
BTC 2025 is the sole selection segment; BTC 2026 untouched; ETH frozen transfer.
OI is aggregate contract count, not actual liquidations or institutional inventory.
"""
from pathlib import Path
import pandas as pd
import numpy as np
import json
OUT=Path("analysis/independent_oi_accumulation_20261119")
ROOT=Path("data/delta_india")
START=10000.0
FEE=.0005*1.18
SLIP=.0002
RISK=.005
CAP=2.0
CONFIG=dict(lookback=24,oi_growth=.04,compression=.75,breakout=.001,stop=.012,trail=.045,hold=168)
def load(symbol):
    def read(folder):
        paths=sorted(folder.glob("20??-??.csv.gz"))
        if not paths:raise RuntimeError("missing "+str(folder))
        frames=[pd.read_csv(p,compression="gzip") for p in paths]
        x=pd.concat(frames,ignore_index=True)
        x["time"]=pd.to_datetime(x["time"].astype("int64"),unit="s",utc=True)
        x=x.set_index("time").sort_index()
        if not x.index.is_unique:raise RuntimeError("duplicate time")
        return x
    p=read(ROOT/symbol/"1m")
    o=read(ROOT/symbol/"institutional/history/open_interest_5m")
    if p.index.to_series().diff().iloc[1:].ne(pd.Timedelta(minutes=1)).any():raise RuntimeError("missing 1m")
    h=p.resample("1h",label="left",closed="left").agg({"open":"first","high":"max","low":"min","close":"last"})
    count=p["close"].resample("1h").count()
    h=h[count==60].copy()
    oi=o["close"].astype(float).resample("1h").last().reindex(h.index)
    h["oi"]=oi
    if h["oi"].isna().any():raise RuntimeError("missing OI hours")
    return h.astype(float)
def backtest(h,c,reverse=False):
    n=len(h); look=c["lookback"]
    high=h.high.to_numpy();low=h.low.to_numpy();close=h.close.to_numpy();op=h.open.to_numpy();oi=h.oi.to_numpy()
    prior_high=pd.Series(high).rolling(look).max().shift(1).to_numpy()
    prior_low=pd.Series(low).rolling(look).min().shift(1).to_numpy()
    oi_start=pd.Series(oi).shift(look).to_numpy()
    width=(prior_high-prior_low)/pd.Series(close).shift(1).to_numpy()
    rolling_width=pd.Series(width).rolling(30*24,min_periods=10*24).median().shift(1).to_numpy()
    equity=START;peak=START;dd=0;trades=[];curve=[];i=30*24+look+2
    while i<n-1:
        timestamp=h.index[i]
        # signal formed at completed hour i, filled at hour i+1 open
        signal=0
        if np.isfinite(rolling_width[i]) and oi_start[i]>0 and oi[i]/oi_start[i]-1>=c["oi_growth"] and width[i]<c["compression"]*rolling_width[i]:
            if close[i]>prior_high[i]*(1+c["breakout"]):signal=1
            elif close[i]<prior_low[i]*(1-c["breakout"]):signal=-1
        if reverse:signal=-signal
        if signal==0:
            curve.append((str(timestamp),equity));i+=1;continue
        j=i+1;entry=op[j]*(1+signal*SLIP)
        stop=entry*(1-signal*c["stop"])
        qty=min(equity*RISK/(entry*c["stop"]),equity*CAP/entry)
        entry_fee=qty*entry*FEE
        equity-=entry_fee
        extreme=entry;exitprice=None;reason="timeout"
        end=min(n-1,j+c["hold"])
        for k in range(j,end+1):
            # adverse intrabar priority: stop first, then update trailing using completed bar
            if signal==1 and low[k]<=stop:
                exitprice=stop*(1-SLIP);reason="stop";break
            if signal==-1 and high[k]>=stop:
                exitprice=stop*(1+SLIP);reason="stop";break
            if signal==1:
                extreme=max(extreme,high[k])
                stop=max(stop,extreme*(1-c["trail"]))
            else:
                extreme=min(extreme,low[k])
                stop=min(stop,extreme*(1+c["trail"]))
            if k==end:exitprice=close[k]*(1-signal*SLIP)
        exitfee=qty*exitprice*FEE
        pnl=signal*(exitprice-entry)*qty-entry_fee-exitfee
        equity+=signal*(exitprice-entry)*qty-exitfee
        peak=max(peak,equity);dd=max(dd,1-equity/peak)
        trades.append(dict(entry_utc=str(h.index[j]),exit_utc=str(h.index[k]),direction=signal,entry=entry,exit=exitprice,qty=qty,net_pnl=pnl,r=pnl/(qty*entry*c["stop"]),reason=reason,equity=equity))
        curve.append((str(h.index[k]),equity));i=k+1
    t=pd.DataFrame(trades)
    if t.empty:return {"trades":0,"net_return_pct":0,"pf":0,"max_dd_pct":dd*100,"win_rate_pct":0,"avg_win_loss":0,"largest_r":0,"monthly":[]},t
    w=t[t.net_pnl>0].net_pnl;l=t[t.net_pnl<0].net_pnl
    monthly=t.assign(month=pd.to_datetime(t.exit_utc,utc=True).dt.tz_convert("Asia/Kolkata").dt.strftime("%Y-%m")).groupby("month").net_pnl.agg(["sum","count"])
    monthly["pf"]=t.assign(month=pd.to_datetime(t.exit_utc,utc=True).dt.tz_convert("Asia/Kolkata").dt.strftime("%Y-%m")).groupby("month").net_pnl.apply(lambda x:float(x[x>0].sum()/(-x[x<0].sum())) if (x<0).any() else None)
    summary=dict(trades=len(t),net_return_pct=round((equity/START-1)*100,3),pf=round(float(w.sum()/-l.sum()),3) if len(l) else None,max_dd_pct=round(dd*100,3),win_rate_pct=round(100*len(w)/len(t),2),avg_win_loss=round(float(w.mean()/-l.mean()),3) if len(w) and len(l) else None,largest_r=round(float(t.r.max()),3),monthly=monthly.reset_index().to_dict("records"),without_largest_winner_pct=round(100*(equity-START-t.net_pnl.max())/START,3))
    return summary,t
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    btc=load("BTCUSD");eth=load("ETHUSD")
    # Fixed economic thresholds chosen ex ante; no optimization on 2026 or ETH.
    train=btc.loc["2025"];evaluation=btc.loc["2026"]
    results={}
    for name,h in [("BTC_2025_training",train),("BTC_2026_evaluation",evaluation),("ETH_2025",eth.loc["2025"]),("ETH_2026",eth.loc["2026"])]:
        s,t=backtest(h,CONFIG)
        control,ct=backtest(h,CONFIG,True)
        results[name]={"primary":s,"opposite_direction_control":control}
        t.to_csv(OUT/(name+"_trades.csv"),index=False)
        ct.to_csv(OUT/(name+"_control_trades.csv"),index=False)
    (OUT/"results.json").write_text(json.dumps(dict(hypothesis="Open-interest buildup during compression predicts explosive breakouts",config=CONFIG,selection="No optimization; BTC-only preregistered thresholds",results=results,limitations=["OI is a proxy, not positions or liquidations","Hourly OHLC cannot resolve intrabar order; stop-first used","Funding not modeled","No L2 spreads; slippage assumption","No mark-to-market intratrade drawdown","Partial 2026, no full 2026 annual return"]),indent=2))
    print(json.dumps({k:{z:v[z]["net_return_pct"] for z in v} for k,v in results.items()},indent=2))
if __name__=="__main__":main()
