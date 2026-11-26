/** Immutable local experiment snapshots; no CSV, token, or account credentials. */
import type {BatchInput,LocalResult} from "./parallelReplay";
export const MAX_RUNS=30;
const MAX_RECORD_BYTES=256*1024;
export type RunRecord={id:string;created:number;name:string;graph:string;symbol:BatchInput["symbol"];settings:Record<string,string>;result:LocalResult;elapsedMs:number;totalMs:number};
export function recordRun(input:BatchInput,graph:string,name:string,result:LocalResult,elapsedMs:number,totalMs:number):RunRecord{
 return {id:crypto.randomUUID(),created:Date.now(),name:name.trim().slice(0,80)||"Experiment",graph,symbol:input.symbol,settings:{...input.settings},result:{...result,scenarios:result.scenarios.map(({details: _details,...summary})=>summary)},elapsedMs,totalMs};
}
export function mergeRuns(...groups:RunRecord[][]){
 const byId=new Map<string,RunRecord>();
 for(const group of groups)for(const r of group)byId.set(r.id,r);
 return [...byId.values()].sort((a,b)=>b.created-a.created||b.id.localeCompare(a.id)).slice(0,MAX_RUNS);
}
function open():Promise<IDBDatabase>{return new Promise((resolve,reject)=>{
 const req=indexedDB.open("btc-analysis-local-experiments",1);
 req.onupgradeneeded=()=>req.result.createObjectStore("runs",{keyPath:"id"});
 req.onsuccess=()=>resolve(req.result);req.onerror=()=>reject(req.error);req.onblocked=()=>reject(new Error("Experiment database blocked"));
});}
async function transact<T>(mode:IDBTransactionMode,fn:(store:IDBObjectStore,tx:IDBTransaction,resolveValue:(value:T)=>void)=>void):Promise<T>{
 const db=await open();
 try{return await new Promise<T>((resolve,reject)=>{
  let value:T;
  const tx=db.transaction("runs",mode);
  tx.oncomplete=()=>resolve(value);tx.onerror=()=>reject(tx.error);tx.onabort=()=>reject(tx.error??new Error("Experiment transaction aborted"));
  try{fn(tx.objectStore("runs"),tx,v=>{value=v;});}catch(e){tx.abort();reject(e);}
 });}finally{db.close();}
}
function validRecord(r:RunRecord){
 return !!r&&typeof r.id==="string"&&Number.isFinite(r.created)&&typeof r.name==="string"&&typeof r.graph==="string"&&
  (r.symbol==="BTCUSD"||r.symbol==="ETHUSD")&&!!r.settings&&!!r.result&&
  typeof r.result.result_sha256==="string"&&typeof r.result.engine_version==="string"&&Array.isArray(r.result.scenarios)&&
  new TextEncoder().encode(JSON.stringify(r)).byteLength<=MAX_RECORD_BYTES;
}
export async function loadRuns():Promise<RunRecord[]>{
 return transact("readonly",(store,_tx,set)=>{const r=store.getAll();r.onsuccess=()=>set(mergeRuns((r.result as RunRecord[]).filter(validRecord)));});
}
export async function persistRuns(records:RunRecord[]){
 if(records.length>MAX_RUNS||records.some(r=>!validRecord(r)))throw new Error("Experiment record exceeds bounded storage or is invalid.");
 return transact<void>("readwrite",(store,tx,set)=>{
  const read=store.getAll();
  read.onsuccess=()=>{
   const old=read.result as RunRecord[];
   const next=mergeRuns(old.filter(validRecord),records);
   const ids=new Set(next.map(r=>r.id));
   for(const r of old)if(!ids.has(r.id))store.delete(r.id);
   for(const r of records)if(ids.has(r.id))store.put(r);
   set(undefined);
  };
  read.onerror=()=>tx.abort();
 });
}
export async function removeRun(id:string){return transact<void>("readwrite",(s,_tx,set)=>{s.delete(id);set(undefined);});}
export async function clearRuns(){return transact<void>("readwrite",(s,_tx,set)=>{s.clear();set(undefined);});}
export function comparable(a:RunRecord,b:RunRecord){
 return a.symbol===b.symbol&&a.result.data_sha256===b.result.data_sha256&&a.result.engine_version===b.result.engine_version&&
  JSON.stringify(Object.entries(a.settings).sort())===JSON.stringify(Object.entries(b.settings).sort());
}
