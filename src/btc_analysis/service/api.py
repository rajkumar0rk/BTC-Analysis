"""Authenticated local API. Bearer secrets supplied by operator, never generated into UI."""
from __future__ import annotations
import hashlib
import hmac
import os
import json
from typing import Annotated, Literal
from fastapi import FastAPI, Depends, HTTPException, Header, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, StringConstraints
from .store import Store, Missing, Conflict, Invalid
from .diagnostics import validate_source, DiagnosticUnavailable
from ..indicators import CATALOG
from ..visual import Graph, compile_graph, recover_graph
from .historical import HistoricalRequest, snapshots, prepare, MAX_MINUTES
from .analytics import analytics, trade_replay
from .optimization import OptimizationRequest, prepare_optimization
from .validation import ValidationRequest, prepare_validation

MAX_BODY=100_000
Name=Annotated[str,StringConstraints(strip_whitespace=True,min_length=1,max_length=100)]
Source=Annotated[str,StringConstraints(min_length=1,max_length=65536)]
Key=Annotated[str,StringConstraints(pattern=r"^[A-Za-z0-9._:-]{1,128}$")]


class StrictModel(BaseModel):
    model_config=ConfigDict(extra="forbid",strict=True)


class StrategyCreate(StrictModel):
    name:Name
    source:Source


class RevisionCreate(StrictModel):
    source:Source
    expected_version:Annotated[int,Field(ge=1,le=100)]


class RegistryTransition(StrictModel):
    action:Literal["freeze","archive","restore"]
    expected_state:Annotated[int,Field(ge=0)]
    expected_version:Annotated[int,Field(ge=1,le=100)]


class CloneRequest(StrictModel):
    version:Annotated[int,Field(ge=1,le=100)]
    name:Name


class SyntaxRequest(StrictModel):
    source:Source


class FixtureRequest(StrictModel):
    kind:Literal["reference_fixture"]="reference_fixture"
    bars:Annotated[int,Field(ge=20,le=600)]=120
    signal_minutes:Literal[1,5,15]=5


class BodyLimit:
    """Reject over-limit bodies before JSON parse, including chunked requests."""
    def __init__(self,app):self.app=app
    async def __call__(self,scope,receive,send):
        if scope["type"]!="http" or scope["method"] not in ("POST","PUT","PATCH"):
            await self.app(scope,receive,send);return
        chunks=[];size=0
        while True:
            msg=await receive()
            if msg["type"]=="http.disconnect":return
            body=msg.get("body",b"");size+=len(body)
            if size>MAX_BODY:
                await JSONResponse({"detail":"request too large"},413)(scope,receive,send);return
            chunks.append(body)
            if not msg.get("more_body",False):break
        sent=False
        async def replay():
            nonlocal sent
            if not sent:
                sent=True;return {"type":"http.request","body":b"".join(chunks),"more_body":False}
            return await receive()
        await self.app(scope,replay,send)


def create_app(db_path,tokens,history_root=None):
    if not isinstance(tokens,dict) or not tokens:raise ValueError("explicit API identities required")
    digests={}
    for owner,token in tokens.items():
        if not isinstance(owner,str) or not owner.strip() or len(owner)>100 or not isinstance(token,str) or len(token)<32:
            raise ValueError("invalid identity/token; min 32-character random secret")
        d=hashlib.sha256(token.encode()).digest()
        if d in digests:raise ValueError("duplicate identity token")
        digests[d]=owner
    store=Store(db_path)
    app=FastAPI(title="BTC-Analysis API",version="0.6.0",docs_url=None,redoc_url=None,openapi_url=None)
    app.add_middleware(BodyLimit)

    def owner(authorization:Annotated[str|None,Header()]=None):
        if not authorization or not authorization.startswith("Bearer ") or len(authorization)>1024:
            raise HTTPException(401,"authentication required",headers={"WWW-Authenticate":"Bearer"})
        supplied=hashlib.sha256(authorization[7:].encode()).digest()
        found=None
        for digest,user in digests.items():
            if hmac.compare_digest(supplied,digest):found=user
        if found is None:raise HTTPException(401,"invalid credentials")
        return found

    @app.exception_handler(Missing)
    def missing(request:Request,exc:Missing):return JSONResponse({"detail":str(exc)},404)
    @app.exception_handler(Conflict)
    def conflict(request:Request,exc:Conflict):return JSONResponse({"detail":str(exc)},409)
    @app.exception_handler(Invalid)
    def invalid(request:Request,exc:Invalid):return JSONResponse({"detail":str(exc)},422)

    @app.middleware("http")
    async def headers(request,call_next):
        response=await call_next(request)
        response.headers["Cache-Control"]="no-store"
        response.headers["X-Content-Type-Options"]="nosniff"
        return response

    @app.get("/health")
    def health():return {"status":"ok","custom_python_execution":False,"job_kinds":["reference_fixture"]}

    @app.get("/v1/capabilities")
    def capabilities(user:str=Depends(owner)):
        available=snapshots(history_root)
        return {"custom_python_execution":False,"historical_runs":bool(available),"job_kinds":["reference_fixture"]+(["historical_visual","optimization","validation"] if available else []),
                "historical_max_minutes":MAX_MINUTES,
                "strategy_storage":True,"worker_concurrency":1,"fixture_max_bars":600}

    @app.post("/v1/strategies/validate")
    def validate(body:SyntaxRequest,user:str=Depends(owner)):
        try:return validate_source(body.source)
        except ValueError as exc:raise HTTPException(422,str(exc)) from exc
        except DiagnosticUnavailable as exc:raise HTTPException(503,str(exc)) from exc

    @app.get("/v1/sdk/catalog")
    def catalog(user:str=Depends(owner)):
        return {"sdk_version":"1","indicators":[
            {"name":name,"defaults":{k:(str(v) if not isinstance(v,int) else v) for k,v in defaults.items()},
             "outputs":list(fields)} for name,(defaults,fields) in sorted(CATALOG.items())],
             "execution_allowed":False}

    @app.post("/v1/visual/compile")
    def visual_compile(body:Graph,user:str=Depends(owner)):
        try:return compile_graph(body)
        except ValueError as exc:raise HTTPException(422,str(exc)) from exc

    @app.post("/v1/visual/recover")
    def visual_recover(body:SyntaxRequest,user:str=Depends(owner)):
        try:return recover_graph(body.source)
        except ValueError as exc:raise HTTPException(422,str(exc)) from exc

    @app.post("/v1/strategies",status_code=201)
    def create(body:StrategyCreate,user:str=Depends(owner)):
        return store.create_strategy(user,body.name,body.source)

    @app.get("/v1/strategies")
    def strategies(user:str=Depends(owner)):return store.strategies(user)

    @app.post("/v1/strategies/{sid}/versions",status_code=201)
    def revision(sid:str,body:RevisionCreate,user:str=Depends(owner)):
        return store.add_revision(user,sid,body.source,body.expected_version)

    @app.get("/v1/strategies/{sid}/versions")
    def versions(sid:str,user:str=Depends(owner)):return store.versions(user,sid)

    @app.post("/v1/strategies/{sid}/state")
    def transition(sid:str,body:RegistryTransition,user:str=Depends(owner)):
        return store.transition(user,sid,body.action,body.expected_state,body.expected_version)

    @app.post("/v1/strategies/{sid}/clone",status_code=201)
    def clone(sid:str,body:CloneRequest,user:str=Depends(owner)):
        return store.clone(user,sid,body.version,body.name)

    @app.get("/v1/strategies/{sid}/jobs")
    def strategy_jobs(sid:str,offset:int=0,user:str=Depends(owner)):
        if not 0<=offset<=1000:raise HTTPException(422,"invalid offset")
        return store.strategy_jobs(user,sid,offset)

    @app.get("/v1/strategies/{sid}/versions/{version}")
    def get_revision(sid:str,version:int,user:str=Depends(owner)):
        return store.revision(user,sid,version)

    @app.get("/v1/datasets")
    def datasets(user:str=Depends(owner)):
        return snapshots(history_root)

    @app.post("/v1/jobs/validation",status_code=202)
    def validation(body:ValidationRequest,idempotency_key:Annotated[Key,Header()],user:str=Depends(owner)):
        job=store.job(user,body.optimization_job_id)
        if job["request"]["kind"]!="optimization":raise HTTPException(422,"optimization job required")
        revision=store.revision(user,job["request"]["strategy_id"],job["request"]["version"])
        try:payload=prepare_validation(history_root,body,job,revision)
        except (ValueError,OSError,KeyError) as exc:raise HTTPException(422,"Validation configuration invalid: "+str(exc)[:300]) from exc
        return store.submit(user,idempotency_key,payload)

    @app.post("/v1/jobs/optimization",status_code=202)
    def optimization(body:OptimizationRequest,idempotency_key:Annotated[Key,Header()],user:str=Depends(owner)):
        revision=store.revision(user,body.strategy_id,body.version)
        try:payload=prepare_optimization(history_root,body,revision)
        except (ValueError,OSError,KeyError) as exc:raise HTTPException(422,"Optimization configuration invalid: "+str(exc)[:300]) from exc
        return store.submit(user,idempotency_key,payload)

    @app.post("/v1/jobs/historical",status_code=202)
    def historical(body:HistoricalRequest,idempotency_key:Annotated[Key,Header()],user:str=Depends(owner)):
        revision=store.revision(user,body.strategy_id,body.version)
        try:payload=prepare(history_root,body,revision)
        except (ValueError,OSError,KeyError) as exc:raise HTTPException(422,"Historical configuration invalid: "+str(exc)[:300]) from exc
        return store.submit(user,idempotency_key,payload)

    @app.post("/v1/jobs",status_code=202)
    def submit(body:FixtureRequest,idempotency_key:Annotated[Key,Header()],user:str=Depends(owner)):
        if body.bars%body.signal_minutes:raise HTTPException(422,"bars must divide into full signal intervals")
        return store.submit(user,idempotency_key,body.model_dump())

    @app.get("/v1/jobs")
    def jobs(user:str=Depends(owner)):return store.jobs(user)

    @app.get("/v1/jobs/{jid}")
    def job(jid:str,user:str=Depends(owner)):return store.job(user,jid)

    @app.get("/v1/jobs/{jid}/analytics")
    def job_analytics(jid:str,user:str=Depends(owner)):
        j=store.job(user,jid)
        try:return analytics(j)
        except ValueError as exc:raise HTTPException(422,str(exc)) from exc

    @app.get("/v1/jobs/{jid}/replay")
    def replay(jid:str,path:str,trade_id:str,offset:int=0,user:str=Depends(owner)):
        j=store.job(user,jid)
        try:return trade_replay(j,path,trade_id,history_root,offset)
        except (ValueError,OSError,KeyError) as exc:raise HTTPException(422,"Replay unavailable: "+str(exc)[:200]) from exc

    @app.post("/v1/jobs/{jid}/cancel")
    def cancel(jid:str,user:str=Depends(owner)):return store.cancel(user,jid)

    return app


def app_from_env():
    # Fail closed if operator configuration absent; no default credentials.
    return create_app(os.environ["BTC_PLATFORM_DB"],json.loads(os.environ["BTC_PLATFORM_TOKENS_JSON"]),os.environ.get("BTC_PLATFORM_HISTORY"))
