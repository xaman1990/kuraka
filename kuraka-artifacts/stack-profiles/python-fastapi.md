# Stack Profile — Python / FastAPI

**Profile version**: 1
**Covers**: Python 3.10+, FastAPI 0.100+, SQLAlchemy 2.x, Pydantic v2,
Alembic, pytest. Package manager: pip / poetry / uv (any).
**Status**: stable

---

## When this profile applies

The agent loads this profile when `stack.backend.framework` in
`kuraka.config.yaml` equals `fastapi`. Companion conventions assumed when
present in the config:

- `stack.backend.orm: sqlalchemy`
- `stack.database.migration_tool: alembic`

If the project uses FastAPI without these companions, the agent should
adapt rather than enforce the SQLAlchemy/Alembic sections below.

## Implementation order

When implementing a story, create files in this order:

1. **Migration** (only if schema changes) — adds the table/column.
2. **Model** — SQLAlchemy class mapping to the table.
3. **Schema** — Pydantic models for request/response shapes (Create, Update,
   Response are separate classes; do not reuse the model class as a schema).
4. **Repository** — data access only. One repository per aggregate.
5. **Service** — business logic. Calls repositories; never DB directly.
6. **Endpoint** — HTTP handling only. Delegates to services.

Order rationale: each layer imports the previous one. Reversing the order
produces files that fail import or pass type-check but break at first use.

## Idiomatic file paths

Paths are relative to `architecture.paths.backend_root` from the config.
The agent should mirror this layout unless
`.claude/project/conventions/architecture.md` overrides it.

| Artifact | Path |
|---|---|
| Models | `api/models/{module}/{model}.py` |
| Schemas | `api/schemas/{module}/{schema}.py` |
| Repositories | `repositories/{module}/{repository}.py` |
| Services | `api/services/{module}/{service}.py` |
| Endpoints | `api/endpoints/{module}/{endpoint}.py` |
| Migrations | `{migrations_root}/{YYYYMMDD}_{NNNN}_{slug}.py` |
| Tests | `tests/unit/{layer}/{module}/test_{name}.py` |

Where `{module}` is the bounded context the artifact belongs to (e.g.,
`tools`, `users`, `cases`). The agent picks `{module}` from the story's
scope; if the story doesn't name one, ask the user.

## Architecture invariants

Rules the agent enforces because of FastAPI's idioms. Violations are
flagged as IMPORTANT or BLOCKER during review.

- **No try/except in endpoints.** Middleware translates exceptions to HTTP
  responses. Endpoints that catch exceptions defeat the global error contract
  and produce inconsistent response shapes.
- **No try/except in services either** unless there's a meaningful local
  recovery (rare). Default behavior is to let exceptions propagate to the
  endpoint, where middleware handles them. Catching to log-and-rethrow is
  an anti-pattern (the middleware already logs).
- **No `db.query(...)` inside services.** Services must call a repository
  method. Direct DB access in services makes the service un-mockable in unit
  tests and couples business logic to the ORM.
- **No business logic in endpoints.** The endpoint signature + delegation +
  return is the whole body. Logic of any kind (filtering, branching on
  business state, computing derived values) belongs in the service.
- **No SQL/ORM expressions in repositories' return values.** Repositories
  return models or simple lists/dicts; never query objects. Callers must not
  add filters on top of a repository result.
- **No layer skipping.** Endpoint → Service → Repository → Model.
  An endpoint that imports a repository directly, or a service that hits an
  endpoint, is a BLOCKER finding.
- **Pydantic models for I/O, SQLAlchemy models for persistence.** Do not pass
  a SQLAlchemy instance to the endpoint response; convert to its Pydantic
  schema explicitly.

## Test patterns

- **Framework**: pytest with AAA (Arrange / Act / Assert) pattern.
- **Endpoint tests**: `from fastapi.testclient import TestClient`. Each test
  uses a fresh client fixture; do not share state across tests.
- **Unit tests for services**: mock the repository, do not hit the DB. The
  service's tests are about business logic, not data access.
- **Unit tests for repositories**: use an in-memory or test DB; assert the
  emitted SQL or the returned shapes.
- **Fixtures**: live in `tests/conftest.py` at the layer where they're shared.
  Common: `db_session`, `test_tenant`, `client`, `auth_headers`.
- **File location**: tests mirror the source layout one-for-one
  (`api/services/X.py` → `tests/unit/services/test_X.py`).
- **Naming**: `test_should_{action}_when_{condition}` — declarative, reads
  as a sentence.

## Naming and typing conventions

Stack-specific (generic conventions like `naming_language` come from CFG).

- **`T | None`** instead of `typing.Optional[T]`. The `Optional[T]` alias is
  legacy (pre-3.10) and the union syntax is the project standard.
- **No `from __future__ import annotations`** unless the project requires
  Python ≤ 3.9 compat. The union syntax above already requires 3.10+.
- **Strict types in function signatures.** Every parameter and return value
  is annotated. Untyped functions are an IMPORTANT finding.
- **`async def`** for any endpoint or service that touches I/O. Mixing sync
  and async in the same call stack is a common subtle bug.
- **`Enum` (or `StrEnum`) for closed sets** of states/types. String literals
  for states are flagged as magic strings.

## Reference command surface

Typical FastAPI project commands. The actual commands run come from
`stack.backend.{lint,test,typecheck,format}_cmd` in the config; this is
reference for someone writing a fresh config.

| Purpose | Typical command |
|---|---|
| Lint | `ruff check .` |
| Format | `ruff format .` |
| Typecheck | `mypy .` (or `pyright`) |
| Test | `pytest` (or `make test` if the project wraps it) |
| Single-file test | `pytest tests/path/to/file.py -v` |
| Migration apply | `alembic upgrade head` |
| Migration create | `alembic revision -m "{slug}"` |

## Common pitfalls

- **Repository returning query objects.** A repository method like
  `def get_active(self): return db.query(X).filter(X.active==True)` lets the
  caller chain more filters and breaks the abstraction. Return the executed
  list/model.
- **Service injecting `Depends`.** `Depends` is for endpoint signatures.
  Services receive their dependencies via `__init__`. A service that uses
  `Depends` cannot be unit-tested without spinning up FastAPI's DI.
- **Pydantic schema reused as DB model.** Causes circular import nightmares
  and surfaces ORM internals in the API contract.
- **Synchronous DB calls in `async def` endpoints.** Blocks the event loop.
  Either use async SQLAlchemy or put the sync call in a `run_in_threadpool`.
- **Forgetting `response_model=` on endpoints.** Without it, FastAPI returns
  whatever the function returns, which often leaks fields. Always declare.

## Anti-patterns flagged by reviewers

- Catching `Exception` to "log and re-raise" (loses traceback context;
  middleware already logs). Use `logger.exception(...)` only at the top of
  long-running tasks.
- Returning `dict` from a service. Hides what the caller is supposed to do
  with the data; use a Pydantic model or a dataclass.
- Using `**kwargs` in repository signatures. Defeats type-check and makes
  the repository's contract opaque. Spell out the parameters.
- Mixing transactions across repositories without a unit-of-work wrapper.
  If two repositories must commit atomically, the orchestration of that
  belongs in a service, not in the endpoint.
- Renaming an entity (model class, table, column) without updating
  string-based references. Beyond the obvious code callers, also update:
  Alembic migrations that reference the old name (data migrations, seed
  scripts), import scripts in `scripts/` or `bin/`, and any JSON/YAML
  config files. `grep -rn "{old_name}" .` is the cheapest verification.
