#!/usr/bin/env python3
"""Causal volume × volatility ablation of prior BTCUSD 15m Supertrend touch.

210 variants: 6 prior-closed-bar volume regimes, 7 prior-closed-bar ATR
regimes and the five original TPs. Original entry, closing-stop and cost
conventions preserved. No untouched historical OOS.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import research_supertrend_15m_line_touch as base

OUT = Path("analysis/supertrend_15m_filter_grid_20261122")
VOLUME = {
    "vol_off": ("off", 0.0),
    "vol_ge_1p0": ("ge", 1.0),
    "vol_ge_1p25": ("ge", 1.25),
    "vol_ge_1p5": ("ge", 1.5),
    "vol_ge_2p0": ("ge", 2.0),
    "vol_le_0p8": ("le", 0.8),
}
VOLATILITY = {
    "atr_off": ("off", 0.0, "off"),
    "atrpct_ge_0p10": ("pct", 0.10, "ge"),
    "atrpct_ge_0p20": ("pct", 0.20, "ge"),
    "atrpct_ge_0p30": ("pct", 0.30, "ge"),
    "atrpct_ge_0p40": ("pct", 0.40, "ge"),
    "atrrel_ge_1p25": ("rel", 1.25, "ge"),
    "atrrel_le_0p8": ("rel", 0.8, "le"),
}
TP = base.TP_PCTS
PERIODS = ["2025_train", "2026_H1_check", "2026_H2_seen_recheck"]
BASELINE = {
    0.2: (782, 315, -95477.50),
    0.4: (782, 220, -87667.46),
    0.5: (782, 191, -86638.39),
    0.6: (781, 163, -88524.06),
    1.0: (781, 115, -88680.47),
}


def wilder_atr(h, period=14):
    a=h[["open","high","low","close"]].to_numpy(float)
    high=a[:,1]; low=a[:,2]; cl=a[:,3]
    prev=np.r_[cl[0],cl[:-1]]
    tr=np.maximum(high-low,np.maximum(abs(high-prev),abs(low-prev)))
    atr=np.full(len(h),np.nan)
    atr[period-1]=tr[:period].mean()
    for i in range(period,len(h)):
        atr[i]=(atr[i-1]*(period-1)+tr[i])/period
    return pd.Series(atr,index=h.index)


def build_features(h):
    v=h.volume.astype(float)
    vol=v / v.rolling(20,min_periods=20).mean().shift(1)
    atr=wilder_atr(h)
    atr_pct=100*atr/h.close
    atr_rel=atr / atr.rolling(50,min_periods=50).mean().shift(1)
    return vol.to_numpy(float),atr_pct.to_numpy(float),atr_rel.to_numpy(float)


def candidate_touch_events(minute,h,line,direction,vol,atr_pct,atr_rel):
    lows=minute.low.to_numpy(float); opens=minute.open.to_numpy(float)
    events=[]
    cycle=0
    n=len(h)
    close=h.close.to_numpy(float)
    fail=np.zeros(n,dtype=bool)
    for i in range(base.PERIOD+1,n):
        if direction[i-1]==-1 and direction[i-2]!=-1:
            cycle+=1
        if direction[i-1]!=-1:
            continue
        # The stop is always decided using the support that was known at
        # the START of this 15m block; not its final (recomputed) line.
        fail[i]=(close[i]<line[i-1] or direction[i]==1)
        start=i*15; end=start+15
        hit=np.flatnonzero(lows[start:end]<=line[i-1])
        if not len(hit):
            continue
        j=start+int(hit[0])
        events.append((cycle,i,j,min(float(opens[j]),float(line[i-1])),
                       float(line[i-1]),float(vol[i-1]),float(atr_pct[i-1]),
                       float(atr_rel[i-1])))
    # Include failed closing blocks even if no touch, for positions open from
    # prior blocks; first failure after entry determines the stop bar.
    assert len(fail)==n
    stopbar=np.flatnonzero(fail)
    return events,stopbar


def matches(value,spec):
    rule,threshold=spec
    if rule=="off":return True
    return bool(np.isfinite(value) and (
        value>=threshold if rule=="ge" else value<=threshold))


def volatility_match(pct,relative,spec):
    metric,threshold,operator=spec
    if metric=="off":return True
    return matches(pct if metric=="pct" else relative, (operator,threshold))


def replay_variant(events,stopbar,minute,v_spec,a_spec,tp):
    high=minute.high.to_numpy(float)
    op=minute.open.to_numpy(float)
    close=minute.close.to_numpy(float)
    times=minute.index
    last_cycle=None
    trades=[]
    # Each completed bullish cycle has at most one trade. A filtered-out
    # touch does NOT consume the cycle, so later touches can qualify.
    for cycle,bar,j,mid,line,vol,pct,relative in events:
        if cycle==last_cycle:
            continue
        if not matches(vol,v_spec) or not volatility_match(pct,relative,a_spec):
            continue
        last_cycle=cycle
        entry_fill=mid+base.SLIP
        target=entry_fill*(1+tp)
        stop_i=np.searchsorted(stopbar,bar,side="left")
        last_bar=int(stopbar[stop_i]) if stop_i<len(stopbar) else -1
        end_minute=(last_bar+1)*15 if last_bar>=0 else len(high)
        # The price path INSIDE the entry minute is unknown: never award an
        # immediate favorable TP. A 15m closing stop cannot precede that
        # candle's subsequent observed 1m highs.
        hits=np.flatnonzero(high[j+1:end_minute]>=target)
        p=dict(entry_i=j,entry_mid=mid,entry_fill=entry_fill,
               entry_line=line,tp_pct=tp,target=target)
        if len(hits):
            exit_j=j+1+int(hits[0])
            trades.append(base.record(p,exit_j,target,"target",times))
        else:
            if end_minute<len(high):
                trades.append(base.record(p,end_minute,float(op[end_minute]),
                                          "15m_close_stop",times))
            else:
                trades.append(base.record(p,len(high)-1,float(close[-1]),
                                          "data_end",times))
    t=pd.DataFrame(trades)
    if len(t):
        t["month_ist"]=pd.to_datetime(t.exit_utc,utc=True).dt.tz_convert(
                          "Asia/Kolkata").dt.strftime("%Y-%m")
    return t


def period_for_month(m):
    if m<"2026-01":return "2025_train"
    if m<"2026-07":return "2026_H1_check"
    if m<"2026-11":return "2026_H2_seen_recheck"
    return "Nov_partial"


def stats(t):
    if len(t)==0:
        return dict(trades=0,wins=0,losses=0,win_rate_pct=None,
                    tp_hits=0,close_stops=0,gross_pts=0.0,net_pts=0.0,
                    net_avg_pts=None,pf=None,max_drawdown_pts=0.0,
                    fees_pts=0.0)
    v=t.net_pts.to_numpy(float)
    eq=np.r_[0.0,np.cumsum(v)]
    win=v[v>0]; loss=v[v<=0]
    return dict(trades=len(t),wins=len(win),losses=len(loss),
                win_rate_pct=round(100*len(win)/len(t),2),
                tp_hits=int((t.exit_reason=="target").sum()),
                close_stops=int((t.exit_reason=="15m_close_stop").sum()),
                gross_pts=round(float(t.gross_pts.sum()),2),
                net_pts=round(float(v.sum()),2),
                net_avg_pts=round(float(v.mean()),2),
                pf=round(float(win.sum()/-loss.sum()),3) if len(loss) and -loss.sum()>0 else None,
                max_drawdown_pts=round(float(np.max(np.maximum.accumulate(eq)-eq)),2),
                fees_pts=round(float(t.fees_pts.sum()),2))


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    minute,h,files=base.load()
    line,dirn=base.supertrend(h)
    vol,pct,rel=build_features(h)
    events,stops=candidate_touch_events(minute,h,line,dirn,vol,pct,rel)
    assert len(events)>500, f"Unexpectedly few touch events: {len(events)}"
    assert len(stops)>100, f"Unexpectedly few closing stops: {len(stops)}"
    print("DATA",len(minute),"minutes",len(h),"15m bars",len(events),
          "candidate touch blocks",len(stops),"15m closes below support")

    rows=[]; per=[]; months=[]; ledgers=[]
    for vol_name,v_spec in VOLUME.items():
        for atr_name,a_spec in VOLATILITY.items():
            for tp in TP:
                t=replay_variant(events,stops,minute,v_spec,a_spec,tp)
                if len(t):
                    t["volume_filter"]=vol_name
                    t["volatility_filter"]=atr_name
                    t["target_pct"]=round(tp*100,2)
                    t["period"]=t.month_ist.map(period_for_month)
                    ledgers.append(t)
                complete=t[t.month_ist<"2026-11"] if len(t) else t
                complete_stats=stats(complete)
                month_sums=(complete.groupby("month_ist").net_pts.sum()
                            if len(complete) else pd.Series(dtype=float))
                fullmonths=base.MONTHS
                pnl=[float(month_sums.get(m,0.0)) for m in fullmonths]
                out=dict(volume_filter=vol_name,volatility_filter=atr_name,
                         tp_pct=round(tp*100,2),
                         positive_months=sum(a>0 for a in pnl),
                         negative_months=sum(a<0 for a in pnl),
                         flat_months=sum(a==0 for a in pnl),
                         **complete_stats)
                rows.append(out)
                for partition in PERIODS:
                    sub=(complete[complete.period==partition] if len(complete) else complete)
                    s=stats(sub)
                    range_months=range(0,12) if partition=="2025_train" else (
                        range(12,18) if partition=="2026_H1_check" else range(18,22))
                    pp=[pnl[k] for k in range_months]
                    per.append(dict(volume_filter=vol_name,
                                    volatility_filter=atr_name,
                                    tp_pct=round(tp*100,2),
                                    period=partition,
                                    positive_months=sum(x>0 for x in pp),
                                    flat_months=sum(x==0 for x in pp),
                                    **s))
                for m,n in zip(fullmonths,pnl):
                    months.append(dict(volume_filter=vol_name,
                                       volatility_filter=atr_name,
                                       tp_pct=round(tp*100,2),
                                       month_ist=m,net_pts=round(n,2),
                                       trades=int((complete.month_ist==m).sum())
                                           if len(complete) else 0))
    summary=pd.DataFrame(rows)
    split=pd.DataFrame(per)
    monthly=pd.DataFrame(months)

    # Integrity: deliberately include the original baseline in this grid.
    audit=[]
    for p, (n,w,net) in BASELINE.items():
        x=summary[(summary.volume_filter=="vol_off")&
                  (summary.volatility_filter=="atr_off")&
                  (abs(summary.tp_pct-p)<1e-8)]
        assert len(x)==1,(p,"missing baseline")
        a=x.iloc[0]
        same=(int(a.trades)==n and int(a.wins)==w and abs(float(a.net_pts)-net)<0.1)
        audit.append(dict(tp_pct=p,expected_trades=n,found_trades=int(a.trades),
                          expected_wins=w,found_wins=int(a.wins),
                          expected_net_pts=net,found_net_pts=float(a.net_pts),
                          passes=same))
        if not same:
            raise AssertionError(f"Baseline parity FAILED: {audit[-1]}")
    print("BASELINE_PARITY",json.dumps(audit))

    summary.to_csv(OUT/"all_210_combinations.csv",index=False)
    split.to_csv(OUT/"all_splits.csv",index=False)
    monthly.to_csv(OUT/"monthly_22_months.csv.gz",index=False,compression="gzip")
    pd.concat(ledgers,ignore_index=True).to_csv(
        OUT/"trade_ledger.csv.gz",index=False,compression="gzip")
    (OUT/"baseline_parity.json").write_text(json.dumps(audit,indent=2)+"\n")

    # Rank on 2025 ONLY, assess separately on full Jan-Oct 2026. Include
    # a sample-size gate, to avoid boasting about thin filtered signals.
    tr=split[(split.period=="2025_train")][[
        "volume_filter","volatility_filter","tp_pct","trades",
        "wins","net_pts","net_avg_pts","pf","positive_months"]].rename(
            columns={x:x+"_2025" for x in [
                "trades","wins","net_pts","net_avg_pts","pf","positive_months"]})
    score=summary.merge(tr,on=["volume_filter","volatility_filter","tp_pct"])
    score["eligible_rank"]=score.trades_2025.ge(30)&score.trades.ge(60)
    ranked=score[score.eligible_rank].sort_values(
             ["net_avg_pts_2025","trades_2025"],ascending=[False,False])
    ranked.to_csv(OUT/"ranked_by_2025_only.csv",index=False)
    positive=summary[summary.net_pts>0].sort_values("net_pts",ascending=False)
    profitable_monthly=summary.sort_values(
        ["positive_months","net_pts"],ascending=[False,False])
    quality=dict(data_source="Delta Exchange India BTCUSD perpetual 1m",
       archived_months=len(files), observed_minutes=len(minute), complete_15m=len(h),
       sample_start=str(minute.index[0]),sample_end=str(minute.index[-1]),
       touch_event_candidates_15m=len(events),stop_close_events_15m=len(stops),
       months="22 complete IST Jan 2025–Oct 2026, November excluded",
       universe="Long-only Supertrend ATR(10) factor3, one fill per bullish cycle",
       volume_ratio="last CLOSED 15m vol / mean 20 older complete 15m vols",
       atr14_pct="last CLOSED 15m Wilder ATR14 / close * 100",
       atr14_relative="last CLOSED ATR14 / mean previous 50 ATR14 values",
       filter_timing="all at start of candidate 15m bar; latest fully closed 15m",
       target_values_pct=[100*x for x in TP],
       combinations=len(rows),
       assumptions=["Causal 1m touch limit first hit, gap at open no price improvement invented",
                    "No favorable same-entry-1m TP",
                    "15m close stop next 1m open",
                    "Per-side taker fee 0.05% + 18% GST",
                    "5 BTCUSD price points adverse slippage on each side",
                    "Funding, spread/queue, leverage and liquidation not modeled",
                    "BTC price-points per 1 BTC-equivalent hypothetical trade only",
                    "No independent untouched OOS; choosing top filter invites selection bias"],
       baseline_parity_passed=True)
    (OUT/"quality.json").write_text(json.dumps(quality,indent=2)+"\n")
    cols=["volume_filter","volatility_filter","tp_pct","trades","wins",
         "win_rate_pct","net_pts","net_avg_pts","pf","positive_months",
         "flat_months","max_drawdown_pts"]
    report=[
        "# BTCUSD 15m bullish Supertrend line touch: volume × ATR filters",
        "",
        "Full 210-configuration search; complete IST Jan 2025–Oct 2026.",
        "See NOVELTY_CHECK.md and quality.json. All P&L is **price-point equivalent**,",
        "not account $ or return; fees/GST/slippage estimated, funding excluded.",
        "Data selection, filtering, and 1m execution strictly causal at order placement.",
        "",
        "## Unfiltered baseline parity — PASS",
        pd.DataFrame(audit).to_markdown(index=False),
        "",
        "## Top 2025-trained configurations (>=30 2025, >=60 total trades)",
        ranked[cols+["net_avg_pts_2025","trades_2025"]].head(20).to_markdown(index=False),
        "",
        "## Most profitable entire 22-month paths (descriptive ONLY, hindsight-ranked)",
        summary.sort_values("net_pts",ascending=False)[cols].head(20).to_markdown(index=False),
        "",
        "## Configurations with positive total net P&L",
        f"{len(positive)} / {len(summary)}",
        "",
        "## Most positive complete months",
        profitable_monthly[cols].head(15).to_markdown(index=False),
        "",
        "## Interpretation and warnings",
        "- A support-line touch can be a continued breakdown, not a bounce.",
        "- This tests only last COMPLETED 15m volume and volatility, not unfinished touch-bar volume.",
        "- Filters that reject early touches can allow a **later** touch in the same bullish cycle.",
        "- Gross target may be profitable while net results lose to costs.",
        "- 2025 used for screening; 2026 is research-seen, not untouched OOS.",
        "- No confidence/uncertainty or true live-limit queue position is established."
    ]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")
    print("VARIANTS",len(summary),"PROFITABLE_NET",len(positive))
    print("HINDSIGHT_TOP_10\n",summary.sort_values(
        "net_pts",ascending=False)[cols].head(10).to_string(index=False))
    print("2025_RANK_TOP_10\n",ranked[cols+["net_avg_pts_2025","trades_2025"]]
        .head(10).to_string(index=False))
    print("MONTHS_TOP\n",profitable_monthly[cols].head(10).to_string(index=False))
    print("REPORT_PATH",str(OUT/"RESEARCH_REPORT.md"))

if __name__=="__main__":
    main()
