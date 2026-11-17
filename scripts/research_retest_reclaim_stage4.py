#!/usr/bin/env python3
"""Stage 4: event-conditioned retest/reclaim entries after BTC hourly expansion.

Decision-time discipline:
- Hourly event uses completed current/prior hours only.
- Retest and reclaim must occur in DIFFERENT fully completed 5m blocks.
- Market entry uses the NEXT minute open after the reclaim 5m close.
- Stops use only price history already observed at entry; stop wins ambiguity.
- All history, including July-Oct 2026, is already research-exposed.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd

from research_behavioral_discovery import features, SLIP
from research_directional_acceptance import signals

OUT = Path("analysis/institutional_discovery_stage4")
STANDARD_SIDE_FEE = 0.0005 * 1.18
MAX_HOLD_BARS = {"immediate_all": 60, "immediate_on_retest": 60,
                 "retest_fixed": 60, "retest_structure": 120}
STYLES = ("immediate_all", "immediate_on_retest", "retest_fixed", "retest_structure")
RULES = ("expansion_follow", "accepted_12h_breakout", "rejected_12h_sweep")
SEED = 20261117

def period(t):
    if t < pd.Timestamp("2026-01-01", tz="UTC"): return "2025_train"
    if t < pd.Timestamp("2026-07-01", tz="UTC"): return "2026_H1_validation"
    return "2026_H2_seen_recheck"

def replay(op, hi, lo, cl, start, side, sl, tp, horizon):
    """OHLC replay with gap-aware stop exits, conservative stop-first ambiguity."""
    mid = float(op[start])
    fill_in = mid + side * SLIP
    finish = min(start + horizon, len(op))
    for j in range(start, finish):
        stop_hit = lo[j] <= sl if side == 1 else hi[j] >= sl
        take_hit = hi[j] >= tp if side == 1 else lo[j] <= tp
        if stop_hit:
            # A stop gapping beyond its level is filled at the worse open.
            exit_mid = min(float(op[j]), sl) if side == 1 else max(float(op[j]), sl)
            reason = "stop"
            break
        if take_hit:
            # Never credit a more favorable open on target fills.
            exit_mid = tp
            reason = "target"
            break
    else:
        j = finish - 1
        exit_mid = float(cl[j])
        reason = "timeout"
    fill_out = exit_mid - side * SLIP
    gross = side * (exit_mid - mid)
    # NOTE: price-based points per 1 BTC-equivalent, NOT dollar account P&L.
    fee_entry = STANDARD_SIDE_FEE * fill_in
    fee_exit = STANDARD_SIDE_FEE * fill_out
    hold_mins = j - start + 1
    gross_net_slip = side * (fill_out - fill_in)
    mfe = max(0.0, (float(hi[start:j+1].max()) - mid) if side == 1
              else (mid - float(lo[start:j+1].min())))
    mae = max(0.0, (mid - float(lo[start:j+1].min())) if side == 1
              else (float(hi[start:j+1].max()) - mid))
    return dict(exit_j=j, reason=reason, entry_mid=mid, exit_mid=exit_mid,
                gross_pts=gross, net_standard=gross_net_slip-fee_entry-fee_exit,
                # Counterfactual fee schedule: waived CLOSE only for <=30m.
                net_scalper_sensitivity=gross_net_slip-fee_entry-(0.0 if hold_mins<=30 else fee_exit),
                duration_min=hold_mins, mfe_pts=mfe, mae_pts=mae,
                cost_standard=gross-(gross_net_slip-fee_entry-fee_exit))

def retest_reclaim(z, side, k, op, hi, lo, cl):
    """Return first eligible entry on a completed 5m reclaim after an earlier retest."""
    ref = float(z.close)
    threshold = ref - side * (0.25 * float(z.typical))
    touched_in_prior_block = False
    # Scan 6 fully completed five-minute blocks, allowing an entry by minute 30.
    for b in range(0, 30, 5):
        begin, end = k + b, k + b + 5
        observed_touch = (float(lo[begin:end].min()) <= threshold if side == 1
                          else float(hi[begin:end].max()) >= threshold)
        # Confirmation strictly follows AN EARLIER completed 5m block.
        confirmed = (side * (float(cl[end-1])-ref) > 0 and
                     side * (float(cl[end-1])-float(op[begin])) > 0)
        if touched_in_prior_block and confirmed:
            entry = end
            swing = (float(lo[k:entry].min()) - 10 if side == 1
                     else float(hi[k:entry].max()) + 10)
            risk = side * (float(op[entry]) - swing)
            return entry, swing, risk
        touched_in_prior_block |= observed_touch
    return None

def summarize(tr):
    rows = []
    for key, g in tr.groupby(["rule", "style", "fee_mode", "period"], sort=True):
        g = g.sort_values("entry_utc")
        v = g.net_pts.to_numpy(float)
        eq = np.r_[0.0, np.cumsum(v)]
        losses = -v[v < 0].sum()
        gains = v[v > 0].sum()
        d = g.groupby("ny_date").net_pts.agg(["sum", "count"]).to_numpy(float)
        lo_ci = hi_ci = np.nan
        if len(g) >= 20 and len(d) >= 12:
            rng = np.random.default_rng(SEED)
            index = rng.integers(0, len(d), size=(350, len(d)))
            sampled = d[index].sum(axis=1)
            boot = sampled[:, 0] / sampled[:, 1]
            lo_ci, hi_ci = np.quantile(boot, [0.025, 0.975])
        rows.append(dict(zip(["rule", "style", "fee_mode", "period"], key),
            trades=len(g), days=g.ny_date.nunique(),
            mean_net_pts=round(float(v.mean()), 3),
            median_net_pts=round(float(np.median(v)), 3),
            win_pct=round(float((v > 0).mean()*100), 2),
            profit_factor=round(float(gains/losses), 3) if losses > 0 else np.nan,
            max_drawdown_pts=round(float(np.max(np.maximum.accumulate(eq)-eq)), 2),
            mean_gross_pts=round(float(g.gross_pts.mean()), 2),
            mean_cost_pts=round(float(g.cost_pts.mean()), 2),
            mean_mfe_pts=round(float(g.mfe_pts.mean()), 2),
            mean_mae_pts=round(float(g.mae_pts.mean()), 2),
            mean_hold_min=round(float(g.duration_min.mean()), 2),
            ci95_low=round(float(lo_ci), 2), ci95_high=round(float(hi_ci), 2)))
    return pd.DataFrame(rows)

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    f, h, base_quality = features()
    signal_map = signals(h)
    op = f.open.to_numpy(float)
    hi = f.high.to_numpy(float)
    lo = f.low.to_numpy(float)
    cl = f.close.to_numpy(float)
    fi = f.index
    events = []
    ledger = []
    # Independently enforce no overlap WITHIN each rule/style; do not combine
    # overlapping strategies or count fee variants as separate real trades.
    busy_through = {}
    missed = {"incomplete_hour": 0, "no_retest_reclaim": 0, "invalid_structure_risk": 0}
    for rule in RULES:
        condition, sides = signal_map[rule]
        for i in np.flatnonzero(condition.to_numpy(bool)):
            z = h.iloc[i]
            side = int(sides[i])
            time = h.index[i] + pd.Timedelta(hours=1)
            k = int(fi.searchsorted(time))
            if k + 120 > len(fi) or fi[k] != time or fi[k+119] != time + pd.Timedelta(minutes=119):
                missed["incomplete_hour"] += 1
                continue
            rt = retest_reclaim(z, side, k, op, hi, lo, cl)
            if rt is None:
                missed["no_retest_reclaim"] += 1
            price_dir_30m = side * (float(cl[k+29]) - float(op[k]))
            price_dir_60m = side * (float(cl[k+59]) - float(op[k]))
            events.append(dict(rule=rule, period=period(h.index[i]), signal_utc=str(h.index[i]),
                ny_date=z.ny_date, ny_hour=int(z.ny_next_hour),
                side=side, range_ratio=round(float(z.range_ratio), 3),
                oi_z=round(float(z.oi_z), 3),
                oi_group="rising" if z.oi_z >= 1 else "falling" if z.oi_z <= -1 else "middle",
                retest_reclaim=int(rt is not None),
                signed_30m_pts=round(price_dir_30m, 2),
                signed_60m_pts=round(price_dir_60m, 2)))
            for style in STYLES:
                if style != "immediate_all" and rt is None:
                    continue
                entry = k if style.startswith("immediate") else rt[0]
                key = (rule, style)
                if entry <= busy_through.get(key, -1):
                    continue
                if style == "retest_structure":
                    _, swing, risk = rt
                    if not (100 <= risk <= 650):
                        missed["invalid_structure_risk"] += 1
                        continue
                    stop = swing
                    target = float(op[entry]) + side * (1.5 * risk)
                else:
                    stop = float(op[entry]) - side * 350
                    target = float(op[entry]) + side * 500
                out = replay(op, hi, lo, cl, entry, side, stop, target,
                             MAX_HOLD_BARS[style])
                busy_through[key] = out["exit_j"]
                for fee_mode, net_col in (("standard_taker", "net_standard"),
                                          ("scalper_counterfactual", "net_scalper_sensitivity")):
                    ledger.append(dict(rule=rule, style=style, fee_mode=fee_mode,
                        period=period(h.index[i]), ny_date=z.ny_date,
                        signal_utc=str(h.index[i]),
                        entry_utc=str(fi[entry]), exit_utc=str(fi[out["exit_j"]]),
                        side=side, oi_z=round(float(z.oi_z), 3),
                        gross_pts=round(out["gross_pts"], 3),
                        net_pts=round(out[net_col], 3),
                        cost_pts=round(out["gross_pts"]-out[net_col], 3),
                        duration_min=out["duration_min"],
                        mfe_pts=round(out["mfe_pts"], 3),
                        mae_pts=round(out["mae_pts"], 3),
                        reason=out["reason"]))
    ev = pd.DataFrame(events)
    tr = pd.DataFrame(ledger)
    if ev.empty or tr.empty:
        raise ValueError("No eligible observations or fills")
    summ = summarize(tr)
    ev.to_csv(OUT/"event_observations.csv", index=False)
    tr.to_csv(OUT/"trade_ledger.csv", index=False)
    summ.to_csv(OUT/"trade_summary.csv", index=False)
    event_summ = ev.groupby(["rule", "period"], sort=True).agg(
        events=("signal_utc", "count"), days=("ny_date", "nunique"),
        retest_rate=("retest_reclaim", "mean"),
        signed_30m_pts=("signed_30m_pts", "mean"),
        signed_60m_pts=("signed_60m_pts", "mean")).reset_index()
    event_summ["retest_rate"] = (event_summ.retest_rate * 100).round(2)
    event_summ.to_csv(OUT/"event_summary.csv", index=False)
    # Open-interest associations are observational and not causal; avoid
    # using the already-seen later period to fit a trading threshold.
    oi_summary = ev.groupby(["rule", "period", "oi_group"]).agg(
        events=("signal_utc", "count"), retest_rate=("retest_reclaim", "mean"),
        direction_60m_pts=("signed_60m_pts", "mean")).reset_index()
    oi_summary.to_csv(OUT/"oi_conditional_summary.csv", index=False)
    meta = {
        "source": "Delta Exchange India existing BTCUSD 1m, mark 1m, OI 5m, funding 1h",
        "prior_stage2_quality": base_quality,
        "hourly_signal_count": len(ev), "replayed_rows_including_cost_scenarios": len(tr),
        "missed": missed, "thresholds": {
            "hourly_range_ratio": 2, "retest_depth_prior_48h_median_fraction": 0.25,
            "retest_window_minutes": 30, "retest_then_reclaim_different_5m_blocks": True,
            "entry": "next 1m open following completed 5m confirmation",
            "structure_stop": "observed retracement swing plus 10pts buffer",
            "structure_risk_range_pts": [100, 650], "structure_target_R": 1.5,
            "fixed_target_stop_pts": [500, 350],
            "standard_side_taker_fee_plus_gst": STANDARD_SIDE_FEE,
            "slippage_points_per_side": SLIP,
            "scalper_counterfactual": "zero close fee only if modeled exit <=30m"},
        "caveats": [
            "All periods studied previously; 2026 H2 is not independent out of sample",
            "Scalper sensitivity is COUNTERFACTUAL in older periods; offer eligibility must be checked on actual fills",
            "No historical order-book spread/depth, impact or intraminute tick path",
            "Funding cashflows not reconstructed for holds crossing funding events",
            "1m OHLC stop-first; gap stop worse-of-open-or-stop",
            "OHLC excursions can overstate achievable favorable movement",
            "Overlapping parent strategies and fee scenarios are not independent portfolios",
            "Day-block confidence intervals exploratory, not multiplicity adjusted",
            "No live or independent forward performance established",
            "BTC price-point-equivalent returns, not actual account USD"] }
    (OUT/"quality.json").write_text(json.dumps(meta, indent=2, default=str)+"\n")
    lines = [
        "# Stage 4 — Retracement/reclaim after high-volatility BTC hours",
        "",
        "## Predeclared question",
        "Does a genuine first-30m retracement plus subsequent *separate completed 5m* reclaim improve",
        "execution against the Stage 3 immediate-entry price-only baselines?",
        "This is an execution/selection investigation, not a claim of profitability.",
        "",
        "## Event outcomes", event_summ.to_markdown(index=False), "",
        "## Executable replay, standard taker fees + GST + 5pt slippage per side",
        summ[summ.fee_mode=="standard_taker"].to_markdown(index=False), "",
        "## Counterfactual Scalper Offer sensitivity (waive close fee only for <=30m exits)",
        summ[summ.fee_mode=="scalper_counterfactual"].to_markdown(index=False), "",
        "## Incremental OI description (not a causally controlled study)",
        oi_summary.to_markdown(index=False), "",
        "## Reproduction and caution",
        "- Source: scripts/research_retest_reclaim_stage4.py; Stage 2 shared feature builder.",
        "- immediate_all = first available hourly open, fixed TP 500 / SL 350 / 60m max.",
        "- immediate_on_retest = same fixed execution, restricted to events that LATER met the retest condition; diagnostic only, NOT actionable ex ante.",
        "- retest_fixed = 5m reclaim -> next 1m open; TP 500 / SL 350 / 60m max.",
        "- retest_structure = same reclaim; already-observed swing stop, target 1.5R, 120m max.",
        "- Only one position at a time within each independently measured style/rule.",
        "- All 2026 data have been studied before. Do not call any of it an untouched holdout.",
        "- Standard taker scenario is conservative relative to an eligible closing-fee offer; spread and impact unknown.",
        "- Missing funding, quote-based costs and truly forward data prevent live-deployment claims.",
        "- Retest eligibility is determined by future path; compare only executable retest entries as prospective strategies.",
        "",
        "## Research verdict",
        "No result is selected or optimized automatically. Examine the sign, sample sizes, and consistency",
        "across the first two periods and the *previously seen* 2026 H2 recheck. Preserve negative runs.",
        "Next genuinely independent test requires data collected AFTER the research freeze, with parameters locked.",
        ""]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(lines))
    print("STAGE4_DONE", json.dumps({"events":len(ev),"trade_rows":len(tr),"missed":missed}))
    print("STANDARD_FEE_SUMMARY\n", summ[summ.fee_mode=="standard_taker"].to_string(index=False))
    print("EVENT_SUMMARY\n", event_summ.to_string(index=False))

if __name__ == "__main__":
    main()
