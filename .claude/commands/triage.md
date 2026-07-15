# Triage

Process an owner-authored note, transcript, or meeting summary into the portfolio.
The input follows this command (paste after /triage).

Steps, in order:

1. Read the input and identify:
   - Action items (something to be done, by someone, possibly by a date)
   - Stakeholders mentioned (people with roles/commitments)
   - Roadmap items affected (features, initiatives, decisions)

2. Append each action item to state/action-register.md:
   - Assign the NEXT sequential ACT number. Read the existing register first to
     find the highest number; never reuse or renumber. ACT numbers assigned earlier in the SAME run count as existing - re-read the register, including same-run appends, before each assignment.
   - Fill Action, Owner, Due, Dependency, Status (default OPEN), Opened (today).

3. For each stakeholder mentioned with a new commitment or context, update their
   page in knowledge/people/ (create from _TEMPLATE.md if none exists). Add to
   their Open commitments and Notes log. Do not create pages for passing mentions.

4. For each affected roadmap item, update or create its state/<slug>.yaml from
   _item-template.yaml (stage, next_action, risk as warranted).

5. Output a summary of what changed: ACT numbers created, pages updated, items touched.

Rules:
- Owner-authored input only. Do not process raw third-party source material.
- Do not fabricate. If owner/due/dependency is unstated, leave blank — do not guess.
- Be conservative: a vague mention is not an action item. When unsure, list it in the
  summary as "possible — not recorded" rather than writing a speculative entry.
- Preserve existing register numbering exactly.

## Cross-reference against the existing portfolio (do this BEFORE creating any work item)
Keel already holds a large portfolio (state/) plus a support lane of bugs and note-derived
feature proposals (support/). For EVERY candidate work item you are about to create - each
feature, epic, story, bug, or task - first check whether it already exists, so you never spawn
a silent duplicate. Run, for each candidate, using its name/title as the query:

  python3 /home/keeladmin/keel/tools/find.py --json "<candidate name>"

Read the JSON `verdict` and act:
- EXACT_DUP or LIKELY_MATCH -> do NOT create a new work item. The candidate already exists as
  the top match (its `key`, `name`, `status`, `store`). Instead, record the connection: in the
  action register and the consolidated summary, note "concerns <KEY> (<name>, status <status>,
  <store>) - already in portfolio, no new item created." If the note implies work on that item,
  capture it as an action referencing <KEY>. Do NOT modify <KEY> itself - never change its
  status or fields (Jira/owner owns portfolio status).
- WEAK_MATCH -> create the item as normal, but add to its description: "possible relation to
  <KEY> (<name>) - review." Surface the possible link; let the operator decide.
- NEW -> create the item as described below (features/bugs to support/, per the rules), and
  add to its description: "no portfolio or support match - confirmed new."

This cross-reference spans BOTH state/ and support/. It surfaces connections; it never mutates
existing items. It is annotate-only: propose and flag, never auto-link or auto-change status.

## Work-item creation (epics / features / stories)
When the input describes product work to be built — an epic, a feature, user stories,
or acceptance criteria — create work items from _workitem-template.yaml, not just actions.
When the input clearly describes a defect or bug, or a standalone task to be tracked, create it as a work item with type bug or task written to support/<type>-<slug>.yaml (NOT state/, the portfolio path). A bug/task uses the lighter shape: the template minus the prioritization block (no WSJF/RICE - defects are not portfolio-ranked), status vocabulary open|in-progress|done. Stamp source.origin: keel and leave source.ref blank - the bug originated here and receives its Jira key later, when the import matches and merges it rather than creating a duplicate. Sequential keys per type: BUG-### and TASK-###.

Hierarchy: epic (large body of work) -> feature (a capability) -> story (a single small
user-facing increment) -> acceptance criteria (on the story).

One file per work item: state/<type>-<slug>.yaml. Sequential keys per type: EP-### epics,
FE-### features, ST-### stories. Read existing files to find the next number; never reuse a key. Within a single run, items created earlier in the SAME run count as existing: immediately before EACH key assignment, re-read all keys per type across state/ and support/ (EP/FE/ST/BUG/TASK), including same-run creations, and assign max+1. On collision, advance to the next free number - never renumber an existing file.
Set `parent` to the key of the containing item: a story's containing item is its feature, or the epic directly when no feature applies (feature is optional); a feature's containing item is its epic.

### Content depth — REQUIRED for every work item created
- **Epics**: write a short contextual `description` (what it is and why, 1-3 sentences) and
  first-pass `acceptance_criteria` (3-6 high-level outcomes that mean the epic is done).
- **Features**: write a short contextual `description` and first-pass `acceptance_criteria`
  (3-6 capability-level conditions of satisfaction).
- **Stories**: write `description` in user-story format exactly: "As a <role>, I want
  <capability>, so that <benefit>". Write testable `acceptance_criteria` (Given/When/Then
  or a checklist). Set `size: small`.

### Decomposition — create the stories
For each FEATURE you create or update, DECOMPOSE it into the small stories that deliver it.
Infer the obvious stories a feature requires and create them as ST-### children of that feature,
each in proper user-story format with acceptance criteria. Keep each story SMALL — a single
increment completable in a few days. If a story you would write is too big to be small (covers
multiple roles, multiple workflows, or can't be finished in a few days), do NOT cram it: set
its `size: NEEDS-DECOMPOSITION`, note in its summary that it must be broken down further, and
flag it in the triage summary.

### Draft labeling — provenance
Anything you INFER rather than read explicitly in the source — generated descriptions, first-pass
AC, decomposed stories — must be prefixed "[draft - review] " in that field, so stated content is
distinguishable from generated content. Content the source states explicitly is recorded plain.
Never present inferred AC or stories as if they were stated.

### Scoring
Apply scoring only where components are provided; otherwise leave unscored (surfaces under
Needs prioritization). Do not fabricate WSJF/RICE values from a narrative.

### Summary
Report the hierarchy created: epic/feature/story keys, parent links, which items got drafted
(inferred) descriptions/AC, and any stories flagged NEEDS-DECOMPOSITION.

Distinguish work items from actions: an epic/feature/story is product to be BUILT (state/);
an action is a task someone must DO (action register). A note may produce both.

### Work-item summary must show content
When the triage summary lists work items created, show each item's description and its
acceptance-criteria count (and the AC themselves for stories), not just keys and names, so
the operator can review generated content in chat without opening files.

### Consult the knowledge base first
Before generating, read relevant files in knowledge/, knowledge/context/, knowledge/inbox/, and knowledge/people/
for product, market, strategy, and stakeholder context. Ground generated descriptions,
acceptance criteria, scoring rationale, and drafts in this real context — use the actual product
names, terminology, and constraints found there rather than generic inference. If no relevant
context exists, proceed but say the output is generic for lack of grounding. Never fabricate
facts not supported by the knowledge base or the input.
