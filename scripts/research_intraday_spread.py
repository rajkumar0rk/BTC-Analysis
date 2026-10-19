#!/usr/bin/env python3
"""Intraday hedged relative-value research, NOT directional forecasting or real fill simulation."""
from __future__ import annotations
import hashlib
import io
import itertools
import json
import urllib.request
import zipfile
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path("data/delta_india/BTCUSD")
OUT = Path("analysis/institutional_intraday_spread")
MONTHS = pd.period_range("2025-10", "2026-09", freq="M")
QTY = 0.001
FUT_FEE = .0005 * 1.18
SPOT_FEE = .001
TF = (1, 5, 15)
ZS = (2.0, 3.0)
HURDLES = (0.0, .0032)
HOLDS = (15, 60, 120)
SCENARIOS = ("gross_before_costs", "baseline_taker", "stress_slippage_financing")
PERIODS = ("2025_Q4", "2026_H1", "2026_Q3")


def spot_months():
    series, provenance = [], []
    for m in MONTHS:
        month = str(m)
        url = f"https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1m/BTCUSDT-1m-{month}.zip"
        request = urllib.request.Request(url, headers={"User-Agent": "BTC-Analysis-Research/1.0"})
        with urllib.request.urlopen(request, timeout=120) as response:
            raw = response.read()
        digest = hashlib.sha256(raw).hexdigest()
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            files = [n for n in z.namelist() if n.endswith(".csv")]
            if len(files) != 1:
                raise ValueError(f"Expected one official CSV in {url}, got {files}")
            df = pd.read_csv(io.BytesIO(z.read(files[0])), header=None, usecols=[0, 1, 4])
        t = pd.to_numeric(df.iloc[:, 0], errors="raise").astype("int64")
        unit = "us" if t.iloc[0] > 10**14 else "ms"
        idx = pd.DatetimeIndex(pd.to_datetime(t, unit=unit, utc=True))
        first = m.start_time.tz_localize("UTC")
        last = (m + 1).start_time.tz_localize("UTC")
        expected = pd.date_range(first, last, freq="1min", inclusive="left")
        if not idx.is_unique or not idx.is_monotonic_increasing:
            raise ValueError(f"Duplicate or unsorted official Binance timestamps: {month}")
        unexpected = idx.difference(expected)
        if len(unexpected):
            raise ValueError(f"Off-grid Binance timestamps {month}: {unexpected[:5].tolist()}")
        missing = expected.difference(idx)
        op = pd.to_numeric(df.iloc[:, 1], errors="raise").to_numpy(dtype=float)
        cl = pd.to_numeric(df.iloc[:, 2], errors="raise").to_numpy(dtype=float)
        if not np.isfinite(op).all() or not np.isfinite(cl).all() or np.any(op <= 0) or np.any(cl <= 0):
            raise ValueError("Invalid Binance prices: " + month)
        # Do NOT invent candles. Preserve missing minutes as NaN and exclude any
        # signal whose 12h lookback or possible holding interval intersects a gap.
        month_frame = pd.DataFrame({"spot_open": op, "spot_close": cl}, index=idx).reindex(expected)
        series.append(month_frame)
        provenance.append({"month": month, "url": url, "zip_sha256": digest,
                           "source_rows": len(idx), "expected_rows": len(expected),
                           "missing_minutes": len(missing),
                           "missing_examples_utc": [str(t) for t in missing[:5]]})
        print(f"SPOT_MONTH {month}: source={len(idx)} expected={len(expected)} "
              f"missing={len(missing)} examples={missing[:3].tolist()}", flush=True)
    return pd.concat(series), provenance


def delta_minutes(index):
    start, end = index[0], index[-1]
    frames = []
    for file in sorted((ROOT / "1m").glob("20??-??.csv.gz")):
        month = file.stem.split(".")[0]
        if not ("2025-10" <= month <= "2026-09"):
            continue
        df = pd.read_csv(file, compression="gzip", usecols=["time", "open", "close"])
        idx = pd.to_datetime(df["time"].astype("int64"), unit="s", utc=True)
        frames.append(pd.DataFrame({
            "perp_open": pd.to_numeric(df["open"], errors="raise").to_numpy(float),
            "perp_close": pd.to_numeric(df["close"], errors="raise").to_numpy(float)}, index=idx))
    if not frames:
        raise RuntimeError("Genuine Delta India BTCUSD 1m history not found")
    d = pd.concat(frames).sort_index()
    if not d.index.is_unique:
        raise ValueError("Duplicate Delta minute timestamps")
    if not np.isfinite(d.to_numpy()).all() or (d.to_numpy() <= 0).any():
        raise ValueError("Nonpositive or nonfinite observed Delta prices")
    d = d.reindex(index)
    missing = int(d.perp_open.isna().sum())
    print(f"DELTA_MINUTE_COVERAGE observed={len(d)-missing} missing={missing}", flush=True)
    return d


def period(t):
    if t.year == 2025:
        return "2025_Q4"
    if t < pd.Timestamp("2026-07-01", tz="UTC"):
        return "2026_H1"
    return "2026_Q3"


def summarize(g):
    if g.empty:
        return {"n": 0, "mean_net_usd_proxy": None, "mean_net_pct_spot": None,
                "win_pct": None, "profit_factor": None, "max_drawdown_usd_proxy": None,
                "median_hold_min": None, "mean_gross_usd_proxy": None,
                "mean_cost_usd_proxy": None, "mean_spread_capture_pts": None}
    vals = g["net_usd_proxy"].to_numpy(float)
    cum = np.r_[0, np.cumsum(vals)]
    wins = vals[vals > 0].sum()
    losses = -vals[vals < 0].sum()
    return {"n": len(g), "mean_net_usd_proxy": round(float(vals.mean()), 5),
            "mean_net_pct_spot": round(float(g.net_pct_spot.mean()), 5),
            "win_pct": round(float(100 * np.mean(vals > 0)), 2),
            "profit_factor": round(float(wins / losses), 3) if losses > 0 else None,
            "max_drawdown_usd_proxy": round(float((np.maximum.accumulate(cum) - cum).max()), 5),
            "median_hold_min": round(float(g.hold_min.median()), 2),
            "mean_gross_usd_proxy": round(float(g.gross_usd_proxy.mean()), 5),
            "mean_cost_usd_proxy": round(float(g.cost_usd_proxy.mean()), 5),
            "mean_spread_capture_pts": round(float(g.spread_capture_pts.mean()), 3)}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    spot, provenance = spot_months()
    perp = delta_minutes(spot.index)
    both = spot.join(perp)
    idx = both.index
    n = len(idx)
    s_open = both.spot_open.to_numpy(float)
    s_close = both.spot_close.to_numpy(float)
    p_open = both.perp_open.to_numpy(float)
    p_close = both.perp_close.to_numpy(float)
    spread = p_close - s_close
    complete = np.isfinite(s_open) & np.isfinite(s_close) & np.isfinite(p_open) & np.isfinite(p_close)
    incomplete_prefix = np.r_[0, np.cumsum((~complete).astype(np.int64))]
    print(f"PAIRED_MINUTE_COVERAGE total={n} complete={int(complete.sum())} "
          f"missing={int((~complete).sum())}", flush=True)
    # Signal at the END of minute i, baseline uses minutes i-720 through i-1 only.
    spread_series = pd.Series(spread, index=idx)
    mean = spread_series.rolling(720, min_periods=720).mean().shift(1).to_numpy(float)
    sd = spread_series.rolling(720, min_periods=720).std().shift(1).to_numpy(float)
    # UTC settlement calendar is known in advance, so exclude worst-case full holding window.
    settlements = ((idx.hour % 8 == 0) & (idx.minute == 0)).astype(int)
    settlement_prefix = np.r_[0, np.cumsum(settlements)]
    positions = np.arange(n)
    records, audit, summary = [], [], []
    for tf, z, hurdle, max_hold in itertools.product(TF, ZS, HURDLES, HOLDS):
        name = f"tf{tf}m_z{z:g}_hurdle{hurdle:.4f}_max{max_hold}m"
        valid_signal = ((positions % tf) == tf-1) & complete & np.isfinite(mean) & np.isfinite(sd) & (sd > 0)
        excess = spread - mean
        valid_signal &= (excess > z * sd) & (excess >= hurdle * s_close)
        candidates = np.flatnonzero(valid_signal)
        last_exit = -1
        skipped_funding = skipped_overlap = skipped_end = skipped_gaps = 0
        entries = []
        for i in candidates:
            entry = int(i) + 1
            timeout = entry + max_hold
            if timeout >= n:
                skipped_end += 1
                continue
            if entry <= last_exit:
                skipped_overlap += 1
                continue
            if incomplete_prefix[timeout+1] - incomplete_prefix[entry] > 0:
                skipped_gaps += 1
                continue
            if settlement_prefix[timeout+1] - settlement_prefix[entry] > 0:
                skipped_funding += 1
                continue
            target_mean = mean[i]
            # Evaluate each completed minute after entry; exit at the NEXT minute open.
            exit_at = timeout
            reason = "time_limit"
            for j in range(entry, timeout):
                if spread[j] <= target_mean:
                    exit_at = j + 1
                    reason = "spread_reversion"
                    break
            last_exit = exit_at
            gross_pts = (s_open[exit_at] - s_open[entry]) - (p_open[exit_at] - p_open[entry])
            gross = QTY * gross_pts
            fee = QTY * (FUT_FEE * (p_open[entry] + p_open[exit_at]) +
                         SPOT_FEE * (s_open[entry] + s_open[exit_at]))
            duration = exit_at - entry
            financing = QTY * s_open[entry] * .05 * duration / (365 * 24 * 60)
            basis_in = p_open[entry] - s_open[entry]
            basis_out = p_open[exit_at] - s_open[exit_at]
            for scenario in SCENARIOS:
                if scenario == "gross_before_costs":
                    cost = 0.0
                elif scenario == "baseline_taker":
                    cost = fee + 4 * 5 * QTY
                else:
                    cost = fee + 4 * 15 * QTY + financing
                net = gross - cost
                entries.append({
                    "rule": name, "period": period(idx[entry]), "scenario": scenario,
                    "entry_utc": str(idx[entry]), "exit_utc": str(idx[exit_at]),
                    "tf_minutes": tf, "z_threshold": z, "economic_hurdle": hurdle,
                    "max_hold_min": max_hold, "hold_min": duration,
                    "entry_spot": round(float(s_open[entry]), 4),
                    "entry_perp": round(float(p_open[entry]), 4),
                    "entry_basis_pts": round(float(basis_in), 4),
                    "exit_basis_pts": round(float(basis_out), 4),
                    "signal_z": round(float(excess[i] / sd[i]), 4),
                    "reason": reason,
                    "spread_capture_pts": round(float(basis_in - basis_out), 4),
                    "gross_usd_proxy": round(float(gross), 6),
                    "cost_usd_proxy": round(float(cost), 6),
                    "net_usd_proxy": round(float(net), 6),
                    "net_pct_spot": round(float(100 * net / (QTY * s_open[entry])), 6)})
        audit.append({"rule": name, "signal_candidates": len(candidates),
                      "excluded_funding_window": skipped_funding,
                      "excluded_overlapping_position": skipped_overlap,
                      "excluded_missing_paired_minutes": skipped_gaps,
                      "excluded_end_of_history": skipped_end,
                      "completed_trades": len(entries) // len(SCENARIOS)})
        records.extend(entries)
        print(f"RULE {name}: {len(entries)//3} trades, {skipped_funding} funding-window exclusions", flush=True)
        one = pd.DataFrame(entries)
        for scenario in SCENARIOS:
            for p in PERIODS:
                if one.empty:
                    part = pd.DataFrame()
                else:
                    part = one[(one.scenario == scenario) & (one.period == p)].sort_values("exit_utc")
                summary.append({"rule": name, "tf_minutes": tf, "z_threshold": z,
                                "economic_hurdle": hurdle, "max_hold_min": max_hold,
                                "scenario": scenario, "period": p, **summarize(part)})
    ledger = pd.DataFrame(records)
    results = pd.DataFrame(summary)
    audit_df = pd.DataFrame(audit)
    ledger.to_csv(OUT / "trade_ledger.csv", index=False)
    results.to_csv(OUT / "all_configurations.csv", index=False)
    audit_df.to_csv(OUT / "signal_audit.csv", index=False)
    quality = {"spot_data": provenance, "rows": n, "start_utc": str(idx[0]),
               "end_utc": str(idx[-1]), "strategies": len(audit_df),
               "scenario_rows": len(ledger), "config_period_rows": len(results),
               "paired_missing_minutes": int((~complete).sum()),
               "no_interpolation": "True: missing source candles remain NaN; signals and complete possible hold windows crossing gaps are excluded.",
               "fee_assumptions": {"delta_taker_each_side_with_gst": FUT_FEE,
                                   "spot_taker_each_side_assumed": SPOT_FEE,
                                   "slippage_points_each_leg_each_side": 5,
                                   "stress_slippage_points_each_leg_each_side": 15,
                                   "stress_financing_annual": .05},
               "funding": "All candidate trades touching a potential scheduled settlement are excluded",
               "non_executable": "Trade-price OHLC opens are not actual bid/ask quotes; historical L2, queue, liquidity, cross-venue capital constraints unavailable.",
               "venue_risk": "BTCUSDT on Binance and BTCUSD on Delta India differ in quote asset, venue and collateral; true executable arbitrage not established.",
               "research_warning": "Many correlated configurations, same historical archive, selection bias. Never aggregate variant returns as independent strategies."}
    (OUT / "quality.json").write_text(json.dumps(quality, indent=2) + "\n")
    base = results[results.scenario == "baseline_taker"]
    best = base[(base.period == "2026_H1") & (base.n >= 10)].sort_values("mean_net_pct_spot", ascending=False)
    all_neg = int((base[base.n > 0].mean_net_usd_proxy < 0).sum())
    lines = [
        "# Intraday institutional relative-value study — real 1-minute archives",
        "",
        "**Research only. No prediction of BTC's absolute direction, no validated executable edge.**",
        "Buy Binance BTCUSDT spot and sell Delta India BTCUSD perpetual when the premium is > 2/3 trailing-standard deviations; trade only after completed 1m/5m/15m signals.",
        "All entry and exit fills are next-minute trade-price OPEN proxies, **not historical bid/ask fills**. Funding events are excluded, not estimated.",
        "",
        "## Data and audit",
        f"- Source minute rows: {n}; 36 preregistered configurations; {len(ledger)} scenario-trade records; {len(results)} configuration/period/scenario summaries.",
        f"- Baseline rows with negative mean among nonempty: {all_neg} of {int((base.n > 0).sum())}.",
        "- Binance official source ZIP SHA256 per month and data-quality limitations: quality.json.",
        "- No held-out untouched dataset. Comparing many configurations inflates false-positive risk.",
        "",
        "## Highest modeled baseline net mean on 2026 H1 (not selected as a tradeable winner)",
        best.head(15).to_markdown(index=False) if not best.empty else "No eligible variants with >=10 H1 trades.",
        "",
        "## Every scenario and period",
        results.to_markdown(index=False),
        "",
        "## Signal and exclusion audit",
        audit_df.to_markdown(index=False),
        "",
        "## Economic interpretation",
        "This is a two-leg *spread* trade; direction of BTC is hedged in the model. Gross spread changes are not profits until two-leg fees, slippage, financing, and venue constraints are accounted for.",
        "Binance BTCUSDT and Delta BTCUSD are different quote/collateral assets. A positive proxy return cannot be called risk-free arbitrage.",
        "Missing synchronized executable bid/ask and queue data prevents credible maker-fill and liquidity-provision backtests.",
        "All variants are exploratory; genuinely forward quote-based replication and operational hedge feasibility are required."
    ]
    (OUT / "RESEARCH_REPORT.md").write_text("\n".join(lines) + "\n")
    print("INTRADAY_SPREAD_COMPLETED", json.dumps({k:v for k,v in quality.items() if k!="spot_data"}), flush=True)
    print("TOP_2026_H1_BASELINE\n", best.head(12).to_string(index=False), flush=True)


if __name__ == "__main__":
    main()
