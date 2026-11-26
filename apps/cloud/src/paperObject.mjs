import {ACTIVE,init,validateConfig,parseCandle,advance} from "./paperEngine.mjs";
const SOURCE="https://api.india.delta.exchange/v2/history/candles";
const out=(value,status=200)=>Response.json(value,{status,headers:{"Cache-Control":"no-store"}});
const sameConfig=(a,b)=>Object.keys(a).length===Object.keys(b).length&&Object.keys(a).every(k=>a[k]===b[k]);
export class PaperLane{
 constructor(ctx,env){this.ctx=ctx;this.env=env;this.storage=ctx.storage;}
 now(){return Date.now();}
 async candle(symbol,t){
  const url=new URL(SOURCE);url.search=new URLSearchParams({symbol,resolution:"1m",start:String(t/1000),end:String(t/1000+60)}).toString();
  const response=await fetch(url,{method:"GET",redirect:"error",signal:AbortSignal.timeout(8000),headers:{Accept:"application/json"}});
  if(!response.ok||!response.body)throw Error("market_unavailable");
  const reader=response.body.getReader();let n=0,parts=[];
  try{while(true){const x=await reader.read();if(x.done)break;n+=x.value.byteLength;if(n>65536){await reader.cancel();throw Error("market_response_too_large");}parts.push(x.value);}}finally{reader.releaseLock();}
  const bytes=new Uint8Array(n);let pos=0;for(const p of parts){bytes.set(p,pos);pos+=p.byteLength;}
  const body=JSON.parse(new TextDecoder().decode(bytes));
  if(body.success!==true||!Array.isArray(body.result)||body.result.length>3)throw Error("market_invalid_response");
  const match=body.result.filter(x=>x.time===t/1000);if(match.length!==1)throw Error("missing_candle");
  return parseCandle(match[0],t);
 }
 async fetch(req){
  const url=new URL(req.url);const path=url.pathname;
  if(path==="/state"&&req.method==="GET"){return out({session:await this.storage.get("state")??null,scale:"100000000",reference_only:true});}
  if(path==="/ledger"&&req.method==="GET"){
   const s=await this.storage.get("state");
   if(!s)return out({session:null,fills:[]});
   const after=Number(url.searchParams.get("after")??0);
   if(!Number.isSafeInteger(after)||after<0)return out({error:"invalid_cursor"},400);
   const key=(id)=>"fill:"+s.id+":"+String(id).padStart(8,"0");
   const records=await this.storage.list({prefix:"fill:"+s.id+":",startAfter:key(after),limit:100});
   return out({session:s.id,fills:[...records.values()],next:records.size?Number([...records.values()].at(-1).id):after,scale:"100000000"});
  }
  if(path==="/start"&&req.method==="POST"){
   let c,b;try{b=await req.json();if(!["BTCUSD","ETHUSD"].includes(b.symbol))throw Error();c=validateConfig(b.config);}catch{return out({error:"invalid_paper_config"},400);}
   return this.storage.transaction(async()=>{
    const old=await this.storage.get("state");
    if(old?.id===c.request_id)return sameConfig(old.config,c)?out({session:old}):out({error:"request_conflict"},409);
    // Single retained session per lane. Explicit clear required; no silent deletion.
    if(old)return out({error:"lane_not_empty"},409);
    const s=init(b.symbol,c,this.now());
    await this.storage.put("state",s);
    await this.storage.setAlarm(s.cursor+70000);
    return out({session:s},201);
   });
  }
  if(path==="/stop"&&req.method==="POST"){
   const b=await req.json();
   return this.storage.transaction(async()=>{
    const s=await this.storage.get("state");
    if(!s||s.id!==b.id)return out({error:"not_found"},404);
    if(ACTIVE(s)){s.status="stopped";s.reason="operator_stop";s.pending=null;await this.storage.put("state",s);await this.storage.deleteAlarm();}
    return out({session:s});
   });
  }
  if(path==="/clear"&&req.method==="POST"){
   const b=await req.json();
   return this.storage.transaction(async()=>{
    const s=await this.storage.get("state");
    if(!s||s.id!==b.id)return out({error:"not_found"},404);
    if(ACTIVE(s))return out({error:"active_session"},409);
    // Bounded deletion in chunks. State remains until all ledger keys are gone.
    const records=await this.storage.list({prefix:"fill:"+s.id+":",limit:100});
    if(records.size){await this.storage.delete([...records.keys()]);return out({cleared:false,removed:records.size});}
    await this.storage.delete("state");await this.storage.deleteAlarm();return out({cleared:true,removed:0});
   });
  }
  return out({error:"not_found"},404);
 }
 async alarm(){
  const snapshot=await this.storage.get("state");if(!ACTIVE(snapshot))return;
  const t=snapshot.cursor,id=snapshot.id,now=this.now();
  const commit=async(fn)=>this.storage.transaction(async()=>{
   const s=await this.storage.get("state");if(!ACTIVE(s)||s.id!==id||s.cursor!==t)return;
   await fn(s);
  });
  const halt=async(s,reason)=>{s.status="halted";s.pending=null;s.reason=reason;await this.storage.put("state",s);await this.storage.deleteAlarm();};
  // Set retry alarm before network I/O. State CAS fences stop/restart and duplicate delivery.
  if(now>t+180000){await commit(s=>halt(s,"stale_or_missing_candle"));return;}
  if(now<t+70000){await commit(()=>this.storage.setAlarm(t+70000));return;}
  await commit(()=>this.storage.setAlarm(Math.min(t+180001,now+15000)));
  let bar;
  try{bar=await this.candle(snapshot.symbol,t);}catch{return;}
  await commit(async s=>{
   if(this.now()>t+180000){await halt(s,"stale_or_missing_candle");return;}
   const next=advance(s,bar);
   for(const e of next.events)await this.storage.put("fill:"+id+":"+String(e.id).padStart(8,"0"),e);
   await this.storage.put("state",next.state);
   if(ACTIVE(next.state))await this.storage.setAlarm(Math.max(this.now()+1000,next.state.cursor+70000));else await this.storage.deleteAlarm();
  });
 }
}
