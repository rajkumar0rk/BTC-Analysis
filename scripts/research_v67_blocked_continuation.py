#!/usr/bin/env python3
"""V67: one fresh continuation attempt after a blocked original signal; training only."""
import itertools,json
from pathlib import Path
import numpy as np
import pandas as pd
import research_v67_execution as v

OUT=Path("analysis/v67_blocked_continuation");OUT.mkdir(parents=True,exist_ok=True)
CAPS=(("V42",1.5,float("inf"),24,7,1.,0.,False),("V53",1.25,2.,48,7,1.,0.,False),("V58",1.25,2.,48,10,1.,0.,False),("V60",1.25,2.,48,10,.75,0.,False),("V64_010",1.25,2.,48,10,.75,.1,False),("V64_025",1.25,2.,48,10,.75,.25,False),("V67_continuation",1.25,2.,48,10,.75,0.,True))
CFG=dict(family="expansion_breakout",timeframe=240,lookback=20,stop_fraction=3.,rr=0.,exit_kind="breakeven_1r",hold_minutes=10080,activation_r=1.,lock_r=0.,early_kind="contraction",early_param=.75,early_hours=24)

def train():
    m,ctx=v.load("train")
    ctx["atr"]={240:v.atr_series(m,240)}
    ctx["channels"]={n:v.channel_series(m,n) for n in (10,20)}
    ctx["exit_context"]=v.exit_context(m)
    z=m.resample("240min").agg(open=("open","first"),high=("high","max"),low=("low","min"),close=("close","last"),count=("close","count"))
    z=z[z["count"]==240]
    upper=z.high.shift(1).rolling(20).max()
    lower=z.low.shift(1).rolling(20).min()
    prev=z.close.shift(1)
    tr=pd.concat([z.high-z.low,(z.high-prev).abs(),(z.low-prev).abs()],axis=1).max(axis=1)
    prior=tr.ewm(alpha=1/14,adjust=False,min_periods=14).mean().shift(1)
    def events_for(threshold):
        expansion=tr>=threshold*prior
        up=expansion&(z.close>upper);dn=expansion&(z.close<lower)
        events=[]
        for i in np.flatnonzero((up^dn).to_numpy()):
            j=int(m.index.searchsorted(z.index[i]+pd.Timedelta(minutes=240)))
            if j<len(m) and m.index[j].tz_convert(v.IST).dayofweek<5:
                events.append((j,1 if up.iat[i] else -1,0,0))
        return np.asarray(events,dtype=np.int64).reshape(-1,4)
    assert np.array_equal(events_for(1.5),v.signals(m,"expansion_breakout",240,20))
    rows=[];monthly=[];diagnostics=[]
    for name,threshold,cap,hours,days,activation,lock,continuation in CAPS:
        events=events_for(threshold)
        j=events[:,0];side=events[:,1]
        close,channel_upper,channel_lower,_=ctx["exit_context"]
        extension=side*(close[j]-np.where(side==1,channel_upper[j],channel_lower[j]))/ctx["atr"][240][j-240]
        assert np.isfinite(extension).all() and (extension>0).all()
        events=events[extension<=cap]
        if continuation:
            original_times=set(events[:,0].tolist())
            extra=[]
            for origin,direction,_,_ in events:
                level=channel_upper[origin] if direction==1 else channel_lower[origin]
                for bars in (2,3):
                    k=int(origin+240*bars)
                    if k>=len(m) or k in original_times or m.index[k].tz_convert(v.IST).dayofweek>=5:continue
                    if m.index[k]-m.index[origin]!=pd.Timedelta(minutes=240*bars):continue
                    path=close[origin+240:k+1:240]
                    if len(path)!=bars or not np.isfinite(path).all() or not (direction*(path-level)>0).all():continue
                    if direction*(close[k]-close[k-240])<=0:continue
                    a0=ctx["atr"][240][k-240]
                    if not np.isfinite(a0) or a0<=0 or direction*(close[k]-level)>cap*a0:continue
                    extra.append((k,int(direction),int(origin)+1,0))
            if extra:
                events=np.concatenate([events,np.asarray(extra,dtype=np.int64).reshape(-1,4)])
                events=events[np.lexsort((-events[:,2],events[:,0]))]
        for label,a,b in v.FOLDS+[("continuous","2024-02-01","2026-01-01")]:
            p=v.period(m,ctx,events,a,b)
            for lev,(sc,mode) in itertools.product((20,50,200),((v.SC[0],0),(v.SC[1],1))):
                r=v.run(ctx,p,dict(CFG,early_hours=hours,hold_minutes=days*1440,activation_r=activation,lock_r=lock),lev,sc,mode,audit=True)
                ledger=r.pop("ledger")
                executed=ledger[ledger[:,0]==3]
                durations=executed[:,2]-executed[:,1]+1
                supplemental=p[1][:,2]>0
                resumed=ledger[supplemental&(ledger[:,0]==3)]
                r.update(original_signals=int((~supplemental).sum()),continuation_candidates=int(supplemental.sum()),continuation_trades=len(resumed),continuation_net_usd=float(resumed[:,9].sum()),continuation_rejected=int((supplemental&(ledger[:,0]==2)).sum()),busy_signals=int((ledger[:,0]==1).sum()),other_skips=int((ledger[:,0]==0).sum()))
                if label=="continuous" and lev==50:
                    for event,rec in zip(p[1],ledger):
                        diagnostics.append(dict(profile=name,scenario=sc[0],signal_time=str(m.index[int(event[0])]),side=int(event[1]),status=int(rec[0]),continuation=bool(event[2]>0),source_signal_index=int(event[2]-1),net_usd=rec[9],mfe_r=rec[7],mae_r=rec[8],blocking_exit_index=rec[11]))
                r.update(trades_held_7d=int((durations>=7*1440).sum()),holding_limit_exits=int(((executed[:,10]==3)&(durations>=days*1440)).sum()))
                us=r.pop("monthly_usd");re=r.pop("monthly_returns");r.pop("monthly_points")
                if label=="continuous":
                    r.update(year2024_usd=float(us[:11].sum()),year2025_usd=float(us[11:].sum()))
                    monthly.extend(dict(profile=name,leverage=lev,scenario=sc[0],month=str(pd.Period("2024-02",freq="M")+i),net_usd=u,return_pct=re[i]) for i,u in enumerate(us))
                rows.append(dict(profile=name,fold=label,leverage=lev,scenario=sc[0],**r))
        print("V67_PROFILE_DONE",name,flush=True)
    pd.DataFrame(diagnostics).to_csv(OUT/"signal_diagnostics.csv",index=False)
    df=pd.DataFrame(rows)
    df.to_csv(OUT/"training_folds.csv",index=False)
    pd.DataFrame(monthly).to_csv(OUT/"training_monthly.csv",index=False)
    full=df[df.fold=="continuous"]
    def result(name,scenario):
        return full[(full.profile==name)&(full.leverage==50)&(full.scenario==scenario)].iloc[0]
    base=result("V42","base");stress=result("V42","combined")
    assert abs(base.net_usd-34.990697617170554)<1e-6
    assert abs(stress.net_usd-29.456191741520115)<1e-6
    ranking=[]
    high=result("V53","base")
    assert abs(high.net_usd-40.586868798209196)<1e-6
    assert abs(result("V53","combined").net_usd-28.81567281620687)<1e-6
    best=result("V60","base")
    beststress=result("V60","combined")
    assert abs(best.net_usd-43.23976710154696)<1e-6
    assert abs(beststress.net_usd-37.998880340961364)<1e-6
    for control,expected,stress_expected in [("V64_010",41.28385339461741,37.83324688612572),("V64_025",41.28071962884141,26.250332944349097)]:
        assert abs(result(control,"base").net_usd-expected)<1e-6
        assert abs(result(control,"combined").net_usd-stress_expected)<1e-6
    for name,threshold,cap,hours,days,activation,lock,continuation in CAPS:
        x=result(name,"base");y=result(name,"combined");a=df[df.profile==name]
        passed=bool(name.startswith("V67") and x.net_usd>=best.net_usd and x.positive_months>=best.positive_months and x.months_ge_1pct>=best.months_ge_1pct and x.closed_dd_pct<=high.closed_dd_pct and x.mark_dd_upper_pct<=high.mark_dd_upper_pct and x.year2024_usd>=base.year2024_usd and x.year2025_usd>=base.year2025_usd and y.net_usd>=beststress.net_usd and (a.net_usd>0).all() and (a.liquidations==0).all())
        ranking.append(dict(profile=name,min_expansion_atr=threshold,max_extension_atr=cap,contraction_delay_hours=hours,max_hold_days=days,activation_r=activation,lock_r=lock,continuation=continuation,net_usd=x.net_usd,positive_months=x.positive_months,months_ge_1pct=x.months_ge_1pct,closed_dd_pct=x.closed_dd_pct,mark_dd_upper_pct=x.mark_dd_upper_pct,year2024_usd=x.year2024_usd,year2025_usd=x.year2025_usd,stress_net_usd=y.net_usd,trades=x.trades,signals=x.signal_count,trades_held_7d=x.trades_held_7d,holding_limit_exits=x.holding_limit_exits,risk_rejected=x.risk_rejected,busy_signals=x.busy_signals,other_skips=x.other_skips,original_signals=x.original_signals,continuation_candidates=x.continuation_candidates,continuation_trades=x.continuation_trades,continuation_net_usd=x.continuation_net_usd,continuation_rejected=x.continuation_rejected,training_pass=passed))
    pd.DataFrame(ranking).to_csv(OUT/"training_ranking.csv",index=False)
    (OUT/"quality.json").write_text(json.dumps(dict(baseline_parity=True,training_period="2024-02 to 2025-12",validation_2026_run=False,new_configurations=1,control_profiles=['V42','V53','V58','V60','V64_010','V64_025'],confirmation_window_bars=[2,3],require_full_post_exit_bar=True,one_attempt_per_blocked_signal=True,require_original_level_and_directional_close=True,activation_r=[.75,1.],lock_r=[0.,.1,.25],hold_days=[7,10],contraction_delay_hours=48,min_expansion_atr=1.25,max_extension_atr=2.,risk_pct=v.RISK,exposure_cap=v.CAP,holdout_previously_examined=True,selection_bias_possible=True),indent=2))
    print(pd.DataFrame(ranking).to_string(index=False),flush=True)

if __name__=="__main__":train()
