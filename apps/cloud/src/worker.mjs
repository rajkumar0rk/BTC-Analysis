/** Lightweight Cloudflare module Worker. No backtest, arbitrary code or trading execution. */
const MAX_BODY=96*1024,MAX_SOURCE=65536,MAX_OWNERS=8;
const encoder=new TextEncoder();
const ID=/^[0-9a-f]{32}$/,HASH=/^[0-9a-f]{64}$/,OWNER=/^[a-zA-Z0-9_-]{1,64}$/;
class HttpError extends Error{
 constructor(status,code){super(code);this.status=status;this.code=code;}
}
const fail=(status,code)=>{throw new HttpError(status,code);};
async function hash(s){return Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256",encoder.encode(s))),x=>x.toString(16).padStart(2,"0")).join("");}
function same(a,b){
 let diff=a.length^b.length;
 for(let i=0;i<64;i++)diff|=(a.charCodeAt(i)||0)^(b.charCodeAt(i)||0);
 return diff===0;
}
function origins(env){
 const values=(env.ALLOWED_ORIGINS||"").split(",").map(x=>x.trim()).filter(Boolean);
 if(values.length>4||values.some(x=>{try{const u=new URL(x);return u.origin!==x||u.protocol!=="https:";}catch{return true;}}))fail(503,"invalid_origin_configuration");
 return values;
}
function headers(origin){
 const h=new Headers({"Content-Type":"application/json; charset=utf-8","Cache-Control":"no-store","X-Content-Type-Options":"nosniff","Referrer-Policy":"no-referrer","X-Frame-Options":"DENY","Content-Security-Policy":"default-src 'none'; frame-ancestors 'none'","Vary":"Origin"});
 if(origin)h.set("Access-Control-Allow-Origin",origin);
 return h;
}
function json(data,status=200,origin=null){return new Response(JSON.stringify(data),{status,headers:headers(origin)});}
async function auth(req,env){
 let owners;
 try{owners=JSON.parse(env.AUTH_HASHES_JSON||"null");}catch{fail(503,"authentication_not_configured");}
 if(!owners||typeof owners!=="object"||Array.isArray(owners))fail(503,"authentication_not_configured");
 const entries=Object.entries(owners);
 if(!entries.length||entries.length>MAX_OWNERS||entries.some(([o,h])=>!OWNER.test(o)||typeof h!=="string"||!HASH.test(h))||new Set(entries.map(x=>x[1])).size!==entries.length)fail(503,"authentication_not_configured");
 const token=req.headers.get("Authorization")||"";
 if(!/^Bearer [A-Za-z0-9_-]{43,128}$/.test(token))fail(401,"invalid_credentials");
 const digest=await hash(token.slice(7));let owner=null;
 for(const [o,h] of entries)if(same(digest,h))owner=o;
 if(owner===null)fail(401,"invalid_credentials");
 return owner;
}
async function body(req){
 if((req.headers.get("Content-Type")||"").split(";")[0].trim().toLowerCase()!=="application/json")fail(415,"json_required");
 const declared=req.headers.get("Content-Length");
 if(declared!==null&&(!/^\d+$/.test(declared)||Number(declared)>MAX_BODY))fail(413,"body_too_large");
 if(!req.body)fail(400,"body_required");
 const reader=req.body.getReader();const parts=[];let bytes=0,fragments=0;
 try{
  while(true){const {done,value}=await reader.read();if(done)break;
   bytes+=value.byteLength;if(bytes>MAX_BODY||++fragments>1024){await reader.cancel();fail(413,"body_too_large");}
   parts.push(value);
  }
 }finally{reader.releaseLock();}
 const raw=new Uint8Array(bytes);let offset=0;
 for(const part of parts){raw.set(part,offset);offset+=part.byteLength;}
 let obj;try{obj=JSON.parse(new TextDecoder("utf-8",{fatal:true}).decode(raw));}catch{fail(400,"invalid_json");}
 if(!obj||typeof obj!=="object"||Array.isArray(obj))fail(400,"invalid_json_object");
 return obj;
}
function exact(o,keys){if(Object.keys(o).sort().join(",")!==[...keys].sort().join(","))fail(400,"invalid_fields");}
function source(s){if(typeof s!=="string"||!s.trim()||encoder.encode(s).byteLength>MAX_SOURCE||s.includes("\0"))fail(400,"invalid_source");return s;}
function name(s){if(typeof s!=="string"||!s.trim()||encoder.encode(s.trim()).byteLength>160||/[\u0000-\u001f\u007f]/.test(s))fail(400,"invalid_name");return s.trim();}
function version(v){if(!Number.isSafeInteger(v)||v<1||v>100)fail(400,"invalid_version");return v;}
function requireStorage(store){if(!store)fail(503,"persistent_storage_not_configured");return store;}
function errorStatus(code){
 return {not_found:404,version_conflict:409,quota_exceeded:409,archived:409}[code]||503;
}
// Production factory deliberately returns no storage in M26. M27 adds D1 adapter.
// Injectable adapter is ONLY for local contract tests. No global memory persistence.
export function makeHandler(storageFactory=()=>null){
 return async function handle(req,env={}){
  let origin=null;
  try{
   const url=new URL(req.url),path=url.pathname;
   if(url.search)fail(400,"query_not_supported");
   const incoming=req.headers.get("Origin");
   if(incoming){if(!origins(env).includes(incoming))fail(403,"origin_not_allowed");origin=incoming;}
   if(req.method==="OPTIONS"){
    if(!origin)fail(403,"origin_required");
    const method=req.headers.get("Access-Control-Request-Method")||"";
    const requested=(req.headers.get("Access-Control-Request-Headers")||"").split(",").map(s=>s.trim().toLowerCase()).filter(Boolean);
    if(!["GET","POST","PUT"].includes(method)||requested.some(x=>!["authorization","content-type"].includes(x)))fail(403,"preflight_not_allowed");
    if(!path.startsWith("/v1/cloud/"))fail(404,"not_found");
    const h=headers(origin);h.set("Access-Control-Allow-Methods","GET, POST, PUT");h.set("Access-Control-Allow-Headers","Authorization, Content-Type");h.set("Access-Control-Max-Age","300");
    return new Response(null,{status:204,headers:h});
   }
   if(path==="/health"&&req.method==="GET")return json({status:"ok",service:"btc-analysis-cloud",schema_version:1},200,origin);
   if(!path.startsWith("/v1/cloud/"))fail(404,"not_found");
   const owner=await auth(req,env);
   const store=storageFactory(env);
   if(path==="/v1/cloud/capabilities"&&req.method==="GET")return json({schema_version:1,owner,storage:!!store,source_execution:false,backtest_execution:false,paper_trading:false,live_orders:false,max_source_bytes:MAX_SOURCE,max_strategies:30,max_revisions:100},200,origin);
   if(path==="/v1/cloud/strategies"){
    if(req.method==="GET")return json({strategies:await requireStorage(store).list(owner)},200,origin);
    if(req.method==="POST"){
     const s=requireStorage(store),b=await body(req);exact(b,["name","source"]);const src=source(b.source);
     return json(await s.create(owner,{id:crypto.randomUUID().replaceAll("-",""),name:name(b.name),source:src,code_sha256:await hash(src),created:Math.floor(Date.now()/1000)}),201,origin);
    }
    fail(405,"method_not_allowed");
   }
   const match=path.match(/^\/v1\/cloud\/strategies\/([0-9a-f]{32})(?:\/revisions\/([0-9]{1,3}))?$/);
   if(match&&ID.test(match[1])){
    const s=requireStorage(store),id=match[1];
    if(match[2]&&req.method==="GET"){
     const r=await s.revision(owner,id,version(Number(match[2])));if(!r)fail(404,"not_found");return json(r,200,origin);
    }
    if(!match[2]&&req.method==="PUT"){
     const b=await body(req);exact(b,["expected_version","source"]);const src=source(b.source);
     return json(await s.revise(owner,id,version(b.expected_version),{source:src,code_sha256:await hash(src),created:Math.floor(Date.now()/1000)}),200,origin);
    }
    fail(405,"method_not_allowed");
   }
   fail(404,"not_found");
  }catch(e){
   if(e instanceof HttpError)return json({error:e.code},e.status,origin);
   if(e&&["not_found","version_conflict","quota_exceeded","archived"].includes(e.code))return json({error:e.code},errorStatus(e.code),origin);
   return json({error:"service_unavailable"},503,origin);
  }
 };
}
const handle=makeHandler();
export default {fetch:handle};
