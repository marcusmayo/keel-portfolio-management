#!/usr/bin/env python3
"""Deterministic Jira CSV normalizer. Reads the newest raw Jira export, maps type +
status to canonical values, routes by type (portfolio vs bug vs sub-task), and writes
two normalized JSONs consumed by reconcile. Stdlib only. No LLM. Real source keys are
preserved as source.ref, enabling exact-ref matching in reconcile."""

import csv, json, sys, glob, os
from pathlib import Path
from datetime import datetime

RAW_GLOB = "knowledge/import/raw/*.csv"
OUT_PORTFOLIO = Path("state/normalized/jira-portfolio.json")
OUT_BUGS      = Path("state/normalized/jira-bugs.json")

# --- column names we need (selected by NAME, robust to Jira column reordering) ---
COLS = {
    "key":        "Issue key",
    "type":       "Issue Type",
    "status":     "Status",
    "name":       "Summary",
    "parent":     "Parent",
    "priority":   "Priority",
    "resolution": "Resolution",
}

# --- type routing ---
PORTFOLIO_TYPES = {"epic": "epic", "story": "story", "task": "task"}
BUG_TYPES       = {"bug": "bug"}
SUBTASK_TYPES   = {"sub-task": "sub-task", "subtask": "sub-task"}

# --- status map (locked with operator) ---
STATUS_MAP = {
    "done": "done",
    "dev verified": "done",
    "deployed dev": "done",
    "to do": "not-started",
    "in progress": "in-progress",
    "code review": "in-progress",
    "dev testing": "in-progress",
    "blocked": "blocked",
    "analysis": "analysis",
    "requirement gathering": "analysis",
}

def newest_csv():
    files = sorted(glob.glob(RAW_GLOB))
    if not files:
        sys.exit(f"ABORT: no CSV in {RAW_GLOB}")
    # newest by filename (date-stamped) then mtime as tiebreak
    files.sort(key=lambda f: (os.path.basename(f), os.path.getmtime(f)))
    return files[-1]

def build_index(header):
    idx = {}
    for logical, colname in COLS.items():
        found = None
        for i, h in enumerate(header):
            if h.strip().lower() == colname.lower():
                found = i
                break
        idx[logical] = found  # may be None; handled per-row
    if idx["key"] is None or idx["type"] is None:
        sys.exit(f"ABORT: required columns missing (Issue key / Issue Type). Header had: {header[:10]}...")
    return idx

def cell(row, i):
    if i is None or i >= len(row):
        return ""
    return (row[i] or "").strip()

def map_status(raw):
    return STATUS_MAP.get(raw.strip().lower(), f"unmapped:{raw.strip().lower()}")

def main():
    src = newest_csv()
    with open(src, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.reader(f))
    header, data = rows[0], rows[1:]
    idx = build_index(header)

    portfolio, bugs, subtasks = [], [], []
    type_counts, status_counts = {}, {}
    unmapped_status = set()

    for row in data:
        rawtype = cell(row, idx["type"]).lower()
        key     = cell(row, idx["key"])
        name    = cell(row, idx["name"])
        rawstat = cell(row, idx["status"])
        status  = map_status(rawstat)
        if status.startswith("unmapped:"):
            unmapped_status.add(rawstat)

        rec = {
            "type": None,  # set below
            "name": name,
            "status": status,
            "raw_status": rawstat,
            "source": {"origin": "jira", "ref": key},
            "parent": cell(row, idx["parent"]),
            "priority": cell(row, idx["priority"]),
            "resolution": cell(row, idx["resolution"]),
        }

        type_counts[rawtype] = type_counts.get(rawtype, 0) + 1
        status_counts[rawstat] = status_counts.get(rawstat, 0) + 1

        if rawtype in PORTFOLIO_TYPES:
            rec["type"] = PORTFOLIO_TYPES[rawtype]
            portfolio.append(rec)
        elif rawtype in BUG_TYPES:
            rec["type"] = "bug"
            bugs.append(rec)
        elif rawtype in SUBTASK_TYPES:
            rec["type"] = "sub-task"
            subtasks.append(rec)
        else:
            # unknown type - never guess; flag into portfolio with type unknown
            rec["type"] = "unknown"
            rec["_flag"] = f"unknown Jira type: {rawtype!r}"
            portfolio.append(rec)

    OUT_PORTFOLIO.parent.mkdir(parents=True, exist_ok=True)
    meta = {
        "generated": datetime.now().astimezone().isoformat(),
        "source_file": src,
        "jira_type_counts": type_counts,
        "jira_status_counts": status_counts,
    }
    OUT_PORTFOLIO.write_text(json.dumps({
        **meta, "stream": "portfolio", "count": len(portfolio), "rows": portfolio,
    }, indent=2), encoding="utf-8")
    OUT_BUGS.write_text(json.dumps({
        **meta, "stream": "bugs", "count": len(bugs),
        "subtask_count": len(subtasks), "rows": bugs, "subtasks": subtasks,
    }, indent=2), encoding="utf-8")

    print(f"=== normalize-jira: {src.split('/')[-1]} ===")
    print(f"  total data rows: {len(data)}")
    print(f"  portfolio (epic/story/task): {len(portfolio)}  -> {OUT_PORTFOLIO}")
    print(f"  bugs: {len(bugs)}  -> {OUT_BUGS}")
    print(f"  sub-tasks (flagged, held): {len(subtasks)}")
    print()
    print("  Jira type counts:")
    for t, c in sorted(type_counts.items(), key=lambda x: -x[1]):
        print(f"    {c:4d}  {t}")
    print()
    unknown = sum(1 for r in portfolio if r['type'] == 'unknown')
    if unknown:
        print(f"  WARNING: {unknown} rows had unknown Jira type (flagged, not guessed)")
    if unmapped_status:
        print(f"  WARNING: unmapped statuses (passed through flagged): {sorted(unmapped_status)}")
    else:
        print("  all statuses mapped cleanly")
    refs = sum(1 for r in portfolio if r['source']['ref'])
    print(f"  portfolio rows carrying source ref: {refs}/{len(portfolio)} (enables exact-ref match)")

if __name__ == "__main__":
    main()
