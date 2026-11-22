#!/usr/bin/env python3
"""BTCUSD — First EMA9/21 crossover, ONE entry per favorable Supertrend regime.

Historical research, not a live profit validation.
Pre-registered in analysis/supertrend_first_cross_once/NOVELTY_CHECK.md.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from research_supertrend_ema921 import source, supertrend, FEE, SLIP, IST, MONTHS
from research_supertrend_ema921_fixed_grid import simulate, scoring, START_MONTH

OUT = Path("analysis/supertrend_first_cross_once")
THREE = [(100,300),(150,450),(200,600),(300,900),(400,1200),
         (500,1500),(600,1800),(800,2400),(1000,3000)]
FOUR = [(100,400),(200,800),(300,1200),(400,1600),
        (500,2000),(600,2400),(800,3200),(1000,4000)]
EXTRA = [(100,200),(200,2000),(1000,2000)]
PAIRS = THREE + FOUR + EXTRA
assert len(PAIRS) == len(set(PAIRS)) == 20

def first_crossover_once(supertrend_direction, ema9, ema21):
    """One signal at the FIRST qualified EMA cross after each ST flip.

    A regime flip resets eligibility and flip-bar EMA crosses do not count.
    Following the first qualifying crossover, subsequent crosses during that
    same ST regime cannot signal, even if the trade has already exited.
    """
    st = np.asarray(supertrend_direction, dtype=np.int8)
    fast = np.asarray(ema9, dtype=np.float64)
    slow = np.asarray(ema21, dtype=np.float64)
    assert len(st)==len(fast)==len(slow)
    sig = np.zeros(len(st), dtype=np.int8)
    regime = 0
    fired = False
    for i in range(100,len(st)):
        cur = int(st[i])
        if cur != regime:
            regime = cur
            fired = False
            continue   # no entry on Supertrend flip, even simultaneous EMA cross
        if cur not in (-1,1) or st[i-1] != cur or fired:
            continue
        up = (fast[i-1] <= slow[i-1]) and (fast[i] > slow[i])
        down = (fast[i-1] >= slow[i-1]) and (fast[i] < slow[i])
        if (up if cur == 1 else down):
            sig[i] = cur
            fired = True    # consume the ONE entry opportunity for this regime
    return sig

def assert_semantics():
    pad = 110
    def run(st, fast, slow=2):
        return first_crossover_once(
            np.r_[np.zeros(pad,dtype=int),np.asarray(st,dtype=int)],
            np.r_[np.ones(pad,dtype=float),np.asarray(fast,dtype=float)],
            np.r_[np.full(pad,float(slow)),np.full(len(st),float(slow))])[pad:]
    # GREEN regime: first cross-up at index 3; second and third ignored.
    st = [-1,-1,1,1,1,1,1,1,1,1]
    f =  [1,1,1,3,1,3,1,3,1,3]
    o = run(st,f)
    assert np.array_equal(np.flatnonzero(o),[3]) and o[3]==1, ("one LONG per regime",o)
    # Without any EMA9 crossover after the Supertrend flips, do not enter.
    assert not run([-1,-1,1,1,1,1],[3,3,3,3,3,3]).any(), "no crossover no trade"
    # Simultaneous flip and cross at index 2 does not count; index 4 is first eligible.
    o = run([-1,-1,1,1,1,1],[1,1,3,1,3,1])
    assert np.array_equal(np.flatnonzero(o),[4]) and o[4]==1, ("flip-bar cross excluded",o)
    # Supertrend flip resets the allowance: first eligible cross of NEW green is allowed.
    o = run([-1,-1,1,1,1,-1,-1,1,1,1],
            [1,1,1,3,1,1,1,1,3,1])
    assert np.array_equal(np.flatnonzero(o),[3,8]) and np.all(o[[3,8]]==1), (
        "reset one trade each green regime",o)
    # SHORT mirrors the LONG: only first bearish EMA crossover, next ignored.
    o = run([1,1,-1,-1,-1,-1,-1,-1,-1,-1],
            [3,3,3,1,3,1,3,1,3,1])
    assert np.array_equal(np.flatnonzero(o),[3]) and o[3]==-1, ("one SHORT per red",o)
    print("UNIT TESTS PASSED: first cross only, no crossover no trade, "
          "simultaneous flip excluded, one trade per ST color cycle, "
          "reset on flip, symmetric short",flush=True)

def events(raw: pd.DataFrame, tf: int):
    rule = {5: "5min", 15: "15min", 60: "1h"}[tf]
    b = raw.resample(rule, closed="left", label="left").agg({
        "open":"first","high":"max","low":"min","close":"last","volume":"sum"})
    c = raw.close.resample(rule, closed="left", label="left").count()
    b=b.loc[c.eq(tf)].copy()
    ema9 = b.close.ewm(span=9, adjust=False).mean().to_numpy(float)
    ema21 = b.close.ewm(span=21, adjust=False).mean().to_numpy(float)
    st = supertrend(b, n=10, multiplier=3.0)
    sig = first_crossover_once(st,ema9,ema21)
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
           "first_crossover_once_long":int((sig==1).sum()),
           "first_crossover_once_short":int((sig==-1).sum()),
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
       "entries":"Exactly FIRST same-direction EMA9/21 crossover after ST has already turned favorable; at most ONE signal per ST regime; no crossover no trade; reset on ST flip; symmetric SHORT",
       "unit_tests":"PASSED first-only, no-crossover-no-trade, ST regime reset, flip-crossover exclusion, later crosses ignored, symmetric SHORT tests",
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
    report=["# BTCUSD — FIRST EMA9/21 crossover, at most ONE trade per Supertrend GREEN/RED regime",
        "",
        "## This entry differs from first-alignment, unrestricted first-crossover and first-crossover once backtests",
        "",
        "LONG waits for first completed EMA9 cross-up while Supertrend stays GREEN,",
        "then EMA9 crosses above EMA21 **on the current closed bar**.",
        "enter only on this FIRST cross. Further crosses in the SAME Supertrend green cycle are ignored even after exit. SHORT mirrors for first cross-down in red. ST flip resets allowance.",
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
