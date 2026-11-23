#!/usr/bin/env python3
"""Frozen November 2026 audit: Step7 after-bar profit closes versus Step6 base.

No Nov reoptimization. Uses already validated zero online Step6 direction flips
on the Nov2-Nov20 weekdays, checked against old precise result. Mandatory
1 trade EVERY IST weekday; any profit cut only at NEXT 1m OPEN.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import research_btc_every_weekday_reset_step1 as base
import research_btc_daily_causal_regime_step5 as regime
import research_btc_daily_exit_invalidation_step7 as step7
import audit_btc_daily_fallback_regime_november_2026 as nov

OUT=Path("analysis/btc_daily_exit_invalidation_step7/november_check")
CASES={
  "step6_unchanged":("baseline_30min","baseline_30min"),
  "hindsight_291_winners":("baseline_30min","profit_close_at_0.1pct_after_20m"),
  "hindsight_286_higher_profit":("baseline_30min","profit_close_at_0.15pct_after_20m"),
  "rejected_2025_316_wins":("profit_close_at_0.1pct_after_10m","profit_close_at_0.1pct_after_10m"),
}
def measures(x):
    eq=np.cumprod(1+x)
    peak=np.maximum.accumulate(np.r_[1.,eq])[1:]
    return dict(weekday_trades=len(x),
       profitable_days=int(np.sum(x>0)),losing_days=int(np.sum(x<0)),
       winning_day_fraction_pct=round(float(np.mean(x>0)*100),3),
       net_account_pct=round(float((eq[-1]-1)*100),6),
       max_closed_dd_pct=round(float(np.max(1-eq/peak)*100),6),
       worst_day_pct=round(float(np.min(x)*100),6))

def run():
    OUT.mkdir(parents=True,exist_ok=True)
    m=nov.load_with_nov()
    starts,hours,sides,fallback=nov.determine_entries(m,"follow5")
    if len(starts)!=15 or int(np.sum(fallback))!=6:
        raise AssertionError("Nov weekday count/fallback changed")
    volumes=m.volume.to_numpy(float)
    ratios=np.zeros(15)
    for d,i in enumerate(starts):
        old=volumes[i-105:i-5].reshape(20,5).sum(axis=1)
        mean=float(old.mean())
        ratios[d]=float(volumes[i-5:i].sum()/mean) if mean>0 else 0.
    allcfg,cfgids=regime.build_cfg()
    cfg=np.asarray([allcfg[
          cfgids["lock050"] if not fallback[d] else
          cfgids["trail075"] if ratios[d]>=1.25 else cfgids["trail050"]]
          for d in range(15)],dtype=float)
    policies,names=step7.build_exit_policies()
    ids={name:i for i,name in enumerate(names)}
    replay=step7.replay_with_nextbar_exits(
        m.open.to_numpy(float),m.high.to_numpy(float),
        m.low.to_numpy(float),m.close.to_numpy(float),
        starts,sides,cfg,policies,base.COST,base.SLIP
    )
    results=[];daily=[]
    for case,(eventexit,fallbackexit) in CASES.items():
        pertrade=np.where(fallback,ids[fallbackexit],ids[eventexit])
        d=np.arange(15)
        for fee_i,mode in enumerate(base.MODES):
            p=replay[0][d,pertrade,fee_i]
            costs=replay[1][d,pertrade,fee_i]
            gross=replay[2][d,pertrade]
            why=replay[3][d,pertrade]
            duration=replay[4][d,pertrade]
            z=measures(p)
            z.update(strategy=case,cost_model=mode,
                fallback_entries=int(np.sum(fallback)),
                signal_entries=int(np.sum(~fallback)),
                early_profit_closures=int(np.sum(why==4)),
                total_fees_gst_points=round(float(np.sum(costs)),3))
            results.append(z)
            for k,day in enumerate(nov.NDAYS):
                daily.append(dict(
                    strategy=case,cost_model=mode,day_ist=day.strftime("%Y-%m-%d"),
                    entry_hour_ist=int(hours[k]),
                    direction="LONG" if sides[k]>0 else "SHORT",
                    trigger="FORCED_FALLBACK" if fallback[k] else "VOLUME_SIGNAL",
                    preentry_volume5_ratio=round(float(ratios[k]),4),
                    exit_policy=fallbackexit if fallback[k] else eventexit,
                    net_account_pct=round(float(p[k]*100),6),
                    gross_btc_points=round(float(gross[k]),3),
                    total_fees_gst_btc_points=round(float(costs[k]),3),
                    exit_reason="STOP" if why[k]==2 else ("TP" if why[k]==1 else ("TIMEOUT" if why[k]==3 else "PREV_BAR_PROFIT_CUT")),
                    hold_minutes=int(duration[k])))
    df=pd.DataFrame(results)
    ledger=pd.DataFrame(daily)
    assert len(df)==8 and len(ledger)==120
    old=df[(df.strategy=="step6_unchanged")&(df.cost_model=="scalper_offer")].iloc[0]
    if old.profitable_days!=10 or abs(float(old.net_account_pct)-.019249)>.00011:
        raise AssertionError("Step6 Nov baseline parity drift "+str(old.to_dict()))
    df.to_csv(OUT/"all_four_frozen_variants_two_fee_models.csv",index=False)
    ledger.to_csv(OUT/"all_15_weekdays_four_frozen_variants.csv",index=False)
    (OUT/"summary.json").write_text(json.dumps(dict(
        predeclared_four_policies=list(CASES),
        audited_ist_dates="Nov 2–20 2026, 15 complete Mon-Fri days",
        one_trade_per_weekday=True,
        November_previously_exposed_to_prior_study=True,
        confirmed_step6_previous_result=True,
        results=results,
        limitations=["15 observations not statistically convincing","November prior exposure for older B/E",
           "No actual Scalper historical activation/fills, funding, market depth or tick ordering",
           "Other 2025-Oct2026 trials and full-sample choices create multiple-comparison overfit"]
    ),indent=2)+"\n")
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join([
        "# Step7 frozen November later chronological audit","",
        "All strategies trade the same 15 weekdays, under standard and hypothetical Scalper Offer costs.","",
        df.to_markdown(index=False),
        "","## Complete individual trade ledger","",
        ledger.to_markdown(index=False),
        "","## Interpretation",
        "All Step7 exit variants were inspected in old Jan2025-Oct2026 research. This 15-day November window is chronologically later but previously examined for Step6 baseline; cannot be called pristine blind OOS."
    ])+"\n")
    print("STEP7_NOVEMBER_RESULTS "+json.dumps(results,sort_keys=True),flush=True)
    print("STEP7_NOVEMBER_COMPLETE",flush=True)

if __name__=="__main__":
    run()
