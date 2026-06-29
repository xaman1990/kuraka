# 🪢 Kuraka — Control Plane

> Phase 0 dashboard (Obsidian-native). Requires the **Dataview** plugin.
> Definition: [[CONTROL-PLANE]] · Recurring issues: [[RECURRING-ISSUES]]

## Projects

```dataview
TABLE
  status,
  stack,
  kuraka_version AS version,
  has_project_layer AS "proj-layer",
  default_mode AS mode,
  last_mount AS mounted
FROM "projects"
SORT status ASC, name ASC
```

## Onboarding / attention

```dataview
LIST "→ " + path
FROM "projects"
WHERE status = "onboarding" OR has_project_layer = false
```

## Agent catalog (framework source of truth — edit ONLY here)

```dataview
TABLE model, description
FROM "agents"
WHERE model
SORT model ASC, file.name ASC
```

> Routing convention: **opus** = judgment-heavy (po-analyst, reviewers, final-auditor);
> **sonnet** = implementation; **haiku** = mechanical.

## RETRO triage feed

```dataview
TABLE project, decision, applied
FROM "retro-triage"
WHERE file.name != "_TEMPLATE"
SORT file.name DESC
```

## Quick links
- [[CONTROL-PLANE]] — architecture & roadmap
- [[RECURRING-ISSUES]] — latest cross-cycle pattern report
- `agents/` — framework agents · `skills/` — phase skills · `rules/` — meta-rules
