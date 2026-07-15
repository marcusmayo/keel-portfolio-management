#!/usr/bin/env python3
"""apply_scores.py -- write approved score proposals into item YAML.

Reads exports/score-proposals.json (from score_pass.py). DRY-RUN by default;
--commit writes with .pre-score backups. Line-based edits only (inline
comments survive). Idempotent: items already status:scored are skipped.

Usage:
  python3 tools/apply_scores.py                     # dry-run, all proposals
  python3 tools/apply_scores.py --skip ST-045,EP-032
  python3 tools/apply_scores.py --only EP-038
  python3 tools/apply_scores.py --include-done      # also score done items
  python3 tools/apply_scores.py --commit
"""
import argparse, json, re, shutil
from datetime import date
from pathlib import Path
from _require import require

DONE = {"done", "completed", "dev-verified"}
PROPOSALS = "exports/score-proposals.json"

def fmt(n):
    f = float(n)
    return str(int(f)) if f.is_integer() else str(f)

def work_status(lines):
    for ln in lines:
        m = re.match(r'^  status:\s*"?([A-Za-z-]+)"?\s*$', ln)
        if m:
            return m.group(1).lower()
    return ""

def find_block(lines):
    """Return (wsjf_i, rice_i, status_i) line indexes inside prioritization block."""
    pi = None
    for i, ln in enumerate(lines):
        if re.match(r"^  prioritization:\s*$", ln):
            pi = i
            break
    if pi is None:
        return None, None, None
    wi = ri = si = None
    for j in range(pi + 1, len(lines)):
        ln = lines[j]
        if ln.strip() and not ln.startswith("    "):
            break  # dedent = end of block
        s = ln.strip()
        if s.startswith("wsjf:"):
            wi = j
        elif s.startswith("rice:"):
            ri = j
        elif s.startswith("status:"):
            si = j
    return wi, ri, si

def new_lines(p, today):
    w, r = p["wsjf"], p["rice"]
    wl = ("    wsjf: {user_business_value: %s, time_criticality: %s, "
          "risk_reduction_opportunity: %s, job_size: %s, score: %s}" % (
              fmt(w["ubv"]), fmt(w["tc"]), fmt(w["rro"]), fmt(w["js"]), fmt(w["score"])))
    rl = ("    rice: {reach: %s, impact: %s, confidence: %s, effort: %s, score: %s}" % (
        fmt(r["reach"]), fmt(r["impact"]), fmt(r["confidence"]),
        fmt(r["effort"]), fmt(r["score"])))
    sl = "    status: scored"
    st = ("    scored: {by: claude-suggested, approved: operator, date: %s, grounding: %s}"
          % (today, p.get("grounding", "generic")))
    return wl, rl, sl, st

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--commit", action="store_true")
    ap.add_argument("--include-done", action="store_true")
    ap.add_argument("--only", default="")
    ap.add_argument("--skip", default="")
    ap.add_argument("--proposals", default=PROPOSALS)
    a = ap.parse_args()

    data = json.loads(require(a.proposals).read_text())
    props = data["proposals"]
    only = {k.strip() for k in a.only.split(",") if k.strip()}
    skip = {k.strip() for k in a.skip.split(",") if k.strip()}
    today = date.today().isoformat()

    applied, skipped_done, skipped_flag, already, errors = [], [], [], [], []
    for p in props:
        key = p["key"]
        if only and key not in only:
            continue
        if key in skip:
            skipped_flag.append(key)
            continue
        f = Path(p["file"])
        if not f.exists():
            errors.append((key, "file missing: %s" % f))
            continue
        txt = f.read_text(encoding="utf-8")
        if not re.search(r'^\s*key:\s*"?%s"?\b' % re.escape(key), txt, re.M):
            errors.append((key, "key not found in %s" % f))
            continue
        lines = txt.splitlines(keepends=True)
        bare = [ln.rstrip("\n") for ln in lines]
        if not a.include_done and work_status(bare) in DONE:
            skipped_done.append(key)
            continue
        wi, ri, si = find_block(bare)
        if wi is None or ri is None or si is None:
            errors.append((key, "prioritization block incomplete (wsjf/rice/status)"))
            continue
        if "unscored" not in bare[si]:
            already.append(key)
            continue
        wl, rl, sl, st = new_lines(p, today)
        nl = "\r\n" if lines[si].endswith("\r\n") else "\n"
        lines[wi] = wl + nl
        lines[ri] = rl + nl
        lines[si] = sl + nl + st + nl
        applied.append((key, p, f, "".join(lines)))

    mode = "COMMIT" if a.commit else "DRY-RUN"
    print("%s | to apply: %d | skipped-done: %d | skipped-flag: %d | "
          "already-scored: %d | errors: %d"
          % (mode, len(applied), len(skipped_done), len(skipped_flag),
             len(already), len(errors)))
    for key, reason in errors:
        print("  ERROR %s: %s" % (key, reason))
    if skipped_done:
        print("  skipped (done): %s%s"
              % (", ".join(skipped_done[:12]),
                 " ... +%d" % (len(skipped_done) - 12) if len(skipped_done) > 12 else ""))
    print()
    for key, p, f, _ in applied[:15]:
        print("  %-8s WSJF %-6s RICE %-9s [%s] -> %s"
              % (key, p["wsjf"]["score"], p["rice"]["score"],
                 p.get("grounding", "?")[:3], f.name))
    if len(applied) > 15:
        print("  ... +%d more" % (len(applied) - 15))

    if not a.commit:
        print("\ndry-run only. Re-run with --commit to write (with .pre-score backups).")
        return
    for key, p, f, content in applied:
        shutil.copy2(f, str(f) + ".pre-score")
        f.write_text(content, encoding="utf-8")
    print("\nwrote %d files (.pre-score backups alongside)." % len(applied))

if __name__ == "__main__":
    main()
