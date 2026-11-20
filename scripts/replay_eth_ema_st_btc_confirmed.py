#!/usr/bin/env python3
"""ETHUSD futures historical backtest with optional BTCUSD EMA20/ST confirmation.

Only ETHUSD is traded. 15-minute BTCUSD data are entry triggers/filters.
ETH liquidation, ETH sizing, ATR stop, relative trailing and exits are reused
from replay_eth_ema_st_fixed10_100x.py without modifications to defaults.
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import replay_btc_ema_st_eth_confirmed as cross
import replay_eth_ema_st_fixed10_100x as eth_prior

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/"analysis/eth_ema_st_btc_confirm_20261120"

def run_variant(name,frame,allowed,last_month,external_side=None,guarded=False):
    entry_frame=frame.copy()
    assert allowed.index.equals(frame.index)
    # Local ETH signal is still computed by the ETH original replay. Mask the
    # existing volume gate only; leave ETH ST direction/exits completely intact.
    if external_side is None:
        entry_frame["volume_ratio"]=entry_frame.volume_ratio.where(allowed,0.0)
    out={}
    for offer in (True,False):
        for fill in ("threshold","bankruptcy"):
            key=("offer" if offer else "nooffer")+"_"+fill
            trades,stats=eth_prior.replay(
                entry_frame,0,fill,guarded=guarded,offer=offer,
                external_entry_side=None if external_side is None else external_side.to_numpy()
            )
            monthly=eth_prior.monthly(trades,"2025-01",last_month)
            complete=monthly[monthly.complete_month]
            stats["completed_months"]=int(len(complete))
            stats["profitable_completed_months"]=int((complete.net_profit_usd>0).sum())
            stats["losing_completed_months"]=int((complete.net_profit_usd<0).sum())
            stats["flat_completed_months"]=int((complete.net_profit_usd==0).sum())
            stats["candidate_signal_bars"]=int(allowed.sum())
            trades.to_csv(OUT/f"{name}_{key}_trades.csv.gz",index=False,compression="gzip")
            monthly.to_csv(OUT/f"{name}_{key}_monthly.csv",index=False)
            out[key]=stats
            print(f"RESULT {name}/{key} net=${stats['net_profit_usd']:+.2f} "
                  f"PF={stats['net_profit_factor']} trades={stats['completed_trades']} "
                  f"wins={stats['win_rate_pct']}% liqs={stats['assumed_liquidations']} "
                  f"positive_months={stats['profitable_completed_months']}/"
                  f"{stats['completed_months']}",flush=True)
    return out

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    btc_bars,b_manifest,n_btc=cross.load_symbol("BTCUSD")
    eth_bars,e_manifest,n_eth=cross.load_symbol("ETHUSD")
    btc_full=cross.source.indicators(btc_bars)
    eth_full=cross.source.indicators(eth_bars)
    common=btc_full.index.intersection(eth_full.index)
    if len(common)<1000:raise RuntimeError("Insufficient shared BTC/ETH history")
    assert common.is_unique and common.is_monotonic_increasing
    assert ((common[1:]-common[:-1])==pd.Timedelta(minutes=15)).all()
    btc=btc_full.loc[common].copy()
    eth=eth_full.loc[common].copy()
    assert btc.index.equals(eth.index)
    b=cross.sides(btc)
    e=cross.sides(eth)
    btc_st=pd.Series(np.where(btc.dir.to_numpy()==-1,1,-1),index=common,dtype="int8")
    eth_st=pd.Series(np.where(eth.dir.to_numpy()==-1,1,-1),index=common,dtype="int8")
    simultaneous=(e!=0)&(e==b)
    eth_trigger_eth_btc_trend=(e!=0)&(e==btc_st)
    btc_trigger=b.where(b==eth_st,0)
    assert not (simultaneous & ~eth_trigger_eth_btc_trend).any()
    last_month=str(common[-1].to_period("M"))
    report={
      "traded_instrument":"ETHUSD",
      "signal_instrument":"BTCUSD",
      "timeframe":"15m",
      "first_common_bar_utc":str(common[0]),
      "last_common_bar_utc":str(common[-1]),
      "aligned_15m_bars":len(common),
      "verified_input_1m_bars":{"ETHUSD":n_eth,"BTCUSD":n_btc},
      "source_manifest_generated_utc":{"ETHUSD":e_manifest["generated_at_utc"],"BTCUSD":b_manifest["generated_at_utc"]},
      "candidate_signal_bars":{"eth_only":int((e!=0).sum()),
          "btc_full_signal_triggers_eth_matching_st":int((btc_trigger!=0).sum()),
          "eth_full_signal_btc_matching_st":int(eth_trigger_eth_btc_trend.sum()),
          "both_full_signals":int(simultaneous.sum())},
      "model_settings":eth_prior.PARAMS,
      "cost_warning":"30-minute scalper offer assumed historically; no slippage, spreads or funding. "
                     "ETH-based liquidation uses traded OHLC approximation not Mark Price. "
                     "Signal close fills are optimistic and cannot guarantee live fill.",
      "results":{}
    }
    report["results"]["eth_only"]=run_variant("eth_only",eth,e!=0,last_month)
    report["results"]["btc_full_signal_triggers_eth_matching_st"]=run_variant(
        "btc_full_signal_triggers_eth_matching_st",eth,btc_trigger!=0,last_month,external_side=btc_trigger)
    report["results"]["eth_full_signal_btc_matching_st"]=run_variant(
        "eth_full_signal_btc_matching_st",eth,eth_trigger_eth_btc_trend,last_month)
    report["results"]["both_full_signals"]=run_variant("both_full_signals",eth,simultaneous,last_month)
    # Optional liquidation-distance guard sensitivity of the requested trigger.
    report["results"]["btc_trigger_guarded"]=run_variant(
        "btc_trigger_guarded",eth,btc_trigger!=0,last_month,external_side=btc_trigger,guarded=True)
    (OUT/"summary.json").write_text(json.dumps(report,indent=2)+"\n")
    print("SUCCESS: ETH futures backtest with BTC confirmation complete",flush=True)

if __name__=="__main__":main()
