import {useEffect,useRef,useState} from "react";
import type {Diagnostic} from "./api";
type Parameter={name:string;kind:"integer"|"decimal";default:string;minimum:string;maximum:string;line:number};
export type SourceValidation={source_sha256:string;valid:boolean;kind:"python"|"visual";diagnostics:Diagnostic[];parameters:Parameter[];timeframes:number[];indicators:{name:string;timeframe:number;parameters:Record<string,unknown>}[]};
type Applied={source:string;validation:SourceValidation};
function request<T>(action:"validate_strategy"|"apply_parameters",source:string,values?:Record<string,string>):{promise:Promise<T>;cancel:()=>void}{
 const worker=new Worker(new URL("./browser-python-worker.js",document.baseURI));
 let timer:number|undefined,settled=false,rejectRequest:(e:Error)=>void=()=>{};
 const stop=()=>{window.clearTimeout(timer);worker.terminate();};
 const promise=new Promise<T>((resolve,reject)=>{
  rejectRequest=reject;
  function finish(error?:string,result?:T){if(settled)return;settled=true;stop();if(error)reject(Error(error));else resolve(result as T);}
  timer=window.setTimeout(()=>finish("Source validation exceeded 120 seconds."),120000);
  worker.onmessage=e=>{if(e.data.id!==1)return;if(e.data.status==="error")finish(String(e.data.message));else if(e.data.status==="done")finish(undefined,e.data.result);};
  worker.onerror=()=>finish("Local validation worker failed.");
  worker.postMessage({id:1,action,graph:source,values});
 });
 return {promise,cancel:()=>{if(!settled){settled=true;stop();rejectRequest(Error("Validation cancelled."));}}};
}
export function useStrategyValidation(source:string,onSource:(s:string)=>void){
 const [checked,setChecked]=useState<{source:string;result:SourceValidation}|null>(null),[busy,setBusy]=useState(false),[error,setError]=useState(""),[values,setValues]=useState<Record<string,string>>({});
 const pending=useRef<{cancel:()=>void}|null>(null),current=useRef(source);current.current=source;
 const generation=useRef(0);
 useEffect(()=>()=>{generation.current++;pending.current?.cancel();},[]);
 const valid=checked?.source===source?checked.result:null;
 function remember(s:string,r:SourceValidation){setChecked({source:s,result:r});setValues(Object.fromEntries(r.parameters.map(p=>[p.name,p.default])));}
 async function execute<T>(action:"validate_strategy"|"apply_parameters",s:string,changes?:Record<string,string>){
  pending.current?.cancel();const id=++generation.current;setBusy(true);setError("");
  try{const work=request<T>(action,s,changes);pending.current=work;const r=await work.promise;if(id!==generation.current||current.current!==s)throw Error("Source changed during validation; validate again.");return r;}
  catch(e){if(id===generation.current)setError(e instanceof Error?e.message:String(e));throw e;}
  finally{if(id===generation.current){setBusy(false);pending.current=null;}}
 }
 async function validate(){
  const s=source,r=await execute<SourceValidation>("validate_strategy",s);remember(s,r);return r;
 }
 async function apply(){
  const s=source,r=await execute<Applied>("apply_parameters",s,values);onSource(r.source);remember(r.source,r.validation);
 }
 return {valid,busy,error,values,setValues,validate,apply};
}
export function StrategyValidation({source,controller,disabled}:{source:string;controller:ReturnType<typeof useStrategyValidation>;disabled:boolean}){
 const {valid,busy,error,values,setValues,validate,apply}=controller;const locked=disabled||busy;
 return <section className="scenario" aria-label="Strategy source validation"><h3>Strategy validation and parameters</h3><p className="muted">Validate syntax, SDK compatibility, declarations and initialization locally. Callback logic is tested during replay; validation is not a profitability or safety certification.</p>
 <button disabled={locked||!source.trim()||new TextEncoder().encode(source).length>65536} onClick={()=>void validate().catch(()=>{})}>Validate strategy source</button>
 {busy&&<p role="status">Checking source…</p>}{error&&<p role="alert" className="error">{error}</p>}
 {valid&&<><p role="status">{valid.valid?"Source validation passed":"Source validation failed"}</p>
 {!valid.valid&&valid.diagnostics.map((d,i)=><p className="error" key={i}>Line {d.line}, column {d.column}: {d.message}</p>)}
 {valid.valid&&<><p>Mode: {valid.kind==="python"?"SDK Python":"Visual"} · Timeframes: {valid.timeframes.map(t=>t/60+"m").join(", ")}</p><details><summary>Declared indicators ({valid.indicators.length})</summary>{valid.indicators.map((v,i)=><p key={i}>{v.name} · {v.timeframe/60}m · {JSON.stringify(v.parameters)}</p>)}</details>
 {valid.parameters.length>0?<><div className="visual-config">{valid.parameters.map(p=><label key={p.name}>{p.name} ({p.minimum}–{p.maximum})<input aria-label={"Parameter "+p.name} value={values[p.name]??p.default} disabled={locked} onChange={e=>setValues(old=>({...old,[p.name]:e.target.value}))}/></label>)}</div><button disabled={locked} onClick={()=>void apply().catch(()=>{})}>Apply parameter values to source</button><small>Edits the declared defaults in your source, preserving all other trading logic and the exact saved version.</small></>:<p className="muted">No declared editable parameters. Python class fields can use parameter(default, minimum, maximum), with integer or Decimal literals.</p>}</>}
 </>}
 </section>;
}
