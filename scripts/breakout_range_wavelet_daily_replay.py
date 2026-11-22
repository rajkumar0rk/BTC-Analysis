#!/usr/bin/env python3
"""Source-pinned WaveletTwoB versus TwoB, causal UTC daily signal / authentic 1m fills."""
import csv,gzip,json,hashlib,math
from pathlib import Path
from datetime import datetime,timezone,timedelta
import numpy as np,pandas as pd,pywt
from zoneinfo import ZoneInfo

ROOT=Path("data/delta_india/BTCUSD/1m")
OUT=Path("analysis/breakout_range_wavelet_daily")
FEE=.0005*1.18
START=pd.Timestamp("2025-01-01",tz="UTC")
END=pd.Timestamp("2026-11-01",tz="UTC")
def load():
    manifest=json.loads((ROOT/"manifest.json").read_text())
    frames=[]; hashes={}
    for p in manifest["partitions"]:
        file=p["file"]
        if not ("2024-01"<=file[:7]<="2026-10"):continue
        payload=(ROOT/file).read_bytes(); digest=hashlib.sha256(payload).hexdigest()
        assert digest==p["sha256_gzip"],file
        import io
        f=pd.read_csv(io.BytesIO(gzip.decompress(payload)))
        key=next(k for k in ("time","timestamp","start","ts") if k in f)
        ts=pd.to_numeric(f[key]); ts=ts.where(ts<1e11,ts/1000)
        f["t"]=pd.to_datetime(ts,unit="s",utc=True)
        f=f.set_index("t")[["open","high","low","close","volume"]].astype(float)
        assert len(f)==p["observed_candles"] and f.index.is_unique
        assert f.index.to_series().diff().dropna().eq(pd.Timedelta(minutes=1)).all()
        frames.append(f);hashes[file]=digest
    minute=pd.concat(frames).sort_index()
    assert minute.index.is_unique
    return minute,hashes

def signals(daily,kind):
    n=len(daily); h=daily.high.to_numpy();l=daily.low.to_numpy();c=daily.close.to_numpy()
    tr=pd.concat([daily.high-daily.low,(daily.high-daily.close.shift()).abs(),(daily.low-daily.close.shift()).abs()],axis=1).max(axis=1)
    atr=tr.rolling(14).mean().to_numpy()
    high=np.full(n,np.nan);low=np.full(n,np.nan)
    if kind=="two_b":
        high=pd.Series(h).shift().rolling(20).max().to_numpy()
        low=pd.Series(l).shift().rolling(20).min().to_numpy()
    else:
        den=np.full(n,np.nan)
        wave=pywt.Wavelet("db6")
        level=max(pywt.dwt_max_level(128,wave.dec_len),1)
        for i in range(127,n):
            window=c[i-127:i+1]; coeff=pywt.wavedec(window,"db6",level=level)
            sigma=np.median(np.abs(coeff[-1]))/.6745
            threshold=sigma*np.sqrt(2*np.log(128))*.5
            den[i]=pywt.waverec([coeff[0]]+[pywt.threshold(x,threshold,mode="soft") for x in coeff[1:]],"db6")[:128][-1]
        last_h=np.nan;last_l=np.nan;last_hi=-5;last_lo=-5
        for i in range(n):
            k=i-3
            if k>=1 and np.isfinite(den[k]) and np.isfinite(atr[k]):
                left=den[max(0,k-5):k];right=den[k+1:i+1];prev=den[max(0,k-20):k]
                if len(left) and len(right) and len(prev) and np.isfinite(left).all() and np.isfinite(prev).all():
                    if den[k]>max(left) and den[k]>max(right) and den[k]-max(min(prev),min(right))>=atr[k] and k-last_hi>=5:
                        last_h=h[k];last_hi=k
                    if den[k]<min(left) and den[k]<min(right) and min(max(prev),max(right))-den[k]>=atr[k] and k-last_lo>=5:
                        last_l=l[k];last_lo=k
            high[i]=last_h;low[i]=last_l
    # Upstream two_b_rule: a breakout at b can confirm on b,b+1,b+2,b+3.
    # This is evaluated at confirmation close only, never on breakout day open.
    sig=np.zeros(n,dtype=int)
    for b in range(n):
        for t in range(b,min(b+4,n)):
            if h[b]>high[b] and c[t]<high[b]:
                sig[t]=-1;break
        for t in range(b,min(b+4,n)):
            if l[b]<low[b] and c[t]>low[b]:
                if sig[t]==0:sig[t]=1
                break
    return sig

def replay(minute,daily,sig,name):
    # UTC day D signal only becomes tradable at D+1 00:00 UTC.
    action={daily.index[i]+pd.Timedelta(days=1):int(v) for i,v in enumerate(sig) if v}
    cash=10000.;qty=0.;entry=0.;stop=0.;side=0;entry_t=None;entry_fee=0.
    trades=[];equity=[];previous_day=None;last_t=None;last_close=None
    def close(t,price,reason):
        nonlocal cash,qty,entry,stop,side,entry_t,entry_fee
        fee=qty*price*FEE;gross=side*qty*(price-entry)
        cash+=gross-fee
        trades.append(dict(strategy=name,entry_time=entry_t.isoformat(),exit_time=t.isoformat(),side=side,entry=entry,exit=price,qty=qty,gross=gross,entry_fee=entry_fee,exit_fee=fee,net=gross-entry_fee-fee,reason=reason))
        side=0;qty=0.
    for t,row in minute.loc[(minute.index>=START)&(minute.index<END)].iterrows():
        price=float(row.open); last_t=t;last_close=float(row.close)
        if side and t in action and action[t]==-side:close(t,price,"opposite_signal")
        if not side and t in action:
            direction=action[t]; prior=t-pd.Timedelta(days=1)
            if prior in daily.index:
                d=daily.loc[prior];sl=float(d.low if direction==1 else d.high)
                dist=direction*(price-sl)
                if dist>0:
                    size=min(cash*.005/dist,cash*3/price)
                    fee=size*price*FEE
                    if size>0 and fee<cash:
                        cash-=fee;qty=size;entry=price;stop=sl;side=direction;entry_t=t;entry_fee=fee
        if side:
            # At an already-open stop, fill at open (gap). Intraminute stop-first.
            if side==1 and row.low<=stop:close(t,min(price,stop),"stop")
            elif side==-1 and row.high>=stop:close(t,max(price,stop),"stop")
        mark=cash+(side*qty*(last_close-entry) if side else 0)
        equity.append((t,mark))
    if side:
        close(last_t,last_close,"end_of_data")
        # Terminal mark must include the actual final liquidation fee.
        equity[-1]=(last_t,cash)
    eq=pd.DataFrame(equity,columns=["t","nav"]).set_index("t")
    ist=eq.tz_convert("Asia/Kolkata")
    monthly=ist.nav.resample("MS").agg(["first","last"])
    # Monthly NAV returns use previous month-end, not first bar of current month.
    monthly["prior_nav"]=monthly["last"].shift(1).fillna(10000.)
    monthly["net_pct"]=(monthly["last"]/monthly["prior_nav"]-1)*100
    monthly["coverage"]="complete"
    monthly.loc[monthly.index[0],"coverage"]="partial_start_utc_archive"
    monthly.loc[monthly.index[-1],"coverage"]="partial_end_utc_archive"
    # Last row may be November IST (UTC Oct31 after 18:30); never label it October.
    monthly["month_ist"]=monthly.index.strftime("%Y-%m")
    trade=pd.DataFrame(trades)
    if len(trade):
        trade["exit_ist_month"]=pd.to_datetime(trade.exit_time,utc=True).dt.tz_convert("Asia/Kolkata").dt.strftime("%Y-%m")
        count=trade.groupby("exit_ist_month").size().to_dict()
        monthly["trades"]=[count.get(x.strftime("%Y-%m"),0) for x in monthly.index]
    else:monthly["trades"]=0
    OUT.mkdir(parents=True,exist_ok=True)
    trade.to_csv(OUT/(name+"_trades.csv"),index=False)
    monthly.to_csv(OUT/(name+"_monthly.csv"))
    net=trade.net.sum() if len(trade) else 0
    pf=float(trade.loc[trade.net>0,"net"].sum()/-trade.loc[trade.net<0,"net"].sum()) if len(trade) and (trade.net<0).any() else None
    return dict(name=name,trades=len(trade),net_trade_pnl=net,ending_cash=cash,nav_reconciliation_error=cash-10000-net,profit_factor=pf,max_drawdown_pct=float((eq.nav/eq.nav.cummax()-1).min()*100),positive_months=int(((monthly.net_pct>0)&(monthly.coverage=="complete")).sum()),negative_months=int(((monthly.net_pct<0)&(monthly.coverage=="complete")).sum()),flat_months=int(((monthly.net_pct==0)&(monthly.coverage=="complete")).sum()),monthly_rows=len(monthly),partial_months=int((monthly.coverage!="complete").sum()),fee_gst_total=float(trade.entry_fee.sum()+trade.exit_fee.sum()) if len(trade) else 0)

def main():
    minute,hashes=load()
    daily=minute.resample("1D",origin="start_day",label="left",closed="left").agg({"open":"first","high":"max","low":"min","close":"last","volume":"sum"})
    counts=minute.close.resample("1D").count()
    daily=daily.loc[counts.eq(1440)].copy()
    # No synthetic daily bars across missing days; check calendar continuity.
    assert daily.index.to_series().diff().dropna().eq(pd.Timedelta(days=1)).all()
    # Causal prefix-invariance gate: future candles must never change earlier signals.
    # Check multiple chronological cuts, both source baselines, without modifying fills.
    prefix_checks=[]
    for kind in ("two_b","wavelet_two_b"):
        full=signals(daily,kind)
        for cut in ("2025-06-30","2025-12-31","2026-06-30"):
            prefix=daily.loc[:cut]
            if len(prefix)<130:continue
            observed=signals(prefix,kind)
            mismatch=np.flatnonzero(observed!=full[:len(prefix)])
            assert not len(mismatch),f"LOOKAHEAD {kind} {cut}: {mismatch[:10]}"
            prefix_checks.append(dict(strategy=kind,through=cut,bars=len(prefix),mismatches=0))
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"causal_prefix_checks.json").write_text(json.dumps(prefix_checks,indent=2))
    output={"source_commit":"5d879b3d04031952f41d2b4d4c4a3cce43f04150","data_hashes":hashes,"fee_each_side_including_gst":FEE,"slippage":0,"funding":"unmodeled","daily_bars":len(daily),"results":[]}
    for name in ("two_b","wavelet_two_b"):
        sig=signals(daily,name)
        output["results"].append(replay(minute,daily,sig,name))
    (OUT/"summary.json").write_text(json.dumps(output,indent=2))
    print(json.dumps(output["results"],indent=2))
if __name__=="__main__":main()
