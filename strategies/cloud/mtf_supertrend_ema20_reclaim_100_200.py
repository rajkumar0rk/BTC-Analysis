# btc-reviewed-mtf-pullback-v1 reclaim
# 1H/15M Supertrend ATR 10 x 3, 15M EMA20.
# Completed 15M reclaim of EMA fixed at candle start; enter next open.
# 100-hour initialization; IST weekdays for entry, all days for exits.
# One trade per contiguous aligned Supertrend cycle; no overlapping positions.
# Fixed 100-point SL / 200-point TP from actual modeled fill.
# No trailing stop or reversal exit. No live orders.
# Reviewed SDK implementation; exposure defaults to 50% of equity.
from btc_analysis.examples.mtf_pullback import MTFPullbackStrategy

class Strategy(MTFPullbackStrategy):
    def __init__(self):
        super().__init__("reclaim")
