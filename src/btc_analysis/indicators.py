"""Deterministic streaming indicator library for trusted strategy SDK v1.
Indicators consume completed candles only. Decimal arithmetic, explicit seeds,
None until ready. No arbitrary expressions, third-party strategy code or future data.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from decimal import Decimal as D, localcontext
from typing import Mapping

from .contracts import Candle, Timeframe

MAX_PERIOD = 4096
MAX_INDICATORS = 128
ZERO = D(0)
ONE = D(1)

# Each entry is (default parameters, returned series). Multi-output names are explicit.
CATALOG = {
    "sma": ({"period":20}, ("value",)),
    "ema": ({"period":20}, ("value",)),
    "atr": ({"period":14}, ("value",)),
    "rsi": ({"period":14}, ("value",)),
    "adx": ({"period":14}, ("value","plus_di","minus_di")),
    "supertrend": ({"period":10,"multiplier":D(3)}, ("line","direction")),
    "bollinger": ({"period":20,"multiplier":D(2)}, ("middle","upper","lower")),
    "donchian": ({"period":20}, ("upper","lower","middle")),
    "roc": ({"period":10}, ("value",)),
    "volume_ratio": ({"period":20}, ("value",)),
    "vwap": ({"period":20}, ("value",)),
    "macd": ({"fast":12,"slow":26,"signal":9}, ("line","signal","histogram")),
    "stddev": ({"period":20}, ("value",)),
}


@dataclass(frozen=True, slots=True)
class IndicatorSpec:
    name: str
    timeframe: Timeframe
    parameters: tuple[tuple[str, int | D | str], ...]

    @classmethod
    def create(cls, name: str, timeframe: Timeframe, parameters: Mapping | None = None):
        if not isinstance(timeframe,Timeframe):
            raise ValueError("expected Timeframe")
        base, sep, field = name.lower().partition(".") if isinstance(name,str) else ("","","")
        if base not in CATALOG:
            raise ValueError(f"unknown indicator {name}")
        defaults, fields = CATALOG[base]
        field = field if sep else fields[0]
        if field not in fields:
            raise ValueError("unknown indicator output")
        params = dict(parameters or {})
        if set(params)-set(defaults):
            raise ValueError("unknown indicator parameter")
        values = {**defaults, **params}
        for key, value in values.items():
            if key=="multiplier":
                if type(value) is int: value=D(value)
                elif isinstance(value,str):
                    try: value=D(value)
                    except ArithmeticError as e: raise ValueError("invalid multiplier") from e
                if not isinstance(value,D) or not value.is_finite() or not ZERO<value<=D(1000):
                    raise ValueError("invalid multiplier")
            elif type(value) is not int or not 1<=value<=MAX_PERIOD:
                raise ValueError(f"{key} must be integer 1..{MAX_PERIOD}")
            values[key]=value
        if base=="macd" and values["fast"]>=values["slow"]:
            raise ValueError("MACD fast must be below slow")
        return cls(base+"."+field,timeframe,tuple(sorted(values.items())))

    @property
    def base(self): return self.name.split(".")[0]
    @property
    def field(self): return self.name.split(".")[1]


def spec(name, timeframe, **parameters):
    """Canonical declaration helper. e.g. spec('ema', Timeframe(900), period=20)."""
    return IndicatorSpec.create(name,timeframe,parameters)


class Smooth:
    """SMA seed, then alpha-weighted recurrence; Wilder alpha=1/n."""
    def __init__(self,n,alpha):
        self.n=n; self.alpha=alpha; self.count=0; self.total=ZERO; self.value=None
    def update(self,x):
        if self.value is None:
            self.count+=1; self.total+=x
            if self.count==self.n: self.value=self.total/D(self.n)
        else:
            self.value=self.value+self.alpha*(x-self.value)
        return self.value


class Window:
    def __init__(self,n):
        self.n=n;self.values=deque();self.total=ZERO
    def append(self,x):
        if len(self.values)==self.n:self.total-=self.values.popleft()
        self.values.append(x);self.total+=x
    @property
    def ready(self):return len(self.values)==self.n
    @property
    def mean(self):return self.total/D(self.n) if self.ready else None


class StreamingIndicator:
    """One canonical output; state is private to an individual scenario."""
    def __init__(self,definition:IndicatorSpec):
        if definition!=IndicatorSpec.create(definition.name,definition.timeframe,dict(definition.parameters)):
            raise ValueError("noncanonical indicator declaration")
        self.definition=definition
        self.p=dict(definition.parameters)
        self.reset()

    def reset(self):
        self.last=None;self.value=None;self.prev=None;self.upper=None;self.lower=None;self.direction=None
        n=self.p.get("period",1);kind=self.definition.base
        self.window=Window(n+1 if kind=="roc" else n)
        self.window2=Window(n)
        self.ranges=deque(maxlen=n)
        with localcontext() as ctx:
            ctx.prec=50
            self.smooth=Smooth(n,ONE/D(n) if kind!="ema" else D(2)/D(n+1))
            self.up=Smooth(n,ONE/D(n));self.down=Smooth(n,ONE/D(n))
            self.dx=Smooth(n,ONE/D(n))
            self.fast=Smooth(self.p.get("fast",1),D(2)/D(self.p.get("fast",1)+1))
            self.slow=Smooth(self.p.get("slow",1),D(2)/D(self.p.get("slow",1)+1))
            self.signal=Smooth(self.p.get("signal",1),D(2)/D(self.p.get("signal",1)+1))

    def update(self,candle:Candle):
        if candle.timeframe!=self.definition.timeframe:
            raise ValueError("indicator timeframe mismatch")
        if self.last is not None and (candle.instrument!=self.prev.instrument or candle.open_utc<self.last):
            raise ValueError("indicator candles must be chronological and nonoverlapping")
        with localcontext() as ctx:
            ctx.prec=50
            result=self._compute(candle)
        self.last=candle.close_utc;self.prev=candle;self.value=result
        return result

    def _compute(self,c):
        k=self.definition.base;f=self.definition.field;n=self.p.get("period",1)
        prev=self.prev
        if k in ("sma","bollinger","stddev"):
            self.window.append(c.close)
            mean=self.window.mean
            if mean is None:return None
            if k=="sma" or (k=="bollinger" and f=="middle"):return mean
            sd=(sum(((x-mean)**2 for x in self.window.values),ZERO)/D(n)).sqrt()
            if k=="stddev":return sd
            return mean+(ONE if f=="upper" else -ONE)*self.p["multiplier"]*sd
        if k=="ema":return self.smooth.update(c.close)
        if k=="roc":
            self.window.append(c.close)
            return (c.close/self.window.values[0]-ONE)*100 if self.window.ready else None
        if k=="donchian":
            self.ranges.append((c.high,c.low))
            if len(self.ranges)<n:return None
            hi=max(x[0] for x in self.ranges);lo=min(x[1] for x in self.ranges)
            return hi if f=="upper" else lo if f=="lower" else (hi+lo)/2
        if k=="volume_ratio":
            # Current volume / mean of PREVIOUS n volumes.
            mean=self.window.mean
            self.window.append(c.volume)
            return c.volume/mean if mean is not None and mean>0 else None
        if k=="vwap":
            typical=(c.high+c.low+c.close)/3
            self.window.append(typical*c.volume);self.window2.append(c.volume)
            return self.window.total/self.window2.total if self.window.ready and self.window2.total>0 else None
        if k=="macd":
            a=self.fast.update(c.close);b=self.slow.update(c.close)
            if a is None or b is None:return None
            line=a-b;signal=self.signal.update(line)
            return line if f=="line" else signal if f=="signal" else (line-signal if signal is not None else None)
        if k=="rsi":
            if prev is None:return None
            delta=c.close-prev.close
            up=self.up.update(max(delta,ZERO));down=self.down.update(max(-delta,ZERO))
            if up is None or down is None:return None
            if down==0:return D(50) if up==0 else D(100)
            return D(100)-D(100)/(ONE+up/down)
        tr=max(c.high-c.low,abs(c.high-prev.close),abs(c.low-prev.close)) if prev else c.high-c.low
        if k=="adx":
            if prev is None:return None
            u=c.high-prev.high;v=prev.low-c.low
            atr=self.smooth.update(tr)
            pd=self.up.update(u if u>v and u>0 else ZERO)
            md=self.down.update(v if v>u and v>0 else ZERO)
            if atr is None:return None
            plus=100*pd/atr if atr>0 else ZERO
            minus=100*md/atr if atr>0 else ZERO
            dx=100*abs(plus-minus)/(plus+minus) if plus+minus>0 else ZERO
            adx=self.dx.update(dx)
            return plus if f=="plus_di" else minus if f=="minus_di" else adx
        atr=self.smooth.update(tr)
        if atr is None:return None
        if k=="atr":return atr
        if k=="supertrend":
            mid=(c.high+c.low)/2;basic_upper=mid+self.p["multiplier"]*atr;basic_lower=mid-self.p["multiplier"]*atr
            if self.direction is None:
                self.upper=basic_upper;self.lower=basic_lower
                # Explicit bearish seed, then switch only on strict crossings.
                self.direction=-ONE
            else:
                old_upper=self.upper;old_lower=self.lower
                self.upper=basic_upper if basic_upper<old_upper or prev.close>old_upper else old_upper
                self.lower=basic_lower if basic_lower>old_lower or prev.close<old_lower else old_lower
                if self.direction<0 and c.close>self.upper:self.direction=ONE
                elif self.direction>0 and c.close<self.lower:self.direction=-ONE
            return self.direction if f=="direction" else self.lower if self.direction>0 else self.upper
        raise AssertionError("unhandled indicator")


class IndicatorBook:
    def __init__(self,definitions=(),history_limit=4096):
        if type(history_limit) is not int or not 1<=history_limit<=MAX_PERIOD:
            raise ValueError("invalid indicator history limit")
        if not isinstance(definitions,tuple) or len(definitions)>MAX_INDICATORS:
            raise ValueError("indicator declarations must be a bounded tuple")
        self.entries={}; self.by_timeframe={}
        for definition in definitions:
            if not isinstance(definition,IndicatorSpec):raise ValueError("expected IndicatorSpec")
            if definition in self.entries:raise ValueError("duplicate indicator declaration")
            item=StreamingIndicator(definition),deque(maxlen=history_limit)
            self.entries[definition]=item
            self.by_timeframe.setdefault(definition.timeframe.seconds,[]).append(item)

    def update(self,candle):
        for indicator,history in self.by_timeframe.get(candle.timeframe.seconds,()):
            history.append(indicator.update(candle))

    def get(self,name,timeframe,parameters=None,limit=1):
        if type(limit) is not int or not 1<=limit<=MAX_PERIOD:raise ValueError("invalid indicator history limit")
        key=IndicatorSpec.create(name,timeframe,parameters)
        if key not in self.entries:raise ValueError("indicator must be declared before replay")
        return tuple(self.entries[key][1])[-limit:]
