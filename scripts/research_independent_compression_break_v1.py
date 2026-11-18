#!/usr/bin/env python3
"""Independent 1H pre-break compression -> confirmed expansion breakout, paired BTC/ETH."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from eth_native_crossfamily_v2 import load,aggregate,MONTHS,RISK,CAP,FEE
from research_btc_eth_monthly_volatility_balance import replay_instrument,month_table,flatten,ledger_detail,events_for
OUT=Path("analysis/independent_compression_break_v1")
def main():
 OUT.mkdir(parents=True,exist_ok=True)
 summaries=[];monthly=[];ledgers=[]
 for symbol in ("BTCUSD","ETHUSD"):
  f=load(symbol); x=aggregate(f,"1h")
  ist=f.index.tz_convert("Asia/Kolkata")
  codes=np.asarray(ist.year*100+ist.month,dtype=np.int32)
  op=f.open.to_numpy(float);hi=f.high.to_numpy(float);lo=f.low.to_numpy(float);cl=f.close.to_numpy(float)
  # All channel levels, compression and baseline ATR come from bars completed BEFORE breakout candle.
  for lookback in (12,24,48):
   upper=x.high.shift(1).rolling(lookback,min_periods=lookback).max()
   lower=x.low.shift(1).rolling(lookback,min_periods=lookback).min()
   prior_atr=x.atr.shift(1)
   compression=(upper-lower)/prior_atr
   for max_width in (3.,5.,8.):
    for min_body in (.3,.6):
     body=(x.close-x.open).abs()/x.atr
     long=(x.valid&(compression<=max_width)&(x.close>upper)&(x.close>x.open)&(body>=min_body))
     short=(x.valid&(compression<=max_width)&(x.close<lower)&(x.close<x.open)&(body>=min_body))
     _,k,side,j=events_for((x,long.fillna(False),short.fillna(False)),f)
     if not len(k):continue
     stops=x.atr.to_numpy(float)[j]
     for sm,rr in ((1.5,2.),(2.5,3.)):
      model=f"1h:prior_channel_compression{lookback}:width{max_width:g}:body{min_body:g}:sl{sm:g}:rr{rr:g}"
      ledger=replay_instrument(op,hi,lo,cl,codes,k,side,stops,rr,1440,sm,RISK,CAP,
       5. if symbol=="BTCUSD" else 0.,0. if symbol=="BTCUSD" else .0002,FEE)
      m=month_table(ledger,codes,symbol,model)
      s=flatten(symbol,model,ledger,m)
      strong5=sum((v=="infinite" or (isinstance(v,(int,float)) and v>=1.5)) and r>=5 and t>=3 for v,r,t in zip((z["profit_factor"] for z in m),(z["net_return_pct"] for z in m),(z["trades"] for z in m)))
      strong10=sum((v=="infinite" or (isinstance(v,(int,float)) and v>=1.5)) and r>=10 and t>=3 for v,r,t in zip((z["profit_factor"] for z in m),(z["net_return_pct"] for z in m),(z["trades"] for z in m)))
      s.update(months_pf1p5_net5=int(strong5),months_pf1p5_net10=int(strong10),full_2025_gt500=bool(s["net_return_2025_pct"]>500))
      summaries.append(s);monthly.extend(m)
      if len(ledger):ledgers.append(ledger_detail(symbol,model,ledger,f))
  print("FINISHED",symbol,flush=True)
 s=pd.DataFrame(summaries);m=pd.DataFrame(monthly)
 assert len(s[s.market=="BTCUSD"])==len(s[s.market=="ETHUSD"])
 s.to_csv(OUT/"all_summary.csv",index=False);m.to_csv(OUT/"all_22_months.csv",index=False)
 if ledgers:pd.concat(ledgers,ignore_index=True).to_csv(OUT/"all_trade_ledgers.csv.gz",index=False,compression="gzip")
 selected=set()
 for symbol in ("BTCUSD","ETHUSD"):
  q=s[(s.market==symbol)&(s.trades_2025>=15)].copy()
  if len(q):
   q["score"]=q.strong_months_2025*3+q.positive_months_2025+q.net_return_2025_pct.clip(-100,100)/10
   selected.update(q.sort_values("score",ascending=False).head(3).model.tolist())
 s[s.model.isin(selected)].to_csv(OUT/"selected_pair_summary.csv",index=False)
 m[m.model.isin(selected)].to_csv(OUT/"selected_pair_months.csv",index=False)
 quality=dict(strategy="Prior completed 12/24/48-hour price channel compression relative to lagged ATR, confirmed 1H close breakout with directional body; next 1m open entry",models_per_market=int(len(s)//2),selection="2025-only",data="Delta native 1m BTC and ETH; Jan2025 IST first 5.5h unavailable",fee="0.05% each side + 18% GST",slippage="BTC 5 price points/side, ETH 0.02%/side",risk="0.5% equity at stop, capped at 3x notional",omitted=["funding","verified spread","impact","lot sizes","margin/liquidation"],monthly_accounting="trades closed at IST month boundary; month equity includes net exit PnL; NOT continuous mark-to-market",not_pristine_2026=True)
 (OUT/"quality.json").write_text(json.dumps(quality,indent=2))
 (OUT/"DECISION.md").write_text("# Independent paired compression breakout audit\n\n"+json.dumps(quality,indent=2)+"\n\n## 2025-selected candidates paired results\n\n"+s[s.model.isin(selected)].to_markdown(index=False)+"\n\n## All 22 monthly rows\n\n"+m[m.model.isin(selected)].to_markdown(index=False))
 print("DONE",json.dumps(dict(models_per_market=int(len(s)//2),net_positive_BTC=int(((s.market=="BTCUSD")&(s.net_return_pct>0)).sum()),net_positive_ETH=int(((s.market=="ETHUSD")&(s.net_return_pct>0)).sum()),high_monthly_5=int((s.months_pf1p5_net5>=12).sum()),high_monthly_10=int((s.months_pf1p5_net10>=12).sum()),annual_2025_gt500=int(s.full_2025_gt500.sum()),top=s.sort_values(["months_pf1p5_net5","net_return_pct"],ascending=False).head(4)[["market","model","months_pf1p5_net5","months_pf1p5_net10","net_return_2025_pct","net_return_2026_pct","trades"]].to_dict("records"))),flush=True)
if __name__=="__main__":main()
