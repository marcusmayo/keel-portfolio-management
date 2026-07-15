#!/usr/bin/env python3
"""Single-item portfolio query. Given free text (a feature/idea), score it against all
state/ item NAMES and return top matches grouped by status, so you can see at a glance:
already DONE, similar PLANNED (backlog/in-progress), or a likely DUPLICATE (exact title).
Same tokeniser/overlap as reconcile, so /find agrees with the reconcile engine.
Stdlib + PyYAML. No LLM. Usage: python3 tools/find.py "live captions translation" """

import sys, re, glob
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parent.parent
STATE_GLOB   = str(ROOT / "state" / "*.yaml")
SUPPORT_GLOB = str(ROOT / "support" / "*.yaml")
TOP = 12          # max matches to show
FLOOR = 0.30      # ignore anything weaker than this

WORD = re.compile(r"[a-z0-9]+")
def toks(s): return set(WORD.findall((s or "").lower()))
def overlap(a, b):
    ta, tb = toks(a), toks(b)
    if not ta or not tb: return 0.0
    inter = len(ta & tb)
    if inter == 0: return 0.0
    if min(len(ta), len(tb)) >= 2:
        return inter / min(len(ta), len(tb))
    return inter / len(ta | tb)

DONE = {"done", "released", "complete", "completed"}

def load_items():
    out = []
    for globpat, store in ((STATE_GLOB, "portfolio"), (SUPPORT_GLOB, "support")):
        for f in glob.glob(globpat):
            if Path(f).stem.startswith("_"): continue
            try:
                w = (yaml.safe_load(Path(f).read_text(encoding="utf-8")) or {}).get("workitem") or {}
            except Exception:
                continue
            if not w or not w.get("name"): continue
            out.append({
                "key": w.get("key", ""), "type": w.get("type", ""),
                "name": w.get("name", ""), "status": w.get("status", ""),
                "stage": w.get("stage", ""),
                "ref": (w.get("source") or {}).get("ref", ""),
                "store": store,
            })
    return out

def _score_all(q, items):
    qn = " ".join(sorted(toks(q)))
    scored = []
    for it in items:
        s = overlap(q, it["name"])
        exact = (" ".join(sorted(toks(it["name"]))) == qn) and qn != ""
        if s >= FLOOR or exact:
            scored.append((1.0 if exact else s, exact, it))
    scored.sort(key=lambda x: (-x[0], not x[1]))
    return scored

def main():
    import json as _json
    args = sys.argv[1:]
    as_json = "--json" in args
    if as_json:
        args = [a for a in args if a != "--json"]
    q = " ".join(args).strip()
    if not q:
        if as_json:
            print(_json.dumps({"query": "", "verdict": "EMPTY", "matches": []})); return
        print("usage: /find <feature or idea text>"); return
    items = load_items()

    if as_json:
        scored = _score_all(q, items)[:TOP]
        matches = [{"key": it["key"], "type": it["type"], "name": it["name"],
                    "status": it["status"], "store": it.get("store", ""),
                    "score": round(s, 2), "exact": e} for s, e, it in scored]
        if any(m["exact"] for m in matches):
            verdict = "EXACT_DUP"
        elif matches and matches[0]["score"] >= 0.70:
            verdict = "LIKELY_MATCH"
        elif matches:
            verdict = "WEAK_MATCH"
        else:
            verdict = "NEW"
        print(_json.dumps({"query": q, "verdict": verdict, "matches": matches}, indent=2))
        return
    scored = []
    qn = " ".join(sorted(toks(q)))
    for it in items:
        s = overlap(q, it["name"])
        exact = (" ".join(sorted(toks(it["name"]))) == qn) and qn != ""
        if s >= FLOOR or exact:
            scored.append((1.0 if exact else s, exact, it))
    scored.sort(key=lambda x: (-x[0], not x[1]))
    scored = scored[:TOP]

    print(f'=== /find: "{q}" vs {len(items)} portfolio items ===')
    if not scored:
        print("  no matches above threshold -> looks NEW (no similar item in the portfolio)")
        return

    done   = [(s,e,it) for s,e,it in scored if it["status"] in DONE]
    active = [(s,e,it) for s,e,it in scored if it["status"] not in DONE]
    dupes  = [(s,e,it) for s,e,it in scored if e]

    def line(s, e, it):
        tag = "  <== EXACT TITLE (likely duplicate)" if e else ""
        print(f"  {int(round(s*100)):3d}%  {it['key']:7s} {it['type']:5s} {it['status']:12s} "
              f"{it['name'][:46]!r}{(' ['+it['ref']+']') if it['ref'] else ''}{tag}")

    if dupes:
        print("\nEXACT-TITLE MATCHES (duplicate risk):")
        for s,e,it in dupes: line(s,e,it)
    if done:
        print("\nALREADY DONE (completed - may not need to rebuild):")
        for s,e,it in done:
            if not e: line(s,e,it)
    if active:
        print("\nSIMILAR / PLANNED (backlog or in-progress):")
        for s,e,it in active:
            if not e: line(s,e,it)

    print(f"\n  read: >=~70% = strong match; exact title = duplicate; "
          f"done = already built; backlog/in-progress = similar planned. "
          f"Lexical match only - eyeball near-misses.")

if __name__ == "__main__":
    main()
