#!/usr/bin/env python3
"""BTCUSD causal 1H regime census + 4 predeclared 1M-executed strategy baselines."""
import json
import hashlib
from pathlib import Path
import numpy as np
import pandas as pd

SOURCE = Path("data/delta_india/BTCUSD/1m")
OUT = Path("analysis/btc_regime_attribution_20261121")
OUT.mkdir(parents=True, exist_ok=True)
FEE = 0.0005*1.18
SLIP = 5.
INITIAL = 10000.
RISK = .005
LEV_CAP = 3.
LAST_MONTH = "2026-10"
SPECS = {"trend_pullback":(1.6,3.,24),
         "donchian_breakout":(1.8,3.,36),
         "bollinger_reversion":(1.2,1.5,12),
         "failed_break_fade":(1.3,2.,12)}
STATES = ["shock","breakout_up","breakout_down","trend_up","trend_down",
          "compression","range","mixed"]

def load():
    manifest=json.loads((SOURCE/"manifest.json").read_text())
    blocks=[]
    for p in manifest["partitions"]:
        f=SOURCE/p["file"]
        if hashlib.sha256(f.read_bytes()).hexdigest()!=p["sha256_gzip"]:
            raise RuntimeError("Hash mismatch: "+str(f))
        df=pd.read_csv(f,compression="gzip")
        cols=["time","open","high","low","close","volume"]
        if not set(cols).issubset(df.columns):
            raise RuntimeError("Missing columns: "+str(f))
        t=df.time.to_numpy(np.int64)
        lo=int(pd.Timestamp(p["utc_start"]).timestamp())
        hi=int(pd.Timestamp(p["utc_end_exclusive"]).timestamp())
        if len(t)!=p["expected_minutes"] or len(t)!=p["observed_candles"]:
            raise RuntimeError("Count mismatch: "+str(f))
        if t[0]!=lo or t[-1]!=hi-60 or (np.diff(t)!=60).any():
            raise RuntimeError("Timestamp gap: "+str(f))
        if not np.isfinite(df[cols[1:]].to_numpy(float)).all():
            raise RuntimeError("Nonfinite candles: "+str(f))
        blocks.append(df[cols])
    x=pd.concat(blocks,ignore_index=True)
    x.time=pd.to_datetime(x.time,unit="s",utc=True)
    x=x.set_index("time")
    if x.index.has_duplicates or not x.index.is_monotonic_increasing:
        raise RuntimeError("Duplicate or unsorted minutes")
    if not x.index.to_series().diff().iloc[1:].eq(pd.Timedelta(minutes=1)).all():
        raise RuntimeError("Gap between months")
    if ((x.high<x[["open","close","low"]].max(axis=1)) |
        (x.low>x[["open","close","high"]].min(axis=1))).any():
        raise RuntimeError("Inconsistent OHLC")
    return x,manifest

def features(one):
    h=one.resample("1h").agg(open=("open","first"),high=("high","max"),
         low=("low","min"),close=("close","last"),volume=("volume","sum"))
    if not one.close.resample("1h").count().eq(60).all():
        raise RuntimeError("Incomplete hourly bar")
    prev=h.close.shift()
    tr=pd.concat([h.high-h.low,(h.high-prev).abs(),(h.low-prev).abs()],axis=1).max(axis=1)
    h["atr"]=tr.ewm(alpha=1/14,adjust=False,min_periods=14).mean()
    dh=h.high.diff()
    dl=-h.low.diff()
    plus=dh.where((dh>dl)&(dh>0),0.).ewm(alpha=1/14,adjust=False,min_periods=14).mean()
    minus=dl.where((dl>dh)&(dl>0),0.).ewm(alpha=1/14,adjust=False,min_periods=14).mean()
    h["plus_di"]=100*plus/h.atr
    h["minus_di"]=100*minus/h.atr
    dx=100*(h.plus_di-h.minus_di).abs()/(h.plus_di+h.minus_di).replace(0,np.nan)
    h["adx"]=dx.ewm(alpha=1/14,adjust=False,min_periods=14).mean()
    h["ema20"]=h.close.ewm(span=20,adjust=False,min_periods=20).mean()
    h["ema50"]=h.close.ewm(span=50,adjust=False,min_periods=50).mean()
    h["hi24"]=h.high.rolling(24,min_periods=24).max().shift()
    h["lo24"]=h.low.rolling(24,min_periods=24).min().shift()
    h["er12"]=(h.close-h.close.shift(12)).abs()/h.close.diff().abs().rolling(12).sum().replace(0,np.nan)
    h["atr_ratio"]=h.atr/h.atr.rolling(72,min_periods=72).median().shift()
    h["bb_mid"]=h.close.rolling(20,min_periods=20).mean()
    stdev=h.close.rolling(20,min_periods=20).std(ddof=0)
    h["bb_hi"]=h.bb_mid+2*stdev
    h["bb_lo"]=h.bb_mid-2*stdev
    req=["atr","adx","plus_di","minus_di","ema20","ema50","hi24","lo24",
         "er12","atr_ratio","bb_mid","bb_hi","bb_lo"]
    h["valid"]=np.isfinite(h[req].to_numpy(float)).all(axis=1)
    shock=(tr>2.2*h.atr)|(h.atr_ratio>=1.8)
    brup=(h.close>h.hi24)&((h.high-h.low)>.9*h.atr)&(h.atr_ratio>1)
    brdn=(h.close<h.lo24)&((h.high-h.low)>.9*h.atr)&(h.atr_ratio>1)
    tup=(h.adx>=23)&(h.plus_di>h.minus_di)&(h.ema20>h.ema50)&(h.close>h.ema20)&(h.er12>=.25)
    tdn=(h.adx>=23)&(h.plus_di<h.minus_di)&(h.ema20<h.ema50)&(h.close<h.ema20)&(h.er12>=.25)
    comp=(h.atr_ratio<=.75)&(h.er12<=.22)&(h.adx<=24)
    rng=(h.adx<=19)&(h.er12<=.35)
    h["regime"]="warmup"
    v=h.valid
    h.loc[v,"regime"]=np.select([z[v].fillna(False).to_numpy() for z in
       [shock,brup,brdn,tup,tdn,comp,rng]],STATES[:-1],default="mixed")
    sweep_hi=(h.high>h.hi24)&(h.close<h.hi24)
    sweep_lo=(h.low<h.lo24)&(h.close>h.lo24)
    body=(h.close-h.open).abs()
    span=(h.high-h.low).replace(0,np.nan)
    wick=np.maximum(h.high-h[["open","close"]].max(axis=1),
                    h[["open","close"]].min(axis=1)-h.low)
    h["event_false_break"]=v&(sweep_hi|sweep_lo)
    h["event_trend_pullback"]=v&(
      ((h.ema20>h.ema50)&(h.low<=h.ema20)&(h.close>h.ema20))|
      ((h.ema20<h.ema50)&(h.high>=h.ema20)&(h.close<h.ema20)))
    h["event_ema_reversal"]=v&(
      ((h.ema20>h.ema50)&(h.ema20.shift()<=h.ema50.shift()))|
      ((h.ema20<h.ema50)&(h.ema20.shift()>=h.ema50.shift())))
    h["event_wick_rejection"]=v&((wick/span>=.6)&(body/span<=.3))
    return h

def prepare_signals(h):
    up=(h.ema20>h.ema50)&(h.low<=h.ema20)&(h.close>h.ema20)
    dn=(h.ema20<h.ema50)&(h.high>=h.ema20)&(h.close<h.ema20)
    bu=h.close>h.hi24
    bd=h.close<h.lo24
    ru=(h.low<=h.bb_lo)&(h.close>h.bb_lo)&(h.close<h.bb_mid)
    rd=(h.high>=h.bb_hi)&(h.close<h.bb_hi)&(h.close>h.bb_mid)
    fu=(h.low<h.lo24)&(h.close>h.lo24)
    fd=(h.high>h.hi24)&(h.close<h.hi24)
    pairs={"trend_pullback":(up,dn),"donchian_breakout":(bu,bd),
           "bollinger_reversion":(ru,rd),"failed_break_fade":(fu,fd)}
    return {name:np.where(h.valid,np.where(a&~b,1,np.where(b&~a,-1,0)),0)
            for name,(a,b) in pairs.items()}

def next_month_utc(t):
    return (t.tz_convert("Asia/Kolkata")+pd.offsets.MonthBegin(1)).normalize().tz_convert("UTC")

def run(one,h,sides):
    idx=one.index
    opens=one.open.to_numpy(float)
    highs=one.high.to_numpy(float)
    lows=one.low.to_numpy(float)
    closes=one.close.to_numpy(float)
    rows=[]
    for name,sig in sides.items():
        smult,targ_r,hold=SPECS[name]
        equity=INITIAL
        occupied=pd.Timestamp("1900-01-01",tz="UTC")
        for j in np.flatnonzero(sig):
            t=h.index[j]+pd.Timedelta(hours=1)
            at=int(idx.searchsorted(t))
            if at==len(idx) or idx[at]!=t or t<=occupied:
                continue
            month=t.tz_convert("Asia/Kolkata").strftime("%Y-%m")
            if month>LAST_MONTH:
                continue
            atr=float(h.atr.iat[j])
            if not np.isfinite(atr) or atr<=0 or equity<=0:
                continue
            limit=min(at+60*hold,len(idx),int(idx.searchsorted(next_month_utc(t))))
            if limit<=at: continue
            side=int(sig[j])
            entry=float(opens[at])
            risk_pts=smult*atr
            qty=min(equity*RISK/risk_pts,equity*LEV_CAP/entry)
            stop=entry-side*risk_pts
            target=entry+side*risk_pts*targ_r
            hh,ll=highs[at:limit],lows[at:limit]
            bad=np.flatnonzero(ll<=stop if side>0 else hh>=stop)
            good=np.flatnonzero(hh>=target if side>0 else ll<=target)
            b=int(bad[0]) if len(bad) else len(hh)
            g=int(good[0]) if len(good) else len(hh)
            if b<=g and b<len(hh):
                k=at+b
                raw_exit=min(stop,opens[k]) if side>0 else max(stop,opens[k])
                reason="stop"
            elif g<len(hh):
                k=at+g
                raw_exit=target
                reason="target"
            else:
                k=limit-1
                raw_exit=closes[k]
                reason="timeout_or_IST_month_end"
            ep=entry+side*SLIP
            xp=raw_exit-side*SLIP
            feepts=FEE*(ep+xp)
            netpts=side*(xp-ep)-feepts
            pnl=qty*netpts
            pct=100*pnl/equity
            equity+=pnl
            occupied=idx[k]
            rows.append(dict(strategy=name,regime=h.regime.iat[j],
                entry_utc=str(t),exit_utc=str(idx[k]),month_ist=month,side=side,
                entry_price=ep,exit_price=xp,risk_points=risk_pts,qty=qty,
                net_points_per_btc=netpts,net_R=netpts/risk_pts,pnl_usd=pnl,
                return_pct=pct,fee_gst_usd=qty*feepts,slippage_usd=qty*2*SLIP,
                exit_reason=reason,equity_usd=equity))
    return pd.DataFrame(rows)

def summarize(one,h,tr,manifest):
    census=h[h.valid].copy()
    census["month_ist"]=(census.index+pd.Timedelta(hours=1)).tz_convert("Asia/Kolkata").strftime("%Y-%m")
    census=census[census.month_ist<=LAST_MONTH]
    count=census.regime.value_counts().reindex(STATES,fill_value=0)
    share=pd.DataFrame({"regime":STATES,"hours":count.values,
                        "pct_hours":(100*count.values/len(census)).round(3)})
    share.to_csv(OUT/"regime_share.csv",index=False)
    mx=pd.crosstab(census.month_ist,census.regime).reindex(columns=STATES,fill_value=0)
    mp=mx.div(mx.sum(axis=1),axis=0)*100
    mp.round(3).to_csv(OUT/"monthly_regime_pct.csv")
    ev=pd.DataFrame([dict(event=col.removeprefix("event_"),hours=int(census[col].sum()),
                          pct_hours=round(100*census[col].mean(),3))
                     for col in census if col.startswith("event_")])
    ev.to_csv(OUT/"event_flags.csv",index=False)
    months=[str(x) for x in pd.period_range("2025-01",LAST_MONTH,freq="M")]
    month_rows=[]
    cond_rows=[]
    summaries=[]
    for name in SPECS:
        a=tr[tr.strategy==name]
        eq=INITIAL
        rets=[]
        for month in months:
            g=a[a.month_ist==month]
            mr=(np.prod(1+g.return_pct.to_numpy(float)/100)-1)*100
            rets.append(float(mr))
            eq*=1+mr/100
            month_rows.append(dict(strategy=name,month_ist=month,trades=len(g),
                wins=int((g.pnl_usd>0).sum()),losses=int((g.pnl_usd<0).sum()),
                net_return_pct=round(float(mr),6),pnl_usd=round(float(g.pnl_usd.sum()),2),
                fee_gst_usd=round(float(g.fee_gst_usd.sum()),2),
                slippage_usd=round(float(g.slippage_usd.sum()),2)))
        for state in STATES:
            g=a[a.regime==state]
            gains=g.pnl_usd[g.pnl_usd>0].sum()
            losses=-g.pnl_usd[g.pnl_usd<0].sum()
            cond_rows.append(dict(strategy=name,regime=state,trades=len(g),
                win_pct=round(100*(g.pnl_usd>0).mean(),2) if len(g) else None,
                mean_net_R=round(float(g.net_R.mean()),3) if len(g) else None,
                net_pnl_usd=round(float(g.pnl_usd.sum()),2),
                profit_factor=round(float(gains/losses),3) if losses>0 else None))
        equity=np.r_[INITIAL,a.equity_usd.to_numpy(float)]
        dd=(1-equity/np.maximum.accumulate(equity))*100
        gains=a.pnl_usd[a.pnl_usd>0].sum()
        losses=-a.pnl_usd[a.pnl_usd<0].sum()
        summaries.append(dict(strategy=name,trades=len(a),
            net_account_pct=round(100*(eq/INITIAL-1),3),
            profitable_months=int(np.sum(np.array(rets)>0)),
            losing_months=int(np.sum(np.array(rets)<0)),
            idle_months=int(np.sum(np.array(rets)==0)),
            max_trade_close_drawdown_pct=round(float(dd.max()),2),
            profit_factor=round(float(gains/losses),3) if losses>0 else None))
    month=pd.DataFrame(month_rows)
    conditional=pd.DataFrame(cond_rows)
    summary=pd.DataFrame(summaries)
    month.to_csv(OUT/"monthly_by_strategy.csv",index=False)
    conditional.to_csv(OUT/"performance_by_entry_regime.csv",index=False)
    summary.to_csv(OUT/"strategy_summary.csv",index=False)
    q=dict(exchange="Delta Exchange India",symbol="BTCUSD",
        minute_partitions=len(manifest["partitions"]),minute_bars=len(one),
        first_utc=str(one.index[0]),last_utc=str(one.index[-1]),
        verified_missing_minutes=0,hourly_bars=len(h),classified_complete_month_hours=len(census),
        fee_each_side_incl_gst=FEE,slippage_each_side_btc_price_points=SLIP,
        account_initial_usd=INITIAL,stop_risk_fraction=RISK,leverage_cap=LEV_CAP,
        complete_IST_months=len(months),partial_Nov_2026_excluded=True,
        is_2026_blind_holdout=False)
    (OUT/"quality.json").write_text(json.dumps(q,indent=2)+"\n")
    rpt=[
      "# BTCUSD 1H regime frequencies and conditional fixed-strategy backtest","",
      "## Method",
      "Native 1M SHA256 and continuous timestamp audit passed. 1H state is determined only after signal-hour CLOSE. Entry at next native 1M OPEN. Every hour has one primary state; event flags may overlap.",
      "Frozen baselines: EMA20/50 1H pullback; prior-24H closing Donchian breakout; Bollinger 20/2 reversion; failed prior-24H break. Fixed stop multiples/targets/timeouts documented in NOVELTY_CHECK.md. No parameter optimization.",
      "One open trade per strategy, 1M stop-first OHLC replay, adverse stop gap fill, IST month-end flatten.",
      "Hypothetical separate $10,000 account per strategy; risk 0.5% per trade capped at 3x notional; 0.05% taker each side + GST 18% and five price points adverse slippage each side.",
      "",
      "## Data quality",json.dumps(q,indent=2),"",
      "## Share of available classified hours",share.to_markdown(index=False),"",
      "## Additional overlapping events",ev.to_markdown(index=False),"",
      "## Separate baseline account results",summary.to_markdown(index=False),"",
      "## Entry regime conditional performance",conditional.to_markdown(index=False),"",
      "## Every complete IST month, net account % per baseline",
      month.pivot(index="month_ist",columns="strategy",values="net_return_pct").round(3).to_markdown(),"",
      "## Important limits",
      "- Historical spreads/book depth, realized funding payments, financing, market impact and liquidation are not simulated. Tradeability not established.",
      "- 2026 history was examined by earlier research and is not a pristine independent out-of-sample set.",
      "- Price-action 'shock' is not proof of forced liquidations. 1H states depend on predeclared thresholds.",
      "- Some regime-by-strategy cells have very small trade samples. Do not cherry-pick winner cells without independent testing.",
      "- January 2025 begins at 00:00 UTC, so initial Jan 1 IST hours are not in the archive.",
      "- November 2026 is incomplete and not counted as a full profitable or losing month.",
    ]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(rpt)+"\n")
    print(share.to_string(index=False))
    print(summary.to_string(index=False))
    print("COMPLETED",json.dumps(q))

def main():
    one,manifest=load()
    h=features(one)
    tr=run(one,h,prepare_signals(h))
    if tr.empty:
        raise RuntimeError("No trades: abort instead of generating misleading zero report")
    tr.to_csv(OUT/"trade_ledger.csv",index=False)
    summarize(one,h,tr,manifest)

if __name__=="__main__":
    main()
