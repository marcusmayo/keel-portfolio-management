# Portfolio Health

Cross-check consistency across the whole portfolio and report mismatches. Read:
- state/*.yaml work items
- state/action-register.md
- knowledge/people/*.md stakeholder pages
- state/daily-logs/ recent entries

Check and report each category (only list items that have a problem):

1. **Broken work-item links** — any work item whose `parent` references a key that
   does not exist.

2. **Action ↔ work-item links** — any work item whose `next_action_ref` points to an
   ACT number not in the register; any register action that references a work item key
   (in its Action text) that no longer exists.

3. **Stakeholder ↔ commitment consistency** — any action whose Owner is a person with no
   stakeholder page; any open commitment on a stakeholder page that has no matching action
   in the register.

4. **Stale / orphaned** — work items in `in-progress` status with no open action driving
   them; actions marked OPEN whose referenced work item is `done`.

5. **Unscored work items** — epics/features with no scoring inputs and no override (these
   need prioritization).

Output: for each category, list the specific items and the mismatch. If a category is
clean, say so in one line. End with a short "suggested fixes" list — but do NOT modify any
files; this check is read-only and advisory.

Rules:
- Read-only. Report only; never write.
- Be specific: name the keys, ACT numbers, and people involved in each mismatch.
- Do not flag normal states (e.g. a backlog item with no action is fine; an in-progress
  one without an action is not).

6. **Possible duplicates** — compare work items for overlap that suggests duplication:
   - two items (any type) describing the same capability under different keys
   - a story that substantially duplicates another story (same role + same goal)
   - a feature whose scope is already covered by another feature
   For each suspected pair, list both keys, names, and why they look like duplicates, and
   suggest a resolution (merge into one, or confirm they're distinct). This is advisory:
   report candidates, never auto-merge. Judge by described capability, not just similar names —
   and do not flag a parent/child relationship as a duplicate.
