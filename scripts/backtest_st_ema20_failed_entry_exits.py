#!/usr/bin/env python3
"""Research-only failure management of BTCUSD 1H EMA20 + Supertrend stepped 100/500/1000 lock."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import backtest_st_ema20_variable_profit_ladders as base

OUT=Path("analysis/st_ema20_failed_entry_exits_1h")
LADDER_ID="L05_100_500_1000"
INTERPRETATION="behind"

# Fixed a priori; no data-dependent retuning. hard_stop_points, after_minutes,
# min_favorable_before_minutes, hourly_ema_fail_closes.
SCENARIOS={
    "baseline": (None,None,None,None),
    "hard300": (300,None,None,None),
    "hard500": (500,None,None,None),
    "hard800": (800,None,None,None),
    "hard1200": (1200,None,None,None),
    "hard2000": (2000,None,None,None),
    "time120_mfe200": (None,120,200,None),
    "time240_mfe200": (None,240,200,None),
    "time240_mfe300": (None,240,300,None),
    "time240_mfe500": (None,240,500,None),
    "time480_mfe200": (None,480,200,None),
    "time480_mfe300": (None,480,300,None),
    "time480_mfe500": (None,480,500,None),
    "hourly_ema1": (None,None,None,1),
    "hourly_ema2": (None,None,None,2),
    "hybrid_hard800_time240mfe300": (800,240,300,None),
    "hybrid_hard800_ema1": (800,None,None,1),
    "hybrid_time240mfe300_ema1": (None,240,300,1),
}


def check_hard_stop(side,opened,high,low,level,entry_minute):
    if level is None:
        return None
    touched=(low<=level) if side==1 else (high>=level)
    if not touched:
        return None
    if entry_minute:
        return float(level)
    return float(min(opened,level) if side==1 else max(opened,level))


def unit_tests():
    assert check_hard_stop(1,110,130,104,105,False)==105.
    assert check_hard_stop(1,90,130,80,105,False)==90.
    assert check_hard_stop(-1,102,130,70,95,False)==102.
    assert check_hard_stop(1,100,120,90,95,True)==95.
    assert check_hard_stop(1,120,130,110,95,False) is None
    levels=base.EXTENDED[LADDER_ID]
    assert base.desired_lock(499,levels,INTERPRETATION) is None
    assert base.desired_lock(500,levels,INTERPRETATION)==100.
    assert base.desired_lock(1000,levels,INTERPRETATION)==500.
    assert base.desired_lock(1500,levels,INTERPRETATION)==1000.


def replay(m,h,entries,mode,config):
    hard_points,delay_m,favorable_required,ema_closes=SCENARIOS[config]
    op=m.open.to_numpy(float);hi=m.high.to_numpy(float);lo=m.low.to_numpy(float)
    close=m.close.to_numpy(float);times=m.index
    hside=h.side.to_numpy();hclose=h.close.to_numpy(float);hema=h.ema.to_numpy(float)
    total=len(op);n_hours=len(h)
    levels=base.EXTENDED[LADDER_ID]
    trades=[];cash=base.START_USD;peak=base.START_USD
    worst_mark=base.START_USD;max_excursion=0.
    open_trade=None

    for event in entries:
        side=event["side"];j0=event["entry_j"];entry=event["entry"]
        hard_level=entry-side*hard_points if hard_points is not None else None
        lock_stop=None
        stop=hard_level
        favorable_high=0.;max_adverse=0.;locked_points=0.;upgrades=0
        ema_bad_count=0
        flip_j=total
        for hour in range(j0//60+1,n_hours):
            if int(hside[hour-1])!=side:
                flip_j=hour*60
                break

        exit_j=None;exit_mid=None;exit_reason=None
        for j in range(j0,min(flip_j,total)):
            if j==j0:
                # Ambiguous entry minute: conservatively allow the hard stop to
                # execute, not a profitable lock/price excursion.
                price=check_hard_stop(side,op[j],hi[j],lo[j],hard_level,True)
                if price is not None:
                    exit_j=j;exit_mid=price;exit_reason="hard_stop";break
                continue

            if j%60==0 and lock_stop is None and ema_closes is not None:
                completed_hour=(j//60)-1
                if side*(hclose[completed_hour]-hema[completed_hour])<0:
                    ema_bad_count+=1
                else:
                    ema_bad_count=0
                if ema_bad_count>=ema_closes:
                    exit_j=j;exit_mid=float(op[j]);exit_reason="hourly_ema_invalidation";break

            if lock_stop is None and delay_m is not None and j-j0>=delay_m and favorable_high<favorable_required:
                exit_j=j;exit_mid=float(op[j]);exit_reason="no_progress_timeout";break

            price=check_hard_stop(side,op[j],hi[j],lo[j],stop,False)
            if price is not None:
                exit_j=j;exit_mid=price
                exit_reason="profit_lock" if lock_stop is not None else "hard_stop"
                break

            favorable_px=hi[j] if side==1 else lo[j]
            adverse_px=lo[j] if side==1 else hi[j]
            favorable=max(0.,side*(favorable_px-entry))
            adverse=max(0.,side*(entry-adverse_px))
            favorable_high=max(favorable_high,favorable)
            max_adverse=max(max_adverse,adverse)
            hypo_exit=adverse_px-side*base.SLIP
            marked=cash+base.QTY*side*(hypo_exit-entry)-base.QTY*base.FEE*(entry+hypo_exit)
            worst_mark=min(worst_mark,marked)
            max_excursion=max(max_excursion,peak-marked)

            requested_lock=base.desired_lock(favorable_high,levels,INTERPRETATION)
            if requested_lock is not None and requested_lock>locked_points:
                # Lock becomes active in the next 1m bar, never retroactively.
                locked_points=requested_lock
                lock_stop=entry+side*locked_points
                stop=lock_stop
                upgrades+=1

        if exit_j is None and flip_j<total:
            exit_j=flip_j;exit_mid=float(op[flip_j]);exit_reason="supertrend_flip"

        if exit_j is None:
            exit_hypo=float(close[-1])-side*base.SLIP
            unrealized=base.QTY*side*(exit_hypo-entry)-base.QTY*base.FEE*(entry+exit_hypo)
            open_trade=dict(entry_utc=str(times[j0]),
                entry_price=round(entry,2),side="LONG" if side==1 else "SHORT",
                locked_profit_points=locked_points,hypothetical_net_usd=round(unrealized,5),
                note="Not closed by actual strategy. Hypothetical liquidation not modeled.")
            continue

        exit_fill=exit_mid-side*base.SLIP
        gross=base.QTY*side*(exit_fill-entry)
        fees=base.QTY*base.FEE*(entry+exit_fill)
        net=gross-fees
        trades.append(dict(
            mode=mode,config=config,setup=event["kind"],
            side="LONG" if side==1 else "SHORT",
            entry_utc=str(times[j0]),signal_utc=event["signal"],
            exit_utc=str(times[exit_j]),
            entry_price=round(entry,2),exit_price=round(exit_fill,2),
            hard_stop_points=hard_points,locked_points=locked_points,
            stop_upgrades=upgrades,
            hold_minutes=exit_j-j0,
            gross_usd=round(gross,6),fees_usd=round(fees,6),net_usd=round(net,6),
            exit_reason=exit_reason,
            max_favorable_points=round(favorable_high,2),
            max_adverse_points=round(max_adverse,2)))
        cash+=net;peak=max(peak,cash)

    frame=pd.DataFrame(trades)
    counts=frame.exit_reason.value_counts().to_dict() if len(frame) else {}
    return frame,dict(
        config=config,
        rule=dict(hard_stop_points=hard_points,timeout_minutes=delay_m,
                  min_favorable_points=favorable_required,ema_fail_closes=ema_closes),
        exit_counts={k:int(v) for k,v in counts.items()},
        open_trade=open_trade,
        worst_open_mark_equity_usd=round(worst_mark,4),
        max_excursion_below_previous_realized_peak_usd=round(max_excursion,4),
        note="Only new exits prior to first profit-lock; 1m price execution, historical no funding/liquidation")


def impacts(old_trades,new_trades):
    original={r.entry_utc:r for r in old_trades.itertuples(index=False)}
    current={r.entry_utc:r for r in new_trades.itertuples(index=False)}
    old_flips=[v for v in original.values() if v.exit_reason=="supertrend_flip"]
    old_locks=[v for v in original.values() if v.exit_reason=="profit_lock"]
    def group(a):
        usable=[(old,current[x.entry_utc]) for old in a if x_in_current(x=old,current=current)]
        original_pnl=sum(float(p.net_usd) for p,_ in usable)
        new_pnl=sum(float(q.net_usd) for _,q in usable)
        improved=sum(float(q.net_usd)>float(p.net_usd)+1e-8 for p,q in usable)
        worsened=sum(float(q.net_usd)<float(p.net_usd)-1e-8 for p,q in usable)
        return dict(n=len(usable),original_net_usd=round(original_pnl,4),new_net_usd=round(new_pnl,4),
                    improvement_usd=round(new_pnl-original_pnl,4),
                    improved_count=improved,worsened_count=worsened)
    return dict(original_flip_group=group(old_flips),original_lock_group=group(old_locks))


def x_in_current(x,current):
    return x.entry_utc in current


def main():
    unit_tests()
    m,h,nfiles=base.load()
    h=base.features(h)
    OUT.mkdir(parents=True,exist_ok=True)
    entries={mode:base.entry_candidates(m,h,mode) for mode in ("touch","reclaim","combined")}
    quality=dict(
        source="Delta Exchange India BTCUSD perpetual 1m OHLCV",source_files=nfiles,
        minute_bars=len(m),hourly_bars=len(h),
        first_utc=str(m.index[0]),last_utc=str(m.index[-1]),
        validated_consecutive_minutes=True,
        initial_cash_usd=base.START_USD,quantity_btc=base.QTY,
        fee_plus_GST_per_side=base.FEE,slippage_points_per_side=base.SLIP,
        baseline_ladder=[100,500,1000],
        baseline_first_lock_trigger=500,baseline_first_lock_points=100,
        no_fixed_take_profit=True,
        strategies=list(SCENARIOS.keys()),entry_modes=list(entries.keys()),
        lookahead_safe=True,one_filled_trade_per_supertrend_cycle=True,
        caveats=[
            "Exploratory only; baseline 61 failures were known in advance, not an untouched holdout",
            "No funding, liquidation, mark price, real bid-ask, latency or broker margin modeling",
            "A fixed stop can gap through the stop price. Entry-bar stop touch is conservatively executed",
            "Time/EMA stop only when no profit lock already activated",
            "Monthly P&L is assigned to IST EXIT month, November 2026 partial"]
    )
    (OUT/"quality.json").write_text(json.dumps(quality,indent=2)+"\n")
    summaries={}
    rows=[]
    for mode,evs in entries.items():
        orig,orig_extra=base.replay(m,h,evs,mode,LADDER_ID,INTERPRETATION)
        prior=dict(original_total=round(float(orig.net_usd.sum()),4),
                   original_trades=len(orig),
                   original_flips=int((orig.exit_reason=="supertrend_flip").sum()))
        assert len(orig)==len(evs) or orig_extra["open_trade"] is not None
        assert mode!="touch" or (len(orig)==253 and prior["original_flips"]==61
                 and abs(prior["original_total"]-1.2527)<.00015),(
                     "Exact baseline parity failed; abandon backtest",mode,prior)

        for config in SCENARIOS:
            t,extra=replay(m,h,evs,mode,config)
            if config=="baseline":
                assert len(t)==len(orig),("baseline trade count mismatch",mode)
                assert abs(t.net_usd.sum()-orig.net_usd.sum())<.00005,(
                     "baseline pnl mismatch",mode,t.net_usd.sum(),orig.net_usd.sum())
                assert (t.exit_reason.values==orig.exit_reason.values).all(),(
                     "baseline exit reason mismatch",mode)
            t.to_csv(OUT/f"{mode}_{config}_trades.csv",index=False)
            month=base.monthly(t,m.index[0],m.index[-1])
            month.to_csv(OUT/f"{mode}_{config}_monthly_ist.csv",index=False)
            summary=base.summarize(t,extra)
            summary["profitable_full_months"]=int(((month.net_usd>0)&month.complete_month).sum())
            summary["total_full_months"]=int(month.complete_month.sum())
            effects=impacts(orig,t)
            summary["impacts_vs_prior"]=effects
            key=f"{mode}_{config}"
            summaries[key]=summary
            rows.append(dict(
                mode=mode,config=config,
                trades=summary.get("closed_trades"),
                wins=summary.get("wins"),loses=summary.get("losses"),
                win_rate_pct=summary.get("win_rate_pct"),
                gross_usd=summary.get("gross_usd"),
                fees_usd=summary.get("fees_usd"),
                net_usd=summary.get("realized_net_usd"),
                profit_factor=summary.get("profit_factor"),
                max_realized_dd_pct=summary.get("realized_max_drawdown_pct"),
                profitable_full_months=summary.get("profitable_full_months"),
                remaining_st_flip_exits=extra["exit_counts"].get("supertrend_flip",0),
                hard_stop_exits=extra["exit_counts"].get("hard_stop",0),
                timeout_exits=extra["exit_counts"].get("no_progress_timeout",0),
                ema_invalid_exits=extra["exit_counts"].get("hourly_ema_invalidation",0),
                lock_exits=extra["exit_counts"].get("profit_lock",0),
                prior61_pnl_now_usd=effects["original_flip_group"]["new_net_usd"],
                prior61_pnl_change_usd=effects["original_flip_group"]["improvement_usd"],
                prior192_pnl_change_usd=effects["original_lock_group"]["improvement_usd"],
                prior61_improved_trades=effects["original_flip_group"]["improved_count"],
                prior61_worsened_trades=effects["original_flip_group"]["worsened_count"]))
            print(key,json.dumps({
                "net_usd":summary.get("realized_net_usd"),
                "months":summary["profitable_full_months"],
                "rem_flips":extra["exit_counts"].get("supertrend_flip",0),
                "prior61_change":effects["original_flip_group"]["improvement_usd"],
                "prior192_change":effects["original_lock_group"]["improvement_usd"]
            }),flush=True)
    pd.DataFrame(rows).to_csv(OUT/"comparison.csv",index=False)
    (OUT/"summary.json").write_text(json.dumps(summaries,indent=2)+"\n")


if __name__=="__main__":
    main()
