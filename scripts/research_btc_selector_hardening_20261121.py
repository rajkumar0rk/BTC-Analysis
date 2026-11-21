#!/usr/bin/env python3
"""BTCUSD 1H multi-regime: audit stricter past-only selector against fixed, prior,
shock-only, and no-trade controls, with actual 1M single-account equity replays.
This is a frozen diagnostic, not parameter optimization.
"""
import json
from math import sqrt
from pathlib import Path
import numpy as np
import pandas as pd

import research_btc_regime_attribution_20261121 as base
import research_btc_multiregime_audit_20261121 as original

OUT = Path("analysis/btc_selector_hardening_20261121")
OUT.mkdir(parents=True, exist_ok=True)
MONTHS = [str(x) for x in pd.period_range("2025-01", "2026-10", freq="M")]
BASE_PRIOR = Path("analysis/btc_multiregime_audit_20261121")

def month_start(month):
    return pd.Timestamp(month+"-01",tz="Asia/Kolkata").tz_convert("UTC")

def wilson(p,n):
    if not n:
        return None,None
    z=1.96
    c=(p+z*z/(2*n))/(1+z*z/n)
    d=z*sqrt(p*(1-p)/n+z*z/(4*n*n))/(1+z*z/n)
    return round(max(0,100*(c-d)),2), round(min(100,100*(c+d)),2)

def label_audit(h):
    # No adjacent future bars are used to create the classifier: evidence from
    # earlier frozen prefix-invariance test MUST pass.
    audit=json.loads((BASE_PRIOR/"classifier_audit.json").read_text())
    assert not audit["history_revision_detected"]
    assert audit["mutually_exclusive_primary_state"]
    assert all(t["label_mismatches"]==0 and t["validity_mismatches"]==0
               for t in audit["label_and_validity_history_prefix_invariance"])
    rows=[]
    n=len(h)
    # Every 4h sampling origin is independent in time, though returns can
    # still be serially dependent across market episodes.
    for state in base.STATES:
        for year in ["2025","2026"]:
            state_mask=h.valid & h.regime.eq(state) & (h.index.year==int(year))
            # Restrict to fully observed Jan 2025 - Oct 2026
            state_mask &= (h.index+pd.Timedelta(hours=1)).tz_convert("Asia/Kolkata").strftime("%Y-%m") <= "2026-10"
            next_mask=state_mask.iloc[:-1].to_numpy()
            n_state=int(next_mask.sum())
            persist=int((h.regime.iloc[:-1].to_numpy()[next_mask]==h.regime.iloc[1:].to_numpy()[next_mask]).sum())
            sample=[]
            for j in np.flatnonzero(state_mask.to_numpy()):
                if j%4==0 and j+4<n and pd.notna(h.atr.iat[j]) and h.atr.iat[j]>0:
                    # Forward prices are diagnostic ONLY, not inputs to labels or signal selection.
                    future_close=float(h.close.iat[j+4])
                    future_low=float(h.low.iloc[j+1:j+5].min())
                    future_high=float(h.high.iloc[j+1:j+5].max())
                    sample.append((future_close-float(h.close.iat[j]),
                            (future_high-future_low)/float(h.atr.iat[j])))
            x=np.array(sample)
            num=len(x)
            up=int((x[:,0]>0).sum()) if num else 0
            prob=100*up/num if num else None
            lo,hi=wilson(up/num,num) if num else (None,None)
            directional=None
            if state in ["trend_up","breakout_up"] and num:
                directional=round(prob,2)
            if state in ["trend_down","breakout_down"] and num:
                directional=round(100*(x[:,0]<0).sum()/num,2)
            rows.append(dict(regime=state,year=year,classified_hours=n_state,
                 persistence_next1h_pct=round(100*persist/n_state,2) if n_state else None,
                 nonoverlap4h_samples=num,
                 next4h_up_pct=round(prob,2) if prob is not None else None,
                 next4h_up_wilson_low95=lo,next4h_up_wilson_high95=hi,
                 same_direction_as_regime_pct=directional,
                 mean_next4h_high_low_over_signal_ATR=round(float(x[:,1].mean()),3) if num else None))
    results=pd.DataFrame(rows)
    results.to_csv(OUT/"regime_forward_validation.csv",index=False)
    return audit,results

def decisions_and_maps(candidates):
    prior=pd.read_csv(BASE_PRIOR/"selector_decisions.csv").fillna("")
    if len(prior)!=len(MONTHS)*len(base.STATES):
        raise RuntimeError("Missing prior selector decisions")
    exittime=pd.to_datetime(candidates.exit_utc,utc=True)
    candidate_data=candidates.copy()
    candidate_data["exit_time"]=exittime
    maps={}
    maps["no_trade"]={m:{s:None for s in base.STATES} for m in MONTHS}
    fixed=dict(shock="donchian_breakout",breakout_up="donchian_breakout",
       breakout_down="donchian_breakout",trend_up="trend_pullback",
       trend_down="trend_pullback",range="bollinger_reversion",
       compression=None,mixed=None)
    maps["fixed_logic"]={m:fixed.copy() for m in MONTHS}
    maps["shock_only"]={m:{s:("donchian_breakout" if s=="shock" else None)
                             for s in base.STATES} for m in MONTHS}
    past={(r.month_ist,r.regime):r.strategy if r.strategy!="NO_TRADE" else None
          for r in prior.itertuples(index=False)}
    maps["prior_selector"]={m:{s:past[(m,s)] for s in base.STATES} for m in MONTHS}
    strict={}
    details=[]
    for k,month in enumerate(MONTHS):
        strict[month]={}
        training_months=MONTHS[max(0,k-6):k]
        recent=training_months[-3:]
        begin=month_start(month)
        for state in base.STATES:
            best=None
            evaluated=[]
            if k>=6:
                subset=candidate_data[
                     candidate_data.month_ist.isin(training_months)&
                     (candidate_data.exit_time < begin)&
                     (candidate_data.regime==state)
                ]
                if len(subset) and not subset.exit_time.lt(begin).all():
                    raise RuntimeError("Future training outcome found")
                for strategy in base.SPECS:
                    g=subset[subset.strategy==strategy]
                    n=len(g)
                    active=int(g.month_ist.nunique())
                    r=g.net_R.to_numpy(float)
                    avg=float(np.mean(r)) if n else None
                    sd=float(np.std(r,ddof=1)) if n>1 else None
                    lower=avg-1.645*sd/sqrt(n) if n>1 else None
                    recentr=float(g[g.month_ist.isin(recent)].net_R.sum())
                    eligible=(n>=30 and active>=4 and lower is not None
                        and lower>0 and recentr>0)
                    evaluated.append(dict(month_ist=month,regime=state,
                        strategy=strategy,training_trades=n,
                        active_months=active,train_mean_net_R=round(avg,5) if avg is not None else None,
                        train_one_sided_95pct_lower_mean_net_R=round(lower,5) if lower is not None else None,
                        recent3_net_R=round(recentr,4),
                        eligible=bool(eligible),training_months=",".join(training_months),
                        trained_before_utc=str(begin)))
                    if eligible:
                        ranking=(lower,n)
                        if best is None or ranking>best[0] or (ranking==best[0] and strategy<best[1]):
                            best=(ranking,strategy)
            else:
                evaluated.append(dict(month_ist=month,regime=state,strategy="ALL",
                        training_trades=0,active_months=0,eligible=False,
                        training_months=",".join(training_months),
                        trained_before_utc=str(begin)))
            strict[month][state]=best[1] if best else None
            details.extend(evaluated)
    maps["strict_lower_bound"]=strict
    pd.DataFrame(details).to_csv(OUT/"strict_training_evidence.csv",index=False)
    pd.DataFrame([dict(model=model,month_ist=m,regime=s,
               strategy=strategy or "NO_TRADE") for model,mp in maps.items()
               for m,states in mp.items() for s,strategy in states.items()
              ]).to_csv(OUT/"monthly_regime_strategy_decisions.csv",index=False)
    return maps

def validate_replay(trades):
    if trades.empty:
        return
    t0=pd.to_datetime(trades.entry_utc,utc=True)
    t1=pd.to_datetime(trades.exit_utc,utc=True)
    if not (t1>=t0).all() or not t0.is_monotonic_increasing:
        raise RuntimeError("Trade sequence invalid")
    if not (t0.iloc[1:].to_numpy()>t1.iloc[:-1].to_numpy()).all():
        raise RuntimeError("Overlapping positions: execution parity broken")
    if not (t0.dt.tz_convert("Asia/Kolkata").dt.strftime("%Y-%m")==trades.month_ist).all():
        raise RuntimeError("Entry wrong IST month")
    if not (t1.dt.tz_convert("Asia/Kolkata").dt.strftime("%Y-%m")==trades.month_ist).all():
        raise RuntimeError("Exit crosses IST month-end")
    if not (trades.fee_gst_usd>=0).all() or not (trades.slippage_usd>=0).all():
        raise RuntimeError("Bad execution costs")
    if abs(float(trades.pnl_usd.sum())+base.INITIAL-float(trades.equity_usd.iloc[-1]))>0.001:
        raise RuntimeError("Equity and trade PnL not reconciled")

def monthly(trades,model):
    rows=[]
    equity=base.INITIAL
    for month in MONTHS:
        g=trades.loc[trades.month_ist==month] if not trades.empty else trades
        profit=float(g.pnl_usd.sum()) if len(g) else 0.
        mo=100*profit/equity
        equity+=profit
        rows.append(dict(model=model,month_ist=month,trades=len(g),
          wins=int((g.pnl_usd>0).sum()) if len(g) else 0,
          losses=int((g.pnl_usd<0).sum()) if len(g) else 0,
          monthly_net_return_pct=round(mo,6),
          monthly_net_pnl_usd=round(profit,2),
          month_end_equity_usd=round(equity,4),
          fee_gst_usd=round(float(g.fee_gst_usd.sum()),2) if len(g) else 0,
          slippage_usd=round(float(g.slippage_usd.sum()),2) if len(g) else 0,
          status="Profit" if profit>1e-9 else ("Loss" if profit < -1e-9 else "No trade")))
    if len(trades) and abs(float(trades.equity_usd.iloc[-1])-equity)>0.001:
        raise RuntimeError("Monthly equity mismatch")
    return pd.DataFrame(rows)

def summary(trades,month,model):
    gains=float(trades.loc[trades.pnl_usd>0,"pnl_usd"].sum()) if len(trades) else 0
    losses=-float(trades.loc[trades.pnl_usd<0,"pnl_usd"].sum()) if len(trades) else 0
    eq=np.r_[base.INITIAL,trades.equity_usd.to_numpy(float)] if len(trades) else np.array([base.INITIAL])
    dd=100*(1-eq/np.maximum.accumulate(eq))
    final=float(eq[-1])
    return dict(model=model,trades=int(len(trades)),
      wins=int((trades.pnl_usd>0).sum()) if len(trades) else 0,
      losses=int((trades.pnl_usd<0).sum()) if len(trades) else 0,
      positive_months=int((month.monthly_net_pnl_usd>0).sum()),
      negative_months=int((month.monthly_net_pnl_usd<0).sum()),
      idle_months=int((month.monthly_net_pnl_usd==0).sum()),
      positive_evaluation_months=int((month.loc[month.month_ist>="2025-07","monthly_net_pnl_usd"]>0).sum()),
      net_return_pct=round(100*(final/base.INITIAL-1),4),
      net_pnl_usd=round(final-base.INITIAL,2),
      ending_equity_usd=round(final,2),
      profit_factor=round(gains/losses,4) if losses else None,
      max_trade_close_drawdown_pct=round(float(dd.max()),3),
      total_fee_gst_usd=round(float(trades.fee_gst_usd.sum()),2) if len(trades) else 0,
      total_slippage_usd=round(float(trades.slippage_usd.sum()),2) if len(trades) else 0,
      passes_22_profitable_months=bool((month.monthly_net_pnl_usd>0).all()))

def cost_stress(trades,model):
    results=[]
    if not len(trades):
        return [dict(model=model,extra_roundtrip_bps=bps,net_return_pct=0.,
              ending_account_usd=base.INITIAL,positive_months=0,
              negative_months=0,idle_months=22,
              extra_cost_usd=0.) for bps in (0,2,5,10)]
    start_eq=np.r_[base.INITIAL,trades.equity_usd.to_numpy(float)[:-1]]
    raw_pnl=trades.pnl_usd.to_numpy(float)
    proportional_qty=trades.qty_btc_equiv.to_numpy(float)/start_eq
    entry=trades.entry_price.to_numpy(float)
    for bps in (0,2,5,10):
        eq=base.INITIAL
        by_month={m:0. for m in MONTHS}
        extra_cost_total=0.
        for i,month in enumerate(trades.month_ist):
            curr_extra=eq*proportional_qty[i]*entry[i]*bps/10000
            curr_pnl=eq*raw_pnl[i]/start_eq[i]-curr_extra
            by_month[month]+=curr_pnl
            extra_cost_total+=curr_extra
            eq+=curr_pnl
            if eq<=0: raise RuntimeError("Stress scenario account bankruptcy: "+model)
        pos=sum(v>1e-8 for v in by_month.values())
        neg=sum(v < -1e-8 for v in by_month.values())
        idle=22-pos-neg
        if bps==0 and abs(eq-float(trades.equity_usd.iloc[-1]))>0.001:
            raise RuntimeError("Cost stress 0bps failed exact equity parity")
        results.append(dict(model=model,extra_roundtrip_bps=bps,
           net_return_pct=round(100*(eq/base.INITIAL-1),4),
           ending_account_usd=round(eq,2),
           positive_months=pos,negative_months=neg,idle_months=idle,
           extra_cost_usd=round(extra_cost_total,2)))
    return results

def main():
    one,manifest=base.load()
    h=base.features(one)
    audit,forecast=label_audit(h)
    signal=base.prepare_signals(h)
    candidates=base.run(one,h,signal)
    if len(candidates)!=3800:
        raise RuntimeError("Four-strategy baseline parity lost")
    maps=decisions_and_maps(candidates)
    reports=[]; months=[]; stresses=[]
    for model,mp in maps.items():
        trades,counters=original.portfolio_replay(one,h,signal,mp)
        validate_replay(trades)
        if not trades.empty:
            trades.to_csv(OUT/(model+"_trades.csv"),index=False)
        else:
            (OUT/(model+"_trades.csv")).write_text("month_ist,regime,strategy,entry_utc,exit_utc,pnl_usd\n")
        m=monthly(trades,model)
        s=summary(trades,m,model)
        s.update(counters)
        if model=="prior_selector" and (len(trades)!=221 or abs(s["net_return_pct"]-(-24.0037))>0.02):
            raise RuntimeError("Old selector parity failed")
        if model=="shock_only" and (len(trades)!=301 or abs(s["net_return_pct"]-3.3469)>0.02):
            raise RuntimeError("Shock-only independent replay parity failed")
        if model=="no_trade" and len(trades)>0:
            raise RuntimeError("No-trade control generated trades")
        reports.append(s)
        months.append(m)
        stresses.extend(cost_stress(trades,model))
    sm=pd.DataFrame(reports)
    mon=pd.concat(months,ignore_index=True)
    sc=pd.DataFrame(stresses)
    sm.to_csv(OUT/"comparison_summary.csv",index=False)
    mon.to_csv(OUT/"monthly_by_model.csv",index=False)
    sc.to_csv(OUT/"cost_sensitivity.csv",index=False)
    quality=dict(
        source="Delta India BTCUSD native 1M, SHA256 and timestamp audited",
        native_minutes=len(one),native_partitions=len(manifest["partitions"]),
        state_causal_prefix_invariance_verified=True,
        all_models_on_identical_single_account_1M_engine=True,
        legacy_selector_parity_verified=True,
        shock_only_parity_verified=True,
        calendar_months=22,
        predeclared_comparators=list(maps),
        historical_spread_realized_funding_liquidation_included=False,
        historical_funding_is_rate_proxy_not_settlement=True,
        is_externally_blind_holdout=False,
        cost_stress_hypothetical_not_historical=True)
    (OUT/"quality.json").write_text(json.dumps(quality,indent=2)+"\n")
    lines=[
      "# BTC multi-regime hardening: classifier uncertainty, strict selector and execution costs",
      "",
      "## Why this audit",
      "Prior causal 6-month selector made 221 trades and -24% net; the shock-only strategy had +3.35% but only 10/22 positive months. The question is whether a stronger past-only eligibility gate and intuitive mapping improve reliable month-to-month performance. This is a frozen NON-OPTIMIZED comparator audit, not a search for an ex-post winner.",
      "",
      "## Verification","~~~json",json.dumps(quality,indent=2),"~~~","",
      "Historical-prefix regime labels were invariant in three checks; the regime has only descriptive price-action semantics and no independent ground-truth label. 2025/26 data has been used in previous research, so not externally blind.",
      "",
      "## Results: common 1M exclusive-position account, net after base fees/GST/slip",
      sm.to_markdown(index=False),"",
      "## Per-month net percentage, all 22 complete IST months including no-trade",
      mon.pivot(index="month_ist",columns="model",values="monthly_net_return_pct").round(3).to_markdown(),"",
      "## Historical regime persistence and NEXT 4H direction by year",
      "Forward returns are used ONLY for diagnostics after the state is determined; nonoverlapping four-hour start times; Wilson confidence interval on future up frequency.",
      forecast.to_markdown(index=False),"",
      "## Hypothetical additional roundtrip execution cost stress",
      "2/5/10 extra basis points on entry notional as a spread-like scenario, NOT reconstructed historical bid/ask. No change in model selection rules as cost increases.",
      sc.to_markdown(index=False),"",
      "## Interpretation",
      "- The classifier correctly obeys history-prefix causality but no quantified true-regime accuracy is possible without independent ground-truth labels.",
      "- Past-only selector correctness does not ensure strategic edge. A no-trade decision is valid but fails the 22/22 positive-month target.",
      "- Statistical lower confidence bounds assume iid trades and may overstate certainty given regime clustering; 2026 was previously researched.",
      "- Stop-first per original 1M intrabar execution. Fees 0.05% per side plus 18% GST; assumed 5 BTC points adverse slippage on both legs.",
      "- No historical L1 bid/ask depth, queue, actual fills, cash funding settlements, liquidation or contract rounding. Extra cost sensitivities are scenario tests only.",
      "- Drawdown sampled on each trade close; intratrade equity may show larger risk.",
      "- No regime switch or candidate is promoted for real-money trading from this audit alone.",
    ]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(lines)+"\n")
    print("BASELINE_AND_SELECTOR_RESULTS")
    print(sm.to_string(index=False))
    print("COST_SENSITIVITY")
    print(sc.to_string(index=False))
    print("MONTHLY_RETURN_PCT")
    print(mon.pivot(index="month_ist",columns="model",values="monthly_net_return_pct").round(3).to_string())
    print("COMPLETE")

if __name__=="__main__":
    main()
