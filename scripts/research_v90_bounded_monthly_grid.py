#!/usr/bin/env python3
"""V90: bounded 3x3 coarse lookback/ATR stop grid on 2024-2025 only; monthly-first ranking, no holdout."""
import itertools,json
from pathlib import Path
import numpy as np
import pandas as pd
import research_v48_progressive_trailing as v

OUT=Path("analysis/v90_bounded_monthly_grid");OUT.mkdir(parents=True,exist_ok=True)
PROFILES=tuple(("V69_no_cap" if n==20 and stop==3. else f"V90_n{n}_s{stop:g}",n,stop) for n in (10,15,20) for stop in (2.,2.5,3.))
CFG=dict(family="expansion_breakout",lookback=20,stop_fraction=3.,rr=0.,exit_kind="breakeven_1r",activation_r=.75,lock_r=0.,early_kind="contraction",early_param=.75)

def setup(m,tf,n=20):
    z=m.resample(f"{tf}min").agg(high=("high","max"),low=("low","min"),close=("close","last"),count=("close","count"))
    z=z[z["count"]==tf]
    prev=z.close.shift(1)
    tr=pd.concat([z.high-z.low,(z.high-prev).abs(),(z.low-prev).abs()],axis=1).max(axis=1)
    a=tr.ewm(alpha=1/14,adjust=False,min_periods=14).mean()
    upper=z.high.shift(1).rolling(n).max()
    lower=z.low.shift(1).rolling(n).min()
    prior=a.shift(1)
    up=(tr>=1.25*prior)&(z.close>upper)
    dn=(tr>=1.25*prior)&(z.close<lower)
    events=[]
    for i in np.flatnonzero((up^dn).to_numpy()):
        t=z.index[i]+pd.Timedelta(minutes=tf)
        j=int(m.index.searchsorted(t))
        if j<len(m) and m.index[j]==t and m.index[j].tz_convert(v.IST).dayofweek<5:
            events.append((j,1 if up.iat[i] else -1,0,0))
    aligned=pd.DataFrame(dict(close=z.close,upper=upper,lower=lower,expansion=tr/prior))
    aligned.index+=pd.Timedelta(minutes=tf)
    aligned=aligned.reindex(m.index)
    ec=tuple(aligned[k].to_numpy(float) for k in ("close","upper","lower","expansion"))
    if tf==240 and n==20:
        for x,y in zip(ec,v.exit_context(m)):
            assert np.allclose(x,y,equal_nan=True)
    return np.asarray(events,dtype=np.int64).reshape(-1,4),ec

def train():
    m,ctx=v.load("train")
    # The existing channel trailing exits are inactive; preserve engine inputs.
    ctx["channels"]={n:v.channel_series(m,n) for n in (10,20)}
    rows=[];monthly=[];trades=[]
    for name,n,stop in PROFILES:
        tf=240
        ctx["atr"]={tf:v.atr_series(m,tf)}
        ev,ctx["exit_context"]=setup(m,tf,n)
        # Preserve bar counts: 60 bars maximum holding, 12 bars before contraction.
        hold=60*tf;hours=12*tf//60
        cfg=dict(CFG,timeframe=tf,lookback=n,stop_fraction=stop,hold_minutes=hold,early_hours=hours)
        for label,a,b in v.FOLDS+[("continuous","2024-02-01","2026-01-01")]:
            p=v.period(m,ctx,ev,a,b)
            for lev,(sc,mode) in itertools.product((20,50,200),((v.SC[0],0),(v.SC[1],1))):
                r=v.run(ctx,p,cfg,lev,sc,mode,audit=True)
                ledger=r.pop("ledger")
                executed=ledger[ledger[:,0]==3]
                assert (executed[1:,1]>executed[:-1,2]).all()
                pnl=executed[:,9]
                assert abs(float(pnl.sum())-r["net_usd"])<1e-6
                winners=np.sort(pnl[pnl>0])[::-1]
                gross=float(winners.sum());loss=float(-pnl[pnl<0].sum())
                r.update(gross_profit_usd=gross,gross_loss_usd=loss,profit_factor=gross/loss if loss>0 else None,net_ex_top3_usd=float(pnl.sum()-winners[:3].sum()),net_ex_top5_usd=float(pnl.sum()-winners[:5].sum()),busy_signals=int((ledger[:,0]==1).sum()))
                us=r.pop("monthly_usd");re=r.pop("monthly_returns");r.pop("monthly_points")
                if label=="continuous":
                    r.update(year2024_usd=float(us[:11].sum()),year2025_usd=float(us[11:].sum()),inactive_months=int((re==0).sum()),negative_months=int((re<0).sum()),positive_2024=int((re[:11]>0).sum()),positive_2025=int((re[11:]>0).sum()),months_ge_1pct_2024=int((re[:11]>=1).sum()),months_ge_1pct_2025=int((re[11:]>=1).sum()),worst_month_pct=float(re.min()),median_month_pct=float(np.median(re)))
                    monthly.extend(dict(profile=name,leverage=lev,scenario=sc[0],month=str(pd.Period("2024-02",freq="M")+i),net_usd=u,return_pct=q) for i,u,q in zip(range(len(us)),us,re))
                    if lev==50:
                        for event,rec in zip(p[1],ledger):
                            if rec[0]==3:
                                trades.append(dict(profile=name,scenario=sc[0],entry=str(m.index[int(rec[1])]),exit=str(m.index[int(rec[2])]),side=int(event[1]),net_usd=float(rec[9]),exit_reason=int(rec[10])))
                rows.append(dict(profile=name,tf_minutes=tf,lookback=n,stop_atr=stop,hold_hours=hold/60,contraction_delay_hours=hours,fold=label,leverage=lev,scenario=sc[0],**r))
        print("V90_PROFILE_DONE",name,flush=True)
    df=pd.DataFrame(rows)
    df.to_csv(OUT/"training_folds.csv",index=False)
    pd.DataFrame(monthly).to_csv(OUT/"training_monthly.csv",index=False)
    pd.DataFrame(trades).to_csv(OUT/"training_trades.csv",index=False)
    full=df[(df.fold=="continuous")&(df.leverage==50)]
    def result(name,scenario):
        return full[(full.profile==name)&(full.scenario==scenario)].iloc[0]
    base=result("V69_no_cap","base");stress=result("V69_no_cap","combined")
    assert abs(base.net_usd-49.277536827321114)<1e-6
    assert abs(stress.net_usd-42.020963450250946)<1e-6
    assert base.trades==68 and base.signal_count==261
    assert base.positive_months==17 and base.months_ge_1pct==13
    assert abs(result("V90_n10_s3","base").net_usd-29.942377351397283)<1e-6
    assert abs(result("V90_n15_s3","base").net_usd-41.40026333443549)<1e-6
    assert abs(result("V90_n10_s3","combined").net_usd-30.534205062767086)<1e-6
    assert abs(result("V90_n15_s3","combined").net_usd-39.02993777764482)<1e-6
    ranking=[]
    for name,n,stop in PROFILES:
        tf=240
        x=result(name,"base");y=result(name,"combined");a=df[df.profile==name]
        f=a[(a.fold!="continuous")&(a.leverage==50)]
        profitable_base=int(((f.scenario=="base")&(f.net_usd>0)).sum())
        profitable_stress=int(((f.scenario=="combined")&(f.net_usd>0)).sum())
        passed=bool(name.startswith("V90") and x.trades>=300 and x.net_usd>=base.net_usd and x.positive_months>base.positive_months and x.months_ge_1pct>base.months_ge_1pct and x.positive_2024>=base.positive_2024 and x.positive_2025>=base.positive_2025 and y.positive_months>=stress.positive_months and y.months_ge_1pct>=stress.months_ge_1pct and x.worst_month_pct>=base.worst_month_pct and y.worst_month_pct>=stress.worst_month_pct and x.closed_dd_pct<=base.closed_dd_pct and x.mark_dd_upper_pct<=base.mark_dd_upper_pct and x.year2024_usd>=base.year2024_usd and x.year2025_usd>=base.year2025_usd and y.net_usd>=stress.net_usd and (a.net_usd>0).all() and (a.liquidations==0).all() and x.net_ex_top5_usd>=base.net_ex_top5_usd and y.net_ex_top3_usd>=stress.net_ex_top3_usd)
        ranking.append(dict(profile=name,timeframe_minutes=tf,lookback=n,stop_atr=stop,hold_hours=x.hold_hours,contraction_delay_hours=x.contraction_delay_hours,net_usd=x.net_usd,positive_months=x.positive_months,months_ge_1pct=x.months_ge_1pct,negative_months=x.negative_months,inactive_months=x.inactive_months,positive_2024=x.positive_2024,positive_2025=x.positive_2025,months_ge_1pct_2024=x.months_ge_1pct_2024,months_ge_1pct_2025=x.months_ge_1pct_2025,worst_month_pct=x.worst_month_pct,median_month_pct=x.median_month_pct,stress_positive_months=y.positive_months,stress_months_ge_1pct=y.months_ge_1pct,stress_worst_month_pct=y.worst_month_pct,closed_dd_pct=x.closed_dd_pct,mark_dd_upper_pct=x.mark_dd_upper_pct,year2024_usd=x.year2024_usd,year2025_usd=x.year2025_usd,stress_net_usd=y.net_usd,trades=x.trades,wins=x.wins,profit_factor=x.profit_factor,signals=x.signal_count,risk_rejected=x.risk_rejected,busy_signals=x.busy_signals,profitable_folds_base=profitable_base,profitable_folds_stress=profitable_stress,liquidations_all=int(a.liquidations.sum()),net_ex_top5_usd=x.net_ex_top5_usd,stress_net_ex_top3_usd=y.net_ex_top3_usd,training_pass=passed))
    rank=pd.DataFrame(ranking)
    # Local robustness diagnostic, not an independent validation. Neighbors differ by one coarse grid step.
    for i,x in rank.iterrows():
        near=rank[((rank.lookback-x.lookback).abs()/5+(rank.stop_atr-x.stop_atr).abs()/.5)<=1.000001]
        rank.loc[i,"neighbor_min_positive_months"]=int(near.positive_months.min())
        rank.loc[i,"neighbor_profitable_fraction"]=float(((near.net_usd>0)&(near.stress_net_usd>0)).mean())
        rank.loc[i,"neighbor_median_months"]=float(near.positive_months.median())
    rank["monthly_improvement_only"]=(rank.positive_months>base.positive_months)&(rank.net_usd>0)&(rank.stress_net_usd>0)
    rank["full_target_met"]=(rank.positive_months==23)&(rank.months_ge_1pct==23)&rank.training_pass
    rank=rank.sort_values(["positive_months","months_ge_1pct","stress_positive_months","neighbor_median_months","net_usd"],ascending=False)
    rank.to_csv(OUT/"training_ranking.csv",index=False)
    (OUT/"quality.json").write_text(json.dumps(dict(training_period="2024-02 to 2025-12",validation_2026_run=False,new_configurations=6,total_configurations=9,baseline_parity=True,prior_v78_parity=True,timeframes_minutes=[240],entry_channel="prior completed highs/lows",entry_expansion_ratio=1.25,lookback_grid=[10,15,20],stop_atr_grid=[2.,2.5,3.],neighbor_check=True,monthly_first_ranking=True,exit_geometry_unchanged=True,candle_anchor="UTC midnight",strict_monthly_improvement=True,yearwise_monthly_non_regression=True,worst_month_non_regression=True,overlap_asserted=True,original_costs_retained=True,monthly_pnl_basis="realized cash PnL with modeled funding allocation, not end-of-month mark-to-market",hold_bars=60,contraction_delay_bars=12,risk_pct=v.RISK,exposure_cap=v.CAP,minimum_trades=300,aspirational_positive_months=23,aspirational_months_ge_1pct=23,holdout_previously_examined=True,selection_bias_possible=True),indent=2))
    print(rank.to_string(index=False),flush=True)

if __name__=="__main__":train()
