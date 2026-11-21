#!/usr/bin/env python3
"""Audit original BTC +$4298.18 / ETH +$6773.09 reported 1H OHLC trades.

Do NOT change the strategy. Replay exact old inferred hourly paths and
capture pos['best'] at every close, thereby measuring historical *modeled*
maximum favorable excursion (MFE) before the assumed exit.  Separately
count actually booked gross exit-price gains >= 100 and >= 200 BTCUSD price points; ETH uses equivalent percentages
of each trade's entry: 0.125% and 0.25%.
For BTC thresholds are 100 and 200 literal BTCUSD dollars;
ETH thresholds are BTC-equivalent entry-scaled levels
100*ETHentry/80000 and 200*ETHentry/80000, i.e. 0.125% and 0.25%
(usually several ETHUSD points, never fixed $100/$200 for ETH).
Raw measured excursion and exit moves are native coin price points;
these are not levered ROI or position PnL dollars. Any nominal MFE inherits the
hourly OHLC inferred-path assumption and is NOT tick-verified.

Source: analysis/ema_st_1h_all_stops_hourly_1_0p1_20261120/
  btc_1h_inferred_trades.csv.gz
  eth_1h_inferred_trades.csv.gz
Original reference historical source Jan 2025-Oct 2026.
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
import backtest_ema_st_hourly_stops_1_0p1_20261120 as h

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"analysis"/"ema_st_1h_all_stops_hourly_1_0p1_20261120"
OUT=ROOT/"analysis"/"audit_original_1h_ohlc_reach_100_200_20261121"
OUT.mkdir(parents=True,exist_ok=True)

original=json.loads((SOURCE/"summary.json").read_text())
original_close=h.prior.close

def close_with_mfe(pos,price,t,reason,wallet,offer):
    amount,record=original_close(pos,price,t,reason,wallet,offer)
    s=pos["side"]
    best=float(pos.get("best",pos["entry"]))
    # Include a possible gap exit or Supertrend-flip exit more favorable
    # than the last recorded trailing best.
    m=max(0.,s*(best-pos["entry"]),s*(price-pos["entry"]))
    record["modeled_mfe_points"]=m
    record["modeled_best_price_at_exit"]=best
    return amount,record

h.prior.close=close_with_mfe

def audit(asset,mod):
    original_ledger=pd.read_csv(SOURCE/f"{asset.lower()}_1h_inferred_trades.csv.gz")
    expected=original["assets"][asset]["hourly_results"]["inferred"]
    assert len(original_ledger)==expected["trade_count"],(asset,len(original_ledger),expected["trade_count"])
    # Original wallet may have an OPEN POSITION whose entry fee has already
    # reduced cash but is not represented in the CLOSED-trades ledger.
    # Therefore reconcile ledger transactions, not closed net sum to wallet.
    b,quality=mod.source()
    d,atr,long,short=mod.features(b)
    stats,trades=h.replay_hourly(asset,b,d,atr,long,short,mode="inferred",offer=False)
    assert len(trades)==len(original_ledger)==expected["trade_count"]
    assert abs(stats["net_usd"]-expected["net_usd"])<.001,(asset,stats["net_usd"],expected["net_usd"])
    # Complete ledger must agree, independent of new MFE annotations.
    for k in ("entry_epoch","exit_epoch","entry","exit","gross_usd","net_usd","fees_gst_usd"):
        assert np.allclose(trades[k],original_ledger[k],rtol=0,atol=.000001),(
            asset,"TRADE_LEDGER_MISMATCH",k)
    assert trades["exit_reason"].equals(original_ledger["exit_reason"])
    side=np.where(trades.side.to_numpy()=="LONG",1.,-1.)
    points=(trades.exit.to_numpy(float)-trades.entry.to_numpy(float))*side
    mfe=trades.modeled_mfe_points.to_numpy(float)
    assert np.all(mfe+1e-6>=np.maximum(points,0)),(asset,"MFE_INCONSISTENT")
    first=np.full(len(trades),100.,dtype=float) if asset=="BTC" else trades.entry.to_numpy(float)*.00125
    second=np.full(len(trades),200.,dtype=float) if asset=="BTC" else trades.entry.to_numpy(float)*.0025
    t1=(mfe>=first-1e-8)
    t2=(mfe>=second-1e-8)
    x1=(points>=first-1e-8)
    x2=(points>=second-1e-8)
    assert np.all(t2<=t1) and np.all(x2<=x1)
    result={
        "asset":asset,
        "source_original_22_month_reported_net_usd":expected["net_usd"],
        "original_trade_count":len(trades),
        "reproduced_original_trade_ledger_every_row":True,
        "reach_definition":"Modeled maximum favorable excursion before assumed exit, from original hourly OHLC-inferred-path replay (pos.best plus favorable exit gap). For ETH use 100/200 BTC-equivalent points = 0.125%/0.25% of trade entry price, not fixed $100/$200.",
        "thresholds":{"BTC":{"first_absolute_price_points":100,"second_absolute_price_points":200},"ETH":{"first_pct_of_entry":0.125,"second_pct_of_entry":0.25,"example_for_eth_at_4000":{"first_native_eth_points":5.,"second_native_eth_points":10.}}}[asset],
        "realized_definition":"Gross directional price-point difference entry vs exit, disregards fees, margin and leverage.",
        "counts":{
          "modeled_reached_100_or_more":int(np.count_nonzero(t1)),
          "modeled_reached_200_or_more":int(np.count_nonzero(t2)),
          "modeled_reached_100_to_under_200":int(np.count_nonzero(t1&~t2)),
          "modeled_reached_below_100":int(np.count_nonzero(~t1)),
          "realized_gross_exit_gain_100_or_more":int(np.count_nonzero(x1)),
          "realized_gross_exit_gain_200_or_more":int(np.count_nonzero(x2)),
          "realized_gross_exit_gain_100_to_under_200":int(np.count_nonzero(x1&~x2)),
          "realized_gross_exit_gain_below_100":int(np.count_nonzero(~x1)),
          "net_profit_trades_usd_positive":int(np.count_nonzero(trades.net_usd>0)),
        },
        "max_mfe_points":round(float(np.max(mfe)),4),
        "max_realized_gain_points":round(float(np.max(points)),4),
        "modeled_reached_pct_100":round(float(np.mean(t1))*100,2),
        "modeled_reached_pct_200":round(float(np.mean(t2))*100,2),
        "caveat":"MFE is reconstructed from the original OHLC-inferred (not observed tick) path; possible high/low sequence uncertainty and unrealistic sub-tick trailing profits. This is NOT evidence the original +$4,298/+6,773 were achievable.",
    }
    trades["threshold_100_native_points"]=first
    trades["threshold_200_native_points"]=second
    trades["reached_100_btc_equivalent"]=t1
    trades["reached_200_btc_equivalent"]=t2
    trades["realized_100_btc_equivalent"]=x1
    trades["realized_200_btc_equivalent"]=x2
    trades["gross_exit_gain_points"]=points
    trades.to_csv(OUT/f"{asset.lower()}_inferred_with_mfe.csv.gz",index=False,compression="gzip")
    return result

def main():
    result={
        "reference":"original 1H OHLC inferred-path profit BTC +4298.1778 / ETH +6773.09",
        "date_window":"2025-01-01 through 2026-10-31 UTC, 22 complete months",
        "source_branch":"research/ema-st-1h-stop-trail-hourly-20261120",
        "metrics":"BTC literal $100/$200 price points; ETH 0.125%/0.25% of own entry (100/200 BTC-equivalent), not literal $100/$200",
        "assets":{}
    }
    for asset,mod in (("BTC",h.btc),("ETH",h.eth)):
        print("REPLAY_ORIGINAL_WITH_MFE",asset,flush=True)
        result["assets"][asset]=audit(asset,mod)
        print("MFE_REACH_RESULT",json.dumps(result["assets"][asset]),flush=True)
    (OUT/"summary.json").write_text(json.dumps(result,indent=2)+"\n")
    print("MFE_100_200_AUDIT_SUCCESS",flush=True)

if __name__=="__main__":
    main()
