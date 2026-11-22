#!/usr/bin/env python3
"""12 fixed 100-point-unit SL:TP tuples × 42 ST15m filters × 10 protect modes.

Research ONLY. 1m conservative stop-first replay. 15m close stop retained.
"""
from pathlib import Path
import gzip
import csv
import json
import numpy as np
import pandas as pd

import research_supertrend_15m_line_touch as base
import research_supertrend_15m_filter_grid as filters
import research_supertrend_15m_profit_protection as prot

OUT=Path("analysis/supertrend_15m_12_rr_20261122")
RATIOS=[(1,1),(1,2),(1,3),(1,4),
        (2,2),(2,4),(2,6),(2,8),
        (3,3),(3,6),(3,9),(3,12)]
assert len(RATIOS)==12
REPRESENTATIVE=[
    ("vol_off","atr_off"),
    ("vol_ge_1p25","atrpct_ge_0p30"),
    ("vol_ge_1p5","atrpct_ge_0p30"),
    ("vol_ge_2p0","atrpct_ge_0p30"),
    ("vol_ge_2p0","atrpct_ge_0p40"),
    ("vol_le_0p8","atrpct_ge_0p40"),
]


def protection_at_peak(peak,entry_mid,mode):
    kind,arm,lock,step=prot.MODES[mode]
    if kind=="off" or peak-entry_mid<arm:return -np.inf
    if kind=="lock":return entry_mid+lock
    if kind=="step":
        return entry_mid+lock+step*int(
            max(peak-entry_mid-arm,0)//step)
    if kind=="trail":return peak-step
    raise ValueError(mode)


def replay_entries(selected, stops, arrays, slpoints,tppoints,mode):
    high,low,opening,closing,times=arrays
    results=[]
    n=len(high)
    for cycle,bar,j,mid,line in selected:
        fixed_stop=mid-slpoints
        tp=mid+tppoints
        firstclosing=np.searchsorted(stops,bar,side="left")
        next_stop_bar=int(stops[firstclosing]) if firstclosing<len(stops) else -1
        end=(next_stop_bar+1)*15 if next_stop_bar>=0 else n
        assert end>j
        end=min(end,n)
        exitj=-1; exit_mid=np.nan
        reason=""; ambiguous=0
        peak=mid
        protective=-np.inf
        protective_trigger=int(prot.MODES[mode][1])

        # The resting buy limit was filled when the market moved down to
        # support. If the entry minute ALSO reaches the adverse hard SL,
        # that SL must not be ignored: it is necessarily reached no earlier
        # than that descending touch (or the bar's open gap fill).
        if low[j]<=fixed_stop:
            exitj=j
            exit_mid=float(fixed_stop)
            reason="hard_stop_same_entry_minute"
        else:
            for k in range(j+1,end):
                pre=max(fixed_stop,protective)
                # Price crossing a previously working SL before an intrabar
                # TP is treated pessimistically as SL-first.
                if low[k]<=pre:
                    exitj=k
                    exit_mid=float(min(opening[k],pre))
                    reason=("profit_protect_existing" if protective>fixed_stop
                            else "hard_stop")
                    ambiguous=int(high[k]>=tp)
                    break
                new_peak=max(peak,high[k])
                candidate=max(protective,protection_at_peak(new_peak,mid,mode))
                target_hit=(high[k]>=tp)
                newly_armed=(candidate>pre and low[k]<=candidate)
                if target_hit and tppoints<=protective_trigger:
                    # A standing TP below (or exactly at) the protection
                    # trigger necessarily precedes a NEW profit protection.
                    newly_armed=False
                if newly_armed:
                    exitj=k
                    exit_mid=float(candidate)
                    reason="profit_protect_new_same_minute"
                    ambiguous=1  # high/low ordering not knowable from OHLC
                    break
                if target_hit:
                    exitj=k
                    exit_mid=float(tp)
                    reason="take_profit"
                    break
                peak=new_peak
                protective=candidate
        if exitj<0:
            if end<n:
                exitj=end
                exit_mid=float(opening[end])
                reason="15m_close_stop"
            else:
                exitj=n-1
                exit_mid=float(closing[-1])
                reason="data_end"
        enterfill=mid+base.SLIP
        exitfill=exit_mid-base.SLIP
        fee=base.FEE*(enterfill+exitfill)
        net=exitfill-enterfill-fee
        results.append(dict(
            cycle=cycle,entry_index=j,exit_index=exitj,
            entry_utc=str(times[j]),exit_utc=str(times[exitj]),
            month_ist=times[j].tz_convert("Asia/Kolkata").strftime("%Y-%m"),
            sl_points=slpoints,tp_points=tppoints,protection=mode,
            entry_mid=round(float(mid),5),exit_mid=round(float(exit_mid),5),
            reason=reason,ambiguous=ambiguous,
            gross_pts=round(float(exit_mid-mid),5),
            fee_pts=round(float(fee),5),
            net_pts=round(float(net),5),
            holding_minutes=exitj-j))
    return pd.DataFrame(results)


def summary(frame,vs,aspec,r1,r2,mode,scope,months):
    a=frame[frame.month_ist.isin(months)].sort_values("entry_index")
    n=len(a)
    v=a.net_pts.to_numpy(float) if n else np.empty(0)
    wins=v[v>0];loss=v[v<=0]
    eq=np.r_[0.0,np.cumsum(v)]
    bymonth=(a.groupby("month_ist").net_pts.sum()
             if n else pd.Series(dtype=float))
    monthvals=[float(bymonth.get(m,0.0)) for m in months]
    return dict(
        vol_filter=vs,atr_filter=aspec,rr=f"{r1}:{r2}",
        sl_pts=r1*100,tp_pts=r2*100,protection=mode,period=scope,
        trades=n,wins=len(wins),
        win_rate_pct=round(100*len(wins)/n,2) if n else None,
        tp_exits=int((a.reason=="take_profit").sum()) if n else 0,
        sl_exits=int(a.reason.str.startswith("hard_stop").sum()) if n else 0,
        protection_exits=int(a.reason.str.startswith("profit_protect").sum()) if n else 0,
        supertrend_close_exits=int((a.reason=="15m_close_stop").sum()) if n else 0,
        ambiguous_exits=int(a.ambiguous.sum()) if n else 0,
        gross_pts=round(float(a.gross_pts.sum()),2) if n else 0.,
        fees_pts=round(float(a.fee_pts.sum()),2) if n else 0.,
        net_pts=round(float(v.sum()),2) if n else 0.,
        net_per_trade_pts=round(float(v.mean()),2) if n else None,
        pf=round(float(wins.sum()/-loss.sum()),3) if len(loss) and -loss.sum()>0 else None,
        max_dd_pts=round(float(np.max(np.maximum.accumulate(eq)-eq)),2),
        profitable_months=sum(x>0 for x in monthvals),
        losing_months=sum(x<0 for x in monthvals),
        flat_months=sum(x==0 for x in monthvals))


def selftest():
    # Hard stop hit in entry minute MUST beat entry-minute TP (which isn't
    # observable). Also assert a new protection may not beat a nearer TP.
    times=pd.date_range("2025-01-01",periods=32,freq="min",tz="UTC")
    op=np.full(32,1000.);h=np.full(32,1000.);lo=np.full(32,1000.)
    c=np.full(32,1000.)
    sel=[(1,0,0,1000.,990.)]
    lo[0]=890.;h[0]=1500.
    a=replay_entries(sel,np.array([],dtype=int),(h,lo,op,c,times),
                     100,200,"off")
    assert a.iloc[0].reason=="hard_stop_same_entry_minute" and a.iloc[0].net_pts<0
    lo[0]=1000.;h[0]=1000.
    h[1]=1300.;lo[1]=900.
    a=replay_entries(sel,np.array([],dtype=int),(h,lo,op,c,times),
                     400,200,"lock_200_100")
    assert a.iloc[0].reason=="take_profit", a.iloc[0].to_dict()
    a=replay_entries(sel,np.array([],dtype=int),(h,lo,op,c,times),
                     400,500,"lock_200_100")
    assert a.iloc[0].reason=="profit_protect_new_same_minute",a.iloc[0].to_dict()
    # Existing protective stop gap fill must use low open, not stop price.
    h[1]=1250.;lo[1]=1175.;op[1]=1200.;c[1]=1200.
    h[2]=1190.;lo[2]=1000.;op[2]=1050.
    a=replay_entries(sel,np.array([],dtype=int),(h,lo,op,c,times),
                     400,500,"lock_200_100")
    assert a.iloc[0].reason.startswith("profit_protect"),a.iloc[0].to_dict()
    print("BUILTIN_OHLC_ORDERING_TESTS_PASS",flush=True)


def main():
    selftest()
    OUT.mkdir(parents=True,exist_ok=True)
    m,b,files=base.load()
    line,direction=base.supertrend(b)
    v,atrpct,atrrel=filters.build_features(b)
    candidates,stops=filters.candidate_touch_events(
        m,b,line,direction,v,atrpct,atrrel)
    arrays=(m.high.to_numpy(float),m.low.to_numpy(float),
            m.open.to_numpy(float),m.close.to_numpy(float),m.index)
    fullmonths=base.MONTHS
    assert len(fullmonths)==22 and len(filters.VOLUME)==6 and len(filters.VOLATILITY)==7
    rows=[];splits=[];monthly=[]
    legs=OUT/"all_trade_ledger.csv.gz"
    head=None; written=0
    with gzip.open(legs,"wt",newline="",compresslevel=4) as ff:
        writer=None
        for vname,vspec in filters.VOLUME.items():
            for aname,aspec in filters.VOLATILITY.items():
                entries=prot.select_events(candidates,vspec,aspec)
                # The previous backtest runner implements select_events and
                # supplies the exact initial entries for all 42 filters.
                assert len(entries)>0
                for slunits,tpunits in RATIOS:
                    for name in prot.MODES:
                        trades=replay_entries(entries,stops,arrays,
                            100*slunits,100*tpunits,name)
                        trades["vol_filter"]=vname
                        trades["atr_filter"]=aname
                        trades["rr"]=f"{slunits}:{tpunits}"
                        if writer is None:
                            writer=csv.DictWriter(ff,fieldnames=list(trades.columns))
                            writer.writeheader()
                        writer.writerows(trades.to_dict("records"))
                        written+=len(trades)
                        rows.append(summary(trades,vname,aname,slunits,tpunits,
                                            name,"all22",fullmonths))
                        for label,mo in [
                            ("2025_reference",fullmonths[:12]),
                            ("2026_H1",fullmonths[12:18]),
                            ("2026_JulOct",fullmonths[18:22])]:
                            splits.append(summary(trades,vname,aname,
                                          slunits,tpunits,name,label,mo))
                        grouped=trades.groupby("month_ist").agg(
                            net_pts=("net_pts","sum"),trades=("net_pts","count"),
                            wins=("net_pts",lambda x:int((x>0).sum())))
                        for mo in fullmonths:
                            x=grouped.loc[mo] if mo in grouped.index else None
                            monthly.append(dict(
                                vol_filter=vname,atr_filter=aname,
                                rr=f"{slunits}:{tpunits}",
                                sl_pts=slunits*100,tp_pts=tpunits*100,
                                protection=name,month_ist=mo,
                                trades=int(x.trades) if x is not None else 0,
                                wins=int(x.wins) if x is not None else 0,
                                net_pts=round(float(x.net_pts),2) if x is not None else 0.0))
                print("DONE_FILTER",vname,aname,
                      "entries",len(entries),"rows",len(rows),flush=True)

    # Exclude partial Nov by entry month; any Nov exits of October entries
    # stay part of October entry-month accounting.
    frame=pd.DataFrame(rows)
    split=pd.DataFrame(splits)
    mon=pd.DataFrame(monthly)
    assert len(frame)==12*42*len(prot.MODES)==5040,len(frame)
    assert len(split)==len(frame)*3
    unfil=frame[(frame.vol_filter=="vol_off")&(frame.atr_filter=="atr_off")]
    assert unfil.trades.eq(782).all(), unfil.trades.unique()
    assert frame.groupby(["vol_filter","atr_filter","rr"]).trades.nunique().eq(1).all()
    for rr in ("1:2","2:2"):
        assert frame[(frame.vol_filter=="vol_off")&
                     (frame.atr_filter=="atr_off")&
                     (frame.rr==rr)&(frame.protection=="off")].iloc[0].tp_exits<=299

    frame.to_csv(OUT/"all_5040_configurations.csv",index=False)
    split.to_csv(OUT/"2025_2026_splits.csv",index=False)
    mon.to_csv(OUT/"monthly_22_months.csv.gz",
               index=False,compression="gzip")

    # A rank only based on 2025 (already research-exposed), with a robust
    # minimum number of trades. 2026 remains a descriptive re-check.
    train=split[split.period=="2025_reference"][
        ["vol_filter","atr_filter","rr","protection",
         "trades","net_pts","net_per_trade_pts","pf"]].rename(
        columns={"trades":"n_2025","net_pts":"net_2025",
                 "net_per_trade_pts":"avgnet_2025","pf":"pf_2025"})
    score=frame.merge(train,on=["vol_filter","atr_filter","rr","protection"])
    eligible=score[(score.n_2025>=30)&(score.trades>=60)]
    best2025=eligible.sort_values(
        ["avgnet_2025","n_2025"],ascending=[False,False])
    best2025.to_csv(OUT/"rank_2025_only.csv",index=False)

    # Comparison table: unfiltered RRs (without protection) and best
    # protection *within each RR* for two representative filters.
    allbest=[]
    for vn,an in [("vol_off","atr_off"),
                  ("vol_ge_2p0","atrpct_ge_0p30"),
                  ("vol_ge_2p0","atrpct_ge_0p40")]:
        for one,two in RATIOS:
            sub=frame[(frame.vol_filter==vn)&(frame.atr_filter==an)&
                      (frame.rr==f"{one}:{two}")]
            winner=sub.sort_values("net_pts",ascending=False).iloc[0]
            off=sub[sub.protection=="off"].iloc[0]
            allbest.append(dict(
                vol_filter=vn,atr_filter=an,rr=f"{one}:{two}",
                sl_pts=one*100,tp_pts=two*100,trades=int(off.trades),
                off_net=round(float(off.net_pts),2),
                off_winrate=round(float(off.win_rate_pct),2),
                best_protection=winner.protection,
                best_net=round(float(winner.net_pts),2),
                best_winrate=round(float(winner.win_rate_pct),2),
                improvement_pts=round(float(winner.net_pts-off.net_pts),2),
                best_pf=winner.pf,best_profitable_months=int(winner.profitable_months),
                best_ambiguous_events=int(winner.ambiguous_exits)))
    highlight=pd.DataFrame(allbest)
    highlight.to_csv(OUT/"comparison_12_rr_with_best_protection.csv",index=False)

    counts=dict(variants=len(frame),net_profitable=int((frame.net_pts>0).sum()),
                ratio_count=len(RATIOS),filter_combinations=42,
                protection_modes=len(prot.MODES),total_trade_ledger_rows=written,
                data_minutes=len(m),bar15=len(b))
    bestnet=frame.sort_values(["net_pts","profitable_months"],
            ascending=[False,False])
    bestfrequency=frame.sort_values(["profitable_months","net_pts"],
            ascending=[False,False])
    keys=["vol_filter","atr_filter","rr","protection",
          "trades","wins","win_rate_pct","tp_exits",
          "sl_exits","protection_exits","supertrend_close_exits",
          "ambiguous_exits","net_pts","net_per_trade_pts","pf",
          "max_dd_pts","profitable_months","flat_months"]
    report=[
        "# BTCUSD 15m Supertrend touch: 12 stop:target point tuples",
        "",
        "Interpretation: 1 unit = **100 BTC price points**, e.g. 1:3 is",
        "hard SL 100 pts / TP 300 pts; 3:12 = SL 300 / TP 1200.",
        "15m closing-stop retained as a secondary exit. 1m hard SL including entry",
        "minute adverse move; 1m TP only after entry minute (conservative).",
        "42 causal volume/ATR filter combinations × 12 ratios × 10 profit protection",
        "= **5,040 configurations**; **22 complete IST entry months Jan2025–Oct2026**.",
        "Research only; previously examined history, no untouched OOS.",
        "",
        "## Quality/summary",json.dumps(counts,indent=2),"",
        "## No filter — 12 RRs, fixed TP and point stop, no profit protection",
        unfil[unfil.protection=="off"][keys].to_markdown(index=False),"",
        "## No filter — best ex-post protection per RR",
        highlight[(highlight.vol_filter=="vol_off")][[
            "rr","sl_pts","tp_pts","trades","off_net","best_protection",
            "best_net","improvement_pts","best_profitable_months",
            "best_ambiguous_events"]].to_markdown(index=False),"",
        "## Volume >=2x and ATR >=0.30% — best ex-post protection per RR",
        highlight[(highlight.vol_filter=="vol_ge_2p0")&
             (highlight.atr_filter=="atrpct_ge_0p30")][[
             "rr","trades","off_net","best_protection","best_net",
             "improvement_pts","best_profitable_months"]].to_markdown(index=False),"",
        "## Volume >=2x and ATR >=0.40% — best ex-post protection per RR",
        highlight[(highlight.vol_filter=="vol_ge_2p0")&
             (highlight.atr_filter=="atrpct_ge_0p40")][[
             "rr","trades","off_net","best_protection","best_net",
             "improvement_pts","best_profitable_months"]].to_markdown(index=False),"",
        f"## Full-history positive-net combinations: {int((frame.net_pts>0).sum())}/5040",
        "",
        "## Top 25 by full-history net (hindsight-ranked; NOT validation)",
        bestnet[keys].head(25).to_markdown(index=False),"",
        "## Top 15 by positive months (note flat/no-trade months)",
        bestfrequency[keys].head(15).to_markdown(index=False),"",
        "## Ranked by 2025 average P&L per trade only (>=30 2025 trades; >=60 total)",
        best2025[keys+["n_2025","net_2025","avgnet_2025"]].head(20).to_markdown(index=False),"",
        "## Execution / limitations",
        "- Entries are identical across all 12 RR configurations for a given filter;",
        "  there is no second entry within the same bullish Supertrend cycle.",
        "- OHLC cannot establish same-minute high-low sequence. Existing hard and",
        "  protective stops win over targets when both touched in a single 1m.",
        "- A newly armed protective stop and its touch within a 1m is assumed",
        "  high-then-low and filled at stop, marked *ambiguous*.",
        "- A take-profit at or below a protection activation is executed before",
        "  a protection stop activated that minute; the latter cannot preempt TP.",
        "- Entry minute low below the hard point SL is **counted as a stop**.",
        "- Entry minute favorable high is ignored because it might predate fill.",
        "- No bid/ask queue, spread, funding, margin or liquidation modeling;",
        "  0.05% taker per side, GST 18% on fees, 5 BTC points/slippage per side.",
        "- P&L is 1BTC-equivalent BTC **price points**, not leveraged account profit.",
        "- Monthly attribution is IST **entry month** so total and monthly sum",
        "  agree; previous reports used exit months. Don't compare month counts",
        "  without this adjustment.",
        "- All date partitions have previously been used for strategy research.",
        "- Filtered configurations heavily overlap; never sum their trade counts.",
        ""
    ]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report))
    (OUT/"quality.json").write_text(json.dumps(dict(
        **counts,ratios=[f"{a}:{b}" for a,b in RATIOS],
        ratio_unit_points=100,complete_months="2025-01 through 2026-10",
        entry="first qualified bullish 15m Supertrend(10,3) line touch per cycle",
        fixed_hard_stop="raw entry midpoint - absolute risk points, 1m monitor including entry minute",
        tp="raw entry midpoint + absolute target points, 1m monitor after entry minute",
        alternate_stop="15m close under prior closed bullish support or bearish reversal, next 1m open",
        filters="previous complete 15m volume/ATR only",
        secondary_exits="10 protection modes from previous study",
        simultaneous_ohlc_policy="active stops pessimistically before TP; newly active protection assumes high then low, flags ambiguity",
        fees="0.05% each side plus 18% GST on fee",
        adverse_slippage_points_each_side=base.SLIP,
        month_pnl_allocation="IST entry month to preserve complete Jan2025-Oct2026 cohort sum",
        limitations=["OHLC ambiguity for same-minute stop/target and new activation",
                     "Missing exchange order book fill uncertainty",
                     "No funding, leverage, liquidation, spread or capital sizing",
                     "No independent out-of-sample historical data",
                     "Hindsight selection bias across 5040 variants"]),
        indent=2)+"\n")
    print("SUMMARY",json.dumps(counts),flush=True)
    print("ALL_12_UNFILTERED_NO_PROTECT\n"+unfil[unfil.protection=="off"][
          keys].to_string(index=False),flush=True)
    print("UNFILTERED_12_RR_BEST_PROTECTION\n"+
          highlight[highlight.vol_filter=="vol_off"].to_string(index=False),flush=True)
    print("BEST_25\n"+bestnet[keys].head(25).to_string(index=False),flush=True)
    print("REPORT",OUT/"RESEARCH_REPORT.md",flush=True)

if __name__=="__main__":
    main()
