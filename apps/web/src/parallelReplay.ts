/** Bounded batch orchestration. Each worker owns its own Python runtime/cache. */
export type LocalScenario={path:string;bars:number;final_equity:string;fees:string;taxes:string;metrics:Record<string,string|number|null>;monthly:{month:string;pnl:string;return_pct:string|null}[]};
export type LocalResult={engine_version:string;source:string;data_sha256:string;graph_sha256:string;result_sha256:string;worst_path:string;scenarios:LocalScenario[];limitations:string[]};
export type BatchInput={csv:string;symbol:"BTCUSD"|"ETHUSD";settings:Record<string,string>;assume:boolean};
export type Variant={id:number;name:string;graph:string};
export type Status="queued"|"initializing"|"running"|"completed"|"failed"|"cancelled"|"timed_out";
export type BatchRow=Variant&{status:Status;progress:number;result?:LocalResult;error?:string;elapsedMs?:number;totalMs?:number};
export type BatchSnapshot={rows:BatchRow[];active:number;peak:number;elapsedMs:number;finished:boolean;limit:number};
export const MAX_VARIANTS=6;
const terminal=(s:Status)=>s==="completed"||s==="failed"||s==="cancelled"||s==="timed_out";
export function recommendedConcurrency(){
 const ram=(navigator as Navigator&{deviceMemory?:number}).deviceMemory;
 return navigator.hardwareConcurrency>=4&&ram!==undefined&&ram>=4?2:1;
}
type Slot={worker:Worker;row:BatchRow|null;timer?:number};
export class ParallelReplay{
 private slots:Slot[]=[];
 private rows:BatchRow[];
 private disposed=false;
 private started=false;
 private peak=0;
 private startTime=0;
 private elapsed=0;
 private input:BatchInput;
 constructor(input:BatchInput,variants:Variant[],private limit:number,private onUpdate:(snapshot:BatchSnapshot)=>void){
  if(!input.csv||!input.assume||input.csv.length>16777216||variants.length<2||variants.length>MAX_VARIANTS||
     new Set(variants.map(v=>v.id)).size!==variants.length||variants.some(v=>!v.name.trim()||!v.graph.trim()||v.graph.length>65536)||
     !Number.isInteger(limit)||limit<1||limit>recommendedConcurrency())throw new Error("Invalid bounded batch configuration.");
  this.input={...input,settings:{...input.settings}};
  this.rows=variants.map(v=>({...v,status:"queued",progress:0}));
 }
 start(){if(this.started||this.disposed)return;this.started=true;this.startTime=performance.now();this.pump();}
 private snapshot():BatchSnapshot{
  const active=this.rows.filter(r=>r.status==="initializing"||r.status==="running").length;
  const finished=this.rows.every(r=>terminal(r.status));
  this.peak=Math.max(this.peak,active);
  this.elapsed=performance.now()-this.startTime;
  return {rows:this.rows.map(r=>({...r})),active,peak:this.peak,elapsedMs:this.elapsed,finished,limit:this.limit};
 }
 private emit(){
  if(this.disposed)return;
  const s=this.snapshot();
  if(s.finished)this.closeSlots();
  this.onUpdate(s);
 }
 private closeSlot(slot:Slot){
  window.clearTimeout(slot.timer);slot.worker.terminate();
  this.slots=this.slots.filter(s=>s!==slot);
 }
 private closeSlots(){for(const slot of [...this.slots])this.closeSlot(slot);}
 private pump(){
  if(this.disposed)return;
  while(this.rows.some(r=>r.status==="queued")){
   let slot=this.slots.find(s=>s.row===null);
   if(!slot&&this.slots.length>=this.limit)break;
   const row=this.rows.find(r=>r.status==="queued")!;
   try{
    if(!slot){slot={worker:new Worker(new URL("./browser-python-worker.js",document.baseURI)),row:null};this.slots.push(slot);}
    this.launch(slot,row);
   }catch(e){
    if(slot)this.closeSlot(slot);
    row.status="failed";row.error=String(e).slice(0,2000);
   }
  }
  this.emit();
 }
 private launch(slot:Slot,row:BatchRow){
  slot.row=row;row.status="initializing";
  const current=()=>!this.disposed&&slot.row===row&&!terminal(row.status)&&this.slots.includes(slot);
  const fail=(status:"failed"|"timed_out",message:string)=>{
   if(!current())return;
   row.status=status;row.error=message.slice(0,2000);this.closeSlot(slot);this.pump();
  };
  slot.worker.onmessage=e=>{
   const m=e.data;if(!current()||m.id!==row.id)return;
   if(m.status==="initializing")return;
   if(m.status==="running"){row.status="running";this.emit();return;}
   if(m.status==="progress"){if(Number.isFinite(m.progress))row.progress=Math.max(row.progress,Math.min(99,m.progress));this.emit();return;}
   if(m.status==="error"){fail("failed",String(m.message));return;}
   if(m.status==="done"){
    if(!m.result||typeof m.result.result_sha256!=="string"||!Array.isArray(m.result.scenarios)){fail("failed","Invalid result");return;}
    window.clearTimeout(slot.timer);slot.timer=undefined;
    row.result=m.result;row.elapsedMs=m.elapsed_ms;row.totalMs=m.total_ms;row.progress=100;row.status="completed";slot.row=null;this.pump();
   }
  };
  slot.worker.onerror=()=>fail("failed","Python worker failed. Verify runtime assets.");
  slot.worker.onmessageerror=()=>fail("failed","Worker result could not be decoded.");
  slot.timer=window.setTimeout(()=>fail("timed_out","Local run exceeded 120 seconds."),120000);
  slot.worker.postMessage({id:row.id,...this.input,graph:row.graph});
 }
 cancel(id:number){
  if(this.disposed)return;
  const row=this.rows.find(r=>r.id===id);if(!row||terminal(row.status))return;
  row.status="cancelled";
  const slot=this.slots.find(s=>s.row===row);if(slot)this.closeSlot(slot);
  this.pump();
 }
 cancelAll(){
  if(this.disposed)return;
  for(const row of this.rows)if(!terminal(row.status))row.status="cancelled";
  this.closeSlots();this.emit();
 }
 dispose(){this.disposed=true;this.closeSlots();}
}
