---
description: daily activity rollup — today, or any past day (/digest yesterday, /digest 2026-06-18)
---

Produce a short, glanceable rollup of activity for a given day, read from the daily logs.

## Which day

Parse the argument after `/digest`:
- No argument → today (ET).
- `yesterday` → the day before today (ET).
- A weekday name (`monday`, `wednesday`, etc.) → the MOST RECENT past occurrence of that weekday. If ambiguous (could mean this week or last), state which date you used.
- An ISO date `YYYY-MM-DD` → that exact day.
- Anything you cannot resolve → say so plainly and ask for an ISO date.

Always state the resolved date explicitly at the top, e.g. "Digest for Wednesday, June 18, 2026."

## Where to read

The day's log is at `state/daily-logs/<YYYY-MM-DD>.md`. It has a `## Actions` section with lines formatted `- HH:MM ET — <verb> <what> (<refs>)`.

If the file does not exist OR has no entries under `## Actions`, say plainly that nothing was recorded through Keel that day (note: this means nothing ran THROUGH Keel — direct file edits over SSH are not captured). Do not invent activity.

## What to produce

Keep it genuinely glanceable — this is low-friction awareness, not a report. Two parts:

Open with the resolved date line, then two short labelled sections. Do NOT use markdown headers (no ##/###) or bold — just the plain labels "What moved:" and "Still open:" each on their own line, with the content below. Keep the whole thing visually light.

What moved:
Group the day's logged actions into a short recap, lightly clustered by theme (documents handled, roadmap work, drafts written, triage done, etc.). Plain past-tense lines. Collapse repetition — if five documents were staged, say "I staged five documents" with the names, not five separate lines. Aim for 3-8 lines total. No timestamps unless a specific time matters.

Still open:
A brief look at loose ends as of that day:
- Anything in `knowledge/inbox/` awaiting triage (check the directory).
- Drafts written but not acted on, if the log shows a draft with no corresponding send/discard.
- If the weekly CEO report is due within two days of the digest date (it's due Fridays), note it.

If nothing is open, say "Nothing pending" — don't pad.

## Tone

First person where natural ("I staged...", "I drafted..."), matching how Keel speaks elsewhere.

CRITICAL — translate, do not pass through. The daily log is written in internal shorthand (work-item keys like ACT-001 or EP-003, counts like "three epics, nine features", terms like "ingested", "transcript", "unscored", "WSJF", "RICE"). Your output must NOT contain any of that. Translate it into plain executive language:
   – "ingested a team member's transcript" → "reviewed a team member's training session"
- "opened ACT-001 through ACT-006" → "captured the follow-up actions from it"
- "created three epics, nine features, fourteen stories" → "mapped out the roadmap for it"
- "items are unscored / need WSJF inputs" → "those still need prioritizing"
Never name a work-item key, never give a count of epics/features/stories, never say WSJF or RICE. If you catch yourself about to write one, rephrase to what it means in plain terms.

Short. Scannable. This is a glance, not a read.

## Do not

- Do not send anything anywhere. This is a read-only summary.
- Do not modify the daily log or any state.
- Do not summarize days other than the one resolved.
