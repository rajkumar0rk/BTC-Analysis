#!/usr/bin/env python3
"""Stage25 paired BTC/ETH: high-volume absorption then directional displacement.
New rule family; 2025-only shared selection, 2026 historical recheck.
This is NOT an executable investment recommendation or an OOS validation.
"""
from pathlib import Path
import hashlib,json
import numpy as np
import pandas as pd
from numba import njit

ROOT=Path("data/delta_india")
OUT=Path("analysis/paired_absorption_displacement_stage25")
MONTHS=pd.period_range("2025-01","2026-10",freq="M").astype(str).tolist()
FEE=.0005*1.18
INIT_EQUITY=10000.
RISK_FRAC=.005
LEV_CAP=3.
HOLD_MIN=480
CONFIGS=[(v,r,a,reward,align) for v in (1.2,1.6)
         for r in (1.0,1.4) for a in (1.5,2.5)
         for reward in (2.,3.) for align in (False,True)]

def load_native(symbol):
    directory=ROOT/symbol/"1m"
    meta=json.loads((directory/"manifest.json").read_text())
    parts=[p for p in meta["partitions"] if "2025-01.csv.gz"<=p["file"]<="2026-11.csv.gz"]
    if len(parts)!=23:raise AssertionError(f"{symbol}: source monthly partitions {len(parts)} !=23")
    frames=[];hashes={}
    for p in parts:
        file=directory/p["file"]
        raw=file.read_bytes()
        digest=hashlib.sha256(raw).hexdigest()
        if digest!=p["sha256_gzip"]:raise AssertionError("Invalid source hash "+str(file))
        hashes[p["file"]]=digest
        x=pd.read_csv(file,compression="gzip",
           usecols=["time","open","high","low","close","volume"])
        if len(x)!=p["observed_candles"] or p["missing_minutes"]:
            raise AssertionError("Missing source candles "+str(file))
        frames.append(x)
    f=pd.concat(frames,ignore_index=True).sort_values("time",kind="stable").reset_index(drop=True)
    secs=f.time.to_numpy(np.int64)
    if np.any(np.diff(secs)!=60):raise AssertionError(symbol+" gap, duplicate or reverse data")
    a=f[["open","high","low","close","volume"]].to_numpy(float)
    if not np.isfinite(a).all():raise AssertionError(symbol+" invalid candles")
    if ((f.low<=0)|(f.high<f.low)|(f.open<f.low)|(f.open>f.high)|
        (f.close<f.low)|(f.close>f.high)|(f.volume<0)).any():
        raise AssertionError(symbol+" OHLCV inconsistency")
    f.index=pd.to_datetime(secs,unit="s",utc=True)
    cutoff=pd.Timestamp("2026-10-31T18:30:00Z")
    if f.index.min()!=pd.Timestamp("2025-01-01T00:00:00Z"):
        raise AssertionError(symbol+" archive start inconsistent")
    f=f.loc[f.index<cutoff].copy()
    if f.index.max()!=cutoff-pd.Timedelta(minutes=1):
        raise AssertionError(symbol+" October IST final minute missing")
    actual=pd.Series(1,index=f.index.tz_convert("Asia/Kolkata")).resample("MS").sum()
    coverage={}
    for month in MONTHS:
        start=pd.Timestamp(month+"-01",tz="Asia/Kolkata")
        following=start+pd.offsets.MonthBegin(1)
        wanted=int((following-start)/pd.Timedelta(minutes=1))
        got=int(actual.get(start,0))
        gap=330 if month=="2025-01" else 0
        if got!=wanted-gap:
            raise AssertionError(f"{symbol} IST {month} {got}/{wanted} minute completeness")
        coverage[month]={"observed":got,"expected":wanted,"missing":wanted-got}
    return f,{"symbol":symbol,"first_utc":str(f.index[0]),"last_utc":str(f.index[-1]),
      "partition_SHA256":hashes,"IST_months":coverage,
      "initial_2025_IST_gap_minutes":330,"October_2026_UTC_archive_complete":True}

def make_events(f):
    b=f[["open","high","low","close","volume"]].resample(
        "15min",label="right",closed="left").agg(
        {"open":"first","high":"max","low":"min","close":"last","volume":"sum"})
    b["n"]=f.close.resample("15min",label="right",closed="left").count()
    b["valid"]=b.n.rolling(100,min_periods=100).min().eq(15)
    span=(b.high-b.low).replace(0,np.nan)
    pclose=b.close.shift(1)
    tr=pd.concat([b.high-b.low,(b.high-pclose).abs(),(b.low-pclose).abs()],axis=1).max(axis=1)
    b["atr"]=tr.rolling(14,min_periods=14).mean()
    b["setup_vratio"]=b.volume.shift(1)/b.volume.shift(2).rolling(
        32,min_periods=32).mean().replace(0,np.nan)
    b["setup_rratio"]=span.shift(1)/span.shift(2).rolling(
        32,min_periods=32).median().replace(0,np.nan)
    b["setup_body"]=(b.close.shift(1)-b.open.shift(1)).abs()/span.shift(1)
    b["trigger_location"]=(b.close-b.low)/span
    b["trigger_vratio"]=b.volume/b.volume.shift(1).rolling(
        20,min_periods=20).mean().replace(0,np.nan)
    # 1h candles have right-edge timestamps, so ffill uses completed hours only.
    h=f[["close"]].resample("1h",label="right",closed="left").agg({"close":"last"})
    h["n"]=f.close.resample("1h",label="right",closed="left").count()
    h["valid"]=h.n.rolling(60,min_periods=60).min().eq(60)
    h["ema20"]=h.close.ewm(span=20,adjust=False).mean()
    h["ema50"]=h.close.ewm(span=50,adjust=False).mean()
    hb=h.reindex(b.index,method="ffill")
    b["trend_long"]=((hb.valid)&(hb.ema20>hb.ema50)&
        (hb.close>hb.ema20)).fillna(False).to_numpy(bool)
    b["trend_short"]=((hb.valid)&(hb.ema20<hb.ema50)&
        (hb.close<hb.ema20)).fillna(False).to_numpy(bool)
    is_long=(b.close>b.high.shift(1))&(b.close>b.open)&(b.trigger_location>=.65)
    is_short=(b.close<b.low.shift(1))&(b.close<b.open)&(b.trigger_location<=.35)
    good=b.valid&(b.setup_body<=.55)&(b.trigger_vratio>=.8)&b.atr.gt(0)
    mapped=f.index.get_indexer(b.index)
    events=[]
    for i in np.flatnonzero(good.to_numpy(bool)):
        k=int(mapped[i])
        if k<1500:continue
        side=1 if bool(is_long.iat[i]) else -1 if bool(is_short.iat[i]) else 0
        if not side:continue
        vr=float(b.setup_vratio.iat[i]);rr=float(b.setup_rratio.iat[i])
        atr=float(b.atr.iat[i])
        if not (np.isfinite(vr) and np.isfinite(rr) and np.isfinite(atr)):continue
        aligned=bool(b.trend_long.iat[i]) if side==1 else bool(b.trend_short.iat[i])
        events.append((k,side,vr,rr,atr,aligned))
    return np.array(events,dtype=np.float64).reshape(-1,6)

@njit(cache=True)
def exit_replay(op,hi,lo,cl,k,side,risk,reward,hold):
    ent=op[k];stop=ent-side*risk;target=ent+side*reward*risk
    worst=ent
    end=min(k+hold,len(op))
    for j in range(k,end):
        adverse=lo[j] if side==1 else hi[j]
        if side*(adverse-worst)<0:worst=adverse
        if (side==1 and lo[j]<=stop) or (side==-1 and hi[j]>=stop):
            px=min(op[j],stop) if side==1 else max(op[j],stop)
            return j,px,0,worst
        if (side==1 and hi[j]>=target) or (side==-1 and lo[j]<=target):
            return j,target,1,worst
    return end-1,cl[end-1],2,worst

def simulate(f,events,symbol,stress=False):
    op=f.open.to_numpy(float);hi=f.high.to_numpy(float)
    lo=f.low.to_numpy(float);cl=f.close.to_numpy(float)
    unix=f.time.to_numpy(np.int64)
    slip_abs=10. if stress else 5.
    slip_relative=.00035 if stress else .0002
    records=[];results=[]
    for vt,cap,sm,rr,aligned in CONFIGS:
        eq=INIT_EQUITY;peak=eq;dd=0.;busy=-1
        for kf,sf,v,range_ratio,atr,trend in events:
            k=int(kf);side=int(sf)
            if k<=busy or v<vt or range_ratio>cap or (aligned and not bool(trend)):continue
            mid=float(op[k]);risk=float(atr*sm)
            if not np.isfinite(risk) or risk<=0 or risk/mid>.15:continue
            in_slip=slip_abs if symbol=="BTCUSD" else mid*slip_relative
            fill_in=mid+side*in_slip
            qty=min(eq*RISK_FRAC/risk,eq*LEV_CAP/fill_in)
            if qty<=0:continue
            j,exit_mid,reason,worst=exit_replay(op,hi,lo,cl,k,side,risk,rr,HOLD_MIN)
            busy=j
            out_slip=slip_abs if symbol=="BTCUSD" else exit_mid*slip_relative
            fill_out=exit_mid-side*out_slip
            pnl=float(qty*(side*(fill_out-fill_in)-FEE*(fill_in+fill_out)))
            adverse_exit=worst-side*(slip_abs if symbol=="BTCUSD" else worst*slip_relative)
            worst_eq=eq+qty*(side*(adverse_exit-fill_in)-FEE*(fill_in+adverse_exit))
            dd=max(dd,100*(1-min(worst_eq,eq)/peak))
            start_eq=eq
            eq+=pnl
            peak=max(peak,eq)
            dd=max(dd,100*(1-eq/peak))
            if eq<=0:raise RuntimeError("Equity bankruptcy")
            records.append({"symbol":symbol,"vol_threshold":vt,"range_cap":cap,
                "atr_stop":sm,"reward_R":rr,"trend_align":aligned,"stress":stress,
                "entry_unix":int(unix[k]),"exit_unix":int(unix[j]),"side":side,
                "entry_mid":mid,"exit_mid":float(exit_mid),"entry_fill":fill_in,
                "exit_fill":fill_out,"quantity":qty,"start_equity_usd":start_eq,
                "ending_equity_usd":eq,"risk_distance":risk,"leverage":qty*fill_in/start_eq,
                "net_usd":pnl,"reason":("stop","target","timeout")[reason]})
        results.append({"symbol":symbol,"vol_threshold":vt,"range_cap":cap,
            "atr_stop":sm,"reward_R":rr,"trend_align":aligned,"stress":stress,
            "final_equity":eq,"max_drawdown_pct":dd})
    return pd.DataFrame(records),pd.DataFrame(results)

def profit_factor(vals):
    a=np.asarray(vals,dtype=float)
    if not len(a):return None
    gains=a[a>0].sum();losses=-a[a<0].sum()
    return float(gains/losses) if losses else (float("inf") if gains else None)

def audit_accounts(ledger,metrics):
    keys=["symbol","vol_threshold","range_cap","atr_stop","reward_R","trend_align","stress"]
    ledger["month_ist"]=pd.to_datetime(ledger.exit_unix,unit="s",utc=True
        ).dt.tz_convert("Asia/Kolkata").dt.strftime("%Y-%m")
    months=[];summaries=[]
    for key,g in ledger.groupby(keys,sort=True):
        g=g.sort_values(["exit_unix","entry_unix"],kind="stable")
        metric=metrics
        for col,val in zip(keys,key):metric=metric[metric[col]==val]
        if len(metric)!=1:raise AssertionError("Missing scenario metric")
        meta=metric.iloc[0]
        equity=INIT_EQUITY;rows=[]
        for mon in MONTHS:
            m=g[g.month_ist==mon]
            pnl=float(m.net_usd.sum());start=equity;equity+=pnl
            row=dict(zip(keys,key))
            row.update(month_ist=mon,trades=len(m),
                wins=int((m.net_usd>0).sum()),losses=int((m.net_usd<0).sum()),
                breakeven=int((m.net_usd==0).sum()),
                profit_usd=float(m.net_usd.clip(lower=0).sum()),
                loss_usd=float(m.net_usd.clip(upper=0).sum()),
                profit_factor=profit_factor(m.net_usd),
                net_return_pct=100*pnl/start,start_equity=start,end_equity=equity)
            months.append(row);rows.append(row)
        m=pd.DataFrame(rows)
        if len(m)!=22 or m.trades.sum()!=len(g):raise AssertionError("Monthly count parity")
        if not np.isclose(equity,meta.final_equity,atol=1e-7):
            raise AssertionError("Monthly full-ledger equity parity")
        meaningful=m[(m.trades>=3)&np.isfinite(m.profit_factor)]
        in2025=g[g.month_ist.str.startswith("2025-")]
        in2026=g[g.month_ist.str.startswith("2026-")]
        v=m.net_return_pct.to_numpy(float)
        s=dict(zip(keys,key))
        s.update(trades=len(g),wins=int((g.net_usd>0).sum()),
            losses=int((g.net_usd<0).sum()),overall_PF=profit_factor(g.net_usd),
            PF_2025=profit_factor(in2025.net_usd),
            PF_2026_YTD=profit_factor(in2026.net_usd),
            strong_months=int(((m.profit_factor>=1.5)&(m.trades>=3)).sum()),
            strong_and_positive=int(((m.profit_factor>=1.5)&(m.trades>=3)&(m.net_return_pct>0)).sum()),
            strong_and_5pct=int(((m.profit_factor>=1.5)&(m.trades>=3)&(m.net_return_pct>=5)).sum()),
            months_5pct=int((v>=5).sum()),months_10pct=int((v>=10).sum()),
            months_20pct=int((v>=20).sum()),positive_months=int((v>0).sum()),
            negative_months=int((v<0).sum()),zero_trade_months=int((m.trades==0).sum()),
            median_month_return_pct=float(np.median(v)),
            median_finite_month_PF=float(meaningful.profit_factor.median()) if len(meaningful) else None,
            worst_month_pct=float(v.min()),
            net_2025_full_year_pct=100*(m.iloc[11].end_equity/INIT_EQUITY-1),
            net_2026_Jan_Oct_YTD_pct=100*(m.iloc[-1].end_equity/m.iloc[11].end_equity-1),
            total_22mo_net_pct=100*(equity/INIT_EQUITY-1),
            max_drawdown_pct=float(meta.max_drawdown_pct),
            full_year_2025_exceeds_500pct=bool(m.iloc[11].end_equity>INIT_EQUITY*6),
            final_equity_usd=equity)
        summaries.append(s)
    return pd.DataFrame(months),pd.DataFrame(summaries)

def match(df,row):
    for name in ("vol_threshold","range_cap","atr_stop","reward_R","trend_align"):
        df=df[df[name]==row[name]]
    return df

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    evidence=[];scenarios=[];qualities={};events_count={}
    for symbol in ("BTCUSD","ETHUSD"):
        f,quality=load_native(symbol)
        qualities[symbol]=quality
        events=make_events(f)
        events_count[symbol]=len(events)
        if not len(events):raise RuntimeError("No signals "+symbol)
        for stress in (False,True):
            ledger,metric=simulate(f,events,symbol,stress)
            if ledger.empty:raise RuntimeError("No executable trades "+symbol)
            evidence.append(ledger);scenarios.append(metric)
    alltrades=pd.concat(evidence,ignore_index=True)
    metrics=pd.concat(scenarios,ignore_index=True)
    alltrades.to_csv(OUT/"all_original_trade_ledgers.csv.gz",compression="gzip",index=False)
    monthly,stats=audit_accounts(alltrades,metrics)
    monthly.to_csv(OUT/"all_monthly.csv.gz",compression="gzip",index=False)
    stats.to_csv(OUT/"all_summary.csv",index=False)
    base=stats[~stats.stress].copy()
    names=["vol_threshold","range_cap","atr_stop","reward_R","trend_align"]
    ranks=[]
    for setting,grp in base.groupby(names):
        if len(grp)!=2:raise AssertionError("Missing paired backtest")
        x=match(monthly,dict(zip(names,setting)))
        x=x[(~x.stress)&x.month_ist.str.startswith("2025-")]
        ranks.append(dict(zip(names,setting),
            strong_5pct_2025=int(((x.profit_factor>=1.5)&(x.trades>=3)&(x.net_return_pct>=5)).sum()),
            strong_2025=int(((x.profit_factor>=1.5)&(x.trades>=3)).sum()),
            profitable_2025=int((x.net_return_pct>0).sum()),
            median_return_2025=float(x.net_return_pct.median()),
            trade_sample_2025=int(x.trades.sum()),
            worst_month_2025=float(x.net_return_pct.min()),
            drawdown=float(grp.max_drawdown_pct.max())))
    ranking=pd.DataFrame(ranks).sort_values(
        ["strong_5pct_2025","strong_2025","profitable_2025","median_return_2025",
         "trade_sample_2025","drawdown"],
        ascending=[False,False,False,False,False,True],kind="stable")
    ranking.to_csv(OUT/"shared_2025_only_rank.csv",index=False)
    choice=ranking.iloc[0]
    selected_month=match(monthly,choice)
    selected_month=selected_month[~selected_month.stress].sort_values(["month_ist","symbol"])
    selected_month.to_csv(OUT/"selected_22_months.csv",index=False)
    selected_stats=match(stats,choice)
    selected_stats.to_csv(OUT/"selected_summaries.csv",index=False)
    selected_ledger=match(alltrades,choice)
    selected_ledger.to_csv(OUT/"selected_original_trade_ledger.csv.gz",index=False,compression="gzip")
    audit={"hypothesis":"15m high-volume narrow-body absorption followed by next completed 15m bar close beyond setup high/low; enter first 1m open in break direction",
      "parameter_selection":"single shared BTC/ETH setting using 2025 monthly outcomes only",
      "2026_holdout":"Previously researched, not independently untouched",
      "models_per_market":len(CONFIGS),"candidate_events_per_market":events_count,
      "source_quality":qualities,
      "cost_model":{"fee_each_side":.0005,"GST_on_fees":.18,
        "BTC_slip_points_each_side_base":5,"BTC_stress":10,
        "ETH_slip_fraction_each_side_base":.0002,"ETH_stress":.00035},
      "capital_model":{"initial_usd":INIT_EQUITY,"risk_frac":RISK_FRAC,
         "max_leverage":LEV_CAP,"max_hold_minutes":HOLD_MIN},
      "unmodeled":["funding settlement cashflow","historical bid-ask order book spreads",
         "depth/impact beyond conservative slippage proxy","contract minimum quantities",
         "actual exchange risk tiers, margin and liquidation"],
      "other_limits":["Jan 2025 IST first 330 minutes unavailable",
        "source manifests and compressed source hashes verified in run",
        "open-position drawdown based on 1m OHLC adverse wick rather than tick path",
        "2026 research-exposed, not pristine forward test",
        "no future trade labels, month-based skipping or post-2025 parameter changes"]}
    (OUT/"quality.json").write_text(json.dumps(audit,indent=2,default=str)+"\n")
    cols=["symbol","stress","net_2025_full_year_pct","PF_2025",
      "net_2026_Jan_Oct_YTD_pct","PF_2026_YTD","strong_months",
      "strong_and_5pct","months_5pct","months_10pct","months_20pct",
      "median_month_return_pct","worst_month_pct","max_drawdown_pct",
      "overall_PF","total_22mo_net_pct","trades"]
    report=["# Stage25 paired absorption -> displacement","",
       "Research only; identical causal rules and parameters across BTC and ETH.",
       "Shared model selected using 2025 monthly rank only. 2026 previously exposed.",
       "## 2025-only paired setting ranks",ranking.head(12).to_markdown(index=False),
       "## Selected 22 IST month-by-month BTC versus ETH",
       selected_month[["month_ist","symbol","net_return_pct","profit_factor",
                       "trades","wins","losses"]].to_markdown(index=False),
       "## 2025 FULL YEAR vs Jan-Oct 2026 YTD",selected_stats[cols].to_markdown(index=False),
       "## Source, assumptions and limitations",json.dumps(audit,indent=2),
       "Unmodeled execution costs mean this is not a claim of validated profitability."]
    (OUT/"RESEARCH_REPORT.md").write_text("\n\n".join(report)+"\n")
    print("STAGE25_PAIRED_DONE",json.dumps({
        "setting":{n:(bool(choice[n]) if n=="trend_align" else float(choice[n])) for n in names},
        "events":events_count,
        "selected":selected_stats[~selected_stats.stress].to_dict(orient="records")},default=str))

if __name__=="__main__":main()
