#!/usr/bin/env python3
"""BTCUSD 1H Bollinger 30/2, ATR14 x.25 stop, fixed 3R, true Delta 1m exits.

Reuses the exact daily study's fill, funding and portfolio accounting engines for
the controlled 1H-versus-1D experiment, changing signal timeframe only.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from research_daily_bollinger_30_3r import load_1m, load_funding, backtest
from research_daily_bollinger_30_3r_concurrent import simulate

OUT = Path("analysis/hourly_bollinger_30_3r")


def hourly_signals(d):
    # Full hour [H:00,H+1:00); index labels H+1:00 = first possible executable minute.
    hourly = d.resample("1h", label="right", closed="left").agg(
        {"open":"first", "high":"max", "low":"min", "close":"last"}
    )
    hourly["count"] = d.close.resample(
        "1h", label="right", closed="left"
    ).count()
    # No partial candle, no interpolation; source loader rejects gaps.
    hourly = hourly[hourly["count"] == 60].copy()
    close = hourly.close
    mid = close.rolling(30, min_periods=30).mean()
    sd = close.rolling(30, min_periods=30).std(ddof=0)
    hourly["bb_mid"] = mid
    hourly["bb_upper"] = mid + 2.0*sd
    hourly["bb_lower"] = mid - 2.0*sd
    prev = close.shift(1)
    true_range = pd.concat(
        (hourly.high-hourly.low, (hourly.high-prev).abs(),
         (hourly.low-prev).abs()), axis=1
    ).max(axis=1)
    ranges = true_range.to_numpy(float)
    atr = np.full(len(hourly), np.nan, dtype=float)
    if len(atr) >= 14:
        atr[13] = np.mean(ranges[:14])
        for i in range(14, len(atr)):
            atr[i] = (atr[i-1]*13 + ranges[i])/14.0
    hourly["atr14"] = atr
    hourly["side"] = np.where(
        close > hourly["bb_upper"], 1,
        np.where(close < hourly["bb_lower"], -1, 0)
    )
    hourly.loc[hourly.atr14.isna(), "side"] = 0

    signals = {}
    for ts, x in hourly.iterrows():
        side = int(x.side)
        if side == 0:
            continue
        stop = float(
            x.low - 0.25*x.atr14 if side > 0
            else x.high + 0.25*x.atr14
        )
        signals[int(ts.timestamp())] = (
            side, stop, str(ts - pd.Timedelta(hours=1)),
            float(x.close), float(x.atr14)
        )
    return hourly, signals


def split_trade_stats(df, suffix):
    if suffix == "isolated":
        datecol = "exit_ist_month"
        pnlcol = "net_usd"
        holdcol = "held_minutes"
        targetcol = "result"
        targetval = "target"
        riskcol = "net_R"
    else:
        datecol = "exit_ist_month"
        pnlcol = "net_usd"
        holdcol = "held_minutes"
        targetcol = "reason"
        targetval = "target"
        riskcol = "net_R"
    dates = df[datecol].astype(str)
    periods = [
        ("2025", dates.str.startswith("2025")),
        ("2026_Jan_Oct", (dates>="202601") & (dates<="202611")),
        ("2026_Nov_partial", dates=="202611"),
        ("through_Oct_2026", dates<"202611"),
        ("entire_archive", dates.notna()),
    ]
    rows = []
    for name, mask in periods:
        sel = df[mask]
        net = sel[pnlcol].to_numpy(float)
        if len(net) == 0:
            rows.append(dict(scenario=suffix,period=name,trades=0,wins=0,losses=0,
                 win_rate_pct=None,net_profit_factor=None,net_closed_usd=0.0,
                 avg_net_R=None,targets_hit=0,median_held_minutes=None))
            continue
        plus = net[net>0].sum()
        minus = -net[net<0].sum()
        rows.append(dict(
            scenario=suffix,period=name,trades=len(sel),
            wins=int((net>0).sum()),losses=int((net<=0).sum()),
            win_rate_pct=round(float((net>0).mean()*100),2),
            net_profit_factor=round(float(plus/minus),3) if minus>0 else None,
            net_closed_usd=round(float(net.sum()),2),
            avg_net_R=round(float(sel[riskcol].mean()),4),
            targets_hit=int((sel[targetcol] == targetval).sum()),
            median_held_minutes=round(float(sel[holdcol].median()),2)))
    return pd.DataFrame(rows)


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    d, archive_parts = load_1m()
    hours, sig = hourly_signals(d)
    funding, rateparts = load_funding()
    iso_trades, iso_month, iso_result = backtest(d, sig, funding)
    con_trades, con_month, con_result = simulate(d, sig, funding)
    # Preserve every result including null / failed candidates.
    iso_trades.to_csv(OUT/"isolated_trade_ledger.csv",index=False)
    iso_month.to_csv(OUT/"isolated_monthly_ist.csv",index=False)
    con_trades.to_csv(OUT/"concurrent_trade_ledger.csv",index=False)
    con_month.to_csv(OUT/"concurrent_monthly_ist.csv",index=False)
    split = pd.concat([
        split_trade_stats(iso_trades,"isolated"),
        split_trade_stats(con_trades,"concurrent")
    ],ignore_index=True)
    split.to_csv(OUT/"period_trade_statistics.csv",index=False)
    summaries = dict(
        strategy="Completed 1h close beyond BB(30,2), stop +/- 0.25 Wilder ATR14 beyond 1h bar, fixed 3R",
        data_source="Delta India BTCUSD perpetual real 1m 2025-01-01 to 2026-11-19",
        entry="next genuine 1m OPEN after completed 1h close",
        execution="1m stop-first for intraminute ambiguity, no max hold, no trailing",
        portfolio_models="isolated one position versus overlapping independent positions under 2x gross cap",
        source_partitions=len(archive_parts),
        funding_proxy_partitions=rateparts,
        one_minute_bars=len(d),
        complete_hourly_bars=len(hours),
        signal_events_total=len(sig),
        signal_events_executable=sum(int(t in d.time.values) for t in []),
        time_span_utc=[str(d.index.min()),str(d.index.max())],
        isolated=iso_result,
        concurrent=con_result,
        limitations=[
            "Period exposure previously researched: not pristine out of sample.",
            "Funding estimates are proxy rates, not settled funding cashflow. Missing rates are unmodeled.",
            "Fees 0.05% taker per side plus 18% GST, adverse 5 price points each fill.",
            "No L1 order book, impact, actual liquidation or exact contract lot-size rounding.",
            "Concurrent overlapping opposite-direction positions may not be operationally possible in one netted trading account.",
            "Account figures for partial November include open-position mark-to-market; not realized profit.",
            "1H interval labels refer to the close boundary; no indicator or ATR lookahead."
        ]
    )
    # Fix signal count: final completed hour may end exactly at first unseen minute.
    summaries["signal_events_executable"] = sum(1 for t in sig if
        int(d.time.iloc[0]) <= t <= int(d.time.iloc[-1]))
    (OUT/"summary.json").write_text(json.dumps(summaries,indent=2,allow_nan=False)+"\n")
    notes = [
        "# Delta BTCUSD 1H Bollinger (30,2), ATR14 structural stop, 3R",
        "",
        "**Method:** the exact indicator parameters of the Daily BB30 backtest, now on fully closed 1-hour candles, same 1m fill/exit engine. No fitting to dates.",
        "**Signal:** close > BB upper LONG or close < BB lower SHORT; ATR(14) Wilder; SL 0.25 ATR outside signal candle wick; TP fixed at 3x entry-to-SL distance; allow every signal.",
        "**Entry:** next genuine 1-minute candle OPEN, adverse $5; **Exit:** minute stop or target, stop-first ambiguity, adverse $5.",
        "**Costs:** Delta futures taker 0.05% each side + 18% GST on fees; historical hourly funding-rate series as approximate settlement proxy; 1% initial stop risk per trade, 2x aggregate notional cap.",
        "**Account:** starts at $10,000, IST monthly marked P&L; no forced month-end liquidation, partial November is not full-month observation.",
        "",
        "## Comparison including all trade losses",
        split.to_markdown(index=False),
        "",
        "## One position only — IST month-end marked P&L",
        iso_month.to_markdown(index=False),
        "",
        "## Overlapping entries — IST month-end marked P&L",
        con_month.to_markdown(index=False),
        "",
        "## Data/validity limitations",
        *["- "+s for s in summaries["limitations"]],
        "",
        "Results are historical model outputs, not validated live fill probabilities or independent out-of-sample proof. Refer to trade ledgers for every trade."
    ]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(notes)+"\n")
    print("ONE_HOUR_BB30_3R_COMPLETED")
    print(json.dumps({k:v for k,v in summaries.items() if k not in ("isolated","concurrent")},indent=2))
    print("ISOLATED",json.dumps(iso_result,indent=2))
    print("CONCURRENT",json.dumps(con_result,indent=2))
    print(split.to_string(index=False))
    print(iso_month.to_string(index=False))
    print(con_month.to_string(index=False))


if __name__=="__main__":
    main()
