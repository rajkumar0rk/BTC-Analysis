#!/usr/bin/env python3
"""V7.1, preregistered research: accepted breakout -> 15m retest -> 15m continuation.

Source: original Delta India BTCUSD 2025 1m OHLCV, no 2026 candles.
Research with consistent 1m execution proxies; not live fill or institutional identity data.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from v7_2025_trend_discovery import START, END, aggregate, context, load

TARGET = 1000.0
STOP = 500.0
SLIPPAGE = 5.0
TAKER_FEE_GST = 0.0005 * 1.18
RETEST_BARS = 8
CONFIRM_BARS = 4
RETEST_ATR_FRACTION = 0.25
BODY_ATR_MIN = 0.40
HORIZONS = (24, 48)
REQUIRED_END = max(HORIZONS) * 60 + (RETEST_BARS + CONFIRM_BARS) * 15

def initial_signals(hour: pd.DataFrame) -> pd.DataFrame:
    out = []
    for ts, z in hour.iterrows():
        if ts < START or ts >= END - pd.Timedelta(minutes=REQUIRED_END):
            continue
        if not np.isfinite(z.atr14) or z.atr14 <= 0 or not z.body_atr >= BODY_ATR_MIN:
            continue
        for side, flag, structure, level in (
            (1, "long_accept", "bull", "prior12_high"),
            (-1, "short_accept", "bear", "prior12_low"),
        ):
            if not bool(z[flag]) or not bool(z[structure]):
                continue
            out.append(dict(
                signal_time=ts, month=ts.strftime("%Y-%m"),
                side=side, boundary=float(z[level]), atr14=float(z.atr14),
                base_entry_time=ts,
            ))
    return pd.DataFrame(out)

def find_retest(signal, quarter: pd.DataFrame):
    """Only COMPLETED future 15m candles; frozen signal boundary/ATR."""
    ts = signal.signal_time
    side = int(signal.side)
    level = float(signal.boundary)
    tolerance = RETEST_ATR_FRACTION * float(signal.atr14)
    window = quarter.loc[
        ts + pd.Timedelta(minutes=15):
        ts + pd.Timedelta(minutes=RETEST_BARS * 15)]
    assert len(window) == RETEST_BARS, (ts, len(window))

    # Must touch the frozen old support/resistance, reject through it at the close.
    # A retest that decisively closes through the level is invalid.
    for t, bar in window.iterrows():
        if side == 1:
            touch = (bar.low <= level + tolerance) and (bar.low >= level - tolerance)
            reclaim = bar.close > level
        else:
            touch = (bar.high >= level - tolerance) and (bar.high <= level + tolerance)
            reclaim = bar.close < level
        if not (touch and reclaim):
            continue

        confirm_window = quarter.loc[
            t + pd.Timedelta(minutes=15):
            t + pd.Timedelta(minutes=CONFIRM_BARS * 15)]
        for confirm_t, confirm in confirm_window.iterrows():
            if side == 1:
                valid = confirm.close > max(float(bar.high), level) and confirm.close > confirm.open
            else:
                valid = confirm.close < min(float(bar.low), level) and confirm.close < confirm.open
            if valid:
                return dict(retest_time=t, confirm_time=confirm_t, entry_time=confirm_t)
        # First valid retest defines the setup. No retrospective choice of later retests.
        return None
    return None

def simulate(minute: pd.DataFrame, time: pd.Timestamp, side: int, horizon_hours: int):
    """Conservative BTC-point proxy with next 1m OPEN and 1m OHLC protective checks.

    Stop wins if stop and target are both present in one 1m candle. Exit slippage
    and fees included in net price-point P&L for one BTC position.
    """
    end = time + pd.Timedelta(hours=horizon_hours)
    if time not in minute.index or end > END:
        return None
    section = minute.loc[time:end - pd.Timedelta(minutes=1)]
    if len(section) != horizon_hours*60:
        raise AssertionError("Missing one-minute candles during horizon")
    raw_open = float(section.iloc[0].open)
    entry = raw_open + side * SLIPPAGE
    target = entry + side * TARGET
    stop = entry - side * STOP
    reason = "TIMEOUT"
    exit_time = section.index[-1]
    exit_raw = float(section.iloc[-1].close)
    max_fav = 0.0
    max_adv = 0.0

    for t, bar in section.iterrows():
        fav = (float(bar.high) - entry) if side == 1 else (entry - float(bar.low))
        adv = (entry - float(bar.low)) if side == 1 else (float(bar.high) - entry)
        max_fav = max(max_fav, fav)
        max_adv = max(max_adv, adv)
        touched_stop = (float(bar.low) <= stop) if side == 1 else (float(bar.high) >= stop)
        touched_target = (float(bar.high) >= target) if side == 1 else (float(bar.low) <= target)
        if touched_stop:
            # If the candle opens beyond the stop, fill at the worse opening price.
            exit_raw = min(stop, float(bar.open)) if side == 1 else max(stop, float(bar.open))
            exit_time = t
            reason = "STOP"
            break
        if touched_target:
            exit_raw = target
            exit_time = t
            reason = "TARGET"
            break

    exit_fill = exit_raw - side * SLIPPAGE
    gross = side * (exit_fill - entry)
    costs = TAKER_FEE_GST * (entry + exit_fill)
    net = gross - costs
    return dict(
        entry_time=time, exit_time=exit_time, entry_price=round(entry, 2),
        exit_price=round(exit_fill, 2), exit_reason=reason,
        gross_pts=round(gross, 3), cost_pts=round(costs, 3),
        net_pts=round(net, 3),
        target_before_stop=(reason == "TARGET"),
        mfe_pts=round(max_fav, 2), mae_pts=round(max_adv, 2),
    )

def label_all(base: pd.DataFrame, quarter: pd.DataFrame, minute: pd.DataFrame):
    records = []
    for sig in base.itertuples(index=False):
        rt = find_retest(sig, quarter)
        for cohort, entry_time in (
            ("V7_control", sig.base_entry_time),
            ("V7_1_retest", rt["entry_time"] if rt is not None else None),
        ):
            if entry_time is None:
                records.append(dict(
                    signal_time=sig.signal_time, signal_month=sig.month,
                    side="LONG" if sig.side == 1 else "SHORT",
                    cohort=cohort, status="NO_RETEST_CONFIRM",
                    entry_time=pd.NaT, horizon_h=24, target_before_stop=False,
                    net_pts=np.nan, exit_time=pd.NaT,
                ))
                continue
            for horizon in HORIZONS:
                outcome = simulate(minute, entry_time, int(sig.side), horizon)
                if outcome is None:
                    raise AssertionError("Insufficient 2025 horizon data")
                records.append(dict(
                    signal_time=sig.signal_time, signal_month=sig.month,
                    side="LONG" if sig.side == 1 else "SHORT",
                    cohort=cohort, status="ENTERED", horizon_h=horizon,
                    retest_time=rt["retest_time"] if rt else pd.NaT,
                    confirm_time=rt["confirm_time"] if rt else pd.NaT,
                    **outcome,
                ))
    return pd.DataFrame(records)

def distinct_trades(events: pd.DataFrame):
    """Research-only one-position-at-a-time, same minute execution for both cohorts."""
    result = {}
    for cohort in ("V7_control", "V7_1_retest"):
        pool = events.loc[
            (events.cohort == cohort) &
            (events.status == "ENTERED") &
            (events.horizon_h == 24)
        ].sort_values(["entry_time", "signal_time", "side"])
        accepted = []
        active_to = pd.Timestamp("2025-01-01T00:00:00Z")
        for row in pool.itertuples(index=False):
            if row.entry_time < active_to:
                continue
            accepted.append(row._asdict())
            active_to = row.exit_time + pd.Timedelta(minutes=1)
        result[cohort] = pd.DataFrame(accepted)
    return result

def count_summary(frame: pd.DataFrame):
    if frame.empty:
        return {"signals": 0, "target_first": 0, "success_pct": None}
    return {
        "signals": len(frame),
        "target_first": int(frame.target_before_stop.sum()),
        "success_pct": round(100 * frame.target_before_stop.mean(), 2),
    }

def portfolio_summary(trades):
    if trades.empty:
        return dict(trades=0, wins=0, net_points=0.0, profitable_months=0)
    monthly = trades.groupby(trades.exit_time.dt.strftime("%Y-%m")).net_pts.sum().to_dict()
    full_months = {f"2025-{i:02d}": round(float(monthly.get(f"2025-{i:02d}", 0)), 2)
                   for i in range(3, 13)}
    return dict(
        trades=len(trades),
        target_hits=int(trades.target_before_stop.sum()),
        net_points=round(float(trades.net_pts.sum()), 2),
        profitable_months=sum(v > 0 for v in full_months.values()),
        monthly_net_points=full_months,
    )

def make_report(stats):
    lines = [
        "# V7.1 — Breakout / Retest / Continuation: 2025 BTC",
        "",
        "**Research only; no 2026 candles. One-BTC price-point proxies, not account USD profits.**",
        "",
        "## Fixed rules",
        "- Base signal: V7 4H structure + 1H closed 12-bar breakout + strong candle body >=0.4 ATR14.",
        "- Frozen breakout level: the previous 12 completed 1H highs/lows.",
        "- Retest: within next 8 completed 15M bars, touches level within +/-0.25 of 1H ATR and closes back through it.",
        "- Confirmation: a DIFFERENT subsequent completed 15M candle (within 4 bars) closes beyond retest extreme in trend direction.",
        "- Enter at next 1M open when confirmation candle closes. No continuation means no trade.",
        "- Stop = 500 BTC points; target = 1,000 points; maximum 24h. Minute-level stop-first when ambiguous.",
        "- Taker fee 0.05% per side plus GST 18%; 5 points of adverse entry and exit slippage.",
        "- Entries restricted to signals with both candidate 48h evaluation windows fully inside 2025.",
        "",
        "## Signal quality: 24h outcomes, including overlapping signals",
        "",
        "| Metric | V7 base | V7.1 retest |",
        "|---|---:|---:|",
    ]
    x, y = stats["signal_events"]["V7_control"], stats["signal_events"]["V7_1_retest"]
    for label, key in (("Initial eligible signals", "base_signal_count"),
                       ("Confirmed entries", "entered"),
                       ("Reached +1,000 before -500", "target_first"),
                       ("Hit rate (confirmed entries)", "success_pct")):
        lines.append(f"| {label} | {x.get(key)} | {y.get(key)} |")
    lines += [
        "",
        "## Exclusive one-position-at-a-time research replay (24h)",
        "",
        "| Metric | V7 base | V7.1 retest |",
        "|---|---:|---:|",
    ]
    p, q = stats["exclusive"]["V7_control"], stats["exclusive"]["V7_1_retest"]
    for label, key in (("Trades", "trades"), ("Target hits", "target_hits"),
                       ("Net BTC price-point equivalents after costs", "net_points"),
                       ("Profitable months", "profitable_months")):
        lines.append(f"| {label} | {p.get(key)} | {q.get(key)} |")
    lines += [
        "",
        "## Monthly net points, modeled exclusive trades",
        "",
        "| Month | V7 base | V7.1 retest |",
        "|---|---:|---:|",
    ]
    for month in p.get("monthly_net_points", {}):
        lines.append(f"| {month} | {p['monthly_net_points'][month]} | {q['monthly_net_points'].get(month, 0)} |")
    lines += [
        "",
        "## Important caveats",
        "- A 1,000-point hit rate is not strategy profitability; the exclusive replay is a simplified model only.",
        "- Retest signals are chosen causally; all original signals without a confirmation are included as skipped.",
        "- Some signal windows overlap; exclusive replay removes overlapping positions within each model.",
        "- No real bid/ask, slippage distribution, funding payments, leverage/liquidation, or portfolio-risk sizing.",
        "- 2025 development-period selection alone cannot establish future performance.",
        "- Signals at the end of December are censored to avoid using any 2026 candle.",
        "",
    ]
    return "\n".join(lines)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", type=Path, default=Path("data/delta_india/BTCUSD/1m"))
    ap.add_argument("--output-dir", type=Path, default=Path("analysis/v7_1_2025"))
    args = ap.parse_args()

    minute = load(args.data_dir)
    hour = context(aggregate(minute, "1h", 60), aggregate(minute, "4h", 240))
    quarter = aggregate(minute, "15min", 15)
    base = initial_signals(hour)
    if base.empty:
        raise RuntimeError("No baseline 2025 signals")

    events = label_all(base, quarter, minute)
    exclusive = distinct_trades(events)
    x = events[(events.cohort == "V7_control") &
               (events.horizon_h == 24) &
               (events.status == "ENTERED")]
    y = events[(events.cohort == "V7_1_retest") &
               (events.horizon_h == 24) &
               (events.status == "ENTERED")]
    stats = {
        "source": "2025 Delta India BTCUSD 1m OHLCV",
        "initial_signals": len(base),
        "signal_events": {
            "V7_control": dict(base_signal_count=len(base), entered=len(x),
                               **count_summary(x)),
            "V7_1_retest": dict(base_signal_count=len(base), entered=len(y),
                                missed_without_confirmation=len(base)-len(y),
                                **count_summary(y)),
        },
        "exclusive": {k: portfolio_summary(v) for k, v in exclusive.items()},
    }
    report = make_report(stats)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir/"V7_1_RESEARCH_REPORT.md").write_text(report+"\n")
    (args.output_dir/"v7_1_summary.json").write_text(json.dumps(stats, indent=2)+"\n")
    events.to_csv(args.output_dir/"v7_1_event_ledger.csv", index=False)
    for k, v in exclusive.items():
        v.to_csv(args.output_dir/f"{k}_exclusive_trades.csv", index=False)
    print(report)

if __name__ == "__main__":
    main()
