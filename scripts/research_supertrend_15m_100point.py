#!/usr/bin/env python3
"""Count +100 BTC points before 15m Supertrend closing stop, same as 200/500/1000 report.
No hard fixed-price SL and no profit-protection stop. 1m highs AFTER entry minute.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import research_supertrend_15m_line_touch as base
import research_supertrend_15m_filter_grid as f
import research_supertrend_15m_200point as passage

OUT=Path("analysis/supertrend_15m_touch_100point_20261122")
POINTS=(100,200,500,1000)
FOCUS=[
("vol_off","atr_off"),("vol_ge_1p25","atrpct_ge_0p30"),
("vol_ge_1p5","atrpct_ge_0p30"),("vol_ge_2p0","atrpct_ge_0p30"),
("vol_ge_1p5","atrpct_ge_0p40"),("vol_ge_2p0","atrpct_ge_0p40")]

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    minute,h,files=base.load()
    line,direction=base.supertrend(h)
    volume,atrpct,atrrel=f.build_features(h)
    events,stopbar=f.candidate_touch_events(
        minute,h,line,direction,volume,atrpct,atrrel)
    rows=[];monthly=[];ledgers=[]
    for target in POINTS:
        passage.POINTS=float(target)
        for vn,vs in f.VOLUME.items():
            for an,ats in f.VOLATILITY.items():
                t=passage.measure(events,stopbar,minute,vn,vs,an,ats)
                if len(t):
                    t["month_ist"]=pd.to_datetime(t.entry_utc,utc=True).dt.tz_convert(
                        "Asia/Kolkata").dt.strftime("%Y-%m")
                    t["target_pts"]=target
                    ledgers.append(t)
                for period,months in [
                    ("2025",base.MONTHS[:12]),
                    ("2026_H1",base.MONTHS[12:18]),
                    ("2026_JulOct",base.MONTHS[18:22]),
                    ("22_months",base.MONTHS)]:
                    sub=t[t.month_ist.isin(months)] if len(t) else t
                    hits=int(sub.first_200_hit.sum()) if len(sub) else 0
                    after_slip=int(sub.first_200_after_fills.sum()) if len(sub) else 0
                    n=len(sub)
                    rows.append(dict(
                        target_pts=target,volume_filter=vn,
                        volatility_filter=an,period=period,
                        trades=n,reached_before_close_stop=hits,
                        pct_reached=round(100*hits/n,2) if n else None,
                        reached_after_entry_slippage=after_slip,
                        not_reached=n-hits,
                        illustrative_net_pts=round(float(sub.net_pts.sum()),2)
                              if n else 0.0))
                for month in base.MONTHS:
                    sub=t[t.month_ist==month] if len(t) else t
                    monthly.append(dict(
                        target_pts=target,volume_filter=vn,
                        volatility_filter=an,month_ist=month,
                        trades=len(sub),hits=int(sub.first_200_hit.sum())
                        if len(sub) else 0))
    out=pd.DataFrame(rows)
    allperiod=out[out.period=="22_months"]
    unfil=allperiod[(allperiod.volume_filter=="vol_off")&
                    (allperiod.volatility_filter=="atr_off")].sort_values("target_pts")
    assert len(out)==len(POINTS)*len(f.VOLUME)*len(f.VOLATILITY)*4
    assert len(unfil)==len(POINTS)
    assert unfil.trades.eq(782).all()
    for target,n in [(200,299),(500,171),(1000,92)]:
        got=int(unfil[unfil.target_pts==target].reached_before_close_stop.iloc[0])
        assert got==n, f"Parity +{target}: expected {n} got {got}"
    c100=allperiod[allperiod.target_pts==100]
    focus=c100[c100.apply(lambda r:
              (r.volume_filter,r.volatility_filter) in FOCUS,axis=1)]
    out.to_csv(OUT/"all_100_200_500_1000_splits.csv",index=False)
    pd.DataFrame(monthly).to_csv(OUT/"monthly_first_passage_counts.csv",index=False)
    pd.concat(ledgers,ignore_index=True).to_csv(
        OUT/"trade_ledger_all_4_targets.csv.gz",index=False,compression="gzip")
    (OUT/"quality.json").write_text(json.dumps(dict(
        data_source="Delta India BTCUSD perpetual 1m archive",
        period="22 complete IST entry months, Jan2025-Oct2026",
        minute_count=len(minute),bar15_count=len(h),target_points=POINTS,
        unfiltered_parity=unfil.to_dict("records"),
        entry="15m ST(10,3) bullish support first eligible touch, one per cycle",
        exit="15m prior closed Supertrend support closing breach, exit next 1m open",
        first_passage="1m high AFTER entry minute >= entry-mid + target BEFORE 15m close-stop",
        slippage_points_each_side=base.SLIP,
        fees="0.05% per side plus 18% GST",
        caveats=["No fixed hard SL; compare to 1:1 study separately",
                 "No entry-minute favorable exit from ambiguous OHLC",
                 "Overlapping filter combinations, counts non-additive",
                 "Historical 1m OHLC not true bid/ask or limit fill sequence",
                 "Funding, leverage, margin, and exchange queue absent",
                 "No untouched out of sample"]),indent=2)+"\n")
    cols=["target_pts","volume_filter","volatility_filter","trades",
          "reached_before_close_stop","pct_reached",
          "reached_after_entry_slippage","not_reached"]
    rep=[
        "# BTCUSD 15m Supertrend: how many first-touch entries reach +100?",
        "",
        "Delta India BTCUSD perpetual; 1m OHLC, 22 completed IST months Jan2025-Oct2026.",
        "Gross price excursion **before 15m closing stop**; NO fixed 100-point hard SL.",
        "One entry per bullish Supertrend(10,3) cycle.",
        "",
        "## Unfiltered +100, +200, +500 and +1,000 comparison",
        unfil[cols].to_markdown(index=False),"",
        "## +100 with representative prior-closed-bar volume/ATR filters",
        focus[cols].to_markdown(index=False),"",
        "## 42 combinations at +100, ranked by hit rate (>=50 trades)",
        c100[c100.trades>=50].sort_values("pct_reached",ascending=False)[cols]
           .head(20).to_markdown(index=False),"",
        "## Reconciliation",
        "- Unfiltered +200 = 299, +500 = 171, +1000 = 92 — all passed prior report parity.",
        "- +100 hit count is a gross move; not net +100 profit.",
        "- The separate 1:1 RR study reported 325 target exits from 782 entries",
        "  with a 100-point **hard SL**. Hard-stop-first vs Supertrend-stop-only",
        "  are different questions; don't compare or conflate counts.",
        "- Excludes price highs in the entry minute, because OHLC ordering is unknown.",
        "- Volume/volatility data is last fully closed 15m bar (no lookahead).",
        "- 2025/2026 dates have already been researched; not new OOS."
    ]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(rep)+"\n")
    print("UNFILTERED",unfil[cols].to_string(index=False))
    print("FILTERS_AT_100",focus[cols].to_string(index=False))
    print("RECONCILIATION_PASS",flush=True)
if __name__=="__main__":
    main()
