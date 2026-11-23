#!/usr/bin/env python3
"""Frozen November 2–20 2026 audit of 2025-selected online BTC event direction.

No re-optimization. Seed the online event learner with Jan2025–Oct2026
settled shadow outcomes; then update ONLY after each previous Nov weekday.
One real position per weekday (15 total); compares frozen Step6 versus E.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import research_btc_every_weekday_reset_step1 as base
import research_btc_every_weekday_exit_protection_step3 as protect
import research_btc_daily_causal_regime_step5 as regime
import audit_btc_daily_fallback_regime_november_2026 as nov
import research_btc_daily_online_direction_step6 as online

OUT=Path("analysis/btc_daily_online_direction_step6/november_audit")
DAYCOUNT=15

def report_metrics(ret):
    r=np.asarray(ret,dtype=float)
    w=np.cumprod(1+r)
    peak=np.maximum.accumulate(np.r_[1.,w])[1:]
    return dict(
        trades=len(r),profitable_days=int(np.sum(r>0)),
        losing_days=int(np.sum(r<0)),
        profitable_days_pct=round(float(100*np.mean(r>0)),3),
        net_compounded_account_pct=round(float(100*(w[-1]-1)),6),
        max_closed_dd_pct=round(float(100*np.max(1-w/peak)),6),
        worst_day_pct=round(float(100*np.min(r)),6)
    )

def run():
    OUT.mkdir(parents=True,exist_ok=True)
    # Existing full 2025-through-October history, no November included.
    historic=online.retrieve(base.load())
    old_events=~historic["isfallback"]
    old_returns=historic["event"][1][0][old_events,:]
    contexts=historic["eventimpulse"][old_events]
    event_history=[list(row) for row in old_returns]
    event_history_ctx=[bool(x) for x in contexts]
    assert len(event_history)==260 and old_returns.shape==(260,2)

    m=nov.load_with_nov()
    st,hr,side,fb=nov.determine_entries(m,"follow5")
    assert len(st)==DAYCOUNT and int(np.sum(~fb))==9 and int(np.sum(fb))==6
    # Keep exactly the same 1m stop/lock/trailing recipe definitions as Step6.
    cfg,lookup=regime.build_cfg()
    raw_baseline=protect.run_exit_grid(m.open.to_numpy(float),
        m.high.to_numpy(float),m.low.to_numpy(float),st,hr,side,cfg,base.COST,base.SLIP)
    raw_counter=protect.run_exit_grid(m.open.to_numpy(float),
        m.high.to_numpy(float),m.low.to_numpy(float),st,hr,-side,cfg,base.COST,base.SLIP)

    cl=m.close.to_numpy(float)
    op=m.open.to_numpy(float)
    volume=m.volume.to_numpy(float)
    impulse=np.zeros(DAYCOUNT,dtype=bool)
    target_exit=np.full(DAYCOUNT,lookup["lock050"],dtype=np.int16)
    ratio=np.zeros(DAYCOUNT)
    for di in range(DAYCOUNT):
        i=st[di]
        pclose=float(cl[i-1])
        impulse[di]=abs(pclose/float(op[i-5])-1)>=.0015
        historicalvol=volume[i-105:i-5].reshape(20,5).sum(axis=1)
        meanvol=float(historicalvol.mean())
        ratio[di]=float(volume[i-5:i].sum()/meanvol) if meanvol else 0.
        if fb[di]:
            target_exit[di]=lookup["trail075"] if ratio[di]>=1.25 else lookup["trail050"]

    # **Chronological**: select day d only using earlier finished trading days.
    follow=np.zeros(DAYCOUNT,dtype=bool)
    same_context_counts=np.zeros(DAYCOUNT,dtype=int)
    for d in range(DAYCOUNT):
        if not fb[d]:
            max_prior=min(30,len(event_history))
            idx=np.arange(len(event_history)-max_prior,len(event_history),dtype=int)
            idx=idx[np.asarray(event_history_ctx,dtype=bool)[idx]==impulse[d]]
            same_context_counts[d]=len(idx)
            if len(idx)>=12:
                prior=np.asarray(event_history,dtype=float)[idx]
                mean=np.mean(prior,axis=0)
                # Arm 0=FADE5; arm 1=FOLLOW5; stringent preference margin.
                follow[d]=bool(mean[1]>mean[0]+.0003)
            # Only AFTER deciding today, observe today's counterfactual
            # exits (known by end of current day). No within-day leak.
            past_fade=float(raw_baseline[0][d,lookup["lock050"],1])
            past_follow=float(raw_counter[0][d,lookup["lock050"],1])
            event_history.append([past_fade,past_follow])
            event_history_ctx.append(bool(impulse[d]))
    assert not np.any(follow & fb)
    outcomes=[]
    days=[]
    for version in ("E_previous","STEP6_online"):
        for mi,mode in enumerate(base.MODES):
            chosen=np.arange(DAYCOUNT)
            q=target_exit
            p=raw_baseline[0][chosen,q,mi].copy()
            c=raw_baseline[1][chosen,q,mi].copy()
            g=raw_baseline[2][chosen,q].copy()
            reason=raw_baseline[3][chosen,q].copy()
            duration=raw_baseline[4][chosen,q].copy()
            switched=(follow if version=="STEP6_online" else np.zeros(DAYCOUNT,dtype=bool))
            if np.any(switched):
                use=np.flatnonzero(switched)
                p[use]=raw_counter[0][use,lookup["lock050"],mi]
                c[use]=raw_counter[1][use,lookup["lock050"],mi]
                g[use]=raw_counter[2][use,lookup["lock050"]]
                reason[use]=raw_counter[3][use,lookup["lock050"]]
                duration[use]=raw_counter[4][use,lookup["lock050"]]
            summary=report_metrics(p)
            summary.update(version=version,fees=mode,
                           volume_event_days=int(np.sum(~fb)),
                           mandatory_fallback_days=int(np.sum(fb)),
                           event_direction_swaps=int(np.sum(switched)),
                           total_fee_gst_btc_points=round(float(np.sum(c)),2),
                           stop_exits=int(np.sum(reason==2)),
                           tp_exits=int(np.sum(reason==1)),
                           timeout_exits=int(np.sum(reason==3)))
            outcomes.append(summary)
            for d in range(DAYCOUNT):
                days.append(dict(
                    model=version,fees=mode,
                    day_ist=nov.NDAYS[d].strftime("%Y-%m-%d"),
                    hour_ist=int(hr[d]),
                    signal="FALLBACK" if fb[d] else "VOLUME_EVENT",
                    side="LONG" if side[d]*(-1 if switched[d] else 1)>0 else "SHORT",
                    online_follow5=bool(switched[d]),
                    prior_matching_event_cases=int(same_context_counts[d]),
                    preentry_impulse5=bool(impulse[d]),
                    preentry_volume_ratio=round(float(ratio[d]),5),
                    exit_rule=next(name for name,x in lookup.items() if x==q[d]),
                    net_account_pct=round(float(100*p[d]),6),
                    gross_btc_points=round(float(g[d]),4),
                    fees_gst_points=round(float(c[d]),4),
                    hold_minutes=int(duration[d]),
                    exit_reason="STOP" if reason[d]==2 else ("TARGET" if reason[d]==1 else "TIMEOUT")
                ))
    tab=pd.DataFrame(outcomes)
    ledger=pd.DataFrame(days)
    if len(tab)!=4 or len(ledger)!=60:
        raise AssertionError("Expected four 15-day trade ledgers")
    prev=tab[(tab.version=="E_previous")&(tab.fees=="scalper_offer")].iloc[0]
    if int(prev.profitable_days)!=10 or abs(float(prev.net_compounded_account_pct)-.01925)>.00011:
        raise AssertionError("Earlier November E baseline parity failed "+str(prev.to_dict()))
    tab.to_csv(OUT/"november_2026_four_repricing_results.csv",index=False)
    ledger.to_csv(OUT/"november_2026_frozen_daily_15_trades.csv",index=False)
    (OUT/"summary.json").write_text(json.dumps(dict(
        frozen_method="online_impulse5, last 30 prior completed EVENT weekdays, same context, min 12 observations, +0.0003 mean return margin, fallback fixed at 21h FOLLOW5",
        train_causal_shadow_source="Delta BTCUSD true 1m Jan2025–Oct2026",
        period="Nov 2–20 2026; 15 full IST weekdays",
        event_eligible_days=9,forced_fallback_days=6,
        actual_nov_event_side_flips=int(np.sum(follow)),
        no_current_day_prices_used_in_selection=True,
        results=outcomes,
        caveats=[
          "15-day audit has previously been exposed for older baseline, not an independently unobserved period",
          "All old shadow arm returns are after-cost hypothetical fills, not sent live orders",
          "Offer historical opt-in/fill and actual latency unknown, no funding or exchange depth",
          "No selection on November outcomes allowed"]),indent=2)+"\n")
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join([
        "# Frozen Step6 previous-days-only direction: November 2026 audit",
        "",
        "All variants place exactly one trade on each November 2–20 IST weekday.",
        "The last-30 EVENT-day adaptation is seeded ONLY with completed 2025–Oct2026 shadow outcomes, updates only after a new day is closed.",
        "",
        tab.to_markdown(index=False),
        "",
        "## 15 audited trades",
        "",
        ledger.to_markdown(index=False),
        "",
        "## Caveats",
        "November 2026 has been inspected in earlier BTC-Analysis studies; this later-period audit is not statistically pristine. Hypothetical Scalper Offer eligibility, actual fills, ticks, depth and funding remain limitations."
    ])+"\n")
    print("STEP6_NOVEMBER_RESULTS "+json.dumps(outcomes,sort_keys=True),flush=True)
    print("STEP6_NOVEMBER_AUDIT_COMPLETE",flush=True)

if __name__=="__main__":
    run()
