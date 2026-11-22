#!/usr/bin/env python3
"""Diagnostic 500/1000 BTC-point first passage for bullish ST15m touch.

Same historical instruments, first filtered support touch, candle close stop
and 1m OHLC replay as the established 200-point first-passage diagnostic.
No optimization and no untouched validation window.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import research_supertrend_15m_200point as original
import research_supertrend_15m_filter_grid as grid
import research_supertrend_15m_line_touch as base

OUT=Path("analysis/supertrend_15m_touch_500_1000_20261122")
THRESHOLDS=(500.0,1000.0)
REPRESENTATIVE=(
    ("vol_off","atr_off"),
    ("vol_ge_1p25","atrpct_ge_0p30"),
    ("vol_ge_1p5","atrpct_ge_0p30"),
    ("vol_ge_2p0","atrpct_ge_0p30"),
    ("vol_ge_1p5","atrpct_ge_0p40"),
    ("vol_ge_2p0","atrpct_ge_0p40"),
)

def describe(t,part,vol_name,atr_name,target,months):
    t=t[t.month_ist.isin(months)].sort_values("entry_utc") if len(t) else t
    n=len(t)
    hits=int(t.first_200_hit.sum()) if n else 0
    slip_hits=int(t.first_200_after_fills.sum()) if n else 0
    v=t.net_pts.to_numpy(float) if n else np.empty(0,float)
    eq=np.r_[0.0,np.cumsum(v)]
    return dict(volume_filter=vol_name,volatility_filter=atr_name,
                target_points=int(target),period=part,trades=n,
                reached_target=hits,
                hit_rate_pct=round(100*hits/n,2) if n else None,
                reached_after_entry_slippage=slip_hits,
                close_stop_exits=int((t.exit_reason=="15m_close_stop").sum()) if n else 0,
                illustrative_net_pts=round(float(v.sum()),2),
                illustrative_win_trades=int((v>0).sum()),
                illustrative_max_drawdown_pts=round(float(
                    np.max(np.maximum.accumulate(eq)-eq)),2))

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    minute,h,files=base.load()
    line,direction=base.supertrend(h)
    vol,pct,rel=grid.build_features(h)
    events,stopbars=grid.candidate_touch_events(
        minute,h,line,direction,vol,pct,rel)
    # Structural baseline parity against the prior reported 200-point count:
    original.POINTS=200.0
    check=original.measure(events,stopbars,minute,"vol_off",
                  grid.VOLUME["vol_off"],"atr_off",grid.VOLATILITY["atr_off"])
    check["month_ist"]=pd.to_datetime(check.entry_utc,utc=True).dt.tz_convert(
                     "Asia/Kolkata").dt.strftime("%Y-%m")
    check=check[check.month_ist.isin(base.MONTHS)]
    assert len(check)==782, f"Unfiltered prior entry count changed: {len(check)}"
    assert int(check.first_200_hit.sum())==299, (
        f"Unfiltered +200 count not identical to published baseline:"
        f" {int(check.first_200_hit.sum())} instead of 299")
    results=[]; ledger=[]
    months=[]
    for target in THRESHOLDS:
        original.POINTS=target
        for volume_name,volume_spec in grid.VOLUME.items():
            for atr_name,atr_spec in grid.VOLATILITY.items():
                trades=original.measure(events,stopbars,minute,volume_name,
                                        volume_spec,atr_name,atr_spec)
                if len(trades):
                    trades["month_ist"]=pd.to_datetime(
                        trades.entry_utc,utc=True).dt.tz_convert(
                            "Asia/Kolkata").dt.strftime("%Y-%m")
                    trades["target_points"]=int(target)
                    ledger.append(trades)
                for label,partition in [
                    ("2025_baseline",base.MONTHS[:12]),
                    ("2026_H1_check",base.MONTHS[12:18]),
                    ("2026_H2_seen_recheck",base.MONTHS[18:22]),
                    ("22_complete_months",base.MONTHS)]:
                    results.append(describe(trades,label,volume_name,
                                            atr_name,target,partition))
                for mo in base.MONTHS:
                    sub=(trades[trades.month_ist==mo] if len(trades) else trades)
                    months.append(dict(
                        volume_filter=volume_name,volatility_filter=atr_name,
                        target_points=int(target),month_ist=mo,
                        trades=len(sub),
                        hits=int(sub.first_200_hit.sum()) if len(sub) else 0))
    df=pd.DataFrame(results)
    full=df[df.period=="22_complete_months"].copy()
    t500=full[full.target_points==500].set_index(
        ["volume_filter","volatility_filter"])
    t1000=full[full.target_points==1000].set_index(
        ["volume_filter","volatility_filter"])
    assert (t1000.trades==t500.trades).all()
    assert (t1000.reached_target<=t500.reached_target).all(), (
        "First passage monotonicity failed: 1,000 reached before 500")
    compare=t500[["trades","reached_target","hit_rate_pct"]].rename(columns={
        "reached_target":"hit_500","hit_rate_pct":"rate_500_pct"}).join(
        t1000[["reached_target","hit_rate_pct"]].rename(columns={
            "reached_target":"hit_1000","hit_rate_pct":"rate_1000_pct"})).reset_index()
    compare["hit_both"]=compare.hit_1000

    df.to_csv(OUT/"all_500_1000_splits.csv",index=False)
    compare.to_csv(OUT/"compare_500_1000_counts.csv",index=False)
    pd.DataFrame(months).to_csv(OUT/"monthly_counts_500_1000.csv",index=False)
    pd.concat(ledger,ignore_index=True).to_csv(
        OUT/"trade_ledger_500_1000.csv.gz",compression="gzip",index=False)
    (OUT/"quality.json").write_text(json.dumps(dict(
        data_source="Delta India BTCUSD 1m 2025-01 through 2026-11-21 UTC",
        minutes=len(minute),complete_15m=len(h),
        complete_ist_months="2025-01 through 2026-10",
        original_200_parity={"trades":782,"reached_200":299,"passed":True},
        instrument="BTCUSD perpetual long-only Supertrend(10,3) 15m first filtered line touch",
        thresholds=list(THRESHOLDS),
        condition="1m price high on later minute reaches entry-mid plus target, BEFORE 15m close stop",
        stop="At 15m close below previously published Supertrend support, next 1m open",
        slippage="5 points adverse at entry and exit",
        fees="0.05% per side plus 18% GST",
        limitations=[
            "1m OHLC does not resolve same-minute order; entry-minute target not counted",
            "Missing order-book depth, maker/taker fill guarantees, funding and liquidation",
            "These are 1BTC-equivalent price point first-passages, not account profit",
            "All historical months are research-exposed, no independent holdout",
            "Filters overlap: do NOT sum their trade counts"]),
        indent=2)+"\n")
    cols=["volume_filter","volatility_filter","trades","hit_500",
          "rate_500_pct","hit_1000","rate_1000_pct"]
    representative=compare[compare.apply(
        lambda x: (x.volume_filter,x.volatility_filter) in REPRESENTATIVE,
        axis=1)]
    high500=compare[compare.trades>=50].sort_values(
        ["rate_500_pct","trades"],ascending=[False,False]).head(12)
    high1000=compare[compare.trades>=50].sort_values(
        ["rate_1000_pct","trades"],ascending=[False,False]).head(12)
    nofil=compare[(compare.volume_filter=="vol_off") &
                  (compare.volatility_filter=="atr_off")].iloc[0]
    report=[
        "# BTCUSD 15m Supertrend first-touch: 500 and 1,000 BTC-point first passage",
        "",
        "Delta India BTCUSD perpetual, Jan 2025–Oct 2026 complete IST months.",
        "Same 15m close stop, one long per bullish cycle, 1m execution.",
        "The same-entry minute is excluded because OHLC cannot resolve ordering.",
        "",
        "## Unfiltered (all eligible touches)",
        f"- {int(nofil.trades)} trades.",
        f"- +500 reached BEFORE closing stop: **{int(nofil.hit_500)}** "
        f"({float(nofil.rate_500_pct):.2f}%).",
        f"- +1,000 reached BEFORE closing stop: **{int(nofil.hit_1000)}** "
        f"({float(nofil.rate_1000_pct):.2f}%).",
        "- +1,000 counts are a subset of +500; do not add them.",
        "",
        "## Representative volume/volatility combinations",
        representative[cols].to_markdown(index=False),"",
        "## Highest +500 hit rates (at least 50 trades)",
        high500[cols].to_markdown(index=False),"",
        "## Highest +1,000 hit rates (at least 50 trades)",
        high1000[cols].to_markdown(index=False),"",
        "## Definitions",
        "- Volume factor: last closed 15m volume / mean of preceding 20 fully closed 15m volumes.",
        "- ATR percentage: 15m Wilder ATR14 / last closed price × 100.",
        "- All support lines and filters known before the candidate 15m candle.",
        "- +500/1,000 are **gross price movement**, NOT 500/1000 net profit.",
        "- Individual results and estimated net target-TP replay in CSV; costs assumed.",
        "- The 42 variants overlap, so summed hit counts are meaningless.",
        "- All previously researched months; not an untouched out-of-sample test."
    ]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")
    print("200_POINT_PARITY 782 entries, 299 hits — PASS")
    print("UNFILTERED",json.dumps(nofil.to_dict()))
    print("REPRESENTATIVE\n"+representative[cols].to_string(index=False))
    print("TOP_500_MIN50\n"+high500[cols].to_string(index=False))
    print("TOP_1000_MIN50\n"+high1000[cols].to_string(index=False))
    print("DONE")
if __name__=="__main__":
    main()
