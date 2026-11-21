#!/usr/bin/env python3
"""15M EMA20/ST(10,3) entry, 1M ATR-only trailing parameter grid.

SOURCE: user-supplied Pine v6 Pasted markdown(10).md, with four screenshot
settings and subsequent explicit user change:
- Initial SL: 15M confirmed ATR(14) x configurable multiplier.
- Profit trailing: native 1M chart ATR(14) x configurable multiplier,
  activated after best favorable BTCUSD point excursion. Stop updated
  after each completed 1M candle for subsequent bars, never retroactively.
- Fixed Trailing Distance OFF, Additional Trailing Stop Points OFF,
  therefore NO native point trailing (even though old inputs are present).
- EMA20 touch/reclaim, continuing Supertrend(10,3) 15M signals;
  no high volume/volatility entry filter, ST flip exit ON.
- Entry at confirmed 15m candle CLOSE on native 1m chart, as in Pine
  with process_orders_on_close=true. Trade size one TV contract=.001 BTC.
- Test BTC only: the supplied Pine is BTCUSD, not a validated ETH bot.

Explore 8 initial ATR multipliers * 8 1M trailing ATR multipliers *
8 point activation values = 512 parameter triples. Evaluate MARK and
TRADED monitoring independently (1024 historical execution replays).
For each, compute assumed all-history 30-minute scalper exit-fee waiver
AND conservative no-waiver (2048 performance score cases).
Other fees: .05% taker entry and exit, GST18%, modeled funding zero.
Funding, true spread, slippage, latency, real broker fills, margin and
liquidation excluded. No historical wallet funding guard. These are
sensitivity simulations, not TradingView tick-by-tick strategy-test data.

Full 22 complete UTC months: Jan2025-Oct2026; current partial week from
Nov16 00:00 IST through Nov21 07:30 IST. 2025 training, 2026 holdout
are reported to expose selection effects. Top historical and weekly
parameters are IN-SAMPLE winners, not prospective trading evidence.

Regression check: reproduce all trade-row values from the previously
validated ATR-only code at initial3/trail3/activation200 in BTC TRADED and
MARK models, with and without assumed scalper offer. No changes to live
trading systems; isolated research branch in BTC-Analysis.
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
from numba import njit
from backtest_pine_atr_only_no_fixed_no_points_20261121 import (
    inputs, execute as original_execute, statistics, reports, ledger_frame,
    TICK,FEE,GST,QTY,ROOT,FULL_START,FULL_END,SPLIT,MONTHS,
)
from current_week_100_300_initial9atr_20261121 import (
    refresh_nov,WEEK_START,END,
)
from optimize_1h_additional_trailing_stop_points_20261121 import stop_round

OUT=ROOT/"analysis"/"grid_15m_atr_only_initial_trailing_activation_20261121"
OUT.mkdir(parents=True,exist_ok=True)

INITIAL_ATR_MULTS=(1.,1.5,2.,3.,4.,5.,7.,9.)
TRAIL_ATR_MULTS=(.5,1.,1.5,2.,3.,4.,5.,7.)
ACTIVATION_POINTS=(0.,50.,100.,200.,300.,500.,800.,1200.)
SOURCE_MODELS=(("TRADED",0),("MARK",1))
FEES=(("SCALPER_ASSUMED",1),("NO_SCALPER",0))
MIN_WEEK_TRADES=5
MIN_FULL_TRADES=100

@njit(cache=True)
def simulate(ts,to,th,tl,tc,mo,mh,ml,mc,signal,flip,atr15,atr1m,
             price_source,initmult,trailmult,activation,scalper):
    """Exact original single-custom-stop logic (native point switches OFF).
    Result schema matches original 17-column trade ledger for strict parity.
    Entry 15M completed bar close; 1M stop active only from following bar.
    """
    out=np.zeros((16000,17),dtype=np.float64)
    nout=0;active=0;side=0
    entry=0.;entry_t=0;custom=0.;initial=0.;best=0.;updates=0
    skips=np.zeros(3,dtype=np.int64)
    for i in range(len(ts)):
        if price_source==0:
            o=to[i];hi=th[i];lo=tl[i]
        else:
            o=mo[i];hi=mh[i];lo=ml[i]
        ec=0;xp=0.
        was_open=active==1
        if was_open:
            if (side==1 and o<=custom) or (side==-1 and o>=custom):
                ec=1;xp=to[i]
            elif (side==1 and lo<=custom) or (side==-1 and hi>=custom):
                ec=3;xp=custom if price_source==0 else tc[i]
            elif flip[i]==side:
                ec=4;xp=tc[i]
            else:
                best=max(best,hi) if side==1 else min(best,lo)
                if side*(best-entry)>=activation and np.isfinite(atr1m[i]):
                    cand=stop_round(best-side*trailmult*atr1m[i],TICK,side)
                    tighter=max(custom,cand) if side==1 else min(custom,cand)
                    if abs(tighter-custom)>=TICK*.5:updates+=1
                    custom=tighter
        if ec:
            hold=(ts[i]-entry_t)/60.
            gross=(xp-entry)*side*QTY
            opening=entry*QTY*FEE
            closing=xp*QTY*FEE
            if scalper and hold<=30.:closing=0.
            fees=opening+closing
            gst=fees*GST
            if nout>=len(out):raise RuntimeError("Trade buffer overrun")
            out[nout,0]=entry_t;out[nout,1]=ts[i];out[nout,2]=side
            out[nout,3]=entry;out[nout,4]=xp;out[nout,5]=QTY
            out[nout,6]=gross;out[nout,7]=fees;out[nout,8]=gst
            out[nout,9]=gross-fees-gst
            out[nout,10]=initial;out[nout,11]=custom
            out[nout,12]=np.nan;out[nout,13]=ec
            out[nout,14]=hold;out[nout,15]=updates
            out[nout,16]=0.
            nout+=1;active=0;updates=0
        # Entry at the 1m CLOSE that confirms the 15m signal.
        if active==0 and signal[i]!=0:
            if atr15[i]>0 and np.isfinite(atr15[i]):
                active=1;side=signal[i];entry=tc[i];entry_t=ts[i]
                initial=stop_round(entry-side*initmult*atr15[i],TICK,side)
                custom=initial;best=entry;updates=0
            else:skips[0]+=1
        elif was_open and active and signal[i]!=0:skips[1]+=1
    return out[:nout],skips,active


def fee_mode(raw,scalper):
    """Recompute net/fees from the same trade prices, independent of stops."""
    if scalper:return raw
    other=raw.copy()
    if len(other):
        # Historical Pine assumes conditional fee waiver only when enabled.
        add=other[:,4]*QTY*FEE*(other[:,14]<=30.)
        other[:,7]+=add
        other[:,8]=other[:,7]*GST
        other[:,9]=other[:,6]-other[:,7]-other[:,8]
    return other


def rank_row(asset,source,initmult,trailmult,activation,fee_label,rec,op):
    return {
      "asset":asset,"monitor":source,
      "initial_atr_multiplier":initmult,
      "trailing_atr_multiplier":trailmult,
      "atr_activation_points":activation,"fee_mode":fee_label,
      "week_net_usd":rec["current_partial_week"]["net_usd"],
      "week_pf":rec["current_partial_week"]["profit_factor"],
      "week_trades":rec["current_partial_week"]["trades"],
      "week_winrate":rec["current_partial_week"]["win_rate_pct"],
      "full22_net_usd":rec["full22"]["net_usd"],
      "full22_pf":rec["full22"]["profit_factor"],
      "full22_trades":rec["full22"]["trades"],
      "full22_drawdown_usd":rec["full22"]["max_closed_trade_dd_usd"],
      "positive_months":rec["positive_months"],
      "year2025_net_usd":rec["year2025"]["net_usd"],
      "jan_oct2026_net_usd":rec["jan_oct2026"]["net_usd"],
      "open_trade_at_week_end":bool(op),
    }


def reduced_monthly(raw):
    times=raw[:,1]
    full=raw[(times>=FULL_START)&(times<FULL_END)]
    dates=full[:,1].astype(np.int64).astype("datetime64[s]").astype("datetime64[M]")
    return [{"month_utc":m,**statistics(full[dates==np.datetime64(m,"M")])}
            for m in MONTHS]


def pair_scores(a,b):
    assert (a["initial_atr_multiplier"],a["trailing_atr_multiplier"],
            a["atr_activation_points"],a["fee_mode"])==(
            b["initial_atr_multiplier"],b["trailing_atr_multiplier"],
            b["atr_activation_points"],b["fee_mode"])
    return {
       "initial_atr":a["initial_atr_multiplier"],
       "trailing_atr":a["trailing_atr_multiplier"],
       "activation_points":a["atr_activation_points"],
       "fee_mode":a["fee_mode"],
       "traded_week_net":a["week_net_usd"],"mark_week_net":b["week_net_usd"],
       "robust_week_net":min(a["week_net_usd"],b["week_net_usd"]),
       "week_trades_min":min(a["week_trades"],b["week_trades"]),
       "traded_week_pf":a["week_pf"],"mark_week_pf":b["week_pf"],
       "traded_full22_net":a["full22_net_usd"],"mark_full22_net":b["full22_net_usd"],
       "robust_full22_net":min(a["full22_net_usd"],b["full22_net_usd"]),
       "full22_trades_min":min(a["full22_trades"],b["full22_trades"]),
       "traded_full22_pf":a["full22_pf"],"mark_full22_pf":b["full22_pf"],
       "positive_months_min":min(a["positive_months"],b["positive_months"]),
       "traded_2025_net":a["year2025_net_usd"],
       "mark_2025_net":b["year2025_net_usd"],
       "robust_2025_net":min(a["year2025_net_usd"],b["year2025_net_usd"]),
       "traded_2026_net":a["jan_oct2026_net_usd"],
       "mark_2026_net":b["jan_oct2026_net_usd"],
       "robust_2026_net":min(a["jan_oct2026_net_usd"],b["jan_oct2026_net_usd"]),
    }


def main():
    fresh=refresh_nov()
    arrays,meta=inputs()
    # Strict baseline parity with the previously completed run,
    # independent of model and assumed fee mode.
    regression={}
    for source,sourceid in SOURCE_MODELS:
        for flabel,fid in FEES:
            old,_,_=original_execute(*arrays,sourceid,0,fid,False)
            new,_,_=simulate(*arrays,sourceid,3.,3.,200.,fid)
            assert new.shape==old.shape
            assert np.allclose(new,old,atol=1e-9,rtol=0,equal_nan=True),(
                "Baseline trade-level mismatch",source,flabel)
            regression[f"{source}_{flabel}"]={
                "matches_original_every_trade_field":True,
                "baseline_full22_net":reports(new)["full22"]["net_usd"],
                "baseline_week_net":reports(new)["current_partial_week"]["net_usd"],
            }
    report={
       "goal":"15M entries / 1M ATR-only trailing parameter sweep; both section-7 fixed/native point trails OFF",
       "source":"Actual BTCUSD Pine v6 supplied by user, prior validated ATR-only regression",
       "settings":{"entry_tf":"15m","monitoring_tf":"1m",
           "ST_atr_length":10,"ST_factor":3,"EMA_length":20,
           "pullback":"EMA20","volume_volatility_filters":"OFF",
           "supertrend_flip_exit":"ON","enable_trailing":"ON",
           "trail_mode":"ATR Only",
           "initial_stop":"configurable multiplier of completed 15m ATR14",
           "trailing_stop":"configurable multiplier of current 1m chart ATR14",
           "ATR_activation":"configurable BTCUSD favorable price points",
           "enable_fixed_distance":False,"enable_trailing_stop_points":False},
       "grid":{"initial_atr":list(INITIAL_ATR_MULTS),
           "trailing_atr":list(TRAIL_ATR_MULTS),
           "activation_points":list(ACTIVATION_POINTS),
           "unique_settings":len(INITIAL_ATR_MULTS)*len(TRAIL_ATR_MULTS)*len(ACTIVATION_POINTS),
           "price_models":["TRADED","MARK"],
           "cost_models":["SCALPER_ASSUMED","NO_SCALPER"],
           "scenario_score_count":len(INITIAL_ATR_MULTS)*len(TRAIL_ATR_MULTS)*len(ACTIVATION_POINTS)*4},
       "cost":"0.05% taker both sides; GST18%, 1 contract=0.001 BTC, estimated 30m exit-fee waiver when flagged all history",
       "limitations":"Pine/TradingView 1m OHLC approximation, not true tick path or real stop fills. MARK is sensitivity only, not TV source; no historical scalper eligibility proof, funding, spread, slippage, margin/liquidation, wallet depletion.",
       "period":{"historical":"Jan2025-Oct2026 22 complete UTC months",
           "current_partial_week":"Mon Nov16 00:00 IST - Sat Nov21 07:30 IST (exclusive)"},
       "data":meta,"nov_refresh":fresh,"baseline_regression":regression,
       "rankings":{},"selected":{},
    }
    allrows=[];allmonths=[];by_key={}
    for initial in INITIAL_ATR_MULTS:
        for trailing in TRAIL_ATR_MULTS:
            for activation in ACTIVATION_POINTS:
                for source,sourceid in SOURCE_MODELS:
                    # Run once per model; derive both fee interpretations
                    # without changing trade outcomes.
                    arr,skips,openpos=simulate(
                        *arrays,sourceid,float(initial),float(trailing),
                        float(activation),1)
                    assert not np.count_nonzero(arr[:,16])
                    for label,fid in FEES:
                        sub=fee_mode(arr,fid)
                        rec=reports(sub)
                        row=rank_row("BTC",source,initial,trailing,activation,label,rec,openpos)
                        allrows.append(row)
                        key=(initial,trailing,activation,source,label)
                        by_key[key]=row
                        for m in rec["monthly"]:
                            allmonths.append({
                               "initial_atr":initial,"trailing_atr":trailing,
                               "activation":activation,"source":source,
                               "fee_model":label,**m
                            })
                # One parameter triple has been completed for BOTH source models.
            print("ATR_GRID_PROGRESS","initial",initial,"trailing",trailing,flush=True)
    paired={}
    for fee_label,_ in FEES:
        pairs=[]
        for initial in INITIAL_ATR_MULTS:
            for trailing in TRAIL_ATR_MULTS:
                for activation in ACTIVATION_POINTS:
                    a=by_key[(initial,trailing,activation,"TRADED",fee_label)]
                    b=by_key[(initial,trailing,activation,"MARK",fee_label)]
                    pairs.append(pair_scores(a,b))
        pairs_w=[p for p in pairs if p["week_trades_min"]>=MIN_WEEK_TRADES]
        pairs_h=[p for p in pairs if p["full22_trades_min"]>=MIN_FULL_TRADES]
        assert pairs_w and pairs_h
        by_week=sorted(pairs_w,key=lambda p:(p["robust_week_net"],p["robust_full22_net"]),reverse=True)
        by_full=sorted(pairs_h,key=lambda p:(p["robust_full22_net"],p["positive_months_min"]),reverse=True)
        by_month=sorted(pairs_h,key=lambda p:(p["positive_months_min"],p["robust_full22_net"]),reverse=True)
        by_train=sorted(pairs_h,key=lambda p:(p["robust_2025_net"],p["robust_2026_net"]),reverse=True)
        report["rankings"][fee_label]={
            "total_pairs":len(pairs),
            "positive_week_both_sources":int(sum(p["robust_week_net"]>0 for p in pairs)),
            "positive_full22_both_sources":int(sum(p["robust_full22_net"]>0 for p in pairs)),
            "profitable_22_months":int(sum(p["positive_months_min"]==22 for p in pairs)),
            "top10_week":by_week[:10],
            "top10_full22":by_full[:10],
            "top10_positive_months":by_month[:10],
            "best_2025_train_then_2026_holdout":by_train[0],
            "original_3_3_200":next(p for p in pairs if p["initial_atr"]==3.
                                     and p["trailing_atr"]==3.
                                     and p["activation_points"]==200.),
        }
        paired[fee_label]=pairs
        pd.DataFrame(pairs).to_csv(OUT/f"paired_{fee_label.lower()}.csv",index=False)
    pd.DataFrame(allrows).to_csv(OUT/"all_2048_model_scores.csv",index=False)
    pd.DataFrame(allmonths).to_csv(OUT/"all_45056_monthly_scores.csv.gz",index=False,compression="gzip")
    # Materialize detailed monthly and daily reports for highest-ranked
    # choices under both fee models, and baseline.
    selected={(3.,3.,200.)}
    for name in report["rankings"]:
        z=report["rankings"][name]
        for k in ("top10_week","top10_full22","top10_positive_months"):
            for item in z[k][:4]:
                selected.add((item["initial_atr"],item["trailing_atr"],item["activation_points"]))
        tr=z["best_2025_train_then_2026_holdout"]
        selected.add((tr["initial_atr"],tr["trailing_atr"],tr["activation_points"]))
    for initial,trailing,activation in sorted(selected):
        key=f"initial{initial:g}_trail{trailing:g}_act{activation:g}".replace(".","p")
        report["selected"][key]={}
        for src,srcid in SOURCE_MODELS:
            arr,_,_=simulate(*arrays,srcid,initial,trailing,activation,1)
            for label,fid in FEES:
                sub=fee_mode(arr,fid)
                rec=reports(sub)
                report["selected"][key][f"{src}_{label}"]={
                    "full22":rec["full22"],"positive_months":rec["positive_months"],
                    "train2025":rec["year2025"],"test2026":rec["jan_oct2026"],
                    "week":rec["current_partial_week"],
                    "monthly":rec["monthly"],"daily_ist":rec["daily_ist"],
                }
                name=f"{key}_{src.lower()}_{label.lower()}"
                pd.DataFrame(rec["monthly"]).to_csv(OUT/f"{name}_monthly.csv",index=False)
                pd.DataFrame(rec["daily_ist"]).to_csv(OUT/f"{name}_daily.csv",index=False)
                weekarr=sub[(sub[:,1]>=WEEK_START)&(sub[:,1]<END)]
                ledger_frame(weekarr).to_csv(OUT/f"{name}_weekly_trades.csv",index=False)
    (OUT/"summary.json").write_text(json.dumps(report,indent=2)+"\n")
    for label,z in report["rankings"].items():
        print("ATR_GRID_RANK",label,json.dumps({
            "weekly":z["top10_week"][0],
            "full22":z["top10_full22"][0],
            "months":z["top10_positive_months"][0],
            "train2025_then_holdout":z["best_2025_train_then_2026_holdout"],
            "positive_full22":z["positive_full22_both_sources"],
        }),flush=True)
    print("ATR_ONLY_15M_MULTIVALUE_GRID_SUCCESS",str(OUT),flush=True)

if __name__=="__main__":
    main()
