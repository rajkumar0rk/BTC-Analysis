"""Disk-backed exact event archive for the trusted long-run simulator.
No source execution. Only current-bar fills are retained in memory.
"""
from dataclasses import dataclass
from collections import deque
from decimal import Decimal as D
from hashlib import sha256
from pathlib import Path
from contextlib import ExitStack
from ..serialization import canonical_bytes
from .engine import MAX_PENDING,MAX_EVENTS

MAX_BYTES=1024**3
ZERO=D(0)

class Series:
    def __init__(self,root,name,stack,*,tail=0):
        self.name=name+".ndjson";self.file=stack.enter_context((root/self.name).open("xb"))
        self.digest=sha256();self.count=0;self.bytes=0
        self.tail=deque(maxlen=tail)
        self.gain=ZERO;self.loss=ZERO;self.wins=0;self.losses=0
    def __len__(self):return self.count
    def append(self,value):
        raw=canonical_bytes(value)+b"\n"
        if self.bytes+len(raw)>MAX_BYTES:raise ValueError("archive event byte quota exceeded")
        self.file.write(raw);self.digest.update(raw);self.count+=1;self.bytes+=len(raw)
        self.tail.append(value)
        if self.name=="closed_trades.ndjson":
            p=value.net_pnl
            if p>0:self.gain+=p;self.wins+=1
            if p<0:self.loss-=p;self.losses+=1
    def __getitem__(self,key):
        if not isinstance(key,slice) or key.stop is not None or key.step is not None or key.start is None:
            raise TypeError("only current-bar tail slice supported")
        n=self.count-key.start
        if n<0 or n>len(self.tail):raise ValueError("fill tail exceeded")
        return list(self.tail)[-n:] if n else []
    def ref(self):
        return {"file":self.name,"rows":self.count,"bytes":self.bytes,"sha256":self.digest.hexdigest()}

@dataclass(frozen=True)
class ArchivedScenario:
    path:str
    bars:int
    observed_candle_sha256:str
    warmup_candle_sha256:str|None
    risk_stream_sha256:str|None
    indicator_specs:tuple
    extra_timeframes:tuple
    final_equity:D
    summary:dict
    monthly:tuple
    files:dict

class ScenarioArchive:
    def __init__(self,root,path):
        self.root=Path(root)/path
        self.stack=ExitStack()
    def __enter__(self):
        self.root.mkdir()
        return self
    def __exit__(self,*args):return self.stack.__exit__(*args)
    def bind(self,sim):
        self.series={}
        for attr,name in (("orders","orders"),("fills","fills"),("evidence","execution_evidence"),
                          ("trades","closed_trades"),("curve","equity_curve")):
            series=Series(self.root,name,self.stack,tail=MAX_PENDING+1 if attr=="fills" else 0)
            self.series[name]=series;setattr(sim,attr,series)
    def finish(self,s,e,unreal):
        t=self.series["closed_trades"];n=len(t)
        summary=dict(initial_equity=s.cfg.initial_equity,final_equity=e,balance=s.balance,
            net_pnl=e-s.cfg.initial_equity,gross_realized_pnl=s.gross,fees=s.fees,taxes=s.taxes,
            open_quantity=s.quantity,open_unrealized_pnl=unreal,max_event_drawdown_pct=s.dd,
            trades=n,wins=t.wins,losses=t.losses,breakeven=n-t.wins-t.losses,
            win_rate_pct=D(t.wins)*100/n if n else None,
            profit_factor=t.gain/t.loss if t.loss else None,
            profit_factor_status="finite" if t.loss else "no_losses" if t.gain else "undefined",
            closed_trade_net=t.gain-t.loss,warmup_bars=s.warmup_bars,
            positive_months=sum(m.pnl>0 for m in s.monthly),negative_months=sum(m.pnl<0 for m in s.monthly),
            flat_months=sum(m.pnl==0 for m in s.monthly))
        return ArchivedScenario(s.path,s.bar_count,s.digest.hexdigest(),s.warmup_hash,None,
            s.definitions,s.extra_frames,e,summary,tuple(s.monthly),{k:v.ref() for k,v in self.series.items()})
