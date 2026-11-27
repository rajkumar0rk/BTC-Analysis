"""Bounded causal fold planner. Training selection never accesses test metrics."""
from copy import deepcopy
from decimal import Decimal as D, localcontext
from math import lcm
from typing import Annotated,Literal
from pydantic import BaseModel,ConfigDict,Field,model_validator
from ..visual import Graph,compile_graph,recover_graph,DecimalText
from ..serialization import fingerprint,to_wire
from .historical import frames
from .optimization import Search,variants,rank_candidate
from .fixture import Cancelled

class Study(BaseModel):
    model_config=ConfigDict(extra="forbid",strict=True)
    start:Annotated[int,Field(ge=0,le=4102444800)]
    train_minutes:Annotated[int,Field(ge=2,le=527040)]
    test_minutes:Annotated[int,Field(ge=2,le=527040)]
    folds:Annotated[int,Field(ge=2,le=4)]=2
    mode:Literal["rolling","expanding"]="rolling"
    search:Search
    objective:Literal["net_return","profit_factor","win_rate","monthly_consistency"]="net_return"
    fee_multiplier:DecimalText="1.5"
    extra_slippage_bps:DecimalText="2"
    min_test_return_pct:DecimalText="0"
    leverage_values:list[DecimalText]=Field(default_factory=list,max_length=8)
    funding_stress_multiplier:DecimalText="2"
    acknowledge:Literal[True]
    @model_validator(mode="after")
    def check(self):
        if self.start%60 or self.start+60*(self.train_minutes+self.test_minutes*self.folds)>4102444800:
            raise ValueError("invalid study clock")
        if not 1<D(self.fee_multiplier)<=5 or not 0<D(self.extra_slippage_bps)<=100:
            raise ValueError("stress must increase fees and slippage")
        if not -100<=D(self.min_test_return_pct)<=1000:raise ValueError("invalid test return threshold")
        if any(not 1<=D(v)<=100 for v in self.leverage_values) or len({D(v) for v in self.leverage_values})!=len(self.leverage_values):raise ValueError("invalid or duplicate study leverage")
        if not 1<D(self.funding_stress_multiplier)<=5:raise ValueError("funding stress multiplier must be >1 and <=5")
        return self

def compiled_source(text):
    if len(text.encode())>65536:raise ValueError("source too large")
    return recover_graph(text) if text.startswith("# btc-visual-v1 ") else compile_graph(Graph.model_validate_json(text))

def plan(base,study,*,budget):
    choices=variants(base["graph"],study.search)
    if study.leverage_values:
        choices=[({**p,"leverage":to_wire(D(v))},c) for p,c in choices for v in sorted(study.leverage_values,key=D)]
        if len(choices)>8:raise ValueError("combined leverage and graph candidates exceed eight")
    if len(choices)<2:raise ValueError("walk-forward needs at least two distinct candidates")
    g=Graph.model_validate(base["graph"])
    if g.execution_timeframe!=60:raise ValueError("walk-forward requires 1m execution")
    clock=lcm(*frames(g));windows=[]
    total=0
    for n in range(study.folds):
        cut=study.start+60*(study.train_minutes+n*study.test_minutes)
        lo=study.start if study.mode=="expanding" else cut-study.train_minutes*60
        hi=cut+60*study.test_minutes
        if any(t%clock for t in (lo,cut,hi)):raise ValueError("all fold boundaries must align with strategy timeframes")
        windows.append(dict(fold=n+1,train_start=lo,train_end=cut,test_start=cut,test_end=hi))
        total+=len(choices)*(cut-lo)//60+(9 if study.leverage_values else 5)*study.test_minutes
    if total>budget:raise ValueError("study exceeds bounded candidate/replay minute budget")
    return choices,windows,total

def select_metrics(result):
    return [s["metrics"] for s in result["scenarios"]]

def month_score(result):
    # Partial calendar-month segments are included, not claimed as full months.
    with localcontext() as ctx:
        ctx.prec=50
        scores=[];minimums=[]
        for s in result["scenarios"]:
            months=s["monthly"]
            if not months:raise ValueError("monthly results absent")
            scores.append(D(sum(D(m["pnl"])>0 for m in months))/len(months))
            returns=[D(m["return_pct"]) for m in months if m["return_pct"] is not None]
            minimums.append(min(returns) if len(returns)==len(months) else D("-Infinity"))
        return min(scores),min(minimums)

def risk_failures(result):
    if not all(type(s.get("liquidation_count")) is int and type(s.get("preliq_count")) is int for s in result["scenarios"]):raise ValueError("missing risk counters")
    return (["liquidation"] if any(s["liquidation_count"] for s in result["scenarios"]) else [])+(["preliquidation_halt"] if any(s["preliq_count"] for s in result["scenarios"]) else [])

def train_row(params,compiled,result,study):
    search=study.search.model_copy(update={"objective":study.objective if study.objective!="monthly_consistency" else "net_return"})
    score,dd,trades,reasons=rank_candidate(select_metrics(result),search)
    if study.leverage_values:reasons+=risk_failures(result)
    ratio,minimum=month_score(result)
    if study.objective=="monthly_consistency" and not minimum.is_finite():reasons.append("undefined_month_return")
    return to_wire(dict(parameters=params,graph_sha256=compiled["graph_sha256"],result_sha256=result["result_sha256"],
        score=score,positive_month_ratio=ratio,min_month_return=minimum if minimum.is_finite() else None,
        max_drawdown_pct=dd,min_trades=trades,eligible=not reasons,rejections=reasons,scenarios=result["scenarios"]))

def rank_key(row,study):
    score=D(row["score"]) if row["score"] is not None else D("-Infinity")
    primary=(-D(row["positive_month_ratio"]),-D(row["min_month_return"]) if row["min_month_return"] is not None else D("Infinity")) if study.objective=="monthly_consistency" else ()
    return (not row["eligible"],*primary,-score,D(row["max_drawdown_pct"]),row["graph_sha256"])

def gate(result,study):
    metrics=select_metrics(result)
    worst=min(D(m["account_return_pct"]) for m in metrics)
    dd=max(D(m["max_event_drawdown_pct"]) for m in metrics)
    trades=min(m["trades"] for m in metrics)
    failures=[]
    if worst<D(study.min_test_return_pct):failures.append("minimum_return")
    if dd>D(study.search.max_drawdown_pct):failures.append("drawdown")
    if trades<study.search.min_trades:failures.append("minimum_trades")
    if study.leverage_values:failures+=risk_failures(result)
    return to_wire(dict(worst_return_pct=worst,max_drawdown_pct=dd,min_trades=trades,passed=not failures,failures=failures))

def stress_settings(settings,study):
    fee={k:to_wire(D(settings[k])*D(study.fee_multiplier)) for k in ("maker_bps","taker_bps")}
    slip={"slippage_bps":to_wire(D(settings["slippage_bps"])+D(study.extra_slippage_bps))}
    if any(D(v)>100 for v in (*fee.values(),*slip.values())):raise ValueError("stress exceeds supported bps range")
    return [("baseline",dict(settings)),("fee_stress",{**settings,**fee}),("slippage_stress",{**settings,**slip}),("combined_stress",{**settings,**fee,**slip})]

def evaluate_fold(base,study,choices,window,settings,runner,progress=lambda p:True,risk=None):
    """runner receives only the requested time window and fixed compiled graph."""
    if bool(study.leverage_values)!=(risk is not None):raise ValueError("leverage candidates and explicit risk configuration required together")
    stress=stress_settings(settings,study)
    if risk is not None and risk["funding_enabled"]:
        stress += [("funding_positive",dict(settings)),("funding_negative",dict(settings)),("combined_funding_positive",stress[3][1]),("combined_funding_negative",stress[3][1])]
    n=len(choices)+len(stress)+1;done=0;training=[]
    def execute(compiled,lo,hi,cost,params,label="baseline"):
        nonlocal done
        if not progress(done*100//n):raise Cancelled()
        result=runner(compiled,lo,hi,cost,params["leverage"],label) if risk is not None else runner(compiled,lo,hi,cost)
        done+=1
        return result
    for params,compiled in choices:
        r=execute(compiled,window["train_start"],window["train_end"],settings,params)
        training.append(train_row(params,compiled,r,study))
    training.sort(key=lambda r:rank_key(r,study))
    winner=next((r for r in training if r["eligible"]),None)
    tests=[]
    if winner:
        params,chosen=next(x for x in choices if x[0]==winner["parameters"] and x[1]["graph_sha256"]==winner["graph_sha256"])
        scales={a.key:max(D(v) for v in a.values)-min(D(v) for v in a.values) for a in study.search.axes}
        if study.leverage_values:scales["leverage"]=max(map(D,study.leverage_values))-min(map(D,study.leverage_values))
        neighbor=min((x for x in choices if x[0]!=params),
            key=lambda x:(sum(abs(D(x[0][k])-D(params[k]))/scales[k] for k in params if scales[k]),x[1]["graph_sha256"],tuple(sorted(x[0].items()))))
        for label,cost in stress+[("parameter_neighbor",dict(settings))]:
            c=neighbor[1] if label=="parameter_neighbor" else chosen
            chosen_params=neighbor[0] if label=="parameter_neighbor" else params
            r=execute(c,window["test_start"],window["test_end"],cost,chosen_params,label)
            tests.append(dict(test=label,graph_sha256=c["graph_sha256"],result_sha256=r["result_sha256"],
                settings=cost,scenarios=r["scenarios"],**({"leverage":chosen_params["leverage"]} if risk is not None else {}),**gate(r,study)))
    out=dict(window=window,training=training,winner_graph_sha256=winner["graph_sha256"] if winner else None,
        winner_parameters=winner["parameters"] if winner else None,tests=tests,
        modeled_checks_passed=bool(winner) and len(tests)==len(stress)+1 and all(t["passed"] for t in tests),
        limitations=["Fresh independent account and indicators per window; no compounded OOS equity.",
            "Calendar-month segments may be partial; no claim of full-month consistency.",
            "Training-only selection within each fold; later folds may train on earlier test windows.",
            "User has seen the source data; untouched status not independently verified.",
            ("Explicit modeled margin/funding inputs; reject liquidation and pre-liquidation halts on either path. Funding stress uses both signs of multiplied absolute rates, not actual historical settlements. No exchange-certified fills." if risk is not None else "1x, no funding, spread or liquidation; no arbitrary Python execution.")])
    if not progress(100):raise Cancelled()
    return {**out,"fold_sha256":fingerprint(out)}

def browser_fold(csv_text,graph_text,symbol,settings,assume_open,study,fold,progress=lambda p:True,risk=None):
    import csv,io
    from hashlib import sha256
    from .browser_replay import replay,MAX_CSV,MAX_ROWS
    from .browser_cache import ReplayCache
    if assume_open is not True or len(csv_text.encode())>MAX_CSV:raise ValueError("explicit bounded CSV required")
    spec=Study.model_validate(study);base=compiled_source(graph_text)
    choices,windows,total=plan(base,spec,budget=120000)
    if type(fold) is not int or not 1<=fold<=len(windows):raise ValueError("invalid fold")
    reader=csv.reader(io.StringIO(csv_text,newline=""))
    header=["time","open","high","low","close","volume"]
    if next(reader,None)!=header:raise ValueError("invalid trade CSV header")
    rows=[];first=None
    for row in reader:
        if len(rows)>=MAX_ROWS or len(row)!=6 or not row[0].isascii() or not row[0].isdigit() or len(row[0])>10:
            raise ValueError("invalid bounded CSV")
        t=int(row[0])
        if first is None:first=t
        if t!=first+60*len(rows) or t%60:raise ValueError("noncontiguous CSV")
        rows.append(row)
    if first is None or spec.start<first or windows[-1]["test_end"]>first+60*len(rows):raise ValueError("study outside CSV")
    if bool(spec.leverage_values)!=(risk is not None):raise ValueError("explicit leveraged study configuration required")
    if risk is not None:
        from .study_risk import StudyRisk
        risk_source=StudyRisk(risk,require_marks=True)
    cache=ReplayCache();slices={}
    def runner(compiled,lo,hi,cost,leverage=None,label="baseline"):
        key=(lo,hi)
        if key not in slices:
            text=io.StringIO(newline="");writer=csv.writer(text,lineterminator="\n")
            writer.writerow(header);writer.writerows(rows[(lo-first)//60:(hi-first)//60]);slices.clear();slices[key]=text.getvalue()
        return replay(slices[key],compiled["source"],symbol,cost,True,cache=cache,risk=risk_source.window(lo,hi,leverage,label,spec.funding_stress_multiplier) if risk is not None else None)
    out=evaluate_fold(base,spec,choices,windows[fold-1],settings,runner,progress,risk=risk)
    return dict(study_sha256=fingerprint(dict(study=spec.model_dump(),data_sha256=sha256(csv_text.encode()).hexdigest(),
        graph_sha256=base["graph_sha256"],symbol=symbol,settings=settings,**({"risk_sha256":fingerprint(risk)} if risk is not None else {}))),total_candidate_minutes=total,**out)
