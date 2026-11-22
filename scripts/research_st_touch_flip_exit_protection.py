#!/usr/bin/env python3
"""Causal 1m execution replay: exits and profit protection for BTC ST portfolio.

Original:
 - BTCUSD 15m ST(10,3) Line Touch after second green,
   Vol >= 1, ATRpct >= .20, SL .75%, TP 1.5%,
   last COMPLETE 1h close > EMA20 AND 1h EMA20 rising.
 - BTCUSD 15m ST(10,3) Bullish Flip next green,
   Vol <= .8, ATRpct >= .20, SL 3%, TP .5%,
   last COMPLETE 1h RSI14 >= 50.
 - ST close exit ON, 1m stop-first OHLC, one open position,
   one position per bullish ST cycle.
 - Fee + GST and 5 BTC price-point slippage on both entry/exit.

This study changes EXIT parameters only (SL, TP, protection, timed exit).
Trailing/lock stops can activate ONLY from prior COMPLETED 1m highs, no
same-minute future-high activation. Gaps through stops exit at next open.
Same 1m bar touching fixed stop and target -> pessimistic stop-first.

This is fully retrospective and NO genuine out-of-sample validation.
"""
from pathlib import Path
from functools import lru_cache
import json
import numpy as np
import pandas as pd
import research_supertrend_15m_line_touch as base
import research_supertrend_15m_filter_grid as feat
import research_st_three_best_combined_portfolio as port
import research_st_touch075_flip_lowvol_combination as fixed
import research_st_touch_flip_causal_regime_filters as htf
import research_st_touch_flip_reduce_loss_months as study
import research_second_green_percent_rr_scenarios as rr

OUT=Path("analysis/st_touch_flip_exit_protection_20261122")
MONTHS=tuple(base.MONTHS)
DEFAULT_T=(.75,1.5,"off",0.,0.,0)
DEFAULT_F=(3.,.5,"off",0.,0.,0)
# Side tuple: stop%, target%, mode, arm%, lock-or-trail%, max minutes
# Modes "lock" and "trail" are NOT armed until AFTER a completed 1m
# candle confirms a favorable high. "off" uses original stop/TP only.
def side(sl,tp,mode="off",arm=0.,value=0.,timecap=0):
    return (float(sl),float(tp),mode,float(arm),float(value),int(timecap))

def variant_list():
    d={"baseline":(DEFAULT_T,DEFAULT_F)}
    for new_sl in (.35,.50,.60,1.,1.25):
        d[f"touch_SL_{new_sl}"]=(side(new_sl,1.5),DEFAULT_F)
    for new_sl in (.75,1.,1.5,2.,2.5):
        d[f"flip_SL_{new_sl}"]=(DEFAULT_T,side(new_sl,.5))
    for new_tp in (.75,1.,1.25,1.75,2.,2.25,2.5,3.):
        d[f"touch_TP_{new_tp}"]=(side(.75,new_tp),DEFAULT_F)
    for new_tp in (.3,.35,.4,.6,.75,1.):
        d[f"flip_TP_{new_tp}"]=(DEFAULT_T,side(3.,new_tp))
    # Coarse low-parameter stop-level and target sensitivity on BOTH.
    for ts in (.5,.75,1.):
      for fs in (1.,1.5,2.,3.):
        d[f"touchSL_{ts}_flipSL_{fs}"]=(side(ts,1.5),side(fs,.5))
    for tp in (1.,1.5,2.):
      for fp in (.35,.5,.75):
        d[f"touchTP_{tp}_flipTP_{fp}"]=(side(.75,tp),side(3.,fp))
    # Long-side lock after movement, conservative next-minute activation.
    for arm in (.4,.6,.8,1.):
      for val in (.1,.15,.2,.3,.4):
        if val>=arm:continue
        d[f"touch_lock_{arm}_{val}"]=(
            side(.75,1.5,"lock",arm,val),DEFAULT_F)
    # Flip TP is only .5% so only small arms (<TP) are possible.
    for arm in (.15,.2,.25,.35,.4):
      for val in (.05,.1,.15,.2,.25,.3):
        if val>=arm:continue
        d[f"flip_lock_{arm}_{val}"]=(
            DEFAULT_T,side(3.,.5,"lock",arm,val))
    # Trailing: "value" is DISTANCE in % of entry fill from peak
    for arm in (.4,.6,.8,1.):
      for trail in (.25,.4,.6,.8):
        if trail>=arm+0.4:continue
        d[f"touch_trail_{arm}_{trail}"]=(
            side(.75,1.5,"trail",arm,trail),DEFAULT_F)
    for arm in (.15,.25,.35):
      for trail in (.12,.2,.3):
        d[f"flip_trail_{arm}_{trail}"]=(
            DEFAULT_T,side(3.,.5,"trail",arm,trail))
    # Modest ALL-STRATEGY protection, not 2 independent optimizations.
    for ts,fs in ((.5,1.5),(.5,2.),(.6,1.5),(.75,1.5)):
      d[f"both_SL_touch_{ts}_flip_{fs}"]=(
         side(ts,1.5),side(fs,.5))
    for a,l in ((.6,.15),(.8,.2),(1.,.3)):
      for fa,fl in ((.2,.1),(.3,.15)):
        d[f"both_locks_touch_{a}_{l}_flip_{fa}_{fl}"]=(
           side(.75,1.5,"lock",a,l),
           side(3.,.5,"lock",fa,fl))
    for tcap in (180,360,720,1440):
        d[f"touch_timecap_{tcap}"]=(side(.75,1.5,timecap=tcap),DEFAULT_F)
        d[f"flip_timecap_{tcap}"]=(DEFAULT_T,side(3.,.5,timecap=tcap))
    for tcap,fcap in ((360,360),(720,360),(720,720),(1440,720)):
        d[f"both_timecap_{tcap}_{fcap}"]=(
          side(.75,1.5,timecap=tcap),side(3.,.5,timecap=fcap))
    return d

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    rr.configure_grid()
    port.SPECS=fixed.COHORTS
    minute,bars,files=base.load()
    st,trend=base.supertrend(bars)
    vol,ap,ar=feat.build_features(bars)
    events,stopbars=feat.candidate_touch_events(minute,bars,st,trend,vol,ap,ar)
    signals=port.decode_signals(minute,bars,trend,vol,ap,ar,events,stopbars)
    raw=port.compute_candidates(minute,trend,stopbars,signals)
    assert len(raw)==150
    gate=htf.features(bars,trend)
    indices=raw.entry_bar.to_numpy(int)
    is_touch=(raw.strategy=="line_touch").to_numpy()
    is_flip=~is_touch
    mask=((is_touch&gate["1h_above_ema20_and_rising"].to_numpy(bool)[indices])|
      (is_flip&gate["1h_rsi50"].to_numpy(bool)[indices]))
    candidates=raw[mask].copy().reset_index(drop=True)
    assert len(candidates)==87,(len(candidates),"unexpected filtered candidates")
    high=minute.high.to_numpy(float)
    low=minute.low.to_numpy(float)
    op=minute.open.to_numpy(float)
    close=minute.close.to_numpy(float)
    n=len(minute)
    months=minute.index.tz_convert("Asia/Kolkata").strftime("%Y-%m").to_numpy()
    contexts=[]
    for v in candidates.itertuples():
        j=int(v.entry_idx);bar=int(v.entry_bar)
        k=np.searchsorted(stopbars,bar,side="left")
        stend=min((int(stopbars[k])+1)*15,n) if k<len(stopbars) else n
        assert stend>j
        # Fixed, precomputed 1-minute OHLC for this signal's entire
        # *originally valid* bullish Supertrend period.
        highs=high[j:stend]
        prevpeak=np.r_[-np.inf,np.maximum.accumulate(highs[:-1])]
        contexts.append(dict(j=j,stend=stend,prevpeak=prevpeak,
            open=op[j:stend],high=highs,low=low[j:stend],
            mid=float(v.entry_mid),entryfill=float(v.entry_mid)+base.SLIP,
            base_row=v))
    assert len(contexts)==len(candidates)
    @lru_cache(maxsize=None)
    def replay(rowid,params):
        sl,tp,mode,arm,val,cap=params
        ctx=contexts[rowid]
        j,stend=ctx["j"],ctx["stend"]
        end=min(stend,j+cap) if cap else stend
        length=end-j
        assert length>0
        entry=ctx["entryfill"]
        static_stop=entry*(1.-sl/100.)
        target=entry*(1.+tp/100.)
        h=ctx["high"][:length]
        l=ctx["low"][:length]
        o=ctx["open"][:length]
        upper=ctx["prevpeak"][:length]
        if mode=="off":
            active=np.full(length,static_stop)
        else:
            qualified=upper>=entry*(1.+arm/100.)
            if mode=="lock":
                protected=np.full(length,entry*(1.+val/100.))
            elif mode=="trail":
                protected=upper-entry*(val/100.)
            else:raise AssertionError(mode)
            active=np.where(qualified,np.maximum(static_stop,protected),
                            static_stop)
        # Even if the price gaps through, SL fills at worse minute OPEN.
        stopped=l<=active
        targeted=h>=target
        indices=np.flatnonzero(stopped|targeted)
        if len(indices):
            off=int(indices[0])
            exitidx=j+off
            if stopped[off]:
                endmid=float(min(o[off],active[off]))
                why=("protective_stop" if active[off]>static_stop+1e-7
                     else "percent_stop_loss")
            else:
                endmid=float(target)
                why="percent_take_profit"
            collision=int(stopped[off] and targeted[off])
        else:
            if end<n:
                exitidx=end
                endmid=float(op[end])
                why="time_cap" if end<stend else "original_15m_supertrend_close"
            else:
                exitidx=n-1
                endmid=float(close[-1])
                why="archive_end_close"
            collision=0
        assert j<=exitidx<n,(rowid,exitidx,j,n)
        exitfill=endmid-base.SLIP
        fee=base.FEE*(entry+exitfill)
        net=exitfill-entry-fee
        return exitidx,endmid,net,fee,why,collision

    # Mandatory replay parity on original source trades, before scoring
    # ANY modification. Compare exact fills, reasons, exit index and net.
    diffs=[]
    for i,v in enumerate(candidates.itertuples()):
        params=DEFAULT_T if v.strategy=="line_touch" else DEFAULT_F
        xi,mid,net,fee,reason,col=replay(i,params)
        if xi!=v.exit_idx or abs(mid-v.exit_mid)>0.00005 or abs(net-v.net_pts)>0.0002 or reason!=v.reason:
            diffs.append((int(v.Index),v.strategy,v.exit_idx,xi,
                          v.exit_mid,mid,v.net_pts,net,v.reason,reason))
    assert not diffs,("Original baseline execution parity FAILED",diffs[:6])
    print("EXACT_1MIN_BASELINE_TRADE_PARITY_PASS",len(candidates),flush=True)
    def ledger_for(params_touch,params_flip):
        records=[]
        for i,v in enumerate(candidates.itertuples()):
            z=params_touch if v.strategy=="line_touch" else params_flip
            exitidx,mid,net,fee,reason,col=replay(i,z)
            d=v._asdict()
            d.update(exit_idx=exitidx,exit_utc=str(minute.index[exitidx]),
              exit_month_ist=str(months[exitidx]),
              exit_mid=mid,exit_fill=mid-base.SLIP,
              net_pts=net,fee_pts=fee,reason=reason,collision=col,
              win=int(net>0),holding_minutes=exitidx-int(v.entry_idx),
              sl_pct=z[0],tp_pct=z[1])
            records.append(d)
        return pd.DataFrame(records).sort_values(["entry_idx","strategy"]).reset_index(drop=True)

    variants=variant_list()
    baseline=ledger_for(DEFAULT_T,DEFAULT_F)
    selected,_=port.portfolio(baseline,("line_touch","bullish_flip"),
                              ("line_touch","bullish_flip"),True)
    baseline_stats=study.evaluate(selected)
    assert len(selected)==85
    assert abs(baseline_stats["y2025_net_pts"]-13719.58)<.025
    assert abs(baseline_stats["y2026_net_pts"]-4243.57)<.025
    assert baseline_stats["all22_winning_months"]==17
    print("EXACT_EXCLUSIVE_PORTFOLIO_PARITY_PASS",baseline_stats,flush=True)
    rows=[]
    kept={}
    for k,(name,(t,f)) in enumerate(variants.items()):
        ledger=ledger_for(t,f)
        chosen,blocked=port.portfolio(ledger,("line_touch","bullish_flip"),
                                    ("line_touch","bullish_flip"),True)
        d=study.evaluate(chosen)
        rows.append(dict(profile=name,
             touch_SL_pct=t[0],touch_TP_pct=t[1],
             touch_mode=t[2],touch_arm_pct=t[3],
             touch_lock_or_trail_pct=t[4],touch_timecap_minutes=t[5],
             flip_SL_pct=f[0],flip_TP_pct=f[1],
             flip_mode=f[2],flip_arm_pct=f[3],
             flip_lock_or_trail_pct=f[4],flip_timecap_minutes=f[5],
             entry_candidates=len(ledger),
             blocked_overlap=blocked["blocked_overlaps"],
             blocked_cycle=blocked["blocked_one_cycle"],
             exit_stop_exits=int((chosen.reason=="percent_stop_loss").sum()),
             exit_protect_exits=int((chosen.reason=="protective_stop").sum()),
             exit_target_exits=int((chosen.reason=="percent_take_profit").sum()),
             exit_st_exits=int((chosen.reason=="original_15m_supertrend_close").sum()),
             exit_timecap_exits=int((chosen.reason=="time_cap").sum()),
             ambiguous_bar_exits=int(chosen.collision.sum()),
             **d))
        if k%25==0:
            print("EXITS_CHECKED",k+1,"of",len(variants),flush=True)
    tab=pd.DataFrame(rows)
    assert len(tab)==len(variants)
    main=tab[tab.profile=="baseline"].iloc[0]
    assert main["all22_net_pts"]==17963.15
    assert main["all22_winning_months"]==17
    # Rank the 2025-only development selection: 2026 is evaluation,
    # NOT pristine OOS because 2026 was already seen in earlier research.
    tab["train_2025_ok"]=(
      (tab.y2025_net_pts>0)&(tab.y2025_trade_count>=25)&
      (tab.y2025_winning_months>=8)&
      (tab.y2025_first_net_pts>0)&(tab.y2025_second_net_pts>0))
    tab["activity_ok"]=(
       (tab.y2025_trade_count>=25)&(tab.y2026_trade_count>=20)&
       (tab.y2025_winning_months+tab.y2025_losing_months>=10)&
       (tab.y2026_winning_months+tab.y2026_losing_months>=8))
    tab["positive_both_years"]=(tab.y2025_net_pts>0)&(tab.y2026_net_pts>0)
    train=tab[tab.train_2025_ok].sort_values(
       ["y2025_winning_months","y2025_net_pts"],
       ascending=[False,False])
    diagnostic=tab[(tab.activity_ok)&(tab.positive_both_years)].sort_values(
       ["all22_winning_months","y2026_winning_months",
        "y2026_net_pts","all22_net_pts"],ascending=[False]*4)
    stable=diagnostic[(diagnostic.y2026_first_net_pts>0)&
                      (diagnostic.y2026_late_net_pts>0)&
                      (diagnostic.y2025_first_net_pts>0)&
                      (diagnostic.y2025_second_net_pts>0)]
    tab.to_csv(OUT/"all_exit_and_profit_protection_scenarios.csv",index=False)
    train.to_csv(OUT/"ranked_2025_only_development.csv",index=False)
    diagnostic.to_csv(OUT/"retrospective_month_consistency_NOT_OOS.csv",index=False)
    stable.to_csv(OUT/"positive_four_timeblocks_EXPLORATORY.csv",index=False)
    focus=list(dict.fromkeys(["baseline"]+
       train.profile.head(2).tolist()+
       diagnostic.profile.head(6).tolist()))
    for name in focus:
        a,b=variants[name]
        l=ledger_for(a,b)
        picked,_=port.portfolio(l,("line_touch","bullish_flip"),
                                 ("line_touch","bullish_flip"),True)
        kept[name]=picked
    fullmonthly=[];fullledger=[]
    for name,tr in kept.items():
        mm=port.month_table(tr,minute,name)
        mm["profile"]=name
        fullmonthly.append(mm)
        tmp=tr.copy();tmp["profile"]=name
        fullledger.append(tmp)
    pd.concat(fullmonthly,ignore_index=True).to_csv(
      OUT/"focus_profiles_monthly.csv",index=False)
    pd.concat(fullledger,ignore_index=True).to_csv(
      OUT/"focus_profiles_trade_ledgers.csv.gz",compression="gzip",index=False)
    columns=["profile","touch_SL_pct","touch_TP_pct","touch_mode",
        "touch_arm_pct","touch_lock_or_trail_pct","touch_timecap_minutes",
        "flip_SL_pct","flip_TP_pct","flip_mode","flip_arm_pct",
        "flip_lock_or_trail_pct","flip_timecap_minutes",
        "y2025_net_pts","y2026_net_pts",
        "y2025_winning_months","y2026_winning_months",
        "y2025_losing_months","y2026_losing_months",
        "y2025_trade_count","y2026_trade_count",
        "y2026_first_net_pts","y2026_late_net_pts",
        "all22_net_pts","all22_winning_months",
        "max_closed_trade_drawdown_pts",
        "exit_protect_exits","exit_timecap_exits"]
    report=[
      "# BTCUSD ST Touch + Flip: new exit & profit-protection research",
      "",
      "Original positive 17/22 months strategy reproduced EXACTLY by",
      "per-signal 1-minute OHLC entry+exit parity AND exclusive portfolio.",
      "Touch 1H above & rising EMA20; Flip 1H RSI14>=50. Original",
      "ST(10,3), filters, one-position, one-per-cycle remain intact.",
      "",
      "## Baseline and best exploratory candidates",
      tab[tab.profile.isin(focus)][columns].to_markdown(index=False),
      "",
      "## Selection using 2025 only (development), 2026 evaluated",
      train[columns].head(18).to_markdown(index=False),
      "",
      "## Highest historical 22-month consistency - RETROSPECTIVE NOT OOS",
      diagnostic[columns].head(25).to_markdown(index=False),
      "",
      "## Four time blocks individually positive - retrospective",
      stable[columns].head(18).to_markdown(index=False),
      "",
      "## Method",
      "All percent SL/TP levels computed from simulated BUY entry fill;",
      "entry +5 points, exit -5 points slippage, fee .05% each way",
      "and 18% GST. Prior-minute highs ONLY activate locks/trails",
      "on the following 1-minute bar; same candle SL/TP hit is SL first.",
      "Original 15-minute ST close-stop exits at the NEXT minute OPEN.",
      "Timecaps exit next minute open when elapsed timer is reached.",
      "",
      "## Caveats",
      "These and prior settings tested 2025-2026 repeatedly,",
      "so results are IN-SAMPLE and selection overfits easily.",
      "2025-only ranked candidates are not fully independent on 2026",
      "because their underlying base signals were already selected",
      "with 2026 information. Funding/leverage/liquidation/order-book",
      "slippage/latency NOT modeled; points per 1 BTC equivalent."
    ]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")
    qual={
      "run":"BTC ST Touch+Flip exit/protection causal 1m grid",
      "number_variants":len(variants),
      "baseline_signal_parity_passed":len(candidates),
      "baseline_portfolio_parity_passed":True,
      "base_net_points":float(main.all22_net_pts),
      "base_winning_months":int(main.all22_winning_months),
      "train_2025_qualified":len(train),
      "retrospective_positive_both_years_activity":len(diagnostic),
      "retrospective_positive_four_timeblocks":len(stable),
      "one_open_position":True,"one_trade_per_ST_cycle":True,
      "profit_lock_activation":"previous COMPLETED minute HIGH only",
      "sl_and_tp_same_minute":"SL first",
      "actual_realized_exit_month":True,
      "funding_and_liquidation_modeled":False,
      "independent_out_of_sample":False,
      "historical_period":"Jan2025 to Oct2026",
      "focus_profiles":focus}
    (OUT/"quality.json").write_text(json.dumps(qual,indent=2)+"\n")
    print("SUCCESS_EXIT_GRID",len(tab),flush=True)
    print("2025_ONLY_TOP\n"+train[columns].head(10).to_string(index=False),flush=True)
    print("RETROSPECTIVE_TOP\n"+diagnostic[columns].head(10).to_string(index=False),flush=True)
    print("FOUR_BLOCKS_TOP\n"+stable[columns].head(8).to_string(index=False),flush=True)

if __name__=="__main__":
    main()
