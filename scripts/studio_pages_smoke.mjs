import {chromium} from "../apps/web/node_modules/playwright/index.mjs";
import {spawn} from "node:child_process";
import {readFileSync,mkdirSync,cpSync,rmSync,mkdtempSync} from "node:fs";
import {tmpdir} from "node:os";
import {join} from "node:path";
import assert from "node:assert/strict";
const root=mkdtempSync(join(tmpdir(),"studio-pages-"));mkdirSync(join(root,"BTC-Analysis"));
cpSync("dashboard-site",join(root,"BTC-Analysis"),{recursive:true});
const server=spawn("python",["-m","http.server","8766","--bind","127.0.0.1","--directory",root],{stdio:"ignore"});
let browser;
try{
 const origin="http://127.0.0.1:8766",url=origin+"/BTC-Analysis/studio/";
 for(let n=0;n<50;n++){try{if((await fetch(url)).ok)break;}catch{}await new Promise(r=>setTimeout(r,100));}
 browser=await chromium.launch({headless:true});const page=await browser.newPage({viewport:{width:390,height:844}});
 const errors=[],unexpected=[];page.on("pageerror",e=>errors.push(e.message));page.on("request",r=>{if(!r.url().startsWith(url)&&!r.url().startsWith("blob:")&&!r.url().startsWith("data:"))unexpected.push(r.url());});
 await page.goto(url);await page.getByRole("heading",{name:"Strategy Studio",exact:true}).waitFor();
 const nav=page.getByRole("navigation",{name:"Workspace navigation"});
 assert.equal(await nav.getByRole("link",{name:"Backtest Explorer",exact:true}).getAttribute("href"),"../");
 assert.equal(await nav.getByRole("link",{name:"Strategy Studio",exact:true}).getAttribute("aria-current"),"page");
 assert.equal(await nav.getByRole("link",{name:"Private Cloud",exact:true}).getAttribute("href"),"https://btc-analysis.rajkumar55853.workers.dev");
 assert.equal(await nav.getByRole("link",{name:"Private Cloud",exact:true}).getAttribute("rel"),"noreferrer");
 assert.equal(await page.getByLabel("Cloud bearer token").count(),0);
 assert.equal(await page.getByLabel("API access token").count(),0);
 await page.getByRole("button",{name:"Generate local Python"}).click();
 await page.getByLabel("Generated local Python").waitFor({timeout:120000});
 assert.match(await page.getByLabel("Generated local Python").inputValue(),/^# btc-visual-v1 /);
 await page.getByRole("button",{name:"Use generated strategy in backtest"}).click();
 const o=JSON.parse(readFileSync("apps/web/tests/browser-oracle.json","utf8"));
 await page.getByLabel("Historical CSV").setInputFiles({name:"fixture.csv",mimeType:"text/csv",buffer:Buffer.from(o.csv)});
 await page.getByLabel("Local visual source").fill(JSON.stringify(o.graph));
 await page.getByText("Assume CSV times are candle opens; provenance and contract specs are unverified.").click();
 await page.getByRole("button",{name:"Run local Python",exact:true}).click();
 await page.getByRole("heading",{name:"Local reference result"}).waitFor({timeout:125000});
 await page.getByText("Result SHA-256: "+o.result.result_sha256,{exact:false}).waitFor();
 assert.deepEqual(errors,[]);assert.deepEqual(unexpected,[]);
 console.log("Nested Pages smoke passed: local compiler, real WASM replay, native parity, no external API requests.");
}finally{await browser?.close();server.kill();rmSync(root,{recursive:true,force:true});}
