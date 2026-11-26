"""Validated, immutable domain contracts (M1). Monetary values use Decimal.
A timestamp is the UTC availability time unless its field explicitly says otherwise.
Actual pricing, lot rounding, scheduling and margin calculations belong to future engines.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from enum import StrEnum
from typing import Literal
from zoneinfo import ZoneInfo
import re


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def utc(value: datetime) -> None:
    require(isinstance(value, datetime) and value.tzinfo is not None
            and value.utcoffset() == timedelta(0), "timestamp must be timezone-aware UTC")


def dec(value: Decimal, name: str, *, positive: bool = False,
        nonnegative: bool = False) -> None:
    require(isinstance(value, Decimal) and value.is_finite(), f"{name} must be a finite Decimal")
    if positive:
        require(value > 0, f"{name} must be positive")
    if nonnegative:
        require(value >= 0, f"{name} must be nonnegative")


def ident(value: str, name: str) -> None:
    require(isinstance(value, str) and bool(value.strip()) and len(value) <= 256,
            f"{name} must be a nonempty identifier (max 256 characters)")


def digest(value: str) -> None:
    require(isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None,
            "expected lowercase SHA-256")


def enum(value: object, kind: type[StrEnum]) -> None:
    require(isinstance(value, kind), f"expected {kind.__name__}")


class AssetClass(StrEnum):
    CRYPTO_PERPETUAL = "crypto_perpetual"
    FUTURE = "future"
    OPTION = "option"
    SPOT = "spot"


class Side(StrEnum):
    BUY = "buy"
    SELL = "sell"


class OrderType(StrEnum):
    MARKET = "market"
    LIMIT = "limit"
    STOP_MARKET = "stop_market"
    STOP_LIMIT = "stop_limit"


class MarginMode(StrEnum):
    CASH = "cash"
    ISOLATED = "isolated"
    CROSS = "cross"
    PORTFOLIO = "portfolio"


class IntrabarPolicy(StrEnum):
    STOP_FIRST = "stop_first"
    BOTH_PATHS = "both_paths"
    TICK_SEQUENCE = "tick_sequence"


class DataKind(StrEnum):
    OHLCV = "ohlcv"
    TRADES = "trades"
    QUOTES = "quotes"
    MARK = "mark"
    FUNDING = "funding"
    OPEN_INTEREST = "open_interest"


@dataclass(frozen=True, slots=True)
class Instrument:
    venue: str
    symbol: str
    asset_class: AssetClass
    quote_currency: str
    settlement_currency: str
    tick_size: Decimal
    lot_size: Decimal
    contract_multiplier: Decimal
    expiry_utc: datetime | None = None
    strike: Decimal | None = None
    option_right: Literal["call", "put"] | None = None

    def __post_init__(self) -> None:
        for n in ("venue", "symbol", "quote_currency", "settlement_currency"):
            ident(getattr(self, n), n)
        enum(self.asset_class, AssetClass)
        for n in ("tick_size", "lot_size", "contract_multiplier"):
            dec(getattr(self, n), n, positive=True)
        if self.asset_class in (AssetClass.FUTURE, AssetClass.OPTION):
            require(self.expiry_utc is not None, "dated derivatives require expiry")
            utc(self.expiry_utc)
        else:
            require(self.expiry_utc is None, "spot/perpetual cannot have expiry")
        if self.asset_class is AssetClass.OPTION:
            require(self.strike is not None and self.option_right in ("call", "put"),
                    "option requires strike and right")
            dec(self.strike, "strike", positive=True)
        else:
            require(self.strike is None and self.option_right is None,
                    "non-option cannot have strike or right")


@dataclass(frozen=True, slots=True)
class Timeframe:
    seconds: int

    def __post_init__(self) -> None:
        require(type(self.seconds) is int and 0 < self.seconds <= 31_536_000,
                "timeframe must be positive integer seconds")


@dataclass(frozen=True, slots=True)
class Candle:
    instrument: Instrument
    timeframe: Timeframe
    open_utc: datetime
    close_utc: datetime  # exclusive right edge; only visible at/after this time
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal

    def __post_init__(self) -> None:
        utc(self.open_utc)
        utc(self.close_utc)
        require(self.close_utc - self.open_utc == timedelta(seconds=self.timeframe.seconds),
                "bar duration mismatch")
        for n in ("open", "high", "low", "close"):
            dec(getattr(self, n), n, positive=True)
        dec(self.volume, "volume", nonnegative=True)
        require(self.low <= min(self.open, self.close) <= max(self.open, self.close) <= self.high,
                "invalid OHLC envelope")


@dataclass(frozen=True, slots=True)
class DatasetRef:
    dataset_id: str
    instrument: Instrument
    kind: DataKind
    timeframe: Timeframe | None
    start_utc: datetime
    end_utc: datetime  # exclusive
    manifest_sha256: str
    source: str
    gap_count: int
    coverage_verified: bool

    def __post_init__(self) -> None:
        ident(self.dataset_id, "dataset_id")
        ident(self.source, "source")
        enum(self.kind, DataKind)
        utc(self.start_utc)
        utc(self.end_utc)
        require(self.start_utc < self.end_utc, "empty/inverted dataset range")
        digest(self.manifest_sha256)
        require(type(self.gap_count) is int and self.gap_count >= 0, "invalid gap count")
        require(type(self.coverage_verified) is bool, "coverage flag must be bool")
        require(self.kind != DataKind.OHLCV or self.timeframe is not None,
                "OHLCV requires timeframe")


@dataclass(frozen=True, slots=True)
class CostModel:
    maker_bps: Decimal
    taker_bps: Decimal
    tax_rate: Decimal  # fraction, e.g. 0.18, not 18
    slippage_bps: Decimal
    include_funding: bool
    include_spread: bool
    include_liquidation: bool
    model_id: str

    def __post_init__(self) -> None:
        for n in ("maker_bps", "taker_bps", "slippage_bps"):
            dec(getattr(self, n), n, nonnegative=True)
        dec(self.tax_rate, "tax_rate", nonnegative=True)
        require(self.tax_rate <= 1, "tax_rate is a fraction in [0,1]")
        require(all(type(getattr(self, n)) is bool for n in
                    ("include_funding", "include_spread", "include_liquidation")),
                "cost switches must be bool")
        ident(self.model_id, "model_id")


@dataclass(frozen=True, slots=True)
class StrategyRef:
    strategy_id: str
    version: str
    code_sha256: str
    parameters_sha256: str
    sdk_version: str = "1"

    def __post_init__(self) -> None:
        for n in ("strategy_id", "version", "sdk_version"):
            ident(getattr(self, n), n)
        digest(self.code_sha256)
        digest(self.parameters_sha256)


@dataclass(frozen=True, slots=True)
class BacktestConfig:
    strategy: StrategyRef
    instrument: Instrument
    datasets: tuple[DatasetRef, ...]
    start_utc: datetime
    end_utc: datetime
    signal_timeframe: Timeframe
    execution_timeframe: Timeframe
    initial_equity: Decimal
    account_currency: str
    leverage: Decimal
    margin_mode: MarginMode
    costs: CostModel
    intrabar_policy: IntrabarPolicy
    reporting_timezone: str
    calendar_id: str
    allow_data_gaps: bool = False
    random_seed: int = 0
    schema_version: int = 1

    def __post_init__(self) -> None:
        utc(self.start_utc)
        utc(self.end_utc)
        require(self.start_utc < self.end_utc, "empty/inverted backtest range")
        require(self.signal_timeframe.seconds % self.execution_timeframe.seconds == 0,
                "execution interval must divide signal interval")
        dec(self.initial_equity, "initial_equity", positive=True)
        dec(self.leverage, "leverage", positive=True)
        require(self.leverage >= 1, "leverage must be >= 1")
        ident(self.account_currency, "account_currency")
        enum(self.margin_mode, MarginMode)
        enum(self.intrabar_policy, IntrabarPolicy)
        require(self.margin_mode != MarginMode.CASH or self.leverage == 1,
                "cash margin requires 1x")
        require(self.instrument.asset_class != AssetClass.SPOT or self.margin_mode == MarginMode.CASH,
                "spot margin borrowing is not part of v1")
        ZoneInfo(self.reporting_timezone)
        ident(self.calendar_id, "calendar_id")
        require(type(self.allow_data_gaps) is bool, "allow_data_gaps must be bool")
        require(type(self.random_seed) is int and 0 <= self.random_seed < 2**32, "invalid seed")
        require(self.schema_version == 1, "unsupported config schema")
        require(isinstance(self.datasets, tuple) and bool(self.datasets), "immutable datasets required")
        require(len({d.dataset_id for d in self.datasets}) == len(self.datasets), "duplicate dataset id")
        for d in self.datasets:
            require(d.instrument == self.instrument, "dataset instrument mismatch")
            require(d.start_utc <= self.start_utc and d.end_utc >= self.end_utc,
                    "dataset does not cover requested interval")
            if not self.allow_data_gaps:
                require(d.coverage_verified and d.gap_count == 0, "unverified or gapped dataset")
        require(any(d.kind == DataKind.OHLCV and d.timeframe == self.execution_timeframe
                    for d in self.datasets), "execution OHLCV dataset missing")
        kinds = {d.kind for d in self.datasets}
        for enabled, kind in ((self.costs.include_funding, DataKind.FUNDING),
                              (self.costs.include_spread, DataKind.QUOTES),
                              (self.costs.include_liquidation, DataKind.MARK),
                              (self.intrabar_policy == IntrabarPolicy.TICK_SEQUENCE, DataKind.TRADES)):
            require(not enabled or kind in kinds, f"required input missing: {kind.value}")


@dataclass(frozen=True, slots=True)
class OrderIntent:
    intent_id: str
    instrument: Instrument
    decision_utc: datetime
    side: Side
    order_type: OrderType
    quantity: Decimal
    reason: str
    limit_price: Decimal | None = None
    stop_price: Decimal | None = None
    reduce_only: bool = False

    def __post_init__(self) -> None:
        ident(self.intent_id, "intent_id")
        ident(self.reason, "reason")
        utc(self.decision_utc)
        enum(self.side, Side)
        enum(self.order_type, OrderType)
        dec(self.quantity, "quantity", positive=True)
        require(self.quantity % self.instrument.lot_size == 0, "quantity not aligned to lot")
        require(type(self.reduce_only) is bool, "reduce_only must be bool")
        needs_limit = self.order_type in (OrderType.LIMIT, OrderType.STOP_LIMIT)
        needs_stop = self.order_type in (OrderType.STOP_MARKET, OrderType.STOP_LIMIT)
        require((self.limit_price is not None) == needs_limit, "limit price/order type mismatch")
        require((self.stop_price is not None) == needs_stop, "stop price/order type mismatch")
        for v in (self.limit_price, self.stop_price):
            if v is not None:
                dec(v, "order price", positive=True)
                require(v % self.instrument.tick_size == 0, "price not aligned to tick")


@dataclass(frozen=True, slots=True)
class Fill:
    fill_id: str
    order_id: str
    instrument: Instrument
    event_utc: datetime
    side: Side
    quantity: Decimal
    price: Decimal
    fee: Decimal
    tax: Decimal
    currency: str
    reason: str  # emitted at execution, not inferred after replay

    def __post_init__(self) -> None:
        for n in ("fill_id", "order_id", "currency", "reason"):
            ident(getattr(self, n), n)
        utc(self.event_utc)
        enum(self.side, Side)
        for n in ("quantity", "price"):
            dec(getattr(self, n), n, positive=True)
        for n in ("fee", "tax"):
            dec(getattr(self, n), n, nonnegative=True)
        require(self.quantity % self.instrument.lot_size == 0, "fill quantity off lot")
        require(self.price % self.instrument.tick_size == 0, "fill price off tick")


@dataclass(frozen=True, slots=True)
class ClosedTrade:
    trade_id: str
    entry_fills: tuple[Fill, ...]
    exit_fills: tuple[Fill, ...]
    entry_reason: str
    exit_reason: str
    gross_pnl: Decimal
    fees: Decimal
    taxes: Decimal
    funding_paid: Decimal  # negative if received
    net_pnl: Decimal
    currency: str

    def __post_init__(self) -> None:
        for n in ("trade_id", "entry_reason", "exit_reason", "currency"):
            ident(getattr(self, n), n)
        require(isinstance(self.entry_fills, tuple) and isinstance(self.exit_fills, tuple)
                and bool(self.entry_fills) and bool(self.exit_fills), "trade requires immutable fills")
        first = self.entry_fills[0]
        all_fills = self.entry_fills + self.exit_fills
        require(len({f.fill_id for f in all_fills}) == len(all_fills), "duplicate fill id")
        require(all(f.instrument == first.instrument and f.currency == self.currency for f in all_fills),
                "mixed instrument/currency trade")
        require(all(f.side == first.side for f in self.entry_fills)
                and all(f.side != first.side for f in self.exit_fills), "wrong fill direction")
        require(sum(f.quantity for f in self.entry_fills) == sum(f.quantity for f in self.exit_fills),
                "closed trade must reconcile quantity")
        # Supports scale-ins after partial exits; never exit more than held, and no same-time ambiguity.
        events = [(f.event_utc, 0, f.quantity) for f in self.entry_fills]
        events += [(f.event_utc, 1, -f.quantity) for f in self.exit_fills]
        held = Decimal(0)
        for _, _, delta in sorted(events):
            held += delta
            require(held >= 0, "exit before available entry quantity")
        for n in ("gross_pnl", "funding_paid", "net_pnl"):
            dec(getattr(self, n), n)
        for n in ("fees", "taxes"):
            dec(getattr(self, n), n, nonnegative=True)
        require(self.fees == sum(f.fee for f in all_fills)
                and self.taxes == sum(f.tax for f in all_fills), "fill costs do not reconcile")
        require(self.net_pnl == self.gross_pnl - self.fees - self.taxes - self.funding_paid,
                "net P&L does not reconcile")


@dataclass(frozen=True, slots=True)
class RunManifest:
    run_id: str
    config_sha256: str
    engine_version: str
    code_sha256: str
    dataset_sha256s: tuple[str, ...]
    result_sha256: str
    created_utc: datetime
    limitations: tuple[str, ...]
    schema_version: int = 1

    def __post_init__(self) -> None:
        ident(self.run_id, "run_id")
        ident(self.engine_version, "engine_version")
        for v in (self.config_sha256, self.code_sha256, self.result_sha256):
            digest(v)
        require(isinstance(self.dataset_sha256s, tuple) and bool(self.dataset_sha256s),
                "dataset fingerprints required")
        for v in self.dataset_sha256s:
            digest(v)
        utc(self.created_utc)
        require(isinstance(self.limitations, tuple), "limitations must be immutable")
        for v in self.limitations:
            ident(v, "limitation")
        require(self.schema_version == 1, "unsupported manifest schema")
