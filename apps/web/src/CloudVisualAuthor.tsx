import {useEffect,useRef,useState} from "react";
import {FrameSelect,RuleEdit,AdvancedVisualControls} from "./VisualBuilder";
import {initialGraph,keys} from "./visualTypes";
import type {Graph,Compiled} from "./visualTypes";
import type {Catalog} from "./api";

export function CloudVisualAuthor({disabled,onSource}:{disabled:boolean;onSource:(source:string)=>void}){
 const [graph,setGraph]=useState<Graph>(initialGraph),[catalog,setCatalog]=useState<Catalog|null>(null),[busy,setBusy]=useState(false),[error,setError]=useState("");
 const slot=useRef<{worker:Worker;timer:number}|null>(null);
 function stop(){if(slot.current){window.clearTimeout(slot.current.timer);slot.current.worker.terminate();slot.current=null;}}
 function request(action:string,callback:(x:unknown)=>void){
  stop();setBusy(true);setError("");
  try{
   const worker=new Worker(new URL("./browser-python-worker.js",document.baseURI));
   const finish=(e?:string)=>{stop();setBusy(false);if(e)setError(e);};
   const timer=window.setTimeout(()=>finish("Visual builder worker timed out."),120000);
   slot.current={worker,timer};
   worker.onmessage=e=>{if(e.data.id!==1)return;if(e.data.status==="error")finish(String(e.data.message));if(e.data.status==="done"){try{callback(e.data.result);finish();}catch(err){finish(String(err));}}};
   worker.onerror=()=>finish("Visual builder worker failed.");
   worker.postMessage({id:1,action,graph:JSON.stringify(graph)});
  }catch(e){stop();setBusy(false);setError(String(e));}
 }
 useEffect(()=>{request("visual_catalog",x=>setCatalog(x as Catalog));return stop;},[]);
 const locked=disabled||busy;
 return <section className="scenario" aria-label="Cloud visual authoring"><h3>Visual strategy builder</h3><p>Build conditions visually, then generate source for the same Cloud library. No Python knowledge required.</p>
 <fieldset disabled={locked}><div className="visual-config"><FrameSelect label="Signal timeframe" value={graph.signal_timeframe} disabled={locked} change={v=>setGraph(g=>({...g,signal_timeframe:v}))}/>
 {(["exposure_pct","stop_loss_pct","take_profit_pct"] as const).map((k,i)=><label key={k}>{["Exposure %","Stop loss %","Take profit %"][i]}<input value={graph[k]} onChange={e=>setGraph(g=>({...g,[k]:e.target.value}))}/></label>)}</div>
 <AdvancedVisualControls graph={graph} change={setGraph} disabled={locked}/><p className="muted">Visual strategies use 1m execution. {graph.advanced?.exit_mode==="points"?"Fixed-point protection starts on the entry minute; percentage fields are inactive.":"Percentage protection starts after the entry candle."}</p>
 {catalog&&keys.map(k=><RuleEdit key={k} title={k.replaceAll("_"," ")} rule={graph[k]} change={v=>setGraph(g=>({...g,[k]:v}))} catalog={catalog} disabled={locked}/>)}
 <button disabled={!catalog||locked} onClick={()=>request("compile_visual",x=>{const result=x as Compiled;if(typeof result.source!=="string")throw Error("Invalid compiler response");onSource(result.source);})}>Generate visual strategy source</button></fieldset>
 {busy&&<p role="status">Loading local Python compiler…</p>}{error&&<p role="alert" className="error">{error}</p>}
 </section>;
}
