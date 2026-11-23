#!/usr/bin/env python3
"""Count BTCUSD 15M strategy trades touching +0.158% FAVORABLE market move
before their original exit. Uses 1m OHLC replay, with exit-minute path order
constrained by original stop/TP/flip, not an early-take-profit backtest.

Input trades are already archived from BTC-only 15m branch, in two hypothesized
1m price path orders; compare to avoid exit-candle lookahead. No 1h signals.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from research_ema20_second_touch import read_source, FEE, SLIP

BASE=Path("analysis/btc_only_15m_touch_reclaim_20261123")
OUT=Path("analysis/btc15m_first_0158_favorable_before_exit_20261123")
STRATEGIES=("touch_close_2R","touch_close_3R","reclaim4_2R","reclaim4_3R",
            "combined4_2R","combined4_3R","reclaim8_3R","combined8_3R")
PATHS=("O-H-L-C","O-L-H-C")
MOVES=(0.00158,0.002,0.0025,0.003)
MINUTES=29

def price_levels(filled_entry,side):
    raw_entry=filled_entry/(1+side*SLIP)
    fixed={f"move_{p*100:.3f}pct":raw_entry*(1+side*p) for p in MOVES}
    # PnL includes entry/exit slippage and 0.05% per side taker fee * 1.18 GST.
    # LONG break even: ((1-FEE)*exit_raw*(1-SLIP) - (1+FEE)*entry) >= 0
    # SHORT break even: ((1-FEE)*entry - (1+FEE)*exit_raw*(1+SLIP)) >= 0
    if side==1:
        b=filled_entry*(1+FEE)/((1-FEE)*(1-SLIP))
    else:
        b=filled_entry*(1-FEE)/((1+FEE)*(1+SLIP))
    fixed["exact_fee_gst_slip_break_even"]=b
    return fixed,raw_entry

def first_hit(df_arrays,index0,index1,side,level,reason,stop,target,path):
    """Earliest minute where favorable threshold crossed before original exit.
    Mid-minute order is one hypothesized OHLC path. Entry is 15m bar open.
    For TP/STOP, don't include later excursion in their exit minute.
    """
    o,h,l,c=df_arrays
    if index1<index0: raise ValueError("exit before entry")
    # All preceding minutes are necessarily held open in the archived ledger.
    if index1>index0:
        extremes=h[index0:index1] if side==1 else l[index0:index1]
        hit=np.flatnonzero(extremes>=level if side==1 else extremes<=level)
        if len(hit):return int(index0+hit[0])
    i=index1
    raw_open=float(o[i])
    if side*(raw_open-level)>=0:
        return i
    if reason in ("SUPERTREND_FLIP","STOP_GAP"):
        # Exits at minute open; subsequent minute OHLC must NOT be counted.
        return None
    if reason=="SAMPLE_END_ACCOUNTING_ONLY":
        # Original position held through final minute close.
        extreme=float(h[i] if side==1 else l[i])
        return i if side*(extreme-level)>=0 else None
    if reason not in ("STOP","TP"):
        raise AssertionError(("UNKNOWN_EXIT_REASON",reason))
    seq=(raw_open,float(h[i]),float(l[i]),float(c[i])) if path=="O-H-L-C" else (raw_open,float(l[i]),float(h[i]),float(c[i]))
    # Archived strategy enforces opening gap exits before traversing intraminute bars.
    if side*(raw_open-target)>=0 or side*(raw_open-stop)<=0:
        return None
    cur=seq[0]
    for dest in seq[1:]:
        # Exactly match historical stop/TP event ordering. Each segment monotone.
        if side*(dest-target)>=0:
            endpoint=float(target)
            triggered=True
        elif side*(dest-stop)<=0:
            endpoint=float(stop)
            triggered=True
        else:
            endpoint=float(dest)
            triggered=False
        if side*(endpoint-level)>=0:
            return i
        if triggered:
            return None
        cur=dest
    # When the archived exit flags STOP or TP, that boundary must be reached.
    raise AssertionError(("EXIT_BOUNDARY_NOT_REPLAYED",reason,path,i,stop,target,seq))

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    df,q=read_source("BTCUSD")
    path=BASE/"trades.csv.gz"
    assert path.is_file(),f"Missing archived 15m trade ledger: {path}"
    trades=pd.read_csv(path,compression="gzip")
    summary=pd.read_csv(BASE/"summary.csv")
    t=df.time.to_numpy(np.int64)
    assert len(t)==963030 and len(trades)>0
    arrays=tuple(df[k].to_numpy(float) for k in ("open","high","low","close"))
    subset=trades[trades.config.isin(STRATEGIES)].copy()
    subset["e_sec"]=pd.to_datetime(subset.entry_time_utc,utc=True).astype("int64")//(10**9)
    subset["x_sec"]=pd.to_datetime(subset.exit_time_utc,utc=True).astype("int64")//(10**9)
    subset["e_idx"]=np.searchsorted(t,subset.e_sec.to_numpy(np.int64),side="left")
    subset["x_idx"]=np.searchsorted(t,subset.x_sec.to_numpy(np.int64),side="left")
    assert (t[subset.e_idx.to_numpy()]==subset.e_sec.to_numpy()).all()
    assert (t[subset.x_idx.to_numpy()]==subset.x_sec.to_numpy()).all()
    assert (subset.x_idx>=subset.e_idx).all()
    records=[]
    for row in subset.itertuples(index=False):
        side=1 if row.direction=="LONG" else -1
        lvl,raw=price_levels(float(row.entry),side)
        data=dict(config=row.config,path_assumption=row.path_assumption,direction=row.direction,
                  entry_time_utc=row.entry_time_utc,exit_time_utc=row.exit_time_utc,
                  exit_reason=row.exit_reason,net_usd=float(row.net_usd),
                  entry_mid_before_slippage=raw,original_entry_fill=float(row.entry),
                  original_R=float(row.R), original_stop=float(row.stop),original_target=float(row.target))
        for name,level in lvl.items():
            i=first_hit(arrays,int(row.e_idx),int(row.x_idx),side,level,
                        row.exit_reason,float(row.stop),float(row.target),row.path_assumption)
            data[f"hit_{name}"]=i is not None
            data[f"hit_{name}_within_29min"]=i is not None and (i-int(row.e_idx))<=MINUTES
            if name=="move_0.158pct":
                data["minutes_to_first_0158_touch"]=(i-int(row.e_idx)) if i is not None else np.nan
        records.append(data)
    out=pd.DataFrame(records)
    reports=[]
    for (conf,path),group in out.groupby(["config","path_assumption"],sort=False):
        ref=summary[(summary.config==conf)&(summary.path_assumption==path)].iloc[0]
        assert len(group)==int(ref.trades),(conf,path,len(group),ref.trades)
        hit=group.hit_move_0_158pct if "hit_move_0_158pct" in group else group["hit_move_0.158pct"]
        n=int(hit.sum())
        reports.append(dict(symbol="BTCUSD",signal_tf="15m",config=conf,path_assumption=path,
           total_trades=len(group),hit_0p158_before_exit=n,
           hit_0p158_pct=round(100*n/len(group),2),
           hit_0p158_under_30min=int(group["hit_move_0.158pct_within_29min"].sum()),
           hit_true_cost_breakeven=int(group["hit_exact_fee_gst_slip_break_even"].sum()),
           hit_0p20_before_exit=int(group["hit_move_0.200pct"].sum()),
           hit_0p25_before_exit=int(group["hit_move_0.250pct"].sum()),
           hit_0p30_before_exit=int(group["hit_move_0.300pct"].sum()),
           original_net_return_pct=float(ref.net_return_pct),
           original_positive_trades=int(ref.wins),
           touched_threshold_but_originally_lost=int(((hit)&(group.net_usd<0)).sum()),
           hit_0p158_LONG=int((hit&(group.direction=="LONG")).sum()),
           hit_0p158_SHORT=int((hit&(group.direction=="SHORT")).sum())))
    res=pd.DataFrame(reports)
    # Make exact path sensitivity legible and check all 8 original counts.
    assert len(res)==len(STRATEGIES)*len(PATHS),(len(res),len(STRATEGIES)*len(PATHS))
    assert (res.hit_0p158_before_exit<=res.total_trades).all()
    assert (res.hit_0p158_under_30min<=res.hit_0p158_before_exit).all()
    assert (res.hit_true_cost_breakeven<=res.total_trades).all()
    assert (res.hit_0p20_before_exit<=res.hit_0p158_before_exit).all()
    assert (res.hit_0p25_before_exit<=res.hit_0p20_before_exit).all()
    assert (res.hit_0p30_before_exit<=res.hit_0p25_before_exit).all()
    out.to_csv(OUT/"trade_mfe_flags.csv.gz",index=False,compression="gzip")
    res.to_csv(OUT/"summary.csv",index=False)
    check=res[res.path_assumption=="O-H-L-C"][["config","total_trades",
          "hit_0p158_before_exit","hit_0p158_pct","hit_0p158_under_30min",
          "hit_true_cost_breakeven","hit_0p20_before_exit","hit_0p25_before_exit",
          "original_positive_trades","touched_threshold_but_originally_lost",
          "original_net_return_pct"]]
    desc=[
      "# BTCUSD 15M: How many trades touched +0.158% FAVORABLE before exit?",
      "",
      "**This counts favorable excursion under the ORIGINAL exit logic; it does not simulate exiting at +0.158%.**",
      "BTCUSD only; all entry indicators 15m, trade execution and path ambiguity checked on archived 1m OHLC.",
      "22 completed IST months Jan 2025–Oct 2026; trades include fee, 18% GST and 0.02% per-side slippage on original exits.",
      "The 0.158% hurdle uses BTC underlying quote movement from raw 1m market open at entry (before adverse fill slip).",
      "Exact cost break-even is computed using filled entry, both taker fees + GST and adverse exit slip.",
      "For a stop/TP exit minute, only the movement BEFORE that original stop/TP event on the assumed OHLC path counts.",
      "For a confirmed ST flip or stop gap at minute open, the remainder of that minute is not included.",
      "Within-29-min counts earliest touching minute, not a guarantee of fill or fee promotion eligibility.",
      "",
      "## Results (assumed O-H-L-C path)","",check.to_markdown(index=False),"",
      "O-L-H-C path results and complete trade-level first-touch flags are in the sidecar CSVs.",
      "Touching 0.158% does not imply the eventual trade was profitable; an unexecuted opportunity can reverse before exit.",
      "No tick-level transaction data or funding, bid-ask spread, depth or liquidation." ]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(desc)+"\n")
    (OUT/"quality.json").write_text(json.dumps({
      "source":q,"symbol":"BTCUSD","signal_tf":"15m","execution_tf":"1m",
      "input_trade_file":str(path),"input_trade_rows":int(len(trades)),
      "analyzed_trade_rows":len(out),"original_configs":STRATEGIES,"paths":PATHS,
      "nominal_raw_market_threshold_pct":.158,
      "fee_including_GST_per_side":FEE,"slippage_per_side":SLIP,
      "limitations":"1m assumed O-H-L-C/O-L-H-C price path, not ticks; before original exit not alternative TP backtest"
    },indent=2,default=str)+"\n")
    print("ANALYSIS_DONE",len(reports),len(out),flush=True)
    print(res.to_string(index=False),flush=True)
if __name__=="__main__":
    main()
