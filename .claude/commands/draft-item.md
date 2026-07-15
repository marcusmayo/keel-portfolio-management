# Draft Item

Author a description + acceptance criteria for a work item, and write it in as a
[draft - review] draft. Two modes:

- EXISTING item: the operator gives a key (e.g. "/draft-item ST-042"). Draft into
  that item if it has no real description.
- NEW item from text: the operator gives an idea, not a key (e.g. "/draft-item As
  a user I want to bulk-export transcripts so that ..."). CREATE a new item, let
  Keel assign the key and infer the type, then draft into it.

## Decide the mode
- If the input is a work-item key (matches like ST-42, EP-7, FE-13), it is
  EXISTING mode -> read that item's YAML from state/ or support/.
- Otherwise the input is idea text -> NEW-item mode.

## EXISTING mode: when to act vs. decline
- ACT only if the item's description is EMPTY, missing, or a bare placeholder
  ("Imported from Jira ...", or under ~30 chars of real content).
- If it already has a substantive authored description, DECLINE: say so and point
  to the export + /apply-edits. Do not overwrite authored content.

## Consult the knowledge base first (both modes)
Read relevant files in knowledge/, knowledge/context/, knowledge/inbox/,
knowledge/people/ for product, market, stakeholder context. Ground the draft in
the real product -- actual feature names, terminology, constraints. If no
grounding exists, proceed but say the draft is generic. NEVER fabricate facts,
dates, or commitments. Prefer a clear [bracketed placeholder] over a guess.

## What to produce (house format by type)
- epic    -> description: what/why (1-3 sentences); AC = high-level done-outcomes (3-6).
- feature -> description: short contextual; AC = capability-level conditions (3-6).
- story   -> description: "As a <role>, I want <capability>, so that <benefit>";
             AC = testable Given/When/Then (2-4).

## How to write it (deterministic tool does the write)
Do NOT hand-edit YAML. After composing the draft, call the writer:

EXISTING mode (you have the key):
    python3 tools/draft_item_write.py --key <KEY> \
      --desc "<description text>" --ac "<ac line>" --ac "<ac line>" ...

NEW-item mode (idea text, no key -- Keel assigns key + type):
    python3 tools/draft_item_write.py --create-text "<the operator's idea text>" \
      --desc "<polished description>" --ac "<ac line>" --ac "<ac line>" ...

Pass description/AC text WITHOUT the [draft - review] prefix -- the tool adds it.
In NEW-item mode the tool prints the assigned key (e.g. "created new story
ST-250"); tell the operator that key.

Type inference (NEW mode): the tool infers epic/feature/story from phrasing
("As a..." -> story; "ability to/capability" -> feature; "initiative/theme" ->
epic; default story). The operator can force it by starting the text with
"epic:", "feature:", or "story:".

## After writing
Tell the operator: the item's draft (and its key, if newly created) is now in the
portfolio as [draft - review] content, flagged for confirmation. Review it in the
Keel-Origin export; a newly-created item also appears in the Unconfirmed sheet
(confirm it via /apply-inference). Approve the text by removing the [draft -
review] prefix and running /apply-edits.

## Rules
- Only description + acceptance_criteria are written (plus item creation in NEW mode).
- Everything written carries the [draft - review] prefix (the review gate).
- New items are flagged draft-inferred -> they go through the confirmation gate.
- Decline on already-authored existing items rather than overwriting.
