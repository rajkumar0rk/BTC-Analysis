#!/usr/bin/env python3
"""Fixed 200/100 BTC points and dynamically scaled ETH equivalent for second-EMA20-touch entry.

Uses identical validated source reader and 15m/1h indicators as the prior experiment.
Signals use last FULLY CLOSED higher-timeframe indicators; 1m OHLC approximates immediate touch.
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from research_ema20_second_touch import read_source, features, MONTHS, FEE, SLIP

OUT = Path("analysis/ema20_second_touch_fixed_tpsl_20261121")
INITIAL_EQUITY = 1000.0

def simulate(df, btc_prior_close, symbol, tf):
    ema, atr, supertrend, complete = features(df, tf)
    if len(btc_prior_close) != len(df):
        raise ValueError("BTC/ETH 1m arrays unaligned")
    time = df.time.to_numpy(dtype=np.int64)
    op = df.open.to_numpy(dtype=float)
    hi = df.high.to_numpy(dtype=float)
    lo = df.low.to_numpy(dtype=float)
    cl = df.close.to_numpy(dtype=float)
    assert time[0] % (tf*60) == 0
    ledger = []
    equity = INITIAL_EQUITY
    count = 0
    last_touch_htf = -1
    last_direction = 0
    position = None
    for i in range(len(df)):
        b = i//tf
        last_complete = b-1
        if last_complete < 100 or last_complete >= len(ema) or not complete[last_complete]:
            continue
        direction = int(supertrend[last_complete])
        if direction == 0 or not np.isfinite(ema[last_complete]):
            continue

        # Supertrend state changes are observable only after flip bar CLOSE.
        if last_direction != direction:
            count = 0
            last_touch_htf = -1
            last_direction = direction

        o, h, l = float(op[i]), float(hi[i]), float(lo[i])
        t = int(time[i])
        if position is not None:
            p = position
            s = p["side"]
            stop = p["stop"]
            take = p["take"]
            if s == 1:
                gap_stop = o <= stop
                gap_take = o >= take
                in_stop = l <= stop
                in_take = h >= take
            else:
                gap_stop = o >= stop
                gap_take = o <= take
                in_stop = h >= stop
                in_take = l <= take
            if gap_stop:
                exit_raw = o  # adverse gap, never fictional stop fill
                reason = "stop_gap"
            elif gap_take:
                exit_raw = take  # assume target limit, no price improvement
                reason = "take_gap"
            elif in_stop:
                exit_raw = stop  # conservative: stop first if both touched
                reason = "stop"
            elif in_take:
                exit_raw = take
                reason = "take"
            else:
                continue
            exit_fill = exit_raw*(1-s*SLIP)
            gross = s*p["qty"]*(exit_fill-p["entry"])
            fees = FEE*p["qty"]*(p["entry"]+exit_fill)
            net = gross-fees
            equity += net
            ledger.append(dict(symbol=symbol, signal_timeframe=f"{tf}m",
                entry_time_utc=pd.Timestamp(p["entry_time"],unit="s",tz="UTC").isoformat(),
                exit_time_utc=pd.Timestamp(t,unit="s",tz="UTC").isoformat(),
                month_ist=pd.Timestamp(t,unit="s",tz="UTC").tz_convert("Asia/Kolkata").strftime("%Y-%m"),
                direction="LONG" if s==1 else "SHORT",
                entry=p["entry"],exit=exit_fill,
                tp_points=p["tp_points"],sl_points=p["sl_points"],
                reference_btc_previous_minute=p["ref_btc"],
                exit_reason=reason,gross_usd=gross,fees_gst_usd=fees,
                net_usd=net,equity_after_usd=equity))
            position = None
            count = 0
            # Keep last_touch_htf equal to the entry candle, preventing any
            # accidental second counting of the same 15m or 1h candle.
            continue

        # A touch is only counted once per DISTINCT signal timeframe candle.
        if last_touch_htf == b:
            continue
        level = float(ema[last_complete])
        if not (l <= level <= h):
            continue
        count += 1
        last_touch_htf = b
        if count != 2:
            continue
        ref_btc = float(btc_prior_close[i])
        if not np.isfinite(ref_btc) or ref_btc <= 0:
            raise AssertionError("BTC reference missing at entry")
        entry = level*(1+direction*SLIP)
        if symbol == "BTCUSD":
            tp_points, sl_points = 200., 100.
        else:
            # Equivalent BTC percent move, scaled to ETH entry price.
            tp_points = 200.*entry/ref_btc
            sl_points = 100.*entry/ref_btc
        if sl_points <= 0 or tp_points <= 0:
            raise AssertionError("bad stop/target")
        qty = equity/entry  # 1x notional at evolving model equity
        p = dict(side=direction,entry=entry,
            stop=entry-direction*sl_points,take=entry+direction*tp_points,
            qty=qty,entry_time=t,tp_points=tp_points,sl_points=sl_points,ref_btc=ref_btc)
        count = 0
        position = p

        # Entry-minute OHLC cannot order EMA touch vs 1m extremes.
        # Count an adverse stop crossing; never credit target inside
        # the triggering minute even when favorable extreme reaches it.
        if (direction == 1 and l <= p["stop"]) or (direction == -1 and h >= p["stop"]):
            exit_fill = p["stop"]*(1-direction*SLIP)
            gross = direction*qty*(exit_fill-entry)
            fees = FEE*qty*(entry+exit_fill)
            net = gross-fees
            equity += net
            ledger.append(dict(symbol=symbol, signal_timeframe=f"{tf}m",
                entry_time_utc=pd.Timestamp(t,unit="s",tz="UTC").isoformat(),
                exit_time_utc=pd.Timestamp(t,unit="s",tz="UTC").isoformat(),
                month_ist=pd.Timestamp(t,unit="s",tz="UTC").tz_convert("Asia/Kolkata").strftime("%Y-%m"),
                direction="LONG" if direction==1 else "SHORT",
                entry=entry,exit=exit_fill,tp_points=tp_points,sl_points=sl_points,
                reference_btc_previous_minute=ref_btc,
                exit_reason="entry_minute_stop_first",gross_usd=gross,fees_gst_usd=fees,
                net_usd=net,equity_after_usd=equity))
            position = None

    # The last sample may still have an open trade: close conservatively,
    # and label this exit as a forced sample-end mark, not a normal TP or SL.
    if position is not None:
        p = position
        s = p["side"]
        exit_fill = float(cl[-1])*(1-s*SLIP)
        gross = s*p["qty"]*(exit_fill-p["entry"])
        fees = FEE*p["qty"]*(p["entry"]+exit_fill)
        net = gross-fees
        equity += net
        t = int(time[-1])
        ledger.append(dict(symbol=symbol, signal_timeframe=f"{tf}m",
            entry_time_utc=pd.Timestamp(p["entry_time"],unit="s",tz="UTC").isoformat(),
            exit_time_utc=pd.Timestamp(t,unit="s",tz="UTC").isoformat(),
            month_ist=pd.Timestamp(t,unit="s",tz="UTC").tz_convert("Asia/Kolkata").strftime("%Y-%m"),
            direction="LONG" if s==1 else "SHORT",
            entry=p["entry"],exit=exit_fill,tp_points=p["tp_points"],
            sl_points=p["sl_points"],reference_btc_previous_minute=p["ref_btc"],
            exit_reason="sample_end",gross_usd=gross,fees_gst_usd=fees,
            net_usd=net,equity_after_usd=equity))
    trades = pd.DataFrame(ledger)
    if trades.empty:
        trades = pd.DataFrame(columns=["symbol","signal_timeframe","month_ist",
                                       "net_usd","equity_after_usd","gross_usd","fees_gst_usd"])
    if abs(float(trades.net_usd.sum())-(equity-INITIAL_EQUITY))>0.01:
        raise AssertionError("equity/pnl mismatch")
    monthly=[]
    monthly_start=INITIAL_EQUITY
    for month in MONTHS:
        x=trades.loc[trades.month_ist == month]
        net=float(x.net_usd.sum())
        end=monthly_start+net
        monthly.append(dict(symbol=symbol,timeframe=f"{tf}m",
            month_ist=month,trades=len(x),
            winners=int((x.net_usd>0).sum()),
            losers=int((x.net_usd<0).sum()),
            take_exits=int(x.exit_reason.isin(["take","take_gap"]).sum()) if "exit_reason" in x else 0,
            stop_exits=int(x.exit_reason.isin(["stop","stop_gap","entry_minute_stop_first"]).sum()) if "exit_reason" in x else 0,
            net_usd=round(net,6),net_return_pct=round(100*net/monthly_start,6)))
        monthly_start=end
    profit=float(trades.loc[trades.net_usd>0,"net_usd"].sum())
    loss=-float(trades.loc[trades.net_usd<0,"net_usd"].sum())
    trajectory=np.r_[INITIAL_EQUITY,trades.equity_after_usd.to_numpy()]
    running_max=np.maximum.accumulate(trajectory)
    dd=float(np.max((running_max-trajectory)/running_max))
    end_2025=INITIAL_EQUITY+sum(m["net_usd"] for m in monthly[:12])
    s=dict(symbol=symbol,timeframe=f"{tf}m",trades=len(trades),
        winners=int((trades.net_usd>0).sum()),losers=int((trades.net_usd<0).sum()),
        win_rate_pct=round(100*float((trades.net_usd>0).mean()),4) if len(trades) else 0.,
        tp_exits=sum(m["take_exits"] for m in monthly),
        sl_exits=sum(m["stop_exits"] for m in monthly),
        profit_factor=round(profit/loss,5) if loss else None,
        gross_profit_usd=round(profit,5),gross_loss_usd=round(loss,5),
        fees_gst_usd=round(float(trades.fees_gst_usd.sum()),5),
        net_profit_usd=round(equity-INITIAL_EQUITY,5),
        net_return_pct=round(100*(equity/INITIAL_EQUITY-1),5),
        max_closed_trade_drawdown_pct=round(dd*100,5),
        positive_months=sum(m["net_usd"]>0 for m in monthly),
        negative_months=sum(m["net_usd"]<0 for m in monthly),
        flat_months=sum(m["net_usd"]==0 for m in monthly),
        return_2025_pct=round(100*(end_2025/INITIAL_EQUITY-1),5),
        return_2026_jan_oct_pct=round(100*(equity/end_2025-1),5))
    return trades, monthly, s

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    btc,q_btc=read_source("BTCUSD")
    eth,q_eth=read_source("ETHUSD")
    if not np.array_equal(btc.time.to_numpy(),eth.time.to_numpy()):
        raise AssertionError("BTC ETH 1m timestamps not perfectly aligned")
    bc=btc.close.to_numpy(dtype=float)
    prior_btc=np.r_[np.nan,bc[:-1]]
    all_trades=[]
    all_months=[]
    summary=[]
    for symbol,df in (("BTCUSD",btc),("ETHUSD",eth)):
        for tf in (15,60):
            print("RUN",symbol,tf,flush=True)
            ledger,monthly,s=simulate(df,prior_btc,symbol,tf)
            all_trades.append(ledger)
            all_months.extend(monthly)
            summary.append(s)
            print("RESULT",json.dumps(s,sort_keys=True),flush=True)
    pd.concat(all_trades,ignore_index=True).to_csv(OUT/"trade_ledger.csv.gz",
        index=False,compression="gzip")
    pd.DataFrame(all_months).to_csv(OUT/"monthly_results.csv",index=False)
    pd.DataFrame(summary).to_csv(OUT/"summary.csv",index=False)
    quality=dict(BTCUSD=q_btc,ETHUSD=q_eth,
       entry_rule="second distinct HTF candle touching frozen last-completed HTF EMA20; Supertrend flip bar excluded",
       eth_scaling="200*ETH entry/prior BTC minute close TP; 100*ETH entry/prior BTC minute close SL",
       btc_tp_points=200,btc_sl_points=100,
       taker_fee_fraction_each_side=0.0005,gst_on_fee_fraction=0.18,
       adverse_slippage_fraction_each_side=SLIP,initial_usd=INITIAL_EQUITY,
       notional_exposure="1x of evolving account equity",
       one_position="per asset per timeframe",
       first_minute_handling="stop-first; never award favorable TP on entry minute",
       double_touch_same_minute="stop first",
       gap_handling="adverse stop gap at open; TP at target limit price",
       monthly_timezone="Asia/Kolkata",nov_2026_incomplete_excluded=True,
       limitations="OHLC no tick sequencing, no actual bid ask, funding, order book or latency. Historical backtest only.")
    (OUT/"quality.json").write_text(json.dumps(quality,indent=2)+"\n")
    lines=[
        "# Fixed TP/SL 200/100 BTC-equivalent — second EMA20 touch",
        "",
        "Historical 1-minute Delta Exchange India OHLC research. 22 IST calendar months Jan 2025–Oct 2026. No tuning.",
        "ETH distances dynamically scaled to ex-ante BTC percentage at each entry; NEVER 200/100 ETH dollars.",
        "",
        "| Asset | Signal TF | Trades | Wins | Win rate | TP hit | SL hit | PF | Net return | Drawdown | Positive months |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"
    ]
    for s in summary:
        lines.append("| {symbol} | {timeframe} | {trades} | {winners} | {win_rate_pct:.2f}% | {tp_exits} | {sl_exits} | {profit_factor} | {net_return_pct:.3f}% | {max_closed_trade_drawdown_pct:.2f}% | {positive_months}/22 |".format(**s))
    lines.extend(["","- 1× notional evolving account exposure with $1000 initial equity.",
        "- 0.05% taker fee each side, 18% GST on fee; 0.02% adverse slippage each side.",
        "- Stop first whenever stop and target touched within the same 1-minute candle.",
        "- No TP credit on entry minute because touch ordering is unknowable; adverse stop honored.",
        "- No trailing or breakeven. Funding, spreads, real tick order sequence and latency unavailable.",
        "- 2026 period already explored in other studies; not a pristine out-of-sample check.",
        "- Early Jan 2025 IST first 5.5h unavailable; all other scored minutes contiguous.",
        "","See monthly_results.csv, summary.csv, trade_ledger.csv.gz, quality.json, NOVELTY_CHECK.md."
    ])
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(lines)+"\n")
    print("BACKTEST_DONE",json.dumps(summary),flush=True)

if __name__=="__main__":
    main()
