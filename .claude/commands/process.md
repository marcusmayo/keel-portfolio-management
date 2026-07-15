# Process

Batch-triage every pending document in the triage inbox (knowledge/inbox/), then graduate each
processed document to the context library.

For each file in knowledge/inbox/ with frontmatter triaged: false (or no triaged field):
1. Triage it exactly as the /triage skill does: extract action items into state/action-register.md
   with the next ACT numbers; create/update typed work items (epic/feature/story) with parent links,
   inferred content labeled [draft - review], stories in As a/I want/so that with Given/When/Then AC,
   size small; update stakeholder pages for anyone with a commitment; record material changes in the
   daily log. Ground everything in the knowledge base (knowledge/, knowledge/context/, knowledge/inbox/).
2. After triaging, set the file's frontmatter triaged: true in place. The file stays in knowledge/inbox/ and is now both triaged and durable context. Never mv the file; the gate blocks file moves by design.

Process documents oldest-first by ingested date. After all are done, give ONE consolidated summary:
which documents were processed, what work items each produced (by key), and which graduated in place.
If knowledge/inbox/ is empty, say there is nothing to process and stop.

Respect the work-item model and draft-labeling. Never fabricate facts not supported by the source
or knowledge base. Flag anything inferred for review.
