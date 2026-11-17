#!/usr/bin/env python3
"""Stage 10: Expand high-volume exhaustion reversal profits using dynamic exits.

Reuses the EXACT Stage 8 M_exhaustion_reversal signal with no optimization of
entries. Studies gross TP 200/300/500/800/1200, cost-aware step-up and trailing.
The stop is checked before TP on ambiguous 1m OHLC bars. All stop changes
become active ONLY after the 1m candle CLOSE, never retroactively intrabar.
On a gap beyond a stop fill worse than stop. A trailing lock is a stop order,
not a guaranteed price. Source data Jan 2025 through Nov 16 2026.
"""
from pathlib import Path
import json
import math
import numpy as np
import pandas as pd
from numba import njit
from research_every_candle_200 import read_archive, periods, PERIOD_NAMES, FEE, SLIPPAGE
from research_anytime_volume_volatility_patterns import detect, build_events

OUT=Path("analysis/institutional_discovery_stage10_dynamic_exits")
PATTERN="M_exhaustion_reversal"
# More than 200, exit at price barrier or time. 0 target denotes unlimited.
MODELS={
    "fixed200": ("fixed",200.0),
    "fixed300": ("fixed",300.0),
    "fixed500": ("fixed",500.0),
    "fixed800": ("fixed",800.0),
    "fixed1200": ("fixed",1200.0),
    "trail100_after_net200": ("trail",100.0),
    "trail200_after_net200": ("trail",200.0),
    "trail_vol_after_net200": ("trail_vol",0.0),
    "step100_per_200_after_net200": ("step",0.0),
}
STOP_METHODS={
    "fixed100": ("fixed",100.0),
    "fixed200": ("fixed",200.0),
    "volatility_scaled": ("vol",0.0),
}
HORIZONS=(30,60,120,240)
MIN_3_PERIODS=(50,25,25)

@njit(cache=True)
def replay_one(op,hi,lo,cl,k,side,typical_range5,kind,arg,stop_kind,stop_arg,horizon):
    """Return exit index, gross, net, eligible-waiver hypothetical, type and MFE.
    
    kind: 0 fixed, 1 trail, 2 vol trail, 3 step profit lock.
    Stop and target checked before current minute CLOSE. Stop wins same-bar.
    """
    entry=float(op[k])
    fee_buffer=(2.*FEE*entry+2.*SLIPPAGE)
    if stop_kind==2:
        risk=max(150.0,min(500.0,1.5*typical_range5))
    else:
        risk=stop_arg
    stop_price=entry-side*risk
    target_price=entry+side*arg if kind==0 else 0.
    duration=horizon
    exit_price=float(cl[k+horizon-1])
    exit_code=2  # timeout
    last=k+horizon-1
    max_good=0.0
    min_bad=0.0
    trail_size=max(100.,min(500.,1.25*typical_range5)) if kind==2 else arg
    for j in range(k,k+horizon):
        if side==1:
            stop_touch=lo[j]<=stop_price
            target_touch=hi[j]>=target_price if kind==0 else False
            good=hi[j]-entry
            bad=entry-lo[j]
        else:
            stop_touch=hi[j]>=stop_price
            target_touch=lo[j]<=target_price if kind==0 else False
            good=entry-lo[j]
            bad=hi[j]-entry
        # High/low of stop minute may be unreachable before the stop itself;
        # MFE is descriptive only, NEVER used as fill logic.
        if good>max_good:max_good=good
        if bad>min_bad:min_bad=bad
        if stop_touch:
            if side==1:
                exit_price=min(op[j],stop_price)
            else:
                exit_price=max(op[j],stop_price)
            exit_code=0
            last=j
            break
        if target_touch:
            exit_price=target_price
            exit_code=1
            last=j
            break
        # After a fully closed minute, update the trailing level.
        # Activate when the CLOSE has achieved 200 points NET unrealized,
        # using conservative fee and adverse slippage allowance.
        if kind!=0:
            progress=side*(cl[j]-entry)
            if progress>=200.+fee_buffer:
                if kind==3:
                    # first lock net +50, then +150, +250 ... per extra
                    # 200 of close-confirmed favorable net price motion.
                    steps=math.floor((progress-(200.+fee_buffer))/200.)
                    locked_gross=fee_buffer+50.+100.*steps
                else:
                    locked_gross=progress-trail_size
                proposed=entry+side*locked_gross
                if side==1:
                    if proposed>stop_price:stop_price=proposed
                else:
                    if proposed<stop_price:stop_price=proposed
    fill_in=entry+side*SLIPPAGE
    fill_out=exit_price-side*SLIPPAGE
    realized=side*(fill_out-fill_in)
    normal=realized-FEE*(fill_in+fill_out)
    holding=last-k+1
    offer=realized-FEE*fill_in-(0.0 if holding<=30 else FEE*fill_out)
    return (last,exit_code,side*(exit_price-entry),normal,offer,holding,
            max_good,min_bad,risk)


def run_case(ev,op,hi,lo,cl,model_name,stop_name,horizon):
    kind_text,arg=MODELS[model_name]
    stop_text,stop_arg=STOP_METHODS[stop_name]
    kind={"fixed":0,"trail":1,"trail_vol":2,"step":3}[kind_text]
    stop_kind={"fixed":0,"vol":2}[stop_text]
    # Sort both LONG and SHORT chronologically; enforce one shared position.
    # This is per strategy model, not sum of simultaneous systems.
    filtered=ev.sort_values(["k","side"])
    rows=[]
    last=-1
    for z in filtered.itertuples(index=False):
        k=int(z.k)
        if k<=last:continue
        result=replay_one(op,hi,lo,cl,k,int(z.side),float(z.typical_range5),
                          kind,arg,stop_kind,stop_arg,int(horizon))
        j,reason,gross,net,offer,held,mfe,mae,used_risk=result
        last=int(j)
        rows.append(dict(entry_unix=int(z.entry_unix),exit_unix=int(z.entry_unix+60*(j-k)),
            period=z.period,side=z.side_name,model=model_name,
            stop=stop_name,horizon=horizon,
            target_reason=("stop" if reason==0 else "target" if reason==1 else "timeout"),
            entry_idx=k,exit_idx=int(j),gross_pts=round(gross,2),
            net_standard_pts=round(net,2),net_scalper_whatif_pts=round(offer,2),
            duration_min=int(held),mfe_pts=round(mfe,2),mae_pts=round(mae,2),
            initial_risk_pts=round(used_risk,2)))
    return rows


def stats(df):
    rows=[]
    for key,g in df.groupby(["period","model","stop","horizon"],sort=True):
        g=g.sort_values("entry_unix")
        for fee,net_field in (("standard_taker","net_standard_pts"),
                              ("scalper_eligibility_whatif","net_scalper_whatif_pts")):
            v=g[net_field].to_numpy(float)
            eq=np.r_[0.,np.cumsum(v)]
            gains=float(v[v>0].sum())
            losses=float(-v[v<0].sum())
            rows.append(dict(zip(["period","model","stop","horizon"],key),
                fee_model=fee,trades=len(g),profit_trades=int((v>0).sum()),
                losses_or_flat=int((v<=0).sum()),
                win_rate=round(float((v>0).mean()*100),2),
                net_mean=round(float(v.mean()),2),
                net_total=round(float(v.sum()),2),
                profit_factor=round(gains/losses,3) if losses else None,
                worst_net=round(float(v.min()),2),
                max_drawdown=round(float(np.max(np.maximum.accumulate(eq)-eq)),2),
                avg_mfe=round(float(g.mfe_pts.mean()),2),
                avg_duration_min=round(float(g.duration_min.mean()),2),
                share_mfe_300=round(float((g.mfe_pts>=300).mean()*100),2),
                share_mfe_500=round(float((g.mfe_pts>=500).mean()*100),2),
                share_mfe_800=round(float((g.mfe_pts>=800).mean()*100),2),
                share_mfe_1200=round(float((g.mfe_pts>=1200).mean()*100),2),
                stop_exits=int((g.target_reason=="stop").sum()),
                target_exits=int((g.target_reason=="target").sum()),
                timeout_exits=int((g.target_reason=="timeout").sum())))
    return pd.DataFrame(rows)


def robust(summary):
    out=[]
    std=summary[(summary.fee_model=="standard_taker")]
    for (model,stop,horizon),g in std.groupby(["model","stop","horizon"],sort=True):
        periods={z.period:z for z in g.itertuples()}
        key=PERIOD_NAMES[:3]
        if not all(name in periods for name in key):continue
        a,b,c=[periods[name] for name in key]
        ncut=MIN_3_PERIODS
        adequate=(a.trades>=ncut[0] and b.trades>=ncut[1] and c.trades>=ncut[2])
        out.append(dict(model=model,stop=stop,horizon=horizon,
            n2025=a.trades,net2025=a.net_mean,
            n2026h1=b.trades,net2026h1=b.net_mean,
            n2026h2=c.trades,net2026h2=c.net_mean,
            adequate_sample=adequate,
            all_positive=bool(adequate and min(a.net_mean,b.net_mean,c.net_mean)>0)))
    return pd.DataFrame(out)


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    f,seg_start,seg_end,quality=read_archive()
    periods_arr=periods(f.index)
    a,patterns=detect(f)
    base=build_events(f,seg_start,seg_end,periods_arr,a,{PATTERN:patterns[PATTERN]})
    # Same Stage 8 signal. Typical range measured BEFORE signal event at
    # close, using preceding 24 completed 5m bars only.
    at=pd.to_datetime(base.entry_utc,utc=True)
    base["typical_range5"]=a.loc[at,"rmed"].to_numpy(float)
    base["entry_unix"]=f.time.to_numpy(np.int64)[base.k.to_numpy(np.int32)]
    base["side_name"]=base.side.map({1:"LONG",-1:"SHORT"})
    if base.typical_range5.isna().any() or (base.typical_range5<=0).any():
        raise ValueError("Invalid prior candle volatility scaling")
    op=f.open.to_numpy(np.float64)
    hi=f.high.to_numpy(np.float64)
    lo=f.low.to_numpy(np.float64)
    cl=f.close.to_numpy(np.float64)
    alltrades=[]
    for model in MODELS:
        for stop in STOP_METHODS:
            for h in HORIZONS:
                alltrades.extend(run_case(base,op,hi,lo,cl,model,stop,h))
    if len(alltrades)==0:raise ValueError("No trades")
    trades=pd.DataFrame(alltrades)
    tab=stats(trades)
    comparison=robust(tab)
    trades.to_csv(OUT/"trade_ledger.csv.gz",index=False,
        compression={"method":"gzip","compresslevel":5,"mtime":0})
    tab.to_csv(OUT/"exit_comparison.csv",index=False)
    comparison.to_csv(OUT/"chronological_consistency.csv",index=False)
    good=comparison[comparison.all_positive] if not comparison.empty else comparison
    top=tab[(tab.fee_model=="standard_taker")&(tab.stop=="fixed200")&
            (tab.horizon==120)]
    summary=dict(
        pattern=PATTERN,data_1m_rows=len(f),first_utc=str(f.index[0]),
        last_utc=str(f.index[-1]),missing_minutes=quality["missing_minutes"],
        event_rows=len(base),simulated_independent_trades=len(trades),
        exit_models=list(MODELS),stop_models=list(STOP_METHODS),
        hold_windows_minutes=list(HORIZONS),
        consistent_positive_models=len(good),
        2025_2026_have_previously_been_studied=True,
        fee_per_side_including_gst=FEE,slippage_pts_per_side=SLIPPAGE,
        assumptions=[
            "M exhaustion reversal entry reproduced EXACTLY from Stage8",
            "Entry at first minute OPEN after complete 5m reversal signal",
            "Both directions share at most one position at a time within a given model",
            "Fixed targets are gross price points; trailing activation is fee-aware net +200 at close",
            "Trailing updates use CLOSED minute only, next minute stop check",
            "Stop checked before target if both touched in same minute",
            "Gapped stops fill at worse of minute open or stop level",
            "Time exits at last minute close; no extrapolation outside real minute data",
            "Taker fees 0.05% per side plus GST 18%; 5 points adverse slippage per side",
            "Hypothetical waived closing fee only for <=30m; historical eligibility unverified",
            "No funding, mark price liquidation, bid/ask spread, impact or maker execution",
            "Positive historical cells subject to many-tests bias, previously seen 2026 is not an independent holdout",
            "No target/stop or profit lock can guarantee zero losing trades"])
    (OUT/"quality.json").write_text(json.dumps(summary,indent=2)+"\n")
    report=[
        "# Stage 10 — Let high-volume exhaustion reversal profits run beyond 200 points",
        "",
        "## What changed",
        "Entry signal: **unchanged Stage 8 M_exhaustion_reversal**, on any 5-minute boundary.",
        "Compare gross fixed exits (200/300/500/800/1200), 200 NET activation trailing",
        "(100/200 points or prior-volatility distance), and step-up locks",
        "(first +50 NET lock then +100 for each additional +200 close-confirmed NET rise).",
        "Original 100/200 fixed initial stops, plus a prior 24x5m-range scaled initial stop.",
        "Holds 30/60/120/240m; one trade at a time across LONG and SHORT per model.",
        "",
        "## Main comparisons (fixed200 initial stop, 120 minute max hold, standard taker)",
        top[["period","model","trades","win_rate","net_mean","net_total",
             "profit_factor","max_drawdown","avg_duration_min",
             "share_mfe_500","share_mfe_800"]].to_markdown(index=False), "",
        "## Chronological consistency for every model",
        comparison.to_markdown(index=False),"",
        "## Stable positive variants (>= 50 / 25 / 25 independent 2025 / H1 / H2 trades)",
        good.to_markdown(index=False) if len(good) else "No consistently positive variant found.", "",
        "## Caveats",
        *["- "+x for x in summary["assumptions"]],"",
        "## Reproduce",
        "- scripts/research_dynamic_exit_stage10.py",
        "- exit_comparison.csv — every period, exit, stop, horizon and fee model",
        "- chronological_consistency.csv — stability audit",
        "- trade_ledger.csv.gz — full raw evidence in GitHub Actions artifact",
        "- quality.json — fee, fill and data limitations",
    ]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")
    print("STAGE10_COMPLETE "+json.dumps({k:summary[k] for k in
        ("event_rows","simulated_independent_trades","consistent_positive_models")}))
    print("MAIN_COMPARISON_FIXED200_STOP_120MIN")
    print(top.to_string(index=False))
    print("STABLE_POSITIVE")
    print(good.to_string(index=False))
    print("TOP_2025_STD")
    print(tab[(tab.fee_model=="standard_taker")&
              (tab.period=="2025_train")&
              (tab.trades>=50)].sort_values("net_mean",ascending=False).head(15).to_string(index=False))
    print("TOP_2026_H1_STD")
    print(tab[(tab.fee_model=="standard_taker")&
              (tab.period=="2026_H1_validation")&
              (tab.trades>=25)].sort_values("net_mean",ascending=False).head(12).to_string(index=False))

if __name__=="__main__":
    main()
