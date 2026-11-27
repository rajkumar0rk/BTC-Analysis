"""Six independent entries x four alignment filters x five predeclared exits."""
import csv,gzip,json,math
from pathlib import Path
import numpy as np
from numba import njit
import research_independent_big_move_2024_2025 as base
import research_independent_big_move_mtf_2024_2025 as mtf
OUT=Path("scratch/independent_big_move_exits")
EXITS=("15m-channel","1h-supertrend","1h-atr-trail","1h-channel","4h-trend-reversal")
RULES={
"15m-channel":"Original ratcheting 10 completed 15m candle channel.",
"1h-supertrend":"Fresh completed H1 Supertrend(ATR10,3) flip against position after entry; exit next 1m open.",
"1h-atr-trail":"At each completed H1 boundary after entry, ratchet highest/lowest observed since entry minus/plus 3 H1 ATR14.",
"1h-channel":"Ratchet opposite extreme of last 10 completed H1 candles; 1m stop touch.",
"4h-trend-reversal":"Fresh completed H4 EMA20/50 cross against position after entry; exit next 1m open."
}

def supertrend(f):
    h,l,c,tr=(f[x] for x in ("h","l","c","tr"));n=len(c)
    a=np.full(n,np.nan);upper=a.copy();lower=a.copy();direction=np.zeros(n,dtype=np.int8)
    if n<10:return direction
    a[9]=np.mean(tr[:10]);upper[9]=(h[9]+l[9])/2+3*a[9];lower[9]=(h[9]+l[9])/2-3*a[9]
    direction[9]=-1
    for i in range(10,n):
        a[i]=(9*a[i-1]+tr[i])/10
        u=(h[i]+l[i])/2+3*a[i];b=(h[i]+l[i])/2-3*a[i]
        upper[i]=u if u<upper[i-1] or c[i-1]>upper[i-1] else upper[i-1]
        lower[i]=b if b>lower[i-1] or c[i-1]<lower[i-1] else lower[i-1]
        direction[i]=(1 if c[i]>upper[i] else -1) if direction[i-1]==-1 else (-1 if c[i]<lower[i] else 1)
    return direction

@njit
def exit_trade(O,H,L,C,k,d,initial,mode,st,atr,hi,lo,h4):
    stop=initial;highest=O[k];lowest=O[k]
    for j in range(k,len(O)):
        if j%60==0:
            z=j//60-1
            if z>=0:
                if mode==2 and j>k and np.isfinite(atr[z]):
                    level=highest-3*atr[z] if d==1 else lowest+3*atr[z]
                    stop=max(stop,level) if d==1 else min(stop,level)
                elif mode==3:
                    level=lo[z] if d==1 else hi[z]
                    if np.isfinite(level):stop=max(stop,level) if d==1 else min(stop,level)
        # Stop at opening gap takes priority over a scheduled market exit.
        if d*(O[j]-stop)<=0:return j,O[j],stop,1
        if j>k and mode==1 and j%60==0:
            z=j//60-1
            if z>=1 and st[z]==-d and st[z-1]==d:return j,O[j],stop,3
        if j>k and mode==4 and j%240==0:
            z=j//240-1
            if z>=1 and h4[z]==-d and h4[z-1]==d:return j,O[j],stop,4
        if (d==1 and L[j]<=stop) or (d==-1 and H[j]>=stop):return j,stop,stop,1
        highest=max(highest,H[j]);lowest=min(lowest,L[j])
    return len(O)-1,C[-1],stop,2

def replay(bars,f,sig,name,flt,mode,start,end,h1,st,h4):
    if mode==0:
        v=base.replay(bars,f,sig,name,15,start,end)
    else:
        O,H,L,C=bars;trades=[];free=0
        for i in np.flatnonzero(sig):
            k=(int(i)+1)*15
            if k>=len(O) or k<free:continue
            d=int(sig[i]);ep=float(O[k]);risk=max(base.TICK,math.ceil(2*f["atr"][i]/base.TICK)*base.TICK);initial=ep-d*risk
            j,xp,stop,reason=exit_trade(O,H,L,C,k,d,initial,mode,st,h1["atr"],h1["high10"],h1["low10"],h4)
            free=j+1;gross=d*(float(xp)-ep);fee=(ep+float(xp))*base.FEE;net=gross-fee
            trades.append(dict(entry_utc=base.dt(start+k*60).isoformat(),trigger_utc=base.dt(start+k*60).isoformat(),
                exit_utc=base.dt(end if reason==2 else start+j*60).isoformat(),side=d,entry_price=ep,exit_price=float(xp),stop_price=initial,
                final_stop=float(stop),target_price=None,gross_points=gross,fee_points=fee,net_points=net,net_R=net/risk,
                assumed_slippage_points=0,entry_reason=name,exit_reason={1:"Initial/trailing stop",2:"End of yearly evaluation",3:"H1 Supertrend reversal",4:"H4 EMA reversal"}[reason],
                holding_minutes=int(j-k),signal_context=dict(initial_risk_points=risk,atr14=float(f["atr"][i]),signal_timeframe_minutes=15),indicator_values={}))
        months=[f"{base.dt(start).year}-{m:02d}" for m in range(base.dt(start).month,13)]
        s=base.summarize(trades,months);s["signal_count"]=int(np.count_nonzero(sig))
        v=dict(summary=s,trades=trades,parameters=dict(strategy=name,signal_timeframe_minutes=15,initial_stop="2 ATR14",fixed_tp=None,entry_rule=base.RULES[name]))
    key=f"{name}-15m-{flt}-{EXITS[mode]}";v.update(key=key,name=key)
    v["parameters"].update(trend_filter=flt,exit=EXITS[mode],exit_rule=RULES[EXITS[mode]],trend_rule="Latest completed EMA20 vs EMA50; both agree for dual filter")
    return v

def tests():
    mtf.tests()
    rng=np.random.default_rng(17);c=100+np.cumsum(rng.normal(0,.3,240*60));o=np.r_[c[0],c[:-1]]
    bars=np.array([o,np.maximum(o,c)+.2,np.minimum(o,c)-.2,c])
    a=supertrend(base.features(bars,60));b=supertrend(base.features(bars[:,:240*53],60))
    assert np.array_equal(a[:len(b)],b)
    # H1 opposite flip cannot affect a trade before the hourly candle closes.
    O=np.full(181,100.);H=O+1;L=O-1;C=O.copy()
    st=np.array([1,-1,1],dtype=np.int8);atr=np.array([2.,2.,2.]);hi=O[:3]+10;lo=O[:3]-10;h4=np.zeros(1,dtype=np.int8)
    assert exit_trade(O,H,L,C,60,1,90.,1,st,atr,hi,lo,h4)==(120,100.,90.,3)
    # No lookahead: trail can move only at the boundary, and only uses observed highs since entry.
    H[61]=110.;L[120]=99.
    assert exit_trade(O,H,L,C,60,1,90.,2,st,atr,hi,lo,h4)==(120,100.,104.,1)
    # Entry after prior H1 flip doesn't retroactively close.
    assert exit_trade(O,O+1,O-1,C,120,1,90.,1,st,atr,hi,lo,h4)[3]==2

def run():
    tests();by_year={}
    for year,start,end,reader in ((2024,base.data24.START,base.data24.END,base.data24.candles_2024),(2025,base.data25.START,base.data25.END,base.data25.candles)):
        bars=base.read_bars(reader,start,end)
        f=base.features(bars,15);ss=base.signals(f);align=mtf.filters(bars);h1=base.features(bars,60);st=supertrend(h1)
        close4=bars[3,239::240];e20=base.ema(close4,20);e50=base.ema(close4,50)
        h4=np.where(e20>e50,1,np.where(e20<e50,-1,0)).astype(np.int8)
        by_year[year]=[]
        for name,expected in zip(base.FAMILIES,mtf.EXPECTED[year]):
            for flt in mtf.FILTERS:
                sig=ss[name] if flt=="none" else np.where(ss[name]==align[flt],ss[name],0).astype(np.int8)
                for mode in range(len(EXITS)):
                    v=replay(bars,f,sig,name,flt,mode,start,end,h1,st,h4)
                    if mode==0 and flt=="none":assert math.isclose(v["summary"]["net"],expected,abs_tol=1e-6),v["summary"]
                    by_year[year].append(v)
    variants=[]
    for a,b in zip(by_year[2024],by_year[2025]):
        assert a["key"]==b["key"]
        trades=a["trades"]+b["trades"];months=list(a["summary"]["monthly_entry_attribution"])+list(b["summary"]["monthly_entry_attribution"])
        s=base.summarize(trades,months);s["years"]={"2024":a["summary"],"2025":b["summary"]}
        v=dict(key=a["key"],name=a["name"],parameters=a["parameters"],summary=s,trades=trades)
        variants.append(v)
        # Compact log; full monthly series in artifact.
        fields=("net","net_R","trades","trades_per_month","profitable_months","profitable_R_months","profit_factor","pf_R","realized_drawdown_points","winners_3R","winners_5R","winners_10R","best_trade_R","gross_points","fees")
        compact={k:s[k] for k in fields}
        compact["years"]={y:{k:ys[k] for k in fields} for y,ys in s["years"].items()}
        print("RESULT",v["key"],json.dumps(compact,separators=(",",":"),allow_nan=False))
    assert len(variants)==120
    OUT.mkdir(parents=True,exist_ok=True)
    with gzip.open(OUT/"all_ledgers.json.gz","wt") as f:json.dump(variants,f,separators=(",",":"),allow_nan=False)
    rows=[]
    for v in variants:
        s=v["summary"];row=dict(key=v["key"],**v["parameters"],**{k:x for k,x in s.items() if not isinstance(x,dict)})
        for y,ys in s["years"].items():row.update({y+"_"+k:x for k,x in ys.items() if not isinstance(x,dict)})
        rows.append(row)
    with (OUT/"all_results.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    (OUT/"provenance.json").write_text(json.dumps(dict(families=base.RULES,filters=mtf.FILTERS,exits=RULES,initial_stop="2 ATR14 at 15m entry; fixed unless channel or ATR ratchet",
        period="2024 Feb 1 12 UTC to Jan 1 2025 and full 2025; yearly reset and accounting close",costs="0.05% taker per side +18% GST; no offer; no extra slippage, liquidation or funding",
        execution="completed bars only; next 1m open for entry or reversal; stop monitored every minute; one position, all days",
        selection="120 independent comparisons; 24 baselines, 96 new; 2026 untouched; not independent validation"),indent=2))
    print("TOTAL",len(variants),"PROFITABLE",sum(v["summary"]["net"]>0 for v in variants),"BOTH",sum(all(y["net"]>0 for y in v["summary"]["years"].values()) for v in variants))
if __name__=="__main__":run()
