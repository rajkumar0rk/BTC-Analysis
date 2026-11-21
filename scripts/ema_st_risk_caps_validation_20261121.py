#!/usr/bin/env python3
"""Validate promising EMA20+ST modifications under tighter risk policies.

Uses the SAME modified entry+1M engine as replay_modified_ema_st_20261121.py.
Compares raw ST/ATR stops, caps at % of entry, and skips high-risk signals.
This is critical for small isolated margin and 100x scenarios: mere historical
stop hits do not guarantee survival before mark-price liquidation.

Costs include 0.05% taker each side, GST 18%, one adverse native tick each
side. Hypothetical all-adverse 0.01% funding per eight-hour interval and extra
ticks are only sensitivity scenarios, NOT historical funding.
"""
import json,sys,math
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from replay_ema_st_15m_entries_1m_exits_20261121 import load
from ema_st_entry_quality_oos_20261121 import aggregate,adx14,all_signals
from replay_modified_ema_st_20261121 import core,MODES,FEERATE,GST,ENTRY_CUTOFF

OUT=ROOT/"analysis"/"ema_st_modified_risk_caps_20261121"
OUT.mkdir(parents=True,exist_ok=True)
CANDIDATES=(
 ("BTC","15m","atr_ratio_1p2","STline50_trail_2R_1R"),
 ("ETH","1h","candle_body40","STline50_trail_2R_1R_flip"),
 ("ETH","15m","candle_body40","STline50_TP3R"),
 ("ETH","1h","candle_body40","ATR2_trail_2R_1R_BE1R"),
)
SCENARIOS=(
 ("uncapped","raw",0.),
 ("cap_0p50pct","cap",0.005),
 ("cap_0p75pct","cap",0.0075),
 ("cap_1p00pct","cap",0.01),
 ("skip_over_0p50pct","skip",0.005),
 ("skip_over_0p75pct","skip",0.0075),
 ("skip_over_1p00pct","skip",0.01),
)
def report(output,asset,tf,gate,mode,scenario,m,rate=0.0001):
    ei,xi,ep,xp,side,risk,reason,fee,net,amb,bigrisk,skipped,entered,openpos=output
    qty=0.001 if asset=="BTC" else 0.01
    tick=0.5 if asset=="BTC" else 0.05
    start=pd.to_datetime(m.time.iloc[ei].to_numpy(),unit="s",utc=True)
    end=pd.to_datetime(m.time.iloc[xi].to_numpy(),unit="s",utc=True)
    mon=end.tz_convert("Asia/Kolkata").strftime("%Y-%m")
    years=start.year.to_numpy()
    # Approximate adverse funding settled at most once per 8h; ceil is
    # intentionally conservative and DOES NOT replicate settlement schedule.
    funding_intervals=np.ceil((xi-ei)/480.)
    funding_cost=funding_intervals*rate*ep*qty
    norm=net/(qty)*(1.0 if asset=="BTC" else 80000.0/ep)
    with_funding=net-funding_cost
    more_slippage=net-4*tick*qty # 2 extra adverse ticks per side
    z={"asset":asset,"timeframe":tf,"filter":gate,"exit":mode,"risk_policy":scenario,
       "closed_trades":len(net),"unresolved_trades":openpos,
       "initial_stop_too_wide_for_100x_proxy_count":bigrisk,
       "stop_target_same_1m_ambiguity":amb,
       "ignored_signals_while_position_open":skipped,
       "net_usd_one_contract":round(float(np.sum(net)),4),
       "mean_btc_equiv_points":round(float(np.mean(norm)),2) if len(net) else None,
       "net_usd_with_hypothetical_adverse_funding_0p01pct_per8h":round(float(np.sum(with_funding)),4),
       "net_usd_with_extra_2_ticks_each_side":round(float(np.sum(more_slippage)),4),
       "fees_and_gst_usd_one_contract":round(float(np.sum(fee)),4),
       "avg_hold_min":round(float(np.mean(xi-ei)),1) if len(ei) else None,
       "median_hold_min":round(float(np.median(xi-ei)),1) if len(ei) else None,
       "max_stop_pct":round(float(np.max(risk/ep)*100),3) if len(ep) else 0,
       "mean_stop_pct":round(float(np.mean(risk/ep)*100),3) if len(ep) else 0,
       "min_single_trade_net_usd":round(float(np.min(net)),3) if len(ep) else 0}
    if len(net):
        gain=float(np.sum(net[net>0]));loss=float(-np.sum(net[net<0]))
        z["profit_factor_net"]=round(gain/loss,3) if loss else None
        curve=np.cumsum(net);peak=np.maximum.accumulate(np.r_[0,curve])[1:]
        z["max_closed_trade_drawdown_usd_one_contract"]=round(float(np.max(peak-curve)),3)
        mx=pd.DataFrame({"month":mon,"pnl":net}).groupby("month").pnl.sum()
        z["profitable_months"]=int((mx>0).sum())
        z["losing_months"]=int((mx<0).sum())
        z["flat_months"]=22-z["profitable_months"]-z["losing_months"]
        z["monthly_net_usd"]={str(k):round(float(v),3) for k,v in mx.items()}
    for y in (2025,2026):
        ynet=net[years==y]
        z[f"{y}_trades"]=len(ynet)
        z[f"{y}_net_usd_one_contract"]=round(float(np.sum(ynet)),3)
        z[f"{y}_net_usd_with_funding_sensitivity"]=round(float(np.sum(with_funding[years==y])),3)
        z[f"{y}_net_usd_with_extra_slippage"]=round(float(np.sum(more_slippage[years==y])),3)
    return z

def main():
    reports=[]
    modes={t[0]:t for t in MODES}
    for asset in ("BTC","ETH"):
        m,b15,manifest=load(asset)
        b15["adx14"]=adx14(b15)
        b60=aggregate(m,60)
        b240=aggregate(m,240)
        o=m.open.to_numpy(float)
        h=m.high.to_numpy(float);l=m.low.to_numpy(float);c=m.close.to_numpy(float)
        t=m.time.to_numpy(np.int64)
        tick=0.5 if asset=="BTC" else 0.05
        qty=0.001 if asset=="BTC" else 0.01
        for tf,mins,bars,higher,hm in (("15m",15,b15,b60,60),("1h",60,b60,b240,240)):
            chosen=[x for x in CANDIDATES if x[0]==asset and x[1]==tf]
            if not chosen:continue
            sigrows=all_signals(bars,higher,mins,hm,t)
            ar=np.zeros(len(m));st=np.zeros(len(m));flips=np.zeros(len(m),np.int8)
            a=bars.atr14.to_numpy(float)
            s=bars.st.to_numpy(float)
            d=bars.dir.to_numpy(np.int8)
            for i in range(36,len(bars)-1):
                j=(i+1)*mins
                ar[j]=a[i];st[j]=s[i]
                if d[i]!=d[i-1]:flips[j]=d[i]
            for _,_,gate,name in chosen:
                nm,stopkind,stoparg,tr,be,act,dist,flip=modes[name]
                for label,policy,cap in SCENARIOS:
                    signals=np.zeros(len(m),dtype=np.int8)
                    skipped_for_risk=0
                    for j,side,gates in sigrows:
                        if not gates[gate]:continue
                        ep=o[j]+side*tick
                        if stopkind==0:risk=stoparg*(1. if asset=="BTC" else ep/80000.)
                        elif stopkind==1:risk=stoparg*ar[j]
                        else:risk=side*(ep-(st[j]-side*stoparg*(1. if asset=="BTC" else ep/80000.)))
                        if policy=="skip" and risk>cap*ep:
                            skipped_for_risk+=1
                            continue
                        signals[j]=side
                    nmax=int(np.count_nonzero(signals))+1
                    result=core(o,h,l,c,t,signals,ar,st,flips,asset=="ETH",
                        stopkind,stoparg,tr,be,act,dist,flip,tick,qty,
                        FEERATE,GST,ENTRY_CUTOFF,nmax,
                        cap if policy=="cap" else 0.)
                    row=report(result,asset,tf,gate,name,label,m)
                    row["skipped_entries_for_risk"]=skipped_for_risk
                    reports.append(row)
                    print("RISK_AUDIT_RESULT",json.dumps(row),flush=True)
    (OUT/"risk_audit_results.json").write_text(json.dumps(reports,indent=2)+"\n")
    tab=pd.DataFrame([{k:v for k,v in x.items() if k!="monthly_net_usd"} for x in reports])
    tab.to_csv(OUT/"risk_audit_summary.csv",index=False)
    for row in reports:
        if row["risk_policy"] in ("uncapped","cap_0p50pct","skip_over_0p50pct"):
            compact={k:v for k,v in row.items() if k!="monthly_net_usd"}
            print("RISK_AUDIT_HIGHLIGHT",json.dumps(compact),flush=True)
    print("RISK_AUDIT_COMPLETE",len(reports),flush=True)

if __name__=="__main__":
    main()
