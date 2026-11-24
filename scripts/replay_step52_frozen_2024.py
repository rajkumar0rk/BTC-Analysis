#!/usr/bin/env python3
"""Replay Step52's original frozen rule stack on genuine 2024 candles.
Only historical sample assertions and dimension bindings are changed in an
isolated temporary source copy. No optimization. Earlier learners cold start.
Cost stress reprices identical original-model selected orders, no feedback.
"""
import ast,importlib,json,os,re,shutil,sys,tempfile
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path.cwd()
SOURCE=ROOT/"scripts"
OUT=ROOT/"analysis/btc_step52_frozen_2024"
OUT.mkdir(parents=True,exist_ok=True)
DATA=ROOT/"prior2024"
def load(pattern):
    files=sorted(DATA.rglob(pattern))
    assert files,pattern
    d=pd.concat([pd.read_csv(f) for f in files],ignore_index=True)
    d["time"]=pd.to_datetime(d.time.astype("int64"),unit="s",utc=True)
    d=d.set_index("time").sort_index()
    assert not d.index.has_duplicates
    return d
m=load("2024_data/*.csv.gz")
assert m[["open","high","low","close","volume"]].notna().all().all()
assert ((m.low>0)&(m.high>=m[["open","low","close"]].max(axis=1))&(m.low<=m[["open","high","close"]].min(axis=1))&(m.volume>=0)).all()
expected=pd.date_range("2024-01-01","2024-12-31",freq="B",tz="Asia/Kolkata")
days=[];missing=[]
for day in expected:
    # Original prepare constructs all 24 hourly choices. Retain complete
    # day and preceding 4h to keep indexing and all feature lookbacks valid.
    a=(day-pd.Timedelta(hours=4)).tz_convert("UTC")
    b=(day+pd.Timedelta(minutes=1439)).tz_convert("UTC")
    x,y=m.index.get_indexer([a,b])
    if x<0 or y-x!=1679 or not np.array_equal(m.index[x:y+1],pd.date_range(a,b,freq="min")):
        missing.append(str(day.date()))
    else:days.append(day)
days=pd.DatetimeIndex(days)
assert len(days)>200
months=np.unique(days.strftime("%Y-%m"))
print("STEP52_2024_COVERAGE",json.dumps(dict(candles=len(m),days=len(days),expected=len(expected),missing=missing,month_counts=pd.Series(days.strftime("%Y-%m")).value_counts().sort_index().to_dict())),flush=True)

def adapt(path,text):
    name=path.name
    # Only sample-size checks, old performance parity, and report labels.
    # All numerical trading thresholds and policy selection are untouched.
    if name=="research_btc_every_weekday_reset_step1.py":
        return text.replace("starts.shape!=(477,24)","starts.shape!=(len(DAYS),24)")
    if name=="research_btc_daily_structure_step10.py":
        text=text.replace("N=477","N=len(base.DAYS)").replace("TRAIN=260","TRAIN=base.NTRAIN")
    if name=="research_btc_daily_online_direction_step6.py":
        text=text.replace("    assert np.sum(isfallback)==217 and np.sum(~isfallback)==260","    assert len(isfallback)==len(base.DAYS)")
    if name=="research_btc_daily_causal_neighbors_step8.py":
        text=text.replace('    if int(np.sum((e_idx==1)&(~mask)))!=20:\n        raise AssertionError("Step6 event direction count changed")','    assert len(e_idx)==N')
        text=text.replace('    if int(np.sum(mask))!=217 or int(np.sum(~mask))!=260:\n        raise AssertionError("Step6 source counts changed")','    assert len(mask)==N')
    if name=="research_btc_daily_structure_step10.py":
        text=text.replace('    if old["profitable_days"]!=277 or abs(old["net_total_pct"]-21.423313)>.00011:\n        raise AssertionError("Step8 2025-selected exact baseline changed")','    assert old["trades"]==N')
    if name=="research_btc_daily_monthly_exit_step13.py":
        text=text.replace(" or int(np.sum(mask))!=217","")
    if name=="research_btc_january2025_loss_recovery_step29.py":
        text=text.replace('    if int(changed.sum())!=4:\n        raise AssertionError("Frozen Ridge direction parity drift")','    assert len(changed)==N')
    if name=="research_btc_one_percent_monthly_floor_step36.py":
        text=text.replace("january2026=float(monthly[12])","january2026=float('nan')")
        text=text.replace("len(monthly)!=22","len(monthly)!=len(base.MONTH_KEYS)")
    if name=="audit_step52_frozen_strategy.py":
        text=text.replace("assert n==477","assert n==len(s.base.DAYS)").replace("assert len(months)==22","assert len(months)==len(s.base.MONTH_KEYS)").replace("range(22)","range(len(months))")
        # Keep original (not strict) feature definitions; old result constants
        # are meaningful only on 2025-26, not as 2024 acceptance criteria.
        tree=ast.parse(text)
        class OldSampleParity(ast.NodeTransformer):
            def visit_If(self,node):
                if ast.unparse(node.test)=="not strict" and all(isinstance(x,(ast.Assert,ast.If)) for x in node.body):
                    return ast.copy_location(ast.Pass(),node)
                return self.generic_visit(node)
        tree=OldSampleParity().visit(tree)
        text=ast.unparse(ast.fix_missing_locations(tree))
        text=text.replace("audit_fills(m, cfg, features, mask, policies, labels, p52, s, OUT, strict)","audit_fills(m, cfg, features, mask, policies, labels, p52, s, OUT, strict)")
        return text
    if name=="step52_validation_engine.py":
        return text.replace("len(df)==477 and df.day_ist.nunique()==477","len(df)==len(s.base.DAYS) and df.day_ist.nunique()==len(s.base.DAYS)")
    # Numeric 477 denotes sample size in this original module family, not
    # a trading threshold. Change executable literals only; retain strings.
    tree=ast.parse(text)
    class Calendar(ast.NodeTransformer):
        def visit_Module(self,node):
            body=[]
            for x in node.body:
                if isinstance(x,ast.Assert):
                    expr=ast.unparse(x.test)
                    if re.search(r"\b(477|260|217)\b",expr):
                        # Remove only old-sample clauses, preserve grid checks.
                        clauses=x.test.values if isinstance(x.test,ast.BoolOp) and isinstance(x.test.op,ast.And) else [x.test]
                        keep=[a for a in clauses if not re.search(r"\b(477|260|217)\b|len\(UNIQUE_MONTHS\) == 22",ast.unparse(a))]
                        if not keep:continue
                        x.test=keep[0] if len(keep)==1 else ast.BoolOp(op=ast.And(),values=keep)
                body.append(x)
            node.body=body
            return self.generic_visit(node)
        def visit_Constant(self,node):
            if type(node.value) is int and node.value==477:
                return ast.copy_location(ast.parse("len(base.DAYS)",mode="eval").body,node)
            return node
    return ast.unparse(ast.fix_missing_locations(Calendar().visit(tree)))

with tempfile.TemporaryDirectory(prefix="step52_2024_") as td:
    td=Path(td)
    for p in SOURCE.glob("*.py"):
        # Adapt only the original Step52 dependency family; keep other
        # scripts byte-identical and do not modify committed sources.
        text=p.read_text()
        if p.name.startswith("research_btc_") and re.search(r"step\d+\.py$",p.name) or p.name in ("audit_step52_frozen_strategy.py","step52_validation_engine.py","audit_btc_daily_risk_crosscheck_step20.py"):
            text=adapt(p,text)
        (td/p.name).write_text(text)
    sys.path.insert(0,str(td))
    import research_btc_every_weekday_reset_step1 as base
    base.DAYS=days
    base.NTRAIN=int(np.count_nonzero(days.month<=6))
    base.IST_DAYS=np.asarray(days.strftime("%Y-%m-%d"))
    base.MONTH_LABELS=np.asarray(days.strftime("%Y-%m"))
    base.MONTH_KEYS,base.MONTH_IDX=np.unique(base.MONTH_LABELS,return_inverse=True)
    base.MONTHS=base.MONTH_KEYS.tolist()
    base.load=lambda:m
    import audit_step52_frozen_strategy as audit
    audit.OUT=OUT
    os.environ["STRICT_PREENTRY"]="0"
    audit.main()
    df=pd.read_csv(OUT/"original_independent_trade_ledger.csv")
    assert len(df)==len(days)
    assert (df.day_ist.to_numpy()==base.IST_DAYS).all()
    # Reprice the frozen order ledger using the same adverse-only historical
    # funding estimate as prior research. No changes to decision path.
    mark=load("2024_aux/mark_*.csv.gz")
    fund=load("2024_aux/funding_*.csv.gz")
    rate=fund.close.shift(1)
    entry=pd.to_datetime(df.entry_utc,utc=True)
    exit=pd.to_datetime(df.exit_utc,utc=True)
    scenario=[]
    for mode,slip in [("original_offer30",5),("historical15",5),("standard",5),("historical15",20),("standard",20)]:
        vals=[];mark_missing=0;fund_missing=0;peak=eq=1.;md=0.
        for i,row in df.iterrows():
            sd=row.direction;en=row.entry_mid+sd*slip;ex=row.exit_mid-sd*slip
            waiver=row.hold_min<=30 if mode=="original_offer30" else row.hold_min<15 if mode=="historical15" else False
            fee=base.COST*(en+ex*(not waiver))/en
            f=0.
            mk=mark.reindex(pd.date_range(entry[i],exit[i],freq="min"))
            markok=mk[["open","high","low"]].notna().all().all()
            if not markok:mark_missing+=1
            if mode!="original_offer30":
                for x in pd.date_range(entry[i],exit[i],freq="min")[:-1]:
                    rr=rate.asof(x)
                    if not markok or not np.isfinite(rr):fund_missing+=1;f=np.nan;break
                    f+=abs(rr/100*mk.loc[x,"open"]/en)/480
            r=sd*(ex-en)/en-fee-f
            vals.append(r)
            if markok and np.isfinite(r):
                fav=sd*((mk.high.max() if sd>0 else mk.low.min())-en)/en
                adv=sd*((mk.low.min() if sd>0 else mk.high.max())-en)/en
                peak=max(peak,eq*(1+fav-base.COST))
                md=max(md,1-eq*(1+adv-2*base.COST-f)/peak)
            if np.isfinite(r):
                eq*=1+r;peak=max(peak,eq);md=max(md,1-eq/peak)
        p=np.array(vals)
        if not np.isfinite(p).all():
            scenario.append(dict(mode=mode,slip=slip,status="FUNDING_MISSING",fund_missing=fund_missing));continue
        eqs=np.cumprod(1+p);peaks=np.maximum.accumulate(np.r_[1.,eqs])[1:]
        monthly=pd.Series(p,index=base.MONTH_LABELS).groupby(level=0).apply(lambda z:100*(np.prod(1+z)-1))
        scenario.append(dict(mode=mode,slip=slip,net_pct=100*(eqs[-1]-1),closed_dd_pct=100*np.max(1-eqs/peaks),mark_dd_pct=100*md if not mark_missing else None,mark_missing=mark_missing,wins=int((p>0).sum()),losses=int((p<0).sum()),positive_months=int((monthly>0).sum()),months_ge1=int((monthly>=1).sum()),monthly=monthly.to_dict()))
    assert abs(scenario[0]["net_pct"]-100*(np.prod(1+df.net_offer)-1))<1e-7
    result=dict(trades=len(df),expected=len(expected),missing=missing,candles=len(m),independent_replay=True,frozen_step=52,no_optimization=True,cold_start=True,scenarios=scenario)
    (OUT/"2024_summary.json").write_text(json.dumps(result,indent=2))
    print("STEP52_2024_FINAL",json.dumps(result),flush=True)
