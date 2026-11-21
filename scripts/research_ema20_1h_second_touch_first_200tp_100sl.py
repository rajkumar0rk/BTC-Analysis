#!/usr/bin/env python3
"""First-hit analysis: unchanged 1H Supertrend/EMA20 second-touch entry,
fixed TP +200 vs SL -100, original BTC price points or scaled ETH equivalent.
Compare barrier-only versus confirmed Supertrend flip exits; model two 1m OHLC
continuous intraminute paths since historical ticks are unavailable.
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from research_ema20_second_touch import read_source, features, MONTHS, FEE, SLIP

OUT=Path("analysis/ema20_1h_second_touch_200tp_100sl_first_hit_20261121")
TF=60
TP_BTC=200.
SL_BTC=100.
INITIAL=1000.
PATHS=("O-H-L-C","O-L-H-C")
MODES=("BARRIER_ONLY","FLIP_EXIT")

def stamp(x):
    return pd.Timestamp(int(x),unit="s",tz="UTC")

def run(df,symbol,btc_prior,mode,path_name):
    if mode not in MODES or path_name not in PATHS:
        raise AssertionError((mode,path_name))
    ema,_,st,valid=features(df,TF)
    t=df.time.to_numpy(dtype=np.int64)
    o=df.open.to_numpy(float)
    h=df.high.to_numpy(float)
    l=df.low.to_numpy(float)
    c=df.close.to_numpy(float)
    assert len(t)==len(btc_prior) and t[0]%(TF*60)==0

    month_end_idx={}
    for month in MONTHS:
        p=pd.Period(month,freq="M")
        end=(p+1).start_time.tz_localize("Asia/Kolkata").tz_convert("UTC")-pd.Timedelta(minutes=1)
        ix=int(np.searchsorted(t,int(end.timestamp()),side="right")-1)
        if ix<0 or t[ix]!=int(end.timestamp()):
            raise AssertionError("Month-end 1m candle missing "+month)
        month_end_idx[ix]=month

    cash=INITIAL
    pos=None
    prev_trend=0
    epoch=0
    traded_epochs=set()
    last_touch_h=-1
    touches_count=0
    trade_rows=[]
    month_rows=[]
    worst_eq=INITIAL
    peak_eq=INITIAL
    max_dd=0.
    first_negative=None
    ambiguous_exit_bar_count=0
    first_touch_events=0
    max_hold=0.
    total_flips=0

    def equity_if_mark(raw):
        if pos is None:
            return cash
        s=pos["side"]
        hypothetical_exit=raw*(1-s*SLIP)
        return (cash+s*pos["qty"]*(hypothetical_exit-pos["entry"])
              -FEE*pos["qty"]*hypothetical_exit)

    def mark(raw,now):
        nonlocal worst_eq,peak_eq,max_dd,first_negative
        eq=equity_if_mark(raw)
        worst_eq=min(worst_eq,eq)
        peak_eq=max(peak_eq,eq)
        if peak_eq>0:
            max_dd=max(max_dd,100.*(peak_eq-eq)/peak_eq)
        if first_negative is None and eq<=0:
            first_negative=stamp(now).isoformat()

    def close_position(raw,now,why,minute_index):
        nonlocal pos,cash,max_hold,ambiguous_exit_bar_count
        p=pos
        assert p is not None
        side=p["side"]
        exit_fill=raw*(1-side*SLIP)
        gross=side*p["qty"]*(exit_fill-p["entry"])
        exit_fee=FEE*p["qty"]*exit_fill
        net=gross-p["entry_fee"]-exit_fee
        cash+=gross-exit_fee
        held=(now-p["entry_at"])/3600.
        max_hold=max(max_hold,held)
        both=bool(h[minute_index]>=max(p["tp"],p["sl"]) and
                  l[minute_index]<=min(p["tp"],p["sl"]))
        if why in ("TP200","SL100") and both:
            ambiguous_exit_bar_count+=1
        trade_rows.append(dict(symbol=symbol,variant=mode,ohlc_path=path_name,
            epoch=p["epoch"],entry_utc=stamp(p["entry_at"]).isoformat(),
            exit_utc=stamp(now).isoformat(),
            month_ist=stamp(now).tz_convert("Asia/Kolkata").strftime("%Y-%m"),
            side=("LONG" if side==1 else "SHORT"),entry_fill=p["entry"],
            target_price=p["tp"],stop_price=p["sl"],exit_fill=exit_fill,
            exit_reason=why,exit_minute_spans_both_tp_and_sl=both,
            tp_BTC_points=TP_BTC,sl_BTC_points=SL_BTC,btc_reference=p["btc_prior"],
            net_usd=net,fees_gst_usd=p["entry_fee"]+exit_fee,
            cash_after=cash,hours_held=held))
        pos=None

    def walk(a,b,now,i):
        nonlocal pos
        p=pos
        if p is None:
            return
        side=p["side"]
        tp,sl=p["tp"],p["sl"]
        # The segment is monotonic, so only one of two opposite barriers
        # can be FIRST in it. Gap at its first price is handled explicitly.
        if side*(a-tp)>=0:
            close_position(tp,now,"TP200",i)
            return
        if side*(a-sl)<=0:
            close_position(a,now,"SL100",i)
            return
        if side*(b-a)>0 and side*(b-tp)>=0:
            close_position(tp,now,"TP200",i)
        elif side*(b-a)<0 and side*(b-sl)<=0:
            close_position(sl,now,"SL100",i)
        else:
            mark(b,now)

    for i in range(len(t)):
        hour=i//TF
        last=hour-1
        if last<100 or last>=len(ema) or not valid[last] or int(st[last])==0:
            continue
        direction=int(st[last])
        now=int(t[i])
        if direction!=prev_trend:
            if pos is not None and mode=="FLIP_EXIT":
                assert pos["side"]==-direction
                close_position(float(o[i]),now,"SUPERTREND_FLIP",i)
                total_flips+=1
            epoch+=1
            prev_trend=direction
            last_touch_h=-1
            touches_count=0

        path=(o[i],h[i],l[i],c[i]) if path_name=="O-H-L-C" else (o[i],l[i],h[i],c[i])
        if pos is not None:
            # Across 1m candles, open can gap beyond TP/SL.
            walk(float(path[0]),float(path[0]),now,i)
        mark(float(path[0]),now)

        for j in range(3):
            a,b=float(path[j]),float(path[j+1])
            if pos is not None:
                walk(a,b,now,i)
                continue
            if cash<=0 or epoch in traded_epochs or last_touch_h==hour:
                continue
            ema_level=float(ema[last])
            if not np.isfinite(ema_level) or not(min(a,b)<=ema_level<=max(a,b)):
                mark(b,now)
                continue
            last_touch_h=hour
            touches_count+=1
            first_touch_events+=1
            if touches_count<2:
                mark(b,now)
                continue

            assert touches_count==2
            if epoch in traded_epochs:
                raise AssertionError("Repeat entry in same Supertrend epoch")
            entry=ema_level*(1+direction*SLIP)
            btc_ref=float(btc_prior[i])
            if not np.isfinite(btc_ref) or btc_ref<=0:
                raise AssertionError("No completed BTC reference minute")
            d_tp=(TP_BTC if symbol=="BTCUSD" else TP_BTC*entry/btc_ref)
            d_sl=(SL_BTC if symbol=="BTCUSD" else SL_BTC*entry/btc_ref)
            qty=cash/entry
            entry_fee=FEE*qty*entry
            cash-=entry_fee
            pos=dict(side=direction,entry=entry,qty=qty,
                tp=entry+direction*d_tp,sl=entry-direction*d_sl,
                entry_fee=entry_fee,entry_at=now,epoch=epoch,btc_prior=btc_ref)
            traded_epochs.add(epoch)
            touches_count=0
            mark(ema_level,now)
            # Enter on first path-segment crossing of the second touch EMA.
            # Continue only remaining segment (rather than use entire minute
            # high/low, which would be pre-entry lookahead).
            walk(ema_level,b,now,i)

        if i in month_end_idx:
            month_rows.append(dict(symbol=symbol,variant=mode,ohlc_path=path_name,
                month_ist=month_end_idx[i],
                equity_mark_usd=equity_if_mark(float(c[i])),
                position_open=(pos is not None),realized_cash_usd=cash))

    if pos is not None:
        close_position(float(c[-1]),int(t[-1]),"SAMPLE_END_ACCOUNTING_ONLY",len(t)-1)
        month_rows[-1]["equity_mark_usd"]=cash
    assert len(month_rows)==22
    trades=pd.DataFrame(trade_rows)
    months=pd.DataFrame(month_rows)
    assert not trades.empty
    assert not trades.epoch.duplicated().any()
    assert abs(float(trades.net_usd.sum())-(cash-INITIAL))<0.01
    months["return_pct"]=(100*months.equity_mark_usd/
        months.equity_mark_usd.shift(1,fill_value=INITIAL)-100)
    n_tp=int((trades.exit_reason=="TP200").sum())
    n_sl=int((trades.exit_reason=="SL100").sum())
    n_flip=int((trades.exit_reason=="SUPERTREND_FLIP").sum())
    n_sample=int((trades.exit_reason=="SAMPLE_END_ACCOUNTING_ONLY").sum())
    assert n_tp+n_sl+n_flip+n_sample==len(trades)
    positive=trades.loc[trades.net_usd>0,"net_usd"].sum()
    negative=-trades.loc[trades.net_usd<0,"net_usd"].sum()
    year25=float(months.loc[months.month_ist=="2025-12","equity_mark_usd"].iloc[0])
    summary=dict(symbol=symbol,variant=mode,path_assumption=path_name,
        trades=len(trades),tp200_hit_first=n_tp,sl100_hit_first=n_sl,
        supertrend_flip_first=n_flip,sample_end_forced=n_sample,
        tp_first_pct_of_entries=round(100*n_tp/len(trades),3),
        tp_first_pct_of_resolved_barriers=round(100*n_tp/(n_tp+n_sl),3) if n_tp+n_sl else None,
        sl_first_pct_of_entries=round(100*n_sl/len(trades),3),
        same_1m_bar_spanned_both_exit_barriers=ambiguous_exit_bar_count,
        after_cost_winning_trades=int((trades.net_usd>0).sum()),
        after_cost_losing_trades=int((trades.net_usd<0).sum()),
        after_cost_win_rate_pct=round(100*(trades.net_usd>0).mean(),3),
        profit_factor=round(float(positive/negative),4) if negative>0 else None,
        modeled_net_usd=round(cash-INITIAL,4),
        modeled_net_return_pct=round(100*(cash/INITIAL-1),4),
        max_floating_drawdown_pct=round(max_dd,4),
        min_floating_equity_usd=round(worst_eq,4),
        floating_equity_reached_zero=first_negative is not None,
        first_zero_utc=first_negative,
        positive_months=int((months.return_pct>0).sum()),
        negative_months=int((months.return_pct<0).sum()),
        return_2025_pct=round(100*(year25/INITIAL-1),4),
        return_2026_jan_oct_pct=round(100*(cash/year25-1),4),
        max_hold_hours=round(max_hold,3),
        supertrend_epochs=epoch,epochs_with_entry=len(traded_epochs),
        ema_touch_events=first_touch_events,
        fee_gst_usd=round(float(trades.fees_gst_usd.sum()),4),
        is_tick_exact=False)
    return trades,months,summary

def self_test():
    # Monotone synthetic path. A $200 target and $100 stop both lie
    # inside minute range. Outcome changes when H or L happens first.
    entry=80000.
    tp=entry+TP_BTC
    sl=entry-SL_BTC
    assert sl==79900 and tp==80200
    for path,first in [([80000,80220,79880,80000],"TP200"),
                       ([80000,79880,80220,80000],"SL100")]:
        assert max(path)>=tp and min(path)<=sl
        assert (("TP200" if path[1]>=tp else "SL100"))==first
    print("SELF_TEST_OK: 80200 TP vs 79900 SL, O-H-L-C may differ O-L-H-C",flush=True)

def main():
    self_test()
    OUT.mkdir(parents=True,exist_ok=True)
    btc,bq=read_source("BTCUSD")
    eth,eq=read_source("ETHUSD")
    assert np.array_equal(btc.time.to_numpy(dtype=np.int64),
                          eth.time.to_numpy(dtype=np.int64))
    btc_prior=np.r_[np.nan,btc.close.to_numpy(dtype=float)[:-1]]
    all_trades=[]
    all_months=[]
    summary=[]
    for mode in MODES:
        for path in PATHS:
            for symbol,df in (("BTCUSD",btc),("ETHUSD",eth)):
                print("RUN",symbol,mode,path,flush=True)
                trades,months,row=run(df,symbol,btc_prior,mode,path)
                all_trades.append(trades)
                all_months.append(months)
                summary.append(row)
                print("RESULT",json.dumps(row,sort_keys=True,default=str),flush=True)
    pd.concat(all_trades,ignore_index=True).to_csv(OUT/"trade_ledger.csv.gz",compression="gzip",index=False)
    pd.concat(all_months,ignore_index=True).to_csv(OUT/"monthly_mark_to_market.csv",index=False)
    pd.DataFrame(summary).to_csv(OUT/"summary.csv",index=False)
    meta=dict(source={"BTCUSD":bq,"ETHUSD":eq},
        entry="same 1H EMA20 2nd distinct touch after confirmed Supertrend10,3 flip, one entry per epoch",
        first_passage="first TP +200 BTC points OR SL -100 BTC points, both sides mirrored",
        eth_distances="200/100 * executed ETH entry / previous completed BTC 1m close, frozen at entry",
        modes=list(MODES),paths=list(PATHS),
        data="1m OHLC, no full-sample historical ticks",
        warning="Within-minute O-H-L-C vs O-L-H-C invented paths, not real tick sequence",
        fees={"taker_side":0.0005,"GST_on_fee":0.18,"adverse_slippage_side":SLIP},
        excluded=["funding","margin and liquidation","real bid ask","latency","orderbook"],
        historical_period="Jan 2025 to Oct 2026 IST, 22 months, first 5h30m Jan 1 not sourced")
    (OUT/"quality.json").write_text(json.dumps(meta,indent=2)+"\n")
    lines=[
      "# Same 1H second-touch entry: TP200 reached before SL100?",
      "",
      "**TP and SL are fixed price barriers, not 200-step ratchet and not trail.**",
      "Two exit variants: barrier-only answers price-event race, and flip-exit applies the current mandatory confirmed 1H Supertrend flip rule.",
      "All results rely on hypothetical 1m paths, not historical ticks; even 1m OHLC cannot always resolve which level was hit first.",
      "",
      "| Mode | 1m hypothetical path | Asset | Trades | TP +200 first | SL -100 first | ST flip first | TP % all entries | TP % resolved barriers | Both levels in exit 1m |",
      "|---|---|---|---:|---:|---:|---:|---:|---:|---:|"
    ]
    for v in summary:
        lines.append(f"| {v['variant']} | {v['path_assumption']} | {v['symbol']} | {v['trades']} | {v['tp200_hit_first']} | {v['sl100_hit_first']} | {v['supertrend_flip_first']} | {v['tp_first_pct_of_entries']}% | {v['tp_first_pct_of_resolved_barriers']}% | {v['same_1m_bar_spanned_both_exit_barriers']} |")
    lines+=["","## Caveats",
      "- No fixed TP optimization, one entry per trend epoch exactly as present strategy; EMA touch within second 1H candle on 1m raw OHLC.",
      "- ETH distances proportionally scaled to BTC at entry, not absolute ETH price points.",
      "- O-H-L-C and O-L-H-C are invented hypothetical price sequences and are not rigorous bounds; actual 1m path is not known.",
      "- Includes illustrative taker fees, 18% GST and 0.02% adverse slippage; excludes funding, real tick execution and liquidation.",
      "- A Supertrend flip exit is **not** counted as TP nor SL; it is distinct in FLIP_EXIT variant.",
      "- 2026 historical data was used in prior research and is not an out-of-sample validation.",
      "","Files: summary.csv, monthly_mark_to_market.csv, trade_ledger.csv.gz, quality.json."]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(lines)+"\n")
    print("BACKTEST_DONE",len(summary),flush=True)

if __name__=="__main__":
    main()
