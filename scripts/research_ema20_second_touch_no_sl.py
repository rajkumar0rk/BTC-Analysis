#!/usr/bin/env python3
"""15M Supertrend EMA20 second touch + volume/volatility; TP only, NO STOP.
Research-only; 1m OHLC cannot prove live fills, actual margin, liquidation, funding.
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from research_ema20_second_touch import read_source, features, MONTHS, FEE, SLIP

OUT=Path("analysis/ema20_second_touch_no_sl_20261121")
INITIAL=1000.0
VOL_RATIO_MIN=1.20
ATR_RATIO_MIN=1.0
TF=15

def model(bars, btc_prev, symbol):
    ema,atr,st,good=features(bars,TF)
    o=bars.open.to_numpy(float)
    hi=bars.high.to_numpy(float)
    lo=bars.low.to_numpy(float)
    cl=bars.close.to_numpy(float)
    ts=bars.time.to_numpy("int64")
    vbars=bars.resample("15min",label="left",closed="left").agg({"volume":"sum","close":"count"})
    v=vbars.volume.to_numpy(float)
    vcount=vbars.close.to_numpy("int64")
    vmean=pd.Series(v).shift(1).rolling(20,min_periods=20).mean().to_numpy()
    amean=pd.Series(atr).shift(1).rolling(20,min_periods=20).mean().to_numpy()
    assert len(v)==len(ema) and len(atr)==len(st)
    assert len(btc_prev)==len(ts)

    # Month-end last 1m bars in IST, with a frozen point-in-time equity snapshot
    monthends={}
    for m in MONTHS:
        p=pd.Period(m,freq="M")
        last=(p+1).start_time.tz_localize("Asia/Kolkata").tz_convert("UTC")-pd.Timedelta(minutes=1)
        k=int(np.searchsorted(ts,int(last.timestamp()),side="right")-1)
        if k<0 or ts[k]!=int(last.timestamp()):
            raise AssertionError("Missing final IST minute for "+m)
        monthends[k]=m

    balance=INITIAL # cash equity after fees on open trade, before its floating PnL
    peak=INITIAL
    worst_mtm=INITIAL
    max_mtm_dd=0.
    crossed_zero=False
    first_inso_time=None
    month_snapshots={}
    count=0
    last_touch_bar=-1
    last_direction=0
    pos=None
    trades=[]
    rejected=0
    touches=0
    max_adverse_points=0.
    max_adverse_pct=0.
    for i in range(len(bars)):
        b=i//TF
        last=b-1
        t=int(ts[i])
        if last>=100 and last<len(ema) and good[last] and st[last]!=0:
            direction=int(st[last])
            if last_direction!=direction:
                count=0
                last_touch_bar=-1
                last_direction=direction
            if pos is not None:
                side=pos["side"]
                # The TP-hit 1m candle may also have moved deeply against us.
                # Include the adverse wick in each trade's MAE before exiting,
                # rather than silently omitting same-bar adverse excursion.
                adverse_now=(max(0.,pos["entry"]-lo[i]) if side==1
                             else max(0.,hi[i]-pos["entry"]))
                pos["mae_pts"]=max(pos["mae_pts"],adverse_now)
                pos["mae_pct"]=max(pos["mae_pct"],100*adverse_now/pos["entry"])
                max_adverse_points=max(max_adverse_points,adverse_now)
                max_adverse_pct=max(max_adverse_pct,pos["mae_pct"])
                # No SL, and no Supertrend reversal/timeout exit.
                # TP only on strictly subsequent 1m bars.
                tgt=pos["target"]
                if i>pos["entry_idx"] and ((side==1 and hi[i]>=tgt) or (side==-1 and lo[i]<=tgt)):
                    # Limit target price, no favorable gap price improvement.
                    fill=tgt*(1-side*SLIP)
                    gross=side*pos["qty"]*(fill-pos["entry"])
                    exit_fee=FEE*pos["qty"]*fill
                    pnl=gross-exit_fee-pos["entry_fee"]
                    balance+=gross-exit_fee
                    trades.append(dict(symbol=symbol,timeframe="15m",
                        entry_time_utc=pd.Timestamp(pos["entry_ts"],unit="s",tz="UTC").isoformat(),
                        exit_time_utc=pd.Timestamp(t,unit="s",tz="UTC").isoformat(),
                        exit_month_ist=pd.Timestamp(t,unit="s",tz="UTC").tz_convert("Asia/Kolkata").strftime("%Y-%m"),
                        direction="LONG" if side==1 else "SHORT",
                        entry=pos["entry"],exit=fill,qty=pos["qty"],take_profit_price=tgt,
                        tp_distance=pos["tpdist"],reference_btc_previous_close=pos["btc_ref"],
                        exit_reason="TP",
                        holding_hours=(t-pos["entry_ts"])/3600,
                        maximum_adverse_price_points=pos["mae_pts"],
                        maximum_adverse_price_pct=pos["mae_pct"],
                        gross_profit_usd=gross,total_fees_gst_usd=pos["entry_fee"]+exit_fee,
                        net_profit_usd=pnl,cash_equity_after=balance))
                    pos=None
                    count=0
                    last_touch_bar=b
            elif last_touch_bar!=b and np.isfinite(ema[last]):
                ema0=float(ema[last])
                if lo[i]<=ema0<=hi[i]:
                    touches+=1
                    count+=1
                    last_touch_bar=b
                    if count==2:
                        vv=float(vmean[last])
                        aa=float(amean[last])
                        valid_volume=(vcount[last]==TF and np.isfinite(vv) and vv>0 and
                            v[last]>=VOL_RATIO_MIN*vv)
                        valid_volatility=(np.isfinite(aa) and aa>0 and
                            np.isfinite(atr[last]) and atr[last]>=ATR_RATIO_MIN*aa)
                        count=0
                        if not(valid_volume and valid_volatility):
                            rejected+=1
                        else:
                            if balance<=0:
                                raise RuntimeError("Nonpositive cash account; cannot open a new 1x trade")
                            entry=ema0*(1+direction*SLIP)
                            btc_ref=float(btc_prev[i])
                            if not(np.isfinite(btc_ref) and btc_ref>0):
                                raise AssertionError("BTC reference unavailable")
                            tpdist=200. if symbol=="BTCUSD" else 200.*entry/btc_ref
                            qty=balance/entry
                            entry_fee=FEE*qty*entry
                            balance-=entry_fee
                            pos=dict(side=direction,entry=entry,qty=qty,
                                entry_fee=entry_fee,target=entry+direction*tpdist,
                                entry_ts=t,entry_idx=i,mae_pts=0.,mae_pct=0.,
                                btc_ref=btc_ref,tpdist=tpdist)

        if pos is not None:
            side=pos["side"]
            # Track full adverse entry-minute wick conservatively; true intraminute
            # ordering is unknown. Mark-to-market at close and worst intraminute wick.
            adverse=(max(0.,pos["entry"]-lo[i]) if side==1 else
                     max(0.,hi[i]-pos["entry"]))
            pos["mae_pts"]=max(pos["mae_pts"],adverse)
            pos["mae_pct"]=max(pos["mae_pct"],100*adverse/pos["entry"])
            max_adverse_points=max(max_adverse_points,adverse)
            max_adverse_pct=max(max_adverse_pct,pos["mae_pct"])
            close_fill=cl[i]*(1-side*SLIP)
            advers_raw=lo[i] if side==1 else hi[i]
            adverse_fill=advers_raw*(1-side*SLIP)
            close_equity=balance+side*pos["qty"]*(close_fill-pos["entry"])-FEE*pos["qty"]*close_fill
            worst_equity=balance+side*pos["qty"]*(adverse_fill-pos["entry"])-FEE*pos["qty"]*adverse_fill
        else:
            close_equity=balance
            worst_equity=balance

        # Realizable-account equity includes unclosed loss, opposite to a TP-only
        # ledger's often misleading win rate.
        peak=max(peak,close_equity)
        worst_mtm=min(worst_mtm,worst_equity)
        if peak>0:
            max_mtm_dd=max(max_mtm_dd,100*(peak-worst_equity)/peak)
        if worst_equity<=0 and not crossed_zero:
            crossed_zero=True
            first_inso_time=pd.Timestamp(t,unit="s",tz="UTC").isoformat()
        if i in monthends:
            month_snapshots[monthends[i]]=dict(
                month_ist=monthends[i],equity_mark_usd=close_equity,
                realized_cash_usd=balance,open_position_at_month_end=pos is not None,
                equity_min_adverse_seen_to_date=worst_mtm)

    # TP-only strategy does NOT exit until TP in live logic. Force close the
    # final remaining position solely for final-sample accounting, prominently labelled.
    sample_end_open=(pos is not None)
    if pos is not None:
        s=pos["side"]
        fill=float(cl[-1])*(1-s*SLIP)
        gross=s*pos["qty"]*(fill-pos["entry"])
        exit_fee=FEE*pos["qty"]*fill
        pnl=gross-exit_fee-pos["entry_fee"]
        balance+=gross-exit_fee
        trades.append(dict(symbol=symbol,timeframe="15m",
            entry_time_utc=pd.Timestamp(pos["entry_ts"],unit="s",tz="UTC").isoformat(),
            exit_time_utc=pd.Timestamp(int(ts[-1]),unit="s",tz="UTC").isoformat(),
            exit_month_ist=pd.Timestamp(int(ts[-1]),unit="s",tz="UTC").tz_convert("Asia/Kolkata").strftime("%Y-%m"),
            direction="LONG" if s==1 else "SHORT",
            entry=pos["entry"],exit=fill,qty=pos["qty"],
            take_profit_price=pos["target"],tp_distance=pos["tpdist"],
            reference_btc_previous_close=pos["btc_ref"],exit_reason="SAMPLE_END_FORCED",
            holding_hours=(int(ts[-1])-pos["entry_ts"])/3600,
            maximum_adverse_price_points=pos["mae_pts"],
            maximum_adverse_price_pct=pos["mae_pct"],
            gross_profit_usd=gross,total_fees_gst_usd=pos["entry_fee"]+exit_fee,
            net_profit_usd=pnl,cash_equity_after=balance))
        month_snapshots[MONTHS[-1]]["equity_mark_usd"]=balance
        month_snapshots[MONTHS[-1]]["realized_cash_usd"]=balance
        # Still flagged open at the natural test boundary, before forced close.

    ledger=pd.DataFrame(trades)
    assert not ledger.empty, "No TP or sample-end exits; cannot score"
    if abs(float(ledger.net_profit_usd.sum())-(balance-INITIAL))>0.01:
        raise AssertionError("PnL reconciliation failed")
    monthly=[]
    prev=INITIAL
    for m in MONTHS:
        mark=month_snapshots[m]
        x=ledger.loc[ledger.exit_month_ist==m]
        monthly.append(dict(symbol=symbol,month_ist=m,
            exits=len(x),take_profit_exits=int((x.exit_reason=="TP").sum()),
            forced_end_exits=int((x.exit_reason=="SAMPLE_END_FORCED").sum()),
            positive_exits=int((x.net_profit_usd>0).sum()),
            realized_trade_pnl_usd=float(x.net_profit_usd.sum()),
            equity_mark_usd=round(mark["equity_mark_usd"],6),
            equity_monthly_mark_return_pct=round(100*(mark["equity_mark_usd"]/prev-1),6) if prev>0 else None,
            cash_usd=round(mark["realized_cash_usd"],6),
            open_position_at_month_end=mark["open_position_at_month_end"]))
        prev=mark["equity_mark_usd"]
    wins=ledger.loc[ledger.net_profit_usd>0,"net_profit_usd"]
    losses=ledger.loc[ledger.net_profit_usd<0,"net_profit_usd"]
    pf=float(wins.sum())/abs(float(losses.sum())) if len(losses) else None
    count_month_pos=sum(x["equity_monthly_mark_return_pct"] is not None and x["equity_monthly_mark_return_pct"]>0 for x in monthly)
    summary=dict(symbol=symbol,timeframe="15m",sl_enabled=False,
        vol_filter_enabled=True,volatility_filter_enabled=True,
        entries=len(ledger),take_profit_exits=int((ledger.exit_reason=="TP").sum()),
        sample_end_forced_exits=int((ledger.exit_reason=="SAMPLE_END_FORCED").sum()),
        net_profitable_closed_exits=int((ledger.net_profit_usd>0).sum()),
        net_unprofitable_closed_exits=int((ledger.net_profit_usd<0).sum()),
        win_rate_closed_pct=round(100*float((ledger.net_profit_usd>0).mean()),3),
        profit_factor_with_end_close=round(pf,4) if pf is not None else None,
        net_model_pnl_usd=round(balance-INITIAL,5),
        net_model_return_pct=round(100*(balance/INITIAL-1),5),
        estimated_mark_to_market_max_dd_pct=round(max_mtm_dd,4),
        minimum_mark_to_market_equity_usd=round(worst_mtm,4),
        estimated_equity_at_or_below_zero=crossed_zero,
        first_at_or_below_zero_utc=first_inso_time,
        max_adverse_price_points=round(max_adverse_points,4),
        max_adverse_price_pct=round(max_adverse_pct,4),
        longest_holding_hours=round(float(ledger.holding_hours.max()),2),
        median_holding_hours=round(float(ledger.holding_hours.median()),2),
        average_holding_hours=round(float(ledger.holding_hours.mean()),2),
        profitable_months_mark_to_market=count_month_pos,
        losing_months_mark_to_market=sum(x["equity_monthly_mark_return_pct"] is not None and x["equity_monthly_mark_return_pct"]<0 for x in monthly),
        filtered_second_touch_rejections=rejected,
        total_first_and_second_eligible_touches=touches,
        sample_end_position_open=sample_end_open,
        fees_gst_usd=round(float(ledger.total_fees_gst_usd.sum()),5))
    return ledger,monthly,summary

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    btc,quality_btc=read_source("BTCUSD")
    eth,quality_eth=read_source("ETHUSD")
    if not np.array_equal(btc.time.to_numpy(),eth.time.to_numpy()):
        raise AssertionError("Price timelines do not align")
    previous_btc=np.r_[np.nan,btc.close.to_numpy(float)[:-1]]
    logs=[]; monthly=[]; summary=[]
    for symbol,df in (("BTCUSD",btc),("ETHUSD",eth)):
        print("RUN",symbol,flush=True)
        ledger,mm,ss=model(df,previous_btc,symbol)
        logs.append(ledger);monthly.extend(mm);summary.append(ss)
        print("RESULT",json.dumps(ss,sort_keys=True),flush=True)
    pd.concat(logs,ignore_index=True).to_csv(OUT/"trade_ledger.csv.gz",index=False,compression="gzip")
    pd.DataFrame(monthly).to_csv(OUT/"monthly_mark_to_market.csv",index=False)
    pd.DataFrame(summary).to_csv(OUT/"summary.csv",index=False)
    quality=dict(BTCUSD=quality_btc,ETHUSD=quality_eth,
        data="original 1m Delta Exchange India candles, 22 IST months January 2025 through October 2026",
        signal="second EMA20 touch with completed 15m Supertrend, volume >=1.2x prior20, ATR14 >= prior20 ATR mean",
        entry="immediate 1m frozen EMA touch; no current-candle volume or ATR",
        stop_loss="NONE",trailing="NONE",reverse_exit="NONE",time_exit="NONE",
        btc_take_profit_usd_points=200,
        eth_take_profit_usd_points="200 * ETHentry / preceding 1m BTC close",
        source_previous_script="scripts/research_ema20_second_touch_15m_filters.py",
        fees_per_side=FEE,slippage_per_side=SLIP,initial_cash_usd=INITIAL,
        sample_end_forced_close="reporting-only, not a strategy exit rule",
        intraminute_ordering="same-entry minute TP intentionally never counted",
        risk_warning="no actual liquidation, margins, tick sequencing, funding, bid/ask spread, market impact; 1x notional modeled")
    (OUT/"quality.json").write_text(json.dumps(quality,indent=2)+"\n")
    lines=["# TP-only 15M EMA20 second touch — BTC/ETH","",
      "Same 15M completed-candle volume and volatility gates as the prior fixed 200/100 model. SL removed entirely.",
      "2025-01 through 2026-10 (22 IST months), Delta India 1m. One independent 1x cash-equity trade at a time per symbol.",
      "A TP-only win rate does not capture the risk of holding an unbounded loss; compare floating drawdown and holding time.","",
      "| Symbol | Exits | TP | Forced final close | Net return | Worst mark-to-market drawdown | Longest hold (hours) | MTM positive months |",
      "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for x in summary:
        lines.append(f"| {x['symbol']} | {x['entries']} | {x['take_profit_exits']} | {x['sample_end_forced_exits']} | {x['net_model_return_pct']:.3f}% | {x['estimated_mark_to_market_max_dd_pct']:.3f}% | {x['longest_holding_hours']:.1f} | {x['profitable_months_mark_to_market']}/22 |")
    lines.extend(["","## Risk and methodology",
       "- **NO stop-loss**. Supertrend changes, EMA crosses and time passage do NOT close positions.",
       "- Fixed TP +200 BTC price points or equivalent ETH percentage at entry, frozen.",
       "- Model marks floating equity minute by minute; worst wick adverse price and first crossing of zero equity measured.",
       "- Positive closed trades can mask unrecoverable floating drawdown or exchange liquidation. No margin/liquidation/funding model is provided.",
       "- Forced close at October 2026 boundary is ONLY for measuring the dataset, not a live exit rule.",
       "- 0.05% taker each side plus 18% GST; adverse slippage 0.02% on both sides, no verified actual bid/ask spread.",
       "- January 2025 first 330 IST minutes unavailable; 2026 not an untouched statistical validation.",
       "","Outputs: summary.csv, monthly_mark_to_market.csv, trade_ledger.csv.gz, quality.json."])
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(lines)+"\n")
    print("BACKTEST_DONE",json.dumps(summary),flush=True)

if __name__=="__main__":
    main()
