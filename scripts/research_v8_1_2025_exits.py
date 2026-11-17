#!/usr/bin/env python3
"""V8.1 2025 BTC exit experiment: FIXED V8 daily+4H aligned entries, varied exits.

Uses completed candles and next-1m OPEN entry. No 2026 observations; fee+GST,
bidirectional slippage, exclusive positions and stop-first minute-level fills.
This is exploratory 2025 historical modeling, not a reliable future profit claim.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
from research_v8_2025_big_moves import hourly_features
from research_v7_2_daily_4h_2025 import load_2025

START = pd.Timestamp("2025-03-01", tz="UTC")
END = pd.Timestamp("2026-01-01", tz="UTC")
FEE_GST_PER_SIDE = 0.0005 * 1.18  # taker 0.05% * 1.18 GST
SLIP = 5.0
STOP_PTS = 1000.0
MAX_HOLD_MIN = 48*60

# Predeclared exit comparisons; only exit settings vary, NOT entry rules.
VARIANTS = {
    "fixed_500": dict(mode="fixed", target=500, hours=48),
    "fixed_750": dict(mode="fixed", target=750, hours=48),
    "fixed_1000": dict(mode="fixed", target=1000, hours=48),
    "fixed_1500": dict(mode="fixed", target=1500, hours=48),
    "fixed_2000": dict(mode="fixed", target=2000, hours=48),
    "fixed_3000": dict(mode="fixed", target=3000, hours=48),
    "fixed_5000": dict(mode="fixed", target=5000, hours=48),
    "fixed_2000_24h": dict(mode="fixed", target=2000, hours=24),
    "trail_1000_500": dict(mode="trailing", activation=1000, trail=500, hours=48),
    "trail_1500_750": dict(mode="trailing", activation=1500, trail=750, hours=48),
}

def initial_signals(hourly: pd.DataFrame) -> pd.DataFrame:
    """Every completed 1h time when 4h AND Daily aligned. Same V8 signal."""
    out = []
    for ts,z in hourly.loc[(hourly.index>=START)&(hourly.index<END)].iterrows():
        if ts.tz_convert("Asia/Kolkata").weekday()>=5:
            continue
        if z.day_long and z.four_long:
            out.append((ts, 1))
        elif z.day_short and z.four_short:
            out.append((ts, -1))
    signals = pd.DataFrame(out,columns=["signal_utc","side"])
    if signals.empty:
        raise RuntimeError("No eligible alignment signals in 2025")
    return signals

def first_hit(condition: np.ndarray) -> int:
    result = np.flatnonzero(condition)
    return int(result[0]) if len(result) else 2**31-1

def simulate_variant(minute: pd.DataFrame, signals: pd.DataFrame,
                     spec: dict, label: str) -> pd.DataFrame:
    idx=minute.index
    O=minute.open.to_numpy(dtype=float)
    H=minute.high.to_numpy(dtype=float)
    L=minute.low.to_numpy(dtype=float)
    C=minute.close.to_numpy(dtype=float)
    next_allowed=0
    trades=[]
    n=len(idx)

    for signal in signals.itertuples(index=False):
        i=int(idx.searchsorted(signal.signal_utc))
        if i>=n or i<next_allowed:
            continue
        side=int(signal.side)
        length=min(int(spec["hours"])*60,n-i)
        end=i+length
        entry=O[i]+side*SLIP
        initial_stop=entry-side*STOP_PTS
        hs=H[i:end];ls=L[i:end];opens=O[i:end]
        favorable=(hs-entry) if side==1 else (entry-ls)
        adverse=(entry-ls) if side==1 else (hs-entry)
        initial_hit=first_hit(adverse>=STOP_PTS)

        if spec["mode"]=="fixed":
            target_hit=first_hit(favorable>=float(spec["target"]))
            if initial_hit<=target_hit and initial_hit<length:
                hit=initial_hit;reason="STOP"
                raw_stop=initial_stop
                raw_exit=min(raw_stop,opens[hit]) if side==1 else max(raw_stop,opens[hit])
            elif target_hit<length:
                hit=target_hit;reason="TARGET"
                raw_exit=entry+side*float(spec["target"])
            else:
                hit=length-1
                reason="YEAR_END" if end==n else "TIME_EXIT"
                raw_exit=C[i+hit]
        else:
            # Evaluate trailing stop on 1m high/low. Same-minute ambiguity is
            # pessimistically resolved as stop first, never assumed target first.
            peak=np.maximum.accumulate(favorable)
            active=peak>=float(spec["activation"])
            trail_line=entry+side*(peak-float(spec["trail"]))
            if side==1:
                effective_stop=np.where(active,np.maximum(initial_stop,trail_line),initial_stop)
                trail_hit=(ls<=effective_stop)
            else:
                effective_stop=np.where(active,np.minimum(initial_stop,trail_line),initial_stop)
                trail_hit=(hs>=effective_stop)
            trailing_index=first_hit(trail_hit)
            if trailing_index<length:
                hit=trailing_index
                reason="TRAIL_STOP" if active[hit] and (
                    (effective_stop[hit]>initial_stop) if side==1
                    else (effective_stop[hit]<initial_stop)) else "STOP"
                raw_stop=effective_stop[hit]
                raw_exit=min(raw_stop,opens[hit]) if side==1 else max(raw_stop,opens[hit])
            else:
                hit=length-1
                reason="YEAR_END" if end==n else "TIME_EXIT"
                raw_exit=C[i+hit]

        j=i+hit
        exit_price=raw_exit-side*SLIP
        gross=side*(exit_price-entry)
        cost=(entry+exit_price)*FEE_GST_PER_SIDE
        net=gross-cost
        # Last minute included for MFE/MAE; diagnostic only, not entry logic.
        max_fav=float(np.max(favorable[:hit+1]))
        max_adv=float(np.max(adverse[:hit+1]))
        trades.append(dict(
            variant=label, signal_utc=signal.signal_utc,
            entry_utc=idx[i], exit_utc=idx[j],
            side="LONG" if side==1 else "SHORT",
            exit_reason=reason,entry_price=round(entry,2),
            exit_price=round(exit_price,2),
            gross_points=round(float(gross),2),
            modeled_cost_points=round(float(cost),2),
            net_points=round(float(net),2),
            mfe_points=round(max_fav,2),mae_points=round(max_adv,2),
            realized_1000plus=bool(gross>=1000),
            duration_minutes=int(hit+1),
            exit_month=idx[j].strftime("%Y-%m")
        ))
        # One open position per variant, next signal strictly after exited minute.
        next_allowed=j+1
    return pd.DataFrame(trades)

def metrics(frame: pd.DataFrame):
    months={f"2025-{i:02d}":0.0 for i in range(3,13)}
    if frame.empty:
        return dict(trades=0,win_rate_pct=None,net_points=0,profit_factor=None,
                    max_drawdown_points=0,profitable_months=0,monthly_net_points=months)
    groups=frame.groupby("exit_month").net_points.sum()
    for name in months:
        months[name]=round(float(groups.get(name,0)),2)
    net=frame.net_points.to_numpy(dtype=float)
    positive=float(net[net>0].sum())
    negative=-float(net[net<0].sum())
    equity=np.cumsum(net)
    dd=np.maximum.accumulate(np.r_[0,equity])[1:]-equity
    return dict(
        trades=len(frame),
        wins=int((net>0).sum()),
        win_rate_pct=round(100*float((net>0).mean()),2),
        net_points=round(float(net.sum()),2),
        profit_factor=round(positive/negative,3) if negative>0 else None,
        max_drawdown_points=round(float(dd.max()),2),
        profitable_months=int(sum(v>0 for v in months.values())),
        gross_points=round(float(frame.gross_points.sum()),2),
        modeled_cost_points=round(float(frame.modeled_cost_points.sum()),2),
        realized_1000plus=int(frame.realized_1000plus.sum()),
        median_duration_hours=round(float(frame.duration_minutes.median()/60),1),
        monthly_net_points=months,
    )

def compare_period(frame: pd.DataFrame):
    if frame.empty:return dict(mar_aug=metrics(frame),sep_dec=metrics(frame))
    month=frame.exit_month
    return dict(
        mar_aug=metrics(frame[month<"2025-09"]),
        sep_dec=metrics(frame[month>="2025-09"])
    )

def make_report(summary: dict):
    lines=[
        "# V8.1 — BTC 2025 Exit Comparisons","",
        "**Historical model, not a proven profitable trading system. No 2026 candles.**","",
        "## Fixed entry across EVERY exit comparison","",
        "- On each completed hourly candle, daily and 4h trend EMAs must BOTH align.",
        "- Daily/4h up: Close > EMA20 > EMA50 for LONG; inverse for SHORT.",
        "- Enter at next 1-minute OPEN, weekdays IST only, whenever no position is open.",
        "- Only one open position per variant, no daily trade limit.",
        "- 1,000 BTC-point initial stop, monitored 1-minute, gap-aware, stop-first if ambiguous.",
        "- Compare fixed +500/+750/+1000/+1500/+2000/+3000/+5000 point targets,",
        "  +2000 with 24h max, and 1,000/500 or 1,500/750 activation/trailing.",
        "- All other variants have a 48-hour maximum hold; remaining trades closed at 2025 year-end.",
        "- Taker fees: 0.05% per side +18% GST, plus 5 BTC-point adverse slippage per side.",
        "- No funding or margin/liquidation modeling. Price-points are 1-BTC-equivalent, NOT USD account returns.",
        "",
        "## Exclusive trade backtests","",
        "| Exit | Trades | Win % | Net points | Profit factor | Profitable months | Drawdown pts |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for name,r in summary["variants"].items():
        lines.append(f"| {name} | {r['trades']} | {r['win_rate_pct']} | {r['net_points']} | {r['profit_factor']} | {r['profitable_months']}/10 | {r['max_drawdown_points']} |")
    lines+=["","## Monthly net points (exit month)","",
        "| Month | "+" | ".join(summary["variants"].keys())+" |",
        "|---|"+"---:|"*len(summary["variants"])]
    for mo in (f"2025-{m:02d}" for m in range(3,13)):
        lines.append("| "+mo+" | "+" | ".join(str(v["monthly_net_points"][mo]) for v in summary["variants"].values())+" |")
    lines+=["","## Split stability — net points","",
        "| Exit | Mar–Aug | Sep–Dec |",
        "|---|---:|---:|"]
    for name,r in summary["split"].items():
        lines.append(f"| {name} | {r['mar_aug']['net_points']} | {r['sep_dec']['net_points']} |")
    lines+=["","## Limitations","",
        "- This changes only the exit; entry remains V8 Daily+4H aligned, a condition not previously profitable.",
        "- Candidate trades are exclusive per variant; trade populations diverge after exits (realistic path dependence).",
        "- Trailing is conservatively stop-first on an ambiguous 1-minute candle.",
        "- No 2026 test, no unseen holdout, no live market impact, actual fees or funding.",
        "- Do not select a strategy solely because one of many exits wins on 2025.",
        ""]
    return "\n".join(lines)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--data-dir",type=Path,default=Path("data/delta_india/BTCUSD/1m"))
    ap.add_argument("--output-dir",type=Path,default=Path("analysis/v8_1_2025_exits"))
    args=ap.parse_args()
    data=load_2025(args.data_dir)
    features=hourly_features(data)
    signals=initial_signals(features)
    output={};periods={};ledgers=[]
    for label,config in VARIANTS.items():
        trades=simulate_variant(data,signals,config,label)
        output[label]=metrics(trades)
        periods[label]=compare_period(trades)
        if not trades.empty:ledgers.append(trades)
    summary={
        "source":"2025 Delta India BTCUSD futures 1m",
        "period":"2025-03-01 through 2025-12-31",
        "initial_signal_count":int(len(signals)),
        "initial_stop_points":STOP_PTS,
        "variants":output,"split":periods,
        "caveat":"2025 historical testing; 2026 untouched, not a proven profit edge"
    }
    args.output_dir.mkdir(parents=True,exist_ok=True)
    (args.output_dir/"v8_1_summary.json").write_text(json.dumps(summary,indent=2)+"\n")
    (args.output_dir/"V8_1_RESEARCH_REPORT.md").write_text(make_report(summary)+"\n")
    signals.to_csv(args.output_dir/"v8_1_entry_signals.csv",index=False)
    (pd.concat(ledgers,ignore_index=True) if ledgers else pd.DataFrame()).to_csv(
        args.output_dir/"v8_1_trade_ledger.csv",index=False)
    print(make_report(summary))

if __name__=="__main__":
    main()
