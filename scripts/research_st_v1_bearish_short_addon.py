#!/usr/bin/env python3
"""Independent bearish SHORT supplement while freezing BOTH V1.0 LONG legs.

EXACT locked Line Touch and Bullish Flip trades are reproduced, unchanged.
SHORT trades are allowed only in bearish 15-minute Supertrend cycles, with
a causal second-red confirmation. Bullish cycles and original core trades
are never reoptimized, modified, replaced, or excluded.

All net PnL on exit-month IST, 1m stop-first, 0.05% per-side taker +
18% GST, 5 BTC points per-side slippage. Trade PnL normalized to 1 BTC
equivalent, not leveraged account return. SHORT position margin,
liquidation, funding, depth and latency are not modeled.

This is a RETROSPECTIVE exploratory experiment on already viewed data.
A resulting 18/22 is NOT independent out-of-sample evidence.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import research_supertrend_15m_line_touch as base
import research_supertrend_15m_filter_grid as feat
import research_st_three_best_combined_portfolio as port
import research_st_touch075_flip_lowvol_combination as original
import research_st_touch_flip_causal_regime_filters as htf
import research_st_preserve_all_profitable_month_pnl as locked
import research_second_green_percent_rr_scenarios as rr

OUT=Path("analysis/st_v1_bearish_short_addon_preserve_both_20261124")
MONTHS=tuple(base.MONTHS)
SLS=(.35,.5,.75,1.,1.5)
TPS=(.3,.5,.75,1.,1.5,2.)
VOLUME={"ge1":("ge",1.),"ge1p25":("ge",1.25),
        "le0p8":("le",.8),"off":("off",0.)}
ATRPCT=(.2,.3,.4)
HTF=("off","1h_bear_ema20","1h_bear_rsi50","4h_bear_ema20","1h_4h_bear_ema20")
SOURCE=("bearish_flip","bearish_line_touch","both")
def net_month(ledger,month):
    return float(ledger.loc[ledger.exit_month_ist==month,"net_pts"].sum())

def main():
    rr.configure_grid()
    port.SPECS=original.COHORTS
    OUT.mkdir(parents=True,exist_ok=True)
    minute,bars,files=base.load()
    st,trend=base.supertrend(bars)
    vol,ap,ar=feat.build_features(bars)
    events,stopbars=feat.candidate_touch_events(
        minute,bars,st,trend,vol,ap,ar)
    core_signals=port.decode_signals(
        minute,bars,trend,vol,ap,ar,events,stopbars)
    raw=port.compute_candidates(minute,trend,stopbars,core_signals)
    assert len(raw)==150
    gates=htf.features(bars,trend)
    k=raw.entry_bar.to_numpy(int)
    touch=(raw.strategy=="line_touch").to_numpy()
    eligible=((touch & gates["1h_above_ema20_and_rising"].to_numpy(bool)[k]) |
              (~touch & gates["1h_rsi50"].to_numpy(bool)[k]))
    core_raw=raw[eligible].copy().reset_index(drop=True)
    assert len(core_raw)==87
    core_all,tcount=locked.add_stopped_trade_replays(core_raw,minute,stopbars)
    core,_=port.portfolio(core_all,
         ("line_touch","bullish_flip"),("line_touch","bullish_flip"),True)
    assert len(core)==85 and core.st_cycle.is_unique
    assert abs(float(core.net_pts.sum())-19099.62)<.03
    baseline=np.array([net_month(core,x) for x in MONTHS])
    assert sum(baseline>0)==17 and sum(baseline<0)==5
    assert abs(baseline[:12].sum()-14553.35)<.03
    assert abs(baseline[12:].sum()-4546.27)<.03
    print("LOCKED_BOTH_CORE_PARITY_PASS",len(core),len(core_all),
          float(baseline.sum()),flush=True)

    # Reference locked trade ledger, compare exact original contributions.
    checkpoint=pd.read_csv(
       "analysis/st_v1_locked_monthly_by_strategy_20261122/monthly_contributions_wide.csv")
    assert len(checkpoint)==22
    for leg in ("line_touch","bullish_flip"):
       ref=checkpoint[leg].to_numpy(float)
       got=np.array([net_month(core[core.strategy==leg],m) for m in MONTHS])
       assert np.all(abs(ref-got)<.04),leg

    high=minute.high.to_numpy(float)
    low=minute.low.to_numpy(float)
    open_=minute.open.to_numpy(float)
    close=minute.close.to_numpy(float)
    nmin=len(minute)
    bopen=bars.open.to_numpy(float)
    bclose=bars.close.to_numpy(float)
    bvol=np.asarray(vol,float)
    batr=np.asarray(ap,float)
    minsmonth=minute.index.tz_convert("Asia/Kolkata").strftime("%Y-%m").to_numpy()
    cycles=np.cumsum((trend==1)&np.r_[True,trend[:-1]!=1])
    fail=np.zeros(len(bars),bool)
    for i in range(1,len(bars)):
        if trend[i-1]!=1:continue
        fail[i]=(bclose[i]>st[i-1] or trend[i]==-1)
    shortstops=np.flatnonzero(fail)
    # Only two completed-bar bearish setup families, with identical
    # third-candle-open timing; no candle's close used at its OPEN.
    rows=[]
    for i in range(15,len(bars)-2):
       nxt=i+1;third=i+2
       if trend[i]!=1 or trend[nxt]!=1:continue
       if not bclose[nxt]<bopen[nxt]:continue
       if not (minsmonth[third*15] in MONTHS):continue
       is_flip=(trend[i-1]==-1)
       # bearish ST resistance touched INSIDE signal bar i, after
       # the last completed ST line known at its start.
       is_touch=(trend[i-1]==1 and
             np.any(high[i*15:(i+1)*15]>=st[i-1]) and not fail[i])
       if not (is_flip or is_touch):continue
       if fail[nxt]:continue
       start=int(third*15)
       kstop=np.searchsorted(shortstops,third,side="left")
       end=(int(shortstops[kstop])+1)*15 if kstop<len(shortstops) else nmin
       end=min(end,nmin)
       if end<=start:continue
       cycle=int(cycles[nxt])
       assert cycle>0
       for label,flag in (("bearish_flip",is_flip),
                          ("bearish_line_touch",is_touch)):
          if not flag:continue
          measure=i if is_flip else i-1
          rows.append(dict(setup=label,entry_bar=int(third),
                entry_idx=start,st_cycle=-cycle,
                signal_vol=float(bvol[measure]),
                signal_atr_pct=float(batr[measure]),
                stop_end=end))
    short=pd.DataFrame(rows).sort_values(
         ["entry_idx","setup"]).reset_index(drop=True)
    assert len(short)>50,("Unexpectedly few SHORT candidates",len(short))
    assert ((short.st_cycle<0)).all()
    gb=short.entry_bar.to_numpy(int)
    f={
      "off":np.ones(len(short),bool),
      "1h_bear_ema20":~gates["1h_above_ema20"].to_numpy(bool)[gb],
      "1h_bear_rsi50":~gates["1h_rsi50"].to_numpy(bool)[gb],
      "4h_bear_ema20":~gates["4h_above_ema20"].to_numpy(bool)[gb],
      "1h_4h_bear_ema20":(
          (~gates["1h_above_ema20"].to_numpy(bool)[gb])&
          (~gates["4h_above_ema20"].to_numpy(bool)[gb]))}

    # Each candidate traded at third candle's OPEN (short SELL at bid).
    # Precompute earliest 1m stop/target hits for each SL and TP pair;
    # candidate paths are capped at next opposite Supertrend close.
    allreplay={}
    for i,v in enumerate(short.itertuples()):
        j=int(v.entry_idx);end=int(v.stop_end)
        hs=high[j:end];ls=low[j:end]
        assert len(hs)>0
        sell=open_[j]-base.SLIP
        maxh=np.maximum.accumulate(hs)
        minl=np.minimum.accumulate(ls)
        for sl in SLS:
          stop=sell*(1.+sl/100.)
          stopoffset=int(np.searchsorted(maxh,stop,side="left"))
          for tp in TPS:
            target=sell*(1.-tp/100.)
            tpoffset=int(np.searchsorted(-minl,-target,side="left"))
            if stopoffset<len(hs) and stopoffset<=tpoffset:
                xi=j+stopoffset
                cover_mid=float(max(open_[xi],stop))
                reason="short_stop"
            elif tpoffset<len(hs):
                xi=j+tpoffset
                cover_mid=float(target)
                reason="short_target"
            elif end<nmin:
                xi=end;cover_mid=float(open_[xi])
                reason="ST_green_closing_exit"
            else:
                xi=nmin-1;cover_mid=float(close[-1])
                reason="archive_end"
            cover=cover_mid+base.SLIP
            fees=base.FEE*(sell+cover)
            net=sell-cover-fees
            allreplay[(i,sl,tp)]=(xi,cover_mid,net,fees,reason)
    print("SHORT_CANDIDATES",len(short),"PRECOMPUTED_TRADES",
          len(allreplay),flush=True)
    results=[]; ledgers={}
    positive_ref=baseline>0
    scenarios=0
    for setup in SOURCE:
      source=(np.ones(len(short),bool) if setup=="both"
              else short.setup.to_numpy()==setup)
      for vn,(vr,vth) in VOLUME.items():
        if vr=="off":vm=np.ones(len(short),bool)
        elif vr=="ge":vm=short.signal_vol.to_numpy()>=vth
        else:vm=short.signal_vol.to_numpy()<=vth
        for atr in ATRPCT:
         av=short.signal_atr_pct.to_numpy()>=atr
         for fn in HTF:
          candidate_mask=source&vm&av&f[fn]
          selected=short[candidate_mask].copy()
          if len(selected)==0:continue
          # Deterministic first valid setup per red ST cycle.
          selected=selected.sort_values(
              ["entry_idx","setup"]).drop_duplicates("st_cycle",keep="first")
          for sl in SLS:
            for tp in TPS:
              records=[]
              for row in selected.itertuples():
                 xi,cover_mid,net,fees,why=allreplay[(int(row.Index),sl,tp)]
                 sell=float(open_[row.entry_idx]-base.SLIP)
                 records.append(dict(
                    strategy="short_addon",signal_cycle=-row.st_cycle,
                    st_cycle=int(row.st_cycle),entry_bar=int(row.entry_bar),
                    entry_idx=int(row.entry_idx),exit_idx=int(xi),
                    entry_utc=str(minute.index[row.entry_idx]),
                    exit_utc=str(minute.index[xi]),
                    entry_month_ist=str(minsmonth[row.entry_idx]),
                    exit_month_ist=str(minsmonth[xi]),
                    sl_pct=sl,tp_pct=tp,
                    entry_fill=sell,exit_fill=cover_mid+base.SLIP,
                    entry_mid=float(open_[row.entry_idx]),
                    exit_mid=cover_mid,net_pts=net,fee_pts=fees,
                    reason=why,collision=0,
                    holding_minutes=int(xi-row.entry_idx),win=int(net>0)))
              extras=pd.DataFrame(records)
              allrows=pd.concat([core,extras],ignore_index=True)
              combined,block=port.portfolio(
                 allrows,("line_touch","bullish_flip","short_addon"),
                 ("line_touch","bullish_flip","short_addon"),True)
              selected_core=combined[combined.strategy!="short_addon"]
              # If a third strategy blocks an original core position, it's
              # NOT a valid complement and must be excluded, not silently
              # credited with a substituted performance history.
              core_intact=(len(selected_core)==85 and
                   set(selected_core.entry_idx.to_numpy())==
                   set(core.entry_idx.to_numpy()))
              addons=combined[combined.strategy=="short_addon"]
              mon=np.array([net_month(combined,m) for m in MONTHS])
              losses=baseline<0
              # Require ALL 17 originally profitable months to remain at
              # least as profitable to within rounding precision.
              guard=bool((mon[positive_ref]>=baseline[positive_ref]-.035).all())
              total_guard=bool(mon.sum()>=baseline.sum()-.035)
              nprof=int(sum(mon>0.00001))
              nloss=int(sum(mon<-0.00001))
              values=combined.sort_values("exit_idx").net_pts.to_numpy(float)
              eq=np.r_[0.,np.cumsum(values)]
              maxdd=float((np.maximum.accumulate(eq)-eq).max())
              name=f"{setup}|{vn}|atr{atr}|{fn}|sl{sl}|tp{tp}"
              row=dict(config=name,setup=setup,volume=vn,
                  atr_pct=atr,htf=fn,short_sl_pct=sl,short_tp_pct=tp,
                  short_candidates=len(selected),short_executed=len(addons),
                  all_core_trades_unchanged=core_intact,
                  positive_months=nprof,losing_months=nloss,
                  newly_profitable_losing_months=int(
                      sum((baseline<0)&(mon>0))),
                  baseline_profitable_months_not_degraded=guard,
                  net_profit_not_decreased=total_guard,
                  net_2025=round(float(mon[:12].sum()),2),
                  net_2026=round(float(mon[12:].sum()),2),
                  net_all22=round(float(mon.sum()),2),
                  net_delta=round(float(mon.sum()-baseline.sum()),2),
                  max_closed_equity_drawdown=round(maxdd,2),
                  max_drawdown_not_increased=bool(maxdd<=2894.09+.04),
                  individual_core_line_touch_stays=bool(core_intact),
                  earliest_short_exit_month=str(addons.exit_month_ist.min()) if len(addons) else "")
              results.append(row)
              if(core_intact and guard and total_guard and
                 nprof>17 and maxdd<=2894.09+.04):
                  ledgers[name]=(combined,mon)
              scenarios+=1
              if scenarios%500==0:
                  print("TESTED",scenarios,flush=True)
    out=pd.DataFrame(results)
    assert len(out)>=100
    out["strict_profit_months_and_core"]=(
       out.all_core_trades_unchanged&
       out.baseline_profitable_months_not_degraded&
       out.net_profit_not_decreased)
    strict=out[out.strict_profit_months_and_core].sort_values(
      ["positive_months","net_all22"],
      ascending=[False,False])
    strict_dd=strict[strict.max_drawdown_not_increased]
    best_relaxed=out[out.all_core_trades_unchanged].sort_values(
      ["positive_months","net_all22"],ascending=[False,False])
    out.to_csv(OUT/"all_bearish_short_addon_scenarios.csv",index=False)
    strict.to_csv(OUT/"core_and_profit_months_preserved.csv",index=False)
    strict_dd.to_csv(OUT/"core_profit_months_and_drawdown_preserved.csv",
        index=False)
    best_relaxed.to_csv(OUT/"exploratory_win_months_WITH_TRADEOFFS.csv",
        index=False)
    focus=list(dict.fromkeys(["baseline"]+strict.config.head(3).tolist()+
                    strict_dd.config.head(3).tolist()+
                    best_relaxed.config.head(3).tolist()))
    monthrows=[]
    for name in focus:
      if name=="baseline":
         monthly=baseline
      else:
         c=out[out.config==name].iloc[0]
         # Calculate independently from precomputed data; avoid storing
         # every large ledger in memory.
         src=(np.ones(len(short),bool) if c.setup=="both" else
              short.setup.to_numpy()==c.setup)
         vr,vth=VOLUME[c.volume]
         vm=np.ones(len(short),bool) if vr=="off" else (
             short.signal_vol.to_numpy()>=vth if vr=="ge" else
             short.signal_vol.to_numpy()<=vth)
         sel=short[src&vm&
              (short.signal_atr_pct.to_numpy()>=float(c.atr_pct))&
              f[c.htf]].sort_values(
              ["entry_idx","setup"]).drop_duplicates("st_cycle")
         # Core exact P&L already is original; extras cannot overlap
         # the chosen core if scenario's guard says intact.
         extra=np.zeros(len(MONTHS))
         for item in sel.itertuples():
           xi,_,net,_,_=allreplay[(int(item.Index),float(c.short_sl_pct),
                                                float(c.short_tp_pct))]
           month=str(minsmonth[xi])
           if month in MONTHS:
             extra[MONTHS.index(month)]+=net
         monthly=baseline+extra
      for m,val,original_val in zip(MONTHS,monthly,baseline):
          monthrows.append(dict(config=name,month_ist=m,
              new_net=round(float(val),2),
              locked_core_net=round(float(original_val),2),
              improvement=round(float(val-original_val),2)))
    pd.DataFrame(monthrows).to_csv(OUT/"focus_monthly_profit_protection.csv",
                                 index=False)
    cols=["config","short_executed","positive_months",
          "newly_profitable_losing_months","baseline_profitable_months_not_degraded",
          "net_profit_not_decreased","net_2025","net_2026",
          "net_all22","net_delta","max_closed_equity_drawdown",
          "max_drawdown_not_increased"]
    report=[
      "# BTCUSD V1.0 both LONG legs untouched + separate bearish SHORT supplement",
      "",
      "Core preserved exactly: 67 Line Touch + 18 Bullish Flip = 85",
      "trades, net +19,099.62 BTC-equivalent price points, 17/22 months.",
      "All 22 originally seen profitable-month values must NEVER fall",
      "below their locked baseline, and neither original LONG component",
      "can be skipped or changed by the supplementary SHORT.",
      "",
      "## Strict pass: ALL existing winning months and core trades retained",
      strict[cols].head(25).to_markdown(index=False),
      "",
      "## Strict pass and closed-equity drawdown no worse",
      strict_dd[cols].head(25).to_markdown(index=False),
      "",
      "## High historical win month count, with potential tradeoffs - DO NOT LOCK",
      best_relaxed[cols].head(15).to_markdown(index=False),
      "",
      "## Conservative execution",
      "Bearish flip + next red 15m close and/or bearish resistance touch",
      "+ next red 15m close. SHORT SELL at following candle's OPEN",
      "less 5 point slippage. SL above entry fill, TP below entry fill.",
      "Always stop first in same 1m high/low ambiguity. Green ST",
      "closing exit buys back at next minute OPEN; no time travel.",
      "One short per bearish ST cycle, all original bullish cycles untouched.",
      "Separate live margin/account allocation NOT modeled.",
      "",
      "## Research limitations",
      "This grid is RETROSPECTIVE over 2025 to Oct2026, fully seen in",
      "the earlier strategy development. History used for model selection.",
      "NO truly blind test or forward proof; futures funding, liquidation,",
      "margin, orderbook depth, latency omitted. BTC-equivalent points",
      "NOT dollar-account return. No automatic production deployment."
    ]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")
    quality=dict(
      checked_configs=len(out),short_candidate_patterns=len(short),
      retained_original_long_trades=85,
      original_line_touch_and_bullish_flip_unmodified=True,
      original_2025_pnl=round(float(baseline[:12].sum()),2),
      original_2026_pnl=round(float(baseline[12:].sum()),2),
      original_22month_pnl=round(float(baseline.sum()),2),
      original_winning_months=17,
      strict_profit_months_and_core_count=len(strict),
      strict_profit_months_core_and_drawdown_count=len(strict_dd),
      strict_improve_months=int(sum(strict.positive_months>17)),
      strict_improve_months_with_drawdown_control=int(
         sum(strict_dd.positive_months>17)),
      max_strict_winning_months=int(strict.positive_months.max())
                  if len(strict) else 0,
      max_retrospective_winning_months=int(
          best_relaxed.positive_months.max()) if len(best_relaxed) else 0,
      independent_holdout=False,
      last_complete_month="2026-10",
      execution="1m conservative STOP-FIRST for SHORT; 15m green ST exit",
      short_margin_and_liquidation_not_modeled=True,
      future_market_information_in_filters=False)
    (OUT/"quality.json").write_text(json.dumps(quality,indent=2)+"\n")
    print("SUCCESS_BEARISH_SHORT_COMPLEMENT",json.dumps(quality),flush=True)
    print("STRICT_TOP\n"+strict[cols].head(10).to_string(index=False),
          flush=True)
    print("WITH_DD_CONTROL\n"+strict_dd[cols].head(10).to_string(index=False),
          flush=True)
    print("RELAXED_TOP\n"+best_relaxed[cols].head(8).to_string(index=False),
          flush=True)
if __name__=="__main__":
    main()
