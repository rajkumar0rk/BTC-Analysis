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


def formula_program(definitions):
    """Compile only bounded expressions through the existing SDK interpreter."""
    import ast
    from .service.python_strategy import Program
    allowed={"series","sum","mean","stddev","sqrt","D","Decimal","abs","min","max","len","int"}
    methods=[];decl=[]
    for i,d in enumerate(definitions):
        expression=d["expression"]
        if "\n" in expression or "\r" in expression:raise ValueError("custom formula must be a single expression")
        try:node=ast.parse(expression,mode="eval")
        except SyntaxError as exc:raise ValueError("invalid custom formula expression") from exc
        for n in ast.walk(node):
            if isinstance(n,ast.Name) and n.id not in allowed|{"bars","previous"}:
                raise ValueError("unknown custom formula name: "+n.id)
            if isinstance(n,ast.Call) and (not isinstance(n.func,ast.Name) or n.func.id not in allowed):
                raise ValueError("custom formula call not allowed")
            if isinstance(n,ast.Attribute) and n.attr not in {"open","high","low","close","volume"}:
                raise ValueError("custom formula attribute not allowed")
        method="formula"+str(i)
        decl.append("("+repr(d["name"])+", Timeframe("+str(d["timeframe"])+"), "+str(d["lookback"])+", "+repr(method)+")")
        methods.append("    def "+method+"(self, bars, previous):\n        return ("+expression+")")
    source="class Strategy(PythonStrategy):\n    def on_signal(self, ctx):\n        pass\n    def custom_indicators(self):\n        return ("+", ".join(decl)+",)\n"+"\n".join(methods)+"\n"
    try:
        program=Program(source)
        program.make()
        return program
    except SyntaxError as exc:raise ValueError("invalid custom formula") from exc


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
    sequence_config=None
    machine_config=None
    exit_machine_config=None
    partial_config=None
    partial_levels_config=None
    conditional_lock_config=None
    conditional_target_config=None
    custom_config=None

    def __init__(self):
        super().__init__()
        self.entry_streak={1:0,-1:0}
        self.entry_cycle={1:0,-1:0}
        self.used_cycle={1:-1,-1:-1}
        self.last_flat_signal=None
        self.signal_count=0
        self.pending_cycle=None
        self.sequence_state={1:(0,None),-1:(0,None)}
        self.machine_state={1:(0,None),-1:(0,None)}
        self.exit_machine_state={1:(0,None),-1:(0,None)}
        self.partial_consumed=False
        self.partial_pending=False
        self.partial_level_index=0
        self.partial_level_pending=None
        self.formula_runtime=formula_program(self.custom_config).make() if self.custom_config else None

    def on_completed_candle(self,candle):
        if self.formula_runtime is not None:self.formula_runtime.on_completed_candle(candle)

    def position_pair(self,ctx,field):
        # Undefined while flat (except signed quantity). No synthetic previous
        # snapshot is exposed, so crossovers are rejected during validation.
        value=getattr(ctx,field) if field=="position_quantity" or ctx.position_quantity else None
        return (None,value)

    def custom_pair(self,name):
        history=self.formula_runtime.custom[name][3]
        return (history[-2] if len(history)>1 else None,history[-1] if history else None)

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

    def sequence_stage(self,ctx,direction,index):return False
    def sequence_reset(self,ctx,direction):return False

    def machine_transition(self,ctx,direction,index):return False
    def machine_reset(self,ctx,direction):return False

    def exit_machine_transition(self,ctx,direction,index):return False
    def exit_machine_reset(self,ctx,direction):return False

    def machine_ready(self,ctx,direction,position_exit=False):
        config=self.exit_machine_config if position_exit else self.machine_config
        states=self.exit_machine_state if position_exit else self.machine_state
        transition=self.exit_machine_transition if position_exit else self.machine_transition
        reset=self.exit_machine_reset if position_exit else self.machine_reset
        if direction not in (config or {}):return True
        ready,expiry,edges=config[direction]
        state,started=states[direction]
        invalid_position=ctx.position_quantity*direction<=0 if position_exit else ctx.position_quantity!=0
        if invalid_position or reset(ctx,direction):
            states[direction]=(0,None)
            return False
        if started is not None and self.signal_count-started>expiry:
            state,started=0,None
        # A single ordered transition per completed signal candle. Reset and
        # position checks take priority. Returning to idle restarts the clock.
        if state!=ready:
            for i,(source,target) in enumerate(edges):
                if source==state and transition(ctx,direction,i):
                    if target==0:started=None
                    elif state==0:started=self.signal_count
                    state=target
                    break
        states[direction]=(state,started)
        return state==ready

    def sequence_ready(self,ctx,direction):
        if direction in (self.machine_config or {}):return self.machine_ready(ctx,direction)
        config=(self.sequence_config or {}).get(direction)
        if config is None:return True
        stages,expiry=config
        index,started=self.sequence_state[direction]
        # Reset always wins, including on the bar of a potential final stage.
        if ctx.position_quantity!=0 or self.sequence_reset(ctx,direction):
            self.sequence_state[direction]=(0,None)
            return False
        if started is not None and self.signal_count-started>expiry:
            index,started=0,None
        # At most one stage on each completed signal candle. A completed
        # sequence remains armed until fill, expiry, reset or an open position.
        if index<stages and self.sequence_stage(ctx,direction,index):
            if index==0:started=self.signal_count
            index+=1
        self.sequence_state[direction]=(index,started)
        return index==stages

    def conditional_target_rule(self,ctx,direction):return False

    def maybe_target(self,ctx,direction):
        config=(self.conditional_target_config or {}).get(direction)
        if config is not None and self.conditional_target_rule(ctx,direction):
            points,mode=config
            ctx.adjust_fixed_target(D(points),mode=mode)

    def conditional_lock_rule(self,ctx,direction):return False

    def maybe_lock(self,ctx,direction):
        points=(self.conditional_lock_config or {}).get(direction)
        if points is not None and self.conditional_lock_rule(ctx,direction):
            if isinstance(points,tuple):ctx.tighten_fixed_stop(D(points[0]),cost_adjusted=True)
            else:ctx.tighten_fixed_stop(D(points))

    def partial_rule(self,ctx,direction):return False

    def partial_level_rule(self,ctx,direction,index):return False

    def maybe_partial_level(self,ctx,direction,levels):
        index=self.partial_level_index
        if index>=len(levels) or self.partial_level_pending is not None:return
        if not self.partial_level_rule(ctx,direction,index):return
        total=abs(ctx.position_quantity);lot=ctx.instrument.lot_size
        qty=(total*D(levels[index])/100/lot).to_integral_value(rounding=ROUND_FLOOR)*lot
        if qty<lot or total-qty<lot:return
        reason=("visual_long_partial_level_" if direction>0 else "visual_short_partial_level_")+str(index+1)
        self.order(ctx,Side.SELL if direction>0 else Side.BUY,qty,reason,reduce_only=True)
        self.partial_level_pending=reason

    def maybe_partial(self,ctx,direction):
        levels=(self.partial_levels_config or {}).get(direction)
        if levels is not None:
            self.maybe_partial_level(ctx,direction,levels)
            return
        pct=(self.partial_config or {}).get(direction)
        if pct is None or self.partial_consumed or self.partial_pending or not self.partial_rule(ctx,direction):return
        total=abs(ctx.position_quantity)
        lot=ctx.instrument.lot_size
        qty=(total*D(pct)/100/lot).to_integral_value(rounding=ROUND_FLOOR)*lot
        # Never silently convert a partial exit into a full exit or round up.
        if qty<lot or total-qty<lot:return
        self.order(ctx,Side.SELL if direction>0 else Side.BUY,qty,
                   "visual_long_partial_exit" if direction>0 else "visual_short_partial_exit",reduce_only=True)
        # One request per position; market reduction is eligible at next open.
        # Fail closed after a rejected request rather than issuing duplicates.
        self.partial_pending=True

    def on_signal(self,ctx):
        bars=ctx.candles(Timeframe(self.signal_seconds),1)
        if not bars or bars[-1].close_utc!=ctx.now_utc:return
        q=ctx.position_quantity
        a=self.advanced_controls
        if a is not None:
            self.signal_count+=1
            # Evaluate raw entry conditions even while a position is open.
            ready={direction:self.sequence_ready(ctx,direction) for direction in (1,-1)}
            raw={1:ready[1] and self.long_entry(ctx),-1:ready[-1] and self.short_entry(ctx)}
            for direction,active in raw.items():
                if active:
                    if self.entry_streak[direction]==0:self.entry_cycle[direction]+=1
                    self.entry_streak[direction]+=1
                else:self.entry_streak[direction]=0
        if self.exit_machine_config:
            for direction in (1,-1):
                if q*direction<=0:self.exit_machine_state[direction]=(0,None)
        if q>0:
            if self.machine_ready(ctx,1,position_exit=True) and self.long_exit(ctx):self.close_position(ctx,"visual_long_rule_exit")
            else:
                self.maybe_lock(ctx,1)
                self.maybe_target(ctx,1)
                self.maybe_partial(ctx,1)
            return
        if q<0:
            if self.machine_ready(ctx,-1,position_exit=True) and self.short_exit(ctx):self.close_position(ctx,"visual_short_rule_exit")
            else:
                self.maybe_lock(ctx,-1)
                self.maybe_target(ctx,-1)
                self.maybe_partial(ctx,-1)
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
        if self.partial_levels_config:
            if ctx.position_quantity==0 or fill.reason in ("visual_long_entry","visual_short_entry"):
                self.partial_level_index=0;self.partial_level_pending=None
            elif self.partial_level_pending is not None and fill.reason==self.partial_level_pending:
                self.partial_level_index+=1;self.partial_level_pending=None
        if self.partial_config:
            if ctx.position_quantity==0 or fill.reason in ("visual_long_entry","visual_short_entry"):
                self.partial_consumed=False;self.partial_pending=False
            elif fill.reason in ("visual_long_partial_exit","visual_short_partial_exit"):
                self.partial_consumed=True;self.partial_pending=False
        if self.exit_machine_config and (ctx.position_quantity==0 or fill.reason in ("visual_long_entry","visual_short_entry")):
            self.exit_machine_state={1:(0,None),-1:(0,None)}
        if self.advanced_controls is not None:
            if fill.reason in ("visual_long_entry","visual_short_entry"):
                direction=1 if fill.reason=="visual_long_entry" else -1
                if self.pending_cycle is not None and self.pending_cycle[0]==direction:self.used_cycle[direction]=self.pending_cycle[1]
                self.pending_cycle=None
                if self.sequence_config:
                    self.sequence_state={1:(0,None),-1:(0,None)}
                    for d in self.sequence_config:self.entry_streak[d]=0
                if self.machine_config:
                    self.machine_state={1:(0,None),-1:(0,None)}
                    for d in self.machine_config:self.entry_streak[d]=0
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
