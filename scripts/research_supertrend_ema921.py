#!/usr/bin/env python3
"""Delta BTCUSD Supertrend ATR10*3 + EMA9/21 causal 1m execution research.

Rules and novelty pre-registered at analysis/supertrend_ema921/NOVELTY_CHECK.md.
"""
from __future__ import annotations
import calendar
import json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path("data/delta_india/BTCUSD/1m")
OUT = Path("analysis/supertrend_ema921")
IST = "Asia/Kolkata"
SLIP = 5.0
FEE = 0.0005 * 1.18
MONTHS = pd.period_range("2025-01", "2026-10", freq="M").astype(str).tolist()
END_UTC = pd.Timestamp("2026-11-01 00:00:00", tz=IST).tz_convert("UTC")

def source():
    files = sorted(ROOT.glob("20??-??.csv.gz"))
    assert len(files) >= 22, "Missing Delta India month files"
    frames = [pd.read_csv(p, compression="gzip",
                 usecols=["time", "open", "high", "low", "close", "volume"]) for p in files]
    f = pd.concat(frames, ignore_index=True).sort_values("time", kind="stable")
    f = f.loc[f.time.astype("int64") < int(END_UTC.timestamp())].copy()
    t = f.time.astype("int64").to_numpy()
    assert len(t) > 500000, "Unexpectedly small archive"
    assert np.all(np.diff(t) > 0), "Duplicate/out-of-order candles"
    assert np.isfinite(f[["open","high","low","close","volume"]].to_numpy()).all()
    assert ((f.low <= f.open) & (f.open <= f.high) &
            (f.low <= f.close) & (f.close <= f.high)).all(), "Invalid OHLC"
    f.index = pd.to_datetime(t, unit="s", utc=True)
    f = f[["open","high","low","close","volume"]]
    miss = np.where(np.diff(t) != 60)[0]
    gaps = [{"after_utc":str(f.index[i]), "before_utc":str(f.index[i+1]),
             "missing_minutes":int((t[i+1]-t[i])//60-1)} for i in miss]
    return f, gaps

def supertrend(b, n=10, multiplier=3.0):
    h = b.high.to_numpy(float); l = b.low.to_numpy(float)
    c = b.close.to_numpy(float)
    p = np.r_[c[0],c[:-1]]
    tr = np.maximum(h-l, np.maximum(np.abs(h-p),np.abs(l-p)))
    atr = np.full(len(b), np.nan)
    if len(tr)<n: return np.zeros(len(b),np.int8)
    atr[n-1] = np.mean(tr[:n])
    for j in range(n,len(tr)):
        atr[j] = (atr[j-1]*(n-1)+tr[j])/n
    up = (h+l)/2 + multiplier*atr
    dn = (h+l)/2 - multiplier*atr
    final_up=np.full(len(b),np.nan); final_dn=np.full(len(b),np.nan)
    direction=np.zeros(len(b),np.int8)
    final_up[n-1]=up[n-1]; final_dn[n-1]=dn[n-1]
    direction[n-1]=-1
    for j in range(n,len(b)):
        final_up[j] = up[j] if (up[j]<final_up[j-1] or c[j-1]>final_up[j-1]) else final_up[j-1]
        final_dn[j] = dn[j] if (dn[j]>final_dn[j-1] or c[j-1]<final_dn[j-1]) else final_dn[j-1]
        if direction[j-1]<0:
            direction[j] = 1 if c[j]>final_up[j] else -1
        else:
            direction[j] = -1 if c[j]<final_dn[j] else 1
    return direction

def minute_alignment(raw, tf):
    rule = {5:"5min", 15:"15min", 60:"1h"}[tf]
    agg=raw.resample(rule,closed="left",label="left").agg(
        {"open":"first","high":"max","low":"min","close":"last","volume":"sum"})
    count=raw.close.resample(rule,closed="left",label="left").count()
    agg=agg.loc[count.eq(tf)].copy()
    # All trading data is continuous in this snapshot. If this changes,
    # refuse to smooth indicators across a missing source minute.
    e9=agg.close.ewm(span=9,adjust=False).mean().to_numpy()
    e21=agg.close.ewm(span=21,adjust=False).mean().to_numpy()
    st=supertrend(agg)
    aligned=np.where((e9>e21)&(st>0),1,np.where((e9<e21)&(st<0),-1,0)).astype(np.int8)
    aligned[:100]=0
    valid_from = agg.index + pd.Timedelta(minutes=tf)
    stream=pd.Series(aligned,index=valid_from)
    sig=stream.reindex(raw.index,method="ffill").fillna(0).to_numpy(np.int8)
    return sig, {"tf_minutes":tf,"higher_bars":len(agg),
                 "aligned_long_bars":int((aligned==1).sum()),
                 "aligned_short_bars":int((aligned==-1).sum())}

def execute(raw, sig, tf, mode, month_key):
    op=raw.open.to_numpy(float); hi=raw.high.to_numpy(float)
    lo=raw.low.to_numpy(float); close=raw.close.to_numpy(float)
    n=len(raw); position=0; entry_mid=entry_fill=0.0; entry_k=0
    rows=[]; equity=1.0; peak=1.0; drawdown=0.0
    def close_trade(k, mid, why):
        nonlocal equity, peak, drawdown, position
        fill=mid-position*SLIP
        fee=FEE*(entry_fill+fill)
        gross=position*(mid-entry_mid)
        net=position*(fill-entry_fill)-fee
        ret=net/entry_fill
        equity*=1+ret
        peak=max(peak,equity)
        drawdown=max(drawdown,100*(1-equity/peak))
        rows.append({"timeframe":f"{tf}m", "policy":mode,
            "entry_ist":raw.index[entry_k].tz_convert(IST).isoformat(),
            "exit_ist":raw.index[k].tz_convert(IST).isoformat(),
            "month_ist":MONTHS[month_key[k]-2025*12-1] if False else raw.index[k].tz_convert(IST).strftime("%Y-%m"),
            "side":"LONG" if position==1 else "SHORT",
            "entry_mid":round(float(entry_mid),3), "exit_quote":round(float(mid),3),
            "gross_points_per_btc":round(float(gross),4),
            "fees_gst_per_btc":round(float(fee),4),
            "slippage_points_per_btc":2*SLIP,
            "net_points_per_btc":round(float(net),4),
            "net_trade_1x_return_pct":float(100*ret),
            "win":bool(net>0), "exit_reason":why,
            "minutes_held":int(k-entry_k+1)})
        position=0
    def open_trade(k, side):
        nonlocal position, entry_mid, entry_fill, entry_k
        position=int(side); entry_mid=float(op[k])
        entry_fill=entry_mid+position*SLIP; entry_k=k

    for k in range(n):
        direction=int(sig[k]); previous=int(sig[k-1]) if k else 0
        # The prior minute closes precisely at the previous month end.
        if k>0 and month_key[k]!=month_key[k-1] and position:
            close_trade(k-1,float(close[k-1]),"month_flat")
        if mode=="signal_exit":
            if position and direction!=position:
                close_trade(k,float(op[k]),"alignment_lost")
            if not position and direction!=0:
                open_trade(k,direction)
        else:
            # Only fresh alignment events may initiate a fixed-exit position.
            if not position and direction!=0 and direction!=previous:
                open_trade(k,direction)
            if position:
                stop=entry_fill-position*100.0
                target=entry_fill+position*200.0
                stop_gap=(op[k]<=stop if position>0 else op[k]>=stop)
                stop_hit=(lo[k]<=stop if position>0 else hi[k]>=stop)
                tp_hit=(hi[k]>=target if position>0 else lo[k]<=target)
                if stop_gap:
                    close_trade(k,float(op[k]),"stop_gap")
                elif stop_hit:
                    close_trade(k,float(stop),"stop_first_both" if tp_hit else "stop")
                elif tp_hit:
                    close_trade(k,float(target),"target")
    if position:
        close_trade(n-1,float(close[-1]),"end_of_data")
    df=pd.DataFrame(rows)
    return df, drawdown

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    raw,gaps=source()
    if gaps:
        raise RuntimeError("Source contains minutes missing; refusing discontinuous EMA/Supertrend: "+str(gaps[:5]))
    local=raw.index.tz_convert(IST)
    month_key=np.asarray(local.year,dtype=np.int32)*12+np.asarray(local.month,dtype=np.int32)
    obs=pd.Series(1,index=local).groupby(local.strftime("%Y-%m")).count()
    coverage={}
    for m in MONTHS:
        year,month=map(int,m.split("-"))
        expected=calendar.monthrange(year,month)[1]*1440
        count=int(obs.get(m,0))
        coverage[m]={"expected_minutes":expected,"observed_minutes":count,
                     "complete":count==expected}
    all_summary=[]; all_monthly=[]; all_trades=[]; signal_quality={}
    for tf in (5,15,60):
        sig,stats=minute_alignment(raw,tf)
        signal_quality[str(tf)]=stats
        for mode in ("signal_exit","SL100_TP200"):
            df,dd=execute(raw,sig,tf,mode,month_key)
            all_trades.append(df)
            monthly=[]; eq=1.0
            for m in MONTHS:
                g=df.loc[df.month_ist.eq(m)]
                start=eq
                for r in g.itertuples(index=False):
                    eq*=1+r.net_trade_1x_return_pct/100.0
                mret=100*(eq/start-1)
                row={"timeframe":f"{tf}m","policy":mode,"month_ist":m,
                    "trades":int(len(g)),"wins":int(g.win.sum()),
                    "losses":int(len(g)-g.win.sum()),
                    "net_1x_account_return_pct":float(mret),
                    "complete_data":coverage[m]["complete"]}
                monthly.append(row);all_monthly.append(row)
            wins=int(df.win.sum());losses=len(df)-wins
            pos=float(df.loc[df.net_points_per_btc>0,"net_points_per_btc"].sum())
            neg=-float(df.loc[df.net_points_per_btc<=0,"net_points_per_btc"].sum())
            summary={"timeframe":f"{tf}m","policy":mode,
                "trades":len(df),"wins":wins,"losses":losses,
                "win_rate_pct":100*wins/len(df) if len(df) else 0.0,
                "gross_points_per_btc":float(df.gross_points_per_btc.sum()),
                "fees_gst_per_btc":float(df.fees_gst_per_btc.sum()),
                "slippage_points_per_btc":float(df.slippage_points_per_btc.sum()),
                "net_points_per_btc":float(df.net_points_per_btc.sum()),
                "profit_factor":pos/neg if neg else None,
                "total_net_1x_account_return_pct":100*(eq-1),
                "positive_months_22":sum(z["net_1x_account_return_pct"]>0 for z in monthly),
                "negative_months_22":sum(z["net_1x_account_return_pct"]<0 for z in monthly),
                "max_trade_close_drawdown_pct":float(dd),
                "positive_2025":sum(z["net_1x_account_return_pct"]>0 for z in monthly if z["month_ist"]<"2026-01"),
                "positive_2026_JanOct":sum(z["net_1x_account_return_pct"]>0 for z in monthly if z["month_ist"]>="2026-01")}
            all_summary.append(summary)
            print("RESULT",json.dumps(summary,sort_keys=True),flush=True)
    sm=pd.DataFrame(all_summary); mo=pd.DataFrame(all_monthly)
    sm.to_csv(OUT/"summary.csv",index=False)
    mo.to_csv(OUT/"monthly_results.csv",index=False)
    pd.concat(all_trades,ignore_index=True).to_csv(OUT/"trade_ledger.csv.gz",compression="gzip",index=False)
    quality={"source":"Delta India BTCUSD authentic 1m OHLCV",
             "start_utc":str(raw.index[0]),"last_utc":str(raw.index[-1]),
             "candles":int(len(raw)),"gaps":gaps,
             "fees_each_side_including_GST":FEE,"slippage_points_per_side":SLIP,
             "coverage_IST":coverage,"signals":signal_quality,
             "note":"No funding, live spreads, or liquidation. Drawdown at trade closes. 2026 previously researched."}
    (OUT/"quality.json").write_text(json.dumps(quality,indent=2))
    pivot=mo.pivot(index="month_ist",columns=["timeframe","policy"],values="net_1x_account_return_pct")
    report=["# BTCUSD Supertrend ATR10×3 with EMA9/21 — actual 1m replay",
        "", "## After-cost 1× strategy comparison", "",
        sm.to_markdown(index=False,floatfmt=".2f"), "",
        "## Monthly IST net 1× account return (%)", "",
        pivot.to_markdown(floatfmt=".2f"), "",
        "## Locked execution assumptions", "",
        "- Same-timeframe 5m, 15m, 1H variants tested separately (not a 1H+15M+5M MTF filter).",
        "- Long when EMA9 > EMA21 AND Supertrend bullish; short inverse; only a new transition into alignment triggers initial entry.",
        "- Signal-exit variant closes/reverses at next 1m OPEN after alignment loss.",
        "- SL100/TP200 variant uses actual 1m OHLC, stop-first if both touched; values from slippage-adjusted entry fill, reentry only after new alignment.",
        "- One position at a time, 24/7, IST month-end flatten, never infer intrabar direction on a higher timeframe.",
        "- $5 adverse slippage per side, 0.05% taker fee per side plus 18% GST, 1× notional compounded, drawdown based on trade-close equity.",
        f"- Original 1m candles: {len(raw):,} from {raw.index[0]} to {raw.index[-1]}.",
        f"- Unfilled 1m gaps: {len(gaps)}; IST months with incomplete source: {[m for m in MONTHS if not coverage[m]['complete']]}.",
        "- Source index UTC minute labels assumed candle OPEN; verify alignment with TradingView or Delta before live deployment.",
        "- 2025 and 2026 already researched, not a blind out-of-sample verification; no funding/spread/depth, margin, or liquidation model.",
        "", "## Reproduce", "",
        "Run `python scripts/research_supertrend_ema921.py` using repository data.",
        "See `NOVELTY_CHECK.md`, `quality.json`, `monthly_results.csv`, `trade_ledger.csv.gz`."]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")
    print("COMPLETE 6 experiments, monthly report and trade ledgers",flush=True)

if __name__=="__main__": main()
