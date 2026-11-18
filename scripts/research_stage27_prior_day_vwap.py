#!/usr/bin/env python3
"""Stage27 fixed-rule prior UTC day VWAP reclaim; reproducible BTCUSD 1m replay."""
import gzip,hashlib,json
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path("data/delta_india/BTCUSD/1m")
OUT=Path("analysis/independent_stage27_prior_day_vwap")
IST="Asia/Kolkata"
FEE=0.0005*1.18
SLIP=5.
MONTHS=pd.period_range("2025-01","2026-10",freq="M").astype(str).tolist()
def load():
    manifest=json.loads((ROOT/"manifest.json").read_text())
    parts={p["file"]:p for p in manifest["partitions"]}
    frames=[]
    for period in pd.period_range("2025-01","2026-10",freq="M"):
        name=str(period)+".csv.gz";path=ROOT/name;p=parts[name]
        assert hashlib.sha256(path.read_bytes()).hexdigest()==p["sha256_gzip"],name
        assert p["observed_candles"]==p["expected_minutes"],name
        df=pd.read_csv(path,compression="gzip",usecols=["time","open","high","low","close","volume"])
        assert len(df)==p["expected_minutes"],name
        df["time"]=pd.to_datetime(df.time,unit="s",utc=True)
        frames.append(df)
    x=pd.concat(frames,ignore_index=True).set_index("time").sort_index()
    assert not x.index.has_duplicates
    assert len(x)==len(pd.date_range("2025-01-01", "2026-11-01",freq="min",tz="UTC",inclusive="left"))
    assert (x.index.to_series().diff().dropna()==pd.Timedelta(minutes=1)).all()
    assert (x.low>0).all() and (x.high>=x[["open","close","low"]].max(axis=1)).all()
    assert (x.low<=x[["open","close"]].min(axis=1)).all()
    assert (x.volume>=0).all()
    return x
def signals(x):
    typ=(x.high+x.low+x.close)/3
    day=(typ*x.volume).resample("1D").sum()/x.volume.resample("1D").sum().replace(0,np.nan)
    h=x.resample("1h",label="left",closed="left").agg(open=("open","first"),high=("high","max"),low=("low","min"),close=("close","last"),n=("close","size"))
    h=h[h.n==60].copy()
    prev=h.close.shift(1)
    tr=pd.concat([h.high-h.low,(h.high-prev).abs(),(h.low-prev).abs()],axis=1).max(axis=1)
    h["atr"]=tr.rolling(14,min_periods=14).mean()
    # Yesterday's completed UTC VWAP is available at current day 00:00 UTC.
    h["anchor"]=day.shift(1).reindex(h.index.normalize()).to_numpy()
    h["side"]=np.select([(prev<h.anchor)&(h.close>h.anchor)&(h.close>h.open),
                          (prev>h.anchor)&(h.close<h.anchor)&(h.close<h.open)],[1,-1],default=0)
    h=h[(h.side!=0)&(h.atr>0)&h.anchor.notna()].copy()
    h.index=h.index+pd.Timedelta(hours=1)
    return h
def replay(x,s):
    idx=x.index;opens=x.open.to_numpy();highs=x.high.to_numpy();lows=x.low.to_numpy();closes=x.close.to_numpy()
    equity=1000.;ledger=[];months=[];busy=-1
    for month in MONTHS:
        start=pd.Timestamp(month+"-01",tz=IST).tz_convert("UTC")
        end=(pd.Timestamp(month+"-01",tz=IST)+pd.offsets.MonthBegin(1)).tz_convert("UTC")
        initial=equity;cnt=win=loss=0
        for t,z in s[(s.index>=start)&(s.index<end)].iterrows():
            k=int(idx.searchsorted(t))
            if k>=len(idx) or idx[k]!=t or k<=busy or idx[k]>=end:continue
            side=int(z.side);entry=float(opens[k])+side*SLIP;dist=1.5*float(z.atr)
            if dist<=0 or entry<=0:continue
            qty=min(equity*0.005/dist,equity*3/entry)
            if qty<=0:continue
            stop=entry-side*dist;target=entry+side*2*dist
            last=min(k+719,int(idx.searchsorted(end))-1,len(idx)-1)
            if last<k:continue
            j=last;price=float(closes[j]);why="timeout"
            for v in range(k,last+1):
                if (lows[v]<=stop if side==1 else highs[v]>=stop):
                    price=stop;why="stop";j=v;break
                if (highs[v]>=target if side==1 else lows[v]<=target):
                    price=target;why="target";j=v;break
            exitprice=price-side*SLIP
            gross=side*(exitprice-entry)*qty
            fee=(abs(entry)+abs(exitprice))*qty*FEE
            net=gross-fee;before=equity;equity+=net
            ledger.append(dict(month_ist=month,entry_utc=str(t),exit_utc=str(idx[j]),side=side,entry=entry,exit=exitprice,qty_btc=qty,reason=why,gross_usd=gross,fees_gst_usd=fee,net_usd=net,equity_before=before,equity_after=equity))
            busy=j;cnt+=1;win+=int(net>0);loss+=int(net<0)
            if equity<=0:break
        months.append(dict(month_ist=month,return_pct=100*(equity/initial-1) if initial>0 else -100,start_equity=initial,end_equity=equity,trades=cnt,wins=win,losses=loss))
        if equity<=0:break
    return pd.DataFrame(months),pd.DataFrame(ledger)
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    x=load();s=signals(x);m,l=replay(x,s)
    m.to_csv(OUT/"monthly.csv",index=False);l.to_csv(OUT/"ledger.csv",index=False)
    curve=np.r_[1000.,l.equity_after.to_numpy()] if len(l) else np.array([1000.])
    dd=100*(curve/np.maximum.accumulate(curve)-1).min()
    q=dict(strategy="prior_utc_day_vwap_hourly_reclaim",months=len(m),positive_months=int((m.return_pct>0).sum()),months_ge10=int((m.return_pct>=10).sum()),all_22_positive=bool(len(m)==22 and (m.return_pct>0).all()),all_22_ge10=bool(len(m)==22 and (m.return_pct>=10).all()),total_trades=len(l),wins=int((l.net_usd>0).sum()) if len(l) else 0,losses=int((l.net_usd<0).sum()) if len(l) else 0,win_rate_pct=100*(l.net_usd>0).mean() if len(l) else 0,max_trade_close_drawdown_pct=float(dd),start_equity=1000.,end_equity=float(curve[-1]),net_return_pct=float((curve[-1]/1000-1)*100),fee_with_gst_per_side=FEE,slippage_btc_points_per_side=SLIP,source="Delta India BTCUSD 1m verified manifest 2025-01 to 2026-10",first_IST_month_missing_hours=5.5,missing=["funding","bid_ask_spread","market_impact","lot_size","margin_liquidation"],not_pristine_out_of_sample=True)
    (OUT/"quality.json").write_text(json.dumps(q,indent=2)+"\n")
    (OUT/"RESEARCH_REPORT.md").write_text("# Stage27 previous-day VWAP reclaim\n\nSingle predeclared rule, no 2026 tuning. Not a live trading signal.\n\n"+m.to_markdown(index=False)+"\n\n## Audit\n\n```json\n"+json.dumps(q,indent=2)+"\n```\n")
    print(json.dumps(q,indent=2))
if __name__=="__main__":main()
