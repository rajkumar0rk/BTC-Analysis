#!/usr/bin/env python3
"""Small predeclared grid, training 2024/25 only, one frozen validation candidate."""
import sys,inspect,itertools,json,hashlib,os
from pathlib import Path
import numpy as np
import pandas as pd
import research_btc15m_worst_month_loss_pause_20261123 as base
OUT=Path("analysis/btc15m_repaired23m_robust_20261124")
DATA=Path("_repaired/data/delta_india/BTCUSD/2024_verified_archive")
ARCHIVE_COMMIT="edcf60fa0a229108d09772dc6cbe04eb15476291"
TZ="Asia/Kolkata"
# Three risk distances, two reward multiples, two exit policies, two filters.
# No monthly/account-history rules, no side-specific parameters.
GRID=[dict(sl=sl,rr=rr,flip=False,filter=fil) for sl,rr,fil in itertools.product([2.,3.,4.],[2.,3.],["any","slope4","body35"])]
CONTROL=GRID.index(dict(sl=3.,rr=3.,flip=False,filter="any"))
SHARDS=6
def date(s):return pd.Timestamp(s,tz=TZ).tz_convert("UTC")
def source24():
    manifest=json.loads((DATA/"manifest.json").read_text())
    assert manifest["synthetic_rows"]==0
    parts={p["month"]:p for p in manifest["months"] if p["series"]=="trade_1m"}
    frames=[]
    for mon in pd.period_range("2024-02","2024-12",freq="M").astype(str):
        p=parts[mon];f=DATA/"trade_1m"/(mon+".csv.gz")
        assert p["missing"]==0 and p["observed"]==p["expected"] and hashlib.sha256(f.read_bytes()).hexdigest()==p["sha256"]
        d=pd.read_csv(f,usecols=["time","open","high","low","close","volume"])
        assert len(d)==p["expected"]
        frames.append(d)
    df=pd.concat(frames,ignore_index=True)
    assert np.array_equal(df.time.to_numpy(np.int64),np.arange(int(date("2024-02-01").timestamp()),int(date("2025-01-01").timestamp()),60))
    df.index=pd.to_datetime(df.time,unit="s",utc=True)
    return df
def source25_26(period):
    root=Path("data/delta_india/BTCUSD/1m")
    manifest=json.loads((root/"manifest.json").read_text())
    lo,hi=("2025-01","2025-12") if period=="2025" else ("2025-12","2026-10")
    parts=[p for p in manifest["partitions"] if lo+".csv.gz"<=p["file"]<=hi+".csv.gz"]
    assert len(parts)==(12 if period=="2025" else 11)
    frames=[]
    for p in parts:
        f=root/p["file"]
        assert hashlib.sha256(f.read_bytes()).hexdigest()==p["sha256_gzip"] and p["missing_minutes"]==0
        d=pd.read_csv(f);assert len(d)==p["observed_candles"];frames.append(d)
    df=pd.concat(frames,ignore_index=True)
    assert np.all(np.diff(df.time.to_numpy(np.int64))==60)
    df.index=pd.to_datetime(df.time,unit="s",utc=True)
    end=date("2026-01-01" if period=="2025" else "2026-11-01")
    return df.loc[df.index<end].copy()
def prep(period):
    if period=="2024":
        df=source24()
        start=date("2024-02-03")
        months=pd.period_range("2024-02","2024-12",freq="M")
    elif period=="2025":
        df=source25_26(period);start=date("2025-01-01");months=pd.period_range("2025-01","2025-12",freq="M")
    else:
        df=source25_26(period);start=date("2026-01-01");months=pd.period_range("2026-01","2026-10",freq="M")
    assert len(df)%15==0
    ema,st,trend,valid=base.st_and_ema(df,base.TF)
    ind=base.make_indicators(df)
    start_i=int(np.searchsorted(df.time.to_numpy(),int(start.timestamp())))
    sig=base.make_signals(df,ema,trend,valid,"reclaim",4)[0]
    sig={i:v for i,v in sig.items() if i>=start_i}
    return df,ema,st,trend,ind,sig,months.astype(str).tolist()
def engine():
    src=inspect.getsource(base.simulate)
    assert src.count("qty=cash/entry")==1
    src=src.replace("qty=cash/entry",'qty=cash/entry*float(name.split("__P_")[1])/100')
    ns=dict(base.__dict__)
    def causal_filter(fil,side,j,ema,ind):
        if fil in ("slope3","slope4","slope5"):
            n=int(fil[5:])
            return j>=n and side*(ema[j]-ema[j-n])>0
        return base.check_filter(fil,side,j,ema,ind)
    ns["check_filter"]=causal_filter
    exec(compile(src,"<simple_core>","exec"),ns);return ns
def replay(ns,data,period,cid,cfg,prof,path,stress=False):
    df,ema,st,trend,ind,sig,months=data
    ns["MONTHS"]=months
    ns["FEE"]=base.FEE;ns["SLIP"]=base.SLIP*(3 if stress else 1)
    name=f"C{cid:02d}"+("_FLIPON_" if cfg["flip"] else "_NOFLIP_")+f"__P_{prof}"
    x,m,l=ns["simulate"](df,ema,st,trend,ind,name,(4,cfg["filter"],"PCT",cfg["sl"],cfg["rr"],"none"),sig,path)
    for k in ("profitable_2025_months","profitable_2026_months","return_2025_pct","return_2026_pct"):x.pop(k,None)
    x.update(candidate=cid,period=period,profile=prof,stress=stress,**cfg)
    x["geo_month_pct"]=100*((1+x["net_return_pct"]/100)**(1/len(months))-1)
    x["positive_fraction"]=x["profitable_months"]/len(months)
    x["worst_month"]=float(m.monthly_return_pct.min())
    m=m.assign(candidate=cid,period=period,profile=prof,stress=stress)
    l=l.assign(candidate=cid,period=period,profile=prof,stress=stress)
    return x,m,l
def train():
    OUT.mkdir(parents=True,exist_ok=True)
    i=int(os.environ["SHARD_INDEX"]);ns=engine();rows=[];monthly=[]
    for period in ("2024","2025"):
        data=prep(period)
        for cid,cfg in enumerate(GRID):
            if cid%SHARDS!=i:continue
            for path in base.PATHS:
                for stress in (False,True):
                    x,m,_=replay(ns,data,period,cid,cfg,100,path,stress)
                    rows.append(x);monthly.append(m)
                    print("TRAIN",period,cid,path,stress,x["net_return_pct"],flush=True)
    d=OUT/f"shard_{i}";d.mkdir(parents=True,exist_ok=True)
    pd.DataFrame(rows).to_csv(d/"training.csv",index=False)
    pd.concat(monthly,ignore_index=True).to_csv(d/"monthly.csv",index=False)
def freeze():
    OUT.mkdir(parents=True,exist_ok=True)
    s=pd.concat([pd.read_csv(OUT/f"shard_{i}"/"training.csv") for i in range(SHARDS)],ignore_index=True)
    m=pd.concat([pd.read_csv(OUT/f"shard_{i}"/"monthly.csv") for i in range(SHARDS)],ignore_index=True)
    assert len(s)==len(GRID)*2*2*2
    assert not s.duplicated(["candidate","period","path_assumption","stress"]).any()
    c=s[(s.candidate==CONTROL)&(~s.stress)]
    assert len(c)==4
    c13=GRID.index(dict(sl=3.,rr=3.,flip=False,filter="slope4"))
    assert np.allclose(s[(s.candidate==c13)&(s.period==2025)&(~s.stress)].net_return_pct,7.7141,atol=.001)
    s.to_csv(OUT/"training.csv",index=False);m.to_csv(OUT/"training_monthly.csv",index=False)
    a=s.groupby("candidate").agg(min_geo=("geo_month_pct","min"),min_win_fraction=("positive_fraction","min"),max_dd=("max_floating_drawdown_pct","max"),min_trades=("trades","min"),min_net=("net_return_pct","min")).reset_index()
    a["score"]=a.min_geo-.05*a.max_dd
    # Local stability: one adjacent grid coordinate differs; no isolated winner.
    scores=dict(zip(a.candidate,a.score));positive=dict(zip(a.candidate,a.min_net>0))
    def neighbors(i):
        c=GRID[i];out=[]
        for j,d in enumerate(GRID):
            diff=[k for k in c if c[k]!=d[k]]
            if len(diff)!=1:continue
            k=diff[0]
            if k=="filter":out.append(j)
            elif k in ("sl","rr"):
                values=sorted(set(g[k] for g in GRID))
                if abs(values.index(c[k])-values.index(d[k]))==1:out.append(j)
        return out
    a["neighbor_median"]=a.candidate.map(lambda i:float(np.median([scores[j] for j in neighbors(i)])))
    a["neighbor_positive_fraction"]=a.candidate.map(lambda i:float(np.mean([positive[j] for j in neighbors(i)])))
    a["robust_score"]=.5*a.score+.5*a.neighbor_median
    # Same earlier gate, now required under baseline AND stressed execution.
    a["eligible"]=(a.min_net>0)&(a.min_trades>=8)&(a.max_dd<=25)&(a.neighbor_median>0)&(a.neighbor_positive_fraction>=.5)
    a=a.sort_values(["eligible","robust_score","candidate"],ascending=[False,False,True])
    a.to_csv(OUT/"training_ranked.csv",index=False)
    top=a.iloc[0];cid=int(top.candidate)
    frozen=dict(candidate=cid,config=GRID[cid],control_candidate=CONTROL,passes_training_gate=bool(top.eligible),selection="Training only, both years and baseline/stressed costs. Same previous minimum return, DD, trade and positive neighbor score gates plus majority-positive adjacent configs. If none qualifies, top candidate diagnostic only.",archive_commit=ARCHIVE_COMMIT,training_periods=["2024-02..12 (first 2 days warmup)","2025-01..12"],prior_2026_exposure=True,grid=GRID,training_sha256=hashlib.sha256((OUT/"training.csv").read_bytes()).hexdigest())
    (OUT/"FROZEN.json").write_text(json.dumps(frozen,indent=2)+"\n")
    print("FROZEN",frozen,flush=True)
def validate():
    f=json.loads((OUT/"FROZEN.json").read_text())
    assert hashlib.sha256((OUT/"training.csv").read_bytes()).hexdigest()==f["training_sha256"]
    cid=f["candidate"];cfg=f["config"];assert cfg==GRID[cid]
    if not f["passes_training_gate"]:
        (OUT/"REPORT.md").write_text("# Repaired archive training result\n\nNo configuration passed the predefined training robustness gate. 2026 deliberately not replayed; no approved frozen candidate. See training_ranked.csv and FROZEN.json (diagnostic only).\n")
        return
    ns=engine();rows=[];monthly=[];ledger=[]
    # Same selected configuration only. No reranking or fallback based on 2026.
    for period in ("2024","2025","2026"):
        data=prep(period)
        for prof in (80,100):
            for path in base.PATHS:
                for stress in (False,True):
                    x,m,l=replay(ns,data,period,cid,cfg,prof,path,stress)
                    rows.append(x);monthly.append(m);ledger.append(l)
    s=pd.DataFrame(rows);m=pd.concat(monthly,ignore_index=True);l=pd.concat(ledger,ignore_index=True)
    s.to_csv(OUT/"frozen_summary.csv",index=False);m.to_csv(OUT/"frozen_monthly.csv",index=False);l.to_csv(OUT/"frozen_ledger.csv",index=False)
    z=s.groupby(["period","profile","stress"],as_index=False).agg(net=("net_return_pct","min"),dd=("max_floating_drawdown_pct","max"),months=("profitable_months","min"),trades=("trades","min"),wins=("wins","min"),losses=("losses","max"))
    cols=["period","profile","stress","net","dd","months","trades","wins","losses"]
    lines=["# Repaired archive simple strategy training / frozen validation","",f"18 predeclared configurations; 144 training path/cost replays. Selected C{cid:02d}: {cfg}. Training gate passed: {f['passes_training_gate']}.","Training: Feb-Dec 2024 (Feb 1-2 warmup), Jan-Dec 2025 (source starts Jan 1 UTC). Validation: Jan-Oct 2026 (Dec 2025 warmup, no pre-2026 entries). 2026 was examined in previous research, so this is a procedural holdout, not genuinely untouched OOS. No tuning on validation results.","At most one simple entry filter (none, four-bar EMA slope, or 35% directional candle body). No adaptive rules. No combined strategies, hedging, monthly or account-history switches. Fixed exposure. Baseline costs 0.05% taker per side+GST18%, slip 0.02% per side; stress slip 0.06%. Funding excluded.","",z[cols].to_markdown(index=False),"","## Monthly returns (normal costs, worse of two paths)",m[~m.stress].groupby(["month_ist","profile"]).monthly_return_pct.min().unstack().to_markdown(),""]
    (OUT/"REPORT.md").write_text("\n".join(lines)+"\n")
    print("\n".join(lines),flush=True)
if __name__=="__main__":
    if sys.argv[1]=="train":train()
    elif sys.argv[1]=="freeze":freeze()
    else:validate()
