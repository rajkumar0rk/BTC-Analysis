"""Strict per-window risk slices, no synthesized baseline settlement events."""
import csv,io
from decimal import Decimal as D
from .leveraged_replay import csv_rows,epoch,decimal
from ..serialization import to_wire

class StudyRisk:
    def __init__(self,risk,require_marks):
        if not isinstance(risk,dict) or type(risk.get("funding_enabled")) is not bool:raise ValueError("invalid study risk input")
        self.base=dict(risk)
        self.marks={}
        self.funding={}
        if require_marks:
            self.marks=self.parse(self.base.pop("mark_csv",None),["time","open","high","low","close"],mark=True)
            if not self.marks:raise ValueError("matching mark CSV required")
        elif "mark_csv" in self.base:raise ValueError("repository study must use repository marks")
        if risk["funding_enabled"]:
            self.funding=self.parse(risk["funding_csv"],["time","rate","reference_mark"],mark=False)
            interval=risk.get("funding_interval_seconds");anchor=risk.get("funding_anchor_epoch")
            if type(interval) is not int or not 60<=interval<=86400 or interval%60 or type(anchor) is not int or anchor%60:raise ValueError("invalid funding schedule")
            if any((t-anchor)%interval for t in self.funding):raise ValueError("unexpected funding timestamp")
        elif risk.get("funding_csv"):raise ValueError("funding CSV supplied but disabled")

    @staticmethod
    def parse(text,header,mark):
        result={};previous=-1
        for row in csv_rows(text,header):
            t=int(epoch(row[0]).timestamp())
            if t<=previous:raise ValueError("risk rows must be unique and increasing")
            previous=t
            if mark:
                op,hi,lo,cl=(decimal(x,"0.000000000000000001","999999999999999999") for x in row[1:])
                if not lo<=min(op,cl)<=max(op,cl)<=hi:raise ValueError("invalid mark OHLC")
            else:
                decimal(row[1],"-0.1","0.1");decimal(row[2],"0.000000000000000001","999999999999999999")
            result[t]=row
        return result

    def window(self,lo,hi,leverage,label,multiplier):
        out={**self.base,"leverage":leverage}
        if self.marks:
            rows=[]
            for t in range(lo,hi,60):
                if t not in self.marks:raise ValueError("missing study mark minute")
                rows.append(self.marks[t])
            out["mark_csv"]=self.encode(["time","open","high","low","close"],rows)
        if out["funding_enabled"]:
            interval=out["funding_interval_seconds"];anchor=out["funding_anchor_epoch"]
            rows=[]
            for t in range(lo+(anchor-lo)%interval,hi,interval):
                if t not in self.funding:raise ValueError("missing study funding settlement")
                row=list(self.funding[t])
                if label.endswith("funding_positive") or label.endswith("funding_negative"):
                    rate=abs(D(row[1]))*D(multiplier)
                    if rate>D(".1"):raise ValueError("funding stress exceeds supported rate")
                    row[1]=to_wire(-rate if label.endswith("negative") else rate)
                    # Stressed values are explicitly synthetic and never attested.
                    out["funding_provenance"]="stress_synthetic"
                rows.append(row)
            out["funding_csv"]=self.encode(["time","rate","reference_mark"],rows)
        return out

    @staticmethod
    def encode(header,rows):
        out=io.StringIO(newline="")
        w=csv.writer(out,lineterminator="\n");w.writerow(header);w.writerows(rows)
        return out.getvalue()
