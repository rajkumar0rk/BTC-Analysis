"use strict";
const $=id=>document.getElementById(id),fmt=n=>n==null?"Not recorded":Number(n).toLocaleString("en-US",{maximumFractionDigits:4}), esc=s=>String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c])),sign=n=>n>0?"pos":n<0?"neg":"";
let index,run,ledger=[],trade,bars=[],limit=0,timer,monthToken=0,tradeToken=0,windowDay=0,sourceBars=[],dayIndicatorSeries={},chartFrame=1,frameRun=null,curveToken=0,curves=[],page=0;const PAGE=100;
const cache=new Map();
// Native TradingView chart handles all market-series rendering and navigation.
const DAY=86400,MAX_HISTORY_DAYS=31,MIN_VISIBLE=6,MAX_VISIBLE=600;
let replayMode=false,browseAnchor=null,historyDays=new Map(),historyBusy=false,historyStatus="",historySerial=0;
let chart=null,candleSeries=null,markers=null,seriesById=new Map(),priceLines=[],nativeRows=[],nativeTimes=[],chartFrameRendered=null,chartStructure="",chartUpdating=false,resetRange=true,drawQueued=false,historyTimer=null;
let chartMode="pan",drawings=[],draft=null,drawingPointer=null,drawingQueued=false,undoStack=[],redoStack=[];
const drawingModes=["pan","measure","trend","horizontal","rectangle","ray","fib"];
let indicatorPreferences=new Map(),indicatorLegend=new Map(),latestIndicatorValues=new Map(),displayOptions={grid:true,marks:true,levels:true};
function clamp(v,lo,hi){return Math.max(lo,Math.min(hi,v))}
function replayCutoff(){return bars.length&&limit?bars[Math.min(limit,bars.length)-1][0]+60:null}
function dayKeys(){return (index?.candle_days?.[run?.symbol]||[]).map(d=>Date.parse(d+"T00:00:00Z")/1000)}
function archiveBounds(){const keys=dayKeys();return keys.length?{min:keys[0],max:keys.at(-1)+DAY}:{min:windowDay,max:windowDay+DAY}}
function chartCutoff(){return replayMode?replayCutoff():archiveBounds().max}
function resetViewport(clear=true){resetRange=true;draft=null;drawingPointer=null;if(clear){drawings=[];undoStack=[];redoStack=[];syncDrawingButtons()}scheduleDraw()}
function scheduleDraw(){if(!drawQueued){drawQueued=true;requestAnimationFrame(()=>{drawQueued=false;draw()})}}
function queueDrawings(){if(!drawingQueued){drawingQueued=true;requestAnimationFrame(()=>{drawingQueued=false;paintDrawings()})}}
function mergeHistory(){
 const sorted=[...historyDays.entries()].sort((a,b)=>a[0]-b[0]);sourceBars=sorted.flatMap(([,d])=>d.candles);
 const merged={};for(const [,d] of sorted)for(const [id,points] of Object.entries(d.series||{})){const m=merged[id]??(merged[id]=new Map());for(const p of points)if(Array.isArray(p)&&p.length===2)m.set(p[0],p[1])}
 dayIndicatorSeries=Object.fromEntries(Object.entries(merged).map(([id,m])=>[id,[...m].sort((a,b)=>a[0]-b[0])]))
}
async function fetchHistoryDay(day,r){
 const key=new Date(day*1000).toISOString().slice(0,10);
 const [candles,series]=await Promise.all([get("candles/"+r.symbol+"/"+key+".json"),(r.indicator_days||[]).includes(key)?get("runs/"+r.id+"/indicators/"+key+".json"):Promise.resolve({})]);return {candles,series}
}
function queueHistory(){clearTimeout(historyTimer);historyTimer=setTimeout(()=>void extendHistory(),100)}
function visibleTimes(){const range=chart?.timeScale().getVisibleLogicalRange();if(!range||!nativeTimes.length)return null;const first=nativeTimes[0],step=chartFrame*60;return {from:first+range.from*step,to:first+range.to*step}}
async function extendHistory(){
 if(historyBusy||!trade||!historyDays.size||!nativeTimes.length||chartUpdating)return;
 const v=visibleTimes();if(!v)return;
 const first=nativeTimes[0],last=nativeTimes.at(-1),span=chartFrame*60*20,cutoff=chartCutoff(),keys=dayKeys();
 const left=Math.floor(first/DAY)*DAY,right=Math.floor(last/DAY)*DAY;
 let day=null;
 if(v.from<=first+span)day=keys.filter(d=>d<left).at(-1)??null;
 if(day===null&&!replayMode&&v.to>=last-span)day=keys.find(d=>d>right)??null;
 if(day===null||day>=cutoff||historyDays.has(day))return;
 const token=tradeToken,serial=historySerial,r=run;historyBusy=true;historyStatus="Loading archived candles…";$("chartHistory").textContent=historyStatus;
 try{
  const data=await fetchHistoryDay(day,r);if(token!==tradeToken||serial!==historySerial)return;
  historyDays.set(day,data);
  if(historyDays.size>MAX_HISTORY_DAYS){const far=[...historyDays.keys()].filter(d=>d!==day).sort((a,b)=>day<left?b-a:a-b)[0];historyDays.delete(far)}
  mergeHistory();historyStatus="";draw();
 }catch(e){if(token===tradeToken&&serial===historySerial)historyStatus="History unavailable: "+e.message}
 finally{if(token===tradeToken&&serial===historySerial){historyBusy=false;$("chartHistory").textContent=historyStatus}}
}
function panBy(seconds){const ts=chart?.timeScale(),r=ts?.getVisibleLogicalRange();if(!r)return;stop();const n=seconds/(chartFrame*60);ts.setVisibleLogicalRange({from:r.from+n,to:r.to+n});queueHistory()}
function zoomBy(factor){const ts=chart?.timeScale(),r=ts?.getVisibleLogicalRange();if(!r)return;stop();const span=clamp((r.to-r.from)*factor,MIN_VISIBLE,MAX_VISIBLE),mid=(r.from+r.to)/2;ts.setVisibleLogicalRange({from:mid-span/2,to:mid+span/2});queueDrawings();queueHistory()}
function syncReplayControls(){
 $("chart-mode").value=replayMode?"replay":"browse";$("play").textContent=timer?"Pause":"Play replay";
 $("prev").disabled=!replayMode||limit<=1;$("next").disabled=!replayMode||limit>=bars.length;
 $("replay-start").disabled=!bars.length;$("replay-end").disabled=!bars.length;$("replay-seek").disabled=!replayMode||!bars.length;
 $("replay-seek").max=Math.max(1,bars.length);$("replay-seek").value=Math.max(1,limit)
}
function setReplayMode(on,reset=false){stop();replayMode=on;if(on&&reset)limit=1;resetRange=true;syncReplayControls();draw()}
function stepReplay(n){if(!bars.length)return;if(!replayMode)setReplayMode(true,true);limit=clamp(limit+n,1,bars.length);resetRange=true;syncReplayControls();draw()}
function setChartMode(mode){chartMode=mode;draft=null;drawingPointer=null;for(const id of drawingModes)$("tool-"+id).setAttribute("aria-pressed",String(id===mode));$("chart-drawings").style.pointerEvents=mode==="pan"?"none":"auto";$("chart-drawings").style.cursor=mode==="pan"?"default":"crosshair";queueDrawings()}
function elapsedLabel(seconds){const m=Math.round(Math.abs(seconds)/60),d=Math.floor(m/1440),h=Math.floor(m%1440/60);return (d?d+"d ":"")+(h?h+"h ":"")+(m%60||!d&&!h?m%60+"m":"")}
function measurement(a,b){const delta=b.price-a.price;return {delta,pct:a.price?delta/a.price*100:null,bars:Math.round(Math.abs(b.time-a.time)/(chartFrame*60)),elapsed:elapsedLabel(b.time-a.time)}}
function measurementText(a,b){const m=measurement(a,b),signed=n=>(n>=0?"+":"")+fmt(n);return signed(m.delta)+" pts · "+(m.pct===null?"n/a":signed(m.pct)+"%")+" · "+m.bars+" bars · "+m.elapsed}

const RAW="https://raw.githubusercontent.com/rajkumar0rk/BTC-Analysis/";
const LOCAL=["127.0.0.1","localhost"].includes(location.hostname)&&!new URLSearchParams(location.search).has("remote");
let dataBase=LOCAL?"./data/":"",activeSnapshot=null,refreshBusy=false;
async function json(url,options){const res=await fetch(url,options);if(!res.ok)throw Error("Data request failed ("+res.status+"): "+url);return res.json()}
async function get(path){const base=dataBase,key=base+path;if(cache.has(key)){const v=cache.get(key);cache.delete(key);cache.set(key,v);return v}const v=await json(key);if(base===dataBase){cache.set(key,v);if(cache.size>24)cache.delete(cache.keys().next().value)}return v}
function fail(e){$("notice").textContent="Unable to load data: "+e.message}
function options(el,items){el.replaceChildren(...items.map(([v,t])=>new Option(t,v)))}
function stop(){clearInterval(timer);timer=null;if($("play"))$("play").textContent="Play replay"}
function renderRun(preferredMonth=null,preferredTrade=null){run=index.runs.find(r=>r.id===$("run").value);if(!run)return;const unit=run.unit||"price points";$("netUnit").textContent="Net "+unit;$("monthUnit").textContent="Entry-month realized "+unit+"; not account MTM"+(run.automatic_version?" · "+(run.latest_version?"Latest":"Previous")+" version · source total "+fmt(run.source_summary.net)+" "+unit:"");options($("compare"),[["","None"],...index.runs.filter(r=>r.symbol===run.symbol&&r.unit===run.unit&&r.id!==run.id).map(r=>[r.id,runLabel(r)])]);renderComparison().catch(fail);$("metrics").innerHTML=[["Trades",run.trades],["Net "+unit,run.net],["Win rate",run.win_rate+"%"],["Profit factor",run.profit_factor??"N/A"],["Realized DD "+unit,run.drawdown]].map(([k,v],i)=>'<div class="metric"><small>'+k+'</small><strong class="'+(i===1?sign(v):"")+'">'+esc(typeof v==="number"?fmt(v):v)+'</strong></div>').join("");const max=Math.max(1,...run.months.map(m=>Math.abs(m.net)));$("months").replaceChildren(...run.months.map(m=>{const b=document.createElement("button");b.className="month "+sign(m.net);b.style.setProperty("--h",Math.max(2,Math.abs(m.net)/max*38)+"px");b.innerHTML='<span>'+esc(m.month.slice(2))+'</span><i></i><small>'+fmt(m.net)+'</small>';b.title=m.month+" · "+m.trades+" trades";b.onclick=()=>{$("month").value=m.month;loadMonth().catch(fail)};return b}));options($("month"),run.months.map(m=>[m.month,m.month+" ("+m.trades+")"]));$("month").value=run.months.some(m=>m.month===preferredMonth)?preferredMonth:run.months.filter(m=>m.trades>0).at(-1)?.month||run.months.at(-1)?.month||"";loadMonth(preferredTrade).catch(fail)}
async function loadMonth(preferredTrade=null){const seq=++monthToken;++tradeToken;stop();trade=null;bars=[];draw();$("details").textContent="Loading trades…";$("ledger").replaceChildren();$("notice").textContent="";ledger=[];page=0;if(run.detail_available===false){$("details").textContent="Summary only: full trade detail exceeds publication budget. Original ledger: "+run.source;$("count").textContent="Summary only";return}const data=await get("runs/"+run.id+"/"+$("month").value+".json");if(seq!==monthToken)return;ledger=data;renderLedger(preferredTrade)}
function renderLedger(preferredTrade=null){const filter=$("filter").value,list=ledger.filter(t=>!filter||(filter==="win"?t.net_points>0:t.net_points<=0));const preferredIndex=list.findIndex(t=>t.id===preferredTrade);if(preferredIndex>=0)page=Math.floor(preferredIndex/PAGE);page=Math.max(0,Math.min(page,Math.ceil(list.length/PAGE)-1));const shown=list.slice(page*PAGE,(page+1)*PAGE);$("count").textContent=list.length+" trades · page "+(page+1)+" / "+Math.max(1,Math.ceil(list.length/PAGE));$("ledger").replaceChildren(...shown.map(t=>{const tr=document.createElement("tr");tr.tabIndex=0;tr.innerHTML='<td>'+esc(t.entry_utc.slice(0,16))+'</td><td>'+(t.side===1?"LONG":"SHORT")+'</td><td>'+esc(t.result)+'</td><td class="'+sign(t.net_points)+'">'+fmt(t.net_points)+'</td>';tr.onclick=()=>selectTrade(t,tr).catch(fail);tr.onkeydown=e=>{if(e.key==="Enter"||e.key===" "){e.preventDefault();tr.click()}};return tr}));if(shown.length)$("ledger").children[preferredIndex>=0?preferredIndex%PAGE:0].click();else{++tradeToken;stop();trade=null;bars=[];draw();$("details").textContent="No matching trades."}}
function secs(t){return t?Date.parse(t.replace(" ","T"))/1000:NaN}
async function selectTrade(t,row){stop();resetViewport();replayMode=false;browseAnchor=null;trade=t;if(frameRun!==run.id){chartFrame=Number(t.signal_tf)||1;if(![1,3,5,15,30,60,240].includes(chartFrame))chartFrame=1;$("timeframe").value=String(chartFrame);frameRun=run.id}windowDay=Math.floor(secs(t.entry_utc)/86400)*86400;$("ledger").querySelectorAll("tr").forEach(x=>x.classList.toggle("active",x===row));const pairs=o=>'<dl>'+Object.entries(o).map(([k,v])=>'<dt>'+esc(k.replaceAll("_"," "))+'</dt><dd>'+esc(v==null?"Not recorded":typeof v==="number"?fmt(v):v)+'</dd>').join("")+'</dl>';$("details").innerHTML='<div class="details"><article><h3>Why entered</h3><p>'+esc(t.entry_reason||"Not recorded in source ledger")+'</p>'+pairs({audit:run.audit,signal_utc:t.trigger_utc,signal_minutes:t.signal_tf,entry_utc:t.entry_utc,entry_price:t.entry_price,...t.signal_context})+'</article><article><h3>Why exited</h3><p>'+esc(t.exit_reason||"Not recorded in source ledger")+'</p>'+pairs({exit_utc:t.exit_utc,exit_price:t.exit_price,stop_price:t.stop_price,target_price:t.target_price,trailing_stop_price:t.trailing_stop_price,liquidation_price:t.liquidation_price,gross_points:t.gross_points,fee_points:t.fee_points,slippage_points:t.assumed_slippage_points,[run.unit==="account USD"?"net_account_usd":"net_points"]:t.net_points,split:t.split})+'</article></div>';await loadWindow()}
function aggregate(rows,minutes,complete=false){
 const seconds=minutes*60,out=[];let g=null;
 for(const row of rows){const [t,o,h,l,c,v]=row,bucket=Math.floor(t/seconds)*seconds;
  if(!g||g[0]!==bucket){g=[bucket,o,h,l,c,v||0,1,t,t];out.push(g)}
  else{g[2]=Math.max(g[2],h);g[3]=Math.min(g[3],l);g[4]=c;g[5]+=v||0;g[6]++;g[8]=t}
 }
 return complete?out.filter(g=>g[6]===minutes&&g[7]===g[0]&&g[8]===g[0]+seconds-60):out
}
// Generic recorded indicator transport. No strategy-name dispatch.
function recordedIndicators(r,t){
 const defs=Array.isArray(r?.indicator_definitions)?r.indicator_definitions:[];
 const series={...(t?.indicator_series||{}),...(t===trade?dayIndicatorSeries:{})},values=t?.indicator_values||{},seen=new Set(),out=[];
 for(const d of defs.slice(0,64)){
  if(!d||typeof d.id!=="string"||!d.id||seen.has(d.id)||typeof d.name!=="string"||!Number.isInteger(d.timeframe_minutes)||d.timeframe_minutes<1||!["price","panel"].includes(d.panel))continue;
  seen.add(d.id);
  const raw=Object.hasOwn(series,d.id)?series[d.id]:null;
  const points=(Array.isArray(raw)?raw:[]).filter(p=>Array.isArray(p)&&p.length===2&&Number.isFinite(p[0])&&(p[1]===null||Number.isFinite(p[1]))).slice(0,100000).sort((a,b)=>a[0]-b[0]);
  out.push({...d,points,snapshot:Object.hasOwn(values,d.id)&&Number.isFinite(values[d.id])?values[d.id]:null})
 }
 return out
}
function legacySignalValues(t){
 return Object.entries(t?.signal_context||{}).filter(([key,v])=>Number.isFinite(v)&&/^(ema\d+|sma\d+|supertrend|rsi\d*|atr\d*|signal_atr|volume_ratio|atr_ratio|prior_high|prior_low|adx\d*|macd(?:_signal|_histogram)?|vwap|bollinger_(?:upper|middle|lower))$/i.test(key))
}
const indicatorColors=["#f0c36a","#67d4c0","#c5a1ff","#79baff","#fb7785","#f59e0b","#b8d68c","#f2a1c7"];
// Presentation registry is keyed by indicator output type, never strategy/run ID.
// It changes only visual styles; declared observations and native frames stay intact.
function indicatorType(d){return String(d.name).toLowerCase()}
// Only recognized output families are grouped; unknown custom outputs retain
// independent identities. Never infer or calculate missing outputs.
const indicatorCatalog={
 supertrend:{label:"Supertrend",outputs:["line","direction"],primary:"line"},
 bollinger:{label:"Bollinger Bands",outputs:["middle","upper","lower"],primary:"middle"},
 donchian:{label:"Donchian Channel",outputs:["middle","upper","lower"],primary:"middle"},
 macd:{label:"MACD",outputs:["line","signal","histogram"],primary:"line",levels:[0]},
 stochastic:{label:"Stochastic",outputs:["value","k","d","%k","%d","fast","slow"],primary:"k",levels:[20,50,80],range:[0,100]},
 stoch:{label:"Stochastic",outputs:["value","k","d","%k","%d","fast","slow"],primary:"k",levels:[20,50,80],range:[0,100]},
 rsi:{label:"RSI",outputs:["value"],primary:"value",levels:[30,50,70],range:[0,100]},
 williams:{label:"Williams %R",outputs:["value","r","percent_r"],primary:"value",levels:[-80,-50,-20],range:[-100,0]},
 williams_r:{label:"Williams %R",outputs:["value","r","percent_r"],primary:"value",levels:[-80,-50,-20],range:[-100,0]},
 williamsr:{label:"Williams %R",outputs:["value","r","percent_r"],primary:"value",levels:[-80,-50,-20],range:[-100,0]},
 cci:{label:"CCI",outputs:["value"],primary:"value",levels:[-100,0,100]},
 ema:{label:"EMA",outputs:["value"],primary:"value"},
 sma:{label:"SMA",outputs:["value"],primary:"value"},
 atr:{label:"ATR",outputs:["value"],primary:"value"},
 adx:{label:"ADX",outputs:["value"],primary:"value"},
 vwap:{label:"VWAP",outputs:["value"],primary:"value"}
};
function indicatorFamily(name){
 const [family,output,...rest]=String(name).toLowerCase().split(".");
 return !rest.length&&indicatorCatalog[family]?.outputs.includes(output)?family:null
}
function indicatorLevels(family){return [...(indicatorCatalog[family]?.levels||[])]}
function parameterEntries(d){return Object.entries(d.parameters||{}).sort(([x],[y])=>x.localeCompare(y))}
function sameIndicatorParams(a,b){return a.timeframe_minutes===b.timeframe_minutes&&JSON.stringify(parameterEntries(a))===JSON.stringify(parameterEntries(b))}
function pairedDirection(d,defs){return defs.find(x=>indicatorType(x)==="supertrend.direction"&&sameIndicatorParams(x,d))}
function indicatorKey(d){return JSON.stringify([d.name,d.timeframe_minutes,parameterEntries(d)])}
function indicatorFrame(d){return d.timeframe_minutes>=60&&d.timeframe_minutes%60===0?d.timeframe_minutes/60+"h":d.timeframe_minutes+"m"}
function indicatorLabel(d){
 const type=indicatorType(d),family=indicatorFamily(type),p=d.parameters||{},frame=indicatorFrame(d);
 if(!family)return d.name+" ("+parameterEntries(d).map(([k,v])=>k+"="+String(v)).join(", ")+(Object.keys(p).length?", ":"")+frame+")";
 const name=type==="supertrend.direction"?"Supertrend direction":indicatorCatalog[family].label;
 const params=p.fast!=null&&p.slow!=null&&p.signal!=null?" "+[p.fast,p.slow,p.signal].join(", "):(p.period!=null?" "+p.period:"")+(p.multiplier!=null?" × "+p.multiplier:"");
 const extras=parameterEntries(d).filter(([k])=>!["period","multiplier","fast","slow","signal"].includes(k)).map(([k,v])=>k+"="+String(v));
 return name+params+(extras.length?" ("+extras.join(", ")+")":"")+" · "+frame
}
function groupIndicators(defs){
 const groups=new Map();
 for(const d of defs){
  const family=indicatorFamily(d.name),type=indicatorType(d);
  // Supertrend line and direction may be declared in different panels.
  const key=family?JSON.stringify([family,d.timeframe_minutes,parameterEntries(d),family==="supertrend"?"combined":d.panel]):"custom:"+d.id;
  let g=groups.get(key);
  // A second declaration with an identical output cannot overwrite the first.
  if(g?.outputs.some(o=>indicatorType(o)===type)){g=null}
  if(!g){g={key:groups.has(key)?key+":"+d.id:key,family,outputs:[]};groups.set(g.key,g)}
  g.outputs.push(d)
 }
 return [...groups.values()].map(g=>{
  const cfg=indicatorCatalog[g.family],primary=g.outputs.find(d=>indicatorType(d)===g.family+"."+cfg?.primary)||g.outputs[0];
  const direction=g.family==="supertrend"?g.outputs.find(d=>indicatorType(d)==="supertrend.direction"):null;
  const helper=direction&&direction!==primary?direction:null;
  return {...g,primary,helper,label:indicatorLabel(primary),panel:primary.panel,plotted:g.outputs.filter(d=>d!==helper)}
 })
}
function indicatorVisual(d,i,defs){
 const type=indicatorType(d),paired=type==="supertrend.direction"&&defs.some(x=>indicatorType(x)==="supertrend.line"&&sameIndicatorParams(x,d));
 const color=({"ema.value":"#f0b44c","sma.value":"#60a5fa","supertrend.line":"#26a69a","supertrend.direction":"#26a69a","rsi.value":"#b794f4","atr.value":"#60a5fa","macd.line":"#42a5f5","macd.signal":"#ff9800","macd.histogram":"#26a69a","bollinger.middle":"#f0b44c","bollinger.upper":"#60a5fa","bollinger.lower":"#60a5fa","donchian.middle":"#f0b44c","donchian.upper":"#60a5fa","donchian.lower":"#60a5fa","stochastic.k":"#60a5fa","stochastic.d":"#ff9800"})[type]||indicatorColors[i%indicatorColors.length];
 const pref=indicatorPreferences.get(indicatorKey(d))||{};
 return {visible:pref.visible??!paired,color:pref.color||color,width:pref.width||2,type,paired};
}
function visibleIndicatorDefs(groups,all){
 const out=[];
 for(const [i,g] of groups.entries()){
  const style=indicatorVisual(g.primary,i,all);
  if(!style.visible)continue;
  for(const [j,d] of g.plotted.entries()){
   const own=indicatorVisual(d,i+j,all);
   out.push({...d,panel:g.panel,groupKey:g.key,family:g.family,visual:{...own,width:style.width,visible:true}})
  }
  // Diagnostic is opt-in and not a second normal legend item. Ignore old
  // per-output visibility preferences from the ungrouped UI.
  if(g.helper&&indicatorPreferences.get(indicatorKey(g.primary))?.diagnostic===true)
   out.push({...g.helper,panel:"panel",groupKey:g.key+":diagnostic",family:null,visual:{...indicatorVisual(g.helper,i,all),visible:true}})
 }
 return out
}
function setIndicatorPref(d,patch){const k=indicatorKey(d);indicatorPreferences.set(k,{...indicatorPreferences.get(k),...patch});saveChartPreferences();draw()}
function saveChartPreferences(){try{localStorage.setItem("btc-chart-ui-v1",JSON.stringify({indicators:[...indicatorPreferences],options:displayOptions}))}catch{}}
function restoreChartPreferences(){try{const p=JSON.parse(localStorage.getItem("btc-chart-ui-v1")||"{}");if(Array.isArray(p.indicators))for(const [k,v] of p.indicators.slice(0,256)){if(typeof k!=="string"||!v||typeof v!=="object")continue;indicatorPreferences.set(k,{...(typeof v.visible==="boolean"?{visible:v.visible}:{}),...(typeof v.diagnostic==="boolean"?{diagnostic:v.diagnostic}:{}),...(/^#[0-9a-f]{6}$/i.test(v.color||"")?{color:v.color}:{}),...([1,2,3,4].includes(v.width)?{width:v.width}:{})})}for(const k of Object.keys(displayOptions))if(typeof p.options?.[k]==="boolean")displayOptions[k]=p.options[k]}catch{}}
restoreChartPreferences();
function indicatorValueLabel(d,v){if(!Number.isFinite(v))return "—";if(indicatorType(d)==="supertrend.direction")return v===1?"Bullish":v===-1?"Bearish":fmt(v);return fmt(v)}
function outputLabel(d){const name=indicatorType(d).split(".").at(-1);return ({middle:"Basis",upper:"Upper",lower:"Lower",line:"Line",signal:"Signal",histogram:"Hist",k:"%K",d:"%D"})[name]||name}
function updateIndicatorLegend(values){
 for(const {group:g,value,swatch} of indicatorLegend.values()){
  if(g.helper){
   const side=values.get(g.helper.id),state=side===1?"Bullish":side===-1?"Bearish":"Direction unavailable";
   value.textContent=indicatorValueLabel(g.primary,values.get(g.primary.id))+" · "+state;
   value.className=side===1?"pos":side===-1?"neg":"";
   swatch.style.background=side===1?"#26a69a":side===-1?"#ef5350":"#8492a6";
  }else{
   value.textContent=g.plotted.length===1?indicatorValueLabel(g.primary,values.get(g.primary.id)):g.plotted.map(d=>outputLabel(d)+" "+indicatorValueLabel(d,values.get(d.id))).join(" · ");
   value.className=""
  }
 }
}
function renderIndicatorControls(groups,defs){
 const host=$("indicatorValues");host.replaceChildren();indicatorLegend=new Map();
 for(const [i,g] of groups.entries()){
  const d=g.primary,visual=indicatorVisual(d,i,defs),row=document.createElement("span");row.className="indicator-control"+(visual.visible?"":" indicator-hidden");row.dataset.family=g.family||"custom";
  const toggle=document.createElement("button");toggle.type="button";toggle.className="indicator-eye";toggle.textContent=visual.visible?"◉":"○";toggle.title=(visual.visible?"Hide ":"Show ")+g.label;toggle.setAttribute("aria-label",toggle.title);toggle.setAttribute("aria-pressed",String(visual.visible));toggle.onclick=()=>setIndicatorPref(d,{visible:!visual.visible});
  const swatch=document.createElement("span");swatch.className="indicator-swatch";swatch.style.background=visual.color;
  const label=document.createElement("span");label.textContent=g.label;label.title=g.outputs.map(x=>x.name).join(", ")+" · "+JSON.stringify(d.parameters||{});
  const value=document.createElement("strong");value.textContent="—";indicatorLegend.set(g.key,{group:g,value,swatch});row.append(toggle,swatch,label,value);host.append(row);
 }
}
function renderIndicatorSettings(defs){
 const host=$("indicatorSettings");host.replaceChildren();const groups=groupIndicators(defs);
 for(const [i,g] of groups.entries()){
  const d=g.primary,visual=indicatorVisual(d,i,defs),row=document.createElement("div");row.className="indicator-setting";
  const label=document.createElement("label"),enabled=document.createElement("input");enabled.type="checkbox";enabled.checked=visual.visible;enabled.onchange=()=>setIndicatorPref(d,{visible:enabled.checked});label.append(enabled,document.createTextNode(g.label));
  const color=document.createElement("input");color.type="color";color.value=visual.color;color.setAttribute("aria-label","Color "+g.label);color.disabled=!!g.helper;color.title=color.disabled?"Uses recorded bullish/bearish direction":"Primary output color";color.onchange=()=>setIndicatorPref(d,{color:color.value});
  const width=document.createElement("select");width.setAttribute("aria-label","Line width "+g.label);options(width,[1,2,3,4].map(n=>[String(n),n+" px"]));width.value=String(visual.width);width.onchange=()=>setIndicatorPref(d,{width:Number(width.value)});
  row.append(label,color,width);host.append(row);
  if(g.helper){const diagnostic=document.createElement("label"),check=document.createElement("input");diagnostic.className="indicator-diagnostic";check.type="checkbox";check.checked=indicatorPreferences.get(indicatorKey(d))?.diagnostic===true;check.onchange=()=>setIndicatorPref(d,{diagnostic:check.checked});diagnostic.append(check,document.createTextNode("Show "+g.label+" direction diagnostic"));host.append(diagnostic)}
  const levels=indicatorLevels(g.family);if(levels.length){const info=document.createElement("small");info.className="indicator-reference";info.textContent="Display guides: "+levels.slice().reverse().join(" / ");host.append(info)}
 }
 if(!groups.length)host.textContent="No indicator definitions available for this result.";
}
function sampleIndicator(d,rows,cutoff){
 let j=-1;return rows.map(r=>{const end=Math.min(r[8]+60,cutoff);while(j+1<d.points.length&&d.points[j+1][0]<=end)j++;const v=j>=0&&end-d.points[j][0]<d.timeframe_minutes*60?d.points[j][1]:null;return [r[0],Number.isFinite(v)?v:null]})
}
function syncTimeframeButtons(){for(const b of $("frameButtons").querySelectorAll("button"))b.setAttribute("aria-pressed",String(Number(b.dataset.frame)===chartFrame))}
function updateChartHeading(){const title=$("chartInstrument");title.textContent=(run?.symbol||"Market")+" · "+(chartFrame>=60&&chartFrame%60===0?chartFrame/60+"h":chartFrame+"m")+" · UTC";syncTimeframeButtons()}

async function loadWindow(){
 const token=++tradeToken,t=trade,r=run;stop();historySerial++;historyBusy=false;historyStatus="";historyDays=new Map();bars=[];sourceBars=[];dayIndicatorSeries={};resetRange=true;draw();if(!t)return;
 const available=new Set(index.candle_days?.[r.symbol]||[]),day=new Date(windowDay*1000).toISOString().slice(0,10);if(!available.has(day)){if(token===tradeToken)$("cursor").textContent="No source candles for "+day;return}
 const data=await fetchHistoryDay(windowDay,r);if(token!==tradeToken)return;historyDays.set(windowDay,data);mergeHistory();
 const anchor=Math.min(secs(t.entry_utc),secs(t.trigger_utc)||secs(t.entry_utc)),start=Math.max(windowDay,Math.floor((anchor-1800)/14400)*14400),end=Math.min(windowDay+86399,secs(t.exit_utc)+1800);
 bars=data.candles.filter(c=>c[0]>=start&&c[0]<=end);if(!bars.length)bars=data.candles;limit=bars.length;
 browseAnchor=replayCutoff();syncReplayControls();draw();queueHistory()
}
function createNativeChart(defs){
 const lib=window.LightweightCharts;
 if(!lib||typeof lib.createChart!=="function")throw Error("TradingView Lightweight Charts bundle missing; run scripts/prepare_dashboard_chart.sh");
 if(chart)chart.remove();seriesById=new Map();priceLines=[];markers=null;
 const host=$("chart-native");host.style.setProperty("--chart-height",(440+new Set(defs.filter(d=>d.panel==="panel").map(d=>d.groupKey)).size*160)+"px");
 chart=lib.createChart(host,{autoSize:true,layout:{background:{type:"solid",color:"#131722"},textColor:"#a7b1c2",fontSize:12,attributionLogo:true,panes:{enableResize:true,separatorColor:"#303849",separatorHoverColor:"#53617a"}},grid:{vertLines:{color:"#242b38",visible:displayOptions.grid},horzLines:{color:"#242b38",visible:displayOptions.grid}},crosshair:{mode:lib.CrosshairMode.Normal,vertLine:{color:"#758096",width:1,style:lib.LineStyle.Dashed,labelBackgroundColor:"#364152"},horzLine:{color:"#758096",width:1,style:lib.LineStyle.Dashed,labelBackgroundColor:"#364152"}},rightPriceScale:{borderColor:"#26364a",minimumWidth:80},timeScale:{borderColor:"#26364a",timeVisible:true,secondsVisible:false,rightOffset:3,barSpacing:10,minBarSpacing:2,fixLeftEdge:false,fixRightEdge:false},handleScroll:{mouseWheel:true,pressedMouseMove:true,horzTouchDrag:true,vertTouchDrag:false},handleScale:{axisPressedMouseMove:true,mouseWheel:true,pinch:true},kineticScroll:{mouse:true,touch:true}});
 candleSeries=chart.addSeries(lib.CandlestickSeries,{upColor:"#26a69a",downColor:"#ef5350",borderVisible:false,wickUpColor:"#26a69a",wickDownColor:"#ef5350",priceFormat:{type:"price",precision:2,minMove:.01}});
 let pane=0;const panesByGroup=new Map(),guidesApplied=new Set();
 for(const d of defs){
  const visual=d.visual;
  if(d.panel==="panel"&&!panesByGroup.has(d.groupKey))panesByGroup.set(d.groupKey,++pane);
  const panel=d.panel==="panel"?panesByGroup.get(d.groupKey):0,stepLine=visual.type==="supertrend.line"||visual.type==="supertrend.direction";
  const cfg=indicatorCatalog[d.family],levels=indicatorLevels(d.family),hist=visual.type==="macd.histogram";
  const opts={title:indicatorLabel(d)+(d.family&&["bollinger","donchian","macd","stochastic","stoch"].includes(d.family)?" · "+outputLabel(d):""),color:visual.color,priceLineVisible:false,lastValueVisible:true,priceFormat:{type:"price",precision:2,minMove:.01}};
  if(!hist)Object.assign(opts,{lineWidth:visual.width,lineType:stepLine?lib.LineType.WithSteps:lib.LineType.Simple,crosshairMarkerVisible:true});
  else opts.base=0;
  if(cfg?.range)opts.autoscaleInfoProvider=()=>({priceRange:{minValue:cfg.range[0],maxValue:cfg.range[1]}});
  else if(levels.length)opts.autoscaleInfoProvider=original=>{const a=original();if(!a?.priceRange)return a;return {...a,priceRange:{minValue:Math.min(a.priceRange.minValue,...levels),maxValue:Math.max(a.priceRange.maxValue,...levels)}}};
  const series=chart.addSeries(hist?lib.HistogramSeries:lib.LineSeries,opts,panel);seriesById.set(d.id,series);
  if(panel>0&&!guidesApplied.has(d.groupKey)){
   for(const [i,value] of levels.entries()){const middle=levels.length===1||i===Math.floor(levels.length/2);series.createPriceLine({price:value,color:middle?"#65738a":"#9a80c7",lineWidth:1,lineStyle:middle?lib.LineStyle.Dotted:lib.LineStyle.Dashed,axisLabelVisible:true,title:levels.length===1?"Zero":middle?"Middle":i===0?"Lower":"Upper"})}
   if(visual.type==="supertrend.direction")series.createPriceLine({price:0,color:"#526075",lineWidth:1,lineStyle:lib.LineStyle.Dotted,axisLabelVisible:false,title:""});
   guidesApplied.add(d.groupKey)
  }
 }
 markers=lib.createSeriesMarkers(candleSeries,[]);
 chart.timeScale().subscribeVisibleLogicalRangeChange(()=>{queueDrawings();if(!chartUpdating){updateRangeLabel();queueHistory()}});
 chart.subscribeCrosshairMove(param=>{
  if(!param.time||typeof param.time!=="number"){updateIndicatorLegend(latestIndicatorValues);return}
  const row=param.seriesData.get(candleSeries);
  if(!row||row.open===undefined){$("chartInspect").textContent="No source candle at this time";return}
  const source=nativeRows.find(r=>r[0]===param.time),pieces=[new Date(param.time*1000).toISOString().slice(0,16).replace("T"," ")+" UTC","O "+fmt(row.open),"H "+fmt(row.high),"L "+fmt(row.low),"C "+fmt(row.close),source?"Vol "+fmt(source[5]):""];
  const values=new Map();for(const [id,lookup] of sampledIndicators)values.set(id,lookup.get(param.time));
  updateIndicatorLegend(values);$("chartInspect").textContent=pieces.filter(Boolean).join("  ·  ")
 });
 const panes=chart.panes();if(panes.length>1){for(const p of panes.slice(1))p.setHeight(160)}
}
function updateRangeLabel(){const range=chart?.timeScale().getVisibleRange();if(!range)return;const label=t=>new Date(Number(t)*1000).toISOString().slice(0,16).replace("T"," ");$("chartRange").textContent="View: "+label(range.from)+" – "+label(range.to)+" UTC · "+historyDays.size+" loaded day"+(historyDays.size===1?"":"s")}
let sampledIndicators=new Map();
function draw(){
 const declared=trade?recordedIndicators(run,trade):[],legacy=trade&&!Array.isArray(run?.indicator_definitions)?legacySignalValues(trade):[],show=$("overlay").checked,groups=groupIndicators(declared),defs=show?visibleIndicatorDefs(groups,declared):[];
 updateChartHeading();
 $("chartFrame").textContent=chartFrame+"m chart · recorded 1m execution · UTC";
 $("indicatorInfo").textContent=trade?(declared.length?(run.indicator_provenance?.method==="pinned_input_replay_snapshot_verified"?"Strategy indicators · reproduced from pinned original inputs and verified against recorded signal values.":"Declared strategy indicators · recorded data only; missing series are not reconstructed."):Array.isArray(run?.indicator_definitions)?"No indicators declared for this strategy.":legacy.length?"Legacy archive: recorded signal fields only; indicator declarations and time series unavailable.":"Legacy archive: no indicator declarations or recorded indicator fields."):"";
 $("chartHistory").textContent=historyStatus;$("chartInspect").textContent="Hover a candle to inspect OHLC and indicator values.";renderIndicatorControls(show?groups:[],declared);if($("chart-settings").open)renderIndicatorSettings(declared);
 const structure=JSON.stringify(defs.map(d=>[d.id,d.name,d.panel,d.groupKey,d.family,d.timeframe_minutes,d.parameters,d.visual]));
 const previous=chart&&!resetRange&&chartFrameRendered===chartFrame?visibleTimes():null;
 chartUpdating=true;
 try{
  if(!chart||structure!==chartStructure){createNativeChart(defs);chartStructure=structure}
  chart.applyOptions({grid:{vertLines:{visible:displayOptions.grid},horzLines:{visible:displayOptions.grid}}});
  const cutoff=chartCutoff(),step=chartFrame*60;
  nativeRows=trade&&bars.length&&cutoff!==null?aggregate(sourceBars.filter(r=>r[0]<cutoff),chartFrame):[];
  nativeTimes=[];
  // Use explicit whitespace only within the loaded continuous date span.
  // Missing bars remain empty, never synthesized as OHLC.
  if(nativeRows.length){const first=nativeRows[0][0],last=nativeRows.at(-1)[0];for(let t=first;t<=last;t+=step){if(nativeTimes.length>=45000)throw Error("Chart data exceeds history budget");nativeTimes.push(t)}}
  const byTime=new Map(nativeRows.map(r=>[r[0],r]));
  candleSeries.setData(nativeTimes.map(time=>{const r=byTime.get(time);return r?{time,open:r[1],high:r[2],low:r[3],close:r[4],...(r[6]<chartFrame?{color:r[4]>=r[1]?"#217e69":"#984954",wickColor:r[4]>=r[1]?"#217e69":"#984954"}:{})}:{time}}));
  const chip=(label,color)=>{const el=document.createElement("span");el.className="indicator-chip";el.textContent=label;if(color)el.style.borderColor=color;$("indicatorValues").append(el)};
  sampledIndicators=new Map(declared.map(d=>[d.id,new Map(sampleIndicator(d,nativeRows,cutoff))]));
  latestIndicatorValues=new Map(declared.map(d=>[d.id,sampledIndicators.get(d.id)?.get(nativeRows.at(-1)?.[0])]));
  for(const d of defs){
   const lookup=sampledIndicators.get(d.id),direction=d.visual.type==="supertrend.line"?pairedDirection(d,declared):null,dir=direction?sampledIndicators.get(direction.id):null;
   const data=nativeTimes.map(time=>{const v=lookup.get(time);if(!Number.isFinite(v))return {time};const side=dir?.get(time)??(d.visual.type==="supertrend.direction"?v:d.visual.type==="macd.histogram"?Math.sign(v):null);return {time,value:v,...(side===1?{color:"#26a69a"}:side===-1?{color:"#ef5350"}:direction?{color:"#8492a6"}:{})}});
   seriesById.get(d.id).setData(data);
  }
  updateIndicatorLegend(latestIndicatorValues);
  if(show&&trade&&secs(trade.trigger_utc)<=cutoff)for(const [key,value] of legacy)chip(key.toUpperCase()+": "+fmt(value));
  for(const p of priceLines)candleSeries.removePriceLine(p);priceLines=[];
  if(trade&&nativeTimes.length){
   const mark=[];
   for(const [time,price,text,color] of [[secs(trade.entry_utc),trade.entry_price,"ENTRY","#66b5ff"],[secs(trade.exit_utc),trade.exit_price,"EXIT","#c5a1ff"]]){
    const bucket=Math.floor(time/step)*step;if(time<=cutoff&&byTime.has(bucket)&&Number.isFinite(price))mark.push({time:bucket,position:text==="ENTRY"?"belowBar":"aboveBar",shape:text==="ENTRY"?"arrowUp":"arrowDown",color,text:text+" "+fmt(price)})
   }
   markers.setMarkers(displayOptions.marks?mark.sort((a,b)=>a.time-b.time):[]);
   for(const [price,title,when] of [[trade.stop_price,"SL",secs(trade.entry_utc)],[trade.target_price,"TP",secs(trade.entry_utc)],[trade.trailing_stop_price,"TRAIL (recorded)",secs(trade.exit_utc)],[trade.liquidation_price,"LIQ (recorded)",secs(trade.exit_utc)]])if(displayOptions.levels&&Number.isFinite(price)&&when<=cutoff)priceLines.push(candleSeries.createPriceLine({price,color:"#eab66b",lineWidth:1,lineStyle:window.LightweightCharts.LineStyle.Dashed,axisLabelVisible:true,title}))
   const first=nativeTimes[0],last=nativeTimes.at(-1),ts=chart.timeScale();
   if(previous){ts.setVisibleLogicalRange({from:(previous.from-first)/step,to:(previous.to-first)/step})}
   else{const anchor=replayMode?replayCutoff():browseAnchor??replayCutoff(),right=clamp((Math.floor((anchor-1)/step)*step-first)/step+3,3,nativeTimes.length+3);ts.setVisibleLogicalRange({from:right-80,to:right})}
   $("cursor").textContent=(replayMode?"Replay: ":"Browse: ")+new Date((replayMode?cutoff:browseAnchor??last+step)*1000).toISOString().slice(0,16).replace("T"," ")+" UTC · "+nativeRows.length+" loaded chart candles";
  }else{markers.setMarkers([]);$("cursor").textContent="";$("chartRange").textContent=""}
  chartFrameRendered=chartFrame;resetRange=false;updateRangeLabel();queueDrawings()
 }finally{chartUpdating=false}
}
function drawingPoint(e){
 if(!chart||!candleSeries)return null;
 const rect=$("chart-drawings").getBoundingClientRect(),x=e.clientX-rect.left,y=e.clientY-rect.top,t=chart.timeScale().coordinateToTime(x),price=candleSeries.coordinateToPrice(y);
 if(typeof t!=="number"||!Number.isFinite(price)||!nativeRows.some(r=>r[0]===t)||y<0||y>chart.panes()[0].getHeight()||replayMode&&t>=chartCutoff())return null;
 return {time:t,price}
}
function svgNode(tag,attrs,text){const node=document.createElementNS("http://www.w3.org/2000/svg",tag);for(const [k,v] of Object.entries(attrs))node.setAttribute(k,String(v));if(text!==undefined)node.textContent=text;return node}
function syncDrawingButtons(){$("tool-undo").disabled=!undoStack.length;$("tool-redo").disabled=!redoStack.length}
function rememberDrawing(){undoStack.push(drawings.slice());if(undoStack.length>50)undoStack.shift();redoStack=[];syncDrawingButtons()}
function addDrawing(d){rememberDrawing();drawings.push(d);if(drawings.length>50)drawings.shift();queueDrawings()}
function paintDrawings(){
 const svg=$("chart-drawings");svg.replaceChildren();if(!chart||!candleSeries)return;
 const w=chart.timeScale().width(),h=chart.panes()[0].getHeight();svg.style.width=w+"px";svg.style.height=h+"px";svg.setAttribute("viewBox","0 0 "+w+" "+h);
 const all=[...drawings,...(draft?.b?[draft]:[])];
 for(const d of all){
  if(replayMode&&(d.a.time>=chartCutoff()||d.b.time>=chartCutoff()))continue;
  const x1=chart.timeScale().timeToCoordinate(d.a.time),x2=d.kind==="horizontal"?w:chart.timeScale().timeToCoordinate(d.b.time),y1=candleSeries.priceToCoordinate(d.a.price),y2=d.kind==="horizontal"?y1:candleSeries.priceToCoordinate(d.b.price);
  if([x1,x2,y1,y2].some(v=>v===null||!Number.isFinite(v)))continue;
  const color=d.kind==="measure"?"#78bcff":"#eab66b";
  if(d.kind==="measure"||d.kind==="rectangle")svg.append(svgNode("rect",{x:Math.min(x1,x2),y:Math.min(y1,y2),width:Math.abs(x2-x1),height:Math.abs(y2-y1),fill:color,"fill-opacity":.13,stroke:color,"stroke-dasharray":d.kind==="measure"?"4 3":""}));
  if(d.kind==="fib"){
   for(const ratio of [0,.236,.382,.5,.618,.786,1]){
    const price=d.a.price+(d.b.price-d.a.price)*ratio,yy=candleSeries.priceToCoordinate(price);
    if(yy===null)continue;
    const left=Math.min(x1,x2),right=Math.max(x1,x2);svg.append(svgNode("line",{x1:left,y1:yy,x2:right,y2:yy,stroke:ratio===.618?"#26a69a":"#8e9ab0","stroke-width":1,"stroke-dasharray":"4 2"}),svgNode("text",{x:clamp(left+4,0,Math.max(0,w-120)),y:yy-4,fill:"#cbd5e1","font-size":11},ratio+" · "+fmt(price)))
   }
  }else if(d.kind==="ray"){const end=x2>=x1?w:0,yy=x2===x1?y2:y1+(y2-y1)*(end-x1)/(x2-x1);svg.append(svgNode("line",{x1,y1,x2:x2===x1?x2:end,y2:yy,stroke:color,"stroke-width":1.5}))}
  else if(d.kind!=="rectangle")svg.append(svgNode("line",{x1:d.kind==="horizontal"?0:x1,y1,x2,y2,stroke:color,"stroke-width":1.5}));
  if(d.kind!=="horizontal")for(const [cx,cy] of [[x1,y1],[x2,y2]])svg.append(svgNode("circle",{cx,cy,r:3,fill:color}));
  if(d.kind==="fib")continue;
  const label=d.kind==="measure"?measurementText(d.a,d.b):d.kind==="horizontal"?fmt(d.a.price):fmt(d.b.price-d.a.price)+" pts",width=Math.min(w,Math.max(90,label.length*6.5+12)),x=clamp(Math.min(x1,x2),0,Math.max(0,w-width)),y=clamp(Math.min(y1,y2)-25,0,Math.max(0,h-22));
  svg.append(svgNode("rect",{x,y,width,height:22,rx:4,fill:"#152335",stroke:color}),svgNode("text",{x:x+6,y:y+15,fill:"#e3edf5","font-size":11},label))
 }
}
function bindChart(){
 const host=$("chart"),svg=$("chart-drawings");
 for(const mode of drawingModes)$("tool-"+mode).onclick=()=>setChartMode(mode);
 $("tool-clear").onclick=()=>{if(drawings.length)rememberDrawing();drawings=[];draft=null;queueDrawings()};
 $("tool-undo").onclick=()=>{if(undoStack.length){redoStack.push(drawings.slice());drawings=undoStack.pop();draft=null;syncDrawingButtons();queueDrawings()}};
 $("tool-redo").onclick=()=>{if(redoStack.length){undoStack.push(drawings.slice());drawings=redoStack.pop();draft=null;syncDrawingButtons();queueDrawings()}};
 syncDrawingButtons();
 for(const b of $("frameButtons").querySelectorAll("button"))b.onclick=()=>{$("timeframe").value=b.dataset.frame;$("timeframe").dispatchEvent(new Event("change"))};
 $("chart-settings").addEventListener("toggle",()=>{if($("chart-settings").open)renderIndicatorSettings(trade?recordedIndicators(run,trade):[])});
 for(const k of Object.keys(displayOptions)){const el=$("chart-setting-"+k);el.checked=displayOptions[k];el.onchange=()=>{displayOptions[k]=el.checked;saveChartPreferences();draw()}}
 $("chart-setting-reset").onclick=()=>{indicatorPreferences.clear();displayOptions={grid:true,marks:true,levels:true};for(const k of Object.keys(displayOptions))$("chart-setting-"+k).checked=true;saveChartPreferences();draw()};
 const shell=$("chartWorkspace"),expand=$("chart-expand");
 expand.onclick=async()=>{if(document.fullscreenElement===shell){await document.exitFullscreen();return}if(shell.classList.contains("chart-expanded")){shell.classList.remove("chart-expanded");expand.setAttribute("aria-pressed","false");expand.textContent="⛶";return}if(shell.requestFullscreen){try{await shell.requestFullscreen();return}catch{}}shell.classList.add("chart-expanded");expand.setAttribute("aria-pressed","true");expand.textContent="×"};
 document.addEventListener("fullscreenchange",()=>{const on=document.fullscreenElement===shell;expand.setAttribute("aria-pressed",String(on));expand.textContent=on?"×":"⛶";queueDrawings()});
 document.addEventListener("keydown",e=>{if(e.key==="Escape"&&shell.classList.contains("chart-expanded")){shell.classList.remove("chart-expanded");expand.setAttribute("aria-pressed","false");expand.textContent="⛶"}});
 $("chart-reset").onclick=()=>{resetViewport(false);queueHistory()};
 $("chart-mode").onchange=()=>setReplayMode($("chart-mode").value==="replay",true);
 $("replay-start").onclick=()=>setReplayMode(true,true);$("replay-end").onclick=()=>setReplayMode(false);
 $("replay-seek").oninput=()=>{if(replayMode){stop();limit=Number($("replay-seek").value);resetRange=true;syncReplayControls();draw()}};
 $("chart-older").onclick=()=>panBy(-20*chartFrame*60);$("chart-newer").onclick=()=>panBy(20*chartFrame*60);
 $("chart-zoom-in").onclick=()=>zoomBy(.75);$("chart-zoom-out").onclick=()=>zoomBy(1.35);
 svg.addEventListener("pointerdown",e=>{
  if(e.button>0||chartMode==="pan")return;const p=drawingPoint(e);if(!p)return;e.preventDefault();svg.setPointerCapture(e.pointerId);
  if(chartMode==="horizontal"){addDrawing({kind:"horizontal",a:p,b:p});draft=null}
  else if(draft){draft.b=p;addDrawing(draft);draft=null}
  else{draft={kind:chartMode,a:p,b:p};drawingPointer={id:e.pointerId,x:e.clientX,y:e.clientY}}
  queueDrawings()
 });
 svg.addEventListener("pointermove",e=>{if(draft){const p=drawingPoint(e);if(p){draft.b=p;queueDrawings()}}});
 svg.addEventListener("pointerup",e=>{if(draft&&drawingPointer?.id===e.pointerId&&Math.hypot(e.clientX-drawingPointer.x,e.clientY-drawingPointer.y)>4){const p=drawingPoint(e);if(p){draft.b=p;addDrawing(draft);draft=null}}drawingPointer=null;queueDrawings()});
 svg.addEventListener("pointercancel",()=>{draft=null;drawingPointer=null;queueDrawings()});
 host.addEventListener("keydown",e=>{if(e.key==="ArrowLeft"){e.preventDefault();panBy(-5*chartFrame*60)}else if(e.key==="ArrowRight"){e.preventDefault();panBy(5*chartFrame*60)}else if(e.key==="+"||e.key==="="){e.preventDefault();zoomBy(.8)}else if(e.key==="-"){e.preventDefault();zoomBy(1.25)}else if(e.key==="Home"){e.preventDefault();resetViewport(false)}else if(e.key==="Escape")setChartMode("pan")});
 // Price-axis zoom and pane resizing also move the drawing coordinates.
 new ResizeObserver(queueDrawings).observe($("chart-native"));
 host.addEventListener("pointermove",queueDrawings);host.addEventListener("wheel",queueDrawings,{passive:true})
}
bindChart();
$("run").onchange=()=>renderRun();$("month").onchange=()=>loadMonth().catch(fail);$("filter").onchange=()=>{page=0;renderLedger()};$("tradePrev").onclick=()=>{page--;renderLedger()};$("tradeNext").onclick=()=>{page++;renderLedger()};$("prev").onclick=()=>{stop();stepReplay(-1)};$("next").onclick=()=>{stop();stepReplay(1)};$("full").onclick=()=>setReplayMode(false);$("play").onclick=()=>{if(timer){stop();return}if(!bars.length)return;if(!replayMode||limit>=bars.length)setReplayMode(true,true);timer=setInterval(()=>{stepReplay(1);if(limit>=bars.length)stop()},120);syncReplayControls()};window.addEventListener("resize",()=>{queueDrawings();drawCurves()});$("overlay").onchange=draw;$("timeframe").onchange=()=>{stop();chartFrame=Number($("timeframe").value);resetRange=true;draw();queueHistory()};$("windowPrev").onclick=()=>{if(trade){windowDay-=DAY;loadWindow().catch(fail)}};$("windowNext").onclick=()=>{if(trade){windowDay+=DAY;loadWindow().catch(fail)}};
function runLabel(r){return (r.automatic_version?(r.latest_version?"[Latest] ":"[Previous] "):"")+r.strategy+(r.target==null?"":" / TP "+r.target+" / SL "+r.stop)+(r.detail_available===false?" [summary only]":"")+(r.research_reference?" [research diagnostic · USD]":"")+(r.automatic_version?" · run "+r.source_run_id+"."+r.source_attempt:"")}
function rankedRuns(rows){
 return [...rows].sort((a,b)=>Number(!!b.automatic_version)-Number(!!a.automatic_version)||String(b.completed_at||"").localeCompare(String(a.completed_at||""))||Number(!!b.latest_version)-Number(!!a.latest_version)||((b.source_run_id||0)-(a.source_run_id||0)))
}
function chooseSymbol(preferred=null,preferredMonth=null,preferredTrade=null){
 const same=rankedRuns(index.runs.filter(r=>r.symbol===$("symbol").value));options($("run"),same.map(r=>[r.id,runLabel(r)]));
 if(same.some(r=>r.id===preferred))$("run").value=preferred;
 options($("compare"),[["","None"],...same.map(r=>[r.id,runLabel(r)])]);renderRun(preferredMonth,preferredTrade)
}
function renderLatest(){
 const list=rankedRuns(index.runs.filter(r=>r.automatic_version));
 const newest=list[0]?.source_run_id;
 $("latestSummary").textContent=list.length?list.length+" published versions · newest run "+newest+" · includes losing and zero-trade results":"No standardized backtest artifacts published yet.";
 const rows=$("latestRuns");rows.replaceChildren();
 for(const r of list){
  const tr=document.createElement("tr");tr.dataset.runId=r.id;
  const fields=[r.strategy,r.symbol,r.source_run_id+"."+r.source_attempt,String(r.completed_at||"").replace("T"," ").replace("Z"," UTC"),r.trades,fmt(r.net)+" "+r.unit,r.latest_version?"Latest variant":"Previous version"];
  for(const [i,v] of fields.entries()){const td=document.createElement("td");td.textContent=v;if(i===5)td.className=sign(r.net);tr.append(td)}
  const cell=document.createElement("td"),button=document.createElement("button");button.textContent="Open result";button.onclick=()=>{ $("symbol").value=r.symbol;$("filter").value="";chooseSymbol(r.id);$("run").scrollIntoView({block:"center",behavior:"smooth"}) };cell.append(button);tr.append(cell);rows.append(tr)
 }
}

$("showBranches").onclick=async()=>{try{const rows=await get("branches.json");$("branchCoverage").replaceChildren(...rows.map(r=>{const a=document.createElement("a");a.href="https://github.com/rajkumar0rk/BTC-Analysis/tree/"+r.sha;a.textContent=r.name;const p=document.createElement("p");p.append(a);return p}))}catch(e){fail(e)}};
async function renderComparison(){const token=++curveToken,other=index.runs.find(r=>r.id===$("compare").value&&r.symbol===run.symbol&&r.unit===run.unit),selected=[run,...(other&&other.id!==run.id?[other]:[])];$("comparison").innerHTML='<div class="comparison-row"><b>Configuration</b><b>Net '+esc(run.unit||"price points")+'</b><b>Win rate</b><b>Realized drawdown</b></div>'+selected.map(r=>'<div class="comparison-row"><span>'+esc(runLabel(r))+'</span><span>'+fmt(r.net)+'</span><span>'+fmt(r.win_rate)+'%</span><span>'+fmt(r.drawdown)+'</span></div>').join("");const years={};for(const m of run.months){const y=m.month.slice(0,4);years[y]=(years[y]||0)+m.net}$("yearly").replaceChildren(...Object.entries(years).map(([y,n])=>{const el=document.createElement("div");el.className="metric";el.innerHTML='<small>'+esc(y)+' · entry-month total</small><strong class="'+sign(n)+'">'+fmt(n)+'</strong>';return el}));const data=await Promise.all(selected.map(r=>get("runs/"+r.id+"/curve.json")));if(token!==curveToken)return;curves=data;drawCurves()}
function drawCurves(){const c=$("equity"),w=c.clientWidth,h=c.clientHeight,dpr=window.devicePixelRatio||1;c.width=w*dpr;c.height=h*dpr;const x=c.getContext("2d");x.scale(dpr,dpr);if(!curves.length)return;const all=curves.flat(),ts=all.map(v=>secs(v[0])),tmin=Math.min(...ts),tmax=Math.max(...ts),lo=Math.min(0,...all.map(v=>Math.min(v[1],-v[2]))),hi=Math.max(1,...all.map(v=>v[1])),px=t=>12+(t-tmin)/Math.max(1,tmax-tmin)*(w-80),py=v=>12+(hi-v)/Math.max(1,hi-lo)*(h-40);x.font="11px system-ui";for(let i=0;i<5;i++){const v=lo+(hi-lo)*i/4;x.strokeStyle="#26364a";x.beginPath();x.moveTo(12,py(v));x.lineTo(w-65,py(v));x.stroke();x.fillStyle="#9aafc2";x.fillText(fmt(v),w-62,py(v)+4)}curves.forEach((series,i)=>{for(const [col,field,sgn] of [[i?"#79baff":"#36d8aa",1,1],[i?"#d9a4ff":"#fb7785",2,-1]]){x.strokeStyle=col;x.beginPath();series.forEach((v,j)=>j?x.lineTo(px(secs(v[0])),py(sgn*v[field])):x.moveTo(px(secs(v[0])),py(sgn*v[field])));x.stroke()}});x.fillStyle="#9aafc2";x.fillText("Green/blue: realized P&L · red/purple: negative drawdown",12,h-8)}
$("symbol").onchange=()=>chooseSymbol();$("compare").onchange=()=>renderComparison().catch(fail);$("showCoverage").onclick=async()=>{try{const rows=await get("coverage.json");$("archiveCoverage").innerHTML='<table><thead><tr><th>Source ledger</th><th>Coverage</th></tr></thead><tbody>'+rows.map(r=>'<tr><td><a href="'+esc(r.url||("https://github.com/rajkumar0rk/BTC-Analysis/blob/main/"+encodeURI(r.path)))+'">'+esc(r.path)+'</a></td><td>'+esc(r.status)+(r.configurations?" · "+r.configurations:"")+'</td></tr>').join("")+'</tbody></table>'}catch(e){fail(e)}};
function renderSupertrend(rows){
 const host=$("supertrendStrategies");host.replaceChildren();$("supertrendMonthly").replaceChildren();
 const table=document.createElement("table");table.innerHTML="<thead><tr><th>Strategy / source</th><th>Period</th><th>Net (source unit)</th><th>Drawdown</th><th>Positive months</th><th>Trades</th><th>Status</th><th>Evidence</th></tr></thead>";
 const body=document.createElement("tbody");
 for(const r of rows){
  const tr=document.createElement("tr"),net=r.net==null?"Not reported":fmt(r.net)+(r.unit==="account return %"?"%":" USD"),dd=r.drawdown==null?"Not reported":fmt(r.drawdown)+"% ("+r.drawdown_label+")";
  tr.innerHTML='<td><a href="'+esc(r.source)+'" target="_blank" rel="noopener">'+esc(r.name)+'</a></td><td>'+esc(r.window)+'</td><td class="'+sign(r.net)+'">'+esc(net)+'</td><td>'+esc(dd)+'</td><td>'+r.positive_months+'/'+r.months+'</td><td>'+esc(r.trades??"Not reported")+'</td><td>'+esc(r.status)+'</td>';
  const actions=document.createElement("td"),b=document.createElement("button");b.textContent="Details";b.onclick=()=>{
   $("supertrendMonthly").innerHTML="<h3>"+esc(r.name)+"</h3><p>"+esc(r.notes)+"</p>"+(r.monthly.length?'<table><thead><tr><th>Month (source)</th><th>'+esc(r.unit)+'</th></tr></thead><tbody>'+r.monthly.map(m=>'<tr><td>'+esc(m.month)+'</td><td class="'+sign(m.value)+'">'+fmt(m.value)+'</td></tr>').join("")+'</tbody></table>':"<p>Exact monthly series not recorded for this selected configuration.</p>");
  };actions.append(b);
  if(r.replay_id){const replay=document.createElement("button");replay.textContent="Replay";replay.onclick=()=>{$("symbol").value="BTCUSD";chooseSymbol(r.replay_id);$("run").scrollIntoView({block:"center"})};actions.append(replay)}
  tr.append(actions);body.append(tr)
 }
 table.append(body);host.append(table)
}
async function refreshData(force=false){
 if(refreshBusy)return;refreshBusy=true;
 try{
  let manifest,base;
  if(LOCAL){manifest={data_commit:"local",published_at:"local"};base="./data/"}
  else{
   manifest=await json(RAW+"dashboard-data/latest.json?minute="+Math.floor(Date.now()/60000),{cache:"no-store"});
   if(manifest.schema!==1||manifest.data_schema!==2||! /^[a-f0-9]{40}$/.test(manifest.data_commit))throw Error("Invalid or incompatible published data pointer");
   base=RAW+manifest.data_commit+"/data/";
  }
  if(activeSnapshot===manifest.data_commit){$("dataStatus").textContent="Up to date · checked "+new Date().toLocaleTimeString();return}
  const next=await json(base+"index.json");
  const frozen=await json(base+"frozen.json");
  const supertrend=await json(base+"supertrend.json");
  if(next.schema!==2||!Array.isArray(next.runs)||!next.runs.length)throw Error("Invalid result index");
  const symbol=$("symbol").value,preferred=$("run").value,preferredMonth=$("month").value,preferredTrade=trade?.id;
  stop();++monthToken;++tradeToken;++curveToken;cache.clear();dataBase=base;activeSnapshot=manifest.data_commit;index=next;ledger=[];trade=null;bars=[];curves=[];
  $("coverage").textContent=index.selection_policy.retained+" ranked replays · "+index.supertrend_replay_count+" Supertrend evidence replays · "+(index.automatic_run_count||0)+" versioned backtests · "+frozen.length+" frozen summaries";
  renderLatest();renderSupertrend(supertrend);
  $("frozenStrategies").innerHTML="<table><thead><tr><th>Strategy</th><th>Profitable months</th><th>Trades</th><th>Recorded net USD (0.001 BTC)</th><th>Research status</th></tr></thead><tbody>"+frozen.map(r=>'<tr><td><a href="https://github.com/rajkumar0rk/BTC-Analysis/blob/'+encodeURIComponent(r.sha)+'/'+encodeURI(r.path)+'">'+esc(r.name)+'</a></td><td>'+r.positive_months+'/'+r.months+'</td><td>'+r.trades+'</td><td>'+fmt(r.net_usd_min)+' – '+fmt(r.net_usd_max)+'</td><td>'+esc(r.status)+'</td></tr>').join("")+"</tbody></table>";
  $("provenance").textContent="Source commit: "+index.commit+" | Data snapshot: "+activeSnapshot+" | ETH workflow run: "+(index.eth_workflow_run||"not recorded")+" | Archived runs preserve their own cost assumptions. Indicator declarations and histories are read only from recorded run data. Legacy signal fields are separately labeled. Research only.";
  $("dataStatus").textContent="Published "+manifest.published_at+" · auto-refresh every minute";
  $("notice").textContent="";
  const symbols=[...new Set(index.runs.map(r=>r.symbol))];options($("symbol"),symbols.map(s=>[s,s]));if(symbols.includes(symbol))$("symbol").value=symbol;chooseSymbol(preferred,preferredMonth,preferredTrade);
 }catch(e){$("dataStatus").textContent=activeSnapshot?"Refresh failed; showing last verified snapshot":"Published data unavailable";if(!activeSnapshot)fail(e);else console.warn(e)}
 finally{refreshBusy=false}
}
$("refreshData").onclick=()=>refreshData(true);
refreshData();
if(!LOCAL){setInterval(()=>{if(!document.hidden)refreshData()},60000);document.addEventListener("visibilitychange",()=>{if(!document.hidden)refreshData()})}
