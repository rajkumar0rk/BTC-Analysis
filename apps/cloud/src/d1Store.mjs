/** Owner-scoped D1 adapter; no global persistence or untrusted SQL. */
const err=code=>Object.assign(new Error(code),{code});
function classify(e){
 const message=String(e?.message||e);
 if(message.includes("quota_exceeded"))throw err("quota_exceeded");
 if(message.includes("version_conflict"))throw err("version_conflict");
 throw e;
}
export function d1Store(db){
 if(!db||typeof db.prepare!=="function"||typeof db.batch!=="function")return null;
 const q=(sql,...values)=>db.prepare(sql).bind(...values);
 const all=async(sql,...v)=>(await q(sql,...v).all()).results;
 const first=(sql,...v)=>q(sql,...v).first();
 return {
  async usage(owner){
   const r=await first("SELECT (SELECT count(*) FROM strategies WHERE owner=?) AS strategies, (SELECT count(*) FROM revisions WHERE owner=?) AS revisions, (SELECT count(*) FROM results WHERE owner=?) AS results",owner,owner,owner);
   return {strategies:r.strategies,revisions:r.revisions,results:r.results};
  },
  async list(owner){return all("SELECT id,name,latest_version,created FROM strategies WHERE owner=? ORDER BY created DESC,id LIMIT 30",owner);},
  async create(owner,v){
   try{
    await db.batch([
     q("INSERT INTO strategies(owner,id,name,created) VALUES(?,?,?,?)",owner,v.id,v.name,v.created),
     q("INSERT INTO revisions(owner,strategy_id,version,source,code_sha256,created) VALUES(?,?,1,?,?,?)",owner,v.id,v.source,v.code_sha256,v.created)
    ]);
    return {...v,version:1};
   }catch(e){classify(e);}
  },
  async revision(owner,id,version){
   return first("SELECT r.strategy_id AS id,s.name,r.version,r.source,r.code_sha256,r.created FROM revisions r JOIN strategies s ON s.owner=r.owner AND s.id=r.strategy_id WHERE r.owner=? AND r.strategy_id=? AND r.version=?",owner,id,version);
  },
  async revise(owner,id,expected,v){
   if(expected>=100)throw err("quota_exceeded");
   try{
    // Guarded insert + trigger advances head in the same atomic SQL statement.
    const inserted=await q("INSERT INTO revisions(owner,strategy_id,version,source,code_sha256,created) SELECT owner,id,latest_version+1,?,?,? FROM strategies WHERE owner=? AND id=? AND latest_version=? RETURNING strategy_id AS id,version,source,code_sha256,created",v.source,v.code_sha256,v.created,owner,id,expected).first();
    if(inserted)return inserted;
    if(!await first("SELECT id FROM strategies WHERE owner=? AND id=?",owner,id))throw err("not_found");
    throw err("version_conflict");
   }catch(e){classify(e);}
  },
  async listResults(owner){return all("SELECT id,strategy_id,version,symbol,dataset_sha256,result_sha256,payload_sha256,created FROM results WHERE owner=? ORDER BY created DESC,id LIMIT 200",owner);},
  async result(owner,id){
   const r=await first("SELECT id,strategy_id,version,symbol,dataset_sha256,result_sha256,payload_sha256,payload,created FROM results WHERE owner=? AND id=?",owner,id);
   if(!r)return null;
   const {payload,...meta}=r;
   return {...meta,summary:JSON.parse(payload),verification:"client_reported"};
  },
  async saveResult(owner,v){
   try{
    // A retry with the same id and payload is safe, conflicting reuse fails.
    const res=await q("INSERT INTO results(owner,id,strategy_id,version,symbol,dataset_sha256,result_sha256,payload_sha256,payload,created) SELECT ?,?,?,?,?,?,?,?,?,? FROM revisions WHERE owner=? AND strategy_id=? AND version=? AND code_sha256=? ON CONFLICT(owner,id) DO NOTHING RETURNING id",
     owner,v.id,v.strategy_id,v.version,v.symbol,v.dataset_sha256,v.result_sha256,v.payload_sha256,v.payload,v.created,owner,v.strategy_id,v.version,v.code_sha256).first();
    const row=await this.result(owner,v.id);
    if(row&&row.payload_sha256===v.payload_sha256&&row.strategy_id===v.strategy_id&&row.version===v.version&&row.result_sha256===v.result_sha256&&row.dataset_sha256===v.dataset_sha256&&row.symbol===v.symbol)return {record:row,created:!!res};
    if(row)throw err("version_conflict");
    throw err("not_found");
   }catch(e){classify(e);}
  },
  async removeResult(owner,id){
   const r=await q("DELETE FROM results WHERE owner=? AND id=?",owner,id).run();
   return r.meta.changes===1;
  }
 };
}
