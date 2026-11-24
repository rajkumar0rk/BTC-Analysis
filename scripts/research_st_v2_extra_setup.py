#!/usr/bin/env python3
"""Third/fourth setup research. Freeze V1 + audited 23-short candidate.
Causal additional 15m flip or EMA20 reclaim, chronological single position.
Prior 108 trades are not reserved using future knowledge: earlier new signals
can block core trades, and those configurations fail post-replay acceptance.
One trade per signed Supertrend cycle; stop first, 1m, fee GST slippage.
All data already seen, exploratory only, not forward validation.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import research_supertrend_15m_line_touch as b
import research_supertrend_15m_filter_grid as f

OUT=Path("analysis/st_v2_extra_setup_month_preservation_20261124")
MONTHS=list(b.MONTHS)
SL=(.5,.75,1.,1.5)
TP=(.25,.3,.4,.5,.75,1.,1.5)
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    minute,bars,files=b.load()
    st,trend=b.supertrend(bars)
    vol,ap,ar=f.build_features(bars)
    baseline=pd.read_csv("analysis/st_v1_short_addon_independent_audit_20261124/independently_verified_108_portfolio_trades.csv").sort_values("entry_idx")
    assert len(baseline)==108 and baseline.st_cycle.is_unique
    assert abs(baseline.net_pts.sum()-22633.90)<.05
    assert (baseline.strategy.value_counts().to_dict()=={"line_touch":67,"short_addon":23,"bullish_flip":18})
    mindex={m:i for i,m in enumerate(MONTHS)}
    im=minute.index.tz_convert("Asia/Kolkata").strftime("%Y-%m").to_numpy()
    core=[(int(v.entry_idx),int(v.exit_idx),int(v.st_cycle),float(v.net_pts),mindex[v.exit_month_ist]) for v in baseline.itertuples()]
    assert all(core[i][0]>core[i-1][1] for i in range(1,len(core)))
    ref=np.bincount([x[4] for x in core],weights=[x[3] for x in core],minlength=22)
    def dd(values):
        e=np.r_[0.,np.cumsum(values)]
        return float((np.maximum.accumulate(e)-e).max())
    base_dd=dd([x[3] for x in core])
    assert abs(base_dd-2642.53)<.05 and sum(ref>0)==18
    o=minute.open.to_numpy(float);h=minute.high.to_numpy(float)
    l=minute.low.to_numpy(float);c=minute.close.to_numpy(float)
    bo=bars.open.to_numpy(float);bc=bars.close.to_numpy(float)
    bh=bars.high.to_numpy(float);bl=bars.low.to_numpy(float)
    ema=bars.close.ewm(span=20,adjust=False).mean().to_numpy()
    # HTF values known at entry; align closed H1 to 15m bar open.
    h1=bars.resample("1h",label="left",closed="left").close.last()
    he=h1.ewm(span=20,adjust=False).mean()
    bull=(h1>he).shift(1).reindex(bars.index,method="ffill").fillna(False).to_numpy(bool)
    bear=(h1<he).shift(1).reindex(bars.index,method="ffill").fillna(False).to_numpy(bool)
    h4=bars.resample("4h",label="left",closed="left").close.last()
    e4=h4.ewm(span=20,adjust=False).mean()
    bull4=(h4>e4).shift(1).reindex(bars.index,method="ffill").fillna(False).to_numpy(bool)
    bear4=(h4<e4).shift(1).reindex(bars.index,method="ffill").fillna(False).to_numpy(bool)
    # Signed cycle ids use same convention as the verified baseline.
    cb=np.cumsum((trend==-1)&np.r_[True,trend[:-1]!=-1])
    cs=np.cumsum((trend==1)&np.r_[True,trend[:-1]!=1])
    bullfail=np.flatnonzero((np.r_[0,trend[:-1]]==-1)&((bc<np.r_[np.nan,st[:-1]])|(trend==1)))
    bearfail=np.flatnonzero((np.r_[0,trend[:-1]]==1)&((bc>np.r_[np.nan,st[:-1]])|(trend==-1)))
    rows=[]
    for i in range(25,len(bars)-1):
        side=1 if trend[i]==-1 else -1
        j=(i+1)*15
        if im[j] not in mindex:continue
        if side==1 and (bc[i]<=bo[i]):continue
        if side==-1 and (bc[i]>=bo[i]):continue
        cycle=int(cb[i]) if side==1 else -int(cs[i])
        failures=bullfail if side==1 else bearfail
        stopidx=np.searchsorted(failures,i+1)
        end=min((int(failures[stopidx])+1)*15,len(o)) if stopidx<len(failures) else len(o)
        if end<=j:continue
        flip=trend[i]!=trend[i-1]
        confirm=trend[i]==trend[i-1] and trend[i-1]!=trend[i-2]
        reclaim=(trend[i]==trend[i-1] and
                 ((side==1 and bl[i]<=ema[i-1] and bc[i]>ema[i]) or
                  (side==-1 and bh[i]>=ema[i-1] and bc[i]<ema[i])))
        breakout=(trend[i]==trend[i-1] and
                  ((side==1 and bc[i]>max(bh[i-12:i])) or
                   (side==-1 and bc[i]<min(bl[i-12:i]))))
        for setup,hit,measure in (("flip",flip,i),("confirm",confirm,i-1),
                                 ("ema20_reclaim",reclaim,i),("range12_break",breakout,i)):
            if not hit:continue
            rows.append((setup,side,j,end,cycle,float(vol[measure]),float(ap[measure]),bool(bull[i+1] if side==1 else bear[i+1]),bool(bull4[i+1] if side==1 else bear4[i+1])))
    rows.sort(key=lambda x:x[2])
    print("ENTRY_CANDIDATES",len(rows),flush=True)
    setups=np.array([r[0] for r in rows]);sides=np.array([r[1] for r in rows])
    volumes=np.array([r[5] for r in rows]);atrs=np.array([r[6] for r in rows])
    align1=np.array([r[7] for r in rows]);align4=np.array([r[8] for r in rows])
    # Precompute exit index / net using only causal entry levels. Stop-first
    # within each 1m OHLC and adverse open if market gaps through stop.
    exits={}
    for k,(setup,side,j,end,cycle,*_) in enumerate(rows):
        entry=o[j]+side*b.SLIP
        adverse=np.maximum.accumulate(h[j:end] if side==-1 else -l[j:end])
        favorable=np.maximum.accumulate(h[j:end] if side==1 else -l[j:end])
        for sl in SL:
            stop=entry*(1-side*sl/100)
            si=np.searchsorted(adverse,-side*stop)
            for tp in TP:
                target=entry*(1+side*tp/100)
                ti=np.searchsorted(favorable,side*target)
                if si<len(adverse) and si<=ti:
                    x=j+int(si);mid=min(o[x],stop) if side==1 else max(o[x],stop)
                elif ti<len(favorable):
                    x=j+int(ti);mid=target
                else:
                    x=end if end<len(o) else len(o)-1
                    mid=o[x] if end<len(o) else c[x]
                fill=mid-side*b.SLIP
                net=side*(fill-entry)-b.FEE*(entry+fill)
                exits[(k,sl,tp)]=(j,x,cycle,float(net),mindex.get(im[x],-1))
    # Existing entry ledger is kept as a chronological competing stream,
    # not a look-ahead veto. Core priority only applies at same timestamp.
    def run(ks,sl,tp,detail=False):
        new=[exits[(int(k),sl,tp)] for k in ks]
        a=i=0; last=-1;used=set();accepted=[];newcount=0;corecount=0
        while a<len(core) or i<len(new):
            iscore=(a<len(core) and (i==len(new) or core[a][0]<=new[i][0]))
            if iscore:r=core[a];a+=1
            else:r=new[i];i+=1
            j,x,cycle,net,m=r
            if j<=last or cycle in used:continue
            if m<0:
                # A trade beyond October is still an executed position;
                # not counted as realized October profit.
                last=x;used.add(cycle)
                if not iscore:newcount+=1
                continue
            last=x;used.add(cycle);accepted.append((r,iscore))
            if iscore:corecount+=1
            else:newcount+=1
        mon=np.bincount([r[4] for r,_ in accepted],weights=[r[3] for r,_ in accepted],minlength=22)
        return mon,dd([r[3] for r,_ in accepted]),corecount,newcount,accepted if detail else None
    results=[];focus={}
    volm={"le0.6":volumes<=.6,"le0.8":volumes<=.8,"le1.0":volumes<=1.,
          "ge1.0":volumes>=1.,"ge1.25":volumes>=1.25}
    htfs={"off":np.ones(len(rows),bool),"H1":align1,"H4":align4,"H1H4":align1&align4}
    seen={}
    for setup in ("flip","confirm","ema20_reclaim","range12_break"):
      for side in (1,-1):
       for vn,vm in volm.items():
        for atr in (.2,.3,.4):
         for hn,hm in htfs.items():
          ks=np.flatnonzero((setups==setup)&(sides==side)&vm&(atrs>=atr)&hm)
          if len(ks)==0:continue
          key=tuple(ks)
          if key in seen:continue
          seen[key]=True
          for sl in SL:
           for tp in TP:
            mon,draw,kept,nnew,_=run(ks,sl,tp)
            delta=mon-ref
            config=f"{setup}|{'long' if side==1 else 'short'}|{vn}|atr{atr}|{hn}|sl{sl}|tp{tp}"
            result=dict(config=config,setup=setup,side=side,volume=vn,atr_pct=atr,htf=hn,sl=sl,tp=tp,
              candidate_signals=len(ks),core_trades_kept=kept,extra_trades=nnew,positive_months=int(sum(mon>0)),
              net_points=round(float(mon.sum()),2),net_2025=round(float(mon[:12].sum()),2),net_2026=round(float(mon[12:].sum()),2),
              max_dd=round(draw,2),original_positive_months_degraded=int(sum((ref>0)&(delta<-.03))),
              any_month_degraded=int(sum(delta<-.03)),negative_months_fixed=int(sum((ref<0)&(mon>0))),
              strict=bool(kept==108 and np.all(delta[ref>0]>=-.03) and mon.sum()>=ref.sum()-.03 and draw<=base_dd+.03),
              strict_all_months=bool(kept==108 and np.all(delta>=-.03) and draw<=base_dd+.03))
            results.append(result)
            if result["strict"] and nnew>0:focus[config]=(ks,sl,tp,mon)
      print("TESTED",setup,len(results),flush=True)
    df=pd.DataFrame(results)
    rank=df.sort_values(["positive_months","net_points"],ascending=False)
    strict=rank[rank.strict&(rank.extra_trades>0)]
    allmonth=strict[strict.strict_all_months]
    df.to_csv(OUT/"all_tested.csv",index=False)
    strict.to_csv(OUT/"strict_candidates.csv",index=False)
    allmonth.to_csv(OUT/"all_months_no_harm.csv",index=False)
    strict_improve=strict[strict.positive_months>18]
    shortlist=list(dict.fromkeys(strict.config.head(5).tolist()+allmonth.config.head(3).tolist()))
    monthly=[];tr=[]
    for name in shortlist:
        ks,sl,tp,mon=focus[name]
        m,draw,kept,nnew,accepted=run(ks,sl,tp,True)
        assert np.array_equal(m,mon)
        for mm,old,new in zip(MONTHS,ref,m):
            monthly.append(dict(config=name,month=mm,baseline=round(old,2),new=round(new,2),delta=round(new-old,2)))
        for r,iscore in accepted:
            if not iscore:tr.append(dict(config=name,entry_idx=r[0],exit_idx=r[1],cycle=r[2],net=r[3],month=MONTHS[r[4]],entry_utc=str(minute.index[r[0]]),exit_utc=str(minute.index[r[1]])))
    pd.DataFrame(monthly).to_csv(OUT/"focus_monthly.csv",index=False)
    pd.DataFrame(tr).to_csv(OUT/"focus_extra_trades.csv",index=False)
    cols=["config","core_trades_kept","extra_trades","positive_months","net_2025","net_2026","net_points","max_dd","any_month_degraded"]
    report=["# V2 independent extra setup: historical no-harm screening","",
       "Original 108 trades: 67 Line Touch LONG, 18 Bullish Flip LONG, 23 Bearish Flip SHORT. Baseline 18/22, +22633.90 points, closed drawdown 2642.53.",
       "Single position and signed ST cycle cap. New entries compete chronologically; a candidate that blocks any original trade fails. No future core-trade reservation. 1m stop-first. Same estimated costs. Deduplicated entry masks, four setup families.",
       "","## Strict candidates",strict[cols].head(20).to_markdown(index=False),
       "","## Strict ALL months nondecreasing",allmonth[cols].head(20).to_markdown(index=False),
       "","## Caveats","All periods previously seen. Multiple comparisons, not independent forward evidence. No funding, liquidation, margin or order-book effects."]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")
    q=dict(tested=len(df),unique_entry_masks=len(seen),strict_new_trade_profiles=len(strict),strict_more_positive_months=len(strict_improve),strict_no_month_degraded=len(allmonth),best_strict_months=int(strict.positive_months.max()) if len(strict) else 18,baseline_108_trades=108,baseline_net=round(float(ref.sum()),2),baseline_dd=round(base_dd,2),independent_forward_validation=False)
    (OUT/"quality.json").write_text(json.dumps(q,indent=2)+"\n")
    print("RESULTS",json.dumps(q),flush=True)
    print(strict[cols].head(10).to_string(index=False),flush=True)
if __name__=="__main__":main()
