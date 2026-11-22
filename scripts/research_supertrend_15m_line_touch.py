#!/usr/bin/env python3
"""15m bullish Supertrend line touch, 1m entry/TP replay, 15m closing stop.

This is a research-only, predeclared comparison, not a validated live model.
See analysis/supertrend_15m_touch_20261122/NOVELTY_CHECK.md.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd

DATA = Path("data/delta_india/BTCUSD/1m")
OUT = Path("analysis/supertrend_15m_touch_20261122")
TP_PCTS = (0.002, 0.004, 0.005, 0.006, 0.01)
FEE = 0.0005 * 1.18
SLIP = 5.0
PERIOD, FACTOR = 10, 3.0
CUT = "2026-11"
MONTHS = pd.period_range("2025-01", "2026-10", freq="M").astype(str).tolist()


def load():
    files = sorted(DATA.glob("20??-??.csv.gz"))
    assert len(files) >= 22, f"Not enough 1m archive partitions: {len(files)}"
    pieces = []
    for f in files:
        x = pd.read_csv(f, compression="gzip",
                        usecols=["time", "open", "high", "low", "close", "volume"])
        pieces.append(x)
    x = pd.concat(pieces, ignore_index=True)
    x["time"] = pd.to_datetime(x.time.astype("int64"), unit="s", utc=True)
    x = x.sort_values("time").set_index("time")
    if x.index.has_duplicates:
        raise ValueError("Duplicate 1m times")
    if x[["open","high","low","close"]].isna().any().any():
        raise ValueError("OHLC missing")
    diffs = x.index.to_series().diff().dropna()
    bad = diffs.ne(pd.Timedelta(minutes=1))
    if bad.any():
        bad_idx = bad[bad].index[:5]
        raise ValueError("Missing/discontinuous 1m data; refuse to fabricate: " +
                         str(list(map(str, bad_idx))))
    expected = pd.date_range(x.index[0], x.index[-1], freq="min", tz="UTC")
    if len(expected) != len(x):
        raise ValueError("Unexpected archive minute count")
    h = x.resample("15min", label="left", closed="left").agg(
        {"open":"first", "high":"max", "low":"min", "close":"last",
         "volume":"sum"})
    counts = x.close.resample("15min", label="left", closed="left").count()
    if not counts.eq(15).all():
        raise ValueError("Incomplete 15m bucket, no invented candles")
    assert x.index[0] == h.index[0]
    assert len(x) == len(h) * 15
    return x, h, files


def supertrend(h):
    hi = h.high.to_numpy(float); lo = h.low.to_numpy(float)
    cl = h.close.to_numpy(float)
    n = len(h)
    tr = np.maximum(hi-lo, np.maximum(
        abs(hi-np.r_[cl[0], cl[:-1]]),
        abs(lo-np.r_[cl[0], cl[:-1]])))
    atr = np.full(n, np.nan)
    atr[PERIOD-1] = tr[:PERIOD].mean()
    for i in range(PERIOD, n):
        atr[i] = (atr[i-1]*(PERIOD-1) + tr[i])/PERIOD
    line = np.full(n, np.nan)
    direction = np.full(n, 1, dtype=np.int8)  # +1 bearish, -1 bullish
    ub = np.nan; lb = np.nan; previous_st = np.nan
    for i in range(PERIOD-1, n):
        basic_u=(hi[i]+lo[i])/2 + FACTOR*atr[i]
        basic_l=(hi[i]+lo[i])/2 - FACTOR*atr[i]
        prev_u, prev_l = ub, lb
        if np.isfinite(prev_u):
            ub = basic_u if (basic_u < prev_u or cl[i-1] > prev_u) else prev_u
            lb = basic_l if (basic_l > prev_l or cl[i-1] < prev_l) else prev_l
        else:
            ub, lb = basic_u, basic_l
        if np.isfinite(previous_st):
            if previous_st == prev_u:
                direction[i] = -1 if cl[i]>ub else 1
            else:
                direction[i] = 1 if cl[i]<lb else -1
        line[i] = lb if direction[i] == -1 else ub
        previous_st = line[i]
    return line, direction


def record(p, end_i, end_mid, reason, times):
    entry_mid = p["entry_mid"]
    entry_fill = p["entry_fill"]
    exit_fill = end_mid - SLIP
    gross = end_mid-entry_mid
    fee = FEE * (entry_fill + exit_fill)
    net = exit_fill-entry_fill-fee
    return dict(tp_pct=p["tp_pct"]*100, entry_utc=str(times[p["entry_i"]]),
                exit_utc=str(times[end_i]), entry_index=p["entry_i"],
                exit_index=end_i, entry_mid=entry_mid,
                exit_mid=end_mid, entry_fill=entry_fill, exit_fill=exit_fill,
                entry_line=p["entry_line"], exit_reason=reason,
                gross_pts=gross, fees_pts=fee, slippage_pts=2*SLIP,
                net_pts=net, net_return_pct=100*net/entry_fill,
                holding_minutes=end_i-p["entry_i"])


def replay(x, h, st, direction, target_pct):
    times=x.index; op=x.open.to_numpy(float)
    hi=x.high.to_numpy(float); lo=x.low.to_numpy(float)
    cl=x.close.to_numpy(float)
    hclose=h.close.to_numpy(float)
    n=len(h)
    trades=[]; p=None; used=False
    eligible_cycles=0; touched_cycles=0
    for i in range(PERIOD+1,n):
        if direction[i-1]==-1 and direction[i-2]!=-1:
            used=False
            eligible_cycles+=1
        if direction[i-1]==-1:
            prev_support = float(st[i-1])
        else:
            prev_support = np.nan
        # Complete contiguous 15m units, the only time allowed to update line.
        start=i*15; end=start+15
        for j in range(start,end):
            if p is not None and j>p["entry_i"] and hi[j]>=p["target"]:
                trades.append(record(p,j,p["target"],"target",times))
                p=None
            if p is None and direction[i-1]==-1 and not used and lo[j]<=prev_support:
                mid=min(float(op[j]),prev_support)  # resting buy-limit, gap-aware
                fill=mid+SLIP
                p=dict(entry_i=j,entry_mid=mid,entry_fill=fill,
                       entry_line=prev_support, tp_pct=target_pct,
                       target=fill*(1+target_pct))
                used=True
                touched_cycles+=1
        if p is not None and direction[i-1]==-1:
            # Closing stop uses the support line known BEFORE the bar opened.
            closing_breach=(hclose[i]<prev_support) or (direction[i]==1)
            if closing_breach:
                if end<len(op): # first open after confirmed 15m closing breach
                    trades.append(record(p,end,float(op[end]),"15m_close_stop",times))
                else:
                    trades.append(record(p,len(op)-1,float(cl[-1]),"data_end",times))
                p=None
        elif p is not None and direction[i-1]!=-1:
            raise AssertionError("Position remained open after bearish 15m state")
    if p is not None:
        trades.append(record(p,len(op)-1,float(cl[-1]),"data_end",times))
    return pd.DataFrame(trades), dict(eligible_bull_cycles=eligible_cycles,
                                    entered_cycles=touched_cycles)


def summarize(df, p):
    v=df.net_pts.to_numpy(float)
    positive=v[v>0]; nonpos=v[v<=0]
    eq=np.r_[0,np.cumsum(v)]
    gross=df.gross_pts.sum()
    return dict(tp_pct=p*100,trades=int(len(df)),
                wins=int(len(positive)), losses=int(len(nonpos)),
                win_rate_pct=round(100*len(positive)/len(df),2),
                target_hits=int((df.exit_reason=="target").sum()),
                close_stops=int((df.exit_reason=="15m_close_stop").sum()),
                gross_pts=round(float(gross),2),
                net_pts=round(float(v.sum()),2),
                avg_net_pts=round(float(v.mean()),2),
                avg_net_trade_return_pct=round(float(df.net_return_pct.mean()),4),
                fees_pts=round(float(df.fees_pts.sum()),2),
                slippage_pts=round(float(df.slippage_pts.sum()),2),
                profit_factor=round(float(positive.sum()/-nonpos.sum()),3)
                    if len(nonpos) else None,
                max_drawdown_pts=round(float(np.max(np.maximum.accumulate(eq)-eq)),2))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    minute, bars, files=load()
    line,direction=supertrend(bars)
    all_rows=[]; summary=[]; month_rows=[]; quality={}
    for tp in TP_PCTS:
        trades, q = replay(minute,bars,line,direction,tp)
        if trades.empty:
            raise ValueError(f"No trades generated for TP {tp}")
        trades["month_ist"]=pd.to_datetime(trades.exit_utc,utc=True).dt.tz_convert(
            "Asia/Kolkata").dt.strftime("%Y-%m")
        trades["period"]=np.where(trades.month_ist<"2026-01","2025_baseline",
             np.where(trades.month_ist<"2026-07","2026_H1_check",
               np.where(trades.month_ist<"2026-11","2026_H2_seen_recheck",
                        "2026_Nov_partial")))
        full=trades[trades.month_ist.isin(MONTHS)]
        summary.append(dict(scope="22_complete_months",**summarize(full,tp),**q))
        other=trades[trades.month_ist >= CUT]
        if len(other):
            summary.append(dict(scope="Nov_2026_partial",**summarize(other,tp),**q))
        for month in MONTHS + ["2026-11"]:
            sub=trades[trades.month_ist==month]
            month_rows.append(dict(tp_pct=tp*100,month_ist=month,
                         is_complete=month in MONTHS,
                         trades=int(len(sub)),wins=int((sub.net_pts>0).sum()),
                         net_pts=round(float(sub.net_pts.sum()),2),
                         gross_pts=round(float(sub.gross_pts.sum()),2)))
        all_rows.append(trades)
        print("TP",round(tp*100,2),"complete 22 months",
              json.dumps(summary[-2] if len(other) else summary[-1]))
    alltr=pd.concat(all_rows,ignore_index=True)
    summed=pd.DataFrame(summary)
    monthly=pd.DataFrame(month_rows)
    positive=(monthly[monthly.is_complete].groupby("tp_pct").net_pts
              .agg(["sum",lambda s:int((s>0).sum()),lambda s:int((s==0).sum())]))
    positive.columns=["sum_net_pts","positive_months","flat_months"]
    summed=summed.merge(positive,left_on="tp_pct",right_index=True,how="left")
    alltr.to_csv(OUT/"trade_ledger.csv.gz",index=False,compression="gzip")
    monthly.to_csv(OUT/"monthly_ist.csv",index=False)
    summed.to_csv(OUT/"summary.csv",index=False)
    quality=dict(instrument="Delta Exchange India BTCUSD perpetual futures",
       data_start_utc=str(minute.index.min()),data_end_utc=str(minute.index.max()),
       archive_months=len(files),observed_1m=len(minute),complete_15m=len(bars),
       minute_gaps=0,
       fixed_indicator="Supertrend Wilder ATR(10) multiplier 3; bullish cycle",
       entry="first 1m low touching previous completed bullish 15m ST line, one fill per cycle",
       tp_pct=[100*z for z in TP_PCTS],
       tp_execution="subsequent 1m high >= target, skip entry minute ambiguity",
       stop="15m close below previous completed bullish ST support or bearish flip; next 1m open",
       fee_rate_each_side=FEE,slippage_points_per_side=SLIP,
       monthly_assignment="IST month of exit",completed_months="2025-01 to 2026-10",
       incomplete_month="2026-11 excluded from headline",
       limits=["One BTC-equivalent price-unit ledger, not leveraged account equity",
               "Monthly PNL assigned on exit; not unrealized MTM",
               "No book spread, maker queue or funding charges",
               "Same-minute TP ignored on entry; conservative but cannot reconstruct ticks",
               "All periods previously used in research; no untouched holdout",
               "Five target variants compared with correlated trades"])
    (OUT/"quality.json").write_text(json.dumps(quality,indent=2)+"\n")
    display = summed[summed.scope=="22_complete_months"]
    cols=["tp_pct","trades","wins","losses","win_rate_pct","target_hits",
          "close_stops","gross_pts","net_pts","profit_factor","max_drawdown_pts",
          "positive_months","flat_months"]
    report=["# BTCUSD 15m bullish Supertrend line-touch — 1m execution replay",
       "", "## Net outcomes, 22 complete IST months Jan 2025–Oct 2026",
       display[cols].to_markdown(index=False),"",
       "## Monthly net BTC price points by take-profit target (IST exit month)",
       monthly.pivot(index="month_ist",columns="tp_pct",values="net_pts").to_markdown(),
       "", "## Execution / limitations",
       "See NOVELTY_CHECK.md and quality.json. Gross/net are 1 BTC-equivalent PRICE POINTS,",
       "not leverage-adjusted dollar account P&L. Costs: 0.05% taker/side + 18% GST,",
       "5 USD adverse slippage/side; funding and book depth omitted.",
       "A bearish closing candle can touch the prior bullish support and fill a resting",
       "order before the close stop is observed. That trade exits at next-minute open.",
       "No same-minute entry/TP ordering credit. 2026 is not untouched holdout.",
       "November 2026 excluded from the complete-month score."]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")
    print("SUMMARY_22_MONTHS")
    print(display[cols].to_string(index=False))
    print("POSITIVE_MONTHS",positive.to_string())
    print("COVERAGE",json.dumps(quality,indent=2))
    print("MONTHLY_IS_T",monthly.pivot(index="month_ist",columns="tp_pct",
                                         values="net_pts").to_string())

if __name__=="__main__":
    main()
