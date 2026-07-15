# Show

Display the full content of a single work item in a readable form for the chat.

Input: a work item key (EP-###, FE-###, or ST-###) — e.g. "/show ST-002".
Find state/<...>.yaml whose key matches. If no match, say so and list available keys.

Print, formatted for reading (not raw YAML):
- **Key — Name**  (type, status, stage)
- **Parent**: key + name (or "top-level" for an epic)
- **Description**: full text (user-story format for stories)
- **Acceptance criteria**: numbered list, showing [draft - review] markers as-is
- **Priority**: computed WSJF/RICE if scored, override rank+reason if set, else "unscored"
- **Stakeholders**: names
- **Children**: for an epic, its features AND any story whose parent is the epic directly; for a feature, its stories (key + name + status each). A feature-less story is listed under its epic, never dropped.
- **Next action**: next_action and any ACT- ref
- For stories, show **Size** (small / NEEDS-DECOMPOSITION)

Rules:
- Read-only. Never modify.
- Show acceptance criteria in full — this is the view for reviewing them.
- If a field is empty, show it as "—" rather than omitting, so gaps are visible.
- Terse formatting; this is for quick review in chat.
