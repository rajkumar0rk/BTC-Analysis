#!/usr/bin/env python3
"""Test LONG entry on second GREEN 15m candle after ST touch or bullish flip.

Original touch vs (A) next green after touch, (B) next green after ST flip.
Market entries at open of 3rd candle; no lookahead. 1m hard stops / TPs.
Jan2025–Oct2026 complete IST months. Research only, no untouched OOS.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd

import research_supertrend_15m_line_touch as base
import research_supertrend_15m_filter_grid as fil
import research_supertrend_15m_profit_protection as protect
import research_supertrend_15m_12_rr as risk
import research_supertrend_15m_200point as passage

OUT=Path("analysis/supertrend_15m_second_green_20261122")
KINDS=("touch_immediate","second_green_after_touch","second_green_after_flip")
PROTECT=("off","be_200","lock_500_200")
TARGETS=(100,200,500,1000)
SELECTED_FILTERS=[
    ("vol_off","atr_off"),
    ("vol_ge_1p25","atrpct_ge_0p30"),
    ("vol_ge_1p5","atrpct_ge_0p30"),
    ("vol_ge_2p0","atrpct_ge_0p30"),
    ("vol_ge_2p0","atrpct_ge_0p40"),
]
assert set(PROTECT).issubset(set(protect.MODES))
assert len(risk.RATIOS)==12

def after_touch_green(selected,bar15,trend,stops,opening):
    """Candle1 = touch bar. Candle2 = NEXT bar green, both confirmed bullish.
       Enter only at 3rd 15m bar start, after candle2 completes.
    """
    out=[]
    bopen=bar15.open.to_numpy(float)
    bclose=bar15.close.to_numpy(float)
    stopset=set(int(s) for s in stops)
    for cycle,bar,j,mid,line in selected:
        bar=int(bar); nxt=bar+1; third=bar+2
        if third>=len(bar15):continue
        if trend[bar]!=-1 or trend[nxt]!=-1:continue
        if bar in stopset or nxt in stopset:continue
        if not bclose[nxt]>bopen[nxt]:continue
        ej=third*15
        out.append((cycle,third,ej,float(opening[ej]),float(line)))
    assert len({e[0] for e in out})==len(out), "one confirm per bull cycle"
    return out

def after_flip_green(bar15,trend,volume,atr_pct,atr_rel,vs,ats,
                     stops,opening):
    """Candle1 = confirmed ST bullish flip. Candle2 = next 15m green,
       current bullish ST state; enter 3rd bar at opening.
       Filter features evaluated at completion of flip candle, causally.
    """
    out=[]
    o=bar15.open.to_numpy(float);c=bar15.close.to_numpy(float)
    stopset=set(int(s) for s in stops)
    cycle=0
    for i in range(1,len(bar15)-2):
        if trend[i]!=-1 or trend[i-1]==-1:continue
        cycle+=1
        nxt=i+1;third=i+2
        if trend[nxt]!=-1 or nxt in stopset:continue
        if not c[nxt]>o[nxt]:continue
        if not fil.matches(volume[i],vs):continue
        if not fil.volatility_match(atr_pct[i],atr_rel[i],ats):continue
        ej=third*15
        out.append((cycle,third,ej,float(opening[ej]),float("nan")))
    return out

def market_replay(selected,stops,arrays,slpts,tppts,mode,month_by_minute):
    """Market buy at 3rd-bar first-minute OPEN, 1m stop-first if ambiguous.

    Unlike a resting touch limit fill during a bar, both favorable high and
    adverse low of the ENTRY minute happen after its OPEN and are eligible.
    """
    high,low,op,cl,times=arrays
    n=len(high)
    rows=[]
    activation=int(protect.MODES[mode][1])
    for cycle,bar,j,mid,line in selected:
        hard=mid-slpts
        tp=mid+tppts
        kstop=np.searchsorted(stops,bar,side="left")
        closebar=int(stops[kstop]) if kstop<len(stops) else -1
        end=min((closebar+1)*15,n) if closebar>=0 else n
        if end<=j:
            raise AssertionError("Stop bar precedes market entry")
        peak=mid
        protect_stop=-np.inf
        exit_index=-1;end_mid=np.nan;reason="";ambiguous=0
        for k in range(j,end):
            working=max(hard,protect_stop)
            if low[k]<=working:
                exit_index=k
                end_mid=float(min(op[k],working))
                reason=("profit_protect_existing" if protect_stop>hard
                        else "hard_stop")
                ambiguous=int(high[k]>=tp)
                break
            new_peak=max(peak,float(high[k]))
            next_prot=max(protect_stop,
                          risk.protection_at_peak(new_peak,mid,mode))
            target_hit=high[k]>=tp
            new_prot_hit=(next_prot>working and low[k]<=next_prot)
            if target_hit and tppts<=activation:
                new_prot_hit=False
            if new_prot_hit:
                exit_index=k
                end_mid=float(next_prot)
                reason="profit_protect_new_same_minute"
                ambiguous=1
                break
            if target_hit:
                exit_index=k
                end_mid=float(tp)
                reason="take_profit"
                break
            peak=new_peak
            protect_stop=next_prot
        if exit_index<0:
            if end<n:
                exit_index=end
                end_mid=float(op[end])
                reason="15m_close_stop"
            else:
                exit_index=n-1
                end_mid=float(cl[-1])
                reason="data_end"
        fill=mid+base.SLIP
        xfill=end_mid-base.SLIP
        fee=base.FEE*(fill+xfill)
        net=xfill-fill-fee
        rows.append(dict(
            cycle=cycle,entry_index=j,exit_index=exit_index,
            month_ist=month_by_minute[j],
            sl_points=slpts,tp_points=tppts,protection=mode,
            entry_mid=round(mid,5),exit_mid=round(end_mid,5),
            reason=reason,ambiguous=ambiguous,
            gross_pts=round(end_mid-mid,5),fee_pts=round(fee,5),
            net_pts=round(net,5),holding_minutes=int(exit_index-j)))
    return pd.DataFrame(rows)

def first_passage(entries,stops,high,market_entry,months_by_min):
    """Unprotected gross 1m favorable excursion before original 15m close stop."""
    results=[]
    n=len(high)
    for target in TARGETS:
        total=hits=0
        partitions={p:[0,0] for p in base.MONTHS}
        for cycle,bar,j,mid,line in entries:
            month=months_by_min[j]
            if month not in partitions:continue
            stopidx=np.searchsorted(stops,bar,side="left")
            sb=int(stops[stopidx]) if stopidx<len(stops) else -1
            stopmin=(sb+1)*15 if sb>=0 else n
            start=j if market_entry else j+1
            # Market entry at minute OPEN precedes its observed high,
            # whereas buy limit touch can occur after that same-minute high.
            reach=bool(np.any(high[start:min(stopmin,n)]>=mid+target))
            total+=1
            hits+=int(reach)
            partitions[month][0]+=1
            partitions[month][1]+=int(reach)
        results.append(dict(target_pts=target,trades=total,hits=hits,
                 hit_rate_pct=round(100*hits/total,2) if total else None,
                 monthly=partitions))
    return results

def microtests():
    # green only AFTER bar 1 touch; third candle open is first legal fill.
    idx=pd.date_range("2025-01-01",periods=6,freq="15min",tz="UTC")
    b=pd.DataFrame({"open":[100,100,100,100,100,100],
           "close":[99,101,101,101,100,100]},index=idx)
    trend=np.array([-1,-1,-1,-1,-1,-1],dtype=int)
    o=np.arange(90,dtype=float)+100
    signals=[(1,0,8,100.,99.)]
    c=after_touch_green(signals,b,trend,np.array([],dtype=int),o)
    assert len(c)==1 and c[0][2]==30 and c[0][3]==o[30]
    b.loc[idx[1],"close"]=99
    assert not after_touch_green(signals,b,trend,np.array([],dtype=int),o)
    # for market OPEN fill, a 1m high can legally hit immediate target.
    times=pd.date_range("2025-01-01",periods=75,freq="min",tz="UTC")
    hi=np.full(75,1000.,float); lo=np.full(75,1000.,float)
    op=np.full(75,1000.,float);cl=np.full(75,1000.,float)
    hi[30]=1200
    months=np.array(["2025-01"]*75)
    x=market_replay([(1,2,30,1000.,np.nan)],np.array([],dtype=int),
         (hi,lo,op,cl,times),100,100,"off",months)
    assert x.reason.iloc[0]=="take_profit"
    lo[30]=850.
    x=market_replay([(1,2,30,1000.,np.nan)],np.array([],dtype=int),
         (hi,lo,op,cl,times),100,100,"off",months)
    assert x.reason.iloc[0]=="hard_stop" and x.net_pts.iloc[0]<0
    print("MICROTESTS_PASS",flush=True)

def main():
    microtests()
    OUT.mkdir(parents=True,exist_ok=True)
    minute,bar15,files=base.load()
    st,trend=base.supertrend(bar15)
    vol,atr_pct,atr_rel=fil.build_features(bar15)
    events,stopbars=fil.candidate_touch_events(
        minute,bar15,st,trend,vol,atr_pct,atr_rel)
    high=minute.high.to_numpy(float)
    opening=minute.open.to_numpy(float)
    low=minute.low.to_numpy(float)
    close=minute.close.to_numpy(float)
    arr=(high,low,opening,close,minute.index)
    months_by_min=minute.index.tz_convert("Asia/Kolkata").strftime("%Y-%m").to_numpy()
    headline=[];splits=[];monthly=[];hits=[];trade_ledger=[]
    cohort_rows=[]

    for vn,vs in fil.VOLUME.items():
        for an,ats in fil.VOLATILITY.items():
            touch=protect.select_events(events,vs,ats)
            second=after_touch_green(touch,bar15,trend,stopbars,opening)
            flip=after_flip_green(bar15,trend,vol,atr_pct,atr_rel,
                                  vs,ats,stopbars,opening)
            selected=dict(zip(KINDS,[touch,second,flip]))
            for kind,entry in selected.items():
                for p in first_passage(entry,stopbars,high,
                                      kind!="touch_immediate",months_by_min):
                    m=p.pop("monthly")
                    hits.append(dict(entry_type=kind,vol_filter=vn,
                        atr_filter=an,**p))
                    for month,(n,h) in m.items():
                        cohort_rows.append(dict(
                            entry_type=kind,vol_filter=vn,atr_filter=an,
                            target_pts=p["target_pts"],month_ist=month,
                            trades=n,hits=h))
                for sl,tp in risk.RATIOS:
                    for pmode in PROTECT:
                        if kind=="touch_immediate":
                            trades=risk.replay_entries(entry,stopbars,arr,
                                                  sl*100,tp*100,pmode)
                        else:
                            trades=market_replay(entry,stopbars,arr,
                                   sl*100,tp*100,pmode,months_by_min)
                        if not len(trades):continue
                        trades["entry_type"]=kind
                        trades["vol_filter"]=vn
                        trades["atr_filter"]=an
                        trades["rr"]=f"{sl}:{tp}"
                        # Use complete months defined by previous experiments.
                        all22=risk.summary(trades,vn,an,sl,tp,pmode,
                                          "all22",base.MONTHS)
                        headline.append(dict(entry_type=kind,**all22))
                        for period,mths in [
                           ("2025",base.MONTHS[:12]),
                           ("2026_H1",base.MONTHS[12:18]),
                           ("2026_JulOct",base.MONTHS[18:22])]:
                            splits.append(dict(entry_type=kind,
                                **risk.summary(trades,vn,an,sl,tp,pmode,
                                               period,mths)))
                        groups=trades.groupby("month_ist").agg(
                            net_pts=("net_pts","sum"),trades=("net_pts","count"),
                            wins=("net_pts",lambda x:int((x>0).sum())))
                        for mo in base.MONTHS:
                            u=groups.loc[mo] if mo in groups.index else None
                            monthly.append(dict(
                                entry_type=kind,vol_filter=vn,atr_filter=an,
                                rr=f"{sl}:{tp}",protection=pmode,month_ist=mo,
                                trades=int(u.trades) if u is not None else 0,
                                wins=int(u.wins) if u is not None else 0,
                                net_pts=round(float(u.net_pts),2) if u is not None else 0.))
                        if (vn,an) in SELECTED_FILTERS and pmode=="off":
                            trade_ledger.append(trades[trades.month_ist.isin(
                                    base.MONTHS)].copy())
            print("DONE",vn,an,"original",len(touch),
                 "touch_next_green",len(second),"flip_next_green",len(flip),
                 flush=True)

    sums=pd.DataFrame(headline)
    splitdf=pd.DataFrame(splits)
    mon=pd.DataFrame(monthly)
    hp=pd.DataFrame(hits)
    monthpass=pd.DataFrame(cohort_rows)
    expected=42*len(KINDS)*len(risk.RATIOS)*len(PROTECT)
    assert len(sums)==expected,(len(sums),expected)
    assert len(hp)==42*len(KINDS)*len(TARGETS)
    t0=hp[(hp.entry_type=="touch_immediate")&
          (hp.vol_filter=="vol_off")&(hp.atr_filter=="atr_off")]
    for target,count in [(100,430),(200,299),(500,171),(1000,92)]:
        s=t0[t0.target_pts==target].iloc[0]
        assert s.trades==782 and s.hits==count,(
            "First-passage baseline mismatch",target,s.to_dict())
    orig=sums[(sums.entry_type=="touch_immediate")&
        (sums.vol_filter=="vol_off")&(sums.atr_filter=="atr_off")&
        (sums.rr=="1:1")&(sums.protection=="off")].iloc[0]
    assert orig.trades==782 and orig.tp_exits==325 and abs(
         orig.net_pts-(-94369.90))<0.2,orig.to_dict()
    assert int((sums.net_pts>0).sum())>=0

    sums.to_csv(OUT/"all_4536_combinations.csv",index=False)
    splitdf.to_csv(OUT/"2025_2026_splits.csv",index=False)
    mon.to_csv(OUT/"monthly_22_months.csv.gz",index=False,compression="gzip")
    hp.to_csv(OUT/"all_first_passage_counts.csv",index=False)
    monthpass.to_csv(OUT/"first_passage_monthly_counts.csv",index=False)
    pd.concat(trade_ledger,ignore_index=True).to_csv(
        OUT/"selected_trade_ledgers.csv.gz",index=False,compression="gzip")

    unfil=sums[(sums.vol_filter=="vol_off")&
               (sums.atr_filter=="atr_off")&(sums.protection=="off")]
    frequent=sums[(sums.vol_filter=="vol_ge_2p0")&
                (sums.atr_filter=="atrpct_ge_0p30")&
                (sums.protection=="off")]
    sortedbest=sums.sort_values(["net_pts","profitable_months"],
                                ascending=[False,False])
    key=["entry_type","vol_filter","atr_filter","rr","protection",
       "trades","wins","win_rate_pct","tp_exits","sl_exits",
       "supertrend_close_exits","net_pts","net_per_trade_pts",
       "pf","max_dd_pts","profitable_months","flat_months"]

    # Benchmark identical RR risk/TP under each entry model, not cumulative
    # total only: delayed confirmation trades a smaller count of signals.
    benchmark=sums[(sums.vol_filter=="vol_off")&
          (sums.atr_filter=="atr_off")&(sums.protection=="off")]
    order=pd.CategoricalDtype(KINDS,ordered=True)
    benchmark=benchmark.copy()
    benchmark["entry_type"]=benchmark.entry_type.astype(order)
    benchmark["rr"]=pd.Categorical(benchmark.rr,
        [f"{a}:{b}" for a,b in risk.RATIOS],ordered=True)
    benchmark=benchmark.sort_values(["rr","entry_type"])
    benchmark.to_csv(OUT/"unfiltered_12_rr_entry_comparison.csv",index=False)

    # 2025 ranking purely descriptive; 2026 not untouched OOS.
    t2025=splitdf[splitdf.period=="2025"][[
        "entry_type","vol_filter","atr_filter","rr","protection",
        "trades","net_pts","net_per_trade_pts"]].rename(columns={
        "trades":"trades_2025","net_pts":"net_pts_2025",
        "net_per_trade_pts":"mean_net_2025"})
    ranking=sums.merge(t2025,on=[
        "entry_type","vol_filter","atr_filter","rr","protection"])
    ranking=ranking[(ranking.trades_2025>=30)&(ranking.trades>=60)].sort_values(
        ["mean_net_2025","trades_2025"],ascending=[False,False])
    ranking.to_csv(OUT/"rank_2025_only.csv",index=False)

    q=dict(
        source="Delta Exchange India BTCUSD perpetual archived 1m candles",
        observed_1m=len(minute),observed_15m=len(bar15),
        completed_ist_months="2025-01 through 2026-10",
        entry_types={
            "touch_immediate":"First 1m low crossing previous complete bullish Supertrend support, buy limit hypothetical mid",
            "second_green_after_touch":"First support touch 15m candle as candle1; next candle green and ST stays bullish; market entry candle3 1m open",
            "second_green_after_flip":"First bullish flip 15m candle as candle1; next candle green and ST stays bullish; market entry candle3 1m open"},
        hard_sl_tp="12 user SL:TP pairs in 100-point units, stop-first if both hit 1m",
        protections=list(PROTECT),filters="42 causal volume/ATR regimes from previous experiments",
        result_rows=len(sums),first_passage_rows=len(hp),
        prior_parity="First-passage +100/+200/+500/+1000=430/299/171/92 and 1:1 TP exits 325 all PASS",
        cost="0.05% taker per side × 1.18 GST, 5 adverse price points per side",
        limitations=[
            "No tick-level ordering within 1m bar; choose pessimistic stop-first",
            "Original support-touch limit assumed filled upon 1m low touch (no orderbook queue)",
            "Delayed entries modeled as market at first-minute open, adverse slip 5 points",
            "No funding, spread, actual orderbook fill, margin, liquidation or leverage",
            "No independent historical holdout; hindsight filter selection risk",
            "Long only; user short mirror not assessed",
            "Entry signal frequency changes; compare avg points/trade as well as totals"])
    (OUT/"quality.json").write_text(json.dumps(q,indent=2)+"\n")
    topline=sums.groupby("entry_type",as_index=False).agg(
        configurations=("net_pts","size"),
        profitable=("net_pts",lambda x:int((x>0).sum())),
        best_net_pts=("net_pts","max"))
    selectedhp=hp[(hp.vol_filter=="vol_off")&(hp.atr_filter=="atr_off")].sort_values(
        ["target_pts","entry_type"])
    report=[
        "# BTCUSD 15m Supertrend: second GREEN candle confirmation entry",
        "",
        "BTCUSD perpetual archived 1m Jan2025–Oct2026; 15m Supertrend(10,3) bullish setup.",
        "Original touch vs GREEN next 15m after touch vs GREEN next 15m after bullish flip.",
        "Enter confirmed second green at THIRD candle open. Never assume second",
        "candle green before it closes. One trade maximum per ST bullish cycle.",
        "12 user 100-point risk:reward pairs × 42 volume/ATR filters × 3 entry",
        "methods × 3 protective exit modes = **4,536 configurations**.",
        "",
        "## Baseline parity: PASS",
        "Original touch gross +100/+200/+500/+1000 first-passages = 430/299/171/92,",
        "and 100/100 fixed RR TP fills 325/782, net −94,369.9 pts.",
        "",
        "## Unfiltered — how many reach gross +100/200/500/1000 before 15m closing stop?",
        selectedhp[["entry_type","target_pts","trades","hits","hit_rate_pct"]]
           .to_markdown(index=False),"",
        "## Unfiltered — 12 user fixed SL/TP pairs, no protection",
        benchmark[key].to_markdown(index=False),"",
        "## Strong vol>=2x ATR>=0.30%, 12 RRs × 3 entry modes, no protection",
        frequent[key].to_markdown(index=False),"",
        "## Full 4,536-case outcome totals by entry mode",
        topline.to_markdown(index=False),"",
        "## Top 25 full-series net configurations, *hindsight* only",
        sortedbest[key].head(25).to_markdown(index=False),"",
        "## Top 2025 reference rank (>=30 2025 and >=60 full trades; descriptive)",
        ranking[key+["trades_2025","net_pts_2025","mean_net_2025"]]
           .head(15).to_markdown(index=False),"",
        "## Execution methodology / limitations",
        "- First touch and second-candle-green use same initial touch signal;",
        "  if next 15m candle NOT green or ST/closing support invalidates, skip cycle.",
        "- Bullish flip version is a separate entry logic, not directly the same",
        "  touch cohort. All require closed bar confirmation, third bar open fill.",
        "- For market entry at third 15m bar open, 1m high and low on ENTRY",
        "  minute are both eligible; when simultaneous, hard stop first.",
        "- For resting buy limit touch, entry-minute adverse stop eligible but",
        "  favorable target not credited due uncertain OHLC path.",
        "- Volume/ATR features taken only from bars completed by decision time.",
        "- Stop/target measured in *raw points from assumed entry midpoint*;",
        "  negative/positive net after fee+GST and 5 points adverse slippage each side.",
        "- 15m closing-stop remains a secondary exit at next 1m open.",
        "- The first-passage +100 count has no hard 100-point SL; separate",
        "  fixed 1:1 TP exits ask a different question.",
        "- 2025 and 2026 data have already been exposed to strategy research;",
        "  no untouched validation; results do not establish real execution profits.",
        "- All historical PnL hypothetical 1 BTC-equivalent price points;",
        "  funding, leverage, liquidation and orderbook depth not modeled."]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")
    print("BASELINE_PARITY_PASS",flush=True)
    print("FULL_RESULT_TYPES\n"+topline.to_string(index=False),flush=True)
    print("UNFILTERED_FIRST_PASSAGES\n"+selectedhp.to_string(index=False),flush=True)
    print("UNFILTERED_12RR\n"+benchmark[key].to_string(index=False),flush=True)
    print("HINDSIGHT_BEST\n"+sortedbest[key].head(15).to_string(index=False),flush=True)
    print("REPORT_PATH",OUT/"RESEARCH_REPORT.md",flush=True)

if __name__=="__main__":
    main()
