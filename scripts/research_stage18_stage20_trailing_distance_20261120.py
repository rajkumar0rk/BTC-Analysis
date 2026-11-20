#!/usr/bin/env python3
"""Actual BTC 1-minute trailing-stop vs trailing-distance execution research.

The ORIGINAL Stage14 entry events and Stage15 structural risk model are reused.
The source Stage15 engine prevents overlap and enforces the original weekly -3R
guard. Profit exits and trailing stop touches replay genuine one-minute OHLC:
stop-first, conservative gap-through-open, and a stop update only *after* the
current completed one-minute bar, effective from the following minute.
2025 selects a candidate; 2026 is checked but cannot be used for optimization.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from numba import njit
import research_july_drawdown_stage15 as stage
import research_stage18_stage20_signal_exit_improvement_20261120 as prior
from research_every_candle_200 import read_archive, FEE, SLIPPAGE
from research_structure_rr_stage11 import replay_one as original_replay

OUT=Path("analysis/stage18_stage20_trailing_distance_20261120")
MONTHS=prior.MONTHS

# Modes: 0 fixed stop and TP; 1 fixed-BTC-point trailing stop from first
# completed minute; 2 activate at +N*initial-risk, then trail the favorable
# extreme at a distance of M*initial-risk; 3 activate at +N*initial-risk then
# trail a fixed BTC-price-point distance. Initial risk stop applies throughout.
# NO mode changes an entry filter or ignores a stopped-out trade.
# Rows: label, mode, activation_R, gap, target_R (20R ≈ effectively no TP),
# max_hold_minutes. Predeclared small, interpretable family, not brute search.
TESTS=[
 ("original_3R",0,0.,0.,3.,240),
 ("original_5R",0,0.,0.,5.,240),
 ("immediate_stop_200pt",1,0.,200.,10.,240),
 ("immediate_stop_400pt",1,0.,400.,10.,240),
 ("immediate_stop_600pt",1,0.,600.,10.,240),
 ("distance_200pt_after1R",3,1.,200.,10.,240),
 ("distance_400pt_after2R",3,2.,400.,10.,240),
 ("distance_600pt_after2R",3,2.,600.,10.,240),
 ("distance_800pt_after3R",3,3.,800.,10.,240),
 ("distance_1R_after1R",2,1.,1.,10.,240),
 ("distance_1R_after2R",2,2.,1.,10.,240),
 ("distance_2R_after2R",2,2.,2.,10.,240),
 ("distance_2R_after3R",2,3.,2.,10.,240),
 ("distance_3R_after3R",2,3.,3.,10.,240),
 ("5R_cap_distance_1R_after2R",2,2.,1.,5.,240),
 ("5R_cap_distance_2R_after2R",2,2.,2.,5.,240),
 ("8R_cap_distance_2R_after2R",2,2.,2.,8.,240),
 ("480m_distance_2R_after2R",2,2.,2.,10.,480),
 ("480m_distance_600pt_after2R",3,2.,600.,10.,480),
]

@njit(cache=True)
def replay(O,H,L,C,k,side,original_stop,RR,hold,mode,activate,gap):
    entry=float(O[k])
    risk=side*(entry-original_stop)
    stop=original_stop
    target=entry+side*risk*RR
    # Candidate favorable extreme (long high / short low) is not executable
    # intrabar data. It becomes available only after a completed 1m candle.
    best=entry
    for j in range(k,k+hold):
        # Stop-first on ambiguous same-candle TP/SL. Gap-through-stop at OPEN
        # instead of generously assuming original stop price.
        stop_hit=(L[j]<=stop) if side==1 else (H[j]>=stop)
        take_hit=(H[j]>=target) if side==1 else (L[j]<=target)
        if stop_hit:
            exit_mid=min(O[j],stop) if side==1 else max(O[j],stop)
            why=0
            break
        if take_hit:
            exit_mid=target
            why=1
            break
        # Update only at the END of this 1-minute bar, applying from j+1.
        favorable=H[j] if side==1 else L[j]
        if side==1:
            if favorable>best:best=favorable
        else:
            if favorable<best:best=favorable
        favorable_R=side*(best-entry)/risk
        if mode>0 and favorable_R+1e-12>=activate:
            trail_distance=gap*risk if mode==2 else gap
            proposed=best-side*trail_distance
            # Never relax the stop and preserve the original stop until the
            # chosen trail is genuinely closer.
            if side==1:
                if proposed>stop:stop=proposed
            else:
                if proposed<stop:stop=proposed
    else:
        j=k+hold-1
        exit_mid=C[j]
        why=2
    fill_in=entry+side*SLIPPAGE
    fill_out=exit_mid-side*SLIPPAGE
    gross=side*(exit_mid-entry)
    net=side*(fill_out-fill_in)-FEE*(fill_in+fill_out)
    # Offer hypothetical shown only as legacy replay-compatible field; all
    # comparisons below USE STANDARD TAKER fees, not this offer.
    offer=side*(fill_out-fill_in)-FEE*fill_in-(0. if j-k+1<=30 else FEE*fill_out)
    return j,why,gross,net,offer,net/risk,risk

def execute_case(events,f,case):
    label,mode,activate,gap,target,hold=case
    stage.REWARD_R=target
    stage.HOLD_MINUTES=hold
    if mode==0:
        stage.replay_one=original_replay
    else:
        stage.replay_one=lambda O,H,L,C,k,side,stop,rr,h: replay(
            O,H,L,C,k,side,stop,rr,h,mode,activate,gap)
    rows,skipped=stage.simulate_candidates(
        events,f,label,"weekly_minus_3R",prior.mask(events,"baseline"))
    if not rows:raise AssertionError(f"No trades for {label}")
    ledger=pd.DataFrame(rows).sort_values(["exit_unix","entry_unix"],kind="stable")
    ledger["exit_month_ist"]=pd.to_datetime(ledger.exit_unix,unit="s",utc=True).dt.tz_convert("Asia/Kolkata").dt.strftime("%Y-%m")
    ledger=ledger[ledger.exit_month_ist.isin(MONTHS)].copy()
    ledger["entry_mid"]=f.open.to_numpy(float)[ledger.k.to_numpy(int)]
    # Cap modeled notional at 3x account NAV. All fractional position sizing
    # and contract rounding assumptions remain important validation caveats.
    ledger["risk_fraction"]=np.minimum(
        prior.RISK_FRACTION,prior.MAX_LEVERAGE*ledger.initial_risk_pts/ledger.entry_mid)
    ledger["exit_type"]=np.where(ledger.reason=="stop",
       "initial_or_trailing_stop","target_or_timeout")
    ledger["trailing_mode"]=mode
    ledger["activation_R"]=activate
    ledger["distance"]=gap
    ledger["reward_cap_R"]=target
    ledger["hold_cap_min"]=hold
    return ledger,skipped

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    f,_,_,dataq=read_archive()
    e=stage.selected_events(pd.read_csv(prior.EVENTS))
    archived=prior.saved_sleeves()
    full=[];monthly=[];trades=[];selected={}
    for case in TESTS:
        name,mode,activation,distance,rr,hold=case
        ledger,skipped=execute_case(e,f,case)
        trades.append(ledger)
        for extra in (0,2,5):
            res=prior.replay_nav(ledger,extra)
            for family in ("Stage18","Stage20"):
                nav=prior.portfolio(res,archived["d55"],None) if family=="Stage18" else prior.portfolio(res,archived["d20"],archived["hourly"])
                p=prior.returns(nav)
                full.append(dict(family=family,variant=name,mode=mode,
                    trail_activation_R=activation,trailing_distance=distance,
                    reward_cap_R=rr,hold_cap_minutes=hold,
                    extra_adverse_slip_bps_each_side=extra,
                    core_trades=res["trades"],core_2025_trades=res["trades_2025"],
                    core_pf_netR=res["pf_net_R"],core_2025_pf_netR=res["pf_2025_net_R"],
                    core_avg_netR=res["mean_net_R_per_trade"],
                    core_2025_net_pct=res["net_2025"],
                    core_2026_net_pct=res["net_2026JanOct"],
                    **p))
                monthly.extend([dict(family=family,variant=name,
                    extra_adverse_slip_bps_each_side=extra,month_ist=m,
                    portfolio_net_pct=float(n)) for m,n in zip(MONTHS,nav)])
    frame=pd.DataFrame(full)
    mframe=pd.DataFrame(monthly)
    for family in ("Stage18","Stage20"):
        # Historical original must match the independently archived baseline.
        b=mframe[(mframe.family==family)&(mframe.variant=="original_3R")&
                 (mframe.extra_adverse_slip_bps_each_side==0)].set_index("month_ist").reindex(MONTHS).portfolio_net_pct.to_numpy()
        ref=archived["ref18"] if family=="Stage18" else archived["ref20"]
        diff=float(np.max(np.abs(b-ref)))
        if diff>.04:raise AssertionError(f"Original {family} no longer reconciles: {diff:.6f}")
        # Candidate selection uses BTC 2025 only, stress +2bp each side;
        # exclude candidate with <25 training trades and negative 2025 return.
        candidates=frame[(frame.family==family)&
                         (frame.extra_adverse_slip_bps_each_side==2)&
                         (frame.core_2025_trades>=25)&
                         (frame.net_2025_pct>0)].copy()
        candidates["selection_BTC2025"]=candidates.net_2025_pct-.75*candidates.max_month_end_dd_pct
        candidates=candidates.sort_values(["selection_BTC2025","core_2025_trades"],
                                          ascending=[False,False],kind="stable")
        pick=str(candidates.iloc[0].variant) if len(candidates) else "original_3R"
        selected[family]=pick
        print("TRAIN_2025_RANKED",family,candidates[[
            "variant","selection_BTC2025","net_2025_pct","core_2025_trades",
            "max_month_end_dd_pct"]].head(12).to_json(orient="records"))
        print("BASELINE_RECONCILED",family,round(diff,8))
        print("BTC2025_SELECTED",family,pick)
        # Print core original, 5R, frozen winner and highest BTC-2025 trailing
        # challenger; return all variants to artifact for independent review.
        trail_candidates=candidates[candidates["mode"]!=0]
        toptrail=str(trail_candidates.iloc[0].variant) if len(trail_candidates) else "none"
        print("BEST_TRAILING_CANDIDATE_2025",family,toptrail)
        for name in dict.fromkeys(["original_3R","original_5R",toptrail,pick]):
            if name=="none":continue
            for extra in (0,2,5):
                v=frame[(frame.family==family)&(frame.variant==name)&
                        (frame.extra_adverse_slip_bps_each_side==extra)].iloc[0]
                print("VERIFIED_RESULT",v.to_json())
    frame.to_csv(OUT/"all_trailing_stop_distance_results.csv",index=False)
    mframe.to_csv(OUT/"monthly_22mo_account_return_comparison.csv",index=False)
    pd.concat(trades,ignore_index=True).to_csv(
        OUT/"all_trailing_trade_ledgers.csv.gz",index=False,compression="gzip")
    (OUT/"btc2025_selection.json").write_text(json.dumps(selected,indent=2)+"\n")
    (OUT/"quality_and_execution_limits.json").write_text(json.dumps(dict(
      source="Original Stage14 actual events from GitHub Actions 44118024590; genuine Delta India BTCUSD 1m OHLC",
      data_quality=dataq,source_event_count=len(e),all_cases=TESTS,
      execution="1m stop-first replay; check stop/TP first, then update max favorable excursion for NEXT 1m bar; gap stop at worst of original stop/open",
      compare_to_original="original_3R and original_5R immutable source logic; same entry and structural initial SL, weekly loss gate",
      costs="Standard taker each side 0.05%+GST18%; base 5 BTC points per side + extra pessimistic 0/2/5bps each side",
      critical_limits=[
        "Stage15 core entries/exits were replayed for BTC only. Stage17 and Stage19 remain archived month-summary sleeves, not integrated 1m concurrent portfolio fills.",
        "Month-of-exit core NAV not true marked-to-market for across-month open trades.",
        "Missing source 2026-10-31 UTC and 2025-01-01 00:00–05:29 IST; original historical history is research-exposed.",
        "No exact funding, real spread/order-book impact, minimum lot, intraminute tick order, intrabar liquidation or collateral/margin feasibility.",
        "No native ETH 1m validation of new trailing stop and trailing distance. These results do not prove forward profitability.",
        "Trailing trigger derives from favorable completed 1m OHLC extreme, not a tick-by-tick stop amendment or verified exchange order-fill."
      ],selected_using_BTC_2025_only=selected),indent=2,default=str)+"\n")
    print("TRAILING_DISTANCE_STOP_BTC1M_COMPLETE",json.dumps(selected))
if __name__=="__main__": main()
