#!/usr/bin/env python3
"""V56: compare coarse 16/20/24-candle channel lookbacks, preserving V53 entry expansion, extension, risk and exits. 2024–2025 only."""
import itertools,json
from pathlib import Path
import numpy as np
import pandas as pd
import research_v48_progressive_trailing as v

OUT=Path("analysis/v56_breakout_lookback");OUT.mkdir(parents=True,exist_ok=True)
CAPS=(("V42",1.5,float("inf"),24,20),("V53",1.25,2.,48,20),("V56_16",1.25,2.,48,16),("V56_24",1.25,2.,48,24))
CFG=dict(family="expansion_breakout",timeframe=240,lookback=20,stop_fraction=3.,rr=0.,exit_kind="breakeven_1r",hold_minutes=10080,activation_r=1.,lock_r=0.,early_kind="contraction",early_param=.75,early_hours=24)

def train():
    m,ctx=v.load("train")
    ctx["atr"]={240:v.atr_series(m,240)}
    ctx["channels"]={n:v.channel_series(m,n) for n in (10,20)}
    ctx["exit_context"]=v.exit_context(m)
    z=m.resample("240min").agg(open=("open","first"),high=("high","max"),low=("low","min"),close=("close","last"),count=("close","count"))
    z=z[z["count"]==240]
    prev=z.close.shift(1)
    tr=pd.concat([z.high-z.low,(z.high-prev).abs(),(z.low-prev).abs()],axis=1).max(axis=1)
    prior=tr.ewm(alpha=1/14,adjust=False,min_periods=14).mean().shift(1)
    def events_for(threshold,n):
        upper=z.high.shift(1).rolling(n).max()
        lower=z.low.shift(1).rolling(n).min()
        expansion=tr>=threshold*prior
        up=expansion&(z.close>upper);dn=expansion&(z.close<lower)
        events=[]
        for i in np.flatnonzero((up^dn).to_numpy()):
            j=int(m.index.searchsorted(z.index[i]+pd.Timedelta(minutes=240)))
            if j<len(m) and m.index[j].tz_convert(v.IST).dayofweek<5:
                events.append((j,1 if up.iat[i] else -1,0,0))
        return np.asarray(events,dtype=np.int64).reshape(-1,4)
    assert np.array_equal(events_for(1.5,20),v.signals(m,"expansion_breakout",240,20))
    rows=[];monthly=[]
    for name,threshold,cap,hours,n in CAPS:
        events=events_for(threshold,n)
        j=events[:,0];side=events[:,1]
        close,_,_,_=ctx["exit_context"]
        channel_upper=z.high.shift(1).rolling(n).max()
        channel_lower=z.low.shift(1).rolling(n).min()
        channel_upper.index+=pd.Timedelta(minutes=240)
        channel_lower.index+=pd.Timedelta(minutes=240)
        channel_upper=channel_upper.reindex(m.index).to_numpy(float)
        channel_lower=channel_lower.reindex(m.index).to_numpy(float)
        extension=side*(close[j]-np.where(side==1,channel_upper[j],channel_lower[j]))/ctx["atr"][240][j-240]
        assert np.isfinite(extension).all() and (extension>0).all()
        events=events[extension<=cap]
        for label,a,b in v.FOLDS+[("continuous","2024-02-01","2026-01-01")]:
            p=v.period(m,ctx,events,a,b)
            for lev,(sc,mode) in itertools.product((20,50,200),((v.SC[0],0),(v.SC[1],1))):
                r=v.run(ctx,p,dict(CFG,early_hours=hours,lookback=n),lev,sc,mode)
                us=r.pop("monthly_usd");re=r.pop("monthly_returns");r.pop("monthly_points")
                if label=="continuous":
                    r.update(year2024_usd=float(us[:11].sum()),year2025_usd=float(us[11:].sum()))
                    monthly.extend(dict(profile=name,leverage=lev,scenario=sc[0],month=str(pd.Period("2024-02",freq="M")+i),net_usd=u,return_pct=re[i]) for i,u in enumerate(us))
                rows.append(dict(profile=name,fold=label,leverage=lev,scenario=sc[0],**r))
        print("V56_PROFILE_DONE",name,flush=True)
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
    for name,threshold,cap,hours,n in CAPS:
        x=result(name,"base");y=result(name,"combined");a=df[df.profile==name]
        passed=bool(name.startswith("V56") and x.net_usd>=high.net_usd and x.positive_months>base.positive_months and x.months_ge_1pct>=base.months_ge_1pct and x.closed_dd_pct<=high.closed_dd_pct and x.mark_dd_upper_pct<=high.mark_dd_upper_pct and x.year2024_usd>=base.year2024_usd and x.year2025_usd>=base.year2025_usd and y.net_usd>=stress.net_usd and (a.net_usd>0).all() and (a.liquidations==0).all())
        ranking.append(dict(profile=name,min_expansion_atr=threshold,max_extension_atr=cap,contraction_delay_hours=hours,lookback=n,net_usd=x.net_usd,positive_months=x.positive_months,months_ge_1pct=x.months_ge_1pct,closed_dd_pct=x.closed_dd_pct,mark_dd_upper_pct=x.mark_dd_upper_pct,year2024_usd=x.year2024_usd,year2025_usd=x.year2025_usd,stress_net_usd=y.net_usd,trades=x.trades,signals=x.signal_count,training_pass=passed))
    pd.DataFrame(ranking).to_csv(OUT/"training_ranking.csv",index=False)
    (OUT/"quality.json").write_text(json.dumps(dict(baseline_parity=True,training_period="2024-02 to 2025-12",validation_2026_run=False,new_configurations=2,control_profiles=['V42','V53'],lookbacks=[16,20,24],contraction_delay_hours=48,min_expansion_atr=1.25,max_extension_atr=2.,risk_pct=v.RISK,exposure_cap=v.CAP,holdout_previously_examined=True,selection_bias_possible=True),indent=2))
    print(pd.DataFrame(ranking).to_string(index=False),flush=True)

if __name__=="__main__":train()
