#!/usr/bin/env python3
"""BTCUSD — Supertrend must turn favorable BEFORE EMA9 crosses EMA21.

Historical research, not a live profit validation.
Pre-registered in analysis/supertrend_first_ema_cross/NOVELTY_CHECK.md.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from research_supertrend_ema921 import source, supertrend, FEE, SLIP, IST, MONTHS
from research_supertrend_ema921_fixed_grid import simulate, scoring, START_MONTH

OUT = Path("analysis/supertrend_first_ema_cross")
THREE = [(100,300),(150,450),(200,600),(300,900),(400,1200),
         (500,1500),(600,1800),(800,2400),(1000,3000)]
FOUR = [(100,400),(200,800),(300,1200),(400,1600),
        (500,2000),(600,2400),(800,3200),(1000,4000)]
EXTRA = [(100,200),(200,2000),(1000,2000)]
PAIRS = THREE + FOUR + EXTRA
assert len(PAIRS) == len(set(PAIRS)) == 20

def strict_crossover(supertrend_direction, ema9, ema21):
    """Supertrend already favorable, then completed EMA crossover; no flip-only entries."""
    st = np.asarray(supertrend_direction, dtype=np.int8)
    f = np.asarray(ema9, dtype=np.float64)
    s = np.asarray(ema21, dtype=np.float64)
    prev_st = np.r_[0, st[:-1]]
    prev_f = np.r_[np.nan, f[:-1]]
    prev_s = np.r_[np.nan, s[:-1]]
    longs = (prev_st == 1) & (st == 1) & (prev_f <= prev_s) & (f > s)
    shorts = (prev_st == -1) & (st == -1) & (prev_f >= prev_s) & (f < s)
    assert not (longs & shorts).any()
    result = np.where(longs, 1, np.where(shorts, -1, 0)).astype(np.int8)
    result[:100] = 0
    return result

def assert_semantics():
    # Flip and crossover on same bar MUST be excluded. A later EMA cross is allowed.
    st = [-1,1,1,1,1]
    f = [1,3,4,2,4]
    s = [2,2,2,3,3]
    # Strip warmup in unit checks by padding at least 100 bars.
    pad = 110
    o = strict_crossover(np.array([1]*pad + st),
                         np.array([1]*pad + f,float),
                         np.array([2]*pad + s,float))
    assert o[pad+1] == 0 and o[pad+4] == 1, ("LONG order",o[-5:])
    # Already EMA above, ST flips green: not a valid new crossover.
    o = strict_crossover([1]*pad + [-1,1,1],
                         [1]*pad + [3,3,3],
                         [2]*pad + [2,2,2])
    assert not np.any(o[pad:]), ("Already aligned",o[-3:])
    # SHORT is symmetric and requires ST negative on the *prior* completed bar.
    st = [1,-1,-1,-1,-1]
    f  = [4,1,0,3,0]
    s  = [2,2,2,2,2]
    o = strict_crossover([-1]*pad + st,
                         [3]*pad + f,
                         [2]*pad + s)
    assert o[pad+1] == 0 and o[pad+4] == -1, ("SHORT order",o[-5:])
    # No crossover: no entry, even though bullish ST and EMA9>EMA21.
    o = strict_crossover([1]*(pad+3), [3]*(pad+3), [2]*(pad+3))
    assert not np.any(o), ("Pure alignment should not enter",o[-3:])
    print("UNIT TESTS PASSED: prior-ST, no simultaneous flip, both directions, no alignment-only",flush=True)

def events(raw: pd.DataFrame, tf: int):
    rule = {5: "5min", 15: "15min", 60: "1h"}[tf]
    b = raw.resample(rule, closed="left", label="left").agg({
        "open":"first","high":"max","low":"min","close":"last","volume":"sum"})
    c = raw.close.resample(rule, closed="left", label="left").count()
    b=b.loc[c.eq(tf)].copy()
    ema9 = b.close.ewm(span=9, adjust=False).mean().to_numpy(float)
    ema21 = b.close.ewm(span=21, adjust=False).mean().to_numpy(float)
    st = supertrend(b, n=10, multiplier=3.0)
    sig = strict_crossover(st,ema9,ema21)
    closing_times = b.index + pd.Timedelta(minutes=tf)
    # A bar's signal cannot be traded until AFTER its final 1m candle closes.
    at = raw.index.get_indexer(closing_times)
    mask = (at>=0) & (sig!=0)
    indices = at[mask].astype(np.int32)
    sides = sig[mask].astype(np.int8)
    assert len(indices)>0
    assert np.all(np.diff(indices)>0)
    assert set(np.unique(sides)).issubset({-1,1})
    stats={"timeframe_minutes":tf,"completed_bars":len(b),
           "raw_crossover_long":int((sig==1).sum()),
           "raw_crossover_short":int((sig==-1).sum()),
           "valid_event_count":len(indices),
           "rejected_at_edge_or_unavailable_close":int(((at<0)&(sig!=0)).sum())}
    return indices,sides,stats

def main():
    assert_semantics()
    OUT.mkdir(parents=True,exist_ok=True)
    raw,gaps = source()
    if gaps:
        raise RuntimeError("Gaps in actual 1m archive: "+str(gaps[:5]))
    local=raw.index.tz_convert(IST)
    months=np.asarray(local.year,dtype=np.int32)*12 + np.asarray(local.month,dtype=np.int32)
    op=raw.open.to_numpy(float)
    hi=raw.high.to_numpy(float)
    lo=raw.low.to_numpy(float)
    cl=raw.close.to_numpy(float)
    summaries=[];monthly=[];ledgers=[];signal_stats={}
    for tf in (5,15,60):
        evt, sides, stats=events(raw, tf)
        signal_stats[str(tf)]=stats
        print("TIMEFRAME", tf, json.dumps(stats),flush=True)
        for sl,tp in PAIRS:
            ratio="1:3" if (sl,tp) in THREE else (
                  "1:4" if (sl,tp) in FOUR else "other")
            trade=simulate(op,hi,lo,cl,months,evt,sides,float(sl),float(tp))
            score,mo,_=scoring(trade,months,tf,sl,tp)
            summaries.append({**score, "risk_reward_ratio":ratio})
            monthly.extend([{**m,"risk_reward_ratio":ratio} for m in mo])
            ei,xi,sd,reason,gross,fees,net,pct=trade
            count=len(ei)
            ledger=pd.DataFrame({"timeframe":[f"{tf}m"]*count,
                "sl_points":[sl]*count, "tp_points":[tp]*count,
                "risk_reward_ratio":[ratio]*count,
                "entry_ist":local[ei].astype(str),
                "exit_ist":local[xi].astype(str),
                "month_ist":[MONTHS[int(i)] for i in months[xi]-START_MONTH],
                "side":np.where(sd==1,"LONG","SHORT"),
                "exit_reason":np.array(["stop","target","stop_gap",
                    "stop_first_both","month_flat","end_of_data"])[reason],
                "gross_points_per_btc":np.round(gross,4),
                "fees_gst_per_btc":np.round(fees,4),
                "slippage_points_per_btc":[2*SLIP]*count,
                "net_points_per_btc":np.round(net,4),
                "net_trade_1x_return_pct":pct,
                "entry_index":ei, "exit_index":xi})
            ledgers.append(ledger)
            print("RESULT",json.dumps({
                "tf":tf,"sl":sl,"tp":tp,"trades":score["trades"],
                "wins":score["wins"],"win_pct":round(score["win_rate_pct"],2),
                "positive_months":score["positive_months_22"],
                "net_1x_pct":round(score["total_net_1x_account_return_pct"],4)
            }),flush=True)
    sm=pd.DataFrame(summaries)
    mo=pd.DataFrame(monthly)
    assert len(sm)==60 and len(mo)==22*60
    sm.to_csv(OUT/"summary.csv",index=False)
    mo.to_csv(OUT/"monthly_results.csv",index=False)
    pd.concat(ledgers,ignore_index=True).to_csv(
        OUT/"trade_ledger.csv.gz",index=False,compression="gzip")
    best=sm.sort_values(["total_net_1x_account_return_pct",
                         "positive_months_22"],ascending=False)
    most=sm.sort_values(["positive_months_22",
                         "total_net_1x_account_return_pct"],ascending=False)
    results=best.head(15)
    quality={"source":"Authentic Delta Exchange India BTCUSD perpetual 1-minute candles",
       "start_utc":str(raw.index[0]),"end_utc":str(raw.index[-1]),
       "1m_candles":len(raw),"missing_candle_gaps":gaps,
       "entries":"ST trend must be positive for previous AND current completed bar; EMA9 then crosses EMA21 on current completed bar; inverse for short",
       "unit_tests":"PASSED explicit prior-ST, simultaneous flip exclusion, already-aligned exclusion, symmetric short tests",
       "ratio_1_to_3":THREE,"ratio_1_to_4":FOUR,"other_pairs":EXTRA,
       "independent_timeframes_minutes":[5,15,60],
       "variants":len(sm),"fee_including_gst_per_side":FEE,
       "adverse_slippage_points_each_side":SLIP,
       "signal_event_counts":signal_stats,
       "data_caveat":"IST January 2025 first 330 minutes unavailable; other 21 IST months complete",
       "validation_caveat":"Historical data used previously; 2026 not blind out-of-sample; no funding, order book or liquidation",
       "drawdown_measure":"Peak to trough only at closed trades, not open-equity maximum"}
    (OUT/"quality.json").write_text(json.dumps(quality,indent=2))
    cols=["timeframe","sl_points","tp_points","risk_reward_ratio","trades",
          "wins","losses","win_rate_pct","profit_factor",
          "total_net_1x_account_return_pct","positive_months_22",
          "max_trade_close_drawdown_pct"]
    report=["# BTCUSD — Supertrend GREEN FIRST, then EMA9/21 bullish crossover",
        "",
        "## This entry is NOT the earlier first-alignment backtest",
        "",
        "LONG requires Supertrend green on previous and current completed bars,",
        "then EMA9 crosses above EMA21 **on the current closed bar**.",
        "SHORT symmetric. Both indicators flipping simultaneously is NOT an entry.",
        "Enter next real 1m candle open after trigger close.",
        "",
        "## Top 15 total 1x returns, net of fees/GST/slippage",
        "",results[cols].to_markdown(index=False,floatfmt=".2f"),"",
        "## 15 most profitable-month configurations",
        "",most.head(15)[cols].to_markdown(index=False,floatfmt=".2f"),"",
        "## Requested 100/300, 200/600, 200/800 comparisons",
        "",
        sm[(sm.sl_points.eq(100)&sm.tp_points.eq(300))|
           (sm.sl_points.eq(200)&sm.tp_points.isin([600,800]))][cols].to_markdown(index=False,floatfmt=".2f"),
        "",
        "## All 60 configurations"]
    for tf in (5,15,60):
        report += [f"### {tf}-minute", "",
            sm[sm.timeframe.eq(f"{tf}m")][cols].to_markdown(index=False,floatfmt=".2f"), ""]
    report += ["## Research interpretation and execution assumptions", "",
        "- 60 independent variants (5m, 15m, 1H x 20 exit pairs), real 1m entry and intrabar exit OHLC replay.",
        "- Stop-first when SL and TP touch within the same 1m candle; adverse open when stop gapped.",
        "- Single position at once; signals during open positions ignored; month-end IST flat.",
        "- 1x notional compounding, 0.05% taker fee per side plus GST 18%, $5 adverse slippage each side.",
        "- January 2025 IST is incomplete by 330 minutes; all other source months are complete.",
        "- No actual spread, maker fills, funding, liquidation, margin, or depth.",
        "- Historical 2025 and 2026 both research-exposed, not a pristine forward holdout; multiple tests could overfit.",
        "",
        "## Reproduce", "",
        "`python scripts/research_supertrend_first_ema_cross.py`"]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")
    print("COMPLETE",json.dumps({
        "variants":len(sm),"positive_overall":int((sm.total_net_1x_account_return_pct>0).sum()),
        "max_positive_months":int(sm.positive_months_22.max()),
        "best":best.iloc[0][cols].to_dict()}),flush=True)

if __name__=="__main__":
    main()
