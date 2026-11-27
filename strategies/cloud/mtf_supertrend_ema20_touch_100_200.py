# User-authored strategy source. Copy/paste into the Python editor.
# No dedicated application runtime, metadata or automatic registration.
from decimal import Decimal as D
from btc_analysis.strategy import PythonStrategy, quantity_for_notional
from btc_analysis.contracts import Timeframe
from btc_analysis.indicators import spec

class Strategy(PythonStrategy):
    signal_seconds = 60
    execution_seconds = 60
    exposure = D("0.5")
    fixed_point_bracket = (D("100"), D("200"))
    warmup_minutes = 6000

    def __init__(self):
        self.aligned = 0
        self.ema = None
        self.used = False
        self.minutes = 0

    def indicators(self):
        return (
            spec("supertrend.direction", Timeframe(3600), period=10, multiplier="3"),
            spec("supertrend.direction", Timeframe(900), period=10, multiplier="3"),
            spec("ema.value", Timeframe(900), period=20),
        )

    def on_fill(self, ctx, fill):
        if fill.reason in ("pullback_long", "pullback_short"):
            self.used = True

    def on_execution(self, ctx):
        minute = ctx.candles(Timeframe(60), 2)
        if not minute:
            return
        self.minutes += 1
        previous_alignment = self.aligned
        previous_ema = self.ema
        trend_hour = ctx.indicator("supertrend.direction", Timeframe(3600), {"period": 10, "multiplier": "3"})
        trend_15m = ctx.indicator("supertrend.direction", Timeframe(900), {"period": 10, "multiplier": "3"})
        side = 0
        if trend_hour in (D("-1"), D("1")) and trend_hour == trend_15m:
            side = int(trend_hour)
        self.aligned = side
        self.ema = ctx.indicator("ema.value", Timeframe(900), {"period": 20})
        if side != previous_alignment:
            self.used = False
        if self.minutes < self.warmup_minutes or not side or self.used:
            return
        if ctx.position_quantity != 0 or ctx.equity <= 0:
            return
        if weekday_ist(ctx.now_utc) >= 5:
            return
        # Confirm the completed 1m touch against EMA known at minute open.
        if side != previous_alignment or len(minute) != 2 or previous_ema is None:
            return
        previous = minute[-2]
        candle = minute[-1]
        if not (side * (previous.close - previous_ema) > 0 and side * (candle.open - previous_ema) >= 0 and candle.low <= previous_ema <= candle.high):
            return
        qty = quantity_for_notional(ctx.instrument, ctx.equity * self.exposure, minute[-1].close)
        if qty <= 0:
            return
        if side > 0:
            self.buy(ctx, qty, "pullback_long")
        else:
            self.sell(ctx, qty, "pullback_short")
