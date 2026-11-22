#!/usr/bin/env python3
"""15m second GREEN after ST touch/flip: percentage profit protection ONLY.

Supertrend supplies ENTRY signals, NEVER exits. There is no fixed TP, hard
SL, time stop, or hard-limit drawdown. The ONLY programmed exit is a
stop enabled AFTER favorable price reaches a percentage threshold.
Untriggered trades stay OPEN through the last archive 1m candle. Live
margin and liquidation are NOT modeled.

Activation is based on a completed 1m HIGH; protective stop becomes active
at the NEXT minute, preventing fictitious same-candle high/low sequencing.
"""
from pathlib import Path
import json
import functools
import numpy as np
import pandas as pd

import research_supertrend_15m_line_touch as base
import research_supertrend_15m_filter_grid as filt
import research_supertrend_15m_profit_protection as pp
import research_supertrend_15m_second_green as green

OUT=Path("analysis/second_green_percent_protection_only_20261122")
ARM_PCT=(.12,.20,.30,.50,.75,1.,1.5,2.,3.,5.)
LOCK_FRAC=(0.,.5,.75,1.)
LADDERS={
 "ladder_012_02_03_05_1_2_5": ((.12,.20,.30,.50,1.,2.,5.),(0.,.12,.20,.30,.50,1.,2.)),
 "ladder_02_03_05_1_2_5": ((.20,.30,.50,1.,2.,5.),(0.,.20,.30,.50,1.,2.)),
 "ladder_05_1_2_5": ((.50,1.,2.,5.),(0.,.50,1.,2.)),
 "ladder_1_2_5": ((1.,2.,5.),(0.,1.,2.)),
}
MODES=[(f"arm_{arm:g}_lock_{int(fr*100)}pct_of_arm","single",arm,fr)
       for arm in ARM_PCT for fr in LOCK_FRAC]
MODES += [(name,"ladder",ts,locks) for name,(ts,locks) in LADDERS.items()]
MODE_KEYS=[m[0] for m in MODES]
assert len(MODES)==44 and len(set(MODE_KEYS))==44
MONTHS=base.MONTHS
DISPLAY_FILTERS=(("vol_off","atr_off"),
                 ("vol_ge_1p0","atrpct_ge_0p20"),
                 ("vol_ge_1p25","atrpct_ge_0p20"),
                 ("vol_ge_1p5","atrpct_ge_0p20"),
                 ("vol_ge_2p0","atrpct_ge_0p30"))
NAMES=("after_line_touch","after_bullish_flip")

def price_exit(j, idx, level, opening, close, n):
    """Make protective STOP exit; overnight 1m gap may fill worse."""
    if idx<n:
        return idx,float(min(opening[idx],level)),"protective_stop"
    return n-1,float(close[-1]),"still_open_marked"

def eval_candidate(j,mid,high,low,op,close):
    """For one entry, evaluate ALL 44 modes using O(n) 1m array operations.

    Every entry is market-at-open, fill midpoint+5. Future OHLC cannot
    update stop until FOLLOWING 1-minute bar: no high-then-low assumptions.
    """
    n=len(high)
    fill=float(mid+base.SLIP)
    future_high=high[j:]
    cumhigh=np.maximum.accumulate(future_high)
    length=len(cumhigh)
    results={}
    for activation in ARM_PCT:
        arm_price=fill*(1+activation/100)
        k=int(np.searchsorted(cumhigh,arm_price,side="left"))
        if k>=length-1:
            for frac in LOCK_FRAC:
                key=f"arm_{activation:g}_lock_{int(frac*100)}pct_of_arm"
                results[key]=(n-1,float(close[-1]),"still_open_marked",
                              int(k<length),activation,activation*frac)
            continue
        # From 1m AFTER the first threshold-crossing minute, a stop can
        # be valid. A new stop is never checked retroactively in same 1m.
        first_stop_minute=j+k+1
        lows_from_activation=low[first_stop_minute:]
        prefix_low=np.minimum.accumulate(lows_from_activation)
        negprefix=-prefix_low
        for frac in LOCK_FRAC:
            lock_pct=activation*frac
            lock_price=fill*(1+lock_pct/100)
            f=int(np.searchsorted(negprefix,-lock_price,side="left"))
            exit_idx=first_stop_minute+f if f<len(prefix_low) else n
            key=f"arm_{activation:g}_lock_{int(frac*100)}pct_of_arm"
            ex_idx,ex_price,reason=price_exit(
                j,exit_idx,lock_price,op,close,n)
            results[key]=(ex_idx,ex_price,reason,1,
                          activation,lock_pct)

    cum_pct=(cumhigh/fill-1.)*100.
    for name,(thresholds,locks) in LADDERS.items():
        # Highest threshold reached by a COMPLETED minute high determines
        # where the stop moves for the NEXT minute. No ST/TP/SL other exits.
        stop=np.full(length,-np.inf,float)
        for arm,locked in zip(thresholds,locks):
            stop[cum_pct>=arm]=fill*(1+locked/100.)
        # stop[i-1] is live over minute i. stop[0] is NOT live in entry minute.
        rel=np.flatnonzero(low[j+1:]<=stop[:-1])
        if len(rel):
            k=int(rel[0])+1
            exit_j=j+k
            level=float(stop[k-1])
            exit_idx,exit_price,reason=price_exit(
                j,exit_j,level,op,close,n)
        else:
            exit_idx=n-1;exit_price=float(close[-1])
            reason="still_open_marked"
        armed=int(np.any(cum_pct>=thresholds[0]))
        idxmin=max(0,min(exit_idx-j-1,length-1))
        last_active=int(np.searchsorted(thresholds,cum_pct[idxmin],
                                        side="right"))-1
        locked=locks[last_active] if last_active>=0 else None
        results[name]=(exit_idx,exit_price,reason,armed,
                       thresholds[0],locked)
    return results

def microtests():
    # A minute reaching a new threshold cannot also exit at newly
    # placed stop, even if its LOW was earlier/lower in that same minute.
    op=np.array([100000.,100100.,100200.,100200.,100200.,100200.])
    hi=np.array([100200.,100250.,100250.,100250.,100250.,100250.])
    lo=np.array([99950.,99700.,100150.,100190.,100190.,100190.])
    cl=np.array([100100.,100200.,100200.,100200.,100200.,100200.])
    x=eval_candidate(0,100000.,hi,lo,op,cl)
    assert x["arm_0.12_lock_0pct_of_arm"][0]==1,x
    assert x["arm_0.12_lock_0pct_of_arm"][2]=="protective_stop"
    # No threshold reached => OPEN and no invented ST exit.
    h=np.full(6,100000.);l=np.full(6,99900.)
    y=eval_candidate(0,100000.,h,l,op,cl)
    assert y["arm_5_lock_50pct_of_arm"][2]=="still_open_marked"
    assert y["ladder_1_2_5"][2]=="still_open_marked"
    # Stop gap below working level must fill at worse opening, not stop.
    op2=op.copy();op2[1]=99800.
    z=eval_candidate(0,100000.,hi,lo,op2,cl)
    assert z["arm_0.12_lock_0pct_of_arm"][1]==99800.
    print("MICROTESTS_PROTECTION_ONLY_PASS",flush=True)

def build_replay(entries,filtername,atrname,mode,high,low,opening,close,
                 monthsbyminute,cache):
    n=len(high)
    rows=[]
    skipped=0
    locked_until=-1
    entry_indices=[int(x[2]) for x in sorted(entries,key=lambda x:x[2])
                   if str(monthsbyminute[int(x[2])]) in MONTHS]
    assert len(entry_indices)==len(set(entry_indices))
    for j in entry_indices:
        if j<=locked_until:
            skipped+=1
            continue
        mid=float(opening[j])
        (exit_idx,exit_mid,reason,activated,first_arm,locked_pct)=cache(j)[mode]
        # Single active trade. If still open by data end, all future
        # entry candidates must be ignored.
        locked_until=int(exit_idx)
        ef=mid+base.SLIP
        xf=float(exit_mid)-base.SLIP
        fee=base.FEE*(ef+xf)
        net=xf-ef-fee
        adverse=float(np.min(low[j:exit_idx+1]))
        mae_pct=100*(adverse-ef)/ef
        rows.append(dict(
            entry_type=filtername,mode=mode,entry_index=j,
            exit_index=int(exit_idx),
            month_ist=str(monthsbyminute[j]),
            status=reason,
            activated=int(activated),
            entry_fill=round(ef,5),
            exit_mid_or_data_end_close=round(float(exit_mid),5),
            estimated_fee_pts=round(float(fee),5),
            net_pts_after_friction=round(float(net),5),
            net_win=int(net>0),max_adverse_excursion_pct=round(mae_pct,4),
            holding_minutes=int(exit_idx-j),first_arm_pct=first_arm,
            last_locked_pct=locked_pct))
    return rows,skipped,len(entry_indices)

def stats(rows,skip,eligible,kind,v,a,mode):
    df=pd.DataFrame(rows)
    closed=df[df.status=="protective_stop"] if len(df) else df
    opened=df[df.status=="still_open_marked"] if len(df) else df
    total=len(df); nc=len(closed); no=len(opened)
    gross=float(closed.net_pts_after_friction.sum()) if nc else 0.
    mark=float(opened.net_pts_after_friction.sum()) if no else 0.
    totalmark=gross+mark
    winners=int(closed.net_win.sum()) if nc else 0
    bymonth=(df.groupby("month_ist").net_pts_after_friction.sum()
             if total else pd.Series(dtype=float))
    trueclosed=(closed.groupby("month_ist").net_pts_after_friction.sum()
                if nc else pd.Series(dtype=float))
    monthclosed=np.array([float(trueclosed.get(m,0.)) for m in MONTHS])
    monthmark=np.array([float(bymonth.get(m,0.)) for m in MONTHS])
    # NO CONVENTIONAL EQUITY DRAWDOWN claim for open trade exposure;
    # mark is a single final snapshot, not a full historical equity path.
    return dict(entry_type=kind,vol_filter=v,atr_filter=a,mode=mode,
      accepted_trades=total,signals_during_open_skipped=skip,
      qualifying_signals=eligible,
      closed_trades=nc,still_open=no,
      net_winners=winners,
      closed_winrate_pct=round(winners*100/nc,2) if nc else None,
      net_realized_pts=round(gross,2),
      open_mark_to_market_pts=round(mark,2),
      combined_net_if_open_liquidated=round(totalmark,2),
      avg_net_per_accepted_trade=round(totalmark/total,2) if total else None,
      profitable_months_realized=int((monthclosed>0).sum()),
      losing_months_realized=int((monthclosed<0).sum()),
      flat_months_realized=int((monthclosed==0).sum()),
      net_2025_including_mark=round(float(monthmark[:12].sum()),2),
      net_2026_including_mark=round(float(monthmark[12:].sum()),2),
      total_activated=int(df.activated.sum()) if total else 0,
      worst_trade_mae_pct=round(float(df.max_adverse_excursion_pct.min()),3) if total else None,
      max_holding_days=round(float(df.holding_minutes.max()/1440),2) if total else None)

def main():
    microtests()
    OUT.mkdir(parents=True,exist_ok=True)
    minute,bar15,files=base.load()
    st,trend=base.supertrend(bar15)
    vol,atrpct,atrrel=filt.build_features(bar15)
    events,stops=filt.candidate_touch_events(
        minute,bar15,st,trend,vol,atrpct,atrrel)
    high=minute.high.to_numpy(float)
    low=minute.low.to_numpy(float)
    opening=minute.open.to_numpy(float)
    close=minute.close.to_numpy(float)
    monthsbyminute=minute.index.tz_convert("Asia/Kolkata").strftime("%Y-%m").to_numpy()
    @functools.lru_cache(maxsize=None)
    def cache(j):
        return eval_candidate(j,float(opening[j]),high,low,opening,close)

    baseline=[]
    selectedledgers=[]
    for vn,vs in filt.VOLUME.items():
        for an,a in filt.VOLATILITY.items():
            touch=pp.select_events(events,vs,a)
            signals=dict(
               after_line_touch=green.after_touch_green(
                       touch,bar15,trend,stops,opening),
               after_bullish_flip=green.after_flip_green(
                       bar15,trend,vol,atrpct,atrrel,vs,a,stops,opening))
            for kind,entries in signals.items():
                for mod in MODE_KEYS:
                    rows,skipped,eligible=build_replay(
                        entries,vn,an,mod,high,low,opening,close,
                        monthsbyminute,cache)
                    report=stats(rows,skipped,eligible,kind,vn,an,mod)
                    baseline.append(report)
                    if (vn,an) in DISPLAY_FILTERS and mod in (
                         "arm_0.12_lock_0pct_of_arm",
                         "arm_0.2_lock_50pct_of_arm",
                         "arm_0.3_lock_75pct_of_arm",
                         "arm_1_lock_50pct_of_arm",
                         "arm_2_lock_50pct_of_arm",
                         "arm_5_lock_50pct_of_arm",
                         "ladder_012_02_03_05_1_2_5",
                         "ladder_02_03_05_1_2_5",
                         "ladder_05_1_2_5",
                         "ladder_1_2_5"):
                        for row in rows:
                            selectedledgers.append(dict(
                               strategy=kind,volume_filter=vn,
                               atr_filter=an,**row))
            print("DONE_FILTER",vn,an,"cached_entry_indices",cache.cache_info().currsize,
                  "n_configs",len(baseline),flush=True)

    result=pd.DataFrame(baseline)
    assert len(result)==len(filt.VOLUME)*len(filt.VOLATILITY)*len(MODES)*2==3696
    assert (result.closed_trades+result.still_open==result.accepted_trades).all()
    assert (result.accepted_trades+result.signals_during_open_skipped==
            result.qualifying_signals).all()
    assert all(x not in result.columns for x in ("tp_exits","st_exits","sl_exits"))
    result.to_csv(OUT/"all_3696_profit_protection_only.csv",index=False)
    main=result[(result.vol_filter=="vol_ge_1p0")&
                (result.atr_filter=="atrpct_ge_0p20")]
    main.to_csv(OUT/"same_filters_comparison.csv",index=False)
    raw=result[(result.vol_filter=="vol_off")&
               (result.atr_filter=="atr_off")]
    raw.to_csv(OUT/"unfiltered_comparison.csv",index=False)
    if selectedledgers:
        pd.DataFrame(selectedledgers).to_csv(
            OUT/"selected_trade_ledgers.csv.gz",compression="gzip",index=False)

    # Summarize only closed profit protections and unresolved marks. A large
    # apparent win must be scrutinized for unclosed deep losers and skipped
    # signals. Sort with at least 30 closed trades and no unresolved positions.
    robust=result[(result.closed_trades>=30)&(result.still_open==0)].copy()
    ranked=robust.sort_values(["combined_net_if_open_liquidated",
        "profitable_months_realized"],ascending=[False,False])
    eligible=result[result.closed_trades>=30]
    quality=dict(
       trade_logic="ST10x3 entry only, 15m next-green confirmation, 1m market at third candle OPEN",
       exits="ONLY trailing percent-based profit-protection STOP when activated; NO ST close exit, TP, hard SL, timeout",
       thresholds_pct=list(ARM_PCT),
       standalone_locks_pct_of_activation=[int(fr*100) for fr in LOCK_FRAC],
       ladders={x:dict(activation_pct=list(t),locked_pct=list(l))
                for x,(t,l) in LADDERS.items()},
       protective_activation_timing="Observing 1m HIGH, stop working from NEXT 1m candle; no same-minute retrospective low",
       one_position_at_a_time=True,one_trade_per_ST_cycle=True,
       filters=len(filt.VOLUME)*len(filt.VOLATILITY),
       modes=len(MODES),entry_variants=2,
       tested=int(len(result)),positions_still_open=int(result.still_open.sum()),
       positions_not_liquidated=True,
       status_convention="If last-data open, report hypothetical close at end only as marked-to-market, NOT realized exit",
       model="BTCUSD Delta India 1m Jan 2025-Nov 2026 archive, complete IST entry months Jan 2025-Oct 2026, one-BTC-equivalent",
       execution="Taker entry +5 BTC pt, protect exit -5 pt, taker fee 0.05 percent each side with GST18",
       major_risk="No hard stop or liquidation; price may move materially against entry before first protection is armed, causing huge drawdown",
       absence=["funding","margin","liquidation","tick-level intraminute ordering","bid/ask spread","forced close on ST flip"],
       note="Previously exposed research data, all mined results in sample; no untouched validation")
    (OUT/"quality.json").write_text(json.dumps(quality,indent=2)+"\n")
    cols=["entry_type","mode","accepted_trades","signals_during_open_skipped",
          "closed_trades","still_open","net_winners","closed_winrate_pct",
          "net_realized_pts","open_mark_to_market_pts",
          "combined_net_if_open_liquidated",
          "profitable_months_realized","flat_months_realized",
          "worst_trade_mae_pct","max_holding_days"]
    lines=[
      "# Percentage profit protection ONLY — without ST stop, fixed TP/SL",
      "",
      "BTCUSD 15m ST10x3 entries, second 15m GREEN confirmation, market",
      "third 15m OPEN. No programmed exit except armed protective percentage",
      "stop; positions not armed remain OPEN at archive end. NO ST close exit",
      "or fixed TP / SL. One active position at a time; skip overlapping",
      "new bullish signals. Research 22 complete entry months Jan2025-Oct2026.",
      "",
      "Percentage of **entry fill**, not BTC points or leveraged ROI.",
      "After 1m high reaches percentage activation, a protective stop",
      "becomes eligible **next 1-minute candle**. Stop can gap and fill worse.",
      "Estimated taker 0.05% per side +18% GST, 5 BTC pts slippage each side.",
      "Results in 1 BTC-equivalent BTC price points, not capital returns.",
      "",
      f"Configurations: **{len(result)}** = 44 lock/ladder schedules x 42",
      "volume/ATR filters x two entry methods.",
      "",
      "## Same filters: Volume >=1, ATR >=0.20%",
      main[cols].to_markdown(index=False),
      "",
      "## Unfiltered: 44 modes x two entries",
      raw[cols].to_markdown(index=False),
      "",
      "## Highest marked outcomes with >=30 closed trades, NO unresolved open trade",
      (ranked[["vol_filter","atr_filter"]+cols].head(25)
       .to_markdown(index=False) if len(ranked) else
       "No configurations met 30 closed trades AND zero open positions."),
      "",
      "## Top with >=30 closed trades EVEN IF still open (must inspect)",
      eligible.sort_values("combined_net_if_open_liquidated",
            ascending=False)[["vol_filter","atr_filter"]+cols].head(20)
            .to_markdown(index=False),
      "",
      "## Critical limitations",
      "- There is NO loss-stop or liquidation model. Prior to activation,",
      "  unrealized losses are not capped. Missing exchange margin/liquidation",
      "  can make protection-only strategies untradeable.",
      "- 'Closed' means a percentage protective stop fired. If a trade",
      "  remains open at last available data, it is NOT treated as a",
      "  completed protective-stop exit. Mark-to-market is shown separately.",
      "- Gross positive trade excursions can coexist with massive underwater",
      "  periods. Watch worst MAE and max holding days, not just net total.",
      "- Entry cohorts DIFFER across modes because only one trade can be",
      "  open; later entries are skipped until the old trade actually closes.",
      "- Historical backtest grid is selected after seeing 2025–2026; it",
      "  is not evidence of a validated live trading edge.",
    ]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(lines)+"\n")
    print("PROTECTION_ONLY_VERIFIED",json.dumps({
       "configurations":len(result),
       "standalone":40,"ladders":4,
       "cache_entries":cache.cache_info().currsize,
       "eligible_configurations_30closed":len(eligible),
       "robust_no_open":len(robust)}),flush=True)
    print("SAME_FILTERS\n"+main[cols].to_string(index=False),flush=True)
    print("ROBUST_NO_OPEN_TOP10\n"+
          ranked[["vol_filter","atr_filter"]+cols].head(10)
                .to_string(index=False),flush=True)
    print("REPORT",OUT/"RESEARCH_REPORT.md",flush=True)

if __name__=="__main__":
    main()
