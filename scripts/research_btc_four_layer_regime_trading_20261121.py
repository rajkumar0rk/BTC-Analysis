#!/usr/bin/env python3
"""Four-layer BTCUSD market-state -> eligibility -> 15M confirmation -> 1M exit.

Uses *existing* frozen 1H signal families and the completed 1H/4H causal market
observer. Parameters/ablation controls registered in NOVELTY_CHECK.md before
any outcome is inspected. This is research, NOT live order execution.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

import research_btc_regime_attribution_20261121 as base
import research_btc_mtf_market_structure_audit_20261121 as mtf

OUT = Path("analysis/btc_four_layer_regime_trading_20261121")
OUT.mkdir(parents=True, exist_ok=True)
MONTHS = [str(x) for x in pd.period_range("2025-01", "2026-10", freq="M")]
STRATEGIES = {
    "trend_pullback": (1.6, 2.5, 24),
    "shock_breakout": (1.8, 3.0, 36),
    "structured_breakout": (1.8, 3.0, 36),
    "range_fade": (1.2, 1.5, 12),
}
COMPARATORS = [
    "no_trade",
    "ungated_immediate",
    "regime_eligible_immediate",
    "four_layer_15m_confirmed",
]

def context(one):
    hour = base.features(one)
    states = mtf.classify(one)
    if not hour.index.equals(states.index):
        raise RuntimeError("1H data and market observer disagree on hour boundaries")
    if not ((states.decision_close_utc >= states.available4_utc).loc[states.valid]).all():
        raise RuntimeError("4H future candle leaked to 1H decision")
    signals = base.prepare_signals(hour)
    p15 = one.resample("15min").agg(
        open=("open", "first"), high=("high", "max"),
        low=("low", "min"), close=("close", "last"))
    counts = one.close.resample("15min").count()
    if not counts.eq(15).all():
        raise RuntimeError("15M aggregation contains incomplete candles")

    # Fields from different layers are recorded separately: the market label
    # is never itself a future-price or trade-winning prediction.
    decision = []
    immediate_all = []
    regime_only = []
    confirmed = []
    for j in range(len(hour)):
        state = states.state.iat[j]
        decision_close = hour.index[j] + pd.Timedelta(hours=1)
        mm = decision_close.tz_convert("Asia/Kolkata").strftime("%Y-%m")
        bias4 = int(states.trend_4h_side.iat[j])
        bias1 = int(states.trend_1h_side.iat[j])
        raw_sides = {
            "trend_pullback": int(signals["trend_pullback"][j]),
            "donchian_breakout": int(signals["donchian_breakout"][j]),
            "bollinger_reversion": int(signals["bollinger_reversion"][j]),
        }
        eligibility = None
        reason = "not_eligible_state"
        if mm in MONTHS and states.valid.iat[j]:
            if state in ("confirmed_trend_up", "confirmed_trend_down"):
                side = 1 if state == "confirmed_trend_up" else -1
                if raw_sides["trend_pullback"] == side and bias4 == side and bias1 == side:
                    eligibility = ("trend_pullback", side)
                    reason = "mtf_trend_pullback"
                else:
                    reason = "no_matching_trend_pullback"
            elif state == "shock":
                side = raw_sides["donchian_breakout"]
                if side and bias4 == side:
                    eligibility = ("shock_breakout", side)
                    reason = "shock_direction_matches_closed_4h"
                else:
                    reason = "shock_no_4h_aligned_breakout"
            elif state in ("breakout_up", "breakout_down"):
                side = 1 if state == "breakout_up" else -1
                if raw_sides["donchian_breakout"] == side and bias4 in (0, side):
                    eligibility = ("structured_breakout", side)
                    reason = "confirmed_close_breakout_not_counter_4h"
                else:
                    reason = "breakout_direction_4h_conflict_or_no_signal"
            elif state == "range":
                side = raw_sides["bollinger_reversion"]
                if side != 0 and bias4 == 0:
                    eligibility = ("range_fade", side)
                    reason = "range_bb_reversion_4h_neutral"
                else:
                    reason = "range_no_bb_or_4h_trend"
            else:
                reason = "explicit_no_trade_" + state
        elif mm not in MONTHS:
            reason = "outside_22_complete_months"
        else:
            reason = "hour_or_4h_warmup_unclassified"

        # Unrestricted ablation: a fixed priority among EXACT existing signal
        # families, no 4H regime-based eligibility. No future information.
        raw_trade = None
        if mm in MONTHS and hour.valid.iat[j]:
            if raw_sides["donchian_breakout"]:
                raw_trade = ("structured_breakout", raw_sides["donchian_breakout"])
            elif raw_sides["trend_pullback"]:
                raw_trade = ("trend_pullback", raw_sides["trend_pullback"])
            elif raw_sides["bollinger_reversion"]:
                raw_trade = ("range_fade", raw_sides["bollinger_reversion"])
            if raw_trade:
                immediate_all.append(dict(signal_j=j, strategy=raw_trade[0],
                    side=raw_trade[1], signal_close=decision_close,
                    entry_utc=decision_close, state=state,
                    confirm_15m_close=None))

        confirmed_yes = False
        validation = "not_applicable"
        if eligibility:
            chosen, side = eligibility
            regime_only.append(dict(signal_j=j, strategy=chosen, side=side,
                signal_close=decision_close, entry_utc=decision_close,
                state=state, confirm_15m_close=None))
            if decision_close in p15.index:
                bar = p15.loc[decision_close]
                up = side == 1
                # Only the NEXT complete 15M candle can confirm the original
                # 1H setup. No use of that candle's HIGH/LOW as an earlier fill.
                candle_matches = bool(bar.close > bar.open) if up else bool(bar.close < bar.open)
                if chosen == "trend_pullback":
                    level = float(hour.ema20.iat[j])
                    level_matches = bool(bar.close > level) if up else bool(bar.close < level)
                elif chosen in ("shock_breakout", "structured_breakout"):
                    level = float(hour.hi24.iat[j]) if up else float(hour.lo24.iat[j])
                    level_matches = bool(bar.close > level) if up else bool(bar.close < level)
                else:
                    level = float(hour.close.iat[j])
                    level_matches = bool(bar.close > level) if up else bool(bar.close < level)
                confirmed_yes = candle_matches and level_matches
                validation = "confirmed" if confirmed_yes else "15m_no_direction_or_level_reclaim"
                if confirmed_yes:
                    # Bar opens at the 1H decision boundary and closes 15M
                    # later. Earliest permitted entry is that next minute OPEN.
                    later = decision_close + pd.Timedelta(minutes=15)
                    if later not in one.index:
                        raise RuntimeError("Missing native 1M fill immediately after 15M confirmation")
                    confirmed.append(dict(signal_j=j, strategy=chosen, side=side,
                         signal_close=decision_close, entry_utc=later,
                         state=state, confirm_15m_close=later))
            else:
                validation = "missing_15m_after_hour_close"

        decision.append(dict(
            signal_hour_start_utc=str(hour.index[j]),
            signal_closed_utc=str(decision_close),
            available_4h_close_utc=str(states.available4_utc.iat[j])
                if pd.notna(states.available4_utc.iat[j]) else "",
            month_ist=mm, state=state, observer_valid=bool(states.valid.iat[j]),
            trend_1h_side=bias1, trend_4h_side=bias4,
            raw_donchian_side=raw_sides["donchian_breakout"],
            raw_trend_pullback_side=raw_sides["trend_pullback"],
            raw_bollinger_side=raw_sides["bollinger_reversion"],
            selected_strategy=eligibility[0] if eligibility else "NO_TRADE",
            selected_side=eligibility[1] if eligibility else 0,
            regime_eligibility_reason=reason,
            first_future_15m_completed_utc=str(decision_close+pd.Timedelta(minutes=15)),
            first_15m_confirmed=confirmed_yes,
            fifteen_minute_confirmation_result=validation,
            earliest_confirmed_entry_utc=str(decision_close+pd.Timedelta(minutes=15))
                 if confirmed_yes else "",
        ))
    decisions = pd.DataFrame(decision)
    decisions.to_csv(OUT/"decision_audit.csv", index=False)
    if not (decisions[decisions.first_15m_confirmed].selected_strategy != "NO_TRADE").all():
        raise RuntimeError("An ineligible regime was magically confirmed")
    return hour, states, decisions, immediate_all, regime_only, confirmed

def execute(one, hour, events, model):
    if not events:
        return pd.DataFrame(), dict(
          model=model, candidate_events=0, exclusive_position_rejections=0,
          entry_unavailable=0, executed_trades=0)
    idx=one.index
    opens=one.open.to_numpy(float)
    highs=one.high.to_numpy(float)
    lows=one.low.to_numpy(float)
    closes=one.close.to_numpy(float)
    eq=float(base.INITIAL)
    occupied=pd.Timestamp("1900-01-01",tz="UTC")
    events=sorted(events,key=lambda e:(e["entry_utc"],e["signal_j"]))
    rows=[]
    blocks=0
    unavailable=0
    for e in events:
        t=e["entry_utc"]
        if t<=occupied:
            blocks+=1
            continue
        j=int(e["signal_j"])
        first=e["signal_close"]
        if t<first or (e["confirm_15m_close"] is not None and t<e["confirm_15m_close"]):
            raise RuntimeError("Trade entered before signal hour or confirming 15M bar completed")
        at=int(idx.searchsorted(t))
        if at==len(idx) or idx[at]!=t:
            unavailable+=1
            continue
        if eq<=0:
            raise RuntimeError("Account equity nonpositive; liquidation and broker risk are not modeled")
        strategy=e["strategy"]
        side=int(e["side"])
        if strategy not in STRATEGIES or side not in (-1,1):
            raise RuntimeError("Unregistered signal type")
        stop_atr, target_r, hold_hours=STRATEGIES[strategy]
        risk_pts=stop_atr*float(hour.atr.iat[j])
        if not np.isfinite(risk_pts) or risk_pts<=0:
            raise RuntimeError("Nonfinite ATR risk")
        month=t.tz_convert("Asia/Kolkata").strftime("%Y-%m")
        if month not in MONTHS:
            continue
        limit=min(at+hold_hours*60,len(idx),
                  int(idx.searchsorted(base.next_month_utc(t))))
        if limit<=at:
            continue
        entry=float(opens[at])
        qty=min(eq*base.RISK/risk_pts, eq*base.LEV_CAP/entry)
        if qty<=0:
            raise RuntimeError("Zero notional position")
        stop=entry-side*risk_pts
        tp=entry+side*risk_pts*target_r
        hh=highs[at:limit]
        ll=lows[at:limit]
        bad=np.flatnonzero(ll<=stop if side==1 else hh>=stop)
        good=np.flatnonzero(hh>=tp if side==1 else ll<=tp)
        b=int(bad[0]) if len(bad) else len(hh)
        g=int(good[0]) if len(good) else len(hh)
        if b<=g and b<len(hh):
            k=at+b
            raw_exit=min(stop,opens[k]) if side==1 else max(stop,opens[k])
            reason="stop"
        elif g<len(hh):
            k=at+g
            raw_exit=tp
            reason="target"
        else:
            k=limit-1
            raw_exit=float(closes[k])
            reason="time_or_month_end"
        entryfill=entry+side*base.SLIP
        exitfill=raw_exit-side*base.SLIP
        fee_points=base.FEE*(entryfill+exitfill)
        gross_points=side*(exitfill-entryfill)
        net_points=gross_points-fee_points
        pnl=qty*net_points
        entry_account=eq
        eq+=pnl
        occupied=idx[k]
        if not (idx[k].tz_convert("Asia/Kolkata").strftime("%Y-%m")==month):
            raise RuntimeError("Exited after intended IST month end")
        rows.append(dict(model=model, strategy=strategy, state=e["state"],
              side=side, month_ist=month, signal_hour_utc=str(hour.index[j]),
              signal_closed_utc=str(first),
              confirm_15m_closed_utc=str(e["confirm_15m_close"]) if e["confirm_15m_close"] is not None else "",
              entry_utc=str(t),exit_utc=str(idx[k]),
              entry_price=entryfill,exit_price=exitfill,stop_raw_price=stop,
              target_raw_price=tp,stop_risk_points=risk_pts,
              tp_r_multiple=target_r, qty_btc_equiv=qty,
              gross_before_costs_usd=qty*(gross_points+2*base.SLIP),
              fees_gst_usd=qty*fee_points,
              assumed_slippage_usd=qty*2*base.SLIP,
              net_pnl_usd=pnl,net_R=net_points/risk_pts,
              account_return_pct=100*pnl/entry_account,
              account_equity_usd=eq,exit_reason=reason))
    tr=pd.DataFrame(rows)
    if len(tr):
        entry_times=pd.to_datetime(tr.entry_utc,utc=True)
        exit_times=pd.to_datetime(tr.exit_utc,utc=True)
        if not entry_times.is_monotonic_increasing or \
           (len(tr)>1 and not (entry_times.iloc[1:].to_numpy()>exit_times.iloc[:-1].to_numpy()).all()):
            raise RuntimeError("Overlapping global positions")
        if abs(float(tr.net_pnl_usd.sum())+base.INITIAL-eq)>.001:
            raise RuntimeError("Single account failed PnL reconciliation")
        if not np.allclose(
           tr.gross_before_costs_usd-tr.fees_gst_usd-tr.assumed_slippage_usd,
           tr.net_pnl_usd,atol=1e-6):
            raise RuntimeError("Gross-cost-net cash reconciliation failed")
    return tr,dict(model=model,candidate_events=len(events),
                   exclusive_position_rejections=blocks,
                   entry_unavailable=unavailable,
                   executed_trades=len(tr))

def monthly(tr,model):
    equity=float(base.INITIAL)
    rows=[]
    for month in MONTHS:
        g=tr.loc[tr.month_ist==month] if len(tr) else tr
        pnl=float(g.net_pnl_usd.sum()) if len(g) else 0.
        start=equity
        equity+=pnl
        rows.append(dict(model=model,month_ist=month,trades=len(g),
          wins=int((g.net_pnl_usd>0).sum()) if len(g) else 0,
          losses=int((g.net_pnl_usd<0).sum()) if len(g) else 0,
          month_net_return_pct=round(100*pnl/start,6),
          month_net_pnl_usd=round(pnl,2),
          month_end_equity_usd=round(equity,4),
          fees_gst_usd=round(float(g.fees_gst_usd.sum()),2) if len(g) else 0.,
          slippage_usd=round(float(g.assumed_slippage_usd.sum()),2) if len(g) else 0.,
          status="profit" if pnl>1e-8 else "loss" if pnl < -1e-8 else "no_trade"))
    if len(tr) and abs(equity-float(tr.account_equity_usd.iloc[-1]))>.001:
        raise RuntimeError("Monthly cash and ledger fail reconciliation")
    return pd.DataFrame(rows)

def summarize(tr,month,model,counts):
    gain=float(tr.loc[tr.net_pnl_usd>0,"net_pnl_usd"].sum()) if len(tr) else 0.
    loss=-float(tr.loc[tr.net_pnl_usd<0,"net_pnl_usd"].sum()) if len(tr) else 0.
    curve=np.r_[float(base.INITIAL),tr.account_equity_usd.to_numpy(float)] if len(tr) else np.array([float(base.INITIAL)])
    final=float(curve[-1])
    return dict(model=model,**{k:v for k,v in counts.items() if k!="model"},
         trades=len(tr),wins=int((tr.net_pnl_usd>0).sum()) if len(tr) else 0,
         win_rate_pct=round(float(100*(tr.net_pnl_usd>0).mean()),3) if len(tr) else 0.,
         profit_factor=round(gain/loss,4) if loss else None,
         net_return_pct=round(100*(final/base.INITIAL-1),4),
         net_profit_usd=round(final-base.INITIAL,2),
         ending_equity_usd=round(final,2),
         max_trade_close_drawdown_pct=round(float(100*(1-curve/np.maximum.accumulate(curve)).max()),3),
         fees_gst_usd=round(float(tr.fees_gst_usd.sum()),2) if len(tr) else 0.,
         slippage_usd=round(float(tr.assumed_slippage_usd.sum()),2) if len(tr) else 0.,
         profitable_months=int((month.status=="profit").sum()),
         losing_months=int((month.status=="loss").sum()),
         idle_months=int((month.status=="no_trade").sum()),
         passes_22_22=bool((month.status=="profit").all()))

def main():
    one,manifest=base.load()
    if len(one)!=992160:
        raise RuntimeError("Native SHA256 data manifest changed unexpectedly")
    hour,states,decision,raw,eligible,confirmed=context(one)
    prefixes=mtf.past_recomputation(one,states)
    if any(x["revised_state_labels"] or x["revised_validity_flags"] for x in prefixes):
        raise RuntimeError("Multitimeframe market-state lookahead")
    outputs={"no_trade":[], "ungated_immediate":raw,
             "regime_eligible_immediate":eligible,
             "four_layer_15m_confirmed":confirmed}
    summary_rows=[]; monthly_rows=[]; count_rows=[]
    by_strategy=[]
    for name in COMPARATORS:
        events=outputs[name]
        ledger,counters=execute(one,hour,events,name)
        (OUT/("trade_ledger_"+name+".csv")).write_text(
           ledger.to_csv(index=False) if len(ledger) else
           "model,strategy,state,entry_utc,exit_utc,net_pnl_usd\n")
        mon=monthly(ledger,name)
        summary_rows.append(summarize(ledger,mon,name,counters))
        monthly_rows.append(mon)
        count_rows.append(counters)
        if len(ledger):
            grp=ledger.groupby(["strategy","state"],as_index=False).agg(
                trades=("net_pnl_usd","size"),net_pnl_usd=("net_pnl_usd","sum"),
                wins=("net_pnl_usd",lambda x:int((x>0).sum())))
            grp["model"]=name
            by_strategy.append(grp)
    summary=pd.DataFrame(summary_rows)
    monthlyframe=pd.concat(monthly_rows,ignore_index=True)
    summary.to_csv(OUT/"comparison_summary.csv",index=False)
    monthlyframe.to_csv(OUT/"monthly_account_returns.csv",index=False)
    pd.DataFrame(count_rows).to_csv(OUT/"candidate_execution_counts.csv",index=False)
    if by_strategy:
        pd.concat(by_strategy,ignore_index=True).to_csv(OUT/"by_strategy_and_state.csv",index=False)
    annual=[]
    for (model,year),g in monthlyframe.groupby(["model",monthlyframe.month_ist.str[:4]]):
        annual.append(dict(model=model,year=year,months=len(g),
             trades=int(g.trades.sum()),positive=int((g.status=="profit").sum()),
             losing=int((g.status=="loss").sum()),idle=int((g.status=="no_trade").sum()),
             compounded_net_return_pct=round(float(100*(np.prod(1+g.month_net_return_pct.to_numpy(float)/100)-1)),5)))
    yr=pd.DataFrame(annual)
    yr.to_csv(OUT/"yearly_account_returns.csv",index=False)
    elig=decision[decision.selected_strategy!="NO_TRADE"]
    confirm_count=int(decision.first_15m_confirmed.sum())
    q=dict(data="Delta India native BTCUSD 1M, each source gzip SHA256 verified",
       candles_native_1m=len(one),source_partitions=len(manifest["partitions"]),
       complete_IST_months=22,first_utc=str(one.index[0]),last_utc=str(one.index[-1]),
       full_1h_bars=len(hour),
       valid_current_1h_and_4h_states=int(states.valid.sum()),
       completed_4h_lookahead_violations=0,
       fifteen_minute_bars_verified_complete=True,
       hourly_observation_no_repaint_prefixes=prefixes,
       signal_hourly_decisions=len(decision),
       signals_with_state_strategy_eligibility=len(elig),
       signals_confirmed_by_first_future_15m=confirm_count,
       eligibility_confirmation_acceptance_pct=round(float(100*confirm_count/len(elig)),2) if len(elig) else 0.,
       uncertain_current_state_share_pct=round(float(100*(states.loc[states.valid,"state"]=="mixed_uncertain").mean()),3),
       one_position_globally_per_model=True,
       stop_target_uses_1m_conservative_stop_first=True,
       fee_taker_each_side_plus_GST=base.FEE,
       assumed_adverse_slippage_btc_price_points_each_leg=base.SLIP,
       simulated_account_initial_usd=base.INITIAL,
       stop_risk_frac_current_equity=base.RISK,max_notional_leverage=base.LEV_CAP,
       actual_funding_transfers_included=False,
       historical_bid_ask_spread_available=False,
       liquidation_and_margin_feasibility_modelled=False,
       prospective_fresh_holdout=False,after_cost_live_readiness=False)
    (OUT/"execution_quality.json").write_text(json.dumps(q,indent=2)+"\n")
    report=[
      "# BTCUSD four-layer market-regime trading architecture: independently replayed 22-month 1M research",
      "",
      "## What was built and what it is NOT",
      "Four separate causal layers: **(1) last closed 1H+4H market-state observation → (2) predetermined strategy eligibility → (3) completed subsequent 15M directional confirmation → (4) independent stop-first native 1M exit with own $10k equity and one global position**. This experiment deliberately holds signals and exit rules fixed, comparing eligibility and confirmation ablations. Classification of past structure does not imply knowing the next price direction; no model or threshold was optimized against this run.",
      "",
      "## Data, leakage and execution audits",
      "~~~json",json.dumps(q,indent=2),"~~~","",
      "## Net after modeled taker fees, 18% GST and 5 BTC points slip per leg",
      summary.to_markdown(index=False),"",
      "## 22 complete IST calendar months, actual compounded-account net percent",
      monthlyframe.pivot(index="month_ist",columns="model",values="month_net_return_pct").round(3).to_markdown(),"",
      "## Year-by-year account results",
      yr.to_markdown(index=False),"",
      "## Interpretation",
      "- Market state is a description of already closed 1H+4H price data. MIXED/TRANSITION/COMPRESSION are deliberately abstentions, not predictive failures.",
      "- First subsequent 15M candle is only inspected AFTER closing. Trade entry is its next minute OPEN, never the confirming candle's already-occurred high/low.",
      "- The immediate and 15M-confirmed state-eligible variants have identical predefined 1H eligibility and identical 1M exit/position rules; the difference isolates 15M confirmation and entry latency.",
      "- The ungated immediate reference uses same signal families and stop/TP per strategy with no MTF regime filter, NOT a separately tuned baseline.",
      "- No-trade months FAIL the user's 22/22 net-positive-month target, just like losing months.",
      "- This archive was previously investigated in many research iterations; it is NOT a pristine independent holdout. No funding cash flow, observed spread, order book, exchange contract rounding or liquidation model. These are hypothetical account results, not validated real-money trade fills.",
      "- Time-based drawdown here samples trade closes, not intratrade mark-to-market equity. All capital/return figures should be interpreted with that limit.",
      "- If both eligible versions lose, the correct finding is that adding layers has not created an edge. No live deployment or production change is authorized.",
    ]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")
    print("COMPARISON",summary.to_string(index=False))
    print("YEARLY",yr.to_string(index=False))
    print("MONTHLY",monthlyframe.pivot(index="month_ist",columns="model",values="month_net_return_pct").round(3).to_string())
    print("DONE")

if __name__=="__main__":
    main()
