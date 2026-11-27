"""Explicit linear perpetual margin assumptions. Not a certified exchange model."""
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal as D
from .contracts import Candle, Instrument, MarginMode, dec, utc, ident, require, digest

ZERO=D(0)
BPS=D(10000)


@dataclass(frozen=True, slots=True)
class MarginProfile:
    profile_id: str
    instrument: Instrument
    effective_start: datetime
    effective_end: datetime
    source: str
    initial_rate_floor: D
    maintenance_rate: D
    max_notional: D
    liquidation_fee_bps: D
    funding_interval_seconds: int = 0
    funding_anchor_epoch: int = 0
    preliquidation_buffer_points: D = ZERO
    scalp_window_seconds: int = 0
    scalp_effective_start: datetime | None = None
    scalp_effective_end: datetime | None = None

    def __post_init__(self):
        ident(self.profile_id,"profile_id");ident(self.source,"source")
        utc(self.effective_start);utc(self.effective_end)
        require(self.effective_start<self.effective_end,"invalid profile interval")
        for k in ("initial_rate_floor","maintenance_rate","max_notional"):
            dec(getattr(self,k),k,positive=True)
        dec(self.liquidation_fee_bps,"liquidation_fee_bps",nonnegative=True)
        require(0<self.maintenance_rate<self.initial_rate_floor<=1,"invalid margin rates")
        require(self.liquidation_fee_bps<BPS,"invalid liquidation fee")
        require(type(self.funding_interval_seconds) is int and self.funding_interval_seconds>=0,
                "invalid funding interval")
        require(type(self.funding_anchor_epoch) is int,"invalid funding anchor")
        dec(self.preliquidation_buffer_points,"preliquidation buffer",nonnegative=True)
        require(type(self.scalp_window_seconds) is int and self.scalp_window_seconds in (0,1800),"unsupported scalp window")
        if self.scalp_window_seconds:
            utc(self.scalp_effective_start);utc(self.scalp_effective_end)
            require(self.instrument.symbol in ("BTCUSD","ETHUSD") and self.scalp_effective_start<self.scalp_effective_end,"invalid offer interval/instrument")
        else:require(self.scalp_effective_start is None and self.scalp_effective_end is None,"disabled offer must have no dates")

    def initial_rate(self,leverage):
        return max(self.initial_rate_floor,D(1)/leverage)

    def validate(self,cfg):
        require(cfg.instrument==self.instrument,"margin instrument mismatch")
        require(self.effective_start<=cfg.start_utc<cfg.end_utc<=self.effective_end,"profile does not cover run")
        require(cfg.margin_mode in (MarginMode.ISOLATED,MarginMode.CROSS),"portfolio/cash not modeled")
        require(D(1)/cfg.leverage>=self.initial_rate_floor,"leverage exceeds profile maximum")
        require(cfg.costs.include_liquidation,"leveraged simulation requires liquidation checks")
        require(not cfg.costs.include_spread,"historical spread model not implemented")
        require(self.initial_rate(cfg.leverage)>self.maintenance_rate,"initial margin must exceed maintenance")
        if cfg.costs.include_funding:
            step=cfg.execution_timeframe.seconds
            require(self.funding_interval_seconds>0 and self.funding_interval_seconds%step==0
                    and self.funding_anchor_epoch%step==0,"funding schedule must align with execution grid")

    def initial(self,notional,leverage):return notional*self.initial_rate(leverage)
    def maintenance(self,notional):return notional*self.maintenance_rate

    def is_funding_time(self,when):
        return self.funding_interval_seconds>0 and (
            int(when.timestamp())-self.funding_anchor_epoch)%self.funding_interval_seconds==0

    
@dataclass(frozen=True, slots=True)
class MarginTier:
    upper_notional: D
    initial_rate_floor: D
    maintenance_rate: D
    def __post_init__(self):
        for k in ("upper_notional","initial_rate_floor","maintenance_rate"):
            dec(getattr(self,k),k,positive=True)
        require(0<self.maintenance_rate<self.initial_rate_floor<=1,"invalid tier margin rates")


@dataclass(frozen=True, slots=True)
class TieredMarginProfile(MarginProfile):
    """Whole-position brackets, inclusive upper caps; explicit research assumptions."""
    tiers: tuple[MarginTier,...] = ()
    def __post_init__(self):
        MarginProfile.__post_init__(self)
        require(isinstance(self.tiers,tuple) and 1<=len(self.tiers)<=32
                and all(isinstance(t,MarginTier) for t in self.tiers),"invalid margin tier count")
        first=self.tiers[0]
        require(first.initial_rate_floor==self.initial_rate_floor and first.maintenance_rate==self.maintenance_rate,
                "first tier must match base rates")
        require(self.tiers[-1].upper_notional==self.max_notional,"last tier must equal notional cap")
        for a,b in zip(self.tiers,self.tiers[1:]):
            require(a.upper_notional<b.upper_notional and a.initial_rate_floor<=b.initial_rate_floor
                    and a.maintenance_rate<=b.maintenance_rate,"margin tiers must be ordered and nondecreasing")
    def tier(self,notional):
        require(0<=notional<=self.max_notional,"position outside supplied margin tiers")
        return next(t for t in self.tiers if notional<=t.upper_notional)
    def allows_leverage(self,notional,leverage):
        return D(1)/leverage>=self.tier(notional).initial_rate_floor
    def initial(self,notional,leverage):
        return notional*max(self.tier(notional).initial_rate_floor,D(1)/leverage)
    def maintenance(self,notional):
        return notional*self.tier(notional).maintenance_rate
    def protective_surplus(self,quantity,multiplier,mark):
        # Evaluate the actual bracket at the adverse buffered mark, including
        # discontinuous rate changes. Never extrapolate beyond supplied cap.
        size=abs(quantity)*multiplier
        sign=D(1) if quantity>0 else D(-1)
        adverse=max(ZERO,min(self.max_notional/size,mark-sign*self.preliquidation_buffer_points))
        current=size*mark
        return max(ZERO,size*abs(mark-adverse)+self.maintenance(min(self.max_notional,size*adverse))-self.maintenance(current))


@dataclass(frozen=True, slots=True)
class FundingSettlement:
    event_utc: datetime
    rate: D  # fraction; positive longs pay, negative longs receive
    reference_mark: D
    source_id: str
    def __post_init__(self):
        utc(self.event_utc);dec(self.rate,"funding rate")
        dec(self.reference_mark,"funding mark",positive=True);ident(self.source_id,"funding source")


@dataclass(frozen=True, slots=True)
class RiskBar:
    mark: Candle
    funding: FundingSettlement | None = None


@dataclass(frozen=True, slots=True)
class FundingRecord:
    event_utc: datetime
    quantity: D
    rate: D
    reference_mark: D
    paid: D
    source_id: str


@dataclass(frozen=True, slots=True)
class LiquidationRecord:
    event_utc: datetime
    mark: D
    collateral_equity: D
    maintenance: D
    quantity: D
    phase: str


def funding_payment(quantity,multiplier,rate,mark):
    return quantity*multiplier*rate*mark


def collateral_equity(mode,balance,isolated_collateral,unrealized):
    if mode is MarginMode.ISOLATED:return isolated_collateral+unrealized
    if mode is MarginMode.CROSS:return balance+unrealized
    raise ValueError("unsupported margin mode")
