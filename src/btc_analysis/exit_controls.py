"""Generic fixed-point exit policy validation, shared by all authoring paths."""
from decimal import Decimal as D

def validate_bracket(bracket,tick=None):
    if type(bracket) is not tuple or len(bracket)!=2:
        raise ValueError("fixed-point bracket requires (stop, target or None)")
    stop,target=bracket
    for value in (stop,) if target is None else bracket:
        if type(value) is not D or not value.is_finite() or value<=0 or (tick is not None and value%tick):
            raise ValueError("fixed-point bracket distances must be positive Decimals and exact tick multiples")

def validate_exit_controls(bracket,trailing,lock,tick=None):
    if bracket is not None:validate_bracket(bracket,tick)
    if trailing is None and lock is None:return
    if bracket is None:raise ValueError("managed exits require a positive fixed-point bracket")
    for label,policy in (("trailing_stop_points",trailing),("profit_lock_points",lock)):
        if policy is None:continue
        if type(policy) is not tuple or len(policy)!=2 or any(type(x) is not D or not x.is_finite() or abs(x)>D("1000000000") for x in policy):
            raise ValueError(label+" requires two finite Decimal point values")
        activation,distance=policy
        if activation<=0:raise ValueError(label+" activation must be positive")
        if label=="trailing_stop_points" and distance<=0:raise ValueError("trailing distance must be positive")
        if label=="profit_lock_points" and not 0<=distance<activation:raise ValueError("profit lock must be nonnegative and below activation")
        if tick is not None and any(x%tick for x in policy):raise ValueError(label+" must use exact tick multiples")


def validate_dynamic_trailing(bracket,points,percent,atr):
    """One trailing distance mode, with an existing initial protective stop."""
    from .contracts import Timeframe
    from .indicators import IndicatorSpec
    if sum(policy is not None for policy in (points,percent,atr))>1:
        raise ValueError("select only one trailing distance mode")
    if percent is None and atr is None:return
    if bracket is None:raise ValueError("dynamic trailing requires a fixed-point initial bracket")
    validate_bracket(bracket)
    if percent is not None:
        if type(percent) is not tuple or len(percent)!=2 or any(type(v) is not D or not v.is_finite() or not 0<v<=D(99) for v in percent):
            raise ValueError("trailing_stop_pct requires two positive Decimal percentages <=99")
    if atr is not None:
        if type(atr) is not tuple or len(atr)!=4:raise ValueError("trailing_stop_atr requires (activation_pct, timeframe, period, multiplier)")
        activation,tf,period,multiplier=atr
        if type(activation) is not D or not activation.is_finite() or not 0<activation<=D(99):
            raise ValueError("ATR activation must be a positive Decimal percentage <=99")
        if type(tf) is not Timeframe or tf.seconds not in (60,180,300,900,1800,3600,14400,86400):
            raise ValueError("unsupported ATR timeframe")
        if type(multiplier) is not D or not multiplier.is_finite() or not 0<multiplier<=D(100):
            raise ValueError("ATR multiplier must be a positive Decimal <=100")
        IndicatorSpec.create("atr.value",tf,{"period":period})

def atr_trailing_spec(policy):
    from .indicators import IndicatorSpec
    return IndicatorSpec.create("atr.value",policy[1],{"period":policy[2]}) if policy is not None else None
