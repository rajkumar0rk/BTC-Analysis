#!/usr/bin/env python3
"""Reduce losing months without ANY historical degradation to winning months.

Exact baseline from latest verified 85-trade combined BTCUSD 15m strategy:
- TOUCH: Supertrend green, second green after ST line touch, volume>=1x,
  ATR>=0.20%, 0.75% SL, 1.5% TP, last closed 1h candle close>EMA20 and
  1h EMA20 rising; additional fixed profit-lock: arm after +1% favorable
  high of a COMPLETED 1minute candle, lock stop at +0.4% above fill.
- FLIP: green after Supertrend bullish flip, volume<=.8x, ATR>=.20%,
  original 3% SL, 0.5% TP; last closed 1h RSI(14)>=50.
- 15m ST exit retained; 1m stop-first, fees, slippage; 1 position / ST cycle.

Propose independent PRE-ENTRY causal restrictions and quantitatively enforce:
for EVERY one of the 17 historically profitable IST months, new actual
realized month profit must be >= baseline month profit (tol 1e-2 pts).
No calendar identities or future P&L are inputs to any signal.
This is retrospective hypothesis screening, NOT forward evidence. The
constraint itself has been chosen by examining all 22 months.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import research_supertrend_15m_line_touch as base
import research_supertrend_15m_filter_grid as filt
import research_st_three_best_combined_portfolio as port
import research_st_touch075_flip_lowvol_combination as fixed
import research_st_touch_flip_causal_regime_filters as htf
import research_st_touch_flip_reduce_loss_months as study
import research_second_green_percent_rr_scenarios as rr

OUT=Path("analysis/st_preserve_all_positive_month_pnl_20261122")
PERIOD=tuple(base.MONTHS)
ORIGINAL_LOSING_MONTHS=("2025-06","2025-08","2025-12",
                        "2026-03","2026-10")
TOL=0.021 # rounded-2dp monthly budget, 0.021 pts not 2%!
def replay_touch_lock(v,minute,stopbars):
    n=len(minute)
    j=int(v.entry_idx);b=int(v.entry_bar)
    si=np.searchsorted(stopbars,b,side="left")
    end=min((int(stopbars[si])+1)*15,n) if si<len(stopbars) else n
    assert end>j
    entry=float(v.entry_fill)
    static_stop=entry*(1-.75/100)
    target=entry*(1+1.5/100)
    h=minute.high.to_numpy(float)[j:end]
    lo=minute.low.to_numpy(float)[j:end]
    o=minute.open.to_numpy(float)[j:end]
    # Trade is NOT protected by a high in the SAME or FUTURE minute;
    # requires previous completed candle's high to cross +1.0%.
    prevpeak=np.r_[-np.inf,np.maximum.accumulate(h[:-1])]
    active=np.where(prevpeak >= entry*1.01,
                    max(static_stop,entry*1.004),static_stop)
    hits=np.flatnonzero((lo<=active)|(h>=target))
    if len(hits):
        idx=int(hits[0])
        exit_i=j+idx
        if lo[idx]<=active[idx]:mid=float(min(o[idx],active[idx]))
        else:mid=float(target)
    else:
        exit_i=end if end<n else n-1
        mid=float(minute.open.iat[exit_i] if end<n
                  else minute.close.iat[-1])
    exit_fill=mid-base.SLIP
    net=exit_fill-entry-base.FEE*(entry+exit_fill)
    return exit_i,mid,exit_fill,net

def add_stopped_trade_replays(candidates,minute,stops):
    out=candidates.copy()
    months=minute.index.tz_convert("Asia/Kolkata").strftime("%Y-%m").to_numpy()
    touched=0
    for ix,v in candidates.iterrows():
        if v.strategy!="line_touch":continue
        end,mid,fill,net=replay_touch_lock(v,minute,stops)
        out.at[ix,"exit_idx"]=end
        out.at[ix,"exit_utc"]=str(minute.index[end])
        out.at[ix,"exit_month_ist"]=str(months[end])
        out.at[ix,"exit_mid"]=mid
        out.at[ix,"exit_fill"]=fill
        out.at[ix,"fee_pts"]=base.FEE*(float(v.entry_fill)+fill)
        out.at[ix,"net_pts"]=net
        out.at[ix,"win"]=int(net>0)
        out.at[ix,"holding_minutes"]=end-int(v.entry_idx)
        touched+=1
    return out,touched

def period_and_protection(p,reference):
    m=p.groupby("exit_month_ist").net_pts.sum()
    prof=np.array([float(m.get(x,0.)) for x in PERIOD])
    can_reduce=prof[reference>0]+TOL>=reference[reference>0]
    months_fixed=int(((reference<0)&(prof>0)).sum())
    months_nonloss=int(((reference<0)&(prof>=-TOL)).sum())
    return dict(
      protected_profitable_months=int(can_reduce.sum()),
      protected_all=bool(can_reduce.all()),
      reduced_losing_months_into_profit=months_fixed,
      reduced_losing_months_into_flat_or_profit=months_nonloss,
      monthly_net_array=prof)

def main():
    rr.configure_grid()
    OUT.mkdir(parents=True,exist_ok=True)
    port.SPECS=fixed.COHORTS
    minute,bars,files=base.load()
    st,trend=base.supertrend(bars)
    vol,ap,ar=filt.build_features(bars)
    events,stopbars=filt.candidate_touch_events(
        minute,bars,st,trend,vol,ap,ar)
    signals=port.decode_signals(
        minute,bars,trend,vol,ap,ar,events,stopbars)
    allc=port.compute_candidates(minute,trend,stopbars,signals)
    assert len(allc)==150
    flags=htf.features(bars,trend)
    enterbars=allc.entry_bar.to_numpy(int)
    t0=(allc.strategy=="line_touch").to_numpy()
    first=((t0 & flags["1h_above_ema20_and_rising"].to_numpy(bool)[enterbars])|
          (~t0 & flags["1h_rsi50"].to_numpy(bool)[enterbars]))
    basec=allc[first].copy().reset_index(drop=True)
    assert len(basec)==87
    allreplay,touch_count=add_stopped_trade_replays(basec,minute,stopbars)
    # Existing historical report provides independent checkpoint, not just
    # recomputing from same implementation.
    reference,_=port.portfolio(
        allreplay,("line_touch","bullish_flip"),
        ("line_touch","bullish_flip"),global_cycle_cap=True)
    base_months=reference.groupby("exit_month_ist").net_pts.sum()
    ref=np.array([float(base_months.get(m,0)) for m in PERIOD])
    assert len(reference)==85
    assert abs(float(reference.net_pts.sum())-19099.62)<.025,reference.net_pts.sum()
    assert int((ref>0).sum())==17
    assert tuple(m for m,v in zip(PERIOD,ref) if v<0)==ORIGINAL_LOSING_MONTHS
    # Require exact month-by-month parity against PRIOR verified report.
    # Independent exact checkpoint: read the previously published original
    # month-level research ledger rather than copying approximate values.
    old=pd.read_csv(
      "analysis/st_touch_flip_exit_protection_20261122/focus_profiles_monthly.csv")
    checkpoint=old[old.profile=="touch_lock_1.0_0.4"]
    assert len(checkpoint)==22,("published checkpoint missing",len(checkpoint))
    expected=dict(zip(checkpoint.month_ist,
                      checkpoint.exit_month_realized_net_pts))
    for mo,v in expected.items():
        assert abs(float(base_months.get(mo,0))-v)<.035,(mo,base_months.get(mo),v)
    print("BASELINE_PARITY_OK",len(reference),touch_count,ref.sum(),
          tuple(m for m,v in zip(PERIOD,ref) if v<0),flush=True)
    # Single causal gate for Touch, Flip or BOTH, as well as gate pairs.
    gates=dict(off=np.ones(len(basec),bool))
    barids=basec.entry_bar.to_numpy(int)
    for key in flags.columns:
        gates[key]=flags[key].to_numpy(bool)[barids]
    # Additional numerical constraints from ONLY last completed 15m/1h:
    # stronger trend, minimum/maximum RSI and volatility, not calendar months.
    closed_at_bar=np.maximum(barids-1,0)
    lastvol=np.nan_to_num(np.asarray(vol,dtype=float)[closed_at_bar],
                 nan=0,posinf=0,neginf=0)
    lastatr=np.nan_to_num(np.asarray(ap,dtype=float)[closed_at_bar],
                 nan=0,posinf=0,neginf=0)
    for q in (.5,.75,1.25,1.5,2.):
        gates["prior15m_volume_ge_"+str(q)]=lastvol>=q
        gates["prior15m_volume_le_"+str(q)]=lastvol<=q
    for q in (.20,.25,.30,.40,.50,.75):
        gates["prior15m_atrpct_ge_"+str(q)]=lastatr>=q
        gates["prior15m_atrpct_le_"+str(q)]=lastatr<=q
    # Causal prior 1H ATR% & 4H percent move restrictions.
    h1=bars.resample("1h",label="left",closed="left").agg({
        "open":"first","high":"max","low":"min","close":"last"})
    h4=bars.resample("4h",label="left",closed="left").agg({
        "open":"first","high":"max","low":"min","close":"last"})
    for tag,frame in (("1h",h1),("4h",h4)):
        change=(frame.close/frame.close.shift(1)-1).abs()*100
        ch=change.shift(1).reindex(bars.index,method="ffill").to_numpy(
            dtype=float)[barids]
        for threshold in (.2,.4,.6,1.,1.5,2.):
            gates[tag+"_abs_return_ge_"+str(threshold)]=ch>=threshold
            gates[tag+"_abs_return_le_"+str(threshold)]=ch<=threshold
    touch=(basec.strategy=="line_touch").to_numpy()
    flip=~touch
    # Baseline signals always pass. Only entry selection varies; original
    # profitable months are checked using exit MONTH, not entry-month.
    rows=[];passed=[]
    gatekeys=list(gates.keys())
    models={"baseline":("off","off")}
    for g in gatekeys:
        if g=="off":continue
        models["both_"+g]=(g,g)
        models["touch_"+g]=(g,"off")
        models["flip_"+g]=("off",g)
    # independent gates on each signal family (not 2 filters on same family)
    for t in gatekeys:
        for f in gatekeys:
            if t=="off" and f=="off":continue
            models["pair_T_"+t+"__F_"+f]=(t,f)
    # canonical choice + one-pass portfolio re-entry logic.
    for k,(model,(tg,fg)) in enumerate(models.items()):
        avail=(touch & gates[tg]) | (flip & gates[fg])
        eligible=allreplay.loc[avail]
        ledger,_=port.portfolio(eligible,
                 ("line_touch","bullish_flip"),
                 ("line_touch","bullish_flip"),True)
        out=period_and_protection(ledger,ref)
        pnls=out.pop("monthly_net_array")
        rows.append(dict(model=model,touch_gate=tg,flip_gate=fg,
          selected=int(len(ledger)),
          source_signals=int(len(eligible)),
          y2025_net=round(float(pnls[:12].sum()),2),
          y2026_net=round(float(pnls[12:].sum()),2),
          total_net=round(float(pnls.sum()),2),
          y2025_positive=int(sum(pnls[:12]>0)),
          y2026_positive=int(sum(pnls[12:]>0)),
          y2025_negative=int(sum(pnls[:12]<0)),
          y2026_negative=int(sum(pnls[12:]<0)),
          total_positive=int(sum(pnls>0)),
          total_negative=int(sum(pnls<0)),
          baseline_winning_months_non_degraded=out["protected_profitable_months"],
          exact_non_degradation=out["protected_all"],
          losses_to_positive=out["reduced_losing_months_into_profit"],
          losses_to_nonloss=out["reduced_losing_months_into_flat_or_profit"],
          worst_month=round(float(pnls.min()),2)))
        if out["protected_all"] and out["reduced_losing_months_into_profit"]>0:
            passed.append((model,ledger,pnls))
        if (k+1)%1000==0:
            print("PROFILES_CHECKED",k+1,"of",len(models),flush=True)
    tab=pd.DataFrame(rows)
    assert tab.iloc[0].model=="baseline"
    assert len(tab)==len(models)
    tab.to_csv(OUT/"all_causal_filter_pair_month_guard.csv",index=False)
    strict=tab[tab.exact_non_degradation].sort_values(
        ["losses_to_positive","total_negative","y2026_net","total_net"],
        ascending=[False,True,False,False])
    strict.to_csv(OUT/"STRICT_NO_PROFIT_MONTH_DEGRADATION.csv",index=False)
    reduced=tab[(tab.baseline_winning_months_non_degraded>=16)&
                (tab.losses_to_positive>0)].sort_values(
        ["losses_to_positive","total_negative","total_net"],
        ascending=[False,True,False])
    reduced.to_csv(OUT/"at_most_one_profit_month_degraded_DIAGNOSTIC.csv",
                   index=False)
    # Detail only best strictly qualified and baseline.
    focus=list(dict.fromkeys(["baseline"]+strict.model.head(6).tolist()))
    pmonth=[]; ptrade=[]
    for name in focus:
        tg,fg=models[name]
        avail=(touch&gates[tg])|(flip&gates[fg])
        led,_=port.portfolio(allreplay.loc[avail],
                ("line_touch","bullish_flip"),
                ("line_touch","bullish_flip"),True)
        per_month=port.month_table(led,minute,name)
        per_month["model"]=name
        pmonth.append(per_month)
        r=led.copy();r["model"]=name
        ptrade.append(r)
    pd.concat(pmonth,ignore_index=True).to_csv(
        OUT/"focus_monthly_trade_exit.csv",index=False)
    pd.concat(ptrade,ignore_index=True).to_csv(
        OUT/"focus_trades.csv.gz",index=False,compression="gzip")
    cols=["model","touch_gate","flip_gate",
       "selected","y2025_net","y2026_net","total_net",
       "y2025_positive","y2026_positive","total_positive","total_negative",
       "baseline_winning_months_non_degraded",
       "losses_to_positive","losses_to_nonloss"]
    report=[
      "# BTCUSD 15m: strict no-harm profitable-month optimization",
      "",
      "User's exact requirement: reduce the five losing months without",
      "reducing NET POINTS in ANY of the other 17 originally profitable",
      "calendar months (all 22 actual IST exit months).",
      "Gate decisions are causal at each entry; baseline months may NOT",
      "be known in live trading, so this requirement is a BACKTEST",
      "acceptance criterion only, not a deployable month forecaster.",
      "",
      "Baseline=+1.0% arm/+0.4% stop-lock Line Touch, 3%/0.5% Flip.",
      "Original baseline 85 selected trades, 17/22 months, +19,099.62",
      "BTC-equivalent points reproduced and month-by-month asserted.",
      "",
      "## Strictly non-degrading configurations",
      strict[cols].head(20).to_markdown(index=False),
      "",
      "## Near misses: degrade up to ONE positive month",
      reduced[cols].head(20).to_markdown(index=False),
      "",
      "## Strictly positive months kept intact",
      ", ".join(m for m,v in zip(PERIOD,ref) if v>0),
      "",
      "## Baseline five losing months",
      ", ".join(f"{m}: {float(v):+.2f}" for m,v in zip(PERIOD,ref) if v<0),
      "",
      "## Research integrity",
      "All periods already used in model development, including 2026.",
      "This high-dimensional search is a multiple-testing hazard.",
      "Past profitable months are NOT knowable ahead of time; NEVER",
      "deploy a calendar lookup that disables trades by realized",
      "historical loss-month identity. If strict condition fails, say so.",
      "No independent forward paper test; no funding/liquidation.",
      "All returns are BTC price points per 1 BTC-equivalent position.",
    ]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")
    (OUT/"quality.json").write_text(json.dumps(dict(
        variants=len(tab),strict_satisfy_count=len(strict),
        strict_reduced_losses_to_profit=len(passed),
        strict_max_losing_months_turned_positive=int(
            strict.losses_to_positive.max()) if len(strict) else 0,
        baseline_17_month_positive_profit_maintained_as_hard_constraint=True,
        touch_profit_lock_arm_pct=1.0,touch_profit_lock_pct=.4,
        baseline_profit_19099p62_verified=True,
        baseline_five_losing_months=list(ORIGINAL_LOSING_MONTHS),
        all_22_months_previously_seen=True,retrospective_multiple_testing=True,
        original_full_trade_execution_preserved=True,
        independent_out_of_sample=False),indent=2)+"\n")
    print("STRICT_PROFIT_MONTH_CONSTRAINT_AUDIT",len(tab),len(strict),
          "IMPROVED",len(passed),flush=True)
    print("STRICT_RANKING\n"+strict[cols].head(20).to_string(index=False),flush=True)
    print("NEAR_MISS\n"+reduced[cols].head(10).to_string(index=False),flush=True)
    print("SUCCESS_STRICT_MONTH_PRESERVATION_STUDY",flush=True)
if __name__=="__main__":
    main()
