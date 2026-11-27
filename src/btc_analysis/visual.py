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
from .exit_controls import validate_exit_controls,validate_dynamic_trailing

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


class CustomOperand(Strict):
    kind:Literal["custom"]
    name:Annotated[str,StringConstraints(pattern=r"^[A-Za-z][A-Za-z0-9_]{0,47}$")]
    timeframe:Literal[60,180,300,900,1800,3600,14400,86400]


class CustomFormula(Strict):
    name:Annotated[str,StringConstraints(pattern=r"^[A-Za-z][A-Za-z0-9_]{0,47}$")]
    timeframe:Literal[60,180,300,900,1800,3600,14400,86400]
    lookback:int=Field(ge=1,le=4096)
    expression:Annotated[str,StringConstraints(min_length=1,max_length=512)]


class PositionOperand(Strict):
    kind:Literal["position"]
    field:Literal["position_entry_price","position_unrealized_pnl","position_return_pct",
                  "position_holding_minutes","position_mfe_points","position_mae_points","position_quantity"]


Operand=Annotated[Price|Constant|Indicator|CustomOperand|PositionOperand,Field(discriminator="kind")]


class Condition(Strict):
    left:Operand
    op:Literal["gt","gte","lt","lte","eq","cross_up","cross_down"]
    right:Operand

    @model_validator(mode="after")
    def cross_clock(self):
        if self.op.startswith("cross_"):
            if any(isinstance(o,PositionOperand) for o in (self.left,self.right)):
                raise ValueError("position snapshots support level comparisons only")
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


class EntrySequence(Strict):
    stages:list[Rule]=Field(min_length=2,max_length=4)
    reset:Rule|None=None
    expiry_bars:int=Field(ge=1,le=10000)

    @model_validator(mode="after")
    def check(self):
        if any(not s.enabled for s in self.stages):raise ValueError("sequence stages must be enabled")
        if self.reset is not None and not self.reset.enabled:raise ValueError("sequence reset must be enabled or absent")
        if self.expiry_bars<len(self.stages)-1:raise ValueError("sequence expiry too short for stage count")
        return self


class StateTransition(Strict):
    source:int=Field(ge=0,le=7)
    target:int=Field(ge=0,le=7)
    rule:Rule


class EntryMachine(Strict):
    """Finite directional entry gate; state 0 is idle, last state is armed."""
    state_count:int=Field(ge=2,le=8)
    transitions:list[StateTransition]=Field(min_length=1,max_length=24)
    reset:Rule|None=None
    expiry_bars:int=Field(ge=1,le=10000)

    @model_validator(mode="after")
    def check(self):
        ready=self.state_count-1
        if self.reset is not None and not self.reset.enabled:raise ValueError("machine reset must be enabled")
        edges=set()
        for t in self.transitions:
            if t.source>=ready or t.target>ready or t.source==t.target or not t.rule.enabled:
                raise ValueError("invalid machine transition")
            edge=(t.source,t.target)
            if edge in edges:raise ValueError("duplicate machine edge; combine alternative conditions in one rule")
            edges.add(edge)
        reached={0}
        for _ in range(self.state_count):
            reached|={b for a,b in edges if a in reached}
        if reached!=set(range(self.state_count)):raise ValueError("all machine states must be reachable from idle")
        return self


class TrailingPoints(Strict):
    activation:DecimalText
    distance:DecimalText

class TrailingPercent(Strict):
    activation:DecimalText
    distance:DecimalText

class TrailingATR(Strict):
    activation:DecimalText
    timeframe:Literal[60,180,300,900,1800,3600,14400,86400]
    period:int=Field(ge=1,le=4096)
    multiplier:DecimalText

class ProfitLockPoints(Strict):
    activation:DecimalText
    locked:DecimalText

class AdvancedControls(Strict):
    entry_mode:Literal["continuous","once_per_true_run"]="continuous"
    confirmation_bars:int=Field(default=1,ge=1,le=100)
    cooldown_bars:int=Field(default=0,ge=0,le=10000)
    weekdays_ist:list[Literal[0,1,2,3,4,5,6]]=Field(default_factory=lambda:list(range(7)),min_length=1,max_length=7)
    exit_mode:Literal["percent","points"]="percent"
    stop_points:DecimalText="100"
    target_points:DecimalText="200"
    target_enabled:bool|None=None
    trailing:TrailingPoints|None=None
    trailing_percent:TrailingPercent|None=None
    trailing_atr:TrailingATR|None=None
    profit_lock:ProfitLockPoints|None=None

    @model_validator(mode="after")
    def check(self):
        if len(set(self.weekdays_ist))!=len(self.weekdays_ist):raise ValueError("duplicate entry weekday")
        for key in ("stop_points","target_points"):
            if not Decimal("0")<Decimal(getattr(self,key))<=Decimal("1000000000"):
                raise ValueError(key+" outside supported bounds")
        if self.target_enabled is False and self.exit_mode!="points":raise ValueError("target disabling requires fixed price-point exits")
        if self.trailing is not None or self.profit_lock is not None:
            if self.exit_mode!="points":raise ValueError("managed exits require fixed price-point exits")
            validate_exit_controls((Decimal(self.stop_points),Decimal(self.target_points)),
                (Decimal(self.trailing.activation),Decimal(self.trailing.distance)) if self.trailing is not None else None,
                (Decimal(self.profit_lock.activation),Decimal(self.profit_lock.locked)) if self.profit_lock is not None else None)
        if self.trailing_percent is not None or self.trailing_atr is not None:
            if self.exit_mode!="points":raise ValueError("dynamic trailing requires fixed price-point initial exits")
            validate_dynamic_trailing((Decimal(self.stop_points),Decimal(self.target_points)),
                (Decimal(self.trailing.activation),Decimal(self.trailing.distance)) if self.trailing is not None else None,
                (Decimal(self.trailing_percent.activation),Decimal(self.trailing_percent.distance)) if self.trailing_percent is not None else None,
                (Decimal(self.trailing_atr.activation),Timeframe(self.trailing_atr.timeframe),self.trailing_atr.period,Decimal(self.trailing_atr.multiplier)) if self.trailing_atr is not None else None)
        return self


class PartialExit(Strict):
    pct:DecimalText
    rule:Rule

    @model_validator(mode="after")
    def check(self):
        if not Decimal("0.01")<=Decimal(self.pct)<100:raise ValueError("partial exit percent must be in [0.01,100)")
        if not self.rule.enabled:raise ValueError("partial exit rule must be enabled")
        return self


class ConditionalLock(Strict):
    locked_points:DecimalText
    cost_adjusted:Literal[True]|None=None
    rule:Rule

    @model_validator(mode="after")
    def check(self):
        if not Decimal(0)<=Decimal(self.locked_points)<=Decimal("1000000000"):
            raise ValueError("conditional locked points outside supported bounds")
        if not self.rule.enabled:raise ValueError("conditional lock rule must be enabled")
        return self


class ConditionalTarget(Strict):
    target_points:DecimalText
    mode:Literal["extend","bring_closer"]
    rule:Rule

    @model_validator(mode="after")
    def check(self):
        if not Decimal(0)<Decimal(self.target_points)<=Decimal("1000000000"):
            raise ValueError("conditional target points outside supported bounds")
        if not self.rule.enabled:raise ValueError("conditional target rule must be enabled")
        return self


class Graph(Strict):
    schema_version:Literal[1]=1
    signal_timeframe:Literal[60,180,300,900,1800,3600,14400,86400]=900
    execution_timeframe:Literal[60,180,300,900,1800,3600,14400,86400]=60
    exposure_pct:DecimalText="50"
    stop_loss_pct:DecimalText="1"
    take_profit_pct:DecimalText="2"
    advanced:AdvancedControls|None=None
    custom_formulas:list[CustomFormula]|None=Field(default=None,min_length=1,max_length=16)
    long_sequence:EntrySequence|None=None
    short_sequence:EntrySequence|None=None
    long_machine:EntryMachine|None=None
    short_machine:EntryMachine|None=None
    long_exit_machine:EntryMachine|None=None
    short_exit_machine:EntryMachine|None=None
    long_partial:PartialExit|None=None
    short_partial:PartialExit|None=None
    long_partial_levels:list[PartialExit]|None=Field(default=None,min_length=2,max_length=4)
    short_partial_levels:list[PartialExit]|None=Field(default=None,min_length=2,max_length=4)
    long_lock:ConditionalLock|None=None
    short_lock:ConditionalLock|None=None
    long_target:ConditionalTarget|None=None
    short_target:ConditionalTarget|None=None
    long_entry:Rule
    short_entry:Rule
    long_exit:Rule
    short_exit:Rule

    @model_validator(mode="after")
    def check(self):
        for direction in ("long","short"):
            seq=getattr(self,direction+"_sequence")
            machine=getattr(self,direction+"_machine")
            if seq is not None and machine is not None:raise ValueError("choose a sequence or a state machine per direction")
            if (seq is not None or machine is not None) and (self.advanced is None or not getattr(self,direction+"_entry").enabled):
                raise ValueError("entry sequence or state machine requires advanced controls and an enabled directional entry rule")
            target=getattr(self,direction+"_target")
            if target is not None and (self.advanced is None or self.advanced.exit_mode!="points" or self.advanced.target_enabled is False or not getattr(self,direction+"_entry").enabled):
                raise ValueError("conditional target requires an enabled fixed-point target and directional entry")
            lock=getattr(self,direction+"_lock")
            if lock is not None and (self.advanced is None or self.advanced.exit_mode!="points" or not getattr(self,direction+"_entry").enabled):
                raise ValueError("conditional lock requires fixed-point protection and enabled directional entry")
            partial=getattr(self,direction+"_partial")
            levels=getattr(self,direction+"_partial_levels")
            if partial is not None and levels is not None:raise ValueError("choose single partial exit or ordered partial levels per direction")
            if (partial is not None or levels is not None) and not getattr(self,direction+"_entry").enabled:
                raise ValueError("partial exit requires enabled directional entry")
            exit_machine=getattr(self,direction+"_exit_machine")
            if exit_machine is not None and (self.advanced is None or not getattr(self,direction+"_exit").enabled or not getattr(self,direction+"_entry").enabled):
                raise ValueError("exit state machine requires advanced controls and enabled entry and exit rules")
        if not self.long_entry.enabled and not self.short_entry.enabled:
            raise ValueError("at least one entry rule must be enabled")
        for key,lo,hi in (("exposure_pct",Decimal("0.01"),Decimal(100)),
                          ("stop_loss_pct",Decimal("0.01"),Decimal(99)),
                          ("take_profit_pct",Decimal("0.01"),Decimal(99))):
            if not lo<=Decimal(getattr(self,key))<=hi:
                raise ValueError(key+" outside supported bounds")
        if self.signal_timeframe%self.execution_timeframe:
            raise ValueError("execution timeframe must divide signal timeframe")
        custom={d.name:d for d in (self.custom_formulas or [])}
        if len(custom)!=len(self.custom_formulas or []):raise ValueError("duplicate custom formula name")
        if custom:
            from .visual_runtime import formula_program
            for d in custom.values():
                if d.timeframe%self.execution_timeframe:raise ValueError("custom timeframe must divide into execution bars")
            formula_program([d.model_dump() for d in custom.values()])
        specs=set()
        if self.advanced is not None and self.advanced.trailing_atr is not None:
            a=self.advanced.trailing_atr
            if a.timeframe%self.execution_timeframe:raise ValueError("ATR timeframe must divide into execution bars")
            specs.add(IndicatorSpec.create("atr.value",Timeframe(a.timeframe),{"period":a.period}))
        for rule in self.rules():
            for group in rule.groups:
                for cond in group.conditions:
                    for o in (cond.left,cond.right):
                        if not isinstance(o,(Constant,PositionOperand)):
                            if o.timeframe%self.execution_timeframe:
                                raise ValueError("operand timeframe must divide into execution bars")
                            if cond.op.startswith("cross_") and o.timeframe!=self.signal_timeframe:
                                raise ValueError("crossing series must use the signal timeframe")
                        if isinstance(o,CustomOperand) and (o.name not in custom or custom[o.name].timeframe!=o.timeframe):
                            raise ValueError("custom operand must reference a declared formula with matching timeframe")
                        if isinstance(o,Indicator):
                            specs.add(IndicatorSpec.create(o.name,Timeframe(o.timeframe),o.parameters))
        if len(specs)>64:raise ValueError("too many unique indicators")
        return self

    def rules(self):
        extra=[]
        for seq in (self.long_sequence,self.short_sequence):
            if seq is not None:
                extra.extend(seq.stages)
                if seq.reset is not None:extra.append(seq.reset)
        for machine in (self.long_machine,self.short_machine,self.long_exit_machine,self.short_exit_machine):
            if machine is not None:
                extra.extend(t.rule for t in machine.transitions)
                if machine.reset is not None:extra.append(machine.reset)
        for levels in (self.long_partial_levels,self.short_partial_levels):
            if levels is not None:extra.extend(p.rule for p in levels)
        for partial in (self.long_partial,self.short_partial):
            if partial is not None:extra.append(partial.rule)
        for lock in (self.long_lock,self.short_lock):
            if lock is not None:extra.append(lock.rule)
        for target in (self.long_target,self.short_target):
            if target is not None:extra.append(target.rule)
        return (self.long_entry,self.short_entry,self.long_exit,self.short_exit,*extra)

    def target_config(self):
        return {direction:(p.target_points,p.mode) for direction,p in ((1,self.long_target),(-1,self.short_target)) if p is not None}

    def lock_config(self):
        return {direction:(p.locked_points,True) if p.cost_adjusted else p.locked_points for direction,p in ((1,self.long_lock),(-1,self.short_lock)) if p is not None}

    def partial_levels_config(self):
        return {direction:tuple(p.pct for p in levels) for direction,levels in ((1,self.long_partial_levels),(-1,self.short_partial_levels)) if levels is not None}

    def partial_config(self):
        return {direction:p.pct for direction,p in ((1,self.long_partial),(-1,self.short_partial)) if p is not None}

    def machine_config(self):
        return {direction:(m.state_count-1,m.expiry_bars,tuple((t.source,t.target) for t in m.transitions))
                for direction,m in ((1,self.long_machine),(-1,self.short_machine)) if m is not None}

    def exit_machine_config(self):
        return {direction:(m.state_count-1,m.expiry_bars,tuple((t.source,t.target) for t in m.transitions))
                for direction,m in ((1,self.long_exit_machine),(-1,self.short_exit_machine)) if m is not None}

    def sequence_config(self):
        return {direction: (len(seq.stages),seq.expiry_bars) for direction,seq in ((1,self.long_sequence),(-1,self.short_sequence)) if seq is not None}


def raw_rules(raw):
    for name in ("long_entry","short_entry","long_exit","short_exit"):
        yield raw[name]
    for name in ("long_sequence","short_sequence"):
        seq=raw.get(name)
        if seq is not None:
            yield from seq["stages"]
            if seq.get("reset") is not None:yield seq["reset"]
    for name in ("long_machine","short_machine","long_exit_machine","short_exit_machine"):
        m=raw.get(name)
        if m is not None:
            for t in m["transitions"]:yield t["rule"]
            if m.get("reset") is not None:yield m["reset"]
    for name in ("long_partial","short_partial"):
        p=raw.get(name)
        if p is not None:yield p["rule"]
    for name in ("long_partial_levels","short_partial_levels"):
        for p in raw.get(name) or ():yield p["rule"]
    for name in ("long_target","short_target"):
        p=raw.get(name)
        if p is not None:yield p["rule"]
    for name in ("long_lock","short_lock"):
        p=raw.get(name)
        if p is not None:yield p["rule"]


def canonical_graph(graph:Graph):
    """Normalize decimal text, indicator defaults and parameter order."""
    raw=graph.model_dump(exclude_none=True)
    if graph.advanced is not None:
        raw["advanced"]["weekdays_ist"]=sorted(graph.advanced.weekdays_ist)
        for k in ("stop_points","target_points"):raw["advanced"][k]=to_wire(Decimal(raw["advanced"][k]))
        for key in ("trailing","profit_lock","trailing_percent"):
            if key in raw["advanced"]:
                raw["advanced"][key]={k:to_wire(Decimal(value)) for k,value in raw["advanced"][key].items()}
        if "trailing_atr" in raw["advanced"]:
            for key in ("activation","multiplier"):raw["advanced"]["trailing_atr"][key]=to_wire(Decimal(raw["advanced"]["trailing_atr"][key]))
    for key in ("exposure_pct","stop_loss_pct","take_profit_pct"):
        raw[key]=to_wire(Decimal(raw[key]))
    for name in ("long_partial","short_partial"):
        if name in raw:raw[name]["pct"]=to_wire(Decimal(raw[name]["pct"]))
    for name in ("long_partial_levels","short_partial_levels"):
        for p in raw.get(name) or ():p["pct"]=to_wire(Decimal(p["pct"]))
    for name in ("long_lock","short_lock"):
        if name in raw:raw[name]["locked_points"]=to_wire(Decimal(raw[name]["locked_points"]))
    for name in ("long_target","short_target"):
        if name in raw:raw[name]["target_points"]=to_wire(Decimal(raw[name]["target_points"]))
    for rule in raw_rules(raw):
        for group in rule["groups"]:
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
    if isinstance(o,CustomOperand):return "self.custom_pair("+repr(o.name)+")"
    if isinstance(o,PositionOperand):return "self.position_pair(ctx, "+repr(o.field)+")"
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
    specs=set();frames={g.signal_timeframe,g.execution_timeframe,*(d.timeframe for d in (g.custom_formulas or []))}
    if g.advanced is not None and g.advanced.trailing_atr is not None:
        a=g.advanced.trailing_atr;frames.add(a.timeframe);specs.add(("atr.value",a.timeframe,repr({"period":a.period})))
    for rule in g.rules():
        for group in rule.groups:
            for cond in group.conditions:
                for o in (cond.left,cond.right):
                    if not isinstance(o,(Constant,PositionOperand)):frames.add(o.timeframe)
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
    if g.custom_formulas:
        pos=lines.index("    def indicators(self):")
        lines[pos:pos]=["    custom_config = "+repr(raw["custom_formulas"]), ""]
    if g.sequence_config():
        pos=lines.index("    def indicators(self):")
        lines[pos:pos]=["    sequence_config = "+repr(g.sequence_config()), ""]
    if g.machine_config():
        pos=lines.index("    def indicators(self):")
        lines[pos:pos]=["    machine_config = "+repr(g.machine_config()), ""]
    if g.exit_machine_config():
        pos=lines.index("    def indicators(self):")
        lines[pos:pos]=["    exit_machine_config = "+repr(g.exit_machine_config()), ""]
    if g.partial_levels_config():
        pos=lines.index("    def indicators(self):")
        lines[pos:pos]=["    partial_levels_config = "+repr(g.partial_levels_config()), ""]
    if g.partial_config():
        pos=lines.index("    def indicators(self):")
        lines[pos:pos]=["    partial_config = "+repr(g.partial_config()), ""]
    if g.lock_config():
        pos=lines.index("    def indicators(self):")
        lines[pos:pos]=["    conditional_lock_config = "+repr(g.lock_config()), ""]
    if g.target_config():
        pos=lines.index("    def indicators(self):")
        lines[pos:pos]=["    conditional_target_config = "+repr(g.target_config()), ""]
    for name,tf,params in sorted(specs):
        lines.append("            IndicatorSpec.create("+repr(name)+", Timeframe("+str(tf)+"), "+params+"),")
    lines+=["        )","","    def extra_timeframes(self):",
            "        return ("+", ".join("Timeframe("+str(t)+")" for t in sorted(frames))+",)"]
    for name in ("long_entry","short_entry","long_exit","short_exit"):
        lines+=["","    def "+name+"(self, ctx):","        return "+_rule(getattr(g,name))]
    if g.sequence_config():
        lines+=["","    def sequence_stage(self, ctx, direction, index):"]
        for direction,seq in ((1,g.long_sequence),(-1,g.short_sequence)):
            if seq is not None:
                for i,stage in enumerate(seq.stages):
                    lines+=["        if direction == "+str(direction)+" and index == "+str(i)+":","            return "+_rule(stage)]
        lines+=["        return False","","    def sequence_reset(self, ctx, direction):"]
        for direction,seq in ((1,g.long_sequence),(-1,g.short_sequence)):
            if seq is not None and seq.reset is not None:
                lines+=["        if direction == "+str(direction)+":","            return "+_rule(seq.reset)]
        lines+=["        return False"]
    if g.machine_config():
        lines+=["","    def machine_transition(self, ctx, direction, index):"]
        for direction,m in ((1,g.long_machine),(-1,g.short_machine)):
            if m is not None:
                for i,t in enumerate(m.transitions):
                    lines+=["        if direction == "+str(direction)+" and index == "+str(i)+":","            return "+_rule(t.rule)]
        lines+=["        return False","","    def machine_reset(self, ctx, direction):"]
        for direction,m in ((1,g.long_machine),(-1,g.short_machine)):
            if m is not None and m.reset is not None:
                lines+=["        if direction == "+str(direction)+":","            return "+_rule(m.reset)]
        lines+=["        return False"]
    if g.exit_machine_config():
        lines+=["","    def exit_machine_transition(self, ctx, direction, index):"]
        for direction,m in ((1,g.long_exit_machine),(-1,g.short_exit_machine)):
            if m is not None:
                for i,t in enumerate(m.transitions):
                    lines+=["        if direction == "+str(direction)+" and index == "+str(i)+":","            return "+_rule(t.rule)]
        lines+=["        return False","","    def exit_machine_reset(self, ctx, direction):"]
        for direction,m in ((1,g.long_exit_machine),(-1,g.short_exit_machine)):
            if m is not None and m.reset is not None:
                lines+=["        if direction == "+str(direction)+":","            return "+_rule(m.reset)]
        lines+=["        return False"]
    if g.partial_config():
        lines+=["","    def partial_rule(self, ctx, direction):"]
        for direction,p in ((1,g.long_partial),(-1,g.short_partial)):
            if p is not None:
                lines+=["        if direction == "+str(direction)+":","            return "+_rule(p.rule)]
        lines+=["        return False"]
    if g.lock_config():
        lines+=["","    def conditional_lock_rule(self, ctx, direction):"]
        for direction,p in ((1,g.long_lock),(-1,g.short_lock)):
            if p is not None:
                lines+=["        if direction == "+str(direction)+":","            return "+_rule(p.rule)]
        lines+=["        return False"]
    if g.partial_levels_config():
        lines+=["","    def partial_level_rule(self, ctx, direction, index):"]
        for direction,levels in ((1,g.long_partial_levels),(-1,g.short_partial_levels)):
            if levels is not None:
                for i,p in enumerate(levels):
                    lines+=["        if direction == "+str(direction)+" and index == "+str(i)+":","            return "+_rule(p.rule)]
        lines+=["        return False"]
    if g.target_config():
        lines+=["","    def conditional_target_rule(self, ctx, direction):"]
        for direction,p in ((1,g.long_target),(-1,g.short_target)):
            if p is not None:
                lines+=["        if direction == "+str(direction)+":","            return "+_rule(p.rule)]
        lines+=["        return False"]
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
