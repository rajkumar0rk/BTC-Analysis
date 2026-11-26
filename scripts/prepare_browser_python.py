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

# Publish only the existing public, checksummed monthly OHLCV archives as same-origin
# compressed binary assets. No credentials, private data, or runtime GitHub requests.
import shutil
history=ROOT/"apps/web/public/history-archive"
if history.exists():shutil.rmtree(history)
history.mkdir()
for symbol in ("BTCUSD","ETHUSD"):
    source=ROOT/"data/delta_india"/symbol/"1m"
    manifest=json.loads((source/"manifest.json").read_text())
    if manifest["symbol"]!=symbol or manifest["resolution"]!="1m" or manifest["timestamp_unit"]!="unix_seconds_utc":
        raise ValueError("unexpected history manifest")
    out=history/symbol
    out.mkdir()
    for item in manifest["partitions"]:
        name=item["file"];digest=item["sha256_gzip"]
        if not re.fullmatch(r"[0-9]{4}-[0-9]{2}\.csv\.gz",name) or not re.fullmatch(r"[a-f0-9]{64}",digest):
            raise ValueError("invalid archive partition")
        raw=(source/name).read_bytes()
        if len(raw)>4*1024*1024 or hashlib.sha256(raw).hexdigest()!=digest:
            raise ValueError("archive size/checksum mismatch: "+symbol+"/"+name)
        (out/(digest+".bin")).write_bytes(raw)
    (out/"manifest.json").write_text(json.dumps(manifest,sort_keys=True,separators=(",",":"))+"\n")
print("Staged verified BTCUSD/ETHUSD monthly archive snapshots.")
