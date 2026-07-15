#!/usr/bin/env python3
"""stamp_merges.py -- Merge Step 4: write confirmed jira_ref onto keel items.

Reads state/resolutions.json MERGE decisions; sets source ref on the keel
item (origin unchanged -- provenance preserved, per template comment).
DRY-RUN default; --commit writes with .pre-stamp backups. Idempotent.
Reports duplicate-ref pairs (imported Jira placeholder carrying same ref)
as /delete candidates.
"""
import argparse, glob, json, re, shutil
from pathlib import Path
from _require import require

SRC = re.compile(r'^(\s*source:\s*\{origin:[^,}]*,\s*ref:\s*)("?)("?)(\s*\}.*)$')

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--commit", action="store_true")
    ap.add_argument("--resolutions", default="state/resolutions.json")
    a = ap.parse_args()

    merges = [r for r in json.loads(require(a.resolutions).read_text())["resolutions"]
              if str(r.get("decision", "")).upper() == "MERGE"]

    key2file, ref2files = {}, {}
    for f in sorted(glob.glob("state/*.yaml") + glob.glob("support/*.yaml")):
        if Path(f).stem.startswith("_"):
            continue
        txt = Path(f).read_text(encoding="utf-8")
        km = re.search(r'^\s*key:\s*"?([A-Z]+-\d+)"?', txt, re.M)
        if km:
            key2file[km.group(1)] = f
        rm = re.search(r'^\s*source:.*ref:\s*"?([A-Z]+-\d+)', txt, re.M)
        if rm:
            ref2files.setdefault(rm.group(1), []).append(f)

    plan, errors = [], []
    for m in merges:
        kk, jr = m["keel_key"], m["jira_ref"]
        f = key2file.get(kk)
        if not f:
            errors.append((kk, "no YAML with this key"))
            continue
        lines = Path(f).read_text(encoding="utf-8").splitlines(keepends=True)
        hit = None
        for i, ln in enumerate(lines):
            sm = re.match(r'^(\s*source:\s*\{origin:[^,}]*,\s*ref:\s*)"?([A-Z]+-\d+|)"?(\s*\}.*)$',
                          ln.rstrip("\n"))
            if sm:
                hit = (i, sm)
                break
        if hit is None:
            errors.append((kk, "no source line matched in %s" % f))
            continue
        i, sm = hit
        cur = sm.group(2)
        if cur == jr:
            errors.append((kk, "already stamped %s (idempotent skip)" % jr))
            continue
        if cur:
            errors.append((kk, "CONFLICT: carries ref %s, merge says %s" % (cur, jr)))
            continue
        new_line = sm.group(1) + jr + sm.group(3)
        dups = [d for d in ref2files.get(jr, []) if d != f]
        plan.append((kk, jr, f, i, lines, new_line, dups, m.get("reason", "")))

    mode = "COMMIT" if a.commit else "DRY-RUN"
    print("%s | merges: %d | to stamp: %d | skipped/errors: %d\n"
          % (mode, len(merges), len(plan), len(errors)))
    for kk, reason in errors:
        print("  skip %-8s %s" % (kk, reason))
    del_candidates = []
    for kk, jr, f, i, lines, new_line, dups, why in plan:
        print("  %-8s + %-8s -> %s" % (kk, jr, Path(f).name))
        print("      - %s" % lines[i].rstrip())
        print("      + %s" % new_line)
        for d in dups:
            print("      DUP PAIR: %s also carries %s  -> /delete candidate" % (Path(d).name, jr))
            del_candidates.append((jr, d))
    if not a.commit:
        print("\ndry-run only. --commit to write (with .pre-stamp backups).")
        return
    for kk, jr, f, i, lines, new_line, dups, why in plan:
        shutil.copy2(f, str(f) + ".pre-stamp")
        nl = "\r\n" if lines[i].endswith("\r\n") else "\n"
        lines[i] = new_line + nl
        Path(f).write_text("".join(lines), encoding="utf-8")
    print("\nwrote %d files (.pre-stamp backups)." % len(plan))
    if del_candidates:
        print("/delete candidates (thin Jira-import duplicates):")
        for jr, d in del_candidates:
            print("  %s  (%s)" % (d, jr))

if __name__ == "__main__":
    main()
