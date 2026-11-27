"""Regenerate archived indicator history from pinned source declarations and exact inputs.
No strategy execution, no hardcoded strategy selection, no eval/exec of source code.
Publication is refused unless archived signal snapshots match the replay.
"""
import ast
import csv
import gzip
import hashlib
import json
import math
import re
import subprocess
import sys
import textwrap
from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal as D
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from btc_analysis.contracts import AssetClass, Candle, Instrument, Timeframe
from btc_analysis.indicators import IndicatorBook, spec
from dashboard_archive import dump

def source_fetch(repo,sha,path):
    if not re.fullmatch(r"[a-f0-9]{40}",sha) or not re.fullmatch(r"[A-Za-z0-9_./-]+",path) or ".." in Path(path).parts:
        raise ValueError("invalid pinned source locator")
    return subprocess.check_output(["curl","--fail","--silent","--show-error","--location","--retry","3","--max-time","120",f"https://raw.githubusercontent.com/{repo}/{sha}/{path}"])

def literal(node,env):
    if isinstance(node,ast.Name) and node.id in env:return env[node.id]
    if isinstance(node,ast.Dict):
        return {literal(k,env):literal(v,env) for k,v in zip(node.keys,node.values)}
    if isinstance(node,(ast.Tuple,ast.List)):return tuple(literal(x,env) for x in node.elts)
    if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=="Timeframe" and len(node.args)==1 and not node.keywords:
        return Timeframe(literal(node.args[0],env))
    return ast.literal_eval(node)

def declarations(source,variable):
    # The reviewed workflow contains one inline Python heredoc. Only literal
    # declarations and calls to the known spec constructor are interpreted.
    if "python - <<'PY'" in source:
        source=textwrap.dedent(source.split("python - <<'PY'",1)[1].split("\n          PY",1)[0])
    module=ast.parse(source)
    env={}
    for statement in module.body:
        if not isinstance(statement,ast.Assign) or len(statement.targets)!=1 or not isinstance(statement.targets[0],ast.Name):continue
        name=statement.targets[0].id; node=statement.value
        if name==variable:
            if not isinstance(node,ast.Call) or not isinstance(node.func,ast.Name) or node.func.id!="IndicatorBook" or len(node.args)!=1 or node.keywords or not isinstance(node.args[0],(ast.Tuple,ast.List)):
                raise ValueError("unsupported IndicatorBook declaration")
            out=[]
            for item in node.args[0].elts:
                if not isinstance(item,ast.Call) or not isinstance(item.func,ast.Name) or item.func.id!="spec" or len(item.args)!=2:raise ValueError("unsupported spec declaration")
                args=[literal(x,env) for x in item.args];kw={}
                for k in item.keywords:
                    value=literal(k.value,env)
                    if k.arg is None:kw.update(value)
                    else:kw[k.arg]=value
                out.append(spec(*args,**kw))
            if not out or len(out)>64 or len(set(out))!=len(out):raise ValueError("invalid indicator declarations")
            return tuple(out)
        try:env[name]=literal(node,env)
        except (ValueError,TypeError,KeyError):pass
    raise ValueError("declared indicator book not found")

def metadata(definitions):
    out=[]
    for i,d in enumerate(definitions):
        params={k:str(v) if isinstance(v,D) else v for k,v in d.parameters}
        # General catalog output semantics, not strategy-dependent settings.
        price=d.base in {"ema","sma","vwap","bollinger","donchian"} or d.name=="supertrend.line"
        out.append(dict(id=f"indicator_{i}",name=d.name,timeframe_minutes=d.timeframe.seconds//60,panel="price" if price else "panel",parameters=params))
    return out

def epoch(value):return int(datetime.fromisoformat(value).timestamp())
def dt(value):return datetime.fromtimestamp(value,timezone.utc)

def replay(root,repo,config,records,run_dir,symbol):
    sha=config["source_commit"]
    fetch=lambda path:source_fetch(repo,sha,path)
    # Ensure the currently installed implementation is byte-identical to source.
    for path in ("src/btc_analysis/indicators.py","src/btc_analysis/contracts.py"):
        if (root/path).read_bytes()!=fetch(path):raise ValueError("pinned indicator runtime differs; isolated source runtime required")
    defs=declarations(fetch(config["source_path"]).decode(),config["book_variable"])
    meta=metadata(defs)
    if any(d.timeframe.seconds%60 for d in defs):raise ValueError("non-minute timeframe")
    manifest_path=Path(config["candle_manifest"])
    source_manifest=json.loads(fetch(manifest_path.as_posix()))
    if source_manifest["symbol"]!=symbol:raise ValueError("indicator input symbol mismatch")
    start,end=epoch(config["start_utc"]),epoch(config["end_utc"])
    groups={d.timeframe.seconds:[] for d in defs}
    book=IndicatorBook(defs,history_limit=1)
    # Candle identity is irrelevant to the formulas but stable throughout replay.
    instrument=Instrument("delta_india",symbol,AssetClass.CRYPTO_PERPETUAL,"USD","USD",D("0.5"),D("1"),D("0.001"))
    series={m["id"]:[] for m in meta};last=None;count=0
    for part in source_manifest["partitions"]:
        if epoch(part["utc_end_exclusive"])<=start:continue
        if epoch(part["utc_start"])>=end:break
        rel=manifest_path.parent/part["file"]
        local=root/rel
        raw=local.read_bytes() if local.exists() else b""
        if hashlib.sha256(raw).hexdigest()!=part["sha256_gzip"]:raw=fetch(rel.as_posix())
        if hashlib.sha256(raw).hexdigest()!=part["sha256_gzip"]:raise ValueError("pinned candle hash mismatch: "+str(rel))
        import io
        with gzip.GzipFile(fileobj=io.BytesIO(raw)) as zipped:
            for row in csv.DictReader(io.TextIOWrapper(zipped)):
                t=int(row["time"])
                if t<start:continue
                if t>=end:break
                if t!=(start if last is None else last+60):raise ValueError("noncontinuous pinned indicator inputs")
                last=t;count+=1
                v=tuple(float(row[k]) for k in ("open","high","low","close"))+(float(row["volume"] or 0),)
                for seconds,group in groups.items():
                    group.append(v)
                    if len(group)!=seconds//60:continue
                    o,hi,lo,c,vol=group[0][0],max(x[1] for x in group),min(x[2] for x in group),group[-1][3],sum(x[4] for x in group)
                    candle=Candle(instrument,Timeframe(seconds),dt(t+60-seconds),dt(t+60),*(D(str(x)) for x in (o,hi,lo,c,vol)))
                    book.update(candle);group.clear()
                    for d,m in zip(defs,meta):
                        if d.timeframe.seconds!=seconds:continue
                        value=book.get(d.name,d.timeframe,dict(d.parameters))[-1]
                        series[m["id"]].append([t+60,None if value is None else float(value)])
    if count!=config["expected_bars"] or last!=end-60:raise ValueError("pinned replay bar count mismatch")
    maps={key:dict(points) for key,points in series.items()}
    fields=config["signal_fields"];checks=0
    for trade in records:
        ts=epoch(trade["trigger_utc"]);snap={}
        for d,m in zip(defs,meta):
            field=fields.get(d.name)
            if not field:continue
            expected=trade["signal_context"].get(field)
            actual=maps[m["id"]].get(ts)
            if expected is None or actual is None or not math.isclose(float(expected),actual,rel_tol=1e-10,abs_tol=1e-8):
                raise ValueError(f"indicator snapshot mismatch {trade['id']} {field}: {expected} != {actual}")
            snap[m["id"]]=float(expected);checks+=1
        trade["indicator_values"]=snap
    if not records or checks!=len(records)*len(fields):raise ValueError("incomplete archived snapshot verification")
    # Shard by observation date, plus the previous observation for step continuity.
    days=sorted({dt(t).date().isoformat() for points in series.values() for t,_ in points})
    from bisect import bisect_left
    times={k:[p[0] for p in points] for k,points in series.items()}
    for day in days:
        a=epoch(day+"T00:00:00+00:00");b=a+86400
        shard={}
        for key,points in series.items():
            lo=bisect_left(times[key],a);hi=bisect_left(times[key],b)
            shard[key]=points[max(0,lo-1):hi]
        dump(run_dir/"indicators"/(day+".json"),shard)
    print(f"Verified {checks} archived indicator snapshots, {count} input minutes, {len(days)} indicator days",flush=True)
    return dict(indicator_definitions=meta,indicator_days=days,indicator_provenance={"source_commit":sha,"source_path":config["source_path"],"method":"pinned_input_replay_snapshot_verified","verified_snapshots":checks,"input_bars":count})
