#!/usr/bin/env python3
"""Combine 3 historical BTCUSD 15m ST(10,3) long strategies.

The THREE exact independently optimized settings from the conversation:
- Line Touch:  SL 0.2%, TP 1.5%, volume >=1x, ATR% >=0.20%;
- Bullish Flip: SL 3%, TP 0.5%, volume <=0.8x, ATR% >=0.20%;
- Flip + Breakout: SL 3%, TP 1.5%, volume <=0.8x, ATR% >=0.20%.
Breakout is the next GREEN candle after flip closing above flip high.

Original Supertrend close stop unchanged. Full 1m stop-first OHLC fills.
Compare (i) independent summed trades, (ii) EXCLUSIVE 1 live position
with first-in-chronological-order and configurable same-minute priority
and optional one-position-per-ST-cycle rule. Show actual exit-month PnL,
entry-month legacy attribution and month-end floating mark to market.

Important: 1 BTC-equivalent price-points, not account margin-adjusted profit.
No liquidations/funding/spread depth, no independent out-of-sample.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd

import research_supertrend_15m_line_touch as base
import research_supertrend_15m_filter_grid as filt
import research_supertrend_15m_profit_protection as protect
import research_supertrend_15m_second_green as green
import research_st_three_way_flip_breakout as three
import research_second_green_percent_grid as grid
import research_second_green_percent_rr_scenarios as rr

OUT=Path("analysis/st_three_best_positive_months_combined_20261122")
MONTHS=base.MONTHS
SPECS={
    "line_touch":dict(sl=0.2,tp=1.5,volume="vol_ge_1p0",
                      atr="atrpct_ge_0p20",expected_n=108,
                      expected_w=24,expected_net=4060.14,
                      expected_pos=14,expected_loss=8),
    "bullish_flip":dict(sl=3.0,tp=0.5,volume="vol_le_0p8",
                        atr="atrpct_ge_0p20",expected_n=42,
                        expected_w=33,expected_net=3401.08,
                        expected_pos=14,expected_loss=5),
    "flip_breakout":dict(sl=3.0,tp=1.5,volume="vol_le_0p8",
                        atr="atrpct_ge_0p20",expected_n=34,
                        expected_w=19,expected_net=8392.57,
                        expected_pos=12,expected_loss=4)
}
PRIORITY={
    "default":("flip_breakout","line_touch","bullish_flip"),
    "flip_first":("bullish_flip","line_touch","flip_breakout"),
    "touch_first":("line_touch","flip_breakout","bullish_flip")
}
REASONS={1:"percent_stop_loss",2:"percent_take_profit",
         3:"original_15m_supertrend_close",4:"archive_end_close"}

def decode_signals(minute,bars,trend,vol,pct,rel,events,stops):
    op=minute.open.to_numpy(float)
    out={}
    distinct=set((s["volume"],s["atr"]) for s in SPECS.values())
    cached={}
    for v,a in distinct:
        touch=protect.select_events(events,
                      filt.VOLUME[v],filt.VOLATILITY[a])
        flip=green.after_flip_green(
              bars,trend,vol,pct,rel,
              filt.VOLUME[v],filt.VOLATILITY[a],stops,op)
        green_touch=green.after_touch_green(
              touch,bars,trend,stops,op)
        breakout=three.confirmed_breakout(flip,bars)
        cached[(v,a)]=dict(line_touch=green_touch,
                          bullish_flip=flip,flip_breakout=breakout)
    for name,s in SPECS.items():
        out[name]=cached[(s["volume"],s["atr"])][name]
    return out

def compute_candidates(minute,trend,stops,signal_sets):
    h=minute.high.to_numpy(float)
    l=minute.low.to_numpy(float)
    op=minute.open.to_numpy(float)
    cl=minute.close.to_numpy(float)
    n=len(h)
    months=minute.index.tz_convert("Asia/Kolkata").strftime("%Y-%m").to_numpy()
    cycles=np.cumsum(
      (trend==-1)&(np.r_[True,trend[:-1]!=-1]))
    rows=[]
    for name,s in SPECS.items():
        si=rr.STOP_PCT.index(s["sl"])
        ti=rr.TARGET_PCT.index(s["tp"])
        for cycle,bar,j,mid,line in signal_sets[name]:
            bar=int(bar);j=int(j)
            mo=str(months[j])
            if mo not in MONTHS:continue
            assert j==bar*15 and mid==op[j]
            k=np.searchsorted(stops,bar,side="left")
            sb=int(stops[k]) if k<len(stops) else -1
            end=min((sb+1)*15,n) if sb>=0 else n
            assert end>j
            endmid,endindex,reason,collision=grid.market_ohlc_precompute(
                mid,j,end,h,l,op,cl)
            endmid=float(endmid[si,ti])
            exitidx=int(endindex[si,ti])
            reason=int(reason[si,ti])
            assert j<=exitidx<n
            fill=mid+base.SLIP
            exit_fill=endmid-base.SLIP
            fee=base.FEE*(fill+exit_fill)
            net=exit_fill-fill-fee
            st_cycle=int(cycles[bar-1])
            assert st_cycle>0,("cycle",name,bar)
            rows.append(dict(
                strategy=name,signal_cycle=int(cycle),
                st_cycle=st_cycle,entry_bar=bar,
                entry_idx=j,exit_idx=exitidx,
                entry_utc=str(minute.index[j]),
                exit_utc=str(minute.index[exitidx]),
                entry_month_ist=mo,
                exit_month_ist=str(months[exitidx]),
                sl_pct=s["sl"],tp_pct=s["tp"],
                entry_fill=round(fill,5),exit_fill=round(exit_fill,5),
                entry_mid=round(mid,5),exit_mid=round(endmid,5),
                net_pts=float(net),fee_pts=float(fee),
                reason=REASONS[reason],
                collision=int(collision[si,ti]),
                holding_minutes=exitidx-j,win=int(net>0)))
    df=pd.DataFrame(rows).sort_values(
        ["entry_idx","strategy"]).reset_index(drop=True)
    return df

def month_table(ledger,minute,policy):
    monthly=[]
    month_arr=minute.index.tz_convert("Asia/Kolkata").strftime("%Y-%m").to_numpy()
    closes=minute.close.to_numpy(float)
    prior_marked=0.
    for mo in MONTHS:
        monthend=int(np.flatnonzero(month_arr==mo)[-1])
        # Legacy comparison counts all eventual trade PnL at entry month.
        enter=ledger[ledger.entry_month_ist==mo]
        # Actually realized PnL occurs in the true exit month.
        exit_=ledger[ledger.exit_month_ist==mo]
        realized_through=ledger[ledger.exit_idx<=monthend]
        booked=float(realized_through.net_pts.sum())
        currently_open=ledger[
            (ledger.entry_idx<=monthend)&(ledger.exit_idx>monthend)]
        float_net=0.
        for item in currently_open.itertuples():
            mark_exit_fill=closes[monthend]-base.SLIP
            float_net += (mark_exit_fill-item.entry_fill-
                      base.FEE*(item.entry_fill+mark_exit_fill))
        marked=booked+float_net
        month_pnl=marked-prior_marked
        prior_marked=marked
        monthly.append(dict(
          policy=policy,month_ist=mo,
          entry_month_net_pts=round(float(enter.net_pts.sum()),2),
          exit_month_realized_net_pts=round(float(exit_.net_pts.sum()),2),
          month_end_equity_mtm_pts=round(marked,2),
          month_to_month_mtm_change_pts=round(month_pnl,2),
          month_end_open_positions=len(currently_open),
          realized_closed_trades=len(exit_),
          newly_entered_trades=len(enter)))
    return pd.DataFrame(monthly)

def portfolio(allrows,eligible,priority,global_cycle_cap=True):
    sortpri={name:i for i,name in enumerate(priority)}
    df=allrows[allrows.strategy.isin(eligible)].copy()
    df["priority"]=df.strategy.map(sortpri)
    df=df.sort_values(["entry_idx","priority"]).reset_index(drop=True)
    chosen=[]
    used_cycles=set()
    last_exit=-1
    blocked_overlaps=blocked_cycles=0
    for row in df.itertuples():
        if row.entry_idx<=last_exit:
            blocked_overlaps+=1
            continue
        if global_cycle_cap and row.st_cycle in used_cycles:
            blocked_cycles+=1
            continue
        chosen.append(int(row.Index))
        last_exit=row.exit_idx
        used_cycles.add(row.st_cycle)
    p=df.iloc[chosen].copy()
    assert p.empty or (p.entry_idx.diff().dropna()>0).all()
    assert p.empty or (p.entry_idx.iloc[1:].to_numpy() >
                p.exit_idx.iloc[:-1].to_numpy()).all()
    if global_cycle_cap:assert p.st_cycle.is_unique
    p.drop(columns=["priority"],inplace=True)
    return p,dict(blocked_overlaps=blocked_overlaps,
                  blocked_one_cycle=blocked_cycles,
                  input_signals=len(df),accepted=len(p))

def summarize(ledger,month,policy,blocks):
    net=float(ledger.net_pts.sum())
    win=int(ledger.win.sum())
    count=len(ledger)
    a=ledger.sort_values("exit_idx")
    eq=np.r_[0.,np.cumsum(a.net_pts.to_numpy(float))]
    dd=float(np.max(np.maximum.accumulate(eq)-eq))
    ret=dict(policy=policy,trades=count,wins=win,losses=count-win,
             win_rate_pct=round(100*win/count,2) if count else 0,
             net_pts=round(net,2),
             trade_cost_pts=round(float(ledger.fee_pts.sum()),2),
             max_realized_trade_equity_drawdown_pts=round(dd,2),
             profitable_entry_months=int((month.entry_month_net_pts>0).sum()),
             losing_entry_months=int((month.entry_month_net_pts<0).sum()),
             flat_entry_months=int((month.entry_month_net_pts==0).sum()),
             profitable_realized_exit_months=int(
                 (month.exit_month_realized_net_pts>0).sum()),
             losing_realized_exit_months=int(
                 (month.exit_month_realized_net_pts<0).sum()),
             flat_realized_exit_months=int(
                 (month.exit_month_realized_net_pts==0).sum()),
             profitable_mark_to_market_months=int(
                 (month.month_to_month_mtm_change_pts>0).sum()),
             losing_mark_to_market_months=int(
                 (month.month_to_month_mtm_change_pts<0).sum()),
             flat_mark_to_market_months=int(
                 (month.month_to_month_mtm_change_pts==0).sum()),
             ending_oct_equity_mtm_pts=round(float(
                  month.month_end_equity_mtm_pts.iloc[-1]),2),
             oct_end_open_positions=int(
                  month.month_end_open_positions.iloc[-1]),
             post_oct_exit_trades=int((ledger.exit_month_ist>"2026-10").sum()),
             max_entry_held_days=round(float(
                  ledger.holding_minutes.max()/1440),3) if count else 0)
    return ret|blocks

def main():
    rr.configure_grid()
    OUT.mkdir(parents=True,exist_ok=True)
    minute,bars,files=base.load()
    st,trend=base.supertrend(bars)
    vol,atrpct,atrrel=filt.build_features(bars)
    events,stops=filt.candidate_touch_events(
        minute,bars,st,trend,vol,atrpct,atrrel)
    ss=decode_signals(minute,bars,trend,vol,atrpct,atrrel,events,stops)
    candidates=compute_candidates(minute,trend,stops,ss)
    # Hard validation against all 3 previously verified independent studies.
    validation=[]
    for name,s in SPECS.items():
        a=candidates[candidates.strategy==name]
        mon=a.groupby("entry_month_ist").net_pts.sum()
        assert len(a)==s["expected_n"],(name,"trades",len(a),s["expected_n"])
        assert int(a.win.sum())==s["expected_w"],(name,"wins",int(a.win.sum()))
        assert abs(float(a.net_pts.sum())-s["expected_net"])<0.02,(
                  name,"net",float(a.net_pts.sum()),s["expected_net"])
        assert int((mon>0).sum())==s["expected_pos"],(
                  name,"positive_months",int((mon>0).sum()))
        assert int((mon<0).sum())==s["expected_loss"],(
                  name,"losing_months",int((mon<0).sum()))
        validation.append(dict(strategy=name,expected=s,observed=dict(
            trades=len(a),wins=int(a.win.sum()),net_pts=float(a.net_pts.sum()),
            profitable_months=int((mon>0).sum()))))
    print("THREE_SOURCE_PARITY_PASS",json.dumps(validation),flush=True)
    candidates.to_csv(OUT/"all_independent_signal_trade_ledger.csv.gz",
                      index=False,compression="gzip")
    priority=PRIORITY["default"]
    policies={}
    policies["standalone_line_touch"]=(candidates[
        candidates.strategy=="line_touch"].copy(),dict())
    policies["standalone_bullish_flip"]=(candidates[
        candidates.strategy=="bullish_flip"].copy(),dict())
    policies["standalone_flip_breakout"]=(candidates[
        candidates.strategy=="flip_breakout"].copy(),dict())
    policies["parallel_sum_not_executable_one_position"]=(candidates.copy(),dict(
        duplicated_entry_minutes=int(candidates.entry_idx.duplicated().sum())))
    combos=[
      ("exclusive_touch_plus_flip",("line_touch","bullish_flip")),
      ("exclusive_touch_plus_breakout",("line_touch","flip_breakout")),
      ("exclusive_flip_plus_breakout",("bullish_flip","flip_breakout")),
      ("exclusive_all_three_default",tuple(SPECS)),
    ]
    for name,subset in combos:
        policies[name]=portfolio(candidates,subset,priority,True)
    for alt in ("flip_first","touch_first"):
        policies["exclusive_all_three_"+alt]=portfolio(
                 candidates,tuple(SPECS),PRIORITY[alt],True)
    policies["exclusive_all_three_no_cycle_cap"]=portfolio(
              candidates,tuple(SPECS),priority,False)
    summaries=[];monthlys=[];trades=[]
    for name,(ledger,blocked) in policies.items():
        m=month_table(ledger,minute,name)
        summaries.append(summarize(ledger,m,name,blocked))
        monthlys.append(m)
        t=ledger.copy();t["policy"]=name
        trades.append(t)
    summary=pd.DataFrame(summaries)
    monthly=pd.concat(monthlys,ignore_index=True)
    alltr=pd.concat(trades,ignore_index=True)
    summary.to_csv(OUT/"policy_comparison_summary.csv",index=False)
    monthly.to_csv(OUT/"entry_exit_and_mark_to_market_monthly.csv",index=False)
    alltr.to_csv(OUT/"selected_positions_by_policy.csv.gz",
                 index=False,compression="gzip")
    default=monthly[monthly.policy=="exclusive_all_three_default"]
    assert len(default)==22
    combined=summary[summary.policy=="exclusive_all_three_default"].iloc[0]
    full=summary[summary.policy=="parallel_sum_not_executable_one_position"].iloc[0]
    expected_sum=sum(s["expected_net"] for s in SPECS.values())
    assert abs(float(full.net_pts)-expected_sum)<0.03
    assert int(full.trades)==184
    assert len(default)==22
    # Confirm MTM accounting: as-of 2026-10 value differs from total
    # full-horizon net only if Oct-end position is still open.
    assert abs(float(default.month_to_month_mtm_change_pts.sum())-
               float(combined.ending_oct_equity_mtm_pts))<0.2

    report=[
      "# BTCUSD 15M three best positive-month strategies combined",
      "",
      "Original Supertrend (10,3) closing exit unchanged. Third candle",
      "LONG market entries, fixed percent SL/TP using conservative 1m bars;",
      "ONE POSITION across all strategies in exclusive variants.",
      "",
      "Exact user-selected rules:",
      "- Line Touch: SL .2%, TP 1.5%, volume>=1x, ATRpct>=.20%.",
      "- Bullish Flip: SL 3%, TP .5%, volume<=.8x, ATRpct>=.20%.",
      "- Bullish Flip+Breakout: SL 3%, TP 1.5%, volume<=.8x, ATRpct>=.20%.",
      "- Breakout = next 15m candle green, CLOSE above flip candle HIGH.",
      "",
      "DEFAULT: when candidate entry moments tie, breakout wins before",
      "touch then flip. One new live position only AFTER prior exit minute.",
      "Also globally one trade per ST bullish cycle in default. Tested",
      "both alternate priorities and allowing multiple trades per ST cycle.",
      "Only positions ENTERED in 2025Jan through 2026Oct are counted.",
      "",
      "## Combined result, independently summed reference and sensitivities",
      summary[["policy","trades","wins","losses","win_rate_pct",
         "net_pts","profitable_entry_months","losing_entry_months",
         "flat_entry_months","profitable_realized_exit_months",
         "losing_realized_exit_months","flat_realized_exit_months",
         "profitable_mark_to_market_months","losing_mark_to_market_months",
         "ending_oct_equity_mtm_pts","max_realized_trade_equity_drawdown_pts",
         "blocked_overlaps","blocked_one_cycle"]].to_markdown(index=False),
      "",
      "## Combined portfolio by month (default exclusive)",
      default[["month_ist","newly_entered_trades",
         "entry_month_net_pts","exit_month_realized_net_pts",
         "month_to_month_mtm_change_pts","month_end_equity_mtm_pts",
         "month_end_open_positions"]].to_markdown(index=False),
      "",
      "## Critical month accounting",
      "- Legacy entry-month attribution assigns whole trade P&L to the",
      "  opening calendar month even if it closes in a later month.",
      "- Realized exit-month P&L counts only trades closed in that month.",
      "- MTM end-month includes cumulative realized P&L plus unrealized",
      "  open position mark net of estimated exit fees and slippage.",
      "- Complete 22 months are Jan 2025 through Oct 2026 IST; positions",
      "  opened in Oct and closed in Nov contribute realized P&L to Nov,",
      "  not the preceding 22 exit-month figures.",
      "",
      "## Warnings",
      "- Net is BTC price points per 1 BTC equivalent, NOT USDT account ROI.",
      "- All three parameters selected on the SAME historical dataset;",
      "  combing them does not make historical selection out-of-sample.",
      "- Funding, liquidation, leverage, fill depth and queued orders",
      "  are absent. Stacked margin in the independent sum is NOT modeled.",
      "- Conservative one-minute SL-before-TP ordering is modeled, but",
      "  one-minute OHLC cannot recreate actual tick sequence.",
    ]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")
    quality=dict(data_files=len(files),
      data_start=str(minute.index[0]),data_end=str(minute.index[-1]),
      period="2025-01 through 2026-10 entries in IST",
      standalone_parity_validated=validation,
      priority_default=list(priority),
      one_position_default=True,one_trade_per_ST_cycle_default=True,
      portfolio_variants=list(policies),
      source_code_script=__file__,finance_units="1 BTC-equivalent price points",
      market_data="Delta Exchange India BTCUSD 1-minute OHLC",
      cost_model="0.05% fee per side +18% GST +5 price points slippage per side",
      margin_and_liquidation_model=False,
      funding_model=False,
      independent_out_of_sample=False,
      selected_after_lookback=True)
    (OUT/"quality.json").write_text(json.dumps(quality,indent=2)+"\n")
    print("PORTFOLIO_SUMMARY\n"+summary[["policy","trades","wins",
       "losses","net_pts","profitable_entry_months",
       "profitable_realized_exit_months","profitable_mark_to_market_months",
       "ending_oct_equity_mtm_pts","max_realized_trade_equity_drawdown_pts"]].to_string(index=False),flush=True)
    print("DEFAULT_MONTHLY\n"+default.to_string(index=False),flush=True)
    print("SUCCESS_FULL_COMBINED_BACKTEST",flush=True)

if __name__=="__main__":
    main()
