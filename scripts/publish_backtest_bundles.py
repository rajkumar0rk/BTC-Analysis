"""Unprivileged-data ingestion for the versioned backtest artifact contract.
Never imports or executes files from research branches. Only one bounded JSON file.
The trusted main publisher persists accepted bundles before publishing a snapshot.
"""
import argparse, hashlib, io, json, math, os, re, subprocess, zipfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from backtest_bundle import ARTIFACT
from dashboard_archive import dump, stats, curve

MAX_JSON=120*1024**2
SAFE=re.compile(r"^[A-Za-z0-9_.:-]{1,128}$")
def require(ok,msg):
    if not ok:raise ValueError(msg)
def finite(v):return type(v) in (int,float) and math.isfinite(v)
def stamp(v):
    require(isinstance(v,str),"timestamp must be ISO UTC")
    d=datetime.fromisoformat(v)
    require(d.tzinfo is not None and d.utcoffset().total_seconds()==0,"timestamp must be UTC")
    return d.astimezone(timezone.utc).isoformat()
def integer(v,low,high):return type(v) is int and low<=v<=high
def key(v):return isinstance(v,str) and SAFE.fullmatch(v)
def validate(b,run=None):
    require(isinstance(b,dict) and b.get("schema")==1,"unsupported bundle")
    require(key(b.get("family")) and b.get("symbol") in ("BTCUSD","ETHUSD") and b.get("unit") in ("account USD","price points"),"invalid family/symbol/unit")
    require(re.fullmatch(r"[a-f0-9]{40}",b.get("source_commit","")) and integer(b.get("source_run_id"),1,10**15) and integer(b.get("source_attempt"),1,1000),"invalid source identity")
    if run is not None:
        require(run["conclusion"]=="success" and run["head_sha"]==b["source_commit"] and run["id"]==b["source_run_id"] and run["run_attempt"]==b["source_attempt"],"source run mismatch")
    start,end=stamp(b["start_utc"]),stamp(b["end_utc"]);require(start<end,"bad evaluation window")
    require(integer(b.get("execution_timeframe_minutes"),1,1440) and integer(b.get("signal_timeframe_minutes"),1,1440),"invalid timeframes")
    require(isinstance(b.get("costs"),str) and 0<len(b["costs"])<=20000,"missing cost assumptions")
    require(isinstance(b.get("data_provenance"),dict),"missing provenance")
    defs=b["indicator_definitions"];series=b["indicator_series"]
    require(isinstance(defs,list) and len(defs)<=64 and isinstance(series,dict),"invalid indicator metadata")
    ids=[]
    for d in defs:
        require(key(d.get("id")) and isinstance(d.get("name"),str) and 0<len(d["name"])<=256 and integer(d.get("timeframe_minutes"),1,10080) and d.get("panel") in ("price","panel") and isinstance(d.get("parameters"),dict),"invalid indicator declaration")
        ids.append(d["id"])
    require(len(ids)==len(set(ids)) and set(ids)==set(series),"indicator series must match declarations")
    low=int(datetime.fromisoformat(start).timestamp());high=int(datetime.fromisoformat(end).timestamp())
    for id,points in series.items():
        require(isinstance(points,list) and 0<len(points)<=2000000,"missing or oversized indicator series")
        prev=low-1
        for p in points:
            require(isinstance(p,list) and len(p)==2 and type(p[0]) is int and prev<p[0]<=high and (p[1] is None or finite(p[1])),"invalid indicator observation")
            prev=p[0]
    vs=b["variants"];require(isinstance(vs,list) and 0<len(vs)<=1000,"missing variants")
    used=set()
    for v in vs:
        require(key(v.get("key")) and v["key"] not in used and isinstance(v.get("name"),str) and 0<len(v["name"])<=300 and isinstance(v.get("parameters"),dict),"invalid variant")
        used.add(v["key"]);s=v["summary"];rows=v["trades"]
        require(isinstance(s,dict) and isinstance(rows,list) and len(rows)<=1000000 and s.get("trades")==len(rows),"trade count mismatch")
        require(finite(s.get("net")),"missing source net")
        for t in rows:
            en,ex=stamp(t["entry_utc"]),stamp(t["exit_utc"])
            require(start<=en<=ex<=end and t.get("side") in (-1,1) and type(t["side"]) is int and finite(t.get("entry_price")) and t["entry_price"]>0 and finite(t.get("exit_price")) and t["exit_price"]>0 and finite(t.get("net_points")),"invalid trade")
            if t.get("trigger_utc") is not None:require(stamp(t["trigger_utc"])<=en,"future trigger")
            require(isinstance(t.get("exit_reason"),str) and isinstance(t.get("signal_context",{}),dict),"missing trade evidence")
            for field in ("indicator_values","indicator_series"):
                if field in t:require(isinstance(t[field],dict) and set(t[field])<=set(ids),"undeclared trade indicator")
        realized=sum(t["net_points"] for t in rows)
        # Closed positions reconcile to source total only if the source explicitly
        # declares realized accounting or confirms no open position.
        if s.get("accounting")=="realized" or ("open_position" in s and s["open_position"] is None):
            require(math.isclose(realized,s["net"],rel_tol=1e-7,abs_tol=1e-6),"closed net mismatch")
        if "wins" in s:require(s["wins"]==sum(t["net_points"]>0 for t in rows),"win count mismatch")
        if "events" in v:require(isinstance(v["events"],list) and len(v["events"])<=2000000,"invalid event ledger")
    return b

def api(path):return json.loads(subprocess.check_output(["gh","api",path]))
def collect(cache,repo):
    cache.mkdir(parents=True,exist_ok=True)
    pages=subprocess.check_output(["gh","api","--paginate",f"repos/{repo}/actions/artifacts?name={ARTIFACT}&per_page=100","--jq",".artifacts[] | @json"],text=True)
    for line in pages.splitlines():
        a=json.loads(line)
        if a.get("name")!=ARTIFACT or a.get("expired"):continue
        aid=a["id"];run_id=a.get("workflow_run",{}).get("id")
        if not integer(aid,1,10**16) or not integer(run_id,1,10**15):continue
        dest=cache/f"{aid}.json"
        if dest.exists():continue
        if not integer(a.get("size_in_bytes"),1,MAX_JSON):print("Rejected oversized artifact",aid);continue
        try:
            run=api(f"repos/{repo}/actions/runs/{run_id}")
            if run.get("status")!="completed" or run.get("conclusion")!="success":continue
            if run.get("head_repository",{}).get("full_name")!=repo:continue
            raw=subprocess.check_output(["gh","api",f"repos/{repo}/actions/artifacts/{aid}/zip"])
            require(len(raw)<=MAX_JSON,"oversized download")
            with zipfile.ZipFile(io.BytesIO(raw)) as z:
                require(z.namelist()==["backtest.json"] and z.getinfo("backtest.json").file_size<=MAX_JSON,"unexpected artifact layout")
                b=validate(json.loads(z.read("backtest.json")),run)
            envelope=dict(artifact_id=aid,completed_at=run["updated_at"],branch=run["head_branch"],bundle=b)
            tmp=dest.with_suffix(".tmp");dump(tmp,envelope);tmp.replace(dest)
            print("Accepted completed backtest",run_id,aid,len(b["variants"]))
        except (ValueError,KeyError,TypeError,zipfile.BadZipFile,subprocess.CalledProcessError) as e:
            print(f"::warning::Backtest artifact {aid} not imported: {e}")

def month_keys(start,end):
    a=datetime.fromisoformat(start);b=datetime.fromisoformat(end)
    y,m=a.year,a.month
    while (y,m)<=(b.year,b.month):
        yield f"{y:04d}-{m:02d}";m+=1
        if m==13:y+=1;m=1

def publish(cache,data):
    index=json.loads((data/"index.json").read_text());runs=index["runs"]
    auto=[];seen=set()
    for path in sorted(cache.glob("*.json")):
        envelope=json.loads(path.read_text());b=validate(envelope["bundle"]);aid=envelope["artifact_id"]
        require(str(aid)==path.stem,"artifact cache identity mismatch")
        # Shard recorded values by observation day. Duplicate boundary seed
        # permits accurate cross-day sampling without indicator recalculation.
        shards=defaultdict(dict)
        for id,points in b["indicator_series"].items():
            days=defaultdict(list);prior=None;last_day=None
            for p in points:
                day=datetime.fromtimestamp(p[0],timezone.utc).date().isoformat()
                if day!=last_day and prior is not None:days[day].append(prior)
                days[day].append(p);prior=p;last_day=day
            for day,pts in days.items():shards[day][id]=pts
        for v in b["variants"]:
            identity=(b["source_run_id"],b["source_attempt"],b["family"],v["key"])
            require(identity not in seen,"duplicate version identity");seen.add(identity)
            rid="v"+hashlib.sha256(repr(identity).encode()).hexdigest()[:24];folder=data/"runs"/rid
            rows=[]
            for i,t in enumerate(v["trades"]):
                rec=dict(t,id=f"{rid}-{i}",entry_utc=stamp(t["entry_utc"]),exit_utc=stamp(t["exit_utc"]),result=t.get("result") or t["exit_reason"],signal_tf=b["signal_timeframe_minutes"])
                if rec.get("trigger_utc"):rec["trigger_utc"]=stamp(rec["trigger_utc"])
                rows.append(rec)
            by=defaultdict(list)
            for t in rows:by[t["entry_utc"][:7]].append(t)
            months=[]
            for m in month_keys(b["start_utc"],b["end_utc"]):
                rr=sorted(by[m],key=lambda t:t["entry_utc"]);dump(folder/(m+".json"),rr)
                months.append(dict(month=m,net=round(sum(t["net_points"] for t in rr),6),trades=len(rr),wins=sum(t["net_points"]>0 for t in rr)))
            metrics=stats(rows) if rows else dict(trades=0,net=0,win_rate=0,profit_factor=None,drawdown=0)
            dump(folder/"curve.json",curve(rows) if rows else [[stamp(b["start_utc"]),0,0]])
            ids=[d["id"] for d in b["indicator_definitions"]]
            for day,values in sorted(shards.items()):dump(folder/"indicators"/(day+".json"),{id:values.get(id,[]) for id in ids})
            if "events" in v:dump(folder/"events.json",v["events"])
            r=dict(id=rid,strategy=v["name"],symbol=b["symbol"],unit=b["unit"],source=f"https://github.com/{os.environ.get('GITHUB_REPOSITORY','rajkumar0rk/BTC-Analysis')}/actions/runs/{b['source_run_id']}",audit="Source-recorded closed-trade ledger; source summary kept separately",costs=b["costs"],target=None,stop=None,months=months,detail_available=True,automatic_version=True,family=b["family"],variant_key=v["key"],parameters=v["parameters"],source_commit=b["source_commit"],source_run_id=b["source_run_id"],source_attempt=b["source_attempt"],source_branch=envelope["branch"],completed_at=envelope["completed_at"],signal_timeframe_minutes=b["signal_timeframe_minutes"],execution_timeframe_minutes=b["execution_timeframe_minutes"],start_utc=b["start_utc"],end_utc=b["end_utc"],source_summary=v["summary"],data_provenance=b["data_provenance"],indicator_definitions=b["indicator_definitions"],indicator_days=sorted(shards),indicator_provenance={"method":"source_recorded","source_commit":b["source_commit"]},events_available="events" in v,**metrics)
            auto.append(r)
    latest={}
    for r in auto:
        k=(r["symbol"],r["family"],r["variant_key"])
        rank=(r["completed_at"],r["source_run_id"],r["source_attempt"])
        if k not in latest or rank>latest[k][0]:latest[k]=(rank,r["id"])
    for r in auto:r["latest_version"]=r["id"]==latest[(r["symbol"],r["family"],r["variant_key"])][1]
    # Allocate permanent catalog numbers, in completion order for new entries.
    # Keep the registry even when an older bundle is no longer present.
    previous=os.getenv("DASHBOARD_PREVIOUS_DATA")
    prior=Path(previous)/"index.json" if previous else None
    registry=dict(json.loads(prior.read_text()).get("backtest_number_registry",{}) if prior and prior.is_file() else index.get("backtest_number_registry",{}))
    require(all(isinstance(k,str) and integer(n,1,10**12) for k,n in registry.items()) and len(set(registry.values()))==len(registry),"invalid backtest number registry")
    next_number=max(registry.values(),default=0)+1
    for r in sorted(auto,key=lambda r:(r["completed_at"],r["source_run_id"],r["source_attempt"])):
        if r["id"] not in registry:
            registry[r["id"]]=next_number;next_number+=1
        r["backtest_number"]=registry[r["id"]]
        r["original_strategy"]=r["strategy"]
        r["strategy"]=f'BT-{r["backtest_number"]:04d} | {r["original_strategy"]}'
    index["backtest_number_registry"]=registry
    index["runs"]=runs+sorted(auto,key=lambda r:r["backtest_number"],reverse=True)
    index["automatic_run_count"]=len(auto);index["full_configurations"]=sum(r.get("detail_available",True) for r in index["runs"])
    dump(data/"index.json",index)
    print("Published versioned backtests:",len(auto))

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("mode",choices=["collect","publish"]);p.add_argument("cache",type=Path);p.add_argument("destination");a=p.parse_args()
    if a.mode=="collect":collect(a.cache,a.destination)
    else:publish(a.cache,Path(a.destination))
