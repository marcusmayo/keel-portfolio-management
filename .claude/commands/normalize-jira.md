# Normalize Jira

Read-only. Map a Jira CSV export (flattened in knowledge/inbox/) into canonical work-item proposals, stamped with provenance, for reconcile to consume. NEVER write, create, move, or modify anything. This emits proposals to the chat; reconcile compares them and the operator approves before any state changes.

## Input
A Jira artifact in knowledge/inbox/ whose frontmatter source is a Jira CSV export (e.g. source: <Company> Tech.csv). The body is the upload-flattened form: frontmatter fence, then a `### Sheet: <name>` block containing CSV (header row + data rows). The leading BOM is stripped at upload. If asked for a specific artifact, use it; otherwise list Jira-class artifacts in the inbox and ask which to normalize.

## Column mapping (the Jira export header)
Header: Issue Type, Issue key, Issue id, Summary, Assignee, Assignee Id, Reporter, Reporter Id, Priority, Status, Resolution, Created, Updated, Due date. Map each row:
- Issue key  -> source.ref (the Jira key, e.g. PROJ-63 - a clean column value, NOT buried in prose; this is the cross-source match anchor for reconcile)
- Summary    -> name
- Issue Type -> type and routing (see type routing)
- Status + Resolution -> status (see done-class set and status map)
- Priority   -> priority context (e.g. Medium, High) -> priority_override.reason context, NOT a WSJF/RICE score
- Issue id   -> retain as secondary source reference context, not a canonical key
- Assignee   -> stakeholder context if present
- Created, Updated, Due date, Reporter -> contextual only

Stamp every emitted item: source.origin: jira, source.ref: the Issue key.

## Type routing - this is the key difference from the backlog normalizer
Jira types do not all map to the portfolio. Route by Issue Type:
- Epic  -> portfolio work item, type epic
- Story -> portfolio work item, type story
- Bug      -> support lane: type bug, written to support/ convention (NON-portfolio). Carries source.origin: jira, source.ref: the Issue key.
- Sub-task -> support lane: type task (a sub-task is tracked work, not portfolio altitude), support/ convention, NON-portfolio.
- Task (standalone) -> FLAG as "needs operator decision: standalone task". Do NOT auto-place. The operator rules per-item whether it is portfolio, support-lane, or out-of-scope. (Jira has no Feature tier; Features are never imported - they are synthesized later via decompose, a separate action.)

## Done-class set - a SET of statuses, not one value
An item is a completion candidate (done-class) if Status is in {Done, DEV Verified, Deployed DEV} OR Resolution is Done. Flag such items done-class; reconcile proposes marking the matched portfolio item done, never auto-applies. Non-done statuses map straightforwardly: To Do/Requirement Gathering/Analysis -> backlog/discovery; In Progress/Code Review/DEV Testing -> in-progress; Blocked -> blocked. Any status not recognized -> status: unknown, flagged.

## Parent linkage - none in this export
This Jira export carries no Parent or Epic-Link column. Imported items land FLAT: parent empty. Do not infer epic-story membership from keys or titles during normalization; that is a separate, proposed step at reconcile/decompose. Every portfolio item comes in with an empty parent.

## Draft labeling
All inferred content is proposed. Prefix any generated description with "[draft - review] ". These canonical proposals are inputs to reconcile, not committed items.

## Output (hold-in-output, no files written)
Emit to the chat, do not write to disk:
1. Per-item canonical proposals, grouped by destination: PORTFOLIO (epics/stories) and SUPPORT LANE (bugs/sub-tasks). For each: type, name, status (done-class flagged), priority context, source.origin: jira, source.ref (Issue key), parent (empty).
2. TYPE HISTOGRAM - counts by Issue Type (Epic / Story / Bug / Sub-task / Task) and the destination split (portfolio vs support lane vs flagged-task), so the routing is visible before reconcile.
3. DONE-CLASS COUNT - how many items are completion candidates (Status in the done set or Resolution Done), since reconcile will propose marking matched items done.
4. NEEDS OPERATOR DECISION - standalone Tasks (each listed), and any unknown status. These need a ruling before reconcile resolves them.
5. SUMMARY - total rows read, portfolio vs support vs flagged counts, done-class count, and a one-line statement that these are proposals for reconcile, nothing written.

## Rules
- Read-only. Emit proposals to chat; never write, create, move, or modify. No staging files - hold output in chat for reconcile to consume in the same session.
- Route by Issue Type: Epic/Story -> portfolio, Bug/Sub-task -> support lane, standalone Task -> flagged for operator. Never auto-place a standalone Task.
- Done-class is the SET {Done, DEV Verified, Deployed DEV} or Resolution=Done; mark, never auto-apply.
- Issue key is the cross-source match anchor (clean column); it is a proposed link for reconcile, never an auto-merge.
- Items land flat (empty parent); membership is inferred later, proposed never assumed.
- Dates are ET (box is America/New_York).
- This does not reconcile and does not apply. It normalizes one source to canonical proposals. Reconcile compares; the operator approves; apply writes.
