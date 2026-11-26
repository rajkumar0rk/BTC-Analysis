import {useEffect,useState} from "react";
import {comparable,MAX_RUNS} from "./runHistory";
import type {RunRecord} from "./runHistory";
const fmt=(v:unknown)=>v==null||!Number.isFinite(Number(v))?"—":Number(v).toFixed(4);
const delta=(a:unknown,b:unknown)=>a==null||b==null||!Number.isFinite(Number(a))||!Number.isFinite(Number(b))?null:Number(b)-Number(a);
export function RunComparison({runs,disabled,savedIds,note,save,remove,clear,restore}:{runs:RunRecord[];disabled:boolean;savedIds:Set<string>;note:string;save:()=>void;remove:(id:string)=>void;clear:()=>void;restore:(r:RunRecord)=>void}){
 const [baseline,setBaseline]=useState(""),[candidate,setCandidate]=useState(""),[path,setPath]=useState("O-H-L-C");
 const [confirmClear,setConfirmClear]=useState(false);
 useEffect(()=>{
  setCandidate(old=>runs.some(r=>r.id===old)?old:runs[0]?.id??"");
  setBaseline(old=>runs.some(r=>r.id===old)?old:runs[1]?.id??"");
 },[runs]);
 const a=runs.find(r=>r.id===baseline),b=runs.find(r=>r.id===candidate);
 const aligned=!!a&&!!b&&comparable(a,b);
 const sa=a?.result.scenarios.find(s=>s.path===path),sb=b?.result.scenarios.find(s=>s.path===path);
 const months=[...new Set([...(sa?.monthly??[]).map(m=>m.month),...(sb?.monthly??[]).map(m=>m.month)])].sort();
 const label=(r:RunRecord)=>r.name+" · "+new Date(r.created).toLocaleString()+" · "+r.result.graph_sha256.slice(0,8);
 const metrics=[["Net P&L","account_net",1],["Return %","account_return_pct",1],["Drawdown %","max_event_drawdown_pct",-1],["Profit factor","profit_factor",1],["Win rate %","win_rate_pct",1],["Closed trades","trades",0],["Profitable months","positive_months",1]] as const;
 return <section className="scenario" style={{marginTop:16}} aria-label="Local experiment history">
 <div className="head"><h2>Experiment history &amp; comparison</h2><button disabled={disabled||!runs.length} onClick={save}>Save experiment history on this device</button></div>
 <p className="muted">Every completed run captures its exact source, costs, dataset hash and results. Up to {MAX_RUNS} newest runs. Saving is optional; nothing is uploaded. Saved source is visible to scripts on this origin. {note}</p>
 {runs.length===0?<p>No completed experiments yet.</p>:<>
 <div className="table-wrap"><table><thead><tr><th>Experiment</th><th>Instrument</th><th>Graph version</th><th>Worst path P&amp;L</th><th>Storage</th><th>Action</th></tr></thead><tbody>{runs.map(r=><tr key={r.id}><td>{r.name}<small>{new Date(r.created).toLocaleString()}</small></td><td>{r.symbol}</td><td className="hash">{r.result.graph_sha256.slice(0,12)}</td><td>{fmt(r.result.scenarios.find(s=>s.path===r.result.worst_path)?.metrics.account_net)}</td><td>{savedIds.has(r.id)?"Saved":"Session"}</td><td><button disabled={disabled} onClick={()=>restore(r)}>Restore inputs</button> <button disabled={disabled} onClick={()=>remove(r.id)}>Remove</button></td></tr>)}</tbody></table></div>
 <div className="visual-config"><label>Baseline experiment<select aria-label="Baseline experiment" value={baseline} onChange={e=>setBaseline(e.target.value)}><option value="">Select baseline</option>{runs.map(r=><option key={r.id} value={r.id}>{label(r)}</option>)}</select></label><label>Candidate experiment<select aria-label="Candidate experiment" value={candidate} onChange={e=>setCandidate(e.target.value)}><option value="">Select candidate</option>{runs.map(r=><option key={r.id} value={r.id}>{label(r)}</option>)}</select></label><label>Comparison path<select value={path} onChange={e=>setPath(e.target.value)}><option>O-H-L-C</option><option>O-L-H-C</option></select></label></div>
 <button disabled={runs.length<2} onClick={()=>{setBaseline(runs[1]?.id??"");setCandidate(runs[0]?.id??"");}}>Compare latest two runs</button>
 {a&&b&&sa&&sb&&<><h3>Strategy result comparison</h3><p aria-label="Comparison validity" className={aligned?"muted":"notice"}>{aligned?"Comparable: identical dataset, instrument, engine and account settings.":"Different dataset, instrument, engine or account settings. Results shown for reference; improvement deltas suppressed."}</p>
 <div className="table-wrap"><table><thead><tr><th>Metric</th><th>Baseline</th><th>Candidate</th><th>Change</th></tr></thead><tbody>{metrics.map(([name,key,direction])=>{
 const d=aligned?delta(sa.metrics[key],sb.metrics[key]):null;const meaning=d===null||direction===0||d===0?"":d*direction>0?" · improved":" · deteriorated";
 return <tr key={key}><td>{name}</td><td>{fmt(sa.metrics[key])}</td><td>{fmt(sb.metrics[key])}</td><td>{d===null?"—":(d>0?"+":"")+fmt(d)+meaning}</td></tr>;
 })}</tbody></table></div><h3>Monthly P&amp;L comparison</h3><div className="table-wrap"><table><thead><tr><th>Month</th><th>Baseline</th><th>Candidate</th><th>Change</th></tr></thead><tbody>{months.map(m=>{
 const x=sa.monthly.find(v=>v.month===m)?.pnl,y=sb.monthly.find(v=>v.month===m)?.pnl,d=aligned?delta(x,y):null;return <tr key={m}><td>{m}</td><td>{fmt(x)}</td><td>{fmt(y)}</td><td>{fmt(d)}</td></tr>;
 })}</tbody></table></div>
 <details><summary>Exact input versions and provenance</summary><p className="hash">Baseline graph: {a.result.graph_sha256}<br/>Candidate graph: {b.result.graph_sha256}<br/>Baseline dataset: {a.result.data_sha256}<br/>Candidate dataset: {b.result.data_sha256}<br/>Baseline result: {a.result.result_sha256}<br/>Candidate result: {b.result.result_sha256}</p><div className="scenarios"><div><h3>Baseline source</h3><pre style={{whiteSpace:"pre-wrap",overflowWrap:"anywhere"}}>{a.graph}</pre></div><div><h3>Candidate source</h3><pre style={{whiteSpace:"pre-wrap",overflowWrap:"anywhere"}}>{b.graph}</pre></div></div></details></>}
 <button disabled={disabled} onClick={()=>setConfirmClear(v=>!v)}>Clear experiment history</button>{confirmClear&&<><p>This removes saved and session experiments, not your historical CSV or server strategies.</p><button disabled={disabled} onClick={()=>{setConfirmClear(false);clear();}}>Confirm clear experiments</button><button onClick={()=>setConfirmClear(false)}>Keep experiments</button></>}
 </>}
 </section>;
}
