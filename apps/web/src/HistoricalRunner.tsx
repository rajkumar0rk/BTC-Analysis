import {useEffect,useState,useRef} from "react";
import type {Api,Dataset,Historical,Strategy} from "./api";
export function HistoricalRunner({api,strategies,open,refresh,report}:{api:Api;strategies:Strategy[];open:(id:string)=>void;refresh:()=>Promise<void>;report:(e:unknown)=>void}){
 const [datasets,setDatasets]=useState<Dataset[]>([]),[symbol,setSymbol]=useState<Dataset["symbol"]>("BTCUSD"),[sid,setSid]=useState(""),[version,setVersion]=useState(1);
 const [start,setStart]=useState(""),[end,setEnd]=useState(""),[warm,setWarm]=useState(0),[assume,setAssume]=useState(false),[ack,setAck]=useState(false),[busy,setBusy]=useState(false);
 const [settings,setSettings]=useState({initial_equity:"100",maker_bps:"2",taker_bps:"5",tax_rate:"0.18",slippage_bps:"0",tick_size:"0.1",lot_size:"0.001",multiplier:"1"});
 const retry=useRef<{body:string;key:string}|null>(null);
 useEffect(()=>{let live=true;api.datasets().then(x=>{if(live){setDatasets(x);if(x.length)setSymbol(x[0].symbol);}}).catch(report);return()=>{live=false;};},[api]);
 const dataset=datasets.find(d=>d.symbol===symbol),strategy=strategies.find(s=>s.id===sid);
 const epoch=(v:string)=>Date.parse(v+"Z")/1000,lo=epoch(start),hi=epoch(end);
 const valid=!!dataset&&!!strategy&&!strategy.archived&&(strategy.frozen_version===null||version===strategy.frozen_version)&&version<=strategy.latest_version&&Number.isFinite(lo)&&Number.isFinite(hi)&&hi>lo&&hi-lo<=86400&&lo-warm*60>=dataset.start&&hi<=dataset.end&&Number.isInteger(warm)&&warm>=0&&warm<=1440&&ack&&(dataset.timestamp_label_verified||assume);
 async function run(e:React.FormEvent){e.preventDefault();if(!valid||!dataset||!strategy)return;setBusy(true);
 const payload:Historical={kind:"historical_visual",strategy_id:sid,version,symbol,manifest_sha256:dataset.manifest_sha256,start:lo,end:hi,warmup_minutes:warm,...settings,assume_open:assume,acknowledge_reference:true};
 const body=JSON.stringify(payload);if(retry.current?.body!==body)retry.current={body,key:crypto.randomUUID()};
 try{const job=await api.historical(payload,retry.current.key);retry.current=null;await refresh();open(job.id);}catch(e){report(e);}finally{setBusy(false);}
 }
 return <section className="panel"><h2>Historical visual backtest</h2><p className="notice">Research only: 1× linear reference simulation. Maximum 24 hours per job; no funding, spread or liquidation. Only intact visual revisions are accepted.</p>
 {!datasets.length?<p className="muted">No configured historical snapshots. Import the archive and configure the local service.</p>:<form onSubmit={run}>
 <label>Saved strategy<select value={sid} onChange={e=>{setSid(e.target.value);const s=strategies.find(s=>s.id===e.target.value);setVersion(s?.frozen_version??s?.latest_version??1);}}><option value="">Select strategy</option>{strategies.filter(s=>!s.archived).map(s=><option key={s.id} value={s.id}>{s.name}</option>)}</select></label>
 <label>Version<select value={version} onChange={e=>setVersion(Number(e.target.value))}>{(strategy?.frozen_version!=null?[strategy.frozen_version]:Array.from({length:strategy?.latest_version??1},(_,i)=>i+1)).map(v=><option key={v}>{v}</option>)}</select></label>
 <label>Instrument<select value={symbol} onChange={e=>{setSymbol(e.target.value as Dataset["symbol"]);setAssume(false);}}>{datasets.map(d=><option key={d.symbol}>{d.symbol}</option>)}</select></label>
 {dataset&&<p className="muted hash">Snapshot: {dataset.manifest_sha256}<br/>Available: {new Date(dataset.start*1000).toISOString()} to {new Date(dataset.end*1000).toISOString()} (exclusive)</p>}
 <div className="visual-config"><label>Start UTC<input type="datetime-local" required value={start} onChange={e=>setStart(e.target.value)}/></label><label>End UTC (exclusive)<input type="datetime-local" required value={end} onChange={e=>setEnd(e.target.value)}/></label><label>Warmup minutes<input type="number" min={0} max={1440} value={warm} onChange={e=>setWarm(Number(e.target.value))}/></label></div>
 <p className="muted">Dates must align with every declared strategy timeframe. Execution must be 1 minute.</p>
 <div className="visual-config">{Object.entries(settings).map(([k,v])=><label key={k}>{({initial_equity:"Capital USD",maker_bps:"Maker fee (bps)",taker_bps:"Taker fee (bps)",tax_rate:"Tax fraction",slippage_bps:"Slippage (bps)",tick_size:"Assumed tick size",lot_size:"Assumed lot size",multiplier:"Assumed contract multiplier"} as Record<string,string>)[k]}<input required value={v} onChange={e=>setSettings(s=>({...s,[k]:e.target.value}))}/></label>)}</div>
 {dataset&&!dataset.timestamp_label_verified&&<label className="check"><input type="checkbox" checked={assume} onChange={e=>setAssume(e.target.checked)}/> Explicitly assume raw timestamps are candle opens (unverified).</label>}
 <label className="check"><input type="checkbox" checked={ack} onChange={e=>setAck(e.target.checked)}/> I accept the reference cost and contract assumptions, omitted funding/liquidation, and entry-candle protection limitation.</label>
 <button className="primary" disabled={!valid||busy}>Run historical visual strategy</button></form>}</section>;
}
