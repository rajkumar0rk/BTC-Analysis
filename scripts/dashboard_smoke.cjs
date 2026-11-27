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
  assert.ok(await page.locator("#coverage").innerText().then(t=>t.includes("Supertrend")));
  assert.ok(await page.locator("#supertrendStrategies tbody tr").count()>=12);
  await page.locator("#supertrendStrategies button").filter({hasText:"Details"}).first().click();
  assert.ok(await page.locator("#supertrendMonthly").innerText().then(t=>t.includes("Exact monthly series")));
  assert.ok(await page.locator("#details").innerText().then(t=>t.includes("Why entered")&&t.includes("Why exited")));
  assert.ok(requests.filter(x=>x.includes("/candles/")).length>=1);
  const before=await page.locator("#cursor").innerText();
  await page.locator("#timeframe").selectOption("15");
  assert.ok((await page.locator("#chartFrame").innerText()).startsWith("15m chart"));
  assert.equal((await page.locator("#cursor").innerText()).split(" · ")[0],before.split(" · ")[0]);
  const agg=await page.evaluate(()=>aggregate([[0,1,3,1,2,5],[60,2,5,2,4,7],[120,4,4,3,3,2]],3,true));
  assert.deepEqual(agg,[[0,1,5,1,3,14,3,0,120]]);
  assert.equal(await page.evaluate(()=>aggregate([[0,1,3,1,2,5],[120,4,4,3,3,2]],3,true).length),0);
  await page.locator("#timeframe").selectOption("1");
  await page.locator("#chart-reset").click();
  await page.waitForFunction(()=>chart&&nativeRows.length&&chart.timeScale().getVisibleLogicalRange());
  assert.equal(await page.evaluate(()=>window.LightweightCharts.version()),"5.0.9");
  const beforeRange=await page.evaluate(()=>chart.timeScale().getVisibleLogicalRange());
  await page.locator("#chart-zoom-in").click();
  const afterRange=await page.evaluate(()=>chart.timeScale().getVisibleLogicalRange());assert.ok(afterRange.to-afterRange.from<beforeRange.to-beforeRange.from);
  await page.locator("#chart-native").scrollIntoViewIfNeeded();
  const box=await page.locator("#chart-native").boundingBox();
  const coords=await page.evaluate(()=>{const ts=chart.timeScale(),w=ts.width(),h=chart.panes()[0].getHeight();return nativeRows.map(r=>[ts.timeToCoordinate(r[0]),candleSeries.priceToCoordinate(r[4])]).filter(([x,y])=>x>20&&x<w-20&&y>20&&y<h-20)});
  assert.ok(coords.length>=2);
  await page.mouse.move(box.x+coords[Math.floor(coords.length/3)][0],box.y+coords[Math.floor(coords.length/3)][1]);
  await page.waitForFunction(()=>document.querySelector("#chartInspect").textContent.includes("O "));
  await page.locator("#tool-measure").click();await page.locator("#chart-native").scrollIntoViewIfNeeded();
  const b=await page.locator("#chart-native").boundingBox(),a=coords[Math.floor(coords.length/3)],z=coords[Math.floor(coords.length*2/3)];
  await page.mouse.move(b.x+a[0],b.y+a[1]);await page.mouse.down();await page.mouse.move(b.x+z[0],b.y+z[1],{steps:8});await page.mouse.up();
  assert.ok(await page.evaluate(()=>drawings.some(d=>d.kind==="measure")));
  assert.deepEqual(await page.evaluate(()=>measurement({time:0,price:100},{time:900,price:110})),{delta:10,pct:10,bars:15,elapsed:"15m"});
  await page.locator("#tool-clear").click();assert.equal(await page.evaluate(()=>drawings.length),0);
  await page.locator("#tool-pan").click();
  const cutoff=await page.evaluate(()=>replayCutoff()),prior=await page.evaluate(()=>chart.timeScale().getVisibleLogicalRange().to);
  await page.locator("#chart-older").click();assert.ok(await page.evaluate(()=>chart.timeScale().getVisibleLogicalRange().to)<prior);
  await page.locator("#chart-newer").click();assert.equal(await page.evaluate(()=>replayCutoff()),cutoff);
  await page.locator("#replay-start").click();assert.equal(await page.evaluate(()=>limit),1);
  assert.ok(await page.evaluate(()=>nativeRows.every(r=>r[8]<replayCutoff())));
  const first=await page.evaluate(()=>replayCutoff());if(await page.evaluate(()=>bars.length)>1){await page.locator("#next").click();assert.ok(await page.evaluate(()=>replayCutoff())>first)}
  await page.locator("#replay-end").click();assert.equal(await page.evaluate(()=>replayMode),false);
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
  const research=page.locator("#supertrendStrategies button").filter({hasText:"Replay"}).first();await research.click();await page.locator("#ledger tr").first().waitFor();await page.waitForFunction(()=>document.querySelector("#details").textContent.includes("Why entered"));assert.equal(await page.locator("#netUnit").innerText(),"Net account USD");
  const generic=await page.evaluate(()=>{
    const r={id:"arbitrary-future-run",indicator_definitions:[{id:"custom1",name:"My custom formula",timeframe_minutes:30,panel:"panel",parameters:{lookback:17}}]};
    const t={indicator_series:{custom1:[[60,10],[120,null],[180,20]],unused:[[60,99]]},indicator_values:{custom1:10,unused:99}};
    return {declared:recordedIndicators(r,t),none:recordedIndicators({indicator_definitions:[]},t),legacy:recordedIndicators({},t),fields:legacySignalValues({signal_context:{ema20:123,rsi14:51,equity_after_usd:500}})}
  });
  assert.equal(generic.declared.length,1);assert.equal(generic.declared[0].id,"custom1");assert.equal(generic.declared[0].timeframe_minutes,30);assert.equal(generic.declared[0].points.length,3);
  assert.deepEqual(generic.none,[]);assert.deepEqual(generic.legacy,[]);assert.deepEqual(generic.fields,[["ema20",123],["rsi14",51]]);
  await page.locator("#timeframe").selectOption("60");assert.ok((await page.locator("#chartFrame").innerText()).startsWith("60m chart"));
  await page.setViewportSize({width:390,height:844});
  const nav=page.getByRole("navigation",{name:"Workspace navigation"});
  assert.equal(await nav.getByRole("link").count(),3);
  assert.equal(await nav.getByRole("link",{name:"Backtest Explorer",exact:true}).getAttribute("aria-current"),"page");
  assert.equal(await nav.getByRole("link",{name:"Strategy Studio",exact:true}).getAttribute("href"),"./studio/");
  assert.equal(await nav.getByRole("link",{name:"Private Cloud",exact:true}).getAttribute("href"),"https://btc-analysis.rajkumar55853.workers.dev");
  for(const width of [320,390,768,1440]){
    await page.setViewportSize({width,height:844});
    const layout=await nav.evaluate(el=>({display:getComputedStyle(el).display,width:el.clientWidth,scroll:el.scrollWidth,links:[...el.querySelectorAll("a")].map(a=>{const r=a.getBoundingClientRect();return {left:r.left,right:r.right,height:r.height,top:r.top,border:getComputedStyle(a).borderTopWidth}})}));
    assert.equal(layout.display,"grid");assert.ok(layout.scroll<=layout.width+1,"navigation overflow at "+width);
    for(let i=0;i<layout.links.length;i++){const a=layout.links[i];assert.ok(a.height>=44&&a.border!=="0px","styled tap target at "+width);if(i)assert.ok(a.left>=layout.links[i-1].right+4,"separate navigation links at "+width);}
  }
  assert.equal(errors.length,0,errors.join("\n"));
  console.log("Browser smoke passed; data requests:",requests.length);
 }finally{if(browser)await browser.close();server.kill()}
})().catch(e=>{console.error(e);process.exitCode=1});
