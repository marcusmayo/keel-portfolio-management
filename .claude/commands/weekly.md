# Weekly

Generate the Weekly Operating Priorities and Performance Report for the executive sponsor, in the
EXACT format below. This is the operator's end-of-week report, due Friday before 5:30pm ET. GENERATE ONLY —
produce the draft for the operator to review and send himself. NEVER send it anywhere.

## Determine the week
Cover Monday through Friday of the current week, unless the operator gives a week-ending date in the command
(e.g. "/weekly 2026-06-26"). Compute the Friday date for the "Week Ending" line.

## Sources (read these for the week's range)
- state/daily-logs/<date>.md for each day Mon-Fri — read both the "## Actions" section (the structured
  spine: what changed, with timestamps and keys) and any richer narrative headings (what was covered,
  product facts, follow-ups).
- state/action-register.md — actions opened, in-progress, blocked, or closed (DONE) this week.
- state/*.yaml work items — items whose status changed this week (e.g. moved to in-progress / done).
- knowledge/ and knowledge/people/ — for correct names, org terminology, and context only.

## EXACT output format (match this structure and headings)

Weekly Operating Priorities and Performance Report
As prepared by: the operator
Week Ending: Friday, <DATE>

Operating Priorities:
<Group the week's work under the operating priorities it advanced. For each priority, a name line
then its activities:>
- <Priority name>
  Key Activities:
  - <activity, grounded in the daily logs / action register / status changes>
  - <activity>

Subscription Summary (Active Customers): <number if known from context, else N/A>
Subscription Summary (Free Trial Customers): <number if known, else N/A>

Support:
- <support items handled this week from the logs; else N/A>

Performance Analysis:
- What's Going Well:
  - <grounded positive from the week>
- What's Not Going Well:
  - <grounded blocker / risk from the week>

Resource Needs:
Budget: <N/A unless the logs indicate a need>
Staff: <N/A unless the logs indicate a need>

Additional Notes:
- <material item not captured above; else N/A>

Recommendations:
- <recommendation to the CEO, if any; else N/A>

## Rules
- PLAIN TEXT ONLY. This report is pasted into an email to the CEO, not a markdown viewer. NEVER wrap any text in ** or * for bold/italic. NEVER use # or ## headers. Section headings are plain text followed by a colon exactly as in the EXACT format above (e.g. "Operating Priorities:" not "**Operating Priorities:**"). If you find yourself adding any markdown formatting character (* # _ `), remove it - the output must render identically in plain text.
- Ground EVERY line in the actual daily logs, action register, or work-item changes for the week.
  Do NOT invent activities or numbers. If a section has no real content, write N/A — never pad.
- VOICE — write in FIRST PERSON as the operator, as if the operator personally wrote this report to his CEO.
  Use "I" throughout: "I met with...", "I reviewed...", "I decided...", "I'm recommending...".
  Natural, direct executive prose. No corporate filler, no hedging "just".
- Use correct org and stakeholder names as recorded in knowledge/people/; never guess names.
- Flag anything inferred or uncertain with [draft - review] so the operator can verify before sending.
- This is a generation skill: consult knowledge/, knowledge/context/, knowledge/inbox/, knowledge/people/
  for grounding (names, terminology, context), as the other generation skills do.
- AUTO-SAVE: after generating, save the report to state/weekly-reports/<week-ending-date>.md (use the
  Friday week-ending date, e.g. 2026-06-26.md). Create the directory if needed. If a file for that week
  already exists, overwrite it (a re-run replaces the prior draft for the same week). Then state plainly
  that this is a draft for the operator's review and editing before he sends it to leadership, and confirm the path
  it was saved to.

## Bullet style — SHORT, like the reference report
Match the altitude of the example EOW reports exactly. Each Key Activity is ONE short line, the kind
a busy executive scans in seconds. Real examples of the right level:
   – "Completed product training with a team member on our two core products."
   – "Met with a team member to coordinate efforts with account leads."
   – "Reviewed training progress with a team member."

RULES for every bullet:
  - ONE line. No second sentence, no clause after a dash, no parenthetical explanation.
  - NO metrics, scores, percentages, or targets (no "1/10", "4/10", "70% completion", "30% reduction",
    "9-step", "+40%"). Those belong in a detailed proposal, not a weekly to the CEO.
  - NO lists of specifics packed into one bullet. If something genuinely needs two points, use two bullets.
  - State WHAT happened or WHAT was decided, plainly. Trust the reader; do not over-explain or justify.
  - Aim for 3-5 bullets per priority maximum. Fewer, higher-level priorities (3-4 total) is better than many.

Compress aggressively. "Reviewed our competitive positioning against the main virtual-office players;
our edge is BPO/CCaaS specificity and our biggest gap is the lack of a free tier." is ONE good bullet —
not a paragraph with every competitor named and every gap scored.

## Bullet style — SHORT, like the reference report
Match the altitude of the example EOW reports exactly. Each Key Activity is ONE short line, the kind
a busy executive scans in seconds. Real examples of the right level:
   – "Completed product training with a team member on our two core products."
   – "Met with a team member to coordinate efforts with account leads."
   – "Reviewed training progress with a team member."

RULES for every bullet:
  - ONE line. No second sentence, no clause after a dash, no parenthetical explanation.
  - NO metrics, scores, percentages, or targets (no "1/10", "4/10", "70% completion", "30% reduction",
    "9-step", "+40%"). Those belong in a detailed proposal, not a weekly to the CEO.
  - NO lists of specifics packed into one bullet. If something genuinely needs two points, use two bullets.
  - State WHAT happened or WHAT was decided, plainly. Trust the reader; do not over-explain or justify.
  - Aim for 3-5 bullets per priority maximum. Fewer, higher-level priorities (3-4 total) is better than many.

Compress aggressively. "Reviewed our competitive positioning against the main virtual-office players;
our edge is BPO/CCaaS specificity and our biggest gap is the lack of a free tier." is ONE good bullet —
not a paragraph with every competitor named and every gap scored.

## Executive altitude — what leadership sees and does NOT see
This is a high-level executive report. Leadership reads what the operator DID — who they met, what they learned, what
he decided, what's outstanding — NOT how any of it was recorded or processed.

NEVER use internal/system language. Specifically, do NOT write:
  - "transcript", "ingested", "staged", "context library", "triage inbox", "processed", "work-item portfolio"
  - work-item keys or counts (EP-002, FE-001, ACT-007; "5 epics, 9 features, 20 stories")
  - prioritization jargon (WSJF, RICE, "unscored", "discovery stage")

TRANSLATE Keel's internal actions into business language:
  - reviewing a meeting recording/transcript  -> "I met with X" / "in my product training with X"
  - building the work-item backlog from it     -> "I mapped out the initial product backlog / roadmap"
  - staging a PRD/doc as context               -> "I reviewed the <name> PRD/plan"
  - opening tracked actions                     -> "follow-ups I opened" / "items I'm tracking"
  - reconciling the org chart                   -> "I confirmed the org structure and key stakeholders"

Keep it to themes and decisions. Reference PEOPLE (real names), INFORMATION learned, DECISIONS made,
and FOLLOW-UPS outstanding. A specific product name (e.g. a competitor, a feature) is fine; an internal
key or a process verb is not. Stay strictly within the requested format and altitude.
