#!/usr/bin/env python3
"""First-passage +200 BTC points from Supertrend(10,3) touch, filter-by-filter.

The signal, first selected touch, 1m entry fill, and 15m closing-stop
conventions are identical to research_supertrend_15m_filter_grid.py.
For a raw +200 excursion from assumed limit-fill midprice, start checking
the following 1m bar (same-entry-minute OHLC order is not observable).
Separately report +200 measured from assumed slippage-adjusted fill.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import research_supertrend_15m_line_touch as base
import research_supertrend_15m_filter_grid as f

OUT=Path("analysis/supertrend_15m_touch_200point_20261122")
POINTS=200.0
CUTOFF="2026-11"
BAND_START="2025-01"

def measure(events, stopbar, minute, name_v, v_spec, name_a, a_spec):
    high=minute.high.to_numpy(float)
    opening=minute.open.to_numpy(float)
    closing=minute.close.to_numpy(float)
    times=minute.index
    last_cycle=-1
    records=[]
    for cycle,bar,j,mid,line,volume,atr_pct,atr_rel in events:
        if cycle==last_cycle:continue
        if not f.matches(volume,v_spec) or not f.volatility_match(atr_pct,atr_rel,a_spec):
            continue
        last_cycle=cycle
        k=np.searchsorted(stopbar,bar,side="left")
        sb=int(stopbar[k]) if k<len(stopbar) else -1
        stop_exit=(sb+1)*15 if sb>=0 else len(high)
        end=min(stop_exit,len(high))
        if j+1>=end:
            raw_hit=False; effective_hit=False
            raw_hit_min=None
        else:
            sub=high[j+1:end]
            raw_hits=np.flatnonzero(sub>=mid+POINTS)
            raw_hit=bool(len(raw_hits))
            raw_hit_min=j+1+int(raw_hits[0]) if raw_hit else None
            effective_hit=bool(np.any(sub>=mid+base.SLIP+POINTS))
        # For an illustrative gross 200-point take-profit, model raw +200
        # from the mid-entry, including slippage + taker fees + GST.
        if raw_hit:
            exit_j=raw_hit_min
            exit_mid=mid+POINTS
            reason="hit_200_first"
        elif stop_exit<len(high):
            exit_j=stop_exit
            exit_mid=float(opening[stop_exit])
            reason="15m_close_stop"
        else:
            exit_j=len(high)-1
            exit_mid=float(closing[-1])
            reason="data_end"
        entry_fill=mid+base.SLIP
        exit_fill=exit_mid-base.SLIP
        cost=base.FEE*(entry_fill+exit_fill)
        net=(exit_fill-entry_fill)-cost
        records.append(dict(
            volume_filter=name_v,volatility_filter=name_a,
            cycle=cycle, entry_utc=str(times[j]), exit_utc=str(times[exit_j]),
            entry_price=round(mid,5), support=round(line,5),
            first_200_hit=raw_hit,first_200_after_fills=effective_hit,
            exit_reason=reason, gross_pts=round(exit_mid-mid,5),
            net_pts=round(net,5), duration_min=int(exit_j-j),
            entry_vol_ratio=round(volume,5) if np.isfinite(volume) else None,
            entry_atrpct=round(atr_pct,5) if np.isfinite(atr_pct) else None,
        ))
    return pd.DataFrame(records)


def summarize(t, v, a, period, months):
    current=t[t.month_ist.isin(months)] if len(t) else t
    total=len(current)
    hits=int(current.first_200_hit.sum()) if total else 0
    adj=int(current.first_200_after_fills.sum()) if total else 0
    positives=int((current.net_pts>0).sum()) if total else 0
    net=float(current.net_pts.sum()) if total else 0.0
    eq=np.r_[0.0,np.cumsum(current.net_pts.to_numpy(float))] if total else np.zeros(1)
    return dict(volume_filter=v,volatility_filter=a,period=period,
                trades=total,reached_200_before_close_stop=hits,
                reached_200_after_entry_slip=adj,
                reached_200_pct=round(100*hits/total,2) if total else None,
                net_positive_trades=positives,
                net_positive_pct=round(100*positives/total,2) if total else None,
                estimated_net_pts=round(net,2),
                max_drawdown_pts=round(float(np.max(np.maximum.accumulate(eq)-eq)),2),
                close_stop_exits=int((current.exit_reason=="15m_close_stop").sum())
                     if total else 0)


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    m,h,files=base.load()
    st,direction=base.supertrend(h)
    vol,pct,rel=f.build_features(h)
    events,stopbars=f.candidate_touch_events(m,h,st,direction,vol,pct,rel)
    fullmonths=base.MONTHS
    all_rows=[]
    detail=[]
    for vol_name,v_spec in f.VOLUME.items():
        for atr_name,a_spec in f.VOLATILITY.items():
            t=measure(events,stopbars,m,vol_name,v_spec,atr_name,a_spec)
            if len(t):
                t["month_ist"]=pd.to_datetime(t.entry_utc,utc=True).dt.tz_convert(
                          "Asia/Kolkata").dt.strftime("%Y-%m")
                detail.append(t)
            for name, months in [
                ("2025_baseline",fullmonths[:12]),
                ("2026_H1_check",fullmonths[12:18]),
                ("2026_H2_seen_recheck",fullmonths[18:22]),
                ("22_complete_months",fullmonths)]:
                all_rows.append(summarize(t,vol_name,atr_name,name,months))
    summary=pd.DataFrame(all_rows)
    complete=summary[summary.period=="22_complete_months"]
    assert len(complete)==len(f.VOLUME)*len(f.VOLATILITY)==42
    # 801 total fills in the original %TP baseline through Nov 2026.
    base_all = [x for x in detail if x.volume_filter.iloc[0]=="vol_off" and
                x.volatility_filter.iloc[0]=="atr_off"]
    assert len(base_all)==1, "Unfiltered configuration missing"
    assert len(base_all[0])==801, f"Unfiltered total differs: {len(base_all[0])}"
    assert int(complete[(complete.volume_filter=="vol_off")&
        (complete.volatility_filter=="atr_off")].trades.iloc[0]) in (781,782,783)

    summary.to_csv(OUT/"first_200_summary.csv",index=False)
    ledger=pd.concat(detail,ignore_index=True)
    ledger.to_csv(OUT/"trade_ledger_200.csv.gz",index=False,compression="gzip")
    # Monthly counts help distinguish rare wins from reliable patterns.
    month=ledger[ledger.month_ist.isin(fullmonths)].groupby(
        ["volume_filter","volatility_filter","month_ist"]).agg(
        trades=("first_200_hit","count"),
        reached_200=("first_200_hit","sum"),
        reached_200_after_entry_slip=("first_200_after_fills","sum"),
        net_pts=("net_pts","sum")).reset_index()
    month.to_csv(OUT/"monthly_200_counts.csv",index=False)
    best_count=complete.sort_values("reached_200_before_close_stop",ascending=False)
    best_rate=complete[complete.trades>=50].sort_values(
        ["reached_200_pct","trades"],ascending=[False,False])
    chars=["volume_filter","volatility_filter","trades","reached_200_before_close_stop",
           "reached_200_pct","reached_200_after_entry_slip","estimated_net_pts"]
    txt=[
        "# 15m Supertrend line-touch: how many touch entries reach +200 points first?",
        "",
        "Delta Exchange India BTCUSD perpetual, archived 1m candles resampled to",
        "15m; Supertrend(10,3); stop **only after completed 15m closing breach**.",
        "Count +200 from executed midprice using 1m highs strictly **after**",
        "entry minute, before the next 15m closing-stop execution.",
        "Monthly inclusion by **IST entry month** January 2025 to October 2026;",
        "November 2026 partial month excluded. No shorts, one entry per bullish ST cycle.",
        "",
        "## Unfiltered and representative configurations",
        complete[((complete.volume_filter=="vol_off")&
                  (complete.volatility_filter=="atr_off"))|
                 ((complete.volume_filter=="vol_ge_2p0")&
                  (complete.volatility_filter=="atrpct_ge_0p40"))|
                 ((complete.volume_filter=="vol_ge_1p25")&
                  (complete.volatility_filter=="atrpct_ge_0p40"))|
                 ((complete.volume_filter=="vol_le_0p8")&
                  (complete.volatility_filter=="atrrel_ge_1p25"))][chars].to_markdown(index=False),
        "",
        "## Highest hit COUNTS (filters overlap; NEVER sum across configurations)",
        best_count[chars].head(15).to_markdown(index=False),
        "",
        "## Highest hit PERCENTAGES with at least 50 entries",
        best_rate[chars].head(15).to_markdown(index=False),
        "",
        "## Integrity and limitations",
        "- All filters evaluated using the most recent completed 15m candle only.",
        "- A 200-point hit is a gross PRICE EXCURSION, not a net $200 profit.",
        "- Net illustration assumes target limit at entry-mid +200, 0.05% taker each",
        "  side plus 18% GST, and 5 adverse points each side; funding excluded.",
        "- The stricter column **after_entry_slip** requires high >= entry-mid +205.",
        "- Same 1m entry candle's high is deliberately excluded (unknown event order).",
        "- Historical price data lacks bid/ask spreads and limit order fill certainty.",
        "- Later historical dates have already been used in research, not fresh OOS."
    ]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(txt)+"\n")
    (OUT/"quality.json").write_text(json.dumps(dict(
        source="Delta Exchange India BTCUSD perpetual 1m, archived Jan2025-Nov2026",
        observed_minutes=len(m),complete_15m=len(h),
        complete_ist_months=fullmonths[0]+" through "+fullmonths[-1],
        period_by="IST month of entry",lookahead_prevention="All filters last closed 15m; 1m TP after entry minute; stop at 15m close",
        counts_are_non_additive="42 filtered variants overlap",
        model_target="gross 200 points above mid-entry before closing stop",
        model_costs="0.05% taker per side +18% GST + 5 points adverse slip per side",
        limitations=["1m does not resolve same-minute order or limit-fill queue",
                     "No funding/spread/depth/liquidation/account return modeled",
                     "Historical research-exposed dates not untouched OOS"]),
        indent=2)+"\n")
    print("DATA: minute",len(m),"15m",len(h),"all touch candidates",len(events))
    print("UNFILTERED_22_MONTHS")
    print(complete[(complete.volume_filter=="vol_off")&
       (complete.volatility_filter=="atr_off")][chars].to_string(index=False))
    print("HIGHEST_RATE_50_MIN")
    print(best_rate[chars].head(12).to_string(index=False))
    print("HIGHEST_COUNT")
    print(best_count[chars].head(12).to_string(index=False))

if __name__=="__main__":
    main()
