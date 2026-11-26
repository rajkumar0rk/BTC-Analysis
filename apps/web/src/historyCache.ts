/** Opt-in IndexedDB persistence. One validated CSV slot per instrument. */
export type SymbolName="BTCUSD"|"ETHUSD";
export type SavedHistory={symbol:SymbolName;name:string;csv:string;sha256:string;storedAt:number};
const MAX_BYTES=16*1024*1024;
function open():Promise<IDBDatabase>{return new Promise((resolve,reject)=>{
 const r=indexedDB.open("btc-analysis-local-history",1);
 r.onupgradeneeded=()=>r.result.createObjectStore("csv",{keyPath:"symbol"});
 r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(r.error);
 r.onblocked=()=>reject(new Error("History database blocked"));
});}
async function transact<T>(mode:IDBTransactionMode,action:(s:IDBObjectStore)=>IDBRequest<T>):Promise<T>{
 const db=await open();
 try{return await new Promise<T>((resolve,reject)=>{const tx=db.transaction("csv",mode);const r=action(tx.objectStore("csv"));tx.oncomplete=()=>resolve(r.result);tx.onerror=()=>reject(tx.error);tx.onabort=()=>reject(tx.error??new Error("History transaction aborted"));});}finally{db.close();}
}
async function digest(csv:string){const bytes=new TextEncoder().encode(csv);if(bytes.byteLength>MAX_BYTES)throw new Error("History exceeds 16 MiB.");const hash=await crypto.subtle.digest("SHA-256",bytes);return Array.from(new Uint8Array(hash),b=>b.toString(16).padStart(2,"0")).join("");}
export async function saveHistory(value:SavedHistory){
 if(await digest(value.csv)!==value.sha256)throw new Error("CSV checksum mismatch.");
 await transact("readwrite",s=>s.put(value));
}
export async function loadHistory(symbol:SymbolName):Promise<SavedHistory|undefined>{
 const value=await transact<SavedHistory|undefined>("readonly",s=>s.get(symbol));
 if(value&&(value.symbol!==symbol||typeof value.csv!=="string"||typeof value.name!=="string"||await digest(value.csv)!==value.sha256))throw new Error("Stored CSV checksum mismatch; remove and re-import.");
 return value;
}
export async function deleteHistory(symbol:SymbolName){await transact("readwrite",s=>s.delete(symbol));}
