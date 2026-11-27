import {useEffect,useRef,useState} from "react";
import {recommendedConcurrency} from "./parallelReplay";
import type {BatchInput,LocalScenario} from "./parallelReplay";
import type {StudyRiskSnapshot} from "./LeveragedRunner";
type Test={test:string;leverage?:string;graph_sha256:string;result_sha256:string;worst_return_pct:string;max_drawdown_pct:string;min_trades:number;passed:boolean;failures:string[];scenarios:LocalScenario[]};
type Fold={study_sha256:string;fold_sha256:string;window:{fold:number;train_start:number;train_end:number;test_start:number;test_end:number};winner_graph_sha256:string|null;winner_parameters:Record<string,string>|null;modeled_checks_passed:boolean;training:{parameters:Record<string,string>;eligible:boolean;score:string|null;positive_month_ratio:string;max_drawdown_pct:string;rejections:string[]}[];tests:Test[];limitations:string[]};
type State={fold:number;status:string;progress:number;result?:Fold;error?:string};
const utc=(t:number)=>new Date(t*1000).toISOString().slice(0,16).replace("T"," ");
const num=(v:string|null)=>v===null?"—":Number(v).toFixed(3);
export function WalkForwardRunner({input,graph,disabled,onBusy,from,to,riskSnapshot}:{input:BatchInput;graph:string;disabled:boolean;onBusy:(v:boolean)=>void;from:string;to:string;riskSnapshot:StudyRiskSnapshot|null}){
 const [repository,setRepository]=useState(false),[leveraged,setLeveraged]=useState(false),[leverageValues,setLeverageValues]=useState("5,10"),[fundStress,setFundStress]=useState("2");
 const riskReady=!!riskSnapshot&&riskSnapshot.symbol===input.symbol&&(repository?riskSnapshot.risk.funding_provenance!=="estimated_previous_hour_mark_open":riskSnapshot.csv===input.csv&&!!riskSnapshot.mark);
 const [start,setStart]=useState(""),[train,setTrain]=useState("1440"),[test,setTest]=useState("720"),[folds,setFolds]=useState(2),[mode,setMode]=useState("rolling");
 const [axis,setAxis]=useState([{key:"stop_loss_pct",values:"0.5,1,2"}]),[method,setMethod]=useState("grid"),[samples,setSamples]=useState(3),[seed,setSeed]=useState(42),[objective,setObjective]=useState("net_return");
 const [dd,setDd]=useState("20"),[minimum,setMinimum]=useState(1),[minReturn,setMinReturn]=useState("0"),[fee,setFee]=useState("1.5"),[slip,setSlip]=useState("2"),[ack,setAck]=useState(false);
 const [limit,setLimit]=useState(recommendedConcurrency),[busy,setBusy]=useState(false),[rows,setRows]=useState<State[]>([]),[error,setError]=useState("");
 const workers=useRef(new Map<number,{worker:Worker;timer:number}>()),generation=useRef(0);
 function shutdown(){generation.current++;for(const w of workers.current.values()){window.clearTimeout(w.timer);w.worker.terminate();}workers.current.clear();}
 useEffect(()=>()=>shutdown(),[]);
 function cancel(){shutdown();setRows(old=>old.map(r=>r.status==="queued"||r.status==="running"?{...r,status:"cancelled"}:r));setBusy(false);onBusy(false);}
 function run(){
  if(disabled||busy)return;
  const begin=start.trim()?Number(start):(repository?Date.parse(from+"T00:00:00Z")/1000:Number(input.csv.split(/\r?\n/,2)[1]?.split(",")[0]));
  if(!Number.isSafeInteger(begin)||!Number.isSafeInteger(Number(train))||!Number.isSafeInteger(Number(test))){setError("Use UTC epoch seconds and integer window minutes.");return;}
  if(leveraged&&!riskReady){setError("Copy matching risk assumptions from leveraged replay first.");return;}
  const risk=leveraged&&riskSnapshot?{...riskSnapshot.risk,...(!repository?{mark_csv:riskSnapshot.mark}:{})}:undefined;
  const study={...(leveraged?{leverage_values:leverageValues.split(",").map(x=>x.trim()),funding_stress_multiplier:fundStress}:{}),start:begin,train_minutes:Number(train),test_minutes:Number(test),folds,mode,search:{method,axes:axis.map(a=>({key:a.key.trim(),values:a.values.split(",").map(s=>s.trim())})),samples,seed,objective:objective==="monthly_consistency"?"net_return":objective,max_drawdown_pct:dd,min_trades:minimum},objective,fee_multiplier:fee,extra_slippage_bps:slip,min_test_return_pct:minReturn,acknowledge:ack};
  const captured={...input,settings:{...input.settings}};const source=graph,archiveMode=repository;
  shutdown();const id=generation.current;setError("");setBusy(true);onBusy(true);
  const state:State[]=Array.from({length:folds},(_,i)=>({fold:i+1,status:"queued",progress:0}));
  function emit(){if(id===generation.current)setRows(state.map(s=>({...s})));}
  function pump(){
   if(id!==generation.current)return;
   while(workers.current.size<(archiveMode?1:Math.min(limit,recommendedConcurrency()))){
    const row=state.find(r=>r.status==="queued");if(!row)break;
    row.status="running";
    try{
     const worker=new Worker(new URL("./browser-python-worker.js",document.baseURI));
     const finish=(status:string,message?:string,result?:Fold)=>{
      if(id!==generation.current||row.status!=="running")return;
      const slot=workers.current.get(row.fold);if(slot){window.clearTimeout(slot.timer);slot.worker.terminate();workers.current.delete(row.fold);}
      row.status=status;row.error=message;row.result=result;if(result)row.progress=100;pump();
     };
     const timer=window.setTimeout(()=>finish("failed",archiveMode?"Repository fold exceeded 30 minutes; reduce study size.":"Fold exceeded 300 seconds; reduce the study size."),archiveMode?1800000:300000);
     workers.current.set(row.fold,{worker,timer});
     worker.onmessage=e=>{
      const m=e.data;if(id!==generation.current||m.id!==row.fold||row.status!=="running")return;
      if(m.status==="progress"){row.progress=m.progress;emit();}
      if(m.status==="error")finish("failed",String(m.message));
      if(m.status==="done"){if(m.result?.window?.fold!==row.fold||typeof m.result.fold_sha256!=="string")finish("failed","Invalid fold result");else finish("completed",undefined,m.result);}
     };
     worker.onerror=()=>finish("failed","Python worker failed.");
     worker.postMessage(archiveMode?{id:row.fold,action:"repository_study",from,to,symbol:captured.symbol,settings:captured.settings,assume:captured.assume,graph:source,study,fold:row.fold,...(risk?{risk}:{})}:{id:row.fold,...captured,graph:source,study,fold:row.fold,...(risk?{risk}:{})});
    }catch(e){const slot=workers.current.get(row.fold);if(slot){window.clearTimeout(slot.timer);slot.worker.terminate();workers.current.delete(row.fold);}row.status="failed";row.error=String(e);}
   }
   emit();if(state.every(r=>r.status!=="queued"&&r.status!=="running")){setBusy(false);onBusy(false);}
  }
  pump();
 }
 const completed=rows.filter(r=>r.status==="completed"),consistent=completed.length>0&&new Set(completed.map(r=>r.result?.study_sha256)).size===1;
 return <section className="scenario" style={{marginTop:16}} aria-label="Walk-forward research"><h2>Walk-forward optimization</h2><p className="notice">1× reference or explicit leveraged risk study, up to eight combined strategy/leverage candidates per fold, two to four chronological folds, 120,000 CSV candidate-minutes or 5 million repository candidate-minutes total (two OHLC paths each). Each fold selects on training only and tests fixed parameters on later candles. Monthly segments may be partial; no long-term profitability or overfitting guarantee.</p>
 <fieldset disabled={disabled||busy} style={{minWidth:0}}><label className="check"><input type="checkbox" checked={repository} onChange={e=>setRepository(e.target.checked)}/> Use repository historical data for long studies</label>{repository&&<p className="muted">Repository dates: {from} to {to} UTC. Blank start uses the first selected day. One worker at a time; up to 30 minutes per fold. Desktop recommended.</p>}<label className="check"><input type="checkbox" checked={leveraged} onChange={e=>{setLeveraged(e.target.checked);setAck(false);}}/> Enable leveraged walk-forward</label>{leveraged&&<><p className="notice">{riskReady?"Matching copied risk assumptions available.":"Copy matching risk assumptions from leveraged replay first."} Training and tests reject any liquidation or pre-liquidation halt. Both funding signs are stressed when enabled; use only historically supported margin assumptions. Strategy combinations × leverage candidates must not exceed eight.</p><label>Candidate leverages (1–100, comma separated)<input value={leverageValues} onChange={e=>setLeverageValues(e.target.value)}/></label><label>Funding stress multiplier<input value={fundStress} onChange={e=>setFundStress(e.target.value)}/></label>{riskSnapshot&&<details><summary>Copied risk assumptions</summary><pre style={{whiteSpace:"pre-wrap",overflowWrap:"anywhere"}}>{JSON.stringify({...riskSnapshot.risk,funding_csv:typeof riskSnapshot.risk.funding_csv==="string"?"[supplied CSV]":undefined},null,2)}</pre></details>}</>}<div className="visual-config">
 <label>Study start UTC epoch (blank = data start)<input value={start} onChange={e=>setStart(e.target.value)}/></label>
 <label>Training window minutes<input value={train} onChange={e=>setTrain(e.target.value)}/></label><label>Test window minutes<input value={test} onChange={e=>setTest(e.target.value)}/></label>
 <label>Walk-forward folds<select value={folds} onChange={e=>setFolds(Number(e.target.value))}>{[2,3,4].map(v=><option key={v}>{v}</option>)}</select></label>
 <label>Training window mode<select value={mode} onChange={e=>setMode(e.target.value)}><option>rolling</option><option>expanding</option></select></label>
 <label>Study concurrency<select disabled={repository} value={Math.min(limit,recommendedConcurrency())} onChange={e=>setLimit(Number(e.target.value))}>{Array.from({length:recommendedConcurrency()},(_,i)=><option key={i+1}>{i+1}</option>)}</select></label>
 <label>Search method<select value={method} onChange={e=>setMethod(e.target.value)}><option>grid</option><option>random</option></select></label>
 {method==="random"&&<><label>Study random samples<input type="number" min={2} max={8} value={samples} onChange={e=>setSamples(Number(e.target.value))}/></label><label>Study seed<input type="number" value={seed} onChange={e=>setSeed(Number(e.target.value))}/></label></>}
 <label>Training objective<select value={objective} onChange={e=>setObjective(e.target.value)}><option value="net_return">Worst-path return</option><option value="profit_factor">Worst-path profit factor</option><option value="win_rate">Worst-path win rate</option><option value="monthly_consistency">Monthly consistency (including partial segments)</option></select></label>
 <label>Study maximum drawdown %<input value={dd} onChange={e=>setDd(e.target.value)}/></label><label>Study minimum trades<input type="number" value={minimum} onChange={e=>setMinimum(Number(e.target.value))}/></label>
 <label>Minimum test return %<input value={minReturn} onChange={e=>setMinReturn(e.target.value)}/></label><label>Fee stress multiplier<input value={fee} onChange={e=>setFee(e.target.value)}/></label><label>Extra slippage bps<input value={slip} onChange={e=>setSlip(e.target.value)}/></label></div>
 {axis.map((a,i)=><div key={i} className="rule-group"><label>Study axis {i+1}<input value={a.key} onChange={e=>setAxis(old=>old.map((x,j)=>j===i?{...x,key:e.target.value}:x))}/></label><label>Study values {i+1}<input value={a.values} onChange={e=>setAxis(old=>old.map((x,j)=>j===i?{...x,values:e.target.value}:x))}/></label><button disabled={axis.length===1} onClick={()=>setAxis(old=>old.filter((_,j)=>j!==i))}>Remove study axis</button></div>)}
 <small>Visual axes: lock:long.locked_points, lock:short.locked_points, partial:long.pct, partial:short.pct, exit_machine:long.expiry_bars, exit_machine:short.expiry_bars, machine:long.expiry_bars, machine:short.expiry_bars, custom:formula1.lookback (declared formula name), sequence:long.expiry_bars, sequence:short.expiry_bars, exposure_pct, stop_loss_pct, take_profit_pct, ema.value@900:period, advanced:stop_points, advanced:target_points, advanced:confirmation_bars, advanced:cooldown_bars, advanced:trailing.activation, advanced:trailing.distance, advanced:trailing_percent.activation, advanced:trailing_percent.distance, advanced:trailing_atr.activation, advanced:trailing_atr.period, advanced:trailing_atr.multiplier, advanced:profit_lock.activation, advanced:profit_lock.locked (enabled controls only). Python axes: python:parameter_name for parameters declared with parameter(default, minimum, maximum).</small><button disabled={axis.length>=3} onClick={()=>setAxis(old=>[...old,{key:"take_profit_pct",values:"1,2"}])}>Add study axis</button>
 <label className="check"><input type="checkbox" checked={ack} onChange={e=>setAck(e.target.checked)}/> Acknowledge research-only chronological testing, independent balances and non-attested holdout.</label>
 <button className="primary" disabled={(!repository&&!input.csv)||(repository&&(!from||!to))||!input.assume||!ack||!graph.trim()||(leveraged&&(!riskReady||!leverageValues.trim()))} onClick={run}>Run walk-forward study</button></fieldset>
 {busy&&<button onClick={cancel}>Cancel walk-forward study</button>}{error&&<p role="alert" className="error">{error}</p>}
 {!!rows.length&&<><p role="status" aria-label="Walk-forward progress">{busy?"Study running":"Study finished"} · {completed.length}/{rows.length} completed</p>
 {!busy&&<p>{consistent&&completed.length===rows.length&&completed.every(r=>r.result?.modeled_checks_passed)?"All modeled checks passed (not production approval).":"Study incomplete or at least one modeled check not passed."}</p>}
 {rows.map(r=><article className="scenario" key={r.fold}><h3>Fold {r.fold}</h3><p aria-label={"Fold "+r.fold+" status"}>{r.status} · {r.progress}%</p>{r.error&&<p className="error">{r.error}</p>}{r.result&&<><p>Train {utc(r.result.window.train_start)} → {utc(r.result.window.train_end)} UTC; test {utc(r.result.window.test_start)} → {utc(r.result.window.test_end)} UTC.</p><p>Training winner: {r.result.winner_parameters?JSON.stringify(r.result.winner_parameters):"No eligible candidate"}</p>
 <p className="hash">Fold SHA-256: {r.result.fold_sha256}</p><details><summary>Training candidates</summary><div className="table-wrap"><table><thead><tr><th>Parameters</th><th>Score</th><th>Positive month ratio</th><th>DD %</th><th>Eligible</th></tr></thead><tbody>{r.result.training.map((t,i)=><tr key={i}><td>{JSON.stringify(t.parameters)}</td><td>{num(t.score)}</td><td>{num(t.positive_month_ratio)}</td><td>{num(t.max_drawdown_pct)}</td><td>{t.eligible?"yes":t.rejections.join(", ")}</td></tr>)}</tbody></table></div></details>
 <div className="table-wrap"><table><thead><tr><th>Test</th><th>Worst return %</th><th>Max DD %</th><th>Min trades</th><th>Checks</th></tr></thead><tbody>{r.result.tests.map(t=><tr key={t.test}><td>{t.test}{t.leverage?` (${t.leverage}×)`:""}</td><td>{num(t.worst_return_pct)}</td><td>{num(t.max_drawdown_pct)}</td><td>{t.min_trades}</td><td>{t.passed?"Pass":t.failures.join(", ")}</td></tr>)}</tbody></table></div></>}</article>)}</>}
 </section>;
}
