"""Trusted, deterministic reference simulation (M3)."""
from .engine import run_backtest, BaseStrategy, BacktestResult, ScenarioResult

__all__ = ["run_backtest", "BaseStrategy", "BacktestResult", "ScenarioResult"]
