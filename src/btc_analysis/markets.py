"""Operator-imported market bundles. Explicit provenance, no invented venue specs."""
from __future__ import annotations
import csv
import json
import os
import re
import tempfile
from pathlib import Path
from datetime import datetime,timezone
from decimal import Decimal as D
from hashlib import sha256
from typing import Literal,Annotated
from pydantic import BaseModel,ConfigDict,Field,StringConstraints,model_validator
from .contracts import Instrument,AssetClass,Candle,Timeframe,DatasetRef,DataKind,StrategyRef,BacktestConfig,CostModel,MarginMode,IntrabarPolicy
from .data.calendar import SessionCalendar,ContinuousCalendar
from .serialization import fingerprint,to_wire
from .visual import Graph,compile_graph,DecimalText
from .service.historical import GraphStrategy,frames
from .backtest import run_backtest

MAX_ROWS=100000
MAX_BYTES=32*1024*1024
MAX_RUN=1440
Key=Annotated[str,StringConstraints(pattern=r"^[A-Za-z0-9_.:-]{1,80}$")]
Evidence=Annotated[str,StringConstraints(min_length=1,max_length=256)]
Hash=Annotated[str,StringConstraints(pattern=r"^[0-9a-f]{64}$")]
Epoch=Annotated[int,Field(ge=0,le=4102444800)]

class Strict(BaseModel):
    model_config=ConfigDict(extra="forbid",strict=True)

def dt(t):return datetime.fromtimestamp(t,timezone.utc)

class Spec(Strict):
    venue:Key
    symbol:Key
    underlying:Key
    market:Literal["crypto","stock","index","commodity","currency"]
    asset_class:Literal["crypto_perpetual","future","option","spot"]
    currency:Key
    tick_size:DecimalText
    lot_size:DecimalText
    multiplier:DecimalText
    expiry:Epoch|None=None
    strike:DecimalText|None=None
    option_right:Literal["call","put"]|None=None
    effective_start:Epoch
    effective_end:Epoch
    source:Evidence
    timestamp_evidence:Evidence
    specification_evidence:Evidence
    calendar_evidence:Evidence
    calendar_start:Epoch
    calendar_end:Epoch
    sessions:list[tuple[int,int]]=Field(max_length=1000)
    continuous:bool=False
    linear:bool=False
    @model_validator(mode="after")
    def check(self):
        self.instrument()
        self.calendar()
        if not self.effective_start<self.effective_end:raise ValueError("invalid specification interval")
        if self.expiry is not None and self.effective_end>self.expiry:raise ValueError("spec extends beyond expiry")
        if self.continuous and self.market!="crypto":raise ValueError("noncrypto requires explicit sessions")
        if self.continuous and self.sessions:raise ValueError("continuous calendar cannot have sessions")
        return self
    def instrument(self):
        return Instrument(self.venue,self.symbol,AssetClass(self.asset_class),self.currency,self.currency,
            D(self.tick_size),D(self.lot_size),D(self.multiplier),dt(self.expiry) if self.expiry is not None else None,
            D(self.strike) if self.strike is not None else None,self.option_right)
    def calendar(self):
        if self.continuous:
            SessionCalendar("coverage-check",self.calendar_start,self.calendar_end,())
            return ContinuousCalendar()
        return SessionCalendar("reviewed-session:"+self.venue,self.calendar_start,self.calendar_end,tuple(self.sessions))
    def eligible(self):
        return self.linear and ((self.asset_class=="future" and not self.continuous) or
                                (self.asset_class=="crypto_perpetual" and self.continuous))

def atomic(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent,delete=False) as w:
        w.write(data);name=w.name
    try:os.replace(name,path)
    finally:
        if os.path.exists(name):os.unlink(name)

def read_csv(path,spec,start,end):
    if path.stat().st_size>MAX_BYTES:raise ValueError("CSV size exceeds bound")
    if not spec.calendar_start<=start<end<=spec.calendar_end or not spec.effective_start<=start<end<=spec.effective_end:
        raise ValueError("outside attested range")
    expected=iter(t for a,b in spec.calendar().intervals(start,end,60) for t in range(a,b,60))
    rows=[]
    with path.open(encoding="utf-8",newline="") as r:
        reader=csv.DictReader(r)
        if reader.fieldnames!=["time","open","high","low","close","volume"]:raise ValueError("exact CSV header required")
        for row in reader:
            if len(rows)>=MAX_ROWS:raise ValueError("row limit")
            if None in row or any(v is None or len(v)>100 for v in row.values()):raise ValueError("invalid row")
            t=int(row.pop("time"))
            if t!=next(expected,None):raise ValueError("missing, duplicate or out-of-session candle")
            bar=Candle(spec.instrument(),Timeframe(60),dt(t),dt(t+60),**{k:D(v) for k,v in row.items()})
            rows.append({"time":t,**{k:to_wire(getattr(bar,k)) for k in ("open","high","low","close","volume")}})
    if not rows or next(expected,None) is not None:raise ValueError("missing candles")
    return rows

def import_bundle(root,csv_path,spec,start,end):
    csv_path=Path(csv_path)
    rows=read_csv(csv_path,spec,start,end)
    obj={"schema":1,"spec":spec.model_dump(mode="json"),"start":start,"end":end,
         "rows":rows,"source_sha256":sha256(csv_path.read_bytes()).hexdigest()}
    key=fingerprint(obj)
    atomic(Path(root)/"objects"/(key+".json"),json.dumps(obj,separators=(",",":"),sort_keys=True).encode())
    return key

def load_bundle(root,key):
    if not isinstance(key,str) or not re.fullmatch(r"[a-f0-9]{64}",key):raise ValueError("invalid bundle digest")
    path=Path(root)/"objects"/(key+".json")
    if path.stat().st_size>MAX_BYTES*3:raise ValueError("bundle size exceeds bound")
    obj=json.loads(path.read_text())
    if fingerprint(obj)!=key or obj["schema"]!=1:raise ValueError("bundle checksum/schema mismatch")
    return obj,Spec.model_validate_json(json.dumps(obj["spec"]))

def catalog(root):
    if root is None:return []
    out=[]
    for p in sorted((Path(root)/"objects").glob("*.json"))[:100]:
        try:
            obj,spec=load_bundle(root,p.stem)
            out.append({"bundle_sha256":p.stem,"venue":spec.venue,"symbol":spec.symbol,"underlying":spec.underlying,
                        "market":spec.market,"asset_class":spec.asset_class,"currency":spec.currency,
                        "start":obj["start"],"end":obj["end"],"rows":len(obj["rows"]),"expiry":spec.expiry,
                        "reference_eligible":spec.eligible(),"source":spec.source,
                        "attestation":"operator-supplied, not independently verified",
                        "studio_execution":False})
        except (ValueError,OSError,KeyError):continue
    return out

def rollover_plan(root,keys,roll_times):
    """Explicit research schedule only; no stitched prices or synthetic fills."""
    if not 2<=len(keys)<=12 or len(roll_times)!=len(keys)-1 or len(set(keys))!=len(keys):
        raise ValueError("invalid rollover chain")
    loaded=[load_bundle(root,key) for key in keys]
    first=loaded[0][1]
    identity=lambda s:(s.venue,s.underlying,s.market,s.currency)
    for (a,old),(b,new),t in zip(loaded,loaded[1:],roll_times):
        if old.asset_class!="future" or new.asset_class!="future" or identity(old)!=identity(first) or identity(new)!=identity(first) or old.expiry>=new.expiry:
            raise ValueError("incompatible dated contracts")
        if type(t) is not int or t%60 or not (a["start"]<=t<a["end"] and b["start"]<=t<b["end"] and t<old.expiry):
            raise ValueError("roll outside overlapping pre-expiry data")
        if not any(r["time"]==t for r in a["rows"]) or not any(r["time"]==t for r in b["rows"]):
            raise ValueError("roll requires actual candles in both contracts")
    if any(a>=b for a,b in zip(roll_times,roll_times[1:])):raise ValueError("roll schedule must increase")
    return {"contracts":keys,"roll_times":roll_times,"execution_supported":False,
            "note":"Explicit contract transition plan; no continuous-price stitching or settlement simulation."}

def run_reference(root,key,graph,start,end,initial_equity="100000",maker_bps="0",taker_bps="5",tax_rate="0",slippage_bps="0"):
    obj,spec=load_bundle(root,key)
    if not spec.eligible():raise ValueError("unsupported asset/linear specification")
    if not obj["start"]<=start<end<=obj["end"] or (end-start)//60>MAX_RUN:
        raise ValueError("reference run must be inside bundle and <=1440 minutes")
    if spec.expiry is not None and end>=spec.expiry:raise ValueError("expiry settlement unsupported")
    if spec.calendar().intervals(start,end,60)!=((start,end),):raise ValueError("reference run must stay inside one continuous session")
    if graph.execution_timeframe!=60 or any(t%tf for t in (start,end) for tf in frames(graph)):
        raise ValueError("range must align to all strategy frames")
    compiled=compile_graph(graph);i=spec.instrument()
    rows=[r for r in obj["rows"] if start<=r["time"]<end]
    candles=tuple(Candle(i,Timeframe(60),dt(r["time"]),dt(r["time"]+60),**{k:D(r[k]) for k in ("open","high","low","close","volume")}) for r in rows)
    ds=DatasetRef("market:"+key[:16],i,DataKind.OHLCV,Timeframe(60),dt(start),dt(end),key,spec.source,0,True)
    cfg=BacktestConfig(StrategyRef("imported-visual","1",sha256(compiled["source"].encode()).hexdigest(),compiled["graph_sha256"]),
        i,(ds,),dt(start),dt(end),Timeframe(graph.signal_timeframe),Timeframe(60),D(initial_equity),spec.currency,D(1),
        MarginMode.ISOLATED,CostModel(D(maker_bps),D(taker_bps),D(tax_rate),D(slippage_bps),False,False,False,"operator-reference"),
        IntrabarPolicy.BOTH_PATHS,"UTC",spec.calendar().calendar_id)
    result=run_backtest(cfg,lambda:GraphStrategy(graph),lambda:iter(candles),linear_contract=True,
        dataset_manifest_sha256=key,session_reference=spec.asset_class=="future")
    return {"research_only":True,"bundle_sha256":key,"result_sha256":result.result_sha256,
            "currency":spec.currency,"attestation":"operator-supplied, not independently verified","result":to_wire(result)}

def main():
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument("--root",required=True)
    sub=parser.add_subparsers(dest="action",required=True)
    imp=sub.add_parser("import");imp.add_argument("--spec",required=True);imp.add_argument("--csv",required=True);imp.add_argument("--start",type=int,required=True);imp.add_argument("--end",type=int,required=True)
    sub.add_parser("catalog")
    run=sub.add_parser("run");run.add_argument("--bundle",required=True);run.add_argument("--graph",required=True);run.add_argument("--start",type=int,required=True);run.add_argument("--end",type=int,required=True)
    run.add_argument("--capital",default="100000");run.add_argument("--maker-bps",default="0");run.add_argument("--taker-bps",default="5");run.add_argument("--tax",default="0");run.add_argument("--slippage-bps",default="0")
    args=parser.parse_args()
    if args.action=="import":
        result={"bundle_sha256":import_bundle(args.root,args.csv,Spec.model_validate_json(Path(args.spec).read_text()),args.start,args.end)}
    elif args.action=="catalog":result=catalog(args.root)
    else:result=run_reference(args.root,args.bundle,Graph.model_validate_json(Path(args.graph).read_text()),args.start,args.end,args.capital,args.maker_bps,args.taker_bps,args.tax,args.slippage_bps)
    print(json.dumps(result,indent=2))

if __name__=="__main__":main()
