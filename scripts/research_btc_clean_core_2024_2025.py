#!/usr/bin/env python3
"""Frozen pre-recovery Step5 E core: no month/day/PnL switches, no model search.
Same rules in both years and every fee scenario. One trade per available weekday.
2024 may lack Delta India archive coverage; report gaps and never fill missing data.
"""
import argparse,json
from pathlib import Path
import numpy as np
import pandas as pd
from sync_delta_btcusd_1m import fetch_month,write_month
from collect_delta_institutional_data import http_get
from step52_validation_engine import replay_one
from research_btc_daily_exit_invalidation_step7 import replay_with_nextbar_exits

ROOT=Path("data/delta_india/BTCUSD")
OUT=Path("analysis/btc_clean_core")
FEE=.0005*1.18
TZ="Asia/Kolkata"
POL=np.array([0.,0.,0.,30.])
EVENT=np.array([1,.50,3.,30,.25,.10,0.])
FALL_LOW=np.array([2,.50,3.,30,.35,.20,0.])
FALL_HIGH=np.array([2,.75,3.,30,.35,.20,0.])

def utc(t):return int(t.timestamp())
def load_files(paths):
    frames=[]
    for p in paths:
        if p.exists():
            d=pd.read_csv(p)
            if len(d):
                d["time"]=pd.to_datetime(d.time.astype("int64"),unit="s",utc=True)
                frames.append(d)
    if not frames:return pd.DataFrame()
    d=pd.concat(frames).set_index("time").sort_index()
    assert not d.index.has_duplicates
    return d
def download_2024():
    root=OUT/"2024_data";root.mkdir(parents=True,exist_ok=True)
    for month in pd.period_range("2024-01","2024-12",freq="M"):
        a=month.start_time.tz_localize("UTC");b=(month+1).start_time.tz_localize("UTC")
        p=root/(str(month)+".csv.gz")
        if not p.exists():
            try:
                rows=fetch_month(utc(a),utc(b))
                if rows:write_month(p,rows)
                print("CLEAN_DATA",str(month),len(rows),flush=True)
            except Exception as e: print("CLEAN_DATA_ERROR",str(month),str(e),flush=True)
    return load_files(sorted(root.glob("*.csv.gz")))
def load_2024_aux(m):
    root=OUT/"2024_aux";root.mkdir(parents=True,exist_ok=True)
    out={}
    for name,symbol,res,step in [("mark","MARK:BTCUSD","1m",60),("funding","FUNDING:BTCUSD","1h",3600)]:
        paths=[]
        for mon in sorted(set(m.index.strftime("%Y-%m"))):
            p=root/(name+"_"+mon+".csv.gz");paths.append(p)
            if p.exists():continue
            a=pd.Timestamp(mon+"-01",tz="UTC");b=a+pd.offsets.MonthBegin(1)
            rows={}
            # Request only the intraday region needed for actual trades,
            # but use full hourly funding history to obtain prior closes.
            if name=="mark":
                spans=[(utc(day+pd.Timedelta(hours=12)),utc(day+pd.Timedelta(hours=17))) for day in pd.date_range(a,b-pd.Timedelta(days=1),freq="D") if day.tz_convert(TZ).weekday()<5]
            else:
                spans=[(utc(a)-step,utc(b))]
            try:
                for start,stop in spans:
                    for lo in range(start,stop,1200*step):
                        hi=min(stop-step,lo+1199*step)
                        result=http_get("/v2/history/candles",dict(symbol=symbol,resolution=res,start=lo,end=hi))
                        for bar in result:
                            ts=int(bar["time"])
                            if lo<=ts<=hi and utc(a)<=ts<utc(b):rows[ts]=bar
                if rows:pd.DataFrame(rows.values()).to_csv(p,index=False,compression="gzip")
                print("CLEAN_AUX",name,mon,len(rows),flush=True)
            except Exception as e:print("CLEAN_AUX_ERROR",name,mon,str(e),flush=True)
        out[name]=load_files(paths)
    return out["mark"],out["funding"]

def select(m,year):
    o,h,l,c,v=[m[x].to_numpy(float) for x in ("open","high","low","close","volume")]
    ix=m.index
    expected=pd.date_range(f"{year}-01-01",f"{year}-12-31",freq="B",tz=TZ)
    trades=[];missing=[]
    for d in expected:
        # Complete 105-minute lookback before first 18:00 signal, through
        # final possible 21:30 exit. No future price used to choose entry.
        a=(d+pd.Timedelta(hours=18,minutes=-105)).tz_convert("UTC")
        b=(d+pd.Timedelta(hours=21,minutes=30)).tz_convert("UTC")
        ai=ix.get_indexer([a])[0];bi=ix.get_indexer([b])[0]
        if ai<0 or bi-ai!=int((b-a).total_seconds()/60) or not np.array_equal(ix[ai:bi+1],pd.date_range(a,b,freq="min")):
            missing.append(d.strftime("%Y-%m-%d"));continue
        def feature(j):
            r=c[j-1]/o[j-5]-1
            avg=v[j-105:j-5].reshape(20,5).sum(axis=1).mean()
            rv=v[j-5:j].sum()/avg if avg>0 else 0.
            return (1 if r>=0 else -1),rv
        fallback=True
        for hour in (18,19,20):
            j=ix.get_loc((d+pd.Timedelta(hours=hour)).tz_convert("UTC"))
            sign,rv=feature(j)
            if rv>=1.5:
                side=-sign;recipe=EVENT;fallback=False;break
        if fallback:
            hour=21;j=ix.get_loc((d+pd.Timedelta(hours=hour)).tz_convert("UTC"))
            side,rv=feature(j);recipe=FALL_HIGH if rv>=1.25 else FALL_LOW
        end,mid,why,_,_,both=replay_one(o,h,l,c,j,side,recipe,POL)
        assert end>=j and end<=j+30
        trades.append(dict(date=d.strftime("%Y-%m-%d"),entry=ix[j],exit=ix[end],j=j,end=end,side=side,entry_mid=o[j],exit_mid=mid,hold=end-j,reason=why,fallback=fallback,recipe=recipe))
    if trades:
        starts=np.array([t["j"] for t in trades]);sides=np.array([t["side"] for t in trades],np.int8);cfg=np.stack([t["recipe"] for t in trades])
        raw=replay_with_nextbar_exits(o,h,l,c,starts,sides,cfg,POL[None,:],FEE,5.)
        for i,t in enumerate(trades):
            assert raw[4][i,0]==t["hold"] and raw[3][i,0]==t["reason"]
            assert abs(raw[2][i,0]-t["side"]*(t["exit_mid"]-t["entry_mid"]))<1e-7
            if i:assert trades[i-1]["end"]<t["j"]
    return trades,expected,missing

def report(trades,expected,mark,funding,year):
    # Prior-hour rate; adverse-only funding proxy before/after 2025 transition.
    funding_rate=funding.close.shift(1) if len(funding) else pd.Series(dtype=float)
    scenarios=[]
    for mode,slip in [("standard",5),("historical",5),("conservative",5),("standard",20),("historical",20),("conservative",20),("offer30",5),("offer30",20),("offer30",50),("standard",100),("standard",200)]:
        rows=[];missing_funding=0;missing_mark=0
        eq=peak=mp=1.;dd=md=0.
        for t in trades:
            side=t["side"];entry=t["entry_mid"]+side*slip;exit=t["exit_mid"]-side*slip
            hold=t["hold"];ts=t["entry"];te=t["exit"]
            waive=(mode=="historical" and hold<(15 if ts<pd.Timestamp("2025-10-11",tz=TZ) else 30)) or (mode=="conservative" and ts>=pd.Timestamp("2025-10-11",tz=TZ) and hold<30) or (mode=="offer30" and hold<30)
            fee=FEE*(entry+exit*(not waive))/entry
            marks=mark.reindex(pd.date_range(ts,te,freq="min")) if len(mark) else pd.DataFrame()
            mark_ok=len(marks)>0 and marks[["open","high","low"]].notna().all().all()
            if not mark_ok:missing_mark+=1
            fund=0.;fund_ok=True
            for x in pd.date_range(ts,te,freq="min"):
                pre=x<pd.Timestamp("2025-09-08T12:00Z")
                if not ((pre and x<te) or (not pre and x.minute==0 and x.hour%8==0)):continue
                if not len(funding_rate) or not mark_ok:fund_ok=False;break
                rate=funding_rate.asof(x)
                if not np.isfinite(rate):fund_ok=False;break
                fund+=abs(rate/100*marks.loc[x,"open"]/entry)*(1/480 if pre else 1)
            if not fund_ok:missing_funding+=1
            gross=side*(exit-entry)/entry
            # If incomplete, report price/fee-only separately, never claim full funding.
            net=gross-fee
            netfund=net-fund if fund_ok else np.nan
            r=netfund if fund_ok else net
            if mark_ok and fund_ok:
                for _,bar in marks.iterrows():
                    fav=side*((bar.high if side>0 else bar.low)-entry)/entry
                    adv=side*((bar.low if side>0 else bar.high)-entry)/entry
                    mp=max(mp,eq*(1+fav-FEE));md=max(md,1-eq*(1+adv-2*FEE-fund)/mp)
            eq*=1+r;peak=max(peak,eq);dd=max(dd,1-eq/peak)
            mp=max(mp,eq);md=max(md,1-eq/mp)
            rows.append(dict(date=t["date"],entry=ts,exit=te,side=side,hold=hold,fee_pct=100*fee,net_fee_only=net,net_funding=netfund))
        if not rows:continue
        df=pd.DataFrame(rows);df.to_csv(OUT/f"{year}_{mode}_{slip}_ledger.csv",index=False)
        full=missing_funding==0
        p=df.net_funding.to_numpy() if full else df.net_fee_only.to_numpy()
        eqs=np.cumprod(1+p);peak2=np.maximum.accumulate(np.r_[1.,eqs])[1:]
        months={}
        for mon in pd.period_range(f"{year}-01",f"{year}-12",freq="M"):
            key=str(mon);v=p[df.date.str.startswith(key).to_numpy()]
            needed=sum(x.strftime("%Y-%m")==key for x in expected)
            months[key]=dict(trades=len(v),expected=needed,net_pct=float(100*(np.prod(1+v)-1)) if len(v) else None,complete=len(v)==needed)
        scenarios.append(dict(mode=mode,slip=slip,net_pct=float(100*(eqs[-1]-1)),fee_only_net_pct=float(100*(np.prod(1+df.net_fee_only)-1)),funding_complete=full,missing_funding_trades=missing_funding,missing_mark_trades=missing_mark,closed_dd_pct=float(100*np.max(1-eqs/peak2)),mark_dd_pct=float(100*md) if full and missing_mark==0 else None,wins=int((p>0).sum()),losses=int((p<0).sum()),positive_complete_months=sum(x["complete"] and x["net_pct"]>0 for x in months.values()),ge1_complete_months=sum(x["complete"] and x["net_pct"]>=1 for x in months.values()),months=months))
    return scenarios

def main():
    p=argparse.ArgumentParser();p.add_argument("--year",type=int,required=True);year=p.parse_args().year
    OUT.mkdir(parents=True,exist_ok=True)
    if year==2024:
        m=download_2024()
    else:
        m=load_files([ROOT/"1m"/(str(x)+".csv.gz") for x in pd.period_range("2025-01","2025-12",freq="M")])
    if not len(m):
        print("CLEAN_FINAL",json.dumps(dict(year=year,status="NO_DATA")),flush=True);return
    trades,expected,missing=select(m,year)
    print("CLEAN_COVERAGE",json.dumps(dict(year=year,candles=len(m),trades=len(trades),expected=len(expected),missing=missing,first=str(m.index.min()),last=str(m.index.max()))),flush=True)
    if year==2024:
        # Write preliminary fees-only results even if auxiliary data unavailable.
        preliminary=report(trades,expected,pd.DataFrame(),pd.DataFrame(),year)
        print("CLEAN_PRELIMINARY",json.dumps(dict(year=year,scenarios=preliminary)),flush=True)
        mark,funding=load_2024_aux(m)
    else:
        root=ROOT/"institutional/history"
        mark=load_files(sorted((root/"mark_1m").glob("*.csv.gz")))
        funding=load_files(sorted((root/"funding_1h").glob("*.csv.gz")))
    result=dict(year=year,status="COMPLETE" if not missing else "PARTIAL_COVERAGE",trades=len(trades),expected=len(expected),missing=missing,independent_replay=True,monthly_recovery_rules=0,online_pnl_switches=0,optimization=False,scenarios=report(trades,expected,mark,funding,year))
    (OUT/f"{year}_summary.json").write_text(json.dumps(result,indent=2))
    print("CLEAN_FINAL",json.dumps(result),flush=True)
if __name__=="__main__":main()
