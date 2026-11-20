#!/usr/bin/env python3
"""Independent BTC 1H breakout/pullback edge, real 1m stop + ATR trailing.

Unlike previous Stage18/20 tweaks, these are *new, fully re-executed* 1H
signals with independent positions. Only if an independent strategy is
profitable under BTC2025 conservative costs do we assess a complementary
sleeve. Stage18/20 unchanged original 5R monthly results loaded from a
separate, completed GitHub artifact for comparison. No code change to them.
No real trades. No fabricated exchange-level fills.

Entry signal from a completed 1H candle, filled at the first subsequent 1m
OPEN. Exit checks touch/gap on every actual 1m OHLC; one position at a time;
ATR initial stop 2x, monotonic trail updated from COMPLETED H1 candle only;
reversal and 14-day time cap. GST/fee/slip via Stage17 run_one.
"""
from pathlib import Path
import json
import os
import numpy as np
import pandas as pd
import research_swing_donchian_stage17 as sw
from research_every_candle_200 import read_archive, FEE, SLIPPAGE

OUT=Path("analysis/stage18_stage20_independent_hourly_edge_20261120")
MONTHS=pd.period_range("2025-01","2026-10",freq="M").astype(str).tolist()
# New signal family, channel bars, trend gate, volume gate, ATR trailing x.
CONFIGS=[
 ("break24_trend",24,"break","4h","any",2.0),
 ("break24_trend_trail3",24,"break","4h","any",3.0),
 ("break24_trend_trail4",24,"break","4h","any",4.0),
 ("break48_trend",48,"break","4h","any",2.0),
 ("break48_trend_trail3",48,"break","4h","any",3.0),
 ("break48_trend_trail4",48,"break","4h","any",4.0),
 ("break72_trend_trail3",72,"break","4h","any",3.0),
 ("break24_volume1p2",24,"break","4h","vol1p2",3.0),
 ("break48_volume1p2",48,"break","4h","vol1p2",3.0),
 ("break48_no4h_trail3",48,"break","1h","any",3.0),
 ("hour_pullback_20",24,"pullback","4h","any",2.0),
 ("hour_pullback_20_trail3",24,"pullback","4h","any",3.0),
 ("hour_pullback_vol1p2",24,"pullback","4h","vol1p2",3.0),
 ("hour_pullback_no4h",24,"pullback","1h","any",3.0),
 ("break24_no4h",24,"break","1h","any",3.0),
 ("break72_no4h",72,"break","1h","any",3.0),
]

def hourly_features(f):
    hour=f[["open","high","low","close","volume"]].resample(
        "1h",closed="left",label="right").agg({
        "open":"first","high":"max","low":"min","close":"last","volume":"sum"})
    c=f.close.resample("1h",closed="left",label="right").count()
    hour["complete"]=(c==60)
    hour["history_ok"]=c.rolling(160,min_periods=160).min().eq(60)
    prev=hour.close.shift(1)
    tr=pd.concat([(hour.high-hour.low),(hour.high-prev).abs(),
                   (hour.low-prev).abs()],axis=1).max(axis=1)
    hour["atr"]=tr.rolling(14,min_periods=14).mean()
    hour["ema20"]=hour.close.ewm(span=20,adjust=False).mean()
    hour["ema50"]=hour.close.ewm(span=50,adjust=False).mean()
    hour["ema200"]=hour.close.ewm(span=200,adjust=False).mean()
    hour["volr"]=hour.volume/hour.volume.shift(1).rolling(
       20,min_periods=20).mean().replace(0,np.nan)
    # 4H trend is complete only if that 4H bar has all 240 minutes.
    h4=f[["open","high","low","close"]].resample(
        "4h",closed="left",label="right").agg({
        "open":"first","high":"max","low":"min","close":"last"})
    n4=f.close.resample("4h",closed="left",label="right").count()
    h4["complete"]=(n4==240)
    h4["valid"]=n4.rolling(50,min_periods=50).min().eq(240)
    h4["ema20"]=h4.close.ewm(span=20,adjust=False).mean()
    h4["ema50"]=h4.close.ewm(span=50,adjust=False).mean()
    h4["trendup"]=h4.valid&(h4.close>h4.ema20)&(
       h4.ema20>h4.ema50)&(h4.ema20.diff(3)>0)
    h4["trenddown"]=h4.valid&(h4.close<h4.ema20)&(
       h4.ema20<h4.ema50)&(h4.ema20.diff(3)<0)
    known=h4.reindex(hour.index,method="ffill")
    hour["4h_up"]=known.trendup.fillna(False)
    hour["4h_down"]=known.trenddown.fillna(False)
    return hour

def configure_signals(f,hour,seg_start,cfg):
    _,look,kind,gate,vfilter,trail=cfg
    complete=hour.history_ok & hour.complete & hour.atr.gt(0)
    trend_up=(hour.close>hour.ema50)&(hour.ema20>hour.ema50)
    trend_dn=(hour.close<hour.ema50)&(hour.ema20<hour.ema50)
    if gate=="4h":
        up=trend_up&hour["4h_up"]
        dn=trend_dn&hour["4h_down"]
    else:
        up=trend_up
        dn=trend_dn
    if kind=="break":
        priorhigh=hour.high.shift(1).rolling(look,min_periods=look).max()
        priorlow=hour.low.shift(1).rolling(look,min_periods=look).min()
        # first crossing rather than re-enter on every hour outside channel
        long=(hour.close>priorhigh)&(hour.close.shift(1)<=priorhigh.shift(1))
        short=(hour.close<priorlow)&(hour.close.shift(1)>=priorlow.shift(1))
    else:
        # After preceding FULL 1h candle pulls back into EMA20, a subsequent
        # FULL candle resumes trend through previous high/low.
        pull_long=hour.low.shift(1)<=hour.ema20.shift(1)
        pull_short=hour.high.shift(1)>=hour.ema20.shift(1)
        long=pull_long&(hour.close>hour.high.shift(1))&(hour.close>hour.open)
        short=pull_short&(hour.close<hour.low.shift(1))&(hour.close<hour.open)
    if vfilter=="vol1p2":
        vol=hour.volr>=1.2
        long &= vol;short &= vol
    long &= complete&up;short &= complete&dn
    idx=f.index.get_indexer(hour.index)
    n=len(f)
    signal=np.zeros(n,np.int8)
    updates=np.zeros(n,np.bool_)
    atr=np.full(n,np.nan,np.float64)
    ref=np.full(n,np.nan,np.float64)
    longarr=long.fillna(False).to_numpy(bool)
    shortarr=short.fillna(False).to_numpy(bool)
    val=complete.fillna(False).to_numpy(bool)
    for j,k in enumerate(idx):
        if k<0 or not val[j]:continue
        # All data before hour boundary must be present; price at k is next 1m
        # OPEN, and the previous candle close is known.
        updates[k]=True
        a=float(hour.atr.iat[j])
        a0=float(f.open.iat[k])
        # Cap implicit fractional notional at 3x. Original Stage17 risk=2ATR;
        # RISK_FRACTION=0.5% account: notional leverage = .005*entry/(2ATR).
        if .005*a0/(2*a)>3.0:continue
        atr[k]=a
        ref[k]=float(hour.close.iat[j])
        if longarr[j]:signal[k]=1
        elif shortarr[j]:signal[k]=-1
    return signal,updates,atr,ref

def report_metrics(arr):
    x=np.asarray(arr,float)
    if np.isnan(x).any() or (x<=-100).any():raise ValueError("Invalid months")
    nav=np.cumprod(1+x/100)
    peak=np.maximum.accumulate(np.r_[1.,nav])[1:]
    return dict(net_pct=float(100*(nav[-1]-1)),
       positive_months=int((x>1e-9).sum()),
       losing_months=int((x<-1e-9).sum()),
       flat_months=int((abs(x)<=1e-9).sum()),
       max_monthend_dd_pct=float(100*np.max(1-nav/peak)),
       worst_month_pct=float(x.min()))

def load_original():
    directory=Path(os.environ.get("STAGE18_BASELINE_DIR","/tmp/stage18-base"))
    matches=list(directory.rglob("all_months.csv"))
    if len(matches)!=1:raise FileNotFoundError(f"Missing source Stage18 base artifact {directory}: {matches}")
    z=pd.read_csv(matches[0])
    out={}
    for family in ("Stage18","Stage20"):
        for candidate in ("original_5R","5R_broader_eff25_no_gate"):
            for slip in (0,2,5):
                t=z[(z.family==family)&(z.variant==candidate)&(z.stress_bps_side==slip)]
                if t.month.duplicated().any():raise AssertionError("Duplicate monthly baseline")
                v=t.set_index("month").reindex(MONTHS).net_month_pct.to_numpy(float)
                if np.isnan(v).any():raise AssertionError("Baseline missing months")
                out[(family,candidate,slip)]=v
    # Independent known source reconciliation: original 5R Stage18 +12.0163%
    # and Stage20 +9.5921% after original cost model.
    for fam,expected in (("Stage18",12.01632563),("Stage20",9.59205167)):
        observed=report_metrics(out[(fam,"original_5R",0)])["net_pct"]
        if abs(observed-expected)>.02:raise AssertionError(f"Original baseline mismatch {fam}: {observed}")
    return out

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    f,seg_start,_,quality=read_archive()
    month_codes,labels=sw.build_months(f)
    if labels[:22]!=MONTHS:raise AssertionError("Monthly IST calendar shifted")
    h=hourly_features(f)
    baseline=load_original()
    op=f.open.to_numpy(np.float64);hi=f.high.to_numpy(np.float64)
    lo=f.low.to_numpy(np.float64);cl=f.close.to_numpy(np.float64)
    tm=f.time.to_numpy(np.int64)
    results=[];monthly=[];trades_all=[];selection={}
    for cfg in CONFIGS:
        name,look,kind,gate,vfilter,trail=cfg
        signal,updates,atr,ref=configure_signals(f,h,seg_start,cfg)
        trades,marks,entries,exposure,dd=sw.run_one(
            op,hi,lo,cl,tm,month_codes,seg_start,
            signal,updates,atr,ref,trail,len(labels))
        if np.isnan(marks).any():raise AssertionError("Not all monthly marks available")
        net=100*(marks[1:]/marks[:-1]-1)
        # The first monthly return is from 100 initial equity, not a
        # difference to another month.
        monthly_pct=np.r_[100*(marks[0]/100-1),net][:22]
        if len(monthly_pct)!=22:raise AssertionError("Not 22 months")
        win_R=np.array([float(t[5]) for t in trades])
        win=float(win_R[win_R>0].sum()) if len(win_R) else 0.
        loss=float(-win_R[win_R<0].sum()) if len(win_R) else 0.
        pf=win/loss if loss>0 else None
        train=report_metrics(monthly_pct[:12]);check=report_metrics(monthly_pct[12:]);total=report_metrics(monthly_pct)
        train_trades=sum(t[0]<int(pd.Timestamp("2026-01-01",tz="Asia/Kolkata").tz_convert("UTC").timestamp()) for t in trades)
        info=dict(variant=name,signal_family=kind,channel_lookback=look,trend_gate=gate,
            volume_filter=vfilter,atr_trail_multiplier=trail,
            trades=int(len(trades)),trades_train_2025=int(train_trades),
            core_pf_netR=pf,trade_to_trade_dd_pct=float(dd)*100,
            net_2025=train["net_pct"],positive_2025=train["positive_months"],
            net_2026JanOct=check["net_pct"],positive_2026JanOct=check["positive_months"],
            net_22=total["net_pct"],positive_22=total["positive_months"],
            negative_22=total["losing_months"],flat_22=total["flat_months"],
            max_monthend_dd_2025=train["max_monthend_dd_pct"],
            max_monthend_dd_22=total["max_monthend_dd_pct"])
        results.append(info)
        monthly.extend(dict(variant=name,month=m,net_month_pct=float(y),
            market_exposure=int(exposure[i])) for i,(m,y) in enumerate(zip(MONTHS,monthly_pct)))
        trades_all.extend(dict(variant=name,entry_unix=int(t[0]),exit_unix=int(t[1]),
            side=int(t[2]),risk_pts=float(t[3]),net_pts=float(t[4]),
            net_R=float(t[5]),exit_reason_code=int(t[6])) for t in trades)
    df=pd.DataFrame(results);mn=pd.DataFrame(monthly)
    # Never use 2026 in scoring; require valid after-cost expectancy and
    # adequate independent 2025 trades. No candidate? Don't force an overlay.
    eligible=df[(df.trades_train_2025>=25)&(df.net_2025>0)&
                (df.core_pf_netR>1)].copy()
    eligible["train_score"]=eligible.net_2025 + .5*eligible.positive_2025 - .9*eligible.max_monthend_dd_2025
    eligible=eligible.sort_values(["train_score","trades_train_2025"],ascending=False,kind="stable")
    selected=None if eligible.empty else str(eligible.iloc[0].variant)
    selection["btc_2025_only"]=selected
    print("BTC2025_INDEPENDENT_SIGNAL_RANK",eligible.to_json(orient="records"))
    print("FROZEN_INDEPENDENT_SELECTION",selected)
    for record in results:print("STANDALONE_SIGNAL_RESULT",json.dumps(record))
    # Prevent return fabrication: blended risk-neutral exposure only, never
    # add full Stage18 and independent 0.5%-risk returns as if same capital.
    combos=[]
    if selected is not None:
        x=mn[mn.variant==selected].set_index("month").reindex(MONTHS).net_month_pct.to_numpy()
        for fam in ("Stage18","Stage20"):
            for baseline_variant in ("original_5R","5R_broader_eff25_no_gate"):
                for stress in (0,2,5):
                    b=baseline[(fam,baseline_variant,stress)]
                    ref=report_metrics(b)
                    for w in (.25,.50):
                        combined=(1-w)*b+w*x
                        outcome=report_metrics(combined)
                        row=dict(family=fam,baseline_variant=baseline_variant,
                             new_signal=selected,new_signal_capital_weight=w,
                             baseline_extra_slip_bps_side=stress,
                             baseline_net_22=ref["net_pct"],
                             combined_net_22=outcome["net_pct"],
                             baseline_positive_months=ref["positive_months"],
                             combined_positive_months=outcome["positive_months"],
                             combined_losing_months=outcome["losing_months"],
                             combined_monthend_dd_pct=outcome["max_monthend_dd_pct"],
                             baseline_2025=report_metrics(b[:12])["net_pct"],
                             combined_2025=report_metrics(combined[:12])["net_pct"],
                             baseline_2026=report_metrics(b[12:])["net_pct"],
                             combined_2026=report_metrics(combined[12:])["net_pct"])
                        combos.append(row)
                        print("INDEPENDENT_SLEEVE_RISK_NEUTRAL",json.dumps(row))
    pd.DataFrame(combos).to_csv(OUT/"risk_neutral_portfolio_checks.csv",index=False)
    df.to_csv(OUT/"all_standalone_1h_signal_results.csv",index=False)
    mn.to_csv(OUT/"all_monthly_independent_signal_results.csv",index=False)
    pd.DataFrame(trades_all).to_csv(OUT/"native_btc_1m_trade_ledger.csv.gz",
                                    compression="gzip",index=False)
    (OUT/"btc2025_selection.json").write_text(json.dumps(selection,indent=2))
    (OUT/"limitations.json").write_text(json.dumps(dict(
        source_quality=quality,variants=CONFIGS,selected=selected,
        native_engine="Stage17 1m stop-gap-first ATR risk and 1H-close stop trailing, opposite breakout, 14-day time cap",
        modeled_fills="Original 0.05% taker per side plus 18% GST, adverse 5 BTC price points each side",
        model_risk="Risk 0.5% per trade using fractional lot sizing, signal filtered when theoretical notional >3x NAV",
        portfolio="risk-neutral monthly blended capital 25/50% independent signal; not integrated simultaneous execution",
        limits=[
         "Both 2025 & 2026 have been researched before, not pristine unseen holdout",
         "Native one-minute OHLC cannot reconstruct intraminute fill order, bid/ask or slippage",
         "Funding, minimum contract granularity, shared margin/liquidation and rebalancing fees absent",
         "Stage18/20 monthly source is the previous independent GitHub artifact, not re-executed three-sleeve live account",
         "Known historical source data gaps, earliest Jan2025 IST and last day Oct2026",
         "Native ETH 1m validation not performed",
         "One standalone signal cannot be assumed to improve combined returns; preserve every failed and flat month",
         "A historically promising signal is not forward validated, nor a live-trading recommendation"
        ],no_live_orders=True),indent=2,default=str))
    print("INDEPENDENT_HOURLY_NEW_EDGE_REPLAY_COMPLETE",json.dumps(selection))
if __name__=="__main__":main()
