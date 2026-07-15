#!/usr/bin/env python3
"""Operator CLI: rule work-item types for backlog rows the source sheet leaves
empty/invalid (sheet is owned upstream - repair locally, never guess).
Writes state/backlog-type-overrides.json keyed by Task #, capturing the row
name at ruling time; normalize_backlog applies a ruling only while the name
still matches. All args validated before anything is written (all-or-nothing).

Usage:
  python3 tools/set_backlog_type.py 8=story 24=story 67=feature
  python3 tools/set_backlog_type.py 8=-        # remove ruling for Task # 8
  python3 tools/set_backlog_type.py --list
Types: epic | feature | story
"""
import json, sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STORE = ROOT / "state" / "backlog-type-overrides.json"
NORM = ROOT / "state" / "normalized" / "backlog.json"
VOCAB = {"epic", "feature", "story"}

def load(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return default

def main():
    args = sys.argv[1:]
    if not args:
        sys.exit(__doc__)
    store = load(STORE, {"overrides": {}})
    ovr = store["overrides"]
    if args == ["--list"]:
        if not ovr:
            print("no rulings")
            return
        for k in sorted(ovr, key=lambda x: int(x) if x.isdigit() else 10**9):
            o = ovr[k]
            print(f"  {k}: {o['type']:8s} '{o.get('name','')}' (ruled {o.get('ruled','?')})")
        return
    norm = load(NORM, None)
    if norm is None:
        sys.exit("ERROR: state/normalized/backlog.json not found - run /normalize first")
    names = {r.get("task_id", ""): r.get("name", "") for r in norm.get("rows", [])}
    # pass 1: validate everything - no partial writes
    ops = []
    for a in args:
        if "=" not in a:
            sys.exit(f"ERROR: bad arg {a!r} (want TASKID=type or TASKID=-) - no changes written")
        tid, typ = a.split("=", 1)
        tid, typ = tid.strip(), typ.strip().lower()
        if typ == "-":
            ops.append((tid, None))
            continue
        if typ not in VOCAB:
            sys.exit(f"ERROR: {tid}: type {typ!r} not in {sorted(VOCAB)} - no changes written")
        if tid not in names:
            sys.exit(f"ERROR: Task # {tid!r} not in latest normalize run - no changes written")
        ops.append((tid, typ))
    # pass 2: apply
    for tid, typ in ops:
        if typ is None:
            if tid in ovr:
                old = ovr.pop(tid)
                print(f"removed {tid}: was {old.get('type')} '{old.get('name','')}'")
            else:
                print(f"no ruling for {tid} - nothing removed")
        else:
            ovr[tid] = {"type": typ, "name": names[tid], "ruled": date.today().isoformat()}
            print(f"ruled {tid}: {typ:8s} '{names[tid]}'")
    STORE.write_text(json.dumps(store, indent=2), encoding="utf-8")
    print(f"wrote {STORE.name} ({len(ovr)} rulings)")

if __name__ == "__main__":
    main()
