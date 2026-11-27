export const frames=[60,180,300,900,1800,3600,14400,86400] as const;
export type Frame=typeof frames[number];
export type Operand={kind:"price";timeframe:Frame;field:"open"|"high"|"low"|"close"|"volume"}|{kind:"constant";value:string}|{kind:"indicator";timeframe:Frame;name:string;parameters:Record<string,number|string>};
export const ops=["gt","gte","lt","lte","eq","cross_up","cross_down"] as const;
export type Condition={left:Operand;op:typeof ops[number];right:Operand};
export type Group={mode:"all"|"any";conditions:Condition[]};
export type Rule={enabled:boolean;mode:"all"|"any";groups:Group[]};
export const keys=["long_entry","short_entry","long_exit","short_exit"] as const;
export type RuleKey=typeof keys[number];
export type AdvancedControls={entry_mode:"continuous"|"once_per_true_run";confirmation_bars:number;cooldown_bars:number;weekdays_ist:number[];exit_mode:"percent"|"points";stop_points:string;target_points:string;target_enabled?:boolean|null;trailing?:{activation:string;distance:string}|null;trailing_percent?:{activation:string;distance:string}|null;trailing_atr?:{activation:string;timeframe:Frame;period:number;multiplier:string}|null;profit_lock?:{activation:string;locked:string}|null};
export const advancedDefaults=():AdvancedControls=>({entry_mode:"continuous",confirmation_bars:1,cooldown_bars:0,weekdays_ist:[0,1,2,3,4,5,6],exit_mode:"percent",stop_points:"100",target_points:"200"});
export type Graph={advanced?:AdvancedControls|null;schema_version:1;signal_timeframe:Frame;execution_timeframe:Frame;exposure_pct:string;stop_loss_pct:string;take_profit_pct:string}&Record<RuleKey,Rule>;
export type Compiled={graph:Graph;graph_sha256:string;source:string;compiler_version:string;execution_allowed:false};
export const newCondition=():Condition=>({left:{kind:"price",timeframe:900,field:"close"},op:"gt",right:{kind:"indicator",timeframe:900,name:"ema.value",parameters:{period:20}}});
export const newGroup=():Group=>({mode:"all",conditions:[newCondition()]});
export const initialGraph=():Graph=>({schema_version:1,signal_timeframe:900,execution_timeframe:60,exposure_pct:"50",stop_loss_pct:"1",take_profit_pct:"2",
long_entry:{enabled:true,mode:"any",groups:[newGroup()]},short_entry:{enabled:false,mode:"any",groups:[]},
long_exit:{enabled:true,mode:"any",groups:[{mode:"all",conditions:[{...newCondition(),op:"lt"}]}]},short_exit:{enabled:false,mode:"any",groups:[]}});
