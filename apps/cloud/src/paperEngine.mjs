/** Incremental fixed-point 1m long-only EMA crossover reference, no order API. */
const S=100000000n,BPS=10000n;
const str=x=>String(x);
export const VERSION="ema-cross-fixed8-v1";
export const ACTIVE=s=>s?.status==="scheduled"||s?.status==="running";
export function units(v){
 if(typeof v!=="string"||!/^[0-9]{1,10}(?:\.[0-9]{1,8})?$/.test(v))throw Error("invalid_decimal");
 const [a,b=""]=v.split(".");return BigInt(a)*S+BigInt(b.padEnd(8,"0"));
}
export function validateConfig(c){
 const keys=["request_id","fast","slow","equity","exposure_bps","taker_bps","tax_bps","slippage_bps","duration_minutes","acknowledge"];
 const directional=["direction","stop_bps","target_bps"].some(k=>c&&Object.hasOwn(c,k));
 const extended=directional||["signal_minutes","max_drawdown_bps"].some(k=>c&&Object.hasOwn(c,k));
 if(extended)keys.push("signal_minutes","max_drawdown_bps");
 if(directional)keys.push("direction","stop_bps","target_bps");
 if(!c||typeof c!=="object"||Array.isArray(c)||Object.keys(c).sort().join(",")!==keys.sort().join(",")||typeof c.request_id!=="string"||!/^[0-9a-f]{32}$/.test(c.request_id)||c.acknowledge!==true)throw Error("invalid_config");
 const int=(v,a,b)=>Number.isInteger(v)&&v>=a&&v<=b;
 if(!int(c.fast,2,99)||!int(c.slow,c.fast+1,200)||!int(c.exposure_bps,1,9000)||!int(c.taker_bps,0,100)||!int(c.tax_bps,0,10000)||!int(c.slippage_bps,0,100)||!int(c.duration_minutes,extended?(c.slow+2)*c.signal_minutes:c.slow+2,extended?43200:10080)||units(c.equity)<S||units(c.equity)>1000000n*S)throw Error("invalid_config");
 if(extended&&(![1,5,15,30,60].includes(c.signal_minutes)||!int(c.max_drawdown_bps,1,10000)||c.duration_minutes%c.signal_minutes))throw Error("invalid_config");
 if(directional&&(!["long","short","both"].includes(c.direction)||!int(c.stop_bps,0,10000)||!int(c.target_bps,0,10000)))throw Error("invalid_config");
 return {...c,equity: str(units(c.equity))};
}
export function init(symbol,c,now){
 const step=(c.signal_minutes??1)*60000;
 const start=Math.floor(now/step)*step+step;
 return {schema:1,engine:c.direction?"ema-cross-linear-fixed8-v3":c.signal_minutes?"ema-cross-fixed8-mtf-v2":VERSION,id:c.request_id,symbol,config:c,status:"scheduled",reason:null,start,end:start+c.duration_minutes*60000,cursor:start,
  balance:c.equity,qty:"0",entry:"0",entry_cost:"0",ema_fast:null,ema_slow:null,bars:0,...(c.signal_minutes?{signal_bars:0}:{}),pending:null,fees:"0",tax:"0",trades:0,fill_count:0,last_close:null,equity:c.equity,peak:c.equity,drawdown_bps:0};
}
export function parseCandle(raw,t){
 if(!raw||raw.time!==t/1000)throw Error("missing_candle");
 const p={time:t};
 for(const k of ["open","high","low","close"]){
  // Delta JSON numeric fields are converted to eight decimal places; this is a reference rounding policy.
  const value=raw[k];if(typeof value!=="number"&&typeof value!=="string")throw Error("invalid_candle");
  if(typeof value==="number"&&(!Number.isFinite(value)||value<=0||value>=1e10))throw Error("invalid_candle");
  const x=units(typeof value==="number"?value.toFixed(8):value);
  if(x<=0n)throw Error("invalid_candle");p[k]=str(x);
 }
 if(BigInt(p.low)>BigInt(p.open)||BigInt(p.low)>BigInt(p.close)||BigInt(p.high)<BigInt(p.open)||BigInt(p.high)<BigInt(p.close)||BigInt(p.low)>BigInt(p.high))throw Error("invalid_candle");
 return p;
}
const fee=(n,bps)=> (n*BigInt(bps)+BPS-1n)/BPS;
const ema=(prev,p,n)=>prev===null?p:(BigInt(prev)*BigInt(n-1)+p*2n)/BigInt(n+1);
export function advance(old,bar){
 if(!ACTIVE(old)||bar.time!==old.cursor)throw Error("cursor_mismatch");
 if(old.engine==="ema-cross-linear-fixed8-v3")return advanceDirectional(old,bar);
 const s=structuredClone(old),c=s.config;
 let cash=BigInt(s.balance),qty=BigInt(s.qty),entry=BigInt(s.entry),entryCost=BigInt(s.entry_cost);
 let fees=BigInt(s.fees),taxes=BigInt(s.tax);const events=[];
 const fill=(side,price,q,commission,tax,pnl)=>{
  s.fill_count++;
  events.push({id:s.fill_count,minute:bar.time,side,price:str(price),quantity:str(q),fee:str(commission),tax:str(tax),closed_net:pnl===null?null:str(pnl)});
  fees+=commission;taxes+=tax;
 };
 const open=BigInt(bar.open),close=BigInt(bar.close);
 if(s.pending==="buy"&&qty===0n&&cash>0n){
  const price=(open*(BPS+BigInt(c.slippage_bps))+BPS-1n)/BPS;
  const target=cash*BigInt(c.exposure_bps)/BPS;
  const q=target*S/price,n=q*price/S,commission=fee(n,c.taker_bps),tax=fee(commission,c.tax_bps);
  if(q>0n&&n+commission+tax<=cash){qty=q;entry=price;entryCost=n+commission+tax;cash-=entryCost;fill("buy",price,q,commission,tax,null);}
 }else if(s.pending==="sell"&&qty>0n){
  const price=open*(BPS-BigInt(c.slippage_bps))/BPS;
  const n=qty*price/S,commission=fee(n,c.taker_bps),tax=fee(commission,c.tax_bps);
  cash+=n-commission-tax;fill("sell",price,qty,commission,tax,n-commission-tax-entryCost);s.trades++;qty=0n;entry=0n;entryCost=0n;
 }
 s.pending=null;s.bars++;
 if((bar.time+60000)%((c.signal_minutes??1)*60000)===0){
  if(c.signal_minutes)s.signal_bars++;
  const fast=ema(s.ema_fast,close,c.fast),slow=ema(s.ema_slow,close,c.slow);
  if((s.signal_bars??s.bars)>c.slow&&s.ema_fast!==null&&s.ema_slow!==null){
   if(qty===0n&&BigInt(s.ema_fast)<=BigInt(s.ema_slow)&&fast>slow)s.pending="buy";
   if(qty>0n&&BigInt(s.ema_fast)>=BigInt(s.ema_slow)&&fast<slow)s.pending="sell";
  }
  s.ema_fast=str(fast);s.ema_slow=str(slow);
 }
 s.last_close=str(close);
 s.balance=str(cash);s.qty=str(qty);s.entry=str(entry);s.entry_cost=str(entryCost);s.fees=str(fees);s.tax=str(taxes);
 const equity=cash+qty*close/S,peak=BigInt(s.peak)>equity?BigInt(s.peak):equity;
 s.equity=str(equity);s.peak=str(peak);s.drawdown_bps=Math.max(s.drawdown_bps,Number((peak-equity)*BPS/peak));
 s.cursor+=60000;s.status="running";
 if(c.max_drawdown_bps!==undefined&&s.drawdown_bps>=c.max_drawdown_bps){s.status="halted";s.pending=null;s.reason="drawdown_limit";}
 else if(s.cursor>=s.end){s.status="completed";s.pending=null;s.reason="duration_reached";}
 // No terminal market order: open exposure stays visible.
 return {state:s,events};
}

/** Independent 1x linear P&L reference. Wallet includes reserved notional;
 * signed quantity, entry fees debited, exit fees and realized P&L at close.
 * Not a venue margin/liquidation model. Close-trigger exits fill next open.
 * Legacy spot-like v1/v2 sessions use their original accounting unchanged.
 */
function advanceDirectional(old,bar){
 const s=structuredClone(old),c=s.config,open=BigInt(bar.open),close=BigInt(bar.close);
 let wallet=BigInt(s.balance),qty=BigInt(s.qty),entry=BigInt(s.entry),entryCost=BigInt(s.entry_cost);
 let fees=BigInt(s.fees),taxes=BigInt(s.tax),events=[];
 const abs=n=>n<0n?-n:n;
 const netAt=p=>qty*(p-entry)/S;
 const priceFor=side=>side==="buy"?(open*(BPS+BigInt(c.slippage_bps))+BPS-1n)/BPS:open*(BPS-BigInt(c.slippage_bps))/BPS;
 const fill=(side,price,q,commission,tax,pnl,reason)=>{
  s.fill_count++;fees+=commission;taxes+=tax;
  events.push({id:s.fill_count,minute:bar.time,side,price:str(price),quantity:str(q),fee:str(commission),tax:str(tax),closed_net:pnl===null?null:str(pnl),reason});
 };
 const pending=s.pending;s.pending=null;
 if(pending&&(pending==="long"||pending==="short")&&qty===0n&&wallet>0n){
  const side=pending==="long"?"buy":"sell",price=priceFor(side);
  const target=wallet*BigInt(c.exposure_bps)/BPS,q=target*S/price,n=q*price/S;
  const commission=fee(n,c.taker_bps),tax=fee(commission,c.tax_bps);
  if(q>0n&&n+commission+tax<=wallet){
   qty=pending==="long"?q:-q;entry=price;entryCost=commission+tax;wallet-=entryCost;
   fill(side,price,q,commission,tax,null,"ema_entry");
  }
 }else if(pending&&["ema_exit","stop_close","target_close"].includes(pending)&&qty!==0n){
  const side=qty>0n?"sell":"buy",price=priceFor(side),q=abs(qty);
  const commission=fee(q*price/S,c.taker_bps),tax=fee(commission,c.tax_bps),pnl=netAt(price);
  wallet+=pnl-commission-tax;
  fill(side,price,q,commission,tax,pnl-commission-tax-entryCost,pending);
  s.trades++;qty=0n;entry=0n;entryCost=0n;
 }
 s.bars++;
 // Stop and target are checked using observed minute closes, never inferred
 // intrabar paths. Exit is queued at close and executed at the next open.
 if(qty!==0n){
  const move=(close-entry)*(qty>0n?1n:-1n);
  if(c.stop_bps&&move*BPS<=-entry*BigInt(c.stop_bps))s.pending="stop_close";
  else if(c.target_bps&&move*BPS>=entry*BigInt(c.target_bps))s.pending="target_close";
 }
 if((bar.time+60000)%(c.signal_minutes*60000)===0){
  s.signal_bars++;
  const fast=ema(s.ema_fast,close,c.fast),slow=ema(s.ema_slow,close,c.slow);
  if(s.signal_bars>c.slow&&s.ema_fast!==null&&s.ema_slow!==null&&!s.pending){
   const up=BigInt(s.ema_fast)<=BigInt(s.ema_slow)&&fast>slow;
   const down=BigInt(s.ema_fast)>=BigInt(s.ema_slow)&&fast<slow;
   if(qty===0n&&up&&c.direction!=="short")s.pending="long";
   else if(qty===0n&&down&&c.direction!=="long")s.pending="short";
   else if((qty>0n&&down)||(qty<0n&&up))s.pending="ema_exit";
  }
  s.ema_fast=str(fast);s.ema_slow=str(slow);
 }
 s.last_close=str(close);s.balance=str(wallet);s.qty=str(qty);s.entry=str(entry);s.entry_cost=str(entryCost);s.fees=str(fees);s.tax=str(taxes);
 const equity=wallet+netAt(close),peak=BigInt(s.peak)>equity?BigInt(s.peak):equity;
 // Negative equity is intentionally not floored: this is not a liquidation model.
 s.equity=str(equity);s.peak=str(peak);s.drawdown_bps=Math.max(s.drawdown_bps,Number((peak-equity)*BPS/peak));
 s.cursor+=60000;s.status="running";
 if(equity<=0n||s.drawdown_bps>=c.max_drawdown_bps){s.status="halted";s.pending=null;s.reason=equity<=0n?"nonpositive_equity":"drawdown_limit";}
 else if(s.cursor>=s.end){s.status="completed";s.pending=null;s.reason="duration_reached";}
 return {state:s,events};
}
