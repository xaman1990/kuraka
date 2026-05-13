---
id: LL-002
title: Cache invalidation must cover every sub-key in a namespace, not just the top-level key
date: 2026-03-XX
incident_ref: docs/process/agent-retrospectives/ (the project's stale-cache incident retro)
applies_to: [code-reviewer, backend-developer]
severity: high
tags: [redis, cache, invalidation]
---

## Context

A change invalidated a single top-level cache key (`cache.invalidate(KEY)`)
but left behind sub-keys within the same namespace (`KEY:last_sync`,
`KEY:meta`, `KEY:by_tenant:N`). The next sync read the stale sub-keys and
served outdated data; the bug surfaced in production hours after merge
and required a manual cache flush + a follow-up patch to make the
invalidation namespace-aware.

## Pattern to detect

Code that:

- Calls `cache.invalidate(KEY)` for a specific key.
- Defines or uses sub-keys derived from `KEY` (any `f"{KEY}:..."` pattern).
- Does not invalidate the sub-keys together with the top-level key.

## Required action by the reviewer

For each `cache.invalidate(KEY)` call in the change:

1. Run `grep -rn "{KEY}" backend/` to find every sub-key derived from it.
2. Verify ALL of them are also invalidated.
3. If multiple sub-keys exist, prefer `cache.invalidate_pattern(f"{KEY}*")`
   over individual invalidations — it's atomic across the namespace.
4. If a new sub-key is introduced in the change, ensure existing
   invalidation sites are updated to include it.

## Why this exists

A partial invalidation leaves the system in a state that *parses* and
*runs* but returns stale data. The bug doesn't show up in unit tests
(they typically clear the cache between cases) and slips past code
review unless the reviewer specifically looks for the sub-key pattern.

The cost of a 30-second grep at review time is dwarfed by the cost of a
stale-cache incident in production.

## Related

- `review-checks/code-reviewer.md` check #1 — operational form of this
  lesson, executed every time `code-reviewer` runs on changes that
  touch the cache.
- `conventions/cross-provider-conventions.md` (when present) — the cache
  layout per provider may have specific sub-key shapes documented.
