#!/usr/bin/env python3
"""Small predeclared grid, training 2024/25 only, one frozen validation candidate."""
import sys,inspect,itertools,json,hashlib,os
from pathlib import Path
import numpy as np
import pandas as pd
import research_btc15m_worst_month_loss_pause_20261123 as base
OUT=Path("analysis/btc15m_c05_reclaim_quality_20261124")
DATA=Path("_repaired/data/delta_india/BTCUSD/2024_verified_archive")
ARCHIVE_COMMIT="edcf60fa0a229108d09772dc6cbe04eb15476291"
TZ="Asia/Kolkata"
# One entry-quality hypothesis at a time, with fixed C05 delayed protection.
GRID=[dict(atr=3.5,rr=3.5,wait=4,flip=False,filter=f"h4ema50_{family}_{value}",activation=2.5,lock=0.) for family,values in (("body",[0.25,0.40,0.55]),("distance",[0.5,1.0,1.5])) for value in values]
GRID += [dict(atr=3.5,rr=3.5,wait=4,flip=False,filter="h4ema50",activation=2.5,lock=0.)]
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
    # ATR14 of completed 15m candles, Wilder smoothing.
    h,l,c=ind["H"],ind["L"],ind["C"]
    prev=np.r_[c[0],c[:-1]]
    tr=np.maximum(h-l,np.maximum(abs(h-prev),abs(l-prev)))
    atr=np.full(len(tr),np.nan);atr[13]=np.mean(tr[:14])
    for j in range(14,len(tr)):atr[j]=(13*atr[j-1]+tr[j])/14
    ind["ATR"]=atr
    # Confirmed higher timeframe closes only, aligned by UTC epoch.
    times=df.time.to_numpy(np.int64)
    signal_end=times[14::15]+60
    for hours in (1,4):
        seconds=hours*3600
        tmp=pd.DataFrame({"t":times,"close":df.close.to_numpy(float)})
        tmp["bucket"]=tmp.t//seconds
        grouped=tmp.groupby("bucket",sort=True).agg(close=("close","last"),count=("t","size"))
        grouped=grouped[grouped["count"]==hours*60]
        vals=grouped.close
        avg=vals.ewm(span=50,adjust=False,min_periods=50).mean()
        ends=(grouped.index.to_numpy(np.int64)+1)*seconds
        idx=np.searchsorted(ends,signal_end,side="right")-1
        mapped=np.full(len(signal_end),np.nan)
        ok=idx>=0
        mapped[ok]=(vals-avg).to_numpy()[idx[ok]]
        ind[f"h{hours}ema50"]=mapped
    sig={}
    for wait in (2,4,6):
        q=base.make_signals(df,ema,trend,valid,"reclaim",wait)[0]
        sig[wait]={i:v for i,v in q.items() if i>=start_i}
    return df,ema,st,trend,ind,sig,months.astype(str).tolist()
def engine():
    src=inspect.getsource(base.simulate)
    assert src.count("qty=cash/entry")==1
    src=src.replace("qty=cash/entry",'qty=cash/entry*float(name.split("__P_")[1])/100')
    # Lock is measured in entry-time R, not subsequent ATR.
    # Update only after observing a favorable price; check old stop first.
    anchor='        # An overnight/minute opening price may already cross a rung.'
    assert src.count(anchor)==1
    src=src.replace(anchor, """        if position is not None and ACT>0:
            p=position;side=p["side"]
            if not p["active"] and side*(raw_open-p["entry"])>=ACT*p["R"]:
                candidate=p["entry"]+side*LOCK*p["R"]
                assert side*(candidate-p["stop"])>0
                p["stop"]=candidate;p["active"]=True;p["activation_count"]+=1
        # An overnight/minute opening price may already cross a rung.""")
    anchor='                mark(dest)\n        if i in monthends:'
    assert src.count(anchor)==1
    src=src.replace(anchor, """                if ACT>0 and not p["active"] and side*(dest-p["entry"])>=ACT*p["R"]:
                    candidate=p["entry"]+side*LOCK*p["R"]
                    assert side*(candidate-p["stop"])>0
                    p["stop"]=candidate;p["active"]=True;p["activation_count"]+=1
                mark(dest)
        if i in monthends:""")
    ns=dict(base.__dict__)
    def filter_entry(fil,side,j,ema,ind):
        if fil in ("h1ema50","h4ema50"):return bool(side*ind[fil][j]>0)
        if fil.startswith("h4ema50_"):
            if not side*ind["h4ema50"][j]>0:return False
            _,family,threshold=fil.split("_");threshold=float(threshold)
            if family=="body":return bool(side*(ind["C"][j]-ind["O"][j])>=threshold*(ind["H"][j]-ind["L"][j]))
            if family=="distance":return bool(0<=side*(ind["C"][j]-ema[j])<=threshold*ind["ATR"][j])
            raise ValueError(fil)
        return base.check_filter(fil,side,j,ema,ind)
    ns["check_filter"]=filter_entry
    exec(compile(src,"<simple_core>","exec"),ns);return ns
def replay(ns,data,period,cid,cfg,prof,path,stress=False):
    df,ema,st,trend,ind,sig,months=data
    ns["MONTHS"]=months
    ns["FEE"]=base.FEE;ns["SLIP"]=base.SLIP*(3 if stress else 1);ns["ACT"]=cfg["activation"];ns["LOCK"]=cfg["lock"]
    name=f"C{cid:02d}"+("_FLIPON_" if cfg["flip"] else "_NOFLIP_")+f"__P_{prof}"
    x,m,l=ns["simulate"](df,ema,st,trend,ind,name,(cfg["wait"],cfg["filter"],"ATR",cfg["atr"],cfg["rr"],"none"),sig[cfg["wait"]],path)
    for k in ("profitable_2025_months","profitable_2026_months","return_2025_pct","return_2026_pct"):x.pop(k,None)
    x.update(candidate=cid,period=period,profile=prof,stress=stress,**cfg)
    x["geo_month_pct"]=100*((1+x["net_return_pct"]/100)**(1/len(months))-1)
    x["positive_fraction"]=x["profitable_months"]/len(months)
    x["worst_month"]=float(m.monthly_return_pct.min())
    half=m.month_ist.str[:4]+"H"+np.where(m.month_ist.str[5:].astype(int)<=6,"1","2")
    x["worst_half_pct"]=float(((1+m.monthly_return_pct/100).groupby(half).prod()-1).min()*100)
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
    control=len(GRID)-1
    for year,value in [(2024,48.82),(2025,31.96)]:
        z=s[(s.candidate==control)&(s.period==year)&(~s.stress)&(s.path_assumption=="O-H-L-C")]
        assert len(z)==1 and abs(float(z.net_return_pct.iloc[0])-value)<.015
    s.to_csv(OUT/"training.csv",index=False);m.to_csv(OUT/"training_monthly.csv",index=False)
    a=s.groupby("candidate").agg(min_geo=("geo_month_pct","min"),min_win_fraction=("positive_fraction","min"),max_dd=("max_floating_drawdown_pct","max"),min_trades=("trades","min"),min_net=("net_return_pct","min"),min_half=("worst_half_pct","min")).reset_index()
    a["score"]=a.min_geo-.05*a.max_dd
    # Local stability: one adjacent grid coordinate differs; no isolated winner.
    scores=dict(zip(a.candidate,a.score));positive=dict(zip(a.candidate,a.min_net>0))
    def neighbors(i):
        c=GRID[i];out=[]
        if i==control:return [i]
        for j,d in enumerate(GRID):
            diff=[k for k in c if c[k]!=d[k]]
            if len(diff)!=1:continue
            k=diff[0]
            if k=="filter":
                if j==control:continue
                a0=c[k].split("_");a1=d[k].split("_")
                if a0[1]!=a1[1]:continue
                vals=[0.25,0.40,0.55] if a0[1]=="body" else [0.5,1.0,1.5]
                if abs(vals.index(float(a0[2]))-vals.index(float(a1[2])))==1:out.append(j)
            elif k in ("activation","lock"):
                if j==control:continue
                values=sorted(set(g[k] for g in GRID[:-1]))
                if abs(values.index(c[k])-values.index(d[k]))==1:out.append(j)
        return out or [i]
    a["neighbor_median"]=a.candidate.map(lambda i:float(np.median([scores[j] for j in neighbors(i)])))
    a["neighbor_positive_fraction"]=a.candidate.map(lambda i:float(np.mean([positive[j] for j in neighbors(i)])))
    a["robust_score"]=.5*a.score+.5*a.neighbor_median
    # Same earlier gate, now required under baseline AND stressed execution.
    a["eligible"]=(a.candidate!=control)&(a.min_half>0)&(a.min_net>0)&(a.min_trades>=8)&(a.max_dd<=25)&(a.neighbor_median>0)&(a.neighbor_positive_fraction>=.5)
    # Require better aggregate training monthly count than unchanged C05,
    # without reducing either year's stressed positive-month count.
    worst_counts=s.groupby(["candidate","period"]).profitable_months.min().unstack()
    control_counts=worst_counts.loc[control]
    a["training_positive_months_worst"]=a.candidate.map(worst_counts.sum(axis=1))
    a["monthly_nonregression"]=a.candidate.map((worst_counts>=control_counts).all(axis=1))
    a["eligible"] &= a.monthly_nonregression & (a.training_positive_months_worst>control_counts.sum())
    a["eligible"] &= a.candidate.map((worst_counts[2024]>=5)&(worst_counts[2025]>=9))
    a["eligible"] &= (a.neighbor_positive_fraction==1) & (a.min_net>=float(a.loc[a.candidate==control,"min_net"].iloc[0])) & (a.max_dd<=float(a.loc[a.candidate==control,"max_dd"].iloc[0]))
    a=a.sort_values(["eligible","robust_score","candidate"],ascending=[False,False,True])
    a.to_csv(OUT/"training_ranked.csv",index=False)
    top=a.iloc[0];cid=int(top.candidate)
    frozen=dict(candidate=cid,config=GRID[cid],passes_training_gate=bool(top.eligible),selection="Training only, both years and baseline/stressed costs. Previous gates plus positive returns in all four training half-year segments under both cost scenarios; higher total profitable training months with neither year regressing. Unchanged control excluded from new candidate selection. If none qualifies, top candidate diagnostic only.",archive_commit=ARCHIVE_COMMIT,training_periods=["2024-02..12 (first 2 days warmup)","2025-01..12"],prior_2026_exposure=True,grid=GRID,training_sha256=hashlib.sha256((OUT/"training.csv").read_bytes()).hexdigest())
    (OUT/"FROZEN.json").write_text(json.dumps(frozen,indent=2)+"\n")
    print("FROZEN",frozen,flush=True)
def validate():
    f=json.loads((OUT/"FROZEN.json").read_text())
    assert hashlib.sha256((OUT/"training.csv").read_bytes()).hexdigest()==f["training_sha256"]
    cid=f["candidate"];cfg=f["config"];assert cfg==GRID[cid]
    if not f["passes_training_gate"]:
        (OUT/"REPORT.md").write_text("# C05 reclaim quality training result\n\nNo configuration passed the predefined training robustness gate. 2026 deliberately not replayed; no approved frozen candidate. See training_ranked.csv and FROZEN.json (diagnostic only).\n")
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
    lines=["# C05 reclaim quality training / frozen validation","",f"6 independent reclaim quality variants plus protected C05 control; 56 training path/cost replays. Selected C{cid:02d}: {cfg}. Training gate passed: {f['passes_training_gate']}.","Training: Feb-Dec 2024 (Feb 1-2 warmup), Jan-Dec 2025 (source starts Jan 1 UTC). Validation: Jan-Oct 2026 (Dec 2025 warmup, no pre-2026 entries). 2026 was examined in previous research, so this is a procedural holdout, not genuinely untouched OOS. No tuning on validation results.","Confirmed H4 EMA50, fixed ATR14 stop and TP, fixed 2.5R delayed entry-price lock; one optional reclaim quality filter. Zero-R lock is price breakeven before fees and slippage. No adaptive rules. No combined strategies, hedging, monthly or account-history switches. Fixed exposure. Baseline costs 0.05% taker per side+GST18%, slip 0.02% per side; stress slip 0.06%. Funding excluded.","",z[cols].to_markdown(index=False),"","## Monthly returns (normal costs, worse of two paths)",m[~m.stress].groupby(["month_ist","profile"]).monthly_return_pct.min().unstack().to_markdown(),""]
    (OUT/"REPORT.md").write_text("\n".join(lines)+"\n")
    print("\n".join(lines),flush=True)
if __name__=="__main__":
    if sys.argv[1]=="train":train()
    elif sys.argv[1]=="freeze":freeze()
    else:validate()
