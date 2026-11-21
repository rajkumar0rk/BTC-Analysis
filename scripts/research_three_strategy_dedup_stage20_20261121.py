#!/usr/bin/env python3
"""Deduplicated Stage18 + (Stage20 EXTRA signals only) + 48H Donchian.
All data comes from archived BTC-Analysis backtests. MONTHLY research only.
Assumes Stage18's full component returns, and removes repeated Stage15 core
from Stage20 by keeping only its d20 and 1h momentum components.
"""
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
from research_three_strategy_monthly_portfolio_20261121 import load,score

D55="1D_channel_55_ema50_agrees_trail_3atr"
D20="1D_channel_20_no_trend_filter_trail_3atr"
HOURLY="strong_momentum_6h__4h_adx_le20__3R__480min"

def source(path, model, field, months):
    r=pd.read_csv(path)
    r=r[r.model==model].copy()
    s=r.set_index("month_ist")[field].reindex(months)
    if len(s)!=22 or s.isna().any():
        raise AssertionError("Source monthly model or months missing: "+model)
    return s.to_numpy(float)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--stage-artifact",type=Path,required=True)
    p.add_argument("--donchian-artifact",type=Path,required=True)
    p.add_argument("--daily-monthly",type=Path,required=True,
                   help="analysis/institutional_discovery_stage17_swing_breakout/monthly_mark_to_market.csv")
    p.add_argument("--hourly-monthly",type=Path,required=True,
                   help="analysis/institutional_discovery_stage19_new_1h_patterns/monthly_results.csv")
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    d=load(args.stage_artifact,args.donchian_artifact)
    months=list(d.index)
    d55=source(args.daily_monthly,D55,"month_return_pct",months)
    d20=source(args.daily_monthly,D20,"month_return_pct",months)
    h1=source(args.hourly_monthly,HOURLY,"modeled_return_pct",months)
    core=(d.Stage18.to_numpy(float)-.25*d55)/.75
    reconstructed_stage20=.9*(.75*core+.25*d20)+.1*h1
    if np.max(np.abs(reconstructed_stage20-d.Stage20.to_numpy(float)))>1e-4:
        raise AssertionError("Stage20 archived result is not reconciled")
    # Original Stage20 has 67.5% core, 22.5% D20 and 10% H1.
    # Remove its duplicate core, then proportionally normalize its EXTRA
    # components: 22.5% / 32.5% D20, 10% / 32.5% H1.
    additional=(.225*d20+.10*h1)/.325
    # Capital: 50% Stage18, 20% Stage20-extra ONLY, 30% 48H Donchian.
    dedup=.5*d.Stage18.to_numpy(float)+.2*additional+.3*d["48hDonchian"].to_numpy(float)
    d["stage20_extra_only"]=additional
    d["dedup_50_20_30_month_pct"]=dedup
    assert len(d)==22
    args.out.mkdir(parents=True,exist_ok=True)
    d.to_csv(args.out/"deduplicated_monthly_returns.csv",index_label="month_ist")
    print("DEDUP_MONTHLY_RESULT",score(dedup))
    print("CORE_RECONCILIATION_MAX_ERROR",float(np.max(np.abs(reconstructed_stage20-d.Stage20.to_numpy(float)))))
    print("NEGATIVE_MONTHS",d.index[dedup<0].tolist())

if __name__=="__main__":main()
