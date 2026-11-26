import type {Graph,Compiled} from "./visualTypes";
export type Diagnostic={severity:"error";message:string;line:number;column:number;end_line:number;end_column:number};
export type Validation={source_sha256:string;syntax_valid:boolean;diagnostics:Diagnostic[];execution_allowed:false;python_version:string};
export type Catalog={sdk_version:string;execution_allowed:false;indicators:{name:string;defaults:Record<string,string|number>;outputs:string[]}[]};
export type Capabilities={custom_python_execution:boolean;historical_runs:boolean;strategy_storage:boolean;worker_concurrency:number;fixture_max_bars:number;job_kinds:string[]};
export type RegistryMeta={archived:boolean;frozen_version:number|null;frozen_at:number|null;state_version:number;parent_strategy_id:string|null;parent_version:number|null;parent_code_sha256:string|null};
export type Registry=RegistryMeta&{id:string;versions:{version:number;code_sha256:string;created:number}[];events:{sequence:number;action:string;version:number;code_sha256:string;created:number}[]};
export type Strategy=RegistryMeta&{id:string;name:string;latest_version:number;created:number};
export type Revision=RegistryMeta&{id:string;name:string;version:number;source:string;code_sha256:string};
export type Dataset={symbol:"BTCUSD"|"ETHUSD";manifest_sha256:string;start:number;end:number;timestamp_label_verified:boolean};
export type Historical={kind:"historical_visual";strategy_id:string;version:number;symbol:Dataset["symbol"];manifest_sha256:string;start:number;end:number;warmup_minutes:number;initial_equity:string;maker_bps:string;taker_bps:string;tax_rate:string;slippage_bps:string;tick_size:string;lot_size:string;multiplier:string;assume_open:boolean;acknowledge_reference:true};
export type Search={method:"grid"|"random";axes:{key:string;values:string[]}[];samples:number;seed:number;objective:"net_return"|"profit_factor"|"win_rate";max_drawdown_pct:string;min_trades:number};
export type Optimization=Omit<Historical,"kind">&{kind:"optimization";search:Search;acknowledge_training_only:true};
export type Candidate={rank:number;parameters:Record<string,string>;graph_sha256:string;code_sha256:string;result_sha256:string;score:string|null;max_drawdown_pct:string;min_closed_trades:number;eligible:boolean;rejections:string[];scenarios:{path:string;metrics:Record<string,string|number|null>}[]};
export type Study={training_only:true;search:Search;training_request:Historical;base_graph_sha256:string;candidates:Candidate[];winner_graph_sha256:string|null;timestamp_label_verified:boolean};
export type Fixture={kind:"reference_fixture";bars:number;signal_minutes:1|5|15};
export type Fill={fill_id:string;order_id:string;event_utc:string;side:string;quantity:string;price:string;fee:string;tax:string;reason:string};
export type Trade={trade_id:string;entry_fills:Fill[];exit_fills:Fill[];entry_reason:string;exit_reason:string;gross_pnl:string;fees:string;taxes:string;funding_paid:string;net_pnl:string;currency:string};
export type Analytics={result_sha256:string;scenarios:{path:string;metrics:Record<string,string|number|null>}[]};
export type Replay={symbol:string;dataset_manifest_sha256:string;timestamp_label_verified:boolean;scenario:string;trade_id:string;offset:number;total:number;next_offset:number|null;previous_offset:number|null;candles:{time:number;open:string;high:string;low:string;close:string;volume:string}[];markers:{bar_open:number;bar_close:number;phase:string;path:string;role:string;fill:Fill}[]};
export type Scenario={path:string;final_equity:string;initial_equity:string;net_pnl:string;fees:string;taxes:string;max_event_drawdown_pct:string;closed_trades:Trade[];equity_curve:{equity:string;event_utc:string}[];monthly:{month:string;pnl:string;return_pct:string|null}[]};
export type Job={id:string;status:"queued"|"running"|"cancelling"|"succeeded"|"failed"|"cancelled";progress:number;created:number;error:string|null;request:Fixture|Historical|Optimization;result?:{synthetic:boolean;research_only?:boolean;timestamp_label_verified?:boolean;assumptions?:string[];optimization?:Study;result_sha256:string;result:{worst_path:string;scenarios:Scenario[];limitations:string[]}}|null};
export class ApiError extends Error{constructor(public status:number,message:string){super(message)}}
export function client(token:string){
 async function call<T>(path:string,options:RequestInit={}):Promise<T>{
  const headers=new Headers(options.headers);headers.set("Authorization","Bearer "+token);
  if(options.body)headers.set("Content-Type","application/json");
  const r=await fetch(path,{...options,headers,cache:"no-store",credentials:"omit",redirect:"error"});
  if(!r.ok){const x=await r.json().catch(()=>null);throw new ApiError(r.status,typeof x?.detail==="string"?x.detail:"Request failed ("+r.status+")");}
  return await r.json() as T;
 }
 return {
  capabilities:()=>call<Capabilities>("/v1/capabilities"),
  validate:(source:string)=>call<Validation>("/v1/strategies/validate",{method:"POST",body:JSON.stringify({source})}),
  catalog:()=>call<Catalog>("/v1/sdk/catalog"),
  compileVisual:(graph:Graph)=>call<Compiled>("/v1/visual/compile",{method:"POST",body:JSON.stringify(graph)}),
  recoverVisual:(source:string)=>call<Compiled>("/v1/visual/recover",{method:"POST",body:JSON.stringify({source})}),
  strategies:()=>call<Strategy[]>("/v1/strategies"),
  versions:(id:string)=>call<Registry>("/v1/strategies/"+encodeURIComponent(id)+"/versions"),
  state:(id:string,action:"freeze"|"archive"|"restore",expected_state:number,expected_version:number)=>call<Registry>("/v1/strategies/"+encodeURIComponent(id)+"/state",{method:"POST",body:JSON.stringify({action,expected_state,expected_version})}),
  clone:(id:string,version:number,name:string)=>call<Revision>("/v1/strategies/"+encodeURIComponent(id)+"/clone",{method:"POST",body:JSON.stringify({version,name})}),
  strategyJobs:(id:string,offset=0)=>call<{jobs:(Job&{result_sha256:string|null})[];next_offset:number|null}>("/v1/strategies/"+encodeURIComponent(id)+"/jobs?offset="+offset),
  create:(name:string,source:string)=>call<Revision>("/v1/strategies",{method:"POST",body:JSON.stringify({name,source})}),
  revision:(id:string,v:number)=>call<Revision>("/v1/strategies/"+encodeURIComponent(id)+"/versions/"+v),
  save:(id:string,v:number,source:string)=>call<Revision>("/v1/strategies/"+encodeURIComponent(id)+"/versions",{method:"POST",body:JSON.stringify({source,expected_version:v})}),
  datasets:()=>call<Dataset[]>("/v1/datasets"),
  optimize:(body:Optimization,key:string)=>call<Job>("/v1/jobs/optimization",{method:"POST",headers:{"Idempotency-Key":key},body:JSON.stringify(body)}),
  historical:(body:Historical,key:string)=>call<Job>("/v1/jobs/historical",{method:"POST",headers:{"Idempotency-Key":key},body:JSON.stringify(body)}),
  analytics:(id:string)=>call<Analytics>("/v1/jobs/"+encodeURIComponent(id)+"/analytics"),
  replay:(id:string,path:string,trade:string,offset=0)=>call<Replay>("/v1/jobs/"+encodeURIComponent(id)+"/replay?"+new URLSearchParams({path,trade_id:trade,offset:String(offset)})),
  jobs:()=>call<Job[]>("/v1/jobs"),job:(id:string)=>call<Job>("/v1/jobs/"+encodeURIComponent(id)),
  submit:(body:Fixture,key:string)=>call<Job>("/v1/jobs",{method:"POST",headers:{"Idempotency-Key":key},body:JSON.stringify(body)}),
  cancel:(id:string)=>call<Job>("/v1/jobs/"+encodeURIComponent(id)+"/cancel",{method:"POST"})
 };
}
export type Api=ReturnType<typeof client>;
