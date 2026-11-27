"use strict";
const $=id=>document.getElementById(id),fmt=n=>n==null?"Not recorded":Number(n).toLocaleString("en-US",{maximumFractionDigits:4}), esc=s=>String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c])),sign=n=>n>0?"pos":n<0?"neg":"";
let index,run,ledger=[],trade,bars=[],limit=0,timer,monthToken=0,tradeToken=0,windowDay=0,sourceBars=[],dayIndicatorSeries={},chartFrame=1,frameRun=null,curveToken=0,curves=[],page=0;const PAGE=100;
const cache=new Map();
// Free browsing and causal execution replay have independent clocks.
const DAY=86400,MAX_HISTORY_DAYS=31,MIN_VISIBLE=6,MAX_VISIBLE=600;
let viewEnd=null,viewCount=80,historyDays=new Map(),historyBusy=false,historyStatus="",historySerial=0;
let replayMode=false,browseAnchor=null,chartGeometry=null,chartHover=null,chartMode="pan",drawings=[],draft=null,drag=null,pointers=new Map(),pinch=null,drawQueued=false;
let baseImage=null,baseValid=false,hoverQueued=false,priceLock=null,indicatorCache=null;
function clamp(v,lo,hi){return Math.max(lo,Math.min(hi,v))}
function replayCutoff(){return bars.length&&limit?bars[Math.min(limit,bars.length)-1][0]+60:null}
function dayKeys(){return (index?.candle_days?.[run?.symbol]||[]).map(d=>Date.parse(d+"T00:00:00Z")/1000)}
function archiveBounds(){const keys=dayKeys();return keys.length?{min:keys[0],max:keys.at(-1)+DAY}:{min:windowDay,max:windowDay+DAY}}
function chartCutoff(){return replayMode?replayCutoff():archiveBounds().max}
function currentRight(){const cutoff=chartCutoff();return Math.min(cutoff,viewEnd??(replayMode?cutoff:browseAnchor??replayCutoff()??cutoff))}
function resetViewport(clear=true){viewEnd=null;viewCount=80;chartHover=null;draft=null;drag=null;pinch=null;pointers.clear();priceLock=null;baseValid=false;if(clear)drawings=[]}
function scheduleDraw(){baseValid=false;if(!drawQueued){drawQueued=true;requestAnimationFrame(()=>{drawQueued=false;draw()})}}
function scheduleHover(){if(!hoverQueued){hoverQueued=true;requestAnimationFrame(()=>{hoverQueued=false;if(!baseValid||!chartGeometry||!baseImage)return;const c=$("chart"),x=c.getContext("2d");x.save();x.setTransform(1,0,0,1,0,0);x.clearRect(0,0,c.width,c.height);x.drawImage(baseImage,0,0);x.restore();$("chartInspect").textContent="";paintInteraction(x,chartGeometry)})}}
function viewportBounds(cutoff,frame=chartFrame,count=viewCount,end=currentRight()){
 const seconds=frame*60,right=Math.min(cutoff,end??cutoff),left=right-count*seconds;
 return {start:Math.floor(left/seconds)*seconds,end:Math.ceil(right/seconds)*seconds,left,right,seconds}
}
function mergeHistory(){
 const sorted=[...historyDays.entries()].sort((a,b)=>a[0]-b[0]);
 sourceBars=sorted.flatMap(([,d])=>d.candles);
 const merged={};
 for(const [,d] of sorted)for(const [id,points] of Object.entries(d.series||{})){
  const m=merged[id]??(merged[id]=new Map());
  for(const p of points)if(Array.isArray(p)&&p.length===2)m.set(p[0],p[1])
 }
 dayIndicatorSeries=Object.fromEntries(Object.entries(merged).map(([id,m])=>[id,[...m].sort((a,b)=>a[0]-b[0])]));
 indicatorCache=null
}
async function fetchHistoryDay(day,r){
 const key=new Date(day*1000).toISOString().slice(0,10);
 const [candles,series]=await Promise.all([get("candles/"+r.symbol+"/"+key+".json"),(r.indicator_days||[]).includes(key)?get("runs/"+r.id+"/indicators/"+key+".json"):Promise.resolve({})]);
 return {candles,series}
}
async function extendHistory(){
 if(historyBusy||!trade||!historyDays.size)return;
 const cutoff=chartCutoff();if(cutoff===null)return;
 const bounds=viewportBounds(cutoff),keys=dayKeys(),loaded=[...historyDays.keys()];
 const missing=keys.filter(d=>d<Math.min(bounds.end,cutoff)&&d+DAY>bounds.start&&!historyDays.has(d));
 if(!missing.length)return;
 const center=(bounds.left+bounds.right)/2,day=missing.sort((a,b)=>Math.abs(a+DAY/2-center)-Math.abs(b+DAY/2-center))[0];
 const token=tradeToken,serial=historySerial,r=run;historyBusy=true;historyStatus="Loading archived candles…";scheduleDraw();let ok=false;
 try{
  const data=await fetchHistoryDay(day,r);
  if(token!==tradeToken||serial!==historySerial)return;
  historyDays.set(day,data);
  if(historyDays.size>MAX_HISTORY_DAYS){const far=[...historyDays.keys()].filter(d=>d!==day&&d!==windowDay).sort((a,b)=>Math.abs(b+DAY/2-center)-Math.abs(a+DAY/2-center))[0];if(far!==undefined)historyDays.delete(far)}
  mergeHistory();historyStatus="";ok=true;
 }catch(e){if(token===tradeToken&&serial===historySerial)historyStatus="History unavailable: "+e.message}
 finally{if(token===tradeToken&&serial===historySerial){historyBusy=false;scheduleDraw();if(ok){const b=viewportBounds(chartCutoff());const needed=dayKeys().filter(d=>d<b.right&&d+DAY>b.start);if(needed.length<=MAX_HISTORY_DAYS)void extendHistory()}}}
}
function panBy(seconds){
 const cutoff=chartCutoff();if(cutoff===null||!historyDays.size)return;stop();chartHover=null;
 const current=currentRight(),minEnd=Math.min(cutoff,archiveBounds().min+MIN_VISIBLE*chartFrame*60);
 const next=clamp(current+seconds,minEnd,cutoff);
 viewEnd=next;scheduleDraw();void extendHistory()
}
function zoomBy(factor,anchor=.5){
 const cutoff=chartCutoff();if(cutoff===null||!historyDays.size)return;stop();
 const old=viewCount,next=clamp(old*factor,MIN_VISIBLE,MAX_VISIBLE);
 if(Math.abs(next-old)<.01)return;
 const right=currentRight();viewCount=next;
 viewEnd=clamp(right+(next-old)*chartFrame*60*(1-clamp(anchor,0,1)),Math.min(cutoff,archiveBounds().min+MIN_VISIBLE*chartFrame*60),cutoff);chartHover=null;scheduleDraw();void extendHistory()
}
function syncReplayControls(){
 $("chart-mode").value=replayMode?"replay":"browse";
 $("play").textContent=timer?"Pause":"Play replay";
 $("prev").disabled=!replayMode||limit<=1;
 $("next").disabled=!replayMode||limit>=bars.length;
 $("replay-start").disabled=!bars.length;
 $("replay-end").disabled=!bars.length;
 $("replay-seek").disabled=!replayMode||!bars.length;
 $("replay-seek").max=Math.max(1,bars.length);$("replay-seek").value=Math.max(1,limit);
}
function setReplayMode(on,reset=false){
 stop();replayMode=on;if(on&&reset)limit=1;viewEnd=null;priceLock=null;chartHover=null;syncReplayControls();scheduleDraw();void extendHistory()
}
function stepReplay(n){
 if(!bars.length)return;if(!replayMode)setReplayMode(true,true);
 limit=clamp(limit+n,1,bars.length);viewEnd=null;priceLock=null;syncReplayControls();scheduleDraw();void extendHistory()
}
function setChartMode(mode){chartMode=mode;draft=null;drag=null;for(const id of ["pan","measure","trend","horizontal"]){$("tool-"+id).setAttribute("aria-pressed",String(id===mode))}$("chart").dataset.mode=mode;scheduleDraw()}
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
function renderRun(){run=index.runs.find(r=>r.id===$("run").value);if(!run)return;const unit=run.unit||"price points";$("netUnit").textContent="Net "+unit;$("monthUnit").textContent="Entry-month realized "+unit+"; not account MTM";options($("compare"),[["","None"],...index.runs.filter(r=>r.symbol===run.symbol&&r.unit===run.unit&&r.id!==run.id).map(r=>[r.id,runLabel(r)])]);renderComparison().catch(fail);$("metrics").innerHTML=[["Trades",run.trades],["Net "+unit,run.net],["Win rate",run.win_rate+"%"],["Profit factor",run.profit_factor??"N/A"],["Realized DD "+unit,run.drawdown]].map(([k,v],i)=>'<div class="metric"><small>'+k+'</small><strong class="'+(i===1?sign(v):"")+'">'+esc(typeof v==="number"?fmt(v):v)+'</strong></div>').join("");const max=Math.max(1,...run.months.map(m=>Math.abs(m.net)));$("months").replaceChildren(...run.months.map(m=>{const b=document.createElement("button");b.className="month "+sign(m.net);b.style.setProperty("--h",Math.max(2,Math.abs(m.net)/max*38)+"px");b.innerHTML='<span>'+esc(m.month.slice(2))+'</span><i></i><small>'+fmt(m.net)+'</small>';b.title=m.month+" · "+m.trades+" trades";b.onclick=()=>{$("month").value=m.month;loadMonth().catch(fail)};return b}));options($("month"),run.months.map(m=>[m.month,m.month+" ("+m.trades+")"]));$("month").value=run.months.at(-1)?.month||"";loadMonth().catch(fail)}
async function loadMonth(){const seq=++monthToken;++tradeToken;stop();trade=null;bars=[];draw();$("details").textContent="Loading trades…";$("ledger").replaceChildren();$("notice").textContent="";ledger=[];page=0;if(run.detail_available===false){$("details").textContent="Summary only: full trade detail exceeds publication budget. Original ledger: "+run.source;$("count").textContent="Summary only";return}const data=await get("runs/"+run.id+"/"+$("month").value+".json");if(seq!==monthToken)return;ledger=data;renderLedger()}
function renderLedger(){const filter=$("filter").value,list=ledger.filter(t=>!filter||(filter==="win"?t.net_points>0:t.net_points<=0));page=Math.max(0,Math.min(page,Math.ceil(list.length/PAGE)-1));const shown=list.slice(page*PAGE,(page+1)*PAGE);$("count").textContent=list.length+" trades · page "+(page+1)+" / "+Math.max(1,Math.ceil(list.length/PAGE));$("ledger").replaceChildren(...shown.map(t=>{const tr=document.createElement("tr");tr.tabIndex=0;tr.innerHTML='<td>'+esc(t.entry_utc.slice(0,16))+'</td><td>'+(t.side===1?"LONG":"SHORT")+'</td><td>'+esc(t.result)+'</td><td class="'+sign(t.net_points)+'">'+fmt(t.net_points)+'</td>';tr.onclick=()=>selectTrade(t,tr).catch(fail);tr.onkeydown=e=>{if(e.key==="Enter"||e.key===" "){e.preventDefault();tr.click()}};return tr}));if(shown.length)$("ledger").firstElementChild.click();else{++tradeToken;stop();trade=null;bars=[];draw();$("details").textContent="No matching trades."}}
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
function indicatorLabel(d){const params=Object.entries(d.parameters||{}).map(([k,v])=>k+"="+String(v)).join(", ");return d.name+" ("+d.timeframe_minutes+"m"+(params?"; "+params:"")+")"}
async function loadWindow(){
 const token=++tradeToken,t=trade,r=run;stop();historySerial++;historyBusy=false;historyStatus="";historyDays=new Map();bars=[];sourceBars=[];dayIndicatorSeries={};resetViewport(false);draw();if(!t)return;
 const available=new Set(index.candle_days?.[r.symbol]||[]),day=new Date(windowDay*1000).toISOString().slice(0,10);if(!available.has(day)){if(token===tradeToken)$("cursor").textContent="No source candles for "+day;return}
 const data=await fetchHistoryDay(windowDay,r);if(token!==tradeToken)return;historyDays.set(windowDay,data);mergeHistory();
 const anchor=Math.min(secs(t.entry_utc),secs(t.trigger_utc)||secs(t.entry_utc)),start=Math.max(windowDay,Math.floor((anchor-1800)/14400)*14400),end=Math.min(windowDay+86399,secs(t.exit_utc)+1800);
 bars=data.candles.filter(c=>c[0]>=start&&c[0]<=end);if(!bars.length)bars=data.candles;limit=bars.length;
 browseAnchor=replayCutoff();syncReplayControls();draw()
}
function draw(){
 const c=$("chart"),w=c.clientWidth,dpr=Math.min(2,window.devicePixelRatio||1);
 const declared=trade?(indicatorCache?.trade===trade?indicatorCache.value:(indicatorCache={trade,value:recordedIndicators(run,trade)}).value):[],legacy=trade&&!Array.isArray(run?.indicator_definitions)?legacySignalValues(trade):[],show=$("overlay").checked;
 const panelDefs=show?declared.filter(d=>d.panel==="panel"&&d.points.length):[];
 const h=400+panelDefs.length*100;if(c.style.height!==h+"px")c.style.height=h+"px";const pw=Math.round(w*dpr),ph=Math.round(h*dpr);if(c.width!==pw)c.width=pw;if(c.height!==ph)c.height=ph;const x=c.getContext("2d");x.setTransform(dpr,0,0,dpr,0,0);x.clearRect(0,0,w,h);baseValid=false;
 $("chartFrame").textContent=chartFrame+"m chart · recorded 1m execution · UTC";
 $("indicatorInfo").textContent=trade?(declared.length?(run.indicator_provenance?.method==="pinned_input_replay_snapshot_verified"?"Strategy indicators · reproduced from pinned original inputs and verified against recorded signal values.":"Declared strategy indicators · recorded data only; missing series are not reconstructed."):Array.isArray(run?.indicator_definitions)?"No indicators declared for this strategy.":legacy.length?"Legacy archive: recorded signal fields only; indicator declarations and time series unavailable.":"Legacy archive: no indicator declarations or recorded indicator fields."):"";
 const host=$("indicatorValues");host.replaceChildren();
 chartGeometry=null;
 $("chartHistory").textContent=historyStatus;
 $("chartInspect").textContent="";
 if(!bars.length||!trade){$("cursor").textContent="";$("chartRange").textContent="";syncReplayControls();return}
 const cutoff=chartCutoff();if(cutoff===null)return;
 const bounds=viewportBounds(cutoff);
 // Include complete visible buckets in browse mode; in replay mode strictly
 // truncate raw input before the execution cursor. Never truncate by viewport.
 const dataEnd=replayMode?Math.min(bounds.end,cutoff):bounds.end;
 const visible=sourceBars.filter(row=>row[0]>=bounds.start&&row[0]<dataEnd),b=aggregate(visible,chartFrame),pad=12,right=76,bottom=26;
 if(!b.length){$("cursor").textContent=new Date(cutoff*1000).toISOString().slice(0,16).replace("T"," ")+" UTC";$("chartInspect").textContent="No source candles in this view. Pan right or reset.";return}
 const signal=secs(trade.trigger_utc),signalVisible=Number.isFinite(signal)&&signal<=cutoff;
 const chip=(label,color)=>{const el=document.createElement("span");el.className="indicator-chip";el.textContent=label;if(color)el.style.borderColor=color;host.append(el)};
 const plotted=show?declared.map((d,i)=>{let j=-1;return {...d,color:indicatorColors[i%indicatorColors.length],samples:b.map(row=>{while(j+1<d.points.length&&d.points[j+1][0]<=Math.min(row[8]+60,cutoff))j++;return j>=0&&Math.min(row[8]+60,cutoff)-d.points[j][0]<d.timeframe_minutes*60?d.points[j][1]:null})}}):[];
 if(show){for(const d of plotted){const v=d.samples.at(-1),snap=signalVisible?d.snapshot:null;chip(indicatorLabel(d)+(Number.isFinite(v)?" · "+fmt(v):Number.isFinite(snap)?" · signal "+fmt(snap):" · series unavailable"),d.color)}
  if(signalVisible)for(const [key,value] of legacy)chip(key.replaceAll("_"," ").toUpperCase()+": "+fmt(value));
  else if(legacy.length)host.textContent="Recorded signal fields become available at the signal timestamp.";
 }
 const priceBottom=400-bottom,step=Math.max(1,w-right-pad)/viewCount,at=i=>pad+((b[i][0]-bounds.left)/bounds.seconds+.5)*step;
 const atTime=t=>pad+((Math.floor(t/bounds.seconds)*bounds.seconds-bounds.left)/bounds.seconds+.5)*step;
 const markerIndex=time=>{const t=secs(time);if(!Number.isFinite(t)||t>cutoff)return -1;let i=b.findIndex(v=>t>=v[0]&&t<v[0]+chartFrame*60&&t<=v[8]+60);if(i<0&&t===cutoff&&b.at(-1)[8]+60===cutoff)i=b.length-1;return i};
 const tradeMarkers=[[trade.entry_utc,trade.entry_price,"#66b5ff","ENTRY"],[trade.exit_utc,trade.exit_price,"#c5a1ff","EXIT"]].map(m=>[...m,markerIndex(m[0])]).filter(m=>m[4]>=0&&Number.isFinite(m[1]));
 const signalIndex=markerIndex(trade.trigger_utc);
 const recordedPrice=show&&signalIndex>=0?declared.length?plotted.filter(d=>d.panel==="price"&&Number.isFinite(d.snapshot)).map(d=>[d.name,d.snapshot,d.color]):legacy.filter(([key])=>/^(ema\d+|sma\d+|supertrend|vwap|prior_high|prior_low|bollinger_(upper|middle|lower))$/i.test(key)).map(([k,v])=>[k.toUpperCase(),v,"#fff"]):[];
 const entryVisible=secs(trade.entry_utc)<=cutoff,exitVisible=secs(trade.exit_utc)<=cutoff;
 const levels=[[trade.stop_price,"SL",entryVisible],[trade.target_price,"TP",entryVisible],[trade.trailing_stop_price,"TRAIL (recorded)",exitVisible],[trade.liquidation_price,"LIQ (recorded)",exitVisible]].filter(m=>m[2]&&Number.isFinite(m[0]));
 const priceSeries=plotted.filter(d=>d.panel==="price").flatMap(d=>d.samples).filter(Number.isFinite);
 const rawLo=Math.min(...b.map(v=>v[3]),...priceSeries,...tradeMarkers.map(m=>m[1]),...recordedPrice.map(m=>m[1])),rawHi=Math.max(...b.map(v=>v[2]),...priceSeries,...tradeMarkers.map(m=>m[1]),...recordedPrice.map(m=>m[1])),padding=Math.max((rawHi-rawLo)*.07,rawHi*.0001,.000001);
 const lo=priceLock?.lo??rawLo-padding,hi=priceLock?.hi??rawHi+padding,range=Math.max(hi-lo,.000001),y=p=>pad+(hi-p)/range*(priceBottom-pad);
 chartGeometry={b,plotted,bounds,step,pad,right:w-right,priceBottom,height:h,y,at,atTime,lo,hi,priceAt:yy=>hi-(yy-pad)*range/(priceBottom-pad)};
 x.font="11px system-ui";
 for(let i=0;i<=4;i++){const v=lo+range*i/4,yy=y(v);x.strokeStyle="#26364a";x.beginPath();x.moveTo(pad,yy);x.lineTo(w-right,yy);x.stroke();x.fillStyle="#9aafc2";x.fillText(fmt(v),w-right+4,yy+4)}
 x.save();x.beginPath();x.rect(pad,pad,w-right-pad,priceBottom-pad);x.clip();
 for(const [i,[t,o,high,low,cl,vol,count]] of b.entries()){const xx=at(i);x.strokeStyle=x.fillStyle=cl>=o?"#36d8aa":"#fb7785";x.globalAlpha=count<chartFrame?.55:1;x.beginPath();x.moveTo(xx,y(high));x.lineTo(xx,y(low));x.stroke();x.fillRect(xx-Math.max(1,step*.32),Math.min(y(o),y(cl)),Math.max(1,step*.64),Math.max(1,Math.abs(y(o)-y(cl))));x.globalAlpha=1}
 function line(values,color,scale){x.strokeStyle=color;x.beginPath();let started=false;values.forEach((v,i)=>{if(!Number.isFinite(v)){started=false;return}if(started&&i>0&&b[i][0]-b[i-1][0]===bounds.seconds)x.lineTo(at(i),scale(v));else{x.moveTo(at(i),scale(v));started=true}});x.stroke()}
 for(const d of plotted.filter(d=>d.panel==="price"))line(d.samples,d.color,y);
 for(const [price,label] of levels){x.strokeStyle=x.fillStyle="#eab66b";x.setLineDash([4,4]);x.beginPath();x.moveTo(pad,y(price));x.lineTo(w-right,y(price));x.stroke();x.setLineDash([]);x.fillText(label,pad,y(price)-4)}
 for(const [time,p,color,label,i] of tradeMarkers){const xx=at(i),yy=y(p);x.fillStyle=color;x.beginPath();x.arc(xx,yy,5,0,Math.PI*2);x.fill();x.fillText(label,Math.max(pad,Math.min(xx,w-right-40)),Math.max(12,yy-9))}
 for(const [key,v,color] of recordedPrice){x.fillStyle=color;x.fillRect(at(signalIndex)-3,y(v)-3,6,6);x.fillText(key+" (recorded)",Math.min(at(signalIndex)+5,w-right-110),Math.max(12,y(v)-5))}
 x.restore();
 for(const [i,d] of plotted.filter(d=>d.panel==="panel"&&d.points.length).entries()){
  const top=400+i*100+20,bot=top+58,values=d.samples.filter(Number.isFinite),min=values.length?Math.min(...values):0,max=values.length?Math.max(...values):1,scale=v=>bot-(v-min)/Math.max(max-min,.000001)*(bot-top);
  x.strokeStyle="#26364a";x.beginPath();x.moveTo(pad,top);x.lineTo(w-right,top);x.stroke();x.fillStyle=d.color;x.fillText(indicatorLabel(d),pad,top-5);x.save();x.beginPath();x.rect(pad,top,w-right-pad,bot-top);x.clip();line(d.samples,d.color,scale);x.restore();x.fillStyle="#9aafc2";x.fillText(fmt(max),w-right+4,top+9);x.fillText(fmt(min),w-right+4,bot)
 }
 x.fillStyle="#9aafc2";for(let i=0;i<Math.min(5,b.length);i++){const k=Math.floor(i*(b.length-1)/Math.max(1,Math.min(5,b.length)-1));x.fillText(new Date(b[k][0]*1000).toISOString().slice(5,16).replace("T"," "),Math.max(pad,Math.min(at(k)-28,w-right-62)),400-7)}
 if(!baseImage)baseImage=document.createElement("canvas");
 if(baseImage.width!==c.width)baseImage.width=c.width;if(baseImage.height!==c.height)baseImage.height=c.height;
 const bx=baseImage.getContext("2d");bx.clearRect(0,0,baseImage.width,baseImage.height);bx.drawImage(c,0,0);baseValid=true;
 paintInteraction(x,chartGeometry);
 $("cursor").textContent=(replayMode?"Replay: ":"Browse: ")+new Date((replayMode?cutoff:Math.min(bounds.right,cutoff))*1000).toISOString().slice(0,16).replace("T"," ")+" UTC · "+visible.length+" visible minutes · "+b.length+" chart candles";
 $("chartRange").textContent="View: "+new Date(b[0][0]*1000).toISOString().slice(0,16).replace("T"," ")+" – "+new Date(b.at(-1)[0]*1000).toISOString().slice(0,16).replace("T"," ")+" UTC · "+historyDays.size+" loaded day"+(historyDays.size===1?"":"s");
}
function localPoint(e){const r=$("chart").getBoundingClientRect();return {x:e.clientX-r.left,y:e.clientY-r.top}}
function chartPoint(p){
 const g=chartGeometry;if(!g||p.x<g.pad||p.x>g.right||p.y<g.pad||p.y>g.priceBottom)return null;
 const time=Math.floor((g.bounds.left+(p.x-g.pad)/g.step*g.bounds.seconds)/g.bounds.seconds)*g.bounds.seconds;
 if(replayMode&&time>=chartCutoff())return null;
 const row=g.b.find(row=>row[0]===time);if(!row)return null;
 return {time,price:g.priceAt(p.y)}
}
function paintInteraction(x,g){
 const {pad,right,priceBottom,height,atTime,y,b,plotted}=g;
 x.save();x.beginPath();x.rect(pad,pad,right-pad,priceBottom-pad);x.clip();
 function paint(d){
  const x1=atTime(d.a.time),y1=y(d.a.price),x2=d.kind==="horizontal"?right:atTime(d.b.time),y2=d.kind==="horizontal"?y1:y(d.b.price);
  x.strokeStyle=d.kind==="measure"?"#78bcff":"#eab66b";x.lineWidth=1.5;x.setLineDash(d.kind==="horizontal"?[5,4]:[]);
  if(d.kind==="measure"){x.fillStyle="rgba(120,188,255,.12)";x.fillRect(Math.min(x1,x2),Math.min(y1,y2),Math.abs(x2-x1),Math.abs(y2-y1))}
  x.beginPath();x.moveTo(d.kind==="horizontal"?pad:x1,y1);x.lineTo(x2,y2);x.stroke();x.setLineDash([]);
  if(d.kind!=="horizontal"){for(const [xx,yy] of [[x1,y1],[x2,y2]]){x.fillStyle=x.strokeStyle;x.beginPath();x.arc(xx,yy,3,0,Math.PI*2);x.fill()}}
  const text=d.kind==="measure"?measurementText(d.a,d.b):d.kind==="horizontal"?fmt(d.a.price):fmt(d.b.price-d.a.price)+" pts";
  x.font="12px system-ui";const width=x.measureText(text).width+12,xx=clamp((d.kind==="horizontal"?right-width:Math.min(x1,x2)),pad,Math.max(pad,right-width)),yy=clamp(Math.min(y1,y2)-24,pad,priceBottom-20);
  x.fillStyle="#152335";x.fillRect(xx,yy,width,20);x.fillStyle="#e3edf5";x.fillText(text,xx+6,yy+14);
 }
 for(const d of drawings)paint(d);
 if(draft&&draft.b)paint(draft);
 x.restore();
 if(!chartHover)return;
 const p=chartHover;if(p.x<pad||p.x>right||p.y<pad||p.y>height)return;
 const time=Math.floor((g.bounds.left+(p.x-pad)/g.step*g.bounds.seconds)/g.bounds.seconds)*g.bounds.seconds,i=b.findIndex(row=>row[0]===time);
 if(i<0)return;
 const xx=g.at(i),row=b[i];x.save();x.strokeStyle="#9aafc2";x.lineWidth=1;x.setLineDash([3,4]);
 x.beginPath();x.moveTo(xx,pad);x.lineTo(xx,height-10);
 if(p.y<=priceBottom){x.moveTo(pad,p.y);x.lineTo(right,p.y)}x.stroke();x.setLineDash([]);
 if(p.y<=priceBottom){x.fillStyle="#26364a";x.fillRect(right,p.y-9,74,18);x.fillStyle="#e3edf5";x.fillText(fmt(g.priceAt(p.y)),right+3,p.y+4)}
 x.restore();
 const pieces=[new Date(row[0]*1000).toISOString().slice(0,16).replace("T"," ")+" UTC","O "+fmt(row[1]),"H "+fmt(row[2]),"L "+fmt(row[3]),"C "+fmt(row[4]),"Vol "+fmt(row[5])];
 for(const d of plotted)pieces.push(d.name+" "+fmt(d.samples[i]));
 $("chartInspect").textContent=pieces.join(" · ");
}
function bindChart(){
 const canvas=$("chart");
 const modes=["pan","measure","trend","horizontal"];
 for(const mode of modes)$("tool-"+mode).onclick=()=>setChartMode(mode);
 $("tool-clear").onclick=()=>{drawings=[];draft=null;scheduleDraw()};
 $("chart-reset").onclick=()=>{resetViewport(false);historyStatus="";scheduleDraw();void extendHistory()};
 $("chart-mode").onchange=()=>setReplayMode($("chart-mode").value==="replay",true);
 $("replay-start").onclick=()=>setReplayMode(true,true);
 $("replay-end").onclick=()=>setReplayMode(false);
 $("replay-seek").oninput=()=>{if(replayMode){stop();limit=Number($("replay-seek").value);viewEnd=null;syncReplayControls();scheduleDraw();void extendHistory()}};
 $("chart-older").onclick=()=>panBy(-Math.max(1,Math.floor(viewCount/3))*chartFrame*60);
 $("chart-newer").onclick=()=>panBy(Math.max(1,Math.floor(viewCount/3))*chartFrame*60);
 $("chart-zoom-in").onclick=()=>zoomBy(.75);
 $("chart-zoom-out").onclick=()=>zoomBy(1.35);
 canvas.addEventListener("wheel",e=>{if(!chartGeometry)return;e.preventDefault();const p=localPoint(e);if(e.shiftKey||Math.abs(e.deltaX)>Math.abs(e.deltaY))panBy((e.deltaX||e.deltaY)/Math.max(1,chartGeometry.step)*chartFrame*60);else zoomBy(Math.exp(clamp(e.deltaY,-180,180)*.002),(p.x-chartGeometry.pad)/(chartGeometry.right-chartGeometry.pad))},{passive:false});
 canvas.addEventListener("pointerdown",e=>{
  if(!chartGeometry||e.button>0)return;e.preventDefault();canvas.focus({preventScroll:true});canvas.setPointerCapture(e.pointerId);
  const p=localPoint(e);pointers.set(e.pointerId,p);chartHover=p;
  if(pointers.size===2){const [a,b]=[...pointers.values()];pinch={distance:Math.max(1,Math.abs(a.x-b.x)),center:(a.x+b.x)/2};drag=null;draft=null;return}
  if(pointers.size!==1)return;
  const point=chartPoint(p);drag={id:e.pointerId,x:p.x,y:p.y,lastX:p.x,moved:false,point};
  if(chartMode==="pan"){stop();priceLock={lo:chartGeometry.lo,hi:chartGeometry.hi};return}
  if(chartMode==="horizontal"&&point){drawings.push({kind:"horizontal",a:point,b:point});if(drawings.length>50)drawings.shift();drag=null;scheduleDraw();return}
  if(point&&(chartMode==="measure"||chartMode==="trend")){if(draft){draft.b=point;drawings.push(draft);if(drawings.length>50)drawings.shift();draft=null;drag=null}else draft={kind:chartMode,a:point,b:point};scheduleDraw()}
 });
 canvas.addEventListener("pointermove",e=>{
  const p=localPoint(e);chartHover=p;
  if(pointers.has(e.pointerId))pointers.set(e.pointerId,p);
  if(pinch&&pointers.size===2){const [a,b]=[...pointers.values()],distance=Math.max(1,Math.abs(a.x-b.x)),center=(a.x+b.x)/2;if(Math.abs(distance-pinch.distance)>1){zoomBy(pinch.distance/distance,(center-(chartGeometry?.pad||12))/Math.max(1,(chartGeometry?.right||canvas.clientWidth)-12));pinch.distance=distance}if(Math.abs(center-pinch.center)>1){panBy((pinch.center-center)/Math.max(.1,chartGeometry?.step||8)*chartFrame*60);pinch.center=center}return}
  if(drag&&drag.id===e.pointerId){if(Math.abs(p.x-drag.x)>4||Math.abs(p.y-drag.y)>4)drag.moved=true;
   if(chartMode==="pan"&&chartGeometry){const dx=p.x-drag.lastX;if(dx){drag.lastX=p.x;panBy(-dx/chartGeometry.step*chartFrame*60)}}
  }
  if(draft&&chartMode!=="pan"){const point=chartPoint(p);if(point)draft.b=point}
  if(!drag||chartMode!=="pan")scheduleHover();
 });
 function finish(e,cancel=false){
  pointers.delete(e.pointerId);
  if(pinch){if(pointers.size<2)pinch=null;drag=null;priceLock=null;scheduleDraw();return}
  if(drag&&drag.id===e.pointerId){if(!cancel&&drag.moved&&draft&&(chartMode==="measure"||chartMode==="trend")){const p=chartPoint(localPoint(e));if(p){draft.b=p;drawings.push(draft);if(drawings.length>50)drawings.shift();draft=null}}drag=null}
  if(cancel)draft=null;priceLock=null;scheduleDraw()
 }
 canvas.addEventListener("pointerup",e=>finish(e));canvas.addEventListener("pointercancel",e=>finish(e,true));
 canvas.addEventListener("pointerleave",()=>{if(!pointers.size){chartHover=null;scheduleHover()}});
 canvas.addEventListener("keydown",e=>{if(e.key==="ArrowLeft"){e.preventDefault();panBy(-chartFrame*60*5)}else if(e.key==="ArrowRight"){e.preventDefault();panBy(chartFrame*60*5)}else if(e.key==="+"||e.key==="="){e.preventDefault();zoomBy(.8)}else if(e.key==="-"){e.preventDefault();zoomBy(1.25)}else if(e.key==="Home"){e.preventDefault();resetViewport(false);scheduleDraw()}else if(e.key==="Escape"){draft=null;setChartMode("pan")}});
 canvas.addEventListener("dblclick",()=>{if(chartMode==="pan"){resetViewport(false);scheduleDraw()}});
}
bindChart();
$("run").onchange=renderRun;$("month").onchange=()=>loadMonth().catch(fail);$("filter").onchange=()=>{page=0;renderLedger()};$("tradePrev").onclick=()=>{page--;renderLedger()};$("tradeNext").onclick=()=>{page++;renderLedger()};$("prev").onclick=()=>{stop();stepReplay(-1)};$("next").onclick=()=>{stop();stepReplay(1)};$("full").onclick=()=>{setReplayMode(false);viewEnd=null;scheduleDraw()};$("play").onclick=()=>{if(timer){stop();return}if(!bars.length)return;if(!replayMode||limit>=bars.length)setReplayMode(true,true);timer=setInterval(()=>{stepReplay(1);if(limit>=bars.length)stop()},120);syncReplayControls()};window.addEventListener("resize",()=>{draw();drawCurves()});$("overlay").onchange=draw;$("timeframe").onchange=()=>{stop();chartFrame=Number($("timeframe").value);chartHover=null;priceLock=null;draw();void extendHistory()};$("windowPrev").onclick=()=>{if(trade){windowDay-=86400;loadWindow().catch(fail)}};$("windowNext").onclick=()=>{if(trade){windowDay+=86400;loadWindow().catch(fail)}};
function runLabel(r){return r.strategy+(r.target==null?"":" / TP "+r.target+" / SL "+r.stop)+(r.detail_available===false?" [summary only]":"")+(r.research_reference?" [research diagnostic · USD]":"")}
function chooseSymbol(preferred=null){const same=index.runs.filter(r=>r.symbol===$("symbol").value);options($("run"),same.map(r=>[r.id,runLabel(r)]));if(same.some(r=>r.id===preferred))$("run").value=preferred;options($("compare"),[["","None"],...same.map(r=>[r.id,runLabel(r)])]);renderRun()}
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
  if(activeSnapshot===manifest.data_commit&&!force){$("dataStatus").textContent="Up to date · checked "+new Date().toLocaleTimeString();return}
  const next=await json(base+"index.json");
  const frozen=await json(base+"frozen.json");
  const supertrend=await json(base+"supertrend.json");
  if(next.schema!==2||!Array.isArray(next.runs)||!next.runs.length)throw Error("Invalid result index");
  const symbol=$("symbol").value,preferred=$("run").value;
  stop();++monthToken;++tradeToken;++curveToken;cache.clear();dataBase=base;activeSnapshot=manifest.data_commit;index=next;ledger=[];trade=null;bars=[];curves=[];
  $("coverage").textContent=index.selection_policy.retained+" ranked replays · "+index.supertrend_replay_count+" Supertrend evidence replays · "+frozen.length+" frozen summaries";
  renderSupertrend(supertrend);
  $("frozenStrategies").innerHTML="<table><thead><tr><th>Strategy</th><th>Profitable months</th><th>Trades</th><th>Recorded net USD (0.001 BTC)</th><th>Research status</th></tr></thead><tbody>"+frozen.map(r=>'<tr><td><a href="https://github.com/rajkumar0rk/BTC-Analysis/blob/'+encodeURIComponent(r.sha)+'/'+encodeURI(r.path)+'">'+esc(r.name)+'</a></td><td>'+r.positive_months+'/'+r.months+'</td><td>'+r.trades+'</td><td>'+fmt(r.net_usd_min)+' – '+fmt(r.net_usd_max)+'</td><td>'+esc(r.status)+'</td></tr>').join("")+"</tbody></table>";
  $("provenance").textContent="Source commit: "+index.commit+" | Data snapshot: "+activeSnapshot+" | ETH workflow run: "+(index.eth_workflow_run||"not recorded")+" | Archived runs preserve their own cost assumptions. Indicator declarations and histories are read only from recorded run data. Legacy signal fields are separately labeled. Research only.";
  $("dataStatus").textContent="Published "+manifest.published_at+" · auto-refresh every minute";
  $("notice").textContent="";
  const symbols=[...new Set(index.runs.map(r=>r.symbol))];options($("symbol"),symbols.map(s=>[s,s]));if(symbols.includes(symbol))$("symbol").value=symbol;chooseSymbol(preferred);
 }catch(e){$("dataStatus").textContent=activeSnapshot?"Refresh failed; showing last verified snapshot":"Published data unavailable";if(!activeSnapshot)fail(e);else console.warn(e)}
 finally{refreshBusy=false}
}
$("refreshData").onclick=()=>refreshData(true);
refreshData();
if(!LOCAL)setInterval(()=>{if(!document.hidden&&!trade)refreshData();else if(!document.hidden&&trade)$("dataStatus").textContent="Snapshot pinned while inspecting trade · Refresh results for newer data"},60000);
