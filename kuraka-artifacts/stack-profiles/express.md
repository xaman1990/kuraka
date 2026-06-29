# Stack Profile — TypeScript / Express

**Profile version**: 1
**Covers**: Express 4–5, TypeScript 5.x, Node 20–22, package manager npm/pnpm
(often inside an npm-workspaces monorepo). ORM-agnostic.
**Status**: draft (seeded from kuraka-control retros — expand as cycles run)

---

## When this profile applies

The agent loads this profile when `stack.backend.framework` in
`kuraka.config.yaml` equals `express`.

## Implementation order

1. Types / domain model.
2. Repository / data-access (or filesystem layer when there is no DB).
3. Service (business logic).
4. Route handler (thin) + router wiring.
5. App composition (`createApp()`), then server bootstrap.

Order matters because handlers depend on services, and the app factory must
compose routers last.

## Idiomatic file paths

Relative to `architecture.paths.backend_root`.

| Artifact | Path |
|---|---|
| App factory | `src/app.ts` (exports `createApp()`) |
| Server bootstrap | `src/index.ts` (imports `createApp`, listens) |
| Routes | `src/routes/{resource}.ts` |
| Services | `src/services/{name}.ts` |
| Repositories / fs layer | `src/repositories/{name}.ts` |
| Types | `src/types/{name}.ts` |

## Architecture invariants

- **Export a pure `createApp()` factory** from `src/app.ts`; `src/index.ts` only
  imports it and calls `listen()`. WHY: a side-effecting `index.ts` forces every
  integration test to rebuild the app inline (arki seeded this gap in kuraka-control).
- **Route handlers are thin** — validation + service call + response shaping only;
  no business logic, no direct data access.
- **"Green" includes typecheck** — `vitest`/`jest` transpile per-file and do NOT
  typecheck the graph. A story is not done until `tsc --noEmit` exits 0. Prefer a
  single `make check` = lint + typecheck + test (kuraka-control LL-014: an invalid
  cast rode green ~3 cycles).
- **Every externally-owned `nullable` field is an adversarial input** — guard null
  before binding it into a token scope, a conflict key, or a map key.
- **Fail-open mock defaults are forbidden in prod** — a mock/live factory whose
  mock path skips a security control (signature verify, auth) must throw on `is_prod()`.
- **Gate command integrity** — the test gate must be able to fail; never pipe it
  (`make test | tail`), ensure `--exit-code-from` / proper exit propagation.

## Test patterns

- **Unit tests**: `vitest` / `jest`; mock the service/repo layer.
- **Integration tests**: `supertest` against `createApp()` (not a live server);
  `httpx`/`nock`-style mocking for outbound clients — exercise the live client
  path at least once, asserting by call-count, not message strings.
- **File location**: `*.test.ts` next to source or under `tests/`.
- **Shared DB hygiene**: assert deltas / `>=`, never absolute row counts; strip
  comments/docstrings before any token-scan meta-test.

## Naming and typing conventions

- `camelCase` for variables/functions, `PascalCase` for types.
- Distinguish `field?: T` from `field: T | null` in DTOs.
- Classify error provider responses on structured `code`/`param`, never message text.

## Reference command surface

| Purpose | Typical command |
|---|---|
| Lint | `eslint .` (needs `eslint.config.js` for ESLint v9 flat config) |
| Format | `prettier --write .` |
| Typecheck | `tsc --noEmit` |
| Test | `vitest run` / `jest` |
| Check (all) | `make check` (lint + typecheck + test) |

## Common pitfalls

- **Missing `eslint.config.js`** with ESLint v9 installed → `eslint .` errors or
  no-ops; arki must seed the flat config per workspace.
- **Side-effecting `index.ts`** with no `createApp()` factory.
- **Monorepo misdetection** — npm-workspaces repos must be treated as monorepos
  (root `package.json` `workspaces`); verify, don't trust `single-package`.
- **Verifying a write surface only via green tests** — exercise the mutation
  end-to-end against a disposable temp store, then assert the real store untouched.

## Anti-patterns flagged by reviewers

- Business logic inside route handlers.
- Catch-all `try/catch` that swallows and returns 200 while masking desync.
- Replaying a persisted external ID without verify-or-self-heal.
- Async route handlers without error propagation to the error middleware.
