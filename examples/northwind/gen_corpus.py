#!/usr/bin/env python3
"""Generate a synthetic portfolio corpus for Northwind Robotics (fictional).

Plants deliberate, reconcile-detectable drift between the two sources:
  - jira-only items      (in Jira, absent from the backlog)
  - backlog-only items   (no NWR key at all)
  - status divergence    (Done in Jira, In Progress in the backlog)
  - title divergence     (same NWR key, reworded title)
  - near-duplicates      (different keys, semantically the same work)
  - embedded keys        (NWR-xxx buried in a free-text Notes column)

Usage:  python3 examples/northwind/gen_corpus.py [dest_dir]
Writes: <dest>/knowledge/import/raw/{Northwind Tech.csv, Northwind Backlog.xlsx}
        <dest>/knowledge/people/*.md
        <dest>/knowledge/inbox/*.md
"""
import csv, os, random, sys
from pathlib import Path

random.seed(20260714)  # deterministic corpus

DEST = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
RAW = DEST / "knowledge" / "import" / "raw"
PEOPLE = DEST / "knowledge" / "people"
TRANS = DEST / "knowledge" / "inbox"  # /process contract: the triage inbox, not a side dir
for d in (RAW, PEOPLE, TRANS):
    d.mkdir(parents=True, exist_ok=True)

TEAM = [
    ("Dana Okafor", "VP Engineering", "engineering", "owns delivery; wants fewer in-flight epics"),
    ("Ravi Menon", "Principal Engineer", "engineering", "fleet routing; skeptical of scope creep"),
    ("Sofia Almeida", "Product Manager", "product", "runs the backlog; source of most intake"),
    ("Tom Brennan", "Customer Success Lead", "customer", "escalation path for pilot accounts"),
    ("Yuki Tanaka", "Staff Designer", "design", "warehouse operator UX"),
    ("Miles Webb", "Data Engineer", "engineering", "telemetry pipeline; on-call rotation"),
    ("Priya Raghavan", "QA Lead", "engineering", "release gating; flags regressions"),
    ("Ben Ostrowski", "Solutions Architect", "field", "pilot deployments at customer sites"),
    ("Ana Ruiz", "Engineering Manager", "engineering", "platform team; capacity planning"),
    ("Chris Ngata", "CTO", "exec", "executive sponsor for the weekly report"),
]
for name, role, group, note in TEAM:
    slug = name.lower().replace(" ", "-")
    (PEOPLE / f"{slug}.md").write_text(
        f"# {name}\n\n"
        f"- Role: {role}\n"
        f"- Group: {group}\n"
        f"- Context: {note}\n\n"
        f"## Notes\n\nSynthetic person. Northwind Robotics is a fictional company\n"
        f"used to exercise Keel end to end. No real data.\n",
        encoding="utf-8")
print(f"people:      {len(TEAM)} files -> {PEOPLE}")

# ---------------------------------------------------------------- Jira export
# Real Jira exports carry 200+ columns; normalize_jira only reads COLS and
# tolerates the rest. We emit the required set plus a few realistic extras.
JIRA_COLS = ["Summary", "Issue key", "Issue id", "Issue Type", "Status",
             "Priority", "Resolution", "Assignee", "Parent", "Created"]

EPICS = [
    ("NWR-100", "Autonomous fleet routing", "In Progress"),
    ("NWR-101", "Warehouse operator console", "In Progress"),
    ("NWR-102", "Telemetry and observability pipeline", "In Progress"),
    ("NWR-103", "Pilot deployment tooling", "To Do"),
    ("NWR-104", "Safety interlock certification", "Analysis"),
]
STORIES = [
    # (key, summary, status, parent, planted-drift tag)
    ("NWR-110", "Path replanning when a lane is blocked", "Done", "NWR-100", ""),
    ("NWR-111", "Charging dock handoff protocol", "In Progress", "NWR-100", ""),
    ("NWR-112", "Fleet heartbeat every 5 seconds", "Code Review", "NWR-100", ""),  # PLANT unmapped_status: "Code Review" not in _CANON -> OTHER class -> Disagree YES by fallback
    ("NWR-113", "Collision avoidance envelope tuning", "Dev Testing", "NWR-100", "jira-only"),
    ("NWR-114", "Route cost function v2", "To Do", "NWR-100", "jira-only"),
    ("NWR-120", "Operator can pause a single robot", "Done", "NWR-101", "status-drift"),
    ("NWR-121", "Live floor map with robot positions", "In Progress", "NWR-101", ""),
    ("NWR-122", "Shift handover summary view", "To Do", "NWR-101", "title-drift"),
    ("NWR-123", "Alert banner for stuck robots", "Blocked", "NWR-101", ""),
    ("NWR-124", "Operator audit log", "To Do", "NWR-101", "jira-only"),
    ("NWR-130", "Ingest robot telemetry to time-series store", "Done", "NWR-102", ""),
    ("NWR-131", "Retention policy for raw telemetry", "In Progress", "NWR-102", ""),
    ("NWR-132", "Latency dashboard for the ops team", "To Do", "NWR-102", "near-dup"),
    ("NWR-133", "Alerting rules for pipeline lag", "Requirement Gathering", "NWR-102", ""),
    ("NWR-140", "One-command site provisioning", "To Do", "NWR-103", ""),
    ("NWR-141", "Pre-flight checklist automation", "Analysis", "NWR-103", ""),
    ("NWR-142", "Site config validation", "To Do", "NWR-103", "embedded-key"),
    ("NWR-150", "Emergency stop response time evidence", "Analysis", "NWR-104", ""),
    ("NWR-151", "Interlock test harness", "To Do", "NWR-104", ""),
    ("NWR-152", "Certification document pack", "To Do", "NWR-104", ""),
]
OWNERS = ["Dana Okafor", "Ravi Menon", "Sofia Almeida", "Yuki Tanaka",
          "Miles Webb", "Priya Raghavan", "Ben Ostrowski", "Ana Ruiz"]

rows = []
iid = 40001
for k, s, st in EPICS:
    rows.append({"Summary": s, "Issue key": k, "Issue id": iid, "Issue Type": "Epic",
                 "Status": st, "Priority": "High", "Resolution": "",
                 "Assignee": random.choice(OWNERS), "Parent": "", "Created": "2026-05-04"})
    iid += 1
for k, s, st, parent, _tag in STORIES:
    rows.append({"Summary": s, "Issue key": k, "Issue id": iid, "Issue Type": "Story",
                 "Status": st, "Priority": random.choice(["High", "Medium", "Low"]),
                 "Resolution": "Done" if st == "Done" else "",
                 "Assignee": random.choice(OWNERS), "Parent": parent, "Created": "2026-05-18"})
    iid += 1

csv_path = RAW / "2026-07-14_Northwind_Tech.csv"
with open(csv_path, "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=JIRA_COLS)
    w.writeheader()
    w.writerows(rows)
print(f"jira csv:    {len(rows)} rows -> {csv_path.name}")

# ------------------------------------------------------------ Excel backlog
# Planted drift vs Jira, all reconcile-detectable:
#   status-drift : NWR-120 Done in Jira, In Progress here
#   title-drift  : NWR-122 reworded
#   jira-only    : NWR-113/114/124 deliberately ABSENT here
#   backlog-only : rows with no NWR key at all
#   near-dup     : "Ops latency dashboard" ~ NWR-132
#   embedded-key : NWR-142 only in the Notes prose, not a key column
import openpyxl
wb = openpyxl.Workbook()
ws = wb.active
ws.title = "Backlog"
HDR = ["Task #", "Priority", "Feature", "Weeks", "Status", "Date", "Owner", "Type"]
ws.append(HDR + ["Notes"])

BACKLOG = [
    # Task # is LOCAL numbering. The Jira ref lives in Notes prose -- that is
    # the only place normalize_backlog scans for it (gated on
    # SOURCE_KEY_PREFIX). A real backlog looks like this: someone types the
    # ticket into a notes cell, or forgets to.
    ("T-01", "P1", "Autonomous fleet routing", 12, "IP", "2026-05-04", "Ravi Menon", "epic", "Epic NWR-100"),
    ("T-02", "P1", "Warehouse operator console", 10, "IP", "2026-05-04", "Yuki Tanaka", "epic", "Epic NWR-101"),
    ("T-03", "P2", "Telemetry and observability pipeline", 8, "IP", "2026-05-11", "Miles Webb", "epic", "Epic NWR-102"),
    ("T-04", "P2", "Pilot deployment tooling", 6, "NYS", "2026-06-01", "Ben Ostrowski", "epic", "Epic NWR-103"),
    ("T-05", "P1", "Safety interlock certification", 9, "NYS", "2026-06-01", "Priya Raghavan", "epic", "Epic NWR-104"),
    ("T-06", "P1", "Path replanning when a lane is blocked", 3, "Done", "2026-05-18", "Ravi Menon", "story", "NWR-110 shipped"),
    ("T-07", "P1", "Charging dock handoff protocol", 2, "IP", "2026-05-18", "Ravi Menon", "story", "tracking under NWR-111"),
    ("T-08", "P2", "Fleet heartbeat every 5 seconds", 1, "IP", "2026-05-25", "Miles Webb", "story", "NWR-112"),
    # DRIFT status: Done in Jira, still IP here
    ("T-09", "P1", "Operator can pause a single robot", 2, "IP", "2026-05-18", "Yuki Tanaka", "story", "NWR-120 - eng marked done but the confirm dialog never shipped"),
    ("T-10", "P1", "Live floor map with robot positions", 4, "IP", "2026-05-25", "Yuki Tanaka", "story", "NWR-121"),
    # DRIFT title: Jira says "Shift handover summary view"
    ("T-11", "P2", "End-of-shift handover report", 2, "NYS", "2026-06-08", "Sofia Almeida", "story", "same work as NWR-122"),
    ("T-12", "P2", "Alert banner for stuck robots", 1, "Blocked", "2026-06-01", "Yuki Tanaka", "story", "NWR-123 blocked on interlock ruling"),
    ("T-13", "P2", "Ingest robot telemetry to time-series store", 3, "Done", "2026-05-11", "Miles Webb", "story", "NWR-130"),
    ("T-14", "P2", "Retention policy for raw telemetry", 2, "IP", "2026-06-08", "Miles Webb", "story", "NWR-131"),
    ("T-15", "P3", "Latency dashboard for the ops team", 2, "NYS", "2026-06-15", "Miles Webb", "story", "NWR-132"),
    ("T-16", "P2", "One-command site provisioning", 3, "NYS", "2026-06-15", "Ben Ostrowski", "story", "NWR-140"),
    ("T-17", "P3", "Pre-flight checklist automation", 2, "NYS", "2026-06-22", "Ben Ostrowski", "story", "NWR-141"),
    ("T-18", "P1", "Emergency stop response time evidence", 4, "NYS", "2026-06-01", "Priya Raghavan", "story", "NWR-150 - auditor needs this"),
    ("T-19", "P2", "Interlock test harness", 3, "NYS", "2026-06-22", "Priya Raghavan", "story", "NWR-151"),
    # EMBEDDED KEY: only discoverable by scanning prose
    ("T-20", "P3", "Validate site configs before rollout", 2, "NYS", "2026-06-29", "Ben Ostrowski", "story", "field team re-raised this; already tracked as NWR-142"),
    # NEAR-DUP of NWR-132: no ref, semantically the same work
    ("T-21", "P3", "Ops latency dashboard", 2, "NYS", "2026-06-29", "Miles Webb", "story", "Tom asked for this after the pilot review"),
    # BACKLOG-ONLY: never entered Jira, no ref in prose
    ("T-22", "P2", "Bulk robot firmware rollback", 3, "NYS", "2026-07-06", "Ana Ruiz", "story", "raised after the 6/30 incident"),
    ("T-23", "P1", "Pilot account onboarding runbook", 2, "NYS", "2026-07-06", "Tom Brennan", "story", "CS needs this before the next two pilots"),
    ("T-24", "P3", "Warehouse noise profile study", 4, "NYS", "2026-07-13", "Yuki Tanaka", "story", ""),
    ("T-25", "P2", "Multi-site fleet capacity model", 5, "NYS", "2026-07-13", "Ana Ruiz", "feature", ""),
    # PLANT ambiguous-paraphrase: ref-less epic paraphrasing EP-001 "Autonomous fleet routing"
    # (empty Notes -> no NWR key -> title-overlap route; overlap 0.667 -> AMBIGUOUS band)
    ("T-26", "P2", "Autonomous vehicle fleet navigation", 8, "NYS", "2026-07-13", "Ravi Menon", "epic", ""),
]
for r in BACKLOG:
    ws.append(list(r))
xlsx_path = RAW / "Northwind Backlog.xlsx"
wb.save(xlsx_path)
print(f"backlog xlsx: {len(BACKLOG)} rows -> {xlsx_path.name}")

# ------------------------------------------------------------------- config
# The corpus ships its own prefix. Free-text key scanning is gated on this;
# inheriting another deployment's prefix silently finds zero refs.
import json as _json
(DEST / "keel.config.json").write_text(
    _json.dumps({"SOURCE_KEY_PREFIX": "NWR"}, indent=2) + "\n", encoding="utf-8")
print("config:      SOURCE_KEY_PREFIX=NWR -> keel.config.json")

# ------------------------------------------------------------------- oracle
# Verified landings (build #11, 2026-07-17). Keyed by src_ref / src_name ONLY:
# keel keys are assignment-order-dependent and must never be asserted.
# RCA-1 preventive: a plant does not exist without its assertion here.
EXPECT = {
    "backlog_reconcile": {
        "buckets": {"changed": 21, "gap": 3, "conflict": 0, "ambiguous": 1,
                    "duplicate": 0, "completed": 0, "done_gap": 0},
        "match_modes": {"ref": 20, "title": 1},
        "gap_src_names": ["Bulk robot firmware rollback",
                          "Pilot account onboarding runbook",
                          "Warehouse noise profile study"],
        "plants": {
            "status_drift": {"src_ref": "NWR-120", "src_status": "IP", "keel_status": "done"},
            "title_drift":  {"src_ref": "NWR-122", "src_name": "End-of-shift handover report",
                             "keel_name": "Shift handover summary view"},
            "embedded_key": {"src_ref": "NWR-142", "match_mode": "ref"},
            "ambiguous_paraphrase": {"src_name": "Autonomous vehicle fleet navigation", "keel_name": "Autonomous fleet routing", "keel_key": "EP-001", "bucket": "ambiguous", "overlap": 0.667},
            "unmapped_status": {"src_ref": "NWR-112", "jira_raw": "Code Review",
                                "note": "exercises canon-map OTHER fallback; unmapped statuses must surface loudly"},
            "near_dup":     {"src_name": "Ops latency dashboard", "match_mode": "title",
                             "shares_item_with_ref": "NWR-132"},
        },
    },
    "state_items": {"count": 25},
    "export": {
        "sheets": ["Cross-Source", "Source-Only", "Keel-Origin",
                   "Unconfirmed", "Semantic Matches", "Legend"],
        "cross_source_rows": 25,
        "sources_dist": {"BACKLOG+JIRA": 20, "JIRA": 5},
        "disagree_yes_jira_keys": ["NWR-112", "NWR-120"],
        "no_disagree_jira_keys": ["NWR-122"],
        "source_only_rows": 3,
        "keel_origin_rows": 0,
        "unconfirmed_rows": 0,
    },
}
(DEST / "expectations.json").write_text(_json.dumps(EXPECT, indent=2) + "\n", encoding="utf-8")
print("expect:      landing assertions -> expectations.json")

# --------------------------------------------------------------- transcripts
MEETINGS = [
 ("2026-06-30-fleet-sync.md", "Fleet Sync", "Dana Okafor, Ravi Menon, Miles Webb",
  """Ravi walked through the replanning work (NWR-110) - shipped and stable in the
pilot. Charging dock handoff (NWR-111) is close but the protocol still drops a
frame when two robots queue. Miles raised that heartbeat at 5s (NWR-112) is
generating more telemetry volume than the retention policy assumes.

Dana asked whether collision envelope tuning belongs in this quarter at all.
Ravi: it is in Jira but nobody has picked it up.

Actions: Ravi to fix the dock handoff frame drop by Friday. Miles to size the
retention change before we widen the heartbeat. Dana to decide on envelope
tuning at the next portfolio review."""),
 ("2026-07-02-console-review.md", "Operator Console Review", "Yuki Tanaka, Sofia Almeida, Tom Brennan",
  """Yuki demoed the floor map. Tom flagged that operators at the Reno pilot still
cannot pause a single robot without the confirm dialog - engineering marked that
story done but the dialog never shipped.

Sofia noted the shift handover view is written up two different ways: Jira calls
it a summary view, the backlog calls it an end-of-shift report. Same work.

Tom asked for an onboarding runbook before the next two pilots. Not in Jira.

Actions: Yuki to reopen the pause-robot work. Sofia to reconcile the handover
naming. Tom to draft the runbook requirements."""),
 ("2026-07-06-incident-postmortem.md", "Firmware Incident Postmortem", "Ana Ruiz, Priya Raghavan, Miles Webb",
  """Ana walked the 6/30 firmware rollout that bricked four robots at the Tacoma
site. Root cause: no rollback path. Priya noted QA had no gate for firmware
because firmware is not in the portfolio at all.

Miles: the telemetry pipeline saw the failure 40 minutes before the site called
it in, but nobody was watching the lag.

Actions: Ana to raise bulk firmware rollback. Priya to add a firmware gate to
release checks. Miles to propose alerting rules for pipeline lag."""),
 ("2026-07-08-safety-cert.md", "Safety Interlock Certification", "Priya Raghavan, Chris Ngata, Dana Okafor",
  """Priya reported the certification pack needs emergency-stop response evidence
before the auditor visit. The test harness does not exist yet.

Chris asked the direct question: does this block the two new pilots? Priya said
yes for any site with human co-presence.

Dana pushed back on sequencing - the interlock ruling is also blocking the stuck
robot alert banner.

Actions: Priya to scope the harness this week. Dana to sequence interlock ahead
of console work. Chris wants a date at the next review."""),
 ("2026-07-10-pilot-readiness.md", "Pilot Readiness", "Ben Ostrowski, Tom Brennan, Sofia Almeida",
  """Ben walked site provisioning: still a manual runbook, roughly a day per site.
One-command provisioning is in the backlog but unstaffed.

Field team raised duplicate site config validation - already tracked as NWR-142,
but they re-raised it because they could not find it.

Tom: two pilots land in three weeks and neither has an onboarding path.

Actions: Ben to close the duplicate. Sofia to pull provisioning into the next
sprint if capacity allows. Tom to escalate the runbook gap to Dana."""),
 ("2026-07-13-portfolio-review.md", "Portfolio Review", "Chris Ngata, Dana Okafor, Sofia Almeida",
  """Chris opened with the same question as last quarter: how many epics are in
flight. Answer: five, which is two more than the team can staff.

Sofia noted the backlog and Jira disagree in enough places that the roadmap
cannot be trusted - several items exist in one and not the other.

Dana proposed freezing pilot tooling until interlock certification lands.

Actions: Sofia to reconcile the two sources before the next review. Dana to
bring a staffing plan. Chris to rule on the epic freeze."""),
]
for fname, title, attendees, body in MEETINGS:
    (TRANS / fname).write_text(
        f"# {title}\n\n**Date:** {fname[:10]}  \n**Attendees:** {attendees}\n\n{body}\n",
        encoding="utf-8")
print(f"transcripts: {len(MEETINGS)} files -> {TRANS}")
print("\nPlanted drift (what reconcile should find):")
print("  jira-only:     NWR-113, NWR-114, NWR-124, NWR-133, NWR-152")
print("  backlog-only:  4 rows with no key (firmware rollback, onboarding runbook,")
print("                 noise study, capacity model)")
print("  status-drift:  NWR-120 (Done in Jira, IP in backlog)")
print("  title-drift:   NWR-122 (summary view vs end-of-shift report)")
print("  near-dup:      'Ops latency dashboard' ~ NWR-132")
print("  embedded-key:  NWR-142 in Notes prose only")
