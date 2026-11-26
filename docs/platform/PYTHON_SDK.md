# M4 Python strategy SDK and indicator library

Trusted Python strategies use BaseStrategy or PythonStrategy. The future visual builder compiles to the same interface. Untrusted code is still disabled. Example: btc_analysis.examples.ema_supertrend.EMASupertrendExample (illustrative; not a validated or migrated frozen strategy).

Declare indicator specs and additional timeframes before replay:
```python
from btc_analysis.contracts import Timeframe
from btc_analysis.indicators import spec
from btc_analysis.strategy import PythonStrategy

class Example(PythonStrategy):
    tf = Timeframe(900)

    def indicators(self):
        return (spec("ema", self.tf, period=20),
                spec("supertrend.direction", self.tf, period=10, multiplier=3))

    def on_signal(self, ctx):
        ema = ctx.indicator("ema", self.tf, {"period": 20})
        trend = ctx.indicator("supertrend.direction", self.tf, {"period": 10, "multiplier": 3})
        # None means unavailable during warmup. Only completed candles are visible.
        if ema is None or trend is None:
            return
```

Call indicator_history for previous completed values (including None). Undeclared indicators fail explicitly. Incremental state persists beyond the bounded 4096-item visible history. All additional frames must be multiples of execution and align with warmup and evaluation boundaries. on_signal still follows configured signal timeframe; on_execution can inspect other completed frames. Indicators update before callbacks. Limits: 128 indicators, 18 distinct timeframes, period <=4096. PythonStrategy provides deterministic order IDs, buy/sell/close helpers; crossover/crossunder return false if an input is missing; quantity_for_notional rounds down to lot and does not promise margin approval.

## Indicator conventions
| Name | Definition and readiness |
| --- | --- |
| sma | n closes, arithmetic mean |
| ema | n-close SMA seed, alpha 2/(n+1) thereafter |
| atr | first TR=high-low, subsequent max true range, n-value Wilder seed |
| rsi | n price changes, Wilder gains/losses; flat=50, zero loss with gains=100 |
| adx / plus_di / minus_di | n changes for directional movement and TR; n DX for ADX; zero denominator=0 |
| supertrend.line / direction | Wilder ATR bands, initial bearish seed; strict crossings; +1 bullish, -1 bearish |
| bollinger.middle / upper / lower | n closes, population std dev, explicit multiplier |
| stddev | population standard deviation over n closes |
| donchian.upper / lower / middle | rolling n high/low, includes current completed candle |
| roc | n-period percent change, n+1 closes |
| volume_ratio | current volume divided by PREVIOUS n mean volumes; zero mean unavailable |
| vwap | rolling n-bar typical-price*volume / volume; approximation, not tick VWAP |
| macd.line / signal / histogram | SMA-seeded fast/slow EMAs, SMA-seeded signal EMA |

Decimal 50-digit internal precision; missing warmup values are None. Formula fixtures, reset, prefix invariance and deterministic integration tests included. No claim of TradingView/TA-Lib or frozen-strategy parity.

## Warmup
run_backtest accepts warmup_start_utc and warmup_factory together. The pinned execution dataset must cover warmup. Warmup must be gap-free, chronological and aligned for all declared timeframes; it updates data and indicators without any strategy callbacks, orders, equity effects or evaluation bar count. on_start sees warmed state. Each scenario records warmup count/hash, declarations and candle hash; different scenario streams/declarations fail. Warmup excluded from performance. Caller still attests source and strategy hashes; real historical causal use awaits verified source timestamp convention. No exchange-specific margin, funding or liquidation support yet.

Run tests: `python -m unittest discover -s tests/platform -v`.
