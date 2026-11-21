#!/usr/bin/env python3
"""Concentration, monthly and cost sensitivity audit for selected 22-month BTC/ETH
1H volume/ATR expansion filtered entry strategies. SAME replay engine/archives.

Extra modeled slippage is a *notional-cost stress test*, not true intraminute
fill reconstruction. Real funding/PM margin liquidation not modeled.
"""
from __future__ import annotations
import json
from pathlib import Path
import pandas as pd
import numpy as np
from volume_volatility_entry_filter_full22_20261121 import (
  data_arrays,indicator_signal_ratios,apply_filter,replay,ledger_frame,get_summary,MONTHS,OUT as GRID_OUT
)
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"analysis"/"filter_candidate_cost_monthly_audit_20261121"
OUT.mkdir(parents=True,exist_ok=True)
CASES={
 "BTC":[
   ("unfiltered_BTC_1500_1p5",1500.,1.5,0.,0.,None,None),
   ("atr_expansion_1p25",1500.,1.5,0.,1.25,None,None),
   ("volume_0p75_and_atr_1p25",1500.,1.5,.75,1.25,None,None)
 ],
 "ETH":[
   ("unfiltered_ETH_4000_2",4000.,2.,0.,0.,None,None),
   ("high_volume_2p5_atr_0p75",4000.,2.,2.5,.75,None,None),
   ("high_volume_2p5_atr_1p0",4000.,2.,2.5,1.,None,None),
   ("balanced_volume_1p25_atr_1p0",4000.,1.5,1.25,1.,None,None)
 ]
}
def summary_with_stress(df):
    d={}
    for bps in (0.,2.,5.,10.):
        f=df.copy()
        if len(f):
            extra=(f.entry_price+f.exit_price_proxy)*f.quantity*(bps/10000.)
            f["net_usd"]=f.net_usd-extra
        full=get_summary(f,MONTHS)
        train=get_summary(f,MONTHS[:12])
        holdout=get_summary(f,MONTHS[12:])
        d[str(bps)]={ 
           "full_22_net_usd":full["net_usd"],
           "full_22_pf":full["profit_factor"],
           "full_22_positive_months":full["positive_months"],
           "full_22_max_closed_trade_drawdown_usd":full["max_closed_trade_drawdown_usd"],
           "2025_net_usd":train["net_usd"],
           "2026_jan_oct_net_usd":holdout["net_usd"],
        }
    return d

def concentration(df):
    n=len(df)
    nets=df.net_usd.to_numpy(dtype=float)
    upside=np.sort(nets[nets>0])[::-1]
    return {
       "completed_trades":n,
       "largest_profit_usd":float(np.max(nets)) if n else None,
       "largest_loss_usd":float(np.min(nets)) if n else None,
       "sum_top_3_winners_usd":round(float(upside[:3].sum()),4),
       "sum_top_5_winners_usd":round(float(upside[:5].sum()),4),
       "net_without_largest_win_usd":round(float(nets.sum()-(upside[0] if len(upside) else 0)),4),
       "net_without_top_3_winners_usd":round(float(nets.sum()-upside[:3].sum()),4),
       "avg_net_per_trade_usd":round(float(nets.mean()),4) if n else None,
       "exit_reasons":df.exit_reason.value_counts().to_dict() if n else {},
       "long_net_usd":round(float(df.loc[df.side=="LONG","net_usd"].sum()),4) if n else None,
       "short_net_usd":round(float(df.loc[df.side=="SHORT","net_usd"].sum()),4) if n else None,
       "long_trades":int((df.side=="LONG").sum()) if n else 0,
       "short_trades":int((df.side=="SHORT").sum()) if n else 0,
    }

def main():
    root={
      "period":"2025-01 through 2026-10, UTC; 22 complete months",
      "venue":"Delta India production 1m traded + MARK OHLC history, same 1H signal and ATR stop as grid",
      "fees":"baseline includes 0.05% taker fee EACH side + 18% GST on fee",
      "slippage_stress":"ADD bps/10000 * (entry_notional + exit_notional); each side notional-cost approximation, not actual fill/slippage",
      "excluded":"funding, bid/ask path, actual fills, latency, PM liquidation, unfunded $100 wallet",
      "scenarios":{}
    }
    for asset,cfgs in CASES.items():
        args,provenance=data_arrays(asset)
        indices,vr,ar,_=indicator_signal_ratios(asset,args)
        for name,activation,mult,vol_min,atr_min,vol_max,atr_max in cfgs:
            filtered,passed=apply_filter(args,indices,vr,ar,vol_min,atr_min,vol_max,atr_max)
            for price,price_id in (("MARK",0),("TRADED",1)):
                records,skips,open_at_end=replay(*filtered,activation,mult,int(asset=="ETH"),0,price_id)
                df=ledger_frame(records)
                key=f"{asset.lower()}_{name}_{price.lower()}"
                full=get_summary(df,MONTHS)
                root["scenarios"][key]={
                  "asset":asset,"preset":name,"profit_source":price,
                  "activation":activation,"atr_tp_multiplier":mult,
                  "volume_ratio_min":vol_min,"atr_expansion_min":atr_min,
                  "passed_entry_signals":passed,
                  "monthly":full["monthly"],
                  "cost_sensitivity":summary_with_stress(df),
                  "concentration":concentration(df),
                  "open_at_end":bool(open_at_end[0]),
                }
                pd.DataFrame([{"month_utc":m,**vals} for m,vals in full["monthly"].items()]).to_csv(
                    OUT/f"{key}_monthly.csv",index=False)
                df.to_csv(OUT/f"{key}_trades.csv.gz",index=False,compression="gzip")
                print("FILTER_AUDIT",key,json.dumps({
                   "net":full["net_usd"],"pf":full["profit_factor"],
                   "positive_months":full["positive_months"],
                   "2025":root["scenarios"][key]["cost_sensitivity"]["0.0"]["2025_net_usd"],
                   "2026":root["scenarios"][key]["cost_sensitivity"]["0.0"]["2026_jan_oct_net_usd"],
                   "cost5bps":root["scenarios"][key]["cost_sensitivity"]["5.0"]["full_22_net_usd"],
                   "max_win":root["scenarios"][key]["concentration"]["largest_profit_usd"],
                }),flush=True)
        del args
    (OUT/"summary.json").write_text(json.dumps(root,indent=2)+"\n")
    print("VOLUME_FILTER_COST_AUDIT_PASS",OUT,flush=True)

if __name__=="__main__":
    main()
