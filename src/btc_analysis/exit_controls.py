"""Generic fixed-point exit policy validation, shared by all authoring paths."""
from decimal import Decimal as D

def validate_exit_controls(bracket,trailing,lock,tick=None):
    if trailing is None and lock is None:return
    if type(bracket) is not tuple or len(bracket)!=2 or any(type(x) is not D or not x.is_finite() or x<=0 for x in bracket):
        raise ValueError("managed exits require a positive fixed-point bracket")
    for label,policy in (("trailing_stop_points",trailing),("profit_lock_points",lock)):
        if policy is None:continue
        if type(policy) is not tuple or len(policy)!=2 or any(type(x) is not D or not x.is_finite() or abs(x)>D("1000000000") for x in policy):
            raise ValueError(label+" requires two finite Decimal point values")
        activation,distance=policy
        if activation<=0:raise ValueError(label+" activation must be positive")
        if label=="trailing_stop_points" and distance<=0:raise ValueError("trailing distance must be positive")
        if label=="profit_lock_points" and not 0<=distance<activation:raise ValueError("profit lock must be nonnegative and below activation")
        if tick is not None and any(x%tick for x in policy):raise ValueError(label+" must use exact tick multiples")
