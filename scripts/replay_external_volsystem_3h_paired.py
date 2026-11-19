#!/usr/bin/env python3
"""VolatilitySystem causal 3h paired diagnostic; pinned freqtrade-strategies@f3340ce11f5bdf62f598522e64d1f5638eaa13f5.
Deviation: 1x notional, no adds, 3xATR initial protective stop; otherwise
source signals (3h close change > 2x prior ATR), opposite-signal exit.
Source has no protective stop; this is explicitly a bounded-risk variant.
"""
import hashlib,json
from pathlib import Path
import numpy as np,pandas as pd,talib
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"analysis/external_github_profit_hunt/volatilitysystem_3h_paired"
MONTHS=pd.period_range("2025-01","2026-10",freq="M").astype(str).tolist()
def run(sym):
 folder=ROOT/"data/delta_india"/sym/"1m"
 man=json.loads((folder/"manifest.json").read_text());parts={p["file"][:7]:p for p in man["partitions"]}
 frames=[]
 for ym in MONTHS:
  p=parts[ym];file=folder/p["file"]
  assert p["missing_minutes"]==0 and hashlib.sha256(file.read_bytes()).hexdigest()==p["sha256_gzip"]
  df=pd.read_csv(file,compression="gzip")
  assert len(df)==p["observed_candles"]
  frames.append(df[["time","open","high","low","close"]])
 b=pd.concat(frames,ignore_index=True)
 t=b.time.to_numpy(np.int64);o=b.open.to_numpy(float);h=b.high.to_numpy(float);l=b.low.to_numpy(float);c=b.close.to_numpy(float)
 assert (np.diff(t)==60).all() and len(t)%180==0
 ch=h.reshape(-1,180).max(axis=1);cl=l.reshape(-1,180).min(axis=1);cc=c[179::180]
 atr=talib.ATR(ch,cl,cc,timeperiod=14)
 diff=np.r_[np.nan,np.diff(cc)]
 sig=np.zeros(len(cc),dtype=np.int8)
 for k in range(1,len(cc)-1):
  if np.isfinite(atr[k-1]) and atr[k-1]>0:
   if diff[k]>2*atr[k-1]:sig[k+1]=1
   elif -diff[k]>2*atr[k-1]:sig[k+1]=-1
 cutoff=int(pd.Timestamp("2026-10-31 18:30",tz="UTC").timestamp());n=np.searchsorted(t,cutoff)
 months=pd.to_datetime(t[:n],unit="s",utc=True).tz_convert("Asia/Kolkata").strftime("%Y-%m").to_numpy()
 assert set(months)==set(MONTHS)
 rows={m:dict(month_ist=m,entries=0,trades=0,wins=0,losses=0,gross_wins=0.,gross_losses=0.,active_minutes=0) for m in MONTHS}
 cash=10000.;side=0;qty=0.;entry=0.;entryfee=0.;stop=0.;entrytime=0;trades=[];eq={};prev=""
 fee=.0005*1.18
 def price(raw,s,enter):
  d=s if enter else -s
  return raw+5*d if sym=="BTCUSD" else raw*(1+d*.0002)
 def close(i,raw,reason):
  nonlocal cash,side
  xp=price(raw,side,False);exitfee=abs(qty*xp)*fee;net=(xp-entry)*side*qty-entryfee-exitfee
  cash+=(xp-entry)*side*qty-exitfee
  z=rows[months[i]];z["trades"]+=1;z["wins"]+=int(net>0);z["losses"]+=int(net<0)
  z["gross_wins"]+=max(0,net);z["gross_losses"]+=max(0,-net)
  trades.append(dict(entry_utc=entrytime,exit_utc=int(t[i]),side=side,qty=qty,entry_price=entry,exit_price=xp,entry_fee=entryfee,exit_fee=exitfee,net_pnl=net,exit_month_ist=months[i],reason=reason))
  side=0
 for i in range(n):
  m=months[i];z=rows[m]
  if m!=prev and prev in rows:eq[prev]=cash+(c[i-1]-entry)*side*qty if side else cash
  prev=m
  if i%180==0 and sig[i//180] and side and side!=sig[i//180]:close(i,o[i],"opposite")
  if i%180==0 and sig[i//180] and not side and cash>0:
   side=int(sig[i//180]);entry=price(o[i],side,True);qty=cash/entry
   entryfee=abs(qty*entry)*fee;cash-=entryfee;entrytime=int(t[i]);z["entries"]+=1
   stop=entry-side*3*atr[i//180-1]
  if side:
   z["active_minutes"]+=1
   if (side==1 and l[i]<=stop) or (side==-1 and h[i]>=stop):
    raw=min(o[i],stop) if side==1 else max(o[i],stop)
    close(i,raw,"stop")
 if prev in rows:eq[prev]=cash+(c[n-1]-entry)*side*qty if side else cash
 out=[];prior=10000.
 for m in MONTHS:
  z=rows[m];end=eq[m];ret=100*(end/prior-1);prior=end
  w=z["gross_wins"];loss=z["gross_losses"];pf=w/loss if loss else (float("inf") if w else None)
  out.append({**z,"marked_equity":end,"monthly_net_return_pct":ret,"profit_factor":round(pf,6) if pf is not None and np.isfinite(pf) else ("Infinity" if pf else "N/A"),"high_pf_positive_month":bool(pf is not None and pf>=1.5 and ret>0)})
 df=pd.DataFrame(out);OUT.mkdir(parents=True,exist_ok=True)
 df.to_csv(OUT/(sym+"_22_months.csv"),index=False);pd.DataFrame(trades).to_csv(OUT/(sym+"_trades.csv.gz"),index=False,compression="gzip")
 e=df.marked_equity.to_numpy();y25=df.loc[df.month_ist=="2025-12","marked_equity"].iloc[0]
 result=dict(symbol=sym,trades=len(trades),wins=int(df.wins.sum()),losses=int(df.losses.sum()),high_pf_months=int(df.high_pf_positive_month.sum()),positive_months=int((df.monthly_net_return_pct>0).sum()),negative_months=int((df.monthly_net_return_pct<0).sum()),net_22m_pct=float(100*(e[-1]/10000-1)),net_2025_pct=float(100*(y25/10000-1)),net_2026_ytd_pct=float(100*(e[-1]/y25-1)),aggregate_pf=float(df.gross_wins.sum()/df.gross_losses.sum()) if df.gross_losses.sum()>0 else None,max_month_end_dd_pct=float(100*np.max(1-e/np.maximum.accumulate(np.r_[10000.,e])[1:])),median_monthly_net_pct=float(df.monthly_net_return_pct.median()),full_jan_ist=False,funding_modeled=False)
 print("VOL3H_RESULT "+json.dumps(result),flush=True)
 return result
if __name__=="__main__":
 results=[run(s) for s in ("BTCUSD","ETHUSD")]
 (OUT/"verdict.json").write_text(json.dumps(dict(source_sha="f3340ce11f5bdf62f598522e64d1f5638eaa13f5",source_path="user_data/strategies/futures/VolatilitySystem.py",results=results,verified=False,limitations=["Missing Dec31 2024 UTC 330m January IST segment not yet merged","Funding, spreads, market impact, liquidation not modeled","Causal 3h variant adds 3ATR protective stop, omits source pyramiding and uses 1x exposure","No authentic prehistory for 3h indicator warmup"]),indent=2)+"\n")
