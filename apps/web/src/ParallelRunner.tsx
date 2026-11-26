import {useEffect,useRef,useState} from "react";
import {ParallelReplay,MAX_VARIANTS,recommendedConcurrency} from "./parallelReplay";
import type {BatchInput,BatchSnapshot,Variant} from "./parallelReplay";
const number=(v:string|number|null|undefined)=>v==null?"—":Number(v).toFixed(4);
export function ParallelRunner({input,graph,disabled,onBusy}:{input:BatchInput;graph:string;disabled:boolean;onBusy:(v:boolean)=>void}){
 const [variants,setVariants]=useState<Variant[]>([]),[limit,setLimit]=useState(recommendedConcurrency);
 const [snapshot,setSnapshot]=useState<BatchSnapshot|null>(null),[error,setError]=useState("");
 const [active,setActive]=useState(false);
 const seq=useRef(0),pool=useRef<ParallelReplay|null>(null);
 useEffect(()=>()=>{pool.current?.dispose();},[]);
 const cap=recommendedConcurrency();
 const locked=disabled||active;
 function edit(id:number,patch:Partial<Variant>){setVariants(old=>old.map(v=>v.id===id?{...v,...patch}:v));setSnapshot(null);}
 function add(){const id=++seq.current;setVariants(old=>[...old,{id,name:"Variant "+id,graph}]);setSnapshot(null);}
 function remove(id:number){setVariants(old=>old.filter(v=>v.id!==id));setSnapshot(null);}
 function start(){
  if(locked)return;
  setError("");setSnapshot(null);
  try{
   pool.current?.dispose();
   const p=new ParallelReplay(input,variants,Math.min(limit,cap),s=>{
    setSnapshot(s);
    if(s.finished){setActive(false);onBusy(false);}
   });
   pool.current=p;setActive(true);onBusy(true);p.start();
  }catch(e){pool.current?.dispose();setActive(false);onBusy(false);setError(String(e));}
 }
 const ready=!!input.csv&&input.assume&&variants.length>=2&&variants.every(v=>v.name.trim()&&v.graph.trim()&&v.graph.length<=65536);
 return <section className="scenario" aria-label="Parallel backtest batch" style={{marginTop:16}}>
 <div className="head"><h2>Parallel strategy backtests</h2><button disabled={locked||variants.length>=MAX_VARIANTS||!graph.trim()||graph.length>65536} onClick={add}>Add current strategy as variant</button></div>
 <p className="muted">Test up to {MAX_VARIANTS} independent strategy variants using the current CSV, instrument and account settings. Each variant is a separate 1× simulation, not a combined portfolio. Inputs are snapshotted when the batch starts.</p>
 <fieldset disabled={locked} style={{minWidth:0}}>
 <label>Concurrent workers<select aria-label="Concurrent workers" value={Math.min(limit,cap)} onChange={e=>setLimit(Number(e.target.value))}>{Array.from({length:cap},(_,i)=><option key={i+1} value={i+1}>{i+1}</option>)}</select></label>
 <small>Device-based cap: {cap}. Separate Python runtimes use additional memory; low-memory or unknown devices use one worker. No measured RAM guarantee.</small>
 {variants.map(v=><details key={v.id} className="visual-rule"><summary>{v.name}</summary>
 <label>Variant {v.id} name<input value={v.name} maxLength={80} onChange={e=>edit(v.id,{name:e.target.value})}/></label>
 <label>Variant {v.id} graph<textarea rows={8} aria-label={"Variant "+v.id+" graph"} value={v.graph} onChange={e=>edit(v.id,{graph:e.target.value})}/></label>
 <button onClick={()=>remove(v.id)}>Remove variant {v.id}</button></details>)}
 <button className="primary" disabled={!ready||locked} onClick={start}>Run strategy batch</button></fieldset>
 {active&&<button onClick={()=>pool.current?.cancelAll()}>Cancel entire batch</button>}
 {error&&<p role="alert" className="error">{error}</p>}
 {snapshot&&<>
 <p aria-label="Batch progress" role="status">{snapshot.finished?"Batch finished":"Batch running"} · {snapshot.active}/{snapshot.limit} active · peak {snapshot.peak} · {(snapshot.elapsedMs/1000).toFixed(2)} s elapsed</p>
 <div className="table-wrap"><table><thead><tr><th>Variant</th><th>Status</th><th>Progress</th><th>Worst-path net P&L</th><th>Drawdown %</th><th>Trades</th><th>Compute</th><th>Action</th></tr></thead><tbody>{snapshot.rows.map(r=>{
 const worst=r.result?.scenarios.find(s=>s.path===r.result?.worst_path);
 return <tr key={r.id} aria-label={"Batch variant "+r.id}><td>{r.name}</td><td>{r.status}</td><td><progress max={100} value={r.progress} aria-label={"Variant "+r.id+" progress"}/> {r.progress}%</td><td>{number(worst?.metrics.account_net)}</td><td>{number(worst?.metrics.max_event_drawdown_pct)}</td><td>{worst?.metrics.trades??"—"}</td><td>{r.elapsedMs===undefined?"—":(r.elapsedMs/1000).toFixed(3)+" s"}</td><td>{["queued","running","initializing"].includes(r.status)&&<button onClick={()=>pool.current?.cancel(r.id)}>Cancel variant {r.id}</button>}</td></tr>;
 })}</tbody></table></div>
 {snapshot.rows.map(r=><div key={r.id} style={{marginTop:8}}>{r.error&&<p className="error">{r.name}: {r.error}</p>}{r.result&&<details><summary>{r.name} result evidence</summary><p className="hash">Data SHA-256: {r.result.data_sha256}<br/>Graph SHA-256: {r.result.graph_sha256}<br/>Result SHA-256: {r.result.result_sha256}</p><div className="table-wrap"><table><thead><tr><th>Path</th><th>Net P&L</th><th>PF</th><th>Win rate %</th><th>Drawdown %</th></tr></thead><tbody>{r.result.scenarios.map(s=><tr key={s.path}><td>{s.path}</td><td>{number(s.metrics.account_net)}</td><td>{number(s.metrics.profit_factor)}</td><td>{number(s.metrics.win_rate_pct)}</td><td>{number(s.metrics.max_event_drawdown_pct)}</td></tr>)}</tbody></table></div></details>}</div>)}
 <p className="muted">Compare results from the captured batch inputs, not later edits. Completed variants remain visible after a failure or cancellation. No automatic strategy selection.</p>
 </>}
 </section>;
}
