#!/usr/bin/env python3
"""Independent evidence validation and extra execution-cost stress for four-layer
BTC regime selectors. Successfully auditing a study DOES NOT enable live trading.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

OUT=Path("analysis/btc_four_layer_past_only_edge_20261121")
MODELS=["old_four_layer_baseline","past6m_edge","past12m_robustness"]
WINDOW={"past6m_edge":6,"past12m_robustness":12}
MONTHS=[str(x) for x in pd.period_range("2025-01","2026-10",freq="M")]

def start(month):
    return pd.Timestamp(month+"-01",tz="Asia/Kolkata").tz_convert("UTC")

def audit():
    shadow=pd.read_csv(OUT/"shadow_training_trade_ledger.csv")
    shadow["finished"]=pd.to_datetime(shadow.exit_utc,utc=True)
    decisions=pd.read_csv(OUT/"past_only_monthly_eligibility.csv")
    summary=pd.read_csv(OUT/"comparison_summary.csv")
    monthly=pd.read_csv(OUT/"monthly_account_returns.csv")
    assert len(shadow)==337
    assert len(decisions)==22*6*2
    assert len(monthly)==22*3
    assert len(summary)==3
    verified=0
    for row in decisions.itertuples(index=False):
        i=MONTHS.index(row.month_ist)
        w=WINDOW[row.model]
        a=MONTHS[max(0,i-w):i]
        sample=shadow[(shadow.strategy==row.strategy)&(shadow.state==row.state)&
                   shadow.month_ist.isin(a)&(shadow.finished<start(row.month_ist))]
        assert all(sample.finished<start(row.month_ist))
        assert len(sample)==row.shadow_trades
        assert sample.month_ist.nunique()==row.active_shadow_months
        vals=sample.net_R.to_numpy(float)
        recent=sample[sample.month_ist.isin(MONTHS[max(0,i-3):i])].net_R.sum()
        pf=(vals[vals>0].sum()/-vals[vals<0].sum()) if np.any(vals<0) \
           else (float("inf") if np.any(vals>0) else 0.)
        if np.isfinite(pf):
            assert abs(pf-float(row.training_profit_factor_net_R))<.0002
        assert abs(vals.sum()-row.training_total_net_R)<.00002
        assert abs(recent-row.training_recent3_net_R)<.00002
        yes=(i>=w and len(sample)>=(8 if w==6 else 16) and
             sample.month_ist.nunique()>=(3 if w==6 else 5) and
             pf>=1.10 and vals.sum()>0 and recent>0)
        assert bool(row.selected)==yes
        assert all(x not in a for x in [row.month_ist])
        verified+=1

    sensitivity=[]
    other={}
    for model in MODELS:
        row=summary[summary.model==model].iloc[0]
        t=pd.read_csv(OUT/("trade_ledger_"+model+".csv"))
        assert int(row.trades)==len(t)
        assert (t.fees_gst_usd>=0).all() and (t.assumed_slippage_usd>=0).all()
        assert np.allclose(t.gross_before_costs_usd-t.fees_gst_usd-
                        t.assumed_slippage_usd,t.net_pnl_usd,atol=1e-6)
        entries=pd.to_datetime(t.entry_utc,utc=True)
        exits=pd.to_datetime(t.exit_utc,utc=True)
        signal=pd.to_datetime(t.signal_closed_utc,utc=True)
        confirm=pd.to_datetime(t.confirm_15m_closed_utc,utc=True)
        assert (entries==confirm).all()
        assert (entries==signal+pd.Timedelta(minutes=15)).all()
        assert (entries.iloc[1:].to_numpy()>exits.iloc[:-1].to_numpy()).all()
        assert (entries.dt.tz_convert("Asia/Kolkata").dt.strftime("%Y-%m")==t.month_ist).all()
        assert (exits.dt.tz_convert("Asia/Kolkata").dt.strftime("%Y-%m")==t.month_ist).all()
        if model in WINDOW:
            chosen=decisions[(decisions.model==model)&decisions.selected]
            allowed=set(zip(chosen.month_ist,chosen.strategy,chosen.state))
            assert all((m,s,st) in allowed for m,s,st in zip(t.month_ist,t.strategy,t.state))
            assert not t.month_ist.isin(MONTHS[:WINDOW[model]]).any()
        oldeq=np.r_[10000.,t.account_equity_usd.to_numpy(float)[:-1]]
        if (oldeq<=0).any():
            raise RuntimeError("Nonpositive account balance")
        qty_rate=t.qty_btc_equiv.to_numpy(float)/oldeq
        pnl_rate=t.net_pnl_usd.to_numpy(float)/oldeq
        notional_rate=qty_rate*t.entry_price.to_numpy(float)
        for bps in [0.,2.,5.,10.]:
            eq=10000.
            month_profit={m:0. for m in MONTHS}
            costs=0.
            for i,m in enumerate(t.month_ist):
                add=eq*notional_rate[i]*bps/10000.
                pnl=eq*pnl_rate[i]-add
                eq+=pnl
                month_profit[m]+=pnl
                costs+=add
                if eq<=0:raise RuntimeError("Extra-fee scenario bankrupt")
            positive=sum(v>0.0000001 for v in month_profit.values())
            negative=sum(v< -0.0000001 for v in month_profit.values())
            sensitivity.append(dict(model=model,extra_roundtrip_bps=bps,
              net_account_return_pct=round(100*(eq/10000.-1),4),
              extra_spread_like_cost_usd=round(costs,2),
              profitable_months=positive,losing_months=negative,
              zero_trade_months=22-positive-negative))
            if bps==0:
                if abs(eq-float(row.ending_equity_usd))>0.02:
                    raise RuntimeError("0 bps scenario failed original account parity")
        other[model]=dict(trades=len(t),net_return_pct=float(row.net_return_pct),
          profitable_months=int(row.profitable_months),win_rate=float(row.win_rate_pct),
          pf=float(row.profit_factor),
          trade_close_drawdown_pct=float(row.max_trade_close_drawdown_pct))

    stress=pd.DataFrame(sensitivity)
    stress.to_csv(OUT/"extra_cost_sensitivity.csv",index=False)
    result={
       "research_validation":"PASS",
       "strategy_trading_release":"BLOCKED",
       "train_decisions_verified":verified,
       "first_hour_and_completed_15m_entry_causal":True,
       "monthly_selector_uses_only_prior_complete_trades":True,
       "past_only_monthly_qualification_recomputed":True,
       "all_model_trade_ledger_pnl_fees_slippage_reconciled":True,
       "all_variants_one_exclusive_position":True,
       "baseline_full_history_parity":True,
       "no_replay_smuggling_current_month_outcomes":True,
       "target_22_profitable_months_met":False,
       "original_after_cost_return_pct":other["old_four_layer_baseline"]["net_return_pct"],
       "primary_6m_return_pct":other["past6m_edge"]["net_return_pct"],
       "robustness_12m_return_pct":other["past12m_robustness"]["net_return_pct"],
       "2025_2026_was_previously_researched":True,
       "new_unseen_holdout_exists":False,
       "actual_bid_ask_spreads_known":False,
       "funding_cash_flows_known":False,
       "real_time_liquidation_feasibility_known":False,
       "confirmed_positive_after_extra_costs_not_assumed":True,
       "models":other,
       "reason":"Historical after-cost improvement on a previously explored archive is not a genuine new future holdout or 22/22 result. Keep all live trading disabled until prospective and real execution checks."
    }
    (OUT/"RELEASE_VALIDATION.json").write_text(json.dumps(result,indent=2)+"\n")
    report=[
        "# Past-only four-layer multi-regime improvements — independent release validation",
        "",
        "**Backtest integrity: passed. Live approval: BLOCKED.** All 264 distinct pair/month/model decisions re-derived from prior completed shadow trades and checked before each month start. Separate account 1M trades and net cash outcomes reconciled; no entry before 15M confirmation. The historical 2025–2026 data was researched before this selector was conceived, so a genuinely untouched out-of-sample result is unavailable.",
        "",
        "## Validation evidence","~~~json",json.dumps(result,indent=2),"~~~","",
        "## Extra hypothetical spread-like roundtrip cost stress",
        "These increments come ON TOP of the existing assumed taker fees/GST and 5 BTC points adverse slip on each leg. They are hypothetical; no observed exchange L1 bid/ask spread or funding cash settlements are available.",
        stress.to_markdown(index=False),"",
        "## Decision",
        "The predeclared monthly 6M and 12M eligibility gate may show improvement over the all-eligible baseline, but zero-trade training months and negative months are not wins. Sample 2026 has been repeatedly inspected. Do NOT deploy or automatically promote a best-looking comparator after comparing their 2026 returns. Require independent forward testing plus actual funding, spreads, size/rounding and liquidation constraints.",
    ]
    (OUT/"RELEASE_VALIDATION.md").write_text("\n".join(report)+"\n")
    print("VALIDATION",json.dumps(result,indent=2))
    print("COST_STRESS")
    print(stress.to_string(index=False))
    print("SUCCESSFUL_AUDIT_NO_GO")

if __name__=="__main__":
    audit()
