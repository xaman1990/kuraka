# Tenant isolation — sie_v2 convention

## Scope

Every tenant-scoped table in sie_v2 has a `tenant_id` column (FK to
`tenants.id`). Every query against such a table must filter by
`tenant_id`, even when the application logic "knows" only one tenant
should be present.

## Tables that are NOT tenant-scoped

Global lookups, framework metadata, and cross-tenant shared resources.
Examples: `alembic_version`, `currencies`, `countries`,
`scheduling_task_types`. When in doubt, default to tenant-scoping
and revisit if requirements truly demand global scope.

## Repository pattern (correct)

```python
class CaseRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def list_active(self, tenant_id: int) -> list[Case]:
        return (
            self._db.query(Case)
            .filter(Case.tenant_id == tenant_id, Case.active.is_(True))
            .all()
        )
```

Every public method accepts `tenant_id` (or receives it via a context
object) and includes it in every `.filter()`. There is no exception.

## Service pattern (correct)

Services receive the tenant context (from auth) and pass it through to
repositories. They never hardcode a tenant.

```python
class CaseService:
    def __init__(self, repo: CaseRepository) -> None:
        self._repo = repo

    def get_active_cases(self, tenant_id: int) -> list[CaseResponse]:
        cases = self._repo.list_active(tenant_id=tenant_id)
        return [CaseResponse.from_model(c) for c in cases]
```

## Endpoint pattern (correct)

The tenant comes from the auth dependency. Do not accept `tenant_id` as
a request body / query parameter for tenant-scoped operations — that
would let any authenticated user query any tenant's data.

```python
@router.get("/cases", response_model=list[CaseResponse])
async def list_cases(
    current_user: User = Depends(get_current_user),
    service: CaseService = Depends(get_case_service),
) -> list[CaseResponse]:
    return service.get_active_cases(tenant_id=current_user.tenant_id)
```

## Anti-patterns (flag as HIGH+ in security review)

- A repository method whose signature does not include `tenant_id`
  (or equivalent), unless the table is documented as not tenant-scoped.
- A `.filter()` call on a tenant-scoped table that does not include
  `Model.tenant_id ==`.
- An endpoint that accepts `tenant_id` from the request body or query
  string and trusts it without cross-checking against `current_user.tenant_id`.
- A service that hardcodes a tenant value, even "just for testing".
- A migration that introduces a new tenant-scoped table without a
  `tenant_id` column + FK + index.

## Detection commands

```bash
# Repository methods missing tenant_id
grep -rn "def .*:" backend/repositories/ | grep -v "tenant_id"

# Filter calls on tenant-scoped models without tenant_id check
# (run per-model; this requires the reviewer's judgment about which
#  models are tenant-scoped — the convention says all unless documented otherwise)
grep -rn "\.filter(" backend/api/services/ | grep -v "tenant_id"
```

## Related

- `review-checks/security-reviewer.md` — full set of security greps that
  include tenant checks among other checks.
- `lessons-learned/LL-DD-896-IS-XX-*.md` — historical incidents where a
  tenant leak slipped through review (if any).

## Why this convention exists

The product is multi-tenant SaaS. A leak across tenants is a contract
breach with every customer simultaneously. The cost of one missed
`tenant_id` filter in production exceeds the cost of a thousand redundant
checks during review.
