"""Generate reviewed private deployment config; never provision/deploy remotely."""
import argparse,json,re,uuid
from pathlib import Path
from urllib.parse import urlsplit
ROOT=Path(__file__).resolve().parents[1]
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--worker",required=True);p.add_argument("--origin",required=True);p.add_argument("--database-id",required=True)
    p.add_argument("--database-name",default="btc-analysis");p.add_argument("--enable-paper",action="store_true");p.add_argument("--release-sha",default="")
    a=p.parse_args()
    if a.release_sha and not re.fullmatch(r"[0-9a-f]{40}",a.release_sha):raise SystemExit("invalid release SHA")
    if not re.fullmatch(r"[a-z][a-z0-9-]{2,39}",a.worker) or not re.fullmatch(r"[a-zA-Z0-9_-]{1,63}",a.database_name):raise SystemExit("invalid names")
    u=urlsplit(a.origin)
    if u.scheme!="https" or a.origin!="https://"+u.netloc or not re.fullmatch(re.escape(a.worker)+r"\.[a-z0-9-]+\.workers\.dev",u.netloc):raise SystemExit("use exact matching HTTPS workers.dev origin")
    db=str(uuid.UUID(a.database_id))
    if db=="00000000-0000-4000-8000-000000000001":raise SystemExit("dummy local database prohibited")
    dist=ROOT/"apps/web/dist"
    if not (dist/"index.html").is_file() or not (dist/"python-runtime/pyodide.asm.wasm").is_file():raise SystemExit("build private Studio assets first")
    if not (dist/"private-release.json").is_file() or json.loads((dist/"private-release.json").read_text())!={"mode":"private"}:raise SystemExit("private build marker missing")
    for file in dist.rglob("*"):
        if file.is_file() and (file.name.startswith((".env",".dev.vars")) or file.suffix in (".csv",".sqlite",".db",".parquet")):raise SystemExit("unexpected private data in assets")
    config=ROOT/"apps/cloud/wrangler.release.toml"
    content=f'''name = "{a.worker}"
main = "src/worker.mjs"
compatibility_date = "2026-11-10"
workers_dev = true
preview_urls = false
[vars]
ALLOWED_ORIGINS = "{a.origin}"
RELEASE_SHA = "{a.release_sha}"
PAPER_ENABLED = "{str(a.enable_paper).lower()}"
[assets]
directory = "../web/dist"
run_worker_first = ["/v1/*", "/health"]
[[d1_databases]]
binding = "DB"
database_name = "{a.database_name}"
database_id = "{db}"
migrations_dir = "migrations"
[[durable_objects.bindings]]
name = "PAPER"
class_name = "PaperLane"
[[migrations]]
tag = "paper-v1"
new_sqlite_classes = ["PaperLane"]
'''
    with config.open("x") as dest:dest.write(content)
    (dist/"_headers").write_text("""/*
  X-Content-Type-Options: nosniff
  X-Frame-Options: DENY
  Referrer-Policy: no-referrer
  X-Robots-Tag: noindex
  Content-Security-Policy: default-src 'self'; script-src 'self' 'wasm-unsafe-eval'; worker-src 'self' blob:; connect-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self' data:; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'
""")
    print("Generated local config only:",config)
if __name__=="__main__":main()
