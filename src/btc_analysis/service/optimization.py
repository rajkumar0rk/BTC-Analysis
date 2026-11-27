"""Bounded train-only visual parameter search, no uploaded Python execution."""
from copy import deepcopy
from decimal import Decimal as D
from hashlib import sha256
from itertools import product
from random import Random
from typing import Literal, Annotated
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator
from ..visual import Graph, compile_graph, DecimalText, raw_rules
from ..serialization import fingerprint, to_wire
from .historical import HistoricalRequest, prepare, execute_historical
from .analytics import summarize
from .fixture import Cancelled

MAX_CANDIDATES=8
MAX_GRID=512
MAX_CANDIDATE_MINUTES=5760

class Axis(BaseModel):
    model_config=ConfigDict(extra="forbid",strict=True)
    key:Annotated[str,StringConstraints(pattern=r"^(exposure_pct|stop_loss_pct|take_profit_pct|[a-z_]+\.[a-z_]+@[0-9]+:[a-z_]+|custom:[A-Za-z][A-Za-z0-9_]{0,47}\.lookback|target:(long|short)\.target_points|lock:(long|short)\.locked_points|partial_level:(long|short)\.[1-4]\.pct|partial:(long|short)\.pct|python:[A-Za-z][A-Za-z0-9_]*|(sequence|machine|exit_machine):(long|short)\.expiry_bars|advanced:(stop_points|target_points|confirmation_bars|cooldown_bars|trailing\.activation|trailing\.distance|profit_lock\.activation|profit_lock\.locked|trailing_percent\.activation|trailing_percent\.distance|trailing_atr\.activation|trailing_atr\.period|trailing_atr\.multiplier))$",max_length=80)]
    values:list[DecimalText]=Field(min_length=1,max_length=8)
    @model_validator(mode="after")
    def unique(self):
        if len({D(v) for v in self.values})!=len(self.values):
            raise ValueError("duplicate numeric axis value")
        return self

class Search(BaseModel):
    model_config=ConfigDict(extra="forbid",strict=True)
    method:Literal["grid","random"]="grid"
    axes:list[Axis]=Field(min_length=1,max_length=3)
    samples:Annotated[int,Field(ge=1,le=MAX_CANDIDATES)]=4
    seed:Annotated[int,Field(ge=0,le=2147483647)]=42
    objective:Literal["net_return","profit_factor","win_rate"]="net_return"
    max_drawdown_pct:DecimalText="20"
    min_trades:Annotated[int,Field(ge=1,le=1000)]=1
    @model_validator(mode="after")
    def check(self):
        if not 0<=D(self.max_drawdown_pct)<=100:raise ValueError("invalid drawdown cap")
        if len({a.key for a in self.axes})!=len(self.axes):raise ValueError("duplicate axis")
        return self

class OptimizationRequest(HistoricalRequest):
    kind:Literal["optimization"]
    search:Search
    acknowledge_training_only:Literal[True]

def historical_request(r):
    return HistoricalRequest.model_validate({**r.model_dump(exclude={"search","acknowledge_training_only"}),"kind":"historical_visual"})

def combinations_for(search):
    axes=sorted(search.axes,key=lambda x:x.key)
    combinations=list(product(*(sorted((to_wire(D(v)) for v in a.values),key=D) for a in axes)))
    if len(combinations)>MAX_GRID:raise ValueError("grid exceeds 512 combinations")
    if search.method=="grid":
        if len(combinations)>MAX_CANDIDATES:raise ValueError("grid exceeds 8 candidates; use random search")
        selected=combinations
    else:
        if search.samples>len(combinations):raise ValueError("samples exceed unique combinations")
        selected=Random(search.seed).sample(combinations,search.samples)
    return [dict(zip((a.key for a in axes),combo)) for combo in selected]

def variants(graph,search):
    result=[]
    for params in combinations_for(search):
        g=deepcopy(graph)
        for key,val in params.items():
            a=g.get("advanced") or {}
            if key.startswith("python:"):raise ValueError("Python axes require handwritten SDK source")
            if key in ("exposure_pct","stop_loss_pct","take_profit_pct"):
                if key!="exposure_pct" and a.get("exit_mode")=="points":raise ValueError("percentage axis inactive in fixed-point mode")
                g[key]=val;continue
            if key.startswith("custom:"):
                name=key[len("custom:"):-len(".lookback")]
                if D(val)!=D(val).to_integral_value():raise ValueError("custom lookback must be integer")
                definition=next((d for d in (g.get("custom_formulas") or []) if d["name"]==name),None)
                if definition is None:raise ValueError("custom axis not found: "+name)
                definition["lookback"]=int(D(val));continue
            if key.startswith("target:"):
                direction=key.split(":",1)[1].split(".",1)[0]
                target=g.get(direction+"_target")
                if target is None:raise ValueError("target axis requires enabled conditional target")
                target["target_points"]=val;continue
            if key.startswith("lock:"):
                direction=key.split(":",1)[1].split(".",1)[0]
                lock=g.get(direction+"_lock")
                if lock is None:raise ValueError("lock axis requires enabled conditional lock")
                lock["locked_points"]=val;continue
            if key.startswith("partial_level:"):
                direction,index,_=key.split(":",1)[1].split(".")
                levels=g.get(direction+"_partial_levels")
                if levels is None or int(index)>len(levels):raise ValueError("partial level axis requires declared level")
                levels[int(index)-1]["pct"]=val;continue
            if key.startswith("partial:"):
                direction=key.split(":",1)[1].split(".",1)[0]
                partial=g.get(direction+"_partial")
                if partial is None:raise ValueError("partial axis requires enabled partial exit")
                partial["pct"]=val;continue
            if key.startswith(("sequence:","machine:","exit_machine:")):
                kind,field=key.split(":",1)
                direction=field.split(".",1)[0]
                seq=g.get(direction+"_"+kind)
                if seq is None:raise ValueError("stateful axis requires enabled "+kind)
                if D(val)!=D(val).to_integral_value():raise ValueError("expiry must be integer")
                seq["expiry_bars"]=int(D(val));continue
            if key.startswith("advanced:"):
                name=key.split(":",1)[1]
                if not a:raise ValueError("advanced axis requires enabled advanced controls")
                if name in ("confirmation_bars","cooldown_bars"):
                    if D(val)!=D(val).to_integral_value():raise ValueError("advanced candle count must be integer")
                    a[name]=int(D(val))
                else:
                    if a.get("exit_mode")!="points":raise ValueError("point exit axis requires fixed-point mode")
                    if name=="target_points" and a.get("target_enabled") is False:raise ValueError("take profit disabled")
                    if "." in name:
                        group,field=name.split(".",1)
                        if not isinstance(a.get(group),dict):raise ValueError("managed exit axis requires enabled policy")
                        if group=="trailing_atr" and field=="period":
                            if D(val)!=D(val).to_integral_value():raise ValueError("ATR period must be integer")
                            a[group][field]=int(D(val))
                        else:a[group][field]=val
                    else:a[name]=val
                continue
            name,rest=key.split("@");tf,param=rest.split(":");matched=0
            for rule in raw_rules(g):
                for group in rule["groups"]:
                    for c in group["conditions"]:
                        for side in ("left","right"):
                            o=c[side]
                            if o["kind"]=="indicator" and o["name"]==name and o["timeframe"]==int(tf) and param in o["parameters"]:
                                orig=o["parameters"][param]
                                if type(orig) is int:
                                    if D(val)!=D(val).to_integral_value():raise ValueError("indicator period must be integer")
                                    o["parameters"][param]=int(D(val))
                                else:o["parameters"][param]=val
                                matched+=1
            if not matched:raise ValueError("axis not found in graph: "+key)
        compiled=compile_graph(Graph.model_validate(g))
        result.append((params,compiled))
    if len({c["graph_sha256"] for _,c in result})!=len(result):raise ValueError("duplicate candidate graphs")
    return result

def plan(payload):
    r=OptimizationRequest.model_validate({k:v for k,v in payload.items() if k not in ("graph","graph_sha256","code_sha256")})
    choices=variants(payload["graph"],r.search)
    if len(choices)*((r.end-r.start)//60+r.warmup_minutes)>MAX_CANDIDATE_MINUTES:
        raise ValueError("search exceeds combined 5760 candidate-minute budget")
    return r,choices

def prepare_optimization(root,r,revision):
    pinned=prepare(root,historical_request(r),revision)
    payload={**pinned,"kind":"optimization","search":r.search.model_dump(),"acknowledge_training_only":True}
    plan(payload)
    return payload

def rank_candidate(metrics,search):
    """Conservative scenario-wise objective: no cherry-picked OHLC path."""
    dd=max(D(m["max_event_drawdown_pct"]) for m in metrics)
    trades=min(m["trades"] for m in metrics)
    reasons=[]
    if dd>D(search.max_drawdown_pct):reasons.append("drawdown")
    if trades<search.min_trades:reasons.append("minimum_trades")
    key={"net_return":"account_return_pct","profit_factor":"profit_factor","win_rate":"win_rate_pct"}[search.objective]
    vals=[m[key] for m in metrics]
    score=min(D(v) for v in vals) if all(v is not None for v in vals) else None
    if score is None:reasons.append("undefined_objective")
    return score,dd,trades,reasons

def execute_optimization(payload,root,progress):
    r,choices=plan(payload)
    base=compile_graph(Graph.model_validate(payload["graph"]))
    if base["graph_sha256"]!=payload["graph_sha256"] or sha256(base["source"].encode()).hexdigest()!=payload["code_sha256"]:
        raise ValueError("base source fingerprint mismatch")
    request=historical_request(r).model_dump()
    rows=[];n=len(choices);verified=True;assumptions=[]
    for index,(params,compiled) in enumerate(choices):
        if not progress(index*99//n):raise Cancelled()
        variant={**request,"graph":compiled["graph"],"graph_sha256":compiled["graph_sha256"],
                 "code_sha256":sha256(compiled["source"].encode()).hexdigest()}
        out=execute_historical(variant,root,lambda p:progress((index*99+p)//n))
        metrics=[summarize(s) for s in out["result"]["scenarios"]]
        score,dd,trades,reasons=rank_candidate(metrics,r.search)
        verified=verified and out["timestamp_label_verified"];assumptions=out["assumptions"]
        rows.append(to_wire({"parameters":params,"graph_sha256":compiled["graph_sha256"],
            "code_sha256":variant["code_sha256"],"result_sha256":out["result_sha256"],
            "scenarios":[{"path":s["path"],"metrics":m} for s,m in zip(out["result"]["scenarios"],metrics)],
            "score":score,"max_drawdown_pct":dd,"min_closed_trades":trades,"eligible":not reasons,"rejections":reasons}))
    rows.sort(key=lambda x:(not x["eligible"],-D(x["score"]) if x["score"] is not None else D("Infinity"),D(x["max_drawdown_pct"]),x["graph_sha256"]))
    for i,row in enumerate(rows):row["rank"]=i+1
    study={"schema_version":1,"training_only":True,"search":r.search.model_dump(),
           "base_graph_sha256":payload["graph_sha256"],"base_code_sha256":payload["code_sha256"],
           "training_request":request,"candidates":rows,"winner_graph_sha256":next((x["graph_sha256"] for x in rows if x["eligible"]),None),
           "timestamp_label_verified":verified}
    if not progress(99):raise Cancelled()
    return {"kind":"optimization","synthetic":False,"research_only":True,"timestamp_label_verified":verified,
            "dataset_manifest_sha256":r.manifest_sha256,"result_sha256":fingerprint(study),
            "assumptions":assumptions+["Training-only selection, no untouched validation or deployment approval."],
            "optimization":study,"result":{"scenarios":[],"worst_path":"","limitations":["Candidate summaries only; rerun selected parameters separately for a full ledger."]}}
