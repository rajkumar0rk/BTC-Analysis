"""Stage fixed-version Pyodide and trusted package sources for same-origin hosting."""
import hashlib,json,re,urllib.request,zipfile
from pathlib import Path

VERSION="0.29.3"
BASE="https://cdn.jsdelivr.net/pyodide/v"+VERSION+"/full/"
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"apps/web/public/python-runtime"
OUT.mkdir(parents=True,exist_ok=True)
def get(name,expected=None):
    if not re.fullmatch(r"[A-Za-z0-9_.+-]+",name):raise ValueError("invalid asset name")
    with urllib.request.urlopen(BASE+name,timeout=90) as r:
        data=r.read(40*1024*1024+1)
    if len(data)>40*1024*1024:raise ValueError("asset too large")
    digest=hashlib.sha256(data).hexdigest()
    if expected and digest!=expected:raise ValueError("wheel checksum mismatch: "+name)
    (OUT/name).write_bytes(data)
    return digest
assets={}
for name in ("pyodide.js","pyodide.asm.js","pyodide.asm.wasm","python_stdlib.zip","pyodide-lock.json"):
    assets[name]=get(name)
lock=json.loads((OUT/"pyodide-lock.json").read_text())["packages"]
seen=set()
def package(name):
    name=name.lower().replace("_","-")
    if name in seen:return
    seen.add(name);p=lock[name]
    for d in p.get("depends",[]):package(d)
    file=p["file_name"];assets[file]=get(file,p["sha256"])
for name in ("pydantic","tzdata"):
    package(name)
with zipfile.ZipFile(OUT/"studio-python.zip","w",compression=zipfile.ZIP_DEFLATED) as z:
    for path in sorted((ROOT/"src/btc_analysis").rglob("*.py")):
        if "__pycache__" not in path.parts:z.write(path,path.relative_to(ROOT/"src").as_posix())
assets["studio-python.zip"]=hashlib.sha256((OUT/"studio-python.zip").read_bytes()).hexdigest()
(OUT/"assets.json").write_text(json.dumps({"version":VERSION,"sha256":assets},sort_keys=True,indent=2)+"\n")
print("Prepared Pyodide",VERSION,len(assets),"assets")
