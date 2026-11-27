"""Fixed-point bracket grid for the original direct RSI crossing strategy."""
import json
import math
import hashlib
from array import array
from itertools import product
from research_rsi14_80_20_2025 import (
    ROOT, START, END, FEE, TF, INSTRUMENT, dt, signal, candles,
    Candle, IndicatorBook, spec, IndicatorRecorder, export_bundle,
)

STOPS = (100, 200, 300, 500, 1000)
TARGETS = (200, 500, 600, 1000, 2000)

def path(o,h,l,c):
    if c > o or (c == o and o-l <= h-o):
        return (o,l,h,c)
    return (o,h,l,c)

def bracket(side, stop, target, o,h,l,c):
    # An adverse stop gap fills at the open; a favorable target gap
    # receives the limit price, with no assumed price improvement.
    if side*(o-stop) <= 0:
        return o, "Stop loss gap"
    if side*(o-target) >= 0:
        return target, "Take profit gap"
    seq = path(o,h,l,c)
    for a,b in zip(seq,seq[1:]):
        if side*(b-a) < 0 and min(a,b) <= stop <= max(a,b):
            return stop, "Stop loss"
        if side*(b-a) > 0 and min(a,b) <= target <= max(a,b):
            return target, "Take profit"
    return None

def replay(sigs, bars, sl, tp):
    O,H,L,C = bars
    trades = []
    next_free = 0
    for i,side,rsi in sigs:
        if i < next_free:
            continue
        ep = O[i]
        stop, target = ep-side*sl, ep+side*tp
        for j in range(i,len(O)):
            # Fast path: a minute that touches neither boundary cannot fill.
            if (L[j] <= stop or H[j] >= target) if side==1 else (H[j] >= stop or L[j] <= target):
                fill = bracket(side,stop,target,O[j],H[j],L[j],C[j])
                if fill:
                    xp,reason = fill
                    xt = START+j*60
                    break
        else:
            j = len(O)-1
            xp, reason, xt = C[j], "End of 2025 evaluation", END
        next_free = j+1
        et = START+i*60
        gross = side*(xp-ep)
        fee = (ep+xp)*FEE
        trades.append(dict(entry_utc=dt(et).isoformat(), trigger_utc=dt(et).isoformat(),
            exit_utc=dt(xt).isoformat(), side=side, entry_price=ep, exit_price=xp,
            stop_price=stop, target_price=target, gross_points=gross, fee_points=fee,
            net_points=gross-fee, assumed_slippage_points=0, exit_reason=reason,
            entry_reason="RSI14 crosses above 80" if side==1 else "RSI14 crosses below 20",
            signal_context={"rsi14":rsi,"intraminute_exit_timestamp":"execution bar open label"},
            indicator_values={"indicator_0":rsi}))
    net = math.fsum(t["net_points"] for t in trades)
    wins = sum(t["net_points"]>0 for t in trades)
    gain = math.fsum(max(0,t["net_points"]) for t in trades)
    loss = -math.fsum(min(0,t["net_points"]) for t in trades)
    equity=peak=dd=0.0
    monthly={f"2025-{m:02d}":0.0 for m in range(1,13)}
    for t in trades:
        equity+=t["net_points"]; peak=max(peak,equity); dd=max(dd,peak-equity)
        monthly[t["entry_utc"][:7]]+=t["net_points"]
    summary=dict(accounting="realized",open_position=None,trades=len(trades),net=net,wins=wins,
        win_rate=100*wins/len(trades) if trades else 0,profit_factor=gain/loss if loss else None,
        realized_drawdown_points=dd,monthly_entry_attribution=monthly,profitable_months=sum(v>0 for v in monthly.values()),
        tp_exits=sum(t["exit_reason"].startswith("Take profit") for t in trades),
        sl_exits=sum(t["exit_reason"].startswith("Stop loss") for t in trades))
    return dict(key=f"sl{sl}-tp{tp}",name=f"15M RSI14 80/20 | SL {sl} TP {tp}",
        parameters=dict(rsi_period=14,long_threshold=80,short_threshold=20,stop_loss=sl,take_profit=tp,
            signal="completed 15m",execution="next 1m open; Color OHLC path",exit="fixed bracket only",
            trading_days="all",opposite_signals_while_open="ignored"),summary=summary,trades=trades)

def run():
    assert bracket(1,90,110,100,115,85,105)==(90,"Stop loss")
    assert bracket(1,90,110,100,115,85,95)==(110,"Take profit")
    assert bracket(-1,110,90,100,115,85,105)==(90,"Take profit")
    assert bracket(-1,110,90,100,115,85,95)==(110,"Stop loss")
    assert bracket(1,90,110,85,100,80,95)==(85,"Stop loss gap")
    assert bracket(1,90,110,115,120,100,105)==(110,"Take profit gap")
    assert path(100,112,95,100)==(100,95,112,100)
    assert path(100,105,88,100)==(100,105,88,100)
    book=IndicatorBook((spec("rsi",TF,period=14),),history_limit=2)
    recorder=IndicatorRecorder(book)
    bars=[array("d") for _ in range(4)]
    group=[];sigs=[];prev=None
    for t,o,h,l,c,v in candles():
        for a,val in zip(bars,(o,h,l,c)):a.append(float(val))
        group.append((o,h,l,c,v))
        if len(group)==15:
            end=t+60
            candle=Candle(INSTRUMENT,TF,dt(end-900),dt(end),group[0][0],max(x[1] for x in group),
                min(x[2] for x in group),group[-1][3],sum(x[4] for x in group))
            book.update(candle);recorder.completed(candle)
            current=book.get("rsi",TF,{"period":14})[-1]
            d=signal(prev,current)
            if d and end<END:sigs.append(((end-START)//60,d,float(current)))
            prev=current;group.clear()
    assert not group and len(bars[0])==525600
    variants=[replay(sigs,bars,sl,tp) for sl,tp in product(STOPS,TARGETS)]
    export_bundle("scratch/rsi14_fixed/backtest.json",family="rsi14-fixed-bracket-80-20",symbol="BTCUSD",
        unit="price points",start_utc=dt(START).isoformat(),end_utc=dt(END).isoformat(),
        execution_timeframe_minutes=1,signal_timeframe_minutes=15,
        costs="0.05% taker each side + 18% GST; no Scalper Offer, zero slippage, funding not modeled; fixed unleveraged price points; stop gaps at open, target gaps at limit; no liquidation model.",
        variants=variants,recorder=recorder,
        data_provenance=dict(manifest=str(ROOT/"manifest.json"),manifest_sha256=hashlib.sha256((ROOT/"manifest.json").read_bytes()).hexdigest(),
            input_minutes=525600,timestamp_label="assumed open UTC",warmup="first 15 completed 15m candles in 2025",
            execution_path="Color: bullish OLHC, bearish OHLC, doji nearest extreme first, tie OLHC; intraminute times are bar labels"))
    print("SIGNALS",len(sigs))
    for v in sorted(variants,key=lambda v:v["summary"]["net"],reverse=True):
        s=v["summary"];print("GRID",json.dumps(dict(sl=v["parameters"]["stop_loss"],tp=v["parameters"]["take_profit"],**s),separators=(",",":"),allow_nan=False))

if __name__=="__main__":run()
