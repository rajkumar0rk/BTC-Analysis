#!/usr/bin/env python3
"""ACTUAL single-account union of the already-frozen 6M and 12M BTC four-layer
profit-protected entry filters. No addition of independent account returns.
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd

import research_btc_regime_attribution_20261121 as base
import research_btc_four_layer_regime_trading_20261121 as core
import research_btc_four_layer_trade_management_20261121 as prior

OUT=Path("analysis/btc_6m12m_union_20261122")
OUT.mkdir(parents=True,exist_ok=True)
MONTHS=core.MONTHS
MODELS=["six_only","twelve_only","union_6m12m","intersection_6m12m"]
SOURCE=Path("analysis/btc_four_layer_trade_management_20261121")

def key(event):
    return (int(event["signal_j"]),str(event["entry_utc"]),
            str(event["strategy"]),str(event["state"]),int(event["side"]))

def qualified_events():
    evidence=pd.read_csv(
        "analysis/btc_four_layer_past_only_edge_20261121/past_only_monthly_eligibility.csv")
    if len(evidence)!=264:
        raise RuntimeError("Past-only evidence decision count changed")
    expected={"past6m_edge":6,"past12m_robustness":12}
    for rule,months in expected.items():
        table=evidence[evidence.model==rule]
        if len(table)!=22*6:
            raise RuntimeError("Missing original month-open eligibility decisions")
        assert not table.loc[table.month_ist.isin(MONTHS[:months]),"selected"].any()
    return evidence

def assert_original(name,tr):
    published_name={"six_only":"past6_protected",
                    "twelve_only":"past12_protected"}[name]
    original=pd.read_csv(SOURCE/f"trade_ledger_{published_name}.csv")
    summary=pd.read_csv(SOURCE/"comparison_summary.csv")
    orig=summary[summary.model==published_name].iloc[0]
    if len(original)!=len(tr) or len(tr)!=(55 if name=="six_only" else 51):
        raise RuntimeError("Standalone protected model count drift: "+name)
    for field in ("entry_utc","exit_utc","strategy","state","month_ist"):
        if not np.array_equal(tr[field].astype(str).to_numpy(),
                              original[field].astype(str).to_numpy()):
            raise RuntimeError(name+" original trade field mismatch: "+field)
    for field in ("net_pnl_usd","net_R","fees_gst_usd","assumed_slippage_usd"):
        if not np.allclose(tr[field].to_numpy(float),
                           original[field].to_numpy(float),atol=1e-6,rtol=0):
            raise RuntimeError(name+" original per-trade PnL mismatch: "+field)
    if abs(float(tr.net_pnl_usd.sum())-float(orig.net_profit_usd))>.02:
        raise RuntimeError("Published final PnL mismatch: "+name)

def assert_execution(tr,model):
    if tr.empty: return
    en=pd.to_datetime(tr.entry_utc,utc=True)
    ex=pd.to_datetime(tr.exit_utc,utc=True)
    signal=pd.to_datetime(tr.signal_closed_utc,utc=True)
    conf=pd.to_datetime(tr.confirm_15m_closed_utc,utc=True)
    assert en.is_monotonic_increasing and (ex>=en).all()
    assert (en==conf).all() and (en==signal+pd.Timedelta(minutes=15)).all()
    if len(tr)>1 and not (en.iloc[1:].to_numpy()>ex.iloc[:-1].to_numpy()).all():
        raise RuntimeError("Overlapping account positions in "+model)
    assert (en.dt.tz_convert("Asia/Kolkata").dt.strftime("%Y-%m")==tr.month_ist).all()
    assert (ex.dt.tz_convert("Asia/Kolkata").dt.strftime("%Y-%m")==tr.month_ist).all()
    assert np.allclose(tr.gross_before_costs_usd-tr.fees_gst_usd-
       tr.assumed_slippage_usd,tr.net_pnl_usd,atol=1e-6)
    assert (tr.stop_update_count>=0).all()
    assert not np.any((tr.side==1)&(tr.final_stop_raw<tr.initial_stop_raw-1e-8))
    assert not np.any((tr.side==-1)&(tr.final_stop_raw>tr.initial_stop_raw+1e-8))
    assert tr.strategy.isin(["shock_breakout","structured_breakout"]).all()

def main():
    qualified_events()  # confirms source monthly decisions are present and frozen
    one,manifest=base.load()
    if len(one)!=992160:
        raise RuntimeError("Delta India BTCUSD verified native 1M count drift")
    hour,states,decisions,raw,eligible,confirmed=core.context(one)
    if len(confirmed)!=513:
        raise RuntimeError("Confirmed 15M signal parity failed")
    prior_events=prior.get_events(confirmed)
    six=prior_events["past6m_edge"]
    twelve=prior_events["past12m_robustness"]
    a={key(e):e for e in six}
    b={key(e):e for e in twelve}
    if len(a)!=len(six) or len(b)!=len(twelve):
        raise RuntimeError("Original eligibility signal set contains duplicates")
    union={**a,**b}
    intersection={k:e for k,e in a.items() if k in b}
    assert len(union)==len(a)+len(b)-len(intersection)
    combined={
        "six_only":list(a.values()),"twelve_only":list(b.values()),
        "union_6m12m":list(union.values()),
        "intersection_6m12m":list(intersection.values()),
    }
    candidate_rows=[]
    for k,e in sorted(union.items(),key=lambda x:x[1]["entry_utc"]):
        candidate_rows.append(dict(
            signal_j=e["signal_j"],entry_utc=str(e["entry_utc"]),
            state=e["state"],strategy=e["strategy"],side=e["side"],
            month_ist=e["entry_utc"].tz_convert("Asia/Kolkata").strftime("%Y-%m"),
            eligible_6m=k in a,eligible_12m=k in b,
            union_eligible=True,both_models_agree=(k in intersection)))
    pd.DataFrame(candidate_rows).to_csv(OUT/"union_candidate_provenance.csv",index=False)
    summaries=[];months=[];years=[];stresses=[];attribution=[]
    for model in MODELS:
        events=combined[model]
        tr,counts=prior.execute(one,hour,events,model,"protected")
        assert_execution(tr,model)
        if model in ("six_only","twelve_only"):
            assert_original(model,tr)
        if len(tr):
            tr.to_csv(OUT/f"trade_ledger_{model}.csv",index=False)
        else:
            (OUT/f"trade_ledger_{model}.csv").write_text(
                "model,entry_utc,exit_utc,month_ist,net_pnl_usd\n")
        mon=core.monthly(tr,model)
        summ=core.summarize(tr,mon,model,counts)
        if not len(mon)==22 or mon.month_ist.tolist()!=MONTHS:
            raise RuntimeError("Wrong IST month coverage")
        if len(tr) and abs(float(tr.net_pnl_usd.sum())-float(summ["net_profit_usd"]))>.02:
            raise RuntimeError("Account monthly cash mismatch")
        months.append(mon)
        summaries.append(summ)
        stresses.extend(prior.stress_cost(tr,model) if len(tr) else [])
        for year,g in mon.groupby(mon.month_ist.str[:4]):
            years.append(dict(model=model,year=year,
                  months=len(g),trades=int(g.trades.sum()),
                  profitable_months=int((g.status=="profit").sum()),
                  losing_months=int((g.status=="loss").sum()),
                  idle_months=int((g.status=="no_trade").sum()),
                  compounded_net_pct=round(100*(np.prod(1+g.month_net_return_pct.to_numpy(float)/100)-1),5)))
        if len(tr):
            g=tr.groupby(["state","strategy"],as_index=False).agg(
                executed=("net_pnl_usd","size"),
                positive_trades=("net_pnl_usd",lambda v:int((v>0).sum())),
                account_net_pnl_usd=("net_pnl_usd","sum"))
            g["model"]=model
            attribution.append(g)
    report=pd.DataFrame(summaries)
    mon=pd.concat(months,ignore_index=True)
    annual=pd.DataFrame(years)
    sensitivity=pd.DataFrame(stresses)
    report.to_csv(OUT/"comparison_summary.csv",index=False)
    mon.to_csv(OUT/"combined_monthly_accounts.csv",index=False)
    annual.to_csv(OUT/"yearly_accounts.csv",index=False)
    sensitivity.to_csv(OUT/"additional_cost_sensitivity.csv",index=False)
    pd.concat(attribution,ignore_index=True).to_csv(OUT/"strategy_attribution.csv",index=False)
    quality=dict(
      models=MODELS,complete_IST_months=22,
      source="Delta India BTCUSD SHA256 verified native 1M",
      native_1m_candles=len(one),source_partitions=len(manifest["partitions"]),
      confirmed_first_15m_events=len(confirmed),
      six_month_eligible_unique_signals=len(a),
      twelve_month_eligible_unique_signals=len(b),
      common_signals_deduplicated=len(intersection),
      union_eligible_unique_signals=len(union),
      union_equals_set_sum_minus_intersection=True,
      standalone_six_month_protected_trade_parity=True,
      standalone_twelve_month_protected_trade_parity=True,
      two_filters_enter_once_when_same_signal=True,
      independent_single_combined_account=True,
      one_position_globally_at_a_time=True,
      original_fixed_15m_confirmation_and_next_1m_entry=True,
      no_synthetic_signal_from_future_month_pnl=True,
      same_protected_stop_exit_rules_for_all_variants=True,
      native_1m_stop_first_and_next_bar_stop_updates=True,
      fees_GST_slippage_accounted_as_original_assumptions=True,
      actual_funding_cash_or_historical_orderbook_spread_present=False,
      liquidation_or_contract_rounding_modelled=False,
      external_untouched_prospective_holdout=False,
      approved_for_live_trading=False)
    (OUT/"quality.json").write_text(json.dumps(quality,indent=2)+"\n")
    lines=[
      "# Combined BTC four-layer 6M + 12M protected monthly results",
      "",
      "## Correct definition of combined",
      "UNION means ONE BTCUSD account, one active position, each shared eligible signal executed once, and equity/size/PnL recalculated sequentially on native 1M candles. It is NOT (6M return + 12M return), nor two independent accounts' returns averaged. For completeness INTERSECTION means trade only when both past-only 6M and past-only 12M filters agree. No historical best-month switching.",
      "",
      "## Quality & provenance","~~~json",json.dumps(quality,indent=2),"~~~","",
      "## Combined vs individual performance",
      report.to_markdown(index=False),"",
      "## All 22 IST months — individually compounded account return %",
      mon.pivot(index="month_ist",columns="model",values="month_net_return_pct").round(3).to_markdown(),"",
      "## Yearly account performance",
      annual.to_markdown(index=False),"",
      "## Extra hypothetical spread-like round-trip cost stress",
      sensitivity.to_markdown(index=False),"",
      "## By state contribution",
      pd.concat(attribution,ignore_index=True).round(2).to_markdown(index=False),"",
      "## Limitations",
      "This research has repeatedly examined Jan 2025–Oct 2026, so these figures are not an independent blind result. Real realized funding, historical L1 bid/ask, queue/slippage, liquidation and contract sizing are unavailable. Initial account $10,000, per-trade initial stop risk 0.5% of evolving equity capped 3x, modeled taker/GST+5 BTC point adverse slippage per side. Trade-close drawdown omits intratrade mark drawdown. The true live system remains BLOCKED. A zero-trade month fails the 22/22 monthly profitability objective.",
    ]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(lines)+"\n")
    print("COMPARISON")
    print(report.to_string(index=False))
    print("CANDIDATES",json.dumps({k:quality[k] for k in (
      "six_month_eligible_unique_signals","twelve_month_eligible_unique_signals",
      "common_signals_deduplicated","union_eligible_unique_signals")}))
    print("MONTHLY")
    print(mon.pivot(index="month_ist",columns="model",values="month_net_return_pct").round(3).to_string())
    print("DONE")

if __name__=="__main__":
    main()
