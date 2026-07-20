"""Validated reader for state/normalized/reconcile.json.
Diagnostics and verifiers read through this; never hand-traverse the file."""
import json
from pathlib import Path

BUCKETS = ("changed", "duplicate", "completed", "conflict", "gap", "done_gap", "ambiguous")

def load(path="state/normalized/reconcile.json"):
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    missing = [k for k in ("generated", "summary", "buckets") if k not in d]
    if missing:
        raise SystemExit(f"ERROR: reconcile.json missing {missing} (schema drift?)")
    b = d["buckets"]
    unknown = [k for k in b if k not in BUCKETS]
    if unknown:
        raise SystemExit(f"ERROR: unknown buckets {unknown} (schema drift?)")
    for k in BUCKETS:
        b.setdefault(k, [])
    return d
