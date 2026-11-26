import test from "node:test";
import assert from "node:assert/strict";
import {validateConfig,init,advance,parseCandle,units} from "../src/paperEngine.mjs";
import {PaperLane} from "../src/paperObject.mjs";
const config={request_id:"a".repeat(32),fast:2,slow:3,equity:"100",exposure_bps:2000,taker_bps:5,tax_bps:1800,slippage_bps:0,duration_minutes:20,acknowledge:true};
const candle=(t,p)=>parseCandle({time:t/1000,open:p,high:p,low:p,close:p},t);
test("causal next-open entry, fee accounting and duplicate rejection",()=>{
 let s=init("BTCUSD",validateConfig(config),0),fills=[];
 for(const price of [100,90,80,110,111,80,79,120,121]){
  const prev=s;const r=advance(s,candle(s.cursor,price));s=r.state;fills.push(...r.events);
  assert.throws(()=>advance(s,candle(prev.cursor,price)),/cursor_mismatch/);
 }
 assert.equal(fills[0].side,"buy");assert.equal(fills[0].price,String(units("111")));
 assert.equal(fills[1].side,"sell");assert.equal(fills[1].price,String(units("79")));
 assert.ok(BigInt(s.fees)>0n&&BigInt(s.tax)>0n);assert.equal(s.trades,1);
 assert.equal(s.fill_count,fills.length);
 assert.throws(()=>parseCandle({time:0,open:100,low:110,high:120,close:100},0));
 assert.throws(()=>validateConfig({...config,slow:2}));
});
class Memory{
 map=new Map();alarm=null;
 async get(k){return structuredClone(this.map.get(k));}
 async put(k,v){this.map.set(k,structuredClone(v));}
 async delete(k){for(const x of Array.isArray(k)?k:[k])this.map.delete(x);}
 async setAlarm(t){this.alarm=t;}
 async deleteAlarm(){this.alarm=null;}
 async transaction(fn){return fn(this);}
}
test("alarm advances persisted cursor once, stale halt, stop during fetch fenced",async()=>{
 const storage=new Memory(),obj=new PaperLane({storage},{PAPER_ENABLED:"true"});
 let now=0;obj.now=()=>now;
 const start=()=>obj.fetch(new Request("https://internal/start",{method:"POST",body:JSON.stringify({symbol:"BTCUSD",config})}));
 assert.equal((await start()).status,201);assert.equal((await start()).status,200);
 let s=await storage.get("state");assert.equal(storage.alarm,s.cursor+70000);
 now=s.cursor+70000;obj.candle=async(_,t)=>candle(t,100);
 await obj.alarm();const one=await storage.get("state");assert.equal(one.bars,1);
 await obj.alarm();assert.equal((await storage.get("state")).bars,1);
 now=one.cursor+70000;obj.candle=async(_,t)=>{
  await obj.fetch(new Request("https://internal/stop",{method:"POST",body:JSON.stringify({id:one.id})}));
  return candle(t,100);
 };
 await obj.alarm();s=await storage.get("state");assert.equal(s.status,"stopped");assert.equal(s.bars,1);assert.equal(storage.alarm,null);
 const staleStore=new Memory(),stale=new PaperLane({storage:staleStore},{PAPER_ENABLED:"true"});stale.now=()=>now;
 await stale.fetch(new Request("https://internal/start",{method:"POST",body:JSON.stringify({symbol:"ETHUSD",config})}));
 now=(await staleStore.get("state")).cursor+180001;await stale.alarm();assert.equal((await staleStore.get("state")).status,"halted");
});

test("disabled paper alarm halts without fetching market",async()=>{
 const storage=new Memory(),obj=new PaperLane({storage},{PAPER_ENABLED:"true"});obj.now=()=>0;
 await obj.fetch(new Request("https://internal/start",{method:"POST",body:JSON.stringify({symbol:"BTCUSD",config})}));
 obj.env.PAPER_ENABLED="false";
 obj.candle=async()=>{throw Error("must not fetch");};await obj.alarm();
 const s=await storage.get("state");assert.equal(s.status,"halted");assert.equal(s.reason,"paper_disabled");assert.equal(storage.alarm,null);
});

test("multi-timeframe paper uses completed signals, next minute execution, and drawdown halt",()=>{
 const c=validateConfig({...config,signal_minutes:5,max_drawdown_bps:100,duration_minutes:43200,exposure_bps:9000});
 let s=init("BTCUSD",c,0),events=[];
 assert.equal(s.start,300000);
 const closes=[100,90,80,110,111,50];
 for(const p of closes){
  for(let n=0;n<5;n++){
   if(!["scheduled","running"].includes(s.status))break;
   const r=advance(s,candle(s.cursor,p));s=r.state;events.push(...r.events);
  }
 }
 assert.ok(s.signal_bars>=4);
 assert.equal(events[0].side,"buy");
 assert.equal(events[0].minute,300000+20*60000);
 assert.equal(events[0].price,String(units("111")));
 assert.equal(s.status,"halted");assert.equal(s.reason,"drawdown_limit");assert.equal(s.pending,null);
 assert.ok(BigInt(s.qty)>0n);
 assert.throws(()=>validateConfig({...config,signal_minutes:7,max_drawdown_bps:100}));
 assert.throws(()=>validateConfig({...config,signal_minutes:5,max_drawdown_bps:100,duration_minutes:21}));
});
test("disabled lane refuses starts",async()=>{
 const obj=new PaperLane({storage:new Memory()},{PAPER_ENABLED:"false"});
 const r=await obj.fetch(new Request("https://internal/start",{method:"POST",body:JSON.stringify({symbol:"BTCUSD",config})}));
 assert.equal(r.status,503);
});

test("directional linear short P&L and fee accounting; target fills at next open",()=>{
 const c=validateConfig({...config,signal_minutes:1,max_drawdown_bps:10000,direction:"short",stop_bps:0,target_bps:500,taker_bps:5,tax_bps:1800});
 let s=init("BTCUSD",c,0),fills=[];
 // Explicit pending entry isolates execution/accounting from signal generation.
 s.pending="short";
 for(const p of [100,90,85]){
  const r=advance(s,candle(s.cursor,p));s=r.state;fills.push(...r.events);
 }
 assert.equal(fills.length,2);assert.equal(fills[0].side,"sell");assert.equal(fills[1].side,"buy");assert.equal(fills[1].reason,"target_close");
 assert.equal(fills[1].price,strUnits("85"));assert.equal(s.qty,"0");
 const net=BigInt(fills[1].closed_net);
 assert.ok(net>0n);assert.equal(BigInt(s.balance),units("100")+net);
 assert.equal(BigInt(s.equity),BigInt(s.balance));assert.equal(s.trades,1);
});
const strUnits=v=>String(units(v));
test("directional modes follow completed EMA crosses and preserve old engines",()=>{
 for(const direction of ["long","short","both"]){
  const c=validateConfig({...config,signal_minutes:1,max_drawdown_bps:10000,direction,stop_bps:0,target_bps:0});
  let s=init("ETHUSD",c,0),fills=[];
  for(const p of [100,90,80,110,111,80,79,120,121,70,69,130,131]){
   const r=advance(s,candle(s.cursor,p));s=r.state;fills.push(...r.events);
  }
  const entries=fills.filter(x=>x.reason==="ema_entry");assert.ok(entries.length>0);
  if(direction==="short")assert.ok(entries.every(e=>e.side==="sell"));
  if(direction==="long")assert.ok(entries.every(e=>e.side==="buy"));
  assert.equal(s.engine,"ema-cross-linear-fixed8-v3");
 }
 assert.equal(init("BTCUSD",validateConfig(config),0).engine,"ema-cross-fixed8-v1");
 assert.throws(()=>validateConfig({...config,signal_minutes:1,max_drawdown_bps:1000,direction:"hedge",stop_bps:0,target_bps:0}));
});
test("short adverse price gap preserves negative equity and halts rather than inventing liquidation",()=>{
 const c=validateConfig({...config,signal_minutes:1,max_drawdown_bps:10000,direction:"short",stop_bps:100,target_bps:0,exposure_bps:9000});
 let s=init("BTCUSD",c,0);s.pending="short";
 s=advance(s,candle(s.cursor,100)).state;
 s=advance(s,candle(s.cursor,250)).state;
 assert.ok(BigInt(s.equity)<0n);assert.ok(BigInt(s.qty)<0n);assert.equal(s.status,"halted");assert.equal(s.reason,"nonpositive_equity");
});
