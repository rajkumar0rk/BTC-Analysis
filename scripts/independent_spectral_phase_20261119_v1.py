#!/usr/bin/env python3
"""Independent BTCUSD+ETHUSD 30m Fourier phase hypothesis on native Delta India 1m.

The price-cycle forecast is a research hypothesis, not proof of predictability.
See analysis/independent_spectral_phase_20261119_v1/NOVELTY_CHECK.md.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from numba import njit

ROOT = Path("data/delta_india")
OUT = Path("analysis/independent_spectral_phase_20261119_v1")
MONTHS = pd.period_range("2025-01", "2026-10", freq="M").astype(str).tolist()
MONTH_CODES = np.array([int(m.replace("-", "")) for m in MONTHS], dtype=np.int32)
FEE = .0005 * 1.18
INITIAL_EQUITY = 1000.
RISK = .01
LEVERAGE_CAP = 3.
HOLD_MINUTES = 720
WINDOW = 96
CONFIGS = {
    "A_follow": (.16, .20, +1),
    "A_fade": (.16, .20, -1),
    "B_follow": (.22, .35, +1),
    "B_fade": (.22, .35, -1),
}

def load_original(symbol):
    folder = ROOT / symbol / "1m"
    manifest = json.loads((folder / "manifest.json").read_text())
    partition = {p["file"]: p for p in manifest["partitions"]}
    chunks = []
    checksum_report = []
    for m in MONTHS:
        name = m + ".csv.gz"
        item = partition.get(name)
        if item is None or item["missing_minutes"] or item["observed_candles"] != item["expected_minutes"]:
            raise ValueError(f"Original {symbol}/{name} has absent minutes in manifest")
        path = folder / name
        sha = hashlib.sha256(path.read_bytes()).hexdigest()
        if sha != item["sha256_gzip"]:
            raise ValueError(f"SHA256 mismatch for {symbol}/{name}")
        frame = pd.read_csv(path, compression="gzip",
                            usecols=["time", "open", "high", "low", "close", "volume"])
        if len(frame) != item["observed_candles"]:
            raise ValueError(f"Row count mismatch {symbol}/{name}")
        checksum_report.append({"symbol": symbol, "month_utc": m, "sha256_gzip": sha,
                                "candles": int(len(frame)), "missing_minutes": 0})
        chunks.append(frame)
    f = pd.concat(chunks, ignore_index=True)
    timestamps = f["time"].to_numpy(np.int64)
    if not np.all(np.diff(timestamps) == 60):
        raise ValueError(f"{symbol} non-continuous original minute timestamps")
    o = f["open"].to_numpy(float)
    h = f["high"].to_numpy(float)
    l = f["low"].to_numpy(float)
    c = f["close"].to_numpy(float)
    if (not np.isfinite(f[["open", "high", "low", "close", "volume"]].to_numpy(float)).all()
        or np.any(l <= 0) or np.any(l > np.minimum(o, c))
        or np.any(h < np.maximum(o, c)) or np.any(h < l)):
        raise ValueError(f"{symbol} invalid OHLCV")
    f.index = pd.to_datetime(timestamps, unit="s", utc=True)
    return f, checksum_report

def events(f):
    """Completed-bar FFT only. The next minute's open is the earliest possible fill."""
    fields = {"open": "first", "high": "max", "low": "min", "close": "last"}
    b = f[["open", "high", "low", "close"]].resample(
        "30min", label="right", closed="left").agg(fields)
    counts = f.close.resample("30min", label="right", closed="left").count().to_numpy()
    tr = pd.concat([b.high - b.low,
                    (b.high - b.close.shift(1)).abs(),
                    (b.low - b.close.shift(1)).abs()], axis=1).max(axis=1)
    atr = tr.rolling(14, min_periods=14).mean().to_numpy(float)
    rets = np.log(b.close).diff().to_numpy(float)
    rows = []
    for i in range(WINDOW, len(b)):
        if counts[i] != 30 or np.any(counts[i-WINDOW:i] != 30):
            continue
        v = rets[i-WINDOW+1:i+1]
        if not np.isfinite(v).all() or not np.isfinite(atr[i]) or atr[i] <= 0:
            continue
        centered = v - v.mean()
        rms = np.sqrt(np.mean(v*v))
        if rms <= 1.e-12:
            continue
        spectrum = np.fft.rfft(centered)
        power = np.abs(spectrum[3:17]) ** 2
        fullpower = float(power.sum())
        if fullpower <= 1.e-20:
            continue
        top = int(np.argmax(power)) + 3
        share = float(power[top-3] / fullpower)
        # Next sample's DFT phase: exp(2*pi*i*k*96/96) = 1.
        forecast = float(2. * np.real(spectrum[top]) / WINDOW)
        strength = abs(forecast) / rms
        if forecast == 0:
            continue
        rows.append((b.index[i], int(np.sign(forecast)), share, strength, atr[i], top))
    if not rows:
        raise ValueError("No completed-bar spectral signals available")
    evt = pd.DataFrame(rows, columns=[
        "event_utc", "direction", "peak_share", "forecast_to_rms", "atr", "fft_bin"])
    at = f.index.get_indexer(pd.DatetimeIndex(evt.event_utc))
    ist = f.index.tz_convert("Asia/Kolkata")
    codes = np.asarray(ist.year*100 + ist.month, dtype=np.int32)
    valid = (at >= 0) & (at < len(f))
    valid &= np.array([(codes[int(x)] <= 202610) if x >= 0 else False for x in at],
                      dtype=bool)
    evt = evt.loc[valid].reset_index(drop=True)
    evt["entry_idx"] = at[valid]
    return evt

@njit(cache=True)
def simulate(o, h, l, c, entry_idxs, side, distance, share, signal_strength,
             slip_abs, slip_frac):
    """Exclusive positions, gap-aware stop-first execution on original 1m."""
    ledger = np.empty((len(entry_idxs), 15), np.float64)
    n = 0
    busy = -1
    equity = INITIAL_EQUITY
    for z in range(len(entry_idxs)):
        k = int(entry_idxs[z])
        if k <= busy or k >= len(c) or equity <= 0:
            continue
        sd = int(side[z])
        raw_stop = float(distance[z])
        if sd == 0 or not np.isfinite(raw_stop) or raw_stop <= 0:
            continue
        entry = o[k] + sd*(slip_abs + slip_frac*o[k])
        if entry <= 0:
            continue
        qty = min(equity*RISK/raw_stop, equity*LEVERAGE_CAP/entry)
        if qty <= 0:
            continue
        stop = entry - sd*raw_stop
        target = entry + sd*2.0*raw_stop
        finish = min(k+HOLD_MINUTES-1, len(c)-1)
        end = finish
        exit_px = c[finish]
        reason = 3
        for j in range(k, finish+1):
            if (sd == 1 and l[j] <= stop) or (sd == -1 and h[j] >= stop):
                exit_px = min(stop, o[j]) if sd == 1 else max(stop, o[j])
                end = j
                reason = 1
                break
            if (sd == 1 and h[j] >= target) or (sd == -1 and l[j] <= target):
                exit_px = target
                end = j
                reason = 2
                break
        exit_fill = exit_px - sd*(slip_abs + slip_frac*exit_px)
        pnl = qty*(sd*(exit_fill-entry) - FEE*(entry+exit_fill))
        before = equity
        equity = equity + pnl
        ledger[n,0] = k
        ledger[n,1] = end
        ledger[n,2] = sd
        ledger[n,3] = entry
        ledger[n,4] = exit_fill
        ledger[n,5] = qty
        ledger[n,6] = pnl
        ledger[n,7] = before
        ledger[n,8] = equity
        ledger[n,9] = stop
        ledger[n,10] = target
        ledger[n,11] = reason
        ledger[n,12] = share[z]
        ledger[n,13] = signal_strength[z]
        ledger[n,14] = raw_stop
        n += 1
        busy = end
    return ledger[:n]

LEDGER_FIELDS = ["entry_idx", "exit_idx", "side", "entry_price", "exit_price",
                 "quantity", "net_pnl_usd", "equity_before_usd",
                 "equity_after_usd", "stop_price", "take_profit_price",
                 "exit_reason_code", "spectral_power_share",
                 "forecast_to_rms", "stop_distance"]

def monthly_audit(symbol, model, f, ledger, slip_abs, slip_frac):
    """NAV marks open positions at IST month-end; PF counts exit-month net trades."""
    idx = f.index.tz_convert("Asia/Kolkata")
    codes = np.asarray(idx.year*100 + idx.month, dtype=np.int32)
    end_indices = np.array([np.flatnonzero(codes == mc)[-1] for mc in MONTH_CODES])
    eix = ledger[:,1].astype(np.int64) if len(ledger) else np.empty(0,np.int64)
    six = ledger[:,0].astype(np.int64) if len(ledger) else np.empty(0,np.int64)
    out = []
    nav_start = INITIAL_EQUITY
    pnl = ledger[:,6] if len(ledger) else np.empty(0)
    close = f.close.to_numpy(float)
    for name, mc, last in zip(MONTHS, MONTH_CODES, end_indices):
        closed = (eix <= last)
        realized = INITIAL_EQUITY + float(pnl[closed].sum())
        active = ledger[(six <= last) & (eix > last)]
        mtm = 0.
        for row in active:
            sd = row[2]
            mark = close[last]
            exit_fill = mark - sd*(slip_abs + slip_frac*mark)
            mtm += row[5]*(sd*(exit_fill-row[3]) - FEE*(row[3]+exit_fill))
        nav_end = realized + mtm
        monthpnl = pnl[codes[eix] == mc] if len(ledger) else np.empty(0)
        gp = float(monthpnl[monthpnl > 0].sum())
        gl = float(-monthpnl[monthpnl < 0].sum())
        pf = gp/gl if gl > 0 else (float("inf") if gp > 0 else np.nan)
        ret = 100.*(nav_end/nav_start-1.) if nav_start > 0 else -100.
        # Drawdown sampled at closed-trade equity and month boundary marks,
        # not full intratrade/high-frequency MDD.
        mclosed = ledger[codes[eix] == mc] if len(ledger) else np.empty((0,15))
        equity_path = np.r_[nav_start, mclosed[:,8], nav_end]
        high = np.maximum.accumulate(equity_path)
        month_dd = float(100.*np.min(equity_path/high-1.)) if (high > 0).all() else np.nan
        out.append(dict(market=symbol, model=model, month=name,
                        profit_factor=pf, net_return_pct=ret,
                        net_exit_pnl_usd=float(monthpnl.sum()),
                        nav_change_usd=float(nav_end-nav_start),
                        trades=int(len(monthpnl)),
                        wins=int((monthpnl>0).sum()),
                        losses=int((monthpnl<0).sum()),
                        month_drawdown_sampled_pct=month_dd,
                        nav_start_usd=float(nav_start),
                        nav_end_usd=float(nav_end),
                        open_positions_at_month_end=int(len(active))))
        nav_start = nav_end
    return pd.DataFrame(out)

def summarized(symbol, model, ledger, monthly, f):
    ret = monthly.net_return_pct.to_numpy(float)
    pf = monthly.profit_factor.to_numpy(float)
    strong5 = int(((pf>=1.5)&(ret>=5)).sum())
    strong10 = int(((pf>=1.5)&(ret>=10)).sum())
    nav = np.r_[INITIAL_EQUITY, monthly.nav_end_usd.to_numpy(float)]
    ledgerpath = ledger[:,8] if len(ledger) else np.empty(0)
    sampled = np.r_[nav, ledgerpath]
    sampleddd = float(100.*np.min(sampled/np.maximum.accumulate(sampled)-1.))
    idx = f.index.tz_convert("Asia/Kolkata")
    codes = np.asarray(idx.year*100 + idx.month, dtype=np.int32)
    in_scope = ledger[codes[ledger[:,1].astype(np.int64)]<=202610] if len(ledger) else np.empty((0,15))
    gains = float(in_scope[in_scope[:,6]>0,6].sum()) if len(in_scope) else 0.
    losses = float(-in_scope[in_scope[:,6]<0,6].sum()) if len(in_scope) else 0.
    full_pf = gains/losses if losses>0 else (float("inf") if gains>0 else np.nan)
    year2025 = 100.*(np.prod(1.+ret[:12]/100.)-1.)
    ytd2026 = 100.*(np.prod(1.+ret[12:]/100.)-1.)
    return dict(market=symbol, model=model, total_net_pf=full_pf,
                months_both_pf1p5_net10=strong10, months_both_pf1p5_net5=strong5,
                positive_months=int((ret>0).sum()),
                negative_months=int((ret<0).sum()),
                zero_months=int((ret==0).sum()),
                year2025_full_net_pct=year2025,
                year2025_above500=bool(year2025>500),
                year2026_jan_oct_net_pct=ytd2026,
                year2026_jan_oct_above500=bool(ytd2026>500),
                net_return_22m_pct=100.*(nav[-1]/INITIAL_EQUITY-1.),
                max_sampled_equity_drawdown_pct=sampleddd,
                trades=int(len(in_scope)),
                wins=int((in_scope[:,6]>0).sum()) if len(in_scope) else 0,
                losses=int((in_scope[:,6]<0).sum()) if len(in_scope) else 0)

def trade_dataframe(symbol, model, f, ledger):
    df = pd.DataFrame(ledger, columns=LEDGER_FIELDS)
    if df.empty:
        df["entry_utc"] = pd.Series(dtype=str)
        df["exit_utc"] = pd.Series(dtype=str)
    else:
        df["entry_utc"] = f.index[df.entry_idx.to_numpy(np.int64)].astype(str)
        df["exit_utc"] = f.index[df.exit_idx.to_numpy(np.int64)].astype(str)
    df.insert(0,"model",model)
    df.insert(0,"market",symbol)
    return df

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    ledgers, monthly, summaries, hashes, evt_cache, history = [], [], [], [], {}, {}
    for symbol in ("BTCUSD", "ETHUSD"):
        f, checks = load_original(symbol)
        hashes += checks
        history[symbol] = f
        evt_cache[symbol] = events(f)
        print("SOURCE_VERIFIED", symbol, len(f), "spectral_events", len(evt_cache[symbol]), flush=True)
    for symbol, f in history.items():
        ev = evt_cache[symbol]
        for model, (min_share, min_strength, follow) in CONFIGS.items():
            sub = ev[(ev.peak_share >= min_share)&(ev.forecast_to_rms >= min_strength)]
            slip_abs = 5. if symbol=="BTCUSD" else 0.
            slip_frac = 0. if symbol=="BTCUSD" else .0002
            side = sub.direction.to_numpy(np.int32)*follow
            ledger = simulate(f.open.to_numpy(float), f.high.to_numpy(float),
                              f.low.to_numpy(float), f.close.to_numpy(float),
                              sub.entry_idx.to_numpy(np.int64), side,
                              sub.atr.to_numpy(float)*1.5,
                              sub.peak_share.to_numpy(float),
                              sub.forecast_to_rms.to_numpy(float),
                              slip_abs, slip_frac)
            m = monthly_audit(symbol, model, f, ledger, slip_abs, slip_frac)
            row = summarized(symbol, model, ledger, m, f)
            summaries.append(row)
            monthly.append(m)
            ledgers.append(trade_dataframe(symbol, model, f, ledger))
            print("CANDIDATE", symbol, model, "trades", row["trades"],
                  "strong5", row["months_both_pf1p5_net5"],
                  "strong10", row["months_both_pf1p5_net10"],
                  "2025return", row["year2025_full_net_pct"], flush=True)
    allmonths = pd.concat(monthly, ignore_index=True)
    allsummary = pd.DataFrame(summaries)
    allmonths.to_csv(OUT/"all_configuration_monthly.csv", index=False)
    allsummary.to_csv(OUT/"all_configuration_summary.csv", index=False)
    pd.concat(ledgers, ignore_index=True).to_csv(OUT/"all_configuration_trade_ledger.csv", index=False)
    pd.DataFrame(hashes).to_csv(OUT/"source_partition_sha256.csv", index=False)

    # Select ONE identical configuration for both coins using 2025 ONLY.
    ranking=[]
    for model in CONFIGS:
        months25 = allmonths[(allmonths.model==model)&(allmonths.month<="2025-12")]
        strong=int(((months25.profit_factor>=1.5)&(months25.net_return_pct>=5)).sum())
        pos=int((months25.net_return_pct>0).sum())
        capped=float(months25.net_return_pct.clip(-20,20).sum())
        ranking.append(dict(model=model, train_2025_strong5=strong,
                            train_2025_positive=pos, train_2025_capped_month_sum=capped))
    rank=pd.DataFrame(ranking).sort_values(
        ["train_2025_strong5","train_2025_positive","train_2025_capped_month_sum"],
        ascending=False, kind="stable")
    rank.to_csv(OUT/"2025_joint_selection.csv", index=False)
    chosen=str(rank.iloc[0].model)
    paired=allmonths[allmonths.model==chosen].pivot(index="month",columns="market")
    paired.columns=[f"{market}_{field}" for field,market in paired.columns]
    paired.reset_index().to_csv(OUT/"selected_paired_monthly_22.csv",index=False)
    selected=allsummary[allsummary.model==chosen].copy()
    selected.to_csv(OUT/"selected_summary.csv",index=False)
    pd.concat([df for df in ledgers if df.model.iloc[0]==chosen] if all(len(df)>0 for df in ledgers) else [
        df[df.model==chosen] for df in ledgers], ignore_index=True).to_csv(
            OUT/"selected_trade_ledger.csv",index=False)

    # Conservative ETH sensitivity for the 2025-selected configuration, not re-selection.
    f=history["ETHUSD"]
    ev=evt_cache["ETHUSD"]
    ms, strength, follow=CONFIGS[chosen]
    sub=ev[(ev.peak_share>=ms)&(ev.forecast_to_rms>=strength)]
    stressed=simulate(f.open.to_numpy(float), f.high.to_numpy(float),
                      f.low.to_numpy(float), f.close.to_numpy(float),
                      sub.entry_idx.to_numpy(np.int64),
                      sub.direction.to_numpy(np.int32)*follow,
                      sub.atr.to_numpy(float)*1.5,
                      sub.peak_share.to_numpy(float),
                      sub.forecast_to_rms.to_numpy(float),
                      0., .0004)
    stressedm=monthly_audit("ETHUSD","eth_slip_0p04pct",f,stressed,0.,.0004)
    stressedm.to_csv(OUT/"eth_slippage_sensitivity_monthly.csv",index=False)
    stressedsummary=summarized("ETHUSD","eth_slip_0p04pct",stressed,stressedm,f)
    (OUT/"eth_slippage_sensitivity_summary.json").write_text(
        json.dumps(stressedsummary,indent=2,allow_nan=True)+"\n")

    quality=dict(
        source="Original Delta India BTCUSD ETHUSD 1m original manifest hash verified per partition",
        source_sha256_file="source_partition_sha256.csv",
        months=22, calendar="IST Jan2025 to Oct2026",
        missing_2025_Jan_IST_first_hours=5.5,
        original_2026_Oct31_complete_both=True,
        November_2026_excluded=True,
        native_candles_per_market={sym:len(f) for sym,f in history.items()},
        timeframes="30m completed spectral signals, next original 1m open and 1m stop-first replay",
        selection="one identical config for BTC ETH selected using 2025 both-coin monthly scores; 2026 retrospective check only",
        initial_equity_usd_per_market=INITIAL_EQUITY,
        risk_per_stop_equity_pct=100*RISK, max_leverage=LEVERAGE_CAP,
        standard_taker_fee_each_side=.0005, fee_GST=.18,
        BTC_adverse_slippage_usd_points_each_side=5.,
        ETH_adverse_slippage_fraction_each_side=.0002,
        ETH_stress_slippage_fraction_each_side=.0004,
        months_NAV="Month end mark-to-market using exit fee and slip estimate; positions persist",
        months_PF="winning closed net-USD trade sums / abs(losing closed net-USD trade sums) by IST exit month",
        end_scope_note="Open position at final October IST boundary marked in NAV, not forced flat; any November exit excluded from reported 22-month PF",
        sampled_drawdown_not_tick_path=True,
        costs_not_verified=["settled funding","bid/ask spread","market impact",
                            "margin/liquidation","lot-size constraints","actual execution latency"],
        historical_2026_not_pristine_OOS=True,
        previously_tested_comparators=["hourly autocorr","variance ratio","bipower variation",
                                       "time-day volume","breakout/squeeze","return dispersion"])
    (OUT/"quality.json").write_text(json.dumps(quality,indent=2)+"\n")
    selected_months=allmonths[allmonths.model==chosen].copy()
    selection_fmt=selected_months.pivot(index="month",columns="market",
                       values=["profit_factor","net_return_pct","trades","wins","losses",
                               "net_exit_pnl_usd","month_drawdown_sampled_pct"])
    selection_fmt.columns=[f"{market}_{field}" for field,market in selection_fmt.columns]
    report=[
        "# BTCUSD / ETHUSD rolling spectral phase — independent historical experiment",
        "",
        "**This does not establish a tradable cycle.** Predeclared Fourier peak-power/phase extrapolation on 96 completed 30m returns, 4 signal-strength/direction configurations.",
        "One shared configuration chosen using 2025 **only**; 2026 not used for tuning. Full 2025/2026 research exposure is disclosed.",
        "",
        "## 2025-only shared selection ranking","",rank.to_markdown(index=False),"",
        f"## Selected configuration: {chosen} (both native markets)","",
        "## Each IST month, monthly PF SIDE BY SIDE with monthly NET ACCOUNT return","",
        selection_fmt.to_markdown(),"",
        "## Paired summary including exact 2025 FULL YEAR and 2026 Jan-Oct YTD returns","",
        selected.to_markdown(index=False),"",
        "## All candidate summaries (including rejected variants)","",
        allsummary.to_markdown(index=False),"",
        "## Stress ETH slippage 0.04% per side","",
        json.dumps(stressedsummary,indent=2,allow_nan=True),"",
        "## Quality and missing execution costs","",
        json.dumps(quality,indent=2),"",
        "Exit-month PF sums only closed trade net PnL, including modeled entry/exit taker fees, GST and slippage. ",
        "Account monthly NAV return uses equity plus estimated liquidation net value of any carried open position. ",
        "This distinction means exit-month net PnL need not equal NAV change. ",
        "Drawdowns are based on closed trade equity plus month-end marks, not full intraminute equity lows. ",
        "Historical backtests can overstate live performance; no orders were placed."
    ]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")
    print("SPECTRAL_PHASE_AUDIT_COMPLETE", chosen, selected.to_json(orient="records"), flush=True)

if __name__=="__main__":
    main()
