const {chromium}=require("playwright");
const {spawn}=require("node:child_process");
const assert=require("node:assert/strict");
(async()=>{
 const remote=process.env.DASHBOARD_SMOKE_REMOTE==="1";
 const server=spawn("python",["-m","http.server","8765","--bind","127.0.0.1","--directory",remote?"dashboard":"dashboard-dist"],{stdio:"ignore"});
 let browser;
 try{
  for(let i=0;i<50;i++){try{if((await fetch("http://127.0.0.1:8765")).ok)break}catch{}await new Promise(r=>setTimeout(r,100))}
  browser=await chromium.launch({headless:true});
  const page=await browser.newPage({viewport:{width:1440,height:900}});
  const errors=[],requests=[];
  page.on("pageerror",e=>errors.push(e.message));
  page.on("response",r=>{if(r.url().includes("/data/")){requests.push(r.url());if(!r.ok())errors.push(r.status()+" "+r.url())}});
  await page.goto("http://127.0.0.1:8765"+(remote?"?remote=1":""),{waitUntil:"networkidle"});
  await page.locator("#ledger tr").first().waitFor();
  await page.waitForFunction(()=>document.querySelector("#cursor").textContent.includes("UTC"));
  assert.ok(["BTCUSD","ETHUSD"].includes(await page.locator("#symbol").inputValue()));
  assert.equal(await page.locator("#frozenStrategies tbody tr").count(),2);
  assert.ok(await page.locator("#coverage").innerText().then(t=>t.includes("excluded")));
  assert.ok(await page.locator("#details").innerText().then(t=>t.includes("Why entered")&&t.includes("Why exited")));
  assert.ok(requests.filter(x=>x.includes("/candles/")).length<=1);
  if(remote){assert.ok(requests.some(x=>/^https:\/\/raw\.githubusercontent\.com\/rajkumar0rk\/BTC-Analysis\/[a-f0-9]{40}\/data\/index\.json$/.test(x)),"remote pinned index");assert.ok(requests.every(x=>x.startsWith("https://raw.githubusercontent.com/")),"no bundled data");await page.locator("#refreshData").click();await page.locator("#ledger tr").first().waitFor();}
  await page.locator("#play").click();await page.waitForTimeout(250);await page.locator("#full").click();
  await page.locator("#showCoverage").click();await page.locator("#archiveCoverage table").waitFor();
  const options=await page.locator("#symbol option").allTextContents();
  if(options.includes("ETHUSD")){
    await page.locator("#symbol").selectOption("ETHUSD");
    const full=await page.locator("#run option").evaluateAll(opts=>opts.find(o=>!o.textContent.includes("[summary only]"))?.value);
    assert.ok(full,"ETH full config");
    await page.locator("#run").selectOption(full);
    await page.locator("#ledger tr").first().waitFor();
    await page.waitForFunction(()=>document.querySelector("#details").textContent.includes("Why entered"));
  }
  await page.setViewportSize({width:390,height:844});
  assert.equal(errors.length,0,errors.join("\n"));
  console.log("Browser smoke passed; data requests:",requests.length);
 }finally{if(browser)await browser.close();server.kill()}
})().catch(e=>{console.error(e);process.exitCode=1});
