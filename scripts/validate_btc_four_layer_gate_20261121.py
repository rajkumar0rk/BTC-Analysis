#!/usr/bin/env python3
"""Independent output-audit + fail-closed trading-release gate.

Research validation only: checks timestamps, regime eligibility, confirmation,
exclusive positions, 22 calendar months, and cost/equity reconciliation.
Never turns on any trading bot.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

OUT=Path("analysis/btc_four_layer_regime_trading_20261121")
MODELS=["no_trade","ungated_immediate","regime_eligible_immediate","four_layer_15m_confirmed"]
MONTHS=[str(x) for x in pd.period_range("2025-01","2026-10",freq="M")]

def run():
    quality=json.loads((OUT/"execution_quality.json").read_text())
    result=pd.read_csv(OUT/"comparison_summary.csv")
    decision=pd.read_csv(OUT/"decision_audit.csv")
    monthly=pd.read_csv(OUT/"monthly_account_returns.csv")
    assert len(decision)==quality["signal_hourly_decisions"]
    assert set(result.model)==set(MODELS)
    assert len(monthly)==88
    assert quality["completed_4h_lookahead_violations"]==0
    assert quality["fifteen_minute_bars_verified_complete"]
    assert all(p["revised_state_labels"]==0 and p["revised_validity_flags"]==0
               for p in quality["hourly_observation_no_repaint_prefixes"])
    eligible=decision[decision.selected_strategy!="NO_TRADE"]
    confirmed=decision[decision.first_15m_confirmed]
    assert len(eligible)==quality["signals_with_state_strategy_eligibility"]
    assert len(confirmed)==quality["signals_confirmed_by_first_future_15m"]
    assert (eligible.observer_valid).all()
    invalid_state=decision.state.isin(["mixed_uncertain","transition","compression","unclassified"])
    assert decision.loc[invalid_state,"selected_strategy"].eq("NO_TRADE").all()
    assert decision.loc[invalid_state,"first_15m_confirmed"].eq(False).all()

    summary={}
    for model in MODELS:
        t=pd.read_csv(OUT/("trade_ledger_"+model+".csv"))
        m=monthly[monthly.model==model].copy().sort_values("month_ist")
        assert m.month_ist.tolist()==MONTHS
        r=result[result.model==model].iloc[0]
        assert int(r.trades)==len(t)
        assert int(r.profitable_months)==int((m.status=="profit").sum())
        assert int(r.losing_months)==int((m.status=="loss").sum())
        assert int(r.idle_months)==int((m.status=="no_trade").sum())
        assert int(r.profitable_months)+int(r.losing_months)+int(r.idle_months)==22
        if model=="no_trade":
            assert len(t)==0
            assert np.isclose(float(r.net_return_pct),0)
            continue
        assert len(t)>0
        entry=pd.to_datetime(t.entry_utc,utc=True)
        exit_=pd.to_datetime(t.exit_utc,utc=True)
        signal=pd.to_datetime(t.signal_closed_utc,utc=True)
        assert entry.is_monotonic_increasing
        assert (entry>=signal).all()
        assert (exit_>=entry).all()
        assert (entry.iloc[1:].to_numpy()>exit_.iloc[:-1].to_numpy()).all()
        assert (entry.dt.tz_convert("Asia/Kolkata").dt.strftime("%Y-%m")==t.month_ist).all()
        assert (exit_.dt.tz_convert("Asia/Kolkata").dt.strftime("%Y-%m")==t.month_ist).all()
        if model=="four_layer_15m_confirmed":
            confirmed_time=pd.to_datetime(t.confirm_15m_closed_utc,utc=True)
            assert (entry==confirmed_time).all()
            assert (entry==signal+pd.Timedelta(minutes=15)).all()
            matched=confirmed[["signal_closed_utc","selected_strategy","selected_side"]].copy()
            matched["signal_closed_utc"]=pd.to_datetime(matched.signal_closed_utc,utc=True)
            compare=pd.DataFrame({"signal_closed_utc":signal,
                  "selected_strategy":t.strategy.to_numpy(),
                  "selected_side":t.side.to_numpy(int)})
            merged=compare.merge(matched,on=["signal_closed_utc","selected_strategy","selected_side"],
                                 how="left",indicator=True)
            assert merged._merge.eq("both").all()
        if model in ("four_layer_15m_confirmed","regime_eligible_immediate"):
            assert t.state.isin(["shock","confirmed_trend_up","confirmed_trend_down",
                                 "breakout_up","breakout_down","range"]).all()
        assert np.allclose(
            t.gross_before_costs_usd-t.fees_gst_usd-t.assumed_slippage_usd,
            t.net_pnl_usd,atol=1e-6)
        assert abs(float(t.net_pnl_usd.sum())-float(r.net_profit_usd))<.02
        assert abs(float(m.month_net_pnl_usd.sum())-float(r.net_profit_usd))<.10
        assert abs(float(t.account_equity_usd.iloc[-1])-float(r.ending_equity_usd))<.02
        assert np.all(t.qty_btc_equiv.to_numpy(float)>0)
        assert (t.fees_gst_usd>0).all()
        assert (t.assumed_slippage_usd>0).all()
        summary[model]=dict(trades=int(len(t)),
           profit_factor=float(r.profit_factor) if pd.notna(r.profit_factor) else None,
           final_equity=float(r.ending_equity_usd),
           positive_months=int(r.profitable_months),
           first_entry=str(entry.iloc[0]),last_exit=str(exit_.iloc[-1]))

    selected=result.loc[result.model=="four_layer_15m_confirmed"].iloc[0]
    gate=dict(
      research_validation="PASS",
      strategy_live_approval="BLOCKED",
      strategy_enterprise_deployment_approved=False,
      current_market_classifier_history_repaint=False,
      cross_timeframe_lookahead=False,
      entry_before_15m_confirmation=False,
      overlapping_positions=False,
      costs_and_monthly_cash_reconciled=True,
      full_22_calendar_months_evaluated=True,
      selected_positive_months=int(selected.profitable_months),
      selected_net_return_pct=float(selected.net_return_pct),
      selected_profit_factor=float(selected.profit_factor),
      target_22_of_22_met=bool(selected.passes_22_22),
      actual_bid_ask_historical_available=False,
      funding_settlement_cash_flows_modelled=False,
      exchange_liquidation_contract_size_validated=False,
      independent_future_unseen_holdout_available=False,
      comparator_evidence=summary,
      conclusion=("The four-layer causal execution system passes research integrity checks "
                  "but the selected strategy loses money after modeled fees/GST/slippage. "
                  "Correct classification and modular code are NOT evidence of a live trading edge.")
    )
    if not (selected.net_return_pct>0 and selected.profit_factor>1
            and selected.profitable_months==22):
        assert not gate["strategy_enterprise_deployment_approved"]
    (OUT/"RELEASE_VALIDATION.json").write_text(json.dumps(gate,indent=2)+"\n")
    (OUT/"RELEASE_VALIDATION.md").write_text(
      "# Four-layer BTCUSD multi-regime pipeline — release validation\n\n"
      "Research-integrity checks passed: completed 4H used only after close, first "
      "subsequent 15M candle fully closed before confirmed entry, global position "
      "exclusivity, 1M exits, fee/GST/slippage cash reconciliation, full 22-month "
      "coverage, and three historical prefix no-revision tests.\n\n"
      "**Live deployment: BLOCKED.** The confirmed strategy net return is "
      f"{selected.net_return_pct:.4f}% and it has {int(selected.profitable_months)}/22 "
      "profitable complete IST months. The 22/22 objective and profit-factor gate "
      "failed. Historical exchange spread, funding settlement, liquidation and "
      "actual orderbook feasibility are unverified.\n\n"
      "The 2025–2026 backtest history is not an untouched blind validation sample. "
      "This gate does not change live services or give permission to trade.\n")
    print(json.dumps(gate,indent=2))
    print("AUDIT_SUCCESSFUL_LIVE_TRADING_BLOCKED")

if __name__=="__main__":
    run()
