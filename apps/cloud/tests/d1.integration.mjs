import assert from "node:assert/strict";
import {createHash} from "node:crypto";
const root="http://127.0.0.1:8789/v1/cloud",alice="A".repeat(43),bob="B".repeat(43);
const digest=s=>createHash("sha256").update(s).digest("hex");
async function call(path,method="GET",data,token=alice){
 const r=await fetch(root+path,{method,headers:{Authorization:"Bearer "+token,Origin:"https://studio.example.com",...(data===undefined?{}:{"Content-Type":"application/json"})},body:data===undefined?undefined:JSON.stringify(data)});
 return {status:r.status,body:await r.json()};
}
if(process.argv.includes("--restart")){
 const id=process.env.CLOUD_TEST_STRATEGY_ID;
 const r=await call("/strategies/"+id+"/revisions/1");
 assert.equal(r.status,200);assert.equal(r.body.source,"pass");
 console.log("Persistent revision survived local worker restart");process.exit(0);
}
const cap=await call("/capabilities");assert.equal(cap.body.storage,true);assert.equal(cap.body.results_storage,true);
const a=await call("/strategies","POST",{name:"D1 test",source:"pass"});
assert.equal(a.status,201,JSON.stringify(a));const id=a.body.id,p="/strategies/"+id;
const race=await Promise.all([call(p,"PUT",{expected_version:1,source:"x=1"}),call(p,"PUT",{expected_version:1,source:"x=2"})]);
assert.deepEqual(race.map(r=>r.status).sort(),[200,409]);
assert.equal((await call(p+"/revisions/1")).body.source,"pass");
assert.equal((await call(p+"/revisions/1","GET",undefined,bob)).status,404);
assert.equal((await call(p,"PUT",{expected_version:2,source:"pass"},bob)).status,404);
assert.equal((await call("/strategies","GET",undefined,bob)).body.strategies.length,0);
const row={id:"1".repeat(32),strategy_id:id,version:1,code_sha256:digest("pass"),symbol:"BTCUSD",dataset_sha256:"2".repeat(64),result_sha256:"3".repeat(64),summary:{engine_version:"1",initial_equity:"100",scenarios:["O-H-L-C","O-L-H-C"].map(path=>({path,net_pnl:"1.25",drawdown_pct:"2",trades:3,profit_factor:"1.4",win_rate_pct:"66.7",monthly:[{month:"2025-01",pnl:"1.25"}]}))}};
const saved=await call("/results","POST",row);assert.equal(saved.status,201,JSON.stringify(saved));assert.equal(saved.body.verification,"client_reported");
assert.equal((await call("/results","POST",row)).status,200);
assert.equal((await call("/results","POST",{...row,result_sha256:"4".repeat(64)})).status,409);
assert.equal((await call("/results","POST",{...row,id:"5".repeat(32),code_sha256:"6".repeat(64)})).status,404);
assert.equal((await call("/results","POST",row,bob)).status,404);
assert.equal((await call("/results/"+row.id,"GET",undefined,bob)).status,404);
assert.equal((await call("/results/"+row.id,"DELETE",undefined,bob)).status,404);
assert.equal((await call("/results")).body.results.length,1);
assert.equal((await call("/results/"+row.id)).body.summary.scenarios.length,2);
assert.equal((await call("/results/"+row.id,"DELETE")).status,200);
assert.equal((await call("/results/"+row.id)).status,404);
for(let n=1;n<30;n++)assert.equal((await call("/strategies","POST",{name:"Quota "+n,source:"pass"})).status,201);
assert.equal((await call("/strategies","POST",{name:"Overflow",source:"pass"})).status,409);
assert.equal((await call("/strategies")).body.strategies.length,30);
const usage=await call("/operations");assert.equal(usage.status,200);assert.deepEqual(usage.body.usage,{strategies:30,revisions:31,results:0});assert.equal(usage.body.live_orders,false);assert.equal(usage.body.provider_metrics,"not_measured");
assert.equal((await call("/strategies","POST",{name:"Other owner",source:"pass"},bob)).status,201);
assert.deepEqual((await call("/operations","GET",undefined,bob)).body.usage,{strategies:1,revisions:1,results:0});
console.log("D1 integration passed: atomic CAS, owner isolation, result idempotency, deletion, quota.");
if(process.env.CLOUD_TEST_ID_FILE){const {writeFileSync}=await import("node:fs");writeFileSync(process.env.CLOUD_TEST_ID_FILE,id);}
