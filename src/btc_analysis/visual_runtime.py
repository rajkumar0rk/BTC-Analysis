"""Reviewed SDK primitives used by generated Python. No eval or source loading."""
from decimal import Decimal as D, ROUND_FLOOR, ROUND_CEILING, localcontext
from zoneinfo import ZoneInfo
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

    advanced_controls=None

    def __init__(self):
        super().__init__()
        self.entry_streak={1:0,-1:0}
        self.entry_cycle={1:0,-1:0}
        self.used_cycle={1:-1,-1:-1}
        self.last_flat_signal=None
        self.signal_count=0
        self.pending_cycle=None

    @property
    def fixed_point_bracket(self):
        a=self.advanced_controls
        if a is None or a["exit_mode"]!="points":return None
        return D(a["stop_points"]),None if a.get("target_enabled") is False else D(a["target_points"])

    @property
    def trailing_stop_points(self):
        a=self.advanced_controls
        policy=a.get("trailing") if a is not None else None
        return (D(policy["activation"]),D(policy["distance"])) if policy is not None else None

    @property
    def trailing_stop_pct(self):
        a=self.advanced_controls
        policy=a.get("trailing_percent") if a is not None else None
        return (D(policy["activation"]),D(policy["distance"])) if policy is not None else None

    @property
    def trailing_stop_atr(self):
        a=self.advanced_controls
        policy=a.get("trailing_atr") if a is not None else None
        return (D(policy["activation"]),Timeframe(policy["timeframe"]),policy["period"],D(policy["multiplier"])) if policy is not None else None

    @property
    def profit_lock_points(self):
        a=self.advanced_controls
        policy=a.get("profit_lock") if a is not None else None
        return (D(policy["activation"]),D(policy["locked"])) if policy is not None else None

    def long_entry(self,ctx):return False
    def short_entry(self,ctx):return False
    def long_exit(self,ctx):return False
    def short_exit(self,ctx):return False

    def on_signal(self,ctx):
        bars=ctx.candles(Timeframe(self.signal_seconds),1)
        if not bars or bars[-1].close_utc!=ctx.now_utc:return
        q=ctx.position_quantity
        a=self.advanced_controls
        if a is not None:
            self.signal_count+=1
            # Evaluate raw entry conditions even while a position is open.
            raw={1:self.long_entry(ctx),-1:self.short_entry(ctx)}
            for direction,active in raw.items():
                if active:
                    if self.entry_streak[direction]==0:self.entry_cycle[direction]+=1
                    self.entry_streak[direction]+=1
                else:self.entry_streak[direction]=0
        if q>0:
            if self.long_exit(ctx):self.close_position(ctx,"visual_long_rule_exit")
            return
        if q<0:
            if self.short_exit(ctx):self.close_position(ctx,"visual_short_rule_exit")
            return
        if ctx.equity<=0:return
        if a is None:
            long=self.long_entry(ctx);short=self.short_entry(ctx)
        else:
            if ctx.now_utc.astimezone(ZoneInfo("Asia/Kolkata")).weekday() not in a["weekdays_ist"]:return
            if self.last_flat_signal is not None and self.signal_count-self.last_flat_signal<=a["cooldown_bars"]:return
            def eligible(direction):
                return (raw[direction] and self.entry_streak[direction]>=a["confirmation_bars"]
                        and (a["entry_mode"]!="once_per_true_run" or self.used_cycle[direction]!=self.entry_cycle[direction]))
            # Never turn an ambiguous raw signal into a directional entry via filtering.
            if raw[1] and raw[-1]:return
            long=eligible(1);short=eligible(-1)
        if long==short:return  # ambiguous simultaneous entries are skipped
        qty=quantity_for_notional(ctx.instrument,ctx.equity*self.exposure,bars[-1].close)
        if qty<=0:return
        if a is not None:
            direction=1 if long else -1
            self.pending_cycle=(direction,self.entry_cycle[direction])
        if long:self.buy(ctx,qty,"visual_long_entry")
        else:self.sell(ctx,qty,"visual_short_entry")

    def on_fill(self,ctx,fill):
        if self.advanced_controls is not None:
            if fill.reason in ("visual_long_entry","visual_short_entry"):
                direction=1 if fill.reason=="visual_long_entry" else -1
                if self.pending_cycle is not None and self.pending_cycle[0]==direction:self.used_cycle[direction]=self.pending_cycle[1]
                self.pending_cycle=None
            elif ctx.position_quantity==0:
                self.last_flat_signal=self.signal_count
        if fill.reason not in ("visual_long_entry","visual_short_entry"):return
        if self.fixed_point_bracket is not None:return
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
