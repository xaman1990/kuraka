---
id: LL-DD-896-FM-01
title: Provider analysis missed a 765-LOC utility file that called the client API
date: 2026-04-23
incident_ref: docs/process/agent-retrospectives/RETRO-DD-896-linea-directa.md
applies_to: [po-analyst]
severity: high
tags: [provider, scope, dd-896, finding-mode-01]
---

## Context

During the DD-896 Linea Directa migration (v1 → v2), the `po-analyst`
listed the obvious files under `backend/src/providers/lineadirecta/` and
considered the inventory complete. The list missed
`utils/expedientNoEmail.js` (765 LOC), which was called from the API client
and contained provider-specific business logic for cases without an
associated email thread.

The omission was discovered during Phase 4 implementation, requiring four
separate human corrections to the Phase 1 REQ document and partial story
re-cutting.

## Pattern to detect

A requirement involving a provider integration, where the `po-analyst`
enumerates files based on:

- Names that match `provider.py`, `client.py`, `service.py`, or similar
  "obvious" entry points.
- A subset chosen by reading the directory's `README.md` or a top-level
  file index.
- The ticket's own enumeration (which is typically authored from memory
  by a human reporter).

## Required action

For any provider-related REQ, enumerate the provider directory
exhaustively using `find` (or equivalent), not by inspection or by
memory:

```bash
find backend/src/providers/{provider}/ -type f \
  | grep -v "__pycache__\|node_modules\|.pyc$\|.test.js$" \
  | sort
```

Cross-reference the resulting list against the ticket. Every file in
the directory must be classified in the REQ's "Affected Services &
Repositories" section as either:

- **In scope** (will be modified / removed / replaced)
- **Out of scope but co-located** (not touched, but reviewer should know
  it exists)
- **Boundary** (not modified directly, but is called by modified files —
  needs review even if not edited)

Files in `utils/`, `helpers/`, `lib/`, `_internal/` are the most commonly
missed; pay extra attention.

## Indirect impact

The 765-LOC file in this incident defined a Python class that mutated
the database state in a non-obvious way. Even a "no-touch" file can
hide invariants that the migration must preserve. Flag any utility file
that:

- Defines classes or functions used by the in-scope files.
- Touches `database/`, `cache/`, `queue/`, or external services.
- Contains state-bearing globals (singletons, caches, lazy loaders).

## Why this exists

The cost of a thorough `find` is ~30 seconds. The cost of discovering a
missed file during implementation is hours of REQ rework, story
re-cutting, and reviewer re-engagement. The asymmetry is severe.

## Related

- `LL-001-symbol-removal.md` — same family of "incomplete enumeration"
  failures, but for symbols rather than files.
- `review-checks/po-analyst.md` — operational check #1 is the version
  of this lesson the agent executes per requirement.
