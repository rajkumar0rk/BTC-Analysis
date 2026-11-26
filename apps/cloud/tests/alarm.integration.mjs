import assert from "node:assert/strict";
const url="http://127.0.0.1:8790/v1/cloud/paper/BTCUSD/";
const id="c".repeat(32);
async function call(path,body){const r=await fetch(url+path,{method:body?"POST":"GET",headers:{Authorization:"Bearer "+"A".repeat(43),...(body?{"Content-Type":"application/json"}:{})},body:body?JSON.stringify(body):undefined,signal:AbortSignal.timeout(5000)});const b=await r.json();assert.ok(r.ok,JSON.stringify(b));return b;}
if(process.argv.includes("--start")){
 const r=await call("start",{request_id:id,fast:2,slow:3,equity:"100",exposure_bps:2000,taker_bps:5,tax_bps:1800,slippage_bps:0,duration_minutes:20,acknowledge:true});
 assert.equal(r.session.status,"scheduled");console.log("Alarm armed before runtime restart:",r.session.cursor);process.exit(0);
}
let s;
const deadline=Date.now()+220000;
while(Date.now()<deadline){
 s=(await call("state")).session;assert.equal(s.id,id);assert.notEqual(s.status,"halted",JSON.stringify(s));
 if(s.bars>=2)break;
 await new Promise(r=>setTimeout(r,2000));
}
assert.ok(s&&s.bars>=2,"real alarm did not advance twice");
assert.equal(s.cursor,s.start+s.bars*60000);assert.equal(s.fill_count,0);assert.equal(s.equity,"10000000000");
await call("stop",{id});
console.log("Real local scheduled alarms advanced after runtime restart:",JSON.stringify({bars:s.bars,cursor:s.cursor,status:s.status}));
