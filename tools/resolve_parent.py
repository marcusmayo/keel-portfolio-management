#!/usr/bin/env python3
"""Shared parent resolver for Jira-imported items.

Jira stores parent as an internal numeric ID (e.g. 10100), not an issue key.
Keel hierarchy needs the parent expressed as a Keel key (EP-/FE-/ST-). Chain:
  parent internal ID --(CSV id->key map)--> parent source key --(state ref index)--> parent Keel key

Best-effort by design: returns "" if the parent isn't resolvable yet (e.g. the
parent hasn't landed in the portfolio). Callers leave parent blank; a re-run of
the backfill catches stragglers once all items exist. No LLM, stdlib + nothing else.
"""
import csv, re, glob
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "state"
RAW = ROOT / "knowledge" / "import" / "raw"

def _newest_csv():
    files = sorted(RAW.glob("*.csv"))
    if not files:
        raise SystemExit(f"ERROR: no CSV in {RAW}")
    return files[-1]

def build_id_to_nge(csv_path=None):
    """Map every Jira internal ID -> its issue key, from the CSV's own columns."""
    csv_path = csv_path or _newest_csv()
    with open(csv_path, newline="", encoding="utf-8-sig") as fh:
        r = csv.reader(fh)
        hdr = next(r)
        id_i = hdr.index("Issue id")
        key_i = hdr.index("Issue key")
        m = {}
        for row in r:
            if len(row) > max(id_i, key_i) and row[id_i].strip() and row[key_i].strip():
                m[row[id_i].strip()] = row[key_i].strip()
    return m

def build_nge_to_keel():
    """Map source ref -> Keel key, read from landed state/ YAMLs (key: + ref:)."""
    m = {}
    for f in glob.glob(str(STATE / "*.yaml")):
        if Path(f).stem.startswith("_"):
            continue
        txt = Path(f).read_text(encoding="utf-8")
        km = re.search(r"^\s*key:\s*([A-Z]+-\d+)", txt, re.M)
        rm = re.search(r"^\s*source:.*ref:\s*([A-Z]+-\d+)", txt, re.M)
        if km and rm:
            m[rm.group(1)] = km.group(1)
    return m

class Resolver:
    def __init__(self, csv_path=None):
        self.id2nge = build_id_to_nge(csv_path)
        self.nge2keel = build_nge_to_keel()
    def resolve(self, parent_internal_id):
        """parent internal ID -> Keel key, or '' if not resolvable."""
        pid = str(parent_internal_id or "").strip()
        if not pid:
            return ""
        nge = self.id2nge.get(pid, "")
        if not nge:
            return ""
        return self.nge2keel.get(nge, "")

if __name__ == "__main__":
    r = Resolver()
    print(f"id->nge map: {len(r.id2nge)} entries")
    print(f"nge->keel map: {len(r.nge2keel)} entries")
    # spot-check the sample parents we saw: 10100, 14514, 10096, 10372
    for pid in ("10100", "14514", "10096", "10372"):
        nge = r.id2nge.get(pid, "(no nge)")
        keel = r.resolve(pid)
        print(f"  parent ID {pid} -> {nge} -> Keel {keel or '(unresolved)'}")
