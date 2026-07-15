#!/usr/bin/env python3
"""confirm_item.py -- operator gate for LLM-inferred items (flag: draft-inferred*).

Confirm  -> clears the inferred flag, promoting the item to confirmed work.
           Residual suffix preserved: draft-inferred-needs-repro -> needs-repro;
           draft-inferred-needs-decomposition -> needs-decomposition;
           plain draft-inferred -> flag removed entirely.
Reject   -> sets status: rejected (file kept, reversible, filtered from working
           views by the exports). Inferred flag cleared to rejected-inference.

Operator-explicit --key only (never globs). DRY-RUN default; --commit writes
with .pre-confirm backups + hash-chained audit entry via gate/audit.js.

Usage:
  python3 tools/confirm_item.py --key EP-038 --confirm
  python3 tools/confirm_item.py --key BUG-002 --confirm         # keeps needs-repro
  python3 tools/confirm_item.py --key ST-233 --reject
  python3 tools/confirm_item.py --key EP-038 --confirm --commit
  python3 tools/confirm_item.py --list                          # show all inferred
"""
import argparse, glob, json, re, shutil, subprocess, sys
from datetime import date
from pathlib import Path

DIRS = ["state", "support"]
INFERRED = re.compile(r'^(\s*flag:\s*)"?(draft-inferred(?:-[a-z-]+)?)"?\s*$', re.M)

def files():
    fs = []
    for d in DIRS:
        fs += glob.glob(f"{d}/*.yaml")
    return [f for f in sorted(fs) if not Path(f).stem.startswith("_")]

def key_of(t):
    m = re.search(r'^\s*key:\s*"?([A-Z]+-\d+)', t, re.M)
    return m.group(1) if m else None

def inferred_flag(t):
    m = INFERRED.search(t)
    return m.group(2) if m else None

def audit_record(event):
    js = ("const a=require('./gate/audit');"
          "process.stdout.write(a.record(JSON.parse(process.argv[1])));")
    p = subprocess.run(["node", "-e", js, json.dumps(event)],
                       capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"audit append failed: {p.stderr[:300]}")
    return p.stdout.strip()

def audit_verify():
    p = subprocess.run(["node", "-e",
        "const a=require('./gate/audit');process.stdout.write(JSON.stringify(a.verify()));"],
        capture_output=True, text=True)
    return json.loads(p.stdout) if p.returncode == 0 else {"ok": None}

def list_inferred():
    print(f"{'KEY':8} {'TYPE':8} {'STATUS':10} FLAG")
    n = 0
    for f in files():
        t = Path(f).read_text(encoding="utf-8")
        fl = inferred_flag(t)
        if not fl:
            continue
        k = key_of(t) or Path(f).stem
        typ = (re.search(r'^  type:\s*(\w+)', t, re.M) or [None, "?"])[1]
        st = (re.search(r'^    status:\s*"?(\w+)', t, re.M) or [None, "?"])[1]
        print(f"{k:8} {typ:8} {st:10} {fl}")
        n += 1
    print(f"\ntotal inferred: {n}")

def apply_confirm(t, flag):
    """Return (new_text, note). Preserve residual suffix."""
    suffix = flag[len("draft-inferred"):]  # '' or '-needs-repro' etc.
    if suffix:
        residual = suffix.lstrip("-")
        new = INFERRED.sub(rf'\g<1>{residual}', t, count=1)
        return new, f"flag draft-inferred{suffix} -> {residual} (residual preserved)"
    # plain: remove the whole flag line
    new = re.sub(r'^\s*flag:\s*"?draft-inferred"?\s*\n', "", t, count=1, flags=re.M)
    return new, "flag draft-inferred removed (promoted to confirmed)"

def apply_reject(t, flag):
    """Set status: rejected, clear inferred flag to rejected-inference.
    Handles both prioritization-level (4-space) and top-level (2-space) status."""
    new = INFERRED.sub(r'\g<1>rejected-inference', t, count=1)
    if re.search(r'^    status:\s*', new, re.M):
        new = re.sub(r'^(    status:\s*)"?\w+"?\s*$', r'\g<1>rejected', new, count=1, flags=re.M)
        note = "status -> rejected (prioritization); flag -> rejected-inference"
    elif re.search(r'^  status:\s*', new, re.M):
        new = re.sub(r'^(  status:\s*)"?\w+"?\s*$', r'\g<1>rejected', new, count=1, flags=re.M)
        note = "status -> rejected (top-level); flag -> rejected-inference"
    else:
        note = "flag -> rejected-inference (no status field found)"
    return new, note

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--key", default="")
    ap.add_argument("--confirm", action="store_true")
    ap.add_argument("--reject", action="store_true")
    ap.add_argument("--commit", action="store_true")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()

    if a.list:
        list_inferred()
        return
    if not a.key:
        sys.exit("ABORT: --key required (or --list)")
    if a.confirm == a.reject:
        sys.exit("ABORT: exactly one of --confirm / --reject required")

    target = None
    for f in files():
        t = Path(f).read_text(encoding="utf-8")
        if key_of(t) == a.key:
            target = (f, t)
            break
    if not target:
        sys.exit(f"ABORT: no item with key {a.key}")
    f, t = target
    flag = inferred_flag(t)
    if not flag:
        sys.exit(f"ABORT: {a.key} is not inferred (no draft-inferred flag) -- nothing to gate")

    action = "confirm" if a.confirm else "reject"
    new, note = apply_confirm(t, flag) if a.confirm else apply_reject(t, flag)

    print(f"{'COMMIT' if a.commit else 'DRY-RUN'} | {a.key} | {action}")
    print(f"  file: {f}")
    print(f"  flag: {flag}")
    print(f"  change: {note}")
    # show the changed lines
    import difflib
    diff = list(difflib.unified_diff(t.splitlines(), new.splitlines(),
                                     lineterm="", n=0))
    for ln in diff[2:]:
        if ln.startswith(("+", "-")) and not ln.startswith(("+++", "---")):
            print(f"    {ln}")

    if not a.commit:
        v = audit_verify()
        print(f"  chain: ok={v.get('ok')} length={v.get('length')}")
        print("dry-run only. --commit to write.")
        return

    v = audit_verify()
    if v.get("ok") is False:
        sys.exit("ABORT: audit chain broken -- refusing to write")
    shutil.copy2(f, f + ".pre-confirm")
    Path(f).write_text(new, encoding="utf-8")
    h = audit_record({
        "action": "CONFIRM_ITEM" if a.confirm else "REJECT_ITEM",
        "status": "OK", "redaction": "NONE", "dest": "portfolio",
        "file": Path(f).name, "key": a.key,
        "from_flag": flag, "note": note,
    })
    print(f"  written. audit hash {h[:16]}...")

if __name__ == "__main__":
    main()
