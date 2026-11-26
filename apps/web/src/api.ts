export type Capabilities={custom_python_execution:boolean;historical_runs:boolean;strategy_storage:boolean;worker_concurrency:number;fixture_max_bars:number;job_kinds:string[]};
export type Strategy={id:string;name:string;latest_version:number;created:number};
export type Revision={id:string;name:string;version:number;source:string;code_sha256:string};
export type Fixture={kind:"reference_fixture";bars:number;signal_minutes:1|5|15};
export type Scenario={path:string;final_equity:string;initial_equity:string;net_pnl:string;fees:string;taxes:string;max_event_drawdown_pct:string;closed_trades:unknown[];equity_curve:{equity:string;event_utc:string}[];monthly:{month:string;pnl:string;return_pct:string|null}[]};
export type Job={id:string;status:"queued"|"running"|"cancelling"|"succeeded"|"failed"|"cancelled";progress:number;created:number;error:string|null;request:Fixture;result?:{synthetic:true;result_sha256:string;result:{worst_path:string;scenarios:Scenario[];limitations:string[]}}|null};
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
  strategies:()=>call<Strategy[]>("/v1/strategies"),
  create:(name:string,source:string)=>call<Revision>("/v1/strategies",{method:"POST",body:JSON.stringify({name,source})}),
  revision:(id:string,v:number)=>call<Revision>("/v1/strategies/"+encodeURIComponent(id)+"/versions/"+v),
  save:(id:string,v:number,source:string)=>call<Revision>("/v1/strategies/"+encodeURIComponent(id)+"/versions",{method:"POST",body:JSON.stringify({source,expected_version:v})}),
  jobs:()=>call<Job[]>("/v1/jobs"),job:(id:string)=>call<Job>("/v1/jobs/"+encodeURIComponent(id)),
  submit:(body:Fixture,key:string)=>call<Job>("/v1/jobs",{method:"POST",headers:{"Idempotency-Key":key},body:JSON.stringify(body)}),
  cancel:(id:string)=>call<Job>("/v1/jobs/"+encodeURIComponent(id)+"/cancel",{method:"POST"})
 };
}
export type Api=ReturnType<typeof client>;
