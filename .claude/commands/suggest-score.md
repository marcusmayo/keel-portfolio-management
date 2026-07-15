# Suggest Scores

Propose WSJF and/or RICE scoring components for a work item, for the operator to review and
approve. This is a SUGGESTION step — do not write approved scores until the operator confirms.

Input: a work item key (e.g. ST-001) or name. Read that item's YAML for context
(name, summary, description, stage, value, risk, dependency, acceptance criteria).

Produce suggested components using the fixed scales from CLAUDE.md:
- WSJF (Fibonacci 1,2,3,5,8,13,20): suggest user_business_value, time_criticality,
  risk_reduction_opportunity, job_size — with a one-line rationale for EACH, drawn from
  the item's context. Then compute the suggested WSJF.
- RICE: suggest reach (count/period), impact (3/2/1/0.5/0.25), confidence (1.0/0.8/0.5),
  effort (person-weeks) — each with a one-line rationale. Then compute suggested RICE.

Present as a clear proposal:
  "Suggested WSJF for ST-001: value 8 (rationale), time-criticality 5 (rationale),
   risk 3 (rationale), job-size 3 (rationale) -> WSJF = 16/3 = 5.3"

Then state explicitly:
  "These are estimates for your review. Reply with: APPROVE (write as-is),
   ADJUST <changes> (revise then write), or REJECT (write nothing)."

Rules:
- These are SUGGESTIONS. Do NOT write them into the item file in this step.
- Always show rationale per component and the computed result — never a bare number.
- Be honest about confidence: if the item lacks context to estimate a component, say so
  and suggest what input is needed rather than guessing.
- Only on the operator's explicit APPROVE or ADJUST do you write — and when you write, set the
  prioritization status to "scored" and note in the item that scores were Claude-suggested,
  the operator-approved, with the date.

### Consult the knowledge base first
Before generating, read relevant files in knowledge/, knowledge/context/, knowledge/inbox/, and knowledge/people/
for product, market, strategy, and stakeholder context. Ground generated descriptions,
acceptance criteria, scoring rationale, and drafts in this real context — use the actual product
names, terminology, and constraints found there rather than generic inference. If no relevant
context exists, proceed but say the output is generic for lack of grounding. Never fabricate
facts not supported by the knowledge base or the input.
