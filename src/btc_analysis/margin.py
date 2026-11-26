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
