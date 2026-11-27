"""2025 BTC/ETH legacy 15m paper profile, using archived Delta India trade/mark 1m.
Research approximation: no historical bid/ask, depth, or 3-second path.
No orders, no funding deduction (paper ledger does not implement funding).
"""
import argparse, hashlib, json, math
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]/"data/delta_india"
ASSET="ETH"
TICK=.05
LOT=.01
START=100.
BUDGET=10.
LEVERAGE=100
FEE=.0005*1.18
SHOCK=.01

def rma(s,n):
 v=s.to_numpy(dtype=float);out=np.full(len(v),np.nan)
 valid=np.flatnonzero(~np.isnan(v));seed=valid[n-1]
 out[seed]=np.mean(v[valid[:n]])
 for i in range(seed+1,len(v)):
  out[i]=(out[i-1]*(n-1)+v[i])/n
 return pd.Series(out,index=s.index)

def indicators(x):
 prev=x.close.shift(1)
 tr=pd.concat([x.high-x.low,(x.high-prev).abs(),(x.low-prev).abs()],axis=1).max(axis=1)
 atr10=rma(tr,10);atr14=rma(tr,14)
 ema=x.close.ewm(alpha=2/21,adjust=False).mean()
 mid=(x.high+x.low)/2
 ub=(mid+3*atr10).to_numpy();lb=(mid-3*atr10).to_numpy()
 close=x.close.to_numpy();final_up=np.full(len(x),np.nan);final_lo=np.full(len(x),np.nan)
 direction=np.full(len(x),0,dtype=np.int8);st=np.full(len(x),np.nan)
 for i in range(len(x)):
  if np.isnan(ub[i]):continue
  if i==0 or np.isnan(final_up[i-1]):
   final_up[i]=ub[i];final_lo[i]=lb[i];direction[i]=1;st[i]=final_up[i];continue
  pu=final_up[i-1];pl=final_lo[i-1]
  final_up[i]=ub[i] if (ub[i]<pu or close[i-1]>pu) else pu
  final_lo[i]=lb[i] if (lb[i]>pl or close[i-1]<pl) else pl
  if direction[i-1]==1:direction[i]= -1 if close[i]>final_up[i] else 1
  else:direction[i]=1 if close[i]<final_lo[i] else -1
  st[i]=final_lo[i] if direction[i]==-1 else final_up[i]
 x=x.copy()
 x['ema']=ema;x['atr14']=atr14;x['st']=st;x['dir']=direction
 x['atr_ratio']=atr14/atr14.shift(1).rolling(20,min_periods=20).mean()
 x['volume_ratio']=x.volume/x.volume.shift(1).rolling(20,min_periods=20).mean()
 return x


def load():
    base=ROOT/f"{ASSET}USD/1m"
    doc=json.loads((base/"manifest.json").read_text())
    ms=ROOT/f"{ASSET}USD/institutional/history/mark_1m"
    markdoc=json.loads((ms.parent.parent/"history_manifest.json").read_text())
    trade=[];mark=[]
    for month in range(1,13):
        name=f"2025-{month:02d}.csv.gz"
        p=next(x for x in doc["partitions"] if x["file"]==name)
        path=base/name
        assert p["missing_minutes"]==0 and hashlib.sha256(path.read_bytes()).hexdigest()==p["sha256_gzip"]
        x=pd.read_csv(path)
        assert len(x)==p["observed_candles"]
        trade.append(x)
        mp=next(x for x in markdoc["series"]["mark_1m"]["partitions"] if x["partition"].endswith("/"+name))
        y=pd.read_csv(ms/name)
        assert len(y)==mp["rows"]
        mark.append(y)
    def frame(parts):
        f=pd.concat(parts,ignore_index=True)
        f.index=pd.to_datetime(f.time,unit="s",utc=True)
        f=f[["open","high","low","close","volume"] if "volume" in f else ["open","high","low","close"]]
        target=pd.date_range("2025-01-01","2026-01-01",freq="min",inclusive="left",tz="UTC")
        assert f.index.equals(target) and np.isfinite(f[["open","high","low","close"]]).all().all()
        assert ((f.low<=f[["open","close"]].min(axis=1))&(f.high>=f[["open","close"]].max(axis=1))&(f.low>0)).all()
        return f
    t,m=frame(trade),frame(mark)
    # Use only December 2024 as indicator warmup, never trade in 2024.
    warm=ROOT/f"2024_recovery_candidates/{ASSET}USD/2024-12"
    meta=next(x for x in json.loads((warm/"manifest.json").read_text())["series"] if x["series"]=="trade_1m")
    path=warm/meta["file"]
    assert meta["missing"]==0 and hashlib.sha256(path.read_bytes()).hexdigest()==meta["sha256"]
    w=pd.read_csv(path)
    w.index=pd.to_datetime(w.time,unit="s",utc=True)
    assert w.index.equals(pd.date_range("2024-12-01","2025-01-01",freq="min",inclusive="left",tz="UTC"))
    bars=pd.concat([w[t.columns],t]).resample("15min").agg(dict(open="first",high="max",low="min",close="last",volume="sum"))
    return t,m,indicators(bars)


def quantize(price, side):
    return (math.ceil((price-1e-9)/TICK) if side==1 else math.floor((price+1e-9)/TICK))*TICK


def replay(t,m,bars,path,spread,trigger_points=150,lock_points=0,mode='FIXED',sl_mode='ATR',sl_points=0):
    # 15m close observed with the live 10-second finalization delay:
    # first subsequent minute OPEN proxies the bot's +10s entry/flip; exact +10s quote unknown.
    # Mark and trade extremes paired in each explicit OHLC scenario; not tick truth.
    a=t[["open","high","low","close"]].to_numpy(float)
    b=m[["open","high","low","close"]].to_numpy(float)
    sig=bars.reindex(t.index[::15]-pd.Timedelta(minutes=15))
    prev=bars.dir.shift(1).reindex(sig.index)
    s= sig[["open","high","low","close","ema","atr14","atr_ratio","volume_ratio","dir"]].to_numpy(float)
    prev=prev.to_numpy()
    cash=START;peak=START;dd=0.;p=None;trades=[];months=[];signals=skipped=0
    start_month=START;month_id=t.index[0].month;month_trades=0
    def fill(price,side): # side +1 buy, -1 sell; spread is full width in USD
        return (math.ceil((price+spread/2-1e-9)/TICK) if side==1 else math.floor((price-spread/2+1e-9)/TICK))*TICK
    def equity(price):
        return cash if p is None else cash+p["side"]*p["qty"]*(fill(price,-p["side"])-p["entry"])
    def observe(price):
        nonlocal peak,dd
        e=equity(price);peak=max(peak,e);dd=max(dd,100*(peak-e)/peak)
    def close(price,i,reason):
        nonlocal cash,p,month_trades
        q=p["qty"];xp=fill(price,-p["side"])
        # Upper bound minute-granularity holding duration; no intraminute time assumed.
        hold=i-p["i"]
        fee=0 if reason!="liquidation_proxy" and hold<=30 else q*xp*FEE
        gross=p["side"]*q*(xp-p["entry"])
        realized=gross-fee
        if reason=="liquidation_proxy":realized=max(-cash,realized)
        cash=max(0.,cash+realized)
        net=cash-p["cash_before"]
        trades.append(dict(entry_utc=str(t.index[p["i"]]),exit_utc=str(t.index[i]+pd.Timedelta(minutes=1)),side=p["side"],entry=p["entry"],exit=xp,qty=q,net=net,gross=gross,fees_gst=p["entry_fee"]+fee,reason=reason,hold_minutes=hold,wallet=cash))
        month_trades+=1;p=None
        observe(price)
    def manage_sample(i,k):
        if not p:return
        mark=b[i,k];trade=a[i,k];side=p["side"]
        observe(trade)
        if p["liq"] is not None and side*(mark-p["liq"])<=0:
            close(trade,i,"liquidation_proxy");return
        if mode=="BASELINE_TRAIL":
            if side*(mark-p["entry"])>=p["trigger"]:p["active"]=True
            if p["active"]:
                p["best"]=max(p["best"],mark) if side==1 else min(p["best"],mark)
                new=p["best"]-side*p["lock"]
                p["stop"]=max(p["stop"],new) if side==1 else min(p["stop"],new)
        elif mode=="FIXED" and not p["active"] and side*(mark-p["entry"])>=p["trigger"]:
            # One-time profit protection: fixed entry-relative stop, never follows best.
            new=quantize(p["entry"]+side*p["lock"],side)
            p["stop"]=max(p["stop"],new) if side==1 else min(p["stop"],new)
            p["active"]=True
        if side*(mark-p["stop"])<=0:
            # Preserve original sampled-extreme fill for controlled comparison.
            reason=("trailing" if mode=="BASELINE_TRAIL" else "fixed_profit_lock") if p["active"] else {"ATR":"atr_or_preliq","POINTS":"fixed_sl_or_preliq","FLIP":"preliq_stop"}[sl_mode]
            close(trade,i,reason);return
    for i in range(len(a)):
        if t.index[i].month!=month_id:
            end=equity(a[i-1,3]);months.append(dict(month=f"2025-{month_id:02d}",net=end-start_month,equity=end,trades=month_trades,return_pct=100*(end-start_month)/start_month if start_month else None))
            month_id=t.index[i].month;start_month=end;month_trades=0
        # Observe boundary open first; process the completed 15m signal
        # at the first available 1m open proxy, not the next minute close.
        manage_sample(i,0)
        if i%15==0:
            k=i//15;o,h,l,c,ema,atr,ar,vr,d=s[k];pr=prev[k]
            if p:
                if (p["side"]==1 and pr==-1 and d==1) or (p["side"]==-1 and pr==1 and d==-1):
                    close(a[i,0],i,"supertrend_flip")
            elif np.isfinite([ema,atr,ar,vr]).all() and ar>=1 and vr>=1.5:
                side=1 if d==pr==-1 and l<=ema<c else -1 if d==pr==1 and h>=ema>c else 0
                if side:
                    signals+=1;last=a[i,0]
                    ep=fill(last,side)
                    q=math.floor(min(BUDGET*LEVERAGE,BUDGET/SHOCK)/(ep*LOT)+1e-10)*LOT
                    fee=ep*q*FEE;margin=ep*q*SHOCK
                    if abs(last-c)/c>.002 or q<=0 or cash<margin+fee:skipped+=1
                    else:
                        after=cash-fee
                        rate=SHOCK*.75
                        liq=(q*ep-after)/(q*(1-rate)) if side==1 else (q*ep+after)/(q*(1+rate))
                        if liq<=0:liq=None
                        if sl_mode=="ATR":
                            stop=quantize(ep-side*max(TICK,round(2*atr/TICK)*TICK),side)
                        elif sl_mode=="POINTS":
                            dist=float(sl_points) if ASSET=="BTC" else max(TICK,round(ep*sl_points/80000/TICK)*TICK)
                            stop=quantize(ep-side*dist,side)
                        elif sl_mode=="FLIP":
                            stop=-math.inf if side==1 else math.inf
                        else:
                            raise ValueError(sl_mode)
                        if liq is not None:
                            pre=quantize(liq+side*(.2 if ASSET=="ETH" else 1.),side)
                            if side*(ep-pre)>0:stop=max(stop,pre) if side==1 else min(stop,pre)
                        p=dict(side=side,entry=ep,i=i,qty=q,entry_fee=fee,cash_before=cash,liq=liq,stop=stop,best=ep,active=False,trigger=float(trigger_points) if ASSET=="BTC" else max(TICK,round(ep*trigger_points/80000/TICK)*TICK),lock=float(lock_points) if ASSET=="BTC" else max(0.,round(ep*lock_points/80000/TICK)*TICK))
                        cash=after;observe(last)
        if p:
            # Bullish: low first; bearish: high first. Doji: nearer extreme first.
            # Shared trade/mark scenario; candle color is not known at entry.
            o,h,l,c=a[i]
            low_first=(p["side"]==1) if path=="DIRECTION" else (c>o or (c==o and o-l<=h-o))
            seq=(2,1,3) if low_first else (1,2,3)
            for k in seq:
                manage_sample(i,k)
                if not p:break
        observe(a[i,3])
    end=equity(a[-1,3])
    months.append(dict(month=f"2025-{month_id:02d}",net=end-start_month,equity=end,trades=month_trades,return_pct=100*(end-start_month)/start_month if start_month else None))
    nets=np.array([x["net"] for x in trades])
    grosswin=nets[nets>0].sum();grossloss=-nets[nets<0].sum()
    summary=dict(path=path,spread_usd=spread,starting_equity=START,ending_equity=end,net_profit=end-START,closed_trades=len(trades),win_rate_pct=100*(nets>0).mean() if len(nets) else None,profit_factor=grosswin/grossloss if grossloss else None,max_mark_to_market_dd_pct=dd,profitable_months=sum(x["net"]>0 for x in months),liquidations=sum(x["reason"]=="liquidation_proxy" for x in trades),fees_gst=sum(x["fees_gst"] for x in trades)+(p["entry_fee"] if p else 0),open_at_end=p is not None,signals=signals,skipped=skipped,monthly=months)
    assert abs(sum(x["net"] for x in months)-(end-START))<1e-6
    return summary,trades


if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path,required=True);p.add_argument("--asset",choices=("BTC","ETH"),required=True);args=p.parse_args()
    ASSET=args.asset
    TICK,LOT=(.5,.001) if ASSET=="BTC" else (.05,.01)
    args.output.mkdir(parents=True,exist_ok=True)
    t,m,b=load()
    # Same fixed-profit settings across both assets to avoid selecting asset-specific winners.
    # Control includes previous best BTC/ETH locks with ATR.
    protections=[("NONE",0,0),("FIXED",200,100),("FIXED",300,200),("FIXED",500,400),("FIXED",750,500),("FIXED",1000,750)]
    stops=[("POINTS",100),("POINTS",200),("POINTS",300),("POINTS",500),("POINTS",750),("POINTS",1000),("FLIP",0)]
    combos=[("ATR",0,"BASELINE_TRAIL",150,50)]+[("ATR",0,mode,a,l) for mode,a,l in protections]+[(sl,sp,mode,a,l) for sl,sp in stops for mode,a,l in protections]
    results=[]
    for sl,sp,mode,a,l in combos:
        result,trades=replay(t,m,b,"COLOR",0.,a,l,mode,sl,sp)
        result.update(asset=ASSET,sl_mode=sl,sl_btc_points=sp,sl_eth_pct=100*sp/80000,protection_mode=mode,trigger_btc_points=a,lock_btc_points=l,trigger_eth_pct=100*a/80000,lock_eth_pct=100*l/80000,profit_lock_exits=sum(x["reason"]=="fixed_profit_lock" for x in trades))
        results.append(result)
        pd.DataFrame(trades).to_csv(args.output/f"trades-{sl}-{sp}-{mode}-{a}-{l}.csv",index=False)
        print("SL_RESULT "+json.dumps({k:v for k,v in result.items() if k!="monthly"}),flush=True)
    expected={"BTC":-94.284358225,"ETH":-93.69178691499964}[ASSET]
    assert abs(results[0]["net_profit"]-expected)<1e-7,("baseline regression",results[0]["net_profit"],expected)
    controls={(200,100):{"BTC":-90.59799673999999,"ETH":-93.78907853499985},(500,400):{"BTC":-94.03429195500003,"ETH":-89.99353805000032}}
    for r in results:
        key=(r["trigger_btc_points"],r["lock_btc_points"])
        if r["sl_mode"]=="ATR" and r["protection_mode"]=="FIXED" and key in controls:
            assert abs(r["net_profit"]-controls[key][ASSET])<1e-7
    print("BASELINE_REPRODUCED",ASSET,flush=True)
    pd.DataFrame([{k:v for k,v in r.items() if k!="monthly"} for r in results]).to_csv(args.output/"comparison.csv",index=False)
    pd.DataFrame([dict(asset=ASSET,sl_mode=r["sl_mode"],sl_btc_points=r["sl_btc_points"],protection_mode=r["protection_mode"],trigger_btc_points=r["trigger_btc_points"],lock_btc_points=r["lock_btc_points"],**month) for r in results for month in r["monthly"]]).to_csv(args.output/"monthly.csv",index=False)
    (args.output/"summary.json").write_text(json.dumps(dict(trade_candles=len(t),mark_candles=len(m),assumptions="COLOR 2025. Fixed points initial SL or completed 15m Supertrend flip without ATR SL, with preliq safety and liquidation proxy retained. Supertrend flip exit remains enabled for all. Fixed profit lock once; no continuous trailing except original control. BTC points, ETH equivalent entry percent. Original sampled-extreme fills, fee+GST/30m offer, no spread/slippage/funding; $100 start/$10 trade budget/100x ceiling/portfolio proxy. In-sample only.",results=results),indent=2))
