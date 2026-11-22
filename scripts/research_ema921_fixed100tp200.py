#!/usr/bin/env python3
"""EMA9/21 1H+15M+5M, exact fixed 100-point SL / 200-point TP.

Pre-registered in analysis/ema921_fixed100_200/NOVELTY_CHECK.md.
Use the SAME completed-candle signal generator as the previous 2R/3R experiment.
No maximum holding time: trades settle at 1m stop/target, month close or data edge.
"""
from __future__ import annotations

import calendar
import json
from pathlib import Path

import numpy as np
import pandas as pd
from research_ema921_1h15m5m_rr import candidates, load_source

OUT = Path("analysis/ema921_fixed100_200")
IST = "Asia/Kolkata"
FIRST = pd.Timestamp("2025-01-01T00:00:00", tz=IST)
CUTOFF = pd.Timestamp("2026-11-01T00:00:00", tz=IST)
SL_PTS = 100.0
TP_PTS = 200.0
SLIPPAGE = 5.0
FEE_WITH_GST = 0.0005 * 1.18


def replay(raw, secs, events, weekdays):
    op = raw.open.to_numpy(float)
    hi = raw.high.to_numpy(float)
    lo = raw.low.to_numpy(float)
    close = raw.close.to_numpy(float)
    idx = raw.index.tz_convert(IST)
    months = idx.year.to_numpy(np.int32) * 12 + idx.month.to_numpy(np.int32)
    n = len(op)
    start_ts = int(FIRST.tz_convert("UTC").timestamp())
    cutoff_ts = int(CUTOFF.tz_convert("UTC").timestamp())
    rows = []
    last_exit = -1
    skips = {"overlap":0, "weekend":0, "out_of_period":0}
    for k, side, _old_swing_stop in events:
        if k >= n or secs[k] < start_ts or secs[k] >= cutoff_ts:
            skips["out_of_period"] += 1
            continue
        if k <= last_exit:
            skips["overlap"] += 1
            continue
        if weekdays and idx[k].weekday() >= 5:
            skips["weekend"] += 1
            continue
        # Stop/target price levels are measured from the actual assumed entry
        # fill, not the mid price, so the requested distance is exactly 100/200.
        entry_fill = op[k] + side * SLIPPAGE
        stop = entry_fill - side * SL_PTS
        target = entry_fill + side * TP_PTS
        exit_j = None
        exit_quote = None
        reason = None
        for j in range(k, n):
            stop_gap = (op[j] <= stop if side == 1 else op[j] >= stop)
            stop_hit = (lo[j] <= stop if side == 1 else hi[j] >= stop)
            target_hit = (hi[j] >= target if side == 1 else lo[j] <= target)
            # Conservative rule: in the same one-minute bar, assume stop first.
            if stop_gap:
                exit_j, exit_quote, reason = j, op[j], "stop_gap"
                break
            if stop_hit:
                exit_j, exit_quote, reason = j, stop, (
                    "stop_first_both_touched" if target_hit else "stop")
                break
            if target_hit:
                exit_j, exit_quote, reason = j, target, "target"
                break
            if j + 1 >= n or secs[j+1] - secs[j] != 60:
                exit_j, exit_quote, reason = j, close[j], "data_boundary"
                break
            if months[j+1] != months[j]:
                exit_j, exit_quote, reason = j, close[j], "month_flat"
                break
        if exit_j is None:
            raise AssertionError("No stop/target/boundary closure")
        exit_fill = exit_quote - side * SLIPPAGE
        fee = FEE_WITH_GST * (entry_fill + exit_fill)
        gross = side * (exit_quote - op[k])
        net = side * (exit_fill - entry_fill) - fee
        last_exit = exit_j
        rows.append({
            "entry_ist": idx[k].isoformat(),
            "exit_ist": idx[exit_j].isoformat(),
            "month_ist": idx[exit_j].strftime("%Y-%m"),
            "side": "LONG" if side == 1 else "SHORT",
            "weekdays_IST_only": weekdays,
            "entry_price_mid": round(float(op[k]),3),
            "assumed_entry_fill": round(float(entry_fill),3),
            "fixed_stop_price": round(float(stop),3),
            "fixed_target_price": round(float(target),3),
            "exit_quote": round(float(exit_quote),3),
            "assumed_exit_fill": round(float(exit_fill),3),
            "gross_points": round(float(gross),3),
            "fees_with_gst_usd_per_btc": round(float(fee),4),
            "slippage_usd_per_btc": 2 * SLIPPAGE,
            "net_usd_per_btc": round(float(net),4),
            "net_1x_trade_return_pct": float(100 * net / entry_fill),
            "net_positive": bool(net>0),
            "exit_type": reason,
            "minutes_held": int(exit_j-k+1),
        })
    return pd.DataFrame(rows), skips


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    raw, secs, gaps = load_source()
    entries, signal_stats = candidates(raw)
    local_ix = raw.index.tz_convert(IST)
    obs = pd.Series(1,index=local_ix).groupby(local_ix.strftime("%Y-%m")).count()
    ordered_months = pd.period_range("2025-01", "2026-10", freq="M").astype(str).tolist()
    coverage = {}
    for m in ordered_months:
        year, month = map(int, m.split("-"))
        expected = calendar.monthrange(year, month)[1] * 24 * 60
        actual = int(obs.get(m, 0))
        coverage[m] = {"actual":actual, "expected":expected,
                       "missing":expected-actual, "complete":actual==expected}
    summaries=[]
    monthly=[]
    combined=[]
    for weekdays in (True, False):
        df, skips = replay(raw,secs,entries,weekdays)
        case = "weekdays_IST_SL100_TP200" if weekdays else "all_days_SL100_TP200"
        df.insert(0,"case",case)
        combined.append(df)
        equity = 1.0
        highwater = 1.0
        max_dd = 0.0
        for m in ordered_months:
            trades = df[df.month_ist == m]
            starting = equity
            for trade in trades.itertuples(index=False):
                equity *= max(0, 1 + trade.net_1x_trade_return_pct / 100.0)
                highwater = max(highwater,equity)
                max_dd = max(max_dd,100*(1-equity/highwater))
            monthly.append({
                "case":case,
                "month_ist":m,
                "trades":int(len(trades)),
                "wins":int(trades.net_positive.sum()),
                "losses":int(len(trades)-trades.net_positive.sum()),
                "net_account_return_pct":float(100*(equity/starting-1)),
                "complete_data":coverage[m]["complete"]
            })
        net_2025 = np.prod([
            1+r["net_account_return_pct"]/100
            for r in monthly if r["case"] == case and r["month_ist"] < "2026-01"
        ])
        net_2026 = np.prod([
            1+r["net_account_return_pct"]/100
            for r in monthly if r["case"] == case and r["month_ist"] >= "2026-01"
        ])
        wins = int(df.net_positive.sum())
        summaries.append({
            "case":case,
            "trades":len(df),
            "wins":wins,
            "losses":len(df)-wins,
            "win_rate_pct":float(100*wins/len(df)) if len(df) else 0.0,
            "targets_hit":int((df.exit_type=="target").sum()),
            "stops_hit":int(df.exit_type.str.startswith("stop").sum()),
            "month_flat_exits":int((df.exit_type=="month_flat").sum()),
            "data_boundary_exits":int((df.exit_type=="data_boundary").sum()),
            "gross_points_per_btc":float(df.gross_points.sum()),
            "total_fee_gst_per_btc":float(df.fees_with_gst_usd_per_btc.sum()),
            "total_slippage_per_btc":float(df.slippage_usd_per_btc.sum()),
            "net_points_per_btc":float(df.net_usd_per_btc.sum()),
            "2025_return_pct":float(100*(net_2025-1)),
            "2026_JanOct_return_pct":float(100*(net_2026-1)),
            "total_1x_account_return_pct":float(100*(equity-1)),
            "max_trade_close_drawdown_pct":float(max_dd),
            "positive_months":sum(r["net_account_return_pct"]>0
                                   for r in monthly if r["case"]==case),
            **skips,
        })
        print("RESULT",json.dumps(summaries[-1],sort_keys=True),flush=True)
    pd.concat(combined,ignore_index=True).to_csv(OUT/"trade_ledger.csv",index=False)
    pd.DataFrame(summaries).to_csv(OUT/"summary.csv",index=False)
    pd.DataFrame(monthly).to_csv(OUT/"monthly_results.csv",index=False)
    (OUT/"quality.json").write_text(json.dumps({
        "candle_count":int(len(raw)), "first_utc":str(raw.index[0]),
        "last_utc":str(raw.index[-1]), "gaps":gaps, "signal_stats":signal_stats,
        "coverage":coverage,
        "entry_fill_slip_usd":SLIPPAGE, "exit_fill_slip_usd":SLIPPAGE,
        "taker_fee_with_gst_each_side":FEE_WITH_GST,
        "fixed_sl_pts":SL_PTS, "fixed_tp_pts":TP_PTS
    },indent=2))
    summ_df = pd.DataFrame(summaries)
    month_df = pd.DataFrame(monthly)
    cols = ["case","trades","wins","losses","win_rate_pct","targets_hit",
            "stops_hit","2025_return_pct","2026_JanOct_return_pct",
            "total_1x_account_return_pct","max_trade_close_drawdown_pct",
            "positive_months"]
    wide = month_df.pivot(index="month_ist",columns="case",
                          values="net_account_return_pct").reset_index()
    report = [
        "# BTCUSD EMA9/21 (1H + 15M + 5M): Fixed 100-point stop / 200-point target",
        "",
        "## Complete 1-minute execution results",
        "",
        summ_df[cols].to_markdown(index=False,floatfmt=".2f"),
        "",
        "## IST calendar month net 1x account returns (%)",
        "",
        wide.to_markdown(index=False,floatfmt=".2f"),
        "",
        "## Exact execution and caveats",
        "- Reuses the already-verified signal generator from the previous 2R/3R experiment.",
        "- **100-point SL and 200-point TP are measured from slippage-adjusted entry fill**.",
        "- Confirm 1H and 15M bars are fully closed, confirm 5M close crossover, enter at next available 1m open.",
        "- On 1m stop+target ties, **stop executes first**; stop gaps use adverse opening price.",
        "- No timeout and no trailing; one open trade per case; IST month boundary flattened.",
        "- Entries compared on IST Monday-Friday only vs unrestricted 7 days; existing open trades can exit on weekends.",
        "- Includes 0.05% taker fee per side, 18% GST on fees, and $5 adverse execution per side.",
        "- 1× notional compounding at trade close; maximum drawdown based only on trade-close equity.",
        f"- Data: {len(raw):,} source 1m bars, {raw.index[0]} to {raw.index[-1]}.",
        f"- Historical data gaps: {json.dumps(gaps)}.",
        f"- Partial IST month: {[(m,c['missing']) for m,c in coverage.items() if not c['complete']]}",
        "- 2025 and 2026 previously researched, **not blind forward-tested**. November 2026 excluded.",
        "- No funding, order book spread/impact, maker fills, margin/lot feasibility or liquidation.",
        "- Do not describe a negative/positive return as guaranteed future performance.",
        "",
        "## Reproducible artifacts",
        "- NOVELTY_CHECK.md, trade_ledger.csv, monthly_results.csv, summary.csv, quality.json",
    ]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")
    print("COMPLETE",json.dumps(summaries,sort_keys=True),flush=True)


if __name__=="__main__":
    main()
