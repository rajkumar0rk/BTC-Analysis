"""Strategy API v1; implemented by the M3 trusted reference engine.
A host supplies a read-only causal view. Python is NOT a security boundary.
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Protocol, Sequence
from .contracts import Candle, Timeframe, Instrument, OrderIntent, Fill


class MarketView(Protocol):
    @property
    def now_utc(self) -> datetime: ...
    @property
    def instrument(self) -> Instrument: ...
    def candles(self, timeframe: Timeframe, limit: int) -> tuple[Candle, ...]:
        """Return only completed candles with close_utc <= now_utc."""
        ...
    def indicator(self, name: str, timeframe: Timeframe,
                  parameters: dict[str, int | str | Decimal]) -> Decimal | None:
        """Latest causal indicator; None during warmup."""
        ...


class StrategyContext(MarketView, Protocol):
    @property
    def equity(self) -> Decimal: ...
    @property
    def position_quantity(self) -> Decimal:
        """Signed net quantity for this strategy/instrument only."""
        ...
    def submit(self, intent: OrderIntent) -> None:
        """Emit reason-bearing intent, not an immediate fill."""
        ...
    def cancel(self, intent_id: str) -> None: ...


class Strategy(Protocol):
    def on_start(self, ctx: StrategyContext) -> None: ...
    def on_signal(self, ctx: StrategyContext) -> None:
        """Called only when signal candle closes; decisions cannot fill retroactively."""
        ...
    def on_execution(self, ctx: StrategyContext) -> None:
        """Execution-clock event for risk/position decisions."""
        ...
    def on_fill(self, ctx: StrategyContext, fill: Fill) -> None: ...
    def on_finish(self, ctx: StrategyContext) -> None: ...


class BacktestEngine(Protocol):
    def run(self, config, strategy: Strategy, datasets: Sequence[object]):
        """Interface for a deterministic simulation host."""
        ...


class Indicator(Protocol):
    def update(self, candle: Candle) -> Decimal | None: ...
    def reset(self) -> None: ...
