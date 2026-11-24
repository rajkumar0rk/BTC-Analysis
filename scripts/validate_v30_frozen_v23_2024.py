#!/usr/bin/env python3
"""Frozen V23 common rules; retrospective 2024 validation, no tuning.
Download true trade, mark and funding OHLC from Delta India; do not fill gaps.
Select uninterrupted covered periods by data availability alone."""
import concurrent.futures as cf
import inspect,json,time,hashlib,urllib.parse,urllib.request
from pathlib import Path
import numpy as np
import pandas as pd
import research_v19_leverage_local_recovery as src
import validate_frozen_high_leverage as audit
import research_v24_common_drawdown_control as engine
OUT=Path("analysis/v30_march_december_2024/v23");OUT.mkdir(parents=True,exist_ok=True)
DATA=Path("_v26_2024_data");DATA.mkdir(exist_ok=True)
BASE="https://api.india.delta.exchange/v2/history/candles"
START=pd.Timestamp("2023-12-01",tz="UTC");END=pd.Timestamp("2025-01-01",tz="UTC")
SERIES=(("trade","BTCUSD","1m",60),("mark_1m","MARK:BTCUSD","1m",60),("funding_1h","FUNDING:BTCUSD","1h",3600))
ROOT=Path("data/delta_india/BTCUSD/2024_verified_archive")
FROZEN=json.loads(Path("analysis/v23_common_strategy_cross_margin/common_profile.json").read_text())["profile"]
def load_archive():
    manifest=json.loads((ROOT/"manifest.json").read_text())
    series={}
    for key,label in (("trade","trade_1m"),("mark_1m","mark_1m"),("funding_1h","funding_1h")):
        frames=[]
        for item in manifest["months"]:
            if item["series"]!=label:continue
            path=ROOT/label/(item["month"]+".csv.gz")
            assert hashlib.sha256(path.read_bytes()).hexdigest()==item["sha256"]
            z=pd.read_csv(path)
            assert len(z)==item["observed"] and not z.time.duplicated().any()
            z.index=pd.to_datetime(z.pop("time").astype("int64"),unit="s",utc=True)
            assert np.isfinite(z.to_numpy(float)).all()
            frames.append(z)
        series[key]=pd.concat(frames).sort_index()
        assert not series[key].index.has_duplicates
    # The IST year ends at 18:30 UTC. Retrieve only the 30 following minutes
    # for full UTC-hour aggregation; never allow a post-boundary signal or fill.
    a=int(pd.Timestamp("2024-12-31 18:30",tz="UTC").timestamp())
    for key,symbol in (("trade","BTCUSD"),("mark_1m","MARK:BTCUSD")):
        rows={}
        for pad in (60,3600,7200):
            url=BASE+"?"+urllib.parse.urlencode(dict(symbol=symbol,resolution="1m",start=a-pad,end=a+1800+pad))
            try:
                with urllib.request.urlopen(urllib.request.Request(url,headers={"Accept":"application/json","User-Agent":"BTC-Analysis-research/1.0"}),timeout=40) as resp:d=json.load(resp)
                for r in d["result"]:
                    t=int(r["time"])
                    if a<=t<a+1800 and t%60==0:
                        cols=["open","high","low","close"]+(["volume"] if key=="trade" else [])
                        rows[t]={c:float(r[c]) for c in cols}
            except Exception as exc:print("BOUNDARY_RETRY",str(exc),flush=True)
            if len(rows)==30:break
        assert len(rows)==30,(key,"missing boundary warmdown candles",len(rows))
        z=pd.DataFrame.from_dict(rows,orient="index").sort_index()
        z.index=pd.to_datetime(z.index,unit="s",utc=True)
        series[key]=pd.concat([series[key],z])
    # Funding coverage is complete through 17:00 UTC, the only observation
    # required for the final hour. Include 18:00 only if present, never invent.
    return series,manifest
def context(m,mark,fr):
    # Reuse the V19 frozen feature-generation prefix. Only the data source
    # and calendar indexing change; no change to indicator thresholds.
    prefix=inspect.getsource(src.main).split("        # Candidate tuple:")[0]
    prefix=prefix.replace("m,manifest=v14.shock.load()","m,manifest=INPUT_TRADE.copy(),{}")
    prefix=prefix.replace("(t.year-2025)*12","(t.year-2024)*12")
    p0=prefix.index("    def load_series(label,res):")
    p1=prefix.index('    mark=load_series("mark_1m","1min")',p0)
    prefix=prefix[:p0]+"""    def load_series(label,res):
        return INPUT_MARK if label=="mark_1m" else INPUT_FUND
"""+prefix[p1:]
    # The development-only minimum candidate count is not a trading rule.
    # Keep even infrequent signal groups in this frozen validation.
    prefix=prefix.replace("if len(z)<22:continue","if len(z)==0:continue")
    ns=vars(src).copy();ns.update(LEVS=(50,),INPUT_TRADE=m,INPUT_MARK=mark,INPUT_FUND=fr)
    exec(compile(prefix+"        return locals()\n","frozen_2024_feature_context","exec"),ns)
    return ns["main"]()
def main():
    (OUT/"frozen_profile.json").write_text(json.dumps(FROZEN,indent=2))
    series,archive=load_archive()
    t=series["trade"];mk=series["mark_1m"];fr=series["funding_1h"]
    # Complete UTC hours only; prior hourly rate required for each hour.
    # Do not interpolate any missing prices or rates.
    tc=t.groupby(t.index.floor("h")).size()
    mc=mk.groupby(mk.index.floor("h")).size()
    hours=pd.date_range(t.index[0].ceil("h"),t.index[-1].floor("h"),freq="h")
    good=(tc.reindex(hours,fill_value=0).eq(60)&mc.reindex(hours,fill_value=0).eq(60)&pd.Series(hours-pd.Timedelta(hours=1)).isin(fr.index).set_axis(hours)).to_numpy()
    coverage=[]
    for mon in pd.period_range("2024-01","2024-12",freq="M"):
        a=mon.start_time.tz_localize("Asia/Kolkata").tz_convert("UTC");b=(mon+1).start_time.tz_localize("Asia/Kolkata").tz_convert("UTC")
        expected=int((b-a).total_seconds()/60)
        nt=int(((t.index>=a)&(t.index<b)).sum());nm=int(((mk.index>=a)&(mk.index<b)).sum())
        hf=pd.date_range(a.floor("h")-pd.Timedelta(hours=1),(b-pd.Timedelta(minutes=1)).floor("h")-pd.Timedelta(hours=1),freq="h")
        nf=int(hf.isin(fr.index).sum())
        coverage.append(dict(month=str(mon),expected_minutes=expected,trade_minutes=nt,mark_minutes=nm,missing_trade=expected-nt,missing_mark=expected-nm,funding_expected_hours=len(hf),funding_observed_hours=nf,complete=bool(nt==nm==expected and nf==len(hf))))
    pd.DataFrame(coverage).to_csv(OUT/"coverage.csv",index=False)
    # Longest uninterrupted interval by coverage, with a 30-day warmup.
    # Include only full IST months in the scored window.
    runs=[];start=None
    for i,g in enumerate(np.r_[good,False]):
        if g and start is None:start=i
        if not g and start is not None:
            a=hours[start].ceil("D");b=hours[i-1]+pd.Timedelta(hours=1);start=None
            score=[]
            for mon in pd.period_range("2024-01","2024-12",freq="M"):
                ma=mon.start_time.tz_localize("Asia/Kolkata").tz_convert("UTC")
                mb=(mon+1).start_time.tz_localize("Asia/Kolkata").tz_convert("UTC")
                if ma>=a+pd.Timedelta(days=28) and mb<=b:score.append(mon)
            if score:runs.append((len(score),a,b,score))
    meta=dict(frozen_source="V23/V19 50x common profile, no V25 results used",same_config_all_leverage=True,no_2024_tuning=True,prior_2024_research_exists=True,full_year=False,archive_totals=archive["totals"],frozen_profile_sha256=hashlib.sha256(Path("analysis/v23_common_strategy_cross_margin/common_profile.json").read_bytes()).hexdigest(),data_sources={k:dict(rows=len(v)) for k,v in series.items()},exact_exchange_liquidation=False,exact_funding=False)
    if not runs:
        meta.update(status="insufficient_contiguous_trade_mark_funding_coverage",scored_months=[])
        (OUT/"quality.json").write_text(json.dumps(meta,indent=2));return
    _,a,b,score=max(runs,key=lambda x:(x[0],x[2]-x[1]))
    assert [str(x) for x in score]==[str(x) for x in pd.period_range("2024-03","2024-12",freq="M")], score
    first=score[0].start_time.tz_localize("Asia/Kolkata").tz_convert("UTC")
    last=(score[-1]+1).start_time.tz_localize("Asia/Kolkata").tz_convert("UTC")
    # Signal computation requires aligned complete hours; last score boundary
    # is :30 UTC, compute through next hour then truncate replay at boundary.
    end=last.ceil("h")
    assert end<=b
    m=t.loc[(t.index>=a)&(t.index<end)].copy()
    mm=mk.loc[(mk.index>=a)&(mk.index<end)].copy()
    ff=fr.loc[(fr.index>=a-pd.Timedelta(hours=1))&(fr.index<end)].copy()
    ctx=context(m,mm,ff)
    ctx["end"]=int(m.index.searchsorted(last))
    events=[r for r in audit.signals(ctx,FROZEN) if first<=m.index[r[0]]<last]
    idx=[mo.month-1 for mo in score]
    summary=[];monthly=[]
    for lev in engine.LEVS:
        for margin_mode in ("cross","isolated"):
            for sc in engine.SCENARIOS:
                for fm in (0,1):
                    r=engine.simulate(ctx,FROZEN,events,lev,margin_mode,"fixed_10_margin_budget",sc,fm,{})
                    ret=r.pop("monthly_returns");pts=r.pop("monthly_points");usd=r.pop("monthly_usd")
                    for k in ("months_ge_1pct_points","months_ge_1pct_account","min_month_account_pct","november_account_pct","november_points","pass_account"):r.pop(k,None)
                    base=dict(leverage=lev,margin_mode=margin_mode,scenario=sc[0],funding_mode=fm)
                    summary.append(dict(**base,**r,months_tested=len(idx),months_ge_1pct_account=int((ret[idx]>=1).sum()),positive_months=int((ret[idx]>0).sum()),min_month_return=float(ret[idx].min()),pass_target=bool(r["trades"] and r["liquidations"]==0 and (ret[idx]>=1).all())))
                    monthly.extend(dict(**base,month=str(mo),net_usd=usd[i],account_return_pct=ret[i],net_points=pts[i]) for mo,i in zip(score,idx))
        print("REPLAY",lev,len(summary),flush=True)
    pd.DataFrame(summary).to_csv(OUT/"summary.csv",index=False);pd.DataFrame(monthly).to_csv(OUT/"monthly.csv",index=False)
    meta.update(status="completed",scored_months=[str(x) for x in score],full_year=len(score)==12,minimum_warmup_days=28,indicator_warmup_start=str(a),scored_start=str(first),scored_end_exclusive=str(last),signal_count=len(events),scenario_rows=len(summary))
    (OUT/"quality.json").write_text(json.dumps(meta,indent=2))
if __name__=="__main__":main()
