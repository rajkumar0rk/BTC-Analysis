#!/usr/bin/env python3
"""Fixed-rule 4H/1H/15M/5M BTCUSD/ETHUSD backtest using authentic 1M Delta candles.

Pine-source equivalent (not a Stage13 test): all HTF inputs completed at 5M bar
start, 5M breakout at bar close, next 5M open fill, 1M stop-first replay.
No parameter optimization. No funding, order-book or liquidation modeling.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd

FEE = 0.0005 * 1.18             # Delta India taker + GST per side
INITIAL_EQUITY = 10000.0
RISK_PCT = 0.005
MAX_NOTIONAL_EQUITY = 1.0
RR = 2.5
STOP_ATR_BUFFER = 0.10
START = "2025-01"
END = "2026-10"
OUT = Path("analysis/mtf_4h1h15m5m_20261122")


def wilder(s: pd.Series, n: int) -> pd.Series:
    x = s.to_numpy(dtype=float)
    v = np.full(len(x), np.nan, dtype=float)
    valid = np.flatnonzero(np.isfinite(x))
    if len(valid) < n:
        return pd.Series(v, index=s.index)
    first = int(valid[n - 1])
    average = float(np.mean(x[valid[:n]]))
    v[first] = average
    for i in range(first + 1, len(x)):
        if np.isfinite(x[i]):
            average += (float(x[i]) - average) / n
            v[i] = average
    return pd.Series(v, index=s.index)


def archive(asset: str) -> pd.DataFrame:
    base = Path("data/delta_india") / asset / "1m"
    names = [f"{y}-{m:02d}.csv.gz" for y in (2025, 2026)
             for m in range(1, 13) if (y, m) <= (2026, 10)]
    if len(names) != 22:
        raise AssertionError("Expected exactly 22 source months")
    parts = []
    for name in names:
        path = base / name
        if not path.is_file():
            raise FileNotFoundError(path)
        a = pd.read_csv(path, compression="gzip",
                        usecols=["time", "open", "high", "low", "close", "volume"])
        if a.empty:
            raise ValueError(f"Empty source partition {path}")
        parts.append(a)
    f = pd.concat(parts, ignore_index=True)
    t = f.time.to_numpy(dtype=np.int64)
    if np.any(np.diff(t) != 60):
        raise ValueError("Non-contiguous, duplicate or unordered 1-minute source")
    if not np.isfinite(f[["open", "high", "low", "close", "volume"]].to_numpy(float)).all():
        raise ValueError("Non-finite source candle")
    if ((f.low <= 0) | (f.high < f.low) | (f.open < f.low) |
        (f.open > f.high) | (f.close < f.low) |
        (f.close > f.high) | (f.volume < 0)).any():
        raise ValueError("Invalid OHLCV candle")
    if (t[0] != int(pd.Timestamp("2025-01-01", tz="UTC").timestamp()) or
        t[-1] != int(pd.Timestamp("2026-11-01", tz="UTC").timestamp()) - 60):
        raise ValueError("Unexpected source time coverage")
    f.index = pd.to_datetime(f.time, unit="s", utc=True)
    return f


def bars(f: pd.DataFrame, freq: str, size: int) -> pd.DataFrame:
    agg = f[["open", "high", "low", "close", "volume"]].resample(
        freq, closed="left", label="right"
    ).agg({"open": "first", "high": "max", "low": "min",
           "close": "last", "volume": "sum"})
    count = f.close.resample(freq, closed="left", label="right").count()
    agg["valid"] = count.eq(size)
    return agg


def signals(f: pd.DataFrame) -> pd.DataFrame:
    five = bars(f, "5min", 5)
    fifteen = bars(f, "15min", 15)
    hour = bars(f, "1h", 60)
    four = bars(f, "4h", 240)
    four["e50"] = four.close.ewm(span=50, adjust=False).mean()
    four["e200"] = four.close.ewm(span=200, adjust=False).mean()
    four["e50prev"] = four.e50.shift()
    four["ready"] = four.valid & four.valid.rolling(
        200, min_periods=200).min().eq(1)
    hour["e20"] = hour.close.ewm(span=20, adjust=False).mean()
    hour["e50"] = hour.close.ewm(span=50, adjust=False).mean()
    diff = hour.close.diff()
    gain = wilder(diff.clip(lower=0), 14)
    loss = wilder((-diff).clip(lower=0), 14)
    hour["rsi"] = 100. - 100. / (1. + gain / loss.replace(0., np.nan))
    hour.loc[(loss == 0) & (gain > 0), "rsi"] = 100.
    hour.loc[(loss == 0) & (gain == 0), "rsi"] = 50.
    hour["ready"] = hour.valid & hour.valid.rolling(
        50, min_periods=50).min().eq(1)
    fifteen["e20"] = fifteen.close.ewm(span=20, adjust=False).mean()
    prev = fifteen.close.shift()
    tr = pd.concat([fifteen.high - fifteen.low,
                    (fifteen.high - prev).abs(),
                    (fifteen.low - prev).abs()], axis=1).max(axis=1)
    fifteen["atr"] = wilder(tr, 14)
    fifteen["ready"] = fifteen.valid & fifteen.valid.rolling(
        20, min_periods=20).min().eq(1)
    five["e9"] = five.close.ewm(span=9, adjust=False).mean()
    five["e21"] = five.close.ewm(span=21, adjust=False).mean()

    # At each completed 5M candle, the prior HTF bar was already closed
    # when that 5M candle began. No higher-timeframe current-bar leakage.
    at_start = five.index - pd.Timedelta(minutes=5)
    def known(b: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
        data = b[cols].reindex(at_start, method="ffill")
        data.index = five.index
        return data
    d4 = known(four, ["close", "e50", "e200", "e50prev", "ready"])
    d1 = known(hour, ["close", "e20", "e50", "rsi", "ready"])
    p15 = known(fifteen, ["open", "high", "low", "close",
                           "e20", "atr", "ready"])
    long = (five.valid & d4.ready.fillna(False) &
            d1.ready.fillna(False) & p15.ready.fillna(False) &
            (d4.close > d4.e50) & (d4.e50 > d4.e200) &
            (d4.e50 > d4.e50prev) &
            (d1.close > d1.e20) & (d1.e20 > d1.e50) &
            (d1.rsi > 55.) &
            (p15.low <= p15.e20) & (p15.close > p15.e20) &
            (p15.close > p15.open) &
            (five.close > p15.high) & (five.close > five.open) &
            (five.e9 > five.e21))
    short = (five.valid & d4.ready.fillna(False) &
             d1.ready.fillna(False) & p15.ready.fillna(False) &
             (d4.close < d4.e50) & (d4.e50 < d4.e200) &
             (d4.e50 < d4.e50prev) &
             (d1.close < d1.e20) & (d1.e20 < d1.e50) &
             (d1.rsi < 45.) &
             (p15.high >= p15.e20) & (p15.close < p15.e20) &
             (p15.close < p15.open) &
             (five.close < p15.low) & (five.close < five.open) &
             (five.e9 < five.e21))
    out = five[["open", "high", "low", "close"]].copy()
    out["side"] = np.select([long.fillna(False), short.fillna(False)],
                            [1, -1], default=0).astype(np.int8)
    out["stop_long"] = p15.low - STOP_ATR_BUFFER * p15.atr
    out["stop_short"] = p15.high + STOP_ATR_BUFFER * p15.atr
    return out


def replay(f: pd.DataFrame, sig: pd.DataFrame, slip: float) -> pd.DataFrame:
    O = f.open.to_numpy(float)
    H = f.high.to_numpy(float)
    L = f.low.to_numpy(float)
    C = f.close.to_numpy(float)
    times = f.index
    equity = INITIAL_EQUITY
    last_exit = pd.Timestamp("2025-01-01", tz="UTC")
    last_window = None
    records = []
    candidates = sig.loc[sig.side.ne(0)]
    for s in candidates.itertuples():
        t = s.Index                 # 5M signal bar end / next 5M opening time
        if t < last_exit:
            continue
        window = (t - pd.Timedelta(minutes=5)).floor("15min")
        if last_window == window:
            continue
        side = int(s.side)
        stop = float(s.stop_long if side == 1 else s.stop_short)
        signal_price = float(s.close)
        distance = side * (signal_price - stop)
        if not np.isfinite(distance) or distance <= 0:
            continue
        pos = int(times.searchsorted(t))
        if pos >= len(f) or times[pos] != t:
            continue
        entry = float(O[pos])       # exact subsequent 5M OPEN = this 1M OPEN
        target = signal_price + side * RR * distance
        if side * (entry - stop) <= 0 or side * (target - entry) <= 0:
            continue              # unusable gap: cannot place valid bracket
        qty = min(equity * RISK_PCT / distance,
                  equity * MAX_NOTIONAL_EQUITY / signal_price)
        if not np.isfinite(qty) or qty <= 0 or equity <= 0:
            continue
        # Scan 1-minute candles in chronological order. On same-minute
        # stop and limit touch, choose STOP (conservative). Stop gaps fill
        # no better than the minute's opening price.
        why = "end_of_data"
        z = len(f) - 1
        exit_raw = float(C[z])
        for j in range(pos, len(f)):
            stop_hit = (L[j] <= stop) if side == 1 else (H[j] >= stop)
            tp_hit = (H[j] >= target) if side == 1 else (L[j] <= target)
            if stop_hit:
                why = "stop"
                z = j
                exit_raw = min(float(O[j]), stop) if side == 1 \
                           else max(float(O[j]), stop)
                break
            if tp_hit:
                why = "target"
                z = j
                exit_raw = target
                break
        entry_fill = entry + side * slip
        exit_fill = exit_raw - side * slip if why != "target" else exit_raw
        fee = (entry_fill + exit_fill) * qty * FEE
        gross = side * (exit_raw - entry) * qty
        net = side * (exit_fill - entry_fill) * qty - fee
        before = equity
        equity += net
        records.append({
            "signal_utc": t.isoformat(), "entry_utc": times[pos].isoformat(),
            "exit_utc": times[z].isoformat(),
            "side": "LONG" if side == 1 else "SHORT",
            "entry_open": round(entry, 4), "entry_fill": round(entry_fill, 4),
            "stop": round(stop, 4), "target": round(target, 4),
            "exit_fill": round(exit_fill, 4), "exit_reason": why,
            "risk_points": round(distance, 4), "quantity_btc_equiv": round(qty, 8),
            "fee_usd": round(fee, 6), "gross_usd": round(gross, 6),
            "net_usd": round(net, 6), "equity_before": round(before, 6),
            "equity_after": round(equity, 6)
        })
        last_exit = times[z] + pd.Timedelta(minutes=1)
        last_window = window
    return pd.DataFrame.from_records(records)


def summarize(trades: pd.DataFrame, asset: str, slip: float) -> tuple[dict, pd.DataFrame]:
    months = pd.period_range(START, END, freq="M").astype(str).tolist()
    if trades.empty:
        return {"asset": asset, "slippage_usd_per_market_or_stop_fill": slip,
                "trades": 0, "net_usd": 0, "return_pct": 0,
                "profitable_months": 0, "losing_months": 0,
                "no_trade_months": 22}, pd.DataFrame([
                    {"month_utc": month, "trades": 0, "net_usd": 0.0,
                     "return_pct": 0.0, "status": "NO_TRADE"} for month in months])
    v = trades.net_usd.to_numpy(float)
    peak = np.maximum.accumulate(np.r_[INITIAL_EQUITY, trades.equity_after.to_numpy(float)])
    eq = np.r_[INITIAL_EQUITY, trades.equity_after.to_numpy(float)]
    drawdown = 100 * np.max((peak - eq) / peak)
    profits = float(v[v > 0].sum())
    losses = float(-v[v < 0].sum())
    t = trades.copy()
    t["month_utc"] = pd.to_datetime(t.exit_utc, utc=True).dt.strftime("%Y-%m")
    monthly = []
    current = INITIAL_EQUITY
    for month in months:
        sub = t[t.month_utc == month]
        net = float(sub.net_usd.sum())
        ret = 100 * net / current if current > 0 else float("nan")
        monthly.append({"month_utc": month, "trades": int(len(sub)),
                        "net_usd": round(net, 4), "return_pct": round(ret, 4),
                        "status": "PROFIT" if net > 0 else "LOSS" if net < 0
                                  else "NO_TRADE"})
        current += net
    mo = pd.DataFrame(monthly)
    summary = {
        "asset": asset,
        "data_period_utc": "2025-01-01 through 2026-10-31",
        "slippage_usd_per_market_or_stop_fill": slip,
        "initial_equity_usd": INITIAL_EQUITY,
        "ending_equity_usd": round(float(trades.equity_after.iloc[-1]), 4),
        "net_usd": round(float(v.sum()), 4),
        "return_pct": round(float(v.sum()) / INITIAL_EQUITY * 100, 4),
        "trades": int(len(trades)),
        "longs": int(trades.side.eq("LONG").sum()),
        "shorts": int(trades.side.eq("SHORT").sum()),
        "win_rate_pct": round(float(np.mean(v > 0)) * 100, 4),
        "profit_factor": round(profits / losses, 4) if losses > 0 else None,
        "max_closed_trade_drawdown_pct": round(float(drawdown), 4),
        "stops": int(trades.exit_reason.eq("stop").sum()),
        "targets": int(trades.exit_reason.eq("target").sum()),
        "profitable_months": int(mo.status.eq("PROFIT").sum()),
        "losing_months": int(mo.status.eq("LOSS").sum()),
        "no_trade_months": int(mo.status.eq("NO_TRADE").sum()),
        "year2025_net_usd": round(float(mo.loc[mo.month_utc.str.startswith("2025"), "net_usd"].sum()), 4),
        "year2026_jan_oct_net_usd": round(float(mo.loc[mo.month_utc.str.startswith("2026"), "net_usd"].sum()), 4)
    }
    return summary, mo


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--assets", nargs="+", default=["BTCUSD", "ETHUSD"])
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    all_results = []
    month_rows = []
    for asset in args.assets:
        f = archive(asset)
        sig = signals(f)
        print(f"{asset} minute candles={len(f)} candidate 5M signals={int(sig.side.ne(0).sum())}", flush=True)
        for slip, label in [(2., "reference_2usd"), (5., "stress_5usd")]:
            tr = replay(f, sig, slip)
            result, mo = summarize(tr, asset, slip)
            result["scenario"] = label
            result["candidate_5m_signals"] = int(sig.side.ne(0).sum())
            result["observed_one_minute_candles"] = len(f)
            all_results.append(result)
            mo.insert(0, "scenario", label)
            mo.insert(0, "asset", asset)
            month_rows.append(mo)
            tr.to_csv(OUT / f"{asset}_{label}_trades.csv.gz",
                      compression="gzip", index=False)
            print("RESULT " + json.dumps(result), flush=True)
    monthly = pd.concat(month_rows, ignore_index=True)
    monthly.to_csv(OUT / "monthly_UTC.csv", index=False)
    pd.DataFrame(all_results).to_csv(OUT / "summary.csv", index=False)
    payload = {
        "strategy": "4H EMA50>EMA200 and rising; 1H EMA20>EMA50, RSI14>55; prior 15M EMA20 rejection; next 5M closes beyond pullback high; mirror SHORT",
        "htf": "Higher-timeframe values locked at 5M bar start; no unfinished HTF bars",
        "entry": "5M signal close, following 5M/1M OPEN",
        "exit": "15M pullback extreme +/- 0.1*Wilder ATR14; 2.5R TP; 1M stop-first path",
        "sizing": "0.5% equity theoretical stop-risk cap, 1x notional cap, linear BTC/ETH-equivalent quantity",
        "costs": "0.05% Delta India taker fee + 18% GST each fill, assumed adverse $2/$5 per market/stop fill; target limit at level without slippage",
        "month_timezone": "UTC",
        "limitations": [
            "Historical 2025-2026 periods already used for other research; not pristine out-of-sample",
            "EMA200 requires 200 completed 4H bars of warmup, so January 2025 may have zero entries",
            "No funding, real bid/ask spreads, spread impact, liquidation, or contract-step/minimum sizing",
            "Signal-close bracket levels can differ from next-open realized reward/risk on gaps",
            "Bar-close strategy cannot reproduce exact intraminute queue or exchange order execution",
            "Closed-trade drawdown ignores unrealized intratrade drawdown",
            "1-minute OHLC simultaneous hits always stop-first (conservative)"
        ],
        "results": all_results
    }
    (OUT / "quality_and_results.json").write_text(json.dumps(payload, indent=2) + "\n")
    print("MONTHLY_UTC\n" + monthly.to_string(index=False), flush=True)


if __name__ == "__main__":
    main()
