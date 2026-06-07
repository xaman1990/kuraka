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

## 3. Hardcoded fallbacks masking config errors

**When it applies**: any provider/integration code that reads auth URLs,
contract names, credentials, realms or retry limits from config.

**The check**: convenience fallbacks that silently substitute a value when
config is missing are PROHIBITED — they hide the real misconfiguration
until it blows up end-to-end in production (this masked the Keycloak UAT
realm when prod `token_url` was missing, RETRO-2026-06-04). Grep the
provider code:

```bash
grep -rn "_FALLBACK\|_DEFAULT" backend/ --include="*.py"
# and config-lookup `or` fallbacks:
grep -rn "token_url or \|contract_name or \|realm or " backend/ --include="*.py"
```

If a URL / credential / contract / realm is supplied via a fallback,
flag it. The code MUST raise an error that names the missing field.

**Severity**: BLOCKER. "Config fallbacks hide real misconfiguration. If X
is missing, raise an error that names it; do not silently use a fallback."

## 4. Test reconciliation after refactors

**When it applies**: any refactor that renames a class/method, moves an
API, or removes a contract (especially in provider code).

**The check**: stale tests left behind after a refactor are dead code and
must not be carried forward as "pre-existing failures".

- [ ] Every `test_*` that references the changed class/method either PASSES
      or is explicitly SKIPPED with a comment explaining why (deferred).
- [ ] No test file exercises a removed API/class (e.g. `test_outbound.py`
      testing the deleted `COMMUNICATION_MAP`).
- [ ] If a test is skipped, a ticket is filed with the exact skip reason.
- [ ] If a class is renamed, factory convention AND its tests are updated
      in the same PR.

**Severity**: IMPORTANT. Stale tests are dead code — clean them up, don't
carry them forward as noise.
