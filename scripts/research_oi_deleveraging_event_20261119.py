#!/usr/bin/env python3
"""Pre-registered institution-style OI deleveraging event study, BTCUSD and ETHUSD.

Economic hypothesis: extreme 1h falls in OI concurrent with a large directional
1h price move signify forced position closure. Test whether follow-through has
positive asymmetric net expectancy. Exact same events also tested with the
OPPOSITE direction as a falsification control. No retail indicator optimization.

All evidence from Delta India 1m trade candles, OI:... 5m and FUNDING:... 1h.
OI is a proxy for aggregate positioning, NOT verified liquidation prints.
Signals use only fully completed 5m candles + PREVIOUS 21-day OI lower-tail.
Fill at next 5m minute open, fixed ATR stop, wide 4 x ATR trailing, 1m wick fills.
One open position, no artificial profit target, fixed 0.5% initial equity risk.
Cost 0.05% taker each fill + 18% GST, 2bps slip, proxy funding at 8h UTC
settlements. Stress test same rules at 6bps slip, no parameter curve fitting.
2025 is already research-exposed, 2026 is NOT a pristine holdout.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from numba import njit

BASE=Path("data/delta_india")
OUT=Path("analysis/oi_deleveraging_event_study_20261119")
ASSETS=("BTCUSD","ETHUSD")
INITIAL=1000.
RISK=.005
FEE=.0005*1.18
GAP_FUND_CHARGE=.0001
MAX_LEVERAGE=8.
START=pd.Timestamp("2025-01-01T00:00:00Z")
END=pd.Timestamp("2026-11-18T00:00:00Z")
NMONTHS=23

def load_months(folder,columns):
    fs=sorted(folder.glob("20??-??.csv.gz"))
    if len(fs)!=23:raise RuntimeError(f"{folder}: expected 23 partitions, found {len(fs)}")
    chunks=[]
    for f in fs:
        d=pd.read_csv(f,compression="gzip",usecols=columns)
        if len(d)==0:raise RuntimeError(f"empty {f}")
        chunks.append(d)
    x=pd.concat(chunks,ignore_index=True).sort_values("time")
    t=x.time.to_numpy(np.int64)
    if np.any(np.diff(t)<=0):raise RuntimeError(f"{folder} timestamps duplicated/out of order")
    x.index=pd.to_datetime(t,unit="s",utc=True)
    return x

def load_asset(symbol):
    p=load_months(BASE/symbol/"1m",["time","open","high","low","close","volume"])
    t=p.time.to_numpy(np.int64)
    if t[0]!=int(START.timestamp()) or t[-1]!=int(END.timestamp())-60:
        raise RuntimeError(f"{symbol} dataset boundaries mismatch")
    if not np.all(np.diff(t)==60):raise RuntimeError(f"{symbol} price archive contains gaps")
    for c in ("open","high","low","close"):
        if not np.isfinite(p[c].to_numpy(float)).all():raise RuntimeError(f"{symbol} invalid prices")
    if ((p.low<=0)|(p.open<p.low)|(p.open>p.high)|
        (p.close<p.low)|(p.close>p.high)).any():raise RuntimeError("impossible OHLC")
    oi=load_months(BASE/symbol/"institutional/history/open_interest_5m",["time","close"])
    oi=oi.close.astype(float)
    if not np.isfinite(oi).all() or (oi<=0).any():
        raise RuntimeError(f"{symbol} OI nonpositive/nonfinite: no safe shock signal")
    # Pandas 3 may store DatetimeIndex in seconds, not nanoseconds.
    # Explicit conversion avoids false data-gap flags from .view("int64").
    delta=np.diff(oi.index.as_unit("s").asi8)
    bad=int(np.count_nonzero(delta != 300))
    if bad:
        ix=np.flatnonzero(delta != 300*10**9)
        print("WARN OI TIMESTAMPS",symbol,"irregular gaps",bad,
            "examples",[(str(oi.index[k]),str(oi.index[k+1]),int(delta[k]))
                        for k in ix[:5]],flush=True)
    # Later align against full 5m clock with NaNs; never forward fill OI.
    funding=load_months(BASE/symbol/"institutional/history/funding_1h",["time","close"])
    funding=funding.drop_duplicates("time",keep="last")
    if not np.isfinite(funding.close).all():raise RuntimeError("invalid funding series")
    return p,oi,funding

def engineer(p,oi,fr):
    b=p[["open","high","low","close","volume"]].resample("5min",label="left",closed="left").agg(
        {"open":"first","high":"max","low":"min","close":"last","volume":"sum"})
    counts=p.close.resample("5min",label="left",closed="left").count()
    if not counts.eq(5).all():raise RuntimeError("5 minute bar incomplete")
    o=oi.reindex(b.index)
    missing=int(o.isna().sum())
    if missing>len(o)*0.05:raise RuntimeError(f"missing OI >5% ({missing}/{len(o)})")
    # Missing OI -> NaN returns and NaN signals, no synthetic OI candles.
    # OI 1h delta; lower fifth percentile computed from PRIOR rolling 21d
    # with no less than 14d of fully observed historical changes.
    oi_ret=o/o.shift(12)-1.
    lower=oi_ret.rolling(21*288,min_periods=14*288).quantile(.05).shift(1)
    # Normalized price 1h move, threshold based on prior 3d only.
    hrret=b.close/b.close.shift(12)-1.
    ref=hrret.abs().rolling(3*288,min_periods=3*288).median().shift(1)
    oi_shock=(oi_ret<lower)&(oi_ret<0)
    move=(hrret.abs()>=1.5*ref)&ref.gt(0)
    candidate=oi_shock&move
    # One event on the transition into an OI shock, not repeated each 5m.
    event=candidate & ~candidate.shift(1,fill_value=False)
    side5=np.where(event,np.where(hrret>0,1,-1),0).astype(np.int8)
    # ATR from PREVIOUSLY COMPLETED 1h candles, used for risk, not signal.
    h=p[["high","low","close"]].resample("1h",label="right",closed="left").agg(
        {"high":"max","low":"min","close":"last"})
    pc=h.close.shift(1)
    true_range=pd.concat((h.high-h.low,(h.high-pc).abs(),(h.low-pc).abs()),axis=1).max(axis=1)
    atr=true_range.ewm(alpha=1/14,adjust=False,min_periods=14).mean()
    bar_end=b.index+pd.Timedelta(minutes=5)
    stop_atr=atr.reindex(bar_end,method="ffill")
    side5=np.where(np.isfinite(stop_atr)&(stop_atr>0),side5,0)
    t=p.time.to_numpy(np.int64);n=len(p)
    signal=np.zeros(n,np.int8);sig_atr=np.zeros(n,np.float64)
    at=np.flatnonzero(side5)
    for j in at:
        utc_s=int((b.index[j]+pd.Timedelta(minutes=5)).timestamp())
        k=int(np.searchsorted(t,utc_s))
        if k<n and t[k]==utc_s:
            signal[k]=side5[j];sig_atr[k]=float(stop_atr.iloc[j])
    fundrate={int(ts)+3600:float(val)/100.
        for ts,val in zip(fr.time.to_numpy(np.int64),fr.close.to_numpy(float))
        if np.isfinite(val) and abs(val)<5}
    funding=np.zeros(n,np.float64)
    unknown=0
    for k in np.flatnonzero(t%28800==0):
        v=fundrate.get(int(t[k]))
        if v is None:v=np.nan;unknown+=1
        funding[k]=v
    return signal,sig_atr,funding,{
        "complete_5m_oi_rows":int(o.notna().sum()),"missing_5m_oi_rows":missing,
        "OI_1h_shock_observations":int(oi_shock.sum()),
        "raw_event_count":int(event.sum()),"executable_event_count":int((signal!=0).sum()),
        "long_events":int((signal==1).sum()),"short_events":int((signal==-1).sum()),
        "funding_missing_8h_observations":unknown,
        "OI_1h_delta_quantile":".05 trailing 21 days shifted prior",
        "price_impulse":"absolute 1h return >=1.5x prior three-day rolling median",
        "entry":"next 5m open","exit":"1h ATR initial stop and 4x ATR wide trailing"}

@njit(cache=True)
def run(t,o,h,l,c,signals,atrs,funding,mid,style,slip):
    equity=INITIAL;entry_equity=0.;qty=0.;side=0;entry_fill=0.
    entry_i=0;init_R=0.;atr=0.;extreme=0.;stop=0.
    paid_fees=0.;paid_fund=0.;trade_fees=0.;trade_fund=0.
    peak=INITIAL;maxdd=0.;ntrades=0;blocked=0
    m=np.full(NMONTHS,np.nan);ment=np.zeros(NMONTHS,np.int32)
    mactive=np.zeros(NMONTHS,np.bool_)
    ledger=np.empty((3000,9),np.float64)
    for i in range(len(t)):
        exited=False
        if side!=0:
            mactive[mid[i]]=True
            # trailing uses highest/lowest previously COMPLETED 1m bar;
            # cannot revise a stop using future high in same 1m candle.
            if side==1:
                candidate=extreme-4.*atr
                if candidate>stop:stop=candidate
            else:
                candidate=extreme+4.*atr
                if candidate<stop:stop=candidate
            if t[i]%28800==0:
                if np.isnan(funding[i]):
                    charge=abs(qty*o[i])*GAP_FUND_CHARGE
                else:
                    charge=side*qty*o[i]*funding[i]
                equity-=charge;trade_fund+=charge;paid_fund+=charge
            touched=(l[i]<=stop if side==1 else h[i]>=stop)
            if touched:
                stop_mid=min(o[i],stop) if side==1 else max(o[i],stop)
                fill=stop_mid*(1-side*slip)
                net_price=side*qty*(fill-entry_fill)
                fee=FEE*abs(qty*fill)
                equity+=net_price-fee
                paid_fees+=fee;trade_fees+=fee
                if ntrades>=len(ledger):raise ValueError("trade buffer overflow")
                ledger[ntrades,0]=t[entry_i]
                ledger[ntrades,1]=t[i]
                ledger[ntrades,2]=side
                ledger[ntrades,3]=equity-entry_equity
                ledger[ntrades,4]=(equity-entry_equity)/init_R
                ledger[ntrades,5]=trade_fees
                ledger[ntrades,6]=trade_fund
                ledger[ntrades,7]=entry_fill
                ledger[ntrades,8]=fill
                ntrades+=1;side=0;qty=0.;exited=True
            else:
                if side==1 and h[i]>extreme:extreme=h[i]
                if side==-1 and l[i]<extreme:extreme=l[i]
        if side==0 and not exited and signals[i]!=0 and atrs[i]>0 and equity>0:
            proposed_side=int(signals[i])*style
            at=atrs[i]
            riskcash=RISK*equity
            unit=1.0*at
            price=o[i]*(1+proposed_side*slip)
            amount=riskcash/unit
            if amount*price<=8.*equity:
                side=proposed_side;qty=amount;atr=at;init_R=riskcash
                entry_fill=price;entry_i=i;entry_equity=equity
                stop=price-side*unit;extreme=price
                fee=FEE*qty*price;equity-=fee;paid_fees+=fee
                trade_fees=fee;trade_fund=0.
                ment[mid[i]]+=1;mactive[mid[i]]=True
            else:blocked+=1
        if side!=0:
            liq=c[i]*(1-side*slip)
            mark=equity+side*qty*(liq-entry_fill)-FEE*qty*liq
        else:mark=equity
        if mark>peak:peak=mark
        if peak>0 and (mark/peak-1)<maxdd:maxdd=mark/peak-1
        if i==len(t)-1 or mid[i+1]!=mid[i]:
            m[mid[i]]=mark
    if side!=0:
        i=len(t)-1
        fill=c[i]*(1-side*slip)
        fee=FEE*qty*fill;equity+=side*qty*(fill-entry_fill)-fee
        paid_fees+=fee;trade_fees+=fee
        ledger[ntrades,0]=t[entry_i];ledger[ntrades,1]=t[i]
        ledger[ntrades,2]=side;ledger[ntrades,3]=equity-entry_equity
        ledger[ntrades,4]=(equity-entry_equity)/init_R
        ledger[ntrades,5]=trade_fees;ledger[ntrades,6]=trade_fund
        ledger[ntrades,7]=entry_fill;ledger[ntrades,8]=fill
        ntrades+=1;m[mid[-1]]=equity
    return equity,m,ment,mactive,ledger[:ntrades],paid_fees,paid_fund,maxdd,blocked

def report(symbol,style,slippage,run_out,months):
    cash,marks,entries,active,arr,fees,funds,dd,blocked=run_out
    w=arr[arr[:,3]>0,3];loss=arr[arr[:,3]<0,3]
    wins=len(w);losses=len(loss)
    if len(arr):
        pf=float(w.sum()/-loss.sum()) if len(loss) else None
        wr=float(wins/len(arr))*100
        ratio=float(w.mean()/-loss.mean()) if len(w) and len(loss) else None
        biggest=float(arr[:,4].max())
    else:pf=None;wr=None;ratio=None;biggest=None
    eqprev=INITIAL
    monthly=[]
    for j,mon in enumerate(months):
        val=float(marks[j]);pct=(val/eqprev-1)*100
        monthly.append(dict(symbol=symbol,scenario=style,slip_bps=int(slippage*10000),
            month_ist=mon,net_return_pct=round(pct,4),end_equity=round(val,4),
            entries=int(entries[j]),position_exposure=bool(active[j])))
        eqprev=val
    x=list(arr[:,3]) if len(arr) else []
    maxlosstreak=cur=0
    for v in x:
        if v<=0:cur+=1;maxlosstreak=max(cur,maxlosstreak)
        else:cur=0
    biggest_winner_usd=float(max(w)) if len(w) else 0
    concentration=biggest_winner_usd/float(w.sum()) if len(w) else 0
    row=dict(symbol=symbol,scenario=style,slip_bps=slippage*10000,
        closed_trades=len(arr),wins=wins,losses=losses,win_rate_pct=wr,
        avg_win_over_avg_loss=ratio,profit_factor=pf,
        biggest_winner_R=biggest,winners_ge_10R=int((arr[:,4]>=10).sum()),
        max_consecutive_losses=maxlosstreak,top_winner_pct_of_gross_wins=round(100*concentration,3),
        net_return_total_pct=round(100*(cash/INITIAL-1),3),
        return_2025_pct=round(100*(marks[11]/INITIAL-1),3),
        return_2026_through_nov17_pct=round(100*(marks[-1]/marks[11]-1),3),
        max_MTM_drawdown_pct=round(100*dd,3),fees_GST_usd=round(fees,3),
        funding_proxy_usd=round(funds,3),blocked_leverage=blocked,
        profitable_months=sum(x["net_return_pct"]>0 for x in monthly),
        losing_months=sum(x["net_return_pct"]<0 for x in monthly))
    trades=[]
    for rowtrade in arr:
        trades.append(dict(symbol=symbol,scenario=style,slip_bps=int(slippage*10000),
            entry_utc=pd.to_datetime(int(rowtrade[0]),unit="s",utc=True).isoformat(),
            exit_utc=pd.to_datetime(int(rowtrade[1]),unit="s",utc=True).isoformat(),
            side="LONG" if rowtrade[2]==1 else "SHORT",
            pnl_usd=round(rowtrade[3],5),net_R=round(rowtrade[4],4),
            fees_GST=round(rowtrade[5],5),funding_proxy=round(rowtrade[6],5),
            entry_fill=round(rowtrade[7],5),exit_fill=round(rowtrade[8],5)))
    return row,monthly,trades

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    bounds=pd.date_range("2025-01-01","2026-12-01",tz="Asia/Kolkata",freq="MS").tz_convert("UTC")
    ub=np.array([int(x.timestamp()) for x in bounds],np.int64)
    monthnames=bounds.tz_convert("Asia/Kolkata").strftime("%Y-%m").tolist()[:-1]
    if len(monthnames)!=NMONTHS:raise AssertionError("month label count")
    allsum=[];allmonth=[];alltrades=[];qual=[]
    scenarios=(("follow",1,.0002),("opposite_control",-1,.0002),("follow_stressed",1,.0006))
    for symbol in ASSETS:
        print("READING",symbol,flush=True)
        p,oi,funding=load_asset(symbol)
        sig,at,fr,dat=engineer(p,oi,funding)
        t=p.time.to_numpy(np.int64)
        mid=np.searchsorted(ub,t,side="right")-1
        if mid.min()<0 or mid.max()>=NMONTHS:raise RuntimeError("bad IST month index")
        vals=[p[c].to_numpy(np.float64) for c in ("open","high","low","close")]
        qual.append(dict(symbol=symbol,min_utc=str(p.index.min()),max_utc=str(p.index.max()),
            candle_count=len(p),price_missing_minutes=int((t[-1]-t[0])//60+1-len(p)),**dat))
        for name,sign,slip in scenarios:
            print("REPLAY",symbol,name,flush=True)
            result=run(t,*vals,sig,at,fr,mid,sign,slip)
            met,monthly,trades=report(symbol,name,slip,result,monthnames)
            allsum.append(met);allmonth+=monthly;alltrades+=trades
            print("RESULT",json.dumps(met),flush=True)
    summary=pd.DataFrame(allsum)
    monthly=pd.DataFrame(allmonth)
    ledger=pd.DataFrame(alltrades)
    summary.to_csv(OUT/"summary.csv",index=False)
    monthly.to_csv(OUT/"monthly_ist.csv",index=False)
    ledger.to_csv(OUT/"trades.csv.gz",index=False,compression="gzip")
    passed=summary[(summary.scenario=="follow")&
        (summary.return_2025_pct>500)&(summary.return_2026_through_nov17_pct>0)&
        (summary.profit_factor>=1.5)&(summary.avg_win_over_avg_loss>=5)&
        (summary.biggest_winner_R>=10)&(summary.win_rate_pct<=40)&
        (summary.closed_trades>=30)&(summary.max_MTM_drawdown_pct>=-30)]
    evidence=dict(hypothesis="Aggregate position deleveraging OI shock and one-hour momentum creates directional price follow-through",
        falsification="exact same event set traded in opposite direction, same risk and fees",
        cost_stress="exact same follow-through rule with slip increased 2 to 6bps each fill",
        past_data="2025-01-01 through 2026-11-17, full BTC and ETH 1min plus OI 5m funding 1h",
        no_grid="fixed event threshold 5th percentile of prior 21d OI 1h changes; price impulse >=1.5x previous 3d median",
        funding="prior 1h candle as rate proxy in PERCENT units, charged at 00/08/16 UTC; absent settlement 0.01% charge",
        fee="0.05% each taker fill + GST 18%, no maker rebate",
        capital="1000 USD hypothetical fractional futures, 0.5% initial risk, <=8x notional cap",
        pass_count=int(len(passed)),data=qual,
        caveats=["OI fall does not uniquely prove liquidation; no real liquidation tape",
            "Historical Delta funding candles proxy, not verified executed funding payments",
            "1minute OHLC fill stop is pessimistic open-through-gap but not order-book execution",
            "Pyramiding is deliberately NOT used; cannot manufacture +500% with leverage",
            "2025 research-exposed; 2026 partial through November 17 and research-exposed",
            "Market microstructure hypothesis requires a placebo and future-forward validation",
            "EMA/ATR grid not used; 1h ATR used solely for risk management",
            "This analysis does not provide live execution or a trading recommendation"] )
    (OUT/"quality.json").write_text(json.dumps(evidence,indent=2)+"\n")
    lines=["# Institutional falsification: OI deleveraging and momentum",
        "", "## Pre-registered mechanism","When open-interest collapses in an exceptional directional price impulse,",
        "forced position closure may either accelerate price discovery (follow-through)",
        "or exhaust the move (opposite-direction control). Test BOTH at exactly",
        "the same event timestamps with identical costs and risk.","",
        "## Exact independent backtest results",summary.to_markdown(index=False),"",
        "## Monthly net NAV including mark-to-market liquidation costs",
        monthly.to_markdown(index=False),"",
        f"## High-return asymmetric qualification: {len(passed)}",
        passed.to_markdown(index=False) if len(passed) else "No qualifying strategy.", "",
        "## Data and execution caveats", *["- "+v for v in evidence["caveats"]],"",
        "Full trade evidence in trades.csv.gz; script scripts/research_oi_deleveraging_event_20261119.py"]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(lines)+"\n")
    print("RUN_COMPLETE",len(summary),len(ledger),"passing",len(passed),flush=True)

if __name__=="__main__":main()
