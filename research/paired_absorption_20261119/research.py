#!/usr/bin/env python3
"""Pairwise causal 15m absorption -> displacement study. Native BTC/ETH 1m, research only."""
import hashlib,json
from pathlib import Path
import numpy as np,pandas as pd
O=Path("analysis/paired_absorption_20261119"); O.mkdir(parents=True,exist_ok=True)
MONTHS=pd.period_range("2025-01","2026-10",freq="M").astype(str).tolist()
def load(sym):
 root=Path("data/delta_india")/sym/"1m"; man=json.loads((root/"manifest.json").read_text()); parts=[]
 for p in man["partitions"]:
  if not ("2025-01.csv.gz"<=p["file"]<="2026-11.csv.gz"):continue
  raw=(root/p["file"]).read_bytes()
  assert hashlib.sha256(raw).hexdigest()==p["sha256_gzip"] and p["missing_minutes"]==0
  x=pd.read_csv(root/p["file"],compression="gzip",usecols=["time","open","high","low","close","volume"])
  assert len(x)==p["observed_candles"]==p["expected_minutes"]
  parts.append(x)
 f=pd.concat(parts,ignore_index=True).sort_values("time")
 assert f.time.diff().iloc[1:].eq(60).all()
 f.index=pd.to_datetime(f.time,unit="s",utc=True)
 return f.loc[f.index<pd.Timestamp("2026-10-31 18:30",tz="UTC")].copy()
def signals(f):
 b=f[["open","high","low","close","volume"]].resample("15min",closed="left",label="right").agg({"open":"first","high":"max","low":"min","close":"last","volume":"sum"})
 b["count"]=f.close.resample("15min",closed="left",label="right").count()
 pc=b.close.shift(1); tr=pd.concat([b.high-b.low,(b.high-pc).abs(),(b.low-pc).abs()],axis=1).max(axis=1)
 atr=tr.shift(1).rolling(20).mean()
 vm=b.volume.shift(1).rolling(48).median().shift(1)
 rm=(b.high-b.low).shift(1).rolling(48).median().shift(1)
 absorption=(b.volume.shift(1)>=2*vm)&((b.high.shift(1)-b.low.shift(1))<=.85*rm)
 long=absorption&(b.close>b.high.shift(1))&(b.close>b.open)&(b.close>b.low+.7*(b.high-b.low))
 short=absorption&(b.close<b.low.shift(1))&(b.close<b.open)&(b.close<b.low+.3*(b.high-b.low))
 valid=b["count"].eq(15)&b["count"].shift(1).eq(15)&atr.gt(0)
 ix=f.index.get_indexer(b.index); out=[]
 for i in np.flatnonzero((valid&(long|short)).to_numpy()):
  k=int(ix[i])
  if k>=0 and k<len(f)-1:out.append((k,1 if bool(long.iloc[i]) else -1,float(atr.iloc[i])))
 return out
def run(sym,f,events,stop_mult,rr,hold):
 op=f.open.to_numpy(); hi=f.high.to_numpy();lo=f.low.to_numpy();cl=f.close.to_numpy()
 ist=f.index.tz_convert("Asia/Kolkata");eq=10000.;peak=eq;busy=-1;rows=[]
 for k,side,atr in events:
  if k<=busy:continue
  entry=op[k];dist=stop_mult*atr;qty=min(eq*.005/dist,eq*3/entry)
  stop=entry-side*dist;target=entry+side*rr*dist;end=min(k+hold,len(f)-1)
  px=cl[end];j=end;why="timeout"
  for z in range(k,end+1):
   if (lo[z]<=stop if side==1 else hi[z]>=stop):
    px=min(op[z],stop) if side==1 else max(op[z],stop);j=z;why="stop";break
   if (hi[z]>=target if side==1 else lo[z]<=target):
    px=target;j=z;why="target";break
  busy=j;month=ist[j].strftime("%Y-%m")
  if month not in MONTHS:continue
  slipin=5 if sym=="BTCUSD" else entry*.0002
  slipout=5 if sym=="BTCUSD" else px*.0002
  fillin=entry+side*slipin;fillout=px-side*slipout
  gross=side*(fillout-fillin)*qty;fee=.0005*1.18*qty*(abs(fillin)+abs(fillout));net=gross-fee
  before=eq;eq+=net;assert eq>0
  peak=max(peak,eq)
  rows.append(dict(symbol=sym,month_ist=month,entry_utc=str(f.index[k]),exit_utc=str(f.index[j]),side=side,qty=qty,entry_fill=fillin,exit_fill=fillout,reason=why,gross_usd=gross,fee_gst_usd=fee,net_usd=net,equity_before=before,equity_after=eq,drawdown_pct=100*(1-eq/peak)))
 return pd.DataFrame(rows)
def pf(z):
 w=z.loc[z.net_usd>0,"net_usd"].sum();l=-z.loc[z.net_usd<0,"net_usd"].sum()
 return w/l if l else (float("inf") if w else float("nan"))
def report(sym,model,g):
 eq=10000.;monthly=[]
 for m in MONTHS:
  z=g[g.month_ist==m];n=eq+z.net_usd.sum()
  monthly.append(dict(symbol=sym,model=model,month_ist=m,net_return_pct=100*(n/eq-1),pf=pf(z),trades=len(z),wins=int((z.net_usd>0).sum()),losses=int((z.net_usd<0).sum()),equity_start=eq,equity_end=n));eq=n
 a=pd.DataFrame(monthly);q=a.iloc[:12];r=a.iloc[12:];strong=(a.pf>=1.5)&(a.trades>=3)
 s=dict(symbol=sym,model=model,trades=len(g),wins=int((g.net_usd>0).sum()),losses=int((g.net_usd<0).sum()),profitable_months=int((a.net_return_pct>0).sum()),negative_months=int((a.net_return_pct<0).sum()),high_pf_months=int(strong.sum()),high_pf_plus_5pct=int((strong&(a.net_return_pct>=5)).sum()),months_ge_5pct=int((a.net_return_pct>=5).sum()),months_ge_10pct=int((a.net_return_pct>=10).sum()),months_ge_20pct=int((a.net_return_pct>=20).sum()),median_monthly_return_pct=float(a.net_return_pct.median()),median_finite_pf=float(a.loc[np.isfinite(a.pf)&(a.trades>=3),"pf"].median()),worst_month_pct=float(a.net_return_pct.min()),max_closed_trade_drawdown_pct=float(g.drawdown_pct.max()),overall_pf=pf(g),total_22m_pct=100*(eq/10000-1),full_2025_net_pct=100*(q.iloc[-1].equity_end/q.iloc[0].equity_start-1),full_2025_pf=pf(g[g.month_ist<"2026-01"]),ytd_2026_jan_oct_net_pct=100*(r.iloc[-1].equity_end/r.iloc[0].equity_start-1))
 return a,s
def main():
 ms=[];ss=[];audit={}
 for sym in ("BTCUSD","ETHUSD"):
  f=load(sym);events=signals(f);audit[sym]=dict(first_utc=str(f.index[0]),last_utc=str(f.index[-1]),signal_count=len(events),first_ist_month_missing_minutes=330)
  for mult,rr,hold in [(1.5,2.,96),(2.,3.,192)]:
   model=f"atr{mult}_rr{rr}_hold{hold}"
   g=run(sym,f,events,mult,rr,hold)
   assert len(g)>0
   g.to_csv(O/f"{sym}_{model}_ledger.csv.gz",index=False,compression="gzip")
   a,s=report(sym,model,g);ms.append(a);ss.append(s)
 pd.concat(ms).to_csv(O/"monthly_all_22.csv",index=False)
 pd.DataFrame(ss).to_csv(O/"summary.csv",index=False)
 (O/"audit.json").write_text(json.dumps(audit,indent=2))
 (O/"LIMITATIONS.md").write_text("Research-only. Two fixed paired variants, no instrument-specific tuning. Fees 0.05% taker each side plus 18% GST; BTC 5-point and ETH 0.02% adverse slippage each side. 0.5% stop risk, 3x notional cap, no leverage inflation. Funding, observed spread, impact, contract minimum, liquidation maintenance and intratrade drawdown NOT modeled. Jan 2025 IST first 330 minutes absent. 2026 is research-exposed, not pristine OOS.\n")
 print(pd.DataFrame(ss).to_string(index=False))
if __name__=="__main__":main()
