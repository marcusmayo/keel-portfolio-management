#!/usr/bin/env python3
"""draft_item_write.py -- safely write a [draft - review] description + AC into
a work item's YAML. Called by the /draft-item skill after the LLM composes the
draft. Only touches description + acceptance_criteria; backs up the file.

Usage:
  python3 tools/draft_item_write.py --key ST-999 \
    --desc "As an admin, I want ... so that ..." \
    --ac "Given ..., When ..., Then ..." \
    --ac "Given ..., When ..., Then ..."
"""
import argparse, glob, re, shutil, sys
from datetime import date as _date
from pathlib import Path

PREFIX = "[draft - review] "

def find_file(key):
    for f in sorted(glob.glob("state/*.yaml") + glob.glob("support/*.yaml")):
        if Path(f).stem.startswith("_"):
            continue
        t = Path(f).read_text(encoding="utf-8")
        if re.search(rf'^\s*key:\s*"?{re.escape(key)}"?', t, re.M):
            return f, t
    return None, None

def has_real_desc(t):
    dm = re.search(r'^  description:\s*"(.*)"\s*$', t, re.M)
    if dm:
        d = re.sub(r'\[\s*draft\s*[-\u2013\u2014]\s*review\s*\]\s*', '', dm.group(1)).strip()
        return len(d) >= 30 and "Imported from Jira" not in dm.group(1)
    # block scalar
    if re.search(r'^  description:\s*[>|]', t, re.M):
        return True
    return False

def esc(s):
    return s.replace('\\', '\\\\').replace('"', '\\"')


def next_key(prefix):
    """Highest existing PREFIX-N across state/, numeric. Returns next N."""
    import glob
    hi = 0
    for f in glob.glob("state/*.yaml"):
        for m in re.finditer(rf'key:\s*"?{prefix}-(\d+)', Path(f).read_text(encoding="utf-8")):
            hi = max(hi, int(m.group(1)))
    return hi + 1

def infer_type(text):
    """Infer epic/feature/story from phrasing. Explicit 'epic:'/'feature:'/'story:'
    prefix wins; else default story."""
    t = text.strip().lower()
    for typ in ("epic", "feature", "story"):
        if t.startswith(typ + ":"):
            return typ, text.split(":", 1)[1].strip()
    if t.startswith("as a ") or t.startswith("as an "):
        return "story", text.strip()
    # broad-theme cues -> epic; capability cues -> feature; else story
    if any(w in t for w in ("initiative", "theme", "overarching", "program of")):
        return "epic", text.strip()
    if any(w in t for w in ("ability to", "capability", "support for", "feature to")):
        return "feature", text.strip()
    return "story", text.strip()

def slugify(name):
    import re as _re
    s = _re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
    return s[:50] or "item"

TYPE_PREFIX = {"epic": "EP", "feature": "FE", "story": "ST"}

def create_item(text):
    """Create a new bare item from text. Returns (key, filepath, name, typ)."""
    typ, body = infer_type(text)
    prefix = TYPE_PREFIX[typ]
    n = next_key(prefix)
    key = f"{prefix}-{n:03d}"
    # derive a short name from the body (first ~8 words, or the 'I want X' clause)
    m = re.search(r'i want (?:to )?(.+?)(?:,| so that|\.|$)', body, re.I)
    name = (m.group(1) if m else body)[:60].strip().rstrip('.,')
    name = name[0].upper() + name[1:] if name else "New item"
    slug = f"{typ}-{slugify(name)}"
    today = _date.today().isoformat()
    fpath = Path(f"state/{slug}.yaml")
    i = 2
    while fpath.exists():
        fpath = Path(f"state/{slug}-{i}.yaml"); i += 1
    fpath.write_text(f'''workitem:
  type: {typ}
  key: {key}
  name: "{esc(name)}"
  slug: {fpath.stem}
  summary: "{esc(name)}"

  parent: ""

  description: ""

  acceptance_criteria: []

  size: ""

  stage: discovery
  status: unscored
  next_action: ""
  next_action_ref: ""
  source: {{origin: keel, ref: ""}}

  prioritization:
    wsjf: {{user_business_value: "", time_criticality: "", risk_reduction_opportunity: "", job_size: "", score: ""}}
    rice: {{reach: "", impact: "", confidence: "", effort: "", score: ""}}
    status: unscored

  priority_override: {{rank: "", reason: "", set_by: "", date: ""}}

  stakeholders: []
  flag: draft-inferred
  updated: {today}
''', encoding="utf-8")
    return key, str(fpath), name, typ


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--key", default="")
    ap.add_argument("--create-text", default="", help="create a NEW item from this text (no key needed)")
    ap.add_argument("--desc", required=True)
    ap.add_argument("--ac", action="append", default=[])
    ap.add_argument("--force", action="store_true", help="write even if item has content")
    a = ap.parse_args()

    if a.create_text:
        key, fpath, name, typ = create_item(a.create_text)
        print(f"created new {typ} {key}: {name}")
        print(f"  file: {fpath}")
        a.key = key  # fall through to draft-writing below

    if not a.key:
        sys.exit("ABORT: provide --key (existing item) or --create-text (new item)")

    f, t = find_file(a.key)
    if not f:
        sys.exit(f"ABORT: no item with key {a.key}")
    if has_real_desc(t) and not a.force:
        sys.exit(f"ABORT: {a.key} already has an authored description. Use /apply-edits to "
                 f"review existing drafts, or --force to overwrite (not recommended).")

    lines = t.splitlines(keepends=True)

    # replace description line (single-line quoted form assumed for bare items)
    desc_val = PREFIX + a.desc.strip()
    new_desc = f'  description: "{esc(desc_val)}"\n'
    di = next((i for i, l in enumerate(lines) if re.match(r'^  description:\s*("?.*"?)?\s*$', l)), None)
    if di is None:
        sys.exit("ABORT: no description field found")
    # handle block scalar (multi-line) by replacing through its continuation
    if re.match(r'^  description:\s*[>|]', lines[di]):
        j = di + 1
        while j < len(lines) and (lines[j].strip() == "" or re.match(r'^    ', lines[j])):
            j += 1
        lines[di:j] = [new_desc]
    else:
        lines[di] = new_desc

    # replace acceptance_criteria
    ai = next((i for i, l in enumerate(lines) if re.match(r'^  acceptance_criteria:', l)), None)
    if ai is None:
        sys.exit("ABORT: no acceptance_criteria field found")
    ac_block = ["  acceptance_criteria:\n"]
    for line in a.ac:
        ac_block.append(f'    - "{esc(PREFIX + line.strip())}"\n')
    if not a.ac:
        ac_block = ['  acceptance_criteria: []\n']
    # find extent of existing AC
    if re.match(r'^  acceptance_criteria:\s*\[\]', lines[ai]):
        lines[ai:ai+1] = ac_block
    else:
        j = ai + 1
        while j < len(lines) and (re.match(r'^    - ', lines[j]) or lines[j].strip() == ""):
            if lines[j].strip() == "" and j+1 < len(lines) and not re.match(r'^    - ', lines[j+1]):
                break
            j += 1
        lines[ai:j] = ac_block

    shutil.copy2(f, f + ".pre-draftitem")
    Path(f).write_text("".join(lines), encoding="utf-8")
    print(f"wrote draft to {a.key} ({f})")
    print(f"  description: {desc_val[:80]}...")
    print(f"  AC lines: {len(a.ac)}")
    print(f"  backup: {f}.pre-draftitem")
    print(f"Review in the Keel-Origin export; approve via removing [draft - review] + /apply-edits.")

if __name__ == "__main__":
    main()
