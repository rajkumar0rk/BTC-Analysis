#!/usr/bin/env python3
"""Research-only causal 1H ST(10,3)+EMA20 touch/reclaim on Delta India BTCUSD 1m."""
import json
from pathlib import Path
import numpy as np
import pandas as pd

BASE=Path("data/delta_india/BTCUSD/1m")
OUT=Path("analysis/st_ema20_1h_reversal_only")
QTY=0.001
START_USD=100.
FEE=.0005*1.18
SLIP=5.
STOP_BUFFER=10.

def load():
    files=sorted(BASE.glob("20??-??.csv.gz"))
    if not files: raise RuntimeError("No BTCUSD one-minute source archive")
    a=[]
    for f in files:
        x=pd.read_csv(f,compression="gzip",usecols=["time","open","high","low","close","volume"])
        x["time"]=pd.to_datetime(x.time.astype("int64"),unit="s",utc=True)
        a.append(x.set_index("time"))
    m=pd.concat(a).sort_index()
    if m.index.has_duplicates or not m.index.to_series().diff().dropna().eq(pd.Timedelta(minutes=1)).all():
        raise RuntimeError("Source 1m archive has duplicate or missing timestamps")
    if m[["open","high","low","close"]].isna().any().any(): raise RuntimeError("Missing OHLC")
    if not ((m.low<=m[["open","close"]].min(axis=1)) & (m.high>=m[["open","close"]].max(axis=1))).all():
        raise RuntimeError("Invalid OHLC")
    count=m.close.resample("1h").count()
    if not count.eq(60).all(): raise RuntimeError("Incomplete hourly bar")
    h=m.resample("1h").agg({"open":"first","high":"max","low":"min","close":"last","volume":"sum"})
    return m,h,len(files)

def features(h):
    prev=h.close.shift()
    tr=pd.concat([h.high-h.low,(h.high-prev).abs(),(h.low-prev).abs()],axis=1).max(axis=1).to_numpy()
    n=len(h); atr=np.full(n,np.nan)
    if n<30: raise RuntimeError("Insufficient signal warmup")
    atr[9]=tr[:10].mean()
    for i in range(10,n): atr[i]=(9*atr[i-1]+tr[i])/10
    mid=(h.high.to_numpy()+h.low.to_numpy())/2.
    up=mid+3*atr; down=mid-3*atr
    u=np.full(n,np.nan); d=np.full(n,np.nan); side=np.zeros(n,dtype=np.int8)
    for i in range(9,n):
        if i==9:
            u[i]=up[i];d[i]=down[i];side[i]=-1
        else:
            u[i]=up[i] if up[i]<u[i-1] or h.close.iloc[i-1]>u[i-1] else u[i-1]
            d[i]=down[i] if down[i]>d[i-1] or h.close.iloc[i-1]<d[i-1] else d[i-1]
            side[i]=(1 if side[i-1]==-1 and h.close.iloc[i]>u[i-1] else
                     (-1 if side[i-1]==1 and h.close.iloc[i]<d[i-1] else side[i-1]))
    h=h.copy()
    h["ema"]=h.close.ewm(span=20,adjust=False).mean()
    h["atr"]=atr
    h["side"]=side
    h["supertrend_line"]=np.where(side==1,d,u)
    return h

def setups(h,mode):
    events={}; prev_side=0; seen_adverse=False; cycle=0; flip_i=0
    for i in range(20,len(h)):
        side=int(h.side.iloc[i])
        if side!=prev_side:
            cycle+=1;flip_i=i;seen_adverse=False;prev_side=side
        if side==0 or i==flip_i: continue
        r=h.iloc[i]
        favorable=side*(r.close-r.ema)>0
        adverse=side*(r.close-r.ema)<0
        touch=(favorable and not seen_adverse and
               (r.low<=r.ema if side==1 else r.high>=r.ema))
        reclaim=favorable and seen_adverse
        kind="reclaim" if reclaim else ("touch" if touch else None)
        if adverse: seen_adverse=True
        elif reclaim: seen_adverse=False
        if kind is None or (mode!="combined" and kind!=mode): continue
        start=flip_i if kind=="reclaim" else max(flip_i,i-2)
        stop=(float(h.low.iloc[start:i+1].min())-STOP_BUFFER if side==1
              else float(h.high.iloc[start:i+1].max())+STOP_BUFFER)
        trigger=float(r.high+.5 if side==1 else r.low-.5)
        risk=side*(trigger-stop)
        if risk<=0 or risk>5*r.atr:continue
        events[i+1]=dict(side=side,cycle=cycle,kind=kind,trigger=trigger,stop=stop,
                         max_risk=5*float(r.atr),signal=str(h.index[i]))
    return events

def replay(m,h,mode):
    """Exactly one exit: next 1m open after completed 1H Supertrend flip.
    No initial stop, breakeven lock, trailing stop or TP. Entry rules unchanged.
    """
    events=setups(h,mode)
    op=m.open.to_numpy(float)
    hi=m.high.to_numpy(float)
    lo=m.low.to_numpy(float)
    cl=m.close.to_numpy(float)
    times=m.index
    hour_idx=np.searchsorted(h.index.asi8,m.index.asi8,side="right")-1
    hside=h.side.to_numpy()
    used=set()
    trades=[]
    pos=None
    pending=None
    last_hour=-1
    realized=0.
    equity_peak=START_USD
    max_mtm_dd=0.
    min_mtm_equity=START_USD
    def finish(j,mid,reason):
        nonlocal pos,realized
        side=pos["side"]
        entry=pos["entry"]
        exit_fill=mid-side*SLIP
        gross=QTY*side*(exit_fill-entry)
        fees=QTY*(entry+exit_fill)*FEE
        net=gross-fees
        realized+=net
        trades.append(dict(mode=mode,setup=pos["kind"],
            side="long" if side==1 else "short",
            entry_utc=str(times[pos["entry_j"]]),
            exit_utc=str(times[j]),
            signal_utc=pos["signal"],
            entry_price=round(entry,2),
            exit_price=round(exit_fill,2),
            reference_structure_stop_not_executed=round(pos["reference_stop"],2),
            reference_risk_points=round(pos["reference_risk"],2),
            hold_min=j-pos["entry_j"]+1,
            mfe_points=round(pos["mfe"],2),
            mae_points=round(pos["mae"],2),
            gross_usd=round(gross,5),
            fees_usd=round(fees,5),
            net_usd=round(net,5),
            exit_reason=reason))
        pos=None
    for j,idx in enumerate(hour_idx):
        if idx!=last_hour:
            last_hour=idx
            pending=None
            if idx>0 and pos and int(hside[idx-1])!=pos["side"]:
                finish(j,float(op[j]),"supertrend_flip")
            if pos is None:
                ev=events.get(idx)
                if ev and ev["cycle"] not in used:
                    pending=ev
        if pos is None and pending:
            ev=pending
            side=ev["side"]
            triggered=(hi[j]>=ev["trigger"]) if side==1 else (lo[j]<=ev["trigger"])
            if triggered:
                entry=(max(op[j],ev["trigger"]) if side==1 else
                       min(op[j],ev["trigger"]))+side*SLIP
                ref_risk=side*(entry-ev["stop"])
                if 0<ref_risk<=ev["max_risk"]:
                    pos=dict(side=side,kind=ev["kind"],signal=ev["signal"],
                             entry_j=j,entry=entry,reference_stop=ev["stop"],
                             reference_risk=ref_risk,mfe=0.,mae=0.)
                    used.add(ev["cycle"])
                pending=None
        if pos is not None:
            side=pos["side"]
            pos["mfe"]=max(pos["mfe"], (hi[j]-pos["entry"]) if side==1 else (pos["entry"]-lo[j]))
            pos["mae"]=max(pos["mae"], (pos["entry"]-lo[j]) if side==1 else (hi[j]-pos["entry"]))
            # 1m-close mark-to-market; includes estimated closing slippage/fee.
            marked_exit=cl[j]-side*SLIP
            marked=START_USD+realized+QTY*side*(marked_exit-pos["entry"])-QTY*(pos["entry"]+marked_exit)*FEE
        else:
            marked=START_USD+realized
        equity_peak=max(equity_peak,marked)
        min_mtm_equity=min(min_mtm_equity,marked)
        max_mtm_dd=max(max_mtm_dd,equity_peak-marked)
    if pos is not None:
        finish(len(m)-1,float(cl[-1]),"end_archive_mark_not_supertrend")
    return pd.DataFrame(trades),dict(
        max_mtm_drawdown_usd=round(max_mtm_dd,4),
        min_marked_equity_usd=round(min_mtm_equity,4),
        ended_with_open_position_marked=int(len(trades)>0 and trades[-1]["exit_reason"]=="end_archive_mark_not_supertrend"),
        note="1m-close marked equity only, not liquidation modeling; intraminute losses can be greater")

def report(t):
    if t.empty: return dict(trades=0,net_usd=0)
    x=t.net_usd.to_numpy();curve=np.r_[START_USD,START_USD+np.cumsum(x)]
    peak=np.maximum.accumulate(curve)
    win=x[x>0].sum(); loss=-x[x<0].sum()
    return dict(trades=len(t),wins=int((x>0).sum()),losses=int((x<0).sum()),
                win_pct=round(100*(x>0).mean(),2),net_usd=round(x.sum(),2),
                gross_usd=round(t.gross_usd.sum(),2),fees_usd=round(t.fees_usd.sum(),2),
                profit_factor=round(win/loss,3) if loss else None,
                ending_usd=round(curve[-1],2),
                realized_max_drawdown_usd=round((peak-curve).max(),2),
                realized_max_drawdown_pct=round((100*(peak-curve)/peak).max(),2),
                setup_counts=t.setup.value_counts().to_dict(),
                exit_counts=t.exit_reason.value_counts().to_dict())

def monthly(t,first,last):
    months=pd.period_range(first.tz_convert("Asia/Kolkata").tz_localize(None).to_period("M"),
                           last.tz_convert("Asia/Kolkata").tz_localize(None).to_period("M"))
    if not t.empty:
        t=t.copy()
        t["month"]=pd.to_datetime(t.exit_utc,utc=True).dt.tz_convert("Asia/Kolkata").dt.strftime("%Y-%m")
    rows=[];equity=START_USD
    for month in months:
        key=str(month);g=t[t.month==key] if not t.empty else t
        pnl=float(g.net_usd.sum()) if len(g) else 0.
        rows.append(dict(month_ist=key,trades=len(g),
                         wins=int((g.net_usd>0).sum()) if len(g) else 0,
                         losses=int((g.net_usd<0).sum()) if len(g) else 0,
                         net_usd=round(pnl,4),start_equity_usd=round(equity,4),
                         net_return_pct=round(100*pnl/equity,3) if equity>0 else None,
                         end_equity_usd=round(equity+pnl,4),
                         complete_month=key<"2026-11"))
        equity+=pnl
    return pd.DataFrame(rows)

def main():
    m,h,num=load();h=features(h);OUT.mkdir(parents=True,exist_ok=True)
    qual=dict(exit_method="completed_1h_supertrend_flip_only_no_stop_no_trail_no_tp",archive_files=num,minute_bars=len(m),first_utc=str(m.index[0]),last_utc=str(m.index[-1]),
              hourly_bars=len(h),source="Delta India traded-price monthly CSV.gz",
              capital_usd=START_USD,position_qty_btc=QTY,side_taker_fee_plus_gst=FEE,
              slippage_price_points_per_side=SLIP,
              notes=["1m OHLC not trade ticks or bid/ask; ambiguous stops conservatively first",
                     "Fundings, liquidation, latency, order size constraints not modeled",
                     "No protection stop at all; position can experience severe unrealized losses",
                     "Monthly PnL assigned to exit month, not entry month",
                     "1H indicators use only previously completed hours",
                     "No untouched holdout: historical months studied in earlier research"])
    (OUT/"quality.json").write_text(json.dumps(qual,indent=2)+"\n")
    all_summary={}
    for mode in ["touch","reclaim","combined"]:
        t,diagnostics=replay(m,h,mode)
        t.to_csv(OUT/f"{mode}_trades.csv",index=False)
        mon=monthly(t,m.index[0],m.index[-1])
        mon.to_csv(OUT/f"{mode}_monthly_ist.csv",index=False)
        s=report(t)
        s.update(diagnostics)
        s["positive_full_months"]=int(((mon.net_usd>0)&mon.complete_month).sum())
        s["total_full_months"]=int(mon.complete_month.sum())
        all_summary[mode]=s
        print(mode,json.dumps(s),flush=True)
    (OUT/"summary.json").write_text(json.dumps(all_summary,indent=2)+"\n")

if __name__=="__main__":main()
