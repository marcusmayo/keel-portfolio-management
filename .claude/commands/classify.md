# Classify

Read-only triage-routing view over knowledge/inbox/. For each staged artifact, propose where it belongs and why. NEVER route, move, modify, or create anything — this proposes; the operator decides and the downstream skills act.

List every file in knowledge/inbox/. For each, read its frontmatter (source, ingested, triaged) and enough of the body to judge content. Skip files already marked triaged: true unless asked to re-examine.

## Route each artifact to ONE of four dispositions

1. backlog - a work-item source: a backlog export (CSV/xlsx), a Jira export, or an OCR'd board/issue screenshot. Its rows ARE work items (epic/feature/story/bug/task). Routes to the import pipeline (normalize -> reconcile -> diff -> apply). Until that pipeline exists, label it backlog and list it; do not attempt to create items.

2. context - reference material, not a work-item source and not owner action material: product overviews, strategy docs, market analyses, specs read for grounding. Belongs in the context lane (knowledge/context/), read by skills for grounding, never reconciled as work items.

3. triage - owner-authored or owner-adjacent notes, transcripts, or meeting summaries whose value is action items, decisions, and stakeholder commitments. Handled by /process exactly as today.

4. mixed - an artifact that is more than one of the above at once and must be FANNED OUT, not forced into a single bucket. The common case is a meeting transcript that simultaneously (a) carries action items and decisions (triage), (b) references existing tickets with status changes to reconcile against the portfolio (backlog-reconcile), and (c) raises a net-new defect or task destined to be tracked (support/ lane creation). For a mixed artifact, list each component separately with its own route, so the operator can dispatch each part. Do not merge them into one action.

## Per-artifact output

For every artifact, report:
- filename and frontmatter source + ingested date (ET)
- detected kind: csv | jira-export | ocr-text | notes | transcript | reference-doc
- proposed route: backlog | context | triage | mixed (for mixed, the component breakdown)
- one-line reasoning
- confidence: high | medium | low

### Additional reporting by kind

- For a tabular backlog source (csv/jira-export): report a TYPE HISTOGRAM - counts by detected item type (Epic / Story / Bug / Task / Sub-task or the source's equivalents) so the type mix is visible before normalization and the operator can see which rows are portfolio vs support-lane vs out-of-scope. Also report the DETECTED COLUMN MAPPING (which source column maps to which work-item field) so the normalizer inherits a verified header map. Both are proposals to confirm, not applied.

- For an OCR-sourced artifact (ocr-text from a screenshot): flag it LOWEST TRUST. OCR drops and corrupts keys and status tokens, so every field is draft and an OCR'd key is NEVER a match key - it is a hint to confirm against an authoritative export. State this explicitly on the artifact.

- For a transcript routed mixed: when ticket references appear as spoken-digit prose (e.g. "seven, six, eight" = 768, "NG Seven Five Nine" = NG-759), surface them as PROPOSED references to confirm, never auto-resolved - spoken-digit parsing is fuzzy by nature. Net-new defects raised in discussion ("we'll put a new ticket in") are proposed as support/ lane creations with source.origin: keel.

## Tail summary

Counts per route across all artifacts (backlog / context / triage / mixed), and which artifacts need operator decisions before anything downstream runs. If knowledge/inbox/ is empty, say the inbox is empty and stop.

## Rules
- Read-only. Never route, move, modify, create, or send. This is a proposer.
- Never auto-merge or auto-resolve. Fuzzy and OCR-derived references are always proposed for confirmation.
- Dates are ET (box is America/New_York). Use the ingested frontmatter date.
- Ground judgments in actual frontmatter and content; never invent a source tag or a ticket reference not present in the artifact.
- This does not replace /process or the import pipeline - it routes TO them. State-changing work happens there, on operator confirmation.
