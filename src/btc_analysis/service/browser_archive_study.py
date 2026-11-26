"""Repository-backed causal walk-forward studies in trusted browser Python.

Each fold runs a bounded set of independent continuous replays. Training selects
only on the earlier window. The supplied manifest is pinned in the study hash.
"""
from .browser_long_replay import plan_archive,plan_archive_range,replay_archive,dt
from .walkforward import Study,compiled_source,plan,evaluate_fold
from ..serialization import fingerprint
from .fixture import Cancelled

BUDGET=5_000_000
def prepare_study(manifest_text,symbol,from_date,to_date,graph_text,study,fold):
    spec=Study.model_validate(study)
    base=compiled_source(graph_text)
    choices,windows,total=plan(base,spec,budget=BUDGET)
    if type(fold) is not int or not 1<=fold<=len(windows):raise ValueError("invalid fold")
    outer=plan_archive(manifest_text,symbol,from_date,to_date)
    if spec.start<outer["start"] or windows[-1]["test_end"]>outer["end"]:raise ValueError("study outside selected repository dates")
    window=windows[fold-1]
    selected=plan_archive_range(manifest_text,symbol,window["train_start"],window["test_end"])
    return spec,base,choices,window,total,selected

def study_download_plan(manifest_text,symbol,from_date,to_date,graph_text,study,fold):
    return prepare_study(manifest_text,symbol,from_date,to_date,graph_text,study,fold)[-1]

def repository_fold(manifest_text,symbol,from_date,to_date,graph_text,study,fold,settings,assume_open,folder,progress=lambda p:True):
    if assume_open is not True:raise ValueError("acknowledge unverified timestamp convention")
    spec,base,choices,window,total,selected=prepare_study(manifest_text,symbol,from_date,to_date,graph_text,study,fold)
    # Only the training window is provided to the training replay. The pinned
    # full snapshot hash identifies provenance, not a claim of unseen holdout.
    completed=0;n=len(choices)+5
    def runner(c,lo,hi,cost):
        nonlocal completed
        def report(p):
            if not progress(min(99,(completed*100+p)//n)):raise Cancelled()
            return True
        r=replay_archive(manifest_text,from_date,to_date,c["source"],symbol,cost,True,folder,progress=report,window=(lo,hi))
        completed+=1
        return r
    out=evaluate_fold(base,spec,choices,window,settings,runner,progress)
    out["limitations"] += ["Repository compressed archive; maximum 5 million candidate-minutes across all folds, two paths per replay.","Study uses explicit costs, 1x only. No actual exchange funding or liquidation."]
    # Recompute fold digest because the limitations are part of its evidence.
    out["fold_sha256"]=fingerprint({k:v for k,v in out.items() if k!="fold_sha256"})
    return dict(study_sha256=fingerprint(dict(study=spec.model_dump(),data_sha256=selected["manifest_sha256"],graph_sha256=base["graph_sha256"],symbol=symbol,settings=settings,from_date=from_date,to_date=to_date)),total_candidate_minutes=total,**out)
