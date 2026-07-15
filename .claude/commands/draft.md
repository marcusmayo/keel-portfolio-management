# Draft

Compose a communication (email, message, or update) in the operator's voice.

Input: what the message is about, and to whom (e.g. "/draft a status update to Jordan
on the SSO story slipping a week"). Read:
- system/voice-profile.yaml — apply the operator's voice exactly.
- The recipient's page in knowledge/people/ if named — use their role, comms preference,
  and context to pitch the message appropriately.
- Any referenced work item or action in state/ for accurate detail.

Apply the voice profile strictly:
- Greeting "Hi [First name]," — sign-off "Thanks, the operator".
- Structure: Context → Specifics → Ask or Next Step.
- Frame any ask as options, not open-ended questions.
- No bold in body. No hedging "just". No corporate filler (leverage, utilize, circle back).
  Active voice for own actions. Prefer one recommended approach over a menu.

Output the draft only (subject line if it's an email). Then one line below it:
"Review: reply SEND (yours to send manually), EDIT <changes>, or DISCARD."

Rules:
- Draft only — the operator reviews and sends manually. Do not claim to send anything.
- Use real detail from the portfolio files; do not invent facts, dates, or commitments.
  If a needed fact isn't in the files, leave a clear [bracketed placeholder] rather than
  guessing.
- Match the recipient's communication preference (e.g. concise/async for someone who
  prefers written) where their page states one.
- Keep it tight — the operator consolidates and avoids filler.

### Consult the knowledge base first
Before generating, read relevant files in knowledge/, knowledge/context/, knowledge/inbox/, and knowledge/people/
for product, market, strategy, and stakeholder context. Ground generated descriptions,
acceptance criteria, scoring rationale, and drafts in this real context — use the actual product
names, terminology, and constraints found there rather than generic inference. If no relevant
context exists, proceed but say the output is generic for lack of grounding. Never fabricate
facts not supported by the knowledge base or the input.
