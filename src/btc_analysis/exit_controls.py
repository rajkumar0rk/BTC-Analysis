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
