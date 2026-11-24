#!/usr/bin/env python3
"""Small predeclared grid, training 2024/25 only, one frozen validation candidate."""
import sys,inspect,itertools,json,hashlib,os
from pathlib import Path
import numpy as np
import pandas as pd
import research_btc15m_worst_month_loss_pause_20261123 as base
OUT=Path("analysis/btc15m_c05_efficiency_sizing_20261124")
DATA=Path("_repaired/data/delta_india/BTCUSD/2024_verified_archive")
ARCHIVE_COMMIT="edcf60fa0a229108d09772dc6cbe04eb15476291"
TZ="Asia/Kolkata"
# Predeclared efficiency sizing experiment, standard absolute Kaufman ER.
# Two broad windows (4h/8h of 15m bars) and fixed thresholds .2/.4.
# Below threshold retain 25% exposure, never reject a signal.
def config(threshold,weak,fraction=.25,hard=0.,smooth=False,dmi_size=1.,adx_tf=15,rise=0,rise_size=1.,vol_anchor=1.,vol_power=0.,timeout_hours=0,swing_bars=0,swing_buffer=0.,rvol_threshold=0.,rvol_weak=1.,er_bars=0,er_threshold=0.):
    return dict(atr=3.5,rr=3.5,wait=2,flip=False,filter="h4ema50_volmin_0.8",activation=2.5,lock=0.,stage2=0.,lock2=1.,partial_trigger=3. if fraction else 0.,partial_fraction=fraction,trail_atr=0.,adx_min=hard,adx_threshold=threshold,weak_size=weak,smooth=smooth,dmi_size=dmi_size,adx_tf=adx_tf,rise=rise,rise_size=rise_size,vol_anchor=vol_anchor,vol_power=vol_power,timeout_hours=timeout_hours,swing_bars=swing_bars,swing_buffer=swing_buffer,rvol_threshold=rvol_threshold,rvol_weak=rvol_weak,er_bars=er_bars,er_threshold=er_threshold)
GRID=[config(0.,1.,er_bars=n,er_threshold=t) for n in (16,32) for t in (.2,.4)]
GRID += [config(20.,.25),config(0.,1.,hard=20.),config(0.,1.),config(0.,1.,0.)]
SHARDS=6
def date(s):return pd.Timestamp(s,tz=TZ).tz_convert("UTC")
def source24():
    manifest=json.loads((DATA/"manifest.json").read_text())
    assert manifest["synthetic_rows"]==0
    parts={p["month"]:p for p in manifest["months"] if p["series"]=="trade_1m"}
    frames=[]
    for mon in pd.period_range("2024-02","2024-12",freq="M").astype(str):
        p=parts[mon];f=DATA/"trade_1m"/(mon+".csv.gz")
        assert p["missing"]==0 and p["observed"]==p["expected"] and hashlib.sha256(f.read_bytes()).hexdigest()==p["sha256"]
        d=pd.read_csv(f,usecols=["time","open","high","low","close","volume"])
        assert len(d)==p["expected"]
        frames.append(d)
    df=pd.concat(frames,ignore_index=True)
    assert np.array_equal(df.time.to_numpy(np.int64),np.arange(int(date("2024-02-01").timestamp()),int(date("2025-01-01").timestamp()),60))
    df.index=pd.to_datetime(df.time,unit="s",utc=True)
    return df
def source25_26(period):
    root=Path("data/delta_india/BTCUSD/1m")
    manifest=json.loads((root/"manifest.json").read_text())
    lo,hi=("2025-01","2025-12") if period=="2025" else ("2025-12","2026-10")
    parts=[p for p in manifest["partitions"] if lo+".csv.gz"<=p["file"]<=hi+".csv.gz"]
    assert len(parts)==(12 if period=="2025" else 11)
    frames=[]
    for p in parts:
        f=root/p["file"]
        assert hashlib.sha256(f.read_bytes()).hexdigest()==p["sha256_gzip"] and p["missing_minutes"]==0
        d=pd.read_csv(f);assert len(d)==p["observed_candles"];frames.append(d)
    df=pd.concat(frames,ignore_index=True)
    assert np.all(np.diff(df.time.to_numpy(np.int64))==60)
    df.index=pd.to_datetime(df.time,unit="s",utc=True)
    end=date("2026-01-01" if period=="2025" else "2026-11-01")
    return df.loc[df.index<end].copy()
def prep(period):
    if period=="2024":
        df=source24()
        start=date("2024-02-03")
        months=pd.period_range("2024-02","2024-12",freq="M")
    elif period=="2025":
        df=source25_26(period);start=date("2025-01-01");months=pd.period_range("2025-01","2025-12",freq="M")
    else:
        df=source25_26(period);start=date("2026-01-01");months=pd.period_range("2026-01","2026-10",freq="M")
    assert len(df)%15==0
    ema,st,trend,valid=base.st_and_ema(df,base.TF)
    ind=base.make_indicators(df)
    start_i=int(np.searchsorted(df.time.to_numpy(),int(start.timestamp())))
    # ATR14 of completed 15m candles, Wilder smoothing.
    h,l,c=ind["H"],ind["L"],ind["C"]
    prev=np.r_[c[0],c[:-1]]
    tr=np.maximum(h-l,np.maximum(abs(h-prev),abs(l-prev)))
    atr=np.full(len(tr),np.nan);atr[13]=np.mean(tr[:14])
    for j in range(14,len(tr)):atr[j]=(13*atr[j-1]+tr[j])/14
    ind["ATR"]=atr
    close=pd.Series(ind["C"],dtype=float)
    for n in (16,32):
        distance=close.diff(n).abs()
        travel=close.diff().abs().rolling(n,min_periods=n).sum()
        er=(distance/travel.where(travel>0)).where(travel!=0,0.)
        assert ((er.dropna()>=0)&(er.dropna()<=1+1e-10)).all()
        ind[f"er_{n}"]=er.clip(0,1).to_numpy()
    volume=pd.Series(ind["V"],dtype=float)
    assert np.isfinite(volume).all() and (volume>=0).all() and (volume>0).any(), "invalid or unavailable recorded volume"
    prior_mean=volume.shift(1).rolling(20,min_periods=20).mean()
    ind["relative_volume"]=(volume/prior_mean.where(prior_mean>0)).to_numpy()
    for n in (1,4,8):
        ind[f"swing_low_{n}"]=pd.Series(ind["L"]).rolling(n,min_periods=n).min().to_numpy()
        ind[f"swing_high_{n}"]=pd.Series(ind["H"]).rolling(n,min_periods=n).max().to_numpy()
    # Wilder directional movement: first 14 transitions, then Wilder smoothing.
    def wilder(x,start=1):
        out=np.full(len(x),np.nan)
        j=start+13
        out[j]=np.mean(x[start:j+1])
        for k in range(j+1,len(x)):out[k]=(13*out[k-1]+x[k])/14
        return out
    up=np.r_[0.,np.diff(h)];down=np.r_[0.,-np.diff(l)]
    plus=np.where((up>down)&(up>0),up,0.)
    minus=np.where((down>up)&(down>0),down,0.)
    ps=wilder(plus);ms=wilder(minus)
    den=ps+ms
    dx=np.divide(100*abs(ps-ms),den,out=np.zeros(len(den)),where=den>0)
    dx[:14]=np.nan
    ind["adx14"]=wilder(dx,14)
    for n in (1,3,5):
        a=ind["adx14"]
        slope=np.full(len(a),np.nan)
        slope[n:]=a[n:]-a[:-n]
        ind[f"adx_rise_{n}"]=slope
    # +DI > -DI iff smoothed +DM > smoothed -DM (common positive TR denominator).
    ind["dmi_direction"]=ps-ms
    natr=pd.Series(atr/c)
    # Prior 20 calendar days of 15m bars; 10 days minimum warm-up.
    ref=natr.shift(1).rolling(20*96,min_periods=10*96).median()
    ind["relative_vol"]=(natr/ref.where(ref>0)).to_numpy()
    # Confirmed higher timeframe closes only, aligned by UTC epoch.
    times=df.time.to_numpy(np.int64)
    signal_end=times[14::15]+60
    # UTC-aligned complete bars, never include the currently forming HTF bar.
    for minutes in (30,60,240):
        seconds=minutes*60
        tmp=pd.DataFrame({"t":times,"high":df.high.to_numpy(float),"low":df.low.to_numpy(float)})
        tmp["bucket"]=tmp.t//seconds
        g=tmp.groupby("bucket",sort=True).agg(high=("high","max"),low=("low","min"),count=("t","size"))
        g=g[g["count"]==minutes]
        gh=g.high.to_numpy();gl=g.low.to_numpy()
        u=np.r_[0.,np.diff(gh)];d=np.r_[0.,-np.diff(gl)]
        pp=wilder(np.where((u>d)&(u>0),u,0.))
        mm=wilder(np.where((d>u)&(d>0),d,0.))
        denom=pp+mm
        hdx=np.divide(100*abs(pp-mm),denom,out=np.zeros(len(denom)),where=denom>0)
        hdx[:14]=np.nan
        hadx=wilder(hdx,14)
        ends=(g.index.to_numpy(np.int64)+1)*seconds
        idx=np.searchsorted(ends,signal_end,side="right")-1
        mapped=np.full(len(signal_end),np.nan)
        ok=idx>=0
        assert np.all(ends[idx[ok]]<=signal_end[ok])
        mapped[ok]=hadx[idx[ok]]
        ind[f"adx{minutes}"]=mapped
    for hours in (1,4):
        seconds=hours*3600
        tmp=pd.DataFrame({"t":times,"close":df.close.to_numpy(float)})
        tmp["bucket"]=tmp.t//seconds
        grouped=tmp.groupby("bucket",sort=True).agg(close=("close","last"),count=("t","size"))
        grouped=grouped[grouped["count"]==hours*60]
        vals=grouped.close
        avg=vals.ewm(span=50,adjust=False,min_periods=50).mean()
        ends=(grouped.index.to_numpy(np.int64)+1)*seconds
        idx=np.searchsorted(ends,signal_end,side="right")-1
        mapped=np.full(len(signal_end),np.nan)
        ok=idx>=0
        mapped[ok]=(vals-avg).to_numpy()[idx[ok]]
        ind[f"h{hours}ema50"]=mapped
        if hours==4:
            for n in (2,4,8):
                slope=np.full(len(signal_end),np.nan)
                slope[ok]=(avg-avg.shift(n)).to_numpy()[idx[ok]]
                ind[f"h4ema50_slope_{n}"]=slope
    sig={}
    for wait in (2,4,6,8,12):
        q=base.make_signals(df,ema,trend,valid,"reclaim",wait)[0]
        sig[wait]={i:v for i,v in q.items() if i>=start_i}
    return df,ema,st,trend,ind,sig,months.astype(str).tolist()
def engine():
    src=inspect.getsource(base.simulate)
    assert src.count("qty=cash/entry")==1
    src=src.replace("qty=cash/entry",'qty=cash/entry*float(name.split("__P_")[1])/100*size_factor(ind["adx14"][j],side,ind["dmi_direction"][j],ind["adx_rise"][j],ind["relative_vol"][j],ind["relative_volume"][j],ind["efficiency"][j])*swing_risk_cap(R,R_ATR)')
    anchor='                elif risk_mode=="ATR":R=R_ATR*riskmult'
    assert src.count(anchor)==1
    src=src.replace(anchor,"""                elif risk_mode=="ATR":
                    R=R_ATR*riskmult
                    if SWING_BARS>0:
                        boundary=ind[f"swing_low_{SWING_BARS}" if side>0 else f"swing_high_{SWING_BARS}"][j]
                        structural_stop=boundary-side*SWING_BUFFER*R_ATR
                        R=side*(entry-structural_stop)
                        if not side*(raw_open-structural_stop)>0:R=float("nan")""")
    # Partial fills use the same adverse slippage and fee model as the full exit.
    # Keep a single trade ledger row per original entry, aggregating all exit legs.
    def patch(a,b):
        nonlocal src
        assert src.count(a)==1,("partial engine anchor",a)
        src=src.replace(a,b)
    patch('    def close_trade(raw,sec,reason):',"""    def partial_take(raw):
        nonlocal cash
        p=position
        if PARTIAL_FRACTION<=0 or p.get("partial_done",False):return
        side=p["side"]
        level=p["entry"]+side*PARTIAL_TRIGGER*p["R"]
        if side*(raw-level)<0:return
        assert side*(level-p["target"])<0
        qty=p["qty"]*PARTIAL_FRACTION
        assert 0<qty<p["qty"]
        mark(level)
        fill=level*(1-side*SLIP)
        gross=side*qty*(fill-p["entry"])
        fee=FEE*qty*fill
        p["qty"]-=qty
        p["partial_done"]=True
        p["partial_realized"]=gross-fee
        p["partial_fee"]=fee
        cash+=gross-fee
        mark(level)
    def close_trade(raw,sec,reason):""")
    patch('        net=gross-fee_out-p["fee_in"]','        net=gross-fee_out-p["fee_in"]+p.get("partial_realized",0.)')
    patch('fee_gst_usd=p["fee_in"]+fee_out,','fee_gst_usd=p["fee_in"]+fee_out+p.get("partial_fee",0.),partial_exit=bool(p.get("partial_done",False)),')
    # Existing stop/target gap handling has priority. Deadline exit is a market fill
    # at the current open, before any new signal and before reading the minute high/low.
    patch('        if i in signal_indices and position is not None:\n            skipped_entries_due_to_open_position+=1',"""        if position is not None and TIMEOUT_SECONDS>0:
            p=position
            if p["side"]*(raw_open-p["entry"])>=p["R"]:
                p["reached_one_r"]=True
            if sec-p["entry_sec"]>=TIMEOUT_SECONDS and not p.get("reached_one_r",False):
                mark(raw_open)
                close_trade(raw_open,sec,"TIME_INVALIDATION")
        if i in signal_indices and position is not None:
            skipped_entries_due_to_open_position+=1""")
    # Process a reached partial target before the final target, even on a gap.
    patch('                close_trade(position["target"],sec,"TP")','                partial_take(raw_open)\n                close_trade(position["target"],sec,"TP")')
    patch('        path=(raw_open,h[i],l[i],c[i])','        if position is not None:\n            partial_take(raw_open)\n            advance_trail(position,raw_open)\n        path=(raw_open,h[i],l[i],c[i])')
    patch('            if side*(dest-p["target"])>=0:', '            partial_take(dest)\n            if side*(dest-p["target"])>=0:')
    # Evaluate reached protection levels only after observing the path endpoint.
    # Existing stop and target checks remain first; a stop never moves backward.
    anchor='        # An overnight/minute opening price may already cross a rung.'
    assert src.count(anchor)==1
    src=src.replace(anchor, """        if position is not None:
            advance_lock(position,raw_open)
        # An overnight/minute opening price may already cross a rung.""")
    anchor='                mark(dest)\n        if i in monthends:'
    assert src.count(anchor)==1
    src=src.replace(anchor, """                advance_lock(p,dest)
                advance_trail(p,dest)
                mark(dest)
        if i in monthends:""")
    ns=dict(base.__dict__)
    def filter_entry(fil,side,j,ema,ind):
        if fil in ("h1ema50","h4ema50"):return bool(side*ind[fil][j]>0)
        if fil.startswith("h4ema50_vol"):
            if not side*ind["h4ema50"][j]>0:return False
            if ns["ADX_MIN"]>0 and not (ind["adx14"][j]>=ns["ADX_MIN"]):return False
            if ns["RVOL_THRESHOLD"]>0 and ns["RVOL_WEAK"]==0 and not ind["relative_volume"][j]>=ns["RVOL_THRESHOLD"]:return False
            if ns["RISE"]>0 and ns["RISE_SIZE"]==0 and not ind["adx_rise"][j]>0:return False
            if ns["DMI_SIZE"]==0 and not side*ind["dmi_direction"][j]>0:return False
            _,mode,x=fil.split("_");x=float(x)
            v=ind["relative_vol"][j]
            if not np.isfinite(v):return False
            return bool(v>=x if mode=="volmin" else v<=x)
        return base.check_filter(fil,side,j,ema,ind)
    ns["check_filter"]=filter_entry
    def size_factor(adx,side,dmi,rise,vol,rvol,efficiency):
        if ns["ER_THRESHOLD"]>0:
            return 1. if efficiency>=ns["ER_THRESHOLD"] else .25
        if ns["RVOL_THRESHOLD"]>0:
            if rvol>=ns["RVOL_THRESHOLD"]:return 1.
            assert ns["RVOL_WEAK"]>0., "strict volume filter must run before sizing"
            return ns["RVOL_WEAK"]
        if ns["VOL_POWER"]>0.:
            assert np.isfinite(vol) and vol>0., "relative-vol entry filter must be evaluated first"
            return max(.25,min(1.,(ns["VOL_ANCHOR"]/vol)**ns["VOL_POWER"]))

        if ns["RISE"]>0:
            if rise>0:return 1.
            assert ns["RISE_SIZE"]>0., "strict momentum must be filtered before sizing"
            return ns["RISE_SIZE"]
        if ns["DMI_SIZE"]<1.:
            assert ns["ADX_THRESHOLD"]==0.
            if side*dmi>0:return 1.
            assert ns["DMI_SIZE"]>0., "strict DMI must be filtered before sizing"
            return ns["DMI_SIZE"]
        if ns["ADX_THRESHOLD"]<=0:return 1.
        if not np.isfinite(adx):return ns["WEAK_SIZE"]
        if ns["SMOOTH"]:
            assert ns["ADX_THRESHOLD"]>10.
            w=max(0.,min(1.,(adx-10.)/(ns["ADX_THRESHOLD"]-10.)))
            return ns["WEAK_SIZE"]+(1.-ns["WEAK_SIZE"])*w
        return 1. if adx>=ns["ADX_THRESHOLD"] else ns["WEAK_SIZE"]
    ns["size_factor"]=size_factor
    def swing_risk_cap(r,atr):
        if ns["SWING_BARS"]==0:return 1.
        assert np.isfinite(r) and r>0 and atr>0
        return min(1.,3.5*atr/r)
    ns["swing_risk_cap"]=swing_risk_cap
    def advance_lock(p,price):
        side=p["side"]
        favorable=side*(price-p["entry"])
        if ns["TIMEOUT_SECONDS"]>0 and favorable>=p["R"]:p["reached_one_r"]=True
        for trigger,lock in ((ns["ACT"],ns["LOCK"]),(ns["ACT2"],ns["LOCK2"])):
            if trigger<=0 or favorable<trigger*p["R"]:continue
            candidate=p["entry"]+side*lock*p["R"]
            if side*(candidate-p["stop"])<=0:continue
            if p["active"]:p["lock_increase_count"]+=1
            else:p["activation_count"]+=1
            p["stop"]=candidate;p["active"]=True
    def advance_trail(p,price):
        if ns["TRAIL_ATR"]<=0 or not p.get("partial_done",False):return
        side=p["side"]
        # Distance is based on the entry ATR, never on an incomplete candle.
        distance=ns["TRAIL_ATR"]*p["R"]/3.5
        candidate=price-side*distance
        if side*(candidate-p["stop"])>0:
            assert p["active"], "breakeven must already be armed"
            p["stop"]=candidate
            p["lock_increase_count"]+=1
    ns["advance_trail"]=advance_trail
    ns["advance_lock"]=advance_lock
    exec(compile(src,"<simple_core>","exec"),ns);return ns
def replay(ns,data,period,cid,cfg,prof,path,stress=False):
    df,ema,st,trend,ind,sig,months=data
    ns["MONTHS"]=months
    # Select the already-confirmed aligned ADX series for this replay only.
    ind=dict(ind)
    ind["efficiency"]=ind[f"er_{cfg['er_bars']}"] if cfg["er_bars"] else np.zeros(len(ind["C"]))
    if cfg["adx_tf"]!=15:ind["adx14"]=ind[f"adx{cfg['adx_tf']}"]
    ind["adx_rise"]=ind[f"adx_rise_{cfg['rise']}"] if cfg["rise"] else np.zeros(len(ind["adx14"]))
    ns["FEE"]=base.FEE;ns["SLIP"]=base.SLIP*(3 if stress else 1);ns["ACT"]=cfg["activation"];ns["LOCK"]=cfg["lock"];ns["ACT2"]=cfg["stage2"];ns["LOCK2"]=cfg["lock2"];ns["PARTIAL_TRIGGER"]=cfg["partial_trigger"];ns["PARTIAL_FRACTION"]=cfg["partial_fraction"];ns["TRAIL_ATR"]=cfg["trail_atr"];ns["ADX_MIN"]=cfg["adx_min"];ns["ADX_THRESHOLD"]=cfg["adx_threshold"];ns["WEAK_SIZE"]=cfg["weak_size"];ns["SMOOTH"]=cfg["smooth"];ns["DMI_SIZE"]=cfg["dmi_size"];ns["RISE"]=cfg["rise"];ns["RISE_SIZE"]=cfg["rise_size"];ns["VOL_ANCHOR"]=cfg["vol_anchor"];ns["VOL_POWER"]=cfg["vol_power"];ns["TIMEOUT_SECONDS"]=cfg["timeout_hours"]*3600;ns["SWING_BARS"]=cfg["swing_bars"];ns["SWING_BUFFER"]=cfg["swing_buffer"];ns["RVOL_THRESHOLD"]=cfg["rvol_threshold"];ns["RVOL_WEAK"]=cfg["rvol_weak"];ns["ER_THRESHOLD"]=cfg["er_threshold"]
    name=f"C{cid:02d}"+("_FLIPON_" if cfg["flip"] else "_NOFLIP_")+f"__P_{prof}"
    x,m,l=ns["simulate"](df,ema,st,trend,ind,name,(cfg["wait"],cfg["filter"],"ATR",cfg["atr"],cfg["rr"],"none"),sig[cfg["wait"]],path)
    for k in ("profitable_2025_months","profitable_2026_months","return_2025_pct","return_2026_pct"):x.pop(k,None)
    x.update(candidate=cid,period=period,profile=prof,stress=stress,**cfg)
    x["time_invalidation_exits"]=int((l.exit_reason=="TIME_INVALIDATION").sum())
    if cfg["timeout_hours"]==0:assert x["time_invalidation_exits"]==0
    x["geo_month_pct"]=100*((1+x["net_return_pct"]/100)**(1/len(months))-1)
    x["positive_fraction"]=x["profitable_months"]/len(months)
    x["worst_month"]=float(m.monthly_return_pct.min())
    half=m.month_ist.str[:4]+"H"+np.where(m.month_ist.str[5:].astype(int)<=6,"1","2")
    x["worst_half_pct"]=float(((1+m.monthly_return_pct/100).groupby(half).prod()-1).min()*100)
    m=m.assign(candidate=cid,period=period,profile=prof,stress=stress)
    l=l.assign(candidate=cid,period=period,profile=prof,stress=stress)
    return x,m,l
def train():
    OUT.mkdir(parents=True,exist_ok=True)
    i=int(os.environ["SHARD_INDEX"]);ns=engine();rows=[];monthly=[]
    for period in ("2024","2025"):
        data=prep(period)
        for cid,cfg in enumerate(GRID):
            if cid%SHARDS!=i:continue
            for path in base.PATHS:
                for stress in (False,True):
                    x,m,_=replay(ns,data,period,cid,cfg,100,path,stress)
                    rows.append(x);monthly.append(m)
                    print("TRAIN",period,cid,path,stress,x["net_return_pct"],flush=True)
    d=OUT/f"shard_{i}";d.mkdir(parents=True,exist_ok=True)
    pd.DataFrame(rows).to_csv(d/"training.csv",index=False)
    pd.concat(monthly,ignore_index=True).to_csv(d/"monthly.csv",index=False)
def freeze():
    OUT.mkdir(parents=True,exist_ok=True)
    s=pd.concat([pd.read_csv(OUT/f"shard_{i}"/"training.csv") for i in range(SHARDS)],ignore_index=True)
    m=pd.concat([pd.read_csv(OUT/f"shard_{i}"/"monthly.csv") for i in range(SHARDS)],ignore_index=True)
    assert len(s)==len(GRID)*2*2*2
    assert not s.duplicated(["candidate","period","path_assumption","stress"]).any()
    control=len(GRID)-1
    for year,value in [(2024,65.205),(2025,55.5852)]:
        z=s[(s.candidate==control)&(s.period==year)&(~s.stress)&(s.path_assumption=="O-H-L-C")]
        assert len(z)==1 and abs(float(z.net_return_pct.iloc[0])-value)<.015
    for year,value in [(2024,66.7746),(2025,51.2151)]:
        z=s[(s.candidate==control-1)&(s.period==year)&(~s.stress)&(s.path_assumption=="O-H-L-C")]
        assert len(z)==1 and abs(float(z.net_return_pct.iloc[0])-value)<.015
    for year,value in [(2024,37.9503),(2025,71.6078)]:
        z=s[(s.candidate==control-2)&(s.period==year)&(~s.stress)&(s.path_assumption=="O-H-L-C")]
        assert len(z)==1 and abs(float(z.net_return_pct.iloc[0])-value)<.015
    for year,value in [(2024,49.9938),(2025,66.3419)]:
        z=s[(s.candidate==control-3)&(s.period==year)&(~s.stress)&(s.path_assumption=="O-H-L-C")]
        assert len(z)==1 and abs(float(z.net_return_pct.iloc[0])-value)<.015
    # Unchanged ADX sizing control must still match the baseline trade count.
    reference=s[s.candidate==control-1].set_index(["period","stress","path_assumption"]).trades.sort_index()
    for cid in list(range(control-3))+[control-3]:
        z=s[s.candidate==cid].set_index(["period","stress","path_assumption"]).trades.sort_index()
        assert z.equals(reference),("unexpected trade count change",cid)
    s.to_csv(OUT/"training.csv",index=False);m.to_csv(OUT/"training_monthly.csv",index=False)
    a=s.groupby("candidate").agg(min_geo=("geo_month_pct","min"),min_win_fraction=("positive_fraction","min"),max_dd=("max_floating_drawdown_pct","max"),min_trades=("trades","min"),min_net=("net_return_pct","min"),min_half=("worst_half_pct","min")).reset_index()
    a["score"]=a.min_geo-.05*a.max_dd
    # Local stability: one adjacent grid coordinate differs; no isolated winner.
    scores=dict(zip(a.candidate,a.score));positive=dict(zip(a.candidate,a.min_net>0))
    # Neighboring efficiency windows and thresholds, one coordinate changed.
    def neighbors(i):
        if i>=control-3:return [j for j in range(control-3,control+1) if j!=i]
        c=GRID[i];out=[]
        for j,d in enumerate(GRID[:control-3]):
            if i==j:continue
            if (c["er_bars"]==d["er_bars"]) != (c["er_threshold"]==d["er_threshold"]):out.append(j)
        assert len(out)==2
        return out
    a["neighbor_median"]=a.candidate.map(lambda i:float(np.median([scores[j] for j in neighbors(i)])))
    a["neighbor_positive_fraction"]=a.candidate.map(lambda i:float(np.mean([positive[j] for j in neighbors(i)])))
    a["robust_score"]=.5*a.score+.5*a.neighbor_median
    a["neighbor_min_half_positive_fraction"]=a.candidate.map(lambda i:float(np.mean([float(a.loc[a.candidate==j,"min_half"].iloc[0])>0 for j in neighbors(i)])))
    # Same earlier gate, now required under baseline AND stressed execution.
    a["eligible"]=(a.candidate<control-3)&(a.min_half>0)&(a.min_net>0)&(a.min_trades>=8)&(a.max_dd<=25)&(a.neighbor_median>0)&(a.neighbor_positive_fraction>=.5)
    # Require better aggregate training monthly count than unchanged C05,
    # without reducing either year's stressed positive-month count.
    worst_counts=s.groupby(["candidate","period"]).profitable_months.min().unstack()
    control_counts=worst_counts.loc[control]
    a["training_positive_months_worst"]=a.candidate.map(worst_counts.sum(axis=1))
    a["monthly_nonregression"]=a.candidate.map((worst_counts>=control_counts).all(axis=1))
    a["eligible"] &= a.monthly_nonregression & (a.training_positive_months_worst>control_counts.sum())
    a["eligible"] &= a.candidate.map((worst_counts[2024]>=9)&(worst_counts[2025]>=11)) & (a.training_positive_months_worst>=20)
    # Reject a strategy that achieves consistency merely by suppressing most opportunities.
    min_trades=s.groupby(["candidate","period"]).trades.min().unstack()
    a["retains_trade_coverage"]=a.candidate.map((min_trades>=0.7*min_trades.loc[control-1]).all(axis=1))
    a["eligible"] &= a.retains_trade_coverage
    a["eligible"] &= (a.neighbor_positive_fraction==1) & (a.min_net>=float(a.loc[a.candidate==control,"min_net"].iloc[0])) & (a.max_dd<=float(a.loc[a.candidate==control,"max_dd"].iloc[0]))
    a["eligible"] &= a.neighbor_min_half_positive_fraction>=.5
    # Stronger local stability: at least half of neighbors must retain at least
    # 80% of the candidate's worst annual return and be within two profitable months.
    by_id=a.set_index("candidate")
    def stable_fraction(i):
        row=by_id.loc[i]
        return float(np.mean([by_id.loc[j,"min_net"]>=.8*row.min_net and by_id.loc[j,"training_positive_months_worst"]>=row.training_positive_months_worst-2 for j in neighbors(i)]))
    a["neighbor_joint_stability"]=a.candidate.map(stable_fraction)
    a["eligible"] &= a.neighbor_joint_stability>=.5
    a=a.sort_values(["eligible","robust_score","candidate"],ascending=[False,False,True])
    a.to_csv(OUT/"training_ranked.csv",index=False)
    top=a.iloc[0];cid=int(top.candidate)
    frozen=dict(candidate=cid,config=GRID[cid],passes_training_gate=bool(top.eligible),selection="Training only, both years and baseline/stressed costs. Previous gates plus positive returns in all four training half-year segments under both cost scenarios; at least 9 profitable 2024 months and 11 profitable 2025 months, and at least 20 profitable months combined. At least 70% of control trade coverage per training year; at least half of adjacent settings positive in every training half-year; at least half of neighbors must preserve 80% of worst annual return and be within two profitable months; all four controls excluded from new candidate selection. If none qualifies, top candidate diagnostic only.",archive_commit=ARCHIVE_COMMIT,training_periods=["2024-02..12 (first 2 days warmup)","2025-01..12"],prior_2026_exposure=True,grid=GRID,training_sha256=hashlib.sha256((OUT/"training.csv").read_bytes()).hexdigest())
    (OUT/"FROZEN.json").write_text(json.dumps(frozen,indent=2)+"\n")
    print("FROZEN",frozen,flush=True)
def validate():
    f=json.loads((OUT/"FROZEN.json").read_text())
    assert hashlib.sha256((OUT/"training.csv").read_bytes()).hexdigest()==f["training_sha256"]
    cid=f["candidate"];cfg=f["config"];assert cfg==GRID[cid]
    if not f["passes_training_gate"]:
        (OUT/"REPORT.md").write_text("# C05 efficiency sizing training result\n\nNo configuration passed the predefined training robustness gate. 2026 deliberately not replayed; no approved frozen candidate. See training_ranked.csv and FROZEN.json (diagnostic only).\n")
        return
    ns=engine();rows=[];monthly=[];ledger=[]
    # Same selected configuration only. No reranking or fallback based on 2026.
    for period in ("2024","2025","2026"):
        data=prep(period)
        for prof in (80,100):
            for path in base.PATHS:
                for stress in (False,True):
                    x,m,l=replay(ns,data,period,cid,cfg,prof,path,stress)
                    rows.append(x);monthly.append(m);ledger.append(l)
    s=pd.DataFrame(rows);m=pd.concat(monthly,ignore_index=True);l=pd.concat(ledger,ignore_index=True)
    s.to_csv(OUT/"frozen_summary.csv",index=False);m.to_csv(OUT/"frozen_monthly.csv",index=False);l.to_csv(OUT/"frozen_ledger.csv",index=False)
    z=s.groupby(["period","profile","stress"],as_index=False).agg(net=("net_return_pct","min"),dd=("max_floating_drawdown_pct","max"),months=("profitable_months","min"),trades=("trades","min"),wins=("wins","min"),losses=("losses","max"))
    cols=["period","profile","stress","net","dd","months","trades","wins","losses"]
    lines=["# C05 efficiency sizing training / frozen validation","",f"4 efficiency sizing alternatives plus 4 exact controls; 64 training path/cost replays. Selected C{cid:02d}: {cfg}. Training gate passed: {f['passes_training_gate']}.","Training: Feb-Dec 2024 (Feb 1-2 warmup), Jan-Dec 2025 (source starts Jan 1 UTC). Validation: Jan-Oct 2026 (Dec 2025 warmup, no pre-2026 entries). 2026 was examined in previous research, so this is a procedural holdout, not genuinely untouched OOS. No tuning on validation results.","Confirmed H4 EMA50, two-candle first reclaim, relative volatility >=0.8, fixed 3.5ATR14 stop and 3.5R target, fixed partial trigger at 3R, fixed 3.5R final TP, tested causal 15m Wilder ADX exposure scaling and unchanged 2.5R to breakeven lock; fees and adverse slippage charged on each leg, aggregate trade accounting. Zero-R lock is price breakeven before fees and slippage. No adaptive rules. No combined strategies, hedging, monthly or account-history switches. Exposure capped at ordinary profile size; weaker trend positions use fixed fractional size. Baseline costs 0.05% taker per side+GST18%, slip 0.02% per side; stress slip 0.06%. Funding excluded.","",z[cols].to_markdown(index=False),"","## Monthly returns (normal costs, worse of two paths)",m[~m.stress].groupby(["month_ist","profile"]).monthly_return_pct.min().unstack().to_markdown(),""]
    (OUT/"REPORT.md").write_text("\n".join(lines)+"\n")
    print("\n".join(lines),flush=True)
if __name__=="__main__":
    if sys.argv[1]=="train":train()
    elif sys.argv[1]=="freeze":freeze()
    else:validate()
