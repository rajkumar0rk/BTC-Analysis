import test from "node:test";
import assert from "node:assert/strict";
import worker,{makeHandler} from "../src/worker.mjs";
const origin="https://studio.example.com",token="A".repeat(43),other="B".repeat(43);
const digest=async s=>Buffer.from(await crypto.subtle.digest("SHA-256",new TextEncoder().encode(s))).toString("hex");
const env={ALLOWED_ORIGINS:origin,AUTH_HASHES_JSON:JSON.stringify({alice:await digest(token),bob:await digest(other)})};
const base="https://worker.example/v1/cloud";
const request=(path="",method="GET",auth=token,data,extra={})=>new Request(base+path,{method,headers:{Origin:origin,...(auth?{Authorization:"Bearer "+auth}:{}),...(data===undefined?{}:{"Content-Type":"application/json"}),...extra},...(data===undefined?{}:{body:typeof data==="string"?data:JSON.stringify(data)})});
test("fail closed without configured authentication or storage",async()=>{
 assert.equal((await worker.fetch(request("/capabilities"),{})).status,403);
 assert.equal((await worker.fetch(request("/capabilities"),{ALLOWED_ORIGINS:origin})).status,503);
 assert.equal((await worker.fetch(request("/capabilities","GET",null),env)).status,401);
 assert.equal((await worker.fetch(request("/capabilities","GET","Z".repeat(43)),env)).status,401);
 const r=await worker.fetch(request("/capabilities"),env);
 assert.equal(r.status,200);const b=await r.json();assert.equal(b.storage,false);assert.equal(b.source_execution,false);assert.equal(b.owner,"alice");
 assert.equal(r.headers.get("Cache-Control"),"no-store");assert.equal(r.headers.get("Access-Control-Allow-Origin"),origin);
 assert.equal((await worker.fetch(request("/strategies"),env)).status,503);
});
test("origin rejection, preflight and redaction",async()=>{
 let r=await worker.fetch(request("/capabilities","GET",token,undefined,{Origin:"https://evil.example"}),env);
 assert.equal(r.status,403);assert.equal(r.headers.get("Access-Control-Allow-Origin"),null);
 r=await worker.fetch(new Request(base+"/strategies",{method:"OPTIONS",headers:{Origin:origin,"Access-Control-Request-Method":"POST","Access-Control-Request-Headers":"authorization,content-type"}}),env);
 assert.equal(r.status,204);assert.equal(r.headers.get("Access-Control-Allow-Credentials"),null);
 assert.equal((await worker.fetch(request("/capabilities?token=secret"),env)).status,400);
 assert.equal((await worker.fetch(request("/orders","POST",token,{}),env)).status,404);
});
function memory(){
 const rows=new Map();
 const err=code=>Object.assign(new Error("private details"),{code});
 return {async list(owner){return [...rows.values()].filter(r=>r.owner===owner).map(r=>({id:r.id,name:r.name,latest_version:r.revs.length}));},
 async create(owner,v){const r={...v,owner,revs:[{...v,version:1}]};rows.set(v.id,r);return r.revs[0];},
 async revision(owner,id,v){const r=rows.get(id);return r?.owner===owner?r.revs[v-1]:null;},
 async revise(owner,id,expected,v){const r=rows.get(id);if(r?.owner!==owner)throw err("not_found");if(r.revs.length!==expected)throw err("version_conflict");const rev={...v,id,version:expected+1};r.revs.push(rev);return rev;}};
}
test("strategy contract, immutable revisions, ownership and CAS",async()=>{
 const handle=makeHandler(()=>store),store=memory();
 const r=await handle(request("/strategies","POST",token,{name:"EMA",source:"raise RuntimeError('must remain inert')"}),env);
 assert.equal(r.status,201);const one=await r.json();assert.equal(one.version,1);assert.match(one.id,/^[0-9a-f]{32}$/);assert.equal(one.code_sha256,await digest(one.source));
 const p="/strategies/"+one.id;
 assert.equal((await handle(request(p+"/revisions/1","GET",other),env)).status,404);
 assert.deepEqual((await (await handle(request("/strategies","GET",other),env)).json()).strategies,[]);
 const two=await handle(request(p,"PUT",token,{expected_version:1,source:"pass"}),env);assert.equal(two.status,200);assert.equal((await two.json()).version,2);
 assert.equal((await handle(request(p,"PUT",token,{expected_version:1,source:"pass"}),env)).status,409);
 const original=await (await handle(request(p+"/revisions/1"),env)).json();assert.equal(original.source,one.source);
 assert.equal((await handle(request("/strategies","POST",token,{name:"bad",source:"a".repeat(65537)}),env)).status,400);
 assert.equal((await handle(request("/strategies","POST",token,{name:"bad",source:"pass",owner:"bob"}),env)).status,400);
 assert.equal((await handle(request("/strategies","POST",token,"{broken"),env)).status,400);
 assert.equal((await handle(request("/strategies","POST",token,"a".repeat(100000)),env)).status,413);
 assert.equal((await handle(request("/strategies","POST",token,{} ,{"Content-Type":"text/plain"}),env)).status,415);
});
