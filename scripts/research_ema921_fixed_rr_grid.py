#!/usr/bin/env python3
"""BTCUSD 1H+15M EMA9/21 filter, 5M EMA cross, fixed SL/TP grid.

Matches the 100/200 baseline before reporting any other results.
Historical multiple-comparisons study. NOT a live-edge certification.
"""
from __future__ import annotations
import calendar
import json
from pathlib import Path
import numpy as np
import pandas as pd

from research_ema921_1h15m5m_rr import candidates, load_source

ROOT = Path("analysis/ema921_fixed_rr_grid")
SLIP = 5.0
FEE_GST = 0.0005 * 1.18
IST = "Asia/Kolkata"
START = pd.Timestamp("2025-01-01", tz=IST)
END = pd.Timestamp("2026-11-01", tz=IST)
PAIR_GRID = [
    (50,100),(50,150),(50,200),
    (75,150),(75,225),
    (100,150),(100,200),(100,300),(100,400),(100,500),
    (150,300),(150,450),(150,600),
    (200,300),(200,400),(200,600),(200,800),
    (250,500),(250,750),(250,1000),
    (300,600),(300,900),(300,1200),
    (400,800),(400,1200),(400,1600)
]
REQUIRED_PAIRS = {(100,200),(100,300),(200,600),(200,800)}
assert REQUIRED_PAIRS.issubset(PAIR_GRID)
assert len(PAIR_GRID) == len(set(PAIR_GRID)) == 26

def replay(raw, timestamps, candidates_list, sl_pts, tp_pts, weekdays):
    o = raw.open.to_numpy(dtype=float)
    h = raw.high.to_numpy(dtype=float)
    l = raw.low.to_numpy(dtype=float)
    c = raw.close.to_numpy(dtype=float)
    loc = raw.index.tz_convert(IST)
    local_month_int = loc.year.to_numpy(np.int32)*12 + loc.month.to_numpy(np.int32)
    n = len(o)
    lower = int(START.tz_convert("UTC").timestamp())
    upper = int(END.tz_convert("UTC").timestamp())
    last_exit = -1
    rows = []
    ignored_overlap, ignored_weekend = 0,0
    for k, side, _unused_prior_swing_stop in candidates_list:
        if k < 0 or k >= n or timestamps[k] < lower or timestamps[k] >= upper:
            continue
        if k <= last_exit:
            ignored_overlap += 1
            continue
        if weekdays and loc[k].weekday() >= 5:
            ignored_weekend += 1
            continue
        entry = o[k] + side*SLIP
        stop = entry - side*sl_pts
        target = entry + side*tp_pts
        exit_j = None
        exit_price = None
        kind = None
        for j in range(k,n):
            gap_stop = o[j] <= stop if side == 1 else o[j] >= stop
            hit_stop = l[j] <= stop if side == 1 else h[j] >= stop
            hit_target = h[j] >= target if side == 1 else l[j] <= target
            if gap_stop:
                exit_j,exit_price,kind = j,o[j],"stop_gap"
                break
            if hit_stop:
                exit_j,exit_price,kind = j,stop,(
                    "stop_tie" if hit_target else "stop"
                )
                break
            if hit_target:
                exit_j,exit_price,kind = j,target,"target"
                break
            if j + 1 >= n or timestamps[j+1]-timestamps[j] != 60:
                exit_j,exit_price,kind = j,c[j],"data_edge"
                break
            if local_month_int[j+1] != local_month_int[j]:
                exit_j,exit_price,kind = j,c[j],"month_flat"
                break
        if exit_j is None:
            raise AssertionError("Unclosed position")
        out_fill = exit_price - side*SLIP
        fee = FEE_GST * (entry + out_fill)
        net_points = side*(out_fill-entry) - fee
        last_exit = exit_j
        rows.append({
            "entry_ist":loc[k].isoformat(),
            "exit_ist":loc[exit_j].isoformat(),
            "month_ist":loc[exit_j].strftime("%Y-%m"),
            "direction":"LONG" if side==1 else "SHORT",
            "stop_pts":sl_pts, "tp_pts":tp_pts,
            "entry_fill":round(float(entry),3),
            "stop_price":round(float(stop),3),
            "tp_price":round(float(target),3),
            "exit_fill":round(float(out_fill),3),
            "exit_reason":kind,
            "duration_minutes":int(exit_j-k+1),
            "gross_pts":round(float(side*(exit_price-o[k])),3),
            "fee_gst_usd_per_btc":round(float(fee),6),
            "slippage_usd_per_btc":2*SLIP,
            "net_usd_per_btc":round(float(net_points),6),
            "net_1x_pct":float(100*net_points/entry),
            "winner":bool(net_points>0)
        })
    return rows,{"skipped_overlap":ignored_overlap,
                 "skipped_weekend":ignored_weekend}

def month_coverage(raw):
    local = raw.index.tz_convert(IST)
    actual = pd.Series(1,index=local).groupby(local.strftime("%Y-%m")).count()
    names = pd.period_range("2025-01","2026-10",freq="M").astype(str).tolist()
    return names,{
        m:{
            "expected":calendar.monthrange(int(m[:4]),int(m[5:]))[1]*1440,
            "observed":int(actual.get(m,0)),
            "missing":int(calendar.monthrange(int(m[:4]),int(m[5:]))[1]*1440-actual.get(m,0))
        } for m in names
    }

def analyze(rows, names, coverage, weekdays, sl_pts, tp_pts, skip):
    case = f"{'weekdays' if weekdays else 'all_days'}_SL{sl_pts}_TP{tp_pts}"
    df = pd.DataFrame(rows)
    for r in rows:
        r["case"] = case
    n = len(rows)
    wins = sum(x["winner"] for x in rows)
    ends = {"stop":0,"target":0,"month_flat":0,"data_edge":0}
    for x in rows:
        key=x["exit_reason"]
        if key.startswith("stop"): key="stop"
        ends[key] += 1
    month_rows=[]
    equity,peak,max_dd=1.0,1.0,0.0
    for m in names:
        start_eq = equity
        sub = df[df.month_ist.eq(m)] if n else pd.DataFrame()
        for trade in sub.itertuples(index=False):
            equity *= max(0.0,1 + trade.net_1x_pct/100)
            peak = max(peak,equity)
            max_dd=max(max_dd,100*(1-equity/peak))
        month_rows.append({
            "case":case,"month_ist":m,"sl_points":sl_pts,"tp_points":tp_pts,
            "trades":len(sub),
            "wins":int(sub.winner.sum()) if len(sub) else 0,
            "losses":int(len(sub)-sub.winner.sum()) if len(sub) else 0,
            "net_1x_account_pct":float(100*(equity/start_eq-1)),
            "complete_source_month":coverage[m]["missing"]==0
        })
    y2025 = np.prod([
        1+x["net_1x_account_pct"]/100 for x in month_rows
        if x["month_ist"]<"2026-01"
    ])
    y2026 = np.prod([
        1+x["net_1x_account_pct"]/100 for x in month_rows
        if x["month_ist"]>="2026-01"
    ])
    pos = [x["net_usd_per_btc"] for x in rows if x["net_usd_per_btc"]>0]
    neg = [-x["net_usd_per_btc"] for x in rows if x["net_usd_per_btc"]<0]
    summary = {
        "case":case,"stop_points":sl_pts,"tp_points":tp_pts,
        "rr":round(tp_pts/sl_pts,3),"weekdays_only_IST":weekdays,
        "trades":n,"wins":wins,"losses":n-wins,
        "win_rate_pct":float(100*wins/n) if n else 0,
        "target_hit":ends["target"],"stop_hit":ends["stop"],
        "month_flat_exits":ends["month_flat"],"data_edge_exits":ends["data_edge"],
        "positive_months_22":sum(x["net_1x_account_pct"]>0 for x in month_rows),
        "positive_months_2025":sum(
            x["net_1x_account_pct"]>0 for x in month_rows if x["month_ist"]<"2026-01"
        ),
        "positive_months_2026_JanOct":sum(
            x["net_1x_account_pct"]>0 for x in month_rows if x["month_ist"]>="2026-01"
        ),
        "return_2025_pct":float(100*(y2025-1)),
        "return_2026_JanOct_pct":float(100*(y2026-1)),
        "net_1x_account_pct":float(100*(equity-1)),
        "max_closed_trade_drawdown_pct":float(max_dd),
        "profit_factor_net_points":float(sum(pos)/sum(neg)) if neg else None,
        "gross_points_sum_per_btc":float(sum(x["gross_pts"] for x in rows)),
        "total_fee_GST_usd_per_btc":float(sum(x["fee_gst_usd_per_btc"] for x in rows)),
        "total_slippage_usd_per_btc":float(sum(x["slippage_usd_per_btc"] for x in rows)),
        "net_usd_per_btc":float(sum(x["net_usd_per_btc"] for x in rows)),
        **skip
    }
    return summary,month_rows

def main():
    ROOT.mkdir(parents=True, exist_ok=True)
    raw, timestamps, gaps = load_source()
    events,signal_stats=candidates(raw)
    names, coverage = month_coverage(raw)
    print("DATA",len(raw),"signals",len(events),"gaps",len(gaps),flush=True)
    all_ledger=[]
    all_monthly=[]
    summaries=[]
    for weekdays in (True,False):
        for sl,tp in PAIR_GRID:
            trades,skips=replay(raw,timestamps,events,sl,tp,weekdays)
            summ,month=analyze(trades,names,coverage,weekdays,sl,tp,skips)
            # Mandatory parity check against the already-executed baseline.
            if (sl,tp)==(100,200):
                expected=(1130,359) if weekdays else (1549,482)
                actual=(summ["trades"],summ["wins"])
                if actual!=expected:
                    raise RuntimeError(f"Baseline parity FAILED {actual}, expected {expected}")
            all_ledger.extend(trades)
            all_monthly.extend(month)
            summaries.append(summ)
            print("CASE",summ["case"],"trades",summ["trades"],
                  "wins",summ["wins"],"months",summ["positive_months_22"],
                  "net_1x",round(summ["net_1x_account_pct"],3),flush=True)
    df=pd.DataFrame(summaries)
    mdf=pd.DataFrame(all_monthly)
    pd.DataFrame(all_ledger).to_csv(ROOT/"trade_ledger_all_combinations.csv",index=False)
    df.to_csv(ROOT/"summary_all_combinations.csv",index=False)
    mdf.to_csv(ROOT/"monthly_all_combinations.csv",index=False)
    (ROOT/"quality.json").write_text(json.dumps({
        "candle_count":len(raw),"source":"Delta Exchange India BTCUSD 1m",
        "data_start_utc":str(raw.index[0]),"data_end_utc":str(raw.index[-1]),
        "source_gaps":gaps,"month_coverage_IST":coverage,
        "signal_stats":signal_stats,"pairs_checked":PAIR_GRID,
        "baseline_parity":"PASS",
        "slippage_each_side_points":SLIP,
        "fee_each_side_with_GST_fraction":FEE_GST,
        "caveats":"OHLC only, no live bids/asks, funding, slippage distribution or liquidation. 2026 already researched."
    },indent=2))
    # Rank ONLY by 2025 return, avoiding 2026 used as tuning score,
    # but this ranking is IN-SAMPLE and multiple-comparison biased.
    by_2025=df.sort_values(["return_2025_pct","positive_months_2025"],
                            ascending=[False,False])
    mandatory=df[(df.stop_points.eq(100)&df.tp_points.isin([200,300])) |
                 (df.stop_points.eq(200)&df.tp_points.isin([600,800]))]
    rank_cols=["case","trades","wins","losses","win_rate_pct",
               "positive_months_22","positive_months_2025","positive_months_2026_JanOct",
               "return_2025_pct","return_2026_JanOct_pct","net_1x_account_pct",
               "max_closed_trade_drawdown_pct","profit_factor_net_points"]
    wide=mdf[mdf.case.isin(mandatory.case)].pivot(
        index="month_ist",columns="case",values="net_1x_account_pct"
    ).reset_index()
    report=[
        "# EMA9/21 1H+15M+5M — fixed BTC price-point SL/TP sensitivity",
        "",
        "## Scope and reproducibility",
        f"Tested {len(PAIR_GRID)} exact SL/TP pairs x 2 session masks = {len(df)} scenarios.",
        "Signals unchanged from prior historical EMA 9/21 entry research.",
        "Original 1m OHLC data; stop-first on 1m ties; no trailing or timeout.",
        "Fee 0.05%/side plus 18% GST and $5 execution slip/side, 1x fully-notional account.",
        "No funding/orderbook or liquidation. All sample months were previously inspected and ",
        "**none constitutes a blind holdout**. Top-ranked configurations involve multiple-testing bias.",
        f"Quality: {len(raw):,} 1-minute bars; {len(gaps)} gaps; ",
        f"missing IST minutes: {[(m,x['missing']) for m,x in coverage.items() if x['missing']]}.",
        "Baseline 100/200 parity assertions passed (weekday and all-day counts).",
        "",
        "## Specifically requested pairs (100/200, 100/300, 200/600, 200/800)",
        mandatory[rank_cols].to_markdown(index=False,floatfmt=".2f"),
        "",
        "## Best 2025-only training returns — check unchanged 2026",
        by_2025[rank_cols].head(12).to_markdown(index=False,floatfmt=".2f"),
        "",
        "## All combinations — weekdays only, ranked by 2025 return",
        by_2025[by_2025.weekdays_only_IST][rank_cols].to_markdown(
            index=False,floatfmt=".2f"
        ),
        "",
        "## All combinations — 7 days, ranked by 2025 return",
        by_2025[~by_2025.weekdays_only_IST][rank_cols].to_markdown(
            index=False,floatfmt=".2f"
        ),
        "",
        "## Monthly 1x net account returns (%) for four requested points pairs",
        wide.to_markdown(index=False,floatfmt=".2f"),
        "",
        "## Limitations",
        "- Returns are compounded on an unleveraged 1x notional account and use net estimated fills.",
        "- Max drawdown only samples equity after trade closes, not intratrade adverse excursion.",
        "- Source 2025 January IST month is incomplete by 330 minutes.",
        "- Same minute stop+target collision always counts stop first.",
        "- IST month-end forces closure; those exits are separately counted.",
        "- No separate funding, true spread, market impact, exchange lot limit or liquidation modeling.",
        "- User-requested exit sweep is partial overlap, not a new trading signal.",
        "",
        "## Machine-readable outputs",
        "- summary_all_combinations.csv",
        "- monthly_all_combinations.csv",
        "- trade_ledger_all_combinations.csv",
        "- quality.json",
        "- NOVELTY_CHECK.md"
    ]
    (ROOT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")
    print("COMPLETE",json.dumps({
        "scenarios":len(df),
        "best_2025":by_2025[rank_cols].head(5).to_dict("records"),
        "required":mandatory[rank_cols].to_dict("records"),
    }),flush=True)

if __name__ == "__main__":
    main()
