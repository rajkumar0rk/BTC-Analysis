#!/usr/bin/env python3
"""Improve Stage18/Stage20 monthly expectancy by changing BTC entry rules/exits.

Runs original Stage14 candidate events on actual 1m BTCUSD candles, never by
removing historically losing trades or selecting lucky calendar months.
2025-only cost-stressed model selection, frozen chronological 2026 recheck.
Stage17/19 component NAVs are archived: combined portfolio remains a monthly
blend rather than native shared-margin multi-sleeve execution.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from research_every_candle_200 import read_archive
import research_july_drawdown_stage15 as stage
import research_stage18_stage20_signal_exit_improvement_20261120 as prior
import research_stage18_stage20_trailing_distance_20261120 as trailing
from research_structure_rr_stage11 import replay_one as original_replay

OUT=Path("analysis/stage18_stage20_monthly_consistency_20261120")
MONTHS=prior.MONTHS
FAMILY="S13_pullback_near_half_atr"
# All filters derive from completed 1h/4h bars or previous COMPLETE month,
# already known at time of entry. New variants change genuine eligibility.
# tuple: name, previous month efficiency max, 4H ADX max, 1H volume ratio max,
#         pre-entry additional filter, target R, hold min, trailing 800pt after 3R.
CASES=[
 ("reference_3R",.15,18.,1.2,"all",3.,240,False),
 ("reference_5R",.15,18.,1.2,"all",5.,240,False),
 ("5R_quiet_1h_0p8",.15,18.,.8,"all",5.,240,False),
 ("5R_1h_volume_to1p5",.15,18.,1.5,"all",5.,240,False),
 ("5R_regime_20pct_adx20",.20,20.,1.2,"all",5.,240,False),
 ("5R_regime_25pct_adx22",.25,22.,1.2,"all",5.,240,False),
 ("5R_regime_30pct_adx25",.30,25.,1.2,"all",5.,240,False),
 ("5R_regime_15pct_adx25",.15,25.,1.2,"all",5.,240,False),
 ("5R_regime_25pct_adx18",.25,18.,1.2,"all",5.,240,False),
 ("5R_quiet_4h_efficiency",.15,18.,1.2,"4h_eff_le0p25",5.,240,False),
 ("5R_not_stretched_4h_atr",.15,18.,1.2,"4h_atr_le1p0",5.,240,False),
 ("5R_high_vol_5m",.15,18.,1.2,"volume_5m_ge1p2",5.,240,False),
 ("5R_risk_200_700",.15,18.,1.2,"risk_200_700",5.,240,False),
 ("5R_trade_with_4h_drift",.15,18.,1.2,"4h_drift_align",5.,240,False),
 ("5R_counter_4h_drift",.15,18.,1.2,"4h_drift_opposite",5.,240,False),
 ("5R_regime20_1h_quiet0p8",.20,20.,.8,"all",5.,240,False),
 ("5R_regime25_5m_volume",.25,22.,1.2,"volume_5m_ge1p2",5.,240,False),
 ("4R_regime20_adx20",.20,20.,1.2,"all",4.,240,False),
 ("3R_regime25_adx22",.25,22.,1.2,"all",3.,240,False),
 ("5R_regime20_480m",.20,20.,1.2,"all",5.,480,False),
 ("trail800_after3R_original",.15,18.,1.2,"all",10.,240,True),
 ("trail800_after3R_regime20",.20,20.,1.2,"all",10.,240,True),
 ("trail800_after3R_regime25",.25,22.,1.2,"all",10.,240,True),
]
EXTRA_SLIP_BPS=(0,2,5)
def prospective_filter(e,kind):
    if kind=="all":return np.ones(len(e),dtype=bool)
    if kind=="4h_eff_le0p25":return (e.h4_eff8<=.25).to_numpy(bool)
    if kind=="4h_atr_le1p0":return (e.h4_atr_ratio<=1.0).to_numpy(bool)
    if kind=="volume_5m_ge1p2":return (e.volume_ratio_5m>=1.2).to_numpy(bool)
    if kind=="risk_200_700":return ((e.risk_pts>=200)&(e.risk_pts<=700)).to_numpy(bool)
    if kind=="4h_drift_align":return ((e.h4_directional_drift8*e.side)>=0).to_numpy(bool)
    if kind=="4h_drift_opposite":return ((e.h4_directional_drift8*e.side)<0).to_numpy(bool)
    raise ValueError(kind)
def run_case(raw,f,c):
    name,eff,adx,h1vol,extra,rr,hold,use_trail=c
    eligible=raw.loc[(raw.family==FAMILY)&
                     (raw.previous_month_eff<=eff)&
                     (raw.h4_adx<=adx)].copy()
    if eligible.empty:raise AssertionError(f"{name}: zero entry events")
    keep=(eligible.h1_vr<=h1vol).to_numpy(bool)&prospective_filter(eligible,extra)
    stage.REWARD_R=rr
    stage.HOLD_MINUTES=hold
    if use_trail:
        stage.replay_one=lambda O,H,L,C,k,side,stop,tar,h: trailing.replay(
            O,H,L,C,k,side,stop,tar,h,3,3.,800.)
    else:stage.replay_one=original_replay
    rows,skipped=stage.simulate_candidates(
        eligible,f,name,"weekly_minus_3R",keep)
    if not rows:raise AssertionError(f"{name}: zero executed trades")
    g=pd.DataFrame(rows).sort_values(["exit_unix","entry_unix"],kind="stable")
    g["exit_month_ist"]=pd.to_datetime(g.exit_unix,unit="s",utc=True).dt.tz_convert("Asia/Kolkata").dt.strftime("%Y-%m")
    g=g[g.exit_month_ist.isin(MONTHS)].copy()
    if not len(g):raise AssertionError("No recorded 22m trades")
    g["entry_mid"]=f.open.to_numpy(float)[g.k.to_numpy(int)]
    g["risk_fraction"]=np.minimum(
      prior.RISK_FRACTION,prior.MAX_LEVERAGE*g.initial_risk_pts/g.entry_mid)
    if (g.risk_fraction<=0).any():raise AssertionError("Invalid account risk")
    g["variant"]=name
    g["reward_target_R"]=rr
    g["holding_cap_minutes"]=hold
    g["use_activated_800pt_trailer"]=use_trail
    return g,len(eligible),int(keep.sum()),skipped
def period_metrics(returns):
    v=np.asarray(returns,dtype=float)
    if np.any(~np.isfinite(v)) or np.any(v<=-100):
        raise AssertionError("Invalid account monthly NAV")
    equity=np.cumprod(1+v/100)
    peak=np.maximum.accumulate(np.r_[1.,equity])[1:]
    return dict(ret_pct=float((equity[-1]-1)*100),
        winners=int((v>1e-8).sum()),losers=int((v<-1e-8).sum()),
        flats=int((abs(v)<=1e-8).sum()),
        worst_pct=float(v.min()),mean_pct=float(v.mean()),
        max_monthend_dd_pct=float(100*np.max(1-equity/peak)))
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    f,_,_,quality=read_archive()
    source=pd.read_csv(prior.EVENTS)
    archived=prior.saved_sleeves()
    records=[];all_months=[];trades=[];picks={}
    for case in CASES:
        name=case[0]
        g,eligible,signal_count,skipped=run_case(source,f,case)
        trades.append(g)
        for extra_slip_bps in EXTRA_SLIP_BPS:
            core=prior.replay_nav(g,extra_slip_bps)
            for family in ("Stage18","Stage20"):
                x=prior.portfolio(core,archived["d55"],None) if family=="Stage18" else prior.portfolio(core,archived["d20"],archived["hourly"])
                train=period_metrics(x[:12])
                check=period_metrics(x[12:])
                whole=period_metrics(x)
                records.append(dict(family=family,variant=name,
                    original_event_candidates=eligible,eligible_preentry_signals=signal_count,
                    executed_trades=core["trades"],executed_trades_2025=core["trades_2025"],
                    reward_target_R=case[5],time_cap_minutes=case[6],
                    activated_800pt_trailing=case[7],
                    extra_adverse_slip_bps_per_side=extra_slip_bps,
                    core_pf_netR=core["pf_net_R"],core_mean_netR=core["mean_net_R_per_trade"],
                    btc2025_compounded_pct=train["ret_pct"],
                    btc2025_profitable_months=train["winners"],btc2025_losing_months=train["losers"],
                    btc2025_flat_months=train["flats"],btc2025_worst_month_pct=train["worst_pct"],
                    btc2025_max_monthend_dd_pct=train["max_monthend_dd_pct"],
                    btc2026_JanOct_compounded_pct=check["ret_pct"],
                    btc2026_profitable_months=check["winners"],btc2026_losing_months=check["losers"],
                    btc2026_flat_months=check["flats"],
                    btc22_compounded_pct=whole["ret_pct"],
                    btc22_profitable_months=whole["winners"],btc22_losing_months=whole["losers"],
                    btc22_flat_months=whole["flats"],
                    btc22_worst_month_pct=whole["worst_pct"],
                    btc22_max_monthend_dd_pct=whole["max_monthend_dd_pct"]))
                all_months.extend(dict(family=family,variant=name,
                    extra_adverse_slip_bps_per_side=extra_slip_bps,
                    month_ist=month,net_month_pct=float(y)) for month,y in zip(MONTHS,x))
    rd=pd.DataFrame.from_records(records)
    mo=pd.DataFrame.from_records(all_months)
    for family in ("Stage18","Stage20"):
        original=mo[(mo.family==family)&(mo.variant=="reference_3R")&
            (mo.extra_adverse_slip_bps_per_side==0)].set_index("month_ist").reindex(MONTHS).net_month_pct.to_numpy()
        archived_baseline=archived["ref18"] if family=="Stage18" else archived["ref20"]
        maxdiff=float(np.max(np.abs(original-archived_baseline)))
        if maxdiff>.04:raise AssertionError(f"{family} original 3R baseline discrepancy {maxdiff}")
        fixed5=rd[(rd.family==family)&(rd.variant=="reference_5R")&
                  (rd.extra_adverse_slip_bps_per_side==0)].iloc[0]
        expected=12.01632563 if family=="Stage18" else 9.5920516698
        if abs(fixed5.btc22_compounded_pct-expected)>.07:
            raise AssertionError(f"{family} reference 5R no longer reconciles: {fixed5.btc22_compounded_pct}")
        train=rd[(rd.family==family)&(rd.extra_adverse_slip_bps_per_side==2)].copy()
        # Account-level positive expectancy and sufficient sample are mandatory.
        train=train[(train.executed_trades_2025>=30)&(train.btc2025_compounded_pct>0)]
        # 2025-ONLY score: after-cost NAV, monthly consistency, downside.
        # All results at 2026 and later are entirely excluded from selection.
        train["train_score"]=(
           train.btc2025_compounded_pct+
           .55*train.btc2025_profitable_months-
           .65*train.btc2025_max_monthend_dd_pct-
           .25*np.maximum(0,-train.btc2025_worst_month_pct))
        train=train.sort_values(
           ["train_score","btc2025_compounded_pct","executed_trades_2025"],
           ascending=[False,False,False],kind="stable")
        if train.empty:raise AssertionError("No valid BTC 2025 positive after-cost candidates")
        pick=str(train.iloc[0].variant)
        picks[family]=pick
        print("BASELINE_RECONCILED",family,maxdiff)
        print("BTC2025_RANKING",family,train[["variant","train_score",
           "btc2025_compounded_pct","btc2025_profitable_months",
           "btc2025_max_monthend_dd_pct","executed_trades_2025"]].head(12).to_json(orient="records"))
        print("BTC2025_SELECTED",family,pick)
        # Report selected even if deteriorated on previously-exposed BTC 2026.
        for name in dict.fromkeys(["reference_3R","reference_5R",
                     "trail800_after3R_original",pick]):
            for extra in EXTRA_SLIP_BPS:
                row=rd[(rd.family==family)&(rd.variant==name)&
                       (rd.extra_adverse_slip_bps_per_side==extra)].iloc[0]
                print("MONTHLY_IMPROVEMENT_RESULT",row.to_json())
        # Eligibility: comparison over same 22 calendar months; NOT count flat
        # or no-trade months as winning and don't pretend positive months imply net gain.
        orig=rd[(rd.family==family)&(rd.variant=="reference_5R")&
                (rd.extra_adverse_slip_bps_per_side==0)].iloc[0]
        new=rd[(rd.family==family)&(rd.variant==pick)&
                (rd.extra_adverse_slip_bps_per_side==0)].iloc[0]
        print("FROZEN_2026_CHECK",json.dumps(dict(family=family,
          selected=pick,year2025_model_selection_ONLY=True,
          original_full22_return_pct=float(orig.btc22_compounded_pct),
          selected_full22_return_pct=float(new.btc22_compounded_pct),
          original_winning_months=int(orig.btc22_profitable_months),
          selected_winning_months=int(new.btc22_profitable_months),
          original_2026_return_pct=float(orig.btc2026_JanOct_compounded_pct),
          selected_2026_return_pct=float(new.btc2026_JanOct_compounded_pct),
          improved_month_count_and_return=bool(
             new.btc22_compounded_pct>orig.btc22_compounded_pct and
             new.btc22_profitable_months>orig.btc22_profitable_months))))
    rd.to_csv(OUT/"all_variants_22months.csv",index=False)
    mo.to_csv(OUT/"month_by_month_all_variants.csv",index=False)
    pd.concat(trades,ignore_index=True).to_csv(OUT/"btc_1m_trade_ledgers.csv.gz",index=False,compression="gzip")
    (OUT/"selected_BTC2025.json").write_text(json.dumps(picks,indent=2)+"\n")
    limitations=dict(
      original_stage14_event_actions=44118024590,
      source_1m_quality=quality,
      candidates=[dict(variant=c[0],prior_efficiency_max=c[1],h4_adx_max=c[2],
                       h1_volume_max=c[3],other_filter=c[4],target_R=c[5],
                       hold_max_minutes=c[6],activated_800pt_trailing=c[7]) for c in CASES],
      selection="BTC 2025 ONLY; select +2bps each side stressed after-cost return +0.55*profitable months -0.65*2025 max month-end DD -0.25*abs(worst losing month), >=30 actual trades during 2025, positive 2025 return",
      fees="Base 0.05% taker per side +18%GST on fees +5 BTC points adverse slippage/side; extra 0,2,5bps EACH SIDE stressed",
      assumptions=[
        "BTC 1m stop-first native trade replay only for 1H/15M Stage15 primary; Stage17/19 secondary sleeves remain archived monthly returns (NOT integrated simultaneous multistrategy execution).",
        "Actual historical 1-minute OHLC cannot prove fill ordering within candle or execution at L1 bid/ask quote.",
        "Account core NAV uses exit-month trade realization; not exact month-end mark-to-market on positions held across boundary; month-end drawdown can understate peak-to-trough.",
        "Source 2025 Jan first 330min IST incomplete; 2026 Oct UTC day missing; source covers a time window with gaps, not an uninterrupted complete 22-month feed.",
        "Funding, interest, actual spread, margin, liquidation, shared collateral, lot rounding, portfolio rebalance fees unmodeled.",
        "Full 2026 already researched in prior work, NOT pristine unseen validation, no native ETH test of this new frozen rule; strong in-sample improvement is NOT proof.",
        "Additional candidate variants incur multiple-testing/overfitting risk. Never deploy with real money from this evidence."
      ],
      no_live_orders=True,unchanged_main_branch=True)
    (OUT/"limitations.json").write_text(json.dumps(limitations,indent=2,default=str)+"\n")
    print("STAGE18_20_MONTHLY_EDGE_ACTUAL1M_COMPLETE",json.dumps(picks))
if __name__=="__main__":main()
