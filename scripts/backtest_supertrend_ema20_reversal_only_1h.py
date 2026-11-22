#!/usr/bin/env python3
"""Research-only BTCUSD 1H Supertrend + EMA20; exit ONLY on confirmed Supertrend reversal."""
import json
from pathlib import Path
import numpy as np
import pandas as pd

BASE=Path("data/delta_india/BTCUSD/1m")
OUT=Path("analysis/ema20_st_reversal_only_1h")
QTY=0.001
START_USD=100.
FEE=.0005*1.18
SLIP=5.

def load():
    files=sorted(BASE.glob("20??-??.csv.gz"))
    if not files: raise RuntimeError("No BTCUSD one-minute source archive")
    a=[]
    for f in files:
        x=pd.read_csv(f,compression="gzip",usecols=["time","open","high","low","close","volume"])
        x["time"]=pd.to_datetime(x.time.astype("int64"),unit="s",utc=True)
        a.append(x.set_index("time"))
    m=pd.concat(a).sort_index()
    if m.index.has_duplicates or not m.index.to_series().diff().dropna().eq(pd.Timedelta(minutes=1)).all():
        raise RuntimeError("Source 1m archive has duplicate or missing timestamps")
    if m[["open","high","low","close"]].isna().any().any(): raise RuntimeError("Missing OHLC")
    if not ((m.low<=m[["open","close"]].min(axis=1)) & (m.high>=m[["open","close"]].max(axis=1))).all():
        raise RuntimeError("Invalid OHLC")
    count=m.close.resample("1h").count()
    if not count.eq(60).all(): raise RuntimeError("Incomplete hourly bar")
    h=m.resample("1h").agg({"open":"first","high":"max","low":"min","close":"last","volume":"sum"})
    return m,h,len(files)

def features(h):
    prev=h.close.shift()
    tr=pd.concat([h.high-h.low,(h.high-prev).abs(),(h.low-prev).abs()],axis=1).max(axis=1).to_numpy()
    n=len(h); atr=np.full(n,np.nan)
    if n<30: raise RuntimeError("Insufficient signal warmup")
    atr[9]=tr[:10].mean()
    for i in range(10,n): atr[i]=(9*atr[i-1]+tr[i])/10
    mid=(h.high.to_numpy()+h.low.to_numpy())/2.
    up=mid+3*atr; down=mid-3*atr
    u=np.full(n,np.nan); d=np.full(n,np.nan); side=np.zeros(n,dtype=np.int8)
    for i in range(9,n):
        if i==9:
            u[i]=up[i];d[i]=down[i];side[i]=-1
        else:
            u[i]=up[i] if up[i]<u[i-1] or h.close.iloc[i-1]>u[i-1] else u[i-1]
            d[i]=down[i] if down[i]>d[i-1] or h.close.iloc[i-1]<d[i-1] else d[i-1]
            side[i]=(1 if side[i-1]==-1 and h.close.iloc[i]>u[i-1] else
                     (-1 if side[i-1]==1 and h.close.iloc[i]<d[i-1] else side[i-1]))
    h=h.copy()
    h["ema"]=h.close.ewm(span=20,adjust=False).mean()
    h["atr"]=atr
    h["side"]=side
    h["supertrend_line"]=np.where(side==1,d,u)
    return h


def setups(h, mode):
    """Previous study's completed-hour touch/reclaim signals, minus ALL stop/R filters."""
    events = {}
    prev_side = 0
    seen_adverse = False
    cycle = 0
    flip_i = 0
    for i in range(20, len(h)):
        side = int(h.side.iloc[i])
        if side != prev_side:
            cycle += 1
            flip_i = i
            seen_adverse = False
            prev_side = side
        if side == 0 or i == flip_i:
            continue
        r = h.iloc[i]
        favorable = side * (r.close - r.ema) > 0
        adverse = side * (r.close - r.ema) < 0
        touch = (favorable and not seen_adverse and
                 (r.low <= r.ema if side == 1 else r.high >= r.ema))
        reclaim = favorable and seen_adverse
        kind = "reclaim" if reclaim else ("touch" if touch else None)
        if adverse:
            seen_adverse = True
        elif reclaim:
            seen_adverse = False
        if kind is None or (mode != "combined" and kind != mode):
            continue
        # Entry is only eligible in the NEXT hour after the completed 1H signal.
        events[i + 1] = dict(side=side, cycle=cycle, kind=kind,
                             trigger=float(r.high + .5 if side == 1 else r.low - .5),
                             signal=str(h.index[i]))
    return events


def replay(m, h, mode):
    """Gap-aware breakout entry; 1H-close-confirmed Supertrend flip is the ONLY exit."""
    events = setups(h, mode)
    op = m.open.to_numpy(float)
    hi = m.high.to_numpy(float)
    lo = m.low.to_numpy(float)
    close = m.close.to_numpy(float)
    times = m.index
    hour_for_minute = np.searchsorted(h.index.asi8, m.index.asi8, side="right") - 1
    hside = h.side.to_numpy()
    trades = []
    used_cycles = set()
    pos = None
    pending = None
    last_hour = -1
    realized_cash = START_USD
    peak_closed_cash = START_USD
    worst_open_mark = START_USD
    largest_excursion_below_closed_peak = 0.

    def mark_equity(worst_price):
        """Mark adverse excursion at the observed 1m extreme, with hypothetical exit costs."""
        hypothetical_exit_fill = worst_price - pos["side"] * SLIP
        gross = QTY * pos["side"] * (hypothetical_exit_fill - pos["entry"])
        fees = QTY * FEE * (pos["entry"] + hypothetical_exit_fill)
        return realized_cash + gross - fees

    def finish(j):
        nonlocal pos, realized_cash, peak_closed_cash
        side = pos["side"]
        exit_fill = float(op[j]) - side * SLIP
        gross = QTY * side * (exit_fill - pos["entry"])
        fees = QTY * FEE * (pos["entry"] + exit_fill)
        net = gross - fees
        duration = j - pos["entry_j"]
        trades.append(dict(
            mode=mode, setup=pos["kind"],
            side="LONG" if side == 1 else "SHORT",
            signal_utc=pos["signal"],
            entry_utc=str(times[pos["entry_j"]]),
            exit_utc=str(times[j]),
            entry_price=round(pos["entry"], 2),
            exit_price=round(exit_fill, 2),
            hold_minutes=int(duration),
            gross_usd=round(gross, 6),
            fees_usd=round(fees, 6),
            net_usd=round(net, 6),
            max_favorable_points=round(pos["max_favorable_points"], 2),
            max_adverse_points=round(pos["max_adverse_points"], 2),
            exit_reason="supertrend_flip"))
        realized_cash += net
        peak_closed_cash = max(peak_closed_cash, realized_cash)
        pos = None

    for j, hour in enumerate(hour_for_minute):
        if hour != last_hour:
            last_hour = hour
            pending = None
            # Completed last 1H candle is h[hour-1].
            # Supertrend reversal becomes known NOW (new-hour minute open).
            if hour > 0 and pos is not None and int(hside[hour - 1]) != pos["side"]:
                finish(j)
            if pos is None:
                ev = events.get(hour)
                if ev is not None and ev["cycle"] not in used_cycles:
                    pending = ev

        if pos is None and pending is not None:
            ev = pending
            side = ev["side"]
            hit = (hi[j] >= ev["trigger"] if side == 1 else lo[j] <= ev["trigger"])
            if hit:
                fill_mid = (max(float(op[j]), ev["trigger"]) if side == 1
                            else min(float(op[j]), ev["trigger"]))
                entry_fill = fill_mid + side * SLIP
                pos = dict(side=side, kind=ev["kind"], cycle=ev["cycle"],
                           entry_j=j, entry=entry_fill,
                           signal=ev["signal"], max_adverse_points=0.,
                           max_favorable_points=0.)
                used_cycles.add(ev["cycle"])
                pending = None

        # No initial SL, no TP, no profit protection, no trailing stop.
        # Skip entry minute's extreme in MAE/MFE (order within that minute is unknown).
        if pos is not None and j > pos["entry_j"]:
            side = pos["side"]
            adverse_price = lo[j] if side == 1 else hi[j]
            favorable_price = hi[j] if side == 1 else lo[j]
            adverse_points = max(0., side * (pos["entry"] - adverse_price))
            favorable_points = max(0., side * (favorable_price - pos["entry"]))
            pos["max_adverse_points"] = max(pos["max_adverse_points"], adverse_points)
            pos["max_favorable_points"] = max(pos["max_favorable_points"], favorable_points)
            adverse_equity = mark_equity(adverse_price)
            worst_open_mark = min(worst_open_mark, adverse_equity)
            largest_excursion_below_closed_peak = max(
                largest_excursion_below_closed_peak, peak_closed_cash - adverse_equity)

    open_trade = None
    if pos is not None:
        side = pos["side"]
        hypothetical_exit_price = float(close[-1]) - side * SLIP
        open_net = (QTY * side * (hypothetical_exit_price - pos["entry"])
                    - QTY * FEE * (pos["entry"] + hypothetical_exit_price))
        open_trade = dict(side="LONG" if side == 1 else "SHORT",
                          setup=pos["kind"], cycle=pos["cycle"],
                          entry_utc=str(times[pos["entry_j"]]), entry_price=pos["entry"],
                          mark_price=float(close[-1]), hypothetical_net_usd=round(open_net, 4),
                          note="Unrealized only; NOT exited by strategy, hypothetical exit costs assumed")

    extra = dict(open_trade=open_trade,
                 worst_open_mark_equity_usd=round(worst_open_mark, 4),
                 max_excursion_below_previous_realized_peak_usd=round(
                     largest_excursion_below_closed_peak, 4),
                 note="Intrabar extremes skip the entry minute; no bid-ask, mark-price or liquidation model")
    return pd.DataFrame(trades), extra


def summarize(trades, extra):
    if trades.empty:
        return dict(closed_trades=0, realized_net_usd=0, ending_closed_equity_usd=START_USD, **extra)
    p = trades.net_usd.to_numpy(float)
    closed_eq = np.r_[START_USD, START_USD + np.cumsum(p)]
    peaks = np.maximum.accumulate(closed_eq)
    draw = peaks - closed_eq
    wins = p[p > 0].sum()
    losses = -p[p < 0].sum()
    return dict(
        closed_trades=len(trades),
        wins=int((p > 0).sum()),
        losses=int((p < 0).sum()),
        win_rate_pct=round(float((p > 0).mean() * 100), 3),
        gross_usd=round(float(trades.gross_usd.sum()), 4),
        fees_usd=round(float(trades.fees_usd.sum()), 4),
        realized_net_usd=round(float(p.sum()), 4),
        ending_closed_equity_usd=round(float(closed_eq[-1]), 4),
        profit_factor=round(float(wins / losses), 4) if losses else None,
        realized_max_drawdown_usd=round(float(draw.max()), 4),
        realized_max_drawdown_pct=round(float(np.max(100 * draw / peaks)), 3),
        winning_trades_gross_usd=round(float(wins), 4),
        losing_trades_gross_usd=round(float(losses), 4),
        avg_win_usd=round(float(p[p > 0].mean()), 4) if (p > 0).any() else None,
        avg_loss_usd=round(float(p[p < 0].mean()), 4) if (p < 0).any() else None,
        max_trade_adverse_points=round(float(trades.max_adverse_points.max()), 2),
        max_trade_favorable_points=round(float(trades.max_favorable_points.max()), 2),
        **extra)


def monthly(trades, first, last):
    all_months = pd.period_range(
        first.tz_convert("Asia/Kolkata").tz_localize(None).to_period("M"),
        last.tz_convert("Asia/Kolkata").tz_localize(None).to_period("M"))
    if not trades.empty:
        t = trades.copy()
        # Realized profit belongs to the EXIT month, not the entry month.
        t["month"] = (pd.to_datetime(t.exit_utc, utc=True)
                      .dt.tz_convert("Asia/Kolkata").dt.strftime("%Y-%m"))
    else:
        t = pd.DataFrame()
    rows = []
    cash = START_USD
    for per in all_months:
        month = str(per)
        group = t[t.month == month] if not t.empty else t
        n = len(group)
        net = float(group.net_usd.sum()) if n else 0.
        rows.append(dict(month_ist=month, complete_month=month < "2026-11",
                         closed_trades=n,
                         winning_trades=int((group.net_usd > 0).sum()) if n else 0,
                         losing_trades=int((group.net_usd < 0).sum()) if n else 0,
                         gross_usd=round(float(group.gross_usd.sum()), 4) if n else 0.,
                         fees_usd=round(float(group.fees_usd.sum()), 4) if n else 0.,
                         net_usd=round(net, 4),
                         starting_closed_equity_usd=round(cash, 4),
                         net_return_pct=round(100 * net / cash, 3) if cash > 0 else None,
                         ending_closed_equity_usd=round(cash + net, 4)))
        cash += net
    return pd.DataFrame(rows)


def main():
    m, h, nfiles = load()
    h = features(h)
    OUT.mkdir(parents=True, exist_ok=True)
    quality = dict(source="Delta Exchange India BTCUSD perpetual 1m price OHLCV",
                   source_files=nfiles, minute_bars=len(m), hourly_bars=len(h),
                   first_utc=str(m.index[0]), last_utc=str(m.index[-1]),
                   validated_consecutive_minutes=True)
    quality["qty_btc"] = QTY
    quality["initial_account_usd"] = START_USD
    quality["side_taker_fee_including_gst"] = FEE
    quality["slippage_btc_price_points_per_side"] = SLIP
    quality["exit_only_on_confirmed_supertrend_flip"] = True
    quality["max_one_fill_per_supertrend_cycle"] = True
    quality["caveats"] = [
        "No stop or liquidation model: a real futures position could be liquidated before Supertrend reverses",
        "No funding, spread, depth, exchange latency or actual execution validation",
        "Unrealized open position is NOT forced closed at the archive boundary",
        "No untouched out-of-sample holdout; historic periods previously researched",
        "MAE/MFE and adverse marks exclude entry-minute OHLC ambiguity"
    ]
    (OUT / "quality.json").write_text(json.dumps(quality, indent=2) + "\n")
    results = {}
    for mode in ["touch", "reclaim", "combined"]:
        trades, extra = replay(m, h, mode)
        trades.to_csv(OUT / f"{mode}_trades.csv", index=False)
        month = monthly(trades, m.index[0], m.index[-1])
        month.to_csv(OUT / f"{mode}_monthly_ist.csv", index=False)
        summary = summarize(trades, extra)
        summary["profitable_full_months"] = int(((month.net_usd > 0) & month.complete_month).sum())
        summary["total_full_months"] = int(month.complete_month.sum())
        results[mode] = summary
        print(f"{mode}: {json.dumps(summary)}", flush=True)
    (OUT / "summary.json").write_text(json.dumps(results, indent=2) + "\n")

if __name__ == "__main__":
    main()
