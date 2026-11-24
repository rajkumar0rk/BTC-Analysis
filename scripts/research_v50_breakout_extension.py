#!/usr/bin/env python3
"""V50: cap signal close extension beyond the prior H4 channel in prior ATR units.
Prespecified coarse thresholds; V42 benchmark; train only, no 2026 access."""
import itertools,json
from pathlib import Path
import numpy as np
import pandas as pd
import research_v48_progressive_trailing as v

OUT=Path("analysis/v50_breakout_extension");OUT.mkdir(parents=True,exist_ok=True)
CAPS=(float("inf"),0.5,1.0,2.0)
CFG=dict(family="expansion_breakout",timeframe=240,lookback=20,stop_fraction=3.,rr=0.,exit_kind="breakeven_1r",hold_minutes=10080,activation_r=1.,lock_r=0.,early_kind="contraction",early_param=.75,early_hours=24)

def train():
    m,ctx=v.load("train")
    ctx["atr"]={240:v.atr_series(m,240)}
    ctx["channels"]={n:v.channel_series(m,n) for n in (10,20)}
    ctx["exit_context"]=v.exit_context(m)
    ev=v.signals(m,"expansion_breakout",240,20)
    j=ev[:,0];side=ev[:,1]
    close,upper,lower,_=ctx["exit_context"]
    prior=ctx["atr"][240][j-240]
    extension=side*(close[j]-np.where(side==1,upper[j],lower[j]))/prior
    assert np.isfinite(extension).all() and (extension>0).all()
    rows=[];monthly=[]
    for cap in CAPS:
        name="V42" if np.isinf(cap) else str(cap)
        events=ev[extension<=cap]
        for label,a,b in v.FOLDS+[("continuous","2024-02-01","2026-01-01")]:
            p=v.period(m,ctx,events,a,b)
            for lev,(sc,mode) in itertools.product((20,50,200),((v.SC[0],0),(v.SC[1],1))):
                r=v.run(ctx,p,CFG,lev,sc,mode)
                us=r.pop("monthly_usd");re=r.pop("monthly_returns");r.pop("monthly_points")
                if label=="continuous":
                    r.update(year2024_usd=float(us[:11].sum()),year2025_usd=float(us[11:].sum()))
                    monthly.extend(dict(cap=name,leverage=lev,scenario=sc[0],month=str(pd.Period("2024-02",freq="M")+i),net_usd=u,return_pct=re[i]) for i,u in enumerate(us))
                rows.append(dict(cap=name,fold=label,leverage=lev,scenario=sc[0],**r))
        print("V50_CAP_DONE",name,flush=True)
    df=pd.DataFrame(rows)
    df.to_csv(OUT/"training_folds.csv",index=False)
    pd.DataFrame(monthly).to_csv(OUT/"training_monthly.csv",index=False)
    full=df[df.fold=="continuous"]
    def result(name,scenario):
        return full[(full.cap==name)&(full.leverage==50)&(full.scenario==scenario)].iloc[0]
    base=result("V42","base");stress=result("V42","combined")
    assert abs(base.net_usd-34.990697617170554)<1e-6
    assert abs(stress.net_usd-29.456191741520115)<1e-6
    ranking=[]
    for cap in CAPS:
        name="V42" if np.isinf(cap) else str(cap)
        x=result(name,"base");y=result(name,"combined");a=df[df.cap==name]
        passed=bool(name!="V42" and x.net_usd>=base.net_usd and x.positive_months>base.positive_months and x.months_ge_1pct>=base.months_ge_1pct and x.closed_dd_pct<=base.closed_dd_pct and x.mark_dd_upper_pct<=base.mark_dd_upper_pct and x.year2024_usd>0 and x.year2025_usd>0 and y.net_usd>=stress.net_usd and (a.net_usd>0).all() and (a.liquidations==0).all())
        ranking.append(dict(cap=name,net_usd=x.net_usd,positive_months=x.positive_months,months_ge_1pct=x.months_ge_1pct,closed_dd_pct=x.closed_dd_pct,mark_dd_upper_pct=x.mark_dd_upper_pct,year2024_usd=x.year2024_usd,year2025_usd=x.year2025_usd,stress_net_usd=y.net_usd,trades=x.trades,signals=x.signal_count,training_pass=passed))
    pd.DataFrame(ranking).to_csv(OUT/"training_ranking.csv",index=False)
    pd.DataFrame(dict(signal_time=m.index[j],side=side,extension_prior_atr=extension)).to_csv(OUT/"signal_extension.csv",index=False)
    (OUT/"quality.json").write_text(json.dumps(dict(baseline_parity=True,training_period="2024-02 to 2025-12",validation_2026_run=False,thresholds_prior_atr=[0.5,1.,2.],risk_pct=v.RISK,exposure_cap=v.CAP,holdout_previously_examined=True,selection_bias_possible=True),indent=2))
    print(pd.DataFrame(ranking).to_string(index=False),flush=True)

if __name__=="__main__":train()
