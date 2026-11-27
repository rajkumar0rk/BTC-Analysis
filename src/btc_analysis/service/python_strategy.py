"""Bounded interpreter for a deliberately small Python SDK subset.

No exec/eval, Python import machinery, reflection, host objects as callable
values, or arbitrary attribute lookup. This is not a general Python sandbox.
"""
import ast
import operator
import re
from collections import deque
from types import MappingProxyType
from ..serialization import to_wire
from ..exit_controls import validate_exit_controls,validate_bracket,validate_dynamic_trailing,atr_trailing_spec
from datetime import datetime
from decimal import Decimal as D, localcontext
from hashlib import sha256
from zoneinfo import ZoneInfo
from ..contracts import Candle,Fill,Instrument,Timeframe,Side,OrderType
from ..indicators import IndicatorSpec,spec
from ..strategy import PythonStrategy,quantity_for_notional,crossover,crossunder

FRAMES=(60,180,300,900,1800,3600,14400,86400)
CALLBACKS={"on_start","on_execution","on_signal","on_fill","on_finish"}
SDK_IMPORTS={
    "decimal":{"Decimal"},
    "btc_analysis.strategy":{"PythonStrategy","quantity_for_notional","crossover","crossunder"},
    "btc_analysis.contracts":{"Timeframe","Side","OrderType"},
    "btc_analysis.indicators":{"IndicatorSpec","spec"},
}
CONTEXT_FIELDS={"now_utc","instrument","position_quantity","equity"}
CONTEXT_CALLS={"candles","indicator","indicator_history","cancel"}
ORDER_CALLS={"buy","sell","order","close_position"}
CUSTOM_CALLS={"custom_value","custom_history"}
DECLARATIONS={"indicators","extra_timeframes","custom_indicators"}
RESERVED=ORDER_CALLS|CUSTOM_CALLS|CALLBACKS|{"on_completed_candle"}
FIELDS={
    Candle:{"open","high","low","close","volume","open_utc","close_utc"},
    Fill:{"price","quantity","side","reason","event_utc","fee","tax"},
    Instrument:{"tick_size","lot_size","contract_multiplier","symbol"},
    Timeframe:{"seconds"},
}
BIN={ast.Add:operator.add,ast.Sub:operator.sub,ast.Mult:operator.mul,ast.Div:operator.truediv,ast.FloorDiv:operator.floordiv,ast.Mod:operator.mod}
CMP={ast.Eq:operator.eq,ast.NotEq:operator.ne,ast.Lt:operator.lt,ast.LtE:operator.le,ast.Gt:operator.gt,ast.GtE:operator.ge,ast.Is:operator.is_,ast.IsNot:operator.is_not,ast.In:lambda a,b:a in b,ast.NotIn:lambda a,b:a not in b}
ALLOWED=(ast.Module,ast.ImportFrom,ast.alias,ast.ClassDef,ast.FunctionDef,ast.arguments,ast.arg,ast.Assign,ast.AugAssign,ast.If,ast.Return,ast.Expr,ast.Pass,ast.For,ast.Break,ast.Continue,ast.Name,ast.Attribute,ast.Constant,ast.Tuple,ast.List,ast.Dict,ast.Subscript,ast.Slice,ast.Call,ast.keyword,ast.IfExp,ast.BinOp,ast.UnaryOp,ast.BoolOp,ast.Compare,ast.Load,ast.Store,ast.And,ast.Or,ast.Not,ast.USub,ast.UAdd,*BIN,*CMP)

class Returned(Exception):
    def __init__(self,value):self.value=value
class BreakLoop(Exception):pass
class ContinueLoop(Exception):pass

class StrategyDiagnostic(ValueError):
    def __init__(self,node,message):
        self.line=max(1,getattr(node,"lineno",1))
        self.column=getattr(node,"col_offset",0)+1
        self.end_line=max(self.line,getattr(node,"end_lineno",self.line) or self.line)
        self.end_column=(getattr(node,"end_col_offset",None) or self.column)+1
        self.message=str(message)[:500]
        super().__init__(f"Python strategy line {self.line}: {self.message}")

def reject(node,msg):
    raise StrategyDiagnostic(node,msg)

def parameter_number(node,aliases):
    # Parameter bounds/defaults are literals, never evaluated as user expressions.
    if isinstance(node,ast.Constant) and type(node.value) is int:return bounded(node.value)
    if isinstance(node,ast.UnaryOp) and isinstance(node.op,ast.USub) and isinstance(node.operand,ast.Constant) and type(node.operand.value) is int:
        return bounded(-node.operand.value)
    if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and aliases.get(node.func.id,node.func.id) in ("D","Decimal") and len(node.args)==1 and not node.keywords and isinstance(node.args[0],ast.Constant) and type(node.args[0].value) is str:
        try:return decimal_value(node.args[0].value)
        except (ValueError,ArithmeticError):reject(node,"invalid Decimal parameter literal")
    reject(node,"parameter requires integer literals or Decimal string literals")

def declared_parameter(name,node,aliases):
    if len(node.args)!=3 or node.keywords:reject(node,"parameter(default, minimum, maximum) requires three positional literals")
    if name in ("signal_seconds","execution_seconds","fixed_point_bracket","trailing_stop_points","profit_lock_points","trailing_stop_pct","trailing_stop_atr","leverage","exposure"):reject(node,"reserved execution setting; declare a separate strategy parameter")
    default,lo,hi=(parameter_number(n,aliases) for n in node.args)
    if not type(default) is type(lo) is type(hi) or not lo<=default<=hi or lo>=hi:reject(node,"parameter default and bounds must have one numeric type and minimum < maximum")
    return dict(name=name,kind="integer" if type(default) is int else "decimal",default=str(to_wire(default)),minimum=str(to_wire(lo)),maximum=str(to_wire(hi)),line=node.lineno)


def bounded(value):
    if type(value) is int and abs(value)>10**18:raise ValueError("integer bound exceeded")
    if isinstance(value,D) and (not value.is_finite() or abs(value)>D("1e24") or abs(value.as_tuple().exponent)>100):raise ValueError("decimal bound exceeded")
    if isinstance(value,str) and len(value)>256:raise ValueError("string bound exceeded")
    if isinstance(value,(tuple,list,dict,range)) and len(value)>4096:raise ValueError("collection bound exceeded")
    return value

def decimal_value(v):
    if type(v) not in (str,int,D):raise ValueError("Decimal requires string or integer")
    if isinstance(v,str) and (len(v)>64 or not v):raise ValueError("invalid Decimal literal")
    return bounded(D(v))

def number(v):
    if type(v) not in (D,int):raise ValueError("numeric operands required (use Decimal strings)")
    return v

def weekday(t):
    if type(t) is not datetime:raise ValueError("expected timestamp")
    return t.astimezone(ZoneInfo("Asia/Kolkata")).weekday()

def frame(seconds):
    if type(seconds) is not int or seconds not in FRAMES:raise ValueError("unsupported timeframe")
    return Timeframe(seconds)

def limited_range(*args):
    if not 1<=len(args)<=3 or any(type(v) is not int or abs(v)>4096 for v in args):raise ValueError("range exceeds bound")
    return bounded(range(*args))

def numeric_series(values):
    if type(values) not in (tuple,list) or not 1<=len(values)<=4096:raise ValueError("numeric series requires 1–4096 values")
    return tuple(D(number(v)) for v in values)

def series(bars,field):
    if type(bars) not in (tuple,list) or len(bars)>4096 or field not in ("open","high","low","close","volume"):
        raise ValueError("invalid candle series")
    if any(type(b) is not Candle for b in bars):raise ValueError("series requires completed candles")
    return tuple(getattr(b,field) for b in bars)

def aggregate(values,kind):
    vals=numeric_series(values)
    with localcontext() as c:
        c.prec=50
        total=sum(vals,D(0))
        if kind=="sum":return bounded(total)
        mean=total/D(len(vals))
        if kind=="mean":return bounded(mean)
        return bounded((sum(((v-mean)*(v-mean) for v in vals),D(0))/D(len(vals))).sqrt())

def sqrt_value(v):
    with localcontext() as c:
        c.prec=50
        return bounded(D(number(v)).sqrt())

FUNCS={"series":series,"sum":lambda v:aggregate(v,"sum"),"mean":lambda v:aggregate(v,"mean"),
       "stddev":lambda v:aggregate(v,"stddev"),"sqrt":sqrt_value,
       "D":decimal_value,"Decimal":decimal_value,"Timeframe":frame,"spec":spec,
       "quantity_for_notional":quantity_for_notional,"crossover":crossover,"crossunder":crossunder,
       "weekday_ist":weekday,"abs":abs,"min":min,"max":max,"len":len,"range":limited_range,
       "int":lambda v:bounded(int(number(v)))}

class Program:
    def __init__(self,source):
        if not isinstance(source,str) or not 0<len(source.encode())<=65536:raise ValueError("invalid Python source size")
        self.source=source
        tree=ast.parse(source)
        nodes=list(ast.walk(tree))
        if len(nodes)>4000:raise ValueError("Python strategy AST exceeds bound")
        for node in nodes:
            if not isinstance(node,ALLOWED):reject(node,"unsupported syntax "+type(node).__name__)
            if isinstance(node,ast.Attribute) and node.attr.startswith("_"):reject(node,"private attributes forbidden")
            if isinstance(node,ast.Name) and node.id.startswith("_"):reject(node,"private names forbidden")
            if isinstance(node,ast.Constant) and type(node.value) not in (str,int,bool,type(None)):reject(node,"use Decimal strings instead of floats")
            if isinstance(node,ast.Constant):bounded(node.value)
            if isinstance(node,ast.keyword) and node.arg is None:reject(node,"keyword expansion forbidden")
        self.methods={};self.constants={};self.aliases={};self.parameters={};self.parameter_nodes={};cls=None
        for node in tree.body:
            if isinstance(node,ast.Expr) and isinstance(node.value,ast.Constant) and isinstance(node.value.value,str):continue
            if isinstance(node,ast.ImportFrom):
                if node.level or node.module not in SDK_IMPORTS:reject(node,"import not in SDK allowlist")
                for a in node.names:
                    if a.name not in SDK_IMPORTS[node.module] or (a.asname and a.asname.startswith("_")):reject(node,"unsupported SDK import")
                    alias=a.asname or a.name
                    if alias in self.aliases or alias in ("self","ctx"):reject(node,"invalid alias")
                    self.aliases[alias]=a.name
            elif isinstance(node,ast.ClassDef) and cls is None:cls=node
            else:reject(node,"only SDK imports and one strategy class allowed")
        if cls is None or cls.decorator_list or cls.keywords or len(cls.bases)!=1 or not isinstance(cls.bases[0],ast.Name) or self.aliases.get(cls.bases[0].id,cls.bases[0].id)!="PythonStrategy":
            raise ValueError("define one class Strategy(PythonStrategy)")
        for node in cls.body:
            if isinstance(node,ast.Expr) and isinstance(node.value,ast.Constant) and isinstance(node.value.value,str):continue
            if isinstance(node,ast.FunctionDef):
                a=node.args
                if node.decorator_list or node.returns or a.posonlyargs or a.kwonlyargs or a.vararg or a.kwarg or a.defaults or any(x.annotation for x in a.args):reject(node,"only simple method parameters supported")
                params=[x.arg for x in a.args]
                if not params or params[0]!="self" or len(params)!=len(set(params)) or any(x.startswith("_") for x in params):reject(node,"invalid method signature")
                if node.name in self.methods or node.name in (ORDER_CALLS|CUSTOM_CALLS|{"on_completed_candle"}) or node.name.startswith("_") and node.name!="__init__":reject(node,"invalid method name")
                if node.name in CALLBACKS and params!= (["self","ctx","fill"] if node.name=="on_fill" else ["self","ctx"]):reject(node,"invalid callback signature")
                if node.name in ({"__init__"}|DECLARATIONS) and params!=["self"]:reject(node,"invalid declaration signature")
                self.methods[node.name]=node
            elif isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name):
                name=node.targets[0].id
                if name in self.constants or name in RESERVED or name in DECLARATIONS:reject(node,"invalid class constant")
                if isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Name) and node.value.func.id=="parameter":
                    if len(self.parameters)>=32:reject(node,"maximum 32 declared parameters")
                    self.parameters[name]=declared_parameter(name,node.value,self.aliases)
                    self.parameter_nodes[name]=node.value
                    self.constants[name]=node.value.args[0]
                else:self.constants[name]=node.value
            else:reject(node,"unsupported class member")
        if not CALLBACKS.intersection(self.methods):raise ValueError("define at least one SDK callback")
        if set(self.methods)&set(self.constants):raise ValueError("duplicate class member")
        # Check every call, including branches not reached during initialization.
        # Context aliases may be passed to helper methods; runtime verifies
        # receiver identity and arguments again before any SDK operation.
        allowed_names=set(FUNCS)
        declaration_ids={id(n) for n in self.parameter_nodes.values()}
        for n in nodes:
            if not isinstance(n,ast.Call):continue
            if id(n) in declaration_ids:continue
            target=n.func
            if isinstance(target,ast.Name) and self.aliases.get(target.id,target.id) in allowed_names:continue
            if isinstance(target,ast.Attribute) and isinstance(target.value,ast.Name):
                base=target.value.id;name=target.attr
                if base=="self" and (name in ORDER_CALLS or name in CUSTOM_CALLS or name in self.methods and name not in CALLBACKS and name not in DECLARATIONS and name!="__init__"):continue
                if self.aliases.get(base,base)=="IndicatorSpec" and name=="create":continue
                if name in CONTEXT_CALLS:continue
            reject(n,"call not in SDK allowlist")
        self.hash=sha256(("restricted-python-v1\n"+source).encode()).hexdigest()

    def make(self,leverage=D(1)):
        return InterpretedStrategy(self,leverage)

class InterpretedStrategy(PythonStrategy):
    def __init__(self,program,leverage):
        super().__init__()
        self.program=program;self.state={};self.steps=0;self.depth=0
        self.ctx=None;self.indicator_mode=False;self.custom={};self.indicator_constants={}
        for k,v in program.constants.items():
            self.state[k]=self.expr(v,{})
        # Formula evaluation reads only immutable scalar class constants, not trading state.
        self.indicator_constants=MappingProxyType({k:v for k,v in self.state.items() if type(v) in (int,D,str,bool,type(None))})
        if "__init__" in program.methods:self.invoke("__init__",[])
        self.signal_seconds=self.state.get("signal_seconds",60)
        if type(self.signal_seconds) is not int or self.signal_seconds not in FRAMES:raise ValueError("invalid signal_seconds")
        if self.state.get("execution_seconds",60)!=60:raise ValueError("1m execution required")
        self.exposure=decimal_value(self.state.get("exposure",D(".5")))
        if not 0<self.exposure<=1:raise ValueError("exposure must be a fraction in (0,1]")
        self.state["exposure"]=self.exposure*leverage
        self.state["leverage"]=leverage
        self.exposure=self.state["exposure"]
        bracket=self.state.get("fixed_point_bracket")
        if bracket is not None:
            validate_bracket(bracket)
            self.fixed_point_bracket=bracket
        self.trailing_stop_points=self.state.get("trailing_stop_points")
        self.profit_lock_points=self.state.get("profit_lock_points")
        validate_exit_controls(bracket,self.trailing_stop_points,self.profit_lock_points)
        self.trailing_stop_pct=self.state.get("trailing_stop_pct")
        self.trailing_stop_atr=self.state.get("trailing_stop_atr")
        validate_dynamic_trailing(bracket,self.trailing_stop_points,self.trailing_stop_pct,self.trailing_stop_atr)
        self.specs=self.invoke("indicators",[]) if "indicators" in program.methods else ()
        if not isinstance(self.specs,tuple) or len(self.specs)>64 or any(type(v) is not IndicatorSpec for v in self.specs):raise ValueError("indicators must return a tuple of SDK specs")
        atr_spec=atr_trailing_spec(self.trailing_stop_atr)
        if atr_spec is not None and atr_spec not in self.specs:
            if len(self.specs)>=64:raise ValueError("too many indicator declarations including ATR trailing")
            self.specs=(*self.specs,atr_spec)
        extra=self.invoke("extra_timeframes",[]) if "extra_timeframes" in program.methods else ()
        if not isinstance(extra,tuple) or len(extra)>8 or any(type(v) is not Timeframe or v.seconds not in FRAMES for v in extra):raise ValueError("invalid extra_timeframes")
        definitions=self.invoke("custom_indicators",[]) if "custom_indicators" in program.methods else ()
        if type(definitions) is not tuple or len(definitions)>16:raise ValueError("custom_indicators must return a tuple of at most 16 declarations")
        self.custom_definitions=[]
        for item in definitions:
            if type(item) is not tuple or len(item)!=4:raise ValueError("custom declaration requires (name, Timeframe, lookback, method_name)")
            name,tf,lookback,method=item
            if type(name) is not str or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,47}",name) or name in self.custom:raise ValueError("invalid or duplicate custom indicator name")
            if type(tf) is not Timeframe or tf.seconds not in FRAMES or type(lookback) is not int or not 1<=lookback<=4096:raise ValueError("invalid custom indicator timeframe or lookback")
            if type(method) is not str or method in RESERVED or method in DECLARATIONS or method=="__init__" or method not in program.methods:raise ValueError("invalid custom indicator formula method")
            if [arg.arg for arg in program.methods[method].args.args]!=["self","bars","previous"]:reject(program.methods[method],"formula signature must be (self, bars, previous)")
            self.check_formula(method,set())
            self.custom_definitions.append(dict(name=name,timeframe=tf.seconds,lookback=lookback,method=method))
            self.custom[name]=(tf,method,deque(maxlen=lookback),deque(maxlen=4096))
        self.frames=tuple(sorted({Timeframe(60),Timeframe(self.signal_seconds),*extra,*(s.timeframe for s in self.specs),*(v[0] for v in self.custom.values())},key=lambda t:t.seconds))

    def check_formula(self,method,seen):
        if method in seen:return
        seen.add(method)
        for n in ast.walk(self.program.methods[method]):
            if isinstance(n,ast.Attribute) and isinstance(n.value,ast.Name) and n.value.id=="self":
                if isinstance(n.ctx,ast.Store):reject(n,"custom indicator formulas cannot mutate strategy state")
                if n.attr in ORDER_CALLS|CUSTOM_CALLS|DECLARATIONS:reject(n,"custom indicator formulas cannot access trading or other indicator state")
                if n.attr in self.program.methods:self.check_formula(n.attr,seen)
                elif n.attr not in self.indicator_constants:reject(n,"formula may only read immutable scalar class constants")
            if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr in CONTEXT_CALLS:
                reject(n,"custom indicator formulas cannot access trading context")

    def on_completed_candle(self,candle):
        # Engine invokes this trusted hook only when a bar has fully completed.
        # Every indicator has private rolling history and previous output.
        if not self.custom:return
        for tf,method,bars,history in self.custom.values():
            if candle.timeframe!=tf:continue
            if bars and candle.open_utc!=bars[-1].close_utc:raise ValueError("noncontiguous custom indicator candles")
            bars.append(candle)
            if len(bars)<bars.maxlen:
                history.append(None);continue
            self.indicator_mode=True;self.steps=0
            try:
                result=self.invoke(method,[tuple(bars),history[-1] if history else None])
                if result is not None:
                    if type(result) not in (D,int):reject(self.program.methods[method],"custom indicator must return a number or None")
                    result=bounded(D(result))
                history.append(result)
            finally:self.indicator_mode=False

    def custom_history(self,name,limit=2):
        if self.indicator_mode or self.ctx is None:raise ValueError("custom indicator history is available only to strategy callbacks")
        if type(name) is not str or name not in self.custom:raise ValueError("custom indicator must be declared")
        if type(limit) is not int or not 1<=limit<=4096:raise ValueError("invalid custom indicator history limit")
        return tuple(self.custom[name][3])[-limit:]

    def custom_value(self,name):
        values=self.custom_history(name,1)
        return values[-1] if values else None

    def charge(self,node):
        self.steps+=1
        if self.steps>20000:reject(node,"callback instruction budget exceeded")

    def invoke(self,name,args):
        node=self.program.methods[name]
        names=[a.arg for a in node.args.args][1:]
        if len(names)!=len(args):reject(node,"method argument count mismatch")
        if self.depth>=8:reject(node,"method recursion depth exceeded")
        self.depth+=1
        try:
            self.block(node.body,dict(zip(names,args)))
        except Returned as r:return r.value
        finally:self.depth-=1

    def block(self,body,env):
        for n in body:
            self.charge(n)
            if isinstance(n,ast.Pass):continue
            if isinstance(n,ast.Return):raise Returned(self.expr(n.value,env) if n.value else None)
            if isinstance(n,ast.If):self.block(n.body if self.expr(n.test,env) else n.orelse,env);continue
            if isinstance(n,ast.Expr):self.expr(n.value,env);continue
            if isinstance(n,ast.Assign):
                if len(n.targets)!=1:reject(n,"single assignment target required")
                self.put(n.targets[0],self.expr(n.value,env),env);continue
            if isinstance(n,ast.AugAssign):
                self.put(n.target,self.binary(n.op,self.expr(n.target,env),self.expr(n.value,env)),env);continue
            if isinstance(n,ast.For):
                seq=self.expr(n.iter,env)
                if not isinstance(seq,(tuple,list,range)) or len(seq)>4096:reject(n,"bounded sequence required")
                for val in seq:
                    self.charge(n);self.put(n.target,val,env)
                    try:self.block(n.body,env)
                    except ContinueLoop:continue
                    except BreakLoop:break
                else:self.block(n.orelse,env)
                continue
            if isinstance(n,ast.Break):raise BreakLoop()
            if isinstance(n,ast.Continue):raise ContinueLoop()
            reject(n,"unsupported statement")

    def put(self,target,value,env):
        bounded(value)
        if isinstance(target,ast.Name) and target.id not in ("self","ctx"):
            env[target.id]=value;return
        if isinstance(target,ast.Attribute) and isinstance(target.value,ast.Name) and target.value.id=="self":
            if self.indicator_mode:reject(target,"custom indicator formulas cannot mutate strategy state")
            if target.attr in RESERVED or target.attr in self.program.methods:reject(target,"reserved state field")
            if target.attr in self.program.parameters:reject(target,"declared parameters are immutable; change the source default")
            if self.ctx is not None and target.attr in ("signal_seconds","execution_seconds","fixed_point_bracket","trailing_stop_points","profit_lock_points","trailing_stop_pct","trailing_stop_atr","leverage"):reject(target,"execution configuration is immutable")
            if target.attr not in self.state and len(self.state)>=128:reject(target,"state field limit")
            # Prevent retaining context/host objects; state may retain ordinary
            # numbers, strings, immutable candle snapshots, bounded sequences.
            if value is self.ctx and value is not None:reject(target,"context cannot be stored")
            self.state[target.attr]=value;return
        reject(target,"only local variables and self state assignments supported")

    def binary(self,op,a,b):
        number(a);number(b)
        if isinstance(op,ast.Div):a,b=D(a),D(b)
        with localcontext() as c:
            c.prec=50
            return bounded(BIN[type(op)](a,b))

    def expr(self,n,env):
        try:return self.evaluate(n,env)
        except StrategyDiagnostic:raise
        except (ValueError,TypeError,ArithmeticError,IndexError,KeyError,AttributeError) as exc:
            reject(n,str(exc) or type(exc).__name__)

    def evaluate(self,n,env):
        self.charge(n)
        if isinstance(n,ast.Constant):return bounded(n.value)
        if isinstance(n,ast.Name):
            if n.id in env:return env[n.id]
            reject(n,"unknown value "+n.id)
        if isinstance(n,(ast.Tuple,ast.List)):return bounded(tuple(self.expr(x,env) for x in n.elts))
        if isinstance(n,ast.Dict):
            if any(k is None for k in n.keys):reject(n,"dictionary expansion forbidden")
            return bounded({self.expr(k,env):self.expr(v,env) for k,v in zip(n.keys,n.values)})
        if isinstance(n,ast.Attribute):
            if isinstance(n.value,ast.Name):
                base=n.value.id;alias=self.program.aliases.get(base,base)
                if base=="self":
                    values=self.indicator_constants if self.indicator_mode else self.state
                    if n.attr in values:return values[n.attr]
                    reject(n,"unknown or unavailable strategy field "+n.attr)
                if alias=="Side" and n.attr in ("BUY","SELL"):return Side[n.attr]
                if alias=="OrderType" and n.attr in ("MARKET","LIMIT","STOP_MARKET","STOP_LIMIT"):return OrderType[n.attr]
            obj=self.expr(n.value,env)
            if obj is self.ctx and obj is not None and n.attr in CONTEXT_FIELDS:return getattr(obj,n.attr)
            if n.attr in FIELDS.get(type(obj),set()):return getattr(obj,n.attr)
            reject(n,"attribute not in SDK allowlist")
        if isinstance(n,ast.Subscript):
            obj=self.expr(n.value,env)
            if type(obj) not in (tuple,list,dict,str,range):reject(n,"unsupported subscript")
            if isinstance(n.slice,ast.Slice):
                index=slice(*(self.expr(x,env) if x else None for x in (n.slice.lower,n.slice.upper,n.slice.step)))
            else:index=self.expr(n.slice,env)
            return bounded(obj[index])
        if isinstance(n,ast.BinOp):return self.binary(n.op,self.expr(n.left,env),self.expr(n.right,env))
        if isinstance(n,ast.UnaryOp):
            v=self.expr(n.operand,env)
            return not v if isinstance(n.op,ast.Not) else bounded(-number(v) if isinstance(n.op,ast.USub) else +number(v))
        if isinstance(n,ast.BoolOp):
            for x in n.values:
                v=self.expr(x,env)
                if bool(v)==isinstance(n.op,ast.Or):return v
            return v
        if isinstance(n,ast.Compare):
            a=self.expr(n.left,env)
            for op,x in zip(n.ops,n.comparators):
                b=self.expr(x,env)
                if not CMP[type(op)](a,b):return False
                a=b
            return True
        if isinstance(n,ast.IfExp):return self.expr(n.body if self.expr(n.test,env) else n.orelse,env)
        if isinstance(n,ast.Call):
            args=[self.expr(x,env) for x in n.args];kw={x.arg:self.expr(x.value,env) for x in n.keywords}
            if isinstance(n.func,ast.Name):
                name=self.program.aliases.get(n.func.id,n.func.id)
                if name in FUNCS:return bounded(FUNCS[name](*args,**kw))
            if isinstance(n.func,ast.Attribute) and isinstance(n.func.value,ast.Name):
                base=n.func.value.id;name=n.func.attr
                if base=="self":
                    if name in CUSTOM_CALLS and self.ctx is not None and not self.indicator_mode:return bounded(getattr(self,name)(*args,**kw))
                    if name in self.program.methods and name not in CALLBACKS and name not in DECLARATIONS and name!="__init__" and not kw:return self.invoke(name,args)
                    if name in ORDER_CALLS and not self.indicator_mode and self.ctx is not None and args and args[0] is self.ctx:
                        return bounded(getattr(PythonStrategy,name)(self,*args,**kw))
                if self.program.aliases.get(base,base)=="IndicatorSpec" and name=="create":return IndicatorSpec.create(*args,**kw)
                if env.get(base) is self.ctx and self.ctx is not None and name in CONTEXT_CALLS:return bounded(getattr(self.ctx,name)(*args,**kw))
            reject(n,"call not in SDK allowlist")
        reject(n,"unsupported expression")

    def callback(self,name,ctx,*args):
        if name not in self.program.methods:return
        self.ctx=ctx;self.steps=0
        try:self.invoke(name,[ctx,*args])
        finally:self.ctx=None

    def indicators(self):return self.specs
    def extra_timeframes(self):return self.frames
    def on_start(self,ctx):self.callback("on_start",ctx)
    def on_execution(self,ctx):self.callback("on_execution",ctx)
    def on_signal(self,ctx):self.callback("on_signal",ctx)
    def on_fill(self,ctx,fill):self.callback("on_fill",ctx,fill)
    def on_finish(self,ctx):self.callback("on_finish",ctx)

def prepare_python(source):
    p=Program(source)
    sample=p.make()
    return p,sample.signal_seconds,tuple(t.seconds for t in sample.frames)
