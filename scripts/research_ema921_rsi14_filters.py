#!/usr/bin/env python3
"""RSI(14) on closed 1H and/or 15M as confirmation of EMA9/21 MTF cross.

No RSI on 5M. Weekdays IST for entries. Baseline parity checked against
previous fixed-point SL/TP historical backtests. NOT a prospective validation.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from research_ema921_1h15m5m_rr import candidates, candles, load_source
from research_ema921_fixed_rr_grid import replay, analyze, month_coverage

OUT = Path("analysis/ema921_rsi14_filters")
IST = "Asia/Kolkata"
PERIOD = 14
EXIT_PAIRS = [(100, 200), (400, 1200)]

# Each pair (1h minimum bullish RSI or None, 15m minimum bullish RSI or None).
# Bearish threshold is its complement: 100 - bullish.
PRESET = [
    ("NO_RSI", None, None),
    ("BOTH_50", 50, 50),
    ("BOTH_55", 55, 55),
    ("BOTH_60", 60, 60),
    ("H1_55_ONLY", 55, None),
    ("M15_55_ONLY", None, 55),
    ("H1_60_ONLY", 60, None),
    ("M15_60_ONLY", None, 60),
    ("H1_55_M15_50", 55, 50),
    ("H1_50_M15_55", 50, 55),
]


def wilder_rsi14(close: pd.Series, period=PERIOD) -> pd.Series:
    """True Wilder RSI: SMA seed of 14 differences, then recursive RMA."""
    a = close.to_numpy(float)
    n = len(a)
    out = np.full(n, np.nan, dtype=float)
    if n <= period:
        return pd.Series(out, index=close.index)
    delta = np.diff(a[:period+1])
    avg_gain = float(np.maximum(delta, 0).sum()/period)
    avg_loss = float(np.maximum(-delta, 0).sum()/period)

    def value(g, l):
        if l == 0:
            return 100.0 if g > 0 else 50.0
        return 100.0 - 100.0/(1.0+g/l)

    out[period] = value(avg_gain, avg_loss)
    for i in range(period+1,n):
        diff = a[i] - a[i-1]
        avg_gain = (avg_gain*(period-1) + max(diff, 0.0))/period
        avg_loss = (avg_loss*(period-1) + max(-diff, 0.0))/period
        out[i] = value(avg_gain,avg_loss)
    return pd.Series(out,index=close.index)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    raw, secs, gaps=load_source()
    base_events, sig_stats=candidates(raw)
    hour = candles(raw,60)
    quarter = candles(raw,15)
    rsi_h = wilder_rsi14(hour.close)
    rsi_q = wilder_rsi14(quarter.close)
    # Use only the last COMPLETED (right-labeled) 1h/15m bars at signal instant.
    # A 5m signal timestamp can coincide with the close of its 1h/15m bar.
    # This is lawful, as next 1m opens at the same instant, after the close.
    event_rsi = {}
    for k,side,stop in base_events:
        stamp = raw.index[k]
        hi=int(hour.index.searchsorted(stamp, side="right")-1)
        qi=int(quarter.index.searchsorted(stamp, side="right")-1)
        if hi<0 or qi<0:
            raise AssertionError("Missing completed higher TF timestamp")
        if not (hour.valid.iloc[hi] and quarter.valid.iloc[qi]):
            raise AssertionError("Higher timeframe quality mask diverged")
        event_rsi[k]=(float(rsi_h.iloc[hi]),float(rsi_q.iloc[qi]))

    names,coverage = month_coverage(raw)
    all_summary=[]
    all_monthly=[]
    all_trades=[]
    filter_counts=[]
    for label,h_min,q_min in PRESET:
        filtered=[]
        long_signals=0
        short_signals=0
        for e in base_events:
            k,side,stop=e
            hour_rsi,quarter_rsi=event_rsi[k]
            ok = True
            for rsi,threshold in ((hour_rsi,h_min),(quarter_rsi,q_min)):
                if threshold is None:
                    continue
                if not np.isfinite(rsi):
                    ok = False
                    break
                if side==1 and rsi<threshold:
                    ok=False
                    break
                if side==-1 and rsi>100-threshold:
                    ok=False
                    break
            if ok:
                filtered.append(e)
                if side==1:long_signals+=1
                else:short_signals+=1
        filter_counts.append({
            "filter":label,"rsi_period":PERIOD,
            "1h_bullish_min":h_min,"1h_bearish_max":(100-h_min) if h_min else None,
            "15m_bullish_min":q_min,"15m_bearish_max":(100-q_min) if q_min else None,
            "candidate_signals_all_days":len(filtered),
            "candidate_long":long_signals,"candidate_short":short_signals,
        })
        idx_lookup={
            raw.index[k].tz_convert(IST).isoformat():event_rsi[k]
            for k,_,_ in filtered
        }
        for sl,tp in EXIT_PAIRS:
            rows,skip = replay(raw,secs,filtered,sl,tp,True)
            summ,months = analyze(rows,names,coverage,True,sl,tp,skip)
            if label=="NO_RSI" and (sl,tp)==(100,200):
                if (summ["trades"],summ["wins"])!=(1130,359):
                    raise AssertionError(f"100/200 baseline parity fail: {summ}")
            if label=="NO_RSI" and (sl,tp)==(400,1200):
                if (summ["trades"],summ["wins"])!=(773,208):
                    raise AssertionError(f"400/1200 baseline parity fail: {summ}")
            case=f"{label}_SL{sl}_TP{tp}"
            summ.update({
                "case":case,"filter":label,
                "1h_bullish_rsi_min":h_min,
                "15m_bullish_rsi_min":q_min,
                "pre_overlap_signal_count":len(filtered),
            })
            for r in rows:
                r["case"]=case
                hval,qval=idx_lookup[r["entry_ist"]]
                r["rsi14_1h_last_closed"]=round(hval,3)
                r["rsi14_15m_last_closed"]=round(qval,3)
            for m in months:
                m["case"]=case
                m["filter"]=label
            all_summary.append(summ)
            all_monthly.extend(months)
            all_trades.extend(rows)
            print("CASE",case,"signals",len(filtered),
                  "trades",summ["trades"],"wins",summ["wins"],
                  "profitable months",summ["positive_months_22"],
                  "net",round(summ["net_1x_account_pct"],3),flush=True)

    summary=pd.DataFrame(all_summary)
    monthly=pd.DataFrame(all_monthly)
    ledger=pd.DataFrame(all_trades)
    cdf=pd.DataFrame(filter_counts)
    summary.to_csv(OUT/"summary.csv",index=False)
    monthly.to_csv(OUT/"monthly_results.csv",index=False)
    ledger.to_csv(OUT/"trade_ledger.csv",index=False)
    cdf.to_csv(OUT/"signal_filter_counts.csv",index=False)
    (OUT/"quality.json").write_text(json.dumps({
        "data_rows":len(raw),"data_start":str(raw.index[0]),
        "data_end":str(raw.index[-1]),"gaps":gaps,
        "source_coverage":coverage,"baseline_signal_stats":sig_stats,
        "rsi_implementation":"Wilder RMA14 seeded SMA of first 14 close differences",
        "rsi_only_on_closed_1h_15m":True,
        "rsi_conditions":[[label,h,q] for label,h,q in PRESET],
        "fixed_exit_pairs":EXIT_PAIRS,
        "weekdays_entry_only_IST":True,
        "weekend_exit_permitted":True,
        "baseline_parity":"PASS",
        "fees_each_side_with_GST_fraction":0.00059,
        "slippage_each_side_price_points":5,
        "risk_disclaimers":"Historical already researched, 2026 not unseen holdout. No funding, true spread, marginal liquidation modeling."
    },indent=2))
    cols=["case","pre_overlap_signal_count","trades","wins","losses",
          "win_rate_pct","positive_months_22",
          "return_2025_pct","return_2026_JanOct_pct","net_1x_account_pct",
          "max_closed_trade_drawdown_pct","profit_factor_net_points"]
    # 2025 ranking only; all settings prespecified, ranking still in-sample.
    grid_summary=summary.sort_values(
        ["stop_points","return_2025_pct"],
        ascending=[True,False]
    )
    months_wide=monthly[monthly["filter"].isin(
        ["NO_RSI","BOTH_50","BOTH_55","BOTH_60"]
    )].pivot(index="month_ist",columns="case",values="net_1x_account_pct").reset_index()
    report=[
        "# BTCUSD EMA9/21 1H + 15M RSI14 filter experiment — 5M cross entry",
        "",
        "## Results (Monday–Friday entries, 1m execution)",
        "Same original 1H/15M/5M EMA9/21 trigger as baseline, only add a completed-candle RSI14 trend-strength gate on the 1H, 15M, or both. ",
        "LONG RSI>=cutoff (50/55/60), SHORT RSI<=100-cutoff. For BOTH mode both must pass. ",
        "Fixed exits independently 100/200 and 400/1200 BTC points. Next 1m open, one position, no trailing, stop-first if 1m ambiguous.",
        "",
        grid_summary[cols].to_markdown(index=False,floatfmt=".2f"),
        "",
        "## RSI filter signal counts before weekday/position overlap exclusions",
        cdf.to_markdown(index=False),
        "",
        "## Monthly net 1x account returns for no RSI vs both-timeframe 50/55/60",
        months_wide.to_markdown(index=False,floatfmt=".2f"),
        "",
        "## Methodology / cautions",
        f"- Original 1m candles: {len(raw):,}, gaps {len(gaps)}.",
        "- January 2025 IST starts 330 minutes after month start. November 2026 incomplete and excluded.",
        "- 2025 and Jan-Oct 2026 already researched. This is not blind out-of-sample evidence; parameter comparisons are multiple tests.",
        "- True Wilder RSI(14) (SMA-seeded RMA), computed only on the latest completed 1H / 15M bars.",
        "- Entry filter on Monday–Friday IST, existing positions may exit on weekends.",
        "- Gross-to-net: 0.05% taker per side + GST18% on fees and $5 adverse price slippage per side.",
        "- Stops/targets measured from post-slip entry, stop-first 1m tie, gap-stop on the next available 1m open.",
        "- IST month-end flat, no timeout/trailing/EMA exit. Max DD measured at closes only (understates intratrade DD).",
        "- Account 1x notional per trade with compounded returns, no funding, actual bid/ask spread, liquidation/margin.",
        "- Baseline 100/200=1130 trades/359 wins; 400/1200=773 trades/208 wins: parity PASSED.",
        "- RSI filter changes how many signals remain; trades can increase due to removal of longer overlapping positions.",
        "",
        "## Files",
        "- NOVELTY_CHECK.md, summary.csv, monthly_results.csv, signal_filter_counts.csv, trade_ledger.csv, quality.json."
    ]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")
    print("COMPLETE",json.dumps({
        "case_count":len(summary),
        "parity":"PASS",
        "results":summary[cols].to_dict("records")
    }),flush=True)


if __name__=="__main__":
    main()
