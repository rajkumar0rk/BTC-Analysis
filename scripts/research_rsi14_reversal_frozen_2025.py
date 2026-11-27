"""Reverse only frozen 2025 RSI threshold directions; no optimization."""
import hashlib
import json
import math
from pathlib import Path

import numpy as np

from research_rsi14_runner_refinements_2025 import (
    BASES, ROOT, START, END, checks, load, entry_list, replay, dt, export_bundle,
)

OUT = Path("scratch/rsi14_reversal_frozen")
EXPECTED = (38547.273445, 20298.546545)


def run():
    checks()
    bars, original, snapshots, extra, rec = load()
    # Both threshold crossings occur at identical times. Invert direction
    # before pullback, breakout and EMA checks, not after entry selection.
    reversed_signals = [(i, -d, r, hi, lo) for i, d, r, hi, lo in original]
    assert all((r < 20 if d == 1 else r > 80)
               for _, d, r, _, _ in reversed_signals)
    n = len(bars[0]) // 15 + 1
    atr, st, line = (np.full(n, np.nan) for _ in range(3))
    for k, v in snapshots.items():
        a, s, l = v[0], extra[k][1], extra[k][2]
        for arr, value in ((atr, a), (st, s), (line, l)):
            if value is not None:
                arr[k // 15] = value
    ind = (atr, st, line)
    variants = []
    for base, expected, role in zip(BASES, EXPECTED, ("high-profit", "low-drawdown")):
        entry, trend, sl, tp, be = base
        def run_case(signals):
            entries = entry_list(bars, signals, snapshots, extra, entry, trend, 0)
            return replay(bars, entries, ind, base, False, "fixed-1r",
                          False, False, False, 0)
        reference = run_case(original)
        assert math.isclose(reference["summary"]["net"], expected, abs_tol=1e-5), (
            role, reference["summary"]["net"], expected)
        result = run_case(reversed_signals)
        result["key"] = "reversal-" + role
        result["name"] = "15M RSI14 Reversal | " + (
            "High Profit configuration" if role == "high-profit"
            else "Low Drawdown configuration")
        result["parameters"].update(
            long_threshold=20, short_threshold=80,
            long_cross="below", short_cross="above",
            trailing_activation_points=tp, trailing_distance_points=sl,
            fixed_take_profit=None, trading_days="all",
            setup_expiry="next RSI threshold crossing",
            execution_model="1m Color",
            original_reference_net_points=reference["summary"]["net"],
        )
        for trade in result["trades"]:
            assert (trade["signal_context"]["rsi14"] < 20 if trade["side"] == 1
                    else trade["signal_context"]["rsi14"] > 80)
        variants.append(result)
        print("REFERENCE", role, json.dumps(reference["summary"], allow_nan=False))
        print("REVERSAL", role, json.dumps(result["summary"], allow_nan=False))
    OUT.mkdir(parents=True, exist_ok=True)
    export_bundle(
        OUT / "backtest.json", family="rsi14-reversal-frozen-2025",
        symbol="BTCUSD", unit="price points",
        start_utc=dt(START).isoformat(), end_utc=dt(END).isoformat(),
        execution_timeframe_minutes=1, signal_timeframe_minutes=15,
        costs="0.05% taker per side +18% GST; no Scalper Offer; zero extra slippage; funding and liquidation excluded. Color execution; stops gap at open.",
        variants=variants, recorder=rec,
        data_provenance=dict(
            manifest=str(ROOT / "manifest.json"),
            manifest_sha256=hashlib.sha256((ROOT / "manifest.json").read_bytes()).hexdigest(),
            input_minutes=len(bars[0]), timestamp_label="assumed open UTC",
            selection="Two frozen configurations; reverse RSI direction only; no optimization or 2026 data.",
            execution="Original runner unchanged; no partial exit, no fixed TP, one open position; end-of-sample close for accounting.",
            month_attribution="UTC entry month; realized trade-close drawdown",
        ),
    )


if __name__ == "__main__":
    run()
