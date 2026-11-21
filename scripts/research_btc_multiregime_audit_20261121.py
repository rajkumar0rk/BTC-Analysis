#!/usr/bin/env python3
"""Audit 1H BTC market-state integrity and past-only multi-regime strategy selection.
No optimized thresholds, no invented labels, no use of current-month returns to select.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

import research_btc_regime_attribution_20261121 as base

OUT = Path("analysis/btc_multiregime_audit_20261121")
OUT.mkdir(parents=True, exist_ok=True)
MONTHS = [str(p) for p in pd.period_range("2025-01", "2026-10", freq="M")]
FIRST_TRADE_MONTH = "2025-07"
TRAIN_MONTHS = 6
MIN_COMPLETED_TRADES = 15
MIN_ACTIVE_MONTHS = 3
MIN_PF_NET_R = 1.15
MIN_MEAN_NET_R = 0.05
RECENT_MONTHS = 3

def month_start_utc(month):
    return pd.Timestamp(month+"-01", tz="Asia/Kolkata").tz_convert("UTC")

def audit_classifier(one, h):
    valid = h[h.valid].copy()
    allowed = set(base.STATES)
    unknown = set(valid.regime.unique()) - allowed
    if unknown or valid.regime.isna().any():
        raise RuntimeError("Unclassified or unknown valid-hour state: "+str(unknown))
    if not h.loc[~h.valid, "regime"].eq("warmup").all():
        raise RuntimeError("Invalid warmup got actionable classification")
    if not h.index.is_unique or not h.index.to_series().diff().iloc[1:].eq(pd.Timedelta(hours=1)).all():
        raise RuntimeError("Hourly data has gaps / duplicates")

    prefix_checks = []
    for end in ("2025-04-15T00:00:00Z", "2025-12-15T00:00:00Z",
                "2026-08-15T00:00:00Z"):
        cutoff = pd.Timestamp(end)
        hist = one.loc[one.index < cutoff]
        recomputed = base.features(hist)
        observed = h.loc[recomputed.index]
        mismatch = int((recomputed.regime != observed.regime).sum())
        val_mismatch = int((recomputed.valid != observed.valid).sum())
        if mismatch or val_mismatch:
            raise RuntimeError("Lookahead/repainting detected at "+end)
        prefix_checks.append(dict(cutoff=end, historical_hours=len(recomputed),
                                  label_mismatches=mismatch, validity_mismatches=val_mismatch))

    # Downstream empirical behavior is DIAGNOSTIC, NOT 'objective label accuracy'.
    forward_delta = (h.close.shift(-4)-h.close)/h.atr
    fut_high = pd.concat([h.high.shift(-j) for j in range(1,5)],axis=1).max(axis=1)
    fut_low = pd.concat([h.low.shift(-j) for j in range(1,5)],axis=1).min(axis=1)
    forward_range = (fut_high-fut_low)/h.atr
    # Nonoverlapping 4H origin intervals to reduce dependence.
    sample = h.iloc[::4].copy()
    sample["forward4_net_atr"] = forward_delta.iloc[::4].to_numpy()
    sample["forward4_range_atr"] = forward_range.iloc[::4].to_numpy()
    sample = sample[sample.valid & (sample.index + pd.Timedelta(hours=5) <= h.index[-1] + pd.Timedelta(hours=1))]
    sample = sample[np.isfinite(sample[["forward4_net_atr","forward4_range_atr"]]).all(axis=1)]
    forward_rows=[]
    for regime in base.STATES:
        g=sample[sample.regime==regime]
        forward_rows.append(dict(regime=regime,sampled_nonoverlapping_4h=int(len(g)),
            average_next4h_net_ATR=round(float(g.forward4_net_atr.mean()),4) if len(g) else None,
            next4h_up_pct=round(float(100*(g.forward4_net_atr>0).mean()),2) if len(g) else None,
            next4h_range_ATR=round(float(g.forward4_range_atr.mean()),3) if len(g) else None))
    forward=pd.DataFrame(forward_rows)
    forward.to_csv(OUT/"forward_behavior_diagnostic.csv",index=False)
    current = valid.regime
    counts=current.value_counts().reindex(base.STATES,fill_value=0)
    transitions = pd.crosstab(current.shift(),current).reindex(
        index=base.STATES,columns=base.STATES,fill_value=0)
    transitions.to_csv(OUT/"hourly_regime_transitions.csv")
    state_share=(100*counts/len(valid)).round(3)
    state_share.rename("pct_all_eligible_hours").to_csv(OUT/"regime_share.csv")
    audit={
       "native_minutes":len(one),
       "total_hours":len(h),
       "eligible_hours":len(valid),
       "warmup_hours":int((~h.valid).sum()),
       "primary_states":len(base.STATES),
       "disallowed_labels":list(unknown),
       "mutually_exclusive_primary_state":True,
       "label_and_validity_history_prefix_invariance":prefix_checks,
       "history_revision_detected":False,
       "mixed_hours":int(counts["mixed"]),
       "mixed_share_pct":round(100*int(counts["mixed"])/len(valid),3),
       "all_hours_nonmixed_share_pct":round(100*(1-int(counts["mixed"])/len(valid)),3),
       "one_hour_label_change_pct":round(float(100*(current.ne(current.shift())).iloc[1:].mean()),3),
       "four_hour_diagnostic_nonoverlapping_samples":len(sample),
       "classifier_objective_ground_truth_accuracy_measurable":False,
       "ground_truth_explanation":"Regime names are deterministic technical proxies; independent manually labeled true market regimes are unavailable. Future results measure predictive utility, NOT actual state-label accuracy.",
    }
    (OUT/"classifier_audit.json").write_text(json.dumps(audit,indent=2)+"\n")
    return audit, forward

def evidence(tr, h):
    alltr = tr.copy()
    alltr["end_utc"] = pd.to_datetime(alltr.exit_utc,utc=True)
    decisions=[]
    mapping={}
    for month in MONTHS:
        mapping[month]={}
        if month < FIRST_TRADE_MONTH:
            for state in base.STATES:
                mapping[month][state]=None
                decisions.append(dict(month_ist=month,regime=state,strategy="NO_TRADE",
                     reason="six_month_training_only",n_prior=0,active_months=0,
                     train_mean_net_R=None,train_PF_net_R=None,recent3_net_R=None,
                     training_period_end=str(month_start_utc(month))))
            continue
        start_idx=MONTHS.index(month)
        previous=MONTHS[max(0,start_idx-TRAIN_MONTHS):start_idx]
        recent=previous[-RECENT_MONTHS:]
        begin=month_start_utc(month)
        # Every training sample must be a COMPLETED trade before current IST month.
        train=alltr[(alltr.month_ist.isin(previous)) & (alltr.end_utc < begin)].copy()
        if not train.empty and not train.end_utc.lt(begin).all():
            raise RuntimeError("Future outcome leaked into training")
        for state in base.STATES:
            ranked=[]
            for strategy in base.SPECS:
                g=train[(train.strategy==strategy)&(train.regime==state)]
                n=len(g)
                active=int(g.month_ist.nunique())
                r=g.net_R.to_numpy(dtype=float)
                mean_r=float(r.mean()) if n else float("nan")
                gains=float(r[r>0].sum()) if n else 0.
                losses=-float(r[r<0].sum()) if n else 0.
                pf=gains/losses if losses>0 else float("nan")
                recentR=float(g.loc[g.month_ist.isin(recent),"net_R"].sum())
                eligible=n>=MIN_COMPLETED_TRADES and active>=MIN_ACTIVE_MONTHS and \
                  np.isfinite(pf) and pf>=MIN_PF_NET_R and mean_r>MIN_MEAN_NET_R and recentR>0
                if eligible:
                    ranked.append((mean_r,pf,strategy,n,active,recentR))
            ranked.sort(key=lambda a:(-a[0],-a[1],a[2]))
            if ranked:
                mr,pf,selected,n,active,recentR=ranked[0]
                mapping[month][state]=selected
                reason="eligible_positive_past_six_months"
            else:
                selected="NO_TRADE";mr=pf=recentR=float("nan")
                n=active=0;reason="insufficient_positive_past_evidence"
                mapping[month][state]=None
            decisions.append(dict(month_ist=month,regime=state,strategy=selected,
                     reason=reason,n_prior=n,active_months=active,
                     train_mean_net_R=round(mr,5) if np.isfinite(mr) else None,
                     train_PF_net_R=round(pf,4) if np.isfinite(pf) else None,
                     recent3_net_R=round(recentR,4) if np.isfinite(recentR) else None,
                     training_period_end=str(begin),trained_complete_months=",".join(previous)))
    decisions=pd.DataFrame(decisions)
    decisions.to_csv(OUT/"selector_decisions.csv",index=False)
    return mapping, decisions

def portfolio_replay(one,h,signals,mapping):
    idx=one.index
    opens=one.open.to_numpy(float)
    highs=one.high.to_numpy(float)
    lows=one.low.to_numpy(float)
    closes=one.close.to_numpy(float)
    equity=base.INITIAL
    occupied = pd.Timestamp("1900-01-01",tz="UTC")
    trades=[]
    candidate_hours=0
    selected_hours=0
    blocked=0
    entries=[]
    for j in range(len(h)):
        if not h.valid.iat[j]:
            continue
        entry_dt=h.index[j]+pd.Timedelta(hours=1)
        month=entry_dt.tz_convert("Asia/Kolkata").strftime("%Y-%m")
        if month not in mapping:
            continue
        state=h.regime.iat[j]
        possible=[s for s in base.SPECS if int(signals[s][j])!=0]
        if possible:
            candidate_hours+=1
        selected=mapping[month][state]
        if selected is None or int(signals[selected][j])==0:
            continue
        selected_hours+=1
        if entry_dt <= occupied:
            blocked+=1
            continue
        at=int(idx.searchsorted(entry_dt))
        if at>=len(idx) or idx[at]!=entry_dt:
            raise RuntimeError("Missing 1M opening fill: "+str(entry_dt))
        if equity<=0:
            raise RuntimeError("Account bankruptcy / missing liquidation model")
        stop_mult, targetR, max_hold=base.SPECS[selected]
        atr=float(h.atr.iat[j])
        side=int(signals[selected][j])
        entry=float(opens[at])
        risk_points=stop_mult*atr
        if risk_points<=0 or not np.isfinite(risk_points):
            raise RuntimeError("Nonfinite initial risk")
        qty=min(equity*base.RISK/risk_points,
                equity*base.LEV_CAP/entry)
        limit=min(at+max_hold*60,len(idx),
                  int(idx.searchsorted(base.next_month_utc(entry_dt))))
        if limit<=at: continue
        sl=entry-side*risk_points
        tp=entry+side*risk_points*targetR
        hi=highs[at:limit]
        lo=lows[at:limit]
        stopidx=np.flatnonzero(lo<=sl if side>0 else hi>=sl)
        targetidx=np.flatnonzero(hi>=tp if side>0 else lo<=tp)
        b=int(stopidx[0]) if len(stopidx) else len(hi)
        g=int(targetidx[0]) if len(targetidx) else len(hi)
        if b<=g and b<len(hi):
            k=at+b
            out=min(sl,opens[k]) if side>0 else max(sl,opens[k])
            exit_reason="stop"
        elif g<len(hi):
            k=at+g
            out=tp
            exit_reason="target"
        else:
            k=limit-1
            out=closes[k]
            exit_reason="timeout_or_month_end"
        entry_fill=entry+side*base.SLIP
        exit_fill=out-side*base.SLIP
        fee_pts=base.FEE*(entry_fill+exit_fill)
        net_pts=side*(exit_fill-entry_fill)-fee_pts
        costfee=qty*fee_pts
        costsli=qty*2*base.SLIP
        pnl=qty*net_pts
        start_equity=equity
        equity+=pnl
        occupied=idx[k]
        trades.append(dict(month_ist=month,regime=state,strategy=selected,side=side,
             entry_utc=str(entry_dt),exit_utc=str(idx[k]),exit_reason=exit_reason,
             qty_btc_equiv=qty,entry_price=entry_fill,exit_price=exit_fill,
             risk_points=risk_points,net_R=net_pts/risk_points,
             pnl_usd=pnl,fee_gst_usd=costfee,slippage_usd=costsli,
             account_return_pct=100*pnl/start_equity,equity_usd=equity))
        entries.append(str(entry_dt))
    if len(set(entries))!=len(entries):
        raise RuntimeError("Two positions opened at same time")
    return pd.DataFrame(trades),dict(
       candidate_signal_hours=candidate_hours,
       selected_signal_hours=selected_hours,
       blocked_due_exclusive_position=blocked,
       actually_executed_trades=len(trades))

def monthly_summary(trades):
    monthly=[]
    prior_equity=base.INITIAL
    for month in MONTHS:
        g=trades[trades.month_ist==month] if not trades.empty else trades
        pnl=float(g.pnl_usd.sum()) if len(g) else 0.
        current_equity=prior_equity+pnl
        mr=100*(current_equity/prior_equity-1)
        monthly.append(dict(month_ist=month,
          trades=len(g), wins=int((g.pnl_usd>0).sum()), losses=int((g.pnl_usd<0).sum()),
          net_return_pct=round(mr,6), net_pnl_usd=round(pnl,2),
          gross_before_costs_usd=round(float((g.pnl_usd+g.fee_gst_usd+g.slippage_usd).sum()),2),
          fee_gst_usd=round(float(g.fee_gst_usd.sum()),2),
          slippage_usd=round(float(g.slippage_usd.sum()),2),
          end_equity_usd=round(current_equity,4),
          status="Profit" if pnl>1e-9 else "Loss" if pnl < -1e-9 else "No trade"))
        prior_equity=current_equity
    m=pd.DataFrame(monthly)
    m.to_csv(OUT/"monthly_portfolio_returns.csv",index=False)
    if len(trades) and abs(float(trades.equity_usd.iloc[-1])-prior_equity)>0.001:
        raise RuntimeError("Monthly/account equity reconciliation failed")
    return m

def main():
    one,manifest=base.load()
    h=base.features(one)
    audit,diagnostic=audit_classifier(one,h)
    signals=base.prepare_signals(h)
    separate=base.run(one,h,signals)
    if len(separate)!=3800:
        raise RuntimeError("Base-replay parity drift: expected 3800 independent trades")
    mapping,decisions=evidence(separate,h)
    for month in MONTHS:
        if month >= FIRST_TRADE_MONTH:
            if not all(x in base.STATES for x in mapping[month]):
                raise RuntimeError("Mapping incomplete")
    portfolio,counters=portfolio_replay(one,h,signals,mapping)
    if len(portfolio):
        portfolio.to_csv(OUT/"selected_trade_ledger.csv",index=False)
        ledger=portfolio
        equity=np.r_[base.INITIAL,ledger.equity_usd.to_numpy(float)]
        gains=float(ledger.loc[ledger.pnl_usd>0,"pnl_usd"].sum())
        losses=-float(ledger.loc[ledger.pnl_usd<0,"pnl_usd"].sum())
        pfrac=gains/losses if losses>0 else None
        drawdown=100*(1-equity/np.maximum.accumulate(equity))
    else:
        (OUT/"selected_trade_ledger.csv").write_text("month_ist,regime,strategy,entry_utc,exit_utc,pnl_usd\n")
        equity=np.array([base.INITIAL])
        pfrac=None;drawdown=np.array([0.])
    month=monthly_summary(portfolio)
    first=month[month.month_ist < FIRST_TRADE_MONTH]
    after=month[month.month_ist >= FIRST_TRADE_MONTH]
    final_equity=float(equity[-1])
    summary=dict(
      target_profitable_months=22,months_total=22,
      first_evaluation_month=FIRST_TRADE_MONTH,
      warmup_months=int(len(first)),
      evaluation_months=int(len(after)),
      months_profitable=int((month.net_pnl_usd>0).sum()),
      months_losing=int((month.net_pnl_usd<0).sum()),
      months_idle=int((month.net_pnl_usd==0).sum()),
      evaluation_months_profitable=int((after.net_pnl_usd>0).sum()),
      evaluation_months_losing=int((after.net_pnl_usd<0).sum()),
      evaluation_months_idle=int((after.net_pnl_usd==0).sum()),
      passes_22_of_22=bool((month.net_pnl_usd>0).all()),
      trades=int(len(portfolio)),
      wins=int((portfolio.pnl_usd>0).sum()) if len(portfolio) else 0,
      losses=int((portfolio.pnl_usd<0).sum()) if len(portfolio) else 0,
      win_rate_pct=round(float(100*(portfolio.pnl_usd>0).mean()),3) if len(portfolio) else 0,
      net_account_return_pct=round(float(100*(final_equity/base.INITIAL-1)),4),
      net_account_pnl_usd=round(final_equity-base.INITIAL,2),
      ending_account_usd=round(final_equity,2),
      max_trade_close_drawdown_pct=round(float(drawdown.max()),3),
      profit_factor=round(float(pfrac),4) if pfrac is not None else None,
      fee_gst_usd=round(float(portfolio.fee_gst_usd.sum()),2) if len(portfolio) else 0,
      slippage_usd=round(float(portfolio.slippage_usd.sum()),2) if len(portfolio) else 0,
      gross_before_costs_usd=round(float(
        portfolio.pnl_usd.sum()+portfolio.fee_gst_usd.sum()+portfolio.slippage_usd.sum()),2) if len(portfolio) else 0,
      non_no_trade_choices=int(decisions.strategy.ne("NO_TRADE").sum()),
      **counters)
    (OUT/"strategy_selector_summary.json").write_text(json.dumps(summary,indent=2)+"\n")
    (OUT/"data_quality.json").write_text(json.dumps({
       "native_minutes":len(one),"source_partitions":len(manifest["partitions"]),
       "first_utc":str(one.index[0]),"last_utc":str(one.index[-1]),
       "verified_1M_data_no_missing":True,
       "candidate_comparison_trades":len(separate),
       "past_only_monthly_rule":True,
       "separate_1M_account_replay":True,
       "fees_each_side_plus_gst":base.FEE,
       "assumed_slippage_points_each_side":base.SLIP,
       "missing_funding_and_spread":True,
       "evaluation_period_was_prior_research_exposed":True},indent=2)+"\n")
    years=[]
    for y,g in month.groupby(month.month_ist.str[:4]):
        v=np.prod(1+g.net_return_pct.to_numpy(float)/100)
        years.append(dict(year=y,months=len(g),trades=int(g.trades.sum()),
            positive=int((g.net_return_pct>0).sum()),
            losing=int((g.net_return_pct<0).sum()),
            idle=int((g.net_return_pct==0).sum()),
            compounded_net_return_pct=round(float(100*(v-1)),4)))
    yearly=pd.DataFrame(years)
    yearly.to_csv(OUT/"yearly_portfolio_returns.csv",index=False)
    mode=decisions.groupby(["regime","strategy"],as_index=False).size()
    report=[
       "# BTCUSD multi-regime classifier + causal strategy-selector correctness audit",
       "",
       "## Distinction",
       "Indicator-based regime labels can be checked for causal correctness and empirical *forward utility*, but not definitive factual correctness without independent ground-truth market labels. Selection correctness means decisions are based on past-only data; profitability is a separate measured question.",
       "",
       "## Quality and no-repainting audit","~~~json",json.dumps(audit,indent=2),"~~~","",
       "Classifier audit passed if history-prefix mismatch counts were zero. Markets can still change regime rapidly; labels are known only AFTER each 1H candle closes.",
       "",
       "## Non-overlapping forward 4H diagnostics (NOT market-label accuracy)",
       diagnostic.to_markdown(index=False),"",
       "## Fixed monthly training-only strategy selection",
       "For every new IST month after 6 months warmup, select among four UNCHANGED baselines for each regime using only the PREVIOUS six COMPLETE months' CLOSED trades; >=15, >=3 active months, PF on normalized net R >=1.15, mean net R >0.05 and last three-month total net R >0; otherwise skip trading that regime.",
       "Selection does not know current month's results. A single exclusive-position account then trades the chosen strategy's future signals, with native 1M stop-first replay, 36/24/12h original timeouts, 0.5% stop-risk, 3x notional cap, hypothetical initial $10k equity, fees/GST/slippage and IST month-end flatten.",
       "",
       "## Selector summary","~~~json",json.dumps(summary,indent=2),"~~~","",
       "## Count of regime choices by strategy",mode.to_markdown(index=False),"",
       "## Annual net account return",yearly.to_markdown(index=False),"",
       "## Actual complete monthly returns including training-only idle months",
       month.to_markdown(index=False),"",
       "## Limitations / correctness gates",
       "- The selector is a causal research test, not evidence of optimal strategy choices. Four historical strategy families cannot guarantee all regimes have profitable trades.",
       "- 2025–2026 histories already influenced the choice to research regime switching, so chronological walk-forward checks are not pristine independent holdouts.",
       "- Primary regime classifier has mixed state; do not force assignment of a strategy when the past signal is weak.",
       "- Assumed taker 0.05% each side plus GST 18%, adverse 5 BTC points slippage per leg. Historical spreads, realized funding payments, queue priority, depth, liquidation and actual contract rounding are not modeled.",
       "- Drawdown sampled on completed trades, not an intratrade equity excursion. Paper/forward trading required before live usage.",
       "- Target 22/22 includes no-trade months as failures. Rolling six-month training makes Jan–Jun 2025 idle; do not hide them in a headline claim.",
       "- Shock/reversal/volatility are OHLCV-based proxies; do not imply institutional intent or liquidations from candles.",
    ]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")
    print("CLASSIFIER_AUDIT",json.dumps(audit))
    print("SELECTOR_SUMMARY",json.dumps(summary))
    print("YEARLY")
    print(yearly.to_string(index=False))
    print("MONTHLY")
    print(month.to_string(index=False))
    print("DONE")

if __name__=="__main__":
    main()
