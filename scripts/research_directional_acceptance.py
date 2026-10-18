#!/usr/bin/env python3
"""Stage 3: conditional direction, acceptance, OI incremental value and executable replay.
Known history is exploratory, including July-Oct 2026; future observations required.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from research_behavioral_discovery import features, FEE, SLIP

OUT = Path("analysis/institutional_discovery_stage3")
MIN_SAMPLES = 20
SEED = 1937

def signals(h):
    # A fully completed hourly candle is timestamped at its opening minute.
    # All features below become available only when that hour ends.
    rr = h.range_ratio >= 2
    loc = ((h.close - h.low) / h["range"].replace(0, np.nan))
    up = h.close > h.open
    down = h.close < h.open
    accepted_up = (h.close > h.hi12) & (loc >= .75)
    accepted_down = (h.close < h.lo12) & (loc <= .25)
    rejected_up = (h.high > h.hi12) & (h.close < h.hi12) & (loc <= .35)
    rejected_down = (h.low < h.lo12) & (h.close > h.lo12) & (loc >= .65)
    # (condition, direction), all fixed before reading Stage 3 test outcomes.
    base = {
        "expansion_follow": (rr & (up | down), np.where(up, 1, -1)),
        "expansion_fade": (rr & (up | down), np.where(up, -1, 1)),
        "strong_close_follow": (rr & ((up & (loc >= .80)) | (down & (loc <= .20))),
                                np.where(up, 1, -1)),
        "weak_close_fade": (rr & ((up & (loc <= .35)) | (down & (loc >= .65))),
                            np.where(up, -1, 1)),
        "accepted_12h_breakout": (rr & (accepted_up | accepted_down),
                                  np.where(accepted_up, 1, -1)),
        "rejected_12h_sweep": (rr & (rejected_up | rejected_down),
                               np.where(rejected_up, -1, 1)),
    }
    rules = {}
    for name, (mask, side) in base.items():
        rules[name] = (mask.fillna(False), side)
        if name in ("strong_close_follow", "accepted_12h_breakout", "rejected_12h_sweep"):
            rules[name + "__oi_rising"] = (mask.fillna(False) & (h.oi_z >= 1), side)
            rules[name + "__oi_falling"] = (mask.fillna(False) & (h.oi_z <= -1), side)
    return rules

def period_name(t):
    if t.year == 2025: return "train"
    if t < pd.Timestamp("2026-07-01", tz="UTC"): return "validation"
    return "recheck_seen"

def replay(f, h, rules):
    op = f.open.to_numpy(float)
    hi = f.high.to_numpy(float)
    lo = f.low.to_numpy(float)
    cl = f.close.to_numpy(float)
    index = f.index
    records = []
    descriptive = []
    for rule, (eligible, sides) in rules.items():
        picks = np.flatnonzero(eligible.to_numpy(bool))
        for i in picks:
            z = h.iloc[i]
            t = h.index[i]
            when = t + pd.Timedelta(hours=1)
            k = int(index.searchsorted(when))
            if k + 60 > len(index) or index[k] != when or index[k+59] != when + pd.Timedelta(minutes=59):
                continue
            side = int(sides[i])
            if side not in (-1, 1): continue
            future = h.iloc[i]  # h.future columns are next-hour outcomes
            signed = side * (future.future_close - future.future_open)
            descriptive.append(dict(rule=rule, period=period_name(t), timestamp_utc=str(t),
                ny_date=z.ny_date, side=side, close_location=round(float((z.close-z.low)/z["range"]),4),
                oi_z=round(float(z.oi_z),4), gross_hourly_directional_pts=round(float(signed),4),
                correct_direction=int(signed > 0)))
            # Two decision-time entry schemes: immediate and 5m confirmed.
            # Confirmation uses a COMPLETED first 5m close; fill at minute 5 OPEN.
            for scheme in ("immediate", "5m_confirm"):
                entry_k = k
                if scheme == "5m_confirm":
                    confirmation = cl[k+4]
                    if side * (confirmation-op[k]) <= 0:
                        continue
                    entry_k = k + 5
                entry_mid = op[entry_k]
                entry_fill = entry_mid + side * SLIP
                # All stops/targets calculated relative to observed entry quote proxy.
                stop = entry_mid - side*350
                target = entry_mid + side*500
                first_stop = k + 60
                first_target = k + 60
                for j in range(entry_k, k+60):
                    if (side == 1 and lo[j] <= stop) or (side == -1 and hi[j] >= stop):
                        first_stop = j
                        break
                for j in range(entry_k, k+60):
                    if (side == 1 and hi[j] >= target) or (side == -1 and lo[j] <= target):
                        first_target = j
                        break
                if first_stop <= first_target and first_stop < k + 60:
                    end = first_stop
                    exit_mid = stop
                    reason = "stop"
                elif first_target < k + 60:
                    end = first_target
                    exit_mid = target
                    reason = "target"
                else:
                    end = k+59
                    exit_mid = cl[end]
                    reason = "hour_timeout"
                # Do not assume target is filled at a better-than-level price.
                exit_fill = exit_mid - side * SLIP
                net = side*(exit_fill-entry_fill)-FEE*(entry_fill+exit_fill)
                gross = side*(exit_mid-entry_mid)
                excursion_hi = hi[entry_k:end+1]
                excursion_lo = lo[entry_k:end+1]
                mfe = (float(excursion_hi.max())-entry_mid) if side==1 else (entry_mid-float(excursion_lo.min()))
                mae = (entry_mid-float(excursion_lo.min())) if side==1 else (float(excursion_hi.max())-entry_mid)
                records.append(dict(rule=rule,period=period_name(t),ny_date=z.ny_date,
                    entry_utc=str(index[entry_k]),side=side,scheme=scheme,reason=reason,
                    gross_pts=round(float(gross),4), net_pts=round(float(net),4),
                    mfe_pts=round(float(max(mfe,0)),4),mae_pts=round(float(max(mae,0)),4)))
    return pd.DataFrame(descriptive), pd.DataFrame(records)

def summary(df, value, by, descriptive=False):
    output=[]
    for keys,g in df.groupby(by, sort=True):
        if not isinstance(keys,tuple): keys=(keys,)
        vals=g[value].to_numpy(float)
        n=len(vals)
        result=dict(zip(by, keys))
        result["n"]=n
        result["mean"]=round(float(vals.mean()),3)
        result["win_pct"]=round(100*float((vals>0).mean()),2)
        result["days"]=int(g.ny_date.nunique())
        if not descriptive:
            prof=vals[vals>0].sum()
            loss=-vals[vals<0].sum()
            result["profit_factor"]=round(float(prof/loss),3) if loss else None
            result["max_drawdown_pts"]=round(float(np.max(np.maximum.accumulate(np.r_[0,vals.cumsum()]) - np.r_[0,vals.cumsum()])),2)
            result["avg_mfe_pts"]=round(float(g.mfe_pts.mean()),2)
            result["avg_mae_pts"]=round(float(g.mae_pts.mean()),2)
        # Resample entire New York calendar days (not individual highly correlated trades).
        d=g.groupby("ny_date")[value].agg(["sum","count"]).to_numpy(float)
        if n>=MIN_SAMPLES and len(d)>=12:
            rng=np.random.default_rng(SEED)
            draws=rng.integers(len(d),size=(450,len(d)))
            sums=d[draws].sum(axis=1)
            boot=sums[:,0]/sums[:,1]
            result["bootstrap_mean_95_low"]=round(float(np.quantile(boot,.025)),3)
            result["bootstrap_mean_95_high"]=round(float(np.quantile(boot,.975)),3)
        output.append(result)
    return pd.DataFrame(output)

def incremental(d):
    # Direct within-period comparison against corresponding price-only rule.
    # Conditional differences are descriptive; filtering creates distinct samples.
    out=[]
    for period in sorted(d.period.unique()):
        f=d[d.period==period]
        for parent in ("strong_close_follow","accepted_12h_breakout","rejected_12h_sweep"):
            basic=f[f.rule==parent]
            if basic.empty:continue
            for suffix in ("__oi_rising","__oi_falling"):
                extra=f[f.rule==parent+suffix]
                if extra.empty:continue
                out.append(dict(period=period,base=parent,filter=suffix[2:],
                    n_base=len(basic),n_filter=len(extra),
                    base_accuracy_pct=round(100*basic.correct_direction.mean(),2),
                    filter_accuracy_pct=round(100*extra.correct_direction.mean(),2),
                    accuracy_delta_pp=round(100*(extra.correct_direction.mean()-basic.correct_direction.mean()),2),
                    base_mean_gross_pts=round(basic.gross_hourly_directional_pts.mean(),2),
                    filter_mean_gross_pts=round(extra.gross_hourly_directional_pts.mean(),2)))
    return pd.DataFrame(out)

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    f,h,quality=features()
    rules=signals(h)
    d,tr=replay(f,h,rules)
    if d.empty or tr.empty: raise ValueError("No usable observations")
    ds=summary(d,"gross_hourly_directional_pts",["rule","period"],True)
    ts=summary(tr,"net_pts",["rule","scheme","period"])
    inc=incremental(d)
    d.to_csv(OUT/"directional_observations.csv",index=False)
    tr.to_csv(OUT/"trade_ledger.csv",index=False)
    ds.to_csv(OUT/"directional_summary.csv",index=False)
    ts.to_csv(OUT/"trade_summary.csv",index=False)
    inc.to_csv(OUT/"oi_incremental_comparison.csv",index=False)
    metadata={
        "source": "Delta Exchange India historical futures 1m, mark 1m, OI 5m, funding 1h",
        "input_hourly_rows":len(h), "directional_observations":len(d), "replayed_trades":len(tr),
        "first_utc":str(h.index.min()),"last_utc":str(h.index.max()),
        "fixed_predeclared_rules":list(rules),
        "cost_model":{"taker_per_side_with_gst":FEE,"slippage_points_per_side":SLIP},
        "execution":"completed hourly signal; immediate at following hour open or first completed 5m move confirmed and minute 5 open; intraminute stop-first; one-hour timeout",
        "important_caveats":[
            "2026 July-Oct is previously seen, NOT a globally untouched holdout",
            "L1 bid/ask historical spread and market impact unavailable; simulated fills only",
            "OI is descriptive positioning proxy, not observed institutional trades",
            "Funding for sub-hour holds not reconstructed; additional real cost possible",
            "Multiple variants and repeated research create selection bias",
            "BTC points are not account USD; sizes, collateral and liquidation excluded",
            "Day bootstrap intervals unadjusted for multiple hypothesis tests",
            "Overlapping strategy variants must NEVER be aggregated as independent returns"]
    }
    (OUT/"quality.json").write_text(json.dumps(metadata,indent=2)+"\n")
    def markdown(df):return df.to_markdown(index=False) if len(df) else "No observations."
    top=ts[ts.scheme=="immediate"].copy()
    # Display ALL baseline variants across periods; do not rank on last window.
    lines=[
        "# Stage 3 — Direction after hourly expansion: acceptance, rejection and OI",
        "",
        "## Hypothesis and status",
        "Stage 2 predicts volatility, not price direction. Test whether close location, 12-hour range acceptance or failed sweep makes the next hour directional enough to cover fees.",
        "All thresholds and execution styles are fixed inside the versioned source. THIS IS EXPLORATORY HISTORICAL RESEARCH, NOT FOR LIVE TRADING.",
        "2025 training; Jan-Jun 2026 validation; Jul-Oct 2026 previously inspected chronological recheck, NOT an independent holdout.",
        "",
        "## Next-hour directional gross outcomes (a descriptive forecast, not tradable P&L)",
        markdown(ds),"",
        "## Immediate-entry execution after taker fees/GST and slippage (500 target, 350 stop, 60m max)",
        markdown(top),"",
        "## Confirmation at first completed 5m close; entry at minute 5 open",
        markdown(ts[ts.scheme=="5m_confirm"]), "",
        "## OI incremental contrast against price-only parent (not causal identification)",
        markdown(inc),"",
        "## Limitations",
        *["- "+x for x in metadata["important_caveats"]],
        "",
        "MFE and MAE are derived from 1m OHLC and are upper-bound-like paths within the exit minute; stop-first conservative where both limits touch.",
        "Full ledgers and quality notes are saved alongside this report.",
        "No positive edge should be claimed without post-selection truly forward observations, realistic quote-based fills and independent robustness replication."
    ]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(lines)+"\n")
    print("STAGE3_COMPLETED",json.dumps(metadata))
    print("DIRECTIONAL_SUMMARY\n",ds.to_string(index=False))
    print("TRADE_SUMMARY\n",ts.to_string(index=False))

if __name__=="__main__":
    main()
