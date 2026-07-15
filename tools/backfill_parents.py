#!/usr/bin/env python3
"""One-time backfill: resolve parent for already-landed Jira items whose
parent field is blank. Reads each item's own source ref, finds its parent ID in
the normalized Jira JSON, resolves ID->source-key->Keel via resolve_parent, and writes
the Keel parent key into the YAML in place. DRY-RUN by default; --commit to write.
.pre-backfill backup of each changed file. Idempotent: skips items already parented.
"""
import json, re, sys, glob
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from resolve_parent import Resolver
from _require import require

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "state"
NORM = ROOT / "state" / "normalized" / "jira-portfolio.json"

def main():
    commit = "--commit" in sys.argv
    # normalized rows: source ref -> parent internal ID
    rows = json.loads(require(NORM).read_text(encoding="utf-8"))["rows"]
    ref2parent = {}
    for r in rows:
        ref = (r.get("source") or {}).get("ref", "")
        if ref:
            ref2parent[ref] = str(r.get("parent", "") or "")
    resolver = Resolver()

    unparented = []      # (file, key, ref)
    for f in glob.glob(str(STATE / "*.yaml")):
        if Path(f).stem.startswith("_"):
            continue
        txt = Path(f).read_text(encoding="utf-8")
        # only jira-origin items (have a source ref) with a BLANK parent
        rm = re.search(r"^\s*source:.*ref:\s*([A-Z]+-\d+)", txt, re.M)
        pm = re.search(r'^\s*parent:\s*"(.*)"', txt, re.M)
        if not rm:
            continue
        parent_val = pm.group(1) if pm else None
        if parent_val:   # already parented
            continue
        km = re.search(r"^\s*key:\s*([A-Z]+-\d+)", txt, re.M)
        unparented.append((f, km.group(1) if km else "?", rm.group(1)))

    resolved, unresolved, no_parent = [], [], []
    for f, key, ref in unparented:
        pid = ref2parent.get(ref, "")
        if not pid:
            no_parent.append((key, ref))            # top-level (epic) or no parent in Jira
            continue
        pkeel = resolver.resolve(pid)
        if pkeel:
            resolved.append((f, key, ref, pid, pkeel))
        else:
            unresolved.append((key, ref, pid))      # parent not in portfolio

    print(f"=== backfill_parents ({'COMMIT' if commit else 'DRY-RUN'}) ===")
    print(f"unparented jira items scanned: {len(unparented)}")
    print(f"  resolvable -> will set parent: {len(resolved)}")
    print(f"  no parent in Jira (top-level/epic): {len(no_parent)}")
    print(f"  parent exists in Jira but NOT in portfolio (stays blank): {len(unresolved)}")
    print("\nsample resolutions (first 12):")
    for f, key, ref, pid, pkeel in resolved[:12]:
        print(f"  {key} ({ref}) parent {pid} -> {pkeel}")
    if unresolved:
        print("\nsample unresolved (parent missing from portfolio, first 8):")
        for key, ref, pid in unresolved[:8]:
            print(f"  {key} ({ref}) parent-id {pid} -> {resolver.id2nge.get(pid,'?')} (not landed)")

    if not commit:
        print(f"\nDRY-RUN: nothing written. Re-run with --commit to set {len(resolved)} parents.")
        return

    written = 0
    for f, key, ref, pid, pkeel in resolved:
        p = Path(f)
        p.with_suffix(p.suffix + ".pre-backfill").write_text(p.read_text(encoding="utf-8"), encoding="utf-8")
        txt = p.read_text(encoding="utf-8")
        new = re.sub(r'^(\s*parent:\s*)""', rf'\g<1>"{pkeel}"', txt, count=1, flags=re.M)
        if new != txt:
            p.write_text(new, encoding="utf-8")
            written += 1
    print(f"\nCOMMITTED: set parent on {written} files (.pre-backfill backups written)")

if __name__ == "__main__":
    main()
