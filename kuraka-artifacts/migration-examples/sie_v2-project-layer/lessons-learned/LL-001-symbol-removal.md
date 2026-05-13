---
id: LL-001
title: Symbol removal/renaming requires repo-wide grep before REQ is approved
date: 2026-04-10
incident_ref: docs/process/REQ-history/ (see retros covering symbol-removal incidents)
applies_to: [po-analyst, architect-reviewer]
severity: medium
tags: [refactor, symbol-removal, grep, scope]
---

## Context

Multiple REQs proposed to "eliminate function X" or "rename column Y"
listed only the obvious files (the file where the symbol is defined +
1–2 callers the writer remembered). Implementation phase then revealed
additional references in tests, docs, providers, and integration scripts,
forcing scope creep and rework after the REQ was already approved and
stories cut.

## Pattern to detect

The REQ description contains any of:

- "Eliminate / remove / delete `{symbol}`"
- "Rename `{old_name}` to `{new_name}`"
- "Deprecate `{symbol}`"
- Spanish equivalents: "eliminar", "remover", "renombrar", "deprecar".

Where `{symbol}` is a function, class, constant, variable, column, table,
endpoint path, or configuration key.

## Required action (before approving the REQ)

For each `{symbol}` mentioned in a removal/rename, the `po-analyst` must:

```bash
# Full repo grep — code, tests, docs, scripts, migrations
grep -rn "{symbol}" .
```

Then in the REQ's "Affected Services & Repositories" section:

- List every file and line that contains `{symbol}`.
- For each, note: in-scope (will be updated), out-of-scope-but-affected
  (will break if not updated — flag as story or BLOCKER), documented
  reference (e.g., in a retro or LL file; usually safe to leave or update
  later).

The `architect-reviewer` re-runs the grep in Phase 3 to confirm the list
is current. Drift between Phase 1 grep and Phase 3 grep usually means
some other change landed in main; reconcile before freezing the schema.

## Indirect impact

If the symbol is a constant or config key, also list every function that
imports or references it. The indirect callers may not change in name but
will change in behavior or break at import.

## Why this exists

A renamed function that compiles but is referenced in a markdown docstring
or in a generated SQL string is silent until production. The grep is cheap;
the silent break is not.

## Related

- `review-checks/po-analyst.md` — operational checklist version of this lesson.
- Past incidents are listed in the project's retros directory.
