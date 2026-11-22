#!/usr/bin/env python3
"""Reproduce month-level trade-level results from percentage-grid engine.

BTCUSD 15m Supertrend(10,3), GREEN second 15m after first line touch,
market long at next 15m open, volume>=1x and ATR%>=0.2% prior closed.
1.0% SL and 1.5% TP as percent of entry fill, 1m stop-first, 15m
close-stop. Audit .4% SL/1.5% TP and flip 1%/1.5% comparators.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd

import research_supertrend_15m_line_touch as base
import research_supertrend_15m_filter_grid as f
import research_supertrend_15m_profit_protection as protect
import research_supertrend_15m_second_green as green
import research_second_green_percent_grid as percent

OUT=Path("analysis/second_green_percentage_grid_20261122/monthly_audit")
SCENARIOS=[
    ("line_touch_sl1_tp1p5","after_line_touch",1.0,1.5,108,8822.33,37),
    ("line_touch_sl0p4_tp1p5","after_line_touch",0.4,1.5,108,3740.0,None),
    ("bullish_flip_sl1_tp1p5","after_bullish_flip",1.0,1.5,197,None,None),
]
MONTHS=base.MONTHS

def run_one(kind,entries,sl, tp, stopbars,minute,months_by_min):
    high=minute.high.to_numpy(float)
    low=minute.low.to_numpy(float)
    opening=minute.open.to_numpy(float)
    close=minute.close.to_numpy(float)
    n=len(high)
    sl_index=percent.SL_PCT.index(sl)
    tp_index=percent.TP_PCT.index(tp)
    rec=[]
    for cycle,bar,j,mid,line in entries:
        month=str(months_by_min[j])
        if month not in MONTHS:
            continue
        sidx=np.searchsorted(stopbars,bar,side="left")
        sb=int(stopbars[sidx]) if sidx<len(stopbars) else -1
        end=min((sb+1)*15,n) if sb>=0 else n
        emid,ex,reasons,ambiguity=percent.market_ohlc_precompute(
            mid,j,end,high,low,opening,close)
        exitmid=float(emid[sl_index,tp_index])
        exitidx=int(ex[sl_index,tp_index])
        why=int(reasons[sl_index,tp_index])
        fill=mid+percent.FILL_SLIP
        exit_fill=exitmid-percent.FILL_SLIP
        fee=percent.FEE*(fill+exit_fill)
        net=exit_fill-fill-fee
        rec.append(dict(
            scenario=kind,cycle=cycle,
            entry_utc=str(minute.index[j]),
            exit_utc=str(minute.index[exitidx]),
            month_ist=month,
            entry_mid=round(float(mid),5),
            entry_fill=round(float(fill),5),
            exit_mid=round(exitmid,5),
            exit_fill=round(float(exit_fill),5),
            sl_pct=sl,tp_pct=tp,
            exit_reason={1:"hard_sl",2:"fixed_tp",3:"15m_st_close",4:"archive_end"}[why],
            simultaneous_ohlc_collision=int(ambiguity[sl_index,tp_index]),
            fee_gst_pts=round(float(fee),6),
            net_pts=round(float(net),6),
            net_winner=int(net>0),
            duration_minutes=exitidx-j))
    return pd.DataFrame(rec)

def monthly_summary(t,kind):
    grouped=t.groupby("month_ist").agg(
        trades=("net_pts","count"),
        winners=("net_winner","sum"),
        gross_net_pts=("net_pts","sum"),
        sl_exits=("exit_reason",lambda x:int((x=="hard_sl").sum())),
        tp_exits=("exit_reason",lambda x:int((x=="fixed_tp").sum())),
        st_exits=("exit_reason",lambda x:int((x=="15m_st_close").sum())),
        collision_count=("simultaneous_ohlc_collision","sum"))
    month=[]
    cum=0.
    for mo in MONTHS:
        if mo in grouped.index:
            a=grouped.loc[mo]
            tr=int(a.trades); wi=int(a.winners)
            v=float(a.gross_net_pts)
            sl=int(a.sl_exits); tp=int(a.tp_exits); st=int(a.st_exits)
            amb=int(a.collision_count)
        else:
            tr=wi=sl=tp=st=amb=0
            v=0.0
        cum+=v
        month.append(dict(scenario=kind,month_ist=mo,
            trades=tr,winning_trades=wi,losing_trades=tr-wi,
            win_rate_pct=round(wi*100/tr,2) if tr else None,
            net_pts=round(v,2),cumulative_net_pts=round(cum,2),
            tp_exits=tp,hard_sl_exits=sl,st_close_exits=st,
            ambiguous_1m_collisions=amb))
    return pd.DataFrame(month)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    minute,bar15,files=base.load()
    st,trend=base.supertrend(bar15)
    vol,atrpct,atrrel=f.build_features(bar15)
    events,stopbars=f.candidate_touch_events(
        minute,bar15,st,trend,vol,atrpct,atrrel)
    v=f.VOLUME["vol_ge_1p0"];atr=f.VOLATILITY["atrpct_ge_0p20"]
    touch=protect.select_events(events,v,atr)
    opening=minute.open.to_numpy(float)
    green_touch=green.after_touch_green(
        touch,bar15,trend,stopbars,opening)
    green_flip=green.after_flip_green(
        bar15,trend,vol,atrpct,atrrel,v,atr,stopbars,opening)
    monthids=minute.index.tz_convert("Asia/Kolkata").strftime("%Y-%m").to_numpy()
    result=[];ledger=[];headline=[]
    for name,kind,sl,tp,expected_n,expected_net,expected_winners in SCENARIOS:
        t=run_one(name,green_touch if kind=="after_line_touch" else green_flip,
                  sl,tp,stopbars,minute,monthids)
        assert len(t)==expected_n,(name,len(t),expected_n)
        if expected_net is not None and name=="line_touch_sl1_tp1p5":
            assert abs(t.net_pts.sum()-expected_net)<.1,(name,float(t.net_pts.sum()))
        if expected_winners is not None:
            assert int(t.net_winner.sum())==expected_winners
        m=monthly_summary(t,name)
        assert len(m)==22
        assert abs(m.net_pts.sum()-t.net_pts.sum())<0.12,(
            name,m.net_pts.sum(),t.net_pts.sum())
        assert int(m.trades.sum())==len(t)
        assert int(m.winning_trades.sum())==int(t.net_winner.sum())
        year2025=m.iloc[:12]
        year2026=m.iloc[12:]
        headline.append(dict(scenario=name,
           trades=len(t),winners=int(t.net_winner.sum()),
           winrate_pct=round(100*t.net_winner.mean(),2),
           positive_months=int((m.net_pts>0).sum()),
           losing_months=int((m.net_pts<0).sum()),
           total_net_pts=round(float(t.net_pts.sum()),2),
           net_pts_2025=round(float(year2025.net_pts.sum()),2),
           net_pts_2026=round(float(year2026.net_pts.sum()),2),
           highest_month=str(m.loc[m.net_pts.idxmax(),"month_ist"]),
           highest_month_pts=round(float(m.net_pts.max()),2),
           worst_month=str(m.loc[m.net_pts.idxmin(),"month_ist"]),
           worst_month_pts=round(float(m.net_pts.min()),2)))
        ledger.append(t); result.append(m)

    allm=pd.concat(result,ignore_index=True)
    alltr=pd.concat(ledger,ignore_index=True)
    checks=pd.DataFrame(headline)
    allm.to_csv(OUT/"monthly_22months_three_scenarios.csv",index=False)
    allm[allm.scenario=="line_touch_sl1_tp1p5"].to_csv(
        OUT/"primary_monthly_1pct_SL_1p5pct_TP.csv",index=False)
    alltr.to_csv(OUT/"trade_ledger_all_three_scenarios.csv.gz",
                 index=False,compression="gzip")
    checks.to_csv(OUT/"headline.csv",index=False)
    primary=allm[allm.scenario=="line_touch_sl1_tp1p5"].copy()
    report=[
        "# Monthly BTCUSD results — green-after-touch, 1% SL / 1.5% TP",
        "",
        "January 2025–October 2026, 22 completed IST entry months.",
        "Volume >= 1x and ATR(14) >= 0.20% of 15m price; ST10x3.",
        "Long entered on the THIRD 15m bar OPEN after first bullish",
        "line-touch candle and next bullish GREEN confirmation candle.",
        "Take profit +1.5% of simulated market fill, hard SL -1.0%,",
        "secondary 15m Supertrend closing-stop, next 1m open,",
        "1m high/low replay with hard-stop-first OHLC collision.",
        "Estimated 0.05% taker each side, GST 18% on fees,",
        "5 BTC points adverse slippage each side. No funding or liquidation.",
        "1BTC-equivalent BTC price-point P&L (NOT account dollar profit).",
        "",
        "## Primary configuration (by IST ENTRY month)",
        primary[["month_ist","trades","winning_trades",
                 "losing_trades","win_rate_pct","net_pts",
                 "cumulative_net_pts","tp_exits","hard_sl_exits",
                 "st_close_exits"]].to_markdown(index=False),"",
        "## Reconciliation and alternative configurations",
        checks.to_markdown(index=False),"",
        "## Method and limitations",
        "- Month attribution is by entry timestamp in Asia/Kolkata.",
        "- Metrics are historical; 2025 and 2026 not fresh OOS.",
        "- In same-minute TP/SL collision, SL is treated as first.",
        "- Same-minute favorable target at market open may be counted;",
        "  third candle open entry can happen before that 1m high.",
        "- No exchange funding, bid/ask, order book or actual maker/taker fill uncertainty.",
        "- P&L is raw 1BTC-equivalent price-point units, not capital return."]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")
    (OUT/"quality.json").write_text(json.dumps(dict(
        run="monthly 1percent SL 1.5percent TP from original percentage grid",
        source="Delta India 993600 1m candles",
        min_bars=66240, months=MONTHS,
        parity_primary_total="8822.33 net pts, 108 trades, 37 winners",
        scenarios=checks.to_dict("records"),
        limits="1m OHLC stop-first, no funding/margin/liquidation"),indent=2)+"\n")
    print("RECONCILED",checks.to_string(index=False),flush=True)
    print("PRIMARY_22_MONTHS\n"+primary.to_string(index=False),flush=True)
    print("DONE",OUT/"RESEARCH_REPORT.md",flush=True)

if __name__=="__main__":main()
