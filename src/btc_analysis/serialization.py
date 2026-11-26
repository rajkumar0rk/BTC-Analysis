"""Canonical v1 wire encoding for immutable contracts; never executes user code."""
from dataclasses import fields, is_dataclass
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from hashlib import sha256
import json


def to_wire(value):
    if isinstance(value, Enum):
        return to_wire(value.value)
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("non-finite Decimal")
        # Preserve exact decimal digits without exponent or binary floats.
        if value == 0:
            return "0"
        s = format(value, "f")
        return s.rstrip("0").rstrip(".") if "." in s else s
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("naive timestamp")
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    if is_dataclass(value) and not isinstance(value, type):
        return {f.name: to_wire(getattr(value, f.name)) for f in fields(value)}
    if isinstance(value, (tuple, list)):
        return [to_wire(x) for x in value]
    if isinstance(value, dict):
        if not all(isinstance(k, str) for k in value):
            raise TypeError("wire keys must be strings")
        return {k: to_wire(v) for k, v in value.items()}
    if value is None or isinstance(value, (str, int, bool)):
        return value
    raise TypeError(f"unsupported wire type: {type(value).__name__}")


def canonical_bytes(value) -> bytes:
    return json.dumps(to_wire(value), sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def fingerprint(value) -> str:
    return sha256(canonical_bytes(value)).hexdigest()
