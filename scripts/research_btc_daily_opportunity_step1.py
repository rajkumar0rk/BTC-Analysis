#!/usr/bin/env python3
"""STEP 1 ONLY: price-path opportunities for +0.2% net-account BTCUSD days.

NO signal, NO direction prediction, NO stop, and NO trades. All observed maxima
and minima are ex-post oracle opportunities, NOT investable performance.
Use every complete IST weekday and 24 preselected clock anchors, not cherry picks.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

SOURCE = Path("data/delta_india/BTCUSD/1m")
OUT = Path("analysis/btc_daily_opportunity_step1")
MONTHS = pd.period_range("2025-01", "2026-10", freq="M").astype(str).tolist()
START, END = "2025-01-02", "2026-10-30"
TZ = "Asia/Kolkata"
FEE = 0.0005 * 1.18
SLIP = 5.0
GOAL = 0.002
GROSS_THRESHOLDS = (0.27, 0.35, 0.50)
RANGE_THRESHOLDS = (0.2, 0.27, 0.35, 0.5, 1.0, 2.0)
HORIZONS = ("30m", "120m", "eod")
PRESET_HOURS = (9, 12, 15, 18, 21)


def load():
    parts = []
    for month in MONTHS:
        p = SOURCE / (month + ".csv.gz")
        if not p.exists():
            raise FileNotFoundError(p)
        d = pd.read_csv(p, compression="gzip",
                        usecols=["time", "open", "high", "low", "close", "volume"])
        d["time"] = pd.to_datetime(d.time.astype("int64"), unit="s", utc=True)
        parts.append(d)
    m = pd.concat(parts, ignore_index=True).set_index("time").sort_index()
    if len(m) < 900000:
        raise RuntimeError("Historical dataset unexpectedly short")
    if not m.index.is_unique or m.isna().any().any():
        raise ValueError("Null/duplicate 1-minute candles")
    if not m.index.to_series().diff().iloc[1:].eq(pd.Timedelta(minutes=1)).all():
        raise ValueError("Minute discontinuity: cannot invent candles")
    if ((m.low <= 0) | (m.volume < 0) |
        (m.high < m[["open", "low", "close"]].max(axis=1)) |
        (m.low > m[["open", "high", "close"]].min(axis=1))).any():
        raise ValueError("Bad OHLCV input")
    if m.index[0] != pd.Timestamp("2025-01-01T00:00:00Z"):
        raise AssertionError("First archive timestamp changed")
    if m.index[-1] != pd.Timestamp("2026-10-31T23:59:00Z"):
        raise AssertionError("Last archive timestamp changed")
    return m


def required_mid_exit(open_mid):
    """Side-specific price levels to NET +0.2% of entry notional.

    Net return uses entry adverse fill as capital base, 1x notional.
    Fee on exit uses actual exit fill, not the entry price, for standard.
    """
    long_entry = open_mid + SLIP
    short_entry = open_mid - SLIP
    if short_entry <= 0:
        raise ValueError("Invalid entry for short")
    offer_long = long_entry * (1 + FEE + GOAL) + SLIP
    offer_short = short_entry * (1 - FEE - GOAL) - SLIP
    standard_long = long_entry * (1 + FEE + GOAL) / (1 - FEE) + SLIP
    standard_short = short_entry * (1 - FEE - GOAL) / (1 + FEE) - SLIP
    return {
        "offer_long": offer_long,
        "offer_short": offer_short,
        "standard_long": standard_long,
        "standard_short": standard_short,
    }


def daily_and_fixed_clock(m):
    open_price = m.open.to_numpy(dtype=float)
    high = m.high.to_numpy(dtype=float)
    low = m.low.to_numpy(dtype=float)
    close = m.close.to_numpy(dtype=float)
    days = pd.date_range(START, END, freq="B", tz=TZ)
    expected_days = len(days)
    day_rows, clock_rows = [], []

    for day in days:
        ds = day.strftime("%Y-%m-%d")
        start_i = int(m.index.get_indexer([day.tz_convert("UTC")])[0])
        last_i = int(m.index.get_indexer([(day + pd.Timedelta(minutes=1439)).tz_convert("UTC")])[0])
        if start_i < 0 or last_i < 0 or last_i - start_i != 1439:
            raise AssertionError("Incomplete IST calendar day " + ds)
        price0 = float(open_price[start_i])
        dayhigh = float(high[start_i:last_i+1].max())
        daylow = float(low[start_i:last_i+1].min())
        price_close = float(close[last_i])
        drange = 100.0 * (dayhigh - daylow) / price0
        abs_openclose = 100.0 * abs(price_close - price0) / price0
        entry = dict(day_ist=ds, year=int(day.year), weekday=day.day_name(),
                     open_btcusd=price0, daily_high=dayhigh, daily_low=daylow,
                     daily_close=price_close, daily_range_pct=drange,
                     daily_open_close_abs_pct=abs_openclose)
        for threshold in RANGE_THRESHOLDS:
            entry["range_ge_"+str(threshold).replace(".", "p")] = bool(drange >= threshold)
        day_rows.append(entry)

        for hour in range(24):
            i = start_i + 60 * hour
            mid = float(open_price[i])
            needs = required_mid_exit(mid)
            full30hi = float(high[i:i+30].max())
            full30lo = float(low[i:i+30].min())
            if i + 29 > last_i:
                raise AssertionError("Incomplete 30 minute anchor " + ds)
            for horizon in HORIZONS:
                if horizon == "120m" and i + 119 > last_i:
                    continue
                right = (i + 30 if horizon == "30m" else
                         i + 120 if horizon == "120m" else last_i+1)
                max_future = float(high[i:right].max())
                min_future = float(low[i:right].min())
                long_mfe = 100.0*(max_future - mid)/mid
                short_mfe = 100.0*(mid - min_future)/mid
                std_long = bool(max_future >= needs["standard_long"])
                std_short = bool(min_future <= needs["standard_short"])
                offer_long30 = bool(full30hi >= needs["offer_long"])
                offer_short30 = bool(full30lo <= needs["offer_short"])
                if right > i + 30:
                    later_high = float(high[i+30:right].max())
                    later_low = float(low[i+30:right].min())
                    late_std_long = bool(later_high >= needs["standard_long"])
                    late_std_short = bool(later_low <= needs["standard_short"])
                else:
                    late_std_long = False
                    late_std_short = False
                possible_long = offer_long30 or late_std_long
                possible_short = offer_short30 or late_std_short
                row = dict(
                    day_ist=ds, year=int(day.year), hour_ist=hour,
                    horizon=horizon, entry_btcusd=mid,
                    max_future_high=max_future, min_future_low=min_future,
                    gross_long_mfe_pct=long_mfe, gross_short_mfe_pct=short_mfe,
                    standard_long_possible=std_long,
                    standard_short_possible=std_short,
                    standard_either_possible=std_long or std_short,
                    offer_30m_long_possible=offer_long30,
                    offer_30m_short_possible=offer_short30,
                    offer_30m_either_possible=offer_long30 or offer_short30,
                    offer_path_long_possible=possible_long,
                    offer_path_short_possible=possible_short,
                    offer_path_either_possible=possible_long or possible_short,
                    offer_long_required_pct=100.0*(needs["offer_long"]-mid)/mid,
                    offer_short_required_pct=100.0*(mid-needs["offer_short"])/mid,
                    standard_long_required_pct=100.0*(needs["standard_long"]-mid)/mid,
                    standard_short_required_pct=100.0*(mid-needs["standard_short"])/mid,
                )
                for threshold in GROSS_THRESHOLDS:
                    t = str(threshold).replace(".", "p")
                    lng = bool(long_mfe >= threshold)
                    sht = bool(short_mfe >= threshold)
                    row[f"gross_long_ge_{t}"] = lng
                    row[f"gross_short_ge_{t}"] = sht
                    row[f"gross_either_ge_{t}"] = lng or sht
                clock_rows.append(row)

    daily = pd.DataFrame(day_rows)
    clock = pd.DataFrame(clock_rows)
    assert len(daily) == expected_days
    assert daily.day_ist.is_unique
    assert daily.day_ist.min() == START and daily.day_ist.max() == END
    assert set(clock.hour_ist) == set(range(24))
    assert (clock[clock.horizon=="30m"].groupby("day_ist").size()==24).all()
    assert (clock[clock.horizon=="120m"].groupby("day_ist").size()==23).all()
    assert (clock[clock.horizon=="eod"].groupby("day_ist").size()==24).all()
    assert (clock.offer_path_either_possible | ~clock.standard_either_possible).all()
    return daily, clock


def daily_summary(daily):
    r = {}
    for period, d in [("all",daily),
                      ("2025",daily[daily.year==2025]),
                      ("2026_jan_oct",daily[daily.year==2026])]:
        x = dict(days=int(len(d)),
                 mean_day_range_pct=round(float(d.daily_range_pct.mean()),4),
                 median_day_range_pct=round(float(d.daily_range_pct.median()),4),
                 p10_day_range_pct=round(float(d.daily_range_pct.quantile(.10)),4),
                 p90_day_range_pct=round(float(d.daily_range_pct.quantile(.90)),4),
                 mean_abs_open_close_pct=round(float(d.daily_open_close_abs_pct.mean()),4),
                 median_abs_open_close_pct=round(float(d.daily_open_close_abs_pct.median()),4))
        for t in RANGE_THRESHOLDS:
            key="range_ge_"+str(t).replace(".","p")
            x[key+"_days"]=int(d[key].sum())
            x[key+"_pct"]=round(float(100.0*d[key].mean()),2)
        r[period]=x
    return r


def group_clock(clock):
    records=[]
    for period,d in [("all",clock),
                     ("2025",clock[clock.year==2025]),
                     ("2026_jan_oct",clock[clock.year==2026])]:
        for (hour,horizon),z in d.groupby(["hour_ist","horizon"],sort=True):
            result=dict(period=period,hour_ist=int(hour),horizon=horizon,n_days=int(len(z)),
                gross_long_mfe_median_pct=round(float(z.gross_long_mfe_pct.median()),5),
                gross_short_mfe_median_pct=round(float(z.gross_short_mfe_pct.median()),5))
            for field in ["standard_long_possible","standard_short_possible",
                          "standard_either_possible","offer_30m_long_possible",
                          "offer_30m_short_possible","offer_30m_either_possible",
                          "offer_path_long_possible","offer_path_short_possible",
                          "offer_path_either_possible"]:
                result[field+"_days"]=int(z[field].sum())
                result[field+"_pct"]=round(float(100.0*z[field].mean()),3)
            for t in GROSS_THRESHOLDS:
                key="gross_either_ge_"+str(t).replace(".","p")
                result[key+"_days"]=int(z[key].sum())
                result[key+"_pct"]=round(float(100.0*z[key].mean()),3)
            records.append(result)
    return pd.DataFrame(records)


def run():
    OUT.mkdir(parents=True,exist_ok=True)
    m=load()
    daily,clock=daily_and_fixed_clock(m)
    ds=daily_summary(daily)
    grouped=group_clock(clock)
    # Five locked clocks; annual and horizon results for convenient inspection.
    rows=[]
    for period in ("all","2025","2026_jan_oct"):
        for horizon in HORIZONS:
            for hour in PRESET_HOURS:
                z=grouped[(grouped.period==period)&
                          (grouped.hour_ist==hour)&(grouped.horizon==horizon)]
                if len(z)!=1:raise AssertionError("Missing comparison group")
                a=z.iloc[0]
                rows.append(dict(period=period,horizon=horizon,hour_ist=hour,
                   days=int(a.n_days),
                   gross_0p27_either_pct=float(a.gross_either_ge_0p27_pct),
                   gross_0p35_either_pct=float(a.gross_either_ge_0p35_pct),
                   gross_0p5_either_pct=float(a.gross_either_ge_0p5_pct),
                   long_offer_or_standard_pct=float(a.offer_path_long_possible_pct),
                   short_offer_or_standard_pct=float(a.offer_path_short_possible_pct),
                   either_offer_or_standard_pct=float(a.offer_path_either_possible_pct),
                   standard_either_pct=float(a.standard_either_possible_pct)))
    fixed=pd.DataFrame(rows)

    top={}
    for horizon in HORIZONS:
        a=grouped[(grouped.period=="2025")&(grouped.horizon==horizon)].sort_values(
            ["offer_path_either_possible_pct","hour_ist"],ascending=[False,True])
        best=a.head(5)
        hist=[]
        for _,b in best.iterrows():
            check=grouped[(grouped.period=="2026_jan_oct")&
                          (grouped.horizon==horizon)&(grouped.hour_ist==b.hour_ist)].iloc[0]
            hist.append(dict(hour_ist=int(b.hour_ist),eligible_days_2025=int(b.n_days),
               opportunity_2025_pct=float(b.offer_path_either_possible_pct),
               eligible_days_2026=int(check.n_days),
               opportunity_2026_pct=float(check.offer_path_either_possible_pct),
               long_only_2025_pct=float(b.offer_path_long_possible_pct),
               short_only_2025_pct=float(b.offer_path_short_possible_pct)))
        top[horizon]=hist

    daily.to_csv(OUT/"complete_weekday_ranges.csv",index=False)
    clock.to_csv(OUT/"fixed_hour_price_opportunities.csv.gz",index=False,compression="gzip")
    grouped.to_csv(OUT/"all_hours_2025_2026.csv",index=False)
    fixed.to_csv(OUT/"fixed_9_12_15_18_21_anchors.csv",index=False)
    summary={"step":"1 of 5: no strategy or trades, ex-post maximum opportunity only",
             "source":"Delta Exchange India BTCUSD perpetual 1-minute authentic archive",
             "archive_start":str(m.index[0]),"archive_end":str(m.index[-1]),
             "archive_candles":int(len(m)),
             "full_ist_weekdays":len(daily),
             "daily_range":ds,
             "prespecified_fixed_hours_ist":list(PRESET_HOURS),
             "fixed_hour_summary":fixed.to_dict(orient="records"),
             "top_five_2025_oracle_hours_with_2026_reference":top,
             "cost_assumptions":{"notional_exposure":"1.0x account, unleveraged",
                 "taker_fee_per_side":0.0005,"gst_on_fees":0.18,
                 "slippage_per_side_btc_points":SLIP,
                 "offer":"hypothetically opt-in before entry, zero close fee within 30m only",
                 "target_net_account_return":GOAL},
             "methodological_warnings":[
                 "These are future high-low oracle bounds: direction and exact exit price known only after the fact.",
                 "Both-side/either outcome is not a tradable win rate; only one side can be entered.",
                 "No stop-loss, adverse excursion, stop-before-target, tick path, actual fills or order book modeled.",
                 "15-minute and 30-minute offer classification cannot be exact from only 1-minute candles.",
                 "2026 is already researched, not a pristine independent test.",
                 "Funding/liquidation/position caps not modeled; this is not an account performance backtest."]}
    (OUT/"summary.json").write_text(json.dumps(summary,indent=2)+"\n")
    report=["# Step 1 — BTCUSD daily price opportunity, not an executable strategy",
            "",
            "**Study:** 2025-01-02 to 2026-10-30, all full IST Monday–Friday sessions, no weekend signals; exact 1m archive validated as continuous.",
            "**At a fixed hour**, entry at that minute OPEN and future high/low across selected horizon. Long and short tested separately, and 'either' uses an **omniscient direction choice**. All tables are opportunity upper bounds; actual live hit rates will be lower.",
            "**Net-account +0.2%:** 1x account notional, taker 0.05%/side, GST 18% on fees and 5 BTC quote points adverse slippage per side. Hypothetical regular Scalper Offer waives the exit taker fee only for <=30m hold, opt-in assumed. For longer horizons the early 30m offer OR later double-sided standard fee is tested.",
            "",
            "## Daily high-low ranges",
            "",
            pd.DataFrame.from_dict(ds,orient="index").to_markdown(),
            "",
            "## Fixed preselected IST entry hours: ex-post 'either direction' prices",
            "",
            fixed.to_markdown(index=False),
            "",
            "## 2025 top fixed clock hours, with 2026 historical check",
            ""]
    for horizon, rows in top.items():
        report.extend([f"### {horizon}","",pd.DataFrame(rows).to_markdown(index=False),""])
    report.extend(["## Caveats","","No direction predictor, no stop-first test, no account returns, no actual fills. Selecting the best hour retrospectively would introduce overfitting. Step 2 should measure stop-first using these locked clocks without changing the past.",""])
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report))
    print("STEP1_DAILY "+json.dumps(ds,sort_keys=True),flush=True)
    print("STEP1_FIXED "+fixed.to_string(index=False),flush=True)
    print("STEP1_TOP "+json.dumps(top,sort_keys=True),flush=True)
    print("STEP1_DONE",flush=True)


if __name__=="__main__":
    run()
