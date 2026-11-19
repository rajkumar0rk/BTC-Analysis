#!/usr/bin/env python3
"""Pre-registered BTC-first jump-aftershock persistence test. No parameter optimization."""
import hashlib,json
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path("data/delta_india"); OUT=Path("analysis/daily_jump_aftershock_btcfirst_20261119")
NOTIONAL=1000.; CAPITAL=1000.; BASE=.00158; STRESS=.00238
def load(symbol):
    files=sorted((ROOT/symbol/"1m").glob("20??-??.csv.gz"))
    if len(files)<20: raise RuntimeError("insufficient authentic archives")
    a=[]; provenance=[]
    for f in files:
        z=pd.read_csv(f,compression="gzip",usecols=["time","open","high","low","close"])
        z["time"]=pd.to_datetime(z.time.astype("int64"),unit="s",utc=True)
        a.append(z.set_index("time"))
        provenance.append({"path":str(f),"sha256":hashlib.sha256(f.read_bytes()).hexdigest(),"rows":len(z)})
    x=pd.concat(a).sort_index()
    if x.index.has_duplicates: raise RuntimeError("duplicate minute bars")
    expected=pd.date_range(x.index[0],x.index[-1],freq="min")
    if not x.index.equals(expected): raise RuntimeError("non-dense minute bars")
    return x,provenance
def replay(symbol):
    x,prov=load(symbol)
    ret=np.log(x.close).diff()
    # Causal threshold: last 24h median absolute 1m log return, excluding current minute.
    med=ret.abs().shift(1).rolling(1440,min_periods=1440).median()
    # Completed jump minute j: abs(log return) >= 7 times prior-day median.
    # 30m observation period; enter j+31 minute open if the 30m net return retains
    # at least 50% of the jump's signed move; exclude any new >=7x jump in observation.
    # Jump detection uses only completed candle; entry is strictly later.
    jumps=np.flatnonzero(((ret.abs()>=7*med)&(med>0)).fillna(False).to_numpy())
    candidates={}
    for j in jumps:
        k=j+31
        if k+119>=len(x):continue
        if k//1440 != (j+1)//1440 and x.index[k].date()!=x.index[j].date():continue
        if j<1441:continue
        if (ret.iloc[j+1:j+31].abs().to_numpy()>=7*med.iloc[j+1:j+31].to_numpy()).any():continue
        sign=1 if ret.iloc[j]>0 else -1
        retained=sign*np.log(x.close.iloc[j+30]/x.close.iloc[j-1])
        if retained<.5*abs(ret.iloc[j]):continue
        day=x.index[k].strftime("%Y-%m-%d")
        if day not in candidates:candidates[day]=(k,sign,j)
    records=[]
    days=pd.date_range(x.index[0].floor("D"),x.index[-1].floor("D"),freq="D")
    for d in days:
        day=d.strftime("%Y-%m-%d")
        if day not in candidates:
            records.append(dict(symbol=symbol,day=day,status="NO_TRADE",gross_usd=0,net_usd=0,stress_usd=0,fee_gst_usd=0,slippage_usd=0,reason=""))
            continue
        k,sign,j=candidates[day]
        entry=float(x.open.iloc[k]);stop=entry*(1-sign*.004);target=entry*(1+sign*.008)
        price=float(x.close.iloc[k+119]);reason="TIME"
        for row in x.iloc[k:k+120].itertuples():
            if (sign==1 and row.low<=stop) or (sign==-1 and row.high>=stop):
                price=stop;reason="STOP";break
            if (sign==1 and row.high>=target) or (sign==-1 and row.low<=target):
                price=target;reason="TARGET";break
        gross=NOTIONAL*sign*(price/entry-1)
        net=gross-NOTIONAL*BASE
        records.append(dict(symbol=symbol,day=day,status="PROFIT" if net>0 else "LOSS",gross_usd=gross,
            net_usd=net,stress_usd=gross-NOTIONAL*STRESS,fee_gst_usd=NOTIONAL*.00118,
            slippage_usd=NOTIONAL*.0004,reason=reason,entry_utc=str(x.index[k]),jump_utc=str(x.index[j]),side=sign))
    return pd.DataFrame(records),dict(symbol=symbol,files=prov,first=str(x.index[0]),last=str(x.index[-1]),source="Delta India 1m OHLC; not executable bid/ask")
def summarize(g):
    v=g.net_usd.to_numpy(float); equity=np.r_[0,np.cumsum(v)]; gains=v[v>0].sum();loss=-v[v<0].sum()
    streak=0;worst=0
    for p in v:
        streak=streak+1 if p<0 else 0;worst=max(worst,streak)
    return pd.Series(dict(calendar_days=len(g),profitable_days=int((v>0).sum()),losing_days=int((v<0).sum()),
      no_trade_days=int((g.status=="NO_TRADE").sum()),trades=int((v!=0).sum()),
      net_usd=round(float(v.sum()),3),net_return_pct=round(float(v.sum()/CAPITAL*100),3),
      net_pf=round(float(gains/loss),3) if loss else None,
      max_drawdown_pct=round(float((np.maximum.accumulate(equity)-equity).max()/CAPITAL*100),3),
      worst_losing_streak=worst,median_daily_usd=round(float(np.median(v)),3),
      mean_daily_usd=round(float(v.mean()),3),worst_day_usd=round(float(v.min()),3),
      fees_gst_usd=round(float(g.fee_gst_usd.sum()),3),slippage_usd=round(float(g.slippage_usd.sum()),3),
      stress_net_usd=round(float(g.stress_usd.sum()),3)))
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    # BTC is the only market for hypothesis/parameters; frozen settings replayed on ETH.
    btc,qb=replay("BTCUSD")
    eth,qe=replay("ETHUSD")
    d=pd.concat([btc,eth],ignore_index=True)
    d["year"]=d.day.str[:4];d["month"]=d.day.str[:7]
    d.to_csv(OUT/"calendar_days.csv",index=False)
    annual=d.groupby(["symbol","year"],sort=False).apply(summarize,include_groups=False).reset_index()
    monthly=d.groupby(["symbol","month"],sort=False).apply(summarize,include_groups=False).reset_index()
    annual.to_csv(OUT/"annual.csv",index=False);monthly.to_csv(OUT/"monthly.csv",index=False)
    (OUT/"quality.json").write_text(json.dumps([qb,qe],indent=2))
    verdict="REJECT_BTC" if (annual[annual.symbol=="BTCUSD"].net_usd<=0).any() else "INCONCLUSIVE_UNVERIFIED_EXECUTION"
    report="# BTC-first single-minute jump aftershock persistence\n\nVerdict: "+verdict+"\n\n"+(
      "Economic hypothesis: large single-minute displacement that retains at least half its initial move after 30 minutes reflects persistent repricing, not temporary liquidity demand. Falsified if BTC net edge does not survive 2025 and 2026. No optimization or ETH-dependent tuning.\n\n"
      "Entry next minute open after 30-minute persistence observation, same jump direction; 7x prior-day median absolute return; exclude secondary shock; stop 0.4%, target 0.8%, time 120 minutes, one trade per calendar day, no leverage, no averaging. BTC-only decision; ETH identical frozen dimensionless parameters.\n\n"
      "Costs: 0.118% two-sided taker+GST and 0.040% adverse execution slippage, stress 0.238% total. Funding settlement, executable bid/ask, min contract, liquidation and financing NOT reconstructed. OHLC stop-first ambiguity. These are research estimates, not verified executable PnL. 2026 previously exposed, not pristine holdout.\n\n"
      "## Annual\n"+annual.to_markdown(index=False)+"\n\n## Monthly\n"+monthly.to_markdown(index=False)+"\n")
    (OUT/"REPORT.md").write_text(report)
    print("VERDICT",verdict)
    print(annual.to_string(index=False))
    print("REPORT",OUT/"REPORT.md")
if __name__=="__main__":main()
