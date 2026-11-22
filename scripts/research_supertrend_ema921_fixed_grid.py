#!/usr/bin/env python3
"""Pre-registered fixed-exit robustness grid for Supertrend EMA9/21 BTCUSD.

See analysis/supertrend_ema921_fixed_grid/NOVELTY_CHECK.md.
Same signals and execution as previous Supertrend 100SL/200TP baseline.
"""
from __future__ import annotations
import calendar
import json
from pathlib import Path
import numpy as np
import pandas as pd
from numba import njit
from research_supertrend_ema921 import source, minute_alignment, FEE, SLIP, MONTHS, IST

OUT = Path("analysis/supertrend_ema921_fixed_grid")
STOPS = (100, 200, 300, 500, 800, 1000)
TARGETS = (100, 200, 300, 500, 800, 1000, 1500, 2000, 3000)
TFS = (5, 15, 60)
BASELINE = {
    5: (6922, 2173, -99.98809589106729),
    15: (2254, 724, -94.36815744901256),
    60: (556, 171, -52.96172102470196),
}
START_MONTH = 2025*12 + 1

@njit(cache=True)
def simulate(op, high, low, close, months, events, directions, sl_pts, tp_pts):
    """First-touch actual 1m OHLC, entry next open, stop-priority same-bar tie.

    Event positions precomputed ONLY from fully closed higher-timeframe
    candles by minute_alignment. Returns one result per actual closed trade.
    """
    cap=len(events); n=len(op)
    entry_i=np.empty(cap, dtype=np.int32)
    exit_i=np.empty(cap, dtype=np.int32)
    sides=np.empty(cap, dtype=np.int8)
    exits=np.empty(cap, dtype=np.int8)  # 0 stop,1 tp,2 stop_gap,3 stop_and_target,4 month,5 edge
    gross=np.empty(cap, dtype=np.float64)
    fees=np.empty(cap, dtype=np.float64)
    net=np.empty(cap, dtype=np.float64)
    ret=np.empty(cap, dtype=np.float64)
    count=0; last_exit=-1
    for u in range(cap):
        k=events[u]
        if k <= last_exit:
            continue
        side=directions[u]
        entry=float(op[k]); entry_fill=entry+side*SLIP
        stop=entry_fill-side*sl_pts
        target=entry_fill+side*tp_pts
        j=k
        while True:
            stop_gap = (op[j] <= stop if side==1 else op[j] >= stop)
            stop_hit = (low[j] <= stop if side==1 else high[j] >= stop)
            tp_hit = (high[j] >= target if side==1 else low[j] <= target)
            if stop_gap:
                mid=op[j]; why=2
                break
            if stop_hit:
                mid=stop; why=3 if tp_hit else 0
                break
            if tp_hit:
                mid=target; why=1
                break
            if j + 1 == n:
                mid=close[j]; why=5
                break
            if months[j+1] != months[j]:
                mid=close[j]; why=4
                break
            j+=1
        exit_fill=mid-side*SLIP
        cost=FEE*(entry_fill+exit_fill)
        pnl=side*(exit_fill-entry_fill)-cost
        entry_i[count]=k; exit_i[count]=j
        sides[count]=side; exits[count]=why
        gross[count]=side*(mid-entry); fees[count]=cost
        net[count]=pnl; ret[count]=100*pnl/entry_fill
        count+=1
        last_exit=j
    return (entry_i[:count], exit_i[:count], sides[:count], exits[:count],
            gross[:count], fees[:count], net[:count], ret[:count])

def scoring(result, monthcodes, tf, stop, target):
    entry_i,exit_i,side,why,gross,fees,net,pct=result
    case=dict(timeframe=f"{tf}m",sl_points=stop,tp_points=target)
    win=net>0
    equity=np.cumprod(np.r_[1., 1.+pct/100.])
    hi=np.maximum.accumulate(equity)
    maxdd=float(np.max(100*(1-equity/hi)))
    gain=float(net[win].sum()); loss=float(-net[~win].sum())
    month_idx=monthcodes[exit_i]-START_MONTH
    monthrows=[]
    for im,m in enumerate(MONTHS):
        hits=np.flatnonzero(month_idx==im)
        pcts=pct[hits]
        mret=float(100*(np.prod(1+pcts/100)-1))
        monthrows.append({**case,"month_ist":m,
            "trades":int(len(hits)), "wins":int(win[hits].sum()),
            "losses":int(len(hits)-win[hits].sum()),
            "net_1x_account_return_pct":mret})
    returns=np.array([r["net_1x_account_return_pct"] for r in monthrows])
    s={**case, "trades":len(net), "wins":int(win.sum()), "losses":int((~win).sum()),
       "win_rate_pct":float(100*win.mean()) if len(win) else 0.,
       "targets_hit":int((why==1).sum()), "stop_exits":int(((why==0)|(why==2)|(why==3)).sum()),
       "month_flat_exits":int((why==4).sum()),
       "gross_points_per_btc":float(gross.sum()),
       "fees_gst_per_btc":float(fees.sum()), "slippage_points_per_btc":float(len(net)*2*SLIP),
       "net_points_per_btc":float(net.sum()),
       "profit_factor":gain/loss if loss else None,
       "total_net_1x_account_return_pct":float(100*(equity[-1]-1)),
       "max_trade_close_drawdown_pct":maxdd,
       "positive_months_22":int((returns>0).sum()),
       "negative_months_22":int((returns<0).sum()),
       "positive_2025":int((returns[:12]>0).sum()),
       "positive_2026_JanOct":int((returns[12:]>0).sum()),
       "worst_month_return_pct":float(returns.min()),
       "best_month_return_pct":float(returns.max()),
       "months_ge_10pct":int((returns>=10).sum()),
       "2025_net_1x_return_pct":float(100*(np.prod(1+returns[:12]/100)-1)),
       "2026_JanOct_net_1x_return_pct":float(100*(np.prod(1+returns[12:]/100)-1))}
    return s,monthrows,case

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    raw,gaps=source()
    if gaps:raise RuntimeError(f"Missing source minute(s): {gaps[:5]}")
    obs=raw.index.tz_convert(IST)
    months=np.asarray(obs.year,dtype=np.int32)*12 + np.asarray(obs.month,dtype=np.int32)
    monthnames=pd.Series(1,index=obs).groupby(obs.strftime("%Y-%m")).count()
    coverage={}
    for m in MONTHS:
        y,mo=map(int,m.split("-"))
        expected=calendar.monthrange(y,mo)[1]*1440
        actual=int(monthnames.get(m,0))
        coverage[m]={"expected":expected,"observed":actual,"complete":actual==expected}
    op=raw.open.to_numpy(float)
    hi=raw.high.to_numpy(float)
    lo=raw.low.to_numpy(float)
    cl=raw.close.to_numpy(float)
    summaries=[]; monthly=[]; ledgers=[]
    signal_stats={}
    for tf in TFS:
        sig,stats=minute_alignment(raw,tf)
        signal_stats[str(tf)]=stats
        previous=np.r_[0,sig[:-1]]
        ev=np.flatnonzero((sig!=0)&(sig!=previous)).astype(np.int32)
        sides=sig[ev].astype(np.int8)
        print(f"TF={tf} events={len(ev)}",flush=True)
        for stop in STOPS:
            for target in TARGETS:
                trade=simulate(op,hi,lo,cl,months,ev,sides,float(stop),float(target))
                score,mo,case=scoring(trade,months,tf,stop,target)
                summaries.append(score);monthly.extend(mo)
                ei,xi,sd,why,gross,fees,net,pct=trade
                ledger=pd.DataFrame({**{k:v for k,v in case.items()},
                    "entry_ist":raw.index[ei].tz_convert(IST).astype(str),
                    "exit_ist":raw.index[xi].tz_convert(IST).astype(str),
                    "month_ist":[MONTHS[int(i)] for i in months[xi]-START_MONTH],
                    "side":np.where(sd==1,"LONG","SHORT"),
                    "exit_reason":np.array(["stop","target","stop_gap",
                       "stop_first_both","month_flat","end_of_data"])[why],
                    "gross_points_per_btc":np.round(gross,4),
                    "fees_gst_per_btc":np.round(fees,4),
                    "net_points_per_btc":np.round(net,4),
                    "net_trade_1x_return_pct":pct,
                    "entry_index":ei,"exit_index":xi})
                ledgers.append(ledger)
                print(f"RESULT tf={tf} SL={stop} TP={target} wins={score['wins']}/{score['trades']} months_positive={score['positive_months_22']}/22 return={score['total_net_1x_account_return_pct']:.4f}%",flush=True)
        base=[x for x in summaries if x["timeframe"]==f"{tf}m"
              and x["sl_points"]==100 and x["tp_points"]==200][0]
        expected_trades,expected_wins,expected_return=BASELINE[tf]
        assert base["trades"]==expected_trades, (tf,base["trades"],expected_trades)
        assert base["wins"]==expected_wins, (tf,base["wins"],expected_wins)
        assert abs(base["total_net_1x_account_return_pct"]-expected_return)<0.000001, (
            tf,base["total_net_1x_account_return_pct"],expected_return)
        print(f"BASELINE PARITY PASSED {tf}m",flush=True)
    sm=pd.DataFrame(summaries)
    mo=pd.DataFrame(monthly)
    sm.to_csv(OUT/"summary.csv",index=False)
    mo.to_csv(OUT/"monthly_results.csv",index=False)
    pd.concat(ledgers,ignore_index=True).to_csv(OUT/"trade_ledger.csv.gz",
                                              compression="gzip",index=False)
    top_profit=sm.sort_values(["total_net_1x_account_return_pct",
                               "positive_months_22"],ascending=False)
    top_consistency=sm.sort_values(["positive_months_22","total_net_1x_account_return_pct"],
                                   ascending=False)
    top_profit.head(25).to_csv(OUT/"top_by_return.csv",index=False)
    top_consistency.head(25).to_csv(OUT/"top_by_positive_months.csv",index=False)
    quality={"source":"Delta India BTCUSD 1m authentic OHLCV",
             "start_utc":str(raw.index[0]),"end_utc":str(raw.index[-1]),
             "source_candles":int(len(raw)), "gaps":gaps,
             "SL_points":STOPS,"TP_points":TARGETS,"timeframes_minutes":TFS,
             "variants":len(sm),
             "fee_gst_each_side":FEE,"slippage_price_points_each_side":SLIP,
             "source_coverage_IST":coverage,"signal_stats":signal_stats,
             "baseline_100_200_parity":"PASSED for trades, wins and compounded returns",
             "multiple_testing_warning":"Historical data already researched, no blind holdout",
             "drawdown_measure":"Trade-close peak-to-trough, excludes intratrade margin risks"}
    (OUT/"quality.json").write_text(json.dumps(quality,indent=2))
    report=["# Fixed TP/SL grid — Supertrend ATR10×3 + EMA9/21, BTCUSD",
            "",
            f"**All 162 runs completed** from {len(raw):,} authentic Delta India 1m candles.",
            "Used the identical closed-bar signal generator and minute-by-minute",
            "execution model from the original Supertrend/EMA9/21 study.",
            "Original 100 SL / 200 TP replicated EXACTLY on all timeframes.",
            "",
            "## Highest net 1× account return — top 15",
            "",top_profit.head(15).to_markdown(index=False,floatfmt=".2f"),"",
            "## Most positive IST months — top 15",
            "",top_consistency.head(15).to_markdown(index=False,floatfmt=".2f"),"",
            "## Highest positive-month count by timeframe",
            ""]
    for tf in TFS:
        g=top_consistency[top_consistency.timeframe.eq(f"{tf}m")].iloc[0]
        report.append(f"- **{tf}m:** SL {int(g.sl_points)} TP {int(g.tp_points)}: "
                      f"{g.positive_months_22}/22 months positive; "
                      f"win {g.win_rate_pct:.2f}%; net 1× return "
                      f"{g.total_net_1x_account_return_pct:.2f}%; "
                      f"drawdown {g.max_trade_close_drawdown_pct:.2f}%.")
    report += ["","## All timeframes, all tested pairs: IST positive months",
               "","The cells below show counts out of 22 (not account returns).",""]
    table=sm.pivot_table(index=["timeframe","sl_points"],
                         columns="tp_points",values="positive_months_22")
    report.append(table.to_markdown(floatfmt=".0f"))
    report += ["","## Critical interpretation","",
        "- Higher results from this grid are **in-sample parameter selection**: testing 162 settings increases the chance of accidental winners.",
        "- 2025 and 2026 are research-exposed, not blind out-of-sample.",
        "- All prices are BTC price points, not USD account profit or leverage-adjusted P&L.",
        "- Next 1m OPEN entries after confirmed alignment; 1m stop-first rule for same-minute SL+TP touches; end-of-month flat.",
        "- $5 adverse slippage each side, 0.05% per-side taker fee plus 18% GST; 1× capital compounding.",
        "- No funding, actual live spread, liquidation, real-time stop gaps between 1m ticks, or margin model.",
        "- January 2025 has a 330-minute IST data shortage; the other 21 months are complete.",
        "- Individual trade ledger, every monthly result, summary, and machine-readable quality file are saved.",
        "- No model is suitable for live execution solely because it leads this grid.",""]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report))
    print("COMPLETE 162 VARIANTS and baseline parity check",flush=True)
    print("BEST BY RETURN",top_profit.head(3).to_json(orient="records"),flush=True)
    print("BEST BY MONTH COUNT",top_consistency.head(3).to_json(orient="records"),flush=True)

if __name__=="__main__":
    main()
