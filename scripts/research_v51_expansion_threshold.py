#!/usr/bin/env python3
"""V51: broaden H4 range expansion threshold, keeping V42 entry channel and exit unchanged. Training only."""
import itertools,json
from pathlib import Path
import numpy as np
import pandas as pd
import research_v48_progressive_trailing as v

OUT=Path("analysis/v51_expansion_threshold");OUT.mkdir(parents=True,exist_ok=True)
CAPS=(1.5,1.25,1.0)
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
    rows=[];monthly=[]
    for cap in CAPS:
        name="V42" if cap==1.5 else str(cap)
        events=events_for(cap)
        for label,a,b in v.FOLDS+[("continuous","2024-02-01","2026-01-01")]:
            p=v.period(m,ctx,events,a,b)
            for lev,(sc,mode) in itertools.product((20,50,200),((v.SC[0],0),(v.SC[1],1))):
                r=v.run(ctx,p,CFG,lev,sc,mode)
                us=r.pop("monthly_usd");re=r.pop("monthly_returns");r.pop("monthly_points")
                if label=="continuous":
                    r.update(year2024_usd=float(us[:11].sum()),year2025_usd=float(us[11:].sum()))
                    monthly.extend(dict(expansion_threshold=name,leverage=lev,scenario=sc[0],month=str(pd.Period("2024-02",freq="M")+i),net_usd=u,return_pct=re[i]) for i,u in enumerate(us))
                rows.append(dict(expansion_threshold=name,fold=label,leverage=lev,scenario=sc[0],**r))
        print("V51_THRESHOLD_DONE",name,flush=True)
    df=pd.DataFrame(rows)
    df.to_csv(OUT/"training_folds.csv",index=False)
    pd.DataFrame(monthly).to_csv(OUT/"training_monthly.csv",index=False)
    full=df[df.fold=="continuous"]
    def result(name,scenario):
        return full[(full.expansion_threshold==name)&(full.leverage==50)&(full.scenario==scenario)].iloc[0]
    base=result("V42","base");stress=result("V42","combined")
    assert abs(base.net_usd-34.990697617170554)<1e-6
    assert abs(stress.net_usd-29.456191741520115)<1e-6
    ranking=[]
    for cap in CAPS:
        name="V42" if cap==1.5 else str(cap)
        x=result(name,"base");y=result(name,"combined");a=df[df.expansion_threshold==name]
        passed=bool(name!="V42" and x.net_usd>=base.net_usd and x.positive_months>base.positive_months and x.months_ge_1pct>=base.months_ge_1pct and x.closed_dd_pct<=base.closed_dd_pct and x.mark_dd_upper_pct<=base.mark_dd_upper_pct and x.year2024_usd>0 and x.year2025_usd>0 and y.net_usd>=stress.net_usd and (a.net_usd>0).all() and (a.liquidations==0).all())
        ranking.append(dict(expansion_threshold=name,net_usd=x.net_usd,positive_months=x.positive_months,months_ge_1pct=x.months_ge_1pct,closed_dd_pct=x.closed_dd_pct,mark_dd_upper_pct=x.mark_dd_upper_pct,year2024_usd=x.year2024_usd,year2025_usd=x.year2025_usd,stress_net_usd=y.net_usd,trades=x.trades,signals=x.signal_count,training_pass=passed))
    pd.DataFrame(ranking).to_csv(OUT/"training_ranking.csv",index=False)
    (OUT/"quality.json").write_text(json.dumps(dict(baseline_parity=True,training_period="2024-02 to 2025-12",validation_2026_run=False,thresholds_prior_atr=[1.5,1.25,1.],risk_pct=v.RISK,exposure_cap=v.CAP,holdout_previously_examined=True,selection_bias_possible=True),indent=2))
    print(pd.DataFrame(ranking).to_string(index=False),flush=True)

if __name__=="__main__":train()
