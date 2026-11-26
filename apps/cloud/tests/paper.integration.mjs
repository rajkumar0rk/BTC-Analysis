import assert from "node:assert/strict";
const root="http://127.0.0.1:8789/v1/cloud/paper/BTCUSD/";
async function call(path,method="GET",body,token="A".repeat(43)){
 const r=await fetch(root+path,{method,headers:{Authorization:"Bearer "+token,Origin:"https://studio.example.com",...(body?{"Content-Type":"application/json"}:{})},body:body?JSON.stringify(body):undefined});return {status:r.status,body:await r.json()};
}
const c={request_id:"a".repeat(32),fast:2,slow:3,equity:"100",exposure_bps:2000,taker_bps:5,tax_bps:1800,slippage_bps:0,duration_minutes:20,acknowledge:true};
if(process.argv.includes("--restart")){
 const s=await call("state");assert.equal(s.body.session.id,c.request_id);assert.equal(s.body.session.status,"stopped");
 const clear=await call("clear","POST",{id:c.request_id});assert.equal(clear.body.cleared,true);
 assert.equal((await call("state")).body.session,null);
 console.log("Paper DO persisted stopped session across restart and cleared explicitly.");
}else{
 assert.equal((await call("state")).body.session,null);
 const a=await call("start","POST",c);assert.equal(a.status,201,JSON.stringify(a));
 assert.equal((await call("start","POST",c)).status,200);
 assert.equal((await call("start","POST",{...c,fast:2,slow:4})).status,409);
 assert.equal((await call("state","GET",undefined,"B".repeat(43))).body.session,null);
 assert.equal((await call("clear","POST",{id:c.request_id})).status,409);
 assert.equal((await call("ledger?after=0")).body.fills.length,0);
 assert.equal((await call("stop","POST",{id:c.request_id},"B".repeat(43))).status,404);
 assert.equal((await call("stop","POST",{id:c.request_id})).body.session.status,"stopped");
 console.log("Paper DO local start, idempotency, owner isolation, stop passed.");
}
