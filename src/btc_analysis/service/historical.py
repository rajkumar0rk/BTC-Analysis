"""Bounded historical visual replay. Only validated graph data enters trusted runtime."""
from datetime import datetime, timezone
from decimal import Decimal as D
from hashlib import sha256
from pathlib import Path
from typing import Literal, Annotated
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator
from ..visual import Graph, Indicator, Constant, CustomOperand, PositionOperand, compile_graph, recover_graph, DecimalText
from ..visual_runtime import VisualStrategyBase, compare, constant, price, indicator
from ..contracts import (Instrument, AssetClass, Timeframe, DatasetRef, DataKind,
    StrategyRef, BacktestConfig, CostModel, MarginMode, IntrabarPolicy)
from ..indicators import IndicatorSpec
from ..serialization import to_wire, fingerprint
from ..backtest import run_backtest
from .fixture import Cancelled

MAX_MINUTES=1440
MAX_LONG_MINUTES=3*366*1440
MAX_WARMUP=1440
Hash=Annotated[str,StringConstraints(pattern=r"^[0-9a-f]{64}$")]
Id=Annotated[str,StringConstraints(pattern=r"^[0-9a-f]{32}$")]

class HistoricalRequest(BaseModel):
    model_config=ConfigDict(extra="forbid",strict=True)
    kind:Literal["historical_visual"]
    strategy_id:Id
    version:Annotated[int,Field(ge=1,le=100)]
    symbol:Literal["BTCUSD","ETHUSD"]
    manifest_sha256:Hash
    start:Annotated[int,Field(ge=0,le=4102444800)]
    end:Annotated[int,Field(ge=0,le=4102444800)]
    warmup_minutes:Annotated[int,Field(ge=0,le=MAX_WARMUP)]=0
    initial_equity:DecimalText="100"
    maker_bps:DecimalText="2"
    taker_bps:DecimalText="5"
    tax_rate:DecimalText="0.18"
    slippage_bps:DecimalText="0"
    tick_size:DecimalText="0.1"
    lot_size:DecimalText="0.001"
    multiplier:DecimalText="1"
    assume_open:bool=False
    acknowledge_reference:Literal[True]
    @model_validator(mode="after")
    def check(self):
        if self.start%60 or self.end%60 or not 0<self.end-self.start<=MAX_MINUTES*60:
            raise ValueError("range must be minute aligned, positive and at most 1440 minutes")
        for k,lo,hi in (("initial_equity","1","1000000"),("maker_bps","0","100"),("taker_bps","0","100"),
                        ("tax_rate","0","1"),("slippage_bps","0","100"),("tick_size","0.00000001","1000"),
                        ("lot_size","0.00000001","1000"),("multiplier","0.00000001","1000")):
            if not D(lo)<=D(getattr(self,k))<=D(hi):raise ValueError("invalid "+k)
        return self

def frames(g):
    out={g.signal_timeframe,g.execution_timeframe,*(d.timeframe for d in (g.custom_formulas or []))}
    if g.advanced is not None and g.advanced.trailing_atr is not None:out.add(g.advanced.trailing_atr.timeframe)
    for r in g.rules():
        for group in r.groups:
            for c in group.conditions:
                for o in (c.left,c.right):
                    if not isinstance(o,(Constant,PositionOperand)):out.add(o.timeframe)
    return tuple(sorted(out))

def validate_clock(g,r):
    if g.execution_timeframe!=60:raise ValueError("historical runner requires 1m execution")
    for tf in frames(g):
        if any(t%tf for t in (r.start,r.end,r.start-r.warmup_minutes*60)):
            raise ValueError("start, end and warmup start must align with all visual timeframes")

class GraphStrategy(VisualStrategyBase):
    """Same SDK runtime as generated Python; no exec/eval or dynamic imports."""
    def __init__(self,g):
        self.custom_config=[d.model_dump() for d in g.custom_formulas] if g.custom_formulas else None
        super().__init__()
        self.g=g
        self.signal_seconds=g.signal_timeframe
        self.execution_seconds=g.execution_timeframe
        self.exposure=D(g.exposure_pct)/100
        self.stop_loss=D(g.stop_loss_pct)/100
        self.take_profit=D(g.take_profit_pct)/100
        self.advanced_controls=g.advanced.model_dump() if g.advanced is not None else None
        self.sequence_config=g.sequence_config()
        self.machine_config=g.machine_config()
        self.exit_machine_config=g.exit_machine_config()
    def indicators(self):
        specs=set()
        if self.g.advanced is not None and self.g.advanced.trailing_atr is not None:
            a=self.g.advanced.trailing_atr;specs.add(IndicatorSpec.create("atr.value",Timeframe(a.timeframe),{"period":a.period}))
        for r in self.g.rules():
            for group in r.groups:
                for c in group.conditions:
                    for o in (c.left,c.right):
                        if isinstance(o,Indicator):
                            specs.add(IndicatorSpec.create(o.name,Timeframe(o.timeframe),o.parameters))
        return tuple(sorted(specs,key=lambda x:(x.name,x.timeframe.seconds,repr(dict(x.parameters)))))
    def extra_timeframes(self):return tuple(Timeframe(t) for t in frames(self.g))
    def operand(self,ctx,o):
        if isinstance(o,Constant):return constant(o.value)
        if isinstance(o,Indicator):return indicator(ctx,o.name,o.timeframe,o.parameters)
        if isinstance(o,CustomOperand):return self.custom_pair(o.name)
        if isinstance(o,PositionOperand):return self.position_pair(ctx,o.field)
        return price(ctx,o.timeframe,o.field)
    def rule(self,ctx,r):
        if not r.enabled:return False
        groups=[]
        for g in r.groups:
            values=(compare(c.op,self.operand(ctx,c.left),self.operand(ctx,c.right)) for c in g.conditions)
            groups.append(all(values) if g.mode=="all" else any(values))
        return all(groups) if r.mode=="all" else any(groups)
    def exit_machine_transition(self,ctx,direction,index):
        m=self.g.long_exit_machine if direction==1 else self.g.short_exit_machine
        return self.rule(ctx,m.transitions[index].rule) if m is not None else False
    def exit_machine_reset(self,ctx,direction):
        m=self.g.long_exit_machine if direction==1 else self.g.short_exit_machine
        return self.rule(ctx,m.reset) if m is not None and m.reset is not None else False
    def machine_transition(self,ctx,direction,index):
        m=self.g.long_machine if direction==1 else self.g.short_machine
        return self.rule(ctx,m.transitions[index].rule) if m is not None else False
    def machine_reset(self,ctx,direction):
        m=self.g.long_machine if direction==1 else self.g.short_machine
        return self.rule(ctx,m.reset) if m is not None and m.reset is not None else False
    def sequence_stage(self,ctx,direction,index):
        seq=self.g.long_sequence if direction==1 else self.g.short_sequence
        return self.rule(ctx,seq.stages[index]) if seq is not None else False
    def sequence_reset(self,ctx,direction):
        seq=self.g.long_sequence if direction==1 else self.g.short_sequence
        return self.rule(ctx,seq.reset) if seq is not None and seq.reset is not None else False
    def long_entry(self,ctx):return self.rule(ctx,self.g.long_entry)
    def short_entry(self,ctx):return self.rule(ctx,self.g.short_entry)
    def long_exit(self,ctx):return self.rule(ctx,self.g.long_exit)
    def short_exit(self,ctx):return self.rule(ctx,self.g.short_exit)

def snapshots(root):
    from ..data import HistoryStore
    result=[]
    if root is None:return result
    for symbol in ("BTCUSD","ETHUSD"):
        try:
            with HistoryStore(root,symbol) as h:
                m=h.manifest
                result.append({"symbol":symbol,"manifest_sha256":h.key,"start":m["start"],"end":m["end"],
                    "timestamp_label_verified":m["label_verified"] is True and m["timestamp_label"]=="open"})
        except (OSError,ValueError,KeyError):continue
    return result

def prepare(root,request,revision):
    from ..data import HistoryStore
    if root is None:raise ValueError("historical store is not configured")
    c=recover_graph(revision["source"])
    g=Graph.model_validate(c["graph"]);validate_clock(g,request)
    with HistoryStore(root,request.symbol,request.manifest_sha256) as h:
        h._label(request.assume_open)
        if not h.coverage(request.start-request.warmup_minutes*60,request.end).complete:
            raise ValueError("requested range or warmup contains missing candles")
    return {**request.model_dump(),"graph":c["graph"],"graph_sha256":c["graph_sha256"],
            "code_sha256":revision["code_sha256"]}

class LongHistoricalRequest(HistoricalRequest):
    @model_validator(mode="after")
    def check(self):
        if self.start%60 or self.end%60 or not 0<self.end-self.start<=MAX_LONG_MINUTES*60:
            raise ValueError("long range must be minute aligned and at most 1098 days")
        # Reuse the base financial validation with a short valid interval.
        HistoricalRequest.model_validate({**self.model_dump(),"end":self.start+60})
        return self

def execute_historical(payload,root,progress,*,archive_factory=None):
    from ..data import HistoryStore
    from ..data.store import dt, SOURCE
    if root is None:raise ValueError("historical store not configured")
    raw={k:v for k,v in payload.items() if k not in ("graph","graph_sha256","code_sha256")}
    r=(HistoricalRequest if archive_factory is None else LongHistoricalRequest).model_validate(raw);g=Graph.model_validate(payload["graph"])
    compiled=compile_graph(g)
    if compiled["graph_sha256"]!=payload["graph_sha256"] or sha256(compiled["source"].encode()).hexdigest()!=payload["code_sha256"]:
        raise ValueError("pinned visual source mismatch")
    validate_clock(g,r)
    i=Instrument("delta_india",r.symbol,AssetClass.CRYPTO_PERPETUAL,"USD","USD",
                 D(r.tick_size),D(r.lot_size),D(r.multiplier))
    lo=r.start-r.warmup_minutes*60
    with HistoryStore(root,r.symbol,r.manifest_sha256) as h:
        h._label(r.assume_open)
        verified=h.manifest["label_verified"] is True and h.manifest["timestamp_label"]=="open"
        cov=h.coverage(lo,r.end)
        if not cov.complete:raise ValueError("historical coverage incomplete")
        # coverage_verified refers to gap/count integrity, NOT label attestation.
        # Partition hashes are verified by iter_candles before reading; failure aborts the run.
        ds=DatasetRef("visual-history:"+h.key[:16],i,DataKind.OHLCV,Timeframe(60),
                      dt(lo),dt(r.end),h.key,SOURCE,0,True)
        cfg=BacktestConfig(StrategyRef(r.strategy_id,str(r.version),payload["code_sha256"],compiled["graph_sha256"]),
            i,(ds,),dt(r.start),dt(r.end),Timeframe(g.signal_timeframe),Timeframe(60),D(r.initial_equity),"USD",D(1),
            MarginMode.ISOLATED,CostModel(D(r.maker_bps),D(r.taker_bps),D(r.tax_rate),D(r.slippage_bps),
            False,False,False,"user-assumed-cost-v1"),IntrabarPolicy.BOTH_PATHS,"Asia/Kolkata","crypto-24x7")
        count=0;total=2*((r.end-lo)//60)
        def stream(a,b):
            nonlocal count
            for bar in h.iter_candles(i,a,b,assume_open=r.assume_open):
                count+=1
                if count%(32 if archive_factory is None else 4096)==0 and not progress(min(99,count*99//total)):raise Cancelled()
                yield bar
        if not progress(0):raise Cancelled()
        kwargs={}
        if r.warmup_minutes:kwargs={"warmup_start_utc":dt(lo),"warmup_factory":lambda:stream(lo,r.start)}
        result=run_backtest(cfg,lambda:GraphStrategy(g),lambda:stream(r.start,r.end),
                            linear_contract=True,dataset_manifest_sha256=h.key,archive_factory=archive_factory,**kwargs)
        if not progress(99):raise Cancelled()
        return {"kind":"historical_visual","synthetic":False,"research_only":True,
                "timestamp_label_verified":verified,"dataset_manifest_sha256":h.key,
                "assumptions":["User-supplied linear contract tick, lot and multiplier; not attested venue specifications.",
                               "1x only; no funding, historical spread or liquidation.",
                               "Verified open timestamp label." if verified else "Raw timestamps assumed to be opens; unverified convention.",
                               ("Fixed-point stop/target active from entry minute." if g.advanced is not None and g.advanced.exit_mode=="points" else "Entry candle not protected by generated percentage stop/target.")],
                "result_sha256":result.result_sha256,"result":to_wire(result)}
