#!/usr/bin/env python3
"""Sensitivity audit of the discovered ETH long-only slow-trend Donchian48.

Historical exploratory candidate selected after examining the earlier grid:
NOT an unbiased holdout or proof of generalization. Uses the identical
signal, minute exit, funding proxy and fee components as the parent runner.
"""
from pathlib import Path
import json,sys
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from replay_ema_st_15m_entries_1m_exits_20261121 import load
from research_new_4h15m_breakout_1m_20261121 import (
    prepare,generate_signals,funding_proxy,replay,evaluate,NOTIONAL)
OUT=ROOT/"analysis"/"eth_long_breakout_stress_audit_20261121"
OUT.mkdir(parents=True,exist_ok=True)

def main():
    m,_,_=load("ETH")
    b15,b4=prepare(m)
    all_signals=generate_signals(m,b15,b4)
    key=("slow_50_200","donchian48")
    picks=[x for x in all_signals[key] if x[1]==1]
    assert len(picks)>100
    fc,mc,proof=funding_proxy("ETH",m)
    allstats={}
    ledgers=[]
    for bps in (0,1,2,3,5,8):
        slips=bps/10000.
        trades=replay("ETH",m,{key:picks},(*key,"trail_2atr"),fc,mc,slips)
        assert trades.side.eq("LONG").all()
        stats=evaluate(trades)
        a=trades.net_taker_usd.to_numpy()
        # Count positive months including zero-trade months for a 22-month panel.
        monthly=(trades.groupby("exit_month_utc").net_taker_usd.sum()
                 .reindex(pd.period_range("2025-01","2026-10",freq="M").astype(str),fill_value=0.))
        stats["active_months"]=int((monthly!=0).sum())
        stats["positive_months"]=int((monthly>0).sum())
        stats["negative_months"]=int((monthly<0).sum())
        stats["zero_months"]=int((monthly==0).sum())
        stats["monthly_net"]=dict(zip(monthly.index,monthly.round(3).tolist()))
        stats["top1_net"]=round(float(np.max(a)),4)
        stats["top5_net_total"]=round(float(np.sort(a)[-5:].sum()),4)
        stats["median_trade_net"]=round(float(np.median(a)),4)
        stats["total_net_excluding_top5"]=round(float(a.sum()-np.sort(a)[-5:].sum()),4)
        stats["sum_fees_gst"]=round(float(trades.fees_and_gst_usd.sum()),3)
        stats["sum_gross"]=round(float(trades.gross_usd.sum()),3)
        stats["average_initial_risk_pct"]=round(float((trades.initial_risk_points/trades.entry).mean()*100),3)
        stats["max_holding_minutes"]=int(trades.hold_min.max())
        stats["max_adverse_gap_entry_exit_usd"]=None
        allstats[str(bps)+"bps_per_side"]=stats
        trades["slip_bps"]=bps
        ledgers.append(trades)
        small={"slip_bps":bps,"trades":stats["trades"],
            "net_usd":stats["all"]["net_usd"],
            "funded_net_usd":stats["funding_proxy_all"]["net_usd"],
            "PF":stats["all"]["profit_factor"],
            "2025":stats["annual"]["2025"]["taker"]["net_usd"],
            "2026":stats["annual"]["2026"]["taker"]["net_usd"],
            "months_pos":stats["positive_months"],
            "months_neg":stats["negative_months"],
            "months_zero":stats["zero_months"],
            "top5_net_sum":stats["top5_net_total"],
            "total_without_top5":stats["total_net_excluding_top5"]}
        print("ETH_LONG_STRESS",json.dumps(small),flush=True)
    df=pd.concat(ledgers,ignore_index=True)
    df.to_csv(OUT/"trade_ledger.csv.gz",compression="gzip",index=False)
    (OUT/"summary.json").write_text(json.dumps({
        "audited_candidate":"ETH 4H EMA50/200 trend + 15M Donchian48 confirmed breakout LONG only + 1M ATR chandelier trailing",
        "costs":"0.05% taker each side + 18% GST, scenarios per-side additional adverse price slippage",
        "funding":"observed prior-hour rate snapshots at assumed 00/08/16 UTC payments; not actual settlement",
        "notional":"fixed $1000 USD per trade, no compounding, no real margin/liquidation backtest",
        "critical_limitation":"Exploratory historical candidate chosen after reviewing full sample; requires genuinely unseen forward trades",
        "funding_source":proof,"results":allstats},indent=2)+"\n")
    print("ETH_LONG_AUDIT_COMPLETED",str(OUT),flush=True)

if __name__=="__main__":
    main()
