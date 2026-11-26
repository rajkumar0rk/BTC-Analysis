import {useState,useRef} from "react";
import type {Api,Job,ValidationRequest,ValidationReport} from "./api";
const utc=(n:number)=>new Date(n*1000).toISOString();
export function ValidationPanel({api,job,open,refresh}:{api:Api;job:Job;open:(id:string)=>void;refresh:()=>Promise<void>}){
 const study=job.result!.optimization!;
 const [windows,setWindows]=useState([{start:"",end:""}]),[fee,setFee]=useState("1.5"),[slip,setSlip]=useState("2"),[ret,setRet]=useState("0"),[dd,setDd]=useState("20"),[trades,setTrades]=useState(1),[ack,setAck]=useState(false),[busy,setBusy]=useState(false),[error,setError]=useState("");
 const retry=useRef<{body:string;key:string}|null>(null);
 const parsed=windows.map(w=>({start:Date.parse(w.start+"Z")/1000,end:Date.parse(w.end+"Z")/1000}));
 const valid=ack&&parsed.every((w,i)=>Number.isFinite(w.start)&&Number.isFinite(w.end)&&w.start>=study.training_request.end&&w.end>w.start&&w.end-w.start<=86400&&(i===0||w.start>=parsed[i-1].end));
 async function run(){if(!valid)return;setBusy(true);setError("");const payload:ValidationRequest={optimization_job_id:job.id,optimization_result_sha256:job.result!.result_sha256,windows:parsed,fee_multiplier:fee,extra_slippage_bps:slip,min_return_pct:ret,max_drawdown_pct:dd,min_trades:trades,acknowledge_holdout:true};
 const body=JSON.stringify(payload);if(retry.current?.body!==body)retry.current={body,key:crypto.randomUUID()};
 try{const j=await api.validateStudy(payload,retry.current.key);retry.current=null;await refresh();open(j.id);}catch(e){setError(e instanceof Error?e.message:"Validation submission failed");}finally{setBusy(false);}}
 if(!study.winner_graph_sha256)return <p className="muted">Validation unavailable: no eligible training candidate.</p>;
 return <section className="panel"><h3>Validate fixed training winner</h3><p>Training ends {utc(study.training_request.end)}. Use one or two later, non-overlapping windows on the same snapshot. Each starts with fresh capital. No holdout selection or retraining.</p>
 {windows.map((w,i)=><div className="rule-group" key={i}><label>Holdout {i+1} start UTC<input type="datetime-local" value={w.start} disabled={busy} onChange={e=>setWindows(old=>old.map((x,j)=>j===i?{...x,start:e.target.value}:x))}/></label><label>Holdout {i+1} end UTC<input type="datetime-local" value={w.end} disabled={busy} onChange={e=>setWindows(old=>old.map((x,j)=>j===i?{...x,end:e.target.value}:x))}/></label>{i>0&&<button disabled={busy} onClick={()=>setWindows(old=>old.filter((_,j)=>j!==i))}>Remove window</button>}</div>)}
 <button disabled={busy||windows.length===2} onClick={()=>setWindows(old=>[...old,{start:"",end:""}])}>Add holdout window</button>
 <div className="visual-config"><label>Fee multiplier<input value={fee} onChange={e=>setFee(e.target.value)}/></label><label>Extra slippage (bps)<input value={slip} onChange={e=>setSlip(e.target.value)}/></label><label>Minimum return (%)<input value={ret} onChange={e=>setRet(e.target.value)}/></label><label>Maximum drawdown (%)<input value={dd} onChange={e=>setDd(e.target.value)}/></label><label>Minimum trades per path<input type="number" min={1} value={trades} onChange={e=>setTrades(Number(e.target.value))}/></label></div>
 <p className="muted">Each window: baseline, fee-only, slippage-only, combined stress, nearest training neighbor if available, and prefix fill comparison if aligned. 5,760 total replay-minute limit. Funding and liquidation untested.</p>
 <label className="check"><input type="checkbox" checked={ack} onChange={e=>setAck(e.target.checked)}/> I acknowledge this holdout is research only; prior inspection is not independently verified.</label>
 {error&&<p className="error" role="alert">{error}</p>}<button className="primary" disabled={!valid||busy} onClick={()=>void run()}>Run robustness validation</button></section>;
}
export function ValidationResults({report:r}:{report:ValidationReport}){
 return <section><h3>Robustness validation report</h3><p className="notice">{r.modeled_checks_passed?"All executed modeled checks passed":"One or more modeled checks failed"}. Not production approval.</p><p>Training: {utc(r.training_start)} to {utc(r.training_end)} · {r.timestamp_label_verified?"Verified timestamp convention":"Assumed candle-open convention"}</p><p className="hash">Fixed candidate: {r.winner_graph_sha256}</p>
 <div className="table-wrap"><table><thead><tr><th>Window</th><th>Test</th><th>Worst return %</th><th>Max DD %</th><th>Min trades</th><th>Status</th><th>Evidence</th></tr></thead><tbody>{r.rows.map(x=><tr key={x.window+":"+x.test}><td>{x.window}<small>{utc(x.start)}–{utc(x.end)}</small></td><td>{x.test}</td><td>{x.worst_return_pct??"—"}</td><td>{x.max_drawdown_pct??"—"}</td><td>{x.min_closed_trades??"—"}</td><td>{x.passed?"Pass":x.failures.join(", ")}</td><td><details><summary>Inspect</summary><p className="hash">{x.result_sha256}</p><pre>{JSON.stringify(x.scenarios??{},null,2)}</pre></details></td></tr>)}</tbody></table></div>
 <h3>Not assessed</h3><ul>{r.not_assessed.map(x=><li key={x}>{x}</li>)}</ul><p className="hash">Training result: {r.training_result_sha256}</p></section>;
}
