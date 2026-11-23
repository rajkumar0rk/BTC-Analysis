#!/usr/bin/env python3
"""Apply regular Delta India BTCUSD Scalper Offer to the existing EMA9/21 experiments.

Zero closing trading fee (and thus zero GST on that fee) ONLY when closed
within 30 minutes; opening taker fee + GST remains due. The offer must have
been activated beforehand; this is a *counterfactual* when applied to 2025
and 2026. No promotional Diwali opening-fee cashback included.
"""
from pathlib import Path
import json
import pandas as pd
import numpy as np
import research_ema9_21_daily_quality_1m as orig
import research_ema9_21_quality_upgrade as quality
import research_ema9_21_htf_regime as htf

OUT=Path("analysis/ema9_21_scalper_offer")
FEE=orig.FEE
ALLOCATION=orig.ALLOCATION
MONTHS=quality.MONTHS
SLIP=5.

def apply_offer(d):
    d=d.copy()
    if len(d)==0:
        d["offer_eligible"]=pd.Series(dtype=bool)
        d["waived_exit_fee_gst_points"]=pd.Series(dtype=float)
        return d
    entry=pd.to_datetime(d.entry_utc,utc=True)
    exit=pd.to_datetime(d.exit_utc,utc=True)
    elapsed=(exit-entry).dt.total_seconds()/60
    # Every entry/exit timestamp labels a 1m bar; the exact intrabar
    # fill seconds are not in OHLCV. <=30m is a timestamp-based estimate.
    eligible=elapsed<=30
    # In the standard replay, fee_gst_points = 0.00059 * (fillin+fillout).
    saved=(d.fee_gst_points-FEE*d.entry_fill).clip(lower=0).where(eligible,0.0)
    assert np.isfinite(saved).all()
    d["offer_eligible"]=eligible
    d["waived_exit_fee_gst_points"]=saved
    d["standard_net_points"]=d.net_points
    d["standard_account_return"]=d.account_return
    d["net_points"]=d.net_points+saved
    d["fee_gst_points"]=d.fee_gst_points-saved
    d["account_return"]=ALLOCATION*d.net_points/d.entry_fill
    assert (d.loc[~d.offer_eligible,"waived_exit_fee_gst_points"]==0).all()
    assert (d.fee_gst_points>=0).all()
    return d

def metrics(d):
    stat,month=quality.summarize(d)
    stat.update(
       eligible_30m=int(d.offer_eligible.sum()),
       eligible_pct=round(float(100*d.offer_eligible.mean()),2) if len(d) else 0.,
       waived_fee_gst_points=round(float(d.waived_exit_fee_gst_points.sum()),2),
       winning_months_22=int((month.account_return_pct>0).sum()),
       losing_months_22=int((month.account_return_pct<0).sum()),
       flat_months_22=int((month.account_return_pct==0).sum()),
    )
    return stat,month

def audit_days(d):
    if d.empty:return
    days=d["signal_day_ist"] if "signal_day_ist" in d else d["entry_day_ist"]
    assert days.nunique()==len(d)
    dt=pd.to_datetime(days)
    assert (dt.dt.weekday<5).all()
    assert (days>="2025-01-01").all() and (days<"2026-11-01").all()

def record(name,group,ledger,results,months):
    audit_days(ledger)
    repriced=apply_offer(ledger)
    summary,monthly=metrics(repriced)
    normal,_=quality.summarize(ledger)
    summary.update(variant=name,group=group,
                   standard_return_pct=normal["net_return_pct"],
                   standard_2025_pct=normal["return_2025_pct"],
                   standard_2026_pct=normal["return_2026_pct"],
                   standard_winning_months=normal["positive_2025"]+normal["positive_2026"])
    results.append(summary)
    monthly["variant"]=name
    monthly["group"]=group
    months.append(monthly)
    return repriced,summary,monthly

def run():
    OUT.mkdir(parents=True,exist_ok=True)
    m=orig.load()
    results=[];monthly=[];baseline=None
    baselinesignals=orig.signals(m)
    origledger,_=orig.replay(m,baselinesignals,SLIP)
    baseline,bs,bm=record("baseline_weekday_ema21_reclaim","baseline",
                           origledger,results,monthly)
    baseline.to_csv(OUT/"baseline_repriced_trades.csv.gz",index=False,compression="gzip")
    print("SCALPER_BASELINE "+json.dumps(bs,sort_keys=True),flush=True)

    families,atr5=quality.feature_frame(m)
    quality.MAX_HOLD=720
    for family in quality.FAMILIES:
        for session in quality.SESSIONS:
            for mult in quality.STOP_MULT:
                for rr in quality.RRS:
                    name=f"{family}__{session}__atr{mult:g}__rr{rr:g}"
                    trades=quality.sim(m,families[family],atr5,session,mult,rr,slip=SLIP)
                    _,stat,_=record(name,"quality_32",trades,results,monthly)
                    print("SCALPER_QUALITY "+json.dumps(stat,sort_keys=True),flush=True)

    # Mirror the exact HTF prior run's cutoff and indicator construction.
    cutoff=pd.Timestamp("2026-11-01 00:00:00",tz="Asia/Kolkata").tz_convert("UTC")
    mh=m.loc[m.index<cutoff].copy()
    familyh,atr5h=quality.feature_frame(mh)
    regimes=htf.features(mh)
    for family in ("cross","trend_break"):
        for regime,(bull,bear) in regimes.items():
            a,b=familyh[family]
            for hold in (720,2160):
                quality.MAX_HOLD=hold
                name=f"{family}__{regime}__hold{hold}"
                trades=quality.sim(mh,(a&bull,b&bear),atr5h,"eu_us",2.5,3.,slip=SLIP)
                _,stat,_=record(name,"htf_12",trades,results,monthly)
                print("SCALPER_HTF "+json.dumps(stat,sort_keys=True),flush=True)

    summaries=pd.DataFrame(results)
    allmonths=pd.concat(monthly,ignore_index=True)
    summaries.to_csv(OUT/"all_variants_scalper.csv",index=False)
    allmonths.to_csv(OUT/"all_months_scalper.csv",index=False)
    selected={}
    # 2025 selection ONLY within each preregistered family; full series 2026 shown without retuning.
    for group in ("quality_32","htf_12"):
        options=summaries[summaries.group==group].sort_values(
             ["return_2025_pct","max_closed_dd_pct"],ascending=[False,True])
        best=options.iloc[0]
        selected[group]=best.to_dict()
        print("SCALPER_SELECTED_2025_"+group.upper()+" "+json.dumps(best.to_dict(),sort_keys=True),flush=True)
        bestmonthly=allmonths[(allmonths.group==group)&(allmonths.variant==best.variant)]
        bestmonthly.to_csv(OUT/(group+"_2025selected_monthly.csv"),index=False)
        print("MONTHLY_"+group+"\n"+bestmonthly.to_string(index=False),flush=True)
        # Test predeclared 29-minute hard exit (exit at exact next open after 29m)
        if group=="quality_32":
            family,session,atrpart,rrpart=best.variant.split("__")
            mult=float(atrpart.removeprefix("atr"))
            rr=float(rrpart.removeprefix("rr"))
            quality.MAX_HOLD=29
            forced=quality.sim(m,families[family],atr5,session,mult,rr,slip=SLIP)
        else:
            family,regime,holdpart=best.variant.split("__")
            a,b=familyh[family];rl,rs=regimes[regime]
            quality.MAX_HOLD=29
            forced=quality.sim(mh,(a&rl,b&rs),atr5h,"eu_us",2.5,3.,slip=SLIP)
        repriced,stats,force_month=record(best.variant+"__forced29","forced29_"+group,forced,
                                         results,monthly)
        repriced.to_csv(OUT/(group+"_forced29_ledger.csv.gz"),index=False,compression="gzip")
        force_month.to_csv(OUT/(group+"_forced29_monthly.csv"),index=False)
        selected[group+"_forced29"]=stats
        print("SCALPER_FORCED29_"+group.upper()+" "+json.dumps(stats,sort_keys=True),flush=True)

    selected["baseline"]=bs
    selected["best_by_total_22_hindsight_not_selected"]={}
    for group in ("quality_32","htf_12"):
        ranks=summaries[summaries.group==group]
        best=ranks.sort_values("net_return_pct",ascending=False).iloc[0]
        selected["best_by_total_22_hindsight_not_selected"][group]=best.to_dict()
        print("SCALPER_HINDSIGHT_NOT_SELECTED_"+group.upper()+" "+json.dumps(best.to_dict(),sort_keys=True),flush=True)

    (OUT/"summary.json").write_text(json.dumps(selected,indent=2)+"\n")
    report=["# EMA9/21 1m BTCUSD — Regular Scalper Offer fee counterfactual","",
            "**Offer mechanics:** BTCUSD futures zero closing fee only when closed <=30 minutes, assuming customer consent before entry. Opening 0.05% taker fee + 18% GST remains, noneligible exit 0.05% + GST. No time-period-specific Diwali voucher.","",
            "2025-only selection among fixed 32 and 12 family variants. 2026 is historical recheck but already researched. One entry maximum per IST weekday, zero-trade days allowed. Stop/TP intrabar OHLC replay; real fill seconds unknown. 5 point adverse slippage each side, 10% notional exposure, no leverage; funding excluded.",
            "","## Baseline (recalculated from original full trade ledger)","",json.dumps(bs,indent=2),
            "","## Best 2025-selected per group","",pd.DataFrame.from_records([selected[k] for k in ("quality_32","htf_12")]).to_markdown(index=False),
            "","## 29-minute hard-exit sensitivities on the selected rules","",
            pd.DataFrame.from_records([selected[k+"_forced29"] for k in ("quality_32","htf_12")]).to_markdown(index=False),
            "","## Full variant table","",summaries.to_markdown(index=False),
            "","## Baseline 22-month monthly results","",bm.to_markdown(index=False),
            "","## Historical-exposure limitations","",
            "- Current offer cannot be assumed to have been available/opted into for every historical 2025-26 trade.",
            "- 30-minute classification uses 1m candle timestamps, not millisecond order fills. Exact boundary trades may be misclassified.",
            "- Fees exclude any offer activation timing, actual fill/slippage quality, funding, and liquidation. No maker fills are assumed.",
            "- Chronological selection uses 2025 only; 2026 has already been repeatedly researched and is not pristine unseen data.",
            "- The old EMA9/21 strategy before the offer update is not changed. All outputs are counterfactual reratings.",
            ]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")
    print("EMA_SCALPER_OFFER_REPRICE_COMPLETE",flush=True)

if __name__=="__main__":
    run()
