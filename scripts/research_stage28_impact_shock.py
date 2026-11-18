#!/usr/bin/env python3
"""Stage28: causal 15m relative price-impact shock reversal, original Delta India 1m replay."""
import gzip, hashlib, json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path("data/delta_india/BTCUSD/1m")
OUT=Path("analysis/independent_stage28_impact_shock")
UTC=pd.Timestamp("2025-01-01",tz="UTC")
END=pd.Timestamp("2026-11-01",tz="UTC")
IST="Asia/Kolkata"
FEE=.0005*1.18
SLIP=5.
START_EQUITY=1000.
MONTHS=pd.period_range("2025-01","2026-10",freq="M").astype(str).tolist()

def read():
    manifest=json.loads((ROOT/"manifest.json").read_text())
    parts={x["file"]:x for x in manifest["partitions"]}
    chunks=[]
    for period in pd.period_range("2025-01","2026-10",freq="M"):
        name=str(period)+".csv.gz"
        p=ROOT/name
        assert p.exists(),name
        assert hashlib.sha256(p.read_bytes()).hexdigest()==parts[name]["sha256_gzip"],name+" checksum"
        d=pd.read_csv(p,compression="gzip",usecols=["time","open","high","low","close","volume"])
        assert len(d)==parts[name]["expected_minutes"]==parts[name]["observed_candles"],name+" missing minutes"
        d["time"]=pd.to_datetime(d.time,unit="s",utc=True)
        chunks.append(d)
    x=pd.concat(chunks,ignore_index=True).set_index("time").sort_index()
    assert not x.index.has_duplicates
    assert len(x)==len(pd.date_range(UTC,END,freq="min",inclusive="left"))
    assert (x.index.to_series().diff().dropna()==pd.Timedelta(minutes=1)).all()
    assert (x.low>0).all() and (x.high>=x[["open","close","low"]].max(axis=1)).all()
    assert (x.low<=x[["open","close"]].min(axis=1)).all()
    return x

def make_signals(x, impact_mult):
    b=x.resample("15min",label="left",closed="left").agg(
        open=("open","first"),high=("high","max"),low=("low","min"),
        close=("close","last"),volume=("volume","sum"),n=("close","size"))
    b=b[b.n==15].copy()
    ret=np.log(b.close/b.close.shift(1))
    # Only PRIOR completed 15m bars define the baseline.
    impact=ret.abs()/(b.volume.clip(lower=0)+1.0)
    base=impact.rolling(96,min_periods=96).median().shift(1)
    vbase=b.volume.rolling(96,min_periods=96).median().shift(1)
    prev=b.close.shift(1)
    tr=pd.concat([(b.high-b.low),(b.high-prev).abs(),(b.low-prev).abs()],axis=1).max(axis=1)
    b["atr"]=tr.rolling(14,min_periods=14).mean()
    thin=(b.volume<0.75*vbase)&(vbase>0)
    shock=(impact>impact_mult*base)&(base>0)&thin
    b["side"]=np.select([shock&(ret<0),shock&(ret>0)],[1,-1],default=0)
    b=b[(b.side!=0)&(b.atr>0)].copy()
    b.index=b.index+pd.Timedelta(minutes=15)
    return b

def replay(x,signals,mult):
    idx=x.index
    opens=x.open.to_numpy(); highs=x.high.to_numpy(); lows=x.low.to_numpy(); closes=x.close.to_numpy()
    eq=START_EQUITY; ledger=[]; monthly=[]
    # Monthly equity accounting includes mark-to-market only on closed trades; positions
    # forcibly close at IST month boundary, so calendar-month equity is unambiguous.
    for month in MONTHS:
        month_start=pd.Timestamp(month+"-01",tz=IST).tz_convert("UTC")
        month_end=(pd.Timestamp(month+"-01",tz=IST)+pd.offsets.MonthBegin(1)).tz_convert("UTC")
        start_eq=eq
        ss=signals[(signals.index>=month_start)&(signals.index<month_end)]
        busy_until=-1
        for t,z in ss.iterrows():
            k=int(idx.searchsorted(t))
            if k>=len(idx) or idx[k]!=t or k<=busy_until:continue
            if idx[k]>=month_end:continue
            side=int(z.side); entry=float(opens[k])+side*SLIP
            dist=float(z.atr)*mult
            if dist<=0 or entry<=0:continue
            qty=min(eq*.01/dist,eq*3/entry)
            if qty<=0:continue
            stop=entry-side*dist; target=entry+side*2*dist
            exit_limit=int(idx.searchsorted(month_end))
            maxj=min(k+239,exit_limit-1,len(idx)-1)
            if maxj<k:continue
            # Initial stop/target cannot fill on signal candle; first checked entry minute.
            xp=None;why="timeout";j=maxj
            for v in range(k,maxj+1):
                if side==1:
                    if lows[v]<=stop:xp=stop;why="stop";j=v;break
                    if highs[v]>=target:xp=target;why="target";j=v;break
                else:
                    if highs[v]>=stop:xp=stop;why="stop";j=v;break
                    if lows[v]<=target:xp=target;why="target";j=v;break
            if xp is None:xp=float(closes[j])
            # Exit slippage worsens stop, target and timed exits.
            exit_price=xp-side*SLIP
            gross=side*(exit_price-entry)*qty
            fees=(abs(entry)+abs(exit_price))*qty*FEE
            net=gross-fees
            before=eq;eq+=net
            ledger.append(dict(month_ist=month,entry_utc=str(t),exit_utc=str(idx[j]),side=side,
                qty_btc=qty,entry_price=entry,exit_price=exit_price,reason=why,
                gross_usd=gross,fees_gst_usd=fees,net_usd=net,equity_before=before,equity_after=eq))
            busy_until=j
            if eq<=0:break
        rows=[z for z in ledger if z["month_ist"]==month]
        monthly.append(dict(month_ist=month,return_pct=100*(eq/start_eq-1) if start_eq>0 else -100,
            start_equity=start_eq,end_equity=eq,trades=len(rows),
            wins=sum(z["net_usd"]>0 for z in rows),
            losses=sum(z["net_usd"]<0 for z in rows),
            net_usd=sum(z["net_usd"] for z in rows)))
        if eq<=0:break
    return pd.DataFrame(monthly),pd.DataFrame(ledger)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    x=read()
    results=[];saved={}
    for ratio in (3.,5.):
        signals=make_signals(x,ratio)
        for mult in (1.5,2.5):
            m,l=replay(x,signals,mult)
            key=f"impact{ratio:g}_stop{mult:g}"
            saved[key]=(m,l)
            train=m[m.month_ist<"2026-01"]
            val=m[m.month_ist>="2026-01"]
            results.append(dict(key=key,train_positive=int((train.return_pct>0).sum()),
                recheck_positive=int((val.return_pct>0).sum()),
                train_ge10=int((train.return_pct>=10).sum()),
                recheck_ge10=int((val.return_pct>=10).sum()),
                train_total_pct=float(train.return_pct.sum()),
                worst_month_pct=float(m.return_pct.min()),
                total_trades=int(m.trades.sum()),
                all_22_positive=bool(len(m)==22 and (m.return_pct>0).all()),
                all_22_ge10=bool(len(m)==22 and (m.return_pct>=10).all())))
    r=pd.DataFrame(results).sort_values(
        ["train_positive","train_total_pct"],ascending=False)
    r.to_csv(OUT/"configurations.csv",index=False)
    chosen=r.iloc[0]["key"]
    m,l=saved[chosen]
    m.to_csv(OUT/"monthly_2025_2026.csv",index=False)
    l.to_csv(OUT/"ledger.csv",index=False)
    curve=np.r_[START_EQUITY,l.equity_after.to_numpy()] if not l.empty else np.array([START_EQUITY])
    dd=float((curve/np.maximum.accumulate(curve)-1).min()*100)
    quality=dict(source="Delta Exchange India original BTCUSD 1m",input_months=22,
        source_minutes=len(x),october_2026_complete=True,
        selected_using="2025 only, ranking positive months then sum of monthly net returns",
        chosen=chosen,all_22_positive=bool(len(m)==22 and (m.return_pct>0).all()),
        all_22_ge10=bool(len(m)==22 and (m.return_pct>=10).all()),
        total_trades=int(len(l)),wins=int((l.net_usd>0).sum()) if len(l) else 0,
        losses=int((l.net_usd<0).sum()) if len(l) else 0,
        max_trade_close_drawdown_pct=dd,
        fee_per_side_with_gst=FEE,slippage_points_per_side=SLIP,
        missing=["funding","actual bid/ask spread","actual order-book market impact","lot size/margin/liquidation"],
        first_IST_month_missing_hours=5.5,
        warning="2026 history was seen in previous studies; not pristine forward validation")
    (OUT/"quality.json").write_text(json.dumps(quality,indent=2)+"\n")
    lines=["# Stage28 — 15m relative price-impact shock fade","",
        "This is exploratory, not an executable live edge. Original data checksum verified.",
        "Price impact is only an OHLCV-based displacement/volume proxy, not measured market impact.",
        "October 2026 UTC 1m is fully repaired on the isolated branch.",
        "January 2025 IST lacks the first 5.5 hours; cannot assert fully observed 22 IST months.",
        "Fees and GST included, 5 points adverse slippage each side; no funding, spread, market impact or lot granularity.",
        "Sizing uses 1% equity stop-distance risk and 3x notional cap, not validated Delta margin.",
        "2025-only model selection, 2026 already seen in prior research (not blind).","",
        "## All configurations","",r.to_markdown(index=False),"",
        "## Chosen 2025-only configuration",chosen,"",
        "## Monthly net account returns","",m.to_markdown(index=False),"",
        "## Audit",json.dumps(quality,indent=2),"",
        "No guarantee of future profits. Never place orders from this research."]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(lines)+"\n")
    print(json.dumps(quality,indent=2))

if __name__=="__main__":
    main()
