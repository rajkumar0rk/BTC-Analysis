#!/usr/bin/env python3
"""Actual BTC 1-minute exit/entry-filter improvement of Stage18/20 core Stage15 sleeve.

Replay authentic Stage14 event-state candidates on original 1-minute candles with
the preexisting Stage15 replay_one stop-first engine, changing stop/target/hold or
causal pre-entry filters. No monthly-only portfolio weight optimization.
Then recombine newly executed primary-sleeve trade returns with the ORIGINAL
Stage17 and Stage19 monthly sleeves to evaluate impact on Stage18 and Stage20.
IMPORTANT: the final multi-sleeve blend still lacks integrated shared margin,
real bid/ask spread/funding and true simultaneous portfolio execution.
"""
from pathlib import Path
import os, json
import numpy as np
import pandas as pd
import research_july_drawdown_stage15 as s15
from research_every_candle_200 import read_archive

OUT=Path("analysis/stage18_stage20_signal_exit_improvement_20261120")
MONTHS=pd.period_range("2025-01","2026-10",freq="M").astype(str).tolist()
EVENTS=Path(os.environ.get("STAGE14_EVENTS","/tmp/stage14-events/event_states.csv.gz"))
FEE_STRESS_BPS_PER_SIDE=(0,2,5)
RISK_FRACTION=.005
MAX_LEVERAGE=3.0
DAILY55="1D_channel_55_ema50_agrees_trail_3atr"
DAILY20="1D_channel_20_no_trend_filter_trail_3atr"
HOURLY="strong_momentum_6h__4h_adx_le20__3R__480min"

# Small preregistered set: the selected baseline plus economically motivated
# payout, holding and entry-quality changes. NO 2026/ETH tuning.
CASES=[
 ("baseline_3R_240m",3.0,240,"baseline"),
 ("earlier_target_2R",2.0,240,"baseline"),
 ("let_winners_run_4R",4.0,240,"baseline"),
 ("let_winners_run_5R",5.0,240,"baseline"),
 ("patient_3R_480m",3.0,480,"baseline"),
 ("patient_4R_480m",4.0,480,"baseline"),
 ("low_4h_volatility",3.0,240,"low_volatility"),
 ("very_quiet_1h",3.0,240,"very_quiet"),
 ("require_5m_participation",3.0,240,"5m_volume"),
 ("avoid_large_structural_stops",3.0,240,"small_risk"),
 ("4R_and_low_4h_volatility",4.0,240,"low_volatility"),
 ("4R_and_5m_participation",4.0,240,"5m_volume"),
]
def readcsv(p):return pd.read_csv(p)
def monthly_source(file,condition,key):
    x=readcsv(file)
    x=x[condition(x)].copy()
    if x.month_ist.duplicated().any():raise AssertionError(f"Duplicate source month {file}")
    d=x.set_index("month_ist")[key].astype(float)
    if any(m not in d.index for m in MONTHS):raise AssertionError(f"Missing month {file}")
    return d.reindex(MONTHS).to_numpy(float)
def saved_sleeves():
    swing=Path("analysis/institutional_discovery_stage17_swing_breakout/monthly_mark_to_market.csv")
    h1=Path("analysis/institutional_discovery_stage19_new_1h_patterns/monthly_results.csv")
    d55=monthly_source(swing,lambda z:z.model==DAILY55,"month_return_pct")
    d20=monthly_source(swing,lambda z:z.model==DAILY20,"month_return_pct")
    hourly=monthly_source(h1,lambda z:z.model==HOURLY,"modeled_return_pct")
    fixed_s18=Path("analysis/institutional_discovery_stage18_monthly_dual_strategy/selected_monthly_results.csv")
    ref18=monthly_source(fixed_s18,lambda z: z.stage17==DAILY55,"portfolio_pct")
    fixed_s20=Path("analysis/institutional_discovery_stage20_three_sleeve/selected_month_by_month.csv")
    ref20=monthly_source(fixed_s20,lambda z:z.stage19_model==HOURLY,"portfolio_month_pct")
    return dict(d55=d55,d20=d20,hourly=hourly,ref18=ref18,ref20=ref20)
def mask(e,kind):
    base=(e.h1_vr<=1.2)
    if kind=="baseline":return base
    if kind=="low_volatility":return base&(e.h4_atr_ratio<=1.0)
    if kind=="very_quiet":return base&(e.h1_vr<=0.9)
    if kind=="5m_volume":return base&(e.volume_ratio_5m>=1.)
    if kind=="small_risk":return base&(e.risk_pts<=700.)
    raise ValueError(kind)
def sim(e,f,name,reward,hold,flt):
    s15.REWARD_R=reward
    s15.HOLD_MINUTES=hold
    # Reuse Stage15's underlying original one-minute replay with causally
    # pre-entry known features; skipped events are replayed from full event set.
    rows,diag=s15.simulate_candidates(e,f,name,"weekly_minus_3R",mask(e,flt))
    if not rows:raise AssertionError(f"No trades for {name}")
    g=pd.DataFrame(rows).sort_values(["exit_unix","entry_unix"],kind="stable").reset_index(drop=True)
    g["exit_month_ist"]=pd.to_datetime(g.exit_unix,unit="s",utc=True).dt.tz_convert("Asia/Kolkata").dt.strftime("%Y-%m")
    g=g[g.exit_month_ist.isin(MONTHS)].copy()
    # True entry price is the candidate's NEXT one-minute open. Existing
    # net_R already includes taker fee 0.05% per side + GST and 5pts/side slip.
    op=f.open.to_numpy(float)
    g["entry_mid"]=op[g.k.to_numpy(int)]
    # 3x notional cap: risk fraction=min(0.5% NAV, leverage*stop distance/price).
    g["risk_fraction"]=np.minimum(RISK_FRACTION,MAX_LEVERAGE*g.initial_risk_pts/g.entry_mid)
    if (g.risk_fraction<=0).any():raise AssertionError("Invalid risk fraction")
    g["case"]=name
    return g,diag
def pf(x):
    v=np.asarray(x,dtype=float)
    wins=float(v[v>0].sum());loss=float(-v[v<0].sum())
    return round(wins/loss,6) if loss>0 else (float("inf") if wins>0 else None)
def replay_nav(g,extra_bps):
    # Extra adverse fill slippage assumed on EACH execution in addition to
    # the original 5 BTC points each side and full modeled taker fee+GST.
    extra=2.*(extra_bps/10000.)*g.entry_mid/g.initial_risk_pts
    r=(g.net_R-extra).to_numpy(float)
    fraction=g.risk_fraction.to_numpy(float)
    if np.any(1+fraction*r<=0):raise AssertionError("Account bankruptcy")
    months=g.exit_month_ist.to_numpy()
    # One position in this sleeve; cash NAV is booked on exit. Trades crossing
    # the calendar boundary are not independently MTM: portfolio NAV caveat.
    equity=100.;peak=100.;dd=0.;running=[];monthly=[]
    for m in MONTHS:
        which=np.where(months==m)[0]
        start=equity
        for j in which:
            equity*=1+fraction[j]*r[j]
            peak=max(peak,equity)
            dd=max(dd,100*(1-equity/peak))
            running.append((m,float(equity),float(r[j])))
        monthly.append(dict(month_ist=m,net_pct=100*(equity/start-1),
                            net_R=float(r[which].sum()),trades=len(which),
                            wins=int((r[which]>0).sum()),losses=int((r[which]<0).sum()),
                            nav_end=float(equity)))
    out=np.array([z["net_pct"] for z in monthly],dtype=float)
    train=out[:12]
    # Source is 2025-selected; do NOT use 2026 result to rank variants.
    t=g[g.exit_month_ist.str.startswith("2025")]
    return dict(monthly=monthly,net_2025=100*(np.prod(1+out[:12]/100)-1),
                net_2026JanOct=100*(np.prod(1+out[12:]/100)-1),
                net_22=equity-100,net_R_2025=float(t.net_R.sum()),
                positive_months=int((out>1e-9).sum()),loss_months=int((out<-1e-9).sum()),
                no_profit_months=int((abs(out)<=1e-9).sum()),
                positive_months_2025=int((train>1e-9).sum()),
                worst_2025=float(train.min()),drawdown_trade_close_pct=dd,
                trades=int(len(g)),trades_2025=int(len(t)),
                pf_net_R=pf(r),pf_2025_net_R=pf(r[g.exit_month_ist.str.startswith("2025").to_numpy()]),
                mean_net_R_per_trade=float(r.mean()))
def portfolio(component,other,aux):
    a=np.array([x["net_pct"] for x in component["monthly"]],dtype=float)
    return .75*a+.25*other if aux is None else .9*(.75*a+.25*other)+.1*aux
def returns(arr):
    x=np.asarray(arr,dtype=float)
    if np.any(x<=-100):raise AssertionError("Portfolio wipeout")
    c=np.cumprod(1+x/100)
    peaks=np.maximum.accumulate(np.r_[1,c])[1:]
    return dict(net_2025_pct=float(100*(np.prod(1+x[:12]/100)-1)),
                net_2026JanOct_pct=float(100*(np.prod(1+x[12:]/100)-1)),
                net_22_pct=float(100*(c[-1]-1)),
                positive_months=int((x>1e-9).sum()),
                negative_months=int((x<-1e-9).sum()),
                flat_months=int((abs(x)<=1e-9).sum()),
                worst_month_pct=float(x.min()),
                max_month_end_dd_pct=float(100*np.max(1-c/peaks)))
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    if not EVENTS.exists():raise FileNotFoundError(f"Authentic Stage14 source events not found at {EVENTS}")
    f,_,_,q=read_archive()
    source=readcsv(EVENTS)
    e=s15.selected_events(source)
    # Original selected subset and approved UTC->IST warmup consistency.
    sleeves=saved_sleeves()
    reports=[];monthly_rows=[];trades=[];chosen={};errors={}
    for name,reward,hold,flt in CASES:
        try:
            g,skipped=sim(e,f,name,reward,hold,flt)
            base=replay_nav(g,0);mid=replay_nav(g,2);stress=replay_nav(g,5)
            # Only BTC 2025 stressed risk-adjusted expectancy ranks candidates.
            risk=mid["drawdown_trade_close_pct"]
            good=mid["trades_2025"]>=22 and mid["net_2025"]>0
            score=mid["net_2025"]-.6*risk+.05*mid["positive_months_2025"] if good else -1e5+mid["net_2025"]
            tr=g.copy()
            tr["extra_slip_2bp_each_side_R"]=2.*.0002*tr.entry_mid/tr.initial_risk_pts
            trades.append(tr)
            for fee,b in [(0,base),(2,mid),(5,stress)]:
                for family in ("Stage18","Stage20"):
                    nav=portfolio(b,sleeves["d55"],None) if family=="Stage18" else portfolio(b,sleeves["d20"],sleeves["hourly"])
                    pp=returns(nav)
                    reports.append(dict(family=family,case=name,reward_R=reward,max_hold_minutes=hold,
                        filter=flt,extra_slip_bps_per_side=fee,score_BTC2025=float(score),
                        stage15_trades=int(b["trades"]),stage15_trades_2025=int(b["trades_2025"]),
                        stage15_PF_net_R=b["pf_net_R"],stage15_2025_PF_net_R=b["pf_2025_net_R"],
                        stage15_mean_net_R=b["mean_net_R_per_trade"],
                        stage15_2025_net_account_pct=b["net_2025"],
                        stage15_2026JanOct_net_account_pct=b["net_2026JanOct"],
                        stage15_22m_net_account_pct=b["net_22"],
                        stage15_trade_close_max_dd_pct=b["drawdown_trade_close_pct"],
                        **pp))
                    for m,rt in zip(MONTHS,nav):
                        monthly_rows.append(dict(family=family,case=name,month_ist=m,
                                                 extra_slip_bps_per_side=fee,
                                                 net_account_pct=float(rt)))
        except Exception as ex:
            errors[name]=str(ex)
            raise
    allp=pd.DataFrame(reports)
    month=pd.DataFrame(monthly_rows)
    alltr=pd.concat(trades,ignore_index=True)
    for family in ("Stage18","Stage20"):
        x=allp[(allp.family==family)&(allp.extra_slip_bps_per_side==2)].sort_values(
            ["score_BTC2025","stage15_trades_2025"],ascending=False)
        selected=str(x.iloc[0]["case"])
        chosen[family]=selected
        baseline=month[(month.family==family)&(month.case=="baseline_3R_240m")&
                       (month.extra_slip_bps_per_side==0)].set_index("month_ist").reindex(MONTHS).net_account_pct.to_numpy(float)
        source_ref=sleeves["ref18"] if family=="Stage18" else sleeves["ref20"]
        max_delta=float(np.max(np.abs(baseline-source_ref)))
        if max_delta>.035:raise AssertionError(
          f"{family} baseline vs preserved source monthly NAV diff {max_delta:.5f} pct: INVALID")
        print("BASELINE_RECONCILED",family,round(max_delta,8))
        print("SELECTED",family,selected)
        for variant in ("baseline_3R_240m",selected):
            for stress in (0,2,5):
                row=allp[(allp.family==family)&(allp.case==variant)&
                         (allp.extra_slip_bps_per_side==stress)].iloc[0]
                print("RESULT",row.to_json())
    allp.to_csv(OUT/"all_risk_aware_real_1m_candidate_results.csv",index=False)
    month.to_csv(OUT/"monthly_after_cost_portfolio_comparisons.csv",index=False)
    alltr.to_csv(OUT/"original_one_minute_trade_ledgers.csv.gz",compression="gzip",index=False)
    (OUT/"BTC_2025_selection.json").write_text(json.dumps(chosen,indent=2)+"\n")
    quality=dict(source_run_Stage14=44118024590,source_artifact="btc-stage14-monthly-regime-trades",
      source_1m_quality=q,replay="Stage15 replay_one 1m OHLC, original structural stops",
      cases=[dict(name=n,reward_R=r,max_hold=h,causal_filter=filt) for n,r,h,filt in CASES],
      selected_BTC2025_only=chosen,selection_method="2025 BTC training return after extra 2bp each side -0.6*trade-close DD +0.05*profitable train months, >=22 train trades and positive train return",
      warnings=[
        "Trade ENTRY filters and 2R/3R/4R/5R profit targets truly replayed from complete original entry events on native BTC 1-minute bars; 1m OHLC is NOT tick-by-tick.",
        "Full Stage18/20 portfolio still aggregates revised 1m Stage15 trade-month NAV with archived original Stage17/Stage19 monthly results, not a new simultaneous 3-sleeve order book and margin replay.",
        "The Stage15 account NAV is realized by EXIT month; if positions cross IST month-end this differs from exact marked-to-market NAV.",
        "Month-end portfolio max drawdown hides intramonth drawdown, funding and margin/liquidation; exact lot rounding and spreading omitted.",
        "2025 selection uses repeatedly researched history; 2026 already explored in old studies and is not pristine OOS.",
        "Full 2025-01 IST source warmup missing first 330 minutes; 2026-10-31 UTC day missing from original source. Report October 2026 coverage limitation.",
        "Original 1m fills assume 0.05% taker each side+18%GST and 5 BTC points each-side adverse slippage. +2bp/+5bp per side additional slippage is a cost sensitivity, not measured real bid-ask.",
        "ETH native strategy entry-event generation and identical risk rules NOT YET REPLAYED. Do NOT claim paired native ETH validation.",
        "Exact Stage18 selected daily55 and Stage20 fixed daily20 baseline comparisons are separate. Neither is guaranteed profitable in forward trading.",
      ])
    (OUT/"QUALITY_AND_LIMITS.json").write_text(json.dumps(quality,indent=2,default=str)+"\n")
    report=["# Genuine Stage18 and Stage20 primary-component entry/exit improvements on BTC 1m",
       "","Run is not complete without GitHub Actions success + log reconciliation.",
       "BTC-only strategy rule selection on earlier 2025, later 2026 checked unchanged.",
       "Stage15 real entry-event replay, not just monthly return weights.",
       "Portfolio combination reuses preserved Stage17/Stage19 sleeves; therefore this is an intermediate strategy improvement, NOT integrated portfolio execution or live-ready results.",
       "","## Selected variant per portfolio",json.dumps(chosen,indent=2),
       "","See all_risk_aware_real_1m_candidate_results.csv, monthly_after_cost_portfolio_comparisons.csv and original_one_minute_trade_ledgers.csv.gz.",
       "","## Critical limitations",*[("- "+a) for a in quality["warnings"]]]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")
    print("STAGE18_20_ACTUAL_SIGNAL_EXIT_REPLAY_COMPLETE",json.dumps(chosen))
if __name__=="__main__":main()
