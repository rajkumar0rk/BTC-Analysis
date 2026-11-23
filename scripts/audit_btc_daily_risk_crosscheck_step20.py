#!/usr/bin/env python3
"""Step20: independent 1m trade-level audit of Step18 overlooked Pareto models.

Ten predeclared B/A variants, exact 477 IST Mon-Fri days, all at 1x full
notional, frozen entry side/time and previously chosen month-conditioned
exit policy. All risk caps use only completed PRIOR bars and never widen SL.
All model-comparison results are HINDSIGHT because 2025/2026 seen before.
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd

import research_btc_every_weekday_reset_step1 as base
import research_btc_daily_monthly_exit_step13 as step13
import research_btc_daily_monthly_two_regime_step15 as step15
import research_btc_daily_exit_invalidation_step7 as early
import research_btc_daily_preentry_risk_step18 as prev

OUT=Path("analysis/btc_daily_risk_crosscheck_step20")
N=len(base.DAYS)
TRAIN=base.NTRAIN
MASKS={
  "with60":("with60",0,"fallback",.40),
  "highvol":("high_rvol5",1,"fallback",.25),
  "counter5":("counter5",0,"fallback",.25),
  "rangeedge":("edge_against",0,"fallback",.25),
  "tight60":("tight_range60",1,"both",.40),
  "wide60":("wide_range60",0,"fallback",.25),
  "highvol_event":("high_rvol5",1,"event",.30)
}
# Key, hindsight family, named stop rule parts.
MODELS={
  "B_baseline":("B",()),
  "B_with60_only":("B",("with60",)),
  "A_baseline":("A",()),
  "A_tight60_only":("A",("tight60",)),
  "B_with60_plus_highvol":("B",("with60","highvol")),
  "B_with60_plus_counter5":("B",("with60","counter5")),
  "B_with60_plus_rangeedge":("B",("with60","rangeedge")),
  "B_with60_plus_tight60":("B",("with60","tight60")),
  "B_with60_plus_wide60":("B",("with60","wide60")),
  "B_with60_plus_highvol_event":("B",("with60","highvol_event"))
}
PARAMS={
   "A":("mtd_not_positive","adverse_cut_0.08pct_after_10m",
        "peak_ge_plus1_and_giveback050","profit_close_at_0.1pct_after_10m"),
   "B":("mtd_not_positive","adverse_cut_0.08pct_after_10m",
        "mtd_at_least_plus1","profit_close_at_0.1pct_after_10m")
}
assert len(MODELS)==10 and N==477 and TRAIN==260

def build_capped(cfg,feat,side,mask,rule_ids):
    copy=cfg.copy()
    applied={}
    for name in rule_ids:
        kind,level,scope,cap=MASKS[name]
        test=prev.risk_trigger(kind,level,feat,side)
        if scope=="fallback":
            test=test&mask
        elif scope=="event":
            test=test&(~mask)
        before=copy[:,1].copy()
        copy[test,1]=np.minimum(copy[test,1],cap)
        applied[name]={
            "condition_days":int(test.sum()),
            "additional_shrunk_days":int(np.sum(copy[:,1]<before-1e-12))}
    assert np.all(copy[:,1]<=cfg[:,1]+1e-12)
    return copy,applied,int(np.sum(copy[:,1]<cfg[:,1]-1e-12))

def compute_raw(m,idx,side,cfg,policies):
    return early.replay_with_nextbar_exits(
       m.open.to_numpy(float),m.high.to_numpy(float),
       m.low.to_numpy(float),m.close.to_numpy(float),
       idx,side,cfg,policies,base.COST,base.SLIP
    )

def account_stats(path,monthly):
    p,fee,gross,why,t=path
    account=step15.score(path)
    assert len(p)==477 and int(np.sum(monthly.trade_days))==477
    monthly_pnl=monthly.net_compounded_pct.to_numpy()
    account["monthly_win_rate_pct"]=round(float(100*np.mean(monthly_pnl>0)),5)
    account["recomputed_profitable_months"]=int(np.sum(monthly_pnl>0))
    account["recomputed_2025_profitable_months"]=int(np.sum(monthly_pnl[:12]>0))
    account["recomputed_2026_profitable_months"]=int(np.sum(monthly_pnl[12:]>0))
    account["recomputed_worst_month_pct"]=round(float(np.min(monthly_pnl)),6)
    assert account["recomputed_profitable_months"]==account["win_months_all"]
    assert account["recomputed_2025_profitable_months"]==account["win_months_2025"]
    assert account["recomputed_2026_profitable_months"]==account["win_months_2026"]
    assert abs(account["recomputed_worst_month_pct"]-account["worst_month_pct"])<.000002
    return account

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    m,ctx,mask,fb,side,hour,idx,originalcfg=step13.create_path()
    policy,labels=early.build_exit_policies()
    ids={name:i for i,name in enumerate(labels)}
    baseline_raw=compute_raw(m,idx,side,originalcfg,policy)
    step13.check_parity(baseline_raw,ctx,fb)
    feat=prev.preentry_features(m,idx,side)
    baselineid=ids["profit_close_at_0.1pct_after_20m"]
    summary=[]
    risks={}
    all_months=[]
    for label,(fam,parts) in MODELS.items():
        cfg,applied,changed=build_capped(originalcfg,feat,side,mask,parts)
        raw=compute_raw(m,idx,side,cfg,policy) if changed else baseline_raw
        selection=step15.replay_one(raw,mask,baselineid,PARAMS[fam],ids)
        risks[label]=dict(parts=list(parts),applied=applied,stop_narrowed_trades=changed)
        for modeindex,mode in enumerate(base.MODES):
            path=step15.getout(raw,selection[0],modeindex)
            daily,monthly=step15.saved_ledger(
                path,selection[0],selection[1],selection[2],
                idx,hour,side,mask,mode)
            daily["stop_cap_rule"]=label
            daily["base_initial_stop_pct"]=originalcfg[:,1]
            daily["chosen_initial_stop_pct"]=cfg[:,1]
            daily["initial_stop_narrowed"]=(cfg[:,1]<originalcfg[:,1]-1e-12)
            assert len(daily)==477 and daily.day_ist.nunique()==477
            daily.to_csv(OUT/(label+"_"+mode+"_477_daily.csv"),index=False)
            monthly["model"]=label
            monthly["fee_schedule"]=mode
            monthly.to_csv(OUT/(label+"_"+mode+"_22_months.csv"),index=False)
            all_months.append(monthly)
            stat=account_stats(path,monthly)
            stat.update(model=label,fee_schedule=mode,
                family=fam,stop_rules="+".join(parts) if parts else "unchanged",
                stop_narrowed_trades=changed,
                2025_win_days=int(np.sum(path[0][:TRAIN]>0)) if False else 0)
            del stat["2025_win_days"]
            summary.append(stat)
            print("STEP20_MODEL "+json.dumps({
                "model":label,"fee":mode,"months":stat["win_months_all"],
                "2025_months":stat["win_months_2025"],
                "2026_months":stat["win_months_2026"],
                "net":stat["net_total_pct"],"dd":stat["max_closed_dd_pct"],
                "win_days":stat["profitable_days"],
                "worst_month_pct":stat["worst_month_pct"],
                "worse_day_pct":stat["worst_day_pct"],
                "stop_narrowed":changed}),flush=True)
    frame=pd.DataFrame(summary)
    monthmatrix=pd.concat(all_months,ignore_index=True)
    if len(frame)!=20 or len(monthmatrix)!=10*2*22 or not frame.trades.eq(477).all():
        raise AssertionError("Missing 477-day execution or 22-month comparison")
    frame.to_csv(OUT/"ten_frozen_models_two_fee_scenarios.csv",index=False)
    monthmatrix.to_csv(OUT/"all_22_monthly_returns_by_candidate_and_fee.csv",index=False)

    def get(label,fee):
        return frame[(frame.model==label)&(frame.fee_schedule==fee)].iloc[0]
    for label,expected_net,expected_months,expected_dd in (
        ("A_baseline",24.648136,20,2.715507),
        ("B_baseline",22.480405,21,2.715507),
        ("B_with60_only",24.421194,21,2.617670),
        ("A_tight60_only",25.973352,21,2.715507)
    ):
        val=get(label,"scalper_offer")
        if val.win_months_all!=expected_months or abs(val.net_total_pct-expected_net)>.00011 or abs(val.max_closed_dd_pct-expected_dd)>.00011:
            raise AssertionError("Source Step15/18 results mismatch "+label+": "+str(val.to_dict()))
    print("STEP20_VERIFIED_PRIOR_ARTIFACT_PARITY",flush=True)
    offer=frame[frame.fee_schedule=="scalper_offer"]
    positives=offer[offer.win_months_all==22]
    more=offer.sort_values(["win_months_all","net_total_pct","max_closed_dd_pct"],ascending=[False,False,True])
    result=dict(
      study="Step20: Independently reproduce overlooked historical BTC volatility-stop improvement and audit predeclared conditions",
      source="Step18 previously completed 540-variant risk grid, Step15 previous fully researched A/B families",
      trade_contract="477 actual 1x notional full Mon-Fri BTCUSD positions per model, no skipping and no re-sizing",
      retrospective_not_independent_forward=True,
      candidate_count=len(MODELS),
      both_cost_scenarios=20,
      all_22_positive_month_candidates_RESEARCH_ONLY=int(len(positives)),
      highest_month_positive_retrospective=more.iloc[0].to_dict(),
      source_parity_confirmed=True,
      risk_rules=risks,
      standard_vs_scalper={
         name:{
           fee: {k:get(name,fee)[k] for k in (
             "win_months_all","net_total_pct","max_closed_dd_pct","profitable_days","worst_month_pct"
           )} for fee in base.MODES
         } for name in MODELS
      },
      limits=[
        "All 2025 and 2026 dates repeatedly mined; not genuine independent holdout",
        "B/A base model policy identities were chosen retrospectively using 2026 outcomes",
        "Ten combined stop variants not tested forward; best full-history model is overfit-prone",
        "Real historical scalper opt-in, fills, bid-ask, funding, market depth, latency, liquidation unverified"
      ])
    (OUT/"summary.json").write_text(json.dumps(result,indent=2)+"\n")
    readme=[
       "# BTCUSD Step20 — Verified risk-rule monthly audit",
       "",
       "Every candidate entered exactly once on all 477 complete IST Monday-Friday dates, 1x account notional and frozen Step11 sides. Original 1m stop-first, trailing next-bar and early exits unchanged. Any special stop is based only on completed pre-entry 1m candles.",
       "",
       "## Historical candidate comparison under hypothetical Scalper",
       more[["model","win_months_all","win_months_2025","win_months_2026",
             "net_total_pct","profitable_days","max_closed_dd_pct",
             "worst_month_pct","worst_day_pct","stop_narrowed_trades"]].to_markdown(index=False),
       "",
       "## 22 monthly results by candidate under assumed Scalper",
       monthmatrix[monthmatrix.fee_schedule=="scalper_offer"][[
           "model","month_ist","trade_days","winning_days","net_compounded_pct"
       ]].to_markdown(index=False),
       "",
       "## Source parity",
       "Verified full 1m replay against prior Step15 A/B and Step18 B_with60/A_tight60 outputs. Counts independently recomputed from 477 daily trade returns.",
       "",
       "## Cautions",
       "Historical A/B candidate families and Step18 stop trigger improvements were identified using previously researched 2026 data, so none establishes a live trading edge. Historical scalper fee waiver and execution cannot be independently authenticated from OHLCV."
    ]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(readme)+"\n")
    print("STEP20_COMPLETE "+json.dumps({
       "models":10,"all22":len(positives),
       "best":more.iloc[0][["model","win_months_all","net_total_pct","max_closed_dd_pct"]].to_dict()
    },sort_keys=True),flush=True)

if __name__=="__main__":
    main()
