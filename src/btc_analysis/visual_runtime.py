"""Reviewed SDK primitives used by generated Python. No eval or source loading."""
from decimal import Decimal as D, ROUND_FLOOR, ROUND_CEILING, localcontext
from .contracts import Timeframe, Side, OrderType
from .strategy import PythonStrategy, quantity_for_notional, crossover, crossunder


def constant(value):
    d=D(value)
    return (d,d)


def price(ctx,seconds,field):
    values=ctx.candles(Timeframe(seconds),2)
    if not values:return (None,None)
    return (getattr(values[-2],field) if len(values)>1 else None,getattr(values[-1],field))


def indicator(ctx,name,seconds,parameters):
    values=ctx.indicator_history(name,Timeframe(seconds),parameters,limit=2)
    return ((values[-2] if len(values)>1 else None),(values[-1] if values else None))


def compare(op,left,right):
    a,b=left;c,d=right
    if op=="cross_up":return crossover(a,b,c,d)
    if op=="cross_down":return crossunder(a,b,c,d)
    if b is None or d is None:return False
    if op=="gt":return b>d
    if op=="gte":return b>=d
    if op=="lt":return b<d
    if op=="lte":return b<=d
    if op=="eq":return b==d
    raise ValueError("unsupported comparison")


class VisualStrategyBase(PythonStrategy):
    """One net position, no pyramiding. Signal entry and exits use next open.
    Stop/target submitted from fill callback, active from following execution bar.
    """
    signal_seconds=900
    execution_seconds=60
    exposure=D(".5")
    stop_loss=D(".01")
    take_profit=D(".02")

    def long_entry(self,ctx):return False
    def short_entry(self,ctx):return False
    def long_exit(self,ctx):return False
    def short_exit(self,ctx):return False

    def on_signal(self,ctx):
        bars=ctx.candles(Timeframe(self.signal_seconds),1)
        if not bars or bars[-1].close_utc!=ctx.now_utc:return
        q=ctx.position_quantity
        if q>0:
            if self.long_exit(ctx):self.close_position(ctx,"visual_long_rule_exit")
            return
        if q<0:
            if self.short_exit(ctx):self.close_position(ctx,"visual_short_rule_exit")
            return
        if ctx.equity<=0:return
        long=self.long_entry(ctx);short=self.short_entry(ctx)
        if long==short:return  # ambiguous simultaneous entries are skipped
        qty=quantity_for_notional(ctx.instrument,ctx.equity*self.exposure,bars[-1].close)
        if qty<=0:return
        if long:self.buy(ctx,qty,"visual_long_entry")
        else:self.sell(ctx,qty,"visual_short_entry")

    def on_fill(self,ctx,fill):
        if fill.reason not in ("visual_long_entry","visual_short_entry"):return
        q=ctx.position_quantity
        if q==0:return
        long=q>0
        tick=ctx.instrument.tick_size
        with localcontext() as c:
            c.prec=50
            def rounded(p,mode):
                return max(tick,(p/tick).to_integral_value(rounding=mode)*tick)
            stop=rounded(fill.price*(1-self.stop_loss if long else 1+self.stop_loss),
                         ROUND_CEILING if long else ROUND_FLOOR)
            target=rounded(fill.price*(1+self.take_profit if long else 1-self.take_profit),
                           ROUND_CEILING if long else ROUND_FLOOR)
        side=Side.SELL if long else Side.BUY
        self.order(ctx,side,abs(q),"visual_stop_loss",order_type=OrderType.STOP_MARKET,
                   stop_price=stop,reduce_only=True)
        self.order(ctx,side,abs(q),"visual_take_profit",order_type=OrderType.LIMIT,
                   limit_price=target,reduce_only=True)
