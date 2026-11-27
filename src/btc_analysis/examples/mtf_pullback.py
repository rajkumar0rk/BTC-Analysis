"""Reviewed BTC/ETH MTF Supertrend EMA20 fixed-point research strategy.

No dynamic source execution. The exact library wrappers select one of two
reviewed modes; all implementation lives in this trusted SDK module.
"""
from decimal import Decimal as D
from zoneinfo import ZoneInfo
from ..contracts import Timeframe
from ..indicators import IndicatorSpec
from ..strategy import PythonStrategy,quantity_for_notional
from ..serialization import fingerprint

MIN=Timeframe(60)
M15=Timeframe(900)
H1=Timeframe(3600)
ST={"period":10,"multiplier":"3"}
EMA={"period":20}
IST=ZoneInfo("Asia/Kolkata")
HEADER="# btc-reviewed-mtf-pullback-v1 "
WARMUP_MINUTES=6000

SOURCES={"touch":"# btc-reviewed-mtf-pullback-v1 touch\n# 1H/15M Supertrend ATR 10 x 3, 15M EMA20.\n# Completed 1M touch from the trend side; enter next open.\n# 100-hour initialization; IST weekdays for entry, all days for exits.\n# One trade per contiguous aligned Supertrend cycle; no overlapping positions.\n# Fixed 100-point SL / 200-point TP from actual modeled fill.\n# No trailing stop or reversal exit. No live orders.\n# Reviewed SDK implementation; exposure defaults to 50% of equity.\nfrom btc_analysis.examples.mtf_pullback import MTFPullbackStrategy\n\nclass Strategy(MTFPullbackStrategy):\n    def __init__(self):\n        super().__init__(\"touch\")\n","reclaim":"# btc-reviewed-mtf-pullback-v1 reclaim\n# 1H/15M Supertrend ATR 10 x 3, 15M EMA20.\n# Completed 15M reclaim of EMA fixed at candle start; enter next open.\n# 100-hour initialization; IST weekdays for entry, all days for exits.\n# One trade per contiguous aligned Supertrend cycle; no overlapping positions.\n# Fixed 100-point SL / 200-point TP from actual modeled fill.\n# No trailing stop or reversal exit. No live orders.\n# Reviewed SDK implementation; exposure defaults to 50% of equity.\nfrom btc_analysis.examples.mtf_pullback import MTFPullbackStrategy\n\nclass Strategy(MTFPullbackStrategy):\n    def __init__(self):\n        super().__init__(\"reclaim\")\n"}

def recover_pullback(source):
    if not isinstance(source,str) or not source.startswith(HEADER):
        raise ValueError("not a reviewed MTF pullback script")
    mode=source.split("\n",1)[0][len(HEADER):]
    if mode not in SOURCES or source!=SOURCES[mode]:
        raise ValueError("modified or unsupported MTF pullback source")
    return {"mode":mode,"source":source,"graph_sha256":fingerprint({"recipe":"mtf-pullback-v1","mode":mode,
        "st_period":10,"st_multiplier":"3","ema_period":20,"stop_points":"100","target_points":"200",
        "exposure_pct":"50","warmup_minutes":WARMUP_MINUTES,"timezone":"Asia/Kolkata"})}

def alignment(a,b):
    return int(a) if a in (D(-1),D(1)) and a==b else 0

def touch(direction,previous,bar,ema):
    return bool(direction and previous is not None and ema is not None and
                direction*(previous.close-ema)>0 and direction*(bar.open-ema)>=0 and bar.low<=ema<=bar.high)

def reclaim(direction,previous,bar,ema):
    return bool(direction and previous is not None and ema is not None and
                direction*(previous.close-ema)>0 and bar.low<=ema<=bar.high and direction*(bar.close-ema)>0)

class MTFPullbackStrategy(PythonStrategy):
    exposure=D(".5")
    # Trusted engine opt-in. Brackets are installed at market entry fill,
    # not after the close-time strategy callback.
    fixed_point_bracket=(D(100),D(200))
    def __init__(self,mode):
        super().__init__()
        if mode not in ("touch","reclaim"):raise ValueError("invalid pullback mode")
        self.mode=mode
        self.signal_seconds=60 if mode=="touch" else 900
        self.aligned=0
        self.ema=None
        self.used=False
        self.minutes=0

    def indicators(self):
        return (IndicatorSpec.create("supertrend.direction",H1,ST),
                IndicatorSpec.create("supertrend.direction",M15,ST),
                IndicatorSpec.create("ema.value",M15,EMA))
    def extra_timeframes(self):return (MIN,M15,H1)

    def on_fill(self,ctx,fill):
        if fill.reason in ("mtf_pullback_long","mtf_pullback_short"):
            self.used=True

    def on_execution(self,ctx):
        minute=ctx.candles(MIN,2)
        if not minute:return
        self.minutes+=1
        previous_alignment,previous_ema=self.aligned,self.ema
        side=alignment(ctx.indicator("supertrend.direction",H1,ST),ctx.indicator("supertrend.direction",M15,ST))
        self.aligned=side
        self.ema=ctx.indicator("ema.value",M15,EMA)
        # Reset only when the contiguous alignment changes, including on
        # weekends and while a position is open.
        if side!=previous_alignment:self.used=False
        if (self.minutes<WARMUP_MINUTES or not side or self.used or ctx.position_quantity!=0
                or ctx.equity<=0 or ctx.now_utc.astimezone(IST).weekday()>=5):
            return
        if self.mode=="touch":
            # Previous confirmed indicator state was known at this minute's
            # open. Entry at next open requires alignment still unchanged.
            if side!=previous_alignment or len(minute)!=2 or not touch(side,minute[-2],minute[-1],previous_ema):return
        else:
            candles=ctx.candles(M15,2)
            emas=ctx.indicator_history("ema.value",M15,EMA,limit=2)
            if len(candles)!=2 or len(emas)!=2 or candles[-1].close_utc!=ctx.now_utc:return
            if not reclaim(side,candles[-2],candles[-1],emas[-2]):return
        quantity=quantity_for_notional(ctx.instrument,ctx.equity*self.exposure,minute[-1].close)
        if quantity<=0:return
        if side>0:self.buy(ctx,quantity,"mtf_pullback_long")
        else:self.sell(ctx,quantity,"mtf_pullback_short")
