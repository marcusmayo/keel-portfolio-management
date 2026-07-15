# Decompose

Break a work item down a level: an EPIC into its features, or a FEATURE into small stories.

Input: a work item key (EP-### or FE-###) — e.g. "/decompose FE-001". Read that item's YAML
for context (name, summary, description, acceptance_criteria, parent).
An Epic may also be given an optional `stories` argument (e.g. `/decompose EP-001 stories`), which selects flat mode: decompose the epic straight to stories, with no feature tier. Default with no argument keeps the feature layer.

If the target is an EPIC:
- Identify the features needed to deliver it. Create each as a FE-### work item, parent = the
  epic, with a short contextual description and first-pass acceptance_criteria (3-6 bullets).
- Then, for each new feature, ALSO decompose it into stories (as below).
Flat mode (when the `stories` argument was given): do NOT create features; skip the two epic steps above. Instead create the stories directly under the epic: identify the small stories that deliver the epic and create each as a ST-### work item, parent = the epic key, using the same user-story description format, testable acceptance_criteria, and [draft - review] labeling defined below, and applying the INVEST size check; flag any story that cannot be sized small with NEEDS-DECOMPOSITION.

If the target is a FEATURE:
- Identify the small stories that deliver it. Create each as a ST-### work item, parent = the
  feature, with:
  - `description` in user-story format: "As a <role>, I want <capability>, so that <benefit>"
  - testable `acceptance_criteria` (Given/When/Then or checklist)
  - `size: small`

### Story size check (INVEST — Small)
Every story must be SMALL: single role, single workflow, completable in a few days, one
increment. If a story would be too large, do NOT write it as one story:
- Either split it into multiple small stories, OR
- If it genuinely can't be sized yet, create it with `size: NEEDS-DECOMPOSITION`, note in its
  summary why, and flag it in the output as needing further breakdown.
Prefer splitting into small stories over leaving a large one.

### Keys and links
- Sequential keys per type (read existing files for the next number; never reuse).
- Set `parent` correctly on every created item.
- In flat mode the parent of every created story is the epic key, never a feature.

### Draft labeling
Decomposition is inference, not stated content. Prefix every generated `description` and
acceptance-criterion with "[draft - review] " so it's clear these are proposed, for review.

### Output
List what was created: keys, names, parent links, and any stories flagged
NEEDS-DECOMPOSITION. Note that all generated content is draft for review.

Rules:
- Read the target item first; build from its real context, don't invent unrelated scope.
- Keep stories small; flag oversized ones rather than writing a too-big story.
- Do not modify the parent item's own fields — only create children.

### Summary must show acceptance criteria
In the output, for EACH story created, show its user-story description AND its acceptance
criteria (or at minimum an AC count per story), not just the title. The operator reviews
decomposition in chat and must see the AC without opening files.

### Consult the knowledge base first
Before generating, read relevant files in knowledge/, knowledge/context/, knowledge/inbox/, and knowledge/people/
for product, market, strategy, and stakeholder context. Ground generated descriptions,
acceptance criteria, scoring rationale, and drafts in this real context — use the actual product
names, terminology, and constraints found there rather than generic inference. If no relevant
context exists, proceed but say the output is generic for lack of grounding. Never fabricate
facts not supported by the knowledge base or the input.
