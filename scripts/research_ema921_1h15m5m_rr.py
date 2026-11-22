#!/usr/bin/env python3
"""Pre-registered EMA9/EMA21 1H+15M+5M trend / 5M cross: 2R vs 3R.

Uses closed higher-timeframe candles and next 1m open. Research, not live signals.
No model selection or parameter fitting on 2026. See NOVELTY_CHECK.md.
"""
from __future__ import annotations

import calendar
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("data/delta_india/BTCUSD/1m")
OUT = Path("analysis/ema921_1h15m5m_rr")
FEE_PER_SIDE_WITH_GST = 0.0005 * 1.18
ADVERSE_SLIP_USD_PER_SIDE = 5.0
STOP_BUFFER_USD = 5.0
MAX_HOLD_1M = 1440
IST = "Asia/Kolkata"
CUTOFF = pd.Timestamp("2026-11-01 00:00:00", tz=IST)
FIRST = pd.Timestamp("2025-01-01 00:00:00", tz=IST)


def load_source():
    names = sorted(ROOT.glob("20??-??.csv.gz"))
    if len(names) < 22:
        raise ValueError(f"Need >=22 authentic monthly files, found {len(names)}")
    pieces = []
    for path in names:
        x = pd.read_csv(path, compression="gzip",
                        usecols=["time", "open", "high", "low", "close", "volume"])
        if x.empty:
            raise ValueError(f"Empty archive partition: {path}")
        pieces.append(x)
    raw = pd.concat(pieces, ignore_index=True).sort_values("time")
    raw["time"] = raw.time.astype("int64")
    ts = raw.time.to_numpy(np.int64)
    if not (np.diff(ts) > 0).all():
        raise ValueError("Duplicated or unsorted 1m timestamp")
    if ((np.diff(ts) % 60) != 0).any():
        raise ValueError("Non-minute candle timestamps")
    if not np.isfinite(raw[["open","high","low","close","volume"]].to_numpy(float)).all():
        raise ValueError("OHLCV NaN or infinity")
    if ((raw.low <= 0) | (raw.high < raw.low) |
        (raw.open < raw.low) | (raw.open > raw.high) |
        (raw.close < raw.low) | (raw.close > raw.high) |
        (raw.volume < 0)).any():
        raise ValueError("Inconsistent OHLCV")
    gaps_at = np.flatnonzero(np.diff(ts) != 60)
    gaps = [{"after_utc": str(pd.to_datetime(ts[j], unit="s", utc=True)),
             "before_utc": str(pd.to_datetime(ts[j+1], unit="s", utc=True)),
             "missing_minutes": int((ts[j+1]-ts[j]) // 60 - 1)}
            for j in gaps_at]
    raw.index = pd.to_datetime(raw.time, unit="s", utc=True)
    return raw, ts, gaps


def candles(raw, minutes):
    key = f"{minutes}min"
    a = raw[["open","high","low","close"]].resample(
        key, label="right", closed="left"
    ).agg({"open":"first","high":"max","low":"min","close":"last"})
    counts = raw.close.resample(key, label="right", closed="left").count()
    # Do not treat a partially aggregated bar, or the bars after a gap,
    # as a causal EMA signal. 21 consecutive complete bars are required.
    full = counts.eq(minutes)
    a["valid"] = full.rolling(21, min_periods=21).min().eq(1)
    a["ema9"] = a.close.ewm(span=9, adjust=False, min_periods=21).mean()
    a["ema21"] = a.close.ewm(span=21, adjust=False, min_periods=21).mean()
    return a


def candidates(raw):
    five = candles(raw, 5)
    quarter = candles(raw, 15)
    hour = candles(raw, 60)
    q = quarter.reindex(five.index, method="ffill")
    h = hour.reindex(five.index, method="ffill")
    complete = (five.valid & q.valid.fillna(False) & h.valid.fillna(False))
    up5 = five.ema9 > five.ema21
    dn5 = five.ema9 < five.ema21
    long_cross = up5 & five.ema9.shift(1).le(five.ema21.shift(1))
    short_cross = dn5 & five.ema9.shift(1).ge(five.ema21.shift(1))
    long_higher = ((q.ema9 > q.ema21) & (q.close > q.ema9) &
                   (h.ema9 > h.ema21) & (h.close > h.ema9))
    short_higher = ((q.ema9 < q.ema21) & (q.close < q.ema9) &
                    (h.ema9 < h.ema21) & (h.close < h.ema9))
    signals = complete & (long_cross & long_higher | short_cross & short_higher)
    sl_l = five.low.rolling(3, min_periods=3).min() - STOP_BUFFER_USD
    sl_s = five.high.rolling(3, min_periods=3).max() + STOP_BUFFER_USD
    ix = raw.index.get_indexer(five.index)
    entry_mask = signals.to_numpy(bool) & (ix >= 0)
    locs = np.flatnonzero(entry_mask)
    events = []
    for j in locs:
        side = 1 if bool(long_cross.iloc[j] and long_higher.iloc[j]) else -1
        events.append((int(ix[j]), side,
                       float(sl_l.iloc[j] if side == 1 else sl_s.iloc[j])))
    events.sort(key=lambda z: z[0])
    return events, {"complete_5m_bars": int(five.valid.sum()),
                    "candidate_5m_crosses": len(events),
                    "long_candidates": sum(x[1] == 1 for x in events),
                    "short_candidates": sum(x[1] == -1 for x in events)}


def replay(raw, timestamps, events, rr, weekdays_only):
    o = raw.open.to_numpy(float)
    hi = raw.high.to_numpy(float)
    lo = raw.low.to_numpy(float)
    cl = raw.close.to_numpy(float)
    local = raw.index.tz_convert(IST)
    months = local.year.to_numpy(np.int32) * 12 + local.month.to_numpy(np.int32)
    cutoff_ts = int(CUTOFF.tz_convert("UTC").timestamp())
    first_ts = int(FIRST.tz_convert("UTC").timestamp())
    n = len(o)
    previous_exit = -1
    skipped_wrong_side = 0
    skipped_overlap = 0
    skipped_weekend = 0
    ledger = []
    for k, side, stop in events:
        if k >= n - 1 or timestamps[k] >= cutoff_ts or timestamps[k] < first_ts:
            continue
        if k <= previous_exit:
            skipped_overlap += 1
            continue
        if weekdays_only and local[k].dayofweek >= 5:
            skipped_weekend += 1
            continue
        # Entry at the 1m opening, after 5m signal candle already closed.
        mid_entry = o[k]
        risk = side * (mid_entry - stop)
        if not np.isfinite(risk) or risk <= 0:
            skipped_wrong_side += 1
            continue
        target = mid_entry + side * rr * risk
        exit_index = None
        exit_mid = None
        exit_type = None
        for j in range(k, min(n, k + MAX_HOLD_1M)):
            open_stop = (o[j] <= stop if side == 1 else o[j] >= stop)
            touched_stop = (lo[j] <= stop if side == 1 else hi[j] >= stop)
            touched_tp = (hi[j] >= target if side == 1 else lo[j] <= target)
            # Preserve worst-case assumption when both limits hit in 1m.
            if open_stop:
                exit_index, exit_mid, exit_type = j, o[j], "stop_gap"
                break
            if touched_stop:
                exit_index, exit_mid, exit_type = j, stop, (
                    "stop_and_tp_same_minute" if touched_tp else "stop")
                break
            if touched_tp:
                exit_index, exit_mid, exit_type = j, target, "target"
                break
            if j + 1 >= n or timestamps[j+1] - timestamps[j] != 60:
                exit_index, exit_mid, exit_type = j, cl[j], "data_boundary"
                break
            if months[j+1] != months[j]:
                exit_index, exit_mid, exit_type = j, cl[j], "month_flat"
                break
        if exit_index is None:
            exit_index = min(n-1, k+MAX_HOLD_1M-1)
            exit_mid = cl[exit_index]
            exit_type = "timeout_24h"
        entry_fill = mid_entry + side * ADVERSE_SLIP_USD_PER_SIDE
        exit_fill = exit_mid - side * ADVERSE_SLIP_USD_PER_SIDE
        fee_usd = FEE_PER_SIDE_WITH_GST * (entry_fill + exit_fill)
        gross_pts = side * (exit_mid - mid_entry)
        net_pts = side * (exit_fill - entry_fill) - fee_usd
        previous_exit = exit_index
        ledger.append({
            "entry_ist": local[k].isoformat(),
            "exit_ist": local[exit_index].isoformat(),
            "month_ist": local[exit_index].strftime("%Y-%m"),
            "direction": "LONG" if side == 1 else "SHORT",
            "rr": rr, "weekdays_only": weekdays_only,
            "entry_mid": round(mid_entry, 3),
            "entry_fill": round(entry_fill, 3),
            "stop": round(stop, 3), "target": round(target, 3),
            "exit_mid": round(exit_mid, 3),
            "exit_fill": round(exit_fill, 3),
            "risk_points": round(risk, 3),
            "gross_points": round(gross_pts, 3),
            "fees_gst_usd_per_btc": round(fee_usd, 4),
            "slip_cost_usd_per_btc": 2 * ADVERSE_SLIP_USD_PER_SIDE,
            "net_usd_per_btc": round(net_pts, 4),
            "net_pct_on_1x_notional": 100.0 * net_pts / mid_entry,
            "net_r": net_pts / risk,
            "result": "WIN" if net_pts > 0 else "LOSS",
            "exit_type": exit_type,
            "minutes_held": int(exit_index - k + 1)
        })
    return ledger, {
        "skipped_overlap": skipped_overlap,
        "skipped_weekend": skipped_weekend,
        "skipped_gap_beyond_stop": skipped_wrong_side
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    raw, secs, gaps = load_source()
    events, signal_stats = candidates(raw)
    schedule = pd.period_range("2025-01", "2026-10", freq="M").astype(str).tolist()
    local = raw.index.tz_convert(IST)
    counts = pd.Series(1, index=local).groupby(local.strftime("%Y-%m")).count()
    coverage = {}
    for month in schedule:
        y, m = map(int, month.split("-"))
        expected = calendar.monthrange(y, m)[1] * 1440
        observed = int(counts.get(month, 0))
        coverage[month] = {
            "observed_minutes": observed, "expected_minutes": expected,
            "complete_ist_month": observed == expected,
            "missing_minutes": expected - observed
        }
    all_ledger = []
    summaries = []
    monthly = []
    for weekdays in (True, False):
        for rr in (2.0, 3.0):
            rows, ignored = replay(raw, secs, events, rr, weekdays)
            all_ledger.extend(rows)
            df = pd.DataFrame(rows)
            case = f"{'weekdays_IST' if weekdays else 'all_days'}_{int(rr)}R"
            equity, peak, dd = 1.0, 1.0, 0.0
            for m in schedule:
                subset = df[df.month_ist.eq(m)] if not df.empty else pd.DataFrame()
                eq_start = equity
                if not subset.empty:
                    for r in subset.itertuples(index=False):
                        equity *= (1.0 + r.net_pct_on_1x_notional / 100.0)
                        peak = max(peak, equity)
                        dd = max(dd, 100.0 * (1.0 - equity / peak))
                monthly.append({
                    "case": case, "month_ist": m, 
                    "net_account_return_pct": 100 * (equity / eq_start - 1),
                    "trades": len(subset),
                    "wins": int((subset.result == "WIN").sum()) if len(subset) else 0,
                    "losses": int((subset.result == "LOSS").sum()) if len(subset) else 0,
                    "complete_data": coverage[m]["complete_ist_month"]
                })
            wins = int((df.result == "WIN").sum()) if not df.empty else 0
            stop_count = int(df.exit_type.str.startswith("stop").sum()) if not df.empty else 0
            ntr = len(df)
            this_months = [x for x in monthly if x["case"] == case]
            sm = {
                "case": case, "rr": rr, "weekdays_only": weekdays,
                "trades": ntr, "wins": wins, "losses": ntr - wins,
                "win_rate_pct": 100.0 * wins / ntr if ntr else 0.0,
                "targets_hit": int((df.exit_type == "target").sum()) if ntr else 0,
                "stops_hit": stop_count,
                "timeout_exits": int((df.exit_type == "timeout_24h").sum()) if ntr else 0,
                "monthly_flatten_exits": int((df.exit_type == "month_flat").sum()) if ntr else 0,
                "net_points_per_btc": float(df.net_usd_per_btc.sum()) if ntr else 0.0,
                "total_fee_gst_usd_per_btc": float(df.fees_gst_usd_per_btc.sum()) if ntr else 0.0,
                "total_slip_usd_per_btc": float(df.slip_cost_usd_per_btc.sum()) if ntr else 0.0,
                "net_account_return_compounded_pct": (equity - 1) * 100,
                "max_closed_trade_drawdown_pct": dd,
                "positive_months_22": sum(x["net_account_return_pct"] > 0 for x in this_months),
                "months_ge_10pct_22": sum(x["net_account_return_pct"] >= 10 for x in this_months),
                "2025_account_return_pct": 100 * (
                    np.prod([1+x["net_account_return_pct"]/100 for x in this_months[:12]]) - 1
                ),
                "2026_Jan_Oct_account_return_pct": 100 * (
                    np.prod([1+x["net_account_return_pct"]/100 for x in this_months[12:]]) - 1
                ),
                **ignored
            }
            summaries.append(sm)
            print("CASE", case, json.dumps(sm, sort_keys=True), flush=True)
    pd.DataFrame(all_ledger).to_csv(OUT/"trade_ledger.csv", index=False)
    pd.DataFrame(monthly).to_csv(OUT/"monthly_results.csv", index=False)
    pd.DataFrame(summaries).to_csv(OUT/"summary.csv", index=False)
    quality = {
        "data_source": "GitHub BTC-Analysis Delta Exchange India BTCUSD 1m OHLCV archive",
        "first_utc": str(raw.index[0]), "last_utc": str(raw.index[-1]),
        "one_minute_rows": len(raw), "num_partitions": len(list(ROOT.glob("20??-??.csv.gz"))),
        "gaps": gaps, "coverage_ist": coverage, "signals": signal_stats,
        "full_2025_months": sum(coverage[m]["complete_ist_month"] for m in schedule[:12]),
        "full_2026_Jan_Oct_months": sum(coverage[m]["complete_ist_month"] for m in schedule[12:])
    }
    (OUT/"quality.json").write_text(json.dumps(quality, indent=2))
    def md_table(frame):
        return frame.to_markdown(index=False, floatfmt=".2f")
    sumcols = [
        "case", "trades", "wins", "losses", "win_rate_pct", "targets_hit",
        "stops_hit", "net_account_return_compounded_pct",
        "max_closed_trade_drawdown_pct", "positive_months_22",
        "2025_account_return_pct", "2026_Jan_Oct_account_return_pct"
    ]
    mdf = pd.DataFrame(monthly)
    wide = mdf.pivot(index="month_ist", columns="case",
                     values="net_account_return_pct").reset_index()
    report = [
        "# EMA9/21 1H + 15M + 5M — actual BTCUSD 1-minute replay",
        "",
        "Pre-registered specifications: see NOVELTY_CHECK.md. All settings fixed before test.",
        "",
        "## Four scenario results (fees, GST and adverse $5/side slippage included)",
        md_table(pd.DataFrame(summaries)[sumcols]),
        "",
        "## Net 1x account monthly returns by IST calendar month (%)",
        md_table(wide),
        "",
        "## Data quality and limitations",
        f"- Source 1m rows: {len(raw):,}; span {raw.index[0]} to {raw.index[-1]}",
        f"- Historical missing-data gaps: {json.dumps(gaps)}",
        f"- Months with incomplete IST source: {[(m,c['missing_minutes']) for m,c in coverage.items() if c['missing_minutes']]}",
        f"- Candidate completed 5m aligned EMA crosses: {signal_stats}",
        "- Closed 1H and 15M confirmation; 5M signal known at bar close. Entry at next 1-minute open.",
        "- Same-minute stop and TP: stop-first (conservative), not a known tick sequence.",
        "- 1x fully notional account model, compounding at trade close; max drawdown sampled only at trade exit.",
        "- 2025 and 2026 have previously been researched. 2026 is **seen recheck**, not blind out-of-sample.",
        "- No funding, true bid/ask spread, slippage variability, margin, liquidation, or market depth model.",
        "- Some months may be partial due source gaps. Missing candles were not reconstructed.",
        "",
        "## Files",
        "- trade_ledger.csv; monthly_results.csv; summary.csv; quality.json",
    ]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report) + "\n")
    print("BACKTEST_COMPLETE", json.dumps({"signals": signal_stats, "gaps": gaps,
          "summaries": summaries}), flush=True)


if __name__ == "__main__":
    main()
