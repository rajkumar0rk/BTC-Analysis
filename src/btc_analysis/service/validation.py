"""Fixed training-winner validation, disjoint chronological windows and stress."""
from decimal import Decimal as D
from hashlib import sha256
from math import lcm
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator
from ..visual import Graph, compile_graph, recover_graph, DecimalText
from ..serialization import fingerprint, to_wire
from .historical import HistoricalRequest, Id, Hash, frames, validate_clock, execute_historical
from .optimization import Search, variants
from .analytics import summarize
from .fixture import Cancelled

MAX_VALIDATION_MINUTES=5760

class Strict(BaseModel):
    model_config=ConfigDict(extra="forbid",strict=True)

class Window(Strict):
    start:Annotated[int,Field(ge=0,le=4102444800)]
    end:Annotated[int,Field(ge=0,le=4102444800)]
    @model_validator(mode="after")
    def check(self):
        if self.start%60 or self.end%60 or not 0<self.end-self.start<=86400:
            raise ValueError("validation window must be minute aligned, positive and at most 24h")
        return self

class ValidationRequest(Strict):
    optimization_job_id:Id
    optimization_result_sha256:Hash
    windows:list[Window]=Field(min_length=1,max_length=2)
    fee_multiplier:DecimalText="1.5"
    extra_slippage_bps:DecimalText="2"
    min_return_pct:DecimalText="0"
    max_drawdown_pct:DecimalText="20"
    min_trades:Annotated[int,Field(ge=1,le=1000)]=1
    acknowledge_holdout:Literal[True]
    @model_validator(mode="after")
    def check(self):
        if not 1<D(self.fee_multiplier)<=5 or not 0<D(self.extra_slippage_bps)<=100:
            raise ValueError("stress must increase fees and slippage")
        if not 0<=D(self.max_drawdown_pct)<=100 or not -100<=D(self.min_return_pct)<=1000:
            raise ValueError("invalid acceptance thresholds")
        if any(a.end>b.start for a,b in zip(self.windows,self.windows[1:])):
            raise ValueError("validation windows must be chronological and disjoint")
        return self

def choice_plan(base,study):
    if study["base_graph_sha256"]!=base["graph_sha256"]:
        raise ValueError("base graph mismatch")
    winner=study["winner_graph_sha256"]
    if not winner:raise ValueError("optimization has no eligible training winner")
    search=Search.model_validate(study["search"])
    choices=variants(base["graph"],search)
    chosen=next(((p,c) for p,c in choices if c["graph_sha256"]==winner),None)
    row=next((r for r in study["candidates"] if r["graph_sha256"]==winner and r["eligible"]),None)
    if chosen is None or row is None or sha256(chosen[1]["source"].encode()).hexdigest()!=row["code_sha256"]:
        raise ValueError("winning candidate provenance mismatch")
    # Select one closest evaluated training neighbor, without looking at holdout.
    scale={a.key:max(D(v) for v in a.values)-min(D(v) for v in a.values) for a in search.axes}
    others=[(p,c) for p,c in choices if c["graph_sha256"]!=winner]
    def distance(item):
        p,c=item
        return (sum((abs(D(p[k])-D(chosen[0][k]))/scale[k] for k in p if scale[k]),D(0)),c["graph_sha256"])
    return chosen,min(others,key=distance) if others else None

def plans(base,study,request):
    train=HistoricalRequest.model_validate(study["training_request"])
    chosen,neighbor=choice_plan(base,study)
    if any(w.start<train.end for w in request.windows):
        raise ValueError("validation must start at or after training end")
    jobs=[]
    for i,w in enumerate(request.windows):
        r=train.model_dump();r.update(start=w.start,end=w.end)
        fee={k:to_wire(D(r[k])*D(request.fee_multiplier)) for k in ("maker_bps","taker_bps")}
        slip={"slippage_bps":to_wire(D(r["slippage_bps"])+D(request.extra_slippage_bps))}
        # Each path is independently reset, not compounded across windows.
        for label,patch in (("baseline",{}),("fee_stress",fee),("slippage_stress",slip),("combined_stress",{**fee,**slip})):
            jobs.append((i,label,HistoricalRequest.model_validate({**r,**patch}),chosen[1]))
        if neighbor:jobs.append((i,"parameter_neighbor",HistoricalRequest.model_validate(r),neighbor[1]))
        step=lcm(*frames(Graph.model_validate(chosen[1]["graph"])))
        mid=w.start+((w.end-w.start)//(2*step))*step
        if w.start<mid<w.end:
            jobs.append((i,"causal_prefix",HistoricalRequest.model_validate({**r,"end":mid}),chosen[1]))
    total=sum((r.end-r.start)//60+r.warmup_minutes for _,_,r,_ in jobs)
    if total>MAX_VALIDATION_MINUTES:raise ValueError("validation exceeds 5760 replay-minute budget")
    for _,_,r,c in jobs:validate_clock(Graph.model_validate(c["graph"]),r)
    return train,jobs

def prepare_validation(root,request,job,revision):
    if job["status"]!="succeeded" or job["request"]["kind"]!="optimization" or not job["result"]:
        raise ValueError("completed optimization required")
    out=job["result"];study=out["optimization"]
    if out["result_sha256"]!=request.optimization_result_sha256 or fingerprint(study)!=out["result_sha256"]:
        raise ValueError("optimization result hash mismatch")
    base=recover_graph(revision["source"])
    if revision["code_sha256"]!=study["base_code_sha256"]:raise ValueError("base source hash mismatch")
    train,jobs=plans(base,study,request)
    from ..data import HistoryStore
    if root is None:raise ValueError("historical store not configured")
    with HistoryStore(root,train.symbol,train.manifest_sha256) as h:
        h._label(train.assume_open)
        for _,_,r,_ in jobs:
            if not h.coverage(r.start-r.warmup_minutes*60,r.end).complete:
                raise ValueError("validation data coverage incomplete")
    return {**train.model_dump(),"kind":"validation","graph":base["graph"],"graph_sha256":base["graph_sha256"],
            "code_sha256":revision["code_sha256"],"validation_request":request.model_dump(),"training_study":study}

def gate(metrics,request):
    worst=min(D(m["account_return_pct"]) for m in metrics)
    dd=max(D(m["max_event_drawdown_pct"]) for m in metrics)
    trades=min(m["trades"] for m in metrics)
    reasons=[]
    if worst<D(request.min_return_pct):reasons.append("minimum_return")
    if dd>D(request.max_drawdown_pct):reasons.append("drawdown")
    if trades<request.min_trades:reasons.append("minimum_trades")
    return to_wire({"worst_return_pct":worst,"max_drawdown_pct":dd,"min_closed_trades":trades,
                    "passed":not reasons,"failures":reasons})

def prefix_matches(full,prefix,cut):
    """Compare fills by evidence bar membership, not ambiguous boundary timestamps."""
    def rows(s):
        evidence={e["fill_id"]:e for e in s["execution_evidence"]}
        from datetime import datetime
        def epoch(v):return int(datetime.fromisoformat(v.replace("Z","+00:00")).timestamp())
        return [(f,evidence[f["fill_id"]]) for f in s["fills"] if epoch(evidence[f["fill_id"]]["bar_open_utc"])<cut]
    return all(rows(a)==rows(b) for a,b in zip(full["scenarios"],prefix["scenarios"])) and \
        [s["path"] for s in full["scenarios"]]==[s["path"] for s in prefix["scenarios"]]

def execute_validation(payload,root,progress):
    req=ValidationRequest.model_validate(payload["validation_request"])
    study=payload["training_study"]
    if fingerprint(study)!=req.optimization_result_sha256:raise ValueError("training study fingerprint mismatch")
    base=compile_graph(Graph.model_validate(payload["graph"]))
    if base["graph_sha256"]!=payload["graph_sha256"] or sha256(base["source"].encode()).hexdigest()!=payload["code_sha256"] or payload["code_sha256"]!=study["base_code_sha256"]:
        raise ValueError("base source fingerprint mismatch")
    train,jobs=plans(base,study,req)
    rows=[];baselines={};verified=True;n=len(jobs)
    for k,(i,label,r,c) in enumerate(jobs):
        if not progress(k*99//n):raise Cancelled()
        p={**r.model_dump(),"graph":c["graph"],"graph_sha256":c["graph_sha256"],"code_sha256":sha256(c["source"].encode()).hexdigest()}
        out=execute_historical(p,root,lambda v:progress((k*99+v)//n))
        verified=verified and out["timestamp_label_verified"]
        if label=="baseline":baselines[i]=out["result"]
        row={"window":i+1,"test":label,"start":r.start,"end":r.end,"graph_sha256":c["graph_sha256"],
             "result_sha256":out["result_sha256"],"maker_bps":r.maker_bps,"taker_bps":r.taker_bps,"slippage_bps":r.slippage_bps}
        if label=="causal_prefix":
            ok=prefix_matches(baselines[i],out["result"],r.end)
            row.update(passed=ok,failures=[] if ok else ["prefix_fill_mismatch"])
        else:
            metrics=[summarize(s) for s in out["result"]["scenarios"]]
            row.update(gate(metrics,req))
            row["scenarios"]=[{"path":s["path"],"metrics":m} for s,m in zip(out["result"]["scenarios"],metrics)]
        rows.append(row)
    missing_prefix=len(req.windows)-sum(r["test"]=="causal_prefix" for r in rows)
    no_neighbor=not any(r["test"]=="parameter_neighbor" for r in rows)
    report={"schema_version":1,"training_result_sha256":req.optimization_result_sha256,
        "optimization_job_id":req.optimization_job_id,"winner_graph_sha256":study["winner_graph_sha256"],
        "training_start":train.start,"training_end":train.end,"criteria":req.model_dump(),
        "rows":rows,"modeled_checks_passed":all(r["passed"] for r in rows),
        "not_assessed":(["causal_prefix: window too short"] if missing_prefix else [])+
                       (["parameter_sensitivity: no training neighbor"] if no_neighbor else [])+
                       ["untouched data independently verified","funding","liquidation","exchange execution","multi-year walk-forward"],
        "timestamp_label_verified":verified,"production_approved":False}
    if not progress(99):raise Cancelled()
    return {"kind":"validation","synthetic":False,"research_only":True,"timestamp_label_verified":verified,
        "dataset_manifest_sha256":train.manifest_sha256,"result_sha256":fingerprint(report),"validation":report,
        "result":{"scenarios":[],"worst_path":"","limitations":["Fixed winner; disjoint holdout windows, not independently untouched or rolling retraining."]}}
