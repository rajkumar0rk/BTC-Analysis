#!/usr/bin/env python3
"""Native ETHUSD cross-market trading-family audit with entry-time percentage normalization.

Independent from BTC research ledgers / prior tuned parameters. Defines one causal
rule per historical trading family and a small predeclared risk/exit grid.
This is a representative FAMILY test, not byte-identical reexecution of all
previous individual scripts; exact original-code portability is audited in
the separate eth_all_prior_strategy_runner.py batch.

Fixed BTC points (e.g. 100 stop / 200 target) translated at each entry:
ETH points = ETH entry price * (BTC point threshold / concurrent BTC price).
Native ATR stops are already ETH-scaled. No synthetic OHLC price discontinuities.

Original Delta India ETHUSD and BTCUSD 1m CSV.gz, 22 complete UTC-month partitions;
2025-01 00:00 UTC through 2026-10-31 23:59 UTC. 2026 November excluded.
0.05% taker fee PER SIDE + 18% GST on fee, ETH 0.25 native-price-point
adverse slippage PER SIDE as an unverified sensitivity proxy (actual fills
unknown), funding/spread/impact/contract lot/liquidations not modelled.
5m/15m/1h/4h signals only from fully completed bars; 1m stop-first fills.
Selection by 2025 results only; 2026 history previously viewed (not blind OOS).
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from numba import njit

R=Path("data/delta_india")
OUT=Path("analysis/eth_native_crossfamily_v2")
MONTHS=pd.period_range("2025-01","2026-10",freq="M").astype(str).tolist()
MONTH_CODES=np.array([int(v.replace("-","")) for v in MONTHS],dtype=np.int32)
FEE=.0005*1.18
ETH_SLIP=.25
INITIAL_EQUITY=1000.
RISK=.005
CAP=3.
STRATEGY_LIMIT=42

def load(symbol):
    path=R/symbol/"1m"
    meta=json.loads((path/"manifest.json").read_text())
    info={x["file"]:x for x in meta["partitions"]}
    chunks=[]
    for month in MONTHS:
        file=month+".csv.gz"
        p=path/file
        q=info.get(file)
        if q is None or q["missing_minutes"]!=0 or q["observed_candles"]!=q["expected_minutes"]:
            raise RuntimeError(f"Missing original {symbol} 1m source: {file}")
        import hashlib
        if hashlib.sha256(p.read_bytes()).hexdigest()!=q["sha256_gzip"]:
            raise RuntimeError(f"Original source SHA-256 mismatch: {symbol}/{file}")
        d=pd.read_csv(p,compression="gzip",usecols=["time","open","high","low","close","volume"])
        if len(d)!=q["observed_candles"]:raise RuntimeError("Row count mismatch")
        chunks.append(d)
    f=pd.concat(chunks,ignore_index=True).sort_values("time",kind="stable")
    t=f.time.to_numpy(np.int64)
    if not (np.diff(t)==60).all():
        raise RuntimeError("Original source has missing or duplicate one minute timestamps")
    f.index=pd.to_datetime(t,unit="s",utc=True)
    if f.isna().any().any():raise RuntimeError("NaN ETH or BTC data")
    if ((f.low<=0)|(f.high<f[["open","close","low"]].max(axis=1))|
        (f.low>f[["open","close"]].min(axis=1))).any():
        raise RuntimeError("Invalid original OHLC")
    return f

def aggregate(f,rule):
    x=f[["open","high","low","close","volume"]].resample(
        rule,label="right",closed="left").agg(
        {"open":"first","high":"max","low":"min","close":"last","volume":"sum"})
    n={"5min":5,"15min":15,"1h":60,"4h":240}[rule]
    cnt=f.close.resample(rule,label="right",closed="left").count()
    x["valid"]=(cnt==n)&cnt.rolling(56,min_periods=56).min().eq(n)
    pc=x.close.shift()
    tr=pd.concat([x.high-x.low,(x.high-pc).abs(),(x.low-pc).abs()],axis=1).max(axis=1)
    x["atr"]=tr.rolling(14,min_periods=14).mean()
    for w in (9,20,21,50,200):
        x[f"ema{w}"]=x.close.ewm(span=w,adjust=False).mean()
    for w in (2,14):
        delta=x.close.diff()
        up=delta.clip(lower=0).ewm(alpha=1/w,adjust=False).mean()
        dn=(-delta.clip(upper=0)).ewm(alpha=1/w,adjust=False).mean()
        rs=up/dn.replace(0,np.nan)
        x[f"rsi{w}"]=(100-100/(1+rs)).fillna(
            np.where(up>0,100.,50.))
    x["vr"]=x.volume/x.volume.shift(1).rolling(20).mean().replace(0,np.nan)
    x["rng"]=x.high-x.low
    x["body"]=(x.close-x.open).abs()/x.rng.replace(0,np.nan)
    x["loc"]=(x.close-x.low)/x.rng.replace(0,np.nan)
    for n in (8,20,24,48,55):
        x[f"high{n}"]=x.high.shift(1).rolling(n).max()
        x[f"low{n}"]=x.low.shift(1).rolling(n).min()
    x["quiet"]=(x.rng.shift(1).rolling(6).mean()<
                .80*x.rng.shift(1).rolling(24).median())
    x["daily_vwap"]=(
       (x.close*x.volume).groupby(x.index.tz_convert("Asia/Kolkata").date).cumsum() /
       x.volume.groupby(x.index.tz_convert("Asia/Kolkata").date).cumsum().replace(0,np.nan))
    return x

def add_context(b,h4):
    known=h4[["ema20","ema50","ema200","close","valid"]].reindex(b.index,method="ffill")
    b=b.copy()
    b["bull4"]=(known.valid&(known.close>known.ema20)&(known.ema20>known.ema50)).fillna(False).to_numpy(bool)
    b["bear4"]=(known.valid&(known.close<known.ema20)&(known.ema20<known.ema50)).fillna(False).to_numpy(bool)
    return b

def signal_library(candles):
    all_sig={}
    h4=candles["4h"]
    for frame in ("5min","15min","1h","4h"):
        b=add_context(candles[frame],h4)
        bull=(b.close>b.open)&(b.body>.45)&(b["loc"]>.65)
        bear=(b.close<b.open)&(b.body>.45)&(b["loc"]<.35)
        ema_up=(b.ema20>b.ema50)&(b.close>b.ema20)
        ema_dn=(b.ema20<b.ema50)&(b.close<b.ema20)
        high24=b.high24;low24=b.low24
        lookback=55 if frame=="4h" else 24
        highx=b[f"high{lookback}"]; lowx=b[f"low{lookback}"]
        families={
            "donchian_break":(
                bull&(b.close>highx)&(b.vr>=1),
                bear&(b.close<lowx)&(b.vr>=1)),
            "failed_auction":(
                (b.low<lowx)&(b.close>lowx)&bull,
                (b.high>highx)&(b.close<highx)&bear),
            "ema20_pullback":(
                ema_up&(b.low<=b.ema20)&bull,
                ema_dn&(b.high>=b.ema20)&bear),
            "inside_bar_break":(
                (b.high.shift(1)<b.high.shift(2))&
                (b.low.shift(1)>b.low.shift(2))&bull&
                (b.close>b.high.shift(2)),
                (b.high.shift(1)<b.high.shift(2))&
                (b.low.shift(1)>b.low.shift(2))&bear&
                (b.close<b.low.shift(2))),
            "momentum_expansion":(
                bull&(b.rng>=1.3*b.atr)&(b.vr>=1.25),
                bear&(b.rng>=1.3*b.atr)&(b.vr>=1.25)),
            "squeeze_break":(
                b.quiet&bull&(b.close>b.high8)&(b.vr>=1.15),
                b.quiet&bear&(b.close<b.low8)&(b.vr>=1.15)),
            "rsi2_extreme_fade":(
                (b.rsi2<=3)&(b.close<b.ema20)&(b.close<b.open),
                (b.rsi2>=97)&(b.close>b.ema20)&(b.close>b.open)),
            "engulfing_reversal":(
                bull&(b.open<=b.close.shift(1))&
                (b.close>b.open.shift(1))&(b.close.shift(1)<b.open.shift(1)),
                bear&(b.open>=b.close.shift(1))&
                (b.close<b.open.shift(1))&(b.close.shift(1)>b.open.shift(1))),
            "volume_1p5x_cont":(
                bull&(b.vr>=1.5)&(b.close>b.close.shift(1)),
                bear&(b.vr>=1.5)&(b.close<b.close.shift(1))),
            "trend_efficiency":(
                bull&ema_up&b.bull4&(b.close>b.high8),
                bear&ema_dn&b.bear4&(b.close<b.low8)),
            "ema9_21_crossover":(
                (b.ema9>b.ema21)&(b.ema9.shift(1)<=b.ema21.shift(1))&
                (b.close>b.ema50),
                (b.ema9<b.ema21)&(b.ema9.shift(1)>=b.ema21.shift(1))&
                (b.close<b.ema50))
        }
        if frame=="5min":
            # Previous completed day high/low known from 00:00 UTC.
            days=b.index.floor("D")
            pri=b.groupby(days).agg(day_high=("high","max"),day_low=("low","min")).shift(1)
            ph=pd.Series(days.map(pri.day_high),index=b.index)
            pl=pd.Series(days.map(pri.day_low),index=b.index)
            families["prevday_break"]=(bull&(b.close>ph)&(b.close.shift(1)<=ph),
                bear&(b.close<pl)&(b.close.shift(1)>=pl))
            families["prevday_sweep"]=(bull&(b.low<pl)&(b.close>pl),
                bear&(b.high>ph)&(b.close<ph))
            # first 00:00-04:00 IST ORB; range computed only from prior
            # COMPLETED bars. Expands to later rows without future leakage.
            ist=b.index.tz_convert("Asia/Kolkata")
            day=np.array(ist.date)
            minute=np.array(ist.hour*60+ist.minute)
            first=b[(minute>0)&(minute<=240)].copy()
            first_days=np.array(first.index.tz_convert("Asia/Kolkata").date)
            opening=first.groupby(first_days).agg(hi=("high","max"),lo=("low","min"),
                                                    n=("close","size"))
            opening=opening[opening.n==48]
            hi=pd.Series(pd.Index(day).map(opening.hi),index=b.index)
            lo=pd.Series(pd.Index(day).map(opening.lo),index=b.index)
            after=(minute>240)
            families["ist_opening_range_break"]=(
                after&bull&(b.close>hi)&(b.close.shift(1)<=hi),
                after&bear&(b.close<lo)&(b.close.shift(1)>=lo))
            # Alternative fixed BTC point 100/200 risk/target mappings,
            # converted to native ETH via concurrent pre-entry BTC price.
            families["price_level_break_fixed100_200"]=families["prevday_break"]
        if frame=="15min":
            families["trend_retest"]=(
                b.bull4&(b.close.shift(1)>b.high24.shift(1))&
                (b.low<=b.high24.shift(1))&bull,
                b.bear4&(b.close.shift(1)<b.low24.shift(1))&
                (b.high>=b.low24.shift(1))&bear)
            families["vwap_reclaim"]=(
                bull&(b.low<b.daily_vwap)&(b.close>b.daily_vwap),
                bear&(b.high>b.daily_vwap)&(b.close<b.daily_vwap))
            families["supertrend_ema_proxy"]=(
                b.bull4&(b.low<=b.ema20)&(b.close>b.ema20)&bull,
                b.bear4&(b.high>=b.ema20)&(b.close<b.ema20)&bear)
        if frame=="1h":
            families["hourly_reversal_3c"]=(
                (b.close.shift(2)>b.open.shift(2))&
                (b.close.shift(1)<b.open.shift(1))&
                (b.close.shift(1)<b.open.shift(2))&
                (b.close>b.open),
                (b.close.shift(2)<b.open.shift(2))&
                (b.close.shift(1)>b.open.shift(1))&
                (b.close.shift(1)>b.open.shift(2))&
                (b.close<b.open))
        for name,(l,s) in families.items():
            long=l.fillna(False)&b.valid&b.atr.gt(0)
            short=s.fillna(False)&b.valid&b.atr.gt(0)
            all_sig[f"{frame}:{name}"]=(b,long,short)
    return all_sig

@njit(cache=True)
def replay(open_,high,low,close,month_codes,
           event_idx,side,stoppts,targetR,hold,stopmult,
           risk_pct,cap,slip,fee):
    # Full NAV ledger is computed sequentially, one position maximum.
    ledger=np.zeros((len(event_idx),8),np.float64)
    n=0;busy=-1;eq=1000.
    for i in range(len(event_idx)):
        k=int(event_idx[i])
        if k<=busy:continue
        if k>=len(close) or k<0:continue
        sd=int(side[i])
        rawdist=stoppts[i]*stopmult
        if not np.isfinite(rawdist) or rawdist<=0:continue
        px=open_[k]+sd*slip
        if px<=0:continue
        qty=min(eq*risk_pct/rawdist,eq*cap/px)
        if qty<=0:continue
        stop=px-sd*rawdist
        target=px+sd*rawdist*targetR
        finish=min(k+hold-1,len(close)-1)
        exit_px=close[finish]; j=finish
        reason=3
        for v in range(k,finish+1):
            # Stop-first on OHLC ambiguity, gap fills conservatively at open.
            hit=(low[v]<=stop if sd==1 else high[v]>=stop)
            if hit:
                exit_px=min(stop,open_[v]) if sd==1 else max(stop,open_[v])
                j=v;reason=0
                break
            hit_tp=(high[v]>=target if sd==1 else low[v]<=target)
            if hit_tp:
                exit_px=target; j=v;reason=1
                break
            if v==finish or (v+1<len(close) and month_codes[v+1]!=month_codes[v]):
                exit_px=close[v];j=v
                reason=2 if v+1<len(close) and month_codes[v+1]!=month_codes[v] else 3
                break
        true_exit=exit_px-sd*slip
        pnl=qty*(sd*(true_exit-px)-fee*(px+true_exit))
        before=eq
        eq+=pnl
        ledger[n,0]=k;ledger[n,1]=j;ledger[n,2]=sd
        ledger[n,3]=px;ledger[n,4]=rawdist;ledger[n,5]=qty
        ledger[n,6]=pnl;ledger[n,7]=eq
        n+=1;busy=j
        if eq<=0:break
    return ledger[:n]

def summarize(ledger,monthcodes,config):
    monthly=[]
    eq=INITIAL_EQUITY
    months=monthcodes[ledger[:,1].astype(np.int64)] if len(ledger) else np.array([],np.int32)
    for name,mc in zip(MONTHS,MONTH_CODES):
        r=ledger[months==mc]
        before=eq
        eq=float(r[-1,7]) if len(r) else eq
        monthly.append(dict(month=name,return_pct=(eq/before-1)*100 if before>0 else -100,
            trades=int(len(r)),wins=int((r[:,6]>0).sum()) if len(r) else 0,
            losses=int((r[:,6]<0).sum()) if len(r) else 0,
            equity_start=before,equity_end=eq))
    df=pd.DataFrame(monthly)
    endeq=eq
    c=np.r_[INITIAL_EQUITY,ledger[:,7]] if len(ledger) else np.array([INITIAL_EQUITY])
    dd=(c/np.maximum.accumulate(c)-1).min()*100
    row=dict(config)
    row.update(dict(trades=int(len(ledger)),wins=int((ledger[:,6]>0).sum()) if len(ledger) else 0,
        losses=int((ledger[:,6]<0).sum()) if len(ledger) else 0,
        positive2025=int((df.iloc[:12].return_pct>0).sum()),
        positive2026=int((df.iloc[12:].return_pct>0).sum()),
        months_ge10=int((df.return_pct>=10).sum()),
        all22positive=bool((df.return_pct>0).all()),
        all22_ge10=bool((df.return_pct>=10).all()),
        final_equity_usd=endeq,
        net_total_return_pct=(endeq/INITIAL_EQUITY-1)*100,
        max_trade_close_drawdown_pct=float(dd),
        worst_month_pct=float(df.return_pct.min())))
    return row,df

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    eth=load("ETHUSD");btc=load("BTCUSD")
    if not (eth.index.equals(btc.index)):
        raise RuntimeError("BTC and ETH true-minute timelines not aligned")
    o=eth.open.to_numpy(float);h=eth.high.to_numpy(float)
    l=eth.low.to_numpy(float);c=eth.close.to_numpy(float)
    bp=btc.open.to_numpy(float)
    ist=eth.index.tz_convert("Asia/Kolkata")
    monthcodes=np.array(ist.year*100+ist.month,dtype=np.int32)
    intervals={n:aggregate(eth,n) for n in ("5min","15min","1h","4h")}
    sigs=signal_library(intervals)
    models=[];monthly_by_model={};ledgers={}
    for label,(b,long,short) in sigs.items():
        idx0=np.r_[np.flatnonzero(long.to_numpy(bool)),np.flatnonzero(short.to_numpy(bool))]
        sides=np.r_[np.ones(int(long.sum()),np.int32),
                    -np.ones(int(short.sum()),np.int32)]
        idx_to_entry=eth.index.get_indexer(b.index[idx0])
        valid=(idx_to_entry>=0)&(idx_to_entry<len(c))
        idx0=idx0[valid];sides=sides[valid]
        k=idx_to_entry[valid]
        # If both sides trigger on same minute, deterministic tie-break long.
        order=np.lexsort((-sides,k))
        k=k[order];sides=sides[order];idx0=idx0[order]
        if len(k)>0:
            unique=np.r_[True,np.diff(k)!=0]
            k=k[unique];sides=sides[unique];idx0=idx0[unique]
        # Time-consistent native ETH 1m prices for the signal time.
        if len(k)==0:continue
        stopbase=b.atr.to_numpy(float)[idx0]
        fixed="fixed100_200" in label
        if fixed:
            # BTC 100-point stop => ETH entry price × 100 / BTC entry price.
            # Both prices are available at or before current 1m order open.
            stopbase=100.*o[k]/bp[k]
        tf=label.split(":")[0]
        hold={"5min":240,"15min":720,"1h":1440,"4h":4320}[tf]
        # Fixed 100/200 strategy retains its exact 2:1 BTC *percentage* R:R.
        grid=([(1.,2.)] if fixed else [(1.5,2.),(2.5,2.),(1.5,3.),(2.5,3.)])
        for mult,rr in grid:
            tr=replay(o,h,l,c,monthcodes,k,sides,stopbase,rr,hold,mult,
                      RISK,CAP,ETH_SLIP,FEE)
            key=label+f"__SL{mult:g}_RR{rr:g}"
            row,m=summarize(tr,monthcodes,{
                "model":key,"family":label,"stop_unit":"entry-time percent from BTC" if fixed else "native_ETH_ATR",
                "stop_mult":mult,"target_R":rr,"max_hold_m":hold,
                "risk_per_trade_pct":100*RISK,"cap_leverage":CAP
            })
            models.append(row);monthly_by_model[key]=m;ledgers[key]=tr
    res=pd.DataFrame(models)
    if res.empty:raise RuntimeError("No causal signal models")
    results=res.sort_values(["positive2025","net_total_return_pct","worst_month_pct"],
                            ascending=[False,False,False],kind="stable")
    results.to_csv(OUT/"all_crossfamily_models.csv",index=False)
    selected=[]
    for family,g in res.groupby("family",sort=True):
        # Pick only by 2025 monthly results, not 2026 or 22-month returns.
        g=g.sort_values(["positive2025"],ascending=False,kind="stable")
        # Additional tie-break from 2025 returns ONLY.
        g=g.copy()
        g["train_return_pct"]=[
          float((np.prod(1+monthly_by_model[m].iloc[:12].return_pct.to_numpy()/100)-1)*100)
          for m in g.model]
        g=g.sort_values(["positive2025","train_return_pct"],ascending=False,kind="stable")
        selected.append(g.iloc[0].to_dict())
    best=pd.DataFrame(selected).sort_values(
        ["positive2025","train_return_pct"],ascending=False,kind="stable")
    best.to_csv(OUT/"one_2025_selected_per_family.csv",index=False)
    selected_months=[]
    for row in best.to_dict("records"):
        m=monthly_by_model[row["model"]].copy()
        m.insert(0,"model",row["model"])
        selected_months.append(m)
    months=pd.concat(selected_months,ignore_index=True)
    months.to_csv(OUT/"selected_families_monthly_22.csv",index=False)
    maxpos=int(res.all22positive.sum());maxten=int(res.all22_ge10.sum())
    best_row=best.iloc[0].to_dict()
    model=best_row["model"]
    trade=ledgers[model]
    pd.DataFrame(trade,columns=["entry_index","exit_index","side","entry_eth_price",
                 "stop_eth_points","qty_eth","net_pnl_usd","account_equity"]).to_csv(
                     OUT/"best_training_ranked_trade_ledger.csv",index=False)
    quality={
      "test":"Independent native ETH cross-family proxy replay. NOT a byte-identical port of all historic BTC scripts.",
      "source":"Original Delta Exchange India ETHUSD and BTCUSD 1m 2025-01 through 2026-10",
      "native_eth_minute_candles":len(eth),
      "BTC_200pts_to_ETH_formula":"200 * ETH_entry_price / BTC_entry_price, applied per trade for fixed100_200 family",
      "fixedpoint_200_is_not_200_ETH":True,
      "family_count":len(best),"account_model_count":len(res),
      "models_all22_positive":maxpos,
      "models_all22_ge10":maxten,
      "best_2025_ranked_model":model,
      "fees_taker_per_side":.0005,"GST_on_exchange_fees":.18,
      "assumed_ETH_slippage_per_side_points":ETH_SLIP,
      "unmodelled":["funding","actual bid-ask spread","market impact","lot-size increments","margin and liquidation","order queue"],
      "calendar":"IST months, January 2025 IST initial 5.5h absent because history begins Jan1 UTC",
      "not_blind_OOS":"2026 data already researched in other studies",
      "NOV2026":"Excluded unfinished",
      "source_provenance":"All 22 UTC-month source manifests SHA256 checked for BOTH ETHUSD and BTCUSD",
      "candidate_selection":"2025 monthly-positive count and 2025 train cumulative return only"
    }
    (OUT/"quality.json").write_text(json.dumps(quality,indent=2,default=str)+"\n")
    lines=[
      "# ETHUSD — causal family audit across all completed Jan2025–Oct2026 months","",
      "**Representative research families only**. For exact source-code portability across",
      "the previous BTC research scripts, inspect the independent matrix job as well.",
      "All price data in this backtest are **native ETH prices**; only fixed 100/200",
      "BTC-point rules are translated at each trade to ETH percentage-equivalent",
      "using concurrent observed BTCUSD/ETHUSD data.","",
      f"- Tested representative entry families: **{len(best)}**",
      f"- Tested account models: **{len(res)}**",
      f"- Positive in ALL 22 months: **{maxpos}**",
      f"- At least +10% in ALL 22 months: **{maxten}**",
      "- Costs: 0.05% taker/side + 18% GST; assumed 0.25 ETH pts adverse slip/side.",
      "- Equity risk 0.5% per stop distance, max 3x notional; stop-first 1m fills.",
      "- Funding, actual spread, real fills, liquidation/margin and minimum contract sizes are not observed.",
      "",
      "## One 2025-only selected model per ETH strategy family","",
      best[["family","model","positive2025","positive2026","months_ge10",
            "trades","wins","losses","net_total_return_pct",
            "max_trade_close_drawdown_pct"]].to_markdown(index=False),
      "",
      "## Monthly NET account results for best 2025-ranked family","",
      monthly_by_model[model].to_markdown(index=False),
      "",
      "## Caveats","",
      "- These family representatives are not strict byte-for-byte executions of all old BTC scripts.",
      "- The independent original-code audit can fail on prior-stage output dependencies.",
      "- Positive backtest months do not guarantee future ETH profits.",
      "- January 2025 IST first 5.5 hours are missing from archive (starts Jan1 UTC).",
      "- UTC 2026-10-31 candles are present in BTC and ETH manifests; November 2026 excluded.",
      "- Using only 2025 to pick each family reduces but does not remove selection bias.",
      "- A nominal 0.25 ETH price-point slippage is NOT a live verified bid/ask spread.",
    ]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(lines)+"\n")
    print("ETH_NATIVE_CROSSFAMILY_DONE",json.dumps({
       "families":len(best),"models":len(res),"all22_positive":maxpos,
       "all22_10pct":maxten,"best":model,
       "best_months_positive":int((monthly_by_model[model].return_pct>0).sum())}))
    print(best[["family","model","positive2025","positive2026","trades",
                 "net_total_return_pct"]].to_string(index=False))
if __name__=="__main__":main()
