#!/usr/bin/env python3
"""Exact fixed-parameter DAILY Bollinger30(2) 3R strategy on genuine Delta India BTCUSD 1m.
Research only. Signals at full UTC daily close, fill next minute OPEN; conservative 1m stop-first.
"""
from pathlib import Path
import json
import math
import numpy as np
import pandas as pd

BASE = Path("data/delta_india/BTCUSD/1m")
FUND = Path("data/delta_india/BTCUSD/institutional/history/funding_1h")
OUT = Path("analysis/daily_bollinger_30_3r")
INITIAL = 10000.0
RISK_PCT = 0.01
LEVERAGE_CAP = 2.0
FEE_RATE = 0.0005 * 1.18  # taker fee and 18% GST; not a maker assumption
SLIP_PTS = 5.0  # adverse each fill
START_VALIDATION = "2026-01-01"


def load_1m():
    files = sorted(BASE.glob("20??-??.csv.gz"))
    if len(files) < 20:
        raise RuntimeError("Insufficient BTCUSD 1m archive")
    frames = []
    for p in files:
        z = pd.read_csv(p, compression="gzip", usecols=["time", "open", "high", "low", "close", "volume"])
        frames.append(z)
    d = pd.concat(frames, ignore_index=True).sort_values("time").reset_index(drop=True)
    t = d["time"].to_numpy(np.int64)
    if len(t) == 0 or not np.all(np.diff(t) == 60):
        raise RuntimeError("Missing/duplicate Delta 1m UTC candles; refuse guessed fills")
    for k in ("open", "high", "low", "close", "volume"):
        if not np.isfinite(d[k].to_numpy(dtype=float)).all():
            raise RuntimeError("Nonfinite OHLCV: " + k)
    if ((d.high < d.low) | (d.open < d.low) | (d.open > d.high) |
        (d.close < d.low) | (d.close > d.high)).any():
        raise RuntimeError("OHLC inconsistent")
    d.index = pd.to_datetime(t, unit="s", utc=True)
    return d, files


def daily_signals(d):
    rules = {"open": "first", "high": "max", "low": "min", "close": "last"}
    a = d.resample("1D", label="right", closed="left").agg(rules)
    a["count"] = d.close.resample("1D", label="right", closed="left").count()
    a = a[a["count"] == 1440].copy()  # complete UTC sessions only
    c = a.close
    a["mid"] = c.rolling(30, min_periods=30).mean()
    sigma = c.rolling(30, min_periods=30).std(ddof=0)
    a["upper"] = a.mid + 2 * sigma
    a["lower"] = a.mid - 2 * sigma
    pclose = c.shift()
    tr = pd.concat((a.high-a.low, (a.high-pclose).abs(),
                    (a.low-pclose).abs()), axis=1).max(axis=1)
    # Wilder ATR14, seeded at true range simple average of first 14 daily candles.
    vals = tr.to_numpy(float)
    atr = np.full(len(a), np.nan)
    if len(vals) >= 14:
        atr[13] = float(np.mean(vals[:14]))
        for j in range(14, len(vals)):
            atr[j] = (13.0 * atr[j-1] + vals[j]) / 14.0
    a["atr14"] = atr
    a["side"] = np.where(c > a.upper, 1, np.where(c < a.lower, -1, 0))
    a.loc[a.atr14.isna(), "side"] = 0
    signal_map = {}
    raw_signals = 0
    for ts, x in a.iterrows():
        side = int(x.side)
        if side == 0:
            continue
        raw_signals += 1
        stop = float(x.low - 0.25*x.atr14 if side == 1 else x.high + 0.25*x.atr14)
        signal_map[int(ts.timestamp())] = (side, stop, str(ts - pd.Timedelta(days=1)),
                                          float(x.close), float(x.atr14))
    return a, signal_map, raw_signals


def load_funding():
    parts = sorted(FUND.glob("20??-??.csv.gz"))
    if not parts:
        raise RuntimeError("Historical funding proxy absent; cannot claim after-funding result")
    rates = []
    for p in parts:
        rates.append(pd.read_csv(p, compression="gzip", usecols=["time", "close"]))
    z = pd.concat(rates, ignore_index=True).sort_values("time")
    if z.time.duplicated().any() or not np.isfinite(z.close.to_numpy(float)).all():
        raise RuntimeError("Invalid funding hourly data")
    # At 00/08/16 UTC, use the previous fully completed hour's rate observation.
    # Delta rate 'close' appears in percent, not decimal units; this is NOT cash settlement history.
    ts = z.time.to_numpy(np.int64) + 3600
    rate = z.close.to_numpy(float)
    return {int(t): float(r) for t, r in zip(ts, rate)}, len(parts)


def backtest(d, signal_map, fundmap):
    t = d.time.to_numpy(np.int64)
    o, h, l, c = (d[k].to_numpy(float) for k in ("open","high","low","close"))
    local = d.index.tz_convert("Asia/Kolkata")
    ym = local.year.to_numpy() * 100 + local.month.to_numpy()
    month_end_indices = {}
    for i in range(len(t)):
        if i == len(t)-1 or ym[i] != ym[i+1]:
            month_end_indices[i] = int(ym[i])
    rows = []
    monthly_eq = {}
    equity = INITIAL
    p = None
    ignored = 0
    invalid = 0
    entry_signals = 0
    funding_checks = 0
    funding_missing = 0
    for i in range(len(t)):
        now = int(t[i])
        # Funding is paid by pre-existing positions before any new trade at settlement timestamp.
        if p is not None and now % (8*3600) == 0:
            funding_checks += 1
            if now in fundmap:
                rate = fundmap[now] / 100.0  # source percentage points
                p["funding"] += -p["side"] * p["qty"] * o[i] * rate
                p["funding_events"] += 1
            else:
                funding_missing += 1
        if now in signal_map:
            entry_signals += 1
            if p is not None:
                ignored += 1
            else:
                side, stop, signal_day, signal_close, atr = signal_map[now]
                entry_mid = float(o[i])
                entry_fill = entry_mid + side*SLIP_PTS
                distance = side * (entry_fill-stop)
                if distance <= 0 or not np.isfinite(distance) or equity <= 0:
                    invalid += 1
                else:
                    qty = min(equity*RISK_PCT/distance, equity*LEVERAGE_CAP/entry_fill)
                    if qty > 0:
                        p = dict(side=side, entry_utc=str(d.index[i]), entry_i=i,
                                 signal_day=signal_day, signal_close=signal_close, atr14=atr,
                                 entry_mid=entry_mid, entry_fill=entry_fill, qty=qty,
                                 stop=stop, target=entry_fill + side*3*distance, risk_pts=distance,
                                 initial_equity=equity, funding=0.0, funding_events=0)
        if p is not None:
            side = p["side"]
            stop_hit = (l[i] <= p["stop"]) if side == 1 else (h[i] >= p["stop"])
            target_hit = (h[i] >= p["target"]) if side == 1 else (l[i] <= p["target"])
            if stop_hit or target_hit:
                # Stop takes precedence inside same minute, gap-through stop is not filled optimistically.
                if stop_hit:
                    exit_mid = min(o[i], p["stop"]) if side == 1 else max(o[i], p["stop"])
                    cause = "stop"
                else:
                    exit_mid = p["target"]
                    cause = "target"
                exit_fill = exit_mid - side*SLIP_PTS
                qty = p["qty"]
                gross_mid = side * qty * (exit_mid-p["entry_mid"])
                slip_cost = qty * 2*SLIP_PTS
                fee_cost = qty * (p["entry_fill"]+exit_fill)*FEE_RATE
                gross_after_slip = gross_mid - slip_cost
                net_ex_funding = gross_after_slip - fee_cost
                net = net_ex_funding + p["funding"]
                equity += net
                row = dict(entry_utc=p["entry_utc"], exit_utc=str(d.index[i]),
                    entry_ist_month=str(int(ym[p["entry_i"]])), exit_ist_month=str(int(ym[i])),
                    side="LONG" if side == 1 else "SHORT", signal_day_utc=p["signal_day"],
                    entry_mid=round(p["entry_mid"],4), entry_fill=round(p["entry_fill"],4),
                    exit_mid=round(float(exit_mid),4), exit_fill=round(float(exit_fill),4),
                    stop=round(p["stop"],4), target=round(p["target"],4),
                    initial_risk_pts=round(p["risk_pts"],4), qty_btc=round(qty,8),
                    initial_leverage=round(qty*p["entry_fill"]/p["initial_equity"],5),
                    result=cause, held_minutes=i-p["entry_i"]+1,
                    gross_usd=round(gross_mid,5), slip_usd=round(slip_cost,5),
                    fees_gst_usd=round(fee_cost,5),
                    net_ex_funding_usd=round(net_ex_funding,5),
                    funding_proxy_usd=round(p["funding"],5), funding_events=p["funding_events"],
                    net_usd=round(net,5), net_R=round(net/(qty*p["risk_pts"]),5),
                    equity_usd=round(equity,5))
                rows.append(row)
                p = None
        if i in month_end_indices:
            estimate = equity
            if p is not None:
                exit_est = float(c[i]) - p["side"]*SLIP_PTS
                estimate += (p["side"]*p["qty"]*(exit_est-p["entry_fill"]) -
                             FEE_RATE*p["qty"]*(p["entry_fill"]+exit_est) + p["funding"])
            monthly_eq[month_end_indices[i]] = dict(end_timestamp=str(d.index[i]),
                                                     equity_marked=estimate,
                                                     open_position=(p is not None))
    trades = pd.DataFrame(rows)
    monthly_rows = []
    prev = INITIAL
    for ymnum, z in sorted(monthly_eq.items()):
        end = float(z["equity_marked"])
        month = f"{ymnum//100:04d}-{ymnum%100:02d}"
        closed = trades[trades.exit_ist_month == str(ymnum)] if len(trades) else pd.DataFrame()
        monthly_rows.append(dict(month_ist=month, end_equity_usd=round(end,2),
            net_return_pct=round(100*(end/prev-1),3),
            trades_closed=len(closed),
            wins=int((closed.net_usd>0).sum()) if len(closed) else 0,
            losses=int((closed.net_usd<=0).sum()) if len(closed) else 0,
            net_closed_usd=round(float(closed.net_usd.sum()),2) if len(closed) else 0,
            open_position_at_end=z["open_position"],
            complete=month not in ("2026-11",)))
        prev = end
    m = pd.DataFrame(monthly_rows)
    r = trades.net_usd.to_numpy(float) if len(trades) else np.array([])
    wins = r[r>0].sum()
    losses = -r[r<0].sum()
    curve = np.r_[INITIAL, m.end_equity_usd.to_numpy(float)]
    dd = (curve/np.maximum.accumulate(curve)-1)*100
    summary = dict(
        source="Delta Exchange India BTCUSD perpetual 1m actual OHLCV",
        timeframe="1D UTC close; next 1m OPEN entry, 1m stop/TP",
        bars_1m=len(d), period_start_utc=str(d.index[0]), period_end_utc=str(d.index[-1]),
        initial_equity_usd=INITIAL, final_marked_equity_usd=round(float(m.end_equity_usd.iloc[-1]),2),
        raw_daily_signals=entry_signals, ignored_while_position_open=ignored,
        invalid_risk_signals=invalid, trades_closed=len(trades),
        wins=int((r>0).sum()), losses=int((r<=0).sum()),
        win_rate_pct=round(float(100*(r>0).mean()),2) if len(r) else None,
        profit_factor_net=round(float(wins/losses),3) if losses>0 else None,
        avg_R_net=round(float(trades.net_R.mean()),4) if len(trades) else None,
        total_gross_usd=round(float(trades.gross_usd.sum()),2) if len(trades) else 0,
        total_slippage_usd=round(float(trades.slip_usd.sum()),2) if len(trades) else 0,
        total_fees_gst_usd=round(float(trades.fees_gst_usd.sum()),2) if len(trades) else 0,
        funding_proxy_usd=round(float(trades.funding_proxy_usd.sum()),2) if len(trades) else 0,
        net_closed_usd=round(float(r.sum()),2),
        max_drawdown_month_end_pct=round(float(dd.min()),2),
        positive_complete_ist_months=int(((m.net_return_pct>0)&m.complete).sum()),
        total_complete_ist_months=int(m.complete.sum()),
        funding_settlements_with_open_positions=funding_checks,
        missing_funding_rate_proxy_events=funding_missing,
        remaining_position=None if p is None else dict(side=p["side"],entry_utc=p["entry_utc"],
            entry_fill=p["entry_fill"],stop=p["stop"],target=p["target"],qty_btc=p["qty"]),
        caveats=[
            "Source is Delta BTCUSD perpetual not Binance BTCUSDT spot: cross-venue replication differs.",
            "Publisher permits concurrent opposite side positions; this uses only one total position.",
            "Simulated 5 USD adverse slippage per side, 0.05% taker fee each side plus 18% GST.",
            "Funding rates are hourly indicative proxies, not actual payments; not proven executable.",
            "No spread/L1 order book, impact, fill depth, liquidation, contract minimums or real margin.",
            "Month-end equity includes unrealized open position at pessimistic estimated exit cost.",
            "2026 is previously research-exposed, not a pristine out-of-sample validation."
        ]
    )
    return trades, m, summary


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    d, source_files = load_1m()
    a, signals, raw = daily_signals(d)
    funding, nparts = load_funding()
    tr, mo, summary = backtest(d, signals, funding)
    summary["days_complete"] = int((a["count"]==1440).sum())
    summary["raw_daily_signals_computed"] = raw
    summary["source_partitions"] = len(source_files)
    summary["funding_proxy_partitions"] = nparts
    tr.to_csv(OUT/"trade_ledger.csv",index=False)
    mo.to_csv(OUT/"monthly_ist.csv",index=False)
    (OUT/"summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False)+"\n")
    from collections import defaultdict
    yrs = []
    for label, group in mo.groupby(mo.month_ist.str[:4], sort=True):
        begin = INITIAL if label=="2025" else float(mo.loc[mo.month_ist == f"{int(label)-1}-12", "end_equity_usd"].iloc[-1])
        finish = float(group.end_equity_usd.iloc[-1])
        yrs.append({"year":label,"return_pct":round(100*(finish/begin-1),3),
                    "trades_closed":int(group.trades_closed.sum()),"complete":bool(group.complete.all())})
    pd.DataFrame(yrs).to_csv(OUT/"yearly_ist.csv",index=False)
    report = [
        "# BTCUSD daily Bollinger(30,2), 3R — genuine 1m execution replication",
        "",
        "**Data:** genuine Delta India BTCUSD perpetual 1-minute bars, no reconstructed wick path.",
        "**Signal:** completed UTC day close outside Bollinger(30, 2); stop 0.25 Wilder ATR14 beyond signal bar low/high.",
        "**Fill:** next 1m OPEN; fixed 3R; stop wins ambiguous same-minute bar. No time exit, no trailing.",
        "**Costs:** 0.05% futures taker fee per side and GST 18% on fee; 5 BTC points adverse slip each side; hourly historical funding rates only as a settlement proxy.",
        "**Sizing:** 1% account initial stop-risk, maximum 2x notional/account equity, one position at once, continuous quantity proxy.",
        "**Critical differences from published spot test:** Delta futures, later executable next-minute entry, no concurrent opposites, full Delta fee/tax assumptions.",
        "",
        "## Summary",
        "~~~json",json.dumps(summary,indent=2),"~~~","",
        "## Monthly marked-to-market IST account results",
        mo.to_markdown(index=False),"",
        "## Yearly account results",
        pd.DataFrame(yrs).to_markdown(index=False),"",
        "## Important validity",
        "- Nov 2026 is incomplete. 2025/2026 have prior research exposure; these are not blind validation months.",
        "- Funding estimates do NOT equal reconciled settlement cashflows. Rates treated as percent per source conventions.",
        "- One-minute bars still cannot resolve a stop/target hit order within the same minute; STOP wins ties, conservatively.",
        "- Yearly/monthly marked equity subtracts hypothetical exit fees on positions open at month-end.",
        "- No exchange bid/ask or liquidation modeling. Do not trade live from this study alone.",
        "",
        "See trade_ledger.csv, monthly_ist.csv, yearly_ist.csv and summary.json."
    ]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")
    print("DAILY_BB30_3R_COMPLETE")
    print(json.dumps(summary,indent=2))
    print(mo.to_string(index=False))


if __name__ == "__main__":
    main()
