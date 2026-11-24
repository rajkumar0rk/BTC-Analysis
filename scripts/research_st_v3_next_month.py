#!/usr/bin/env python3
"""Frozen ST V3 plus independent causal realized-loss regime add-on.

All 118 baseline trades retained in accepted candidate. New entries
compete chronologically for one position, not pre-reserved against
future core trades. Any blocked baseline trade disqualifies configuration.
Gate based on realized baseline trade outcomes available strictly before
entry, only; never use future month PnL or specific losing month labels.
Independent add-on uses its own daily/episode caps; the existing ST cycle
cap remains unchanged for original trades. Additional trades can occur
after an original position has closed in its ST cycle.
1m stop-first, gap-aware, .05% fee + GST and 5 point slip each side.
All 22 months already seen, no independent forward validation.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import research_supertrend_15m_line_touch as b
import research_supertrend_15m_filter_grid as f

OUT=Path("analysis/st_v3_next_month_improvement_20261124")
MONTHS=list(b.MONTHS)
SLS=(.25,.4,.6,1.)
TPS=(.3,.5,.75,1.,1.5,2.)
CAPS=(60,240,480)
def dd(vals):
    e=np.r_[0.,np.cumsum(vals)]
    return float((np.maximum.accumulate(e)-e).max())

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    minute,bars,files=b.load()
    core=pd.read_csv("analysis/st_v1_short_addon_independent_audit_20261124/independently_verified_108_portfolio_trades.csv").sort_values("entry_idx")
    assert len(core)==108 and abs(core.net_pts.sum()-22633.9)<.05
    assert core.strategy.value_counts().to_dict()=={"line_touch":67,"short_addon":23,"bullish_flip":18}
    mi={m:i for i,m in enumerate(MONTHS)}
    im=minute.index.tz_convert("Asia/Kolkata").strftime("%Y-%m").to_numpy()
    day=minute.index.tz_convert("Asia/Kolkata").strftime("%Y-%m-%d").to_numpy()
    ref=[(int(v.entry_idx),int(v.exit_idx),float(v.net_pts),mi[v.exit_month_ist]) for v in core.itertuples()]
    # Exact V3 benchmark: V2 trades plus the published 10 Bollinger trades.
    addon=pd.read_csv("analysis/st_v2_causal_loss_regime_addon_20261124/extra_trades.csv")
    addon=addon[addon.config=="bollinger_stretch|dir-1|gate3|aligned|ATR0.3|sl1.0|tp1.0|cap240|ep2"]
    assert len(addon)==10
    for v in addon.itertuples():
        j=minute.index.get_loc(pd.Timestamp(v.entry_utc))
        x=minute.index.get_loc(pd.Timestamp(v.exit_utc))
        ref.append((int(j),int(x),float(v.net),mi[v.month]))
    ref.sort(key=lambda r:r[0])
    assert len(ref)==118
    base=np.bincount([r[3] for r in ref],weights=[r[2] for r in ref],minlength=22)
    assert abs(base.sum()-26452.29)<.05
    ck=pd.read_csv("analysis/st_v2_causal_loss_regime_addon_20261124/monthly.csv")
    ck=ck[ck.config=="bollinger_stretch|dir-1|gate3|aligned|ATR0.3|sl1.0|tp1.0|cap240|ep2"].set_index("month")
    assert len(ck)==22 and np.all(np.abs(ck.loc[MONTHS,"new"].to_numpy(float)-base)<.04)

    base_dd=dd([r[2] for r in ref])
    assert sum(base>0)==19 and abs(base_dd-2392.53)<.05
    assert all(ref[i][0]>ref[i-1][1] for i in range(1,len(ref)))
    op=minute.open.to_numpy(float);hi=minute.high.to_numpy(float)
    lo=minute.low.to_numpy(float);cl=minute.close.to_numpy(float)
    n=len(op)
    bo=bars.open.to_numpy(float);bc=bars.close.to_numpy(float)
    bh=bars.high.to_numpy(float);bl=bars.low.to_numpy(float)
    vol,ap,_=f.build_features(bars)
    close=bars.close
    ema=close.ewm(span=20,adjust=False).mean().to_numpy()
    d=close.diff()
    g=d.clip(lower=0).ewm(alpha=.5,adjust=False,min_periods=2).mean()
    loss=(-d.clip(upper=0)).ewm(alpha=.5,adjust=False,min_periods=2).mean()
    rsi=(100*g/(g+loss).replace(0,np.nan)).to_numpy()
    mean=close.rolling(20).mean().to_numpy()
    std=close.rolling(20).std(ddof=0).to_numpy()
    z=(bc-mean)/np.maximum(std,1e-10)
    h1=bars.resample("1h",label="left",closed="left").close.last()
    he=h1.ewm(span=20,adjust=False).mean()
    htrend=np.sign(h1-he).shift(1).reindex(bars.index,method="ffill").fillna(0).to_numpy()
    # Compute gate state at candidate entry from ONLY core exits strictly
    # earlier than this instant. If a new trade blocks a core trade the
    # entire scenario is invalid and never admitted. No forward veto.
    exits_sorted=sorted(ref,key=lambda r:r[1])
    rows=[];p=0;month_pnl=np.zeros(22);last=[];loss_event=-1
    for i in range(25,len(bars)-1):
        j=(i+1)*15
        if im[j] not in mi:continue
        m=mi[im[j]]
        while p<len(exits_sorted) and exits_sorted[p][1]<j:
            x=exits_sorted[p];month_pnl[x[3]]+=x[2]
            last.append(x)
            if x[2]<0:loss_event=p
            p+=1
        if not last:continue
        latest=last[-1]
        age=j-latest[1]
        if loss_event<0:continue
        last_loss=exits_sorted[loss_event]
        loss_age=j-last_loss[1]
        if loss_age>10*1440:continue
        # Causal gates, evaluated on previous realized exits only.
        gates=(
          latest[2]<0 and age<=360,
          latest[2]<0 and age<=1440,
          latest[2]<0 and age<=3*1440,
          month_pnl[m]<0 and loss_age<=3*1440,
          month_pnl[m]<0 and loss_age<=7*1440,
          sum(q[2] for q in last[-3:])<0 and loss_age<=3*1440,
          month_pnl[m]<-500 and loss_age<=3*1440,
          month_pnl[m]<-500 and loss_age<=7*1440,
          month_pnl[m]<-1000 and loss_age<=7*1440,
          month_pnl[m]<0 and loss_age<=10*1440,
          month_pnl[m]<-500 and loss_age<=10*1440)
        if not any(gates):continue
        # Close-based setups (next 15m opening), independent of ST.
        sig=[]
        if rsi[i]<=5:sig.append(("rsi2_extreme",1))
        if rsi[i]>=95:sig.append(("rsi2_extreme",-1))
        if rsi[i-1]<=10 and rsi[i]>10:sig.append(("rsi2_reversal",1))
        if rsi[i-1]>=90 and rsi[i]<90:sig.append(("rsi2_reversal",-1))
        if z[i]<=-2:sig.append(("bollinger_stretch",1))
        if z[i]>=2:sig.append(("bollinger_stretch",-1))
        if z[i-1]<=-2 and z[i]>-2:sig.append(("bollinger_reenter",1))
        if z[i-1]>=2 and z[i]<2:sig.append(("bollinger_reenter",-1))
        if bc[i]>max(bh[i-12:i]):sig.append(("donchian12",1))
        if bc[i]<min(bl[i-12:i]):sig.append(("donchian12",-1))
        if bl[i]<=ema[i-1] and bc[i]>ema[i] and bc[i]>bo[i]:sig.append(("ema20_reclaim",1))
        if bh[i]>=ema[i-1] and bc[i]<ema[i] and bc[i]<bo[i]:sig.append(("ema20_reclaim",-1))
        # Alternative signal thresholds with no future data.
        if rsi[i-1]<=20 and rsi[i]>20:sig.append(("rsi2_cross20",1))
        if rsi[i-1]>=80 and rsi[i]<80:sig.append(("rsi2_cross20",-1))
        if rsi[i-1]<=5 and rsi[i]>5:sig.append(("rsi2_cross5",1))
        if rsi[i-1]>=95 and rsi[i]<95:sig.append(("rsi2_cross5",-1))
        if z[i]>=1.5:sig.append(("z15_stretch",-1))
        if z[i]<=-1.5:sig.append(("z15_stretch",1))
        if z[i-1]>=1.5 and z[i]<1.5:sig.append(("z15_reenter",-1))
        if z[i-1]<=-1.5 and z[i]>-1.5:sig.append(("z15_reenter",1))
        if z[i]>=2.5:sig.append(("z25_stretch",-1))
        if z[i]<=-2.5:sig.append(("z25_stretch",1))
        if bc[i]>max(bh[i-24:i]):sig.append(("donchian24",1))
        if bc[i]<min(bl[i-24:i]):sig.append(("donchian24",-1))
        for setup,side in sig:
            rows.append((setup,side,j,loss_event,m,str(day[j]),gates,
                 bool(side*htrend[i+1]>0),float(ap[i]),float(vol[i])))
    print("SIGNALS",len(rows),flush=True)
    assert len(rows)>100
    # cache individual 1m executions; horizon cap fixed by known entry.
    replays={}
    for k,r in enumerate(rows):
      setup,side,j,episode,m,date,*_=r
      entry=op[j]+side*b.SLIP
      adverse=np.maximum.accumulate(hi[j:min(j+max(CAPS),n)] if side==-1 else -lo[j:min(j+max(CAPS),n)])
      fav=np.maximum.accumulate(hi[j:min(j+max(CAPS),n)] if side==1 else -lo[j:min(j+max(CAPS),n)])
      for sl in SLS:
       stop=entry*(1-side*sl/100)
       si=int(np.searchsorted(adverse,-side*stop))
       for tp in TPS:
        target=entry*(1+side*tp/100)
        ti=int(np.searchsorted(fav,side*target))
        for cap in CAPS:
          lim=min(cap,n-j)
          if si<lim and si<=ti:
            x=j+si;mid=min(op[x],stop) if side==1 else max(op[x],stop)
          elif ti<lim:x=j+ti;mid=target
          else:
            x=min(j+lim,n-1);mid=op[x] if j+lim<n else cl[x]
          fill=mid-side*b.SLIP
          net=side*(fill-entry)-b.FEE*(entry+fill)
          replays[(k,sl,tp,cap)]=(j,x,float(net),mi.get(im[x],-1),episode,date)
    # Replay one position chronologically; no future core reservation.
    # Add-on cap per realized loss episode and per day. No new position
    # if prior trade remains open. Abort immediately if any original
    # trade is blocked (the profile fails exact preservation).
    def run(ks,sl,tp,cap,episode_cap,detail=False):
      extras=[replays[(int(k),sl,tp,cap)] for k in ks]
      a=i=0;last=-1;accepted=[];counts={};days=set();nextra=0
      while a<len(ref) or i<len(extras):
        iscore=(a<len(ref) and (i==len(extras) or ref[a][0]<=extras[i][0]))
        if iscore:
          j,x,net,m=ref[a];a+=1
          if j<=last:return None
        else:
          j,x,net,m,episode,date=extras[i];i+=1
          if j<=last or date in days or counts.get(episode,0)>=episode_cap:continue
          days.add(date);counts[episode]=counts.get(episode,0)+1;nextra+=1
        last=x
        if m>=0:accepted.append((j,x,net,m,iscore))
      mon=np.bincount([r[3] for r in accepted],weights=[r[2] for r in accepted],minlength=22)
      return mon,dd([r[2] for r in accepted]),nextra,accepted if detail else None
    fam=np.array([r[0] for r in rows]);side=np.array([r[1] for r in rows])
    ga=np.array([r[6] for r in rows],bool);trend=np.array([r[7] for r in rows],bool)
    atr=np.array([r[8] for r in rows]);vols=np.array([r[9] for r in rows])
    results=[];focus={};masks=set();tested=0;blocked=0
    for setup in sorted(set(fam)):
      for direction in (0,1,-1):
       for gate in range(11):
        for ht in ("off","aligned"):
         for vfilter in ("off","ATR0.3","ATR0.4","volume1.0"):
          mask=(fam==setup)&ga[:,gate]
          if direction:mask &= side==direction
          if ht=="aligned":mask &=trend
          if vfilter=="ATR0.3":mask &=atr>=.3
          if vfilter=="ATR0.4":mask &=atr>=.4
          if vfilter=="volume1.0":mask &=vols>=1.
          ks=np.flatnonzero(mask)
          if len(ks)==0:continue
          key=tuple(ks)
          if key in masks:continue
          masks.add(key)
          for sl in SLS:
           for tp in TPS:
            for cap in CAPS:
             for epcap in (1,2):
              tested+=1
              got=run(ks,sl,tp,cap,epcap)
              if got is None:blocked+=1;continue
              mon,draw,count,_=got
              if count==0:continue
              delta=mon-base
              name=f"{setup}|dir{direction}|gate{gate}|{ht}|{vfilter}|sl{sl}|tp{tp}|cap{cap}|ep{epcap}"
              strict=bool(np.all(delta[base>0]>=-.025) and mon.sum()>=base.sum()-.025 and draw<=base_dd+.025)
              strictall=bool(np.all(delta>=-.025) and draw<=base_dd+.025)
              row=dict(config=name,extra_trades=count,positive_months=int(sum(mon>0)),net=round(float(mon.sum()),2),net2025=round(float(mon[:12].sum()),2),net2026=round(float(mon[12:].sum()),2),drawdown=round(draw,2),positive_months_degraded=int(sum((base>0)&(delta<-.025))),all_months_degraded=int(sum(delta<-.025)),fixed_negative_months=int(sum((base<0)&(mon>0))),strict=strict,strict_all=strictall)
              results.append(row)
              if strict:focus[name]=(ks,sl,tp,cap,epcap)
      print("TESTED",setup,tested,"BLOCKED",blocked,flush=True)
    df=pd.DataFrame(results)
    assert len(df)>0
    strict=df[df.strict].sort_values(["positive_months","net"],ascending=False)
    strictall=strict[strict.strict_all]
    df.to_csv(OUT/"core_retained_profiles.csv",index=False)
    strict.to_csv(OUT/"strict_results.csv",index=False)
    strictall.to_csv(OUT/"strict_all_months.csv",index=False)
    monthly=[];tr=[]
    names=list(dict.fromkeys(strict.config.head(10).tolist()+strictall.config.head(5).tolist()))
    for name in names:
      mon,draw,count,accepted=run(*focus[name],detail=True)
      for m,old,new in zip(MONTHS,base,mon):
          monthly.append(dict(config=name,month=m,baseline=round(old,2),new=round(new,2),delta=round(new-old,2)))
      for j,x,net,m,iscore in accepted:
          if not iscore:tr.append(dict(config=name,entry_utc=str(minute.index[j]),exit_utc=str(minute.index[x]),month=MONTHS[m],net=net))
    pd.DataFrame(monthly).to_csv(OUT/"monthly.csv",index=False)
    pd.DataFrame(tr).to_csv(OUT/"extra_trades.csv",index=False)
    q=dict(tested=tested,unique_signal_masks=len(masks),rejected_core_conflict=blocked,nonempty_core_retained=len(df),strict=len(strict),strict_all=len(strictall),strict_improved=int(sum(strict.positive_months>19)),strict_all_improved=int(sum(strictall.positive_months>19)),best_strict_months=int(strict.positive_months.max()) if len(strict) else 19,baseline_net=round(float(base.sum()),2),baseline_drawdown=round(base_dd,2),unseen_holdout=False)
    (OUT/"quality.json").write_text(json.dumps(q,indent=2)+"\n")
    report=["# Frozen V3: causal additional loss-regime setups","",
      "118 original trades, +26452.29, 19/22, DD 2392.53. Independent entry only after recent realized core loss; no hindsight losing-month calendar. All core trades must survive chronological competition. Add-on has one per day and 1/2 per loss episode, may trade after a core position closes in same ST cycle.",
      "","Gate0/1/2: latest core exit negative within 6h/24h/72h; gate3/4: realized current-month core PnL negative and recent loss within 3/7 days; gate5: last 3 core exits sum negative and loss within 3 days. Additional gates6/7/8/9/10: realized month below -500 within 3/7 days, below -1000 within 7 days, below zero within 10 days, below -500 within 10 days. Direction0=both, 1=long, -1=short. Signals at completed 15m close, entry next open. 1m stop-first, fixed time cap. No funding/liquidation or margin model.",
      "","## Strict outcomes",strict.head(25).to_markdown(index=False),"","## All 22 months nondecreasing",strictall.head(25).to_markdown(index=False),"","Entire historical sample previously seen; data-mined exploratory candidates, not forward validation."]
    (OUT/"RESEARCH_REPORT.md").write_text("\n".join(report)+"\n")
    print("RESULTS",json.dumps(q),flush=True)
    print(strict.head(10).to_string(index=False),flush=True)
if __name__=="__main__":main()
