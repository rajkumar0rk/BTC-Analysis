import {chromium} from "../apps/web/node_modules/playwright/index.mjs";
import {spawn} from "node:child_process";
import {readFileSync,writeFileSync} from "node:fs";
import assert from "node:assert/strict";
const [file,out]=process.argv.slice(2),fixture=JSON.parse(readFileSync(file,"utf8"));
const root="http://127.0.0.1:8767/";
const server=spawn("python",["-m","http.server","8767","--bind","127.0.0.1","--directory","apps/web/dist"],{stdio:"ignore"});
let browser;
try{
 for(let n=0;n<60;n++){try{if((await fetch(root)).ok)break;}catch{}await new Promise(r=>setTimeout(r,200));}
 browser=await chromium.launch({headless:true});
 const page=await browser.newPage({viewport:{width:390,height:844}});
 const errors=[],external=[];page.on("pageerror",e=>errors.push(e.message));page.on("request",r=>{if(!r.url().startsWith(root)&&!r.url().startsWith("blob:")&&!r.url().startsWith("data:"))external.push(r.url());});
 await page.goto(root);
 const records=await page.evaluate(async f=>{
  const w=new Worker("./browser-python-worker.js");
  try{
   const run=id=>new Promise((resolve,reject)=>{
    const timeout=setTimeout(()=>reject(Error("31-day replay exceeded 120s")),120000);
    w.onerror=()=>{clearTimeout(timeout);reject(Error("Worker error"));};
    w.onmessage=({data:m})=>{
     if(m.id!==id)return;
     if(m.status==="error"){clearTimeout(timeout);reject(Error(m.message));}
     if(m.status==="done"){clearTimeout(timeout);resolve({result_sha256:m.result.result_sha256,bars:m.result.scenarios.map(s=>s.bars),compute_ms:m.elapsed_ms,total_ms:m.total_ms,cache:m.cacheStats});}
    };
    const {expected,native_seconds,...input}=f;w.postMessage({id,...input});
   });
   return {cold:await run(1),warm:await run(2)};
  }finally{w.terminate();}
 },fixture);
 for(const x of [records.cold,records.warm]){assert.equal(x.result_sha256,fixture.expected);assert.deepEqual(x.bars,[44640,44640]);}
 assert.equal(records.warm.cache.candle_hit,true);assert.ok(records.warm.cache.indicator_updates_reused>0);
 assert.deepEqual(errors,[]);assert.deepEqual(external,[]);
 const report={symbol:fixture.symbol,native_seconds:fixture.native_seconds,...records,runtime:"CI Chromium WASM; not mobile device or Cloudflare CPU"};
 console.log(JSON.stringify(report));writeFileSync(out,JSON.stringify(report,null,2));
}finally{await browser?.close();server.kill();}
