"""Reference event simulator for linear single-instrument 1x perpetual research.

No arbitrary Python sandbox, venue margin, funding, orderbook or liquidation.
Only trusted strategy factories. Source factory must replay identical completed bars.
The execution clock is deterministic; intrabar prices are scenarios, not tick evidence.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal as D, localcontext, ROUND_CEILING, ROUND_FLOOR
from hashlib import sha256
from typing import Callable, Iterable
from zoneinfo import ZoneInfo

from ..contracts import (AssetClass, BacktestConfig, Candle, ClosedTrade, Fill,
    IntrabarPolicy, MarginMode, OrderIntent, OrderType, Side, Timeframe, DataKind)
from ..serialization import canonical_bytes, fingerprint

ENGINE_VERSION = "m3-reference-1"
ZERO = D(0)
BPS = D(10000)
MAX_HISTORY = 4096
MAX_PENDING = 256
MAX_EVENTS = 1_000_000
MAX_BARS = 5_000_000


class BaseStrategy:
    """Convenience lifecycle methods; trusted subclasses override as needed."""
    def on_start(self, ctx): pass
    def on_signal(self, ctx): pass
    def on_execution(self, ctx): pass
    def on_fill(self, ctx, fill): pass
    def on_finish(self, ctx): pass


@dataclass(frozen=True, slots=True)
class OrderEvent:
    event_utc: datetime
    intent_id: str
    status: str
    detail: str
    intent: OrderIntent | None = None


@dataclass(frozen=True, slots=True)
class ExecutionEvidence:
    fill_id: str
    bar_open_utc: datetime
    bar_close_utc: datetime
    phase: str  # open, intrabar_segment_N; modeled availability, not exact tick time
    reference_price: D
    path: str


@dataclass(frozen=True, slots=True)
class EquityPoint:
    event_utc: datetime
    balance: D
    equity: D
    quantity: D


@dataclass(frozen=True, slots=True)
class MonthlyResult:
    month: str
    opening_equity: D
    closing_equity: D
    pnl: D
    return_pct: D | None


@dataclass(frozen=True, slots=True)
class ScenarioResult:
    path: str
    bars: int
    observed_candle_sha256: str
    initial_equity: D
    final_equity: D
    balance: D
    net_pnl: D
    gross_realized_pnl: D
    fees: D
    taxes: D
    open_quantity: D
    open_unrealized_pnl: D
    max_event_drawdown_pct: D
    closed_trades: tuple[ClosedTrade, ...]
    fills: tuple[Fill, ...]
    execution_evidence: tuple[ExecutionEvidence, ...]
    orders: tuple[OrderEvent, ...]
    equity_curve: tuple[EquityPoint, ...]
    monthly: tuple[MonthlyResult, ...]


@dataclass(frozen=True, slots=True)
class BacktestResult:
    engine_version: str
    config_sha256: str
    declared_dataset_sha256s: tuple[str, ...]
    scenarios: tuple[ScenarioResult, ...]
    worst_path: str
    limitations: tuple[str, ...]

    @property
    def result_sha256(self):
        return fingerprint(self)


@dataclass(slots=True)
class Pending:
    intent: OrderIntent
    triggered: bool = False


class Context:
    """Read-only snapshots via public interface; NOT a Python security boundary."""
    __slots__ = ("_sim",)
    def __init__(self, sim): self._sim = sim
    @property
    def now_utc(self): return self._sim.now
    @property
    def instrument(self): return self._sim.cfg.instrument
    @property
    def position_quantity(self): return self._sim.quantity
    @property
    def equity(self): return self._sim.equity(self._sim.mark)
    def candles(self, timeframe, limit):
        if type(limit) is not int or not 1 <= limit <= MAX_HISTORY:
            raise ValueError("history limit outside engine bound")
        if timeframe.seconds not in self._sim.history:
            raise ValueError("unsupported timeframe; use configured execution or signal timeframe")
        return tuple(self._sim.history[timeframe.seconds])[-limit:]
    def indicator(self, name, timeframe, parameters):
        raise NotImplementedError("indicator library is M4")
    def submit(self, intent): self._sim.submit(intent)
    def cancel(self, intent_id): self._sim.cancel(intent_id)


def _validate(cfg):
    if cfg.instrument.asset_class is not AssetClass.CRYPTO_PERPETUAL:
        raise ValueError("M3 supports only explicitly linear perpetual contracts")
    if not (cfg.account_currency == cfg.instrument.quote_currency == cfg.instrument.settlement_currency):
        raise ValueError("M3 requires same quote, settlement and account currency")
    if cfg.leverage != 1 or cfg.margin_mode not in (MarginMode.ISOLATED, MarginMode.CROSS):
        raise ValueError("M3 supports only 1x baseline collateral; venue margin is M5")
    if cfg.costs.include_funding or cfg.costs.include_spread or cfg.costs.include_liquidation:
        raise ValueError("M5 required for funding, spread or liquidation")
    if cfg.costs.slippage_bps >= BPS:
        raise ValueError("slippage must be below 10000 bps")
    if cfg.intrabar_policy not in (IntrabarPolicy.STOP_FIRST, IntrabarPolicy.BOTH_PATHS):
        raise ValueError("tick sequence not supported by candle simulator")
    if cfg.calendar_id != "crypto-24x7" or cfg.allow_data_gaps:
        raise ValueError("M3 requires gap-free continuous UTC data")
    if len(cfg.datasets) != 1 or cfg.datasets[0].kind != DataKind.OHLCV:
        raise ValueError("M3 requires exactly one execution OHLCV dataset")
    step = cfg.execution_timeframe.seconds
    sig = cfg.signal_timeframe.seconds
    if sig // step > MAX_HISTORY:
        raise ValueError("signal aggregation exceeds history bound")
    for t in (cfg.start_utc, cfg.end_utc):
        if t.microsecond or int(t.timestamp()) % sig:
            raise ValueError("M3 range must align to complete UTC signal candles")
    if (cfg.end_utc-cfg.start_utc).total_seconds()//step > MAX_BARS:
        raise ValueError("bar count exceeds reference simulator bound")


def run_backtest(config: BacktestConfig, strategy_factory: Callable[[], BaseStrategy],
                 candle_factory: Callable[[], Iterable[Candle]], *,
                 linear_contract: bool = False, dataset_manifest_sha256: str) -> BacktestResult:
    """Run fresh strategies for each scenario. No mutation of input config or source.

    The caller is a trusted adapter responsible for the declared source manifest and
    strategy code/parameter hashes. The observed candle stream is independently hashed.
    BOTH_PATHS runs separate full O-H-L-C and O-L-H-C simulations, not per-bar
    oracle selection. STOP_FIRST chooses an adverse-first path at each bar based
    on starting position or first pending entry direction (a heuristic).
    """
    _validate(config)
    if linear_contract is not True:
        raise ValueError("trusted adapter must attest a linear contract")
    if dataset_manifest_sha256 != config.datasets[0].manifest_sha256:
        raise ValueError("source manifest does not match pinned configuration")
    paths = ("O-H-L-C","O-L-H-C") if config.intrabar_policy is IntrabarPolicy.BOTH_PATHS else ("adverse-first",)
    out = []
    used = []
    with localcontext() as ctx:
        ctx.prec = 50
        for path in paths:
            strategy = strategy_factory()
            if any(strategy is old for old in used):
                raise ValueError("strategy factory must return fresh instances")
            used.append(strategy)
            sim = Simulator(config, strategy, path)
            out.append(sim.run(candle_factory()))
    if len({x.observed_candle_sha256 for x in out}) != 1:
        raise ValueError("scenario candle streams differ")
    worst = min(out,key=lambda x:(x.final_equity,x.path))
    return BacktestResult(ENGINE_VERSION,fingerprint(config),
        tuple(d.manifest_sha256 for d in config.datasets),tuple(out),worst.path,(
        "Trusted strategy and source adapters only; no untrusted Python execution.",
        "Linear 1x collateral cap only; no exchange margin, funding, spread or liquidation.",
        "OHLC paths are assumptions; limit touch assumes full fill, no volume or queue modeling.",
        "Intrabar fills have bar-close availability timestamps, not observed tick timestamps.",
        "Adverse-first is a heuristic; two fixed paths are scenarios, not worst-case bounds.",
        "Fees use configured bps; no venue-specific rebates, offers or fee rounding.",
        "No forced terminal liquidation; open positions marked at final close.",
        "Drawdown sampled at modeled price events; not actual tick drawdown.",
        "Strategy callbacks are close-time; on_fill observes final bar state, not intrabar state.",
        "Caller attests pinned source and code; observed candle hash recorded independently.",
    ))


class Simulator:
    def __init__(self,cfg,strategy,path):
        self.cfg=cfg; self.strategy=strategy; self.path=path
        self.now=cfg.start_utc; self.mark=None
        self.balance=cfg.initial_equity; self.quantity=ZERO
        self.lots=deque(); self.entries=[]; self.exits=[]; self.trade_gross=ZERO
        self.gross=ZERO; self.fees=ZERO; self.taxes=ZERO
        self.pending={}; self.seen=set(); self.orders=[]; self.fills=[]; self.evidence=[]
        self.trades=[]; self.curve=[]; self.monthly=[]
        self.peak=cfg.initial_equity; self.dd=ZERO
        self.history={k:deque(maxlen=MAX_HISTORY) for k in
            (cfg.execution_timeframe.seconds,cfg.signal_timeframe.seconds)}
        self.group=[]; self.context=Context(self)
        self.active=True; self.bar_count=0; self.digest=sha256()
        self.mult=cfg.instrument.contract_multiplier
        self.tz=ZoneInfo(cfg.reporting_timezone)
        self.month=None; self.month_open=cfg.initial_equity; self.month_close=cfg.initial_equity

    def unrealized(self, price):
        if price is None: return ZERO
        sign=D(1) if self.quantity>0 else D(-1)
        return sum(((price-p)*q*self.mult*sign for q,p in self.lots),ZERO)

    def equity(self,price): return self.balance+self.unrealized(price)

    def sample(self, price):
        self.mark=price; e=self.equity(price)
        self.peak=max(self.peak,e)
        self.dd=max(self.dd,(self.peak-e)/self.peak*100)

    def log(self,i,status,detail,intent=None):
        if len(self.orders)>=MAX_EVENTS: raise ValueError("order event quota exceeded")
        self.orders.append(OrderEvent(self.now,i,status,detail,intent))

    def submit(self,intent):
        if not isinstance(intent,OrderIntent): raise TypeError("expected OrderIntent")
        i=intent.intent_id
        if i in self.seen: raise ValueError("duplicate order intent ID")
        self.seen.add(i)
        if not self.active:
            self.log(i,"rejected","run_finished",intent); return
        if intent.instrument!=self.cfg.instrument or intent.decision_utc!=self.now:
            self.log(i,"rejected","instrument_or_decision_time_mismatch",intent); return
        if len(self.pending)>=MAX_PENDING:
            self.log(i,"rejected","pending_order_limit",intent); return
        self.pending[i]=Pending(intent)
        self.log(i,"accepted","eligible_next_execution_bar",intent)

    def cancel(self,i):
        if i in self.pending:
            del self.pending[i]; self.log(i,"cancelled","strategy_cancel")
        else:
            self.log(i,"cancel_rejected","unknown_or_terminal_order")

    def round_price(self,price,side):
        tick=self.cfg.instrument.tick_size
        r=ROUND_CEILING if side is Side.BUY else ROUND_FLOOR
        return (price/tick).to_integral_value(rounding=r)*tick

    def _fill(self,p,ref,phase,bar,path,limit=False,resting=False):
        o=p.intent; i=o.intent_id
        if i not in self.pending:return
        sign=D(1) if o.side is Side.BUY else D(-1)
        qty=o.quantity
        self.now=bar.open_utc if phase=="open" else bar.close_utc
        opposite=self.quantity*sign<0
        if o.reduce_only:
            if not opposite:
                del self.pending[i]; self.log(i,"rejected","reduce_only_without_position");return
            qty=min(qty,abs(self.quantity))
        elif opposite and qty>abs(self.quantity):
            del self.pending[i];self.log(i,"rejected","reversal_not_supported");return
        if limit:
            price=self.round_price(ref,o.side)
            price=min(price,o.limit_price) if sign>0 else max(price,o.limit_price)
        else:
            price=self.round_price(ref*(1+sign*self.cfg.costs.slippage_bps/BPS),o.side)
        if price<=0: raise ValueError("nonpositive modeled fill price")
        rate=self.cfg.costs.maker_bps if resting else self.cfg.costs.taker_bps
        fee=price*qty*self.mult*rate/BPS; tax=fee*self.cfg.costs.tax_rate
        if not opposite:
            # 1x initial collateral cap: existing marked exposure plus new notional.
            e=self.equity(price)
            if (abs(self.quantity)+qty)*price*self.mult+fee+tax>e:
                del self.pending[i];self.log(i,"rejected","baseline_collateral_cap");return
        if len(self.fills)>=MAX_EVENTS: raise ValueError("fill event quota exceeded")
        del self.pending[i]
        f=Fill(f"fill-{len(self.fills)+1}",i,o.instrument,self.now,o.side,qty,price,fee,tax,
               self.cfg.account_currency,o.reason)
        self.fills.append(f)
        self.evidence.append(ExecutionEvidence(f.fill_id,bar.open_utc,bar.close_utc,phase,ref,path))
        self.log(i,"filled","reduce_only_clipped" if qty!=o.quantity else "modeled_full_fill")
        self.balance-=fee+tax;self.fees+=fee;self.taxes+=tax
        if opposite:
            left=qty; gross=ZERO
            oldsign=D(1) if self.quantity>0 else D(-1)
            while left:
                q,p0=self.lots.popleft()
                take=min(left,q); gross+=(price-p0)*take*self.mult*oldsign
                left-=take
                if take<q:self.lots.appendleft((q-take,p0))
            self.exits.append(f);self.trade_gross+=gross;self.gross+=gross;self.balance+=gross
        else:
            self.lots.append((qty,price));self.entries.append(f)
        self.quantity+=sign*qty
        if self.quantity==0:
            allfills=self.entries+self.exits
            fees=sum((x.fee for x in allfills),ZERO);taxes=sum((x.tax for x in allfills),ZERO)
            self.trades.append(ClosedTrade(f"trade-{len(self.trades)+1}",tuple(self.entries),tuple(self.exits),
                self.entries[0].reason,self.exits[-1].reason,self.trade_gross,fees,taxes,ZERO,
                self.trade_gross-fees-taxes,self.cfg.account_currency))
            self.entries=[];self.exits=[];self.trade_gross=ZERO
            # Prevent stale protection orders from reopening or affecting a later trade.
            for key,other in list(self.pending.items()):
                if other.intent.reduce_only:
                    del self.pending[key];self.log(key,"cancelled","position_flat")
        self.sample(price)

    @staticmethod
    def stop_hit(o,p):
        return p>=o.stop_price if o.side is Side.BUY else p<=o.stop_price
    @staticmethod
    def limit_hit(o,p):
        return p<=o.limit_price if o.side is Side.BUY else p>=o.limit_price

    def _point(self,price,phase,bar,path,*,at_open=False):
        # Stop orders (including reduce-only protective orders) precede other
        # simultaneous hits. FIFO within priority. No strategy callbacks mid-bar.
        ids=sorted(self.pending,key=lambda k:(
            not self.pending[k].intent.reduce_only,
            self.pending[k].intent.order_type not in (OrderType.STOP_MARKET,OrderType.STOP_LIMIT)))
        for i in ids:
            if i not in self.pending:continue
            p=self.pending[i];o=p.intent
            if o.order_type is OrderType.MARKET:
                if at_open:self._fill(p,price,phase,bar,path)
            elif o.order_type is OrderType.STOP_MARKET:
                if self.stop_hit(o,price):self._fill(p,price,phase,bar,path)
            elif o.order_type is OrderType.STOP_LIMIT:
                if not p.triggered and self.stop_hit(o,price):
                    p.triggered=True
                    self.log(i,"triggered","modeled_stop_limit")
                    # If marketable upon trigger, charge taker. Otherwise it rests.
                    if self.limit_hit(o,price):self._fill(p,price,phase,bar,path,limit=True)
                elif p.triggered and self.limit_hit(o,price):
                    self._fill(p,price,phase,bar,path,limit=True,resting=not at_open)
            elif self.limit_hit(o,price):
                self._fill(p,price,phase,bar,path,limit=True,resting=not at_open)
        self.sample(price)

    def _segment(self,a,b,idx,bar,path):
        if a==b:return
        # Events are processed in traversal order, not in order insertion order.
        # Triggered stop-limits can become eligible later on the same segment.
        current=a;phase=f"intrabar_segment_{idx}"
        self.now=bar.close_utc
        while current!=b:
            candidates=[]
            for p in self.pending.values():
                o=p.intent
                levels=[]
                if o.order_type is OrderType.STOP_MARKET or (
                        o.order_type is OrderType.STOP_LIMIT and not p.triggered):
                    levels.append(o.stop_price)
                elif o.order_type in (OrderType.LIMIT,OrderType.STOP_LIMIT):
                    levels.append(o.limit_price)
                candidates.extend(v for v in levels if
                    (current<v<=b if b>current else b<=v<current))
            if not candidates:break
            nxt=min(candidates) if b>current else max(candidates)
            self._point(nxt,phase,bar,path);current=nxt
        if current!=b:self._point(b,phase,bar,path)

    def _execute(self,bar):
        path=self.path
        if path=="adverse-first":
            direction=self.quantity
            if direction==0:
                first=next((p.intent for p in self.pending.values() if not p.intent.reduce_only),None)
                direction= D(-1) if first and first.side is Side.SELL else D(1)
            path="O-L-H-C" if direction>=0 else "O-H-L-C"
        self.now=bar.open_utc
        self.sample(bar.open)
        before=len(self.fills)
        self._point(bar.open,"open",bar,path,at_open=True)
        levels=(bar.open,bar.high,bar.low,bar.close) if path=="O-H-L-C" else (bar.open,bar.low,bar.high,bar.close)
        for i,(a,b) in enumerate(zip(levels,levels[1:]),1):
            self._segment(a,b,i,bar,path)
        self.now=bar.close_utc;self.sample(bar.close)
        return self.fills[before:]

    def _publish(self,bar):
        e=self.cfg.execution_timeframe.seconds;s=self.cfg.signal_timeframe.seconds
        self.history[e].append(bar)
        if e==s:return True
        self.group.append(bar)
        if len(self.group)!=s//e:return False
        a=self.group[0];b=self.group[-1]
        candle=Candle(bar.instrument,Timeframe(s),a.open_utc,b.close_utc,a.open,
                      max(c.high for c in self.group),min(c.low for c in self.group),
                      b.close,sum((c.volume for c in self.group),ZERO))
        self.history[s].append(candle);self.group.clear()
        return True

    def _record_month(self,bar):
        # Month labels use bar open local date. The final close of a month belongs
        # to the last interval in that month, not the next month's first interval.
        m=bar.open_utc.astimezone(self.tz).strftime("%Y-%m")
        if self.month is not None and m!=self.month:
            self._finish_month()
            self.month_open=self.month_close
        self.month=m;self.month_close=self.equity(bar.close)

    def _finish_month(self):
        if self.month is None:return
        p=self.month_close-self.month_open
        r=p/self.month_open*100 if self.month_open>0 else None
        self.monthly.append(MonthlyResult(self.month,self.month_open,self.month_close,p,r))

    def run(self,candles):
        self.strategy.on_start(self.context)
        expected=self.cfg.start_utc
        self.curve.append(EquityPoint(expected,self.balance,self.balance,ZERO))
        for bar in candles:
            if not isinstance(bar,Candle) or bar.instrument!=self.cfg.instrument or bar.timeframe!=self.cfg.execution_timeframe:
                raise ValueError("execution candle identity mismatch")
            if bar.open_utc!=expected or bar.close_utc>self.cfg.end_utc:
                raise ValueError("noncontiguous or out-of-range candle stream")
            expected=bar.close_utc;self.bar_count+=1
            self.digest.update(canonical_bytes(bar));self.digest.update(b"\n")
            fills=self._execute(bar)
            complete=self._publish(bar)
            # These callbacks see only the now-complete bar and final bar position;
            # all submitted orders become eligible at the next bar.
            for f in fills:self.strategy.on_fill(self.context,f)
            self.strategy.on_execution(self.context)
            if complete:self.strategy.on_signal(self.context)
            self._record_month(bar)
            # Bounded result sampling: every signal close, not every execution minute.
            if complete:
                self.curve.append(EquityPoint(self.now,self.balance,self.equity(bar.close),self.quantity))
        if expected!=self.cfg.end_utc or not self.bar_count or self.group:
            raise ValueError("incomplete execution stream")
        self.active=False
        for i in list(self.pending):
            del self.pending[i];self.log(i,"expired","end_of_test")
        self.strategy.on_finish(self.context)
        self._finish_month()
        e=self.equity(self.mark);unreal=self.unrealized(self.mark)
        if self.balance != self.cfg.initial_equity+self.gross-self.fees-self.taxes:
            raise ArithmeticError("balance reconciliation failed")
        if e!=self.balance+unreal or sum((m.pnl for m in self.monthly),ZERO)!=e-self.cfg.initial_equity:
            raise ArithmeticError("equity/month reconciliation failed")
        return ScenarioResult(self.path,self.bar_count,self.digest.hexdigest(),self.cfg.initial_equity,e,self.balance,
            e-self.cfg.initial_equity,self.gross,self.fees,self.taxes,self.quantity,unreal,self.dd,
            tuple(self.trades),tuple(self.fills),tuple(self.evidence),tuple(self.orders),tuple(self.curve),tuple(self.monthly))
