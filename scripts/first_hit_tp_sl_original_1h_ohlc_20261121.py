#!/usr/bin/env python3
"""First-touch TP/SL audit on the EXACT old +4298.18 BTC / +6773.09 ETH trade set.

For each historical TRADE recorded by the original 1H-OHLC "inferred" run,
look at actual archived 1m TRADED candles from that trade's entry hour OPEN
up to but excluding its conservatively reported 1H-bar-END exit timestamp.

Independently test two hypothetical symmetric pairs:
 BTCUSD: +100 TP / -100 SL and +200 TP / -200 SL.
 ETHUSD: +0.125% TP / -0.125% SL and +0.25% TP / -0.25% SL,
         using each trade's own entry price (i.e. original BTC-equivalent
         notion 100/200 per 80000 reference entry).

LONG: TP above entry and SL below; SHORT: TP below and SL above.
Earliest 1m observation takes precedence. If TP and SL were both touched
in the FIRST qualifying 1m candle, report "ambiguous_same_1m", NOT an
optimistically invented winner. If neither hit within the original
reported trade lifetime, report "neither_before_reported_exit".

This is a counterfactual FIRST-TOUCH ANALYSIS *WITHIN THE ORIGINAL trade
windows*, NOT a fresh, independently executed fixed-TP/SL strategy. The
original hourly simulator stamped an intrahour fill at that hour's END,
so some prices observed late in that final hour could have occurred
AFTER the unknown actual stop-exit; this materially limits inference.
The original highly profitable hourly path model is not proven executable.

The market-data series is cryptographically validated by earlier source
functions. Original ledger total and reported wallet-based PnL checked.
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
from numba import njit
import backtest_ema_st_1h_trail_1_0p1_20261120 as prior
import backtest_tv_ema_st_1h_27min_20261120 as btc
import backtest_eth_ema_st_1h_27min_20261120 as eth

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"analysis"/"ema_st_1h_all_stops_hourly_1_0p1_20261120"
OUT=ROOT/"analysis"/"original_1h_ohlc_first_tp_vs_sl_20261121"
OUT.mkdir(parents=True,exist_ok=True)
SOURCE_REPORT=json.loads((BASE/"summary.json").read_text())

# result -1: neither, 0: SL-first, 1: TP-first, 2: same-1m ambiguous
@njit(cache=True)
def first_touch(times,op,hi,lo,entry_t,exit_t,entry_px,side,threshold):
    i=int(np.searchsorted(times,entry_t))
    j=int(np.searchsorted(times,exit_t))
    if i>=len(times) or times[i]!=entry_t:
        return -2,-1,-1
    if j<=i:
        return -2,-1,-1
    tp=entry_px+side*threshold
    sl=entry_px-side*threshold
    for k in range(i,j):
        # A 1m OPEN gap is observed before its high/low.
        if side==1:
            if op[k]>=tp:return 1,times[k],k-i
            if op[k]<=sl:return 0,times[k],k-i
            hit_tp=hi[k]>=tp
            hit_sl=lo[k]<=sl
        else:
            if op[k]<=tp:return 1,times[k],k-i
            if op[k]>=sl:return 0,times[k],k-i
            hit_tp=lo[k]<=tp
            hit_sl=hi[k]>=sl
        if hit_tp and hit_sl:return 2,times[k],k-i
        if hit_tp:return 1,times[k],k-i
        if hit_sl:return 0,times[k],k-i
    return -1,-1,-1

def run_asset(asset,module):
    expected=SOURCE_REPORT["assets"][asset]["hourly_results"]["inferred"]
    raw_ledger=pd.read_csv(BASE/f"{asset.lower()}_1h_inferred_trades.csv.gz")
    minute,source=prior.read_minutes(module)
    assert len(raw_ledger)==expected["trade_count"],(asset,len(raw_ledger),expected["trade_count"])
    assert abs(expected["net_usd"]-({"BTC":4298.1778,"ETH":6773.0919}[asset]))<.0001
    times=minute.time.to_numpy(np.int64)
    op=minute.open.to_numpy(np.float64)
    hi=minute.high.to_numpy(np.float64)
    lo=minute.low.to_numpy(np.float64)
    assert len(times)==963360 and (np.diff(times)==60).all()
    n=len(raw_ledger)
    assert raw_ledger.entry_epoch.is_monotonic_increasing
    row=raw_ledger.copy()
    side=np.where(row.side=="LONG",1,-1).astype(np.int8)
    assert all((row.entry_epoch.to_numpy(np.int64)%3600)==0)
    assert all((row.exit_epoch.to_numpy(np.int64)%3600)==0)
    # Original exits labeled at end of the one-hour candle whose
    # underlying true stop time is unknowable.
    assert all(row.exit_epoch.to_numpy(np.int64)>row.entry_epoch.to_numpy(np.int64))
    result={
      "asset":asset,
      "original_1h_inferred_path_net_usd":expected["net_usd"],
      "original_reported_trades":n,
      "original_source":source,
      "first_hit_window":"from original entry_epoch (hourly boundary, traded 1m open) through 1m candle opening before original exit_epoch (hourly bar-end upper bound)",
      "price_data":"archived Delta India PROD 1m traded OHLC",
      "ETH_equivalence":"100 BTC points = 0.125% of per-trade ETH entry; 200 = 0.25%",
      "counts":{},
    }
    for equiv in (100,200):
        amounts=np.full(n,float(equiv)) if asset=="BTC" else row.entry.to_numpy(float)*(equiv/80000.)
        statuses=np.zeros(n,dtype=np.int8)
        when=np.zeros(n,dtype=np.int64)
        minute_offsets=np.zeros(n,dtype=np.int64)
        for idx in range(n):
            status,t,off=first_touch(
                times,op,hi,lo,int(row.entry_epoch.iloc[idx]),
                int(row.exit_epoch.iloc[idx]),float(row.entry.iloc[idx]),
                int(side[idx]),float(amounts[idx]))
            if status==-2:raise RuntimeError(f"Invalid 1m interval {asset} row {idx}")
            statuses[idx]=status
            when[idx]=t
            minute_offsets[idx]=off
        counts={
           "TP_first":int(np.count_nonzero(statuses==1)),
           "SL_first":int(np.count_nonzero(statuses==0)),
           "ambiguous_TP_and_SL_same_first_1m":int(np.count_nonzero(statuses==2)),
           "neither_before_original_reported_exit":int(np.count_nonzero(statuses==-1)),
        }
        assert sum(counts.values())==n
        counts.update({
            "resolved_first_hit_trades":counts["TP_first"]+counts["SL_first"],
            "TP_first_pct_all_original_trades":round(counts["TP_first"]/n*100,2),
            "SL_first_pct_all_original_trades":round(counts["SL_first"]/n*100,2),
            "TP_first_pct_resolved_hits":round(counts["TP_first"]/(counts["TP_first"]+counts["SL_first"])*100,2) if counts["TP_first"]+counts["SL_first"] else None,
            "TP_first_pct_possible_low_bound":round(counts["TP_first"]/n*100,2),
            "TP_first_pct_possible_high_bound":round((counts["TP_first"]+counts["ambiguous_TP_and_SL_same_first_1m"])/n*100,2),
            "TP":f"+{equiv} BTC price points" if asset=="BTC" else f"+{equiv/800:.3f}% of entry",
            "SL":f"-{equiv} BTC price points" if asset=="BTC" else f"-{equiv/800:.3f}% of entry",
        })
        result["counts"][str(equiv)]=counts
        row[f"threshold_{equiv}_native_points"]=amounts
        row[f"first_hit_{equiv}"]=np.array(["TP","SL","BOTH_SAME_1M","NEITHER"],dtype=object)[
            np.select([statuses==1,statuses==0,statuses==2], [0,1,2], default=3)]
        row[f"first_hit_{equiv}_epoch"]=when
        row[f"first_hit_{equiv}_minute_index_since_entry"]=minute_offsets
    row.to_csv(OUT/f"{asset.lower()}_original_trades_first_hit_tp_sl_1m.csv.gz",
               index=False,compression="gzip")
    return result

def test_synthetic():
    # Long TP first, short SL first, first 1m ambiguous, and gap handling.
    t=np.array([0,60,120,180,240],dtype=np.int64)
    o=np.array([100.,100.,100.,100.,100.])
    h=np.array([100.,111.,111.,111.,100.])
    l=np.array([100.,100.,89.,89.,100.])
    assert first_touch(t,o,h,l,0,240,100.,1,10.)[0]==1
    assert first_touch(t,o,h,l,0,240,100.,-1,10.)[0]==0
    assert first_touch(t,o,h,l,120,180,100.,1,10.)[0]==2
    assert first_touch(t,o,h,l,180,240,100.,-1,10.)[0]==2

def main():
    test_synthetic()
    results={"source":"original 1H-OHLC inferred-path reported profits +4298.1778 BTC and +6773.0919 ETH",
      "date_start":"2025-01-01 UTC","date_end_exclusive":"2026-11-01 UTC",
      "method":"Compare TP and SL first-touch order on actual 1m traded candles, confined to historical original inferred-path trade windows.",
      "warning":"These counts DO NOT represent an independent fixed TP/SL backtest. Original simulated exit times are one-hour bar-end placeholders; after-exit movements inside the final hour may contaminate first-touch result. Same-1m TP/SL order is unknown. Historical actual execution costs, liquidity, liquidation and fills not validated.",
      "assets":{}}
    for asset,mod in (("BTC",btc),("ETH",eth)):
        print("ORIGINAL_1H_TRADE_FIRST_HIT_SCAN",asset,flush=True)
        results["assets"][asset]=run_asset(asset,mod)
        print("FIRST_HIT_COUNTS",json.dumps(results["assets"][asset]["counts"]),flush=True)
    (OUT/"summary.json").write_text(json.dumps(results,indent=2)+"\n")
    print("FIRST_HIT_100_200_COMPLETE",flush=True)

if __name__=="__main__":main()
