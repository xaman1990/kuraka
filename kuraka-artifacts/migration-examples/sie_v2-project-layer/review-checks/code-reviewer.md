# Review checks — code-reviewer (sie_v2)

Project-specific checks the `code-reviewer` agent runs in addition to its
generic framework + stack profile instructions. Loaded automatically when
the agent runs in this project.

## 1. Cache invalidation namespace coverage

**When it applies**: any change that writes to Redis (or any other cache
backend used by the project).

**The check**:

When the implementation calls `cache.invalidate(KEY)`, every sub-key that
lives in the same namespace must be invalidated too. A single top-level
invalidation leaves stale sub-keys for the next sync cycle.

```bash
# For each cache KEY touched by the change, search for variants in the backend:
grep -rn "{KEY}" backend/ --include="*.py"
```

Common sub-key patterns to look for:

- `{KEY}` (the canonical top-level key)
- `f"{KEY}:last_sync"`
- `f"{KEY}:meta"`
- `f"{KEY}:{id}"`
- `f"{KEY}:by_tenant:{tenant_id}"`

**Required action**:

- ALL sub-keys must be invalidated together with the top-level key,
  otherwise stale data survives the cache flush.
- If there are multiple sub-keys, prefer
  `cache.invalidate_pattern(f"{KEY}*")` over multiple individual
  `invalidate` calls — the pattern call is atomic within the namespace.
- If a new sub-key is introduced by this change, verify the existing
  invalidation points already cover it (or update them).

**Severity**:

- BLOCKER if any sub-key is missed in the invalidation.
- IMPORTANT if individual invalidations are used where a single pattern
  call would be safer.

**Why**: see `lessons-learned/LL-002-cache-invalidation.md`.

## 2. Audit log presence on state-mutating operations

**When it applies**: any new endpoint or service method that mutates state
on tenant-owned data (case status changes, contract updates, tool runs).

**The check**: the implementation must call the audit logger
(`audit.log(event, actor, target, metadata)`) before returning. Search
for the mutation pattern; if no `audit.log` call accompanies it, flag.

**Severity**: IMPORTANT (some teams flag as BLOCKER — calibrate with the
project owner).
