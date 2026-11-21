#!/usr/bin/env python3
"""Fixed-rule BTCUSD 1M momentum scalp; 15M completed EMA regime; causal next-open replay."""
from __future__ import annotations
from pathlib import Path
import json
import math
import numpy as np
import pandas as pd

BASE = Path("data/delta_india/BTCUSD/1m")
OUT = Path("analysis/momentum_scalp_1m_15m")
FEE = 0.0005 * 1.18
SLIP = 5.0
HOLD = 60
CAPITAL = 1000.0
RISK_ATR = 1.0
TARGET_R = 2.0

def load():
    files = sorted(BASE.glob("20??-??.csv.gz"))
    if len(files) < 22:
        raise RuntimeError(f"Expected 22+ monthly partitions, received {len(files)}")
    pieces = [pd.read_csv(p, compression="gzip",
        usecols=["time", "open", "high", "low", "close", "volume"]) for p in files]
    f = pd.concat(pieces, ignore_index=True).sort_values("time").reset_index(drop=True)
    t = f.time.to_numpy(dtype=np.int64)
    if not np.all(np.diff(t) > 0) or np.any(np.diff(t) % 60):
        raise ValueError("Duplicate, non-monotonic or off-minute UTC candles")
    cols = ["open","high","low","close","volume"]
    v = f[cols].to_numpy(float)
    if not np.isfinite(v).all() or (v[:,0:4] <= 0).any() or (v[:,4] < 0).any():
        raise ValueError("Invalid prices or volumes")
    if ((f.low > f.high) | (f.open < f.low) | (f.open > f.high) |
        (f.close < f.low) | (f.close > f.high)).any():
        raise ValueError("Invalid OHLC candle")
    gaps = np.flatnonzero(np.diff(t)!=60) + 1
    starts = np.r_[0,gaps]
    ends = np.r_[gaps,len(f)]
    seg_start = np.zeros(len(f),dtype=np.int32)
    seg_end = np.zeros(len(f),dtype=np.int32)
    for a,b in zip(starts,ends):
        seg_start[a:b] = a
        seg_end[a:b] = b
    f.index = pd.to_datetime(t,unit="s",utc=True)
    quality = {
        "data_source":"Delta Exchange India BTCUSD 1-minute OHLCV archive",
        "source_files":[p.name for p in files],
        "rows":len(f), "first_utc":str(f.index[0]), "last_utc":str(f.index[-1]),
        "missing_utc_minutes":int((t[-1]-t[0])//60+1-len(f)),
        "gaps":[{"before":str(f.index[i-1]),"after":str(f.index[i]),
                 "missing_minutes":int((t[i]-t[i-1])//60-1)} for i in gaps],
    }
    return f,seg_start,seg_end,quality

def feature_engineering(f, seg_start, seg_end):
    # Every signal uses the completed minute i, and fills at i+1 OPEN.
    cl = f.close
    hi = f.high
    lo = f.low
    v = f.volume
    prev_hi = hi.rolling(10,min_periods=10).max().shift(1)
    prev_lo = lo.rolling(10,min_periods=10).min().shift(1)
    prev_vol = v.rolling(20,min_periods=20).mean().shift(1)

    # Reset Wilder RSI and ATR at any archive discontinuity.
    n=len(f)
    rsi_arr=np.full(n,np.nan,dtype=np.float64)
    atr_arr=np.full(n,np.nan,dtype=np.float64)
    starts=np.r_[0,np.flatnonzero(seg_start[1:]!=seg_start[:-1])+1]
    ends=np.r_[starts[1:],n]
    for a,b in zip(starts,ends):
        c=cl.iloc[a:b]
        h=hi.iloc[a:b]
        l=lo.iloc[a:b]
        d=c.diff()
        gain=d.clip(lower=0).ewm(alpha=1/14,adjust=False,min_periods=14).mean()
        loss=(-d.clip(upper=0)).ewm(alpha=1/14,adjust=False,min_periods=14).mean()
        rs=gain/loss.replace(0,np.nan)
        rsi=100-100/(1+rs)
        rsi=np.where((loss.to_numpy()==0)&(gain.to_numpy()>0),100,rsi)
        rsi=np.where((gain.to_numpy()==0)&(loss.to_numpy()>0),0,rsi)
        tr=pd.concat([h-l,(h-c.shift(1)).abs(),(l-c.shift(1)).abs()],axis=1).max(axis=1)
        atr=tr.ewm(alpha=1/14,adjust=False,min_periods=14).mean()
        rsi_arr[a:b]=rsi
        atr_arr[a:b]=atr

    # 15-minute candle ending at 00:15 UTC comprises 00:00...00:14.
    # It is ONLY visible at 00:15, so map it to one-minute SIGNAL CLOSE time.
    bars=f.resample("15min",closed="left",label="right").agg(
        close=("close","last"), num=("close","size"))
    valid=bars.num.eq(15)
    close15=bars.close.where(valid)
    e20=close15.ewm(span=20,adjust=False,min_periods=50).mean()
    e50=close15.ewm(span=50,adjust=False,min_periods=50).mean()
    warm=valid.rolling(50,min_periods=50).sum().eq(50)
    regime=pd.Series(np.where(warm & (e20>e50),1,
                       np.where(warm & (e20<e50),-1,0)),index=bars.index)
    # UTC archive labels assumed candle open as used by existing project.
    close_ts=f.index+pd.Timedelta(minutes=1)
    trdir=regime.reindex(close_ts,method="ffill").fillna(0).to_numpy(np.int8)

    # Reject missing timestamp entry, or signals with insufficient fully
    # continuous minute history after a gap. All windows are backward-looking.
    continuous=(np.arange(n)-seg_start >= 1000)
    continuous &= (np.arange(n)+1 < seg_end)
    long=(continuous & (trdir==1) & (rsi_arr>55)
          & (v.to_numpy()>1.5*prev_vol.to_numpy())
          & (cl.to_numpy()>prev_hi.to_numpy()))
    short=(continuous & (trdir==-1) & (rsi_arr<45)
          & (v.to_numpy()>1.5*prev_vol.to_numpy())
          & (cl.to_numpy()<prev_lo.to_numpy()))
    candidates=np.flatnonzero(long|short)
    return candidates,np.where(long[candidates],1,-1).astype(np.int8),atr_arr

def replay(f,seg_end,candidates,sides,atr):
    op=f.open.to_numpy(float); hi=f.high.to_numpy(float)
    lo=f.low.to_numpy(float); cl=f.close.to_numpy(float)
    t=f.time.to_numpy(np.int64)
    loc=f.index.tz_convert("Asia/Kolkata")
    ym=(loc.year.to_numpy()*12+loc.month.to_numpy()).astype(np.int32)
    months=loc.strftime("%Y-%m").to_numpy()
    rows=[]
    last_exit=-1
    n=len(f)
    for signal,side in zip(candidates,sides):
        k=int(signal+1)
        if k<=last_exit or k>=n or k>=seg_end[signal]:
            continue
        risk=float(atr[signal])
        if not np.isfinite(risk) or risk<=0:
            continue
        entry=op[k]
        stop=entry-side*risk*RISK_ATR
        target=entry+side*risk*RISK_ATR*TARGET_R
        last=min(k+HOLD, int(seg_end[k]))-1
        reason="timeout"
        exit_mid=cl[last]
        exit_k=last
        for j in range(k,last+1):
            # stop wins if both extreme prices reached in an ambiguous minute.
            hit_stop=lo[j]<=stop if side==1 else hi[j]>=stop
            hit_tp=hi[j]>=target if side==1 else lo[j]<=target
            if hit_stop:
                exit_mid=min(op[j],stop) if side==1 else max(op[j],stop)
                reason="stop"
                exit_k=j
                break
            if hit_tp:
                exit_mid=target
                reason="target"
                exit_k=j
                break
            # Flatten before a discontinuity, dataset end or IST month change.
            if j==last or (j+1<n and ym[j+1]!=ym[j]):
                exit_mid=cl[j]
                reason=("month_end" if j+1<n and ym[j+1]!=ym[j]
                        else "gap_or_end" if j+1>=int(seg_end[k]) or j+1>=n
                        else "timeout")
                exit_k=j
                break
        fill_in=entry+side*SLIP
        fill_out=exit_mid-side*SLIP
        gross=side*(exit_mid-entry)/entry
        slippage=2*SLIP/entry
        fee=FEE*(fill_in+fill_out)/fill_in
        net=(side*(fill_out-fill_in)-FEE*(fill_in+fill_out))/fill_in
        if net<=-1: raise ValueError("1x account equity exhausted")
        last_exit=exit_k
        rows.append({
            "entry_utc":str(f.index[k]),"exit_utc":str(f.index[exit_k]),
            "month_ist":str(months[k]),"side":"LONG" if side==1 else "SHORT",
            "entry":entry,"exit_mid":float(exit_mid),"exit_reason":reason,
            "atr14":risk,"duration_minutes":int(exit_k-k+1),
            "gross_pct":100*gross,"fee_pct":100*fee,"slippage_pct":100*slippage,
            "net_pct":100*net,"gross_points":side*(exit_mid-entry),
            "net_points_per_btc":side*(fill_out-fill_in)-FEE*(fill_in+fill_out),
        })
    return pd.DataFrame(rows)

def summarize(trades,quality):
    months=pd.period_range("2025-01","2026-11",freq="M")
    output=[]
    for month in months:
        key=str(month)
        t=trades[trades.month_ist==key]
        v=t.net_pct.to_numpy(float)/100 if len(t) else np.array([],dtype=float)
        growth=float(np.prod(1+v))
        winners=int((v>0).sum())
        gross_profit=float(v[v>0].sum()) if len(v) else 0
        gross_loss=float(-v[v<0].sum()) if len(v) else 0
        status=("partial_start_IST" if key=="2025-01" else
                "partial_end_IST" if key=="2026-11" else "full_IST")
        output.append(dict(month_ist=key,coverage=status,
            trades=len(t),wins=winners,losses=int((v<=0).sum()),
            win_rate_pct=round(100*winners/len(t),3) if len(t) else 0.0,
            monthly_net_return_pct=round(100*(growth-1),5),
            total_fee_pct_of_trade_notional=round(t.fee_pct.sum(),5),
            total_slippage_pct_of_trade_notional=round(t.slippage_pct.sum(),5),
            gross_trade_return_pct_sum=round(t.gross_pct.sum(),5),
            profit_factor=round(gross_profit/gross_loss,4) if gross_loss else None,
        ))
    monthly=pd.DataFrame(output)
    # Global chronological close-to-close equity; 1x notional/equity, reinvested.
    pnl=trades.net_pct.to_numpy(float)/100
    equity=np.r_[1.0,np.cumprod(1+pnl)]
    peak=np.maximum.accumulate(equity)
    maxdd=float(np.max((peak-equity)/peak))*100
    complete=monthly[monthly.coverage=="full_IST"]
    positive=int((complete.monthly_net_return_pct>0).sum())
    y2025=trades[trades.month_ist.str.startswith("2025-")].net_pct.to_numpy(float)/100
    y2026=trades[trades.month_ist.str.startswith("2026-")].net_pct.to_numpy(float)/100
    summary=dict(strategy="BTCUSD_1m_volume_RSI_10bar_breakout_15m_EMA",
        archive=quality,total_trades=len(trades),
        net_win_rate_pct=round(100*(pnl>0).mean(),3) if len(pnl) else 0,
        profit_factor=round(float(pnl[pnl>0].sum()/-pnl[pnl<0].sum()),4)
            if (pnl<0).any() else None,
        total_compounded_return_pct=round(100*(equity[-1]-1),5),
        max_closed_trade_drawdown_pct=round(maxdd,5),
        year2025_compounded_return_pct=round(100*(np.prod(1+y2025)-1),5),
        year2026_through_nov20_compounded_return_pct=round(100*(np.prod(1+y2026)-1),5),
        fully_covered_IST_months=len(complete),
        positive_full_IST_months=positive,
        negative_full_IST_months=int((complete.monthly_net_return_pct<0).sum()),
        zero_full_IST_months=int((complete.monthly_net_return_pct==0).sum()),
        full_IST_months_at_least_10_pct=int((complete.monthly_net_return_pct>=10).sum()),
        initial_reference_equity_usd=CAPITAL,
        final_reference_equity_usd=round(CAPITAL*float(equity[-1]),4),
        assumptions=["1x notional/equity at each entry and compounded","Full 15M bars only, strictly causal trend filter",
          "1m Wilder RSI14 and ATR14 computed on closed signal bar",
          "next 1m open plus 5 USD adverse slip per side",
          "0.05 percent taker per side plus 18 percent GST",
          "60 minute timeout, one position shared by both directions",
          "stop-first on same minute target and stop; stop gaps fill worse",
          "IST month boundary flat; Jan 2025 starts 05:30 IST (partial); Nov 2026 partial",
          "No funding, spread, actual bid-ask, order book liquidity, liquidation, market impact",
          "All 2025-2026 historical data previously exposed, not pristine out-of-sample"])
    return monthly,summary

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    f,ss,se,quality=load()
    candidates,sides,atr=feature_engineering(f,ss,se)
    trades=replay(f,se,candidates,sides,atr)
    if trades.empty: raise RuntimeError("No eligible trades")
    monthly,report=summarize(trades,quality)
    monthly.to_csv(OUT/"monthly_results.csv",index=False)
    trades.to_csv(OUT/"trade_ledger.csv.gz",index=False,compression="gzip")
    (OUT/"summary.json").write_text(json.dumps(report,indent=2)+"\n")
    lines=["# BTCUSD 1-minute momentum scalp with closed 15-minute EMA regime","",
      "## Predeclared settings",
      "- Long: EMA20>EMA50 on last closed 15M, RSI14>55 on 1M, volume>1.5x prior20 1M mean, close above prior10 1M highs; short reverse.",
      "- Entry next 1M open; initial stop=1x 1M ATR14; gross take-profit=2x ATR14; stop first if ambiguity.",
      "- One open position, 60-minute max, force flat at IST month boundary.",
      "- Taker 0.05% each leg + 18% GST; 5 USD BTC price slippage each leg; 1x account exposure compounded.","",
      "## Summary","",
      "```json",json.dumps({k:v for k,v in report.items() if k not in ("archive","assumptions")},indent=2),"```","",
      "## Monthly realized NET account returns (IST)","",monthly.to_markdown(index=False),"",
      "## Important caveats",""]
    lines.extend("- "+x for x in report["assumptions"])
    lines.extend(["","## Data quality","",
      "```json",json.dumps(quality,indent=2),"```","",
      "Historical optimization exposure and uncertain API candle label convention require forward validation.",
      "Backtest is not an executable fill guarantee."])
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(lines)+"\n")
    print("MOMENTUM_SCALP_COMPLETE")
    print("SUMMARY "+json.dumps({k:v for k,v in report.items() if k not in ("archive","assumptions")}))
    print("MONTHLY_RESULTS")
    print(monthly.to_string(index=False))
if __name__=="__main__":
    main()
