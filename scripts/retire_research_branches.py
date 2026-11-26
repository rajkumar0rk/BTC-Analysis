#!/usr/bin/env python3
"""Archive original commits before deleting only explicitly reviewed branch heads."""
import json, subprocess, os, re, sys
from pathlib import Path
def run(*args,check=True,data=None):
    p=subprocess.run(args,input=data,text=True,capture_output=True)
    if check and p.returncode:raise RuntimeError(f"{' '.join(args[:4])}: {p.stderr.strip()[:1200]}")
    return p
repo=os.environ["GITHUB_REPOSITORY"]
plan=json.loads(Path("codex/RESEARCH_BRANCH_RETIREMENT_20261126.json").read_text())
archive=plan["archive"]
assert archive=="archive/retired-research-20261126" and plan["version"]==1
targets=plan["retire"]
retained={x["name"] for x in plan["retained"]}
assert len({x["name"] for x in targets})==len(targets)
assert not retained.intersection(x["name"] for x in targets)
for x in targets:
    assert x["name"].startswith(("research/","feature/"))
    assert not re.search(r"(^|[-/])(locked|frozen)([-/]|$)",x["name"],re.I)
    assert re.fullmatch("[a-f0-9]{40}",x["sha"])
def api(path,method="GET",body=None):
    args=["gh","api","--method",method,path]
    if body is not None:args+=["--input","-"]
    return json.loads(run(*args,data=json.dumps(body) if body is not None else None).stdout)
def pages(path):
    return json.loads(run("gh","api","--method","GET","--paginate","--slurp",path).stdout)
def refs():
    result={}
    for line in run("git","ls-remote","--heads","origin").stdout.splitlines():
        sha,ref=line.split("\t")
        result[ref.removeprefix("refs/heads/")]=sha
    return result
def protected_now():
    blocked=set(retained)
    for page in pages(f"repos/{repo}/branches?per_page=100"):
        blocked.update(b["name"] for b in page if b.get("protected"))
    for page in pages(f"repos/{repo}/pulls?state=open&per_page=100"):
        for pr in page:
            blocked.add(pr["base"]["ref"])
            if (pr["head"].get("repo") or {}).get("full_name")==repo:blocked.add(pr["head"]["ref"])
    for status in ("queued","in_progress","requested","waiting","pending"):
        for page in pages(f"repos/{repo}/actions/runs?status={status}&per_page=100"):
            blocked.update(w["head_branch"] for w in page.get("workflow_runs",[]) if w.get("head_branch"))
    return blocked
expected={x["sha"] for x in targets}
def verify_archive(tip):
    found=set()
    current=tip
    steps=0
    while current!=plan["base"]:
        c=api(f"repos/{repo}/git/commits/{current}")
        parents=[p["sha"] for p in c["parents"]]
        if not parents or not c["message"].startswith("archive: reviewed research branch heads"):
            raise RuntimeError("Archive ancestry is not the authorized consolidation chain")
        found.update(parents[1:])
        current=parents[0]
        steps+=1
        if steps>100:raise RuntimeError("Archive ancestry exceeds bound")
    if not expected.issubset(found|{plan["base"]}):raise RuntimeError("Archive missing reviewed commit heads")
    return steps
current=refs()
if archive not in current:
    base=api(f"repos/{repo}/git/commits/{plan['base']}")
    tree=base["tree"]["sha"]
    parent=plan["base"]
    unique=sorted(expected-{parent})
    for start in range(0,len(unique),24):
        group=unique[start:start+24]
        c=api(f"repos/{repo}/git/commits","POST",dict(message=f"archive: reviewed research branch heads {start+1}-{start+len(group)}",tree=tree,parents=[parent,*group]))
        parent=c["sha"]
    api(f"repos/{repo}/git/refs","POST",dict(ref="refs/heads/"+archive,sha=parent))
    current=refs()
    if current.get(archive)!=parent:raise RuntimeError("Archive ref not published")
tip=current[archive]
steps=verify_archive(tip)
print(f"VERIFIED archive {archive} at {tip}: {len(expected)} historical heads, {steps} consolidation commits",flush=True)
deleted=[]; already_absent=[]; skipped=[]; failed=[]
for start in range(0,len(targets),40):
    current=refs()
    if current.get(archive)!=tip:raise RuntimeError("Archive changed; aborting")
    blocked=protected_now()
    batch=[]
    for x in targets[start:start+40]:
        n=x["name"];sha=x["sha"]
        if n not in current:already_absent.append(n)
        elif n in blocked:skipped.append(dict(name=n,reason="protected/open PR/active workflow"))
        elif current[n]!=sha:skipped.append(dict(name=n,reason="head changed"))
        else:batch.append(x)
    if not batch:continue
    leases=[f"--force-with-lease=refs/heads/{x['name']}:{x['sha']}" for x in batch]
    deletes=[f":refs/heads/{x['name']}" for x in batch]
    p=run("git","push","--atomic",*leases,"origin",*deletes,check=False)
    if p.returncode:
        print(f"Atomic batch rejected; retrying individually: {p.stderr[:300]}",flush=True)
        for x in batch:
            n=x["name"];sha=x["sha"]
            if n in protected_now():skipped.append(dict(name=n,reason="new protection/open PR/active workflow"));continue
            one=run("git","push",f"--force-with-lease=refs/heads/{n}:{sha}","origin",f":refs/heads/{n}",check=False)
            if one.returncode:failed.append(dict(name=n,error=one.stderr[:300]))
            else:deleted.append(n)
    else:deleted.extend(x["name"] for x in batch)
    print(f"Progress: {len(deleted)} deleted, {len(skipped)} skipped, {len(failed)} failed",flush=True)
after=refs()
for n in deleted:
    if n in after:failed.append(dict(name=n,error="ref still present or recreated"))
missing=sorted(n for n in retained if n not in after)
if missing:raise RuntimeError("Retained refs missing: "+", ".join(missing))
verify_archive(after[archive])
report=dict(archive=archive,archive_sha=after[archive],planned=len(targets),deleted=len([n for n in deleted if n not in after]),already_absent=len(already_absent),skipped=skipped,failed=failed,remaining=len(after),retained_count=len(retained),remaining_reviewed_targets=[x["name"] for x in targets if x["name"] in after])
Path("branch-retirement-report.json").write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps(report,indent=2),flush=True)
if failed:sys.exit(1)
