import type {SymbolName} from "./historyCache";
const DAY=86400,MAX_DAYS=31,MAX_GZIP=4*1024*1024,MAX_TEXT=8*1024*1024;
const CACHE="btc-analysis-public-archive-v1";
const HEADER="time,open,high,low,close,volume";
type Partition={file:string;utc_start:string;utc_end_exclusive:string;expected_minutes:number;observed_candles:number;missing_minutes:number;sha256_gzip:string};
type Manifest={symbol:SymbolName;resolution:string;timestamp_unit:string;timestamp_label:string;partitions:Partition[];requested_through_utc:string};
const base=(s:SymbolName,kind:"trade"|"mark"|"funding"="trade")=>new URL("history-archive/"+s+"/"+(kind==="trade"?"":kind==="mark"?"mark_1m/":"funding_1h/"),document.baseURI);
function day(value:string){if(!/^\d{4}-\d{2}-\d{2}$/.test(value))throw Error("Choose valid UTC dates.");const ms=Date.parse(value+"T00:00:00Z");if(!Number.isFinite(ms)||new Date(ms).toISOString().slice(0,10)!==value)throw Error("Invalid UTC date.");return ms/1000;}
function epoch(value:string){const n=Date.parse(value)/1000;if(!Number.isSafeInteger(n)||n%60)throw Error("Invalid archive timestamp.");return n;}
async function get(url:URL,signal?:AbortSignal){const r=await fetch(url,{credentials:"omit",redirect:"error",referrerPolicy:"no-referrer",signal});if(!r.ok)throw Error("Historical archive unavailable (HTTP "+r.status+").");return r;}
async function hash(bytes:ArrayBuffer){return Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256",bytes)),b=>b.toString(16).padStart(2,"0")).join("");}
async function bounded(response:Response,max:number){if(!response.body)throw Error("Missing archive body.");const reader=response.body.getReader(),chunks:Uint8Array[]=[];let size=0;try{while(true){const {done,value}=await reader.read();if(done)break;size+=value.byteLength;if(size>max){await reader.cancel();throw Error("Archive exceeds size limit.");}chunks.push(value);}}finally{reader.releaseLock();}const bytes=new Uint8Array(size);let offset=0;for(const chunk of chunks){bytes.set(chunk,offset);offset+=chunk.length;}return bytes.buffer;}
async function partitionBytes(url:URL,digest:string,cacheEnabled:boolean,signal?:AbortSignal){
 let cache:Cache|undefined;if(cacheEnabled){try{cache=await caches.open(CACHE);}catch{/* optional cache */}}
 if(cache){try{const hit=await cache.match(url.href);if(hit){const bytes=await bounded(hit,MAX_GZIP);if(await hash(bytes)===digest)return {bytes,cached:true};await cache.delete(url.href);}}catch{try{await cache.delete(url.href);}catch{/* cache optional */}}}
 const bytes=await bounded(await get(url,signal),MAX_GZIP);if(await hash(bytes)!==digest)throw Error("Historical archive checksum mismatch.");
 if(cache){try{await cache.put(url.href,new Response(bytes));const keys=await cache.keys();for(const key of keys.slice(0,Math.max(0,keys.length-4)))await cache.delete(key);}catch{/* storage quota must not prevent a run */}}
 return {bytes,cached:false};
}
export async function loadRepositoryHistory(symbol:SymbolName,from:string,to:string,cacheEnabled:boolean,signal?:AbortSignal,kind:"trade"|"mark"|"funding"="trade"){
 const step=kind==="funding"?3600:60;
 const start=day(from),end=day(to)+DAY;
 if(end<=start||end-start>MAX_DAYS*DAY)throw Error("Select 1–31 calendar days (inclusive UTC).");
 const root=base(symbol,kind),manifest=JSON.parse(new TextDecoder().decode(await bounded(await get(new URL("manifest.json",root),signal),256*1024))) as Manifest;
 if(manifest.symbol!==symbol||manifest.resolution!==(kind==="funding"?"1h":"1m")||manifest.timestamp_unit!=="unix_seconds_utc"||!Array.isArray(manifest.partitions)||manifest.partitions.length>500)throw Error("Invalid historical manifest.");
 const parts=manifest.partitions.map(p=>{const a=epoch(p.utc_start),b=epoch(p.utc_end_exclusive);if(!/^\d{4}-\d{2}\.csv\.gz$/.test(p.file)||!/^[a-f0-9]{64}$/.test(p.sha256_gzip)||b<=a||b-a>31*DAY||!Number.isSafeInteger(p.observed_candles)||p.observed_candles<0||p.expected_minutes!==(b-a)/step||p.missing_minutes!==p.expected_minutes-p.observed_candles||p.missing_minutes<0)throw Error("Invalid archive partition.");return {p,a,b};}).sort((x,y)=>x.a-y.a);
 const selected=parts.filter(x=>x.a<end&&x.b>start);if(!selected.length||selected.length>3||selected[0].a>start||selected[selected.length-1].b<end)throw Error("Selected dates are outside published archive coverage.");
 const rows:string[]=[];let next=start,cacheHits=0;
 for(const {p,a,b} of selected){
  if(signal?.aborted)throw new DOMException("Cancelled","AbortError");
  const {bytes,cached}=await partitionBytes(new URL(p.sha256_gzip+".bin",root),p.sha256_gzip,cacheEnabled,signal);if(cached)cacheHits++;
  if(typeof DecompressionStream==="undefined")throw Error("This browser does not support gzip decoding. Use a recent browser or import CSV.");
  const decoded=new Response(new Blob([bytes]).stream().pipeThrough(new DecompressionStream("gzip")));
  const lines=new TextDecoder("utf-8",{fatal:true}).decode(await bounded(decoded,MAX_TEXT)).trimEnd().split(/\r?\n/);
  if(lines.shift()!==HEADER||lines.length!==p.observed_candles)throw Error("Archive schema or row count mismatch.");
  let previous=a-step;
  for(const line of lines){
   const cols=line.split(","),t=Number(cols[0]);
   if(cols.length!==6||!/^\d+$/.test(cols[0])||!Number.isSafeInteger(t)||t%step||t<=previous||t<a||t>=b||cols.slice(1).some((v,j)=>!(kind!=="trade"&&j===4&&!v.trim())&&(!v.trim()||!Number.isFinite(Number(v)))))throw Error("Invalid or unordered archive row.");
   previous=t;
   if(t>=start&&t<end){if(t!==next)throw Error("Missing or duplicate 1m candle at "+new Date(next*1000).toISOString());rows.push(kind==="mark"?cols.slice(0,5).join(","):line);next+=step;}
  }
 }
 if(next!==end||rows.length!==(end-start)/step)throw Error("Selected range contains missing 1m candles.");
 const csv=(kind==="mark"?"time,open,high,low,close":HEADER)+"\n"+rows.join("\n")+"\n";if(new TextEncoder().encode(csv).byteLength>16*1024*1024)throw Error("CSV exceeds 16 MiB.");
 return {csv,name:symbol+" "+from+" to "+to+" UTC (repository)",bars:rows.length,cacheHits,partitions:selected.length,coverageThrough:manifest.requested_through_utc};
}
export async function clearRepositoryHistoryCache(){await caches.delete(CACHE);}
