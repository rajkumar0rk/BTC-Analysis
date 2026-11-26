/** Explicit HTTPS cloud endpoint; token lives only in the returned client closure. */
export type CloudCapabilities={schema_version:1;owner:string;storage:boolean;source_execution:false;backtest_execution:false;paper_trading:boolean;live_orders:false;max_source_bytes:number;max_strategies:number;max_revisions:number;max_owner_revisions:number;max_results:number;results_storage:boolean};
export type CloudStrategy={id:string;name:string;latest_version:number};
export type CloudRevision={id:string;name?:string;version:number;source:string;code_sha256:string;created:number};
export type CloudResultSummary={engine_version:string;initial_equity:string;scenarios:{path:"O-H-L-C"|"O-L-H-C";net_pnl:string;drawdown_pct:string;trades:number;profit_factor:string|null;win_rate_pct:string|null;monthly:{month:string;pnl:string}[]}[]};
export type CloudResultInput={id:string;strategy_id:string;version:number;code_sha256:string;symbol:"BTCUSD"|"ETHUSD";dataset_sha256:string;result_sha256:string;summary:CloudResultSummary};
export type CloudResultMeta=Omit<CloudResultInput,"code_sha256"|"summary">&{payload_sha256:string;created:number};
export type CloudResult=CloudResultMeta&{summary:CloudResultSummary;verification:"client_reported"};
export type PaperConfig={request_id:string;fast:number;slow:number;equity:string;exposure_bps:number;taker_bps:number;tax_bps:number;slippage_bps:number;duration_minutes:number;acknowledge:true};
export type PaperSession={id:string;symbol:"BTCUSD"|"ETHUSD";status:string;reason:string|null;start:number;end:number;cursor:number;balance:string;qty:string;equity:string;bars:number;trades:number;fill_count:number;fees:string;tax:string;drawdown_bps:number;engine:string};
export type PaperFill={id:number;minute:number;side:"buy"|"sell";price:string;quantity:string;fee:string;tax:string;closed_net:string|null};
export function cloudClient(endpoint:string,token:string){
 const url=new URL(endpoint);
 if(url.protocol!=="https:"||url.username||url.password||url.search||url.hash||url.pathname!=="/")throw new Error("Cloud API must be an explicit HTTPS origin.");
 if(!/^[A-Za-z0-9_-]{43,128}$/.test(token))throw new Error("Invalid cloud token format.");
 const root=url.origin+"/v1/cloud";
 async function call<T>(path:string,method="GET",body?:unknown):Promise<T>{
  const response=await fetch(root+path,{method,headers:{Authorization:"Bearer "+token,...(body===undefined?{}:{"Content-Type":"application/json"})},body:body===undefined?undefined:JSON.stringify(body),credentials:"omit",redirect:"error",cache:"no-store",signal:AbortSignal.timeout(15000)});
  if(!response.ok)throw new Error("Cloud API request failed ("+response.status+").");
  return response.json() as Promise<T>;
 }
 const id=(value:string)=>{if(!/^[0-9a-f]{32}$/.test(value))throw new Error("Invalid strategy id");return value;};
 const version=(value:number)=>{if(!Number.isInteger(value)||value<1||value>100)throw new Error("Invalid revision");return value;};
 return {capabilities:()=>call<CloudCapabilities>("/capabilities"),strategies:()=>call<{strategies:CloudStrategy[]}>("/strategies"),
  create:(name:string,source:string)=>call<CloudRevision>("/strategies","POST",{name,source}),
  revision:(key:string,v:number)=>call<CloudRevision>("/strategies/"+id(key)+"/revisions/"+version(v)),
  revise:(key:string,v:number,source:string)=>call<CloudRevision>("/strategies/"+id(key),"PUT",{expected_version:version(v),source}),
  results:()=>call<{results:CloudResultMeta[];verification:"client_reported"}>("/results"),
  saveResult:(value:CloudResultInput)=>call<CloudResult>("/results","POST",value),
  result:(key:string)=>call<CloudResult>("/results/"+id(key)),
  deleteResult:(key:string)=>call<{deleted:true}>("/results/"+id(key),"DELETE"),
  paperState:(symbol:"BTCUSD"|"ETHUSD")=>call<{session:PaperSession|null;scale:string}>("/paper/"+symbol+"/state"),
  paperStart:(symbol:"BTCUSD"|"ETHUSD",config:PaperConfig)=>call<{session:PaperSession}>("/paper/"+symbol+"/start","POST",config),
  paperStop:(symbol:"BTCUSD"|"ETHUSD",key:string)=>call<{session:PaperSession}>("/paper/"+symbol+"/stop","POST",{id:id(key)}),
  paperLedger:(symbol:"BTCUSD"|"ETHUSD",after=0)=>call<{session:string|null;fills:PaperFill[];next:number;scale:string}>("/paper/"+symbol+"/ledger?after="+encodeURIComponent(String(after))),
  paperClear:(symbol:"BTCUSD"|"ETHUSD",key:string)=>call<{cleared:boolean;removed:number}>("/paper/"+symbol+"/clear","POST",{id:id(key)})};
}
