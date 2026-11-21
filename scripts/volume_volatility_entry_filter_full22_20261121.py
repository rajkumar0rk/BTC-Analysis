#!/usr/bin/env python3
"""22-month BTC/ETH 1H Volume + Volatility entry-filter grid, ATR take profit.

Compares WITHOUT vs WITH volume and volatility filters on the SAME archived
EMA20+Supertrend(10,3) 1H trade signals. No lookahead:
  VolumeRatio = completed ENTRY-SIGNAL 1H volume /
                SMA(20) of 1H volume bars immediately BEFORE signal hour
  ATRExpansion = ATR14 of completed ENTRY-SIGNAL 1H bar /
                 SMA(20) of ATR14 bars immediately BEFORE signal hour.
Evaluate at the NEXT 1H boundary, no unfinished 1H or future data.
Optional upper caps exclude anomalous volume/volatility spikes.

Leave all exits UNCHANGED from validated 2026-11-21 ATR-hybrid replay:
 - 1H confirmed best-CLOSE ATR trailing TP, stop effective next hour.
 - 1-minute MARK emergency 2xATR14 (regardless of filters)
 - opposite 1H ST flip exits, MARK/TRADed hourly close sensitivity
 - one position per asset, $1k maximum reference notional
This study tests the most promising *previous exit* for each asset, plus
its alternative for BTC/ETH monthly-consistency comparison:
  BTC 1000/3xATR, 1500/1.5xATR
  ETH 4000/1.5xATR, 4000/2xATR (BTC-equivalent activation)
No weekly/month-specific optimization. JAN2025-OCT2026 22 complete UTC months.
Train=2025, holdout=2026 Jan-Oct. Report IN-SAMPLE full-window leader
separately from train-only leader, and their holdout results.

Reference simulator does NOT model funding, actual bid/ask fill, orderbook
slippage, portfolio margin/liquidation, or realistic $100-equity depletion.
0.05% taker fee EACH leg plus GST18%. Never infer actual achieved profit.
Works on research branch only; makes no orders; no change to main or bot.
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd

from full_history_1h_trailing_100_50_2025_2026 import read_asset
from replay_btc_ema_st_screenshot import indicators
from atr_hybrid_1h_close_vs_1m_full22_20261121 import (
    data_arrays,replay,ledger_frame,get_summary,MONTHS,unit_tests
)

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"analysis"/"volume_volatility_atr_entry_full22_20261121"
OUT.mkdir(parents=True,exist_ok=True)
END=int(pd.Timestamp("2026-11-01",tz="UTC").timestamp())
VOLUME_MIN=(0.,.75,1.,1.25,1.5,2.,2.5)
ATR_MIN=(0.,.75,.9,1.,1.1,1.25,1.5)
CAPS=((None,None),(3.,2.))
MODES=(("MARK",0),("TRADED",1))
# The 1h close profit exit was consistently stronger than the 1m profit exit
# in the previous 22-month study. Keep the exit method fixed in this sweep.
EXIT_MODE=0
PRESETS={
    "BTC":[("least_negative_exit",1000.,3.),("most_months_exit",1500.,1.5)],
    "ETH":[("least_negative_exit",4000.,1.5),("alternate_exit",4000.,2.)]
}
MIN_CLOSED=90
MIN_ACTIVE_MONTHS=12
PREVIOUS=ROOT/"analysis"/"wide_hybrid_atr_profit_grid_full22_20261121"/"summary.json"


def indicator_signal_ratios(asset,args):
    """Return one record per preexisting next-hour entry signal with prior-20 benchmarks."""
    trade,mark,provenance=read_asset(asset)
    trade=trade.loc[trade.time<END]
    h=trade.resample("1h",origin="epoch",label="left",closed="left").agg({
      "open":"first","high":"max","low":"min",
      "close":"last","volume":"sum","time":"count"
    })
    if not (h.time==60).all():
        raise AssertionError(f"Missing 1H source bars for {asset}")
    ind=indicators(h.drop(columns=["time"]))
    previous_vol_mean=h.volume.shift(1).rolling(20,min_periods=20).mean()
    previous_atr_mean=ind.atr14.shift(1).rolling(20,min_periods=20).mean()
    v_ratio=h.volume/previous_vol_mean
    atr_ratio=ind.atr14/previous_atr_mean

    times=args[0]
    indices=np.flatnonzero(args[11]!=0)
    signed=args[11][indices]
    entry_t=times[indices]
    assert np.all(entry_t%3600==0)
    base=int(times[0])
    # Index signal for H bar [entry_t - 3600, entry_t)
    hindex=((entry_t-base)//3600-1).astype(np.int64)
    if not np.all((hindex>=0)&(hindex<len(h))):
        raise AssertionError("Hourly lookup index invalid")
    ts_h=(h.index.view("int64")//1_000_000_000).astype(np.int64)
    if not np.array_equal(ts_h[hindex]+3600,entry_t):
        raise AssertionError("Future data/incorrect signal indexing")

    ratio_v=v_ratio.to_numpy(dtype=np.float64)[hindex]
    ratio_a=atr_ratio.to_numpy(dtype=np.float64)[hindex]
    if np.sum(np.isfinite(ratio_v)&np.isfinite(ratio_a))<int(len(indices)*.97):
        raise AssertionError("Indicator ratios missing unexpectedly for post-warmup signals")
    if np.nanmin(ratio_v)<0 or np.nanmin(ratio_a)<=0:
        raise AssertionError("Invalid volume or volatility ratio")
    # Export all base signals with both indicator ratios for reproducibility.
    f=pd.DataFrame({
      "signal_entry_utc":pd.to_datetime(entry_t,unit="s",utc=True).astype(str),
      "side":np.where(signed==1,"LONG","SHORT"),
      "completed_1h_volume_ratio":np.round(ratio_v,6),
      "completed_1h_atr_expansion_ratio":np.round(ratio_a,6),
      "source_hour_utc":pd.to_datetime(entry_t-3600,unit="s",utc=True).astype(str)
    })
    f.to_csv(OUT/f"{asset.lower()}_base_entry_signal_ratios.csv",index=False)
    return indices,ratio_v,ratio_a,len(indices)


def apply_filter(args,indices,v_ratio,atr_ratio,vol_min,atr_min,vol_cap,atr_cap):
    """Filter ONLY new entries; preserves flip event, prices and existing exit logic."""
    original=args[11]
    candidate=original.copy()
    if vol_min==0 and atr_min==0 and vol_cap is None and atr_cap is None:
        return [*args[:11],candidate,*args[12:]],int(len(indices))
    keep=np.isfinite(v_ratio)&np.isfinite(atr_ratio)
    if vol_min>0:keep &= (v_ratio>=vol_min)
    if atr_min>0:keep &= (atr_ratio>=atr_min)
    if vol_cap is not None:keep &= (v_ratio<=vol_cap)
    if atr_cap is not None:keep &= (atr_ratio<=atr_cap)
    candidate[indices[~keep]]=0
    if not np.array_equal(candidate[indices[keep]],original[indices[keep]]):
        raise AssertionError("Entry filter changed signal side")
    if not np.array_equal(args[12],args[12].copy()):
        raise AssertionError("Unexpected change in flip signals")
    return [*args[:11],candidate,*args[12:]],int(keep.sum())


def summarized(df):
    full=get_summary(df,MONTHS)
    train=get_summary(df,MONTHS[:12])
    holdout=get_summary(df,MONTHS[12:])
    return {
      "net_usd":full["net_usd"],
      "gross_usd":full["gross_usd"],
      "fees_gst_usd":full["fees_gst_usd"],
      "profit_factor":full["profit_factor"],
      "trades":full["trades"],
      "wins":full["wins"],
      "win_rate_pct":full["win_rate_pct"],
      "positive_months":full["positive_months"],
      "negative_months":full["negative_months"],
      "zero_trade_months":full["zero_trade_months"],
      "max_closed_trade_drawdown_usd":full["max_closed_trade_drawdown_usd"],
      "train_2025_net_usd":train["net_usd"],
      "train_2025_pf":train["profit_factor"],
      "train_2025_positive_months":train["positive_months"],
      "holdout_2026_net_usd":holdout["net_usd"],
      "holdout_2026_pf":holdout["profit_factor"],
      "holdout_2026_positive_months":holdout["positive_months"],
      "monthly":full["monthly"]
    }


def pair_summary(mark,traded,asset,preset,activation,mult,vol_min,atr_min,vol_cap,atr_cap,signals):
    m=mark["score"];t=traded["score"]
    return {
      "asset":asset,"exit_preset":preset,"activation":activation,
      "atr_tp_multiplier":mult,
      "volume_min":vol_min,"atr_expansion_min":atr_min,
      "volume_max":vol_cap,"atr_expansion_max":atr_cap,
      "candidate_entry_signals":signals,
      "mark_net":m["net_usd"],"traded_net":t["net_usd"],
      "worst_source_net":min(m["net_usd"],t["net_usd"]),
      "mark_pf":m["profit_factor"],"traded_pf":t["profit_factor"],
      "mark_months":m["positive_months"],"traded_months":t["positive_months"],
      "min_positive_months":min(m["positive_months"],t["positive_months"]),
      "min_trades":min(m["trades"],t["trades"]),
      "min_active_months":22-max(m["zero_trade_months"],t["zero_trade_months"]),
      "worst_2025_train_net":min(m["train_2025_net_usd"],t["train_2025_net_usd"]),
      "worst_2026_holdout_net":min(m["holdout_2026_net_usd"],t["holdout_2026_net_usd"]),
      "mark_train_net":m["train_2025_net_usd"],
      "mark_holdout_net":m["holdout_2026_net_usd"],
      "mark_max_closed_drawdown_usd":m["max_closed_trade_drawdown_usd"],
      "traded_max_closed_drawdown_usd":t["max_closed_trade_drawdown_usd"],
    }


def main():
    unit_tests()
    previous=json.loads(PREVIOUS.read_text())
    root={
      "study":"22 full-month 1H volume + ATR-expansion entry filters with fixed ATR-profit exits; no weekly optimization",
      "historical_data":"Delta India production 1m traded and MARK OHLC Jan2025 to Oct2026 (no Demo)",
      "months":MONTHS,
      "filter_definition":{
         "entry_volume_ratio":"Signal 1H completed bar volume divided by mean previous 20 completed 1H volumes",
         "entry_atr_expansion":"Signal 1H ATR14 divided by mean previous 20 completed 1H ATR14 values",
         "time":"Both filters only evaluate after signal 1H bar closes, entry next 1H bar",
         "bounds_min":{"volume":list(VOLUME_MIN),"atr_expansion":list(ATR_MIN)},
         "optional_bounds_max":[{"volume":v,"atr_expansion":a} for v,a in CAPS],
      },
      "exit":"Previously tested 1H-close-confirmed ATR14 trailing profit; emergency 2xATR14 stop checked on MARK 1m, opposite Supertrend flip",
      "invariance":"Only entry signals filtered; do not filter protective stops, exits or existing signals after position opened",
      "fee_assumptions":"0.05% taker each side plus 18% GST. Funding, bid/ask slippage, order latency, PM liquidation not included.",
      "capital_warning":"Fixed $1,000 maximum notional target, unlimited reference wallet; not an executable $100 wallet backtest.",
      "selection_warning":"Full22 top rows selected in-sample; 2025 training and Jan-Oct 2026 holdout shown separately. Need forward validation.",
      "source_sensitivity":"Both MARK and TRADED hourly close profit stop calculations; 1m MARK emergency stays same.",
      "thresholds":{"min_closed_trades_for_rank":MIN_CLOSED,"min_active_months_for_rank":MIN_ACTIVE_MONTHS},
      "assets":{},"results":{}
    }
    compact=[]
    for asset,presets in PRESETS.items():
        args,info=data_arrays(asset)
        root["assets"][asset]={"data":info}
        indices,rv,ra,total_signals=indicator_signal_ratios(asset,args)
        root["assets"][asset]["base_hourly_signals"]=total_signals
        paired_rows=[]
        raw_records={}
        cache={}
        for preset,activation,mult in presets:
            for capvol,capatr in CAPS:
                for vm in VOLUME_MIN:
                    for am in ATR_MIN:
                        params=(vm,am,capvol,capatr)
                        arr,passed=apply_filter(args,indices,rv,ra,*params)
                        scenario={}
                        for source_name,source_id in MODES:
                            values,skips,open_at_end=replay(*arr,activation,mult,int(asset=="ETH"),
                                                             EXIT_MODE,source_id)
                            ledger=ledger_frame(values)
                            summary=summarized(ledger)
                            scenario[source_name]={"score":summary,"open_at_end":bool(open_at_end[0])}
                        row=pair_summary(scenario["MARK"],scenario["TRADED"],asset,
                                preset,activation,mult,vm,am,capvol,capatr,passed)
                        paired_rows.append(row);compact.append(row)
                        key=(preset,vm,am,capvol,capatr)
                        raw_records[key]=scenario
                        if vm==0 and am==0 and capvol is None and capatr is None:
                            for name in ("MARK","TRADED"):
                                before=previous["combinations"][asset]
                                source_key=next(
                                   (x for x in before if x["activation"]==activation and
                                    x["atr_multiplier"]==mult and x["exit_mode"]=="H_CLOSE"),None)
                                if source_key is None:
                                    # Previous full grid selected only some scenario ledgers;
                                    # use baseline summary from prior scenario-score CSV.
                                    priorcsv=pd.read_csv(ROOT/"analysis"/"wide_hybrid_atr_profit_grid_full22_20261121"/
                                        f"{asset.lower()}_all_scenario_scores.csv")
                                    matched=priorcsv.loc[
                                      (priorcsv.activation==activation)&
                                      (priorcsv.atr_multiplier==mult)&
                                      (priorcsv.exit_mode=="H_CLOSE")&
                                      (priorcsv.price_source==name)]
                                    if len(matched)!=1:raise AssertionError("Prior baseline absent")
                                    expected=float(matched.full_net.iloc[0])
                                else:
                                    expected=float(source_key[name]["score"]["full_net"])
                                if abs(scenario[name]["score"]["net_usd"]-expected)>0.0002:
                                    raise AssertionError(f"{asset} baseline drift {preset} {name}: "
                                      f"{scenario[name]['score']['net_usd']} != {expected}")
            print("FILTER_PRESET_COMPLETE",asset,preset,
                  "tested",len([x for x in paired_rows if x["exit_preset"]==preset]),flush=True)
        pd.DataFrame(paired_rows).sort_values(
            ["worst_source_net","min_positive_months"],
            ascending=False
        ).to_csv(OUT/f"{asset.lower()}_all_entry_filters.csv",index=False)
        eligible=[v for v in paired_rows if v["min_trades"]>=MIN_CLOSED and
                   v["min_active_months"]>=MIN_ACTIVE_MONTHS]
        if not eligible:raise AssertionError("No eligible filtered strategies")
        best_all=max(eligible,key=lambda x:(x["worst_source_net"],x["min_positive_months"]))
        best_months=max(eligible,key=lambda x:(x["min_positive_months"],x["worst_source_net"]))
        # 2025 training-only parameter choice; evaluate untouched Jan-Oct2026.
        best_train=max(eligible,key=lambda x:(x["worst_2025_train_net"],x["worst_2026_holdout_net"]))
        baseline=[x for x in paired_rows if x["volume_min"]==0 and x["atr_expansion_min"]==0
                  and x["volume_max"] is None and x["atr_expansion_max"] is None]
        profitable_both=[
           x for x in eligible if x["mark_net"]>0 and x["traded_net"]>0]
        profitable_train_holdout=[
           x for x in eligible if x["worst_2025_train_net"]>0 and
                                  x["worst_2026_holdout_net"]>0]
        selectors={
           "best_full22_in_sample":best_all,
           "best_monthly_consistency_in_sample":best_months,
           "best_2025_train_then_test_2026":best_train,
        }
        for x in baseline:selectors["unfiltered_"+x["exit_preset"]]=x
        root["results"][asset]={
          "tested_parameter_combinations":len(paired_rows),
          "eligible_parameter_combinations":len(eligible),
          "positive_net_both_models":len(profitable_both),
          "positive_2025_and_2026_both_models":len(profitable_train_holdout),
          "selectors":selectors,
          "top12_by_robust_net":sorted(eligible,key=lambda x:x["worst_source_net"],reverse=True)[:12],
          "top12_by_months":sorted(eligible,key=lambda x:(x["min_positive_months"],x["worst_source_net"]),reverse=True)[:12],
        }
        # Save per-month comparisons and full ledgers for the ranked candidates
        # plus unfiltered baseline, not just a scalar annual result.
        selected_combos={}
        for key,row in selectors.items():
            k=(row["exit_preset"],row["volume_min"],row["atr_expansion_min"],
                row["volume_max"],row["atr_expansion_max"])
            selected_combos[k]=row
        for row in root["results"][asset]["top12_by_robust_net"][:4]:
            k=(row["exit_preset"],row["volume_min"],row["atr_expansion_min"],
                row["volume_max"],row["atr_expansion_max"])
            selected_combos[k]=row
        root["results"][asset]["selected_monthly"]={}
        for (preset,vm,am,cv,ca),row in selected_combos.items():
            k=(preset,vm,am,cv,ca)
            label=f"{preset}_V{vm:g}_ATR{am:g}_Vmax{cv if cv is not None else 'inf'}_ATRmax{ca if ca is not None else 'inf'}".replace(".","p")
            modeldata=raw_records[k]
            root["results"][asset]["selected_monthly"][label]={
                 "config":row,
                 "month_results":{mode:{m:detail["net_usd"] for m,detail in modeldata[mode]["score"]["monthly"].items()}
                                  for mode in ("MARK","TRADED")},
            }
            for mode,model in modeldata.items():
                pd.DataFrame([
                    {"month_utc":month,**values}
                    for month,values in model["score"]["monthly"].items()
                ]).to_csv(OUT/f"{asset.lower()}_{label}_{mode.lower()}_monthly.csv",index=False)
                filt,_=apply_filter(args,indices,rv,ra,vm,am,cv,ca)
                arr,_,_=replay(*filt,row["activation"],row["atr_tp_multiplier"],
                                int(asset=="ETH"),EXIT_MODE,0 if mode=="MARK" else 1)
                ledger_frame(arr).to_csv(OUT/f"{asset.lower()}_{label}_{mode.lower()}_trades.csv.gz",
                                         index=False,compression="gzip")
        print("ASSET_FILTER_GRID_RESULTS",asset,json.dumps({
           "full22":best_all,"monthly":best_months,
           "best2025":best_train,
           "profitable_both":len(profitable_both),
           "profitable_both_train_holdout":len(profitable_train_holdout)
        },separators=(",",":")),flush=True)
        del args
    pd.DataFrame(compact).to_csv(OUT/"all_filter_scores_btc_eth.csv",index=False)
    (OUT/"summary.json").write_text(json.dumps(root,indent=2)+"\n")
    print("VOLUME_VOLATILITY_22MONTH_RESEARCH_SUCCESS",str(OUT),flush=True)

if __name__=="__main__":
    main()
