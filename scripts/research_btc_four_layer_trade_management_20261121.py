#!/usr/bin/env python3
"""Frozen exit-only ablation for BTCUSD 4-layer past-only 6m/12m strategy.

All variants share identical, month-open qualified 1H/4H regime + 15M
confirmation signals. Stop updates occur only *after* completed native 1M
candles, never from unknown same-minute high/low movement.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

import research_btc_regime_attribution_20261121 as base
import research_btc_four_layer_regime_trading_20261121 as core
import research_btc_four_layer_past_only_edge_20261121 as previous

OUT=Path("analysis/btc_four_layer_trade_management_20261121")
OUT.mkdir(parents=True,exist_ok=True)
MONTHS=core.MONTHS
MODELS={
    "past12_original":("past12m_robustness","original"),
    "past12_protected":("past12m_robustness","protected"),
    "past12_runner":("past12m_robustness","runner"),
    "past6_original":("past6m_edge","original"),
    "past6_protected":("past6m_edge","protected"),
}
BREAKEVEN_TRIGGER_R=1.5
PROTECTED_PRICE_BUFFER_R=.15
TRAILING_DISTANCE_ATR=1.8
BREAKOUTS={"structured_breakout","shock_breakout"}

def get_events(confirmed):
    df=pd.read_csv(
        "analysis/btc_four_layer_past_only_edge_20261121/past_only_monthly_eligibility.csv")
    if len(df)!=264:
        raise RuntimeError("Missing pre-existing 264 month/pair/rule gates")
    answer={}
    for window in ("past12m_robustness","past6m_edge"):
        qualified=df[(df.model==window)&(df.selected==True)]
        passes=set(zip(qualified.month_ist,qualified.strategy,qualified.state))
        choices=[e for e in confirmed if
          (e["entry_utc"].tz_convert("Asia/Kolkata").strftime("%Y-%m"),
           e["strategy"],e["state"]) in passes]
        expected=80 if window=="past12m_robustness" else 85
        if len(choices)!=expected:
            raise RuntimeError("Predeclared eligible signal parity drift in "+window)
        # No eligibility assigned after the signal was evaluated.
        for e in choices:
            m=e["entry_utc"].tz_convert("Asia/Kolkata").strftime("%Y-%m")
            if m<("2026-01" if window=="past12m_robustness" else "2025-07"):
                raise RuntimeError("Warmup trade leaked")
        answer[window]=choices
    return answer

def execute(one,hour,events,model,exit_mode):
    assert exit_mode in ("original","protected","runner")
    idx=one.index
    op=one.open.to_numpy(float)
    hi=one.high.to_numpy(float)
    lo=one.low.to_numpy(float)
    cl=one.close.to_numpy(float)
    equity=float(base.INITIAL)
    busy=pd.Timestamp("1900-01-01",tz="UTC")
    rows=[]
    blocked=0
    activated_count=0
    stops_raised=0
    sorted_events=sorted(events,key=lambda e:(e["entry_utc"],e["signal_j"]))
    for e in sorted_events:
        t=e["entry_utc"]
        if t<=busy:
            blocked+=1
            continue
        closed=e["signal_close"]
        confirmed=e["confirm_15m_close"]
        if confirmed is None or t!=confirmed or t!=closed+pd.Timedelta(minutes=15):
            raise RuntimeError("Trade attempted before completed 15M confirmation")
        at=int(idx.searchsorted(t))
        if at>=len(idx) or idx[at]!=t:
            raise RuntimeError("Missing native 1M entry")
        j=int(e["signal_j"])
        atr=float(hour.atr.iat[j])
        if not np.isfinite(atr) or atr<=0:
            raise RuntimeError("Entry ATR invalid")
        strat=e["strategy"]
        if strat not in core.STRATEGIES:
            raise RuntimeError("Unknown eligibility strategy")
        side=int(e["side"])
        if side not in (-1,1):
            raise RuntimeError("Invalid trade direction")
        stop_mult,target_r,max_hours=core.STRATEGIES[strat]
        risk=stop_mult*atr
        entry=float(op[at])
        initial_stop=entry-side*risk
        stop=float(initial_stop)
        original_target=entry+side*risk*target_r
        use_target=(exit_mode!="runner" or strat not in BREAKOUTS)
        month=t.tz_convert("Asia/Kolkata").strftime("%Y-%m")
        if month not in MONTHS:continue
        limit=min(at+max_hours*60,len(idx),int(idx.searchsorted(base.next_month_utc(t))))
        if limit<=at: continue
        qty=min(equity*base.RISK/risk,equity*base.LEV_CAP/entry)
        if qty<=0:raise RuntimeError("Nonpositive quantity")
        activated=False
        updates=0
        highwater=float(entry)
        lowwater=float(entry)
        favorable=float(entry+side*BREAKEVEN_TRIGGER_R*risk)
        exit_index=None
        raw_exit=None
        exit_reason=None
        for k in range(at,limit):
            # 1. Check stop orders activated using evidence from PREVIOUS
            # fully completed minute. A new stop from this bar is NOT active.
            stop_touched=(lo[k]<=stop) if side==1 else (hi[k]>=stop)
            target_touched=((hi[k]>=original_target) if side==1
                  else (lo[k]<=original_target)) if use_target else False
            if stop_touched:
                exit_index=k
                raw_exit=min(stop,op[k]) if side==1 else max(stop,op[k])
                exit_reason=("trailing_or_protected_stop" if updates else "initial_stop")
                break
            elif target_touched:
                exit_index=k
                raw_exit=original_target
                exit_reason="fixed_target"
                break
            if k==limit-1:
                exit_index=k
                raw_exit=float(cl[k])
                exit_reason="time_or_ist_month_end"
                break
            # 2. After THIS complete native 1M bar, update extrema. The
            # resulting order update can only be active for minute k+1.
            highwater=max(highwater,hi[k])
            lowwater=min(lowwater,lo[k])
            if exit_mode!="original" and strat in BREAKOUTS:
                favorable_touched=(hi[k]>=favorable if side==1 else lo[k]<=favorable)
                if favorable_touched and not activated:
                    activated=True
                    activated_count+=1
                if activated:
                    if exit_mode=="protected":
                        proposed=entry+side*PROTECTED_PRICE_BUFFER_R*risk
                    else:
                        proposed=(highwater-TRAILING_DISTANCE_ATR*atr
                                  if side==1 else lowwater+TRAILING_DISTANCE_ATR*atr)
                    updated=(max(stop,proposed) if side==1 else min(stop,proposed))
                    if ((updated>stop+1e-9) if side==1 else (updated<stop-1e-9)):
                        stop=updated
                        updates+=1
                        stops_raised+=1
            if (side==1 and stop<initial_stop-1e-8) or (side==-1 and stop>initial_stop+1e-8):
                raise RuntimeError("Trailing stop ever loosened")
        if exit_index is None:
            raise RuntimeError("Unresolved 1M trade outcome")
        filled_entry=entry+side*base.SLIP
        filled_exit=raw_exit-side*base.SLIP
        fee_points=base.FEE*(filled_entry+filled_exit)
        pnlpoints=side*(filled_exit-filled_entry)-fee_points
        pnl=qty*pnlpoints
        opening_equity=equity
        equity+=pnl
        busy=idx[exit_index]
        if busy.tz_convert("Asia/Kolkata").strftime("%Y-%m")!=month:
            raise RuntimeError("Position crossed IST month-end")
        rows.append(dict(model=model,mode=exit_mode,strategy=strat,state=e["state"],
             side=side,month_ist=month,
             signal_hour_utc=str(hour.index[j]),signal_closed_utc=str(closed),
             confirm_15m_closed_utc=str(confirmed),entry_utc=str(t),
             exit_utc=str(idx[exit_index]),
             entry_price=filled_entry,exit_price=filled_exit,
             initial_stop_raw=initial_stop,final_stop_raw=stop,
             original_target_raw=original_target,target_used=bool(use_target),
             risk_points=risk,qty_btc_equiv=qty,
             gross_before_costs_usd=qty*(side*(filled_exit-filled_entry)+2*base.SLIP),
             fees_gst_usd=qty*fee_points,assumed_slippage_usd=qty*2*base.SLIP,
             net_pnl_usd=pnl,net_R=pnlpoints/risk,
             account_return_pct=100*pnl/opening_equity,
             account_equity_usd=equity,
             stop_activated=bool(activated),stop_update_count=int(updates),
             exit_reason=exit_reason))
    tr=pd.DataFrame(rows)
    if len(tr):
        entries=pd.to_datetime(tr.entry_utc,utc=True)
        exits=pd.to_datetime(tr.exit_utc,utc=True)
        if not entries.is_monotonic_increasing or \
           (len(tr)>1 and not (entries.iloc[1:].to_numpy()>exits.iloc[:-1].to_numpy()).all()):
            raise RuntimeError("Exclusive account had two concurrent positions")
        if abs(float(tr.net_pnl_usd.sum())+base.INITIAL-equity)>0.001:
            raise RuntimeError("Account PnL/equity mismatch")
        if not np.allclose(
          tr.gross_before_costs_usd-tr.fees_gst_usd-tr.assumed_slippage_usd,
          tr.net_pnl_usd,atol=1e-6):
            raise RuntimeError("Gross minus costs != net")
    return tr,dict(model=model,candidate_events=len(sorted_events),
       exclusive_position_rejections=blocked,entry_unavailable=0,
       executed_trades=len(tr),trades_activated=activated_count,
       post_bar_stop_updates=stops_raised)

def summary(tr,model,counts):
    mon=core.monthly(tr,model)
    # core.monthly() only requires month_ist/trades/pnl/cost/equity names.
    # This experiment kept every shared name intact.
    s=core.summarize(tr,mon,model,counts)
    return mon,s

def stress_cost(tr,model):
    eqprev=np.r_[base.INITIAL,tr.account_equity_usd.to_numpy(float)[:-1]]
    qtyrate=tr.qty_btc_equiv.to_numpy(float)/eqprev
    pnlrate=tr.net_pnl_usd.to_numpy(float)/eqprev
    notionalrate=qtyrate*tr.entry_price.to_numpy(float)
    rows=[]
    for bps in (0,2,5,10):
        eq=float(base.INITIAL)
        by_month={m:0. for m in MONTHS}
        additional=0.
        for i,m in enumerate(tr.month_ist):
            surcharge=eq*notionalrate[i]*bps/10000
            pnl=eq*pnlrate[i]-surcharge
            eq+=pnl
            by_month[m]+=pnl
            additional+=surcharge
            if eq<=0:raise RuntimeError("Extra-cost stress bankrupted account")
        if bps==0 and abs(eq-float(tr.account_equity_usd.iloc[-1]))>0.001:
            raise RuntimeError("0bps cost sensitivity failed exact original equity")
        positives=sum(v>0.000000001 for v in by_month.values())
        negatives=sum(v < -0.000000001 for v in by_month.values())
        rows.append(dict(model=model,extra_roundtrip_bps=bps,
           net_account_return_pct=round(100*(eq/base.INITIAL-1),4),
           additional_spread_like_cost_usd=round(additional,2),
           profitable_months=positives,losing_months=negatives,
           no_trade_months=22-positives-negatives))
    return rows

def main():
    one,manifest=base.load()
    if len(one)!=992160:
        raise RuntimeError("Delta native BTCUSD archive parity failed")
    hour,states,decisions,raw,eligible,confirmed=core.context(one)
    available=get_events(confirmed)
    if len(confirmed)!=513:
        raise RuntimeError("Original confirmed candidate count changed")
    original=pd.read_csv(
      "analysis/btc_four_layer_past_only_edge_20261121/comparison_summary.csv")
    original6=pd.read_csv(
      "analysis/btc_four_layer_past_only_edge_20261121/trade_ledger_past6m_edge.csv")
    original12=pd.read_csv(
      "analysis/btc_four_layer_past_only_edge_20261121/trade_ledger_past12m_robustness.csv")
    previous_rows={"past12_original":original12,"past6_original":original6}
    result=[];allmonth=[];year=[];extra=[];groups=[]
    for model,(window,exit_mode) in MODELS.items():
        tr,counts=execute(one,hour,available[window],model,exit_mode)
        if model in previous_rows:
            published=previous_rows[model]
            p=original[original.model==window].iloc[0]
            if len(tr)!=len(published) or len(tr)!=int(p.trades):
                raise RuntimeError("Baseline trade count parity failed for "+model)
            if not np.array_equal(tr.entry_utc.to_numpy(),published.entry_utc.to_numpy()):
                raise RuntimeError("Baseline entry order changed for "+model)
            if not np.array_equal(tr.exit_utc.to_numpy(),published.exit_utc.to_numpy()):
                raise RuntimeError("Baseline exit time changed for "+model)
            if not np.allclose(tr.net_pnl_usd.to_numpy(float),
                    published.net_pnl_usd.to_numpy(float),atol=1e-6,rtol=0):
                raise RuntimeError("Baseline trade PnL changed for "+model)
        if not len(tr):
            raise RuntimeError("No strategy trades in selected 2026 data for "+model)
        tr.to_csv(OUT/("trade_ledger_"+model+".csv"),index=False)
        monthly,s=summary(tr,model,counts)
        months0=12 if window=="past12m_robustness" else 6
        if int(monthly.iloc[:months0].trades.sum())!=0:
            raise RuntimeError("Strategy traded during training period")
        result.append(s)
        allmonth.append(monthly)
        extra.extend(stress_cost(tr,model))
        annual=monthly.copy()
        annual["year"]=annual.month_ist.str[:4]
        for y,g in annual.groupby("year"):
            year.append(dict(model=model,year=y,months=len(g),
                profitable=int((g.status=="profit").sum()),
                losing=int((g.status=="loss").sum()),
                no_trade=int((g.status=="no_trade").sum()),
                compounded_net_return_pct=round(100*(np.prod(1+g.month_net_return_pct.to_numpy(float)/100)-1),4)))
        d=tr.groupby(["strategy","state"],as_index=False).agg(
            trades=("net_pnl_usd","size"),wins=("net_pnl_usd",lambda s:int((s>0).sum())),
            net_usd=("net_pnl_usd","sum"),net_R=("net_R","sum"),
            stop_update_trades=("stop_update_count",lambda x:int((x>0).sum())))
        d["model"]=model
        groups.append(d)
    summary_df=pd.DataFrame(result)
    monthly=pd.concat(allmonth,ignore_index=True)
    yy=pd.DataFrame(year)
    sens=pd.DataFrame(extra)
    grouping=pd.concat(groups,ignore_index=True)
    summary_df.to_csv(OUT/"comparison_summary.csv",index=False)
    monthly.to_csv(OUT/"monthly_account_returns.csv",index=False)
    yy.to_csv(OUT/"yearly_account_returns.csv",index=False)
    sens.to_csv(OUT/"additional_spread_sensitivity.csv",index=False)
    grouping.to_csv(OUT/"strategy_and_state_attribution.csv",index=False)
    quality=dict(
        native_1m_bars=len(one),data_partitions=len(manifest["partitions"]),
        original_15m_confirmed_candidate_signals=len(confirmed),
        original_6m_eligibility_event_count=len(available["past6m_edge"]),
        original_12m_eligibility_event_count=len(available["past12m_robustness"]),
        independent_original_6m_baseline_trade_level_parity=True,
        independent_original_12m_baseline_trade_level_parity=True,
        selected_12m_and_6m_gates_fixed_from_previous_study=True,
        fixed_breakout_protect_trigger_R=BREAKEVEN_TRIGGER_R,
        fixed_stop_protection_offset_R=PROTECTED_PRICE_BUFFER_R,
        fixed_runner_trailing_atr=TRAILING_DISTANCE_ATR,
        trailing_updates_only_effective_following_1m_bar=True,
        stop_first_same_1m_bar=True,one_position_global=True,
        original_fee_gst_and_slippage_preserved=True,
        original_month_selection_uses_original_exit_shadow_trades=True,
        realized_funding_ledger_included=False,historical_spread_included=False,
        liquidation_and_exchange_contract_rounding_included=False,
        external_unresearched_validation_available=False,
        live_trading_approved=False
    )
    (OUT/"quality.json").write_text(json.dumps(quality,indent=2)+"\n")
    report=[
      "# BTC four-layer evidence selector — native 1M exit-management follow-up",
      "",
      "## Fixed mechanism and no-hindsight rule",
      "This is a controlled **exit-only** ablation of the already positive 6M/12M past-only eligibility rules. Regime detection and eligibility / first 15M confirmation are unchanged; no retrospective exclusion of losing 2026 months. The same 2025–2026 archive has been repeatedly researched and is **not a pristine holdout**.",
      "",
      "## Quality","~~~json",json.dumps(quality,indent=2),"~~~","",
      "## After-cost 22-month account returns",
      summary_df.to_markdown(index=False),"",
      "## Annual net returns (training-only months count as idle)",
      yy.to_markdown(index=False),"",
      "## Complete month-by-month after-cost % returns",
      monthly.pivot(index="month_ist",columns="model",values="month_net_return_pct").round(3).to_markdown(),"",
      "## Additional hypothetical execution cost sensitivity, roundtrip bps",
      "These are *additional* bps applied on entry notional to existing taker fees+GST+5-price-point slip per leg, not observed exchange L1 spreads.",
      sens.to_markdown(index=False),"",
      "## Account contribution by original strategy / regime",
      grouping.round(3).to_markdown(index=False),"",
      "## Caveats and decision",
      "Stops update only after each fully completed native 1M candle, and only affect subsequent minutes. If active stop and TP touch inside the same candle, stop wins. The original fixed target remains 3R for breakout protection; runner removes the breakout TP and trails at 1.8 ATR14 after 1.5R activation. Original stop and 36-hour timeout unchanged.",
      "Historical monthly eligibility was trained on shadow trades made with the original 3R exits, NOT with the new exit variants. Thus even an improved exit model is a conditional ablation, not an internally re-trained standalone alpha system. Bid/ask, realized funding, liquidation and exchange contract rounding not reconstructed. Drawdown only at trade exits. Never promote a result to real-money trading without genuinely unseen forward testing and actual exchange-cost verification.",
    ]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")
    print("SUMMARY\n"+summary_df.to_string(index=False))
    print("YEARLY\n"+yy.to_string(index=False))
    print("MONTHLY\n"+monthly.pivot(index="month_ist",columns="model",values="month_net_return_pct").round(3).to_string())
    print("STRESS\n"+sens.to_string(index=False))
    print("DONE")

if __name__=="__main__":
    main()
