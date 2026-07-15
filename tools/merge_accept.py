#!/usr/bin/env python3
"""Confirm keel-origin merge proposals into state/resolutions.json. Deterministic, no LLM.
Sub-actions:
  accept              -> write clean MERGE proposals to resolutions (guard blocks story/bug
                         many-to-one; epic-target many-to-one allowed - epics contain children)
  reject  <keys...>   -> mark rejected-this-round: stays UNRESOLVED (re-judged later), not written
  distinct <keys...>  -> write DISTINCT (permanent 'no Jira counterpart', never re-judged)
The reject list is read from a scratch file so /merge-reject then /merge-accept compose."""

import json, sys, datetime
from pathlib import Path

RECON  = Path("state/normalized/reconcile.json")
RESOL  = Path("state/resolutions.json")
JPORT  = Path("state/normalized/jira-portfolio.json")
JBUGS  = Path("state/normalized/jira-bugs.json")
REJECT = Path("state/normalized/.merge_rejects.json")   # ephemeral this-round rejects
TODAY  = datetime.date.today().isoformat()

def load_json(p, default):
    try: return json.loads(p.read_text(encoding="utf-8"))
    except Exception: return default

def proposals():
    return load_json(RECON, {}).get("buckets", {}).get("merge_candidate", [])

def ref_types():
    rt = {}
    for p in (JPORT, JBUGS):
        for r in load_json(p, {}).get("rows", []):
            rt[(r.get("source") or {}).get("ref","")] = r.get("type")
    return rt

def load_resol():
    d = load_json(RESOL, {"resolutions": []})
    return {r["keel_key"]: r for r in d.get("resolutions", []) if r.get("keel_key")}

def save_resol(bykey):
    RESOL.write_text(json.dumps({"resolutions": list(bykey.values())}, indent=2), encoding="utf-8")

def get_rejects():
    return set(load_json(REJECT, {"keys": []}).get("keys", []))

def set_rejects(keys):
    REJECT.write_text(json.dumps({"keys": sorted(keys)}), encoding="utf-8")

def cmd_reject(keys):
    r = get_rejects() | set(keys)
    set_rejects(r)
    print(f"rejected this round (stay open, re-judged later): {sorted(set(keys))}")
    print(f"total rejected this round: {sorted(r)}")
    print("run /merge-accept to accept the remaining clean proposals.")

def cmd_distinct(keys):
    bykey = load_resol()
    props = {p["keel_key"]: p for p in proposals()}
    for k in keys:
        bykey[k] = {"keel_key": k, "decision": "DISTINCT", "jira_ref": "",
                    "by": "operator", "date": TODAY,
                    "reason": (props.get(k, {}).get("reason","")) or "operator: no Jira counterpart"}
    save_resol(bykey)
    print(f"marked DISTINCT (permanent, never re-judged): {sorted(set(keys))}")

def cmd_accept():
    props = proposals()
    rejects = get_rejects()
    rt = ref_types()
    active = [p for p in props if p["keel_key"] not in rejects]

    # guard: a jira STORY/BUG ref claimed by >1 active keel item is illegal (atomic unit)
    from collections import Counter
    cnt = Counter(p["jira_ref"] for p in active)
    blocked = {}
    for p in active:
        ref = p["jira_ref"]
        if cnt[ref] > 1 and rt.get(ref) in ("story", "bug"):
            blocked.setdefault(ref, []).append(p["keel_key"])
    if blocked:
        print("BLOCKED - a Jira story/bug cannot be claimed by multiple keel items (atomic):")
        for ref, keys in blocked.items():
            print(f"  {ref} ({rt.get(ref)}) claimed by {keys}")
        print("Resolve first: /merge-reject all-but-one (keep the right one), or /delete a redundant item.")
        print("Nothing written.")
        return

    bykey = load_resol()
    written = 0
    for p in active:
        bykey[p["keel_key"]] = {"keel_key": p["keel_key"], "decision": "MERGE",
                                "jira_ref": p["jira_ref"], "by": "operator", "date": TODAY,
                                "reason": p.get("reason","")}
        written += 1
    save_resol(bykey)
    if REJECT.exists(): REJECT.unlink()   # clear this-round rejects after a successful accept
    print(f"=== accepted {written} MERGE proposals -> resolutions.json ===")
    for p in active:
        print(f"  MERGE  {p['keel_key']:7s} -> {p['jira_ref']:8s} {p['jira_name'][:40]!r}")
    print("\nNext: /apply stamps these refs onto the keel items (they become Jira-linked).")

def main():
    if len(sys.argv) < 2:
        print("usage: merge_accept.py accept|reject <keys>|distinct <keys>"); return
    action, keys = sys.argv[1], sys.argv[2:]
    if action == "accept":   cmd_accept()
    elif action == "reject": cmd_reject(keys)
    elif action == "distinct": cmd_distinct(keys)
    else: print(f"unknown action: {action}")

if __name__ == "__main__":
    main()
