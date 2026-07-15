# People Lookup

Surface everything known about a stakeholder, from their page plus cross-referenced
commitments across the portfolio.

Input: a person's name (or partial). Find their page in knowledge/people/*.md.
If no page matches, say so and list who does have pages. If multiple match, list them.

For the matched person, present:
- **Who**: name, role, relationship to the portfolio, communication preference.
- **Open commitments**: from their page's Open commitments section.
- **Decision authority**: what they approve / own.
- **Related actions**: scan state/action-register.md for any action where this person is
  the Owner or is named in the Action text. List ACT number, action, status.
- **Related work items**: scan state/*.yaml for work items listing this person in
  `stakeholders`. List key, name, stage.
- **Recent context**: the latest few entries from their Notes log.

Rules:
- Read-only. Never modify files.
- Cross-reference the register and work items, not just the page — the value is showing
  their commitments across the whole portfolio in one view.
- If a section is empty, say so in one line. Do not invent commitments or context.
- Terse, practitioner register.
