"use strict";
const $=id=>document.getElementById(id),fmt=n=>n==null?"Not recorded":Number(n).toLocaleString("en-US",{maximumFractionDigits:4}), esc=s=>String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c])),sign=n=>n>0?"pos":n<0?"neg":"";
let index,run,ledger=[],trade,bars=[],limit=0,timer,monthToken=0,tradeToken=0,windowDay=0,sourceBars=[],chartFrame=1,frameRun=null,curveToken=0,curves=[],page=0;const PAGE=100;
const cache=new Map();
const RAW="https://raw.githubusercontent.com/rajkumar0rk/BTC-Analysis/";
const LOCAL=["127.0.0.1","localhost"].includes(location.hostname)&&!new URLSearchParams(location.search).has("remote");
let dataBase=LOCAL?"./data/":"",activeSnapshot=null,refreshBusy=false;
async function json(url,options){const res=await fetch(url,options);if(!res.ok)throw Error("Data request failed ("+res.status+"): "+url);return res.json()}
async function get(path){const base=dataBase,key=base+path;if(cache.has(key)){const v=cache.get(key);cache.delete(key);cache.set(key,v);return v}const v=await json(key);if(base===dataBase){cache.set(key,v);if(cache.size>24)cache.delete(cache.keys().next().value)}return v}
function fail(e){$("notice").textContent="Unable to load data: "+e.message}
function options(el,items){el.replaceChildren(...items.map(([v,t])=>new Option(t,v)))}
function stop(){clearInterval(timer);timer=null}
function renderRun(){run=index.runs.find(r=>r.id===$("run").value);if(!run)return;const unit=run.unit||"price points";$("netUnit").textContent="Net "+unit;$("monthUnit").textContent="Entry-month realized "+unit+"; not account MTM";options($("compare"),[["","None"],...index.runs.filter(r=>r.symbol===run.symbol&&r.unit===run.unit&&r.id!==run.id).map(r=>[r.id,runLabel(r)])]);renderComparison().catch(fail);$("metrics").innerHTML=[["Trades",run.trades],["Net "+unit,run.net],["Win rate",run.win_rate+"%"],["Profit factor",run.profit_factor??"N/A"],["Realized DD "+unit,run.drawdown]].map(([k,v],i)=>'<div class="metric"><small>'+k+'</small><strong class="'+(i===1?sign(v):"")+'">'+esc(typeof v==="number"?fmt(v):v)+'</strong></div>').join("");const max=Math.max(1,...run.months.map(m=>Math.abs(m.net)));$("months").replaceChildren(...run.months.map(m=>{const b=document.createElement("button");b.className="month "+sign(m.net);b.style.setProperty("--h",Math.max(2,Math.abs(m.net)/max*38)+"px");b.innerHTML='<span>'+esc(m.month.slice(2))+'</span><i></i><small>'+fmt(m.net)+'</small>';b.title=m.month+" · "+m.trades+" trades";b.onclick=()=>{$("month").value=m.month;loadMonth().catch(fail)};return b}));options($("month"),run.months.map(m=>[m.month,m.month+" ("+m.trades+")"]));$("month").value=run.months.at(-1)?.month||"";loadMonth().catch(fail)}
async function loadMonth(){const seq=++monthToken;++tradeToken;stop();trade=null;bars=[];draw();$("details").textContent="Loading trades…";$("ledger").replaceChildren();$("notice").textContent="";ledger=[];page=0;if(run.detail_available===false){$("details").textContent="Summary only: full trade detail exceeds publication budget. Original ledger: "+run.source;$("count").textContent="Summary only";return}const data=await get("runs/"+run.id+"/"+$("month").value+".json");if(seq!==monthToken)return;ledger=data;renderLedger()}
function renderLedger(){const filter=$("filter").value,list=ledger.filter(t=>!filter||(filter==="win"?t.net_points>0:t.net_points<=0));page=Math.max(0,Math.min(page,Math.ceil(list.length/PAGE)-1));const shown=list.slice(page*PAGE,(page+1)*PAGE);$("count").textContent=list.length+" trades · page "+(page+1)+" / "+Math.max(1,Math.ceil(list.length/PAGE));$("ledger").replaceChildren(...shown.map(t=>{const tr=document.createElement("tr");tr.tabIndex=0;tr.innerHTML='<td>'+esc(t.entry_utc.slice(0,16))+'</td><td>'+(t.side===1?"LONG":"SHORT")+'</td><td>'+esc(t.result)+'</td><td class="'+sign(t.net_points)+'">'+fmt(t.net_points)+'</td>';tr.onclick=()=>selectTrade(t,tr).catch(fail);tr.onkeydown=e=>{if(e.key==="Enter"||e.key===" "){e.preventDefault();tr.click()}};return tr}));if(shown.length)$("ledger").firstElementChild.click();else{++tradeToken;stop();trade=null;bars=[];draw();$("details").textContent="No matching trades."}}
function secs(t){return t?Date.parse(t.replace(" ","T"))/1000:NaN}
async function selectTrade(t,row){stop();trade=t;if(frameRun!==run.id){chartFrame=Number(t.signal_tf)||1;if(![1,3,5,15,30,60,240].includes(chartFrame))chartFrame=1;$("timeframe").value=String(chartFrame);frameRun=run.id}windowDay=Math.floor(secs(t.entry_utc)/86400)*86400;$("ledger").querySelectorAll("tr").forEach(x=>x.classList.toggle("active",x===row));const pairs=o=>'<dl>'+Object.entries(o).map(([k,v])=>'<dt>'+esc(k.replaceAll("_"," "))+'</dt><dd>'+esc(v==null?"Not recorded":typeof v==="number"?fmt(v):v)+'</dd>').join("")+'</dl>';$("details").innerHTML='<div class="details"><article><h3>Why entered</h3><p>'+esc(t.entry_reason||"Not recorded in source ledger")+'</p>'+pairs({audit:run.audit,signal_utc:t.trigger_utc,signal_minutes:t.signal_tf,entry_utc:t.entry_utc,entry_price:t.entry_price,...t.signal_context})+'</article><article><h3>Why exited</h3><p>'+esc(t.exit_reason||"Not recorded in source ledger")+'</p>'+pairs({exit_utc:t.exit_utc,exit_price:t.exit_price,stop_price:t.stop_price,target_price:t.target_price,trailing_stop_price:t.trailing_stop_price,liquidation_price:t.liquidation_price,gross_points:t.gross_points,fee_points:t.fee_points,slippage_points:t.assumed_slippage_points,[run.unit==="account USD"?"net_account_usd":"net_points"]:t.net_points,split:t.split})+'</article></div>';await loadWindow()}
// Only reviewed source configurations get reconstructed indicator curves.
function indicatorConfig(r,t){
 if(r.id==="st-rsi-reclaim-3r-tight-color")return {frame:15,ema:[20],st:true,rsi:true,atr:true,filters:true,source:"Original 15M Color sweep · EMA20, ST ATR10×3, ATR14, RSI14; volume ≥1.5× and ATR ≥1× previous 20"};
 if(r.strategy==="US_trend_5m_12bar_break")return {frame:5,ema:[20,50],breakout:true,source:"Original 5M breakout source · EMA20/50, previous 12-bar high/low"};
 return null
}
function aggregate(rows,minutes,complete=false){
 const seconds=minutes*60,out=[];let g=null;
 for(const row of rows){const [t,o,h,l,c,v]=row,bucket=Math.floor(t/seconds)*seconds;
  if(!g||g[0]!==bucket){g=[bucket,o,h,l,c,v||0,1,t,t];out.push(g)}
  else{g[2]=Math.max(g[2],h);g[3]=Math.min(g[3],l);g[4]=c;g[5]+=v||0;g[6]++;g[8]=t}
 }
 return complete?out.filter(g=>g[6]===minutes&&g[7]===g[0]&&g[8]===g[0]+seconds-60):out
}
function smooth(n,alpha,first=false){let value=null,count=0,total=0;return x=>{if(first&&value===null){value=x;return value}if(value===null){total+=x;if(++count===n)value=total/n}else value+=alpha*(x-value);return value}}
function nativeSeries(rows,config){
 if(!config)return [];
 const frames=aggregate(rows,config.frame,true),ema=config.ema.map(n=>smooth(n,2/(n+1),!!config.breakout)),atr10=smooth(10,.1),atr14=smooth(14,1/14),up=smooth(14,1/14),down=smooth(14,1/14);
 let prev=null,upper=null,lower=null,dir=-1;const volumes=[],atrs=[],prior=[];
 return frames.map(b=>{const [t,o,h,l,c,v]=b,tr=prev?Math.max(h-l,Math.abs(h-prev[4]),Math.abs(l-prev[4])):h-l,a10=atr10(tr),a14=atr14(tr),d=prev?c-prev[4]:null,u=d===null?null:up(Math.max(0,d)),dn=d===null?null:down(Math.max(0,-d));
  let st=null;if(a10!==null){const bu=(h+l)/2+3*a10,bl=(h+l)/2-3*a10;if(upper===null){upper=bu;lower=bl;dir=-1}else{upper=bu<upper||prev[4]>upper?bu:upper;lower=bl>lower||prev[4]<lower?bl:lower;if(dir<0&&c>upper)dir=1;else if(dir>0&&c<lower)dir=-1}st=dir>0?lower:upper}
  const mean=a=>a.reduce((s,x)=>s+x,0)/a.length,vr=volumes.length===20&&mean(volumes)>0?v/mean(volumes):null,ar=atrs.length===20&&a14!==null&&mean(atrs)>0?a14/mean(atrs):null;
  const p={time:t+config.frame*60,ema:ema.map(fn=>fn(c)),st,dir,atr:a14,rsi:u===null||dn===null?null:dn===0?(u===0?50:100):100-100/(1+u/dn),vr,ar,volume:v,priorHigh:prior.length===12?Math.max(...prior.map(x=>x[2])):null,priorLow:prior.length===12?Math.min(...prior.map(x=>x[3])):null};
  volumes.push(v);if(volumes.length>20)volumes.shift();if(a14!==null){atrs.push(a14);if(atrs.length>20)atrs.shift()}prior.push(b);if(prior.length>12)prior.shift();prev=b;return p
 })
}
let indicatorRows=[],indicatorMeta=null;
async function loadWindow(){
 const token=++tradeToken,t=trade,r=run;stop();bars=[];sourceBars=[];indicatorRows=[];indicatorMeta=null;draw();if(!t)return;
 const available=new Set(index.candle_days?.[r.symbol]||[]),day=new Date(windowDay*1000).toISOString().slice(0,10);if(!available.has(day)){if(token===tradeToken)$("cursor").textContent="No source candles for "+day;return}
 const config=indicatorConfig(r,t),data=await get("candles/"+r.symbol+"/"+day+".json");if(token!==tradeToken)return;
 const history=[];if(config){const days=[];for(let i=3;i>=1;i--){const d=new Date((windowDay-i*86400)*1000).toISOString().slice(0,10);if(available.has(d))days.push(d)}
  const chunks=await Promise.all(days.map(d=>get("candles/"+r.symbol+"/"+d+".json").catch(()=>[])));if(token!==tradeToken)return;history.push(...chunks.flat())}
 sourceBars=data;indicatorMeta=config;indicatorRows=nativeSeries([...history,...data],config);
 const seconds=chartFrame*60,anchor=Math.min(secs(t.entry_utc),secs(t.trigger_utc)||secs(t.entry_utc));
 const start=Math.max(windowDay,Math.floor((anchor-1800)/seconds)*seconds),end=Math.min(windowDay+86399,secs(t.exit_utc)+1800);bars=data.filter(c=>c[0]>=start&&c[0]<=end);if(!bars.length)bars=data;limit=bars.length;draw()
}
function draw(){
 const c=$("chart"),w=c.clientWidth,h=c.clientHeight,dpr=window.devicePixelRatio||1;c.width=w*dpr;c.height=h*dpr;const x=c.getContext("2d");x.scale(dpr,dpr);
 $("chartFrame").textContent=chartFrame+"m chart · recorded 1m execution · UTC";
 $("indicatorInfo").textContent=trade?(indicatorMeta?indicatorMeta.source+" · reconstructed from published trade candles, limited prior history; recorded signal values below are authoritative.":"No verified full indicator configuration for this archived run. Recorded signal fields are shown below; no generic overlays."):"";
 const indicatorHost=$("indicatorValues");indicatorHost.replaceChildren();
 if(!bars.length||!trade){$("cursor").textContent="";return}
 const visible=bars.slice(0,limit),cutoff=visible.at(-1)?.[0]+60,b=aggregate(visible,chartFrame),pad=12,right=76,bottom=26;if(!b.length)return;
 const cfg=indicatorMeta,show=$("overlay").checked&&cfg,series=show?indicatorRows.filter(p=>p.time<=cutoff):[];
 // Sample only completed native indicator candles at each visible chart candle's end.
 let j=-1;const samples=b.map(row=>{const end=Math.min(row[8]+60,cutoff);while(j+1<series.length&&series[j+1].time<=end)j++;return j>=0?series[j]:null});
 const signal=secs(trade.trigger_utc),signalVisible=Number.isFinite(signal)&&signal<=cutoff;
 const ctx=trade.signal_context||{},recorded=Object.entries(ctx).filter(([k,v])=>/^(ema\\d+|supertrend|rsi\\d*|atr\\d*|signal_atr|volume_ratio|atr_ratio|prior_high|prior_low)$/i.test(k)&&Number.isFinite(v));
 if(signalVisible&&recorded.length){for(const [key,value] of recorded){const item=document.createElement("span");item.className="indicator-chip";item.textContent=key.replaceAll("_"," ").toUpperCase()+": "+fmt(value);indicatorHost.append(item)}}
 else if(recorded.length)indicatorHost.textContent="Recorded indicator values become available at the signal timestamp.";
 const panels=show&&cfg.filters?3:0,priceBottom=h-bottom-panels*62;
 const markerIndex=time=>{const t=secs(time);if(!Number.isFinite(t)||t>cutoff)return -1;let i=b.findIndex(v=>t>=v[0]&&t<v[0]+chartFrame*60&&t<=v[8]+60);if(i<0&&t===cutoff)i=b.length-1;return i};
 const tradeMarkers=[[trade.entry_utc,trade.entry_price,"#66b5ff","ENTRY"],[trade.exit_utc,trade.exit_price,"#c5a1ff","EXIT"]].map(m=>[...m,markerIndex(m[0])]).filter(m=>m[4]>=0&&Number.isFinite(m[1]));
 const levels=signalVisible?[trade.stop_price,trade.target_price,trade.trailing_stop_price,trade.liquidation_price].filter(Number.isFinite):[];
 const recPrice=signalVisible&&markerIndex(trade.trigger_utc)>=0?recorded.filter(([k])=>/^(ema\\d+|supertrend|prior_high|prior_low)$/i.test(k)):[];
 const priceSeries=samples.flatMap(p=>p?[...p.ema,...(cfg?.st?[p.st]:[]),...(cfg?.breakout?[p.priorHigh,p.priorLow]:[])]:[]).filter(Number.isFinite);
 const lo=Math.min(...b.map(v=>v[3]),...levels,...priceSeries,...tradeMarkers.map(m=>m[1]),...recPrice.map(m=>m[1])),hi=Math.max(...b.map(v=>v[2]),...levels,...priceSeries,...tradeMarkers.map(m=>m[1]),...recPrice.map(m=>m[1])),range=Math.max(hi-lo,.000001),y=p=>pad+(hi-p)/range*(priceBottom-pad),step=(w-right-pad)/Math.max(b.length,1),at=i=>pad+(i+.5)*step;
 x.font="11px system-ui";
 for(let i=0;i<=4;i++){const v=lo+range*i/4,yy=y(v);x.strokeStyle="#26364a";x.beginPath();x.moveTo(pad,yy);x.lineTo(w-right,yy);x.stroke();x.fillStyle="#9aafc2";x.fillText(fmt(v),w-right+4,yy+4)}
 for(const [i,[t,o,high,low,cl,vol,count]] of b.entries()){const xx=at(i);x.strokeStyle=x.fillStyle=cl>=o?"#36d8aa":"#fb7785";x.globalAlpha=count<chartFrame?.55:1;x.beginPath();x.moveTo(xx,y(high));x.lineTo(xx,y(low));x.stroke();x.fillRect(xx-Math.max(1,step*.32),Math.min(y(o),y(cl)),Math.max(1,step*.64),Math.max(1,Math.abs(y(o)-y(cl))));x.globalAlpha=1}
 function line(values,color,scale){x.strokeStyle=color;x.beginPath();let started=false;values.forEach((v,i)=>{if(!Number.isFinite(v)){started=false;return}if(started)x.lineTo(at(i),scale(v));else{x.moveTo(at(i),scale(v));started=true}});x.stroke()}
 if(show){cfg.ema.forEach((n,i)=>line(samples.map(p=>p?.ema[i]),i?"#79baff":"#f0c36a",y));if(cfg.st)line(samples.map(p=>p?.st),"#67d4c0",y);if(cfg.breakout){line(samples.map(p=>p?.priorHigh),"#c5a1ff",y);line(samples.map(p=>p?.priorLow),"#fb7785",y)}}
 // Exit-time snapshots such as a final trailing stop must not appear before exit.
 for(const [price,label,visibleNow] of [[trade.stop_price,"SL",signalVisible],[trade.target_price,"TP",signalVisible],[trade.trailing_stop_price,"TRAIL (recorded)",secs(trade.exit_utc)<=cutoff],[trade.liquidation_price,"LIQ (recorded)",secs(trade.exit_utc)<=cutoff]]){if(!visibleNow||!Number.isFinite(price))continue;x.strokeStyle=x.fillStyle="#eab66b";x.setLineDash([4,4]);x.beginPath();x.moveTo(pad,y(price));x.lineTo(w-right,y(price));x.stroke();x.setLineDash([]);x.fillText(label,pad,y(price)-4)}
 for(const [time,p,color,label,i] of tradeMarkers){const xx=at(i),yy=y(p);x.fillStyle=color;x.beginPath();x.arc(xx,yy,5,0,Math.PI*2);x.fill();x.fillText(label,Math.max(pad,Math.min(xx,w-right-40)),Math.max(12,yy-9))}
 if($("overlay").checked){const i=markerIndex(trade.trigger_utc);for(const [key,v] of recPrice){x.fillStyle="#fff";x.fillRect(at(i)-3,y(v)-3,6,6);x.fillText(key.toUpperCase()+" (recorded)",Math.min(at(i)+5,w-right-110),Math.max(12,y(v)-5))}}
 if(panels){function pane(k,title,colors,series,min,max,thresholds=[]){const top=priceBottom+12+k*62,bot=top+44,scale=v=>bot-(v-min)/Math.max(max-min,.0001)*(bot-top);x.strokeStyle="#26364a";x.beginPath();x.moveTo(pad,top);x.lineTo(w-right,top);x.stroke();x.fillStyle="#9aafc2";x.fillText(title,pad,top+11);for(const [v,color] of thresholds){x.strokeStyle=color;x.setLineDash([3,3]);x.beginPath();x.moveTo(pad,scale(v));x.lineTo(w-right,scale(v));x.stroke();x.setLineDash([])}series.forEach((values,i)=>line(values,colors[i],scale));x.fillStyle="#9aafc2";x.fillText(fmt(max),w-right+4,top+9);x.fillText(fmt(min),w-right+4,bot)}
  pane(0,"RSI14 (15m) · 50 / 60",["#c5a1ff"],[samples.map(p=>p?.rsi)],0,100,[[50,"#697888"],[60,"#697888"]]);
  const av=samples.map(p=>p?.atr),maxAtr=Math.max(1,...av.filter(Number.isFinite));pane(1,"ATR14 (15m)",["#79baff"],[av],0,maxAtr);
  const vr=samples.map(p=>p?.vr),ar=samples.map(p=>p?.ar);pane(2,"Volume ratio (gold) / ATR ratio (blue)",["#f0c36a","#79baff"],[vr,ar],0,Math.max(2,...vr.filter(Number.isFinite),...ar.filter(Number.isFinite)),[[1,"#79baff"],[1.5,"#f0c36a"]])
 }
 x.fillStyle="#9aafc2";for(let i=0;i<Math.min(5,b.length);i++){const k=Math.floor(i*(b.length-1)/Math.max(1,Math.min(5,b.length)-1));x.fillText(new Date(b[k][0]*1000).toISOString().slice(11,16),Math.min(at(k),w-right-28),h-7)}
 $("cursor").textContent=new Date(cutoff*1000).toISOString().slice(0,16).replace("T"," ")+" UTC · "+visible.length+" source minutes · "+b.length+" chart candles";
}
$("run").onchange=renderRun;$("month").onchange=()=>loadMonth().catch(fail);$("filter").onchange=()=>{page=0;renderLedger()};$("tradePrev").onclick=()=>{page--;renderLedger()};$("tradeNext").onclick=()=>{page++;renderLedger()};$("prev").onclick=()=>{stop();limit=Math.max(1,limit-1);draw()};$("next").onclick=()=>{stop();limit=Math.min(bars.length,limit+1);draw()};$("full").onclick=()=>{stop();limit=bars.length;draw()};$("play").onclick=()=>{if(timer){stop();return}if(!bars.length)return;if(limit>=bars.length)limit=1;timer=setInterval(()=>{limit=Math.min(bars.length,limit+1);draw();if(limit>=bars.length)stop()},120)};window.addEventListener("resize",()=>{draw();drawCurves()});$("overlay").onchange=draw;$("timeframe").onchange=()=>{stop();chartFrame=Number($("timeframe").value);draw()};$("windowPrev").onclick=()=>{if(trade){windowDay-=86400;loadWindow().catch(fail)}};$("windowNext").onclick=()=>{if(trade){windowDay+=86400;loadWindow().catch(fail)}};
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
  $("provenance").textContent="Source commit: "+index.commit+" | Data snapshot: "+activeSnapshot+" | ETH workflow run: "+(index.eth_workflow_run||"not recorded")+" | Archived runs preserve their own cost assumptions. Indicator curves are reconstructed references only for reviewed configurations; recorded signal fields remain authoritative. Research only.";
  $("dataStatus").textContent="Published "+manifest.published_at+" · auto-refresh every minute";
  $("notice").textContent="";
  const symbols=[...new Set(index.runs.map(r=>r.symbol))];options($("symbol"),symbols.map(s=>[s,s]));if(symbols.includes(symbol))$("symbol").value=symbol;chooseSymbol(preferred);
 }catch(e){$("dataStatus").textContent=activeSnapshot?"Refresh failed; showing last verified snapshot":"Published data unavailable";if(!activeSnapshot)fail(e);else console.warn(e)}
 finally{refreshBusy=false}
}
$("refreshData").onclick=()=>refreshData(true);
refreshData();
if(!LOCAL)setInterval(()=>{if(!document.hidden)refreshData()},60000);
