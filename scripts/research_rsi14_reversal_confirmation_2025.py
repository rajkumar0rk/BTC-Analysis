"""Predefined reversal-specific entry confirmations, BTCUSD 2025 only."""
import hashlib
import json
from datetime import datetime
from pathlib import Path

import numpy as np

from research_rsi14_runner_refinements_2025 import (
    ROOT, START, END, checks, load, replay, dt, export_bundle,
)

OUT = Path("scratch/rsi14_reversal_confirmation")
MODES = ("direct", "reversal-candle", "rsi-recovery", "reversal-candle-breakout")
EXITS = (("original-high-profit", 3000, 0), ("original-low-drawdown", 2000, 1000))


def entries_for(bars, signals, snapshots, extra, rsi, mode):
    O, H, L, C = bars
    entries = []
    for q, (i, d, r, hi, lo) in enumerate(signals):
        until = signals[q+1][0] if q+1 < len(signals) else len(O)
        j = i
        level = hi if d == 1 else lo
        if mode != "direct":
            j = -1
            for k in range(i+15, until, 15):
                _, _, o, c = snapshots[k]
                if mode == "rsi-recovery":
                    previous, current = rsi.get(k-15), rsi.get(k)
                    if previous is None or current is None:
                        continue
                    ok = (previous <= 20 < current if d == 1 else previous >= 80 > current)
                else:
                    ok = d * (c-o) > 0
                if ok:
                    j = k
                    break
            if j < 0:
                continue
        confirmed = j
        if mode == "reversal-candle-breakout":
            hits = np.flatnonzero(d*(C[j:until-1]-level) > 0)
            if not len(hits):
                continue
            j += int(hits[0])+1
        if j >= until or j >= len(O):
            continue
        atr, ema, _, _ = snapshots[(j//15)*15]
        _, _, _, ph, pl, _ = extra[confirmed]
        structure = pl-.5 if d == 1 else ph+.5
        entries.append((j, d, r, i, atr, ema, structure, level, confirmed))
    return entries


def run():
    checks()
    bars, momentum, snapshots, extra, rec = load()
    signals = [(i, -d, r, hi, lo) for i,d,r,hi,lo in momentum]
    # Recorder names are canonical (e.g. rsi.value), not base aliases.
    rsi_defs = [m for d, m in zip(rec.specs, rec.definitions)
                if d.base == "rsi" and m["timeframe_minutes"] == 15]
    assert len(rsi_defs) == 1, rec.definitions
    rsi_id = rsi_defs[0]["id"]
    rsi = {(t-START)//60: r for t,r in rec.series[rsi_id]}
    n = len(bars[0])//15+1
    atr, st, line = (np.full(n, np.nan) for _ in range(3))
    for k,v in snapshots.items():
        for arr,value in ((atr,v[0]),(st,extra[k][1]),(line,extra[k][2])):
            if value is not None:
                arr[k//15] = value
    ind = (atr,st,line)
    variants = []
    for mode in MODES:
        entries = entries_for(bars, signals, snapshots, extra, rsi, mode)
        for label, tp, be in EXITS:
            base = (mode, False, 1000, tp, be)
            def run_case(es):
                return replay(bars, es, ind, base, False, "fixed-1r", False, False, False, 0)
            # Signals that occurred while a previous position was open cannot
            # leave a pending entry behind after that position closes.
            eligible = []
            free = 0
            for e in entries:
                if e[3] < free:
                    continue
                trade = run_case([e])["trades"][0]
                free = (int(datetime.fromisoformat(trade["exit_utc"]).timestamp())-START)//60+1
                eligible.append(e)
            v = run_case(eligible)
            v["key"] = mode + "-" + label
            v["name"] = "15M RSI14 Reversal | " + mode + " | " + label
            v["parameters"].update(long_threshold=20, short_threshold=80,
                long_cross="below", short_cross="above",
                fixed_take_profit=None, trailing_activation_points=tp,
                trailing_distance_points=1000, trading_days="all",
                setup_expiry="next threshold crossing",
                execution_model="1m Color", signals_while_open="ignored")
            for t in v["trades"]:
                ctx = t["signal_context"]
                ctx["confirmation_utc"] = ctx.pop("pullback_utc")
                assert (ctx["rsi14"] < 20 if t["side"] == 1 else ctx["rsi14"] > 80)
            variants.append(v)
            print("RESULT", v["key"], json.dumps(v["summary"], allow_nan=False))
    assert len(variants) == 8
    export_bundle(OUT/"backtest.json", family="rsi14-reversal-confirmation-2025",
        symbol="BTCUSD", unit="price points", start_utc=dt(START).isoformat(),
        end_utc=dt(END).isoformat(), execution_timeframe_minutes=1,
        signal_timeframe_minutes=15, costs="0.05% taker each side +18% GST; no Scalper Offer; zero extra slippage; funding/liquidation excluded; 1m Color execution.",
        variants=variants, recorder=rec, data_provenance=dict(
            manifest=str(ROOT/"manifest.json"),
            manifest_sha256=hashlib.sha256((ROOT/"manifest.json").read_bytes()).hexdigest(),
            input_minutes=len(bars[0]), timestamp_label="assumed open UTC",
            selection="Four predefined reversal entry modes x two unchanged exit configurations; no EMA50 trend filter; 2025 in-sample only.",
            month_attribution="UTC entry month; realized trade-close drawdown",
            execution="Next 1m open after confirmed signal; final sample close for accounting; no partial exit."
        ))


if __name__ == "__main__":
    run()
