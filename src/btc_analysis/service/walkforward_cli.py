"""Native multi-year archive walk-forward; parallel folds with bounded CPU count."""
import argparse,json,tempfile
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from decimal import Decimal as D,localcontext
from .historical import LongHistoricalRequest
from .walkforward import Study,plan,evaluate_fold
from .longrun import run
from ..visual import Graph,compile_graph
from ..serialization import fingerprint,to_wire,canonical_bytes

KEYS=("initial_equity","maker_bps","taker_bps","tax_rate","slippage_bps","tick_size","lot_size","multiplier")

def execute(args):
    root,request,base,study,window=args
    spec=Study.model_validate(study);choices,_,_=plan(base,spec,budget=5_000_000)
    settings={k:request[k] for k in KEYS}
    def runner(c,lo,hi,cost):
        with tempfile.TemporaryDirectory() as d:
            r=run(root,{**request,**cost,"start":lo,"end":hi,"warmup_minutes":0},c["graph"],Path(d)/"archive")
        scenarios=[]
        for s in r["result"]["scenarios"]:
            m=dict(s["summary"])
            with localcontext() as ctx:
                ctx.prec=50;m["account_return_pct"]=to_wire(D(m["net_pnl"])/D(m["initial_equity"])*100)
                m["account_net"]=m["net_pnl"]
            scenarios.append(dict(path=s["path"],metrics=m,monthly=s["monthly"]))
        return dict(result_sha256=r["result_sha256"],scenarios=scenarios)
    return evaluate_fold(base,spec,choices,window,settings,runner)

def run_study(root,request,graph,study,workers=1):
    if type(workers) is not int or workers not in (1,2):raise ValueError("workers must be 1 or 2")
    r=LongHistoricalRequest.model_validate(request);spec=Study.model_validate(study)
    base=compile_graph(Graph.model_validate(graph));_,windows,total=plan(base,spec,budget=5_000_000)
    if r.warmup_minutes or spec.start<r.start or windows[-1]["test_end"]>r.end:raise ValueError("study outside declared archive interval; external warmup unsupported")
    jobs=[(str(root),r.model_dump(),base,spec.model_dump(),w) for w in windows]
    if workers==1:folds=[execute(x) for x in jobs]
    else:
        with ProcessPoolExecutor(max_workers=workers) as pool:folds=list(pool.map(execute,jobs))
    report=dict(schema_version=1,research_only=True,production_approved=False,request=r.model_dump(),study=spec.model_dump(),
        graph_sha256=base["graph_sha256"],graph=base["graph"],candidate_minutes=total,folds=folds,
        modeled_checks_passed=all(f["modeled_checks_passed"] for f in folds),
        limitations=["Independent folds, no compounded returns. Temporary detailed ledgers deleted after summary.",
            "Historical labels/contract specifications require independent attestation. 1x only."])
    return {**report,"study_sha256":fingerprint(report)}

def main():
    p=argparse.ArgumentParser();p.add_argument("--history",required=True);p.add_argument("--request",required=True)
    p.add_argument("--graph",required=True);p.add_argument("--study",required=True);p.add_argument("--output",required=True)
    p.add_argument("--workers",type=int,choices=[1,2],default=1);a=p.parse_args()
    result=run_study(a.history,json.loads(Path(a.request).read_text()),json.loads(Path(a.graph).read_text()),
        json.loads(Path(a.study).read_text()),a.workers)
    with Path(a.output).open("xb") as dest:dest.write(canonical_bytes(result)+b"\n")
    print(json.dumps(dict(study_sha256=result["study_sha256"],folds=len(result["folds"]),modeled_checks_passed=result["modeled_checks_passed"])))
if __name__=="__main__":main()
