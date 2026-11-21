#!/usr/bin/env python3
"""Improve BTC 4-layer research by excluding weak (regime, strategy) combinations
using strictly past-month, after-cost *shadow* trade outcomes.

NO historical hindsight group blacklist, no hyperparameter search, and no
production trades. Replays separate real 1M OHLC accounts for each alternative.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

import research_btc_regime_attribution_20261121 as base
import research_btc_mtf_market_structure_audit_20261121 as mtf
import research_btc_four_layer_regime_trading_20261121 as prior

OUT=Path("analysis/btc_four_layer_past_only_edge_20261121")
OUT.mkdir(parents=True,exist_ok=True)
MONTHS=prior.MONTHS
PAIRS=[
    ("shock_breakout","shock"),
    ("structured_breakout","breakout_up"),
    ("structured_breakout","breakout_down"),
    ("trend_pullback","confirmed_trend_up"),
    ("trend_pullback","confirmed_trend_down"),
    ("range_fade","range"),
]
RULES={
    "past6m_edge":dict(months=6,min_trades=8,min_active=3,pf=1.10),
    "past12m_robustness":dict(months=12,min_trades=16,min_active=5,pf=1.10),
}

def begin_month(month):
    return pd.Timestamp(month+"-01",tz="Asia/Kolkata").tz_convert("UTC")

def verify_shadow(one,hour,confirmed):
    shadow,counters=prior.execute(one,hour,confirmed,"shadow_full_four_layer")
    published=pd.read_csv(
       "analysis/btc_four_layer_regime_trading_20261121/trade_ledger_four_layer_15m_confirmed.csv")
    summary=pd.read_csv(
       "analysis/btc_four_layer_regime_trading_20261121/comparison_summary.csv")
    old=summary[summary.model=="four_layer_15m_confirmed"].iloc[0]
    if len(shadow)!=337 or len(published)!=337 or len(shadow)!=int(old.trades):
        raise RuntimeError("Original full 4-layer 337 trade parity failed")
    if abs(float(shadow.net_pnl_usd.sum())-float(old.net_profit_usd))>0.02:
        raise RuntimeError("Original 22-month account return parity drift")
    # Independent recreation of all entries, exit stamps and price-path PnL.
    if not (shadow.entry_utc.to_numpy()==published.entry_utc.to_numpy()).all():
        raise RuntimeError("Shadow entry chronology mismatches published baseline")
    if not (shadow.exit_utc.to_numpy()==published.exit_utc.to_numpy()).all():
        raise RuntimeError("Shadow stop/target chronology mismatches published baseline")
    if not np.allclose(shadow.net_pnl_usd.to_numpy(float),
                       published.net_pnl_usd.to_numpy(float),rtol=0,atol=1e-6):
        raise RuntimeError("Shadow per-trade net cash mismatch")
    shadow.to_csv(OUT/"shadow_training_trade_ledger.csv",index=False)
    return shadow,counters

def month_gates(shadow):
    ended=pd.to_datetime(shadow.exit_utc,utc=True)
    evidence=shadow.copy()
    evidence["exit_confirmed_utc"]=ended
    all_decisions=[]
    mappings={}
    for rule_name,rule in RULES.items():
        maps={}
        for i,month in enumerate(MONTHS):
            earliest=max(0,i-rule["months"])
            previous=MONTHS[earliest:i]
            latest3=MONTHS[max(0,i-3):i]
            start=begin_month(month)
            allowed={}
            for strategy,state in PAIRS:
                sample=evidence[(evidence.strategy==strategy)&(evidence.state==state)&
                      evidence.month_ist.isin(previous)&(evidence.exit_confirmed_utc<start)]
                if len(sample) and not (sample.exit_confirmed_utc<start).all():
                    raise RuntimeError("Current or future month outcome leaked")
                n=len(sample)
                active=int(sample.month_ist.nunique())
                netR=sample.net_R.to_numpy(float)
                wins=float(netR[netR>0].sum()) if n else 0.
                losses=-float(netR[netR<0].sum()) if n else 0.
                pf=wins/losses if losses>0 else (float("inf") if wins>0 else 0.)
                totalR=float(netR.sum()) if n else 0.
                recent3=float(sample.loc[sample.month_ist.isin(latest3),"net_R"].sum()) if n else 0.
                # A conservative real-money eligibility check: NEVER use the
                # current month, never force a trade in unproven state.
                ok=bool(i>=rule["months"] and n>=rule["min_trades"] and
                  active>=rule["min_active"] and pf>=rule["pf"] and
                  totalR>0 and recent3>0)
                if i<rule["months"]:
                    why="training_only"
                elif n<rule["min_trades"]:
                    why="insufficient_closed_shadow_trades"
                elif active<rule["min_active"]:
                    why="insufficient_active_months"
                elif pf<rule["pf"]:
                    why="past_net_profit_factor_below_threshold"
                elif totalR<=0:
                    why="past_net_R_not_positive"
                elif recent3<=0:
                    why="recent_three_month_net_R_not_positive"
                else:
                    why="qualified_at_month_open"
                allowed[(strategy,state)]=ok
                all_decisions.append(dict(model=rule_name,month_ist=month,
                  strategy=strategy,state=state,selected=ok,reason=why,
                  training_complete_months=",".join(previous),
                  training_ends_before_utc=str(start),
                  shadow_trades=n,active_shadow_months=active,
                  training_profit_factor_net_R=round(pf,4) if np.isfinite(pf) else "inf",
                  training_total_net_R=round(totalR,5),
                  training_recent3_net_R=round(recent3,5)))
            maps[month]=allowed
        mappings[rule_name]=maps
    decisions=pd.DataFrame(all_decisions)
    decisions.to_csv(OUT/"past_only_monthly_eligibility.csv",index=False)
    return mappings,decisions

def gated_events(all_events,mapping,model):
    selected=[]
    denials=[]
    for e in all_events:
        month=e["entry_utc"].tz_convert("Asia/Kolkata").strftime("%Y-%m")
        yes=bool(mapping.get(month,{}).get((e["strategy"],e["state"]),False))
        if yes:
            selected.append(e)
        else:
            denials.append(dict(model=model,entry_utc=str(e["entry_utc"]),
                   month_ist=month,strategy=e["strategy"],state=e["state"],
                   rejected_by_past_only_profitability_gate=True))
    return selected,denials

def main():
    one,manifest=base.load()
    if len(one)!=992160:
        raise RuntimeError("Delta native minute archive does not match verified manifest")
    hour,states,original_decisions,raw,eligible,confirmed=prior.context(one)
    prefix=mtf.past_recomputation(one,states)
    if any(p["revised_state_labels"]!=0 or p["revised_validity_flags"]!=0 for p in prefix):
        raise RuntimeError("Regime repaint detected")
    shadow,shadow_counts=verify_shadow(one,hour,confirmed)
    selection,decisions=month_gates(shadow)
    model_events={"old_four_layer_baseline":confirmed}
    denied=[]
    for key,m in selection.items():
        take,skip=gated_events(confirmed,m,key)
        model_events[key]=take
        denied.extend(skip)
    pd.DataFrame(denied).to_csv(OUT/"rejected_confirmed_signals.csv",index=False)
    summaries=[]
    monthlies=[]
    years=[]
    grouped=[]
    for key,events in model_events.items():
        if key=="old_four_layer_baseline":
            trades=shadow.copy()
            counts=shadow_counts
        else:
            trades,counts=prior.execute(one,hour,events,key)
        outtr=trades.copy()
        if len(outtr):
            outtr.to_csv(OUT/("trade_ledger_"+key+".csv"),index=False)
        else:
            (OUT/("trade_ledger_"+key+".csv")).write_text(
              "model,strategy,state,entry_utc,exit_utc,net_pnl_usd\n")
        # The base portfolio starts with $10k anew for each variant.
        mon=prior.monthly(trades,key)
        summary=prior.summarize(trades,mon,key,counts)
        if key=="old_four_layer_baseline":
            if len(trades)!=337 or abs(summary["net_return_pct"]-(-22.1561))>0.0002:
                raise RuntimeError("Published baseline comparison drift")
        # Audit no trading during the preregistered exclusive warmup months.
        if key in RULES:
            first=MONTHS[:RULES[key]["months"]]
            if int(mon.loc[mon.month_ist.isin(first),"trades"].sum())!=0:
                raise RuntimeError("Past-only rule traded in warmup")
        if len(trades):
            e=pd.to_datetime(trades.entry_utc,utc=True)
            x=pd.to_datetime(trades.exit_utc,utc=True)
            if len(e)>1 and not (e.iloc[1:].to_numpy()>x.iloc[:-1].to_numpy()).all():
                raise RuntimeError("Global position overlap")
            confirm=pd.to_datetime(trades.confirm_15m_closed_utc,utc=True)
            signal=pd.to_datetime(trades.signal_closed_utc,utc=True)
            if not (e.eq(confirm)&e.eq(signal+pd.Timedelta(minutes=15))).all():
                raise RuntimeError("Unconfirmed entry or lookahead")
            if not np.allclose(trades.gross_before_costs_usd-trades.fees_gst_usd-
                      trades.assumed_slippage_usd,trades.net_pnl_usd,atol=1e-6):
                raise RuntimeError("Fees/GST/slippage not reconciled")
        mon["year"]=mon.month_ist.str[:4]
        summaries.append(summary)
        monthlies.append(mon)
        for yr,g in mon.groupby("year"):
            years.append(dict(model=key,year=yr,months=len(g),trades=int(g.trades.sum()),
              profitable_months=int((g.status=="profit").sum()),
              losing_months=int((g.status=="loss").sum()),
              idle_months=int((g.status=="no_trade").sum()),
              net_compounded_return_pct=round(float(100*(np.prod(1+g.month_net_return_pct.to_numpy(float)/100)-1)),5)))
        if len(trades):
            g=trades.groupby(["strategy","state"],as_index=False).agg(
                trades=("net_pnl_usd","size"),wins=("net_pnl_usd",lambda x:int((x>0).sum())),
                net_usd=("net_pnl_usd","sum"),sum_net_R=("net_R","sum"))
            g["model"]=key
            grouped.append(g)
    summary=pd.DataFrame(summaries)
    mon=pd.concat(monthlies,ignore_index=True)
    annual=pd.DataFrame(years)
    summary.to_csv(OUT/"comparison_summary.csv",index=False)
    mon.to_csv(OUT/"monthly_account_returns.csv",index=False)
    annual.to_csv(OUT/"yearly_account_returns.csv",index=False)
    pd.concat(grouped,ignore_index=True).to_csv(OUT/"by_strategy_state.csv",index=False)
    q=dict(data="Delta India native BTCUSD 1M, verified SHA256 + contiguity",
      native_1m_candles=len(one),source_partitions=len(manifest["partitions"]),
      all_IST_months=22,base_shadow_ledger_pnl_entry_exit_parity_verified=True,
      previous_1H_4H_no_repaint_prefixes=prefix,
      original_confirmed_signal_events=len(confirmed),
      original_shadow_executed_trades=len(shadow),
      sample_model_count=len(RULES),
      sample_models_pre_registered_before_output=True,
      training_on_prior_exited_shadow_trades_only=True,
      training_window_at_month_open_only=True,
      no_train_outcome_after_month_begin=True,
      native_1m_stop_first_replay=True,
      next_1m_open_after_15m_confirmation=True,
      all_models_separate_compounded_account=True,
      actual_spreads_funding_liquidation_and_rounding_missing=True,
      globally_untouched_holdout_available=False,
      live_trade_approved=False)
    (OUT/"quality.json").write_text(json.dumps(q,indent=2)+"\n")
    report=[
      "# BTC four-layer multi-regime: strictly past-only after-cost eligibility improvement",
      "",
      "## Hypothesis and no-hindsight control",
      "The previous MTF regime -> strategy -> 15M confirmation -> independent native 1M exit lost 22.16% and earned only 9/22 positive IST months. Instead of deleting losers using hindsight, a **monthly past-only eligibility gate** checks each exact regime-strategy pair's CLOSED after-cost shadow trades in the previous 6 or 12 complete months. Models, parameters and alternatives were written to NOVELTY_CHECK.md BEFORE this test. No tuning or in-sample 'best' choice is authorized.",
      "",
      "## Audited data and scenario limitations",
      "~~~json",json.dumps(q,indent=2),"~~~","",
      "## Full 22-month separate-account net comparison",
      summary.to_markdown(index=False),"",
      "## Net monthly account return % including all zero-trade warmup months",
      mon.pivot(index="month_ist",columns="model",values="month_net_return_pct").round(3).to_markdown(),"",
      "## Annual net results",
      annual.to_markdown(index=False),"",
      "## Trade attribution by pair",
      pd.concat(grouped,ignore_index=True).round(3).to_markdown(index=False),"",
      "## Causal eligibility details",
      "6M rule: >=8 fully closed shadow trades, >=3 distinct active past months, PF(net normalized R)>=1.10, total 6M netR>0 and last 3M netR>0. 12M robustness: >=16 trades, >=5 active months, same PF/netR criteria. Every decision is frozen at IST month open; no current-month results are read. Prior shadow account trades omit events blocked by other shadow positions, so training evidence may be selection-biased. No trade is preferable to evidence-free allocation but zero months fail the user's target.",
      "",
      "## Decision",
      "The new gated account must be judged by 22 independently replayed IST month outcomes, not by hindsight per-state performance of the original strategy. Even if one alternative has a positive backtest, the studied 2025–2026 period is not an externally untouched holdout; live trading remains BLOCKED. Historical L1 spreads, actual funding payments, exchange contract size, queue/impact and liquidation are unavailable.",
    ]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")
    print("SUMMARY",summary.to_string(index=False))
    print("YEARS",annual.to_string(index=False))
    print("GATES",decisions.groupby(["model","selected"],as_index=False).size().to_string(index=False))
    print("MONTHLY",mon.pivot(index="month_ist",columns="model",values="month_net_return_pct").round(3).to_string())
    print("DONE")

if __name__=="__main__":
    main()
