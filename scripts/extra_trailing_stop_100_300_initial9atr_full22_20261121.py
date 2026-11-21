#!/usr/bin/env python3
"""22 complete months: activation 100 / EXTRA Trailing Stop Points 300.

USER SETTINGS, 2026-11-21:
   Enable Trailing Stop: ON
   Enable Additional Trailing Stop Points: ON, 300 BTC-equivalent points
   Activation Points: 100 BTC-equivalent points
   Enable Fixed Trailing Distance (Fixed Points): OFF
   Initial protective stop: 9 * ATR(14) on completed 1H signal candle
   Volume filter: OFF; volatility filter: OFF
   Trend indicator: 1H EMA20 + Supertrend(10,3), 1H opposite-ST flip exit ON
   Price monitoring / stop edits: completed 1M MARK or 1M TRADED OHLC,
                                  with adjustment effective NEXT 1M bar.
Exact original additional Trailing Stop Points implementation reused,
NOT fixed trailing distance, NOT hourly profit close ATR trail.

Candles: archived Delta India production 1m trade + MARK Jan2025-Oct2026,
NOV2026 partial explicitly excluded. Modeled 1m triggering can cross stop
within 1m; estimated fill same traded 1m CLOSE. Not historical fill data.
Regular fees 0.05% EACH side plus GST18%; no funding / actual spread /
liquidation / orderbook / latency. Fixed ~$1000 notional reference strategy,
NOT an executable $100 account without risk of margin exhaustion.

Read-only research branch; no production bot or exchange orders.
"""
from __future__ import annotations
import json
import math
from pathlib import Path
import numpy as np
import pandas as pd
from optimize_1h_additional_trailing_stop_points_20261121 import (
    compute,point_scale,stop_round,prepare,frame_rows,metrics,month_table,checks,MONTHS
)

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"analysis"/"extra_trailing_stop_100_300_initial9atr_full22_20261121"
OUT.mkdir(parents=True,exist_ok=True)
COMPLETE=MONTHS[:22]
ACTIVATION_POINTS=100.
TRAIL_STOP_POINTS=300.
INIT_ATR14_MULT=9.
# Signal-map stopdist is already 2xATR(14); scaling by 9/2 preserves
# exact same bar/ATR definition and the tick-rounded initial-stop placement.
EXISTING_SIGNAL_STOP_ATR_MULT=2.
INIT_STOP_SCALE=INIT_ATR14_MULT/EXISTING_SIGNAL_STOP_ATR_MULT

def unit_tests():
    checks()
    # Source 1H stopdist = 2x ATR. New emergency stop = 9x ATR.
    # For LONG, round UP stop price by tick, SHORT round DOWN as in repo.
    ep=60000.;src_stopdist=200.
    assert stop_round(ep-INIT_STOP_SCALE*src_stopdist,.5,1)==59100.
    assert stop_round(ep+INIT_STOP_SCALE*src_stopdist,.5,-1)==60900.
    # After a LONG advances >=100, candidate stop is best-300.
    # This is an ADDITIONAL STOP, not fixed trailing distance and does NOT
    # necessarily lock a profit immediately (the candidate can be below entry).
    long_entry=60000.
    best=60150.
    prev_stop=59100.
    candidate=stop_round(best-300.,.5,1)
    assert candidate==59850. and max(prev_stop,candidate)==59850.
    assert point_scale(100.,1600.,.05,1)==2.
    assert point_scale(300.,1600.,.05,1)==6.
    assert max(prev_stop,candidate)<long_entry

def costs_and_summary(trades,months):
    return metrics(trades,months)

def main():
    unit_tests()
    report={
       "title":"Activation 100 and EXTRA Trailing Stop Points 300, initial stop 9x ATR14",
       "start_utc":"2025-01-01T00:00:00Z",
       "end_exclusive_utc":"2026-11-01T00:00:00Z",
       "monthly_timezone":"UTC",
       "months_complete":22,
       "signal":"1H EMA20 touch/reclaim in continuing Supertrend10,3, original bidirectional signals",
       "entry_filters":{"volume":False,"volatility":False},
       "initial_stop":{"type":"ATR(14)","multiplier":INIT_ATR14_MULT,
           "monitoring":"1M MARK or traded depending on scenario",
           "note":"One shared stop updated only to tighter level; original initial protection stays until trailing stop tightens"},
       "additional_trailing_stop":{"enabled":True,"activation_points_btc_equiv":ACTIVATION_POINTS,
         "trailing_stop_points_btc_equiv":TRAIL_STOP_POINTS,
         "eth_normalization":"entry price /80000, tick rounded",
         "formula":"LONG stop=max(previous stop, best observed 1M HIGH - stop_points); SHORT stop=min(previous stop,best observed 1M LOW +stop_points); activation when favorable move reaches 100 points",
         "stop_edit_timing":"After completed 1M bar, applies NEXT minute. Never retroactive.",
       },
       "fixed_trailing_distance":{"enabled":False},
       "supertrend_opposite_flip_exit":True,
       "source":"Delta India PRODUCTION archived trade and MARK 1M OHLC, not Demo exchange",
       "fee_model":"Taker fee 0.05% EACH side plus 18% GST, no promo; no funding, live fills, bid/ask, PM liquidation, latency",
       "reference_sizing":"~$1000 max target notional; fixed-notional models not fundable with $100 equity once depleted",
       "exit_price_proxy":"1M traded CLOSE when installed stop crossed during minute; 1M traded OPEN for gap / Supertrend flip; NOT guaranteed fill",
       "models":{"MARK":"1m MARK high/low stop trigger and new stop calculation",
                 "TRADED":"1m TRADED high/low stop trigger and new stop calculation"},
       "historical_data":{},"scenarios":{}
    }
    for asset in ("BTC","ETH"):
        args,info=prepare(asset)
        report["historical_data"][asset]=info
        t=args[0]
        assert int(t[0])==int(pd.Timestamp("2025-01-01",tz="UTC").timestamp())
        # Previous archive includes partial Nov 2026. Truncate data to
        # 22 completed months, not only financial summary, so no future
        # position/stop states leak into the month-end results.
        end=int(pd.Timestamp("2026-11-01",tz="UTC").timestamp())
        n=int(np.searchsorted(t,end,side="left"))
        assert n>963000 and n<len(t)
        assert t[n-1]==end-60 and np.all(np.diff(t[:n])==60)
        # Safely adjust only signal data at index 12 from original signal_map.
        # Orig stopdist = 2*ATR14, so 9*ATR14 = orig*4.5.
        cfg=[v[:n].copy() for v in args]
        assert cfg[12].shape[0]==n
        assert np.all(cfg[12][cfg[9]!=0]>0)
        cfg[12]*=INIT_STOP_SCALE
        # Ensure the change didn't modify signal entries, times or ST flips
        assert np.array_equal(cfg[9],args[9][:n])
        assert np.array_equal(cfg[10],args[10][:n])
        for price,mode in (("MARK",0),("TRADED",1)):
            for walletguard in (False,True):
                data,skips,wallet,openpos=compute(
                   *cfg,ACTIVATION_POINTS,TRAIL_STOP_POINTS,
                   int(asset=="ETH"),mode,walletguard)
                ledger=frame_rows(data)
                full=costs_and_summary(ledger,COMPLETE)
                train=costs_and_summary(ledger,COMPLETE[:12])
                hold=costs_and_summary(ledger,COMPLETE[12:])
                m=month_table(ledger)[:22]
                assert len(m)==22 and sum(x["trades"] for x in m)==full["trades"]
                assert abs(round(sum(x["net_usd"] for x in m),2)-round(full["net_usd"],2))<.03
                name=f"{asset.lower()}_{price.lower()}_walletguard_{str(walletguard).lower()}"
                report["scenarios"][name]={
                   "asset":asset,"price_source":price,
                   "wallet_guard_enabled":walletguard,
                   "full22":full,
                   "train2025":train,
                   "holdout2026":hold,
                   "month_by_month":m,
                   "still_open_at_cutoff":bool(openpos),
                   "wallet_reference_usd_at_cutoff":round(float(wallet),4),
                   "original_signal_count":int(np.count_nonzero(cfg[9])),
                   "skips":{"already_open":int(skips[0]),"deviation":int(skips[1]),
                     "wallet_min_gate":int(skips[2]),"quantity":int(skips[3]),
                     "invalid_initial_stop":int(skips[4])},
                   "trades_with_stop_edits":int((ledger.stop_edits>0).sum()),
                   "avg_stop_edits":round(float(ledger.stop_edits.mean()),4) if len(ledger) else None,
                }
                pd.DataFrame(m).to_csv(OUT/f"{name}_monthly.csv",index=False)
                ledger.to_csv(OUT/f"{name}_trades.csv.gz",index=False,compression="gzip")
                print("100_EXTRA_STOP300_SL9ATR",name,
                     json.dumps({"net":full["net_usd"],"pf":full["profit_factor"],
                       "positive_months":full["positive_months"],"trades":full["trades"],
                       "train":train["net_usd"],"holdout":hold["net_usd"],
                       "drawdown":full["max_closed_trade_drawdown_usd"],
                       "wallet":wallet,"still_open":bool(openpos),
                       "edits":report["scenarios"][name]["trades_with_stop_edits"]}),
                     flush=True)
    (OUT/"summary.json").write_text(json.dumps(report,indent=2)+"\n")
    print("ADDITIONAL_TRAILING_STOP_100_300_INITIAL9ATR_PASS",str(OUT),flush=True)

if __name__=="__main__":
    main()
