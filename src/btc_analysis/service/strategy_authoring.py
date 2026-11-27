"""Local source inspection and literal-only parameter edits.

The complete edited source remains the versioned input to the existing runner.
No hidden configuration, dynamic exec, or server-side source execution.
"""
import ast
import re
from decimal import Decimal as D
from hashlib import sha256
from ..visual import Graph,compile_graph,recover_graph
from .python_strategy import Program,StrategyDiagnostic
from ..serialization import to_wire

def diagnostic(exc):
    if isinstance(exc,StrategyDiagnostic):
        return dict(severity="error",message=exc.message,line=exc.line,column=exc.column,
                    end_line=exc.end_line,end_column=exc.end_column)
    if isinstance(exc,SyntaxError):
        return dict(severity="error",message=exc.msg,line=max(1,exc.lineno or 1),column=max(1,exc.offset or 1),
                    end_line=max(1,exc.end_lineno or exc.lineno or 1),end_column=max(1,exc.end_offset or (exc.offset or 1)+1))
    return dict(severity="error",message=str(exc)[:500],line=1,column=1,end_line=1,end_column=2)

def validate_source(source):
    if not isinstance(source,str) or len(source.encode())>65536:raise ValueError("invalid source size")
    out=dict(source_sha256=sha256(source.encode()).hexdigest(),valid=False,kind="python",diagnostics=[],parameters=[],timeframes=[],indicators=[])
    try:
        if source.startswith("# btc-visual-v1 ") or source.lstrip().startswith("{"):
            out["kind"]="visual"
            c=recover_graph(source) if source.startswith("# btc-visual-v1 ") else compile_graph(Graph.model_validate_json(source))
            from .historical import GraphStrategy
            g=GraphStrategy(Graph.model_validate(c["graph"]))
            out.update(timeframes=[t.seconds for t in g.extra_timeframes()],indicators=[dict(name=s.name,timeframe=s.timeframe.seconds,parameters=to_wire(dict(s.parameters))) for s in g.indicators()])
        else:
            p=Program(source);sample=p.make()
            out.update(parameters=list(p.parameters.values()),timeframes=[t.seconds for t in sample.frames],
                       indicators=[dict(name=s.name,timeframe=s.timeframe.seconds,parameters=to_wire(dict(s.parameters))) for s in sample.specs])
        out["valid"]=True
    except (ValueError,TypeError,ArithmeticError,SyntaxError,IndexError,KeyError,AttributeError,RecursionError) as exc:
        out["diagnostics"]=[diagnostic(exc)]
    return out

def apply_parameters(source,values):
    if not isinstance(values,dict) or not 1<=len(values)<=32:raise ValueError("supply 1–32 declared parameter edits")
    p=Program(source);p.make()
    if not set(values)<=set(p.parameters):raise ValueError("unknown declared parameter")
    raw=source.encode();offsets=[0]
    for line in raw.splitlines(keepends=True):offsets.append(offsets[-1]+len(line))
    edits=[]
    for name,value in values.items():
        meta=p.parameters[name]
        if type(value) is not str or not re.fullmatch(r"-?[0-9]{1,18}(?:\.[0-9]{1,18})?",value):raise ValueError("invalid numeric value for "+name)
        v=D(value)
        if not D(meta["minimum"])<=v<=D(meta["maximum"]):raise ValueError("parameter outside declared bounds: "+name)
        if meta["kind"]=="integer":
            if v!=v.to_integral_value():raise ValueError("integer parameter required: "+name)
            literal=str(int(v))
        else:
            # Canonical exact decimal string. D is an SDK built-in alias.
            literal="D("+repr(to_wire(v))+")"
        n=p.parameter_nodes[name].args[0]
        edits.append((offsets[n.lineno-1]+n.col_offset,offsets[n.end_lineno-1]+n.end_col_offset,literal.encode()))
    for lo,hi,replacement in sorted(edits,reverse=True):raw=raw[:lo]+replacement+raw[hi:]
    edited=raw.decode()
    check=validate_source(edited)
    if not check["valid"]:raise ValueError("edited source failed validation: "+check["diagnostics"][0]["message"])
    return dict(source=edited,validation=check)
