# Morning Briefing

Produce a concise decision-readiness briefing from the portfolio. Read:
- state/action-register.md (open and in-progress actions)
- state/*.yaml roadmap items (stage, next action, risk)
- state/daily-logs/ recent entries (what changed recently)
- knowledge/people/*.md (open commitments)

Output, in this order, in prose not heavy formatting:

1. **Top priorities today** — the few items that most need a decision or move,
   drawn from highest-value / highest-risk roadmap items and their next actions.
2. **Due and overdue** — actions with due dates at or past today, owner and item.
3. **Blocked** — anything marked BLOCKED, with what it waits on.
4. **Recent changes** — what moved since the last briefing, from daily logs.
5. **Open commitments** — outstanding stakeholder commitments worth surfacing.

Rules:
- Decision readiness, not a data dump. Lead with what needs the operator's attention.
- If a section has nothing, say so in one line; do not invent entries.
- Reference ACT- numbers and item names so the operator can act.
- Terse, practitioner register. No corporate filler.
