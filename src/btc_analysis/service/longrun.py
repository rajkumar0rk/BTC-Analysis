"""Operator/CI long replay CLI. No queue timeout, no arbitrary strategy execution."""
import argparse,json,os,shutil
from pathlib import Path
from hashlib import sha256
from ..visual import Graph,compile_graph
from ..serialization import canonical_bytes
from ..backtest.archive import ScenarioArchive
from .historical import LongHistoricalRequest,execute_historical

def run(root,request,graph,output):
    r=LongHistoricalRequest.model_validate(request)
    c=compile_graph(Graph.model_validate(graph))
    payload={**r.model_dump(),"graph":c["graph"],"graph_sha256":c["graph_sha256"],
             "code_sha256":sha256(c["source"].encode()).hexdigest()}
    dest=Path(output).absolute();dest.mkdir(parents=True,exist_ok=False)
    try:
        result=execute_historical(payload,root,lambda p:True,archive_factory=lambda path:ScenarioArchive(dest,path))
        result["archive_format"]="ndjson-v1"
        result["request"]=r.model_dump()
        result["graph"]=c["graph"]
        result["graph_sha256"]=c["graph_sha256"]
        result["code_sha256"]=payload["code_sha256"]
        result["result_sha256"]=sha256(canonical_bytes({k:v for k,v in result.items() if k!="result_sha256"})).hexdigest()
        temp=dest/".manifest.tmp";temp.write_bytes(canonical_bytes(result)+b"\n")
        os.replace(temp,dest/"manifest.json")
        return result
    except BaseException:
        shutil.rmtree(dest)
        raise

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--history",required=True);p.add_argument("--request",required=True)
    p.add_argument("--graph",required=True);p.add_argument("--output",required=True)
    a=p.parse_args()
    result=run(a.history,json.loads(Path(a.request).read_text()),json.loads(Path(a.graph).read_text()),a.output)
    print(json.dumps({"result_sha256":result["result_sha256"],"scenarios":[
        {"path":s["path"],"bars":s["bars"],"summary":s["summary"]} for s in result["result"]["scenarios"]]},indent=2))
if __name__=="__main__":main()
