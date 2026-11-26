"""Strategy authoring helpers shared by handwritten and future visual-generated Python.
Trusted code only. Helpers generate ordinary validated order intents.
"""
from decimal import Decimal as D, ROUND_FLOOR, localcontext
from .contracts import OrderIntent, Side, OrderType, dec
from .backtest import BaseStrategy


def crossover(previous_a,current_a,previous_b,current_b):
    return (None not in (previous_a,current_a,previous_b,current_b)
            and previous_a<=previous_b and current_a>current_b)


def crossunder(previous_a,current_a,previous_b,current_b):
    return (None not in (previous_a,current_a,previous_b,current_b)
            and previous_a>=previous_b and current_a<current_b)


def quantity_for_notional(instrument,notional,price):
    """Linear contract only; rounds down to lot. Does not guarantee a margin approval."""
    dec(notional,"notional",nonnegative=True);dec(price,"price",positive=True)
    with localcontext() as ctx:
        ctx.prec=50
        units=notional/(price*instrument.contract_multiplier*instrument.lot_size)
        return units.to_integral_value(rounding=ROUND_FLOOR)*instrument.lot_size


class PythonStrategy(BaseStrategy):
    def __init__(self):self._sequence=0

    def order(self,ctx,side,quantity,reason,*,order_type=OrderType.MARKET,
              limit_price=None,stop_price=None,reduce_only=False):
        self._sequence+=1
        key=f"strategy-{self._sequence}"
        ctx.submit(OrderIntent(key,ctx.instrument,ctx.now_utc,side,order_type,quantity,
                   reason,limit_price,stop_price,reduce_only))
        return key

    def buy(self,ctx,quantity,reason,**kwargs):
        return self.order(ctx,Side.BUY,quantity,reason,**kwargs)

    def sell(self,ctx,quantity,reason,**kwargs):
        return self.order(ctx,Side.SELL,quantity,reason,**kwargs)

    def close_position(self,ctx,reason):
        q=ctx.position_quantity
        if q==0:return None
        return self.order(ctx,Side.SELL if q>0 else Side.BUY,abs(q),reason,reduce_only=True)
