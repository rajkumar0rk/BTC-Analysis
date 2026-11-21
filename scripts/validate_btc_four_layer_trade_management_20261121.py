#!/usr/bin/env python3
"""Independent four-layer stop-update timing and 22-month result validation.

Synthetic native-1M fixtures stress cases that can falsely inflate OHLC backtests:
a stop and activation in the SAME minute, a stop activated next minute,
and no phantom fixed target in the ATR-only runner mode.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

import research_btc_regime_attribution_20261121 as base
import research_btc_four_layer_trade_management_20261121 as research

OUT=Path("analysis/btc_four_layer_trade_management_20261121")
MODELS=list(research.MODELS)
MONTHS=research.MONTHS

def synthetic_one(bars):
    t=pd.date_range("2026-01-01T01:15:00Z",periods=len(bars),freq="1min")
    return pd.DataFrame(bars,index=t,columns=["open","high","low","close"])

def fixture(mode,bars):
    one=synthetic_one(bars)
    h=pd.DataFrame({"atr":[100.]},index=pd.DatetimeIndex(["2026-01-01T00:00:00Z"]))
    closed=pd.Timestamp("2026-01-01T01:00:00Z")
    e=dict(signal_j=0,strategy="structured_breakout",side=1,
       signal_close=closed,entry_utc=closed+pd.Timedelta(minutes=15),
       state="breakout_up",confirm_15m_close=closed+pd.Timedelta(minutes=15))
    tr,count=research.execute(one,h,[e],"fixture_"+mode,mode)
    if len(tr)!=1:
        raise AssertionError("Synthetic fixture did not execute exactly one trade")
    return tr.iloc[0],count

def assert_fixtures():
    # +1.5R activation threshold is 1270 (entry=1000, risk=180).
    # In the SAME 1M bar: high=1280 but low=810 touches initial stop 820.
    # It MUST stop first at 820; no freshly raised stop allowed.
    bar=[(1000,1280,810,1200),(1000,1300,900,1150)]
    a,_=fixture("protected",bar)
    b,_=fixture("runner",bar)
    assert a.exit_reason=="initial_stop" and a.stop_update_count==0
    assert b.exit_reason=="initial_stop" and b.stop_update_count==0
    assert abs(a.final_stop_raw-820.)<1e-8
    assert str(a.exit_utc).startswith("2026-01-01 01:15")
    # Activation candle finishes without hitting original stop or TP. Its
    # high is known AFTER minute 01:15:00-01:15:59; protective stop (1027)
    # becomes effective 01:16:00. It is hit IN the second minute.
    b2=[(1000,1280,950,1100),(1040,1050,1020,1025),(1000,1010,800,805)]
    p,_=fixture("protected",b2)
    assert p.exit_reason=="trailing_or_protected_stop"
    assert abs(p.final_stop_raw-1027.)<1e-8
    assert p.stop_update_count==1
    assert str(p.exit_utc).startswith("2026-01-01 01:16")
    # Runner trailing next minute from highwater=1280, 1.8*ATR=180:
    # stop moves to 1100 after first candle, and can exit at 1100 second.
    br=[(1000,1280,950,1200),(1110,1300,1090,1110),(1000,1010,800,800)]
    runner,_=fixture("runner",br)
    assert runner.exit_reason=="trailing_or_protected_stop"
    assert abs(runner.final_stop_raw-1100.)<1e-8
    assert str(runner.exit_utc).startswith("2026-01-01 01:16")
    # Prior 3R TP=1540: in runner mode it must NOT be used.
    cap=[(1000,1550,950,1300),(1300,1350,1200,1230),(1200,1210,800,810)]
    o,_=fixture("original",cap)
    rn,_=fixture("runner",cap)
    assert o.exit_reason=="fixed_target"
    assert rn.exit_reason!="fixed_target"
    assert rn.target_used==False
    assert str(o.exit_utc).startswith("2026-01-01 01:15")
    assert str(rn.exit_utc).startswith("2026-01-01 01:16")
    return dict(same_minute_activation_and_initial_stop="PASS_STOP_FIRST",
                next_minute_protected_stop="PASS",
                next_minute_atr_runner="PASS",
                runner_does_not_fill_removed_3R_target="PASS")

def audit():
    scenario=assert_fixtures()
    cmp=pd.read_csv(OUT/"comparison_summary.csv")
    mon=pd.read_csv(OUT/"monthly_account_returns.csv")
    sens=pd.read_csv(OUT/"additional_spread_sensitivity.csv")
    assert set(cmp.model)==set(MODELS)
    assert len(mon)==22*len(MODELS)
    assert len(sens)==4*len(MODELS)
    assert set(sens.extra_roundtrip_bps)=={0,2,5,10}
    baseline_count={"past12_original":51,"past6_original":55}
    for model in MODELS:
        t=pd.read_csv(OUT/("trade_ledger_"+model+".csv"))
        r=cmp[cmp.model==model].iloc[0]
        m=mon[mon.model==model].sort_values("month_ist")
        assert len(m)==22 and m.month_ist.tolist()==MONTHS
        assert len(t)==int(r.trades)
        if model in baseline_count:
            assert len(t)==baseline_count[model]
            assert not t.stop_activated.any()
            assert not t.stop_update_count.any()
            assert t.target_used.all()
        else:
            assert (t.stop_update_count>=0).all()
            assert t.strategy.isin(["structured_breakout","shock_breakout"]).all()
            if model.endswith("protected"):
                assert (t.stop_update_count<=1).all()
                for row in t.itertuples(index=False):
                    if row.stop_update_count:
                        expected=row.entry_price-row.side*base.SLIP + \
                                 row.side*.15*row.risk_points
                        assert abs(row.final_stop_raw-expected)<1e-6
            if model.endswith("runner"):
                assert (~t.target_used).all()
                assert not t.exit_reason.eq("fixed_target").any()
        assert not np.any((t.side==1)&(t.final_stop_raw<t.initial_stop_raw-1e-8))
        assert not np.any((t.side==-1)&(t.final_stop_raw>t.initial_stop_raw+1e-8))
        entries=pd.to_datetime(t.entry_utc,utc=True)
        exits=pd.to_datetime(t.exit_utc,utc=True)
        signals=pd.to_datetime(t.signal_closed_utc,utc=True)
        confirmations=pd.to_datetime(t.confirm_15m_closed_utc,utc=True)
        assert (entries==confirmations).all()
        assert (entries==signals+pd.Timedelta(minutes=15)).all()
        assert (exits>=entries).all()
        assert (entries.iloc[1:].to_numpy()>exits.iloc[:-1].to_numpy()).all()
        assert (entries.dt.tz_convert("Asia/Kolkata").dt.strftime("%Y-%m")==t.month_ist).all()
        assert (exits.dt.tz_convert("Asia/Kolkata").dt.strftime("%Y-%m")==t.month_ist).all()
        assert np.allclose(
            t.gross_before_costs_usd-t.fees_gst_usd-t.assumed_slippage_usd,
            t.net_pnl_usd,atol=1e-6)
        assert abs(float(t.net_pnl_usd.sum())-float(r.net_profit_usd))<.02
        assert abs(float(t.account_equity_usd.iloc[-1])-float(r.ending_equity_usd))<.02
        assert int((m.status=="profit").sum())==int(r.profitable_months)
        assert int((m.status=="loss").sum())==int(r.losing_months)
        assert int((m.status=="no_trade").sum())==int(r.idle_months)
        if model.startswith("past12"):
            assert not t.month_ist.lt("2026-01").any()
        else:
            assert not t.month_ist.lt("2025-07").any()
        # Reconstruct 0 bps stress parity, extra costs strictly reducing
        # return in the fixed-order replay.
        stress=sens[sens.model==model].sort_values("extra_roundtrip_bps")
        assert abs(float(stress.net_account_return_pct.iloc[0])-float(r.net_return_pct))<.0002
        assert np.all(np.diff(stress.net_account_return_pct.to_numpy(float))<0)
    original12=cmp[cmp.model=="past12_original"].iloc[0]
    protected12=cmp[cmp.model=="past12_protected"].iloc[0]
    runner12=cmp[cmp.model=="past12_runner"].iloc[0]
    original6=cmp[cmp.model=="past6_original"].iloc[0]
    protected6=cmp[cmp.model=="past6_protected"].iloc[0]
    decision=dict(
      research_integrity="PASS",
      real_money_trading="BLOCKED",
      synthetic_stop_first_next_bar_timing_checks=scenario,
      exact_6m_and_12m_baseline_replay_parity_verified=True,
      entry_same_as_fully_closed_15m_confirmation=True,
      all_five_models_months_and_cash_reconciled=True,
      no_overlap_and_no_trailing_stop_loosening=True,
      original_12m_net_return_pct=float(original12.net_return_pct),
      protected_12m_net_return_pct=float(protected12.net_return_pct),
      protected_12m_delta_percentage_points=round(
          float(protected12.net_return_pct-original12.net_return_pct),4),
      ATR_runner_12m_net_return_pct=float(runner12.net_return_pct),
      original_6m_net_return_pct=float(original6.net_return_pct),
      protected_6m_net_return_pct=float(protected6.net_return_pct),
      protected_6m_delta_percentage_points=round(
          float(protected6.net_return_pct-original6.net_return_pct),4),
      profitable_22_of_22_calendar_months_achieved=False,
      no_untouched_external_holdout=True,
      realized_funding_historical_spreads_liquidation_not_modelled=True,
      selected_exit_configuration_not_promoted=True,
      reason="Profit protection improved 22-month historical returns slightly but failed 22/22; research archive repeatedly examined; costs and live broker feasibility incomplete.",
    )
    assert not bool(protected12.passes_22_22)
    (OUT/"RELEASE_VALIDATION.json").write_text(json.dumps(decision,indent=2)+"\n")
    lines=[
       "# BTC 4-layer 1M exit improvements: independent release gate",
       "",
       "**Research execution and all reconciliation checks passed; real-money trading remains BLOCKED.**",
       "",
       "## Critical OHLC intrabar timing fixtures",
       "~~~json",json.dumps(scenario,indent=2),"~~~","",
       "## Net return and no-go decision",
       "~~~json",json.dumps(decision,indent=2),"~~~","",
       "The 1.5R activation rule updates the stop ONLY at the end of the triggering 1M candle, effective the next minute. A same-minute stop and activation resolves to the pre-existing stop; it never retroactively captures a known high/low. Both baseline equity paths exactly matched published historical 51 and 55 trades.",
       "",
       "The historically favorable exit alteration is an EXPLORATORY insight on an already researched historical dataset. It is not a pristine out-of-sample improvement. Both cases still have only seven positive months of 22; initial 2025 months are training-only. Keep no-live-trading decision until prospective months, actual order-book spread, funding settlement, margin and liquidation/contract feasibility are independently validated.",
    ]
    (OUT/"RELEASE_VALIDATION.md").write_text("\n".join(lines)+"\n")
    print("VALIDATION",json.dumps(decision,indent=2))
    print("DONE_NO_GO")

if __name__=="__main__":
    audit()
