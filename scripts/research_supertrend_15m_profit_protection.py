#!/usr/bin/env python3
"""15m ST first-support-touch: 1m fixed TP vs 10 profit-protection rules.

Full 42 causal volume/ATR filters * 3 fixed BTC-point targets *
10 profit-protection variants. OHLC ambiguities go stop-first.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd

import research_supertrend_15m_line_touch as base
import research_supertrend_15m_filter_grid as filters

OUT=Path("analysis/supertrend_15m_profit_protection_20261122")
TARGETS=(200,500,1000)
# Name, kind, trigger, protected points above raw entry, trail or step distance
MODES={
 "off":("off",0,0,0),
 "be_200":("lock",200,0,0),
 "lock_200_100":("lock",200,100,0),
 "lock_300_100":("lock",300,100,0),
 "lock_500_200":("lock",500,200,0),
 "step_200_100_plus200":("step",200,100,200),
 "trail_300_100":("trail",300,0,100),
 "trail_500_200":("trail",500,0,200),
 "trail_500_300":("trail",500,0,300),
 "trail_1000_200":("trail",1000,0,200)
}
EXPECTED_HITS={200:(782,299),500:(782,171),1000:(782,92)}
SHOW=[
 ("vol_off","atr_off"),
 ("vol_ge_1p25","atrpct_ge_0p30"),
 ("vol_ge_1p5","atrpct_ge_0p30"),
 ("vol_ge_2p0","atrpct_ge_0p30"),
 ("vol_ge_1p5","atrpct_ge_0p40"),
 ("vol_ge_2p0","atrpct_ge_0p40"),
]


def select_events(events, volume_spec, atr_spec):
    result=[]; used=None
    for cycle,bar,j,mid,line,vol,atrpct,atrrel in events:
        if used==cycle: continue
        if not filters.matches(vol,volume_spec): continue
        if not filters.volatility_match(atrpct,atrrel,atr_spec): continue
        result.append((cycle,bar,j,mid,line))
        used=cycle
    return result


def protection_series(peak, entry_mid, spec):
    kind,arm,lock,step=spec
    if kind=="off":
        return np.full(len(peak),-np.inf)
    # Peak is updated with each subsequent full 1m candle high.
    qualifying=peak>=entry_mid+arm
    if kind=="lock":
        value=np.full(len(peak),entry_mid+lock)
    elif kind=="step":
        crossed=np.floor(np.maximum(peak-entry_mid-arm,0.0)/step)
        value=entry_mid+lock+step*crossed
    elif kind=="trail":
        value=peak-step
    else:raise AssertionError(kind)
    return np.where(qualifying,value,-np.inf)


def replay(entries, stopbar, minute, target, mode):
    high=minute.high.to_numpy(float)
    low=minute.low.to_numpy(float)
    op=minute.open.to_numpy(float)
    cl=minute.close.to_numpy(float)
    times=minute.index
    records=[]
    for cycle,bar,j,mid,line in entries:
        stopidx=np.searchsorted(stopbar,bar,side="left")
        closing_bar=int(stopbar[stopidx]) if stopidx<len(stopbar) else -1
        final=(closing_bar+1)*15 if closing_bar>=0 else len(high)
        assert final>j
        start=j+1; end=min(final,len(high))
        crossed_tp=False; crossed_lock=False; ambiguity=False
        if start<end:
            highs=high[start:end]
            lows=low[start:end]
            opens=op[start:end]
            peak=np.maximum.accumulate(highs)
            proposed=protection_series(peak,mid,MODES[mode])
            target_hit=highs>=mid+target
            protect_hit=lows<=proposed
            any_hit=np.flatnonzero(target_hit|protect_hit)
        else:
            any_hit=np.empty(0,dtype=int)
        if len(any_hit):
            idx=int(any_hit[0])
            exit_j=start+idx
            if protect_hit[idx]:
                # Stop-first if TP and protection trigger in same 1m candle.
                # Treat simultaneous initial activation + stop touch as
                # protective exit; this is a pessimistic OHLC convention.
                last_peak=high[start:exit_j]
                prevpeak=np.max(last_peak) if len(last_peak) else -np.inf
                previous_stop=(
                    protection_series(np.asarray([prevpeak]),mid,
                                      MODES[mode])[0])
                next_stop=float(proposed[idx])
                ambiguity=bool(next_stop>previous_stop and
                               lows[idx]<=next_stop)
                exit_mid=float(min(opens[idx],next_stop))
                why="protective_stop"
                crossed_lock=True
            else:
                exit_mid=mid+target
                why="target"
                crossed_tp=True
        elif final<len(high):
            exit_j=final
            exit_mid=float(op[final])
            why="15m_close_stop"
        else:
            exit_j=len(high)-1
            exit_mid=float(cl[-1])
            why="data_end"
        entry_fill=mid+base.SLIP
        exit_fill=exit_mid-base.SLIP
        fee=base.FEE*(entry_fill+exit_fill)
        net=exit_fill-entry_fill-fee
        records.append(dict(
            cycle=cycle,entry_index=j,exit_index=exit_j,
            entry_utc=str(times[j]),exit_utc=str(times[exit_j]),
            entry_mid=round(float(mid),5),exit_mid=round(exit_mid,5),
            target_pts=target,mode=mode,exit_reason=why,
            ambiguity_same_bar=int(ambiguity),
            gross_pts=round(exit_mid-mid,5),fees_pts=round(fee,5),
            net_pts=round(net,5),
            hold_minutes=int(exit_j-j)))
    df=pd.DataFrame.from_records(records)
    if len(df):
        df["entry_month_ist"]=pd.to_datetime(df.entry_utc,utc=True).dt.tz_convert(
            "Asia/Kolkata").dt.strftime("%Y-%m")
        df["exit_month_ist"]=pd.to_datetime(df.exit_utc,utc=True).dt.tz_convert(
            "Asia/Kolkata").dt.strftime("%Y-%m")
    return df


def stats(t,scope,vol,atr,target,mode,months):
    # Entry-month selection reproduces earlier first-pass measurement.
    sub=(t[t.entry_month_ist.isin(months)].sort_values("entry_index")
           if len(t) else t)
    n=len(sub)
    v=sub.net_pts.to_numpy(float) if n else np.empty(0)
    win=v[v>0]; lose=v[v<=0]
    eq=np.r_[0.0,np.cumsum(v)]
    sums=(sub.groupby("exit_month_ist").net_pts.sum() if n else
          pd.Series(dtype=float))
    allmonth=np.array([float(sums.get(month,0.0)) for month in months])
    return dict(
        volume_filter=vol,volatility_filter=atr,target_pts=target,
        protection=mode,period=scope,trades=n,
        wins=len(win),losses=len(lose),
        win_rate_pct=round(100*len(win)/n,2) if n else None,
        tp_hits=int((sub.exit_reason=="target").sum()) if n else 0,
        protection_exits=int((sub.exit_reason=="protective_stop").sum()) if n else 0,
        closing_stop_exits=int((sub.exit_reason=="15m_close_stop").sum()) if n else 0,
        ambiguous_protective_exits=int(sub.ambiguity_same_bar.sum()) if n else 0,
        gross_pts=round(float(sub.gross_pts.sum()),2) if n else 0.0,
        fee_pts=round(float(sub.fees_pts.sum()),2) if n else 0.0,
        net_pts=round(float(v.sum()),2),
        avg_net_pts=round(float(v.mean()),2) if n else None,
        profit_factor=round(float(win.sum()/-lose.sum()),3)
            if len(lose) and -lose.sum()>0 else None,
        max_drawdown_pts=round(float(np.max(np.maximum.accumulate(eq)-eq)),2),
        positive_months=int((allmonth>0).sum()),
        negative_months=int((allmonth<0).sum()),
        flat_months=int((allmonth==0).sum()),
    )


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    minute,bars,files=base.load()
    st,direction=base.supertrend(bars)
    v,atrp,atrr=filters.build_features(bars)
    events,closing_bars=filters.candidate_touch_events(
        minute,bars,st,direction,v,atrp,atrr)
    print("LOADED",len(minute),"1m",len(bars),"15m",
          len(events),"touch candidates")
    assert len(TARGETS)==3 and len(MODES)==10
    variants=[]; splitrows=[]; monthly=[]; ledgers=[]; parity=[]
    for vn,vspec in filters.VOLUME.items():
        for an,aspec in filters.VOLATILITY.items():
            selected=select_events(events,vspec,aspec)
            if not selected:continue
            print("FILTER",vn,an,"SELECTED",len(selected),flush=True)
            for tp in TARGETS:
                for m in MODES:
                    trades=replay(selected,closing_bars,minute,tp,m)
                    trades["volume_filter"]=vn
                    trades["volatility_filter"]=an
                    ledgers.append(trades)
                    full=stats(trades,"22_complete_months",vn,an,tp,m,
                               base.MONTHS)
                    variants.append(full)
                    for label,mo in (
                        ("2025_reference",base.MONTHS[:12]),
                        ("2026_H1",base.MONTHS[12:18]),
                        ("2026_JulOct",base.MONTHS[18:22])):
                        splitrows.append(stats(trades,label,vn,an,tp,m,mo))
                    # P&L accounting uses exit month, including positions
                    # entering before a boundary but exiting inside the month.
                    totals=trades.groupby("exit_month_ist").agg(
                        net_pts=("net_pts","sum"),
                        wins=("net_pts",lambda x:int((x>0).sum())),
                        exits=("net_pts","count"))
                    for mo in base.MONTHS:
                        x=totals.loc[mo] if mo in totals.index else None
                        monthly.append(dict(
                            volume_filter=vn,volatility_filter=an,
                            target_pts=tp,protection=m,month_ist=mo,
                            net_pts=round(float(x.net_pts),2) if x is not None else 0.0,
                            wins=int(x.wins) if x is not None else 0,
                            exits=int(x.exits) if x is not None else 0))
                    if vn=="vol_off" and an=="atr_off" and m=="off":
                        expected_n,expected_hit=EXPECTED_HITS[tp]
                        audit={
                          "target_pts":tp,
                          "expected_trades":expected_n,
                          "found_trades":full["trades"],
                          "expected_tp_hits":expected_hit,
                          "found_tp_hits":full["tp_hits"],
                          "passed":full["trades"]==expected_n and
                            full["tp_hits"]==expected_hit
                        }
                        parity.append(audit)
                        if not audit["passed"]:
                            raise AssertionError("Baseline parity FAIL "+str(audit))
    assert len(variants)==42*3*10,len(variants)
    assert len(parity)==3 and all(x["passed"] for x in parity)
    full=pd.DataFrame(variants)
    periods=pd.DataFrame(splitrows)
    monthly=pd.DataFrame(monthly)
    full.to_csv(OUT/"all_1260_configurations.csv",index=False)
    periods.to_csv(OUT/"period_splits.csv",index=False)
    monthly.to_csv(OUT/"monthly_22_months.csv.gz",index=False,compression="gzip")
    pd.concat(ledgers,ignore_index=True).to_csv(
        OUT/"trade_ledger.csv.gz",index=False,compression="gzip")
    (OUT/"baseline_parity.json").write_text(json.dumps(parity,indent=2)+"\n")

    # 2025 is research-exposed too; treat this ranking as descriptive, not
    # independently validated parameter selection.
    train=periods[periods.period=="2025_reference"][
       ["volume_filter","volatility_filter","target_pts","protection",
        "trades","avg_net_pts","net_pts","wins"]].rename(columns={
            "trades":"trades_2025","avg_net_pts":"avg_net_pts_2025",
            "net_pts":"net_pts_2025","wins":"wins_2025"})
    rank=full.merge(train,on=[
        "volume_filter","volatility_filter","target_pts","protection"])
    eligible=rank[(rank.trades_2025>=30)&(rank.trades>=60)]
    order=eligible.sort_values(
        ["avg_net_pts_2025","trades_2025"],ascending=[False,False])
    order.to_csv(OUT/"rank_2025_reference.csv",index=False)

    cols=["volume_filter","volatility_filter","target_pts","protection",
          "trades","wins","win_rate_pct","tp_hits","protection_exits",
          "ambiguous_protective_exits","net_pts","avg_net_pts",
          "profit_factor","max_drawdown_pts","positive_months","flat_months"]
    rep=full[full.apply(lambda row:
             (row.volume_filter,row.volatility_filter) in SHOW,axis=1)]
    rep_top=rep.sort_values(
        ["net_pts","positive_months"],ascending=[False,False]).head(25)
    unfil=full[(full.volume_filter=="vol_off")&
               (full.volatility_filter=="atr_off")]
    high_volume=full[(full.volume_filter=="vol_ge_2p0")&
                     (full.volatility_filter=="atrpct_ge_0p30")]
    best=full.sort_values(
        ["net_pts","positive_months"],ascending=[False,False])
    profit=full[full.net_pts>0]
    most_months=full.sort_values(
        ["positive_months","net_pts"],ascending=[False,False])
    split_index=["volume_filter","volatility_filter","target_pts","protection"]
    eval_2026=periods[periods.period.isin(["2026_H1","2026_JulOct"])].groupby(
        split_index,as_index=False).agg({
            "trades":"sum","wins":"sum","net_pts":"sum","tp_hits":"sum",
            "protection_exits":"sum"})
    eval_2026=eval_2026.rename(columns={
            "trades":"trades_2026","wins":"wins_2026",
            "net_pts":"net_pts_2026",
            "tp_hits":"tp_hits_2026",
            "protection_exits":"protection_exits_2026"})
    ranked_2026=order.merge(eval_2026,on=split_index)
    ranked_2026.to_csv(OUT/"rank_with_2026_recheck.csv",index=False)

    q=dict(data_source="Delta Exchange India BTCUSD perpetual 1m",
        archived_partitions=len(files),minutes=len(minute),bars_15m=len(bars),
        dates="Jan 2025-Oct 2026, 22 complete IST months; Nov partial excluded",
        signals="15m Wilder Supertrend ATR10 factor3; first qualifying touch in each bullish cycle",
        filters="Volume relative 20 older complete 15m; ATR14 percent or 50-sample relative, last closed 15m only",
        targets_points=TARGETS,protection_modes=MODES,
        strategy_count=len(full),parity_200_500_1000=parity,
        costs={"taker_side":0.0005,"gst_on_fee":0.18,
               "slippage_points_each_side":base.SLIP},
        simultaneous_exit_policy="protective stop wins over fixed TP in same 1m OHLC bar",
        protective_arming_policy="using current 1m high+low; simultaneous new protection and touch resolves at stop as pessimistic assumption; count flagged in result",
        gap_policy="protective stop gap down exits at min(stop, 1m open)",
        entry_minute="No stop or favorable TP credited within entry minute",
        stop_15m="15m close below last closed bullish support or bearish flip; exit next 1m open",
        pnl_units="1 BTC-equivalent price-point PnL not dollars or return on capital",
        limitations=[
           "Intrabar OHLC cannot show true high/low ordering, especially during arming",
           "Stop-order execution/slippage approximation only; no exchange orderbook queue",
           "Funding, spread, leverage, liquidation, margin not modeled",
           "Historical dates previously researched; no untouched holdout",
           "Variants highly overlapping, best configuration suffers selection bias"])
    (OUT/"quality.json").write_text(json.dumps(q,indent=2)+"\n")
    report=[
        "# BTCUSD 15m Supertrend line-touch — 1m profit-protection comparison",
        "",
        "42 prior-closed-bar volume/ATR configurations × 3 fixed point targets "
        "× 10 profit-protection modes = **1,260 variants**.",
        "Research-only, 22 completed IST months Jan2025–Oct2026.",
        "Points are cumulative hypothetical 1BTC-equivalent price-point PnL after "
        "estimated taker fees/GST/5-point slippage each side; funding, "
        "book/depth and liquidation excluded.",
        "",
        "## Baseline parity (200/500/1000 first passage) — all PASS",
        pd.DataFrame(parity).to_markdown(index=False),"",
        "## Unfiltered: compare fixed targets × profit protection",
        unfil[cols].to_markdown(index=False),"",
        "## High volume >=2x, ATR14 percent >=0.30%",
        high_volume[cols].to_markdown(index=False),"",
        "## Top 25 complete-history totals, hindsight only",
        best[cols].head(25).to_markdown(index=False),"",
        f"## Positive net P&L combinations: {len(profit)} / {len(full)}",
        "",
        "## Most positive months (22 total)",
        most_months[cols].head(15).to_markdown(index=False),"",
        "## Highest-ranked by 2025 average net/trade (>=30 trades in 2025, >=60 total)",
        ranked_2026[cols+["avg_net_pts_2025","trades_2025","net_pts_2025",
                          "net_pts_2026","trades_2026"]].head(20).to_markdown(index=False),"",
        "## Representative best 25 configurations",
        rep_top[cols].to_markdown(index=False),"",
        "## Protect mode semantics",
        *[f"- **{name}**: {spec}" for name,spec in MODES.items()],
        "",
        "## Execution caveats",
        "- Protective stops ratchet with 1m highs, and are hit if the 1m low is "
        "at or below the ratcheted stop. If target/stop are both reached in "
        "the same 1m, count **protective stop first**.",
        "- New arming and protective stop hit in one 1m is **ambiguous**; "
        "a pessimistic stop-first outcome is chosen and flagged, but tick data "
        "could differ; do not call results live-executable.",
        "- Closing-stop remains next 1m open after 15m bearish/breach close.",
        "- Protected breakeven measured from pre-slippage entry; fee/GST and "
        "entry/exit slip mean protected BE is **net negative**.",
        "- One trade per bullish Supertrend cycle; a filtered-out touch may "
        "be followed by a later qualifying touch in the same cycle.",
        "- All 2026 history has been research-exposed; no untouched OOS."
    ]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")
    print("PARITY",json.dumps(parity),flush=True)
    print("CONFIGURATIONS",len(full),"PROFITABLE",len(profit),flush=True)
    print("UNFILTERED",unfil[cols].to_string(index=False),flush=True)
    print("HIGHVOL_ATR030",high_volume[cols].to_string(index=False),flush=True)
    print("BEST_ALL",best[cols].head(20).to_string(index=False),flush=True)
    print("BEST_2025_TRAIN",ranked_2026[cols+[
          "avg_net_pts_2025","net_pts_2025","net_pts_2026","trades_2026"]
          ].head(15).to_string(index=False),flush=True)
    print("REPORT_PATH",OUT/"RESEARCH_REPORT.md")

if __name__=="__main__":
    main()
