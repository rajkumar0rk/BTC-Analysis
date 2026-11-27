"""Independent 2025 RSI(14) momentum reversal baseline, no live orders."""
import csv
import gzip
import hashlib
import json
import math
import sys
from datetime import datetime, timezone
from decimal import Decimal as D
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from btc_analysis.contracts import AssetClass, Candle, Instrument, Timeframe
from btc_analysis.indicators import IndicatorBook, spec
from backtest_bundle import export_bundle, IndicatorRecorder

ROOT = Path("data/delta_india/BTCUSD/1m")
START, END = 1735689600, 1767225600
FEE = 0.0005 * 1.18
TF = Timeframe(900)
INSTRUMENT = Instrument("delta_india", "BTCUSD", AssetClass.CRYPTO_PERPETUAL, "USD", "USD", D("0.5"), D("1"), D("0.001"))

def dt(t):
    return datetime.fromtimestamp(t, timezone.utc)

def signal(prev, current):
    if prev is None or current is None:
        return 0
    if prev <= 80 < current:
        return 1
    if prev >= 20 > current:
        return -1
    return 0

def opposite_color(direction, opening, closing):
    return closing < opening if direction == 1 else closing > opening

def candles():
    manifest = json.loads((ROOT / "manifest.json").read_text())
    parts = [p for p in manifest["partitions"] if p["file"].startswith("2025-")]
    assert len(parts) == 12
    expected = START
    for p in parts:
        path = ROOT / p["file"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == p["sha256_gzip"], path
        assert p["missing_minutes"] == 0, path
        with gzip.open(path, "rt") as f:
            for row in csv.DictReader(f):
                t = int(row["time"])
                assert t == expected, (t, expected)
                expected += 60
                o,h,l,c,v = (D(row[k]) for k in ("open","high","low","close","volume"))
                assert all(x.is_finite() for x in (o,h,l,c,v))
                assert 0 < l <= min(o,c) <= max(o,c) <= h and v >= 0
                yield t,o,h,l,c,v
    assert expected == END

def run():
    assert signal(D(80), D(81)) == 1 and signal(D(20), D(19)) == -1
    assert signal(D(81), D(82)) == 0 and signal(D(19), D(18)) == 0
    assert opposite_color(1, D(10), D(9)) and opposite_color(-1, D(9), D(10))
    assert not opposite_color(1, D(10), D(10)) and not opposite_color(-1, D(10), D(10))
    book = IndicatorBook((spec("rsi", TF, period=14),), history_limit=2)
    recorder = IndicatorRecorder(book)
    trades, group = [], []
    pos, pending, prev, setup, exit_pending = None, None, None, None, False
    last = None
    def close_position(t, price, reason):
        nonlocal pos
        side, entry, ep, rsi, trigger, confirm_rsi, confirm_open, confirm_close = pos
        gross = side * (price - ep)
        fee = (ep + price) * FEE
        trades.append(dict(entry_utc=dt(entry).isoformat(), trigger_utc=dt(trigger).isoformat(),
            exit_utc=dt(t).isoformat(), side=side, entry_price=ep, exit_price=price,
            entry_reason="RSI14 crosses above 80, then bearish candle" if side == 1 else "RSI14 crosses below 20, then bullish candle",
            exit_reason=reason, net_points=gross-fee, gross_points=gross, fee_points=fee,
            assumed_slippage_points=0, signal_context={"rsi14":rsi,"confirmation_rsi14":confirm_rsi,"confirmation_utc":dt(entry).isoformat(),"confirmation_open":confirm_open,"confirmation_close":confirm_close},
            indicator_values={"indicator_0":rsi}))
        pos = None
    for t,o,h,l,c,v in candles():
        last = float(c)
        if exit_pending:
            assert pos is not None
            close_position(t, float(o), "Opposite RSI crossing")
            exit_pending = False
        if pending is not None:
            direction, trigger, value, confirm, confirm_rsi, co, cc = pending
            assert t == confirm and confirm >= trigger + 900
            assert pos is None and opposite_color(direction, co, cc)
            pos = (direction, t, float(o), value, trigger, confirm_rsi, co, cc)
            pending = None
        group.append((o,h,l,c,v))
        if len(group) == 15:
            end = t + 60
            candle = Candle(INSTRUMENT, TF, dt(end-900), dt(end), group[0][0],
                max(x[1] for x in group), min(x[2] for x in group), group[-1][3], sum(x[4] for x in group))
            book.update(candle)
            recorder.completed(candle)
            current = book.get("rsi", TF, {"period":14})[-1]
            direction = signal(prev, current)
            if end < END:
                if direction:
                    if pos is not None and pos[0] != direction:
                        exit_pending = True
                    if pos is None or exit_pending:
                        # A contrary crossing supersedes any unfilled setup.
                        # A repeated same-direction crossing does not postpone it.
                        if setup is None or setup[0] != direction:
                            setup = (direction, end, float(current))
                    else:
                        setup = None
                if setup is not None:
                    d, trigger, value = setup
                    if end > trigger and opposite_color(d, candle.open, candle.close):
                        assert pos is None or exit_pending
                        pending = (d, trigger, value, end, float(current), float(candle.open), float(candle.close))
                        setup = None
            prev = current
            group.clear()
    assert not group and last is not None
    if pos:
        close_position(END, last, "End of 2025 evaluation")
    net = math.fsum(t["net_points"] for t in trades)
    wins = sum(t["net_points"] > 0 for t in trades)
    gain = math.fsum(max(0,t["net_points"]) for t in trades)
    loss = -math.fsum(min(0,t["net_points"]) for t in trades)
    equity = peak = dd = 0
    monthly = {f"2025-{m:02d}":0.0 for m in range(1,13)}
    for t in trades:
        equity += t["net_points"]
        peak = max(peak, equity)
        dd = max(dd, peak-equity)
        monthly[t["entry_utc"][:7]] += t["net_points"]
    summary = dict(accounting="realized", open_position=None, trades=len(trades), net=net, wins=wins,
        win_rate=100*wins/len(trades) if trades else 0, profit_factor=gain/loss if loss else None,
        realized_drawdown_points=dd, monthly_entry_attribution=monthly,
        profitable_months=sum(v>0 for v in monthly.values()))
    export_bundle("scratch/rsi14_80_20/backtest.json", family="rsi14-momentum-80-20", symbol="BTCUSD",
        unit="price points", start_utc=dt(START).isoformat(), end_utc=dt(END).isoformat(),
        execution_timeframe_minutes=1, signal_timeframe_minutes=15,
        costs="0.05% taker per side + 18% GST; no Scalper Offer waiver, zero slippage, funding not modeled; unleveraged fixed price-point accounting; no liquidation model.",
        variants=[dict(key="opposite-color-entry", name="15M RSI14 80/20 momentum | wait for opposite candle",
            parameters=dict(rsi_period=14, long_threshold=80, short_threshold=20, exit="opposite crossing", 
                signal="completed 15m", entry_confirmation="first subsequent opposite-color 15m candle; doji ignored; contrary crossing replaces setup", execution="next 1m open", trading_days="all", stop_loss=None, take_profit=None),
            summary=summary, trades=trades)], recorder=recorder,
        data_provenance=dict(manifest=str(ROOT/"manifest.json"), manifest_sha256=hashlib.sha256((ROOT/"manifest.json").read_bytes()).hexdigest(),
            input_minutes=END//60-START//60, timestamp_label="assumed open UTC", warmup="first 15 completed 15m candles in 2025"))
    print(json.dumps(summary, indent=2, allow_nan=False))

if __name__ == "__main__":
    run()
