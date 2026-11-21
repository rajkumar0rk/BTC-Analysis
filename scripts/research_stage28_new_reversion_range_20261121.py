#!/usr/bin/env python3
"""Stage 28: NEW independent BTCUSD 1H/4H mean-reversion and range entries.

Pre-entry information ONLY, complete 1H/4H candles; next actual BTC 1m open
fills and conservative 1m stop-first tie. Same Delta taker+GST+5pts/side
fees as existing BTC-Analysis; extra 5bps per leg for stressed research.

2025-only selection criteria; Jan-Oct 2026 is previously researched and is
NOT an untouched OOS test. Strategy classes remain separate, no live action.
"""
from pathlib import Path
import itertools
import json
import numpy as np
import pandas as pd
from research_every_candle_200 import read_archive
from research_monthly_regime_stage14 import regime_data
from research_stage27_meanreversion_range_20261121 import generate_events as stage27_events, replay_one as replay

OUT=Path("analysis/stage28_new_reversion_range_20261121")
MONTHS=pd.period_range("2025-01","2026-10",freq="M").astype(str).tolist()
MONTH_INDEX={m:i for i,m in enumerate(MONTHS)}
BASE_CORE=Path("/tmp/stage18-70-30/scenario_monthly_22.csv")
BASE_SWING=Path("/tmp/stage26/4h_donchian_2025selected_monthly.csv")
EPS=1e-8

def tf(f, freq, unit, history):
    b=f[["open","high","low","close","volume"]].resample(
        freq,label="right",closed="left").agg({
        "open":"first","high":"max","low":"min",
        "close":"last","volume":"sum"})
    counts=f.close.resample(freq,label="right",closed="left").count()
    b["complete"]=counts.rolling(history,min_periods=history).min().eq(unit)
    prev=b.close.shift(1)
    tr=pd.concat([b.high-b.low,(b.high-prev).abs(),
                    (b.low-prev).abs()],axis=1).max(axis=1)
    b["atr"]=tr.rolling(14,min_periods=14).mean()
    b["ema20"]=b.close.ewm(span=20,adjust=False).mean()
    b["ema50"]=b.close.ewm(span=50,adjust=False).mean()
    b["sma20"]=b.close.rolling(20,min_periods=20).mean()
    b["std20"]=b.close.rolling(20,min_periods=20).std()
    b["bblo"]=b.sma20-2*b.std20
    b["bbhi"]=b.sma20+2*b.std20
    delta=b.close.diff()
    gain=delta.clip(lower=0).ewm(alpha=.5,adjust=False,min_periods=2).mean()
    loss=(-delta.clip(upper=0)).ewm(alpha=.5,adjust=False,min_periods=2).mean()
    b["rsi2"]=100*gain/(gain+loss).replace(0,np.nan)
    for n in (12,20,24,48):
        b[f"l{n}"]=b.low.shift(1).rolling(n,min_periods=n).min()
        b[f"h{n}"]=b.high.shift(1).rolling(n,min_periods=n).max()
    span=(b.high-b.low).replace(0,np.nan)
    b["loc"]=(b.close-b.low)/span
    return b

def prepare_new_events(f):
    h1=tf(f,"1h",60,60)
    h4=tf(f,"4h",240,65)
    h4reg,_,_,_=regime_data(f)
    h4["adx"]=h4reg.adx
    h4["eff"]=h4reg.eff8
    # Known previous completed 4H bar at 1H signal time.
    hg=h4.reindex(h1.index,method="ffill")
    h1["h4_adx"]=hg.adx.to_numpy(float)
    h1["h4_eff"]=hg.eff.to_numpy(float)
    h1["h4_bull"]=(
       hg.complete&(hg.close>hg.ema50)&(hg.ema50>hg.ema50.shift(3))).fillna(False).to_numpy(bool)
    h1["h4_bear"]=(
       hg.complete&(hg.close<hg.ema50)&(hg.ema50<hg.ema50.shift(3))).fillna(False).to_numpy(bool)
    # Avoid mixed-index forward-shift mistakes: compare the known H4 50 EMA
    # to the EMA value three COMPLETED H4 periods earlier on the H4 index.
    prior_slope=h4.ema50.shift(3)
    prior_trend=prior_slope.reindex(h1.index,method="ffill")
    h1["h4_bull"]=(hg.complete&(hg.close>hg.ema50)&
                   (hg.ema50>prior_trend)).fillna(False).to_numpy(bool)
    h1["h4_bear"]=(hg.complete&(hg.close<hg.ema50)&
                   (hg.ema50<prior_trend)).fillna(False).to_numpy(bool)
    h1["h4_adx"]=hg.adx.to_numpy(float)
    h1["h4_eff"]=hg.eff.to_numpy(float)
    candidates=[]
    pclose=h1.close.shift(1)
    lowband=h1.bblo
    hiband=h1.bbhi
    bull=h1.close>h1.open
    bear=h1.close<h1.open
    # 1H MEAN REVERSION: confirmed RSI2 oversold recovery, distinct from
    # breakout pullback by requiring extreme prior close vs EMA20/Bollinger.
    cond_MR1L=(h1.rsi2.shift(1)<=8)&(
         pclose<h1.ema20.shift(1)-.6*h1.atr.shift(1))&(
         h1.close>pclose)&bull&(h1["loc"]>=.6)&(h1.close<h1.ema20)
    cond_MR1S=(h1.rsi2.shift(1)>=92)&(
         pclose>h1.ema20.shift(1)+.6*h1.atr.shift(1))&(
         h1.close<pclose)&bear&(h1["loc"]<=.4)&(h1.close>h1.ema20)
    # 1H MEAN REVERSION: exceptionally stretched Bollinger close, half-way
    # retrace of previous candle, still on stretched side of rolling mean.
    cond_MR2L=(pclose<h1.bblo.shift(1))&(h1.rsi2.shift(1)<=12)&(
         h1.close>h1.open)&(h1.close>pclose)&(
         h1.close>h1.low.shift(1)+.45*(h1.high.shift(1)-h1.low.shift(1)))&(
         h1.close<h1.sma20)
    cond_MR2S=(pclose>h1.bbhi.shift(1))&(h1.rsi2.shift(1)>=88)&(
         h1.close<h1.open)&(h1.close<pclose)&(
         h1.close<h1.high.shift(1)-.45*(h1.high.shift(1)-h1.low.shift(1)))&(
         h1.close>h1.sma20)
    # 1H MEAN REVERSION: large consecutive downside deviation followed
    # by a recovery bar. Does not require a Bollinger cross.
    cond_MR3L=(pclose<h1.ema20.shift(1)-1.9*h1.atr.shift(1))&(
         h1.close>h1.open)&(h1["loc"]>=.65)&(h1.close<h1.ema20)
    cond_MR3S=(pclose>h1.ema20.shift(1)+1.9*h1.atr.shift(1))&(
         h1.close<h1.open)&(h1["loc"]<=.35)&(h1.close>h1.ema20)
    onehour=[
      ("mr_rsi2_recovery_h1",cond_MR1L,cond_MR1S,h1.ema20),
      ("mr_bollinger_reclaim_h1",cond_MR2L,cond_MR2S,h1.sma20),
      ("mr_ema19atr_shock_h1",cond_MR3L,cond_MR3S,h1.ema20)]
    def add_from_bars(b,patterns,tfname,adx,eff):
        fidx=f.index.get_indexer(b.index)
        ts=f.time.to_numpy(np.int64)
        O=f.open.to_numpy(float)
        for name,flagL,flagS,means in patterns:
            for side,flag in ((1,flagL),(-1,flagS)):
                ids=np.flatnonzero(
                    (b.complete&flag.fillna(False)&b.atr.gt(0)).to_numpy(bool))
                for j in ids:
                    k=int(fidx[j])
                    if k<0 or k+2880>=len(O) or ts[k+2879]-ts[k]!=2879*60:
                        continue
                    atr=float(b.atr.iat[j])
                    entry=float(O[k])
                    low=min(float(b.low.iat[j]),float(b.low.shift(1).iat[j]))
                    high=max(float(b.high.iat[j]),float(b.high.shift(1).iat[j]))
                    stop=low-.15*atr if side==1 else high+.15*atr
                    m=float(means.iat[j])
                    if not np.isfinite(m) or not np.isfinite(adx.iat[j]) or not np.isfinite(eff.iat[j]):
                        continue
                    # Freeze directional trend state from fully closed H4
                    if tfname=="1h":
                        trend=(bool(b.h4_bull.iat[j]) if side==1 else
                               bool(b.h4_bear.iat[j]))
                    else:
                        trend=(bool(b.close.iat[j]>b.ema50.iat[j] and
                                    b.ema50.iat[j]>b.ema50.shift(3).iat[j]) if side==1 else
                               bool(b.close.iat[j]<b.ema50.iat[j] and
                                    b.ema50.iat[j]<b.ema50.shift(3).iat[j]))
                    family="MR" if name.startswith("mr_") else "RANGE"
                    candidates.append(dict(family=family,pattern=name,side=side,
                        k=k,entry_unix=int(ts[k]),entry_mid=entry,atr=atr,
                        structural_stop=stop,mean_target=m,
                        h4_adx=float(adx.iat[j]),h4_eff=float(eff.iat[j]),
                        h4_trend_agrees=trend,timeframe=tfname))
    add_from_bars(h1,onehour,"1h",h1.h4_adx,h1.h4_eff)
    twohour=[]
    # 4H (multi-day) mean reversion: prior bar RSI2 oversold followed
    # by a substantial reversal candle. 4H exposure lowers trading frictions.
    cond4L=(h4.rsi2.shift(1)<=10)&(h4.close>h4.open)&(
         h4.close>h4.close.shift(1))&(h4["loc"]>=.65)&(
         h4.close<h4.ema20)
    cond4S=(h4.rsi2.shift(1)>=90)&(h4.close<h4.open)&(
         h4.close<h4.close.shift(1))&(h4["loc"]<=.35)&(
         h4.close>h4.ema20)
    twohour.append(("mr_4h_rsi2_rebound",cond4L,cond4S,h4.ema20))
    cond4bbL=(h4.close.shift(1)<h4.bblo.shift(1))&(
         h4.close>h4.bblo)&(h4.close<h4.sma20)&(
         h4.close>h4.open)&(h4["loc"]>=.55)
    cond4bbS=(h4.close.shift(1)>h4.bbhi.shift(1))&(
         h4.close<h4.bbhi)&(h4.close>h4.sma20)&(
         h4.close<h4.open)&(h4["loc"]<=.45)
    twohour.append(("mr_4h_bollinger_reentry",cond4bbL,cond4bbS,h4.sma20))
    add_from_bars(h4,twohour,"4h",h4.adx,h4.eff)
    for channel in (12,24):
        lower=h4[f"l{channel}"]
        upper=h4[f"h{channel}"]
        width=upper-lower
        width_ok=(width>2.5*h4.atr)&(width<15*h4.atr)
        l_sweep=width_ok&(h4.low<lower-.05*h4.atr)&(
          h4.close>lower+.15*h4.atr)&(h4.close<h4.open+.55*(h4.high-h4.low))&(
          h4.close>h4.open)&(h4["loc"]>=.60)
        s_sweep=width_ok&(h4.high>upper+.05*h4.atr)&(
          h4.close<upper-.15*h4.atr)&(h4.close<h4.open)&(h4["loc"]<=.40)
        l_touch=width_ok&(h4.low>=lower-.05*h4.atr)&(
          h4.low<=lower+.3*h4.atr)&(h4.close>lower+.4*h4.atr)&(
          h4.close>h4.open)&(h4["loc"]>=.65)
        s_touch=width_ok&(h4.high<=upper+.05*h4.atr)&(
          h4.high>=upper-.3*h4.atr)&(h4.close<upper-.4*h4.atr)&(
          h4.close<h4.open)&(h4["loc"]<=.35)
        mid=(lower+upper)/2
        add_from_bars(h4,[
           (f"range_4h_sweep_{channel}",l_sweep,s_sweep,mid),
           (f"range_4h_touch_{channel}",l_touch,s_touch,mid)],
           "4h",h4.adx,h4.eff)
    d=pd.DataFrame(candidates)
    if d.empty:raise AssertionError("No new MR/RANGE source events")
    original,counts=stage27_events(f)
    # Augment previous Stage27 event family: float h4 price trend on complete bar
    orig=original.rename(columns={
       "entry_price":"entry_mid","h4_eff":"h4_eff",
       "structural_stop":"structural_stop","mean_target":"mean_target"})
    orig["family"]=orig.family.map({
       "MEAN_REVERSION":"MR","RANGE_TRADING":"RANGE"})
    orig["h4_trend_agrees"]=False
    orig["timeframe"]="1h"
    cols=["family","pattern","side","k","entry_unix","entry_mid",
       "atr","structural_stop","mean_target","h4_adx","h4_eff",
       "h4_trend_agrees","timeframe"]
    all_events=pd.concat([d[cols],orig[cols]],ignore_index=True)
    # Keep 1H original MR and range candidates as a benchmark, no hidden substitution.
    all_events=all_events.sort_values(["k","pattern","side"],kind="stable")
    count=all_events.groupby(["family","pattern"]).size().to_dict()
    print("STAGE28_EVENT_COUNTS",json.dumps({str(k):int(v) for k,v in count.items()}))
    return all_events

def stats(v):
    v=np.asarray(v,float)
    n=np.cumprod(1+v/100)
    pk=np.maximum.accumulate(np.r_[1.,n])[1:]
    n25=np.cumprod(1+v[:12]/100)
    pk25=np.maximum.accumulate(np.r_[1.,n25])[1:]
    return dict(net22=float(100*(n[-1]-1)),
       yr25=float(100*(np.prod(1+v[:12]/100)-1)),
       yr26=float(100*(np.prod(1+v[12:]/100)-1)),
       win22=int((v>EPS).sum()),loss22=int((v<-EPS).sum()),
       flat22=int((abs(v)<=EPS).sum()),
       win2025=int((v[:12]>EPS).sum()),
       win2026=int((v[12:]>EPS).sum()),
       first6_2025=float(100*(np.prod(1+v[:6]/100)-1)),
       second6_2025=float(100*(np.prod(1+v[6:12]/100)-1)),
       worst_month=float(v.min()),
       dd22=float(100*np.max(1-n/pk)),
       dd2025=float(100*np.max(1-n25/pk25)))

def replay_models(f,e):
    o=f.open.to_numpy(float);h=f.high.to_numpy(float)
    l=f.low.to_numpy(float);c=f.close.to_numpy(float)
    t=f.time.to_numpy(np.int64)
    configs=[];months=[]
    for pat,events in e.groupby("pattern"):
        fam=str(events.family.iloc[0])
        # Filters avoid unbounded bars but permit directional trend support
        # when the strategy is countertrend on H1 inside the H4 uptrend.
        for regime,adxmax,effmax in (("tight",18,.25),("quiet",25,.35),
                                        ("loose",32,.5),("trend",45,.7)):
            gate=events[(events.h4_adx<=adxmax)&(events.h4_eff<=effmax)]
            for side_mode in ("both","long","short"):
                sub=gate if side_mode=="both" else gate[
                  gate.side==(1 if side_mode=="long" else -1)]
                for trend_filter in ("any","aligned"):
                    if trend_filter=="aligned":
                        sub2=sub[sub.h4_trend_agrees]
                    else:sub2=sub
                    # Original Stage27 entries do not carry additional H4 trend
                    # state; don't use those original signals with aligned=True.
                    if sub2.empty:continue
                    for stopmode,exitmode,hold in itertools.product(
                       ("struct","atr2","atr3"),
                       ("1.2R","2R","3R","to_mean"),
                       (480,960,1920)):
                        name=(f"{pat}__{regime}__{side_mode}__{trend_filter}__"
                          f"{stopmode}__{exitmode}__{hold}")
                        active=-1;tr=[]
                        for z in sub2.itertuples(index=False):
                            k=int(z.k)
                            if k<=active or k+hold>=len(o) or t[k+hold-1]-t[k]!=(hold-1)*60:
                                continue
                            side=int(z.side)
                            risk=(side*(o[k]-float(z.structural_stop)) if stopmode=="struct"
                                  else float(z.atr)*(2 if stopmode=="atr2" else 3))
                            if not np.isfinite(risk) or risk<200 or risk>3500:continue
                            target=(o[k]+side*risk*float(exitmode[:-1])
                                  if exitmode.endswith("R") else float(z.mean_target))
                            reward=side*(target-o[k])/risk
                            if not (.6<=reward<=5.0):continue
                            j,r0,_=replay(o,h,l,c,k,side,risk,target,hold,0.)
                            k2,r5,_=replay(o,h,l,c,k,side,risk,target,hold,5.)
                            if j!=k2:raise AssertionError("Slippage changed price path")
                            active=j
                            mo=pd.Timestamp(int(t[j]),unit="s",tz="UTC").tz_convert(
                                "Asia/Kolkata").strftime("%Y-%m")
                            if mo in MONTH_INDEX:
                                tr.append((MONTH_INDEX[mo],float(r0),float(r5),
                                           float(risk),float(o[k])))
                        m0=np.ones(22);m5=np.ones(22);entry_counts=np.zeros(22,int)
                        for ix,r0,r5,risk,entry in tr:
                            used=min(.005,5*risk/entry)
                            if min(1+used*r0,1+used*r5)<=0:raise AssertionError("Account liquidation")
                            m0[ix]*=(1+used*r0);m5[ix]*=(1+used*r5)
                            entry_counts[ix]+=1
                        v0=100*(m0-1);v5=100*(m5-1)
                        a=stats(v0);b=stats(v5)
                        row=dict(family=fam,model=name,pattern=pat,regime=regime,
                          side=side_mode,trend_filter=trend_filter,
                          stop=stopmode,exit=exitmode,hold_minutes=hold,
                          ntrades=int(entry_counts.sum()),train_trades=int(entry_counts[:12].sum()),
                          **{f"base_{k}":v for k,v in a.items()},
                          **{f"stress5_{k}":v for k,v in b.items()})
                        row["selection_score2025"]=(
                            b["yr25"]-.8*b["dd2025"]+.06*b["win2025"])
                        row["2025_train_valid"]=(row["train_trades"]>=20 and
                            b["first6_2025"]>0 and b["second6_2025"]>0 and b["yr25"]>0)
                        configs.append(row)
                        for ix,mo in enumerate(MONTHS):
                            months.append((fam,name,mo,float(v0[ix]),float(v5[ix]),
                                           int(entry_counts[ix])))
    if not configs:raise AssertionError("No variants simulated")
    df=pd.DataFrame(configs)
    monthly=pd.DataFrame(months,columns=["family","model","month_ist",
                           "base_return_pct","stress5_return_pct","trades"])
    return df,monthly

def select_and_report(models,months):
    selected=[]
    seen_hindsight=[]
    for fam,g in models.groupby("family"):
        eligible=g[g["2025_train_valid"]]
        if eligible.empty:
            print("NO_COST_ROBUST_2025_MODEL",fam)
            pool=g[g.train_trades>=20]
            if pool.empty:pool=g
            chosen=pool.sort_values(["selection_score2025","train_trades"],
                                     ascending=False).iloc[0].to_dict()
            chosen["validated_train_2025"]=False
        else:
            chosen=eligible.sort_values(["selection_score2025","train_trades"],
                                        ascending=False).iloc[0].to_dict()
            chosen["validated_train_2025"]=True
        selected.append(chosen)
        hindsight=g[(g.train_trades>=20)&(g.stress5_yr25>0)&(g.stress5_yr26>0)]
        seen_hindsight.append(dict(family=fam,models_cost_profitable_both_years=int(len(hindsight)),
                                    models_2025_eligible=int(len(eligible))))
        print("STAGE28_2025_ONLY_SELECTION",json.dumps(chosen,default=str))
        print("STAGE28_RESEARCH_BOTH_YEARS_COUNTS",json.dumps(seen_hindsight[-1]))
    sel=pd.DataFrame(selected)
    sel.to_csv(OUT/"selected_2025_vs_researched_2026.csv",index=False)
    bestmonths=months.merge(sel[["family","model"]],on=["family","model"],how="inner")
    if len(bestmonths)!=44:raise AssertionError("Selected monthly completeness")
    bestmonths.to_csv(OUT/"selected_2025_monthly.csv",index=False)
    return sel,bestmonths,seen_hindsight

def combine_portfolio(bestmonthly):
    # Reference previously verified synthetic 90% Core and 10% Stage26 H4
    # Donchian. NOTE: this is never a shared exchange-account execution.
    base=pd.read_csv(BASE_CORE)
    sw=pd.read_csv(BASE_SWING)
    reference={}
    for bps in (0,5):
        c=base[(base.scenario=="stage18_70_30_30d")&
               (base.extra_bps_side==bps)].set_index("month_ist").reindex(MONTHS)
        d=sw[sw.extra_bps_per_side==bps].set_index("month_ist").reindex(MONTHS)
        if c.core_month_pct.isna().any() or d.return_pct.isna().any():
            raise AssertionError("Missing Stage18 Core / Stage26 4H baseline")
        reference[bps]=.9*c.core_month_pct.to_numpy(float)+.1*d.return_pct.to_numpy(float)
    if abs(stats(reference[0])["net22"]-18.78534218)>.02:
        raise AssertionError("Stage27 90/10 baseline parity")
    individual={}
    for fam in ("MR","RANGE"):
        m=bestmonthly[bestmonthly.family==fam].set_index("month_ist").reindex(MONTHS)
        if m.base_return_pct.isna().any():raise AssertionError("Missing selected series")
        individual[(fam,0)]=m.base_return_pct.to_numpy(float)
        individual[(fam,5)]=m.stress5_return_pct.to_numpy(float)
    portfolios=[];pmonths=[]
    for m,r in itertools.product((0,.05,.1,.15,.2),repeat=2):
        if m+r>.3:continue
        w=1-m-r
        for bps in (0,5):
            z=w*reference[bps]+m*individual[("MR",bps)]+r*individual[("RANGE",bps)]
            p=dict(core_4h_reference_weight=w,mr_weight=m,
              range_weight=r,extra_bps_side=bps,**stats(z))
            p["train_score"]=p["yr25"]-.5*max(0,-p["first6_2025"])-.5*max(
                   0,-p["second6_2025"])
            portfolios.append(p)
            pmonths.extend(dict(**{k:p[k] for k in (
              "core_4h_reference_weight","mr_weight","range_weight",
              "extra_bps_side")},month_ist=mo,return_pct=float(x))
              for mo,x in zip(MONTHS,z))
    out=pd.DataFrame(portfolios)
    out.to_csv(OUT/"fixed_portfolio_comparisons.csv",index=False)
    pd.DataFrame(pmonths).to_csv(OUT/"fixed_portfolio_monthly.csv",index=False)
    ranked=out[out.extra_bps_side==5].sort_values("train_score",ascending=False)
    chosen=ranked.iloc[0].to_dict()
    print("STAGE28_PORTFOLIO_SELECTED_2025",json.dumps(chosen))
    print("STAGE28_PORTFOLIO_REFERENCE",json.dumps(
        dict(base=stats(reference[0]),stress5=stats(reference[5]))))
    return chosen

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    f,_,_,quality=read_archive()
    print("STAGE28_SOURCE_1M",json.dumps(dict(
        candles=len(f),missing=quality["missing_minutes"],
        first=quality["first_utc"],last=quality["last_utc"])))
    events=prepare_new_events(f)
    events.to_csv(OUT/"causal_events_all.csv.gz",index=False,compression="gzip")
    models,monthly=replay_models(f,events)
    models.to_csv(OUT/"every_model_summary.csv",index=False)
    monthly.to_csv(OUT/"every_model_monthly.csv.gz",index=False,compression="gzip")
    selected,by_month,counts=select_and_report(models,monthly)
    portfolio=combine_portfolio(by_month)
    summary=dict(nconfigs=len(models),n_by_family=models.groupby("family").size().to_dict(),
       selected=selected.to_dict("records"),counts=counts,portfolio_train2025=portfolio,
       no_live_orders=True,unmodeled_funding_and_depth=True,
       prior_2026_research_exposure=True,
       cost_details="0.05pct taker per leg,18pct GST on fees,5 BTC points adverse slip each leg; stress +5bps adverse each leg",
       strict_execution="completed H1 and H4 bars; next 1m open; same-1m stop-first; no lookahead")
    (OUT/"summary.json").write_text(json.dumps(summary,indent=2,default=str)+"\n")
    print("STAGE28_COMPLETE",json.dumps(dict(nconfigs=len(models),
      selected=[dict(family=x["family"],model=x["model"],base22=x["base_net22"],
        cost5_22=x["stress5_net22"],cost5_2025=x["stress5_yr25"],
        cost5_2026=x["stress5_yr26"],trades=x["ntrades"]) for x in
        selected.to_dict("records")],portfolio=portfolio)))
if __name__=="__main__":main()
