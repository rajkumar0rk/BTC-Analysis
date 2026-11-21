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

OUT = Path("analysis/ema20_second_touch_15m_filters_20261121")
VOL_RATIO_MIN = 1.20
ATR_RATIO_MIN = 1.00
VARIANTS = ("none", "volume", "volatility", "both")
INITIAL_EQUITY = 1000.0

def simulate(df, btc_prior_close, symbol, tf, variant):
    assert tf == 15 and variant in VARIANTS
    ema, atr, supertrend, complete = features(df, tf)
    # Ex-ante indicators: evaluate the LAST COMPLETED 15m candle only.
    bars = df.resample("15min",label="left",closed="left").agg({"volume":"sum","close":"count"})
    vol15 = bars.volume.to_numpy(dtype=float)
    counts15 = bars.close.to_numpy(dtype=int)
    volume_ref = pd.Series(vol15).shift(1).rolling(20,min_periods=20).mean().to_numpy()
    atr_ref = pd.Series(atr).shift(1).rolling(20,min_periods=20).mean().to_numpy()
    if len(vol15) != len(ema):
        raise AssertionError("Feature aggregation mismatch")
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
        # Count the second touch even when a filter rejects the entry, then
        # reset to seek a fresh pair of touches. No current-candle volume/ATR.
        vref = float(volume_ref[last_complete])
        aref = float(atr_ref[last_complete])
        vok = (counts15[last_complete] == 15 and np.isfinite(vref)
               and vref > 0 and vol15[last_complete] >= VOL_RATIO_MIN*vref)
        aok = (np.isfinite(aref) and aref > 0 and np.isfinite(atr[last_complete])
               and atr[last_complete] >= ATR_RATIO_MIN*aref)
        if ((variant in ("volume","both") and not vok) or
            (variant in ("volatility","both") and not aok)):
            count = 0
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
    s["filter_variant"] = variant
    for m in monthly:
        m["filter_variant"] = variant
    if not trades.empty:
        trades["filter_variant"] = variant
    return trades, monthly, s

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    btc,q_btc=read_source("BTCUSD")
    eth,q_eth=read_source("ETHUSD")
    if not np.array_equal(btc.time.to_numpy(),eth.time.to_numpy()):
        raise AssertionError("BTC/ETH timestamps differ")
    ref = np.r_[np.nan,btc.close.to_numpy(dtype=float)[:-1]]
    all_trades=[]
    all_months=[]
    summary=[]
    for symbol,df in (("BTCUSD",btc),("ETHUSD",eth)):
        for variant in VARIANTS:
            print("RUN",symbol,"15m",variant,flush=True)
            trades,monthly,s=simulate(df,ref,symbol,15,variant)
            # The unchanged baseline must exactly match the prior fixed exit run.
            if variant=="none":
                expected={"BTCUSD":(6397,-99.99636),"ETHUSD":(7409,-99.99960)}
                n, pct=expected[symbol]
                if s["trades"]!=n or abs(s["net_return_pct"]-pct)>0.00002:
                    raise AssertionError("Baseline parity regression "+str(s))
            all_trades.append(trades)
            all_months.extend(monthly)
            summary.append(s)
            print("RESULT",json.dumps(s,sort_keys=True),flush=True)
    pd.concat(all_trades,ignore_index=True).to_csv(
        OUT/"trade_ledger.csv.gz",index=False,compression="gzip")
    pd.DataFrame(all_months).to_csv(OUT/"monthly_results.csv",index=False)
    pd.DataFrame(summary).to_csv(OUT/"summary.csv",index=False)
    quality=dict(BTCUSD=q_btc,ETHUSD=q_eth,
        signal_timeframe="15m",monitoring="1m",
        volume_ratio_min=VOL_RATIO_MIN,
        volume_mean="mean of 20 bars strictly preceding last completed 15m bar",
        volatility_atr="Wilder ATR14 on last completed 15m bar",
        volatility_atr_ratio_min=ATR_RATIO_MIN,
        volatility_mean="mean ATR14 of 20 bars strictly preceding last completed 15m bar",
        filters_checked="second touch only, before entry",
        second_touch_filter_failure="discard setup, count reset to zero",
        variants=VARIANTS,btc_fixed_target_points=200,btc_fixed_stop_points=100,
        eth_target_formula="200 * ETH_entry / preceding_1m_BTC_close",
        eth_stop_formula="100 * ETH_entry / preceding_1m_BTC_close",
        fee_taker_each_side=0.0005,gst_on_fees=0.18,
        adverse_slippage_each_side=SLIP,
        assumed_exposure="1x evolving model equity initially USD 1000",
        notes="1m OHLC cannot establish true event order; stop-first, missing funding/quotes")
    (OUT/"quality.json").write_text(json.dumps(quality,indent=2)+"\n")
    lines=["# Second EMA20 touch — 15m volume and volatility filters","",
       "Same 200/100 BTC points and ETH equivalent percent exits as previous baseline.",
       "Data: BTCUSD/ETHUSD Delta India 1m; January 2025–October 2026 (22 IST calendar months).",
       "Volume: last completed 15m volume >= 1.2x mean of PRECEDING 20 bars.",
       "Volatility: last completed 15m ATR14 >= mean of PRECEDING 20 ATR14 readings.",
       "Both checked only upon second EMA20 touch, using closed candles; no future leakage.","",
       "| Asset | Filters | Trades | TP exits | SL exits | Win % | PF | Net return % | Max DD % | Profitable months |",
       "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for x in summary:
        lines.append(f"| {x['symbol']} | {x['filter_variant']} | {x['trades']} | {x['tp_exits']} | {x['sl_exits']} | {x['win_rate_pct']:.2f}% | {x['profit_factor']} | {x['net_return_pct']:.3f}% | {x['max_closed_trade_drawdown_pct']:.2f}% | {x['positive_months']}/22 |")
    lines+=["",
        "## Cautions",
        "- Both filters are applied *only on second touch*, not to the initial touch.",
        "- 0.05% taker fees per side plus 18% GST; 0.02% adverse slippage per side.",
        "- 1x notional; a stopped position is valued with adverse stop-first 1m OHLC.",
        "- 2026 has been examined historically and is not an untouched holdout.",
        "- No verified actual spreads, funding, tick-by-tick touch sequencing or live fills.",
        "- Not investment advice; negative results retained alongside positives.",
        "",
        "Evidence: summary.csv, monthly_results.csv, trade_ledger.csv.gz, quality.json."]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(lines)+"\n")
    print("BACKTEST_DONE",json.dumps(summary),flush=True)

if __name__ == "__main__":
    main()
