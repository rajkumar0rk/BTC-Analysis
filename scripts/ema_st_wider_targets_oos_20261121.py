#!/usr/bin/env python3
"""Causal 15M/1H Supertrend EMA20 first touch tests at wider 3:1 TP/SL.

Risk/reward tests before financing and slippage; includes trade-level taker
fees + GST and hypothetical maker fees (not guaranteed fills). Separate
2025 and 2026 metrics, no parameter fitted to either split. 1m history and
the same 15m / 1h filtered signals as validated earlier studies.
"""
import json
import sys
from pathlib import Path
import pandas as pd
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from replay_ema_st_15m_entries_1m_exits_20261121 import load
from ema_st_entry_quality_oos_20261121 import aggregate,adx14,all_signals,replay,stats

OUT=ROOT/"analysis"/"ema_st_wider_3r_targets_oos_20261121"
OUT.mkdir(parents=True,exist_ok=True)
PAIRS=((600,200),(900,300),(1200,400),(1500,500),(1800,600),
       (2400,800),(3000,1000),(4500,1500))
GATES=("baseline","atr_ratio_1p2","ADX25","candle_body40","higher_ST")

def main():
    rows=[]
    for asset in ("BTC","ETH"):
        m,b15,manifest=load(asset)
        clock=m.time.to_numpy(np.int64)
        b15["adx14"]=adx14(b15)
        b60=aggregate(m,60)
        b240=aggregate(m,240)
        for tf,mins,bars,higher,hm in (("15m",15,b15,b60,60),("1h",60,b60,b240,240)):
            sig=all_signals(bars,higher,mins,hm,clock)
            print("SIGNALS_WIDE",asset,tf,len(sig),flush=True)
            for gate in GATES:
                for tp,sl in PAIRS:
                    trades=replay(asset,m,sig,gate,tp,sl)
                    d=dict(asset=asset,timeframe=tf,filter=gate,tp=tp,sl=sl,**stats(trades))
                    rows.append(d)
                    print("WIDER_RESULT",json.dumps(d),flush=True)
    f=pd.DataFrame(rows)
    f.to_csv(OUT/"wide_target_grid.csv",index=False)
    suitable=f[(f["2025_trades"]>=20)&(f["2026_trades"]>=20)&
              (f["2025_taker_avg_points"]>0)&(f["2026_taker_avg_points"]>0)]
    cols=["asset","timeframe","filter","tp","sl","trades","TP_first_rate_pct",
          "avg_gross_equiv_points","avg_net_taker_equiv_points",
          "avg_net_maker_equiv_points","avg_hold_minutes",
          "2025_trades","2025_taker_avg_points","2026_trades","2026_taker_avg_points"]
    print("CROSS_YEAR_POSITIVE_TAKER",suitable[cols].to_json(orient="records"),flush=True)
    for asset in ("BTC","ETH"):
        for tf in ("15m","1h"):
            x=f[(f.asset==asset)&(f.timeframe==tf)].sort_values("avg_net_taker_equiv_points",ascending=False).head(8)
            print("WIDE_BEST",asset,tf,x[cols].to_json(orient="records"),flush=True)
            base=f[(f.asset==asset)&(f.timeframe==tf)&(f["filter"]=="baseline")]
            print("WIDE_BASELINE",asset,tf,base[cols].to_json(orient="records"),flush=True)
    print("WIDER_EXIT_REPLAY_COMPLETE",flush=True)

if __name__=="__main__":
    main()
