#!/usr/bin/env python3
"""delete_item.py -- operator-explicit, guarded, audit-logged item deletion.

Requires explicit --key (never globs). Refuses if the item is referenced as a
parent unless --reparent-to KEY (rewrites children) or --force. Warns if the
item carries a source ref no sibling retains (would strand Jira linkage). Logs
via gate/audit.js (the existing hash-chained writer -- one hash impl, chain
stays valid). Backs up removed bytes to <file>.pre-delete AND embeds a content
hash + size in the audit entry for recoverability.

Usage:
  python3 tools/delete_item.py --key ST-168                 # dry-run
  python3 tools/delete_item.py --key ST-168 --commit
  python3 tools/delete_item.py --key EP-011 --reparent-to EP-024 --commit
  python3 tools/delete_item.py --key EP-011 --force --commit
"""
import argparse, glob, hashlib, json, re, shutil, subprocess, sys
from pathlib import Path

STATE_DIRS = ["state", "support"]

def all_files():
    fs = []
    for d in STATE_DIRS:
        fs += glob.glob(f"{d}/*.yaml")
    return [f for f in sorted(fs) if not Path(f).stem.startswith("_")]

def key_of(txt):
    m = re.search(r'^\s*key:\s*"?([A-Z]+-\d+)', txt, re.M)
    return m.group(1) if m else None

def ref_of(txt):
    m = re.search(r'^\s*source:.*ref:\s*"?([A-Z]+-\d+)', txt, re.M)
    return m.group(1) if m else None

def audit_record(event):
    """Append a hash-chained entry via the existing Node writer."""
    js = ("const a=require('./gate/audit');"
          "const e=JSON.parse(process.argv[1]);"
          "process.stdout.write(a.record(e));")
    p = subprocess.run(["node", "-e", js, json.dumps(event)],
                       capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"audit append failed: {p.stderr[:300]}")
    return p.stdout.strip()

def audit_verify():
    p = subprocess.run(["node", "-e",
                        "const a=require('./gate/audit');"
                        "process.stdout.write(JSON.stringify(a.verify()));"],
                       capture_output=True, text=True)
    return json.loads(p.stdout) if p.returncode == 0 else {"ok": None, "err": p.stderr[:200]}


# ---- field extraction / merge helpers (policy A: richer-wins, gap-fill) ----
def drop_from_proposals(key):
    """Remove any score proposal for a retired key. Non-fatal: returns 0 if
    the proposals file is absent or the key isn't present. Keeps the proposals
    ledger consistent with live YAML so merges/deletes don't orphan entries."""
    import json
    pf = Path('exports/score-proposals.json')
    if not pf.exists():
        return 0
    try:
        data = json.loads(pf.read_text(encoding='utf-8'))
    except Exception:
        return 0
    is_list = isinstance(data, list)
    props = data if is_list else data.get('proposals', [])
    def keyof(x):
        return x.get('key') if isinstance(x, dict) else None
    kept = [x for x in props if keyof(x) != key]
    dropped = len(props) - len(kept)
    if dropped:
        shutil.copy2(str(pf), str(pf) + '.pre-proposalsdrop')
        out = kept if is_list else {**data, 'proposals': kept}
        pf.write_text(json.dumps(out, indent=2), encoding='utf-8')
    return dropped


def _desc_span(lines):
    """Return (start, end_exclusive, kind) for the description field, kind in
    {'quoted','block'}; or None."""
    for i, l in enumerate(lines):
        if re.match(r'^  description:\s*"', l):
            return (i, i + 1, "quoted")
        if re.match(r'^  description:\s*[>|]', l):
            j = i + 1
            while j < len(lines) and (lines[j].strip() == "" or re.match(r'^    ', lines[j])):
                j += 1
            return (i, j, "block")
    return None

def _desc_text(lines):
    sp = _desc_span(lines)
    if not sp:
        return ""
    s, e, kind = sp
    if kind == "quoted":
        m = re.match(r'^  description:\s*"(.*)"\s*$', lines[s])
        return m.group(1) if m else ""
    return " ".join(l.strip() for l in lines[s + 1:e] if l.strip())

def _is_placeholder(txt):
    d = re.sub(r"\[\s*draft\s*[\u2014\u2013-]\s*review\s*\]\s*", "", txt, flags=re.I).strip()
    return ("Imported from Jira" in d) or d.lower().startswith("[draft") or len(d) < 40

def _ac_span(lines):
    for i, l in enumerate(lines):
        if re.match(r'^  acceptance_criteria:\s*\[\]', l):
            return (i, i + 1, [])
        if re.match(r'^  acceptance_criteria:\s*$', l):
            j, items = i + 1, []
            while j < len(lines):
                if re.match(r'^    - ', lines[j]):
                    items.append(lines[j]); j += 1
                elif lines[j].strip() == "":
                    j += 1
                else:
                    break
            return (i, j, items)
    return None

def _field_line(lines, name):
    for i, l in enumerate(lines):
        if re.match(rf'^  {name}:', l):
            return i
    return None

def _stk_list(txt):
    m = re.search(r'^  stakeholders:\s*\[(.*)\]', txt, re.M)
    if not m:
        return []
    return [x.strip() for x in m.group(1).split(",") if x.strip()]

def _score_block(txt):
    """Return dict of the 4 prioritization lines (wsjf,rice,status,scored) as
    raw strings, or None if absent."""
    lines = txt.splitlines()
    out = {}
    for i, l in enumerate(lines):
        s = l.strip()
        if s.startswith("wsjf:"): out["wsjf"] = l
        elif s.startswith("rice:"): out["rice"] = l
        elif re.match(r'^    status:', l): out["status"] = l
        elif s.startswith("scored:"): out["scored"] = l
    return out

def consolidate(keep_txt, ret_txt, today):
    """Return (new_keep_txt, changes[]) applying policy A."""
    kl = keep_txt.splitlines(keepends=True)
    changes = []

    # description: retiree wins if survivor is placeholder
    k_bare = [l.rstrip("\n") for l in kl]
    if _is_placeholder(_desc_text(k_bare)) and not _is_placeholder(_desc_text(ret_txt.splitlines())):
        rsp = _desc_span(ret_txt.splitlines(keepends=True))
        ret_lines = ret_txt.splitlines(keepends=True)
        rblock = ret_lines[rsp[0]:rsp[1]]
        ksp = _desc_span(kl)
        kl = kl[:ksp[0]] + rblock + kl[ksp[1]:]
        changes.append("description <- retiree (survivor was placeholder)")

    # AC: retiree wins if survivor empty
    k_bare = [l.rstrip("\n") for l in kl]
    ksp = _ac_span(k_bare)
    rsp = _ac_span(ret_txt.splitlines())
    if ksp is not None and rsp is not None and len(ksp[2]) == 0 and len(rsp[2]) > 0:
        ret_lines = ret_txt.splitlines(keepends=True)
        r_items = ret_lines[rsp[0] + 1:rsp[1]]
        header = "  acceptance_criteria:\n"
        kl = kl[:ksp[0]] + [header] + r_items + kl[ksp[1]:]
        changes.append(f"acceptance_criteria <- retiree ({len(rsp[2])} items, survivor was empty)")

    # scores: retiree wins if retiree scored (fills or overwrites)
    r_scores = _score_block(ret_txt)
    k_bare = [l.rstrip("\n") for l in kl]
    if r_scores.get("status") and "scored" in r_scores["status"]:
        for field in ("wsjf", "rice", "status"):
            idx = None
            for i, l in enumerate(kl):
                if (field == "status" and re.match(r'^    status:', l)) or \
                   (field != "status" and l.strip().startswith(field + ":")):
                    idx = i; break
            if idx is not None and field in r_scores:
                nl = "\r\n" if kl[idx].endswith("\r\n") else "\n"
                kl[idx] = r_scores[field].rstrip("\r\n") + nl
        # scored stamp: replace or insert after status
        stamp = r_scores.get("scored")
        if stamp:
            sidx = next((i for i, l in enumerate(kl) if l.strip().startswith("scored:")), None)
            nl = "\n"
            stamp_line = "    " + stamp.strip() + nl if not stamp.startswith("    ") else stamp.rstrip("\r\n") + nl
            if sidx is not None:
                kl[sidx] = stamp_line
            else:
                stidx = next((i for i, l in enumerate(kl) if re.match(r'^    status:', l)), None)
                if stidx is not None:
                    kl.insert(stidx + 1, stamp_line)
        changes.append("scores <- retiree (grounded, policy A)")

    # stakeholders: union
    ku, ru = _stk_list("".join(kl)), _stk_list(ret_txt)
    merged = ku + [x for x in ru if x not in ku]
    if merged != ku:
        idx = next((i for i, l in enumerate(kl) if re.match(r'^  stakeholders:', l)), None)
        if idx is not None:
            nl = "\r\n" if kl[idx].endswith("\r\n") else "\n"
            kl[idx] = "  stakeholders: [" + ", ".join(merged) + "]" + nl
            changes.append(f"stakeholders union (+{len(merged)-len(ku)})")

    # updated bump
    idx = next((i for i, l in enumerate(kl) if re.match(r'^  updated:', l)), None)
    if idx is not None:
        nl = "\r\n" if kl[idx].endswith("\r\n") else "\n"
        kl[idx] = f"  updated: {today}" + nl
        changes.append("updated bumped")

    return "".join(kl), changes

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--key", required=True)
    ap.add_argument("--commit", action="store_true")
    ap.add_argument("--reparent-to", default="")
    ap.add_argument("--merge-into", default="",
                    help="consolidate this item onto KEEP_KEY (policy A) then delete")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()

    files = all_files()
    target, tkey, ttxt = None, None, None
    index = {}
    for f in files:
        txt = Path(f).read_text(encoding="utf-8")
        k = key_of(txt)
        if k:
            index[k] = f
        if k == a.key:
            target, tkey, ttxt = f, k, txt
    if target is None:
        sys.exit(f"ABORT: no item with key {a.key}")

    # inbound parent references
    children = []
    for f in files:
        if f == target:
            continue
        txt = Path(f).read_text(encoding="utf-8")
        if re.search(rf'^\s*parent:\s*"{re.escape(a.key)}"', txt, re.M):
            children.append((f, key_of(txt)))

    # stranded-ref check
    tref = ref_of(ttxt)
    ref_siblings = []
    if tref:
        for f in files:
            if f == target:
                continue
            if ref_of(Path(f).read_text(encoding="utf-8")) == tref:
                ref_siblings.append((f, key_of(Path(f).read_text(encoding="utf-8"))))

    print(f"TARGET: {tkey}  {target}")
    print(f"  ref: {tref or '(none)'}"
          + (f"  | retained by sibling(s): {[k for _,k in ref_siblings]}"
             if tref and ref_siblings else
             (f"  | WARNING: no sibling retains {tref} -- deleting strands Jira linkage"
              if tref else "")))
    print(f"  inbound parent refs (children): {len(children)}")
    for cf, ck in children:
        print(f"    {ck}  {cf}")

    if a.reparent_to:
        if a.reparent_to not in index:
            sys.exit(f"ABORT: --reparent-to {a.reparent_to} is not an existing key")
        if a.reparent_to == a.key:
            sys.exit("ABORT: cannot reparent children to the item being deleted")

    blocked = bool(children) and not a.reparent_to and not a.force
    if blocked:
        print("\nBLOCKED: item is a parent. Re-run with --reparent-to KEY "
              "(rewrites children) or --force (orphans them).")
        sys.exit(2)

    plan = []
    if children and a.reparent_to:
        for cf, ck in children:
            ctxt = Path(cf).read_text(encoding="utf-8")
            new = re.sub(rf'(^\s*parent:\s*)"{re.escape(a.key)}"',
                         rf'\g<1>"{a.reparent_to}"', ctxt, count=1, flags=re.M)
            plan.append((cf, ctxt, new))
        print(f"\nreparent: {len(plan)} child(ren) {a.key} -> {a.reparent_to}")
    elif children and a.force:
        print(f"\nforce: {len(children)} child(ren) will be ORPHANED (parent left dangling)")

    # ---- merge-into (policy A) : consolidate onto survivor, then delete retiree ----
    merge_changes, keep_file, keep_key, keep_new = [], None, None, None
    if a.merge_into:
        if a.merge_into not in index:
            sys.exit(f"ABORT: --merge-into {a.merge_into} is not an existing key")
        if a.merge_into == a.key:
            sys.exit("ABORT: cannot merge an item into itself")
        keep_file = index[a.merge_into]
        keep_txt = Path(keep_file).read_text(encoding="utf-8")
        keep_ref = ref_of(keep_txt)
        if tref and keep_ref and tref != keep_ref:
            sys.exit(f"ABORT: ref mismatch -- retiree {tref} vs survivor {keep_ref}; not a matched set")
        keep_key = a.merge_into
        from datetime import date as _date
        keep_new, merge_changes = consolidate(keep_txt, ttxt, _date.today().isoformat())
        print(f"\nMERGE-INTO {keep_key}  {keep_file}")
        if merge_changes:
            for c in merge_changes:
                print(f"    + {c}")
        else:
            print("    (survivor already richer in all fields; no changes)")

    content_hash = hashlib.sha256(ttxt.encode("utf-8")).hexdigest()
    print(f"\nwould DELETE {target} ({len(ttxt)} bytes, sha256 {content_hash[:16]}...)")
    print(f"  backup -> {target}.pre-delete")
    print("  audit entry -> action=DELETE_ITEM (embeds key, ref, sha256, size)")

    if not a.commit:
        v = audit_verify()
        print(f"\nchain pre-check: ok={v.get('ok')} length={v.get('length')}")
        print("dry-run only. --commit to execute.")
        return

    # verify chain intact before mutating
    v = audit_verify()
    if v.get("ok") is False:
        sys.exit(f"ABORT: audit chain broken at {v.get('brokenAt')} -- refusing to write")

    for cf, _old, new in plan:
        shutil.copy2(cf, cf + ".pre-delete")
        Path(cf).write_text(new, encoding="utf-8")
    if a.merge_into and keep_new is not None:
        shutil.copy2(keep_file, keep_file + ".pre-merge")
        Path(keep_file).write_text(keep_new, encoding="utf-8")
    shutil.copy2(target, target + ".pre-delete")
    Path(target).unlink()
    _proposals_dropped = drop_from_proposals(tkey)
    h = audit_record({
        "action": "DELETE_ITEM", "status": "OK", "redaction": "NONE",
        "proposals_dropped": _proposals_dropped,
        "dest": "trash", "file": Path(target).name,
        "key": tkey, "ref": tref or "", "sha256": content_hash,
        "bytes": len(ttxt), "reparented": len(plan),
        "merged_into": keep_key or "",
        "orphaned": len(children) if (children and a.force) else 0,
    })
    print(f"deleted {tkey}; reparented {len(plan)}; audit hash {h[:16]}...")
    print(f"recover: cp {target}.pre-delete {target}")

if __name__ == "__main__":
    main()
