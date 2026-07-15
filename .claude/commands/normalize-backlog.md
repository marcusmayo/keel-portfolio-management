# Normalize Backlog

Read-only. Map a backlog-export artifact (a flattened xlsx sitting in knowledge/inbox/) into canonical work-item proposals, stamped with provenance, for reconcile to consume. NEVER write, create, move, or modify anything. This emits proposals to the chat; reconcile compares them and the operator approves before any state changes.

## Input
A backlog artifact in knowledge/inbox/ whose frontmatter source ends in .xlsx (e.g. source: Backlog 2026.xlsx). The body is the upload-flattened form: frontmatter fence, then one or more `### Sheet: <name>` blocks, each containing CSV (header row + data rows). Read every `### Sheet:` block; an empty sheet contributes no block. If asked for a specific artifact, use it; otherwise list backlog-class artifacts in the inbox and ask which to normalize.

## Column mapping (the verified header map)
The backlog CSV header is: Task #, Priority, Feature, Weeks, Status, Date, Owner, Type, Notes. Map each row to a canonical work item:
- Feature  -> name (this column is the item TITLE, not a tier indicator)
- Type     -> type (see type rules)
- Status   -> status (see status value-map)
- Weeks    -> job_size / effort hint (numeric weeks; blank -> leave empty)
- Priority -> priority bucket (e.g. "0. Critical", "1. High", "3. Low") -> priority_override.reason context, NOT a WSJF/RICE score
- Notes    -> description (draft-labeled) + embedded-key extraction (see ref rules)
- Task #   -> retain as the source row identifier in source.ref context (not a canonical key)
- Date, Owner -> contextual only; Owner is often a non-breaking-space placeholder (treat as empty)

Stamp every emitted item: source.origin: backlog-xlsx, source.ref: the extracted source key if present (see ref rules), else "".

## Type rules - NEVER guess
- Recognized values: epic, feature, story (case-insensitive) -> map directly to canonical type.
- Empty Type, or a value not in the vocabulary (e.g. a person's name like "Himanshu", a stray token) -> type: unknown. Flag the row in the output under "needs operator decision: unknown type". Do NOT coerce to story or infer from the title.
- Bug/task do not appear in this backlog format; if one ever does, route it to the support lane convention (type bug/task), not the portfolio.

## Status value-map
Map the source Status to a canonical status, and flag anything unrecognized:
- DONE -> done-class (a completion candidate; reconcile proposes marking done, never auto-applies)
- IP -> PENDING OWNER CONFIRMATION: meaning unconfirmed (likely in-progress, not verified). Flag under needs-operator-decision; do not assert until the sheet owner confirms.
- NYS -> PENDING OWNER CONFIRMATION: meaning unconfirmed. Flag under needs-operator-decision; do not assert until the sheet owner confirms.
- In Analysis, Needs Analysis -> analysis/discovery
- BLOCKED -> blocked
- Duplicate -> dedup-flag: the SOURCE itself declares this row a duplicate. Preserve it and surface it as a strong dedup signal for reconcile (still operator-confirmed, never auto-merged).
- blank/empty -> unscored/backlog
- any other value -> status: unknown, flag under "needs operator decision: unknown status".

## Ref rules - embedded keys are proposed, never auto-linked
- Scan Notes for any <SOURCE_KEY_PREFIX>-<digits> pattern (prefix from keel.config.json; skip if unset). If found, set source.ref to that key as a PROPOSED cross-source reference (a match hint for reconcile against the Jira lane), draft-labeled. Never treat it as a confirmed link.
- Multiple keys in one Notes cell -> list all as candidates; reconcile resolves which, if any, applies.
- No key -> source.ref: "".

## Draft labeling
All inferred content is proposed. Prefix any generated description with "[draft - review] ". The canonical proposals are not committed items - they are inputs to reconcile. Never present inferred content as settled.

## Output (hold-in-output, no files written)
Emit to the chat, do not write to disk:
1. Per-item canonical proposals - for each row, the mapped fields: type, name, status, job_size, priority context, description (draft), source.origin: backlog-xlsx, source.ref (proposed key or blank). Skip the empty trailing rows.
2. TYPE HISTOGRAM - counts by mapped type (epic / feature / story / unknown), so the portfolio-vs-unknown mix is visible before reconcile.
3. NEEDS OPERATOR DECISION - list rows with: unknown type, unknown status, embedded-key candidates (proposed refs), and source-declared duplicates. These are the rows reconcile cannot resolve without a ruling.
4. SUMMARY - total rows read, count mapped cleanly vs flagged, and a one-line statement that these are proposals for reconcile, nothing written.

## Rules
- Read-only. Emit proposals to chat; never write, create, move, or modify. No staging files - hold output in chat for reconcile to consume in the same session.
- Never guess type or status; flag unknowns for the operator.
- Embedded keys and duplicate flags are proposals/signals, never auto-applied.
- Read per `### Sheet:` block so a multi-tab backlog parses correctly; tier comes from the Type column, not sheet structure.
- Dates are ET (box is America/New_York).
- This does not reconcile and does not apply. It normalizes one source to canonical proposals. Reconcile compares; the operator approves; apply writes.
