#!/usr/bin/env python3
"""Stage27: TWO genuinely distinct BTCUSD 1h mean-reversion and range strategies.

Evidence only. BTC 1-minute next-open orders, stop-first intrabar replay.
The 1H signal, H4 regime, RSI2, Bollinger/ATR, and historic range are all
computed from completed bars. No current/incomplete higher-timeframe candles.
No retrospective entry labels, hindsight regime switches or real trading.

Select candidate strategy within each family using only 2025 with +5bps/side
additional adverse slippage. Show Jan-Oct 2026 separately (already research-
exposed, NOT independent forward holdout). All costs are explicitly modeled.
Portfolio results are weighted monthly returns, NOT shared-margin trading.
"""
from pathlib import Path
import itertools
import json
import math
import numpy as np
import pandas as pd
from numba import njit
from research_every_candle_200 import read_archive, FEE, SLIPPAGE
from research_monthly_regime_stage14 import regime_data

OUT=Path("analysis/stage27_mean_reversion_range_20261121")
MONTHS=pd.period_range("2025-01","2026-10",freq="M").astype(str).tolist()
MIDX={s:i for i,s in enumerate(MONTHS)}
EPS=1e-9
TRAIN_MIN_TRADES=15
COMPAT_BASE=Path("/tmp/stage18-70-30/scenario_monthly_22.csv")
COMPAT_SWING=Path("/tmp/stage26/4h_donchian_2025selected_monthly.csv")

def generate_events(f):
    b=f[["open","high","low","close","volume"]].resample(
       "1h",label="right",closed="left").agg(
       {"open":"first","high":"max","low":"min","close":"last","volume":"sum"})
    counts=f.close.resample("1h",label="right",closed="left").count()
    b["valid"]=counts.rolling(50,min_periods=50).min().eq(60)
    prev=b.close.shift(1)
    tr=pd.concat([b.high-b.low,(b.high-prev).abs(),(b.low-prev).abs()],axis=1).max(axis=1)
    b["atr"]=tr.rolling(14,min_periods=14).mean()
    b["sma20"]=b.close.rolling(20,min_periods=20).mean()
    b["std20"]=b.close.rolling(20,min_periods=20).std()
    b["lo_band"]=b.sma20-2*b.std20
    b["hi_band"]=b.sma20+2*b.std20
    b["ema20"]=b.close.ewm(span=20,adjust=False).mean()
    diff=b.close.diff()
    gain=diff.clip(lower=0).ewm(alpha=.5,adjust=False,min_periods=2).mean()
    loss=(-diff.clip(upper=0)).ewm(alpha=.5,adjust=False,min_periods=2).mean()
    b["rsi2"]=100*gain/(gain+loss).replace(0,np.nan)
    b["low24"]=b.low.shift(1).rolling(24,min_periods=24).min()
    b["high24"]=b.high.shift(1).rolling(24,min_periods=24).max()
    b["low48"]=b.low.shift(1).rolling(48,min_periods=48).min()
    b["high48"]=b.high.shift(1).rolling(48,min_periods=48).max()
    loc=(b.close-b.low)/(b.high-b.low).replace(0,np.nan)
    body=b.close>b.open
    h4,_,_,_=regime_data(f)
    g=h4.reindex(b.index,method="ffill")
    b["h4_valid"]=g.valid.fillna(False).to_numpy(bool)
    b["h4_adx"]=g.adx.to_numpy(float)
    b["h4_eff"]=g.eff8.to_numpy(float)
    b["h4_atr_ratio"]=g.atr_ratio.to_numpy(float)
    valid=b.valid&b.h4_valid&b.atr.gt(0)&b.h4_adx.notna()&b.h4_eff.notna()
    # We never use future candles to recognize the reversal.
    # Prior close beyond Band, new bar reclaiming it, prior RSI2 extreme.
    mr_boll_L=(b.close.shift(1)<b.lo_band.shift(1))&(
       b.rsi2.shift(1)<=15)&(b.close>b.lo_band)&body&(loc>=.55)&(b.close<b.sma20)
    mr_boll_S=(b.close.shift(1)>b.hi_band.shift(1))&(
       b.rsi2.shift(1)>=85)&(b.close<b.hi_band)&(~body)&(loc<=.45)&(b.close>b.sma20)
    # Independent mean-reversion event: extreme distance from EMA20 after
    # completed bar then an explicit opposite-color reversal.
    mr_ema_L=(b.close.shift(1)<b.ema20.shift(1)-1.35*b.atr.shift(1))&(
       b.rsi2.shift(1)<=15)&body&(b.close>prev)&(loc>=.60)&(b.close<b.ema20)
    mr_ema_S=(b.close.shift(1)>b.ema20.shift(1)+1.35*b.atr.shift(1))&(
       b.rsi2.shift(1)>=85)&(~body)&(b.close<prev)&(loc<=.40)&(b.close>b.ema20)
    patterns=[]
    for n in (24,48):
        lower=b[f"low{n}"]
        upper=b[f"high{n}"]
        width=upper-lower
        width_ok=(width>=2.5*b.atr)&(width<=15*b.atr)
        # Range sweep and recapture after the lower boundary was known.
        # No "breakout" continuation direction is allowed here.
        sweepL=width_ok&(b.low<lower-.03*b.atr)&(
          b.close>lower+.1*b.atr)&body&(loc>=.65)&(b.close<lower+.55*width)
        sweepS=width_ok&(b.high>upper+.03*b.atr)&(
          b.close<upper-.1*b.atr)&(~body)&(loc<=.35)&(b.close>lower+.45*width)
        # Touch-only reversal without boundary penetration.
        touchL=width_ok&(b.low>=lower-.03*b.atr)&(
          b.low<=lower+.2*b.atr)&(b.close>lower+.35*b.atr)&body&(
          loc>=.70)&(b.close<lower+.55*width)
        touchS=width_ok&(b.high<=upper+.03*b.atr)&(
          b.high>=upper-.2*b.atr)&(b.close<upper-.35*b.atr)&(~body)&(
          loc<=.30)&(b.close>lower+.45*width)
        patterns.extend([
            ("range_sweep_"+str(n),sweepL,sweepS, (upper+lower)/2),
            ("range_touch_"+str(n),touchL,touchS, (upper+lower)/2),
        ])
    patterns=[("mr_bollinger_reentry",mr_boll_L,mr_boll_S,b.sma20),
              ("mr_ema_atr_reclaim",mr_ema_L,mr_ema_S,b.ema20)]+patterns
    kindex=f.index.get_indexer(b.index)
    source=f.time.to_numpy(np.int64)
    op=f.open.to_numpy(float)
    records=[]
    count_report={}
    for name,condL,condS,target in patterns:
        seen=0
        for side,mask in ((1,condL),(-1,condS)):
            locations=np.flatnonzero((valid&mask.fillna(False)).to_numpy(bool))
            for ii in locations:
                k=int(kindex[ii])
                if k<0 or k+720>=len(op) or source[k+719]-source[k]!=719*60:
                    continue
                atr=float(b.atr.iat[ii]);entry=float(op[k])
                structural=(min(float(b.low.iat[ii]),float(b.low.shift(1).iat[ii]))-
                  .15*atr) if side==1 else (
                   max(float(b.high.iat[ii]),float(b.high.shift(1).iat[ii]))+.15*atr)
                records.append((name,side,k,int(source[k]),entry,
                   atr,structural,float(target.iat[ii]),
                   float(b.h4_adx.iat[ii]),float(b.h4_eff.iat[ii])))
                seen+=1
        count_report[name]=seen
    e=pd.DataFrame(records,columns=["pattern","side","k","entry_unix",
      "entry_price","atr","structural_stop","mean_target","h4_adx","h4_eff"])
    if e.empty:raise AssertionError("No mean-reversion or range events")
    e["family"]=np.where(e.pattern.str.startswith("mr_"),"MEAN_REVERSION","RANGE_TRADING")
    e=e.sort_values(["k","pattern","side"],kind="stable").reset_index(drop=True)
    print("CAUSAL_SIGNAL_COUNTS",json.dumps(count_report))
    if (e.family=="MEAN_REVERSION").sum()==0 or (e.family=="RANGE_TRADING").sum()==0:
        raise AssertionError("At least one family has zero candidates")
    return e,count_report

@njit(cache=True)
def replay_one(O,H,L,C,k,side,risk,tprofit,hold,extra_bps):
    entry=O[k]
    stop=entry-side*risk
    for j in range(k,k+hold):
        stop_hit=L[j]<=stop if side==1 else H[j]>=stop
        take_hit=H[j]>=tprofit if side==1 else L[j]<=tprofit
        if stop_hit:
            exit_mid=min(O[j],stop) if side==1 else max(O[j],stop)
            reason=0
            break
        if take_hit:
            exit_mid=tprofit
            reason=1
            break
    else:
        j=k+hold-1
        exit_mid=C[j]
        reason=2
    entry_fill=entry+side*(SLIPPAGE+extra_bps*entry/10000.)
    exit_fill=exit_mid-side*(SLIPPAGE+extra_bps*exit_mid/10000.)
    net=side*(exit_fill-entry_fill)-FEE*(entry_fill+exit_fill)
    return j,net/risk,reason

def summarize(v):
    v=np.asarray(v,dtype=float)
    nav=np.cumprod(1+v/100)
    pk=np.maximum.accumulate(np.r_[1.,nav])[1:]
    return dict(returns_22_pct=float(100*(nav[-1]-1)),
       profits=int((v>EPS).sum()),losses=int((v<-EPS).sum()),
       flat=int((abs(v)<=EPS).sum()),
       return_2025_pct=float(100*(np.prod(1+v[:12]/100)-1)),
       return_2026_JanOct_pct=float(100*(np.prod(1+v[12:]/100)-1)),
       wins_2025=int((v[:12]>EPS).sum()),
       wins_2026=int((v[12:]>EPS).sum()),
       first_half_2025_pct=float(100*(np.prod(1+v[:6]/100)-1)),
       second_half_2025_pct=float(100*(np.prod(1+v[6:12]/100)-1)),
       max_monthend_dd_pct=float(100*np.max(1-nav/pk)),
       worst_month_pct=float(v.min()))

def test_configs(f,e):
    O=f.open.to_numpy(np.float64);H=f.high.to_numpy(np.float64)
    L=f.low.to_numpy(np.float64);C=f.close.to_numpy(np.float64)
    T=f.time.to_numpy(np.int64)
    records=[]; monthly=[]; trade_audit=[]
    regimes=[("tight",18.,.22),("quiet",25.,.35),("loose",30.,.45)]
    all_patterns=sorted(e.pattern.unique())
    total=0
    for pattern in all_patterns:
        base=e[e.pattern==pattern]
        family=str(base.family.iloc[0])
        for reg,adxmax,effmax in regimes:
            eligible=base[(base.h4_adx<=adxmax)&(base.h4_eff<=effmax)]
            for direction in ("both","long","short"):
                subset=eligible if direction=="both" else eligible[
                  eligible.side==(1 if direction=="long" else -1)]
                for stopmode,targetmode,hold in itertools.product(
                  ("struct","atr1p5"),("0.8R","1.2R","1.8R","to_mean"),(240,480,720)):
                    name=f"{pattern}__{reg}__{direction}__{stopmode}__{targetmode}__{hold}"
                    trades=[];last=-1
                    for z in subset.itertuples(index=False):
                        k=int(z.k)
                        if k<=last:continue
                        side=int(z.side);entry=float(O[k])
                        risk=side*(entry-float(z.structural_stop)) if stopmode=="struct" else 1.5*float(z.atr)
                        if not (125<=risk<=2000):continue
                        if targetmode=="to_mean":
                            target=float(z.mean_target)
                            reward=side*(target-entry)/risk
                            if not (.6<=reward<=5):continue
                        else:
                            reward=float(targetmode[:-1])
                            target=entry+side*reward*risk
                        # Identical future price path; costs alone differ.
                        exit_index,netR0,reason=replay_one(O,H,L,C,k,side,risk,target,hold,0.)
                        exit5,netR5,reason5=replay_one(O,H,L,C,k,side,risk,target,hold,5.)
                        if exit_index!=exit5 or reason!=reason5:
                            raise AssertionError("Cost test altered stop vs target path")
                        last=exit_index
                        mo=pd.Timestamp(int(T[exit_index]),unit="s",tz="UTC").tz_convert(
                            "Asia/Kolkata").strftime("%Y-%m")
                        if mo in MIDX:
                            trades.append((mo,int(T[k]),int(T[exit_index]),netR0,netR5,risk,entry,side,reason))
                    eq0=np.ones(22);eq5=np.ones(22);counts=np.zeros(22,dtype=int)
                    for mo,ent,ex,r0,r5,risk,entry,side,reason in trades:
                        ix=MIDX[mo]
                        frac=min(.005,5*risk/entry)
                        if min(1+frac*r0,1+frac*r5)<=0:raise AssertionError("Liquidated account")
                        eq0[ix]*=1+frac*r0
                        eq5[ix]*=1+frac*r5
                        counts[ix]+=1
                    v0=(eq0-1)*100;v5=(eq5-1)*100
                    s0=summarize(v0);s5=summarize(v5)
                    r=dict(family=family,model=name,pattern=pattern,regime=reg,
                      adx_max=adxmax,efficiency_max=effmax,
                      direction=direction,stop_mode=stopmode,
                      target_mode=targetmode,hold_minutes=hold,
                      trades=int(counts.sum()),trades_2025=int(counts[:12].sum()),
                      **{f"base_{k}":v for k,v in s0.items()},
                      **{f"stress5_{k}":v for k,v in s5.items()})
                    # Purely 2025 cost-stressed rank and eligibility.
                    r["2025_train_score"]=(s5["return_2025_pct"]-
                         .5*max(0,-s5["first_half_2025_pct"])-
                         .5*max(0,-s5["second_half_2025_pct"])+
                         .12*s5["wins_2025"])
                    records.append(r)
                    for i,mo in enumerate(MONTHS):
                        monthly.append(dict(family=family,model=name,month_ist=mo,
                         trades=int(counts[i]),base_pct=float(v0[i]),
                         stress5_pct=float(v5[i])))
                    total+=1
    if total==0:raise AssertionError("No backtested models")
    return pd.DataFrame(records),pd.DataFrame(monthly)

def choose(models,monthlies):
    selections=[]
    selection_months=[]
    for family,g in models.groupby("family"):
        eligible=g[(g.trades_2025>=TRAIN_MIN_TRADES)&
                   (g.stress5_return_2025_pct>0)&
                   (g.stress5_first_half_2025_pct>0)&
                   (g.stress5_second_half_2025_pct>0)]
        if eligible.empty:
            print("NO_STRESS_ROBUST_2025_TRAIN_WINNER",family)
            # Report exploratory candidate, but do NOT assert it's profitable.
            eligible=g[g.trades_2025>=TRAIN_MIN_TRADES]
        if eligible.empty:
            eligible=g.sort_values("trades_2025",ascending=False).head(1)
        rank=eligible.sort_values(["2025_train_score","trades_2025"],
                         ascending=[False,False],kind="stable")
        win=rank.iloc[0].to_dict()
        win["met_2025_cost_robust_gate"]=bool(
          win["stress5_return_2025_pct"]>0 and
          win["stress5_first_half_2025_pct"]>0 and
          win["stress5_second_half_2025_pct"]>0 and
          win["trades_2025"]>=TRAIN_MIN_TRADES)
        selections.append(win)
        m=monthlies[(monthlies.family==family)&(monthlies.model==win["model"])].copy()
        if len(m)!=22:raise AssertionError("Incomplete selected monthly series")
        selection_months.append(m)
        print("SELECTED_2025_ONLY",json.dumps(win))
    return pd.DataFrame(selections),pd.concat(selection_months,ignore_index=True)

def combine_portfolios(selectedmonths):
    # Fixed 90% Core + 10% 4H Donchian 20 historical baseline.
    core=pd.read_csv(COMPAT_BASE)
    core=core[core.scenario=="stage18_70_30_30d"]
    sw=pd.read_csv(COMPAT_SWING)
    baseline={}
    for bps in (0,5):
        c=core[core.extra_bps_side==bps].set_index("month_ist").reindex(MONTHS)
        s=sw[sw.extra_bps_per_side==bps].set_index("month_ist").reindex(MONTHS)
        if len(c)!=22 or c.core_month_pct.isna().any() or s.return_pct.isna().any():
            raise AssertionError("Baseline missing monthly costs scenario")
        baseline[bps]=.9*c.core_month_pct.to_numpy(float)+.1*s.return_pct.to_numpy(float)
    if not abs(summarize(baseline[0])["returns_22_pct"]-18.79)<.15:
        raise AssertionError("Frozen Core/4H baseline doesn't match previously published 90/10")
    family={}
    for fam in ("MEAN_REVERSION","RANGE_TRADING"):
        a=selectedmonths[selectedmonths.family==fam].set_index("month_ist").reindex(MONTHS)
        if len(a)!=22 or a.base_pct.isna().any():raise AssertionError("Missing selected family")
        family[(fam,0)]=a.base_pct.to_numpy(float)
        family[(fam,5)]=a.stress5_pct.to_numpy(float)
    allrows=[];monthly=[]
    for wm,wr in itertools.product((0,.05,.10,.15,.20),repeat=2):
        if wm+wr>.30:continue
        anchor=1-wm-wr
        for cost in (0,5):
            z=anchor*baseline[cost]+wm*family[("MEAN_REVERSION",cost)]+wr*family[("RANGE_TRADING",cost)]
            r=dict(core4h_baseline_weight=anchor,mean_reversion_weight=wm,
                   range_trading_weight=wr,extra_bps_side=cost,**summarize(z))
            allrows.append(r)
            for mo,x in zip(MONTHS,z):
                monthly.append(dict(month_ist=mo,core4h_baseline_weight=anchor,
                     mean_reversion_weight=wm,range_trading_weight=wr,
                     extra_bps_side=cost,blended_month_pct=float(x)))
    allrows=pd.DataFrame(allrows)
    allrows.to_csv(OUT/"portfolio_blend_comparison.csv",index=False)
    pd.DataFrame(monthly).to_csv(OUT/"portfolio_blend_monthly.csv",index=False)
    train=allrows[allrows.extra_bps_side==5].copy()
    # Portfolio rank is strictly training-year, and minimum 70% anchor.
    train["2025_only_rank"]=train.return_2025_pct-.5*np.maximum(
        0,-train.first_half_2025_pct)-.5*np.maximum(0,-train.second_half_2025_pct)
    best=train.sort_values("2025_only_rank",ascending=False).iloc[0]
    print("TRAIN2025_PORTFOLIO_CHOICE",json.dumps(best.to_dict()))
    print("BASELINE_CORE_4H_90_10",json.dumps(dict(
       base=summarize(baseline[0]),stress5=summarize(baseline[5]))))
    return best.to_dict()

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    f,starts,ends,quality=read_archive()
    print("BTC_SOURCE_QUALITY",json.dumps(dict(
        rows=len(f),missing_minutes=quality["missing_minutes"],
        partitions=quality["months"],first=quality["first_utc"],last=quality["last_utc"])))
    events,counts=generate_events(f)
    events.to_csv(OUT/"causal_signal_events.csv.gz",index=False,compression="gzip")
    models,monthly=test_configs(f,events)
    selected,selection_months=choose(models,monthly)
    models.to_csv(OUT/"every_meanreversion_range_configuration.csv",index=False)
    monthly.to_csv(OUT/"every_strategy_monthly.csv.gz",index=False,compression="gzip")
    selected.to_csv(OUT/"two_strategy_selected_results.csv",index=False)
    selection_months.to_csv(OUT/"two_strategy_selected_monthly.csv",index=False)
    portfolio=combine_portfolios(selection_months)
    summary=dict(variants=len(models),variants_by_family=models.groupby("family").size().to_dict(),
       raw_event_counts=counts,selected=selected.to_dict("records"),portfolio_2025_chosen=portfolio,
       sample_months=[MONTHS[0],MONTHS[-1]],source_minutes=len(f),
       cost="0.05pct taker each leg plus GST 18pct on fees and 5 BTC points slip per leg; stress adds adverse 5bps per leg",
       important_caveats=[
         "Signals use completed H1/H4 bars; next 1m open; stop wins same-minute stop/target touch",
         "Two strategy families are distinct: mean-reversion to EMA/Bollinger mean, range-bound support/resistance fades",
         "Returns include modeled taker+GST+5-point-per-leg slip; cost5 adds 5bps each leg",
         "H4 ADX and efficiency are known at timestamp, not projected",
         "2025 used for model/portfolio selection; 2026 was previously studied, not true OOS",
         "Within family one trade at a time, separate ledgers across families",
         "High-dimensional research has multiple-testing/selection bias",
         "No funding, measured spread, actual order fill, min contract size, liquidation or shared-margin portfolio",
         "Portfolio blending is monthly synthetic, not simultaneous strategy execution",
         "Do not deploy live; no strategy profitability implied until forward testing",
       ])
    (OUT/"summary.json").write_text(json.dumps(summary,indent=2)+"\n")
    print("STAGE27_BTC_MEAN_REVERSION_RANGE_SUCCESS",json.dumps(summary))
if __name__=="__main__":
    main()
