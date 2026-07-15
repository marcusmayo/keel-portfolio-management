# Reconcile

Read-only. Compare normalized source proposals against the existing portfolio (state/*.yaml) and produce a five-bucket diff report with proposed follow-up actions, for the operator to review against the Jira backlog. NEVER write, create, move, modify, or apply anything. This produces a report; the operator decides; a separate apply step (not yet built) makes changes only on approval.

## Scope (stage 1)
Stage 1 reconciles ONE source against the portfolio: the Jira normalized proposals (from /normalize-jira) vs the 37 existing items in state/. Matching is DETERMINISTIC-LOCAL ONLY in this stage - no API/semantic calls. Exact and near-exact normalized-title matches auto-bucket; a middle similarity band is flagged "ambiguous - pending semantic pass" and held, NOT resolved and NOT sent for semantic judgment yet. (Stage 1b adds semantic matching for the ambiguous band. Backlog and transcript sources are added in later stages.)

## Inputs
- Existing portfolio: every state/*.yaml work item (skip _template). Read per item: key, type, name, status, stage, prioritization.wsjf.score, prioritization.rice.score, prioritization.status, updated, source.origin, source.ref.
- Source proposals: run /normalize-jira to get the canonical Jira proposals (key=Issue key, name=Summary, type, status, done-class flag, priority, dates). Use that normalized output; do not re-parse the raw CSV here.

## Matching - deterministic-local only (stage 1)
The existing items have EMPTY source.ref and keys in the EP/FE/ST namespace; Jira items carry their ref in source.ref, not in key. So there is NO key overlap - matching is by title.
1. Key match: if a Jira Issue key equals an existing item's source.ref, that is a definite match. (Currently none exist; this path is for after links are applied.)
2. Title match: normalize both titles (lowercase, trim, collapse whitespace, strip punctuation). 
   - Identical or near-identical normalized titles -> MATCH (high confidence).
   - Clearly unrelated (no meaningful token overlap) -> NO MATCH -> the Jira item is a gap.
   - Middle band (partial token overlap, plausibly the same item) -> AMBIGUOUS: flag "pending semantic pass", do NOT bucket as match or gap, do NOT send for semantic judgment in stage 1. List separately with both candidate titles so the count is visible.
Report the ambiguous count prominently - it is what stage 1b will resolve.

## Five buckets - the verdict for each item
- changed - matched (same item, both sides), but fields differ (status, priority, etc.) -> action: review/update.
- duplicate - the SAME item appears twice: a Jira source-declared relationship, OR two Jira rows with identical normalized titles (same summary, different key), OR a Jira item matching an existing item that already matches another. -> action: merge/confirm.
- completed - matched, the Jira side is done-class (Status in {Done, DEV Verified, Deployed DEV} or Resolution=Done) but the Keel item is not done -> action: mark done (proposed).
- conflict - matched by title but the sides DISAGREE on type or status in a way that is not just a simple field update (e.g. one calls it an Epic, the other a Story; one done, one to-do) -> action: resolve.
- gap - in the Jira source, no matching Keel item -> action: create (or rule out-of-scope). Most Jira portfolio items will land here, since the 37 Keel items are a curated subset.

## Report - the worklist (rendered in chat, hold-in-output)
Produce a table, grouped by bucket (changed, duplicate, completed, conflict, gap, then ambiguous-pending-semantic). Columns:
- source key (e.g. PROJ-###)
- canonical key (EP/FE/ST-### if matched, else blank)
- type
- title
- priority (from Jira; e.g. Medium/High)
- source status (Jira Status/Resolution)
- Keel status (matched item's status, else blank)
- WSJF (matched item's prioritization.wsjf.score; blank = unscored, NOT missing)
- RICE (matched item's prioritization.rice.score; blank = unscored)
- dates (Jira Updated, and/or Keel updated)
- verdict (the bucket)
- proposed action

Blank score/status/date cells mean the source does not carry that field (e.g. a Jira-only gap has no WSJF, no Keel status) - render blank, never invent a value.

## Summary (always)
- counts per bucket (changed / duplicate / completed / conflict / gap / ambiguous-pending-semantic)
- how many Jira items matched an existing item vs landed as gaps
- done-class count among matches (how many "completed" actions would be proposed)
- a one-line statement: this is a report; nothing was written or applied; the ambiguous band awaits the stage-1b semantic pass; apply happens only on operator approval.

## How to match (do this inline, NOT via a script)
Perform the title normalization and comparison as reasoning while producing the report. Do NOT write a matching script and do NOT execute code - reconcile is read-only and produces the report directly in your response. Read the existing item names and the Jira proposal titles, normalize them mentally (lowercase, strip punctuation, collapse whitespace), and judge match/gap/ambiguous per item. The comparison is well within direct reasoning; a script is unnecessary and would require execution approval, which this read-only skill must not need.

## Stage 1b - semantic pass on the ambiguous band (judge inline, NOT via embeddings or a script)
After the deterministic pass produces the ambiguous-pending-semantic list, judge each held pair by reasoning - same as deterministic matching, do this inline in your response, no embeddings service and no script. State the ambiguous count first (so it is visible what is being judged). For each pair, decide whether the Jira item and the candidate Keel item describe the SAME capability/story (judge meaning, not just title overlap), and give a one-line rationale. Then re-bucket:
- confirmed same + Jira is done-class -> move to COMPLETED (action: mark the Keel item done, proposed).
- confirmed same + Jira not done -> move to CHANGED (action: review/update, proposed) or CONFLICT if type/status disagree.
- judged distinct -> the Jira item is a GAP (action: create or rule out-of-scope).
- genuinely uncertain even after reasoning -> leave flagged for operator, do not force a verdict.
Show the re-bucketed results as an addendum to the report (do not silently rewrite the stage-1 buckets; show what moved and why). Still proposed - nothing is applied. If the ambiguous band is large (say >40 pairs), state the count and ask the operator before judging rather than judging all inline.

## Rules
- Read-only. Render the report in chat; never write, create, move, modify, or apply. Hold output in chat.
- Stage 1 is deterministic-local only: no API/semantic calls. The ambiguous band is flagged and held, never auto-resolved.
- Never auto-apply any verdict. Every bucket lists a PROPOSED action the operator confirms.
- Blank columns mean the field is absent in that source - render blank, never fabricate (especially WSJF/RICE, which only exist on Keel items and are mostly unscored).
- Matching is by normalized title (no key overlap exists yet); identical->match, unrelated->gap, middle->ambiguous-pending-semantic.
- Dates are ET (box is America/New_York).
- This does not apply changes. Reconcile reports; the operator approves; a later apply step writes.
