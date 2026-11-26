#!/usr/bin/env python3
"""ETHUSD-native ATR based replay of original BTC-Analysis price action concepts.

All candles are unscaled real Delta India ETHUSD 1m OHLCV.
Do NOT transplant a fixed 200 BTC price-point stop/target to ETH.
Signals from completed 5m, 1h and 4h bars. Next 1m OPEN fills.
No BTC price, BTC-based ratio or virtual BTC quotes in this research.
Stop-first ambiguous OHLC, adverse gap exit. Capital at 0.5% risk
per closed trade, <=5x maximum notional, exclusive position per model.
Fee=0.05% taker EACH side plus 18% GST, assumed slippage=0.02% each side.
No actual ETH funding, observed spread, book depth or margin model.
Do not trade. 22 completed IST months Jan2025-Oct2026, Nov excluded.
"""
from pathlib import Path
import hashlib,json
import numpy as np
import pandas as pd
from numba import njit

ROOT=Path("data/delta_india/ETHUSD/1m")
OUT=Path("analysis/ethusd_native_atr_price_action")
MONTHS=pd.period_range("2025-01","2026-10",freq="M").astype(str).tolist()
FEE=.0005*1.18
SLIP=.0002  # 0.02% assumed adverse ETH price slippage PER SIDE
RISK_FRAC=.005
LEV_CAP=5.
ATRMULT=(1.5,3.)
REWARDS=(2.,3.)
HOLDS=(240,720)

def source():
    manifest=json.loads((ROOT/"manifest.json").read_text())
    parts=[z for z in manifest["partitions"] if z["file"].endswith(".csv.gz")
           and z["file"]<="2026-11.csv.gz"]
    if len(parts)!=23:raise RuntimeError("Missing months of ETHUSD 1m data")
    files=[]
    for p in parts:
        raw=(ROOT/p["file"]).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=p["sha256_gzip"]:
            raise AssertionError("Invalid ETH data SHA: "+p["file"])
        if p["missing_minutes"]!=0:raise AssertionError("ETH source gap")
        df=pd.read_csv(ROOT/p["file"],compression="gzip",
            usecols=["time","open","high","low","close","volume"])
        if len(df)!=p["observed_candles"]:raise AssertionError("Count mismatch "+p["file"])
        files.append(df)
    f=pd.concat(files,ignore_index=True).sort_values("time").reset_index(drop=True)
    ts=f.time.to_numpy("int64")
    if np.any(np.diff(ts)!=60):
        raise RuntimeError("ETH source is not consecutive 1m data")
    if ((f.high<f.low)|(f.open>f.high)|(f.open<f.low)|
        (f.close>f.high)|(f.close<f.low)|(f.low<=0)).any():
        raise AssertionError("Invalid ETH price candle")
    f.index=pd.to_datetime(f.time,unit="s",utc=True)
    # Truncate immediately after the complete October IST close.
    # Last minute of 2026-Oct in IST = 2026-10-31 18:29 UTC.
    cutoff=pd.Timestamp("2026-10-31 18:30:00+00:00")
    f=f.loc[f.index<cutoff].copy()
    return f,dict(raw_rows=len(ts),rows_through_october_ist=len(f),
        utc_start=str(f.index[0]),utc_last=str(f.index[-1]),
        sha256_checked_partitions=len(parts),
        last_month_for_scoring="2026-10",slippage_pct_each_side=100*SLIP,
        first_ist_month_missing_utc_minutes=330,
        january_2025_ist_coverage_complete=False)

def features(f,tf,span):
    cols=["open","high","low","close","volume"]
    b=f[cols].resample(tf,label="right",closed="left").agg(dict(
       open="first",high="max",low="min",close="last",volume="sum"))
    b["count"]=f.close.resample(tf,label="right",closed="left").count()
    b["good"]=b["count"].rolling(60,min_periods=60).min().eq(span)
    b["prevclose"]=b.close.shift(1)
    tr=pd.concat([b.high-b.low,(b.high-b.prevclose).abs(),
           (b.low-b.prevclose).abs()],axis=1).max(axis=1)
    b["atr"]=tr.rolling(14,min_periods=14).mean()
    b["ema20"]=b.close.ewm(span=20,adjust=False).mean()
    b["ema50"]=b.close.ewm(span=50,adjust=False).mean()
    b["range"]=b.high-b.low
    b["loc"]=(b.close-b.low)/b["range"].replace(0,np.nan)
    b["body"]=(b.close-b.open).abs()/b["range"].replace(0,np.nan)
    b["prev12h"]=b.high.shift(1).rolling(12).max()
    b["prev12l"]=b.low.shift(1).rolling(12).min()
    b["prev20h"]=b.high.shift(1).rolling(20).max()
    b["prev20l"]=b.low.shift(1).rolling(20).min()
    b["prev6h"]=b.high.shift(1).rolling(6).max()
    b["prev6l"]=b.low.shift(1).rolling(6).min()
    b["vmean"]=b.volume.shift(1).rolling(20).mean()
    b["vr"]=b.volume/b.vmean.replace(0,np.nan)
    b["rmed"]=b["range"].shift(1).rolling(24).median()
    diff=b.close.diff()
    au=diff.clip(lower=0).ewm(alpha=.5,adjust=False,min_periods=2).mean()
    ad=(-diff.clip(upper=0)).ewm(alpha=.5,adjust=False,min_periods=2).mean()
    b["rsi2"]=100*au/(au+ad).replace(0,np.nan)
    bull=(b.close>b.open)&(b["loc"]>=.68)&(b["body"]>=.35)
    bear=(b.close<b.open)&(b["loc"]<=.32)&(b["body"]>=.35)
    previnside=(b.high.shift(1)<b.high.shift(2)) & (
        b.low.shift(1)>b.low.shift(2))
    comp=(b["range"].shift(1)+b["range"].shift(2)+b["range"].shift(3))/3 \
        < .75*b.rmed
    trendup=(b.ema20>b.ema50)&(b.close>b.ema20)
    trenddn=(b.ema20<b.ema50)&(b.close<b.ema20)
    patterns={
      "donchian20_breakout":(
        bull&(b.close>b.prev20h)&(b.vr>=1.1),
        bear&(b.close<b.prev20l)&(b.vr>=1.1)),
      "sweep12_rejection":(
        bull&(b.low<b.prev12l)&(b.close>b.prev12l),
        bear&(b.high>b.prev12h)&(b.close<b.prev12h)),
      "ema20_pullback":(
        bull&trendup&(b.low<=b.ema20),
        bear&trenddn&(b.high>=b.ema20)),
      "inside_bar_breakout":(
        bull&previnside&(b.close>b.high.shift(2)),
        bear&previnside&(b.close<b.low.shift(2))),
      "compression_breakout":(
        bull&comp&(b.close>b.prev6h)&(b["range"]>=1.3*b.rmed),
        bear&comp&(b.close<b.prev6l)&(b["range"]>=1.3*b.rmed)),
      "rsi2_reversal_confirm":(
        bull&(b.rsi2.shift(1)<=5)&(b.rsi2>=25),
        bear&(b.rsi2.shift(1)>=95)&(b.rsi2<=75)),
      "strong_momentum":(
        bull&(b.close>b.prev6h)&(b["body"]>=.65)&(b.vr>=1.2),
        bear&(b.close<b.prev6l)&(b["body"]>=.65)&(b.vr>=1.2)),
      "failed_break_followthrough":(
        bull&(b.close.shift(1)<b.prev12l.shift(1))&(b.close>b.prev12l),
        bear&(b.close.shift(1)>b.prev12h.shift(1))&(b.close<b.prev12h)),
    }
    idx=f.index.get_indexer(b.index)
    px=f.open.to_numpy(float)
    result=[]
    for pat,(long,short) in patterns.items():
        for s,mask in [(1,long),(-1,short)]:
            eligible=(mask.fillna(False)&b.good&b.atr.gt(0)).to_numpy(bool)
            for j in np.flatnonzero(eligible):
                k=int(idx[j])
                if k<0 or k+max(HOLDS)>len(f):continue
                pr=float(px[k]);atr=float(b.atr.iat[j])
                if not np.isfinite(atr) or atr<=0:continue
                result.append(dict(pattern=f"{tf}_{pat}",tf=tf,k=k,side=s,
                    atr=atr,entry_px=pr,entry_unix=int(f.time.iat[k])))
    return result

@njit(cache=True)
def replay(o,h,l,c,entry_idx,side,risk,rr,hold):
    entry=o[entry_idx]
    stop=entry-side*risk
    target=entry+side*rr*risk
    for j in range(entry_idx,entry_idx+hold):
        sl=(l[j]<=stop) if side==1 else (h[j]>=stop)
        tp=(h[j]>=target) if side==1 else (l[j]<=target)
        if sl:
            mid=min(o[j],stop) if side==1 else max(o[j],stop)
            why=0
            break
        if tp:
            mid=target
            why=1
            break
    else:
        j=entry_idx+hold-1
        mid=c[j]
        why=2
    entryfill=entry*(1+side*SLIP)
    exitfill=mid*(1-side*SLIP)
    gross=side*(mid-entry)
    net=side*(exitfill-entryfill)-FEE*(entryfill+exitfill)
    return j,net,gross,why,entryfill,exitfill,stop,target

def compute(f,events):
    o=f.open.to_numpy(float);h=f.high.to_numpy(float)
    l=f.low.to_numpy(float);c=f.close.to_numpy(float);t=f.time.to_numpy(np.int64)
    E=pd.DataFrame(events)
    if E.empty:raise RuntimeError("No ETH events")
    logs=[]
    names=sorted(E.pattern.unique())
    for name in names:
        filt=E[E.pattern==name].sort_values(["k","side"])
        for mult in ATRMULT:
            for rr in REWARDS:
                for hold in HOLDS:
                    model=f"{name}|SL={mult:g}ATR|TP={rr:g}R|hold={hold}m"
                    last=-1
                    for z in filt.itertuples(index=False):
                        if z.k<=last or z.k+hold>len(f):continue
                        risk=mult*z.atr
                        relative=risk/z.entry_px
                        if not (.0008<=relative<=.12):continue
                        j,net,gross,why,entryfill,exitfill,stop_price,target_price=replay(o,h,l,c,int(z.k),int(z.side),
                            float(risk),float(rr),int(hold))
                        last=j
                        fraction=min(RISK_FRAC,LEV_CAP*risk/z.entry_px)
                        ret=fraction*net/risk
                        if ret<=-1:raise AssertionError("Trade wipes out all equity")
                        logs.append(dict(model=model,pattern=name,
                            entry_unix=z.entry_unix,exit_unix=int(t[j]),
                            month_ist=pd.Timestamp(int(t[j]),unit="s",tz="UTC").
                              tz_convert("Asia/Kolkata").strftime("%Y-%m"),
                            direction="LONG" if z.side==1 else "SHORT",
                            entry_price_usd=float(z.entry_px),
                            entry_fill_usd=float(entryfill),exit_price_usd=float(exitfill),
                            stop_price=float(stop_price),target_price=float(target_price),
                            entry_reason=name,exit_reason=["Stop touched (stop-first)","Target touched","Maximum hold reached"][why],
                            signal_atr=float(z.atr),
                            stop_distance_eth_usd=round(float(risk),6),
                            target_distance_eth_usd=round(float(rr*risk),6),
                            net_eth_price_points=round(float(net),6),
                            gross_eth_price_points=round(float(gross),6),
                            equity_trade_return=float(ret),
                            result=["SL","TP","Timeout"][why]))
    if not logs:raise RuntimeError("No ETH trades after ATR risk band")
    return pd.DataFrame(logs)

def monthly_models(tr):
    allmonths=[];rank=[]
    for model,z in tr.groupby("model",sort=True):
        cnt=[];nav=[]
        for m in MONTHS:
            x=z[z.month_ist==m].sort_values("exit_unix")
            vals=x.equity_trade_return.to_numpy(float)
            compounded=100*(np.prod(1+vals)-1)
            cnt.append(int(len(x)))
            nav.append(compounded)
            allmonths.append(dict(model=model,month_ist=m,
                trades=len(x),
                winning_trades=int((x.net_eth_price_points>0).sum()),
                losing_trades=int((x.net_eth_price_points<0).sum()),
                flat_trades=int((x.net_eth_price_points==0).sum()),
                net_account_return_pct=round(float(compounded),6),
                mean_initial_stop_eth_usd=round(float(x.stop_distance_eth_usd.mean()),4)
                    if len(x) else None,
                mean_initial_target_eth_usd=round(float(x.target_distance_eth_usd.mean()),4)
                    if len(x) else None))
        nav=np.array(nav,dtype=float)
        equity=np.r_[100,100*np.cumprod(1+nav/100)]
        dd=100*float(np.max(1-equity/np.maximum.accumulate(equity)))
        rank.append(dict(model=model,
            months_positive_2025=int((nav[:12]>1e-8).sum()),
            months_positive_2026=int((nav[12:]>1e-8).sum()),
            months_positive_all=int((nav>1e-8).sum()),
            complete_22_positive=bool((nav>1e-8).all()),
            compounding_2025_pct=round(float(100*(np.prod(1+nav[:12]/100)-1)),4),
            compounding_2026_pct=round(float(100*(np.prod(1+nav[12:]/100)-1)),4),
            max_month_end_drawdown_pct=round(dd,5),
            trades=int(cnt.__len__() and sum(cnt)),
            wins=int((z.net_eth_price_points>0).sum()),
            losses=int((z.net_eth_price_points<0).sum())))
    return pd.DataFrame(allmonths),pd.DataFrame(rank)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    f,qual=source()
    all_events=[]
    for tf,span in [("5min",5),("1h",60),("4h",240)]:
        e=features(f,tf,span)
        print("NATIVE_ETH_EVENTS",tf,len(e),flush=True)
        all_events.extend(e)
    tr=compute(f,all_events)
    mon,rank=monthly_models(tr)
    selected=rank.sort_values(["months_positive_2025","compounding_2025_pct"],
        ascending=False).iloc[0]
    selected_month=mon[mon.model==selected.model]
    mon.to_csv(OUT/"all_model_monthly.csv.gz",compression="gzip",index=False)
    rank.to_csv(OUT/"all_model_summary.csv",index=False)
    selected_month.to_csv(OUT/"selected_2025_ranked_monthly.csv",index=False)
    tr.to_csv(OUT/"full_trade_ledger.csv.gz",compression="gzip",index=False)
    metadata=dict(
        symbol="ETHUSD",source=qual,
        old_BTC_200_point_target_used=False,
        stop="1.5x or 3x authentic ETH ATR14 on signal timeframe",
        take_profit="2R or 3R of ATR-based stop distance",
        timeframes=["5min","1h","4h"],
        distinct_pattern_families=8,unique_models=len(rank),
        total_independent_replayed_trade_rows=len(tr),
        historical_all22_positive_models=int(rank.complete_22_positive.sum()),
        selected_2025_only=selected.to_dict(),
        standard_costs="Taker 0.05% each side + GST 18%; assumed 0.02% adverse price slippage each side",
        assumptions=[
         "ETHUSD source is native raw unscaled data with sha256 verified per partition",
         "No literal 200-point BTC stops, targets, or virtual BTC price units",
         "ATR/percent distances adapt natively to ETH price history; actual ETH USD stop/target shown in audit",
         "0.02% slippage assumption is not measured spread, realized fill or market impact",
         "Funding, contract lot size, margin availability, liquidation and actual spread are NOT included",
         "One exclusive trade per model, returns compounded at monthly IST exit time",
         "2026 is previously explored through BTC strategy research, not a pristine OOS sample",
         "Selection uses 2025 only, then reports 2026 without parameter alteration",
         "2026 November excluded; 2025 January lacks first 5.5 IST hours (Dec 31 2024 18:30-23:59 UTC), so not all 22 IST months have complete source coverage"
        ])
    (OUT/"quality.json").write_text(json.dumps(metadata,indent=2,default=str)+"\n")
    report=[
       "# Native ETHUSD ATR price-action family backtest",
       "",
       "All source ETHUSD candles are UNscaled. **No BTC fixed 200-point stop/target.**",
       "Data limitation: Jan 1, 2025 00:00–05:29 IST is absent because the archive begins Jan 1 UTC; other scored IST months have complete source coverage.",
       "Tested 8 entry-pattern families × 3 timeframes × 2 ATR stops × 2R/3R",
       "× 240/720-minute maximum hold.",
       "",
       "## Simulation and costs",
       f"Total model variations: {len(rank)}; trades across separate models: {len(tr)}.",
       "One position per independent model. Slippage assumed 0.02% per side.",
       "Taker fee 0.05% per side plus GST 18%. Missing funding/real order book.",
       "",
       "## Ranked only using Jan-Dec 2025",
       rank.sort_values(["months_positive_2025","compounding_2025_pct"],
           ascending=False).head(20).to_markdown(index=False),"",
       "## Selected model's 2025 and 2026 monthly actual ETH-dollar risk",
       selected_month.to_markdown(index=False),"",
       "## Limitations",
       *["- "+z for z in metadata["assumptions"]],
    ]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")
    print("NATIVE_ETH_COMPLETE "+json.dumps(dict(
       models=len(rank),trades=len(tr),full22=int(rank.complete_22_positive.sum()),
       selected={k:v for k,v in selected.to_dict().items() if k!="model"},
       selected_model=selected.model)),flush=True)
    print("SELECTED_MONTHS\n"+selected_month.to_string(index=False),flush=True)
if __name__=="__main__":main()
