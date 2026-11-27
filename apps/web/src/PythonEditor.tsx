import {useEffect,useRef,useState} from "react";
import * as monaco from "monaco-editor/esm/vs/editor/editor.api";
import "monaco-editor/esm/vs/basic-languages/python/python.contribution";
import "monaco-editor/esm/vs/editor/contrib/suggest/browser/suggestController";
import "monaco-editor/esm/vs/editor/contrib/snippet/browser/snippetController2";
import "monaco-editor/esm/vs/editor/contrib/hover/browser/hoverContribution";
import EditorWorker from "monaco-editor/esm/vs/editor/editor.worker?worker";
import type {Catalog,Diagnostic} from "./api";

self.MonacoEnvironment={getWorker:()=>new EditorWorker()};
const sdkItems=[
 ["custom_indicators","def custom_indicators(self):\n        return ((\"my_indicator\", Timeframe(900), 20, \"my_formula\"),)","Declare a bounded custom indicator; formula signature (self, bars, previous)"],
 ["self.custom_value","self.custom_value(\"my_indicator\")","Latest completed custom indicator value"],
 ["self.custom_history","self.custom_history(\"my_indicator\", 2)","Completed custom indicator output history"],
 ["series","series(bars, \"close\")","Extract completed candle values"],
 ["mean","mean(series(bars, \"close\"))","Decimal arithmetic mean"],
 ["stddev","stddev(series(bars, \"close\"))","Population standard deviation"],
 ["parameter","parameter(20, 2, 100)","Declare an editable integer class parameter; defaults and bounds must be literals"],
 ["weekday_ist","weekday_ist(ctx.now_utc)","IST weekday, Monday=0"],
 ["ctx.candles","ctx.candles(Timeframe(60), 20)","Completed candle history"],
 ["ctx.indicator","ctx.indicator(\"ema\", Timeframe(900), {\"period\": 20})","Declared indicator value"],
 ["ctx.indicator_history","ctx.indicator_history(\"ema\", Timeframe(900), {\"period\": 20}, limit=2)","Completed indicator history"],
 ["ctx.equity","ctx.equity","Current marked equity"],
 ["ctx.position_quantity","ctx.position_quantity","Signed net position"],
 ["self.buy","self.buy(ctx, quantity, \"entry_reason\")","Submit a buy intent"],
 ["self.sell","self.sell(ctx, quantity, \"entry_reason\")","Submit a sell intent"],
 ["self.close_position","self.close_position(ctx, \"exit_reason\")","Reduce-only close"],
 ["spec","spec(\"ema\", Timeframe(900), period=20)","Declare a streaming indicator"],
 ["Timeframe","Timeframe(900)","Timeframe in seconds"],
 ["quantity_for_notional","quantity_for_notional(ctx.instrument, ctx.equity, price)","Round linear size to lot"],
 ["crossover","crossover(previous_a, current_a, previous_b, current_b)","Cross above"],
 ["crossunder","crossunder(previous_a, current_a, previous_b, current_b)","Cross below"],
];
type Props={value:string;onChange:(s:string)=>void;readOnly:boolean;diagnostics:Diagnostic[];catalog:Catalog|null};
export function PythonEditor({value,onChange,readOnly,diagnostics,catalog}:Props){
 const host=useRef<HTMLDivElement>(null);
 const editor=useRef<monaco.editor.IStandaloneCodeEditor|null>(null);
 const callback=useRef(onChange);callback.current=onChange;
 const current=useRef(value);current.current=value;
 const catalogRef=useRef(catalog);catalogRef.current=catalog;
 const [plain,setPlain]=useState(false);const [failed,setFailed]=useState(false);
 const [ready,setReady]=useState(false);
 useEffect(()=>{
  if(plain||failed||!host.current)return;
  let model:monaco.editor.ITextModel|undefined;
  let instance:monaco.editor.IStandaloneCodeEditor|undefined;
  let completion:monaco.IDisposable|undefined;
  let change:monaco.IDisposable|undefined;
  try{
   model=monaco.editor.createModel(current.current,"python");
   instance=monaco.editor.create(host.current,{model,theme:"vs-dark",automaticLayout:true,
     minimap:{enabled:false},fontSize:14,tabSize:4,insertSpaces:true,wordWrap:"on",
     ariaLabel:"Python editor",scrollBeyondLastLine:false,readOnly,accessibilitySupport:"auto",
     quickSuggestions:{other:true,comments:false,strings:true}});
   editor.current=instance;
   change=model.onDidChangeContent(()=>{const v=model!.getValue();if(v!==current.current)callback.current(v);});
   completion=monaco.languages.registerCompletionItemProvider("python",{
    triggerCharacters:[".","\"","'"],
    provideCompletionItems:(m,p)=>{
     if(m!==model)return {suggestions:[]};
     const prefix=m.getLineContent(p.lineNumber).slice(0,p.column-1);
     const match=prefix.match(/[A-Za-z_][A-Za-z0-9_.]*$/);
     const start=match?p.column-match[0].length:p.column;
     const range=new monaco.Range(p.lineNumber,start,p.lineNumber,p.column);
     const entries=[...sdkItems,...(catalogRef.current?.indicators??[]).flatMap(i=>i.outputs.map(o=>{
      const name=i.outputs.length===1?i.name:i.name+"."+o;
      const parameters=Object.entries(i.defaults).map(([k,v])=>k+"="+(typeof v==="number"?v:JSON.stringify(v))).join(", ");
      return [name,"spec("+JSON.stringify(name)+", Timeframe(900), "+parameters+")","SDK indicator declaration"];
     }))];
     return {suggestions:entries.map(([label,insertText,detail])=>({label,kind:monaco.languages.CompletionItemKind.Function,insertText,detail,range}))};
    }});
   setReady(true);
  }catch{setFailed(true);}
  return()=>{setReady(false);completion?.dispose();change?.dispose();instance?.dispose();model?.dispose();editor.current=null;};
 },[plain,failed]);
 useEffect(()=>{const m=editor.current?.getModel();if(m&&m.getValue()!==value)m.setValue(value);},[value,plain,ready]);
 useEffect(()=>{editor.current?.updateOptions({readOnly});},[readOnly,ready]);
 useEffect(()=>{
  const m=editor.current?.getModel();if(!m)return;
  function pos(line:number,column:number){
   const l=Math.max(1,Math.min(m!.getLineCount(),line));
   const text=m!.getLineContent(l);
   const offset=Array.from(text).slice(0,Math.max(0,column-1)).join("").length+1;
   return {lineNumber:l,column:Math.min(m!.getLineMaxColumn(l),offset)};
  }
  monaco.editor.setModelMarkers(m,"python-syntax",diagnostics.map(d=>{
   const s=pos(d.line,d.column),end=pos(d.end_line,d.end_column);
   return {severity:monaco.MarkerSeverity.Error,message:d.message,startLineNumber:s.lineNumber,startColumn:s.column,
    endLineNumber:Math.max(s.lineNumber,end.lineNumber),endColumn:end.lineNumber<=s.lineNumber?Math.max(s.column,end.column):end.column};
  }));
 },[diagnostics,ready,plain]);
 return <div className="python-editor"><div className="head"><strong>Python source</strong>
  <button type="button" onClick={()=>setPlain(p=>!p)} disabled={failed}>{plain?"Use advanced editor":"Use plain text editor"}</button></div>
  {plain||failed?<><label htmlFor="python-source">Python source</label><textarea id="python-source" rows={15} spellCheck={false}
    readOnly={readOnly} maxLength={65536} value={value} onChange={e=>onChange(e.target.value)}/>{failed&&<p className="muted">Advanced editor unavailable; using plain text.</p>}</>:
    <div ref={host} className="monaco-host" aria-label="Advanced Python editor"/>}
  <p className="muted editor-hint">SDK suggestions: Ctrl+Space. Source is stored, never executed by the editor.</p>
 </div>;
}
