#!/usr/bin/env python3
"""Exact after-cost profit-factor audit of ETH 4H Engulfing Reversal,
using the unchanged original study's data, signals, and execution engine.
No strategy parameters, historical scripts, or scheduled jobs are changed.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from eth_native_crossfamily_v2 import (
    load,aggregate,signal_library,replay,summarize,
    RISK,CAP,ETH_SLIP,FEE
)

def main():
    eth=load("ETHUSD")
    btc=load("BTCUSD")
    if not eth.index.equals(btc.index):
        raise AssertionError("BTC and ETH timeline misalignment")
    prices=eth.open.to_numpy(float)
    h=eth.high.to_numpy(float)
    l=eth.low.to_numpy(float)
    c=eth.close.to_numpy(float)
    ist=eth.index.tz_convert("Asia/Kolkata")
    month_codes=np.array(ist.year*100+ist.month,dtype=np.int32)
    intervals={n:aggregate(eth,n) for n in ("5min","15min","1h","4h")}
    label="4h:engulfing_reversal"
    b,long,short=signal_library(intervals)[label]
    idx0=np.r_[np.flatnonzero(long.to_numpy(bool)),
        np.flatnonzero(short.to_numpy(bool))]
    sides=np.r_[np.ones(int(long.sum()),np.int32),
        -np.ones(int(short.sum()),np.int32)]
    k=eth.index.get_indexer(b.index[idx0])
    valid=(k>=0)&(k<len(c))
    idx0=idx0[valid]
    sides=sides[valid]
    k=k[valid]
    order=np.lexsort((-sides,k))
    k=k[order];sides=sides[order];idx0=idx0[order]
    if len(k):
        unique=np.r_[True,np.diff(k)!=0]
        k=k[unique];sides=sides[unique];idx0=idx0[unique]
    stopbase=b.atr.to_numpy(float)[idx0]
    results=[]
    for stop_mult,target_R in ((1.5,3.),(2.5,2.)):
        ledger=replay(prices,h,l,c,month_codes,
            k,sides,stopbase,target_R,4320,stop_mult,
            RISK,CAP,ETH_SLIP,FEE)
        model=f"{label}__SL{stop_mult:g}_RR{target_R:g}"
        pnl=ledger[:,6]
        win_sum=float(pnl[pnl>0].sum())
        loss_sum=float(-pnl[pnl<0].sum())
        pf=win_sum/loss_sum if loss_sum>0 else None
        summary,monthly=summarize(ledger,month_codes,{"model":model})
        output=dict(model=model,profit_factor_after_costs=pf,
            gross_profit_sum_winning_trades_usd=win_sum,
            gross_loss_abs_sum_losing_trades_usd=loss_sum,
            net_pnl_total_usd=float(pnl.sum()),
            total_trades=int(len(pnl)),
            win_trades=int((pnl>0).sum()),
            losing_trades=int((pnl<0).sum()),
            final_equity_usd=float(ledger[-1,7]),
            monthly_positive_2025=summary["positive2025"],
            monthly_positive_2026=summary["positive2026"],
            original_replay_fee_per_side=.0005,
            GST_on_exchange_fees=.18,
            ETH_slippage_points_per_side=float(ETH_SLIP),
            funding_and_actual_spread_included=False)
        results.append(output)
        # Fail closed on any changed model/data or runner semantics.
        expected={ (1.5,3.):(190,78,112,1160.8518786823975),
                  (2.5,2.):(166,82,84,1108.9027039295154)}[(stop_mult,target_R)]
        if (output["total_trades"],output["win_trades"],output["losing_trades"]) != expected[:3]:
            raise AssertionError("Trade counts don't reconcile with existing reported ETH backtest")
        if abs(output["final_equity_usd"]-expected[3])>0.01:
            raise AssertionError("Equity doesn't reconcile with reported backtest")
        print("ETH_ENGULFING_PF",json.dumps(output),flush=True)
    path=Path("analysis/eth_native_crossfamily_v2/engulfing_profit_factor_audit.json")
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps({
        "study":"ETH native cross-family v2 original-code exact replay",
        "instrument":"ETHUSD",
        "results":results,
        "formula":"Sum of positive net trade USD PnL divided by absolute sum of negative net trade USD PnL",
        "limitation":"Fees+GST+nominal slippage included, real spread/funding/impact not included. Source data begins Jan1 2025 UTC, leaving 2025 Jan 1 00:00-05:29 IST absent."
    },indent=2)+"\n")

if __name__=="__main__":
    main()
