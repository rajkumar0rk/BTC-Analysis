"""Five independent baseline families, no grid or 2026 access."""
import csv,gzip,json,math
from pathlib import Path
import numpy as np
from numba import njit
from research_rsi14_depth_stability import y24,y25,q,candles25,checks,summarize,FEE,dt
OUT=Path("scratch/five_independent_strategies")
NAMES=("rsi-trend-pullback","ema20-pullback","failed-breakout","volatility-breakout","vwap-mean-reversion")

@njit
def bracket(O,H,L,C,i,d,risk):
    ep=O[i];sl=ep-d*risk;tp=ep+d*2*risk;mfe=mae=0.
    for j in range(i,len(O)):
        o,h,l,c=O[j],H[j],L[j],C[j]
        if d*(o-sl)<=0:return j,o,1,mfe,max(mae,-d*(o-ep))
        if d*(o-tp)>=0:return j,tp,2,max(mfe,d*(tp-ep)),mae
        mfe=max(mfe,d*(o-ep));mae=max(mae,-d*(o-ep))
        seq=(o,l,h,c) if c>o or (c==o and o-l<=h-o) else (o,h,l,c)
        for k in range(3):
            a,z=seq[k],seq[k+1]
            if d*(z-a)<0:
                if d*(z-sl)<=0:return j,sl,1,mfe,max(mae,risk)
                mae=max(mae,-d*(z-ep))
            elif d*(z-a)>0:
                if d*(z-tp)>=0:return j,tp,2,max(mfe,2*risk),mae
                mfe=max(mfe,d*(z-ep))
    return len(O)-1,C[-1],3,mfe,mae

def unit_checks():
    o=np.array([100.]);h=np.array([125.]);l=np.array([85.])
    assert bracket(o,h,l,np.array([110.]),0,1,10.)[:3]==(0,90.,1)
    assert bracket(o,h,l,np.array([95.]),0,1,10.)[:3]==(0,120.,2)
    assert bracket(o,h,l,np.array([110.]),0,-1,7.)[:3]==(0,86.,2)
    assert bracket(o,h,l,np.array([95.]),0,-1,7.)[:3]==(0,107.,1)
    O=np.array([100.,85.]);H=np.array([105.,90.]);L=np.array([95.,80.]);C=np.array([102.,87.])
    assert bracket(O,H,L,C,0,1,10.)[:3]==(1,85.,1)

def signal_lists(bars,ind,snapshots,extra,start,ev):
    O,H,L,C=bars;volume,_,rsi,_,_,atr=ind
    h=H.reshape(-1,15).max(axis=1);l=L.reshape(-1,15).min(axis=1);c=C[14::15]
    # Daily UTC VWAP approximation using actual 1m exchange candle volume,
    # weighted by 1m typical prices; no tick-level VWAP claimed.
    vwap=np.full(len(c),np.nan);vsum=psum=0.;day=-1
    for j in range(len(O)):
        newday=(start+j*60)//86400
        if newday!=day:day=newday;vsum=psum=0.
        v=volume[j];vsum+=v;psum+=v*(H[j]+L[j]+C[j])/3.
        if j%15==14 and vsum>0:vwap[j//15]=psum/vsum
    out={n:[] for n in NAMES}
    for k in range(41,len(c)):
        i=(k+1)*15
        if i>=len(O) or start+i*60<ev:continue
        a=atr[k+1];ema=snapshots[i][1];prevema=extra[i-15][0]
        if not np.isfinite(a) or a<=0:continue
        up=ema is not None and c[k]>ema;dn=ema is not None and c[k]<ema
        # Entry at the open of the next minute after a completed 15m signal.
        d=1 if up and rsi[k]<=50<rsi[k+1] else -1 if dn and rsi[k]>=50>rsi[k+1] else 0
        if d:out[NAMES[0]].append((i,d,a))
        d=0
        if prevema is not None:
            if up and c[k-1]>prevema and l[k]<=prevema<c[k]:d=1
            elif dn and c[k-1]<prevema and h[k]>=prevema>c[k]:d=-1
        if d:out[NAMES[1]].append((i,d,a))
        hi=float(np.max(h[k-20:k]));lo=float(np.min(l[k-20:k]))
        # Both-sided sweeps are ambiguous, so skip them.
        d=1 if l[k]<lo<c[k]<hi and h[k]<=hi else -1 if h[k]>hi>c[k]>lo and l[k]>=lo else 0
        if d:out[NAMES[2]].append((i,d,a))
        # Previous 15m ATR below its preceding 20 completed ATR observations,
        # then a confirmed close outside the previous 20-bar Donchian range.
        prior=atr[k];avg=np.mean(atr[k-20:k])
        if np.isfinite(avg) and prior<avg:
            d=1 if c[k]>hi else -1 if c[k]<lo else 0
            if d:out[NAMES[3]].append((i,d,a))
        # Cross back inside the +/-1 ATR band around same-day UTC VWAP.
        # Do not compare across midnight resets.
        if (start+i*60-1)//86400==(start+(i-15)*60-1)//86400 and np.isfinite(vwap[k-1]) and np.isfinite(vwap[k]) and np.isfinite(atr[k]):
            zprev=(c[k-1]-vwap[k-1])/atr[k];z=(c[k]-vwap[k])/a
            d=1 if zprev<-1 and -1<=z<0 else -1 if zprev>1 and 0<z<=1 else 0
            if d:out[NAMES[4]].append((i,d,a))
    return out

def replay(bars,signals,start,end):
    O,H,L,C=bars;free=0;ts=[]
    for i,d,a in signals:
        if i<free:continue
        risk=max(.5,math.ceil(2*a*2)/2);ep=float(O[i])
        j,xp,reason,mfe,mae=bracket(O,H,L,C,i,d,risk)
        free=j+1;gross=d*(xp-ep);fee=(ep+xp)*FEE
        ts.append(dict(entry_utc=dt(start+i*60).isoformat(),exit_utc=dt(end if reason==3 else start+j*60).isoformat(),side=d,entry_price=ep,exit_price=float(xp),gross_points=float(gross),fee_points=float(fee),net_points=float(gross-fee),exit_reason={1:"Initial SL",2:"Fixed TP",3:"Evaluation end"}[reason],signal_context=dict(risk_points=float(risk),entry_atr=float(a),mfe=float(mfe),mae=float(mae))))
    return ts

def run():
    checks();unit_checks();OUT.mkdir(parents=True,exist_ok=True)
    results={name:dict(name=name,years={}) for name in NAMES}
    for year in (2024,2025):
        if year==2024:
            q.candles=y24.candles;bars,signals,snapshots,extra,rec=y24.load();start,end,ev=y24.START,y24.END,y24.EVAL
        else:
            q.candles=candles25;bars,signals,snapshots,extra,rec=y25.load();start,end,ev=y25.START,y25.END,y25.START
        ind=q.indicators(bars,snapshots);candidates=signal_lists(bars,ind,snapshots,extra,start,ev)
        for name in NAMES:
            ts=replay(bars,candidates[name],start,end);s=summarize(ts,year);st=summarize(ts,year,50)
            s["signals"]=len(candidates[name]);s["stress"]=dict(net=st["net"],months=st["profitable_months"],pf=st["profit_factor"],dd=st["realized_drawdown_points"])
            s["median_risk"]=float(np.median([t["signal_context"]["risk_points"] for t in ts])) if ts else None
            s["months_1000_points"]=sum(x>=1000 for x in s["monthly_entry_attribution"].values())
            results[name]["years"][year]=dict(summary=s,trades=ts)
        del bars,ind,snapshots,extra,rec
    rows=[]
    for name,v in results.items():
        a,b=[v["years"][y]["summary"] for y in (2024,2025)]
        blocks=[sum(p for m,p in s["monthly_entry_attribution"].items() if (int(m[-2:])>6)==bool(h)) for s in (a,b) for h in (0,1)]
        row=dict(key=name,net24=a["net"],net25=b["net"],net=a["net"]+b["net"],months24=a["profitable_months"],months25=b["profitable_months"],months=a["profitable_months"]+b["profitable_months"],dd24=a["realized_drawdown_points"],dd25=b["realized_drawdown_points"],dd=max(a["realized_drawdown_points"],b["realized_drawdown_points"]),trades24=a["trades"],trades25=b["trades"],pf24=a["profit_factor"],pf25=b["profit_factor"],win24=a["win_rate"],win25=b["win_rate"],stress24=a["stress"]["net"],stress25=b["stress"]["net"],stress_months=a["stress"]["months"]+b["stress"]["months"],positive_blocks=sum(p>0 for p in blocks),blocks=blocks,months_1000_points=a["months_1000_points"]+b["months_1000_points"],fees24=a["fees"],fees25=b["fees"],median_risk24=a["median_risk"],median_risk25=b["median_risk"],accepted=all(x["stress"]["net"]>0 and x["trades"]>=30 for x in (a,b)) and all(p>0 for p in blocks))
        rows.append(row);print("RESULT",json.dumps(row,allow_nan=False))
        print("DETAIL",json.dumps(dict(key=name,years={y:v["years"][y]["summary"] for y in (2024,2025)}),allow_nan=False))
    with (OUT/"results.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    with gzip.open(OUT/"all_results.json.gz","wt") as f:json.dump(results,f,allow_nan=False,separators=(",",":"))
    print("COUNTS",json.dumps(dict(total=len(rows),both_year_positive=sum(x["net24"]>0 and x["net25"]>0 for x in rows),accepted=sum(x["accepted"] for x in rows),max_months=max(x["months"] for x in rows))))
if __name__=="__main__":run()
