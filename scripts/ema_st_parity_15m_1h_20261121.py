#!/usr/bin/env python3
"""Parity validation: SAME modified EMA20+Supertrend 15M vs 1H.

The existing, fully confirmed EMA20 reclaim / ST10,3 entry is preserved.
Only chart timeframe changes: all parameters are otherwise matched.

- Directional entry candle body >= 40% of its high-low range
- Baseline confirmed ATR expansion >= 1x, volume ratio >= 1.5x
- Initial stop: 2x ATR(14), optionally capped at 1% of entry
- Breakeven activation: 1R (includes estimated fees + GST)
- Trailing activation: 2R, distance 1R
- 1m candle-based exits, old protective stop priority and next-minute
  activation of new trailing levels; position-exclusive
- Dates: Jan 2025 to Oct 2026, settle open positions with later 1m archive
- 0.05% taker each side +18% GST, 1 native tick adverse entry and exit
- No funding, historical spread, liquidation, portfolio collateral effects
Research-only. No production trade or main branch mutation.
"""
import json,sys
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from replay_ema_st_15m_entries_1m_exits_20261121 import load
from ema_st_entry_quality_oos_20261121 import aggregate,adx14,all_signals
from replay_modified_ema_st_20261121 import core,MODES,FEERATE,GST,ENTRY_CUTOFF
from ema_st_risk_caps_validation_20261121 import report

OUT=ROOT/"analysis"/"ema_st_parity_15m_1h_1pct_20261121"
OUT.mkdir(parents=True,exist_ok=True)
GATES=("candle_body40",)
MODENAMES=("ATR2_trail_2R_1R_BE1R","STline50_trail_2R_1R")
STOP_CAPS=(("uncapped",0.0),("cap_0p50pct",0.005),("cap_0p75pct",0.0075),("cap_1p00pct",0.01))
def run():
    modes={m[0]:m for m in MODES}
    output=[]
    for asset in ("BTC","ETH"):
        minute,b15,manifest=load(asset)
        b15["adx14"]=adx14(b15)
        b60=aggregate(minute,60)
        b240=aggregate(minute,240)
        op=minute.open.to_numpy(float)
        hi=minute.high.to_numpy(float)
        lo=minute.low.to_numpy(float)
        cl=minute.close.to_numpy(float)
        clock=minute.time.to_numpy(np.int64)
        tick=.5 if asset=="BTC" else .05
        qty=.001 if asset=="BTC" else .01
        for timeframe,tfmins,bars,higher,highermins in (
            ("15m",15,b15,b60,60),("1h",60,b60,b240,240)):
            entryrows=all_signals(bars,higher,tfmins,highermins,clock)
            ar=np.zeros(len(minute),dtype=float)
            st=np.zeros(len(minute),dtype=float)
            flip=np.zeros(len(minute),dtype=np.int8)
            av=bars.atr14.to_numpy(float)
            sv=bars.st.to_numpy(float)
            dv=bars.dir.to_numpy(np.int8)
            for i in range(36,len(bars)-1):
                idx=(i+1)*tfmins
                ar[idx]=av[i]
                st[idx]=sv[i]
                if dv[i]!=dv[i-1]:flip[idx]=dv[i]
            for gate in GATES:
                sig=np.zeros(len(minute),dtype=np.int8)
                for j,side,flags in entryrows:
                    if flags[gate]:sig[j]=side
                for modename in MODENAMES:
                    name,sk,sa,tp,be,act,dist,flip_exit=modes[modename]
                    for capname,cap in STOP_CAPS:
                        params=dict(
                            op=op,hi=hi,lo=lo,cl=cl,clock=clock,signal=sig,
                            atr_st=ar,st_line=st,flipdir=flip,
                            asset_eth=asset=="ETH",stopkind=sk,stoparg=sa,
                            profit_r=tp,be_r=be,activation_r=act,
                            distance_r=dist,use_flip=flip_exit,tick=tick,qty=qty,
                            fee_rate=FEERATE,gst=GST,entry_cutoff=ENTRY_CUTOFF,
                            maxtrades=int(np.count_nonzero(sig))+1,
                            max_risk_fraction=cap)
                        res=core(**params)
                        info=report(res,asset,timeframe,gate,name,capname,minute)
                        output.append(info)
                        print("TIMEFRAME_PARITY_RESULT",json.dumps({
                           k:v for k,v in info.items() if k!="monthly_net_usd"}),flush=True)
    (OUT/"full_results.json").write_text(json.dumps(output,indent=2)+"\n")
    df=pd.DataFrame([{k:v for k,v in item.items() if k!="monthly_net_usd"} for item in output])
    df.to_csv(OUT/"summary.csv",index=False)
    print("TIMEFRAME_PARITY_COMPLETE",len(output),flush=True)

if __name__=="__main__":
    run()
