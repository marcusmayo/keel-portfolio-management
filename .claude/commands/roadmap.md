# Roadmap View

Produce a hierarchical roadmap from state/*.yaml work items (type epic/feature/story),
at a depth controlled by an optional argument after the command.

## Depth levels (argument)
- (no arg) or "ef"  -> Epics + Features + any story whose direct parent is an epic (feature-less stories surface under their epic; stories under features stay in deeper views)
- "epics"           -> Epics only
- "features"        -> Features only (flat list, no epic grouping)
- "full"            -> Epics + Features + Stories
- "fs"              -> Features + their Stories, plus direct epic-child stories listed under their epic key (no story is dropped for lacking a feature)
Accept reasonable synonyms (e.g. "stories" -> full, "all" -> full). If the arg is a work-item
KEY instead of a level, expand just that branch in full (epic with its features+stories, or
feature with its stories).

## Building the tree
Link by parent. Indent by depth in the actual parent chain, not by tier rank: a story whose parent is an epic sits one level under that epic; a story whose parent is a feature sits two levels under the epic. One line per item:
  EPIC     EP-001  Enterprise readiness        [stage] [status] [priority]
    FEATURE  FE-001  SSO                        [stage] [status] [priority]
      STORY    ST-001  Configure SAML SSO       [stage] [status] [AC: 3] [size]

Per line show: key, name, stage, status, and priority (computed WSJF/RICE if scored,
override rank if set, else "unscored"). For stories also show AC count and size.
At "features" level, list features flat with their parent epic key noted.

## Summary (always)
- counts by type (epics / features / stories)
- orphans: any item whose parent points to a missing key (flag these)
- unscored count
- any stories with size NEEDS-DECOMPOSITION (flag for breakdown)

Rules:
- Read-only. Never modify.
- Respect the requested depth — do not show deeper tiers than asked.
- If a parent key is missing OR a story has no parent set at all, list the item under "Orphaned / broken links" so nothing imported can land unparented and vanish.
- Reads state/ only; the support/ lane (type bug/task) is non-portfolio and deliberately excluded.
- Terse; the tree is the output.
