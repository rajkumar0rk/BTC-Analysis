"""Frozen R43 simplification, no parameter selection on any period."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from research_btc_step52_r43_profit_fade import dataset, pricing, stats, SC, TZ

OUT=Path("analysis/r43_clean")
def run(validation):
    m,ix,o,h,l,c,v,mh,ml,pre,post,old,slips,modes,days,grid,_,_,_,_,_=dataset(validation)
    local=ix.tz_convert(TZ)
    valid_days=set(days.strftime("%Y-%m-%d"))
    dates=local.strftime("%Y-%m-%d").to_numpy()
    anchors=np.flatnonzero((local.minute==0)&(local.weekday<5))
    rows=[]
    next_free=0
    for j in anchors:
        if j<211 or j<next_free or dates[j] not in valid_days: continue
        if j+5>=len(ix) or ix[j]-ix[j-210]!=pd.Timedelta(minutes=210): continue
        # Remove regime routing and majority votes: direction of completed hour.
        delta=c[j-1]-o[j-60]
        if delta==0: continue
        sd=1 if delta>0 else -1
        hi=h[j-210:j].reshape(14,15).max(axis=1)
        lo=l[j-210:j].reshape(14,15).min(axis=1)
        prev=c[np.arange(j-211,j-1,15)]
        if len(prev)!=14: continue
        atr=np.maximum(hi-lo,np.maximum(abs(hi-prev),abs(lo-prev))).mean()
        ref=c[j-1]
        risk=np.clip(4*atr/ref,.0025,.015)
        dayend=j+((23-local[j].hour)*60+59)
        for z in range(j+5,min(j+60,dayend-1,len(ix)-2)+1,5):
            if z<next_free: continue
            if ix[z]-ix[j]!=pd.Timedelta(minutes=z-j): break
            if sd*(c[z-1]-ref)>-.1*risk*ref or sd*(c[z-1]-o[z-5])<=0: continue
            # Fixed 4R target, no adaptive exits, no fallback; next 1m open.
            en=o[z];stop=en*(1-sd*risk);target=en*(1+sd*4*risk)
            end=min(j+300,dayend,len(ix)-1)
            if end<=z: break
            if ix[end]-ix[z]!=pd.Timedelta(minutes=end-z): break
            ex=o[end];e=end;reason="time"
            for k in range(z,end):
                if sd*(o[k]-stop)<=0: ex=o[k];e=k;reason="stop_gap";break
                if sd*(o[k]-target)>=0: ex=target;e=k;reason="target";break
                hit_s=(l[k]<=stop if sd>0 else h[k]>=stop)
                hit_t=(h[k]>=target if sd>0 else l[k]<=target)
                if hit_s and hit_t:
                    low_first=c[k]>o[k] or (c[k]==o[k] and o[k]-l[k]<=h[k]-o[k])
                    hit_s=(low_first if sd>0 else not low_first)
                    hit_t=not hit_s
                if hit_s: ex=stop;e=k;reason="stop";break
                if hit_t: ex=target;e=k;reason="target";break
            if not(np.isfinite(mh[z:e+1]).all() and np.isfinite(ml[z:e+1]).all()):
                raise ValueError(f"Missing mark coverage {ix[z]}")
            rows.append((z,e,sd,sd*(ex-en),reason,risk))
            next_free=e+1
            break
    ledger=pd.DataFrame(rows,columns=["start","end","side","gross","reason","risk"])
    st=ledger.start.to_numpy(np.int64); en=ledger.end.to_numpy(np.int64)
    sd=ledger.side.to_numpy(np.int8); gg=ledger.gross.to_numpy(float)
    assert len(st)>0 and (st[1:]>en[:-1]).all()
    path=pricing(st,sd,en-st,gg,o,mh,ml,pre,post,old,slips,modes)
    assert np.isfinite(path).all()
    d=local[st]; y=np.asarray(d.year-(2026 if validation else 2024),np.int64)
    mo=np.asarray(y*12+d.month-1,np.int64)
    net,dd,md,monthly,wins=stats(path,y,mo)
    ledger["entry"]=ix[st];ledger["exit"]=ix[en]
    ledger["net_historical5_pct"]=100*path[:,0,0]
    ledger.to_csv(OUT/(("2026" if validation else "2024_2025")+"_ledger.csv"),index=False)
    result={}
    for year in sorted(set(d.year)):
        mask=d.year==year; yi=year-(2026 if validation else 2024)
        expected=days[days.year==year]
        actual=set(d[mask].strftime("%Y-%m-%d"))
        r={}
        for k,(mode,slip) in enumerate(SC):
            x=path[mask,k,0]; months=sorted(set(expected.month))
            mm={str(m):float(100*monthly[yi*12+m-1,k]) for m in months}
            r[f"{mode}_{slip}"]=dict(net_pct=float(100*net[yi,k]),mark_dd_pct=float(100*md[yi,k]),closed_dd_pct=float(100*dd[yi,k]),pf=float(x[x>0].sum()/-x[x<0].sum()) if (x<0).any() else None,win_rate_pct=float(100*wins[yi,k]/mask.sum()),monthly=mm,positive_months=sum(v>0 for v in mm.values()))
        result[str(year)]=dict(trades=int(mask.sum()),days_with_trades=len(actual),eligible_days=len(expected),missing_days=len(expected)-len(actual),max_daily_trades=int(pd.Series(d[mask].strftime("%Y-%m-%d")).value_counts().max()),scenarios=r)
    print("CLEAN_RESULT",json.dumps(result),flush=True)
    return result
if __name__=="__main__":
    OUT.mkdir(parents=True,exist_ok=True)
    a=run(False)
    b=run(True)
    (OUT/"summary.json").write_text(json.dumps({**a,**b},indent=2))
