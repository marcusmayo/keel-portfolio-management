# Pipeline Status

Produce a prioritized portfolio status from state/*.yaml roadmap items.

For each item, read its prioritization block and determine its ranking basis:
1. If priority_override.rank is set -> use the override. Show the rank AND the
   override reason. The override takes precedence over any computed score.
2. Else if the WSJF or RICE components are present -> COMPUTE the score:
   - WSJF = (user_business_value + time_criticality + risk_reduction_opportunity) / job_size
   - RICE = (reach * impact * confidence) / effort
   Show the computed score and which framework.
3. Else (no override, no components) -> the item is UNSCORED.

Output three groups, in this order:
- **Prioritized** — items with an override or a computed score, ordered by priority
  (overrides first by rank, then computed scores high-to-low). For each: name, stage,
  score or override rank, and override reason if present.
- **Needs prioritization** — all unscored items. For each, note which inputs are missing
  (WSJF components and/or RICE inputs) so the operator knows what to provide.
- **By stage** — a short count of items per lifecycle stage.

Rules:
- Compute scores from components; never accept or invent a final score.
- If an item has partial components (some but not all inputs for a framework), list it
  under Needs prioritization and name the specific missing inputs — do not compute a
  partial score.
- Show override reasons always — the rationale must be visible.
- Terse, practitioner register. No corporate filler.
