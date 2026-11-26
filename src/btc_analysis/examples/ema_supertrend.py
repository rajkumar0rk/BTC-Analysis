"""Illustrative causal EMA/Supertrend strategy; not a migrated or frozen strategy."""
from decimal import Decimal as D
from ..contracts import Timeframe
from ..indicators import spec
from ..strategy import PythonStrategy, quantity_for_notional


class EMASupertrendExample(PythonStrategy):
    def __init__(self,timeframe=Timeframe(900),ema_period=20,atr_period=10,multiplier=D(3),
                 exposure=D(".5")):
        super().__init__()
        self.tf=timeframe;self.ema_period=ema_period;self.atr_period=atr_period;self.multiplier=multiplier
        if not isinstance(exposure,D) or not exposure.is_finite() or not D(0)<exposure<=D(1):
            raise ValueError("exposure must be Decimal in (0,1]")
        self.exposure=exposure

    def indicators(self):
        return (spec("ema",self.tf,period=self.ema_period),
                spec("supertrend.direction",self.tf,period=self.atr_period,multiplier=self.multiplier))

    def on_signal(self,ctx):
        candle=ctx.candles(self.tf,1)
        ema=ctx.indicator("ema",self.tf,{"period":self.ema_period})
        trend=ctx.indicator("supertrend.direction",self.tf,{"period":self.atr_period,"multiplier":self.multiplier})
        if not candle or ema is None or trend is None:return
        close=candle[-1].close;q=ctx.position_quantity
        if q>0 and (trend<0 or close<ema):
            self.close_position(ctx,"long_trend_or_ema_exit");return
        if q<0 and (trend>0 or close>ema):
            self.close_position(ctx,"short_trend_or_ema_exit");return
        if q!=0 or ctx.equity<=0:return
        qty=quantity_for_notional(ctx.instrument,ctx.equity*self.exposure,close)
        if qty==0:return
        if trend>0 and close>ema:self.buy(ctx,qty,"ema_supertrend_long")
        elif trend<0 and close<ema:self.sell(ctx,qty,"ema_supertrend_short")
