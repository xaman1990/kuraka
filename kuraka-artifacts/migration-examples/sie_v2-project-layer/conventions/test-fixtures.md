# Test fixtures inventory — sie_v2

Catalog of fixtures available in `backend/tests/conftest.py` and where
to use them. Loaded by `test-engineer` and `backend-developer` (Phase 6)
to avoid reinventing fixtures that already exist.

## Available fixtures

| Fixture | Scope | Purpose |
|---|---|---|
| `db_session` | function | Transaction-scoped DB session with auto-rollback per test. Use for repository and integration tests. |
| `client` | function | FastAPI `TestClient` with auth mock enabled. Use for endpoint tests. |
| `auth_headers` | function | `{"Authorization": "Bearer test-token"}` — pre-built header dict. |
| `admin_headers` | function | Same as `auth_headers` but with admin role claims. |
| `test_tenant` | session | Creates or reuses test tenant (`id=1`). Idempotent — safe to call from any test. |
| `mock_compania` | function | Sample company dict that mirrors a real `companias` row. Use for service unit tests that need a company shape. |
| `mock_expediente` | function | Sample expediente dict for service unit tests touching expedientes. |

## Test environment defaults

| Variable | Value | Effect |
|---|---|---|
| `ENVIRONMENT` | `testing` | JWT middleware is SKIPPED — auth headers are accepted as-is. |
| `TEST_SEED` | `42` | Deterministic random values across runs. |

Tests run inside Docker via `make test`. The PostgreSQL test DB is
re-migrated to head via Alembic at suite startup.

## Rules

- **Don't recreate fixtures that exist.** If you need a company shape,
  use `mock_compania`; do not build your own dict.
- **`test_tenant` is shared.** Multiple tests can reference it
  concurrently; never mutate it in a way that affects other tests.
- **`db_session` rolls back automatically.** Never call `session.commit()`
  in a test expecting cleanup; the rollback handles it.

## Where it's loaded

- `test-engineer` Phase 2.5 (test planning) — knows which fixtures are
  available when planning what to test.
- `test-engineer` Phase 6 (test writing) — uses them to write tests.
- `backend-developer` Phase 6 fallback — when writing tests in the
  primary implementer role.
