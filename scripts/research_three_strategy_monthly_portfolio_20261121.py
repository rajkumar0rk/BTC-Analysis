#!/usr/bin/env python3
"""Month-end BTC three-strategy capital-allocation screening.
NOT a shared-margin 1m backtest. Uses preserved GitHub Actions CSV artifacts.
Sample:
  python scripts/research_three_strategy_monthly_portfolio_20261121.py \
    --stage-artifact stage18-20-guardfree.zip \
    --donchian-artifact btc-48h-22month.zip \
    --out analysis/btc_three_strategy_portfolio_20261121
"""
import argparse
from pathlib import Path
import zipfile
import numpy as np
import pandas as pd

WEIGHTS={
    "50_20_30":(.50,.20,.30),
    "60_10_30":(.60,.10,.30),
    "70_10_20":(.70,.10,.20),
    "50_30_20":(.50,.30,.20),
    "stage18_only":(1.,0.,0.),
    "stage20_only":(0.,1.,0.),
    "donchian_only":(0.,0.,1.),
}
def load(stage, donchian):
    with zipfile.ZipFile(stage) as z:
        a=pd.read_csv(z.open("all_months.csv"))
    a=a[(a.variant=="5R_broader_eff25_no_gate") &
        (a.stress_bps_side==0)].pivot(
        index="month",columns="family",values="net_month_pct")
    with zipfile.ZipFile(donchian) as z:
        b=pd.read_csv(z.open("all_22_months_and_rejected_signals.csv"))
    b=b[(b.variant=="unmodified") &
        (b.base_slippage_points_each_side==5.) &
        (b.slippage_bps_side==0)].set_index("month_ist").net_pct
    combined=a.join(b.rename("48hDonchian"),how="inner").sort_index()
    expected=pd.period_range("2025-01","2026-10",freq="M").astype(str).tolist()
    assert list(combined.index)==expected
    return combined[["Stage18","Stage20","48hDonchian"]]
def score(r):
    e=np.r_[1,np.cumprod(1+r/100)]
    return dict(positive=int((r>1e-8).sum()),
                negative=int((r< -1e-8).sum()),
                flat=int((abs(r)<=1e-8).sum()),
                net_22_pct=float((e[-1]-1)*100),
                train_2025_pct=float((np.prod(1+r[:12]/100)-1)*100),
                check_2026_pct=float((np.prod(1+r[12:]/100)-1)*100),
                worst_month_pct=float(min(r)),
                month_end_dd_pct=float(100*np.max(1-e/np.maximum.accumulate(e))))
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--stage-artifact",type=Path,required=True)
    p.add_argument("--donchian-artifact",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    d=load(args.stage_artifact,args.donchian_artifact)
    out=args.out
    out.mkdir(parents=True,exist_ok=True)
    records=[]
    for name,w in WEIGHTS.items():
        returns=d.to_numpy()@np.array(w)
        d[name+"_pct"]=returns
        records.append(dict(portfolio=name,stage18=w[0],stage20=w[1],
                            donchian48=w[2],**score(returns)))
    pd.DataFrame(records).to_csv(out/"portfolio_comparison.csv",index=False)
    d.to_csv(out/"month_by_month.csv",index_label="month_ist")
    # Train on BTC2025 only, then inspect frozen 2026 Jan–Oct.
    best=None
    for a in range(5,91):
        for b in range(5,96-a):
            c=100-a-b
            if c<5: continue
            w=np.array((a,b,c))/100
            r=d[["Stage18","Stage20","48hDonchian"]].to_numpy()@w
            tr=score(r[:12]); objective=(tr["positive"],tr["net_22_pct"])
            if best is None or objective>best[0]:
                best=(objective,(a,b,c),score(r))
    print("TRAIN_2025_SELECTION",best)
    print("PREDECLARED_COMPARISONS",pd.DataFrame(records).to_string(index=False))
    assert (d.loc["2026-09",["Stage18","Stage20","48hDonchian"]]<0).all()
    print("NO_22_MONTH_POSITIVE_STATIC_NONNEGATIVE_BLEND: September 2026 all 3 negative")
if __name__=="__main__":
    main()
