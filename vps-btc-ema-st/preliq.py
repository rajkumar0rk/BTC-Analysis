"""Pre-liquidation protective stop calculations for BTC/ETH futures.

STOP PRICE != EXECUTION GUARANTEE. Uses exchange position liquidation_price
for actual demo/live execution; isolated paper uses an explicitly labeled proxy.
Pre-liquidation stop only protects a position, NEVER filters an entry.
"""
import math
from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR

def numeric(value,name):
    try:out=float(value)
    except (TypeError,ValueError):raise ValueError(name+" is missing or non-numeric")
    if not math.isfinite(out) or out<=0:raise ValueError(name+" must be positive and finite")
    return out

def pre_liq_buffer(asset,reference_price,tick,btc_points=1,btc_reference=80000):
    """One BTC price point; for ETH use entry-relative BTC-equivalent amount.

    With ETH 4,000 and BTC reference 80,000 this is $0.05, respecting tick.
    The reference is configurable and is NOT a real-time BTC/ETH ratio.
    """
    p=numeric(reference_price,"reference_price")
    t=numeric(tick,"tick_size")
    pts=numeric(btc_points,"pre_liquidation_btc_points")
    ref=numeric(btc_reference,"btc_reference_price")
    if asset=="BTC":raw=pts
    elif asset=="ETH":raw=pts*p/ref
    else:raise ValueError("Only BTC and ETH are supported")
    # Round UP to instrument tick: do not accidentally set less than requested.
    ticks=max(1,int((Decimal(str(raw))/Decimal(str(t))).to_integral_value(rounding=ROUND_CEILING)))
    return float(Decimal(ticks)*Decimal(str(t)))

def aligned_stop(value,tick,side):
    """LONG stop rounds UP, SHORT stop rounds DOWN, to protect buffer."""
    price=Decimal(str(numeric(value,"stop_price")))
    step=Decimal(str(numeric(tick,"tick_size")))
    rounding=ROUND_CEILING if side=="buy" else ROUND_FLOOR if side=="sell" else None
    if rounding is None:raise ValueError("Invalid position side")
    return float((price/step).to_integral_value(rounding=rounding)*step)

def pre_liq_stop(side,liquidation_price,buffer,tick):
    liq=numeric(liquidation_price,"exchange_liquidation_price")
    b=numeric(buffer,"pre_liquidation_buffer")
    if side=="buy":return aligned_stop(liq+b,tick,"buy")
    if side=="sell":return aligned_stop(liq-b,tick,"sell")
    raise ValueError("Invalid position side")

def effective_stop(side,atr_stop,liq_stop,entry):
    entry=numeric(entry,"entry")
    atr=numeric(atr_stop,"atr_stop")
    near=numeric(liq_stop,"pre_liq_stop")
    if side=="buy":
        stop=max(atr,near)
        if stop>=entry:raise ValueError("Long protective stop at/above entry; close position or refuse entry")
        return stop
    if side=="sell":
        stop=min(atr,near)
        if stop<=entry:raise ValueError("Short protective stop at/below entry; close position or refuse entry")
        return stop
    raise ValueError("Invalid side")

def reported_liquidation(position,side,entry):
    """Use ONLY real authenticated exchange GET /v2/positions liquidation_price."""
    if not isinstance(position,dict):
        raise ValueError("Exchange position expected a JSON object")
    liq=numeric(position.get("liquidation_price"),"exchange_liquidation_price")
    ep=numeric(entry,"position_entry")
    if side=="buy" and not liq<ep:
        raise ValueError("Invalid long liquidation price (not below entry)")
    if side=="sell" and not liq>ep:
        raise ValueError("Invalid short liquidation price (not above entry)")
    if side not in ("buy","sell"):raise ValueError("Unknown side")
    return liq

def estimate_liquidation(entry,side,leverage,maintenance_pct):
    """PAPER and provisional bracket ONLY. NOT exchange liquidation price."""
    entry=numeric(entry,"entry")
    lev=numeric(leverage,"leverage")
    maint=numeric(maintenance_pct,"maintenance_percent")/100
    im=1/lev
    if not(0<maint<im):raise ValueError("Maintenance exceeds initial margin")
    if side=="buy":return entry*(1-im)/(1-maint)
    if side=="sell":return entry*(1+im)/(1+maint)
    raise ValueError("Unknown side")

def stop_crossed(side,mark,stop):
    mark=numeric(mark,"mark_price")
    if side=="buy":return mark<=numeric(stop,"stop")
    if side=="sell":return mark>=numeric(stop,"stop")
    raise ValueError("Invalid side")
