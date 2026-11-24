#!/usr/bin/env python3
"""Neighboring-slope robustness check for an in-sample 6-bar EMA result.

Reuses EXACT verified BTCUSD 15m / 1m simulation, both profiles and both
intrabar paths. Separately tests 3-12 bar EMA20 slope against 4, 6, 8 controls
and the 16 bar monthly-win candidate; no future data or changes to locked files.
"""
import os,sys
from pathlib import Path
import research_btc15m_atr_monthly_win_slope_robustness_20261124 as parent

parent.SPECS={"S000":("none",0)}
for x in [2,3,4,5,6,7,8,9,10,11,12,14,15,16,17,18,19,20,24]:
    parent.SPECS[f"S{len(parent.SPECS):03d}"]=("slope",x)
parent.OUT=Path("analysis/btc15m_atr_slope_neighbors_20261124")
if __name__=="__main__":
    n=int(os.environ.get("SHARD_COUNT","4"))
    if len(sys.argv)>1 and sys.argv[1]=="aggregate":
        parent.aggregate(n)
    else:
        parent.run(int(os.environ.get("SHARD_INDEX","0")),n)
