#!/usr/bin/env python3
"""BTCUSD ST 15m: causal filters on fixed 0.75/1.5 Touch plus 3/0.5 Flip.

2025-only parameter ranking, 2026 Jan-Oct evaluation. Existing baseline
settings already selected using both periods: not an untouched holdout.
Preserve the existing 1m backtester, fees, ST close exit and exclusivity.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import research_supertrend_15m_line_touch as base
import research_supertrend_15m_filter_grid as filt
import research_st_three_best_combined_portfolio as portfolio
import research_st_touch075_flip_lowvol_combination as previous
import research_second_green_percent_rr_scenarios as rr

OUT=Path("analysis/st_touch_flip_causal_regime_filters_20261122")
PRIORITY=("line_touch","bullish_flip")
MONTHS=base.MONTHS
PERIODS={"2025_H1":MONTHS[:6],"2025_H2":MONTHS[6:12],
 "2025_full":MONTHS[:12],"2025_JanOct":MONTHS[:10],
 "2026_H1":MONTHS[12:18],"2026_JulOct":MONTHS[18:22],
 "2026_JanOct":MONTHS[12:22]}

def indicators(frame):
    close=frame.close.astype(float)
    ema20=close.ewm(span=20,adjust=False).mean()
    ema50=close.ewm(span=50,adjust=False).mean()
    up=frame.high.astype(float).diff()
    down=-frame.low.astype(float).diff()
    tr=pd.concat([frame.high-frame.low,
       (frame.high-close.shift(1)).abs(),
       (frame.low-close.shift(1)).abs()],axis=1).max(axis=1)
    atr=tr.ewm(alpha=1/14,adjust=False,min_periods=14).mean()
    pdi=100*up.where((up>down)&(up>0),0.).ewm(
         alpha=1/14,adjust=False,min_periods=14).mean()/atr
    mdi=100*down.where((down>up)&(down>0),0.).ewm(
         alpha=1/14,adjust=False,min_periods=14).mean()/atr
    dx=(100*(pdi-mdi).abs()/(pdi+mdi).replace(0,np.nan))
    adx=dx.ewm(alpha=1/14,adjust=False,min_periods=14).mean()
    d=close.diff()
    gain=d.clip(lower=0).ewm(alpha=1/14,adjust=False,
                                   min_periods=14).mean()
    loss=(-d.clip(upper=0)).ewm(alpha=1/14,adjust=False,
                                   min_periods=14).mean()
    rsi=100-100/(1+gain/loss.replace(0,np.nan))
    return {
      "above_ema20":close>ema20,
      "above_ema50":close>ema50,
      "ema20_rising":ema20>ema20.shift(3),
      "adx20":adx>=20,
      "adx25":adx>=25,
      "bull_di":pdi>mdi,
      "rsi50":rsi>=50,
      "rsi55":rsi>=55}

def features(bars,trend):
    f=pd.DataFrame(index=bars.index)
    for tf,frame in (("15m",bars),
             ("1h",bars.resample("1h",label="left",closed="left").agg({
               "open":"first","high":"max","low":"min","close":"last"})),
             ("4h",bars.resample("4h",label="left",closed="left").agg({
               "open":"first","high":"max","low":"min","close":"last"}))):
        for key,s in indicators(frame).items():
            # Causal: previous completed TF candle only.
            q=s.shift(1).reindex(bars.index,method="ffill").fillna(False)
            f[tf+"_"+key]=q.astype(bool)
    times=bars.index.tz_convert("Asia/Kolkata")
    f["weekday"]=times.dayofweek<5
    f["tue_thu"]=(times.dayofweek>=1)&(times.dayofweek<=3)
    f["session_9_21"]=(times.hour>=9)&(times.hour<21)
    green_age=np.zeros(len(bars),dtype=int)
    for i in range(1,len(bars)):
        green_age[i]=green_age[i-1]+1 if trend[i-1]==-1 else 0
    f["bull_age_min4"]=green_age>=4
    f["bull_age_min8"]=green_age>=8
    f["bull_age_max16"]=(green_age>0)&(green_age<=16)
    f["1h_above_ema20_and_rising"]=f["1h_above_ema20"]&f["1h_ema20_rising"]
    f["1h_above_ema20_and_adx20"]=f["1h_above_ema20"]&f["1h_adx20"]
    f["1h_bull_di_and_adx20"]=f["1h_bull_di"]&f["1h_adx20"]
    f["4h_above_ema20_and_rising"]=f["4h_above_ema20"]&f["4h_ema20_rising"]
    f["1h_4h_above_ema20"]=f["1h_above_ema20"]&f["4h_above_ema20"]
    f["1h_bull_di_4h_ema20"]=f["1h_bull_di"]&f["4h_above_ema20"]
    f["1h_bull_di_and_4h_bull_di"]=f["1h_bull_di"]&f["4h_bull_di"]
    f["1h_above_ema20_weekday"]=f["1h_above_ema20"]&f["weekday"]
    f["1h_above_ema20_age4"]=f["1h_above_ema20"]&f["bull_age_min4"]
    f["1h_adx20_4h_adx20"]=f["1h_adx20"]&f["4h_adx20"]
    return f

def evaluate(trades):
    mon=trades.groupby("exit_month_ist").net_pts.sum()
    z={}
    for name,m in PERIODS.items():
        s=trades[trades.exit_month_ist.isin(m)]
        arr=np.array([float(mon.get(x,0)) for x in m])
        z[name+"_net"]=round(float(s.net_pts.sum()),2)
        z[name+"_trades"]=int(len(s))
        z[name+"_win_months"]=int((arr>0).sum())
        z[name+"_loss_months"]=int((arr<0).sum())
        z[name+"_flat_months"]=int((arr==0).sum())
        z[name+"_win_trades"]=int(s.win.sum())
    values=trades.sort_values("exit_idx").net_pts.to_numpy(float)
    eq=np.r_[0.,np.cumsum(values)]
    z["closed_equity_max_drawdown_pts"]=round(float(
        np.max(np.maximum.accumulate(eq)-eq)),2)
    z["total_trades"]=int(len(trades))
    z["total_net_pts"]=round(float(values.sum()),2)
    return z

def main():
    rr.configure_grid()
    portfolio.SPECS=previous.COHORTS
    OUT.mkdir(parents=True,exist_ok=True)
    minute,bars,files=base.load()
    st,trend=base.supertrend(bars)
    vol,atpct,atrel=filt.build_features(bars)
    events,stops=filt.candidate_touch_events(
        minute,bars,st,trend,vol,atpct,atrel)
    signals=portfolio.decode_signals(
        minute,bars,trend,vol,atpct,atrel,events,stops)
    candidates=portfolio.compute_candidates(minute,trend,stops,signals)
    baseline,_=portfolio.portfolio(
       candidates,tuple(previous.COHORTS),PRIORITY,True)
    baseline_stats=evaluate(baseline)
    assert len(baseline)==143 and baseline_stats["2025_full_net"]==10060.42
    assert baseline_stats["2026_JanOct_net"]==548.16
    print("BASELINE_PARITY_PASS",json.dumps(baseline_stats),flush=True)
    f=features(bars,trend)
    tests=[("baseline","off","off")]
    for gate in f.columns:
        tests.extend([
          ("both_"+gate,gate,gate),
          ("touch_"+gate,gate,"off"),
          ("flip_"+gate,"off",gate)])
    masks={"off":np.ones(len(candidates),dtype=bool)}
    bar_index=candidates.entry_bar.to_numpy(dtype=int)
    for name in f.columns:
        masks[name]=f[name].to_numpy(dtype=bool)[bar_index]
    is_touch=(candidates.strategy=="line_touch").to_numpy()
    is_flip=~is_touch
    rows=[]
    for name,touch,flip in tests:
        eligible=((is_touch & masks[touch]) |
                  (is_flip & masks[flip]))
        available=candidates[eligible]
        kept,meta=portfolio.portfolio(
            available,tuple(previous.COHORTS),PRIORITY,True)
        rows.append(dict(model=name,touch_filter=touch,flip_filter=flip,
            available_signals=int(len(available)),
            blocked_overlap=meta["blocked_overlaps"],
            blocked_same_cycle=meta["blocked_one_cycle"],
            **evaluate(kept)))
    tab=pd.DataFrame(rows)
    assert len(tab)==1+3*len(f.columns)
    tab["2025_qualified"]=(
       (tab["2025_full_trades"]>=35)&
       (tab["2025_full_win_months"]>=6)&
       (tab["2025_full_net"]>0)&
       (tab["2025_H1_net"]>0)&
       (tab["2025_H2_net"]>0))
    qualified=tab[tab["2025_qualified"]].copy()
    assert len(qualified)>0
    ranked=qualified.sort_values(["2025_full_win_months","2025_full_net"],
                          ascending=[False,False])
    rankedprofit=qualified.sort_values(["2025_full_net","2025_full_win_months"],
                          ascending=[False,False])
    best_month=ranked.iloc[0]
    best_profit=rankedprofit.iloc[0]
    diagnostic=qualified.sort_values(
        ["2026_JanOct_net","2026_JanOct_win_months"],
        ascending=[False,False])
    tab.to_csv(OUT/"all_causal_regime_variants.csv",index=False)
    ranked.to_csv(OUT/"2025_only_training_rankings.csv",index=False)
    diagnostic.to_csv(OUT/"2026_diagnostic_NOT_model_selection.csv",index=False)
    cols=["model","touch_filter","flip_filter",
        "2025_full_trades","2025_full_net","2025_full_win_months",
        "2025_H1_net","2025_H2_net",
        "2026_JanOct_trades","2026_JanOct_net",
        "2026_JanOct_win_months","2026_JanOct_loss_months",
        "2026_H1_net","2026_JulOct_net",
        "total_net_pts","total_trades","closed_equity_max_drawdown_pts"]
    shortlist=tab[tab.model.isin(
        ["baseline",best_month.model,best_profit.model])]
    lines=[
      "# BTCUSD Supertrend Touch + Flip: causal trend filter experiments",
      "",
      "Original ST(10,3), 0.75% SL/1.5% TP Touch, 3% SL/0.5% TP",
      "low-volume Flip. Original 15m closing stop and all 1m execution",
      "costs preserved. One active position; one position per bullish cycle.",
      "Only entry gates change, all taken from COMPLETED 15m, 1h, 4h bars.",
      "",
      "## Baseline and candidates selected using 2025 ONLY",
      shortlist[cols].to_markdown(index=False),
      "",
      "## 2025-qualified results ranked by 2025 winning months",
      ranked[cols].head(20).to_markdown(index=False),
      "",
      "## Strongest 2026 outcomes among 2025-qualified (DIAGNOSTIC ONLY)",
      diagnostic[cols].head(15).to_markdown(index=False),
      "",
      "## Methodology and limitations",
      "Predeclared eligibility: at least 35 trades in 2025; at least 6",
      "profitable months; positive 2025 first and second six-month halves.",
      "Rank by 2025 winning months, then 2025 net points. 2026 NOT used",
      "for selecting these candidates, but the original base settings were",
      "already researched on both years: NOT a pristine forward validation.",
      "Many correlated hypotheses: 2025 fitting may overfit. All prices",
      "are BTC-equivalent points after taker fees, GST and slippage;",
      "no funding, leverage, liquidation, depth or order latency.",
    ]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(lines)+"\n")
    metadata=dict(
      model_count=len(tab),qualified_2025_count=len(qualified),
      selection_uses_2026=False,selected_by_2025_months=best_month.model,
      selected_by_2025_net=best_profit.model,
      baseline_parity=baseline_stats,
      2025_gate_min_trades=35,2025_gate_min_profitable_months=6,
      2025_gate_positive_both_halves=True,
      closed_htf_candles_only=True,original_ST_close_exit_unchanged=True,
      independent_future_validation=False,
      original_settings_preselected_with_2025_2026_data=True)
    (OUT/"quality.json").write_text(json.dumps(metadata,indent=2)+"\n")
    print("TESTS",len(tab),"QUALIFIED",len(qualified),flush=True)
    print("SELECTED_2025\n"+shortlist[cols].to_string(index=False),flush=True)
    print("TOP_2026_DIAGNOSTIC_ONLY\n"+diagnostic[cols].head(12).to_string(index=False),flush=True)
    print("SUCCESS_CAUSAL_FILTER_STUDY",flush=True)

if __name__=="__main__":
    main()
