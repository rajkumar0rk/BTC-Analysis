"""Typed, bounded visual rule graph and deterministic Python compiler.
The graph is data, never an expression language. No source is executed here.
"""
from __future__ import annotations

import base64
import binascii
import json
import re
from decimal import Decimal, InvalidOperation
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator
from .contracts import Timeframe
from .indicators import IndicatorSpec
from .serialization import fingerprint, to_wire

FRAMES=(60,180,300,900,1800,3600,14400,86400)
DecimalText=Annotated[str,StringConstraints(pattern=r"^-?[0-9]{1,12}(?:\.[0-9]{1,8})?$")]
OPERATORS=("gt","gte","lt","lte","eq","cross_up","cross_down")
MAX_SOURCE=65536
HEADER="# btc-visual-v1 "


class Strict(BaseModel):
    model_config=ConfigDict(extra="forbid",strict=True)


class Price(Strict):
    kind:Literal["price"]
    timeframe:Literal[60,180,300,900,1800,3600,14400,86400]
    field:Literal["open","high","low","close","volume"]="close"


class Constant(Strict):
    kind:Literal["constant"]
    value:DecimalText


class Indicator(Strict):
    kind:Literal["indicator"]
    timeframe:Literal[60,180,300,900,1800,3600,14400,86400]
    name:Annotated[str,StringConstraints(min_length=1,max_length=40)]
    parameters:dict[str,int|str]=Field(default_factory=dict,max_length=5)

    @model_validator(mode="after")
    def check(self):
        spec=IndicatorSpec.create(self.name,Timeframe(self.timeframe),self.parameters)
        if spec.name!=self.name:
            raise ValueError("use canonical indicator output name, e.g. ema.value")
        return self


Operand=Annotated[Price|Constant|Indicator,Field(discriminator="kind")]


class Condition(Strict):
    left:Operand
    op:Literal["gt","gte","lt","lte","eq","cross_up","cross_down"]
    right:Operand

    @model_validator(mode="after")
    def cross_clock(self):
        if self.op.startswith("cross_"):
            frames={v.timeframe for v in (self.left,self.right) if not isinstance(v,Constant)}
            if len(frames)!=1:
                raise ValueError("crossing requires at least one series and matching timeframes")
        return self


class Group(Strict):
    mode:Literal["all","any"]="all"
    conditions:list[Condition]=Field(min_length=1,max_length=8)


class Rule(Strict):
    enabled:bool=True
    mode:Literal["all","any"]="any"
    groups:list[Group]=Field(default_factory=list,max_length=4)

    @model_validator(mode="after")
    def check(self):
        if self.enabled and not self.groups:raise ValueError("enabled rule requires conditions")
        return self


class AdvancedControls(Strict):
    entry_mode:Literal["continuous","once_per_true_run"]="continuous"
    confirmation_bars:int=Field(default=1,ge=1,le=100)
    cooldown_bars:int=Field(default=0,ge=0,le=10000)
    weekdays_ist:list[Literal[0,1,2,3,4,5,6]]=Field(default_factory=lambda:list(range(7)),min_length=1,max_length=7)
    exit_mode:Literal["percent","points"]="percent"
    stop_points:DecimalText="100"
    target_points:DecimalText="200"

    @model_validator(mode="after")
    def check(self):
        if len(set(self.weekdays_ist))!=len(self.weekdays_ist):raise ValueError("duplicate entry weekday")
        for key in ("stop_points","target_points"):
            if not Decimal("0")<Decimal(getattr(self,key))<=Decimal("1000000000"):
                raise ValueError(key+" outside supported bounds")
        return self


class Graph(Strict):
    schema_version:Literal[1]=1
    signal_timeframe:Literal[60,180,300,900,1800,3600,14400,86400]=900
    execution_timeframe:Literal[60,180,300,900,1800,3600,14400,86400]=60
    exposure_pct:DecimalText="50"
    stop_loss_pct:DecimalText="1"
    take_profit_pct:DecimalText="2"
    advanced:AdvancedControls|None=None
    long_entry:Rule
    short_entry:Rule
    long_exit:Rule
    short_exit:Rule

    @model_validator(mode="after")
    def check(self):
        if not self.long_entry.enabled and not self.short_entry.enabled:
            raise ValueError("at least one entry rule must be enabled")
        for key,lo,hi in (("exposure_pct",Decimal("0.01"),Decimal(100)),
                          ("stop_loss_pct",Decimal("0.01"),Decimal(99)),
                          ("take_profit_pct",Decimal("0.01"),Decimal(99))):
            if not lo<=Decimal(getattr(self,key))<=hi:
                raise ValueError(key+" outside supported bounds")
        if self.signal_timeframe%self.execution_timeframe:
            raise ValueError("execution timeframe must divide signal timeframe")
        specs=set()
        for rule in self.rules():
            for group in rule.groups:
                for cond in group.conditions:
                    for o in (cond.left,cond.right):
                        if not isinstance(o,Constant):
                            if o.timeframe%self.execution_timeframe:
                                raise ValueError("operand timeframe must divide into execution bars")
                            if cond.op.startswith("cross_") and o.timeframe!=self.signal_timeframe:
                                raise ValueError("crossing series must use the signal timeframe")
                        if isinstance(o,Indicator):
                            specs.add(IndicatorSpec.create(o.name,Timeframe(o.timeframe),o.parameters))
        if len(specs)>64:raise ValueError("too many unique indicators")
        return self

    def rules(self):
        return (self.long_entry,self.short_entry,self.long_exit,self.short_exit)


def canonical_graph(graph:Graph):
    """Normalize decimal text, indicator defaults and parameter order."""
    raw=graph.model_dump(exclude_none=True)
    if graph.advanced is not None:
        raw["advanced"]["weekdays_ist"]=sorted(graph.advanced.weekdays_ist)
        for k in ("stop_points","target_points"):raw["advanced"][k]=to_wire(Decimal(raw["advanced"][k]))
    for key in ("exposure_pct","stop_loss_pct","take_profit_pct"):
        raw[key]=to_wire(Decimal(raw[key]))
    for rule in ("long_entry","short_entry","long_exit","short_exit"):
        for group in raw[rule]["groups"]:
            for cond in group["conditions"]:
                for side in ("left","right"):
                    o=cond[side]
                    if o["kind"]=="constant":o["value"]=to_wire(Decimal(o["value"]))
                    if o["kind"]=="indicator":
                        s=IndicatorSpec.create(o["name"],Timeframe(o["timeframe"]),o["parameters"])
                        o["parameters"]={k:to_wire(v) for k,v in s.parameters}
    return Graph.model_validate(raw)


def _params(o):
    return repr(dict(sorted(o.parameters.items())))


def _operand(o):
    if isinstance(o,Constant):return "constant("+repr(o.value)+")"
    if isinstance(o,Price):return "price(ctx, "+str(o.timeframe)+", "+repr(o.field)+")"
    return "indicator(ctx, "+repr(o.name)+", "+str(o.timeframe)+", "+_params(o)+")"


def _condition(c):
    return "compare("+repr(c.op)+", "+_operand(c.left)+", "+_operand(c.right)+")"


def _rule(rule):
    if not rule.enabled:return "False"
    groups=[]
    for group in rule.groups:
        join=" and " if group.mode=="all" else " or "
        groups.append("("+join.join(_condition(c) for c in group.conditions)+")")
    return "("+(" and " if rule.mode=="all" else " or ").join(groups)+")"


def compile_graph(graph:Graph):
    g=canonical_graph(graph)
    raw=g.model_dump(exclude_none=True)
    packed=json.dumps(raw,sort_keys=True,separators=(",",":"),ensure_ascii=True)
    metadata=base64.urlsafe_b64encode(packed.encode()).decode()
    specs=set();frames={g.signal_timeframe,g.execution_timeframe}
    for rule in g.rules():
        for group in rule.groups:
            for cond in group.conditions:
                for o in (cond.left,cond.right):
                    if not isinstance(o,Constant):frames.add(o.timeframe)
                    if isinstance(o,Indicator):specs.add((o.name,o.timeframe,_params(o)))
    lines=[HEADER+metadata,
        "# Generated by BTC Analysis Visual Builder v1. Edit in Python mode if needed.",
        "from decimal import Decimal as D",
        "from btc_analysis.contracts import Timeframe",
        "from btc_analysis.indicators import IndicatorSpec",
        "from btc_analysis.visual_runtime import VisualStrategyBase, compare, constant, price, indicator",
        "",
        "class VisualStrategy(VisualStrategyBase):",
        "    signal_seconds = "+str(g.signal_timeframe),
        "    execution_seconds = "+str(g.execution_timeframe),
        "    exposure = D("+repr(g.exposure_pct)+") / 100",
        "    stop_loss = D("+repr(g.stop_loss_pct)+") / 100",
        "    take_profit = D("+repr(g.take_profit_pct)+") / 100",
        "",
        "    def indicators(self):",
        "        return ("]
    if g.advanced is not None:
        # Configuration is generated solely from validated graph data.
        pos=lines.index("    def indicators(self):")
        lines[pos:pos]=["    advanced_controls = "+repr(raw["advanced"]), ""]
    for name,tf,params in sorted(specs):
        lines.append("            IndicatorSpec.create("+repr(name)+", Timeframe("+str(tf)+"), "+params+"),")
    lines+=["        )","","    def extra_timeframes(self):",
            "        return ("+", ".join("Timeframe("+str(t)+")" for t in sorted(frames))+",)"]
    for name in ("long_entry","short_entry","long_exit","short_exit"):
        lines+=["","    def "+name+"(self, ctx):","        return "+_rule(getattr(g,name))]
    source="\n".join(lines)+"\n"
    if len(source.encode())>MAX_SOURCE:raise ValueError("generated source exceeds limit")
    # The fixed compiler emits only literals and reviewed SDK calls.
    return {"graph":raw,"graph_sha256":fingerprint(raw),"source":source,
            "compiler_version":"visual-v1","execution_allowed":False}


def recover_graph(source):
    if not isinstance(source,str) or len(source.encode())>MAX_SOURCE:
        raise ValueError("invalid source size")
    first=source.split("\n",1)[0]
    if not first.startswith(HEADER):raise ValueError("source is not an intact visual strategy")
    try:
        payload=base64.b64decode(first[len(HEADER):],altchars=b"-_",validate=True)
        graph=Graph.model_validate_json(payload)
        result=compile_graph(graph)
    except (ValueError,UnicodeError,binascii.Error) as exc:
        raise ValueError("invalid visual metadata") from exc
    if source!=result["source"]:raise ValueError("Python source modified; stay in code mode")
    return result
