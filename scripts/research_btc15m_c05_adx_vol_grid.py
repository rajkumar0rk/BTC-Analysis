#!/usr/bin/env python3
"""Small predeclared grid, training 2024/25 only, one frozen validation candidate."""
import sys,inspect,itertools,json,hashlib,os,types
from pathlib import Path
import numpy as np
import pandas as pd
import research_btc15m_worst_month_loss_pause_20261123 as base
OUT=Path("analysis/btc15m_c05_adx_vol_grid_20261125")
DATA=Path("_repaired/data/delta_india/BTCUSD/2024_verified_archive")
ARCHIVE_COMMIT="edcf60fa0a229108d09772dc6cbe04eb15476291"
TZ="Asia/Kolkata"
# Vary ADX sizing threshold and relative ATR eligibility, retaining C05 multipliers.
# Monthly-first ranking; no new entry filters or calendar rules.
def config(threshold,weak,fraction=.25,hard=0.,smooth=False,dmi_size=1.,adx_tf=15,rise=0,rise_size=1.,vol_anchor=1.,vol_power=0.,timeout_hours=0,swing_bars=0,swing_buffer=0.,rvol_threshold=0.,rvol_weak=1.,er_bars=0,er_threshold=0.,early_trigger=0.,early_lock=-1.,age_limit=0,weak_target=0.,h4_exit=0,pre_protection=False,equity_risk=0.,quality_factor=1.,quality_vol=False,linear_floor=-1.,continuous_floor=-1.,breakout_buffer=-1.,limit_offset=-1.,gradual_r=0.,fresh_reset=0,repeat_size=1.,repeat_filter='none',signal_tf=15,first_valid=False,target_rr=3.5,trend_hours=4,vol_min=.8,dmi_ramp=0.,be_activation=2.5,cost_be=False,partial_at=3.,adx_multiplier=0.,dmi_multiplier=0.):
    assert early_trigger>=0 and -1<=early_lock<=0
    assert adx_multiplier in (0.,.125,.25,.375,.5,.75) and dmi_multiplier in (0.,.125,.25,.375,.5,.75)
    assert (adx_multiplier==0.)==(dmi_multiplier==0.)
    assert equity_risk in (0.,.005,.01,.015,.02)
    assert quality_factor in (.25,.5,.75,1.)
    assert linear_floor in (-1.,0.,.2,.5)
    assert continuous_floor in (-1.,.1,.25,.5)
    assert breakout_buffer in (-1.,0.,.1,.2)
    assert limit_offset in (-1.,.1,.2,.3)
    assert gradual_r in (0.,1.5,2.,2.5)
    assert fresh_reset in (0,1,2,4)
    assert repeat_size in (.25,.5,.75,1.)
    assert repeat_filter in ('none','adx','dmi','both')
    assert signal_tf in (5,10,15,30)
    assert target_rr in (1.5,2.,2.5,3.,3.5)
    assert trend_hours in (0,1,2,4)
    assert vol_min in (0.,.4,.6,.8,1.,1.2)
    assert dmi_ramp in (0.,.1,.2,.3)
    assert be_activation in (1.5,2.,2.5)
    assert partial_at in (1.5,2.,2.5,3.)
    assert not cost_be or (quality_factor==.25 and ((fraction in (.25,.5,.75) and target_rr==3.5) or (fraction==0. and target_rr==3.)))
    assert not first_valid or (signal_tf==15 and fresh_reset in (1,2,4) and repeat_filter=='none' and repeat_size==1.)
    assert signal_tf==15 or (fresh_reset==0 and repeat_filter=='none' and limit_offset<0)
    return dict(atr=3.5,rr=target_rr,wait=2,flip=False,filter=f"h{trend_hours}ema50_volmin_{vol_min}",activation=be_activation,lock=0.,stage2=0.,lock2=1.,partial_trigger=partial_at if fraction else 0.,partial_fraction=fraction,trail_atr=0.,adx_min=hard,adx_threshold=threshold,weak_size=weak,smooth=smooth,dmi_size=dmi_size,adx_tf=adx_tf,rise=rise,rise_size=rise_size,vol_anchor=vol_anchor,vol_power=vol_power,timeout_hours=timeout_hours,swing_bars=swing_bars,swing_buffer=swing_buffer,rvol_threshold=rvol_threshold,rvol_weak=rvol_weak,er_bars=er_bars,er_threshold=er_threshold,early_trigger=early_trigger,early_lock=early_lock,age_limit=age_limit,weak_target=weak_target,h4_exit=h4_exit,pre_protection=pre_protection,equity_risk=equity_risk,quality_factor=quality_factor,quality_vol=quality_vol,linear_floor=linear_floor,continuous_floor=continuous_floor,breakout_buffer=breakout_buffer,limit_offset=limit_offset,gradual_r=gradual_r,fresh_reset=fresh_reset,repeat_size=repeat_size,repeat_filter=repeat_filter,signal_tf=signal_tf,first_valid=first_valid,trend_hours=trend_hours,vol_min=vol_min,dmi_ramp=dmi_ramp,cost_be=cost_be,adx_multiplier=adx_multiplier,dmi_multiplier=dmi_multiplier)
ADX_LEVELS=(16.,18.,20.,22.,24.)
VOL_LEVELS=(.4,.6,.8,1.,1.2)
LEVELS=VOL_LEVELS
GRID=[config(a,1.,quality_factor=.25,cost_be=True,adx_multiplier=.25,dmi_multiplier=.125,vol_min=v) for a,v in itertools.product(ADX_LEVELS,VOL_LEVELS)]
CONTROL=12
assert GRID[CONTROL]["adx_threshold"]==20. and GRID[CONTROL]["filter"]=="h4ema50_volmin_0.8"
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
def fresh_signals(ema,trend,valid,ind,reset):
    # Same initial touch/reclaim logic as the reference. After a used or
    # expired attempt, require consecutive entire candles on trend side
    # of EMA20 at both start and close. Only THEN can a new touch qualify.
    h,l,c=ind["H"],ind["L"],ind["C"]
    result={}
    active=0;cycle=0;used=False;pending=None;clear=0;attempt=0
    for j in range(101,len(trend)-1):
        if not valid[j] or not valid[j-1] or not np.isfinite(ema[j-1]) or trend[j]==0:
            pending=None;clear=0;continue
        side=int(trend[j])
        if side!=active:
            active=side;cycle+=1;used=False;pending=None;clear=0;attempt=0;continue
        prev=float(ema[j-1]);end=float(ema[j])
        trend_side=side*(c[j]-prev)>0 and side*(c[j]-end)>0
        other_side=side*(c[j]-prev)<0 and side*(c[j]-end)<0
        if pending is not None:
            if j-pending>2:
                pending=None;clear=0
            elif trend_side:
                # Unique ID per independent pullback, not per ST cycle.
                result[(j+1)*15]=dict(epoch=j,side=side,signal_close_bar=j,cycle=cycle,attempt=attempt,touch_bar=pending)
                pending=None;clear=0
            continue
        if used:
            extreme=l[j] if side>0 else h[j]
            separated=side*(extreme-prev)>0 and side*(extreme-end)>0
            clear=clear+1 if separated else 0
            if clear>=reset:used=False;clear=0
            continue
        if not l[j]<=prev<=h[j]:continue
        used=True;attempt+=1;clear=0
        if other_side:pending=j
    return result

def prep(period,tf=15):
    if period=="2024":
        df=source24()
        start=date("2024-02-03")
        months=pd.period_range("2024-02","2024-12",freq="M")
    elif period=="2025":
        df=source25_26(period);start=date("2025-01-01");months=pd.period_range("2025-01","2025-12",freq="M")
    else:
        df=source25_26(period);start=date("2026-01-01");months=pd.period_range("2026-01","2026-10",freq="M")
    assert len(df)%tf==0 and int(df.time.iloc[0])%(tf*60)==0
    ema,st,trend,valid=base.st_and_ema(df,tf)
    assert valid.all() and len(ema)==len(df)//tf
    def with_tf(fn):
        g=dict(fn.__globals__);g["TF"]=tf
        return types.FunctionType(fn.__code__,g,fn.__name__,fn.__defaults__,fn.__closure__)
    ind=with_tf(base.make_indicators)(df)
    # Running age only: no future flip information. Initial unconfirmed epoch stays old.
    age=np.full(len(trend),np.inf)
    for j in range(1,len(trend)):
        if valid[j] and valid[j-1] and trend[j]!=trend[j-1]:age[j]=1.
        elif valid[j] and valid[j-1]:age[j]=age[j-1]+1.
    ind["trend_age"]=age
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
    ind["dmi_imbalance"]=np.divide(ps-ms,den,out=np.zeros_like(den),where=den>0)
    assert np.all(np.abs(ind["dmi_imbalance"])<=1+1e-12)
    natr=pd.Series(atr/c)
    # Prior 20 calendar days of 15m bars; 10 days minimum warm-up.
    ref=natr.shift(1).rolling(20*1440//tf,min_periods=10*1440//tf).median()
    ind["relative_vol"]=(natr/ref.where(ref>0)).to_numpy()
    # Confirmed higher timeframe closes only, aligned by UTC epoch.
    times=df.time.to_numpy(np.int64)
    signal_end=times[tf-1::tf]+60
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
    for hours in (1,2,4):
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
        assert np.all(ends[idx[ok]]<=signal_end[ok])
        mapped[ok]=(vals-avg).to_numpy()[idx[ok]]
        ind[f"h{hours}ema50"]=mapped
        if hours==4:
            # Distinct previous completed H4 candle, not repeated 15m samples.
            prev=np.full(len(signal_end),np.nan)
            old=idx>=1
            prev[old]=(vals-avg).to_numpy()[idx[old]-1]
            ind["h4ema50_previous"]=prev
            for n in (2,4,8):
                slope=np.full(len(signal_end),np.nan)
                slope[ok]=(avg-avg.shift(n)).to_numpy()[idx[ok]]
                ind[f"h4ema50_slope_{n}"]=slope
    sig={}
    for wait in (2,4,6,8,12):
        q=with_tf(base.make_signals)(df,ema,trend,valid,"reclaim",wait)[0]
        sig[wait]={i:v for i,v in q.items() if i>=start_i}
    for reset in ((1,2,4) if tf==15 else ()):
        q=fresh_signals(ema,trend,valid,ind,reset)
        q={i:v for i,v in q.items() if i>=start_i}
        # Every valid original signal still appears at exactly the same time
        # and side; no future knowledge and no duplicate pullback IDs.
        assert set(sig[2]).issubset(q)
        assert all(q[i]["side"]==v["side"] and q[i]["attempt"]==1 for i,v in sig[2].items())
        assert len({v["epoch"] for v in q.values()})==len(q)
        assert all(1<=v["signal_close_bar"]-v["touch_bar"]<=2 for v in q.values())
        sig[f"fresh_{reset}"]=q
    assert all(i%tf==0 and v["signal_close_bar"]==i//tf-1 and v["side"]==trend[i//tf-1] for i,v in sig[2].items())
    return df,ema,st,trend,ind,sig,months.astype(str).tolist()
def engine():
    src=inspect.getsource(base.simulate)
    assert src.count("qty=cash/entry")==1
    src=src.replace("qty=cash/entry",'qty=cash/entry*float(name.split("__P_")[1])/100*size_factor(ind["adx14"][j],side,ind["dmi_direction"][j],ind["adx_rise"][j],ind["relative_vol"][j],ind["relative_volume"][j],ind["efficiency"][j],ind["trend_age"][j],ind["dmi_imbalance"][j])*swing_risk_cap(R,R_ATR)*(REPEAT_SIZE if sig.get("attempt",1)>1 else 1.)')
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
    patch('                target=(float("inf") if side>0 else float("-inf")) if tp_off else entry+side*tpR*R',"""                weak_target_used=bool(WEAK_TARGET>0 and ind["adx14"][j]<20.)
                target_r=WEAK_TARGET if weak_target_used else tpR
                target=(float("inf") if side>0 else float("-inf")) if tp_off else entry+side*target_r*R""")
    patch('stop=stop,initial_stop=stop,target=target,entry_sec=sec,epoch=sig["epoch"],','stop=stop,initial_stop=stop,target=target,entry_sec=sec,epoch=sig["epoch"],weak_target_used=weak_target_used,target_r=target_r,planned_risk_pct=planned_risk_pct,entry_exposure_pct=entry_exposure_pct,')
    patch('                    fee_in=FEE*qty*entry',"""                    # Estimate loss at the original stop, inclusive of both fees
                    # and adverse stop slippage. Entry is already slip-adjusted.
                    stop_fill=stop*(1-side*SLIP)
                    loss_per_unit=side*(entry-stop_fill)+FEE*(entry+stop_fill)
                    assert np.isfinite(loss_per_unit) and loss_per_unit>0
                    if EQUITY_RISK>0:
                        qty=min(qty,cash*EQUITY_RISK/loss_per_unit)
                    planned_risk_pct=100*qty*loss_per_unit/cash
                    entry_exposure_pct=100*qty*entry/cash
                    assert 0<entry_exposure_pct<=100+1e-8
                    if EQUITY_RISK>0:assert planned_risk_pct<=100*EQUITY_RISK+1e-8
                    fee_in=FEE*qty*entry""")
    patch('    def close_trade(raw,sec,reason):',"""    def partial_take(raw):
        nonlocal cash
        p=position
        if PARTIAL_FRACTION<=0 or p.get("partial_done",False) or PARTIAL_TRIGGER>=p["target_r"]:return
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
    patch('fee_gst_usd=p["fee_in"]+fee_out,','fee_gst_usd=p["fee_in"]+fee_out+p.get("partial_fee",0.),partial_exit=bool(p.get("partial_done",False)),early_risk_reduced=bool(p.get("early_risk_reduced",False)),weak_target_used=p["weak_target_used"],target_r=p["target_r"],planned_risk_pct=p["planned_risk_pct"],entry_exposure_pct=p["entry_exposure_pct"],gradual_updates=p.get("gradual_updates",0),')
    # Existing stop/target gap handling has priority. Deadline exit is a market fill
    # at the current open, before any new signal and before reading the minute high/low.
    patch('        if i in signal_indices and position is not None:\n            skipped_entries_due_to_open_position+=1',"""        # Check only at the first minute of a newly completed UTC H4 bar.
        # At this open, old gap stops/targets have already been processed.
        if position is not None and H4_EXIT>0 and sec%14400==0:
            assert i%TF==0 and tm[i-1]+60==sec
            p=position
            wrong=p["side"]*ind["h4ema50"][done]<0
            prior_wrong=p["side"]*ind["h4ema50_previous"][done]<0
            if wrong and (H4_EXIT==1 or prior_wrong) and (not PRE_PROTECTION or not p["active"]):
                mark(raw_open)
                close_trade(raw_open,sec,"H4_INVALIDATION")
        if position is not None and TIMEOUT_SECONDS>0:
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
    # Resting order lifecycle: placement when flat, no later entry if blocked
    # by an existing position at original signal. Only the post-fill path remains.
    patch('    event_indices=sorted(signal_indices|set(monthends))',"""    event_indices=sorted(signal_indices|set(monthends)|set(LIMIT_ORIGINS))
    blocked_limit_epochs=set()
    executed_cycles=set()""")
    patch('        if i in signal_indices and position is not None:\n            skipped_entries_due_to_open_position+=1',"""        entry_path=None
        if i in LIMIT_ORIGINS and position is not None:
            blocked_limit_epochs.add(LIMIT_ORIGINS[i])
        if i in signal_indices and position is not None:
            skipped_entries_due_to_open_position+=1""")
    patch('        if i in signal_indices and position is None and cash>0 and not monthly_halted and not block_entry:',"""        if i in signal_indices and position is None and cash>0 and not monthly_halted and not block_entry and signals[i]["epoch"] not in blocked_limit_epochs and (not FIRST_VALID or signals[i]["cycle"] not in executed_cycles):""")
    patch('                entry=raw_open*(1+side*SLIP)',"""                if "limit_price" in sig:
                    entry=float(sig["limit_price"])
                else:
                    entry=raw_open*(1+side*SLIP)""")
    patch('                    signal_used+=1',"""                    signal_used+=1
                    if FIRST_VALID:
                        assert sig["cycle"] not in executed_cycles
                        executed_cycles.add(sig["cycle"])
                    if "limit_path" in sig:
                        entry_path=tuple(sig["limit_path"])
                        raw_open=entry_path[0]
                        if side*(raw_open-stop)<=0:
                            close_trade(raw_open,sec,"STOP_GAP")""")
    patch('        mark(path[0])\n        for k in range(3):',"""        if entry_path is not None:path=entry_path
        mark(path[0])
        for k in range(len(path)-1):""")
    ns=dict(base.__dict__)
    def filter_entry(fil,side,j,ema,ind):
        if fil in ("h1ema50","h4ema50"):return bool(side*ind[fil][j]>0)
        if fil.startswith(("h0ema50_vol","h1ema50_vol","h2ema50_vol","h4ema50_vol")):
            trend_key=fil.split("_")[0]
            if trend_key!="h0ema50" and not side*ind[trend_key][j]>0:return False
            if ns["ADX_MIN"]>0 and not (ind["adx14"][j]>=ns["ADX_MIN"]):return False
            if ns["LINEAR_FLOOR"]==0. and ind["adx14"][j]<20. and side*ind["dmi_direction"][j]<=0.:return False
            if ns["RVOL_THRESHOLD"]>0 and ns["RVOL_WEAK"]==0 and not ind["relative_volume"][j]>=ns["RVOL_THRESHOLD"]:return False
            if ns["RISE"]>0 and ns["RISE_SIZE"]==0 and not ind["adx_rise"][j]>0:return False
            if ns["DMI_SIZE"]==0 and not side*ind["dmi_direction"][j]>0:return False
            _,mode,x=fil.split("_");x=float(x)
            v=ind["relative_vol"][j]
            if not np.isfinite(v):return False
            return bool(v>=x if mode=="volmin" else v<=x)
        return base.check_filter(fil,side,j,ema,ind)
    ns["check_filter"]=filter_entry
    def size_factor(adx,side,dmi,rise,vol,rvol,efficiency,age,imbalance):
        if ns["ADX_MULTIPLIER"]>0.:
            assert np.isfinite(adx) and np.isfinite(dmi)
            return (1. if adx>=ns["ADX_THRESHOLD"] else ns["ADX_MULTIPLIER"])*(1. if side*dmi>0. else ns["DMI_MULTIPLIER"])
        if ns["DMI_RAMP"]>0.:
            assert np.isfinite(adx) and np.isfinite(imbalance)
            alignment=max(0.,min(1.,side*imbalance/ns["DMI_RAMP"]))
            return (1. if adx>=20. else .25)*(.25+.75*alignment)
        if ns["CONTINUOUS_FLOOR"]>=0.:
            assert np.isfinite(adx) and np.isfinite(dmi)
            strength=max(0.,min(1.,(adx-10.)/20.))
            alignment=float(side*dmi>0.)
            f=ns["CONTINUOUS_FLOOR"]
            return f+(1.-f)*(strength+alignment)/2.
        if ns["LINEAR_FLOOR"]>=0.:
            assert np.isfinite(adx) and np.isfinite(dmi)
            confirmations=int(adx>=20.)+int(side*dmi>0.)
            f=ns["LINEAR_FLOOR"]
            w=f+(1.-f)*confirmations/2.
            assert 0.<w<=1., "zero exposure must be filtered before entry"
            return w
        if ns["QUALITY_FACTOR"]<1.:
            assert np.isfinite(adx) and np.isfinite(dmi)
            failures=int(adx<20.)+int(side*dmi<=0.)
            if ns["QUALITY_VOL"]:
                assert np.isfinite(vol) and vol>=.8
                failures+=int(vol<1.)
            return ns["QUALITY_FACTOR"]**failures
        if ns["AGE_LIMIT"]>0:return 1. if age<=ns["AGE_LIMIT"] else .25
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
        # The early stop is still a loss stop, not a breakeven activation.
        # Keep the original active flag until the original protection fires.
        if ns["EARLY_TRIGGER"]>0 and favorable>=ns["EARLY_TRIGGER"]*p["R"]:
            candidate=p["entry"]+side*ns["EARLY_LOCK"]*p["R"]
            if side*(candidate-p["stop"])>0:
                assert not p["active"]
                p["stop"]=candidate
                p["early_risk_reduced"]=True
        for trigger,lock in ((ns["ACT"],ns["LOCK"]),(ns["ACT2"],ns["LOCK2"])):
            if trigger<=0 or trigger>=p["target_r"] or favorable<trigger*p["R"]:continue
            candidate=p["entry"]+side*lock*p["R"]
            if ns["COST_BE"] and lock==0.:
                # Entry is the adverse slipped fill. Solve zero net PnL for the
                # exit fill inclusive of both fees, then invert exit slippage.
                fill=p["entry"]*(side+ns["FEE"])/(side-ns["FEE"])
                candidate=fill/(1-side*ns["SLIP"])
                assert abs(side*(fill-p["entry"])-ns["FEE"]*(p["entry"]+fill))<1e-8
                assert side*(candidate-p["entry"])>0
                # Do not place a protective stop beyond the observed price.
                if side*(price-candidate)<0:continue
            if side*(candidate-p["stop"])<=0:continue
            if p["active"]:p["lock_increase_count"]+=1
            else:p["activation_count"]+=1
            p["stop"]=candidate;p["active"]=True
        # A favorable endpoint has been observed before advancing the stop.
        # Old stop/target handling remains first in the simulator. Never loosen.
        if ns["GRADUAL_R"]>0 and p["active"]:
            candidate=price-side*ns["GRADUAL_R"]*p["R"]
            if side*(candidate-p["stop"])>1e-10:
                assert side*(candidate-p["entry"])>=-1e-10
                p["stop"]=candidate
                p["lock_increase_count"]+=1
                p["gradual_updates"]=p.get("gradual_updates",0)+1
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
    ns["TF"]=cfg["signal_tf"]
    assert len(df)==len(ema)*ns["TF"]
    # Select the already-confirmed aligned ADX series for this replay only.
    ind=dict(ind)
    ind["efficiency"]=ind[f"er_{cfg['er_bars']}"] if cfg["er_bars"] else np.zeros(len(ind["C"]))
    if cfg["adx_tf"]!=15:ind["adx14"]=ind[f"adx{cfg['adx_tf']}"]
    ind["adx_rise"]=ind[f"adx_rise_{cfg['rise']}"] if cfg["rise"] else np.zeros(len(ind["adx14"]))
    ns["FEE"]=base.FEE;ns["SLIP"]=base.SLIP*(3 if stress else 1);ns["ACT"]=cfg["activation"];ns["LOCK"]=cfg["lock"];ns["ACT2"]=cfg["stage2"];ns["LOCK2"]=cfg["lock2"];ns["PARTIAL_TRIGGER"]=cfg["partial_trigger"];ns["PARTIAL_FRACTION"]=cfg["partial_fraction"];ns["TRAIL_ATR"]=cfg["trail_atr"];ns["ADX_MIN"]=cfg["adx_min"];ns["ADX_THRESHOLD"]=cfg["adx_threshold"];ns["WEAK_SIZE"]=cfg["weak_size"];ns["SMOOTH"]=cfg["smooth"];ns["DMI_SIZE"]=cfg["dmi_size"];ns["RISE"]=cfg["rise"];ns["RISE_SIZE"]=cfg["rise_size"];ns["VOL_ANCHOR"]=cfg["vol_anchor"];ns["VOL_POWER"]=cfg["vol_power"];ns["TIMEOUT_SECONDS"]=cfg["timeout_hours"]*3600;ns["SWING_BARS"]=cfg["swing_bars"];ns["SWING_BUFFER"]=cfg["swing_buffer"];ns["RVOL_THRESHOLD"]=cfg["rvol_threshold"];ns["RVOL_WEAK"]=cfg["rvol_weak"];ns["ER_THRESHOLD"]=cfg["er_threshold"];ns["EARLY_TRIGGER"]=cfg["early_trigger"];ns["EARLY_LOCK"]=cfg["early_lock"];ns["AGE_LIMIT"]=cfg["age_limit"];ns["WEAK_TARGET"]=cfg["weak_target"];ns["H4_EXIT"]=cfg["h4_exit"];ns["PRE_PROTECTION"]=cfg["pre_protection"];ns["EQUITY_RISK"]=cfg["equity_risk"];ns["QUALITY_FACTOR"]=cfg["quality_factor"];ns["QUALITY_VOL"]=cfg["quality_vol"];ns["LINEAR_FLOOR"]=cfg["linear_floor"];ns["CONTINUOUS_FLOOR"]=cfg["continuous_floor"];ns["GRADUAL_R"]=cfg["gradual_r"];ns["REPEAT_SIZE"]=cfg["repeat_size"];ns["FIRST_VALID"]=cfg["first_valid"];ns["DMI_RAMP"]=cfg["dmi_ramp"];ns["COST_BE"]=cfg["cost_be"];ns["ADX_MULTIPLIER"]=cfg["adx_multiplier"];ns["DMI_MULTIPLIER"]=cfg["dmi_multiplier"]
    name=f"C{cid:02d}"+("_FLIPON_" if cfg["flip"] else "_NOFLIP_")+f"__P_{prof}"
    original=sig[cfg["wait"]]
    signals=sig[f"fresh_{cfg['fresh_reset']}"] if cfg["fresh_reset"] else original
    raw_signals=signals
    if cfg["repeat_filter"]!="none":
        def repeat_eligible(v):
            if v["attempt"]==1:return True
            j=v["signal_close_bar"];side=v["side"]
            adx_ok=bool(ind["adx14"][j]>=20.)
            dmi_ok=bool(side*ind["dmi_direction"][j]>0.)
            return {"adx":adx_ok,"dmi":dmi_ok,"both":adx_ok and dmi_ok}[cfg["repeat_filter"]]
        signals={i:v for i,v in raw_signals.items() if repeat_eligible(v)}
        assert set(original).issubset(signals)
        assert all(raw_signals[i]["attempt"]>1 for i in raw_signals.keys()-signals.keys())
    qualified=confirmed=expired=0
    entry_delays={}
    limit_prices={}
    ns["LIMIT_ORIGINS"]={}
    if cfg["limit_offset"]>=0.:
        signals={}
        op=df.open.to_numpy(float);hi=df.high.to_numpy(float);lo=df.low.to_numpy(float);cl=df.close.to_numpy(float)
        for i,signal in original.items():
            side=int(signal["side"]);j=int(signal["signal_close_bar"])
            assert j==i//15-1 and i%15==0
            if not ns["check_filter"](cfg["filter"],side,j,ema,ind):continue
            qualified+=1
            limit=float(op[i]-side*cfg["limit_offset"]*ind["ATR"][j])
            # Limit execution cannot exceed its price. Instead of adding
            # slippage to entry, require adverse penetration as a fill haircut.
            penetration=limit*(1-side*ns["SLIP"])
            assert np.isfinite(limit) and limit>0
            fill_i=None;post_path=None
            for k in range(i,min(i+15,len(df))):
                p=(op[k],hi[k],lo[k],cl[k]) if path=="O-H-L-C" else (op[k],lo[k],hi[k],cl[k])
                if side*(p[0]-penetration)<0:
                    fill_i=k;post_path=p;break
                for seg in range(1,4):
                    if side*(p[seg]-penetration)<0:
                        assert side*(p[seg-1]-penetration)>=0
                        fill_i=k;post_path=(penetration,)+p[seg:];break
                if fill_i is not None:break
            if fill_i is None:
                expired+=1;continue
            assert 0<=fill_i-i<15 and fill_i not in signals
            assert int(trend[fill_i//15-1])==side
            signals[fill_i]=dict(signal,limit_price=limit,limit_path=post_path)
            ns["LIMIT_ORIGINS"][i]=signal["epoch"]
            entry_delays[signal["epoch"]]=fill_i-i
            limit_prices[signal["epoch"]]=limit
            confirmed+=1
        assert qualified==confirmed+expired and len(signals)==confirmed
    x,m,l=ns["simulate"](df,ema,st,trend,ind,name,(cfg["wait"],cfg["filter"],"ATR",cfg["atr"],cfg["rr"],"none"),signals,path)
    if cfg["limit_offset"]>=0.:
        assert l.epoch.isin(entry_delays).all()
        assert np.allclose(l.entry,l.epoch.map(limit_prices),rtol=0.,atol=1e-8)
        times=set(df.time.iloc[list(signals)].to_numpy(np.int64))
        assert all(int(t.timestamp()) in times for t in pd.to_datetime(l.entry_time_utc,utc=True))
        x.update(limit_qualified=qualified,limit_potential_fills=confirmed,limit_expired=expired,mean_entry_delay_minutes=float(l.epoch.map(entry_delays).mean()))
    if cfg["fresh_reset"]:
        by_epoch={v["epoch"]:v for v in signals.values()}
        assert l.epoch.isin(by_epoch).all()
        if cfg["first_valid"]:
            assert l.epoch.map(lambda e:by_epoch[e]["cycle"]).is_unique, "duplicate executed ST cycle"
            l["st_cycle"]=l.epoch.map(lambda e:by_epoch[e]["cycle"])
            l["pullback_attempt"]=l.epoch.map(lambda e:by_epoch[e]["attempt"])
            x["recovered_cycle_trades"]=int((l.pullback_attempt>1).sum())
        x["fresh_repeat_trades"]=int(l.epoch.map(lambda e:by_epoch[e]["attempt"]>1).sum())
        x["fresh_original_signal_trades"]=int(l.epoch.map(lambda e:(by_epoch[e]["signal_close_bar"]+1)*15 in original).sum())
        x["fresh_total_signal_candidates"]=len(signals)
        x["fresh_additional_signal_candidates"]=len(signals)-len(original)
        x["repeat_filtered_signals"]=len(raw_signals)-len(signals)
        if cfg["repeat_filter"]!="none":assert all(repeat_eligible(by_epoch[e]) for e in l.epoch)
        assert x["fresh_repeat_trades"]+x["fresh_original_signal_trades"]==len(l)
        is_repeat=l.epoch.map(lambda e:by_epoch[e]["attempt"]>1)
        expected=np.where(is_repeat,prof*cfg["repeat_size"],prof)
        assert np.allclose(l.entry_exposure_pct,expected,rtol=0.,atol=1e-7)
        before=l.equity_after_usd-l.net_usd
        assert (before>0).all()
        logret=np.log(l.equity_after_usd/before)
        assert abs(logret.sum()-np.log1p(x["net_return_pct"]/100))<1e-5
        for key,mask in (("first",~is_repeat),("repeat",is_repeat)):
            x[f"{key}_net_usd"]=float(l.loc[mask,"net_usd"].sum())
            x[f"{key}_log_return_pct"]=float(logret[mask].sum()*100)
            x[f"{key}_win_rate_pct"]=float((l.loc[mask,"net_usd"]>0).mean()*100)
            x[f"{key}_mean_trade_return_pct"]=float((l.net_usd[mask]/before[mask]).mean()*100)
        assert (pd.to_datetime(l.entry_time_utc,utc=True).iloc[1:].reset_index(drop=True)>=pd.to_datetime(l.exit_time_utc,utc=True).iloc[:-1].reset_index(drop=True)).all()
    x["timeframe"]=f"{cfg['signal_tf']}m"
    x["eligible_signal_count"]=sum(bool(ns["check_filter"](cfg["filter"],int(v["side"]),int(v["signal_close_bar"]),ema,ind)) for v in signals.values())
    if not cfg["fresh_reset"]:
        by_epoch={v["epoch"]:v for v in signals.values()}
        assert all(ns["check_filter"](cfg["filter"],int(by_epoch[e]["side"]),int(by_epoch[e]["signal_close_bar"]),ema,ind) for e in l.epoch)
    if not cfg["fresh_reset"]:
        assert l.epoch.is_unique
        allowed_times=set(df.time.iloc[list(signals)].to_numpy(np.int64))
        assert all(int(t.timestamp()) in allowed_times for t in pd.to_datetime(l.entry_time_utc,utc=True))
    for k in ("profitable_2025_months","profitable_2026_months","return_2025_pct","return_2026_pct"):x.pop(k,None)
    x.update(candidate=cid,period=period,profile=prof,stress=stress,**cfg)
    x["mean_planned_risk_pct"]=float(l.planned_risk_pct.mean())
    x["max_planned_risk_pct"]=float(l.planned_risk_pct.max())
    if cfg["dmi_ramp"]>0.:
        by_epoch={v["epoch"]:v for v in signals.values()}
        expected=[]
        for e in l.epoch:
            v=by_epoch[e];j=int(v["signal_close_bar"]);side=int(v["side"])
            u=np.clip(side*ind["dmi_imbalance"][j]/cfg["dmi_ramp"],0.,1.)
            expected.append(prof*(1. if ind["adx14"][j]>=20. else .25)*(.25+.75*u))
        assert np.allclose(l.entry_exposure_pct,expected,rtol=0.,atol=1e-7)
    if cfg["cost_be"]:
        z=l[(l.exit_reason=="PROTECTION_STOP") & (~l.partial_exit)]
        assert (z.net_usd.abs()<1e-8).all(), "cost-neutral stop accounting mismatch"
        x["cost_neutral_stop_exits"]=len(z)
        x["cost_neutral_gap_exits"]=int(((l.exit_reason=="PROTECTION_GAP")&(~l.partial_exit)).sum())
        x["wins"]=int((l.net_usd>1e-8).sum())
        x["losses"]=int((l.net_usd< -1e-8).sum())
        x["breakeven_trades"]=int((l.net_usd.abs()<=1e-8).sum())
        x["win_rate_pct"]=100*x["wins"]/len(l)
    x["partial_then_stop_count"]=int((l.partial_exit & l.exit_reason.isin(["STOP","STOP_GAP","PROTECTION_STOP","PROTECTION_GAP"])).sum())
    x["partial_then_stop_positive"]=int((l.partial_exit & l.exit_reason.isin(["STOP","STOP_GAP","PROTECTION_STOP","PROTECTION_GAP"]) & (l.net_usd>1e-8)).sum())
    x["partial_exit_count"]=int(l.partial_exit.sum())
    if cfg["cost_be"] and cfg["rr"]==3.:
        assert cfg["partial_fraction"]==0. and not l.partial_exit.any()
    x["exit_fraction_at_3r"]=1. if cfg["rr"]==3. else cfg["partial_fraction"]
    x["mean_entry_exposure_pct"]=float(l.entry_exposure_pct.mean())
    x["gradual_updated_trades"]=int((l.gradual_updates>0).sum())
    x["gradual_update_events"]=int(l.gradual_updates.sum())
    assert (l.loc[l.gradual_updates>0,"activation_count"]>0).all()
    if cfg["gradual_r"]==0.:assert x["gradual_update_events"]==0
    if cfg["continuous_floor"]>=0.:
        f=cfg["continuous_floor"]
        x["min_entry_exposure_pct"]=float(l.entry_exposure_pct.min())
        x["max_entry_exposure_pct"]=float(l.entry_exposure_pct.max())
        assert x["min_entry_exposure_pct"]>=prof*f-1e-7 and x["max_entry_exposure_pct"]<=prof+1e-7
    if cfg["linear_floor"]>=0.:
        f=cfg["linear_floor"]
        allowed=np.array([prof*(f+(1.-f)*k/2.) for k in (0,1,2)])
        assert np.all(np.min(np.abs(l.entry_exposure_pct.to_numpy()[:,None]-allowed),axis=1)<1e-7)
        for k,v in enumerate(allowed):x[f"linear_exposure_count_{k}"]=int(np.isclose(l.entry_exposure_pct,v,atol=1e-7).sum())
        assert sum(x[f"linear_exposure_count_{k}"] for k in range(3))==len(l)
        if f==0.:assert x["linear_exposure_count_0"]==0
    if cfg["adx_multiplier"]>0.:
        a,d=cfg["adx_multiplier"],cfg["dmi_multiplier"]
        allowed=np.array([prof,prof*a,prof*d,prof*a*d])
        assert np.all(np.min(np.abs(l.entry_exposure_pct.to_numpy()[:,None]-allowed),axis=1)<1e-7)
    elif cfg["quality_factor"]<1.:
        q=cfg["quality_factor"]
        n=4 if cfg["quality_vol"] else 3
        allowed=np.array([prof*q**k for k in range(n)])
        assert np.all(np.min(np.abs(l.entry_exposure_pct.to_numpy()[:,None]-allowed),axis=1)<1e-7)
        for k,v in enumerate(allowed):x[f"quality_exposure_count_{k}"]=int(np.isclose(l.entry_exposure_pct,v,atol=1e-7).sum())
        assert sum(x[f"quality_exposure_count_{k}"] for k in range(n))==len(l)
    if cfg["equity_risk"]:assert x["max_planned_risk_pct"]<=100*cfg["equity_risk"]+1e-8
    x["h4_invalidation_exits"]=int((l.exit_reason=="H4_INVALIDATION").sum())
    if not cfg["h4_exit"]:assert x["h4_invalidation_exits"]==0
    z=l[l.exit_reason=="H4_INVALIDATION"]
    assert all(t.hour%4==0 and t.minute==0 and t.second==0 for t in pd.to_datetime(z.exit_time_utc,utc=True))
    if cfg["pre_protection"]:assert (z.activation_count==0).all()
    x["time_invalidation_exits"]=int((l.exit_reason=="TIME_INVALIDATION").sum())
    if cfg["timeout_hours"]==0:assert x["time_invalidation_exits"]==0
    x["early_risk_reduced_trades"]=int(l.early_risk_reduced.sum())
    if cfg["early_trigger"]==0:assert x["early_risk_reduced_trades"]==0
    x["weak_target_trades"]=int(l.weak_target_used.sum())
    x["weak_target_tp_exits"]=int((l.weak_target_used & (l.exit_reason=="TP")).sum())
    assert not l.loc[l.weak_target_used,"partial_exit"].any()
    if cfg["weak_target"]==0:assert x["weak_target_trades"]==0
    else:assert (l.loc[l.weak_target_used,"target_r"]==cfg["weak_target"]).all()
    assert (l.loc[~l.weak_target_used,"target_r"]==cfg["rr"]).all()
    if cfg["rr"]<=2.5:
        assert not l.partial_exit.any() and (l.activation_count==0).all()
    duration=(pd.to_datetime(l.exit_time_utc,utc=True)-pd.to_datetime(l.entry_time_utc,utc=True)).dt.total_seconds()/3600
    assert (duration>=0).all()
    x["median_hold_hours"]=float(duration.median())
    x["mean_hold_hours"]=float(duration.mean())
    x["mean_net_trade_pct"]=float((100*l.net_usd/(l.equity_after_usd-l.net_usd)).mean())
    x["geo_month_pct"]=100*((1+x["net_return_pct"]/100)**(1/len(months))-1)
    # Do not count floating-point noise on a cost-neutral flat month as profit.
    x["profitable_months"]=int((m.monthly_return_pct>1e-8).sum())
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
        cache={}
        for cid,cfg in enumerate(GRID):
            if cid%SHARDS!=i:continue
            tf=cfg["signal_tf"]
            if tf not in cache:cache[tf]=prep(period,tf)
            data=cache[tf]
            for path in base.PATHS:
                for stress in (False,True):
                    x,m,_=replay(ns,data,period,cid,cfg,100,path,stress)
                    rows.append(x);monthly.append(m)
                    print("TRAIN",period,cid,path,stress,x["net_return_pct"],flush=True)
    d=OUT/f"shard_{i}";d.mkdir(parents=True,exist_ok=True)
    pd.DataFrame(rows).to_csv(d/"training.csv",index=False)
    pd.concat(monthly,ignore_index=True).to_csv(d/"monthly.csv",index=False)
def freeze():
    s=pd.concat([pd.read_csv(OUT/f"shard_{i}"/"training.csv") for i in range(SHARDS)],ignore_index=True)
    m=pd.concat([pd.read_csv(OUT/f"shard_{i}"/"monthly.csv") for i in range(SHARDS)],ignore_index=True)
    assert len(s)==len(GRID)*8 and not s.duplicated(["candidate","period","path_assumption","stress"]).any()
    ref=s[s.candidate==CONTROL].set_index(["period","path_assumption","stress"]).sort_index()
    assert abs(ref.net_return_pct.min()-42.1386)<.015 and abs(ref.max_floating_drawdown_pct.max()-6.543)<.015
    assert ref.groupby("period").profitable_months.min().sum()==20
    coverage={}
    for cid in range(len(GRID)):
        z=s[s.candidate==cid].set_index(["period","path_assumption","stress"]).sort_index()
        assert z.index.equals(ref.index)
        coverage[cid]=bool((z.trades>=ref.trades).all())
        if cid%len(LEVELS)==2:assert z.trades.equals(ref.trades),("ADX sizing unexpectedly changed trade coverage",cid)
    s.to_csv(OUT/"training.csv",index=False);m.to_csv(OUT/"training_monthly.csv",index=False)
    a=s.groupby("candidate").agg(min_net=("net_return_pct","min"),max_dd=("max_floating_drawdown_pct","max"),min_half=("worst_half_pct","min"),min_geo=("geo_month_pct","min"),worst_month=("worst_month","min")).reset_index()
    counts=s.groupby(["candidate","period"]).profitable_months.min().unstack()
    a["months_2024"]=a.candidate.map(counts[2024]);a["months_2025"]=a.candidate.map(counts[2025]);a["months"]=a.months_2024+a.months_2025
    normal=s[(s.path_assumption=="O-H-L-C")&(~s.stress)].set_index(["candidate","period"])
    for year in (2024,2025):
        a[f"return_{year}"]=a.candidate.map(normal.xs(year,level="period").net_return_pct)
        a[f"trades_{year}"]=a.candidate.map(normal.xs(year,level="period").trades)
    a["adx_threshold"]=a.candidate.map(lambda i:GRID[i]["adx_threshold"]);a["vol_min"]=a.candidate.map(lambda i:VOL_LEVELS[i%len(LEVELS)])
    a["retains_trade_coverage"]=a.candidate.map(coverage)
    by=a.set_index("candidate")
    def neighbors(i):
        r,c=divmod(i,len(LEVELS))
        return [u*len(LEVELS)+v for u,v in [(r-1,c),(r+1,c),(r,c-1),(r,c+1)] if 0<=u<len(LEVELS) and 0<=v<len(LEVELS)]
    a["neighbor_min_months"]=a.candidate.map(lambda i:min(by.loc[j,"months"] for j in neighbors(i)))
    a["neighbor_stability"]=a.candidate.map(lambda i:np.mean([by.loc[j,"min_net"]>=.8*by.loc[i,"min_net"] and by.loc[j,"months"]>=by.loc[i,"months"]-1 and by.loc[j,"min_half"]>0 for j in neighbors(i)]))
    # In-sample research trade-off, not a deployment gate: permit up to 20%
    # reduction of worst annual return and 25% higher DD than matched C16.
    a["strict_nonregression"]=(a.min_net>=by.loc[CONTROL,"min_net"])&(a.max_dd<=by.loc[CONTROL,"max_dd"])
    a["research_eligible"]=(a.months>20)&(a.months_2024>=8)&(a.months_2025>=12)&(a.min_net>=.8*42.6013)&(a.max_dd<=1.25*6.543)&(a.min_half>0)&(a.neighbor_stability>=.5)&a.retains_trade_coverage
    a=a.sort_values(["months","research_eligible","min_net","max_dd","candidate"],ascending=[False,False,False,True,True])
    a.to_csv(OUT/"training_ranked.csv",index=False)
    top=a.iloc[0];eligible=a[a.research_eligible]
    choice=eligible.iloc[0] if len(eligible) else a[a.candidate==CONTROL].iloc[0]
    cid=int(choice.candidate)
    (OUT/"FROZEN.json").write_text(json.dumps(dict(candidate=cid,config=GRID[cid],research_eligible=bool(choice.research_eligible),strict_nonregression=bool(choice.strict_nonregression),deployment_approved=False,training_periods=["2024-02..12","2025-01..12"],selection="Monthly-first in-sample, 25 configurations. 2026 excluded. Prior 2026 failure remains relevant. Research acceptance allows at most 20% lower worst annual return and 25% greater max DD relative to original C16 (not progressively relaxed), no loss of trade count in any scenario vs current C05, 12/12 2025 profitable months, positive half years, local stability.",training_sha256=hashlib.sha256((OUT/"training.csv").read_bytes()).hexdigest()),indent=2)+"\n")
    z=m[m.candidate==cid].groupby("month_ist").monthly_return_pct.min()
    control=m[m.candidate==CONTROL].groupby("month_ist").monthly_return_pct.min()
    pd.concat([control.rename("C05_worst_path_cost"),z.rename("selected_worst_path_cost")],axis=1).to_csv(OUT/"monthly_comparison.csv")
    (OUT/"REPORT.md").write_text("# ADX threshold and relative ATR grid — 2024–2025 only\n\n200 simulations, 25 configurations including matched C05. Both costs and paths. No 2026 replay. Funding excluded. In-sample research only.\n\n"+a.to_markdown(index=False)+"\n\n## Selected comparison\n\n"+pd.concat([control.rename("C05"),z.rename("selected")],axis=1).to_markdown()+"\n")
if __name__=="__main__":
    if sys.argv[1]=="train":train()
    elif sys.argv[1]=="freeze":freeze()
    else:raise ValueError("2026 excluded")
