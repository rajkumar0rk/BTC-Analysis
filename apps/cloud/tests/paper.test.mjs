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
 const storage=new Memory(),obj=new PaperLane({storage},{});
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
 const staleStore=new Memory(),stale=new PaperLane({storage:staleStore},{});stale.now=()=>now;
 await stale.fetch(new Request("https://internal/start",{method:"POST",body:JSON.stringify({symbol:"ETHUSD",config})}));
 now=(await staleStore.get("state")).cursor+180001;await stale.alarm();assert.equal((await staleStore.get("state")).status,"halted");
});
