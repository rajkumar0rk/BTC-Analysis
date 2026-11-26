import {useState,useEffect,useMemo,useRef} from "react";
import type {FormEvent} from "react";
import {createRoot} from "react-dom/client";
import {client,ApiError} from "./api";
import type {Api,Capabilities,Job,Strategy,Revision,Fixture,Scenario,Catalog,Validation} from "./api";
import {PythonEditor} from "./PythonEditor";
import {VisualBuilder} from "./VisualBuilder";
import {HistoricalRunner} from "./HistoricalRunner";
import {TradeAnalytics} from "./TradeAnalytics";
import {RegistryPanel} from "./RegistryPanel";
import {OptimizationResults} from "./OptimizationResults";
import {ValidationPanel,ValidationResults} from "./ValidationPanel";
import {PaperTrading} from "./PaperTrading";
import {MarketCatalog} from "./MarketCatalog";
import {BrowserRunner} from "./BrowserRunner";
import "./style.css";
const pages=["Overview","Strategy library","Visual builder","Backtest runner","Job history","Paper trading","Markets","Settings"] as const;
type Page=typeof pages[number];
const active=(j:Job)=>["queued","running","cancelling"].includes(j.status);
const err=(e:unknown)=>e instanceof Error?e.message:"Request failed";
const fmt=(v:string|null)=>v===null?"—":Number(v).toFixed(2);
const starter="from btc_analysis.strategy import PythonStrategy\n\nclass MyStrategy(PythonStrategy):\n    def on_signal(self, ctx):\n        pass\n";
function App(){
 const [local,setLocal]=useState(false);const [token,setToken]=useState("");const [session,setSession]=useState<{token:string;caps:Capabilities}|null>(null);
 const [error,setError]=useState("");const [busy,setBusy]=useState(false);
 async function login(e:FormEvent){e.preventDefault();setBusy(true);setError("");try{const t=token.trim();setSession({token:t,caps:await client(t).capabilities()});setToken("");}catch(e){setError(err(e));}finally{setBusy(false);}}
 if(local)return <main className="panel"><button onClick={()=>setLocal(false)}>Back to sign in</button><BrowserRunner/></main>;
 if(session)return <Studio token={session.token} caps={session.caps} logout={()=>setSession(null)}/>;
 return <main className="login"><section className="panel login-card"><div className="eyebrow">BTC ANALYSIS / RESEARCH</div><h1>Strategy Studio</h1><p>Connect to your local service. Credentials stay in this tab's memory.</p><form onSubmit={login}><label htmlFor="token">API access token</label><input id="token" type="password" autoComplete="off" minLength={32} required value={token} onChange={e=>setToken(e.target.value)}/>{error&&<p role="alert" className="error">{error}</p>}<button className="primary" disabled={busy}>Connect</button></form><button onClick={()=>setLocal(true)}>Open local Python runner</button><p className="muted">Local runner requires no API token. Custom handwritten Python execution remains disabled.</p><a href="https://rajkumar0rk.github.io/BTC-Analysis/" rel="noreferrer">Existing research dashboard</a></section></main>;
}
function Studio({token,caps,logout}:{token:string;caps:Capabilities;logout:()=>void}){
 const api=useMemo(()=>client(token),[token]);
 const [page,setPage]=useState<Page>("Overview");const [jobs,setJobs]=useState<Job[]>([]);const [strategies,setStrategies]=useState<Strategy[]>([]);
 const [pythonRevision,setPythonRevision]=useState<Revision|null>(null);
 const [selected,setSelected]=useState("");const [error,setError]=useState("");const [ready,setReady]=useState(false);
 const generation=useRef(0);const mounted=useRef(true);
 function report(e:unknown){if(!mounted.current)return;if(e instanceof ApiError&&e.status===401){logout();return;}setError(err(e));}
 async function refresh(){const n=++generation.current;try{const [j,s]=await Promise.all([api.jobs(),api.strategies()]);if(mounted.current&&generation.current===n){setJobs(j);setStrategies(s);setReady(true);}}catch(e){if(generation.current===n)report(e);}}
 useEffect(()=>{mounted.current=true;let stopped=false;let timer:number;async function poll(){await refresh();if(!stopped)timer=window.setTimeout(poll,2500);}void poll();return()=>{mounted.current=false;stopped=true;generation.current++;window.clearTimeout(timer);};},[api]);
 function open(id:string){setSelected(id);setPage("Job history");}
 function nav(p:Page){setError("");setPythonRevision(null);setPage(p);}
 return <div className="shell"><a className="skip" href="#main">Skip to content</a><aside><div className="brand"><span className="mark">B</span><div><strong>BTC Analysis</strong><small>Strategy Studio</small></div></div><nav aria-label="Primary navigation">{pages.map((p,i)=><button key={p} aria-current={page===p?"page":undefined} className={page===p?"nav active":"nav"} onClick={()=>nav(p)}><span aria-hidden="true">{["◈","▤","◇","▷","◷","◎","▦","⚙"][i]}</span>{p}</button>)}</nav><div className="bottom"><a href="https://rajkumar0rk.github.io/BTC-Analysis/" target="_blank" rel="noreferrer">Research archive ↗</a><button onClick={logout}>Disconnect</button></div></aside>
 <main id="main" tabIndex={-1}><header><div><div className="eyebrow">RESEARCH WORKSPACE</div><h1>{page}</h1></div><span className="muted">{error?"Service issue":ready?"● API connected":"Connecting…"}</span></header>
 <div className="notice"><strong>Reference environment.</strong> {caps.historical_runs?"Historical visual research and synthetic fixtures available.":"Only synthetic fixtures can run."} Saved arbitrary Python source is inert. No live orders.</div>
 {error&&<div role="alert" className="error">{error} <button onClick={()=>{setError("");void refresh();}}>Retry</button></div>}
 {page==="Overview"&&<><div className="metrics">{[["Saved strategies",strategies.length],["Active jobs",jobs.filter(active).length],["Successful jobs",jobs.filter(j=>j.status==="succeeded").length],["Worker capacity",caps.worker_concurrency]].map(([label,v])=><section className="panel metric" key={label}><span className="muted">{label}</span><strong>{ready?v:"—"}</strong></section>)}</div><section className="panel"><div className="head"><h2>Recent jobs</h2><button className="primary" onClick={()=>nav("Backtest runner")}>New reference run</button></div><Jobs jobs={jobs.slice(0,6)} open={open}/></section></>}
 {page==="Strategy library"&&<Library key={pythonRevision?.id??"library"} initial={pythonRevision} api={api} strategies={strategies} refresh={refresh} report={report} openJob={open}/>}
 {page==="Visual builder"&&<VisualBuilder api={api} strategies={strategies} refresh={refresh} report={report} openPython={r=>{setPythonRevision(r);setPage("Strategy library");}}/>}
 {page==="Backtest runner"&&<><BrowserRunner api={api} strategies={strategies}/><HistoricalRunner api={api} strategies={strategies} open={open} refresh={refresh} report={report}/><Runner api={api} caps={caps} open={open} refresh={refresh} report={report}/></>}
 {page==="Job history"&&<><section className="panel"><div className="head"><h2>Job history</h2><button onClick={()=>void refresh()}>Refresh</button></div><Jobs jobs={jobs} open={open}/></section>{selected&&<Detail key={selected} api={api} id={selected} refresh={refresh} report={report} open={open}/>}</>}
 {page==="Paper trading"&&<PaperTrading api={api} strategies={strategies}/>}
 {page==="Markets"&&<MarketCatalog api={api}/>}
 {page==="Settings"&&<section className="panel"><h2>Service capabilities</h2><dl>{[["Strategy storage",caps.strategy_storage?"Available":"Disabled"],["Custom Python execution",caps.custom_python_execution?"Available":"Disabled"],["Historical jobs",caps.historical_runs?"Available":"Disabled"],["Worker concurrency",caps.worker_concurrency],["Fixture limit",caps.fixture_max_bars],["Authentication","In-memory token"]].map(([k,v])=><div key={k}><dt>{k}</dt><dd>{v}</dd></div>)}</dl></section>}
 </main></div>;
}
function Jobs({jobs,open}:{jobs:Job[];open:(id:string)=>void}){
 return jobs.length?<div className="table-wrap"><table><thead><tr><th>Job</th><th>Status</th><th>Progress</th><th>Submitted</th><th>Details</th></tr></thead><tbody>{jobs.map(j=><tr key={j.id}><td>{j.request.kind==="reference_fixture"?"Synthetic fixture":j.request.symbol+(j.request.kind==="optimization"?" parameter search":j.request.kind==="validation"?" robustness validation":" historical visual")}<small>{j.request.kind==="reference_fixture"?j.request.bars+" bars · "+j.request.signal_minutes+"m":new Date(j.request.start*1000).toISOString().slice(0,16)+" UTC"} · {j.id.slice(0,8)}</small></td><td><span className={"status "+j.status}>{j.status}</span></td><td><progress value={j.progress} max={100} aria-label="Job progress"/> {j.progress}%</td><td>{new Date(j.created*1000).toLocaleString()}</td><td><button onClick={()=>open(j.id)}>Inspect</button></td></tr>)}</tbody></table></div>:<p className="muted">No jobs to display.</p>;
}
function Library({api,strategies,refresh,report,initial,openJob}:{initial:Revision|null;api:Api;strategies:Strategy[];refresh:()=>Promise<void>;report:(e:unknown)=>void;openJob:(id:string)=>void}){
 const [r,setR]=useState<Revision|null>(initial);const [name,setName]=useState(initial?.name??"");const [source,setSource]=useState(initial?.source??starter);
 const [busy,setBusy]=useState(false);const [note,setNote]=useState("");const [validation,setValidation]=useState<Validation|null>(null);
 const [catalog,setCatalog]=useState<Catalog|null>(null);
 const current=strategies.find(s=>s.id===r?.id);
 const latest=Math.max(r?.version??1,current?.latest_version??1);
 const [showArchived,setShowArchived]=useState(false);
 const bytes=new TextEncoder().encode(source).length;
 const readOnly=busy||!!r&&(r.version!==latest||(current??r).archived||(current??r).frozen_version!==null);
 useEffect(()=>{let alive=true;api.catalog().then(c=>{if(alive)setCatalog(c);}).catch(e=>{if(alive)report(e);});return()=>{alive=false;};},[api]);
 function edit(v:string){setSource(v);setValidation(null);setNote("");}
 async function load(id:string,v:number){setBusy(true);setNote("");setValidation(null);try{const x=await api.revision(id,v);setR(x);setName(x.name);setSource(x.source);}catch(e){report(e);}finally{setBusy(false);}}
 async function check(){setBusy(true);setValidation(null);setNote("");try{setValidation(await api.validate(source));}catch(e){report(e);}finally{setBusy(false);}}
 async function save(e:FormEvent){e.preventDefault();setBusy(true);setNote("");setValidation(null);
  try{const v=await api.validate(source);setValidation(v);if(!v.syntax_valid)return;
   const x=r?await api.save(r.id,r.version,source):await api.create(name.trim(),source);setR(x);
   setNote("Saved immutable version "+x.version+".");await refresh();
  }catch(e){report(e);}finally{setBusy(false);}}
 const canCheck=!busy&&bytes>0&&bytes<=65536&&source.trim().length>0;
 return <><div className="split"><section className="panel"><div className="head"><h2>Strategies</h2><button disabled={busy} onClick={()=>{setR(null);setName("");edit(starter);}}>New</button></div>
 <label className="check"><input type="checkbox" checked={showArchived} onChange={e=>setShowArchived(e.target.checked)}/> Show archived strategies</label>
 {strategies.filter(s=>showArchived||!s.archived).map(s=><button className="strategy" key={s.id} disabled={busy} onClick={()=>void load(s.id,s.latest_version)}>{s.name}<small>Version {s.latest_version}{s.archived?" · Archived":s.frozen_version!==null?" · Frozen":""}</small></button>)}
 <details><summary>SDK indicator catalog</summary>{catalog?<div className="catalog">{catalog.indicators.map(i=><div key={i.name}><strong>{i.name}</strong><small>{i.outputs.join(" · ")}</small><small>{Object.entries(i.defaults).map(([k,v])=>k+"="+v).join(", ")}</small></div>)}</div>:<p className="muted">Catalog unavailable.</p>}</details></section>
 <section className="panel"><h2>{r?"Strategy version":"New strategy"}</h2><p className="muted">Python syntax checking and immutable source storage. Custom execution is disabled.</p>
 {r&&<><label htmlFor="version">View version</label><select id="version" value={r.version} disabled={busy} onChange={e=>void load(r.id,Number(e.target.value))}>{Array.from({length:latest},(_,i)=><option key={i+1}>{i+1}</option>)}</select></>}
 <form onSubmit={save}><label htmlFor="name">Name</label><input id="name" required maxLength={100} disabled={busy||!!r} value={name} onChange={e=>setName(e.target.value)}/>
 <PythonEditor value={source} onChange={edit} readOnly={readOnly} diagnostics={validation?.diagnostics??[]} catalog={catalog}/>
 <div className="head"><span className="muted">{bytes.toLocaleString()} / 65,536 bytes</span><button type="button" disabled={!canCheck} onClick={()=>void check()}>Validate syntax</button></div>
 {bytes>65536&&<p role="alert" className="error">Source exceeds 64 KiB.</p>}
 {validation&&<div className={validation.syntax_valid?"validation-ok":"error"} role="status"><strong>{validation.syntax_valid?"Syntax valid":"Syntax errors"}</strong><p>Python {validation.python_version} · Compile only, not execution or strategy validation.</p>
 {validation.diagnostics.map((d,i)=><p key={i}>Line {d.line}, column {d.column}: {d.message}</p>)}</div>}
 {r&&<p className="hash muted">Saved SHA-256: {r.code_sha256}</p>}
 <button className="primary" disabled={readOnly||!canCheck}>{r?"Save new version":"Save strategy"}</button>{note&&<p role="status">{note}</p>}</form></section></div>{r&&<RegistryPanel key={r.id+":"+r.version} api={api} revision={r} strategy={current} refresh={refresh} openJob={openJob} load={x=>{setR(x);setName(x.name);setSource(x.source);setValidation(null);setNote("");}}/>}</>;
}
function Runner({api,caps,open,refresh,report}:{api:Api;caps:Capabilities;open:(id:string)=>void;refresh:()=>Promise<void>;report:(e:unknown)=>void}){
 const [bars,setBars]=useState(120);const [tf,setTf]=useState<1|5|15>(5);const [busy,setBusy]=useState(false);const retry=useRef<{body:string;key:string}|null>(null);
 const valid=Number.isInteger(bars)&&bars>=20&&bars<=caps.fixture_max_bars&&bars%tf===0;
 async function run(e:FormEvent){e.preventDefault();setBusy(true);const payload:Fixture={kind:"reference_fixture",bars,signal_minutes:tf};const body=JSON.stringify(payload);if(retry.current?.body!==body)retry.current={body,key:crypto.randomUUID()};try{const j=await api.submit(payload,retry.current.key);retry.current=null;await refresh();open(j.id);}catch(e){report(e);}finally{setBusy(false);}}
 return <section className="panel runner"><h2>Run a reference backtest</h2><p>Uses a bundled EMA/Supertrend example on generated candles, not historical BTC or ETH data.</p><form onSubmit={run}><label htmlFor="bars">Number of 1-minute fixture bars</label><input id="bars" type="number" min={20} max={caps.fixture_max_bars} step={1} value={bars} onChange={e=>setBars(Number(e.target.value))}/><label htmlFor="tf">Signal timeframe</label><select id="tf" value={tf} onChange={e=>setTf(Number(e.target.value) as 1|5|15)}><option value={1}>1 minute</option><option value={5}>5 minutes</option><option value={15}>15 minutes</option></select>{!valid&&<p role="alert">Bars must be within limits and divisible by the signal interval.</p>}<button className="primary" disabled={busy||!valid||!caps.job_kinds.includes("reference_fixture")}>Run synthetic fixture</button></form></section>;
}
function Detail({api,id,refresh,report,open}:{api:Api;id:string;refresh:()=>Promise<void>;report:(e:unknown)=>void;open:(id:string)=>void}){
 const [j,setJ]=useState<Job|null>(null);const [busy,setBusy]=useState(false);const gen=useRef(0);const mounted=useRef(true);
 async function load(){const n=++gen.current;try{const x=await api.job(id);if(mounted.current&&n===gen.current)setJ(x);return x;}catch(e){if(mounted.current&&n===gen.current)report(e);return null;}}
 useEffect(()=>{mounted.current=true;let stop=false;let timer:number;async function poll(){const x=await load();if(!stop&&(!x||active(x)))timer=window.setTimeout(poll,1500);}void poll();return()=>{mounted.current=false;stop=true;gen.current++;window.clearTimeout(timer);};},[api,id]);
 async function cancel(){setBusy(true);try{await api.cancel(id);await load();await refresh();}catch(e){report(e);}finally{setBusy(false);}}
 if(!j)return <section className="panel">Loading job details…</section>;
 return <section className="panel"><div className="head"><h2>Job detail</h2><span className={"status "+j.status}>{j.status}</span></div><p className="hash muted">{j.id}</p><progress max={100} value={j.progress} aria-label="Selected job progress"/> {j.progress}% {active(j)&&<button disabled={busy||j.status==="cancelling"} onClick={()=>void cancel()}>Cancel job</button>}{j.error&&<p role="alert">{j.error}</p>}{j.result?.optimization&&<><OptimizationResults study={j.result.optimization}/><ValidationPanel api={api} job={j} open={open} refresh={refresh}/></>} {j.result?.validation&&<ValidationResults report={j.result.validation}/>} {j.result&&!j.result.optimization&&!j.result.validation&&<><h3>{j.result.synthetic?"Synthetic fixture result":"Historical visual research result"}</h3><p>{j.result.synthetic?"Generated data only. Not historical trading performance.":"Actual configured candle archive; reference model only, not exchange-verified."}</p>{j.result.assumptions&&<ul>{j.result.assumptions.map(a=><li key={a}>{a}</li>)}</ul>}<p className="hash muted">SHA-256: {j.result.result_sha256}</p><div className="scenarios">{j.result.result.scenarios.map(s=><Results key={s.path} s={s}/>)}</div><TradeAnalytics key={j.id} api={api} job={j}/><details><summary>Simulation limitations</summary><ul>{j.result.result.limitations.map(l=><li key={l}>{l}</li>)}</ul></details></>}</section>;
}
function Results({s}:{s:Scenario}){
 const values=s.equity_curve.map(p=>Number(p.equity)).filter(Number.isFinite);const lo=Math.min(...values),hi=Math.max(...values);const points=values.map((v,i)=>[10+i*300/Math.max(1,values.length-1),110-(v-lo)*100/Math.max(.000001,hi-lo)].join(",")).join(" ");
 return <article className="scenario"><h3>{s.path}</h3><dl>{[["Final equity","$"+fmt(s.final_equity)],["Net P&L","$"+fmt(s.net_pnl)],["Drawdown",fmt(s.max_event_drawdown_pct)+"%"],["Closed trades",s.closed_trades.length],["Fees","$"+fmt(s.fees)],["Tax","$"+fmt(s.taxes)]].map(([k,v])=><div key={k}><dt>{k}</dt><dd>{v}</dd></div>)}</dl>{values.length>0&&<svg className="chart" viewBox="0 0 320 125" role="img" aria-label="Modeled equity curve"><path d="M10 10V110H310" stroke="#76869d" fill="none"/><polyline points={points} fill="none" stroke="#43cabb" strokeWidth="2"/></svg>}<div className="table-wrap"><table><thead><tr><th>Month</th><th>P&L</th><th>Return</th></tr></thead><tbody>{s.monthly.map(m=><tr key={m.month}><td>{m.month}</td><td>{fmt(m.pnl)}</td><td>{fmt(m.return_pct)}%</td></tr>)}</tbody></table></div></article>;
}
createRoot(document.getElementById("root")!).render(<App/>);
