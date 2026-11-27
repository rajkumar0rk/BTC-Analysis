"""Reference event simulator for single-instrument linear perpetual research.

Optional explicit M5 margin, mark and funding scenario; no arbitrary Python sandbox or orderbook.
Only trusted strategy factories. Source factory must replay identical completed bars.
The execution clock is deterministic; intrabar prices are scenarios, not tick evidence.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from decimal import Decimal as D, localcontext, ROUND_CEILING, ROUND_FLOOR
from hashlib import sha256
from typing import Callable, Iterable
from zoneinfo import ZoneInfo

from ..contracts import (AssetClass, BacktestConfig, Candle, ClosedTrade, Fill,
    IntrabarPolicy, MarginMode, OrderIntent, OrderType, Side, Timeframe, DataKind)
from ..serialization import canonical_bytes, fingerprint

from ..indicators import IndicatorBook, IndicatorSpec
from ..exit_controls import validate_exit_controls,validate_bracket,validate_dynamic_trailing,atr_trailing_spec

from ..margin import (MarginProfile, RiskBar, FundingSettlement, FundingRecord,
    LiquidationRecord, funding_payment, collateral_equity)

ENGINE_VERSION = "m5-reference-1"
ZERO = D(0)
BPS = D(10000)
MAX_HISTORY = 4096
MAX_PENDING = 256
MAX_EVENTS = 1_000_000
MAX_BARS = 5_000_000


class BaseStrategy:
    """Convenience lifecycle methods; trusted subclasses override as needed."""
    def indicators(self): return ()
    def extra_timeframes(self): return ()
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
    warmup_bars: int
    warmup_candle_sha256: str | None
    indicator_specs: tuple[IndicatorSpec, ...]
    extra_timeframes: tuple[Timeframe, ...]
    funding_paid: D
    funding_records: tuple[FundingRecord, ...]
    liquidations: tuple[LiquidationRecord, ...]
    risk_stream_sha256: str | None


@dataclass(frozen=True, slots=True)
class BacktestResult:
    engine_version: str
    config_sha256: str
    declared_dataset_sha256s: tuple[str, ...]
    scenarios: tuple[ScenarioResult, ...]
    worst_path: str
    limitations: tuple[str, ...]
    margin_profile_sha256: str | None

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
    def indicator(self, name, timeframe, parameters=None):
        values=self.indicator_history(name,timeframe,parameters,limit=1)
        return values[-1] if values else None
    def indicator_history(self,name,timeframe,parameters=None,*,limit=2):
        return self._sim.indicators.get(name,timeframe,parameters,limit)
    def submit(self, intent): self._sim.submit(intent)
    def cancel(self, intent_id): self._sim.cancel(intent_id)


def _validate(cfg, profile=None, session_reference=False):
    dated=cfg.instrument.asset_class is AssetClass.FUTURE
    if dated:
        if session_reference is not True or profile is not None or cfg.end_utc>=cfg.instrument.expiry_utc:
            raise ValueError("dated futures require a trusted single-session reference, strictly before expiry")
    elif cfg.instrument.asset_class is not AssetClass.CRYPTO_PERPETUAL or session_reference:
        raise ValueError("unsupported instrument/session reference")
    if not (cfg.account_currency == cfg.instrument.quote_currency == cfg.instrument.settlement_currency):
        raise ValueError("M3 requires same quote, settlement and account currency")
    if profile is None:
        if cfg.leverage != 1 or cfg.margin_mode not in (MarginMode.ISOLATED, MarginMode.CROSS):
            raise ValueError("leverage requires explicit margin profile and mark data")
        if cfg.costs.include_funding or cfg.costs.include_spread or cfg.costs.include_liquidation:
            raise ValueError("risk inputs require explicit margin profile")
    else:
        if not isinstance(profile,MarginProfile):raise ValueError("expected MarginProfile")
        profile.validate(cfg)
    if cfg.costs.slippage_bps >= BPS:
        raise ValueError("slippage must be below 10000 bps")
    if cfg.intrabar_policy not in (IntrabarPolicy.STOP_FIRST, IntrabarPolicy.BOTH_PATHS):
        raise ValueError("tick sequence not supported by candle simulator")
    if (not dated and cfg.calendar_id != "crypto-24x7") or (dated and not cfg.calendar_id.startswith("reviewed-session:")) or cfg.allow_data_gaps:
        raise ValueError("M3 requires gap-free continuous UTC data")
    expected_kinds={DataKind.OHLCV}
    if profile is not None:expected_kinds.add(DataKind.MARK)
    if cfg.costs.include_funding:expected_kinds.add(DataKind.FUNDING)
    if len(cfg.datasets)!=len(expected_kinds) or {d.kind for d in cfg.datasets}!=expected_kinds:
        raise ValueError("expected one dataset for each enabled data kind")
    if profile is not None and next(d for d in cfg.datasets if d.kind is DataKind.MARK).timeframe!=cfg.execution_timeframe:
        raise ValueError("mark data must match execution timeframe")
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
                 linear_contract: bool = False, dataset_manifest_sha256: str,
                 warmup_start_utc: datetime | None = None,
                 warmup_factory: Callable[[], Iterable[Candle]] | None = None,
                 margin_profile: MarginProfile | None = None,
                 risk_factory: Callable[[], Iterable[RiskBar]] | None = None,
                 risk_manifest_sha256s: tuple[str, ...] = (),
                 session_reference: bool = False, archive_factory=None, indicator_book_factory=None) -> BacktestResult:
    """Run fresh strategies for each scenario. No mutation of input config or source.

    The caller is a trusted adapter responsible for the declared source manifest and
    strategy code/parameter hashes. The observed candle stream is independently hashed.
    BOTH_PATHS runs separate full O-H-L-C and O-L-H-C simulations, not per-bar
    oracle selection. STOP_FIRST chooses an adverse-first path at each bar based
    on starting position or first pending entry direction (a heuristic).
    """
    _validate(config,margin_profile,session_reference)
    if archive_factory is not None and (session_reference or (margin_profile is not None and not getattr(archive_factory,"supports_risk",False))):
        raise ValueError("archive adapter does not support requested risk/session model")
    execution=next(d for d in config.datasets if d.kind is DataKind.OHLCV)
    if (margin_profile is None)!=(risk_factory is None):
        raise ValueError("margin profile and risk stream required together")
    expected_risk=tuple(d.manifest_sha256 for d in config.datasets if d.kind is not DataKind.OHLCV)
    if risk_manifest_sha256s!=expected_risk:
        raise ValueError("risk manifest mismatch")
    if (warmup_start_utc is None)!=(warmup_factory is None):
        raise ValueError("warmup start and factory must be supplied together")
    if warmup_start_utc is not None:
        from ..contracts import utc
        utc(warmup_start_utc)
        if not execution.start_utc<=warmup_start_utc<config.start_utc:
            raise ValueError("warmup outside pinned dataset")
        if (config.start_utc-warmup_start_utc).total_seconds()//config.execution_timeframe.seconds>MAX_BARS:
            raise ValueError("warmup bar quota exceeded")
    if linear_contract is not True:
        raise ValueError("trusted adapter must attest a linear contract")
    if dataset_manifest_sha256 != execution.manifest_sha256:
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
            sim = Simulator(config, strategy, path, margin_profile,
                            iter(risk_factory()) if risk_factory is not None else None)
            if indicator_book_factory is not None:
                sim.indicators=indicator_book_factory(sim.definitions,MAX_HISTORY)
            if warmup_factory is not None:
                sim.warmup(warmup_start_utc,warmup_factory())
            if archive_factory is None:
                out.append(sim.run(candle_factory()))
            else:
                with archive_factory(path) as archive:
                    archive.bind(sim)
                    out.append(sim.run(candle_factory(),archive=archive))
    if len({(x.observed_candle_sha256,x.warmup_candle_sha256,x.risk_stream_sha256) for x in out}) != 1:
        raise ValueError("scenario candle streams differ")
    if len({(x.indicator_specs,x.extra_timeframes) for x in out}) != 1:
        raise ValueError("scenario strategy declarations differ")
    worst = min(out,key=lambda x:(x.final_equity,x.path))
    return BacktestResult(ENGINE_VERSION,fingerprint(config),
        tuple(d.manifest_sha256 for d in config.datasets),tuple(out),worst.path,(
        "Trusted strategy and source adapters only; no untrusted Python execution.",
        ("Linear 1x collateral cap only; no exchange margin, funding, spread or liquidation." if margin_profile is None else
         ("Single unhedged perpetual stress-margin reference; no exchange portfolio certification." if config.margin_mode is MarginMode.PORTFOLIO else ("Explicit single-position whole-notional bracket simulation; not certified exchange rules." if getattr(margin_profile,"tiers",()) else "Explicit single-position fixed-tier linear margin simulation; not certified exchange rules."))),
        ("No risk stream used." if margin_profile is None else
         ("Mark-first paired OHLC vertices; bounded partial reductions with full fallback at modeled mark, adverse slippage and explicit fee; strategy halted after first step." if getattr(margin_profile,"partial_policy",None) else "Mark-first paired OHLC vertices; liquidation modeled as full close at mark with adverse slippage and explicit fee; halt after liquidation.")),
        ("Funding excluded." if not config.costs.include_funding else
         "Funding supplied as explicit settlement events, applied before opening orders at each boundary."),
        "OHLC paths are assumptions; limit touch assumes full fill, no volume or queue modeling.",
        "Intrabar fills have bar-close availability timestamps, not observed tick timestamps.",
        "Adverse-first is a heuristic; two fixed paths are scenarios, not worst-case bounds.",
        ("Optional conservative single-entry full-close fee waiver with explicit effective period; no voucher or partial-close modeling." if margin_profile is not None and margin_profile.scalp_window_seconds else "Fees use configured bps; no venue-specific rebates, offers or fee rounding."),
        "No forced terminal liquidation; open positions marked at final close.",
        ("Dated contract reference: single reviewed continuous session before expiry; no rollover, delivery or settlement." if session_reference else "Continuous perpetual reference."),
        "Drawdown sampled at modeled price events; not actual tick drawdown.",
        "Strategy callbacks are close-time; on_fill observes final bar state, not intrabar state.",
        "Caller attests pinned source and code; observed candle hash recorded independently.",
        "Indicators use explicit documented seeds and completed UTC-aligned bars; no external library parity claim.",
        "Warmup bars initialize indicators/history only, without orders, callbacks or evaluation P&L.",
        ("Partial liquidation is a research model; no exchange-certified liquidation or full portfolio margin." if getattr(margin_profile,"partial_policy",None) else "Mark-vertex pre-liquidation buffer is modeled only; gaps can liquidate first, protective close halts the run. No historical bid-ask, partial liquidation or portfolio margin." if margin_profile is not None and margin_profile.preliquidation_buffer_points else "No historical bid-ask, partial exchange liquidation, fee offers or portfolio margin."),
    )+(("No multi-position portfolio offsets, options, order reservations or delta hedging.",) if config.margin_mode is MarginMode.PORTFOLIO and getattr(margin_profile,"partial_policy",None) else ("No multi-position portfolio offsets, options, order reservations, delta hedging or partial liquidation.",) if config.margin_mode is MarginMode.PORTFOLIO else ())+(("Partial reference only; residual exposure stays risk-monitored after strategy halt; no exchange-certified sizing or recovery.",) if getattr(margin_profile,"partial_policy",None) else ()),fingerprint(margin_profile) if margin_profile is not None else None)


class Simulator:
    def __init__(self,cfg,strategy,path,profile=None,risk_stream=None):
        self.cfg=cfg; self.strategy=strategy; self.path=path
        self.now=cfg.start_utc; self.mark=None
        self.balance=cfg.initial_equity; self.quantity=ZERO
        self.lots=deque(); self.entries=[]; self.exits=[]; self.trade_gross=ZERO
        self.gross=ZERO; self.fees=ZERO; self.taxes=ZERO
        self.profile=profile;self.risk_stream=risk_stream;self.risk_digest=sha256()
        self.risk_mark=None;self.funding=ZERO;self.trade_funding=ZERO;self.iso_adjustment=ZERO
        self.funding_records=[];self.liquidations=[];self.halted=False;self.liquidating=False
        self.pending={}; self.seen=set(); self.orders=[]; self.fills=[]; self.evidence=[]
        self.trailing_policy=getattr(strategy,"trailing_stop_points",None)
        self.lock_policy=getattr(strategy,"profit_lock_points",None)
        validate_exit_controls(getattr(strategy,"fixed_point_bracket",None),self.trailing_policy,self.lock_policy,cfg.instrument.tick_size)
        self.percent_policy=getattr(strategy,"trailing_stop_pct",None)
        self.atr_policy=getattr(strategy,"trailing_stop_atr",None)
        validate_dynamic_trailing(getattr(strategy,"fixed_point_bracket",None),self.trailing_policy,self.percent_policy,self.atr_policy)
        self.atr_spec=atr_trailing_spec(self.atr_policy)
        self.managed_stop=None
        self.trades=[]; self.curve=[]; self.monthly=[]
        self.peak=cfg.initial_equity; self.dd=ZERO
        self.definitions=getattr(strategy,"indicators",lambda:())()
        if self.atr_spec is not None and self.atr_spec not in self.definitions:self.definitions=(*self.definitions,self.atr_spec)
        self.indicators=IndicatorBook(self.definitions,MAX_HISTORY)
        self.extra_frames=getattr(strategy,"extra_timeframes",lambda:())()
        if not isinstance(self.extra_frames,tuple) or len(self.extra_frames)>16 or any(not isinstance(t,Timeframe) for t in self.extra_frames):
            raise ValueError("extra timeframes must be a bounded tuple of Timeframe")
        e=cfg.execution_timeframe.seconds
        frames={e,cfg.signal_timeframe.seconds,*[t.seconds for t in self.extra_frames],*[d.timeframe.seconds for d in self.definitions]}
        if len(frames)>18:raise ValueError("too many strategy timeframes")
        for seconds in frames:
            if seconds%e or seconds//e>MAX_HISTORY or any(int(t.timestamp())%seconds for t in (cfg.start_utc,cfg.end_utc)):
                raise ValueError("strategy timeframe incompatible with execution/range")
        self.history={k:deque(maxlen=MAX_HISTORY) for k in sorted(frames)}
        self.groups={k:[] for k in self.history if k!=e}
        self.context=Context(self)
        self.warmup_bars=0;self.warmup_hash=None
        self.active=True; self.bar_count=0; self.digest=sha256()
        self.mult=cfg.instrument.contract_multiplier
        self.tz=ZoneInfo(cfg.reporting_timezone)
        self.month=None; self.month_open=cfg.initial_equity; self.month_close=cfg.initial_equity

    def unrealized(self, price):
        if self.profile is not None:price=self.risk_mark
        if price is None: return ZERO
        sign=D(1) if self.quantity>0 else D(-1)
        return sum(((price-p)*q*self.mult*sign for q,p in self.lots),ZERO)

    def equity(self,price): return self.balance+self.unrealized(price)

    def sample(self, price):
        self.mark=self.risk_mark if self.profile is not None else price; e=self.equity(price)
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
        if not self.active or self.halted:
            self.log(i,"rejected","liquidation_halt" if self.halted else "run_finished",intent); return
        if intent.instrument!=self.cfg.instrument or intent.decision_utc!=self.now:
            self.log(i,"rejected","instrument_or_decision_time_mismatch",intent); return
        if len(self.pending)>=MAX_PENDING:
            self.log(i,"rejected","pending_order_limit",intent); return
        self.pending[i]=Pending(intent)
        self.log(i,"accepted","eligible_next_execution_bar",intent)

    def cancel(self,i):
        if self.managed_stop is not None and i==self.managed_stop[0]:
            self.log(i,"cancel_rejected","engine_managed_protection");return
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
        rate=(self.profile.liquidation_fee_bps if self.liquidating else
              self.cfg.costs.maker_bps if resting else self.cfg.costs.taker_bps)
        # Conservative single-entry/full-close waiver. Intrabar evidence only
        # bounds execution time, so use earliest possible entry for eligibility.
        if (self.profile is not None and self.profile.scalp_window_seconds and opposite
                and not self.liquidating and len(self.entries)==1 and not self.exits
                and qty==abs(self.quantity)):
            entry=self.entries[0]
            earliest=entry.event_utc-timedelta(seconds=self.cfg.execution_timeframe.seconds)
            if (self.profile.scalp_effective_start<=earliest<=self.now<self.profile.scalp_effective_end
                    and (self.now-earliest).total_seconds()<=self.profile.scalp_window_seconds):
                rate=ZERO
        fee=price*qty*self.mult*rate/BPS; tax=fee*self.cfg.costs.tax_rate
        if not opposite:
            if self.profile is None:
                e=self.equity(price)
                allowed=(abs(self.quantity)+qty)*price*self.mult+fee+tax<=e
                detail="baseline_collateral_cap"
            else:
                notional=(abs(self.quantity)+qty)*max(price,self.risk_mark)*self.mult
                tiered=bool(getattr(self.profile,"tiers",()))
                allowed=notional<=self.profile.max_notional
                if allowed and tiered:
                    allowed=self.profile.allows_leverage(notional,self.cfg.leverage)
                if allowed and self.cfg.margin_mode is MarginMode.ISOLATED:
                    if tiered:
                        # Re-rate the whole entry-cost basis when adding lots.
                        basis=sum((q*p*self.mult for q,p in self.lots),ZERO)
                        added=qty*price*self.mult
                        allowed=basis+added<=self.profile.max_notional
                        if allowed:
                            required=self.profile.initial(basis+added,self.cfg.leverage)-self.profile.initial(basis,self.cfg.leverage)+fee+tax
                            allowed=required<=self.balance-self.isolated_collateral()
                    else:
                        required=self.profile.initial(qty*price*self.mult,self.cfg.leverage)+fee+tax
                        allowed=required<=self.balance-self.isolated_collateral()
                elif allowed:
                    required=self.profile.initial(notional,self.cfg.leverage)+fee+tax
                    allowed=required<=self.equity(self.risk_mark)
                detail="initial_margin_or_notional_cap"
            if not allowed:
                del self.pending[i];self.log(i,"rejected",detail);return
        if len(self.fills)>=MAX_EVENTS: raise ValueError("fill event quota exceeded")
        del self.pending[i]
        f=Fill(f"fill-{len(self.fills)+1}",i,o.instrument,self.now,o.side,qty,price,fee,tax,
               self.cfg.account_currency,o.reason)
        self.fills.append(f)
        self.evidence.append(ExecutionEvidence(f.fill_id,bar.open_utc,bar.close_utc,phase,ref,path))
        self.log(i,"filled","reduce_only_clipped" if qty!=o.quantity else "modeled_full_fill")
        self.balance-=fee+tax;self.fees+=fee;self.taxes+=tax
        if opposite:
            if self.profile is not None and self.cfg.margin_mode is MarginMode.ISOLATED:
                self.iso_adjustment*= (abs(self.quantity)-qty)/abs(self.quantity)
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
            self.managed_stop=None
            allfills=self.entries+self.exits
            fees=sum((x.fee for x in allfills),ZERO);taxes=sum((x.tax for x in allfills),ZERO)
            self.trades.append(ClosedTrade(f"trade-{len(self.trades)+1}",tuple(self.entries),tuple(self.exits),
                self.entries[0].reason,self.exits[-1].reason,self.trade_gross,fees,taxes,self.trade_funding,
                self.trade_gross-fees-taxes-self.trade_funding,self.cfg.account_currency))
            self.entries=[];self.exits=[];self.trade_gross=ZERO;self.trade_funding=ZERO;self.iso_adjustment=ZERO
            # Prevent stale protection orders from reopening or affecting a later trade.
            for key,other in list(self.pending.items()):
                if other.intent.reduce_only:
                    del self.pending[key];self.log(key,"cancelled","position_flat")
        self.sample(price)
        if self.profile is not None and not self.liquidating:
            self.check_liquidation(bar,phase,path,trade_ref=ref)
        bracket=getattr(self.strategy,"fixed_point_bracket",None)
        if bracket is not None and not opposite and self.quantity and not self.halted:
            if self.quantity!=sign*qty or phase!="open" or o.order_type is not OrderType.MARKET:
                raise ValueError("fixed-point bracket requires a single market entry at open")
            self.install_fixed_bracket(f,ref,phase,bar,path,bracket)

    def install_fixed_bracket(self,fill,ref,phase,bar,path,bracket):
        # Strategies request exact price-point distances; do not
        # silently round them into a different risk/reward.
        stop_points,target_points=bracket
        tick=self.cfg.instrument.tick_size
        validate_bracket(bracket,tick)
        direction=D(1) if self.quantity>0 else D(-1)
        stop=fill.price-direction*stop_points
        target=fill.price+direction*target_points if target_points is not None else None
        if stop<=0 or target is not None and target<=0:raise ValueError("nonpositive fixed-point bracket price")
        side=Side.SELL if direction>0 else Side.BUY
        stop_key="__fixed_stop_"+fill.fill_id
        target_key="__fixed_target_"+fill.fill_id
        for key,kind,reason,limit,trigger in (
            (stop_key,OrderType.STOP_MARKET,"fixed_point_stop",None,stop),
            (target_key,OrderType.LIMIT,"fixed_point_target",target,None)):
            if key==target_key and target is None:continue
            self.submit(OrderIntent(key,self.cfg.instrument,self.now,side,kind,abs(self.quantity),
                                    reason,limit,trigger,True))
            if key not in self.pending:raise ValueError("fixed-point protective order rejected")
        if any(policy is not None for policy in (self.trailing_policy,self.lock_policy,self.percent_policy,self.atr_policy)):
            self.managed_stop=(stop_key,fill.price,direction,fill.price)
        # At the entry open, adverse execution slippage may already place
        # the raw trade reference beyond the stop. Check stop first.
        p=self.pending[stop_key]
        if self.stop_hit(p.intent,ref):
            self._fill(p,ref,phase,bar,path)
        elif target_key in self.pending and self.limit_hit(self.pending[target_key].intent,ref):
            self._fill(self.pending[target_key],ref,phase,bar,path,limit=True)

    def ratchet_protection(self,price):
        if self.managed_stop is None or not self.quantity or self.halted:return
        key,entry,direction,best=self.managed_stop
        if key not in self.pending:raise ValueError("managed protective stop missing")
        # A visited vertex is observable; never inspect future high/low.
        if direction*(price-best)<=0:return
        best=price
        self.managed_stop=(key,entry,direction,best)
        gain=direction*(best-entry)
        p=self.pending[key];old=p.intent.stop_price
        desired=old;reason=p.intent.reason
        if self.lock_policy is not None:
            activation,locked=self.lock_policy
            candidate=entry+direction*locked
            if gain>=activation and direction*(candidate-desired)>0:
                desired=candidate;reason="profit_lock_stop"
        if self.trailing_policy is not None:
            activation,distance=self.trailing_policy
            if gain>=activation:
                candidate=best-direction*distance
                # Round away from best, preserving at least the requested distance.
                candidate=self.round_price(candidate,Side.SELL if direction>0 else Side.BUY)
                if direction*(candidate-desired)>0:
                    desired=candidate;reason="trailing_point_stop"
        if self.percent_policy is not None:
            activation,distance=self.percent_policy
            if gain>=entry*activation/100:
                candidate=self.round_price(best*(1-direction*distance/100),Side.SELL if direction>0 else Side.BUY)
                if direction*(candidate-desired)>0:
                    desired=candidate;reason="trailing_percent_stop"
        if self.atr_policy is not None:
            activation,tf,period,multiplier=self.atr_policy
            if gain>=entry*activation/100:
                values=self.indicators.get("atr.value",tf,{"period":period},1)
                atr=values[-1] if values else None
                if atr is not None and atr>0:
                    candidate=self.round_price(best-direction*atr*multiplier,Side.SELL if direction>0 else Side.BUY)
                    if direction*(candidate-desired)>0:
                        desired=candidate;reason="trailing_atr_stop"
        if direction*(desired-old)>0 and desired>0:
            p.intent=replace(p.intent,stop_price=desired,reason=reason,decision_utc=self.now)
            self.log(key,"amended",reason,p.intent)

    def isolated_collateral(self):
        if self.profile is None:return ZERO
        return self.profile.initial(sum((q*p*self.mult for q,p in self.lots),ZERO),self.cfg.leverage)+self.iso_adjustment

    def check_liquidation(self,bar,phase,path,trade_ref=None):
        if self.profile is None or not self.quantity or self.liquidating:return
        mark=self.risk_mark
        notional=abs(self.quantity)*mark*self.mult
        if notional>self.profile.max_notional:
            raise ValueError("position exceeds supplied margin notional cap; cannot extrapolate")
        equity=collateral_equity(self.cfg.margin_mode,self.balance,self.isolated_collateral(),self.unrealized(mark))
        maintenance=self.profile.maintenance(notional)
        liquidation=equity<=maintenance
        # Fixed price-point buffer expressed as collateral surplus at this mark.
        # At a gap below maintenance liquidation wins; no guaranteed stop fill.
        sign=D(1) if self.quantity>0 else D(-1)
        buffer=(self.profile.protective_surplus(self.quantity,self.mult,mark) if hasattr(self.profile,"protective_surplus") else
                abs(self.quantity)*self.mult*self.profile.preliquidation_buffer_points*(1-sign*self.profile.maintenance_rate))
        protective=(not liquidation and trade_ref is not None and buffer>0 and equity-maintenance<=buffer)
        if not liquidation and not protective:return
        self.now=bar.open_utc if phase=="open" else bar.close_utc
        reason="modeled_liquidation" if liquidation else "modeled_preliquidation_stop"
        for key in list(self.pending):
            del self.pending[key];self.log(key,"cancelled",reason)
        policy=getattr(self.profile,"partial_policy",None)
        if liquidation and policy is not None:
            for _ in range(policy.max_steps):
                if equity<=0:break
                lot=self.cfg.instrument.lot_size
                qty=(abs(self.quantity)*policy.reduction_fraction/lot).to_integral_value(rounding=ROUND_CEILING)*lot
                if qty>=abs(self.quantity):break
                self.risk_close(bar,phase,path,mark,qty,True,"modeled_partial_liquidation",equity,maintenance)
                equity=self.equity(mark)
                maintenance=self.profile.maintenance(abs(self.quantity)*mark*self.mult)
                if equity>=maintenance*policy.recovery_ratio:return
        self.risk_close(bar,phase,path,mark if liquidation else trade_ref,abs(self.quantity),liquidation,reason,equity,maintenance)

    def risk_close(self,bar,phase,path,ref,qty,liquidation,reason,equity,maintenance):
        if liquidation:
            if len(self.liquidations)>=MAX_EVENTS:raise ValueError("liquidation event quota exceeded")
            self.liquidations.append(LiquidationRecord(self.now,self.risk_mark,equity,maintenance,self.quantity,phase))
        key=f"__risk_close_{len(self.fills)+1}"
        if key in self.seen:raise ValueError("reserved liquidation intent ID collision")
        self.seen.add(key)
        side=Side.SELL if self.quantity>0 else Side.BUY
        o=OrderIntent(key,self.cfg.instrument,self.now,side,OrderType.MARKET,qty,reason,reduce_only=True)
        p=Pending(o);self.pending[key]=p;self.log(key,"accepted",reason,o)
        self.liquidating=liquidation;self.halted=True
        try:self._fill(p,ref,phase,bar,path)
        finally:self.liquidating=False

    def risk_open(self,bar,risk,path):
        if not isinstance(risk,RiskBar):raise ValueError("missing risk bar")
        m=risk.mark
        if (m.instrument!=bar.instrument or m.timeframe!=bar.timeframe or
                m.open_utc!=bar.open_utc or m.close_utc!=bar.close_utc):
            raise ValueError("mark stream alignment mismatch")
        required=self.cfg.costs.include_funding and self.profile.is_funding_time(bar.open_utc)
        if required!=(risk.funding is not None):raise ValueError("missing or unexpected funding settlement")
        self.risk_digest.update(canonical_bytes(risk));self.risk_digest.update(b"\n")
        self.risk_mark=m.open
        if risk.funding is not None:
            f=risk.funding
            if not isinstance(f,FundingSettlement) or f.event_utc!=bar.open_utc:
                raise ValueError("funding settlement timestamp mismatch")
            paid=funding_payment(self.quantity,self.mult,f.rate,f.reference_mark)
            self.balance-=paid;self.funding+=paid;self.trade_funding+=paid
            if self.cfg.margin_mode is MarginMode.ISOLATED:self.iso_adjustment-=paid
            self.funding_records.append(FundingRecord(f.event_utc,self.quantity,f.rate,f.reference_mark,paid,f.source_id))
        self.sample(m.open);self.check_liquidation(bar,"open",path,trade_ref=bar.open)

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
        self.ratchet_protection(price)
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

    def _execute(self,bar,risk=None):
        path=self.path
        if path=="adverse-first":
            direction=self.quantity
            if direction==0:
                first=next((p.intent for p in self.pending.values() if not p.intent.reduce_only),None)
                direction= D(-1) if first and first.side is Side.SELL else D(1)
            path="O-L-H-C" if direction>=0 else "O-H-L-C"
        self.now=bar.open_utc
        before=len(self.fills)
        if self.profile is not None:self.risk_open(bar,risk,path)
        self.sample(bar.open)
        self._point(bar.open,"open",bar,path,at_open=True)
        levels=(bar.open,bar.high,bar.low,bar.close) if path=="O-H-L-C" else (bar.open,bar.low,bar.high,bar.close)
        mark_levels=None if risk is None else ((risk.mark.open,risk.mark.high,risk.mark.low,risk.mark.close) if path=="O-H-L-C" else (risk.mark.open,risk.mark.low,risk.mark.high,risk.mark.close))
        for i,(a,b) in enumerate(zip(levels,levels[1:]),1):
            if mark_levels is not None:
                # Explicit mark-first stress ordering: independent source candles
                # cannot establish exact chronological alignment with trades.
                self.now=bar.close_utc;self.risk_mark=mark_levels[i]
                self.sample(self.risk_mark);self.check_liquidation(bar,f"mark_vertex_{i}",path,trade_ref=b)
            self._segment(a,b,i,bar,path)
        self.now=bar.close_utc;self.sample(bar.close)
        return self.fills[before:]

    def _publish(self,bar):
        e=self.cfg.execution_timeframe.seconds;s=self.cfg.signal_timeframe.seconds
        self.history[e].append(bar);self.indicators.update(bar)
        custom_update=getattr(self.strategy,"on_completed_candle",None)
        if custom_update is not None:custom_update(bar)
        signal_complete=e==s
        for seconds,group in self.groups.items():
            group.append(bar)
            if len(group)!=seconds//e:continue
            a=group[0];b=group[-1]
            candle=Candle(bar.instrument,Timeframe(seconds),a.open_utc,b.close_utc,a.open,
                          max(c.high for c in group),min(c.low for c in group),
                          b.close,sum((c.volume for c in group),ZERO))
            self.history[seconds].append(candle);self.indicators.update(candle);group.clear()
            if custom_update is not None:custom_update(candle)
            if seconds==s:signal_complete=True
        return signal_complete

    def warmup(self,start,candles):
        if start.microsecond or any(int(start.timestamp())%seconds for seconds in self.history):
            raise ValueError("warmup must align to every strategy timeframe")
        expected=start;digest=sha256()
        for bar in candles:
            if (not isinstance(bar,Candle) or bar.instrument!=self.cfg.instrument or
                    bar.timeframe!=self.cfg.execution_timeframe or bar.open_utc!=expected or
                    bar.close_utc>self.cfg.start_utc):
                raise ValueError("invalid warmup stream")
            expected=bar.close_utc;self.warmup_bars+=1
            digest.update(canonical_bytes(bar));digest.update(b"\n")
            self._publish(bar)
        if expected!=self.cfg.start_utc or not self.warmup_bars or any(self.groups.values()):
            raise ValueError("incomplete warmup stream")
        self.warmup_hash=digest.hexdigest()

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

    def run(self,candles,*,archive=None):
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
            risk=next(self.risk_stream,None) if self.risk_stream is not None else None
            fills=self._execute(bar,risk)
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
        if self.risk_stream is not None and next(self.risk_stream,None) is not None:
            raise ValueError("excess risk stream data")
        if expected!=self.cfg.end_utc or not self.bar_count or any(self.groups.values()):
            raise ValueError("incomplete execution stream")
        self.active=False
        for i in list(self.pending):
            del self.pending[i];self.log(i,"expired","end_of_test")
        self.strategy.on_finish(self.context)
        self._finish_month()
        e=self.equity(self.mark);unreal=self.unrealized(self.mark)
        if self.balance != self.cfg.initial_equity+self.gross-self.fees-self.taxes-self.funding:
            raise ArithmeticError("balance reconciliation failed")
        if e!=self.balance+unreal or sum((m.pnl for m in self.monthly),ZERO)!=e-self.cfg.initial_equity:
            raise ArithmeticError("equity/month reconciliation failed")
        if archive is not None:return archive.finish(self,e,unreal)
        return ScenarioResult(self.path,self.bar_count,self.digest.hexdigest(),self.cfg.initial_equity,e,self.balance,
            e-self.cfg.initial_equity,self.gross,self.fees,self.taxes,self.quantity,unreal,self.dd,
            tuple(self.trades),tuple(self.fills),tuple(self.evidence),tuple(self.orders),tuple(self.curve),tuple(self.monthly),
            self.warmup_bars,self.warmup_hash,self.definitions,self.extra_frames,
            self.funding,tuple(self.funding_records),tuple(self.liquidations),
            self.risk_digest.hexdigest() if self.profile is not None else None)
